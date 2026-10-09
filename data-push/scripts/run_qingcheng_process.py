"""Prepare and deliver six independent Qingcheng process group reports."""

from __future__ import annotations

from qingcheng_schedule import resolve_slot

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
from preview_qingcheng_public_pool_process import build
from lark_delivery.common import push_log, resend
from lark_delivery.common.readback import available as readback_available
from lark_delivery.common.retry import retry_transport
from lark_delivery.common.runtime import CREATE_NO_WINDOW, ensure_console_streams


SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
CONFIG_DIR = SKILL / "config/departments/qingcheng"
BATCH_CONFIG = CONFIG_DIR / "process_batch_preview.json"
STATE = WORKSPACE / "runtime/qingcheng-process-batch"
LEVELS = ("supervisor", "consultant")
OPERATOR = WORKSPACE / "skills/usql-web-query-operator/scripts/tiangong2_task.py"
AUDIT_CHANNELS = {"public_pool": ("顾问未加好友",), "private": ("私域表单", "私域品效"),
                  "douyin_dm": ("抖音私信",)}

# 执行台账里的 taskName 是执行行建立时的任务名快照。任务在 2026-09-28 由
# `qing2lark` 改名为 `qing2lark_guocheng` 后，新建立的执行行报新名，改名之前建立
# 的行仍报旧名（2026-09-29 00:00 的行已是新名，更早各行仍是旧名）。不可变的 Nezha
# 任务 ID（67318）才是身份锚点，所以两个名字都接受。
#
# stage 日志文件名跟的是平台上的脚本文件，不随任务改名而变：2026-09-29 00:00
# 那次执行行已报新名，产出的仍是 `stage_175092770_qing2lark.log`（175092770 是脚本
# 文件 ID）。两个后缀都保留不是冗余——旧后缀正是当前生效的那个，删掉任一都会让
# 审计选不中唯一的 stage 日志，从而拦停全部青橙推送。
TASK_NAME_ALIASES = ("qing2lark_guocheng", "qing2lark")
STAGE_LOG_SUFFIXES = ("_qing2lark.log", "_qing2lark_guocheng.log")
# The local Qingcheng batches start on the hour while qing2lark runs at :40.
# Nezha's periodTime is normalized to the containing hour, so a 12:00 local
# batch must audit the 11:40 upstream execution, represented as 11:00.
UPSTREAM_RUN_LEAD_MINUTES = 20


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
            raise RuntimeError("Another Qingcheng process batch is already running") from exc
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _batch() -> dict:
    batch = json.loads(BATCH_CONFIG.read_text(encoding="utf-8"))
    calendar = batch["business_calendar"]
    if (batch["schema_version"], batch["domain"], batch["report_type"]) != (1, "qingcheng", "process"):
        raise ValueError("Unexpected Qingcheng process batch scope")
    if [item["id"] for item in batch["channels"]] != ["public_pool", "private", "douyin_dm"]:
        raise ValueError("All Qingcheng process channels must be explicit")
    if (calendar["process_weekdays"], calendar["hours"], calendar["minute"], calendar["retry_window_minutes"], calendar["timezone"]) != ([1, 2, 3], [13, 17, 21], 50, 50, "Asia/Shanghai"):
        raise ValueError("Process batch calendar differs from the reviewed slots")
    upstream = batch["upstream"]
    if (batch["retry_interval_minutes"], batch["windows_task_name"], upstream["project_id"], upstream["folder"],
            upstream["menu_id"], upstream["task_id"], upstream["nezha_task_id"], upstream["task_name"],
            upstream["owner"], upstream["published_version"], upstream["version_id"], upstream["exec_file_id"],
            upstream["source_sha256"], upstream["audit_schema"]) != (
            2, "Codex-Lark-Qingcheng-Process-GroupPush", 308, "吕帅", 103625, 47728, 67318,
            "qing2lark_guocheng", "lvshuai01", "V29", 207387, 831981,
            "2da69b923428509481cb185017d8ad05a1a126e5600c8f418396f51d12130de6",
            "market2lark-two-period-audit-v1"):
        raise ValueError("Qingcheng upstream or Windows task pin differs")
    return batch


