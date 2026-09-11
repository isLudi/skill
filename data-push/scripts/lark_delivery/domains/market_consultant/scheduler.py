#!/usr/bin/env python
"""Fail-closed, four-slot local broadcaster. No upstream or Base mutations.

Only --watch --confirm-send opens the message outlet. Preflight is read-only.
Windows Task Scheduler owns wakeup; SQLite owns durable per-slot delivery claims.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

from ...common import feishu as gp
from ...core import catalog
from ...core.locks import runner_lock
from .workflow import prepare_report
from .adapter import report_arguments
from ...integrations import tiangong_release as rb
from .channels import self_incubated_koc_5 as bp
from . import grade_report as gr
from ...paths import SKILL_ROOT, SKILLS_ROOT

TZ = timezone(timedelta(hours=8))
SKILLS = SKILLS_ROOT
OPERATOR = SKILLS / "usql-web-query-operator/scripts/tiangong2_task.py"
DEFAULT_CONFIG = SKILL_ROOT / "config/scheduled_push.json"
_LIVE_STATUS_PATH = ContextVar("data_push_live_status_path", default=None)


def now():
    return datetime.now(TZ)


def emit(event, **fields):
    payload = {"at": now().isoformat(), "event": event, **fields}
    path = _LIVE_STATUS_PATH.get()
    if path is not None:
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    print(json.dumps(payload, ensure_ascii=False, default=str), flush=True)


@contextmanager
def live_status(state, cfg, slot):
    """Expose only the current run state; never retain a historical status log."""
    path = Path(state) / "live-status.json"
    path.unlink(missing_ok=True)
    token = _LIVE_STATUS_PATH.set(path)
    try:
        emit("started", slot=slot.isoformat(), channel_key=cfg["channel_key"],
             task_name=cfg["windows_task_name"], deadline=(slot + timedelta(minutes=cfg["deadline_minute"])).isoformat())
        yield path
    finally:
        path.unlink(missing_ok=True)
        for temporary in path.parent.glob(f".{path.name}.*.tmp"):
            temporary.unlink(missing_ok=True)
        _LIVE_STATUS_PATH.reset(token)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_config(path):
    cfg = catalog.resolve_compat_config(path, "schedule")
    validate_config(cfg)
    return cfg


def validate_config(cfg):
    catalog.require_registered_schedule(cfg)
    if cfg.get("hours") != [13, 17, 21] or cfg.get("timezone") != "Asia/Shanghai":
        raise ValueError("Unreviewed schedule; expected afternoon China-time slots")
    order = cfg.get("stagger_order")
    start_minute = cfg.get("prepare_minute")
    if (not isinstance(order, int) or order < 1 or start_minute != 19 + order
            or cfg.get("send_minute") != start_minute
            or cfg.get("deadline_minute") != 50 or cfg.get("retry_minutes") != 2
            or not re.fullmatch(r"Codex-Lark-[A-Za-z0-9-]+Push", cfg.get("windows_task_name", ""))):
        raise ValueError("Unreviewed retry window")
    if cfg.get("report_profile") not in {bp.PROFILE, "supervisor-detail"}:
        raise ValueError("Unreviewed delivery profile")
    if not cfg.get("channel_key") and (cfg.get("channels") != [bp.CHANNEL] or cfg.get("chat_id") != bp.CHAT_ID):
        raise ValueError("Unreviewed delivery scope")
    if (cfg.get("period_rule") != "natural_week_friday" or cfg.get("process_weekdays") != list(range(7))
            or cfg.get("result_weekdays") != [4, 5, 6]):
        raise ValueError("Unreviewed business-week period or weekday policy")
    return cfg


def active_slot(at, cfg, preflight=False):
    at = at.astimezone(TZ)
    if at.hour not in cfg["hours"]:
        return None
    slot = at.replace(minute=0, second=0, microsecond=0)
    if not preflight and not (slot + timedelta(minutes=cfg["prepare_minute"]) <= at < slot + timedelta(minutes=cfg["deadline_minute"] + 1)):
        return None
    if slot + timedelta(minutes=cfg["send_minute"]) < datetime.fromisoformat(cfg["first_send_at"]):
        return None
    return slot


def next_check(at, slot, cfg):
    start = slot + timedelta(minutes=cfg["send_minute"])
    if at < start:
        return start
    interval = cfg["retry_minutes"] * 60
    n = math.floor((at - start).total_seconds() / interval) + 1
    return start + timedelta(seconds=interval * n)


def require_send_window(slot, cfg=None):
    start = 20 if cfg is None else cfg["send_minute"]
    deadline = 50 if cfg is None else cfg["deadline_minute"]
    if not slot + timedelta(minutes=start) <= now() < slot + timedelta(minutes=deadline + 1):
        raise ValueError(f"message outlet is outside the authorized :{start:02d}-:{deadline:02d} window")


def operator_reply(command, cfg, *extra):
    u = cfg["upstream"]
    argv = [sys.executable, str(OPERATOR), command, "--project-id", str(u["project_id"]),
            "--folder", u["folder"], "--menu-id", str(u["menu_id"]), "--task-name", u["task_name"], *extra]
    result = subprocess.run(argv, cwd=str(SKILLS.parent), capture_output=True, text=True,
                            encoding="utf-8", timeout=120,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode:
        # Operator artifacts contain redacted diagnostics; do not leak raw CLI errors.
        raise RuntimeError("upstream read-only operator failed: %s exit=%s" % (command, result.returncode))
    reply = json.loads(result.stdout)
    if not reply.get("read_only") or reply.get("remote_mutations") != 0:
        raise RuntimeError("invalid read-only operator receipt")
    return reply


def operator(command, cfg, *extra):
    reply = operator_reply(command, cfg, *extra)
    if not reply.get("ok"):
        raise RuntimeError("upstream read-only operator did not succeed")
    return Path(reply["artifact_dir"])


def validate_history(history, cfg, slot):
    u = cfg["upstream"]
    scope = history["scope"]
    for k in ("project_id", "folder", "menu_id", "task_name", "task_id", "nezha_task_id"):
        if scope.get(k) != u[k]:
            raise ValueError("upstream scope drift: " + k)
    schedule = history["task_schedule"]
    if (history["identity"].get("name") != u["owner"] or schedule.get("supervisor") != u["owner"]
            or schedule.get("scheduleId") != u["schedule_id"] or schedule.get("scheduleFrequency") != "4h"):
        raise ValueError("upstream identity or schedule drift")
    stamp = slot.strftime("%Y-%m-%d %H:%M:%S")
    rows = history["executions"]
    matches = [r for r in rows if r.get("periodTime") == stamp and r.get("planRunTime") == stamp]
    if len(matches) != 1:
        raise ValueError("current scheduled execution missing or ambiguous")
    row = matches[0]
    if row.get("status") != 6 or row.get("taskId") != u["nezha_task_id"]:
        raise ValueError("current upstream execution not successful")
    run = json.loads(row["runConfig"])
    if run.get("execFileId") != u["exec_file_id"] or run.get("triggerSourceEnum") != "SCHEDULE":
        raise ValueError("published execution file changed or non-scheduled run")
    if any(r["id"] != row["id"] and (r.get("startTime") or r.get("planRunTime") or "") > row["startTime"] for r in rows):
        raise ValueError("newer execution observed; data may be replacing")
    return row


def parse_complete_log(doc, directory, cfg, slot, execution):
    validate_history({**doc, "executions": [doc["execution"]]}, cfg, slot)
    if doc["execution"]["id"] != execution["id"] or doc["execution_detail"].get("status") != 6:
        raise ValueError("execution detail mismatch")
    stages = doc["stages"]
    if len(stages) != 1 or stages[0]["metadata"].get("statusDesc") != "success":
        raise ValueError("upstream stages incomplete")
    stage = stages[0]
    if stage["metadata"].get("taskId") != cfg["upstream"]["nezha_task_id"]:
        raise ValueError("stage task mismatch")
    path = (directory / stage["log_file"]).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError("invalid stage log path")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != stage["log_sha256"]:
        raise ValueError("stage log Hash mismatch")
    log = raw.decode("utf-8")
    required = ["新记录回读校验通过", "旧记录删除完成：", "最终回读校验通过：", "SUCCESS:"]
    if any(x not in log for x in required) or not re.search(r"exit_code:\s+0\s*$", log):
        raise ValueError("no complete write/readback success evidence")
    partitions = re.findall(r"采用dt=(\d{8}), hour=(\d+)，延迟(\d+)小时", log)
    counts = re.findall(r"数据校验通过：(\d+)行，期次([^，\r\n]+)，", log)
    final = re.findall(r"最终回读校验通过：(\d+)条", log)
    distributions = re.findall(r"渠道分布：(\{[^\r\n]+\})", log)
    if len(partitions) != 1 or not counts or not final or not distributions:
        raise ValueError("required upstream evidence missing")
    dt, hour, lag = partitions[0]
    if not 2 <= int(lag) <= 7:
        raise ValueError("source partition outside approved 2-7 hour lookback")
    source_at = datetime.strptime(dt + "%02d" % int(hour), "%Y%m%d%H").replace(tzinfo=TZ)
    if slot - source_at != timedelta(hours=int(lag)):
        raise ValueError("source partition not bound to current slot")
    total, period = counts[-1]
    channels = json.loads(distributions[-1])
    if int(total) != int(final[-1]) or sum(channels.values()) != int(total):
        raise ValueError("upstream counts disagree")
    raw_table_id = cfg.get("raw_table_id") or catalog.load_channel(catalog.DEFAULT_CHANNEL)["source"]["raw_table_id"]
    if "目标多维表格校验通过：table_id=" + raw_table_id not in log:
        raise ValueError("upstream Base destination changed")
    period_details = None
    if cfg["upstream"].get("log_protocol") == "two_period_audit_v1":
        audit_lines = re.findall(r"^双期快照清单：(\{[^\r\n]+\})\s*$", log, re.M)
        if len(audit_lines) != 1 or "渠道映射版本：0904" not in log:
            raise ValueError("two-period audit or channel-mapping evidence missing")
        audit = json.loads(audit_lines[0])
        period_details = audit.get("periods", {})
        if (audit.get("schema_version") != "market2lark-two-period-audit-v1" or audit.get("field_count") != 45
                or audit.get("row_count") != int(total) or len(period_details) != 2
                or sorted(period_details) != sorted(period.split("、"))):
            raise ValueError("invalid two-period source audit")
        combined_channels = {}
        for p, info in period_details.items():
            if not re.fullmatch(r"\d{8}期", p):
                raise ValueError("invalid audited period")
            datetime.strptime(p[:8], "%Y%m%d")
            n = info.get("row_count")
            distribution = info.get("channel_counts", {})
            if type(n) is not int or n <= 0 or any(type(v) is not int or v < 0 for v in distribution.values()) or sum(distribution.values()) != n:
                raise ValueError("period/channel audit counts disagree")
            snapshots = info.get("snapshots", [])
            if len(snapshots) != 1 or snapshots[0][0] != dt or int(snapshots[0][1]) != int(hour):
                raise ValueError("period audit has a different data snapshot")
            if any(not re.fullmatch(r"[0-9a-f]{64}", str(info.get(key, ""))) for key in ("key_sha256", "records_sha256")):
                raise ValueError("period audit fingerprints missing")
            for channel, count in distribution.items():
                combined_channels[channel] = combined_channels.get(channel, 0) + count
        if sum(info["row_count"] for info in period_details.values()) != int(total) or combined_channels != channels:
            raise ValueError("two-period totals disagree")
    policy = rb.active_policy(cfg, slot)
    if policy:
        rb.verify_raw_only_log(log, policy, period)
    return {"execution_id": execution["id"], "period": period, "periods": period_details, "dt": dt, "hour": int(hour),
            "total": int(total), "channel_counts": channels, "log_sha256": stage["log_sha256"],
            "artifact_dir": str(directory), "end_time": execution["endTime"]}


def upstream_ready(cfg, slot):
    directory = operator("list-execution-history", cfg, "--limit", "12")
    history = read_json(directory / "history.json")
    policy = rb.active_policy(cfg, slot)
    if policy and policy["previous_exec_file_id"] != cfg["upstream"]["exec_file_id"]:
        raise ValueError("approved release does not match previous file pin")
    file_id = rb.bound_file_id(cfg, policy) if policy else None
    needs_binding = bool(policy and file_id is None)
    if needs_binding:
        if now() >= datetime.fromisoformat(policy["expires_at"]):
            raise ValueError("one-time approved release binding window expired")
        stamp = slot.strftime("%Y-%m-%d %H:%M:%S")
        candidates = [row for row in history["executions"] if row.get("periodTime") == stamp and row.get("planRunTime") == stamp]
        if len(candidates) != 1:
            raise ValueError("approved release execution missing or ambiguous")
        file_id = json.loads(candidates[0]["runConfig"]).get("execFileId")
        if type(file_id) is not int or file_id <= 0:
            raise ValueError("approved release execution has no valid file ID")
    effective = cfg
    if file_id is not None:
        effective = {**cfg, "upstream": {**cfg["upstream"], "exec_file_id": file_id}}
    execution = validate_history(history, effective, slot)
    directory = operator("fetch-execution-log", cfg, "--exec-id", str(execution["id"]))
    evidence = parse_complete_log(read_json(directory / "execution.json"), directory, effective, slot, execution)
    if needs_binding:
        reply = operator_reply("plan-task-publish", cfg)
        if reply.get("status") != "blocked_already_published":
            raise ValueError("approved release publication is not stable")
        path = Path(reply["plan_file"]).resolve()
        root = SKILLS.parent / "runtime/usql-web-query-operator/tiangong2-task"
        if not path.is_relative_to(root.resolve()):
            raise ValueError("publication evidence path escaped Tiangong runtime")
        plan = read_json(path)
        if reply.get("plan_sha256") != plan.get("plan_sha256"):
            raise ValueError("publication evidence receipt mismatch")
        rb.validate_publication(plan, cfg, policy, execution, now())
        rb.persist_binding(cfg, policy, file_id, execution, plan, now())
        emit("approved_release_file_bound", version_id=policy["version_id"], exec_file_id=file_id, execution_id=execution["id"])
    if policy:
        evidence["approved_version_id"] = policy["version_id"]
        evidence["exec_file_id"] = file_id
    return evidence


def verify_bot(cfg):
    status = json.loads(gp.run_lark(["auth", "status", "--json", "--verify"], timeout=60))
    bot = status.get("identities", {}).get("bot", {})
    if not bot.get("verified") or bot.get("openId") != cfg["bot_open_id"] or bot.get("appName") != cfg["bot_name"]:
        raise ValueError("configured bot identity unavailable or changed")
    gp.verify_chat(cfg["chat_id"], cfg["chat_name"], "bot", 60)


def report_args(cfg, channel, slot=None):
    definition = catalog.load_channel(cfg.get("channel_key", catalog.DEFAULT_CHANNEL))
    targets = [target for target in catalog.select_targets(definition) if target["chat_id"] == cfg["chat_id"]]
    if len(targets) != 1 or channel not in definition.get("channels", [definition["channel"]]):
        raise ValueError("Channel/target is not registered")
    return report_arguments(definition, targets[0], channel=channel, state_dir=cfg["state_dir"], slot=slot or now())


def validate_context(context, evidence, cfg=None, slot=None):
    policy = bp
    if cfg is not None and cfg.get("channel_key"):
        from .adapter import policy_for
        policy = policy_for(catalog.load_channel(cfg["channel_key"]))
    source_period = (evidence.get("periods") or {}).get(context["period"])
    expected_count = source_period["channel_counts"].get(context["channel"]) if source_period else evidence["channel_counts"].get(context["channel"])
    period_matches = source_period is not None if evidence.get("periods") is not None else context["period"] == evidence["period"]
    if (not period_matches or context["raw_count"] != expected_count
            or str(context["snapshot"][0]) != evidence["dt"] or int(context["snapshot"][1]) != evidence["hour"]):
        raise ValueError("Base channel/period/partition/count disagrees with complete upstream write")
    if context["raw_read_audit"].get("has_more") is not False or context["raw_read_audit"].get("rev") is None:
        raise ValueError("incomplete Base snapshot")
    if context.get("report_profile") in {bp.PROFILE, "supervisor-detail"}:
        policy.enforce_group_scope(context["chat_id"], context["channel"], context["report_profile"])
        if cfg is not None:
            if context["chat_id"] != cfg["chat_id"] or context["identity"] != "bot":
                raise ValueError("configured group or sender mismatch")
            policy.enforce_live_calendar(context["period"], context["report_type"], slot or now())
            if context["report_type"] != policy.scheduled_report_type(slot or now()):
                raise ValueError("scheduled report type does not match the weekday policy")
        if context.get("skip_delivery"):
            report = context.get("supervisor_report")
            if (context.get("report_profile") != "supervisor-detail"
                    or context.get("skip_reason") != "no_supervisor_rows_meet_minimum_post_leads"
                    or not report or report["blocks"] or context.get("markdown")
                    or context.get("image_path") or context.get("result_image_path")
                    or report["reminder_names"]):
                raise ValueError("invalid no-data skip context")
            return
        info = context["mention_info"]
        expected_target = "supervisor" if context["report_profile"] == "supervisor-detail" else "manager"
        if context["mention_target"] != expected_target or any(info.get(k) for k in ("unresolved", "ambiguous", "lookup_error", "nonmembers")):
            raise ValueError("all lowest reminder accounts must be resolved and in the group")
        if set(info["resolved"]) != set(context["grade_report"]["reminder_names"]):
            raise ValueError("reminder account set mismatch")
        if gr.mention_ids(context["markdown"]) != set(info["resolved"].values()):
            raise ValueError("unexpected or missing manager mentions")
        report_sections = gr.sections(context["report_type"])
        if context["report_profile"] == "supervisor-detail":
            from . import supervisor_report
            report_sections = supervisor_report.sections(context["report_type"])
        for section in report_sections:
            if not context.get("image_path" if section == "process" else "result_image_path"):
                raise ValueError("selected report image missing")
    else:
        if cfg is not None and cfg.get("report_profile") == bp.PROFILE:
            raise ValueError("legacy report cannot be sent through the current group profile")
        if context["mention_target"] != "none" or gr.mention_ids(context["markdown"]):
            raise ValueError("mentions are forbidden in the legacy names-only profile")
        if not context.get("image_path") or not context.get("result_image_path"):
            raise ValueError("both report images are required")


def assert_current_revision(context, cfg):
    # The one-row read is only a revision guard, never the source for aggregation.
    with tempfile.TemporaryDirectory(prefix=".broadcast-rev-") as folder:
        data = gp._unwrap(json.loads(gp.run_lark([
            "base", "+record-list", "--base-token", context["coords"]["base_token"],
            "--table-id", context["raw_table_id"], "--field-id", "lead_id", "--limit", "1",
            "--output", "./revision.ndjson", "--format", "ndjson", "--as", cfg["base_as"]], cwd=folder, timeout=60)))
    if data.get("rev") != context["raw_read_audit"]["rev"]:
        raise ValueError("Base changed after snapshot; rebuild before sending")


def connect_ledger(state_dir):
    state_dir.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(state_dir / "deliveries.sqlite3", timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.execute("CREATE TABLE IF NOT EXISTS deliveries (key TEXT PRIMARY KEY, slot TEXT, channel TEXT, status TEXT, message_id TEXT, detail TEXT)")
    db.commit()
    return db


def delivery_key(cfg, slot, channel):
    scope = cfg["chat_id"] + "|" + slot.isoformat() + "|" + channel + "|both|bot"
    if cfg.get("channel_key") and (cfg["channel_key"] != catalog.DEFAULT_CHANNEL or cfg.get("target_id") != "gaoyang"):
        scope = cfg["channel_key"] + "|" + cfg["target_id"] + "|" + scope
    return hashlib.sha256(scope.encode()).hexdigest()[:40]


def claim(db, key, slot, channel):
    cur = db.execute("INSERT OR IGNORE INTO deliveries VALUES (?,?,?,?,?,?)",
                     (key, slot.isoformat(), channel, "sending", "", "{}"))
    db.commit()
    return cur.rowcount == 1


def receipt_readback(message_id, cfg, context, image_keys):
    data = gp._unwrap(json.loads(gp.run_lark(["im", "+messages-mget", "--message-ids", message_id,
                                            "--no-reactions", "--as", "bot", "--format", "json"], timeout=60)))
    matches = [x for x in data.get("messages", []) if x.get("message_id") == message_id]
    if len(matches) != 1:
        raise ValueError("message readback missing")
    msg = matches[0]
    content = msg.get("content", "")
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    if any(key not in text for key in image_keys.values()) or context["period"] not in text:
        raise ValueError("message readback images or period mismatch")
    expected_mentions = (set(context.get("mention_info", {}).get("resolved", {}).values())
                         if context.get("report_profile") in {bp.PROFILE, "supervisor-detail"} else set())
    actual_mentions = gr.mention_ids(content) | gr.mention_ids({"mentions": msg.get("mentions", [])})
    if actual_mentions != expected_mentions:
        raise ValueError("delivered mention accounts differ from the verified reminder set")
    if msg.get("chat_id") and msg["chat_id"] != cfg["chat_id"]:
        raise ValueError("message readback target mismatch")
    sender = msg.get("sender", {})
    sender_id = sender.get("open_bot_id") or sender.get("open_id") or sender.get("id")
    if str(sender_id).startswith("ou_") and sender_id != cfg["bot_open_id"]:
        raise ValueError("message readback sender ID mismatch")
    if not str(sender_id).startswith("ou_") and sender.get("name") and sender["name"] != cfg["bot_name"]:
        raise ValueError("message readback sender mismatch")
    return {"message_id": message_id, "verified": True, "sender": sender,
            "image_count": len(image_keys), "contains_mentions": bool(actual_mentions), "mention_ids": sorted(actual_mentions)}


def reverify_unverified_delivery(db, key, cfg, context):
    """Read back one already-sent message; this function has no send capability."""
    row = db.execute("SELECT status,message_id,detail FROM deliveries WHERE key=?", (key,)).fetchone()
    if not row or row[0] != "sent_unverified" or not row[1]:
        raise ValueError("delivery is not eligible for readback-only reverification")
    detail = json.loads(row[2])
    detail["readback"] = receipt_readback(row[1], cfg, context, detail["image_keys"])
    detail.pop("readback_error_type", None)
    updated = db.execute(
        "UPDATE deliveries SET status='sent_verified',detail=? WHERE key=? AND status='sent_unverified' AND message_id=?",
        (json.dumps(detail, ensure_ascii=False), key, row[1]))
    if updated.rowcount != 1:
        db.rollback()
        raise ValueError("delivery status changed during reverification")
    db.commit()
    return {"key": key, "message_id": row[1], "status": "sent_verified",
            "readback": detail["readback"]}


def deliver(context, cfg, slot, db, evidence):
    if context.get("skip_delivery"):
        emit("channel_skipped_no_eligible_rows", channel=context["channel"], period=context["period"],
             reason=context["skip_reason"])
        return True
    key = delivery_key(cfg, slot, context["channel"])
    return _deliver_verified(context, cfg, slot, db, evidence, key=key,
                             time_guard=lambda: require_send_window(slot, cfg))


def _deliver_verified(context, cfg, slot, db, evidence, *, key, time_guard):
    """Shared outlet; each authorized caller must supply its own real-time guard."""
    if context.get("skip_delivery"):
        emit("channel_skipped_no_eligible_rows", channel=context["channel"], period=context["period"],
             reason=context["skip_reason"])
        return True
    prior = db.execute("SELECT status,message_id FROM deliveries WHERE key=?", (key,)).fetchone()
    if prior:
        emit("duplicate_suppressed", channel=context["channel"], status=prior[0], message_id=prior[1])
        return prior[0] == "sent_verified"
    time_guard()
    if cfg.get("report_profile") == bp.PROFILE or context.get("report_profile") == bp.PROFILE:
        validate_context(context, evidence, cfg, slot)
        if gp.mention_nonmembers(cfg["chat_id"], context["mention_info"]["resolved"], "bot", 60):
            raise ValueError("reminded manager left the group before sending")
    assert_current_revision(context, cfg)
    markdown = context["markdown"]
    keys = {}
    # Upload failure is retryable; it cannot create a visible message.
    for section, path, refs in gp._image_slots(context):
        if path is None:
            continue
        image_key = gp.upload_image(path, "bot", 60)
        keys[section] = image_key
        for ref in refs:
            markdown = markdown.replace("](%s)" % ref, "](%s)" % image_key)
    # A slow upload or the preceding channel must not carry this send past cutoff.
    time_guard()
    if context.get("report_profile") == bp.PROFILE:
        assert_current_revision(context, cfg)
    if not claim(db, key, slot, context["channel"]):
        return False
    detail = {"upstream": evidence, "period": context["period"], "raw_count": context["raw_count"],
              "rev": context["raw_read_audit"]["rev"], "image_keys": keys}
    try:
        response = gp.send_markdown(cfg["chat_id"], markdown, key, "bot", dry_run=False, timeout=60)
        message_id = gp._message_id(response)
        if not message_id:
            raise RuntimeError("send response lacks actual message_id")
    except BaseException as exc:
        detail["error_type"] = type(exc).__name__
        db.execute("UPDATE deliveries SET status='uncertain',detail=? WHERE key=?", (json.dumps(detail, ensure_ascii=False), key))
        db.commit()
        emit("send_uncertain_manual_check_required", channel=context["channel"], key=key)
        return False
    # Commit the real receipt before cleanup; a crash must never reopen the send outlet.
    db.execute("UPDATE deliveries SET status='sent',message_id=?,detail=? WHERE key=?",
               (message_id, json.dumps(detail, ensure_ascii=False), key))
    db.commit()
    detail["image_cleanup"] = {section: gp._cleanup_local_image(path) for section, path, refs in gp._image_slots(context) if path is not None}
    try:
        detail["readback"] = receipt_readback(message_id, cfg, context, keys)
        status = "sent_verified"
    except Exception as exc:
        status = "sent_unverified"
        detail["readback_error_type"] = type(exc).__name__
    db.execute("UPDATE deliveries SET status=?,detail=? WHERE key=?", (status, json.dumps(detail, ensure_ascii=False), key))
    db.commit()
    emit(status, channel=context["channel"], message_id=message_id, image_cleanup=detail["image_cleanup"])
    return status == "sent_verified"


def run(cfg, preflight=False):
    slot = active_slot(now(), cfg, preflight)
    if (not cfg.get("enabled") and not preflight) or slot is None:
        emit("outside_authorized_window")
        return 0
    state = Path(cfg["state_dir"])
    with live_status(state, cfg, slot):
        db = connect_ledger(state)
        try:
            return run_slot(cfg, preflight, slot, state, db)
        finally:
            db.close()


def run_slot(cfg, preflight, slot, state, db):
    cached = None
    wake = now()
    attempt = 0
    deadline = slot + timedelta(minutes=cfg["deadline_minute"])
    while now() < deadline + timedelta(minutes=1):
        while now() < wake:
            time.sleep(min(20, max(0.01, (wake - now()).total_seconds())))
        try:
            attempt += 1
            emit("checking_bot_identity", attempt=attempt, slot=slot.isoformat())
            verify_bot(cfg)
            emit("checking_upstream", attempt=attempt, slot=slot.isoformat())
            evidence = upstream_ready(cfg, slot)
            if cached is None:
                contexts = []
                for channel in cfg["channels"]:
                    emit("preparing_channel_report", attempt=attempt, channel=channel, slot=slot.isoformat())
                    definition = catalog.load_channel(cfg.get("channel_key", catalog.DEFAULT_CHANNEL))
                    context = prepare_report(report_args(cfg, channel, slot), definition)
                    emit("validating_channel_snapshot", attempt=attempt, channel=channel, slot=slot.isoformat())
                    validate_context(context, evidence, cfg, slot)
                    contexts.append(context)
                if len({c["raw_read_audit"]["rev"] for c in contexts}) != 1:
                    raise ValueError("channels are not from the same Base revision")
                cached = contexts
            for context in cached:
                validate_context(context, evidence, cfg, slot)
                assert_current_revision(context, cfg)
            if preflight:
                for context in cached:
                    if not context.get("skip_delivery"):
                        gp.send_markdown(cfg["chat_id"], context["markdown"], context["idempotency_key"], "bot", dry_run=True, timeout=60)
                summary = {"status": "preflight_passed_no_send", "slot": slot.isoformat(), "upstream": evidence,
                            "channels": [{"channel": c["channel"], "period": c["period"], "rows": c["raw_count"],
                                          "delivery_status": "skipped_no_eligible_rows" if c.get("skip_delivery") else "ready",
                                          "rev": c["raw_read_audit"]["rev"], "process_image": str(c["image_path"]),
                                         "result_image": str(c["result_image_path"])} for c in cached]}
                (state / "preflight.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                emit("preflight_passed_no_send", **{k: v for k, v in summary.items() if k != "status"})
                return 0
            if now() < slot + timedelta(minutes=cfg["send_minute"]):
                emit("prepared_waiting_for_send_time", slot=slot.isoformat())
                wake = slot + timedelta(minutes=cfg["send_minute"])
                continue
            if now() >= deadline + timedelta(minutes=1):
                break
            emit("delivering_channels", attempt=attempt, channels=cfg["channels"], slot=slot.isoformat())
            results = [deliver(context, cfg, slot, db, evidence) for context in cached]
            success = all(results)
            emit("round_finished" if success else "round_needs_attention", slot=slot.isoformat())
            return 0 if success else 1
        except (Exception, SystemExit) as exc:
            emit("not_ready", reason=str(exc)[:220], error_type=type(exc).__name__, slot=slot.isoformat())
            cached = None
            if preflight:
                return 1
            wake = next_check(now(), slot, cfg)
            if wake > deadline:
                break
            emit("waiting_to_retry", attempt=attempt, reason=str(exc)[:220],
                 next_retry_at=wake.isoformat(), deadline=deadline.isoformat(), slot=slot.isoformat())
    emit("deadline_skipped", slot=slot.isoformat())
    return 1


def run_locked(cfg, preflight=False):
    with runner_lock(cfg["state_dir"]) as acquired:
        if not acquired:
            emit("another_instance_active")
            return 0
        return run(cfg, preflight)


def main(argv=None):
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None:
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--watch", action="store_true")
    modes.add_argument("--show-config", action="store_true", help="Read effective local config; no API calls")
    parser.add_argument("--confirm-send", action="store_true")
    args = parser.parse_args(argv)
    if args.watch and not args.confirm_send:
        parser.error("--watch requires --confirm-send")
    cfg = load_config(args.config)
    if args.show_config:
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
        return 0
    return run_locked(cfg, args.preflight)


if __name__ == "__main__":
    raise SystemExit(main())
