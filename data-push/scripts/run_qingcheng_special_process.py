"""Send four independent titled-image reports to Qingcheng's special-channel group."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from fetch_qingcheng_process_source import fetch, probe_revision
from lark_delivery.common import resend
from lark_delivery.common.im import upload_image, verify_chat
from lark_delivery.common.readback import available as readback_available
from lark_delivery.common.retry import retry_transport
from lark_delivery.common.runtime import ensure_console_streams, run_lark
from preview_qingcheng_public_pool_process import _number, _table_image
from preview_qingcheng_special_process import _aggregate, DISPLAY_COLUMNS, GRADES, SOURCE_NUMBERS
from run_qingcheng_process import _batch as _qingcheng_batch, _period, _upstream_audit, _write_json, run_scope
from send_qingcheng_process import _verify_message


SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
CONFIG = SKILL / "config/departments/qingcheng/special_process_batch.json"
STATE = WORKSPACE / "runtime/qingcheng-special-process-batch"
CHANNEL_IDS = ("special_private", "special_books", "special_douyin_dm", "special_public_pool")
AUDIT_NAMES = (("私域表单", "私域品效"), ("武汉图书",), ("抖音私信",), ("顾问未加好友",))


def _config() -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cal = cfg["business_calendar"]
    if (cfg["schema_version"], cfg["domain"], cfg["execution_surface"], cfg["report_type"],
            cfg["report_level"], cfg["status"], cfg["schedule_enabled"], cfg["windows_task_name"],
            cfg["configuration_base_writeback"], cfg["image_only"], cfg["text_header"],
            cfg["show_total"], cfg["split_grade"],
            cfg["minimum_effective_leads"], cfg["source"]["dimension_field"], cfg["source"]["lead_field"],
            cfg["source"]["base_token"], cfg["source"]["table_id"],
            cfg["target_chat_id"], cfg["sender"]["identity"], cfg["sender"]["open_id"],
            cal["period_rule"], cal["process_weekdays"], cal["hours"], cal["minute"],
            cal["deadline_minute"], cal["retry_interval_minutes"], cal["timezone"], cfg["sort"]) != (
            1, "qingcheng", "local", "process", "学部", "active", True,
            "Codex-Lark-Qingcheng-Special-Process-GroupPush", "setup_only", False, True, True, True,
            5, "经理", "退后线索", "QOVib6QCXaUvJ2s2PsbcnMmsnGg", "tblXU4tla3bY36DE",
            "oc_a95c83e488e0dfcc777d5ffad849d8a4", "bot",
            "ou_f3907e865135732c15a1dfce27828411",
             "自然周周五期次", [1, 2, 3], [14], 0, 50, 2, "Asia/Shanghai",
            {"metric": "8min", "direction": "desc", "value": "unrounded"}):
        raise ValueError("Special-channel process task configuration differs")
    if cfg["upstream"] != _qingcheng_batch()["upstream"]:
        raise ValueError("Special-channel qing2lark upstream pin differs")
    if tuple(entry["id"] for entry in cfg["channels"]) != CHANNEL_IDS:
        raise ValueError("Special-channel delivery order differs")
    if tuple(entry["name"] for entry in cfg["channels"]) != ("私域", "图书", "抖音私信", "公海"):
        raise ValueError("Special-channel business names differ")
    if cfg["display_columns"] != DISPLAY_COLUMNS:
        raise ValueError("Special-channel image columns differ")
    if tuple(tuple(entry["audit_secondary_channels"]) for entry in cfg["channels"]) != AUDIT_NAMES:
        raise ValueError("Special-channel audit scope differs")
    if tuple(entry["source_key"] for entry in cfg["channels"]) != (
            "private", "special_books", "douyin_dm", "special_public_pool"):
        raise ValueError("Special-channel source routing differs")
    bars = cfg["visual"]["metric_bars"]
    if (set(bars) != {"好友率", "等待时长", "8min", "24h首call"}
            or bars["等待时长"]["color"] != "#fc999f"
            or any(spec["min"] != 0 or spec["max"] <= 0 for spec in bars.values())
            or set(cfg["visual"]["integer_fields"]) != {"带班人数", "有效线索", "总通时"}):
        raise ValueError("Special-channel process image format differs")
    return cfg


def _slot(now: datetime, cfg: dict) -> datetime:
    cal = cfg["business_calendar"]
    if (now.tzinfo is None or now.utcoffset() != timedelta(hours=8)
            or now.weekday() not in cal["process_weekdays"] or now.hour not in cal["hours"]
            or not cal["minute"] <= now.minute <= cal["deadline_minute"]
            or (now.minute - cal["minute"]) % cal["retry_interval_minutes"]):
        raise ValueError("Outside the special-channel process delivery window")
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
            raise RuntimeError("Another special-channel process batch is running") from exc
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


def _verify_group(cfg: dict) -> None:
    chat = verify_chat(cfg["target_chat_id"], cfg["target_chat_display_name"], "bot", 90)
    if chat["name_changed"]:
        raise ValueError("Special-channel group name changed from the reviewed target")
    members = _data(["im", "+chat-members-list", "--chat-id", cfg["target_chat_id"],
                     "--member-types", "bot", "--member-id-type", "open_id", "--page-all",
                     "--page-limit", "0", "--as", "bot", "--format", "json"])
    bots = members.get("bots", [])
    if (members.get("has_more") is not False or members.get("truncations")
            or members.get("bot_total") != len(bots)
            or cfg["sender"]["open_id"] not in {bot.get("member_id") for bot in bots}):
        raise ValueError("Sender bot was not verified in the complete target-group list")


def _expected(entry: dict, audit: dict) -> int:
    counts = audit["raw_channel_counts"]
    if not isinstance(counts, dict):
        raise ValueError("Qingcheng audit lacks channel counts")
    return sum(counts.get(name, 0) for name in entry["audit_secondary_channels"])


def _source(entry: dict, period: str, folder: Path, audit: dict, slot: datetime) -> tuple[list[dict], dict]:
    path = folder / "source.ndjson"
    manifest = fetch(entry["source_key"], period, path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    expected = _expected(entry, audit)
    if (manifest["records_count"] != len(rows) or len(rows) != expected
            or manifest["period"] != period or manifest["has_more"] is not False
            or [str(value) for value in manifest["snapshot"]] != [str(value) for value in audit["snapshot"]]):
        raise ValueError(f"Special-channel {entry['id']} source differs from current upstream audit")
    if any(row["一级渠道"] != entry["name"] or row["渠道"] not in entry["audit_secondary_channels"]
           or row["年级"] not in GRADES + ["初二"] for row in rows):
        raise ValueError(f"Special-channel {entry['id']} scope contains an unreviewed value")
    for name in entry["audit_secondary_channels"]:
        if sum(row["渠道"] == name for row in rows) != audit["raw_channel_counts"].get(name, 0):
            raise ValueError(f"Special-channel {name} count differs from upstream audit")
    for row in rows:
        if row["年级"] in GRADES:
            for field in SOURCE_NUMBERS:
                _number(row, field)
    source_time = datetime.strptime(f"{manifest['snapshot'][0]} {int(manifest['snapshot'][1]):02d}",
                                    "%Y%m%d %H").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    age = (slot - source_time).total_seconds() / 60
    if age < 0 or age > 240:
        raise ValueError(f"Special-channel {entry['id']} source snapshot is stale")
    return rows, manifest


def _build(entry: dict, rows: list[dict], manifest: dict, cfg: dict, folder: Path) -> dict | None:
    grouped = _aggregate(rows, manifest["period"], cfg["minimum_effective_leads"])
    if not grouped:
        return None
    folder.mkdir(parents=True, exist_ok=True)
    image = folder / "process.png"
    bars = cfg["visual"]["metric_bars"]
    _table_image(grouped, cfg["display_columns"], image, "学部", manifest["period"], entry["name"],
                 split_grade=True,
                 bar_specs={field: (spec["min"], spec["max"], spec["color"]) for field, spec in bars.items()},
                 integer_fields=frozenset(cfg["visual"]["integer_fields"]))
    message = "\n".join([f"## 🔥 **【{manifest['period']}】{entry['name']}渠道学部过程数据播报**", "",
                         "![过程数据](process.png)"])
    (folder / "message.md").write_text(message + "\n", encoding="utf-8")
    review = {"id": entry["id"], "channel": entry["name"], "period": manifest["period"],
              "source_rev": manifest["rev"], "snapshot": manifest["snapshot"],
              "source_rows": len(rows), "eligible_rows": len(grouped), "image": image.name,
              "image_only": False, "text_header": True, "message": message,
              "threshold": cfg["minimum_effective_leads"]}
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


def _reverify(cfg: dict, prior: dict, receipt_path: Path) -> dict:
    """Read back a special-channel message that is already in the group; never re-sends."""
    message_id, image_key = prior.get("message_id"), prior.get("image_key")
    if not message_id or not image_key:
        raise ValueError("Special-channel receipt lacks the message id or image key needed to re-verify")
    try:
        readback = _verify_message(cfg["target_chat_id"], message_id, image_key,
                                   prior["period"], set(), cfg["sender"]["open_id"])
    except Exception as exc:
        if not readback_available(cfg, cfg["target_chat_id"]):
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


def _key(entry: dict, cfg: dict, period: str, slot: datetime) -> str:
    seed = "|".join(("qingcheng", "local", entry["id"], cfg["target_chat_id"],
                     period, "process", slot.isoformat()))
    return f"qcsp_{entry['id']}_{slot:%Y%m%d%H%M}_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _deliver(entry: dict, review: dict, manifest: dict, cfg: dict, folder: Path, slot: datetime) -> dict:
    receipt_path = folder / "send_receipt.json"
    settled = _existing(receipt_path)
    if settled:
        return settled
    prior = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else None
    # A recorded message id means the message is in the group: re-read, never re-send.
    if prior and resend.decide(prior.get("status"), prior.get("message_id")) == resend.REVERIFY:
        return _reverify(cfg, prior, receipt_path)
    # A transport failure here means nothing was learned, so it is retried in-round; a
    # returned revision that differs still fails closed on the first attempt.
    current = retry_transport(lambda: probe_revision(
        entry["source_key"], review["period"], folder / "source_revision_probe.ndjson"))
    if current != manifest["rev"]:
        raise ValueError("Special-channel source Base revision changed before delivery")
    _verify_group(cfg)
    image = folder / review["image"]
    image_sha = hashlib.sha256(image.read_bytes()).hexdigest()
    image_key = upload_image(image, "bot", 90)
    if not re.fullmatch(r"img_[A-Za-z0-9_-]+", image_key):
        raise ValueError("Image upload returned an invalid image key")
    key = _key(entry, cfg, review["period"], slot)
    markdown = review["message"].replace("](process.png)", f"]({image_key})")
    if markdown.count(image_key) != 1:
        raise ValueError("Special-channel message image reference differs")
    send_args = ["im", "+messages-send", "--chat-id", cfg["target_chat_id"],
                 "--markdown", markdown, "--idempotency-key", key, "--as", "bot", "--format", "json"]
    dry_run = json.loads(run_lark([*send_args, "--dry-run"], cwd=WORKSPACE, timeout=90))
    if dry_run.get("ok") is not True:
        raise ValueError("Special-channel message dry-run failed")
    receipt = {"status": "send_attempt_started", "report_id": entry["id"],
               "chat_id": cfg["target_chat_id"], "sender_open_id": cfg["sender"]["open_id"],
               "period": review["period"], "slot": slot.isoformat(), "source_rev": manifest["rev"],
               "image_sha256": image_sha, "image_key": image_key, "idempotency_key": key,
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
            raise ValueError("Special-channel send returned no message ID")
    except Exception as exc:
        receipt.update({"status": "send_result_uncertain", "error": str(exc)})
        _write_json(receipt_path, receipt)
        raise
    receipt.update({"status": "sent_unverified", "message_id": message_id})
    _write_json(receipt_path, receipt)
    try:
        readback = _verify_message(cfg["target_chat_id"], message_id, image_key,
                                   review["period"], set(), cfg["sender"]["open_id"])
        receipt.update({"status": "sent_verified", "readback": readback})
    except Exception as exc:
        if readback_available(cfg, cfg["target_chat_id"]):
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
        old = json.loads(batch_path.read_text(encoding="utf-8"))
        if (old["period"], old["slot"]) != (period, slot.isoformat()):
            raise ValueError("Special-channel batch folder belongs to another business slot")
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
            raise ValueError("Current qing2lark audit lacks channel counts")
    except Exception as exc:
        for entry in pending:
            results[entry["id"]] = {"status": "blocked_upstream", "error": str(exc)}
        _write_json(batch_path, batch)
        return batch
    batch["upstream_audit"] = audit
    prepared: dict[str, tuple[dict, dict]] = {}
    versions = set()
    for entry in pending:
        report_id = entry["id"]
        folder = output / report_id
        try:
            if _expected(entry, audit) == 0:
                results[report_id] = {"status": "skipped_no_source_rows"}
                continue
            rows, manifest = _source(entry, period, folder, audit, slot)
            versions.add((manifest["rev"], tuple(manifest["snapshot"])))
            review = _build(entry, rows, manifest, cfg, folder)
            if review is None:
                results[report_id] = {"status": "skipped_no_eligible_rows"}
            else:
                prepared[report_id] = (review, manifest)
                results[report_id] = {"status": "prepared"}
        except Exception as exc:
            results[report_id] = {"status": "blocked_prepare", "error": str(exc)}
        _write_json(batch_path, batch)
    pin_path = output / "source_version.json"
    pin = json.loads(pin_path.read_text(encoding="utf-8")) if pin_path.exists() else None
    if len(versions) > 1 or (pin and versions and next(iter(versions)) != (pin["rev"], tuple(pin["snapshot"]))):
        for report_id in prepared:
            results[report_id] = {"status": "blocked_source_version"}
        _write_json(batch_path, batch)
        return batch
    if versions and not pin:
        revision, snapshot = next(iter(versions))
        _write_json(pin_path, {"period": period, "slot": slot.isoformat(),
                               "rev": revision, "snapshot": list(snapshot)})
    for entry in pending:
        report_id = entry["id"]
        if report_id not in prepared:
            continue
        review, manifest = prepared[report_id]
        folder = output / report_id
        try:
            results[report_id] = _deliver(entry, review, manifest, cfg, folder, slot)
        except Exception as exc:
            results[report_id] = _existing(folder / "send_receipt.json") or {
                "status": "blocked_delivery", "error": str(exc)}
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
    with run_scope(CONFIG, "special_process_batch") as scope:
        scope.event("run_started", confirmed=True)
        with _single_instance():
            batch = run()
        print(json.dumps(batch, ensure_ascii=True, indent=2))
        scope.adopt(batch)
        failed = any(item["status"] not in {"sent_verified", resend.UNVERIFIABLE,
                                            "skipped_no_source_rows", "skipped_no_eligible_rows"}
                     for item in batch["channels"].values())
        scope.exit_code = 1 if failed else 0
        if failed:
            scope.event("run_needs_attention")
            raise SystemExit(1)
        scope.event("run_finished")


if __name__ == "__main__":
    main()
