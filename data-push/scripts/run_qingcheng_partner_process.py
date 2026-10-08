"""Deliver the three Qingcheng partner-channel process reports in one batch.

Each channel (partner_books / partner_local / supervisor_local) has its own
target group and is fully isolated: source filtering, image build, mention
resolution, group membership check, delivery, and receipt are per channel; a
failure in one channel never blocks the other two. Shared gates (upstream
audit, same-revision source snapshots) block the affected batch only.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta
import hashlib
import html
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from fetch_qingcheng_process_source import fetch, probe_revision
from lark_delivery.common import resend
from lark_delivery.common.im import upload_image, verify_chat
from lark_delivery.common.readback import available as readback_available
from lark_delivery.common.retry import retry_transport
from lark_delivery.common.runtime import ensure_console_streams, run_lark
from preview_qingcheng_public_pool_process import (
    _aggregate,
    _read_snapshot,
    _reminder_people,
    _sort_process_rows,
    _table_image,
)
from run_qingcheng_process import _batch as _qingcheng_batch, _period, _upstream_audit, _write_json, run_scope
from run_qingcheng_sec_process import _members, _resolve
from send_qingcheng_process import _verify_message


SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
CONFIG_PATH = SKILL / "config/departments/qingcheng/partner_process_batch.json"
STATE = WORKSPACE / "runtime/qingcheng-partner-process-batch"
CHANNEL_IDS = ("partner_books", "partner_local", "supervisor_local")
FETCH_KEY = {"partner_books": "partner_books", "partner_local": "partner_local",
             "supervisor_local": "partner_local"}


def _config() -> dict:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cal = cfg["business_calendar"]
    if (cfg["schema_version"], cfg["domain"], cfg["execution_surface"], cfg["report_type"],
            cfg["status"], cfg["schedule_enabled"], cfg["windows_task_name"],
            cfg["configuration_base_writeback"], cal["period_rule"], cal["process_weekdays"],
            cal["hours"], cal["minute"], cal["deadline_minute"], cal["retry_interval_minutes"],
            cal["timezone"], cfg["source"]["lead_field"], cfg["sender"]["identity"],
            cfg["sender"]["open_id"], cfg["source"]["base_token"], cfg["source"]["table_id"],
            cfg["process_sort"], cfg["process_reminder"]) != (
            1, "qingcheng", "local", "process", "active", True,
            "Codex-Lark-Qingcheng-Partner-Process-GroupPush", "setup_only",
             "自然周周五期次", [1, 2, 3], [14, 18, 22], 0, 50, 2, "Asia/Shanghai",
            "退后线索", "bot", "ou_f3907e865135732c15a1dfce27828411",
            "QOVib6QCXaUvJ2s2PsbcnMmsnGg", "tblXU4tla3bY36DE",
            {"metric": "8min", "direction": "desc", "value": "unrounded"},
            {"metric": "8min", "direction": "最低", "rank": "最后1名", "tie_handling": "all_tied_minimum"}):
        raise ValueError("Partner process schedule, sender, or Base-write boundary differs")
    if cfg["upstream"] != _qingcheng_batch()["upstream"]:
        raise ValueError("Partner qing2lark task pin differs from the active Qingcheng batch")
    if [entry["id"] for entry in cfg["channels"]] != list(CHANNEL_IDS):
        raise ValueError("The three partner channels or their delivery order differ")
    if cfg["source"]["matches"] != {
            "partner_books": {"一级渠道": "图书", "渠道": "武汉图书"},
            "partner_local": {"一级渠道": "本地化", "渠道": "河南本地化"},
            "supervisor_local": {"一级渠道": "本地化", "渠道": "河南本地化"}}:
        raise ValueError("Partner source routing differs")
    bars = cfg["visual"]["metric_bars"]
    if (set(bars) != {"好友率", "等待时长", "8min", "24h首call"}
            or bars["好友率"]["color"] != "#8da7ca" or bars["等待时长"]["color"] != "#fc999f"
            or bars["8min"]["color"] != "#f8ca70" or bars["24h首call"]["color"] != "#77c09f"
            or any(spec["min"] != 0 or spec["max"] <= 0 for spec in bars.values())):
        raise ValueError("Partner process color bars differ")
    if set(cfg["visual"]["integer_fields"]) != {"带班人数", "有效线索", "退前线索", "退后线索", "总通时"}:
        raise ValueError("Partner integer display fields differ")
    expected = {
        "partner_books": ("图书", "顾问", "oc_854e5427ec0f6ef2bf654fee0a759f83", 3, ["武汉图书"]),
        "partner_local": ("本地化", "顾问", "oc_7e4ac041d00e583b49749b9a0d01a64c", 3, ["河南本地化"]),
        "supervisor_local": ("本地化", "主管", "oc_be403f4efca7f1adcb0d18a066308627", 5, ["河南本地化"]),
    }
    layout = {"partner_books": (False, "8min_minimum"), "partner_local": (False, "8min_minimum"),
              "supervisor_local": (True, "8min_minimum_grade_text")}
    for entry in cfg["channels"]:
        if tuple(entry[field] for field in ("name", "level", "target_chat_id",
                                            "minimum_effective_leads", "audit_secondary_channels")) != expected[entry["id"]]:
            raise ValueError(f"Partner channel routing differs: {entry['id']}")
        if (entry["split_grade"], entry["process_reminder"]) != layout[entry["id"]] \
                or entry["unresolved_mention_action"] != "invite_then_text":
            raise ValueError(f"Partner channel layout or mention gate differs: {entry['id']}")
        _request(entry)
    return cfg


def _request(entry: dict) -> dict:
    request = json.loads((CONFIG_PATH.parent / entry["request_file"]).read_text(encoding="utf-8"))
    if entry["process_reminder"] != "8min_minimum":
        # supervisor_local: single supervisor carries the channel, so 2026-09-30 the
        # user cancelled the person reminder and @; only a grade-level text hint remains.
        expected_reminder = (entry["level"], "不提醒", "不适用", "不适用", "不提醒")
    else:
        expected_reminder = (entry["level"], entry["level"], "8min", "最低", "最后1名")
    if (request["source"]["request_id"], request["business"]["channel_name"],
            request["business"]["target_chat_id"], request["reminder"]["report_level"],
            request["reminder"]["target"], request["reminder"]["process_metric"],
            request["reminder"]["process_direction"], request["reminder"]["process_rank"],
            request["report"]["minimum"]) != (
            f"qingcheng/{entry['id']}", entry["name"], entry["target_chat_id"],
            *expected_reminder,
            {"metric": "有效线索", "operator": ">=", "value": entry["minimum_effective_leads"]}):
        raise ValueError(f"Partner Base application differs: {entry['id']}")
    return request


def _slot(now: datetime, cfg: dict) -> datetime:
    cal = cfg["business_calendar"]
    if (now.tzinfo is None or now.utcoffset() != timedelta(hours=8)
            or now.weekday() not in cal["process_weekdays"] or now.hour not in cal["hours"]
            or not cal["minute"] <= now.minute <= cal["deadline_minute"]
            or (now.minute - cal["minute"]) % cal["retry_interval_minutes"]):
        raise ValueError("Outside the partner process delivery window")
    return now.replace(minute=cal["minute"], second=0, microsecond=0)


@contextmanager
def _single_instance():
    if os.name != "nt":
        raise RuntimeError("The scheduled Qingcheng sender requires Windows")
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
            raise RuntimeError("Another partner process batch is running") from exc
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _data(args: list[str], *, timeout: int = 90) -> dict:
    response = json.loads(run_lark(args, cwd=WORKSPACE, timeout=timeout))
    if response.get("ok") is not True or not isinstance(response.get("data"), dict):
        raise ValueError("Feishu operation returned no successful data")
    return response["data"]


def _expected(entry: dict, audit: dict) -> int:
    counts = audit["raw_channel_counts"]
    if not isinstance(counts, dict):
        raise ValueError("Qingcheng audit lacks channel counts")
    return sum(counts.get(name, 0) for name in entry["audit_secondary_channels"])


def _source(fetch_key: str, match: dict, period: str, folder: Path, audit: dict, slot: datetime,
            secondary_names: list[str]) -> tuple[list[dict], dict]:
    path = folder / "source.ndjson"
    manifest = fetch(fetch_key, period, path)
    rows, manifest = _read_snapshot(path, {"source": {"match": match}})
    expected = sum(audit["raw_channel_counts"].get(name, 0) for name in secondary_names)
    if (manifest["records_count"] != expected or manifest["period"] != period
            or [str(value) for value in manifest["snapshot"]] != [str(value) for value in audit["snapshot"]]):
        raise ValueError(f"Partner {fetch_key} source count, period, or snapshot differs from upstream audit")
    allowed = set(secondary_names)
    if any(row["渠道"] not in allowed for row in rows):
        raise ValueError(f"Partner {fetch_key} source contains an unreviewed secondary channel")
    for name in allowed:
        if sum(row["渠道"] == name for row in rows) != audit["raw_channel_counts"].get(name, 0):
            raise ValueError(f"Partner {name} raw source count differs from upstream audit")
    source_time = datetime.strptime(f"{manifest['snapshot'][0]} {int(manifest['snapshot'][1]):02d}",
                                    "%Y%m%d %H").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    age = (slot - source_time).total_seconds() / 60
    if age < 0 or age > 240:
        raise ValueError(f"Partner {fetch_key} source snapshot is stale")
    return rows, manifest


def _build(entry: dict, rows: list[dict], manifest: dict, cfg: dict, folder: Path) -> dict | None:
    request = _request(entry)
    split_grade = entry["split_grade"]
    grouped = _sort_process_rows(
        _aggregate(rows, entry["level"], request, split_grade=split_grade,
                   lead_field=cfg["source"]["lead_field"]),
        split_grade=split_grade)
    if not grouped:
        return None
    folder.mkdir(parents=True, exist_ok=True)
    image = folder / "process.png"
    bars = cfg["visual"]["metric_bars"]
    columns = [part.strip() for part in request["report"]["process_display_order"].split("、")]
    _table_image(grouped, columns, image, entry["level"], manifest["period"], entry["name"],
                 split_grade=split_grade,
                 bar_specs={field: (spec["min"], spec["max"], spec["color"]) for field, spec in bars.items()},
                 integer_fields=frozenset(cfg["visual"]["integer_fields"]))
    lines = [f"## 🔥 **【{manifest['period']}】{entry['name']}渠道{entry['level']}过程数据播报**", "",
             "![过程数据](process.png)"]
    reminder_grades: list[str] = []
    if entry["process_reminder"] == "8min_minimum_grade_text":
        # Grade-level text hint, no @: lowest unrounded 8min among grade blocks;
        # every tied grade is listed (including an all-zero tie).
        people = []
        by_grade: dict[str, list[float]] = {}
        for row in grouped:
            by_grade.setdefault(row["年级"], []).append(row["metrics"]["8min"])
        grade_min = {grade: min(values) for grade, values in by_grade.items()}
        least = min(grade_min.values())
        reminder_grades = [grade for grade in ("高一", "高二", "高三", "初三")
                           if grade_min.get(grade) == least]
        lines += ["", "- 8min较低年级：" + "、".join(reminder_grades)]
    elif entry["process_reminder"] == "none":
        people = []
    else:
        people = _reminder_people(entry["level"], grouped)
        lines += ["", f"- 8min较低的{entry['level']}：" + "、".join(person["name"] for person in people)]
    message = "\n".join(lines)
    (folder / "message.md").write_text(message + "\n", encoding="utf-8")
    review = {"id": entry["id"], "channel": entry["name"], "level": entry["level"],
              "period": manifest["period"], "source_rev": manifest["rev"],
              "snapshot": manifest["snapshot"], "raw_rows": len(rows),
              "eligible_rows": len(grouped), "reminder_people": people,
              "reminder_grades": reminder_grades,
              "image": image.name, "message": message,
              "unresolved_mention_action": entry["unresolved_mention_action"]}
    _write_json(folder / "review.json", review)
    return review


def _existing(path: Path) -> dict | None:
    """The settled verdict for one receipt, or None while the report may be re-driven.

    A receipt whose send was never confirmed, or whose readback failed, must come
    back as ``None`` so the round re-drives it. Only a verified send is settled.
    """
    if not path.exists():
        return None
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if resend.decide(receipt.get("status"), receipt.get("message_id")) == resend.DONE:
        return {"status": "sent_verified", "message_id": receipt["message_id"], "receipt": str(path)}
    return None


def _reverify(entry: dict, cfg: dict, prior: dict, receipt_path: Path) -> dict:
    """Read back a partner message that is already in the group; never re-sends."""
    message_id, image_key = prior.get("message_id"), prior.get("image_key")
    if not message_id or not image_key:
        raise ValueError("Partner receipt lacks the message id or image key needed to re-verify")
    try:
        readback = _verify_message(entry["target_chat_id"], message_id, image_key, prior["period"],
                                   set(prior.get("mention_ids") or ()), cfg["sender"]["open_id"])
    except Exception as exc:
        if not readback_available(entry, entry["target_chat_id"]):
            # Unreadable group: the failure carries no information about delivery.
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


def _person_key(person: dict) -> str:
    return person.get("account") or person["name"]


def _render(review: dict, resolved: dict[str, str], display: dict[str, str], image_key: str) -> str:
    message = review["message"]
    people = review["reminder_people"]
    if not image_key.startswith("img_"):
        raise ValueError("Partner reviewed image reference differs")
    if not people:
        # No-@ channels: supervisor_local carries a static grade hint line at most.
        if review.get("reminder_grades"):
            hint = "- 8min较低年级：" + "、".join(review["reminder_grades"])
            if message.count(hint) != 1:
                raise ValueError("Partner reviewed grade hint line differs")
        return message.replace("](process.png)", f"]({image_key})")
    prefix = f"- 8min较低的{review['level']}："
    original = prefix + "、".join(person["name"] for person in people)
    if message.count(original) != 1:
        raise ValueError("Partner reviewed reminder line differs")
    parts = []
    for person in people:
        key = _person_key(person)
        if key in resolved:
            parts.append(f'<at user_id="{resolved[key]}">{html.escape(display[key])}</at>')
        else:
            # Sanctioned plain-name fallback: invited already, still absent or unresolvable.
            parts.append(html.escape(person["name"]))
    return message.replace(original, prefix + "、".join(parts)).replace("](process.png)", f"]({image_key})")


def _key(entry: dict, period: str, slot: datetime) -> str:
    seed = "|".join(("qingcheng", "partner", entry["id"], entry["target_chat_id"], period, slot.isoformat()))
    return f"qcptn_{entry['id'][:12]}_{slot:%Y%m%d%H%M}_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _deliver(entry: dict, review: dict, manifest: dict, cfg: dict, folder: Path, slot: datetime) -> dict:
    receipt_path = folder / "send_receipt.json"
    settled = _existing(receipt_path)
    if settled:
        return settled
    prior = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else None
    # A recorded message id means the message is in the group: re-read, never re-send.
    if prior and resend.decide(prior.get("status"), prior.get("message_id")) == resend.REVERIFY:
        return _reverify(entry, cfg, prior, receipt_path)
    # A transport failure here means nothing was learned, so it is retried in-round; a
    # returned revision that differs still fails closed on the first attempt.
    current = retry_transport(lambda: probe_revision(
        FETCH_KEY[entry["id"]], review["period"], folder / "source_revision_probe.ndjson"))
    if current != manifest["rev"]:
        raise ValueError("Partner source Base revision changed before delivery")
    chat = verify_chat(entry["target_chat_id"], entry["target_chat_name"], "bot", 90)
    if chat["name_changed"]:
        raise ValueError(f"Partner group name changed from the reviewed target: {entry['id']}")
    if review["reminder_people"]:
        member_ids = _members(entry["target_chat_id"], cfg["sender"]["open_id"])
        shim_entry = {"unresolved_mention_action": entry["unresolved_mention_action"]}
        shim_review = {"reminders": [{"grade": None, "people": review["reminder_people"]}]}
        resolved, display, text_only = _resolve(shim_entry, shim_review, member_ids,
                                                chat_id=entry["target_chat_id"],
                                                sender_open_id=cfg["sender"]["open_id"])
        if len(resolved) + len(text_only) != len(review["reminder_people"]):
            raise ValueError(f"Partner reminder coverage differs from the reviewed person set: {entry['id']}")
    else:
        resolved, display = {}, {}
    image = folder / review["image"]
    image_key = upload_image(image, "bot", 90)
    markdown = _render(review, resolved, display, image_key)
    key = _key(entry, review["period"], slot)
    send_args = ["im", "+messages-send", "--chat-id", entry["target_chat_id"],
                 "--markdown", markdown, "--idempotency-key", key,
                 "--as", "bot", "--format", "json"]
    dry_run = json.loads(run_lark([*send_args, "--dry-run"], cwd=WORKSPACE, timeout=90))
    if dry_run.get("ok") is not True:
        raise ValueError("Partner message dry-run failed")
    receipt = {"status": "send_attempt_started", "channel_id": entry["id"],
               "chat_id": entry["target_chat_id"], "sender_open_id": cfg["sender"]["open_id"],
               "period": review["period"], "slot": slot.isoformat(), "source_rev": manifest["rev"],
               "idempotency_key": key, "mention_ids": sorted(resolved.values()),
               "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
               "message_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
               # Re-issue evidence: the key is unchanged, so the platform dedupes if an
               # earlier attempt did land.
               "resend_attempts": (prior or {}).get("resend_attempts", 0) + (1 if prior else 0),
               "prior_status": (prior or {}).get("status", "")}
    _write_json(receipt_path, receipt)
    try:
        sent = _data(send_args)
        message_id = sent.get("message_id")
        if not isinstance(message_id, str) or not message_id.startswith("om_"):
            raise ValueError("Partner send returned no message ID")
    except Exception as exc:
        receipt.update({"status": "send_result_uncertain", "error": str(exc)})
        _write_json(receipt_path, receipt)
        raise
    receipt.update({"status": "sent_unverified", "message_id": message_id, "image_key": image_key})
    _write_json(receipt_path, receipt)
    try:
        readback = _verify_message(entry["target_chat_id"], message_id, image_key,
                                   review["period"], set(resolved.values()), cfg["sender"]["open_id"])
        receipt.update({"status": "sent_verified", "readback": readback})
    except Exception as exc:
        if readback_available(entry, entry["target_chat_id"]):
            receipt.update({"status": "sent_readback_unverified", "readback_error": str(exc)})
        else:
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
            raise ValueError("Partner batch folder belongs to another business slot")
    results = {entry["id"]: _existing(output / entry["id"] / "send_receipt.json")
               for entry in cfg["channels"]}
    pending = [entry for entry in cfg["channels"] if results[entry["id"]] is None]
    batch = {"period": period, "slot": slot.isoformat(), "channels": results}
    if not pending:
        _write_json(batch_path, batch)
        return batch
    try:
        audit = _upstream_audit(period, slot)
        if not isinstance(audit.get("raw_channel_counts"), dict):
            raise ValueError("Qingcheng upstream audit lacks partner channel counts")
    except Exception as exc:
        for entry in pending:
            results[entry["id"]] = {"status": "blocked_upstream", "error": str(exc)}
        _write_json(batch_path, batch)
        return batch
    batch["upstream_audit"] = audit

    # Fetch each distinct source once; a source failure only blocks its own channels.
    source_data: dict[str, tuple[list[dict], dict]] = {}
    source_errors: dict[str, str] = {}
    for fetch_key in dict.fromkeys(FETCH_KEY[entry["id"]] for entry in pending):
        names = sorted({name for entry in pending if FETCH_KEY[entry["id"]] == fetch_key
                        for name in entry["audit_secondary_channels"]})
        if sum(audit["raw_channel_counts"].get(name, 0) for name in names) == 0:
            source_errors[fetch_key] = "zero_source_rows"
            continue
        match = next(cfg["source"]["matches"][entry["id"]] for entry in pending
                     if FETCH_KEY[entry["id"]] == fetch_key)
        try:
            source_data[fetch_key] = _source(fetch_key, match, period, output / fetch_key,
                                             audit, slot, names)
        except Exception as exc:
            source_errors[fetch_key] = str(exc)

    # All partner sources come from one raw table: revisions and snapshots must agree.
    pin_path = output / "source_version.json"
    pin = json.loads(pin_path.read_text(encoding="utf-8")) if pin_path.exists() else None
    observed = {(manifest["rev"], tuple(manifest["snapshot"])) for _, manifest in source_data.values()}
    if len(observed) > 1:
        for fetch_key in source_data:
            source_errors[fetch_key] = "Partner source slices came from different Base revisions or snapshots"
        source_data.clear()
    elif observed:
        revision, snapshot = next(iter(observed))
        if pin and (pin["rev"], tuple(pin["snapshot"])) != (revision, snapshot):
            for fetch_key in source_data:
                source_errors[fetch_key] = "Partner source version changed inside the same delivery slot"
            source_data.clear()
        elif not pin:
            _write_json(pin_path, {"period": period, "slot": slot.isoformat(),
                                   "rev": revision, "snapshot": list(snapshot)})

    # Per-channel build and delivery: one channel's failure never affects the others.
    for entry in pending:
        channel_id = entry["id"]
        folder = output / channel_id
        fetch_key = FETCH_KEY[channel_id]
        try:
            if fetch_key in source_errors:
                if source_errors[fetch_key] == "zero_source_rows":
                    results[channel_id] = {"status": "skipped_no_source_rows"}
                else:
                    raise ValueError(source_errors[fetch_key])
            elif _expected(entry, audit) == 0:
                results[channel_id] = {"status": "skipped_no_source_rows"}
            else:
                rows = [row for row in source_data[fetch_key][0]
                        if row["渠道"] in entry["audit_secondary_channels"]]
                manifest = source_data[fetch_key][1]
                review = _build(entry, rows, manifest, cfg, folder)
                if review is None:
                    results[channel_id] = {"status": "skipped_no_eligible_rows"}
                else:
                    results[channel_id] = _deliver(entry, review, manifest, cfg, folder, slot)
        except Exception as exc:
            results[channel_id] = _existing(folder / "send_receipt.json") or {
                "status": "blocked", "error": str(exc)}
        _write_json(batch_path, batch)
    return batch


def main() -> None:
    ensure_console_streams()  # pythonw.exe has no console streams
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--check-config", action="store_true")
    choice.add_argument("--confirm-send", action="store_true")
    args = parser.parse_args()
    if args.check_config:
        cfg = _config()
        print(json.dumps({"status": "valid", "task": cfg["windows_task_name"],
                          "channels": [entry["id"] for entry in cfg["channels"]]}, ensure_ascii=True))
        return
    with run_scope(CONFIG_PATH, "partner_process_batch") as scope:
        scope.event("run_started", confirmed=True)
        with _single_instance():
            batch = run()
        print(json.dumps(batch, ensure_ascii=False, indent=2))
        scope.adopt(batch)
        failed = any(item["status"] not in {"sent_verified", resend.UNVERIFIABLE, "skipped_no_source_rows",
                                            "skipped_no_eligible_rows"}
                     for item in batch["channels"].values())
        scope.exit_code = 1 if failed else 0
        if failed:
            scope.event("run_needs_attention")
            raise SystemExit(1)
        scope.event("run_finished")


if __name__ == "__main__":
    main()
