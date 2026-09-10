#!/usr/bin/env python
"""Fail-closed, four-slot local broadcaster. No upstream or Base mutations.

Only --watch --confirm-send opens the message outlet. Preflight is read-only.
Windows Task Scheduler owns wakeup; SQLite owns durable per-slot delivery claims.
"""
from __future__ import annotations

import argparse
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

import group_push as gp
import release_binding as rb

TZ = timezone(timedelta(hours=8))
SKILLS = Path(__file__).resolve().parents[2]
OPERATOR = SKILLS / "usql-web-query-operator/scripts/tiangong2_task.py"
DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config/scheduled_push.json"


def now():
    return datetime.now(TZ)


def emit(event, **fields):
    print(json.dumps({"at": now().isoformat(), "event": event, **fields}, ensure_ascii=False), flush=True)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_config(path):
    cfg = read_json(path)
    if cfg.get("hours") != [9, 13, 17, 21] or cfg.get("timezone") != "Asia/Shanghai":
        raise ValueError("Unreviewed schedule; expected four China-time slots")
    if (cfg.get("prepare_minute"), cfg.get("send_minute"), cfg.get("deadline_minute"), cfg.get("retry_minutes")) != (15, 20, 50, 2):
        raise ValueError("Unreviewed retry window")
    if cfg.get("channels") != ["KOC-周帅数学", "KOC-孟亚飞数学"] or cfg.get("chat_id") != "oc_b9dc09ba622ca00059bbc472922a803d":
        raise ValueError("Unreviewed delivery scope")
    return cfg


def active_slot(at, cfg, preflight=False):
    at = at.astimezone(TZ)
    if at.hour not in cfg["hours"]:
        return None
    slot = at.replace(minute=0, second=0, microsecond=0)
    if not preflight and not (slot + timedelta(minutes=15) <= at < slot + timedelta(minutes=51)):
        return None
    if slot + timedelta(minutes=20) < datetime.fromisoformat(cfg["first_send_at"]):
        return None
    return slot


def next_check(at, slot):
    start = slot + timedelta(minutes=20)
    if at < start:
        return start
    n = math.floor((at - start).total_seconds() / 120) + 1
    return start + timedelta(minutes=2 * n)