def _period(day: date) -> str:
    friday = day + timedelta(days=(4 - day.weekday()) % 7)
    return friday.strftime("%Y%m%d") + "期"


def _slot(now: datetime, batch: dict) -> datetime:
    calendar = batch["business_calendar"]
    return resolve_slot(now, weekdays=calendar["process_weekdays"], hours=calendar["hours"],
                        minute=calendar["minute"], retry_minutes=batch["retry_interval_minutes"],
                        window_minutes=calendar["retry_window_minutes"],
                        error="Outside the authorized Qingcheng process window")


def _key(channel: str, level: str, chat_id: str, period: str, slot: datetime) -> str:
    parts = ["qingcheng", "local", channel, chat_id, period, "process", slot.isoformat()]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"qc_{channel[:2]}_{level[:3]}_{slot:%Y%m%d%H%M}_{digest}"


def _fresh(review: dict, period: str, slot: datetime) -> None:
    if review["period"] != period:
        raise ValueError("Raw Base period differs from the business Friday")
    source_time = datetime.strptime(review["snapshot"], "%Y%m%d %H:%M").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    age = (slot - source_time).total_seconds() / 60
    if age < 0 or age > 240:
        raise ValueError("Raw Base source snapshot is outside the freshness window")


def _operator_read(command: str, *args: str) -> dict:
    upstream = _batch()["upstream"]
    result = subprocess.run([sys.executable, str(OPERATOR), command, "--project-id", str(upstream["project_id"]),
                             "--folder", upstream["folder"], "--menu-id", str(upstream["menu_id"]),
                             "--task-name", upstream["task_name"], *args],
                            cwd=WORKSPACE, capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=120, creationflags=CREATE_NO_WINDOW)
    if result.returncode:
        raise ValueError(f"Tiangong2 {command} read failed: {result.stderr[-600:]}")
    payload = json.loads(result.stdout)
    if payload.get("ok") is not True or payload.get("read_only") is not True or payload.get("remote_mutations") != 0:
        raise ValueError(f"Tiangong2 {command} read was not verified")
    return payload


