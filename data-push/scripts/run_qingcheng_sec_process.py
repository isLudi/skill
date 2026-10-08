"""Deliver five independent Qingcheng SEC process reports in one Windows batch."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import html
import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fetch_qingcheng_process_source import fetch, probe_revision
from lark_delivery.common import resend
from lark_delivery.common.im import invite_members, upload_image
from lark_delivery.common.readback import available as readback_available
from lark_delivery.common.retry import retry_transport
from lark_delivery.common.runtime import ensure_console_streams, run_lark
from preview_qingcheng_public_pool_process import _aggregate, _read_snapshot, _table_image
from preview_qingcheng_sec_process import SEC_BAR_FIELDS, _reminders, _sort_rows
from run_qingcheng_process import _batch as _existing_qingcheng_batch, _upstream_audit, _write_json, run_scope
from send_qingcheng_process import _verify_message


SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
CONFIG_PATH = SKILL / "config/departments/qingcheng/sec_process_batch.json"
REQUEST_DIR = CONFIG_PATH.parent
STATE = WORKSPACE / "runtime/qingcheng-sec-process-batch"
REPORT_IDS = ("sec_no_friend_supervisor", "sec_first_period_drop_supervisor",
              "sec_public_consultant", "sec_order_reuse_consultant", "sec_public_supervisor")
GRADES = ["高一", "高二", "高三", "初三"]
COLUMNS = {"期次", "年级", "主管", "顾问", "带班人数", "退前线索", "有效线索",
           "好友率", "等待时长", "24h首call", "沟通率", "外呼时长", "外呼频次", "总通时"}


def _config() -> dict:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    calendar = cfg["business_calendar"]
    if (cfg["schema_version"], cfg["domain"], cfg["execution_surface"], cfg["report_type"],
            cfg["status"], cfg["schedule_enabled"], cfg["windows_task_name"],
            calendar["period_rule"], calendar["process_weekdays"], calendar["hours"],
            calendar["minute"], calendar["deadline_minute"], calendar["retry_interval_minutes"],
            calendar["timezone"], cfg["source"]["lead_field"], cfg["sender"]["identity"],
            cfg["sender"]["open_id"], cfg["configuration_base_writeback"],
            cfg["source"]["base_token"], cfg["source"]["table_id"]) != (
            1, "qingcheng", "local", "process", "active", True,
            "Codex-Lark-Qingcheng-SEC-Process-GroupPush", "自然周周五期次",
             [1, 2, 3, 4, 5, 6], [12, 16, 20], 0, 50, 2, "Asia/Shanghai", "退前线索",
            "bot", "ou_f3907e865135732c15a1dfce27828411", "setup_only",
            "QOVib6QCXaUvJ2s2PsbcnMmsnGg", "tblXU4tla3bY36DE"):
        raise ValueError("SEC schedule, sender, or Base-write boundary differs")
    if cfg["upstream"] != _existing_qingcheng_batch()["upstream"]:
        raise ValueError("SEC qing2lark task pin differs from the active Qingcheng batch")
    if [entry["id"] for entry in cfg["reports"]] != list(REPORT_IDS):
        raise ValueError("The five SEC reports or their delivery order differ")
    if cfg["source"]["sources"] != {
            "sec_public": {"match": {"一级渠道": "公域", "渠道": "公域学霸", "部门": "SEC"}},
            "sec_order_reuse": {"match": {"一级渠道": "订单复用", "部门": "SEC"},
                                "allowed_secondary_channels": ["SEC未加好友", "SEC首期掉海", "SEC招生退费"]}}:
        raise ValueError("SEC source routing differs")
    bars = cfg["visual"]["metric_bars"]
    if (tuple(bars) != SEC_BAR_FIELDS or len({item["color"] for item in bars.values()}) != 4
            or any(item["min"] != 0 or item["max"] <= 0 for item in bars.values())):
        raise ValueError("SEC process color bars differ")
    if set(cfg["visual"]["integer_fields"]) != {"退前线索", "有效线索", "带班人数", "总通时"}:
        raise ValueError("SEC process integer display fields differ")
    expected = {
        "sec_no_friend_supervisor": ("sec_order_reuse", "SEC未加好友", "SEC未加好友", "主管", 5, True, "invite_then_text", "oc_a9e3165a2509e9878fae04dc8394f6b0"),
        "sec_first_period_drop_supervisor": ("sec_order_reuse", "SEC首期掉海", "SEC首期掉海", "主管", 5, True, "invite_then_text", "oc_a9e3165a2509e9878fae04dc8394f6b0"),
        "sec_public_consultant": ("sec_public", None, "公域", "顾问", 3, True, "invite_then_text", "oc_a8e793c81080ebf5b14dd22bd83a05a1"),
        "sec_order_reuse_consultant": ("sec_order_reuse", None, "订单复用", "顾问", 3, True, "invite_then_text", "oc_a8e793c81080ebf5b14dd22bd83a05a1"),
        "sec_public_supervisor": ("sec_public", None, "公域", "主管", 5, False, "invite_then_text", "oc_a9e3165a2509e9878fae04dc8394f6b0"),
    }
    for entry in cfg["reports"]:
        if tuple(entry[field] for field in ("source", "secondary_channel", "channel_name", "level",
                                            "minimum_leads", "split_grade", "unresolved_mention_action", "chat_id")) != expected[entry["id"]]:
            raise ValueError(f"SEC report routing differs: {entry['id']}")
        _request(entry)
    return cfg


def _request(entry: dict) -> dict:
    request = json.loads((REQUEST_DIR / entry["request_file"]).read_text(encoding="utf-8"))
    minimum = request["report"]["minimum"]
    columns = [part.strip() for part in request["report"]["process_display_order"].split("、")]
    if (request["routing"]["domain"], request["business"]["channel_name"],
            request["business"]["target_chat_id"], request["business"]["grades"],
            request["reminder"]["report_level"], request["reminder"]["target"],
            request["reminder"]["process_metric"], request["reminder"]["process_direction"],
            request["reminder"]["process_rank"], minimum["operator"], minimum["value"]) != (
            "qingcheng", entry["channel_name"], entry["chat_id"], GRADES,
            entry["level"], entry["level"], "好友率", "最低", "最后1名", ">=", entry["minimum_leads"]):
        raise ValueError(f"SEC Base application differs: {entry['id']}")
    if (not columns or len(columns) != len(set(columns)) or set(columns) - COLUMNS
            or "期次" not in columns or "好友率" not in columns
            or set(SEC_BAR_FIELDS) - set(columns)
            or (entry["split_grade"] and "年级" not in columns)
            or (entry["level"] == "主管" and "主管" not in columns)
            or (entry["level"] == "顾问" and "顾问" not in columns)):
        raise ValueError(f"SEC Base display columns differ: {entry['id']}")
    return request


def _period(day: date) -> str:
    return (day + timedelta(days=4 - day.weekday())).strftime("%Y%m%d") + "期"


def _slot(now: datetime, cfg: dict) -> datetime:
    calendar = cfg["business_calendar"]
    if (now.tzinfo is None or now.utcoffset() != timedelta(hours=8)
            or now.weekday() not in calendar["process_weekdays"]
            or now.hour not in calendar["hours"]
            or not calendar["minute"] <= now.minute <= calendar["deadline_minute"]
            or (now.minute - calendar["minute"]) % calendar["retry_interval_minutes"]):
        raise ValueError("Outside the SEC process schedule")
    return now.replace(minute=calendar["minute"], second=0, microsecond=0)


@contextmanager
def _single_instance():
    if os.name != "nt":
        raise RuntimeError("The SEC scheduled sender requires Windows")
    import msvcrt

    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / "scheduled.lock").open("a+b") as handle:
        handle.seek(0)
        if not handle.read(1):
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise RuntimeError("Another SEC process batch is running") from exc
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _fresh(manifest: dict, slot: datetime) -> None:
    snapshot = manifest["snapshot"]
    source_time = datetime.strptime(f"{snapshot[0]} {int(snapshot[1]):02d}", "%Y%m%d %H").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    age = (slot - source_time).total_seconds() / 60
    if age < 0 or age > 240:
        raise ValueError("SEC source snapshot is outside the freshness window")


def _source_rows(source: str, period: str, slot_dir: Path, audit: dict, cfg: dict,
                 slot: datetime | None) -> tuple[list[dict], dict]:
    path = slot_dir / source / "source.ndjson"
    manifest = fetch(source, period, path)
    rows, manifest = _read_snapshot(path, {"source": cfg["source"]["sources"][source]})
    names = ("公域学霸",) if source == "sec_public" else ("SEC未加好友", "SEC首期掉海", "SEC招生退费")
    expected = sum(audit["raw_channel_counts"].get(name, 0) for name in names) if audit else len(rows)
    if manifest["records_count"] != expected or manifest["period"] != period:
        raise ValueError(f"SEC {source} source count or period differs from upstream audit")
    if audit and [str(value) for value in manifest["snapshot"]] != [str(value) for value in audit["snapshot"]]:
        raise ValueError(f"SEC {source} source snapshot differs from upstream audit")
    if source == "sec_order_reuse":
        allowed = set(cfg["source"]["sources"][source]["allowed_secondary_channels"])
        if any(row["渠道"] not in allowed for row in rows):
            raise ValueError("SEC order-reuse source contains an unreviewed secondary channel")
        for name in allowed:
            if audit and sum(row["渠道"] == name for row in rows) != audit["raw_channel_counts"].get(name, 0):
                raise ValueError(f"SEC {name} raw source count differs from upstream audit")
    if slot:
        _fresh(manifest, slot)
    return rows, manifest


def _build_report(entry: dict, source_rows: list[dict], manifest: dict, cfg: dict, output: Path) -> dict | None:
    request = _request(entry)
    rows = ([row for row in source_rows if row["渠道"] == entry["secondary_channel"]]
            if entry["secondary_channel"] else source_rows)
    grouped = _aggregate(rows, entry["level"], request, split_grade=entry["split_grade"],
                         lead_field=cfg["source"]["lead_field"])
    if not grouped:
        return None
    grouped = _sort_rows(grouped, request["business"]["grades"], split_grade=entry["split_grade"])
    reminders = _reminders(grouped, request["business"]["grades"], entry["level"],
                           split_grade=entry["split_grade"])
    columns = [part.strip() for part in request["report"]["process_display_order"].split("、")]
    output.mkdir(parents=True, exist_ok=True)
    image = output / "process.png"
    bars = cfg["visual"]["metric_bars"]
    _table_image(grouped, columns, image, entry["level"], manifest["period"], entry["channel_name"],
                 split_grade=entry["split_grade"],
                 bar_specs={field: (spec["min"], spec["max"], spec["color"]) for field, spec in bars.items()},
                 integer_fields=frozenset(cfg["visual"]["integer_fields"]))
    lines = [f"## 🔥 **【{manifest['period']}】{entry['channel_name']}渠道{entry['level']}过程数据播报**", "",
             "![过程数据](process.png)", ""]
    lines.extend(f"- {item['grade'] + '年级' if item['grade'] else ''}好友率较低的{entry['level']}："
                 + "、".join(person["name"] for person in item["people"]) for item in reminders)
    message = "\n".join(lines)
    (output / "message.md").write_text(message + "\n", encoding="utf-8")
    review = {"report_id": entry["id"], "level": entry["level"], "chat_id": entry["chat_id"],
              "period": manifest["period"], "source_rev": manifest["rev"], "snapshot": manifest["snapshot"],
              "raw_rows": len(rows), "eligible_rows": len(grouped), "reminders": reminders,
              "image": image.name, "message": message,
              "unresolved_mention_action": entry["unresolved_mention_action"]}
    _write_json(output / "review.json", review)
    return review


def _data(args: list[str], timeout: int = 90) -> dict:
    envelope = json.loads(run_lark(args, timeout=timeout))
    if envelope.get("ok") is not True or not isinstance(envelope.get("data"), dict):
        raise RuntimeError("Feishu operation returned no successful data")
    return envelope["data"]


def _members(chat_id: str, sender_open_id: str) -> set[str]:
    data = _data(["im", "+chat-members-list", "--chat-id", chat_id, "--member-types", "user,bot",
                  "--member-id-type", "open_id", "--page-all", "--page-limit", "10",
                  "--as", "bot", "--format", "json"])
    users, bots = data.get("users", []), data.get("bots", [])
    if (data.get("has_more") is not False or data.get("truncations")
            or data.get("user_total") != len(users) or data.get("bot_total") != len(bots)):
        raise ValueError("SEC group member list is incomplete")
    ids = {item.get("member_id") for item in users}
    if not all(ids) or len(ids) != len(users):
        raise ValueError("SEC group member IDs are missing or duplicated")
    if sender_open_id not in {item.get("member_id") for item in bots}:
        raise ValueError("SEC sender bot is absent from the target group")
    return ids


def _person_key(person: dict) -> str:
    return person.get("account") or person["name"]


def _resolve(entry: dict, review: dict, member_ids: set[str], chat_id: str = "",
             sender_open_id: str = "") -> tuple[dict[str, str], dict[str, str], set[str]]:
    """Resolve reminder people to native @ targets, with the 2026-10-04 fallback chain.

    Every candidate is first resolved against the directory (unique active employee,
    no group filter). A resolved account that is absent from the group is invited
    once by the sender bot and re-checked; anyone still absent afterwards, or
    unresolved/ambiguous in the directory, degrades to a plain-name mention. The
    person set can no longer block a push.
    """
    people = list({_person_key(person): person for group in review["reminders"]
                   for person in group["people"]}.values())
    if not people or any(not person.get("name") for person in people):
        raise ValueError("SEC reminder person set is empty or malformed")

    def query_for(person: dict) -> str:
        return (f"{person['account']}@gaotu.cn" if person.get("account")
                else re.sub(r"\d+$", "", person["name"]))

    queries = sorted({query_for(person) for person in people})
    statuses, users = {}, []
    for start in range(0, len(queries), 20):
        contact = _data(["contact", "+search-user", "--queries", ",".join(queries[start:start + 20]),
                         "--exclude-external-users", "--lang", "zh_cn", "--as", "user", "--format", "json"])
        statuses.update({item["query"]: item for item in contact.get("queries", [])})
        users.extend(contact.get("users", []))
    resolved, display, text_only = {}, {}, set()
    for person in people:
        key, name, account = _person_key(person), person["name"], person.get("account")
        query = query_for(person)
        status = statuses.get(query, {})
        if status.get("error") or status.get("has_more") is not False:
            raise ValueError(f"Contact search is incomplete for {name}")
        suffix = re.search(r"(\d+)$", name)
        candidates = {}
        for user in users:
            if (user.get("matched_query") != query or user.get("is_activated") is not True
                    or user.get("is_cross_tenant")):
                continue
            label = user.get("localized_name")
            email = str(user.get("enterprise_email") or "")
            if account:
                if email.casefold() != query.casefold():
                    continue
            elif label not in {name, query} or (suffix and not email.split("@", 1)[0].endswith(suffix.group(1))):
                continue
            open_id = user.get("open_id")
            if isinstance(open_id, str) and re.fullmatch(r"ou_[A-Za-z0-9]+", open_id):
                candidates[open_id] = label
        if len(candidates) > 1:
            # Group membership may disambiguate same-name employees: if exactly one
            # candidate is in the group, that is the precise @ target.
            in_group = {open_id: label for open_id, label in candidates.items() if open_id in member_ids}
            if len(in_group) == 1:
                candidates = in_group
        if len(candidates) == 1:
            resolved[key], display[key] = next(iter(candidates.items()))
        else:
            # Unresolved or ambiguous in the directory: plain-name fallback, never a block.
            text_only.add(key)
    if len(set(resolved.values())) != len(resolved):
        raise ValueError("Two SEC reminder identities point to one Feishu account")

    absent = {key: open_id for key, open_id in resolved.items() if open_id not in member_ids}
    if absent and chat_id and sender_open_id:
        invite = invite_members(chat_id, list(absent.values()), "bot", 90)
        review.setdefault("invite_attempts", []).append(invite)
        try:
            member_ids = _members(chat_id, sender_open_id)
        except Exception as exc:  # noqa: BLE001 - a re-check failure degrades to text
            review.setdefault("invite_attempts", []).append(
                {"invited": [], "pending": [], "error": str(exc)[:300]})
        for key, open_id in list(absent.items()):
            if open_id not in member_ids:
                # Still absent after the bot invitation: plain-name fallback.
                text_only.add(key)
                resolved.pop(key, None)
                display.pop(key, None)
    return resolved, display, text_only


def _render(review: dict, resolved: dict[str, str], display: dict[str, str], text_only: set[str], image_key: str) -> str:
    rendered = review["message"]
    for group in review["reminders"]:
        people = group["people"]
        names = [person["name"] for person in people]
        prefix = f"- {group['grade'] + '年级' if group['grade'] else ''}好友率较低的{review['level']}："
        original = prefix + "、".join(names)
        if rendered.count(original) != 1:
            raise ValueError("SEC reviewed reminder line differs from the person set")
        parts = []
        for person in people:
            key = _person_key(person)
            if key in resolved:
                parts.append(f'<at user_id="{resolved[key]}">{html.escape(display[key])}</at>')
            elif key in text_only:
                parts.append(html.escape(person["name"]))
            else:
                raise ValueError("SEC reminder person was neither mentioned nor explicitly text-only")
        rendered = rendered.replace(original, prefix + "、".join(parts))
    image_ref = f"]({review['image']})"
    if rendered.count(image_ref) != 1 or not image_key.startswith("img_"):
        raise ValueError("SEC message image reference differs")
    rendered = rendered.replace(image_ref, f"]({image_key})")
    actual_ids = set(re.findall(r'<at user_id="(ou_[A-Za-z0-9]+)">', rendered))
    if actual_ids != set(resolved.values()):
        raise ValueError("SEC native mentions differ from verified IDs")
    return rendered


def _receipt_status(path: Path) -> dict | None:
    """The settled verdict for one receipt, or None while the report may be re-driven.

    A receipt whose send was never confirmed, or whose readback failed, must come
    back as ``None`` so the round re-drives it. Only a verified send is settled.

    This used to return ``previous_attempt_requires_review`` for everything else,
    which made one transport reset unrecoverable: on 2026-09-29 12:20 the SEC
    公域主管 broadcast took a token-endpoint reset, and every later round read that
    verdict and refused, burning the whole window without re-trying.
    """
    if not path.exists():
        return None
    saved = json.loads(path.read_text(encoding="utf-8"))
    if resend.decide(saved.get("status"), saved.get("message_id")) == resend.DONE:
        return {"status": "sent_verified", "message_id": saved["message_id"], "receipt": str(path)}
    return None


def _key(entry: dict, period: str, slot: datetime) -> str:
    seed = "|".join(("qingcheng", "sec", entry["id"], entry["chat_id"], period, slot.isoformat()))
    return f"qcsec_{entry['id'][:12]}_{slot:%Y%m%d%H%M}_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _reverify(entry: dict, cfg: dict, prior: dict, receipt_path: Path) -> dict:
    """Read back a SEC message that is already in the group; never re-sends.

    This path has no send capability, so re-running it cannot duplicate a message.
    Everything the readback needs was recorded on the first attempt.
    """
    message_id, image_key = prior.get("message_id"), prior.get("image_key")
    if not message_id or not image_key:
        raise ValueError("SEC receipt lacks the message id or image key needed to re-verify")
    try:
        readback = _verify_message(entry["chat_id"], message_id, image_key, prior["period"],
                                   set(prior.get("mention_ids") or ()), cfg["sender"]["open_id"])
    except Exception as exc:
        if not readback_available(entry, entry["chat_id"]):
            # This group's content cannot be read back by anyone, so the failure says
            # nothing about delivery. Accept the acknowledged write and stop retrying.
            prior.update({"status": resend.UNVERIFIABLE, "readback_error": str(exc)})
            _write_json(receipt_path, prior)
            return {"status": resend.UNVERIFIABLE, "message_id": message_id, "receipt": str(receipt_path)}
        prior.update({"status": "sent_readback_unverified", "readback_error": str(exc)})
        _write_json(receipt_path, prior)
        raise
    prior.update({"status": "sent_verified", "readback": readback})
    prior.pop("readback_error", None)
    _write_json(receipt_path, prior)
    return {"status": "sent_verified", "message_id": message_id, "receipt": str(receipt_path)}


def _deliver(entry: dict, review: dict, manifest: dict, cfg: dict, output: Path, slot: datetime) -> dict:
    receipt_path = output / "send_receipt.json"
    settled = _receipt_status(receipt_path)
    if settled:
        return settled
    prior = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else None
    # A recorded message id means the message is in the group: re-read, never re-send.
    if prior and resend.decide(prior.get("status"), prior.get("message_id")) == resend.REVERIFY:
        return _reverify(entry, cfg, prior, receipt_path)
    # The probe is a precondition read: a transport failure means nothing was learned, so
    # it is retried in-round, while a returned revision that differs still fails closed.
    current = retry_transport(lambda: probe_revision(
        entry["source"], review["period"], output / "source_revision_probe.ndjson"))
    if current != manifest["rev"]:
        raise ValueError("SEC Base revision changed before delivery")
    member_ids = _members(entry["chat_id"], cfg["sender"]["open_id"])
    resolved, display, text_only = _resolve(entry, review, member_ids,
                                            chat_id=entry["chat_id"],
                                            sender_open_id=cfg["sender"]["open_id"])
    image = output / review["image"]
    image_key = upload_image(image, "bot", 90)
    markdown = _render(review, resolved, display, text_only, image_key)
    key = _key(entry, review["period"], slot)
    dry_run = json.loads(run_lark(["im", "+messages-send", "--chat-id", entry["chat_id"],
                                   "--markdown", markdown, "--idempotency-key", key,
                                   "--as", "bot", "--format", "json", "--dry-run"], timeout=90))
    if dry_run.get("ok") is not True:
        raise ValueError("SEC message dry-run failed")
    receipt = {"status": "send_attempt_started", "report_id": entry["id"], "chat_id": entry["chat_id"],
               "period": review["period"], "slot": slot.isoformat(), "source_rev": manifest["rev"],
               "idempotency_key": key, "mention_ids": sorted(resolved.values()),
               "text_only_names": sorted(person["name"] for group in review["reminders"]
                                         for person in group["people"] if _person_key(person) in text_only),
               "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
               "message_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
               # Re-issue evidence: the key is unchanged, so the platform dedupes if an
               # earlier attempt did land. Kept on the receipt because the retry loop
               # replaces it every round and the run log only records the final word.
               "resend_attempts": (prior or {}).get("resend_attempts", 0) + (1 if prior else 0),
               "prior_status": (prior or {}).get("status", "")}
    _write_json(receipt_path, receipt)
    try:
        sent = _data(["im", "+messages-send", "--chat-id", entry["chat_id"],
                      "--markdown", markdown, "--idempotency-key", key,
                      "--as", "bot", "--format", "json"])
    except Exception as exc:
        receipt.update({"status": "send_result_uncertain", "error": str(exc)})
        _write_json(receipt_path, receipt)
        raise
    message_id = sent.get("message_id")
    if not isinstance(message_id, str) or not message_id.startswith("om_"):
        receipt.update({"status": "send_result_uncertain", "response": sent})
        _write_json(receipt_path, receipt)
        raise ValueError("SEC send returned no message ID")
    receipt.update({"status": "sent_unverified", "message_id": message_id, "image_key": image_key})
    _write_json(receipt_path, receipt)
    try:
        readback = _verify_message(entry["chat_id"], message_id, image_key,
                                   review["period"], set(resolved.values()), cfg["sender"]["open_id"])
        receipt.update({"status": "sent_verified", "readback": readback})
    except Exception as exc:
        if readback_available(entry, entry["chat_id"]):
            receipt.update({"status": "sent_readback_unverified", "readback_error": str(exc)})
        else:
            # Unreadable group: the write was acknowledged, verification is impossible by
            # policy, and reporting a failure here would be a false alarm on every push.
            receipt.update({"status": resend.UNVERIFIABLE, "readback_error": str(exc)})
    _write_json(receipt_path, receipt)
    return {"status": receipt["status"], "message_id": message_id, "receipt": str(receipt_path)}


def run(*, now: datetime | None = None, output: Path | None = None) -> dict:
    cfg = _config()
    slot = _slot(now or datetime.now(ZoneInfo("Asia/Shanghai")), cfg)
    period = _period(slot.date())
    output = output or STATE / "slots" / slot.strftime("%Y%m%d-%H%M")
    output.mkdir(parents=True, exist_ok=True)
    batch_path = output / "batch.json"
    if batch_path.exists():
        previous = json.loads(batch_path.read_text(encoding="utf-8"))
        if (previous["period"], previous["slot"]) != (period, slot.isoformat()):
            raise ValueError("SEC batch output path belongs to another business slot")
    results = {entry["id"]: _receipt_status(output / entry["id"] / "send_receipt.json")
               for entry in cfg["reports"]}
    pending = [entry for entry in cfg["reports"] if results[entry["id"]] is None]
    batch = {"period": period, "slot": slot.isoformat(), "reports": results}
    if not pending:
        _write_json(batch_path, batch)
        return batch
    try:
        audit = _upstream_audit(period, slot)
        if not isinstance(audit.get("raw_channel_counts"), dict):
            raise ValueError("Qingcheng upstream audit lacks SEC channel counts")
    except Exception as exc:
        for entry in pending:
            results[entry["id"]] = {"status": "blocked_upstream", "error": str(exc)}
        _write_json(batch_path, batch)
        return batch
    batch["upstream_audit"] = audit

    source_data: dict[str, tuple[list[dict], dict]] = {}
    source_errors: dict[str, str] = {}
    for source in dict.fromkeys(entry["source"] for entry in pending):
        names = ("公域学霸",) if source == "sec_public" else ("SEC未加好友", "SEC首期掉海", "SEC招生退费")
        if sum(audit["raw_channel_counts"].get(name, 0) for name in names) == 0:
            source_errors[source] = "zero_source_rows"
            continue
        try:
            source_data[source] = _source_rows(source, period, output, audit, cfg, slot)
        except Exception as exc:
            source_errors[source] = str(exc)

    pin_path = output / "source_version.json"
    pin = json.loads(pin_path.read_text(encoding="utf-8")) if pin_path.exists() else None
    observed = {(manifest["rev"], tuple(manifest["snapshot"])) for _, manifest in source_data.values()}
    if len(observed) > 1:
        for source in source_data:
            source_errors[source] = "SEC source slices came from different Base revisions or snapshots"
        source_data.clear()
    elif observed:
        revision, snapshot = next(iter(observed))
        if pin and (pin["rev"], tuple(pin["snapshot"])) != (revision, snapshot):
            for source in source_data:
                source_errors[source] = "SEC source version changed inside the same delivery slot"
            source_data.clear()
        elif not pin:
            _write_json(pin_path, {"period": period, "slot": slot.isoformat(),
                                   "rev": revision, "snapshot": list(snapshot)})

    for entry in pending:
        report_id = entry["id"]
        report_dir = output / report_id
        try:
            if entry["source"] in source_errors:
                if source_errors[entry["source"]] == "zero_source_rows":
                    results[report_id] = {"status": "skipped_no_source_rows"}
                else:
                    raise ValueError(source_errors[entry["source"]])
            else:
                rows, manifest = source_data[entry["source"]]
                secondary = entry["secondary_channel"]
                if secondary and audit["raw_channel_counts"].get(secondary, 0) == 0:
                    results[report_id] = {"status": "skipped_no_source_rows"}
                else:
                    review = _build_report(entry, rows, manifest, cfg, report_dir)
                    if review is None:
                        results[report_id] = {"status": "skipped_no_eligible_rows"}
                    else:
                        results[report_id] = _deliver(entry, review, manifest, cfg, report_dir, slot)
        except Exception as exc:
            receipt = _receipt_status(report_dir / "send_receipt.json")
            results[report_id] = receipt or {"status": "blocked", "error": str(exc)}
        _write_json(batch_path, batch)
    return batch


def main() -> None:
    ensure_console_streams()  # pythonw.exe has no console streams
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--confirm-send", action="store_true")
    args = parser.parse_args()
    if args.check_config == args.confirm_send:
        parser.error("Choose exactly one of --check-config or --confirm-send")
    if args.check_config:
        cfg = _config()
        print(json.dumps({"status": "valid", "task": cfg["windows_task_name"],
                          "reports": [entry["id"] for entry in cfg["reports"]]}, ensure_ascii=True))
        return
    with run_scope(CONFIG_PATH, "sec_process_batch") as scope:
        scope.event("run_started", confirmed=True)
        with _single_instance():
            result = run()
        print(json.dumps({"period": result["period"], "slot": result["slot"],
                          "reports": result["reports"]}, ensure_ascii=True, indent=2))
        scope.adopt(result)
        failed = any(value["status"] not in {"sent_verified", resend.UNVERIFIABLE,
                                             "skipped_no_source_rows", "skipped_no_eligible_rows"}
                     for value in result["reports"].values())
        scope.exit_code = 1 if failed else 0
        if failed:
            scope.event("run_needs_attention")
            raise SystemExit(1)
        scope.event("run_finished")


if __name__ == "__main__":
    main()