def require_send_window(slot):
    if not slot + timedelta(minutes=20) <= now() < slot + timedelta(minutes=51):
        raise ValueError("message outlet is outside the authorized :20-:50 window")


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
    if "目标多维表格校验通过：table_id=" + gp.push_defaults()["raw_table_id"] not in log:
        raise ValueError("upstream Base destination changed")
    policy = rb.active_policy(cfg, slot)
    if policy:
        rb.verify_raw_only_log(log, policy, period)
    return {"execution_id": execution["id"], "period": period, "dt": dt, "hour": int(hour),
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


def report_args(cfg, channel):
    parser = argparse.ArgumentParser()
    gp.add_common_arguments(parser)
    return parser.parse_args(["--channel", channel, "--report-type", "both", "--as", "bot",
                             "--base-as", cfg["base_as"], "--chat-id", cfg["chat_id"],
                             "--chat-name", cfg["chat_name"], "--no-mentions", "--period", "",
                             "--state-dir", cfg["state_dir"], "--timeout", "60"])


def validate_context(context, evidence):
    if (context["period"] != evidence["period"] or context["raw_count"] != evidence["channel_counts"].get(context["channel"])
            or str(context["snapshot"][0]) != evidence["dt"] or int(context["snapshot"][1]) != evidence["hour"]):
        raise ValueError("Base channel/period/partition/count disagrees with complete upstream write")
    if context["raw_read_audit"].get("has_more") is not False or context["raw_read_audit"].get("rev") is None:
        raise ValueError("incomplete Base snapshot")
    if context["mention_target"] != "none" or re.search(r"<at\b|<mention\b", context["markdown"], re.I):
        raise ValueError("mentions are forbidden")
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
    return hashlib.sha256((cfg["chat_id"] + "|" + slot.isoformat() + "|" + channel + "|both|bot").encode()).hexdigest()[:40]


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
    if re.search(r"<at\b|<mention\b", text, re.I):
        raise ValueError("unexpected mention in delivered message")
    if msg.get("chat_id") and msg["chat_id"] != cfg["chat_id"]:
        raise ValueError("message readback target mismatch")
    sender = msg.get("sender", {})
    if sender.get("name") and sender["name"] != cfg["bot_name"]:
        raise ValueError("message readback sender mismatch")
    return {"message_id": message_id, "verified": True, "sender": sender,
            "image_count": len(image_keys), "contains_mentions": False}


def deliver(context, cfg, slot, db, evidence):
    key = delivery_key(cfg, slot, context["channel"])
    prior = db.execute("SELECT status,message_id FROM deliveries WHERE key=?", (key,)).fetchone()
    if prior:
        emit("duplicate_suppressed", channel=context["channel"], status=prior[0], message_id=prior[1])
        return prior[0] == "sent_verified"
    require_send_window(slot)
    assert_current_revision(context, cfg)
    markdown = context["markdown"]
    keys = {}
    # Upload failure is retryable; it cannot create a visible message.
    for section, path, refs in gp._image_slots(context):
        image_key = gp.upload_image(path, "bot", 60)
        keys[section] = image_key
        for ref in refs:
            markdown = markdown.replace("](%s)" % ref, "](%s)" % image_key)
    # A slow upload or the preceding channel must not carry this send past cutoff.
    require_send_window(slot)
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
    detail["image_cleanup"] = {section: gp._cleanup_local_image(path) for section, path, refs in gp._image_slots(context)}
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
    if not cfg.get("enabled") or slot is None:
        emit("outside_authorized_window")
        return 0
    state = Path(cfg["state_dir"])
    db = connect_ledger(state)
    cached = None
    wake = now()
    while now() < slot + timedelta(minutes=51):
        while now() < wake:
            time.sleep(min(20, max(0.01, (wake - now()).total_seconds())))
        try:
            verify_bot(cfg)
            evidence = upstream_ready(cfg, slot)
            if cached is None:
                contexts = []
                for channel in cfg["channels"]:
                    context = gp.prepare(report_args(cfg, channel))
                    validate_context(context, evidence)
                    contexts.append(context)
                if len({c["raw_read_audit"]["rev"] for c in contexts}) != 1:
                    raise ValueError("channels are not from the same Base revision")
                cached = contexts
            for context in cached:
                validate_context(context, evidence)
                assert_current_revision(context, cfg)
            if preflight:
                for context in cached:
                    gp.send_markdown(cfg["chat_id"], context["markdown"], context["idempotency_key"], "bot", dry_run=True, timeout=60)
                summary = {"status": "preflight_passed_no_send", "slot": slot.isoformat(), "upstream": evidence,
                           "channels": [{"channel": c["channel"], "period": c["period"], "rows": c["raw_count"],
                                         "rev": c["raw_read_audit"]["rev"], "process_image": str(c["image_path"]),
                                         "result_image": str(c["result_image_path"])} for c in cached]}
                (state / "preflight.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                emit("preflight_passed_no_send", **{k: v for k, v in summary.items() if k != "status"})
                return 0
            if now() < slot + timedelta(minutes=20):
                emit("prepared_waiting_for_send_time", slot=slot.isoformat())
                wake = slot + timedelta(minutes=20)
                continue
            if now() >= slot + timedelta(minutes=51):
                break
            results = [deliver(context, cfg, slot, db, evidence) for context in cached]
            success = all(results)
            emit("round_finished" if success else "round_needs_attention", slot=slot.isoformat())
            return 0 if success else 1
        except (Exception, SystemExit) as exc:
            emit("not_ready", reason=str(exc)[:220], error_type=type(exc).__name__, slot=slot.isoformat())
            cached = None
            if preflight:
                return 1
            wake = next_check(now(), slot)
            if wake > slot + timedelta(minutes=50):
                break
    emit("deadline_skipped", slot=slot.isoformat())
    return 1


def main():
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None:
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--watch", action="store_true")
    parser.add_argument("--confirm-send", action="store_true")
    args = parser.parse_args()
    if args.watch and not args.confirm_send:
        parser.error("--watch requires --confirm-send")
    cfg = load_config(args.config)
    state = Path(cfg["state_dir"])
    state.mkdir(parents=True, exist_ok=True)
    # OS-owned lock releases on exit/crash; never steal an age-based lock file.
    with (state / "runner.lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            lock.seek(0)
            if not lock.read(1):
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                emit("another_instance_active")
                return 0
        return run(cfg, args.preflight)


if __name__ == "__main__":
    raise SystemExit(main())
