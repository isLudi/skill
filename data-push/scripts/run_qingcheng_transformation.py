"""Prepare and deliver Qingcheng transformation group reports (five channels).

Scheduled runner for the conversion (transformation) push, mirroring
run_qingcheng_process.py: window-checked slots, per-period source exports,
per-group send isolation, idempotency keys and readback verification. Every
window pushes once (2026-10-02 always-send policy); groups with no conversion
output carry the fallback flag line instead, and the dept level never carries
reminder lines. The dept (学部) level only joins the 14:02 window on
Fri/Sat/Sun plus the Monday 04:00 closing slot (2026-10-03 correction: the
Base request asks for a single daily 14:00 push plus a final Monday write).

Config: config/departments/qingcheng/transformation_batch.json (schedule base,
operator record IDs) + transformation_preview.json (delivery, channel matches,
profiles). The send step delegates to send_qingcheng_transformation.py.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fetch_qingcheng_process_source import fetch, probe_revision
from export_conversion_refresh import FILTERS, BASE_TOKEN, TABLE_ID, export_conversion
from preview_qingcheng_transformation import build
from lark_delivery.common import push_log, resend
from lark_delivery.common.retry import retry_transport
from lark_delivery.common.runtime import CREATE_NO_WINDOW, ensure_console_streams, run_lark


SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
CONFIG_DIR = SKILL / "config/departments/qingcheng"
BATCH_CONFIG = CONFIG_DIR / "transformation_batch.json"
STATE = WORKSPACE / "runtime/qingcheng-transformation-batch"
# 2026-10-02 学部级并入调度：四渠道（公海/私域/抖音私信/图书）dept 维度发
# ⏰渠道专项讨论（同群）；本地化无 dept 申请，_channel_levels 按 profiles 自动跳过。
# 2026-10-03 窗口修正：dept 仅随周五/六/日 14:02 档 + 次周周一 04:00 收官档参与
# （_dept_active），其余窗口记 skipped_not_in_window，不再整窗跟随。
LEVELS = ("supervisor", "consultant", "dept")
CHANNEL_IDS = ["public_pool", "private", "douyin_dm", "partner_books", "partner_local"]
SEND_SCRIPT = SKILL / "scripts/send_qingcheng_transformation.py"

# 2026-10-01 审定状态：五渠道全部参与周常调度（用户确认预览后授权；图书/本地化
# 无转化产出时仍按 no_data_policy 跳过）。
EXPECTED_SCHEDULED = {"public_pool": True, "private": True, "douyin_dm": True,
                      "partner_books": True, "partner_local": True}

# “无转化产出”判定字段：任一非 0 即视为有转化产出。2026-10-02 起仅用于
# 诊断记录（conversion_has_output），不再触发跳过——所有窗口恒推送。
ZERO_FIELDS = ("收款", "退费", "当期收款", "成交人头", "报科数")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


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
            raise RuntimeError("Another Qingcheng transformation batch is already running") from exc
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _batch() -> dict:
    batch = json.loads(BATCH_CONFIG.read_text(encoding="utf-8"))
    calendar = batch["business_calendar"]
    if (batch["schema_version"], batch["domain"], batch["report_type"]) != (1, "qingcheng", "transformation"):
        raise ValueError("Unexpected Qingcheng transformation batch scope")
    if [item["id"] for item in batch["channels"]] != CHANNEL_IDS:
        raise ValueError("All Qingcheng transformation channels must be explicit")
    for item in batch["channels"]:
        if item.get("scheduled") is not EXPECTED_SCHEDULED[item["id"]]:
            raise ValueError(f"Transformation schedule flag differs for {item['id']}")
    # 2026-10-05：周一改为 04:00，等待天宫2 zhuanhua 03:40 批次的 00:00 分区。
    if (calendar["result_weekdays"], calendar["minute"], calendar["deadline_minute"],
            calendar["timezone"]) != ([4, 5, 6, 0], 2, 55, "Asia/Shanghai"):
        raise ValueError("Transformation batch calendar differs from the reviewed slots")
    if calendar.get("minute_by_weekday") != {"0": 0, "4": 2, "5": 2, "6": 2}:
        raise ValueError("Transformation per-weekday minutes differ from the reviewed slots")
    hours = calendar["hours_by_weekday"]
    if (hours.get("4"), hours.get("5"), hours.get("6"), hours.get("0")) != (
            [14, 18, 22], [14, 18, 22], [14, 18, 22], [4]):
        raise ValueError("Transformation per-weekday hours differ from the reviewed slots")
    if (batch["retry_interval_minutes"], batch["windows_task_name"], batch["freshness_max_age_minutes"],
            batch["no_data_policy"]) != (2, "Codex-Lark-Qingcheng-Transformation-GroupPush", 1560,
                                         "always_send_with_fallback_flag"):
        raise ValueError("Transformation task pin or policy differs")
    upstream = batch["upstream"]
    if (upstream["project_id"], upstream["folder"], upstream["task_id"], upstream["task_name"],
            upstream["nezha_task_id"], upstream["menu_id"], upstream["published_version"],
            upstream["version_id"], upstream["source_sha256"], upstream["audit_mode"]) != (
                308, "吕帅", 47775, "qing2lark_zhuanhua", 67397, 103713, "V6", 207547,
                "97aed7e48398d6a4321e0b11fab0cff44de67edb8f5f21622e7d1424a0521a39", "none"):
        raise ValueError("Transformation upstream pin differs")
    return batch


def _period(day: date) -> str:
    """期次=自然周周五期次：周五推当天期次，周六/周日/次周周一回溯到本周五。"""
    offsets = {4: 0, 5: -1, 6: -2, 0: -3}
    if day.weekday() not in offsets:
        raise ValueError("Transformation slots run Fri..Sun and the next Monday only")
    return (day + timedelta(days=offsets[day.weekday()])).strftime("%Y%m%d") + "期"


def _slot(now: datetime, batch: dict) -> datetime:
    calendar = batch["business_calendar"]
    if now.tzinfo is None or now.utcoffset() != timedelta(hours=8):
        raise ValueError("Task clock must be Asia/Shanghai")
    weekday = str(now.weekday())
    minute = calendar.get("minute_by_weekday", {}).get(weekday, calendar["minute"])
    hours = calendar["hours_by_weekday"].get(weekday, [])
    if (now.weekday() not in calendar["result_weekdays"] or now.hour not in hours
            or not minute <= now.minute <= calendar["deadline_minute"]
            or (now.minute - minute) % batch["retry_interval_minutes"]):
        raise ValueError("Outside the authorized Qingcheng transformation window")
    return now.replace(minute=minute, second=0, microsecond=0)


def _dept_active(slot: datetime | None) -> bool:
    """2026-10-03 学部级窗口修正：Base 申请为每日 14:00 单档推送。

    dept 仅随周五/六/日 14:02 档参与；次周周一 04:00 收官档随大盘写入本周最后
    一次数据（用户指令）。预览模式（slot=None）恒参与；其余窗口跳过并记
    skipped_not_in_window（10-02 曾误并入全部 :02 窗口）。
    """
    if slot is None or slot.hour == 14:
        return True
    return slot.weekday() == 0 and slot.hour == 4


def _key(channel: str, level: str, chat_id: str, period: str, slot: datetime) -> str:
    parts = ["qingcheng", "local", channel, chat_id, period, "transformation", slot.isoformat()]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"qtr_{channel[:2]}_{level[:3]}_{slot:%Y%m%d%H%M}_{digest}"


def _fresh(review: dict, period: str, slot: datetime, batch: dict) -> None:
    if review["period"] != period:
        raise ValueError("Raw Base period differs from the business Friday")
    newest = None
    for name in ("process_snapshot", "conversion_snapshot"):
        value = review.get(name)
        if value:
            parsed = datetime.strptime(value, "%Y%m%d %H:%M").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
            newest = parsed if newest is None else max(newest, parsed)
    if newest is None:
        raise ValueError("Review carries no source snapshot")
    age = (slot - newest).total_seconds() / 60
    if age < 0 or age > batch["freshness_max_age_minutes"]:
        raise ValueError("Raw Base source snapshot is outside the freshness window")


def _conversion_output(rows: list[dict]) -> bool:
    """2026-10-02 always-send policy: kept for diagnostics/receipts only.

    The batch no longer skips groups without conversion output; every window
    sends once and a no-data group carries the fallback flag line instead.
    """
    return any(any(float(row.get(field) or 0) != 0 for field in ZERO_FIELDS) for row in rows)


def _probe_conversion_rev(channel: str, probe_file: Path) -> int:
    spec = FILTERS[channel]
    filtered = json.dumps(spec, ensure_ascii=True)
    run_lark(["base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID,
              "--filter-json", filtered, "--offset", "0", "--limit", "1", "--format", "ndjson",
              "--output", str(probe_file), "--as", "user", "--overwrite"], cwd=WORKSPACE, timeout=240)
    manifest = json.loads(probe_file.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    rev = manifest.get("rev")
    if not isinstance(rev, int):
        raise ValueError("Conversion probe returned no revision")
    return rev


def _receipt_state(receipt: Path) -> tuple[str, str]:
    if not receipt.exists():
        return resend.RESEND, ""
    saved = json.loads(receipt.read_text(encoding="utf-8"))
    message_id = str((saved.get("response") or {}).get("message_id") or "")
    if saved.get("status"):
        saved_status = saved["status"]
    else:
        saved_status = "sent_verified" if (saved.get("readback") or {}).get("verified") is True else "sent_unverified"
    return resend.decide(saved_status, message_id), message_id


def _config_chat_id(channel: str, level: str) -> str:
    config = json.loads((CONFIG_DIR / "transformation_preview.json").read_text(encoding="utf-8"))
    entry = next(item for item in config["channels"] if item["id"] == channel)
    return entry["profiles"][level]["target_chat_id"]


def _channel_levels(channel: str) -> tuple[str, ...]:
    """Levels configured for one channel (图书 has no supervisor request)."""
    config = json.loads((CONFIG_DIR / "transformation_preview.json").read_text(encoding="utf-8"))
    entry = next(item for item in config["channels"] if item["id"] == channel)
    return tuple(slug for slug in LEVELS if slug in entry["profiles"])


def _send_group(channel: str, level: str, review_dir: Path, key: str) -> dict:
    receipt = review_dir / f"{level}_transformation_send_{key}.json"
    verdict, message_id = _receipt_state(receipt)
    if verdict == resend.DONE:
        return {"status": "sent_verified", "message_id": message_id, "receipt": str(receipt)}
    mode = "--reverify-only" if verdict == resend.REVERIFY else "--send"
    # 2026-10-02 always-send policy: the scheduled path is pre-authorized to send
    # fallback-only messages (no-data groups carry the flag line instead of being
    # skipped). Manual sends still require the explicit --allow-fallback flag.
    command = [sys.executable, str(SEND_SCRIPT), "--channel", channel, "--level", level,
               "--review-dir", str(review_dir), "--idempotency-key", key,
               "--allow-fallback", mode]
    result = subprocess.run(command, cwd=WORKSPACE, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=300, creationflags=CREATE_NO_WINDOW)
    if result.returncode:
        return {"status": "blocked_or_uncertain", "error": (result.stderr or result.stdout)[-1200:].strip(),
                "receipt": str(receipt) if receipt.exists() else None}
    response = json.loads(result.stdout)
    if response.get("readback", {}).get("verified") is not True:
        return {"status": "readback_failed", "receipt": str(receipt)}
    return {"status": "sent_verified", "message_id": response["readback"]["message_id"], "receipt": str(receipt)}


def _index(output: Path, batch_result: dict) -> None:
    cards = []
    for channel, item in batch_result["channels"].items():
        review = item.get("review") or {}
        for slug, level_result in (review.get("results", {}).get(channel, {}).get("levels") or {}).items():
            cards.append(
                f"<section><h2>{html.escape(channel)} · {html.escape(level_result['level'])}"
                f"<span style='font-size:14px;color:#5a6c85'> {html.escape(str(level_result['rows']))} 行</span></h2>"
                f"<img src='{channel}/{level_result['png']}' alt='转化图片'>"
                f"<pre>{html.escape(level_result['message'])}</pre></section>")
    page = ("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>青橙转化数据批次预览</title>"
            "<style>body{font:16px 'Microsoft YaHei',sans-serif;background:#eef3fb;color:#20314c;padding:24px}"
            "main{max-width:1800px;margin:auto}section{background:white;margin:22px 0;padding:20px;border-radius:12px}"
            "img{max-width:100%;border:1px solid #c3cfe2}pre{white-space:pre-wrap;background:#f2f6fd;padding:14px}</style>"
            f"<main><h1>青橙渠道（公海/私域/抖音私信/图书/本地化）· 转化数据批次</h1><p>{html.escape(batch_result['period'])}</p>"
            + "".join(cards) + "</main></html>")
    (output / "index.html").write_text(page, encoding="utf-8")


def _deliver_groups(batch: dict, batch_result: dict, output: Path, slot: datetime) -> None:
    period = batch_result["period"]
    result_path = output / "batch.json"
    for entry in batch["channels"]:
        channel = entry["id"]
        item = batch_result["channels"][channel]
        review_dir = output / channel
        for level in _channel_levels(channel):
            group = item["groups"][level]
            if group["status"] not in ("prepared", resend.REVERIFY, resend.RESEND):
                continue
            try:
                if group["status"] != resend.REVERIFY:
                    probe_file = review_dir / f"probe_{level}_process.ndjson"
                    current_process_rev = retry_transport(lambda: probe_revision(channel, period, probe_file))
                    current_conversion_rev = retry_transport(
                        lambda: _probe_conversion_rev(channel, review_dir / f"probe_{level}_conversion.ndjson"))
                    if (current_process_rev, current_conversion_rev) != (item["process_rev"], item["conversion_rev"]):
                        raise ValueError("Raw Base revision changed before delivery")
                key = _key(channel, level, _config_chat_id(channel, level), period, slot)
                outcome = _send_group(channel, level, review_dir, key)
            except Exception as exc:
                outcome = {"status": "blocked", "error": str(exc)}
            item["groups"][level] = outcome
            _write_json(result_path, batch_result)


def run(*, period_date: str = "", confirm_send: bool = False, now: datetime | None = None,
        output: Path | None = None) -> dict:
    batch = _batch()
    now = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    if confirm_send:
        if period_date or (batch["status"], batch["schedule_enabled"]) != ("active", True):
            raise ValueError("Batch sending is disabled or a diagnostic period was supplied")
        slot = _slot(now, batch)
        period = _period(slot.date())
    else:
        if not re.fullmatch(r"20\d{6}", period_date) or date.fromisoformat(
                f"{period_date[:4]}-{period_date[4:6]}-{period_date[6:]}").weekday() != 4:
            raise ValueError("Preview period must be a business Friday in YYYYMMDD format")
        slot = None
        period = period_date + "期"
    output = output or (STATE / "slots" / slot.strftime("%Y%m%d-%H%M") if slot else STATE / "previews" / period_date)
    dept_on = _dept_active(slot)
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "batch.json"
    previous = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
    if previous and (previous["period"], previous["slot"]) != (period, slot.isoformat() if slot else None):
        raise ValueError("Existing batch identity differs from this run")
    result = {"period": period, "slot": slot.isoformat() if slot else None, "channels": {}}
    for entry in batch["channels"]:
        channel = entry["id"]
        channel_dir = output / channel
        channel_result = {"process_rev": None, "conversion_rev": None, "snapshots": {},
                          "review": None, "groups": {}}
        result["channels"][channel] = channel_result
        levels = _channel_levels(channel)
        if not entry.get("scheduled", True):
            # 审定门控：图书/本地化在用户确认预览前不参与调度（不取数、不发送）。
            for level in levels:
                channel_result["groups"][level] = {"status": "skipped_schedule_disabled"}
            continue
        try:
            process_source = channel_dir / "source_process.ndjson"
            manifest = fetch(channel, period, process_source)
            channel_result["process_rev"] = manifest["rev"]
            channel_result["snapshots"]["process"] = " ".join(
                (manifest["snapshot"][0], manifest["snapshot"][1] + ":00"))
            conversion_source = channel_dir / "source_conversion.ndjson"
            conversion_manifest = export_conversion(channel, period, conversion_source)
            channel_result["conversion_rev"] = conversion_manifest["rev"]
            conversion_rows = [json.loads(line) for line
                               in conversion_source.read_text(encoding="utf-8").splitlines() if line]
            # 2026-10-02 用户指令：无论有无收款/人头/报科产出，均按预设窗口推送一次；
            # 无数据的群由消息中的 fallback 文案标识（build 渲染，deliver 照常发送）。
            channel_result["conversion_has_output"] = _conversion_output(conversion_rows)
            review = build(process_source, conversion_source, channel_dir,
                           CONFIG_DIR / entry["config"], channels=(channel,))
            if review["period"] != period:
                raise ValueError("Source period differs from requested period")
            if slot:
                _fresh(review, period, slot, batch)
            channel_result["review"] = review
            channel_result["snapshots"]["conversion"] = review["conversion_snapshot"]
            for level in levels:
                if level == "dept" and not dept_on:
                    channel_result["groups"][level] = {"status": "skipped_not_in_window"}
                else:
                    channel_result["groups"][level] = {"status": "prepared"}
        except Exception as exc:
            for level in levels:
                if level == "dept" and not dept_on:
                    channel_result["groups"][level] = {"status": "skipped_not_in_window"}
                else:
                    channel_result["groups"][level] = {"status": "blocked_prepare", "error": str(exc)}
    # 2026-10-01 用户要求推送解耦：任一渠道的版本漂移/快照不一致只记录、只影响
    # 该渠道自身（发送前每个群仍独立 probe 自身双表 rev，见 _deliver_groups），
    # 不再整批拦停其他渠道的推送。
    process_revs = {item["process_rev"] for item in result["channels"].values() if item["process_rev"] is not None}
    conversion_revs = {item["conversion_rev"] for item in result["channels"].values() if item["conversion_rev"] is not None}
    result["rev_consistency"] = "uniform" if len(process_revs) <= 1 and len(conversion_revs) <= 1 else "mixed"
    drifted = []
    if previous:
        for ch, item in result["channels"].items():
            prev_item = previous["channels"].get(ch) or {}
            if (item["process_rev"] is not None and prev_item.get("process_rev") is not None
                    and (prev_item["process_rev"], prev_item.get("conversion_rev"))
                    != (item["process_rev"], item["conversion_rev"])):
                drifted.append(ch)
    result["source_version_drift"] = drifted
    try:
        _index(output, result)
    except Exception as exc:
        if not confirm_send:
            raise
        result["index_error"] = str(exc)
    _write_json(result_path, result)
    if confirm_send:
        _deliver_groups(batch, result, output, slot)
    return result


def run_scope(config_path: Path, channel_id: str):
    try:
        name = json.loads(Path(config_path).read_text(encoding="utf-8")).get("windows_task_name")
    except Exception:  # noqa: BLE001
        name = None
    return push_log.run_scope("qingcheng", channel_id, name or "unknown-task")


def main() -> None:
    ensure_console_streams()  # pythonw.exe has no console streams
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period-date", default="", help="Business Friday YYYYMMDD for local preview")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--confirm-send", action="store_true")
    args = parser.parse_args()
    with run_scope(BATCH_CONFIG, "transformation_batch") as scope:
        scope.event("run_started", confirmed=args.confirm_send, period_date=args.period_date)
        if args.confirm_send:
            with _single_instance():
                result = run(period_date=args.period_date, confirm_send=True, output=args.output)
        else:
            result = run(period_date=args.period_date, output=args.output)
        print(json.dumps({"period": result["period"], "slot": result["slot"],
                          "channels": {channel: {"process_rev": item["process_rev"],
                                                 "conversion_rev": item["conversion_rev"],
                                                 "snapshots": item["snapshots"],
                                                 "groups": item["groups"]}
                                       for channel, item in result["channels"].items()}},
                         ensure_ascii=True, indent=2))
        scope.event("report_ready", period=result["period"], slot=result["slot"])
        scope.adopt(result)
        accepted = ({"sent_verified", resend.UNVERIFIABLE, "skipped_no_conversion_data",
                     "skipped_schedule_disabled", "skipped_not_in_window"}
                    if args.confirm_send else
                    {"prepared", "skipped_no_conversion_data", "skipped_schedule_disabled",
                     "skipped_not_in_window"})
        failed = any(value.get("status") not in accepted
                     for item in result["channels"].values() for value in item["groups"].values())
        scope.exit_code = 1 if failed else 0
        if failed:
            scope.event("run_needs_attention")
            raise SystemExit(1)
        scope.event("run_finished")


if __name__ == "__main__":
    main()