def _expected_upstream_period_time(slot: datetime) -> str:
    upstream_start = slot - timedelta(minutes=UPSTREAM_RUN_LEAD_MINUTES)
    return upstream_start.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def _upstream_audit(period: str, slot: datetime) -> dict:
    history_result = _operator_read("list-execution-history", "--limit", "50")
    history = json.loads((Path(history_result["artifact_dir"]) / "history.json").read_text(encoding="utf-8"))
    upstream_period_time = _expected_upstream_period_time(slot)
    # The upstream runs at :40 before each local on-the-hour batch. Nezha reports
    # that execution's periodTime at the containing hour (for example, 11:40 as
    # 11:00). The source of truth is still the unique successful execution pinned
    # to the reviewed exec file, whatever way it was triggered; uniqueness and the
    # newest-execution guard stay enforced.
    candidates = []
    for entry in history["executions"]:
        if entry.get("periodTime") != upstream_period_time or entry.get("status") != 6:
            continue
        try:
            entry_config = json.loads(entry.get("runConfig") or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        if (entry_config.get("projectId"), entry_config.get("execFileId")) == (308, 831981):
            candidates.append(entry)
    if len(candidates) != 1:
        raise ValueError("Expected upstream-hour successful qing2lark execution is not unique")
    latest = candidates[0]
    if latest["id"] != max(entry["id"] for entry in history["executions"]):
        raise ValueError("A newer qing2lark execution may have replaced the source")
    run_config = json.loads(latest["runConfig"])
    # 执行行报的是该行建立时的任务名快照：改名后建立的行已报新名，改名前的行仍报
    # 旧名。身份锚点是不可变的 Nezha 任务 ID，所以只要求名字落在兼容集合内。
    if latest.get("taskName") not in TASK_NAME_ALIASES:
        raise ValueError("The expected upstream-hour execution is not the qing2lark task")
    if (latest.get("taskId"), latest.get("periodTime"),
            run_config.get("projectId"), run_config.get("execFileId")) != (
            67318, upstream_period_time,
            308, 831981):
        raise ValueError("The expected upstream-hour qing2lark execution is not successful or has drifted")
    if run_config.get("triggerSourceEnum") not in ("SCHEDULE", "EXECUTE"):
        raise ValueError("The expected upstream-hour qing2lark execution has an unexpected trigger")
    log_result = _operator_read("fetch-execution-log", "--exec-id", str(latest["id"]))
    log_dir = Path(log_result["artifact_dir"])
    execution = json.loads((log_dir / "execution.json").read_text(encoding="utf-8"))
    if (execution["scope"]["project_id"], execution["scope"]["menu_id"], execution["scope"]["task_id"],
            execution["scope"]["nezha_task_id"], execution["scope"]["execution_id"],
            execution["identity"]["name"], execution["diagnostic"]["classification"]) != (
            308, 103625, 47728, 67318, latest["id"], "lvshuai01", "execution_success"):
        raise ValueError("Tiangong2 execution identity or outcome differs")
    logs = [path for path in log_dir.glob("stage_*.log") if path.name.endswith(STAGE_LOG_SUFFIXES)]
    if len(logs) != 1:
        raise ValueError("Qingcheng upstream audit stage is not unique")
    lines = logs[0].read_text(encoding="utf-8").splitlines()
    audit_lines = [line.split("：", 1)[1] for line in lines if line.startswith("process表快照清单：")]
    if len(audit_lines) != 1 or not any(line.startswith("SUCCESS: 青橙项目部") for line in lines) or not any(line.strip() == "exit_code:  0" for line in lines):
        raise ValueError("Complete process source audit and readback were not found")
    audit = json.loads(audit_lines[0])
    info = audit.get("periods", {}).get(period)
    if (audit.get("schema_version") != "market2lark-two-period-audit-v1" or audit.get("field_count") != 27
            or info is None or len(info.get("snapshots", [])) != 1 or
            sum(audit["periods"][name]["row_count"] for name in audit["periods"]) != audit["row_count"] or
            any(sum(part["channel_counts"].values()) != part["row_count"] for part in audit["periods"].values()) or
            f"最终回读校验通过：{audit['row_count']}条" not in lines):
        raise ValueError("Process audit period, fields, or snapshot differs")
    snapshot = info["snapshots"][0]
    if len(snapshot) != 2 or not re.fullmatch(r"20\d{6}", snapshot[0]) or not re.fullmatch(r"\d{1,2}", snapshot[1]):
        raise ValueError("Invalid process audit snapshot")
    return {"execution_id": latest["id"], "upstream_period_time": upstream_period_time,
            "snapshot": snapshot,
            "raw_channel_counts": info["channel_counts"],
            "expected_counts": {channel: sum(info["channel_counts"].get(name, 0) for name in names)
                                for channel, names in AUDIT_CHANNELS.items()}}


def _receipt_path(channel: str, level: str, config_path: Path, review_dir: Path,
                  period: str, slot: datetime) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    chat_id = config["profiles"][level]["target_chat_id"]
    return review_dir / f"{level}_process_send_{_key(channel, level, chat_id, period, slot)}.json"


def _receipt_state(receipt: Path) -> tuple[str, str]:
    """``(verdict, message_id)`` for one receipt; ``RESEND`` when nothing is on record.

    A success receipt is the raw send output and carries **no** ``status`` field, so
    the verdict comes from the recorded message id paired with ``readback.verified``.
    """
    if not receipt.exists():
        return resend.RESEND, ""
    saved = json.loads(receipt.read_text(encoding="utf-8"))
    message_id = str((saved.get("response") or {}).get("message_id") or "")
    if saved.get("status"):
        saved_status = saved["status"]
    else:
        saved_status = "sent_verified" if (saved.get("readback") or {}).get("verified") is True else "sent_unverified"
    return resend.decide(saved_status, message_id), message_id


def _send_group(channel: str, level: str, config_path: Path, review_dir: Path, period: str, slot: datetime) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    chat_id = config["profiles"][level]["target_chat_id"]
    key = _key(channel, level, chat_id, period, slot)
    receipt = review_dir / f"{level}_process_send_{key}.json"
    verdict, message_id = _receipt_state(receipt)
    if verdict == resend.DONE:
        return {"status": "sent_verified", "message_id": message_id, "receipt": str(receipt)}
    # The availability question is asked only on a readback failure (below), so a normal
    # send costs no extra API call.
    script = SKILL / "scripts/send_qingcheng_process.py"
    # A recorded message id means the message is in the group: re-read, never re-send.
    # Otherwise re-issue with the SAME key, so the platform dedupes if the earlier
    # attempt did land.
    mode = "--reverify-only" if verdict == resend.REVERIFY else "--send"
    command = [sys.executable, str(script), "--level", level, "--review-dir", str(review_dir),
               "--config", str(config_path), "--idempotency-key", key, mode]
    result = subprocess.run(command, cwd=WORKSPACE, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240, creationflags=CREATE_NO_WINDOW)
    if result.returncode:
        if receipt.exists():
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            message_id = saved.get("response", {}).get("message_id")
            if isinstance(message_id, str) and message_id.startswith("om_") and saved.get("readback", {}).get("verified") is False:
                error = saved["readback"].get("error")
                # Unreadable group: the write was acknowledged and verification is
                # impossible by policy, so this is an accepted terminal state rather than
                # a failure. Never re-issued -- a new key would post a second copy.
                if not readback_available(config["profiles"][level], chat_id):
                    return {"status": resend.UNVERIFIABLE, "message_id": message_id,
                            "error": error, "receipt": str(receipt)}
                return {"status": "readback_failed", "message_id": message_id,
                        "error": error, "receipt": str(receipt)}
        return {"status": "blocked_or_uncertain", "error": (result.stderr or result.stdout)[-1200:].strip(),
                "receipt": str(receipt) if receipt.exists() else None}
    response = json.loads(result.stdout)
    if response.get("readback", {}).get("verified") is not True:
        unreadable = not readback_available(config["profiles"][level], chat_id)
        return {"status": resend.UNVERIFIABLE if unreadable else "readback_failed",
                "receipt": str(receipt)}
    return {"status": "sent_verified", "message_id": response["readback"]["message_id"], "receipt": str(receipt)}


def _index(output: Path, batch_result: dict) -> None:
    cards = []
    for channel, channel_result in batch_result["channels"].items():
        for level in LEVELS:
            review = channel_result["reviews"].get(level)
            if review is None:
                continue
            item = review["results"][level]
            cards.append(f"<section><h2>{html.escape(channel)} · {html.escape(item['level'])}</h2>"
                         f"<img src='{channel}/{level}/{item['process_png']}' alt='过程图片'>"
                         f"<pre>{html.escape(item['process_message'])}</pre></section>")
    page = ("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>青橙过程数据本地预览</title>"
            "<style>body{font:16px 'Microsoft YaHei',sans-serif;background:#edf2f8;color:#20314c;padding:24px}"
            "main{max-width:1900px;margin:auto}section{background:white;margin:22px 0;padding:20px;border-radius:12px}"
            "img{max-width:100%;border:1px solid #c3cfe2}pre{white-space:pre-wrap;background:#f2f6fb;padding:14px}</style>"
            f"<main><h1>青橙公海、私域与抖音私信 · 过程数据本地预览</h1><p>{html.escape(batch_result['period'])}</p>"
            + "".join(cards) + "</main></html>")
    (output / "index.html").write_text(page, encoding="utf-8")


def _deliver_groups(batch: dict, result: dict, output: Path, slot: datetime) -> None:
    period = result["period"]
    result_path = output / "batch.json"
    for entry in batch["channels"]:
        channel = entry["id"]
        for level in LEVELS:
            group = result["channels"][channel]["groups"][level]
            if group["status"] not in ("prepared", resend.REVERIFY, resend.RESEND):
                continue
            try:
                # A readback-only re-verify does not depend on the source at all, and the
                # source has usually moved on by the time one is due -- probing it here
                # would block the one path that cannot duplicate a message.
                if group["status"] != resend.REVERIFY:
                    # A transport failure means nothing was learned, so it is retried
                    # in-round; a returned revision that differs still fails closed.
                    current_rev = retry_transport(lambda: probe_revision(
                        channel, period, output / channel / f"probe_{level}.ndjson"))
                    if current_rev != result["channels"][channel]["source_rev"]:
                        raise ValueError("Raw Base revision changed before delivery")
                outcome = _send_group(channel, level, CONFIG_DIR / entry["config"], output / channel / level, period, slot)
            except Exception as exc:
                outcome = {"status": "blocked", "error": str(exc)}
            result["channels"][channel]["groups"][level] = outcome
            _write_json(result_path, result)


def run(*, period_date: str = "", confirm_send: bool = False, now: datetime | None = None, output: Path | None = None) -> dict:
    batch = _batch()
    now = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    if confirm_send:
        if period_date or (batch["status"], batch["schedule_enabled"]) != ("active", True):
            raise ValueError("Batch sending is disabled or a diagnostic period was supplied")
        slot = _slot(now, batch)
        period = _period(slot.date())
    else:
        if not re.fullmatch(r"20\d{6}", period_date) or date.fromisoformat(f"{period_date[:4]}-{period_date[4:6]}-{period_date[6:]}").weekday() != 4:
            raise ValueError("Preview period must be a business Friday in YYYYMMDD format")
        slot = None
        period = period_date + "期"
    output = output or (STATE / "slots" / slot.strftime("%Y%m%d-%H%M") if slot else STATE / "previews" / period_date)
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "batch.json"
    previous = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
    if previous and (previous["period"], previous["slot"]) != (period, slot.isoformat() if slot else None):
        raise ValueError("Existing batch identity differs from this run")
    audit = _upstream_audit(period, slot) if slot else None
    result = {"period": period, "slot": slot.isoformat() if slot else None, "upstream_audit": audit, "channels": {}}
    for entry in batch["channels"]:
        channel = entry["id"]
        config_path = CONFIG_DIR / entry["config"]
        channel_dir = output / channel
        source = channel_dir / "source.ndjson"
        channel_result = {"source_rev": None, "snapshot": None, "reviews": {}, "groups": {}}
        result["channels"][channel] = channel_result
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            if config["channel_id"] != channel or config["report_type"] != "process":
                raise ValueError("Channel config differs from batch routing")
            if confirm_send and (config["status"], config["schedule_enabled"]) != ("active", True):
                raise ValueError("A child channel is not active")
        except Exception as exc:
            for level in LEVELS:
                channel_result["groups"][level] = {"status": "blocked_config", "error": str(exc)}
            continue
        if audit and audit["expected_counts"][channel] == 0:
            for level in LEVELS:
                channel_result["groups"][level] = {"status": "skipped_no_eligible_rows"}
            continue
        try:
            manifest = fetch(channel, period, source)
            channel_result["source_rev"] = manifest["rev"]
            channel_result["snapshot"] = " ".join((manifest["snapshot"][0], manifest["snapshot"][1] + ":00"))
            if audit and (manifest["records_count"] != audit["expected_counts"][channel]
                          or [manifest["snapshot"][0], str(int(manifest["snapshot"][1]))] != [audit["snapshot"][0], str(int(audit["snapshot"][1]))]):
                raise ValueError("Raw Base slice differs from current upstream audit")
        except Exception as exc:
            for level in LEVELS:
                channel_result["groups"][level] = {"status": "blocked_source", "error": str(exc)}
            continue
        for level in LEVELS:
            try:
                if slot:
                    path = _receipt_path(channel, level, config_path, channel_dir / level, period, slot)
                    verdict, message_id = _receipt_state(path)
                    if verdict == resend.DONE:
                        channel_result["groups"][level] = {"status": "sent_verified",
                                                           "message_id": message_id, "receipt": str(path)}
                        continue
                    if path.exists():
                        # Prepared and dispatched once already, so the review on disk is
                        # still the reviewed one; only the outcome is open. Re-preparing
                        # would re-fetch a source that has since moved and block the retry.
                        channel_result["groups"][level] = {"status": verdict}
                        continue
                review = build(source, CONFIG_DIR / entry["supervisor_request"], CONFIG_DIR / entry["consultant_request"],
                               channel_dir / level, config_path, levels=(level,))
                if review["period"] != period:
                    raise ValueError("Source period differs from requested period")
                if slot:
                    _fresh(review, period, slot)
                channel_result["reviews"][level] = review
                channel_result["groups"][level] = {"status": "prepared"}
            except Exception as exc:
                channel_result["groups"][level] = {"status": "blocked_prepare", "error": str(exc)}
    # 2026-10-01 用户要求推送解耦：任一渠道的快照漂移/版本变化只记录、只影响该
    # 渠道自身（发送前每个群仍独立 probe 自身 rev，见 _deliver_groups），不再整批
    # 拦停其他渠道的推送。上游审计（_upstream_audit）是数据闸而非群推送，保持整批。
    versions = {(item["source_rev"], item["snapshot"]) for item in result["channels"].values() if item["source_rev"] is not None}
    result["rev_consistency"] = "uniform" if len(versions) <= 1 else "mixed"
    drifted = []
    if previous:
        for channel, item in result["channels"].items():
            prev_item = previous["channels"].get(channel) or {}
            if (item["source_rev"] is not None and prev_item.get("source_rev") is not None
                    and (prev_item["source_rev"], prev_item.get("snapshot"))
                    != (item["source_rev"], item["snapshot"])):
                drifted.append(channel)
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
    """Open the external run log for one scheduled Qingcheng run.

    Task Scheduler invokes these runners directly, with no PowerShell wrapper, so
    each runner mirrors its own stdout/stderr and lets the log be read after the
    fact. Reading the task name from the raw config (not the validated one) means
    even a validation failure leaves a log. Never blocks the push.
    """
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
    parser.add_argument("--check-config", action="store_true")
    args = parser.parse_args()
    if args.check_config:
        print(json.dumps({"configuration": "valid", "batch": _batch()}, ensure_ascii=True))
        return
    with run_scope(BATCH_CONFIG, "process_batch") as scope:
        scope.event("run_started", confirmed=args.confirm_send, period_date=args.period_date)
        if args.confirm_send:
            with _single_instance():
                result = run(period_date=args.period_date, confirm_send=True, output=args.output)
        else:
            result = run(period_date=args.period_date, output=args.output)
        print(json.dumps({"period": result["period"], "slot": result["slot"],
                          "channels": {channel: {"source_rev": item["source_rev"], "snapshot": item["snapshot"],
                                                 "rows": {level: review["results"][level]["process_rows"] for level, review in item["reviews"].items()},
                                                 "groups": item["groups"]} for channel, item in result["channels"].items()}},
                         ensure_ascii=True, indent=2))
        scope.event("report_ready", period=result["period"], slot=result["slot"])
        scope.adopt(result)
        accepted = ({"sent_verified", resend.UNVERIFIABLE, "skipped_no_eligible_rows"}
                    if args.confirm_send else {"prepared"})
        failed = any(value.get("status") not in accepted
                     for item in result["channels"].values() for value in item["groups"].values())
        scope.exit_code = 1 if failed else 0
        if failed:
            scope.event("run_needs_attention")
            raise SystemExit(1)
        scope.event("run_finished")


if __name__ == "__main__":
    main()
