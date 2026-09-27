#!/usr/bin/env python
"""Fail-closed local broadcaster; only --watch --confirm-send opens the outlet.
Windows Task Scheduler owns wakeup; SQLite owns durable delivery claims."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

from ...common import feishu as gp
from ...core import catalog
from ...core.locks import runner_lock
from .workflow import prepare_report, prepare_weekend_dual_report, source_channel_count, source_present_channels
from .adapter import SUPERVISOR_PROFILES, policy_for, report_arguments, report_module_for
from .delivery_validation import receipt_readback, validate_weekend_dual_context
from .weekend_dual import REPORT_TYPE as WEEKEND_DUAL_REPORT_TYPE
from ...integrations import tiangong_release as rb
from .channels import self_incubated_koc_5 as bp
from . import grade_report as gr
from . import volume_report as vr
from . import volume_upstream as vu
from . import lead_upstream as lu
from .delivery_ledger import claim, connect_ledger, delivery_key
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
    slot_reports = cfg.get("slot_reports")
    routed = slot_reports is not None
    if cfg.get("timezone") != "Asia/Shanghai":
        raise ValueError("Unreviewed schedule timezone")
    if routed:
        if cfg.get("hours") != [13, 17] or slot_reports != {"13": "regular", "17": "volume"}:
            raise ValueError("Unreviewed two-slot report routing")
    elif cfg.get("hours") not in ([13, 17], [13, 17, 21]):
        raise ValueError("Unreviewed legacy schedule")
    order = cfg.get("stagger_order")
    start_minute = cfg.get("prepare_minute")
    if (type(order) is not int or order < 1 or start_minute != 20 + (order - 1) // 2
            or start_minute > 50
            or cfg.get("send_minute") != start_minute
            or cfg.get("deadline_minute") != 50 or cfg.get("retry_minutes") != 2
            or not re.fullmatch(r"Codex-Lark-[A-Za-z0-9-]+Push", cfg.get("windows_task_name", ""))):
        raise ValueError("Unreviewed retry window")
    if cfg.get("report_profile") not in {bp.PROFILE, *SUPERVISOR_PROFILES}:
        raise ValueError("Unreviewed delivery profile")
    if not cfg.get("channel_key") and (cfg.get("channels") != [bp.CHANNEL] or cfg.get("chat_id") != bp.CHAT_ID):
        raise ValueError("Unreviewed delivery scope")
    if (cfg.get("period_rule") != "natural_week_friday" or cfg.get("process_weekdays") != list(range(7))
            or cfg.get("result_weekdays") != [4, 5, 6]):
        raise ValueError("Unreviewed business-week period or weekday policy")
    volume = cfg.get("volume_report", {})
    if volume:
        if (volume.get("stage") not in {"preview_only", "scheduled"}
                or volume.get("period_rule") != "latest_available" or volume.get("grain") != "年级"
                or volume.get("channel_rule") not in vr.CHANNEL_RULE_DESCRIPTIONS):
            raise ValueError("Unreviewed volume-report policy")
        if volume.get("stage") == "scheduled":
            producer = volume.get("upstream", {})
            if (producer.get("task_name") != "market2lark_jinliang"
                    or producer.get("log_protocol") != "volume_two_period_create_then_delete_v1"
                    or not re.fullmatch(r"[0-9a-f]{64}", str(producer.get("verified_source_sha256", "")))):
                raise ValueError("Scheduled volume producer is not release-bound")
    if routed and volume.get("stage") != "scheduled":
        raise ValueError("Routed volume report must be scheduled")
    return cfg


def report_for_slot(cfg, hour):
    return cfg.get("slot_reports", {}).get(str(hour), "regular")


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
    return lu.parse_complete_log(doc, directory, cfg, slot, execution, validate_history, TZ)


def parse_volume_log(doc, directory, cfg, slot, execution):
    return vu.parse_volume_log(doc, directory, cfg, slot, execution, validate_history, TZ)


def volume_upstream_ready(cfg, slot):
    volume_cfg = {**cfg, "upstream": cfg["volume_report"]["upstream"]}
    directory = operator("list-execution-history", volume_cfg, "--limit", "12")
    history = read_json(directory / "history.json")
    execution = validate_history(history, volume_cfg, slot)
    directory = operator("fetch-execution-log", volume_cfg, "--exec-id", str(execution["id"]))
    return parse_volume_log(read_json(directory / "execution.json"), directory, volume_cfg, slot, execution)


def require_shared_periods(lead_evidence, volume_evidence):
    if sorted(volume_evidence["periods"]) != sorted((lead_evidence.get("periods") or {}).keys()):
        raise ValueError("lead and volume upstream periods disagree")


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
    if report_for_slot(cfg, slot.hour) == "volume":
        evidence["volume"] = volume_upstream_ready(cfg, slot)
        require_shared_periods(evidence, evidence["volume"])
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


def validate_context(context, evidence, cfg=None, slot=None, *, enforce_calendar=True):
    if context.get("report_type") == WEEKEND_DUAL_REPORT_TYPE:
        return validate_weekend_dual_context(context, evidence, cfg, slot, validate_context)
    policy = bp
    if cfg is not None and cfg.get("channel_key"):
        from .adapter import policy_for
        policy = policy_for(catalog.load_channel(cfg["channel_key"]))
    source_period = (evidence.get("periods") or {}).get(context["period"])
    counts = source_period["channel_counts"] if source_period else evidence["channel_counts"]
    match = (cfg or {}).get("channel_match", {})
    expected_count = source_channel_count(counts, match, context["channel"])
    period_matches = source_period is not None if evidence.get("periods") is not None else context["period"] == evidence["period"]
    if (not period_matches or context["raw_count"] != expected_count
            or str(context["snapshot"][0]) != evidence["dt"] or int(context["snapshot"][1]) != evidence["hour"]):
        raise ValueError("Base channel/period/partition/count disagrees with complete upstream write")
    if context["raw_read_audit"].get("has_more") is not False or context["raw_read_audit"].get("rev") is None:
        raise ValueError("incomplete Base snapshot")
    if context.get("report_profile") in {bp.PROFILE, *SUPERVISOR_PROFILES}:
        policy.enforce_group_scope(context["chat_id"], context["channel"], context["report_profile"])
        if cfg is not None:
            if context["chat_id"] != cfg["chat_id"] or context["identity"] != "bot":
                raise ValueError("configured group or sender mismatch")
            if enforce_calendar:
                policy.enforce_live_calendar(context["period"], context["report_type"], slot or now())
            if enforce_calendar and context["report_type"] != policy.scheduled_report_type(slot or now()):
                raise ValueError("scheduled report type does not match the weekday policy")
        if context.get("skip_delivery"):
            report = context.get("supervisor_report")
            if (context.get("report_profile") not in SUPERVISOR_PROFILES
                    or context.get("skip_reason") not in {
                        "no_supervisor_rows_meet_minimum_post_leads",
                        "no_advisor_rows_meet_minimum_post_leads",
                    }
                    or not report or report["blocks"] or context.get("markdown")
                    or context.get("image_path") or context.get("result_image_path")
                    or report["reminder_names"]):
                raise ValueError("invalid no-data skip context")
            return
        info = context["mention_info"]
        definition = catalog.load_channel(cfg["channel_key"]) if cfg is not None else None
        report_module = report_module_for(definition) if definition is not None else None
        expected_target = getattr(report_module, "MENTION_TARGET",
                                   "supervisor" if context["report_profile"] in SUPERVISOR_PROFILES else "manager")
        if context["mention_target"] != expected_target or any(info.get(k) for k in ("unresolved", "ambiguous", "lookup_error", "nonmembers")):
            raise ValueError("all lowest reminder accounts must be resolved and in the group")
        if set(info["resolved"]) != set(context["grade_report"]["reminder_names"]):
            raise ValueError("reminder account set mismatch")
        if gr.mention_ids(context["markdown"]) != set(info["resolved"].values()):
            raise ValueError("unexpected or missing manager mentions")
        report_sections = gr.sections(context["report_type"])
        if context["report_profile"] in SUPERVISOR_PROFILES:
            definition = catalog.load_channel(cfg["channel_key"])
            report_sections = report_module_for(definition).sections(context["report_type"])
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
    if context.get("report_kind") == "volume":
        vr.assert_current_revisions(context, cfg)
        return
    with tempfile.TemporaryDirectory(prefix=".broadcast-rev-") as folder:
        data = gp._unwrap(json.loads(gp.run_lark([
            "base", "+record-list", "--base-token", context["coords"]["base_token"],
            "--table-id", context["raw_table_id"], "--field-id", "lead_id", "--limit", "1",
            "--output", "./revision.ndjson", "--format", "ndjson", "--as", cfg["base_as"]], cwd=folder, timeout=60)))
    if data.get("rev") != context["raw_read_audit"]["rev"]:
        raise ValueError("Base changed after snapshot; rebuild before sending")


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
    key = delivery_key(cfg, slot, context["channel"], context.get("report_kind", "regular"))
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
    if context.get("report_kind") == "volume":
        vr.validate_scheduled_context(context, cfg)
    elif cfg.get("report_profile") == bp.PROFILE or context.get("report_profile") == bp.PROFILE:
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
    if context.get("report_profile") in {bp.PROFILE, "volume"}:
        assert_current_revision(context, cfg)
    if not claim(db, key, slot, context["channel"]):
        return False
    detail = {"upstream": evidence, "period": context["period"], "report_kind": context.get("report_kind", "regular"),
              "raw_count": context["raw_count"], "rev": context["raw_read_audit"]["rev"], "image_keys": keys}
    if context.get("report_kind") == "volume":
        detail.update(vr.delivery_detail(context))
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
                if report_for_slot(cfg, slot.hour) == "volume":
                    emit("preparing_volume_report", attempt=attempt, slot=slot.isoformat())
                    contexts = [vr.prepare_context(cfg, state / "prepared-volume")]
                else:
                    contexts = []
                    definition = catalog.load_channel(cfg.get("channel_key", catalog.DEFAULT_CHANNEL))
                    policy = policy_for(definition)
                    current_period = policy.business_period(slot)
                    selected, absent = source_present_channels(cfg, evidence, current_period)
                    if policy.scheduled_report_type(slot) == WEEKEND_DUAL_REPORT_TYPE:
                        next_period = policy.next_business_period(current_period)
                        next_selected, _ = source_present_channels(cfg, evidence, next_period)
                        selected = [channel for channel in cfg["channels"]
                                    if channel in selected or channel in next_selected]
                        absent = [channel for channel in cfg["channels"] if channel not in selected]
                    for channel in absent:
                        emit("channel_skipped_no_source_rows", channel=channel, period=current_period)
                    if not selected:
                        emit("all_channels_absent_in_upstream", period=current_period)
                        return 0
                    for channel in selected:
                        emit("preparing_channel_report", attempt=attempt, channel=channel, slot=slot.isoformat())
                        args = report_args(cfg, channel, slot)
                        context = (prepare_weekend_dual_report(args, definition)
                                   if args.report_type == WEEKEND_DUAL_REPORT_TYPE
                                   else prepare_report(args, definition))
                        emit("validating_channel_snapshot", attempt=attempt, channel=channel, slot=slot.isoformat())
                        validate_context(context, evidence, cfg, slot)
                        contexts.append(context)
                    if len({c["raw_read_audit"]["rev"] for c in contexts}) != 1:
                        raise ValueError("channels are not from the same Base revision")
                cached = contexts
            for context in cached:
                if context.get("report_kind") == "volume":
                    volume_evidence = evidence.get("volume", {})
                    if (context["period"] != max(volume_evidence.get("periods", [""]))
                            or context["raw_count"] != volume_evidence.get("total")):
                        raise ValueError("volume Base snapshot differs from bound upstream write")
                else:
                    validate_context(context, evidence, cfg, slot)
                assert_current_revision(context, cfg)
            if preflight:
                for context in cached:
                    if not context.get("skip_delivery"):
                        dry_key = context.get("idempotency_key") or delivery_key(
                            cfg, slot, context["channel"], context.get("report_kind", "regular"))
                        gp.send_markdown(cfg["chat_id"], context["markdown"], dry_key, "bot", dry_run=True, timeout=60)
                summary = {"status": "preflight_passed_no_send", "slot": slot.isoformat(), "upstream": evidence,
                            "channels": [{"channel": c["channel"], "report_kind": c.get("report_kind", "regular"),
                                          "source_channels": c.get("channels", [c["channel"]]), "period": c["period"], "rows": c["raw_count"],
                                          "delivery_status": "skipped_no_eligible_rows" if c.get("skip_delivery") else "ready",
                                          "rev": c["raw_read_audit"]["rev"], "process_image": str(c["image_path"]),
                                         "result_image": str(c["result_image_path"]),
                                         "volume_image": str(c.get("volume_image_path"))} for c in cached]}
                (state / "preflight.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                emit("preflight_passed_no_send", **{k: v for k, v in summary.items() if k != "status"})
                return 0
            if now() < slot + timedelta(minutes=cfg["send_minute"]):
                emit("prepared_waiting_for_send_time", slot=slot.isoformat())
                wake = slot + timedelta(minutes=cfg["send_minute"])
                continue
            if now() >= deadline + timedelta(minutes=1):
                break
            emit("delivering_channels", attempt=attempt,
                 channels=[context["channel"] for context in cached], slot=slot.isoformat())
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
