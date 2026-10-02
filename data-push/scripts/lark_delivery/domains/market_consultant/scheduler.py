#!/usr/bin/env python
"""Fail-closed local broadcaster; only --watch --confirm-send opens the outlet.
Windows Task Scheduler owns wakeup; SQLite owns durable delivery claims."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta

from ...common import feishu as gp
from ...common import push_log
from ...common import resend
from ...common.readback import available as readback_available
from ...core import catalog
from ...core.locks import runner_lock
from .workflow import prepare_report, prepare_weekend_dual_report, source_present_channels
from .adapter import SUPERVISOR_PROFILES, policy_for
from .delivery_gate import reverify_unverified_delivery
from .delivery_validation import receipt_readback
from .delivery_ledger import claim, connect_ledger, delivery_key, record_outcome
from .reporting import assert_current_revision, report_args, validate_context
from .weekend_dual import REPORT_TYPE as WEEKEND_DUAL_REPORT_TYPE
from .upstream import parse_complete_log, parse_volume_log, read_json, require_shared_periods, validate_history, verify_bot
from .window import TZ, active_slot, next_check, report_for_slot
from ...integrations import tiangong_release as rb
from .channels import self_incubated_koc_5 as bp
from . import volume_report as vr
from ...paths import SKILL_ROOT, SKILLS_ROOT

SKILLS = SKILLS_ROOT
OPERATOR = SKILLS / "usql-web-query-operator/scripts/tiangong2_task.py"
DEFAULT_CONFIG = SKILL_ROOT / "config/scheduled_push.json"
_LIVE_STATUS_PATH = ContextVar("data_push_live_status_path", default=None)
_RUN_LOG = ContextVar("data_push_run_log", default=None)


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
    run_log = _RUN_LOG.get()
    if run_log is not None:
        try:
            run_log.event(payload)
        except Exception:  # noqa: BLE001 - an external log write must never break a push
            pass
    print(json.dumps(payload, ensure_ascii=False, default=str), flush=True)


def record_channel(db, slot, channel, status, reason="", **extra):
    """Emit one channel's verdict, durably and to the external run log.

    The ledger table is append-only and keyed for observability only, so it can
    never suppress a later real send the way a ``deliveries`` row would.
    """
    emit(push_log.OUTCOME_EVENT, channel=channel, status=status, reason=reason, slot=slot.isoformat(), **extra)
    if db is None:
        return
    try:
        record_outcome(db, now().isoformat(), slot, channel, status, reason)
    except Exception:  # noqa: BLE001 - observability never fails a delivery round
        pass


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


def volume_upstream_ready(cfg, slot):
    volume_cfg = {**cfg, "upstream": cfg["volume_report"]["upstream"]}
    directory = operator("list-execution-history", volume_cfg, "--limit", "12")
    history = read_json(directory / "history.json")
    execution = validate_history(history, volume_cfg, slot)
    directory = operator("fetch-execution-log", volume_cfg, "--exec-id", str(execution["id"]))
    return parse_volume_log(read_json(directory / "execution.json"), directory, volume_cfg, slot, execution)


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




def deliver(context, cfg, slot, db, evidence):
    if context.get("skip_delivery"):
        record_channel(db, slot, context["channel"], "skipped_no_eligible_rows",
                       context.get("skip_reason", ""), period=context["period"])
        return True
    key = delivery_key(cfg, slot, context["channel"], context.get("report_kind", "regular"))
    return _deliver_verified(context, cfg, slot, db, evidence, key=key,
                             time_guard=lambda: require_send_window(slot, cfg))


def _reverify_sent_message(db, key, cfg, context, slot, prior):
    """Redo the readback of a message that is already in the group.

    This path never calls the send outlet, so re-running it cannot duplicate a
    message. A still-failing readback stays ``readback_failed`` rather than
    re-sending: the message is in the group either way, and publishing a second
    copy to fix a bookkeeping error would be worse than the bookkeeping error.
    """
    try:
        reverify_unverified_delivery(db, key, cfg, context)
    except Exception as exc:
        if not readback_available(cfg, cfg.get("chat_id")):
            record_channel(db, slot, context["channel"], resend.UNVERIFIABLE,
                           "消息已确认写入，该群内容不可回读，验证不可能：按可接受终态处理",
                           message_id=prior[1], key=key)
            return True
        record_channel(db, slot, context["channel"], "readback_failed",
                       "消息已在群内但回读未通过：" + type(exc).__name__,
                       message_id=prior[1], key=key)
        return False
    record_channel(db, slot, context["channel"], "sent_verified",
                   "消息已在群内，补回读校验通过", message_id=prior[1], key=key)
    return True


def _deliver_verified(context, cfg, slot, db, evidence, *, key, time_guard):
    """Shared outlet; each authorized caller must supply its own real-time guard."""
    if context.get("skip_delivery"):
        record_channel(db, slot, context["channel"], "skipped_no_eligible_rows",
                       context.get("skip_reason", ""), period=context["period"])
        return True
    prior = db.execute("SELECT status,message_id FROM deliveries WHERE key=?", (key,)).fetchone()
    # The availability question is asked only when a prior row raises it, so a first
    # attempt costs no extra API call. A group whose content cannot be read back at all
    # treats a recorded message id as a completed delivery, not as something to keep
    # re-verifying or re-issuing.
    verdict = (resend.decide(prior[0], prior[1],
                             readback_available=readback_available(cfg, cfg.get("chat_id")))
               if prior else resend.RESEND)
    if verdict == resend.DONE:
        record_channel(db, slot, context["channel"], "duplicate_suppressed",
                       "该时段该渠道已有投递记录，未重复发送", prior_status=prior[0], message_id=prior[1])
        return True
    if verdict == resend.UNVERIFIABLE:
        record_channel(db, slot, context["channel"], resend.UNVERIFIABLE,
                       "消息已确认写入，该群内容不可回读，验证不可能：按可接受终态处理",
                       prior_status=prior[0], message_id=prior[1], key=key)
        return True
    if verdict == resend.REVERIFY:
        return _reverify_sent_message(db, key, cfg, context, slot, prior)
    if prior:
        # Re-issue with the SAME idempotency key. The platform dedupes, so this is
        # safe even if the earlier attempt did reach the group -- and if it did, the
        # returned message id lets the readback verify, so the slot converges.
        record_channel(db, slot, context["channel"], "resending_after_uncertain",
                       "上一轮未确认送达，用同一幂等键重发", prior_status=prior[0], key=key)
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
    # Only a first attempt claims the key; a re-issue already owns the row, and
    # `claim` is INSERT OR IGNORE, so re-claiming would block the send it just allowed.
    if prior is None and not claim(db, key, slot, context["channel"]):
        return False
    detail = {"upstream": evidence, "period": context["period"], "report_kind": context.get("report_kind", "regular"),
              "raw_count": context["raw_count"], "rev": context["raw_read_audit"]["rev"], "image_keys": keys,
              # Full read audit: carries the reviewed duplicate-lead_id merge evidence.
              "raw_read_audit": context["raw_read_audit"]}
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
        record_channel(db, slot, context["channel"], "uncertain",
                       "发送已尝试但未拿到回执，消息可能已进群，需人工核对：" + type(exc).__name__, key=key)
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
        if readback_available(cfg, cfg.get("chat_id")):
            status = "sent_unverified"
            detail["readback_error_type"] = type(exc).__name__
        else:
            # Unreadable group: the write was acknowledged, verification is impossible by
            # policy, and reporting a failure here would be a false alarm on every push.
            status = resend.UNVERIFIABLE
            detail["readback_error"] = str(exc)
    db.execute("UPDATE deliveries SET status=?,detail=? WHERE key=?", (status, json.dumps(detail, ensure_ascii=False), key))
    db.commit()
    record_channel(db, slot, context["channel"], status,
                   detail.get("readback_error_type", ""), message_id=message_id,
                   image_cleanup=detail["image_cleanup"])
    return status in ("sent_verified", resend.UNVERIFIABLE)


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


def rev_consensus(contexts):
    """Split prepared contexts into the consistent majority and the deviants.

    Every channel in one group must describe the same Base snapshot, so a
    channel whose read disagrees is not safe to send next to the others. The
    former behaviour aborted the whole round; the group is now held to the
    revision shared by the most channels (the first prepared channel breaks a
    tie) and only the deviants are dropped.
    """
    grouped = {}
    for context in contexts:
        grouped.setdefault(context["raw_read_audit"]["rev"], []).append(context)
    if len(grouped) < 2:
        return list(contexts), []
    top = max(len(items) for items in grouped.values())
    winners = [rev for rev, items in grouped.items() if len(items) == top]
    keep = contexts[0]["raw_read_audit"]["rev"] if len(winners) > 1 else winners[0]
    agreed = [c for c in contexts if c["raw_read_audit"]["rev"] == keep]
    deviant = [c for c in contexts if c["raw_read_audit"]["rev"] != keep]
    return agreed, deviant


def run_slot(cfg, preflight, slot, state, db):
    """One slot's retry loop, isolated per channel.

    Any single channel's failure — prepare, snapshot validation, revision
    drift or the send itself — must not deny the other channels their message.
    The shared, immutable gates stay global: bot identity and the pinned
    upstream release are still verified once per attempt, and every prepared
    channel still has to agree on one Base revision.
    """
    cached = []
    pending = None
    blocked = {}
    selected = None
    absent = []
    wake = now()
    attempt = 0
    deadline = slot + timedelta(minutes=cfg["deadline_minute"])
    is_volume = report_for_slot(cfg, slot.hour) == "volume"
    definition = None if is_volume else catalog.load_channel(cfg.get("channel_key", catalog.DEFAULT_CHANNEL))
    while now() < deadline + timedelta(minutes=1):
        while now() < wake:
            time.sleep(min(20, max(0.01, (wake - now()).total_seconds())))
        try:
            attempt += 1
            emit("checking_bot_identity", attempt=attempt, slot=slot.isoformat())
            verify_bot(cfg)
            emit("checking_upstream", attempt=attempt, slot=slot.isoformat())
            evidence = upstream_ready(cfg, slot)
            if pending is None:
                if is_volume:
                    emit("preparing_volume_report", attempt=attempt, slot=slot.isoformat())
                    selected = [vr.VOLUME_CHANNEL]
                else:
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
                        record_channel(db, slot, channel, "skipped_no_source_rows",
                                       "本期上游渠道清单中该渠道为0行")
                    if not selected:
                        emit("all_channels_absent_in_upstream", period=current_period)
                        return 0
                pending = list(selected)

            retry = []
            for channel in pending:
                try:
                    emit("preparing_channel_report", attempt=attempt, channel=channel, slot=slot.isoformat())
                    if is_volume:
                        context = vr.prepare_context(cfg, state / "prepared-volume")
                    else:
                        args = report_args(cfg, channel, slot)
                        context = (prepare_weekend_dual_report(args, definition)
                                   if args.report_type == WEEKEND_DUAL_REPORT_TYPE
                                   else prepare_report(args, definition))
                        emit("validating_channel_snapshot", attempt=attempt, channel=channel, slot=slot.isoformat())
                        validate_context(context, evidence, cfg, slot)
                except (Exception, SystemExit) as exc:
                    reason = "%s: %s" % (type(exc).__name__, str(exc)[:200])
                    blocked[channel] = {"status": "blocked_prepare", "reason": reason}
                    record_channel(db, slot, channel, "blocked_prepare", reason)
                    retry.append(channel)
                    continue
                cached.append(context)
                blocked.pop(channel, None)
            pending = retry

            if len(cached) > 1:
                agreed, deviant = rev_consensus(cached)
                for context in deviant:
                    reason = "同一群内渠道 Base 版本不一致，已隔离该渠道"
                    blocked[context["channel"]] = {"status": "blocked_revision", "reason": reason}
                    record_channel(db, slot, context["channel"], "blocked_revision", reason)
                    pending.append(context["channel"])
                cached = agreed

            deliverable = []
            for context in cached:
                channel = context["channel"]
                try:
                    if context.get("report_kind") == "volume":
                        volume_evidence = evidence.get("volume", {})
                        if (context["period"] != max(volume_evidence.get("periods", [""]))
                                or context["raw_count"] != volume_evidence.get("total")):
                            raise ValueError("volume Base snapshot differs from bound upstream write")
                    else:
                        validate_context(context, evidence, cfg, slot)
                    assert_current_revision(context, cfg)
                except (Exception, SystemExit) as exc:
                    reason = "%s: %s" % (type(exc).__name__, str(exc)[:200])
                    blocked[channel] = {"status": "blocked_snapshot", "reason": reason}
                    record_channel(db, slot, channel, "blocked_snapshot", reason)
                    pending.append(channel)
                    continue
                deliverable.append(context)
            cached = deliverable

            if preflight:
                failures = []
                for context in cached:
                    channel = context["channel"]
                    if context.get("skip_delivery"):
                        record_channel(db, slot, channel, "skipped_no_eligible_rows",
                                       context.get("skip_reason", ""))
                        continue
                    try:
                        dry_key = context.get("idempotency_key") or delivery_key(
                            cfg, slot, channel, context.get("report_kind", "regular"))
                        gp.send_markdown(cfg["chat_id"], context["markdown"], dry_key, "bot", dry_run=True, timeout=60)
                    except (Exception, SystemExit) as exc:
                        failures.append(channel)
                        record_channel(db, slot, channel, "blocked_preflight",
                                       "%s: %s" % (type(exc).__name__, str(exc)[:200]))
                        continue
                    record_channel(db, slot, channel, "preflight_ready")
                clean = not failures and not pending
                summary = {"status": "preflight_passed_no_send" if clean else "preflight_incomplete",
                           "slot": slot.isoformat(), "upstream": evidence,
                           "blocked": blocked, "pending": pending, "absent": absent,
                           "channels": [{"channel": c["channel"], "report_kind": c.get("report_kind", "regular"),
                                         "source_channels": c.get("channels", [c["channel"]]), "period": c["period"], "rows": c["raw_count"],
                                         "delivery_status": "skipped_no_eligible_rows" if c.get("skip_delivery") else "ready",
                                         "rev": c["raw_read_audit"]["rev"], "process_image": str(c["image_path"]),
                                         "result_image": str(c["result_image_path"]),
                                         "volume_image": str(c.get("volume_image_path"))} for c in cached]}
                (state / "preflight.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                emit(summary["status"], **{k: v for k, v in summary.items() if k != "status"})
                return 0 if clean else 1

            if not cached:
                raise ValueError("本轮没有任何渠道就绪:" + json.dumps(blocked, ensure_ascii=False)[:160])
            if now() < slot + timedelta(minutes=cfg["send_minute"]):
                emit("prepared_waiting_for_send_time", slot=slot.isoformat())
                wake = slot + timedelta(minutes=cfg["send_minute"])
                continue
            if now() >= deadline + timedelta(minutes=1):
                break
            emit("delivering_channels", attempt=attempt,
                 channels=[context["channel"] for context in cached], slot=slot.isoformat())
            failed = []
            for context in cached:
                channel = context["channel"]
                try:
                    result = deliver(context, cfg, slot, db, evidence)
                except (Exception, SystemExit) as exc:
                    reason = "%s: %s" % (type(exc).__name__, str(exc)[:200])
                    blocked[channel] = {"status": "blocked_delivery", "reason": reason}
                    record_channel(db, slot, channel, "blocked_delivery", reason)
                    pending.append(channel)
                    failed.append(channel)
                    continue
                if result:
                    blocked.pop(channel, None)
                else:
                    failed.append(channel)
            cached = []
            if not failed and not pending:
                emit("round_finished", slot=slot.isoformat())
                return 0
            emit("round_needs_attention", slot=slot.isoformat(), channels=failed, blocked=sorted(blocked))
            if not pending:
                return 1
            wake = next_check(now(), slot, cfg)
            if wake > deadline:
                break
            continue
        except (Exception, SystemExit) as exc:
            emit("not_ready", reason=str(exc)[:220], error_type=type(exc).__name__, slot=slot.isoformat())
            done = {context["channel"] for context in cached}
            pending = None if selected is None else [channel for channel in selected if channel not in done]
            if preflight:
                return 1
            wake = next_check(now(), slot, cfg)
            if wake > deadline:
                break
            emit("waiting_to_retry", attempt=attempt, reason=str(exc)[:220],
                 next_retry_at=wake.isoformat(), deadline=deadline.isoformat(), slot=slot.isoformat())
    emit("deadline_skipped", slot=slot.isoformat(), blocked=blocked, pending=pending)
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
    # One external log per process run, so a silent skip or a blocked retry
    # loop is still explainable after the fact. Opening it never blocks a push.
    started = now()
    run_log = push_log.open_run_log(str(cfg.get("channel_key") or catalog.DEFAULT_CHANNEL).rsplit("/", 1)[-1],
                                    str(cfg.get("windows_task_name") or "unknown-task"), started)
    token = _RUN_LOG.set(run_log)
    code = 1
    try:
        code = run_locked(cfg, args.preflight)
    finally:
        _RUN_LOG.reset(token)
        if run_log is not None:
            try:
                run_log.finish(code, now())
            except Exception:  # noqa: BLE001 - a log write must never change the exit code
                pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
