"""Explicit one-time send, independent of recurring enablement and time windows."""
from contextlib import closing
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re

from ...core import catalog
from ...core.locks import runner_lock
from . import scheduler as schedule
from . import adapter
from .channels import self_incubated_koc_5 as policy


def latest_upstream_slot(at):
    """Tiangong runs at 01/05/09/13/17/21; do not fall back to an older success."""
    at = at.astimezone(schedule.TZ)
    day = at.replace(hour=0, minute=0, second=0, microsecond=0)
    candidates = [day + timedelta(hours=hour) for hour in (1, 5, 9, 13, 17, 21)]
    candidates.append(day - timedelta(hours=3))
    return max(value for value in candidates if value <= at)


def request_key(cfg, request_id, channel=""):
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", request_id or ""):
        raise ValueError("An explicit stable request ID is required for a one-time send")
    scope = "|".join((cfg["channel_key"], cfg["chat_id"], cfg["bot_open_id"], request_id, channel))
    return "now-" + hashlib.sha256(scope.encode()).hexdigest()[:36]


def channel_request_key(cfg, request_id, channel):
    """Keep the deployed single-channel key while isolating multi-channel receipts."""
    return request_key(cfg, request_id, channel if len(cfg["channels"]) > 1 else "")


def require_fresh_request(started, slot, evidence, context, at):
    if not timedelta(0) <= at - started <= timedelta(minutes=10):
        raise ValueError("One-time preparation expired; no message sent")
    if latest_upstream_slot(at) != slot:
        raise ValueError("A new upstream cycle started; prepare again")
    source_at = datetime.strptime(evidence["dt"] + f"{evidence['hour']:02d}", "%Y%m%d%H").replace(tzinfo=schedule.TZ)
    if not timedelta(0) <= at - source_at <= timedelta(hours=7):
        raise ValueError("Latest verified snapshot is not fresh enough for immediate delivery")
    policy.enforce_live_calendar(context["period"], context["report_type"], at)


def verify_publication(cfg):
    reply = schedule.operator_reply("plan-task-publish", cfg)
    if reply.get("status") != "blocked_already_published" or not reply.get("source_matches_latest_published"):
        raise ValueError("Upstream source/publication is not stable")
    plan = schedule.read_json(reply["plan_file"])
    baseline = plan["baseline"]
    if (plan["plan_sha256"] != reply["plan_sha256"]
            or baseline["current_source_sha256"] != cfg["upstream"]["verified_source_sha256"]
            or baseline["latest_published_version_id"] != cfg["upstream"]["verified_version_id"]):
        raise ValueError("Upstream publication differs from its approved source/version pin")
    return {"plan_file": reply["plan_file"], "plan_sha256": reply["plan_sha256"]}


def run(definition, target, request_id, *, preflight=False):
    cfg = catalog.schedule_config(definition, target)
    schedule.validate_config(cfg)
    state = Path(cfg["state_dir"])
    with runner_lock(state) as acquired:
        if not acquired:
            raise ValueError("Another broadcast instance owns this target")
        with closing(schedule.connect_ledger(state)) as db:
            keys = [channel_request_key(cfg, request_id, channel) for channel in cfg["channels"]]
            priors = [db.execute("SELECT status,message_id FROM deliveries WHERE key=?", (key,)).fetchone() for key in keys]
            if all(priors):
                for channel, prior in zip(cfg["channels"], priors):
                    schedule.emit("immediate_duplicate_suppressed", channel=channel, status=prior[0],
                                  message_id=prior[1], request_id=request_id)
                return 0 if all(prior[0] == "sent_verified" for prior in priors) else 1
            started = schedule.now()
            slot = latest_upstream_slot(started)
            schedule.verify_bot(cfg)
            publication = verify_publication(cfg)
            evidence = schedule.upstream_ready(cfg, slot)
            evidence.update(mode="immediate", request_id=request_id, publication=publication)
            contexts = []
            for index, channel in enumerate(cfg["channels"], start=1):
                context = adapter.prepare(definition, target, channel=channel,
                    state_dir=state / "immediate" / request_id / f"channel-{index}")
                schedule.validate_context(context, evidence, cfg, slot)
                require_fresh_request(started, slot, evidence, context, schedule.now())
                schedule.assert_current_revision(context, cfg)
                contexts.append(context)
            if len({context["raw_read_audit"]["rev"] for context in contexts}) != 1:
                raise ValueError("channels are not from the same Base revision")
            items = [{"channel": context["channel"], "key": channel_request_key(cfg, request_id, context["channel"]),
                      "period": context["period"], "report_type": context["report_type"],
                      "raw_count": context["raw_count"], "snapshot": context["snapshot"],
                      "mentions": sorted(context["mention_info"]["resolved"]),
                      "preview": adapter.write_preview(context)} for context in contexts]
            summary = {"request_id": request_id, "chat_id": cfg["chat_id"],
                       "chat_name": contexts[0]["chat_name"], "upstream": evidence, "channels": items}
            output = state / "immediate" / request_id / ("preflight.json" if preflight else "send-summary.json")
            if preflight:
                for context, item in zip(contexts, items):
                    schedule.gp.send_markdown(cfg["chat_id"], context["markdown"], item["key"], "bot", dry_run=True, timeout=60)
                summary["status"] = "immediate_preflight_passed_no_send"
                output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                schedule.emit(summary["status"], **{k: v for k, v in summary.items() if k != "status"})
                return 0

            def guard(context):
                require_fresh_request(started, slot, evidence, context, schedule.now())
                directory = schedule.operator("list-execution-history", cfg, "--limit", "12")
                latest = schedule.validate_history(schedule.read_json(directory / "history.json"), cfg, slot)
                if latest["id"] != evidence["execution_id"]:
                    raise ValueError("Upstream execution changed during one-time preparation")

            results = []
            for context, item in zip(contexts, items):
                prior = db.execute("SELECT status,message_id FROM deliveries WHERE key=?", (item["key"],)).fetchone()
                if prior:
                    schedule.emit("immediate_duplicate_suppressed", channel=context["channel"],
                                  status=prior[0], message_id=prior[1], request_id=request_id)
                    ok = prior[0] == "sent_verified"
                else:
                    ok = schedule._deliver_verified(context, cfg, slot, db, evidence, key=item["key"],
                        time_guard=lambda current=context: guard(current))
                row = db.execute("SELECT status,message_id,detail FROM deliveries WHERE key=?", (item["key"],)).fetchone()
                item.update(status=row[0] if row else "not_sent", message_id=row[1] if row else "",
                            receipt=json.loads(row[2]) if row else {})
                results.append(ok)
            summary["status"] = "sent_verified" if all(results) else "partial_or_failed"
            output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            schedule.emit("immediate_finished", status=summary["status"], channels=len(items), artifact=str(output))
            return 0 if all(results) else 1
