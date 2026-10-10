"""Explicit one-time send, independent of recurring enablement and time windows."""
from contextlib import closing
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re

from ...common import resend
from ...core import catalog
from ...core.locks import runner_lock
from . import scheduler as schedule
from . import adapter
from . import volume_report as vr
from .workflow import source_present_channels
from .adapter import policy_for
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


def require_fresh_request(started, slot, evidence, context, at, *, allow_expired=False, volume=False, cfg=None):
    if not timedelta(0) <= at - started <= timedelta(minutes=10):
        raise ValueError("One-time preparation expired; no message sent")
    if allow_expired:
        if at <= slot + timedelta(minutes=50):
            raise ValueError("Expired-batch backfill is allowed only after the scheduled deadline")
        if at > slot + timedelta(hours=4):
            raise ValueError("Expired-batch backfill window elapsed")
    elif latest_upstream_slot(at) != slot:
        raise ValueError("A new upstream cycle started; prepare again")
    source_at = datetime.strptime(evidence["dt"] + f"{evidence['hour']:02d}", "%Y%m%d%H").replace(tzinfo=schedule.TZ)
    if not timedelta(0) <= at - source_at <= timedelta(hours=7):
        raise ValueError("Latest verified snapshot is not fresh enough for immediate delivery")
    if volume:
        volume_evidence = evidence.get("volume")
        if (not volume_evidence or volume_evidence["dt"] != evidence["dt"]
                or volume_evidence["hour"] != evidence["hour"]
                or context["period"] != max(volume_evidence["periods"])
                or context["raw_count"] != volume_evidence["total"]):
            raise ValueError("Volume Base snapshot differs from the latest verified upstream write")
        return
    channel_policy = policy
    if cfg and cfg.get("channel_key"):
        channel_policy = policy_for(catalog.load_channel(cfg["channel_key"]))
    channel_policy.enforce_live_calendar(context["period"], context["report_type"], at)


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


def run(definition, target, request_id, *, preflight=False, requested_slot=None, allow_expired=False,
        volume=False):
    cfg = catalog.schedule_config(definition, target)
    schedule.validate_config(cfg)
    if volume and (requested_slot is not None or allow_expired or cfg.get("volume_report", {}).get("stage") != "scheduled"):
        raise ValueError("One-time volume delivery requires the current scheduled volume producer")
    state = Path(cfg["state_dir"])
    with runner_lock(state) as acquired:
        if not acquired:
            raise ValueError("Another broadcast instance owns this target")
        with closing(schedule.connect_ledger(state)) as db:
            channels = ["KOC渠道进量"] if volume else cfg["channels"]
            keys = ([request_key(cfg, request_id, "volume")] if volume else
                    [channel_request_key(cfg, request_id, channel) for channel in channels])
            priors = [db.execute("SELECT status,message_id FROM deliveries WHERE key=?", (key,)).fetchone() for key in keys]
            # Short-circuit only when every key is already settled. A request whose
            # earlier attempt was never confirmed falls through to the per-channel
            # loop, which re-issues it with the same key (the platform dedupes).
            if all(priors) and all(resend.decide(prior[0], prior[1]) == resend.DONE for prior in priors):
                for channel, prior in zip(channels, priors):
                    schedule.emit("immediate_duplicate_suppressed", channel=channel, status=prior[0],
                                  message_id=prior[1], request_id=request_id)
                return 0
            started = schedule.now()
            slot = requested_slot or latest_upstream_slot(started)
            if requested_slot is not None:
                if requested_slot.tzinfo is None:
                    raise ValueError("Backfill slot must include a timezone")
                requested_slot = requested_slot.astimezone(schedule.TZ).replace(second=0, microsecond=0)
                if requested_slot.minute != 0 or requested_slot.hour not in cfg["hours"]:
                    raise ValueError("Backfill slot is not a registered scheduled hour")
                slot = requested_slot
                if not allow_expired:
                    raise ValueError("A requested historical slot requires the explicit backfill command")
            schedule.verify_bot(cfg)
            publication = dict(verify_publication(cfg))
            effective_cfg = ({**cfg, "slot_reports": {**cfg.get("slot_reports", {}), str(slot.hour): "volume"}}
                             if volume else cfg)
            if volume:
                volume_cfg = {**cfg, "upstream": cfg["volume_report"]["upstream"]}
                publication["volume"] = verify_publication(volume_cfg)
            evidence = schedule.upstream_ready(effective_cfg, slot)
            evidence.update(mode="volume_immediate" if volume else "backfill" if allow_expired else "immediate",
                            request_id=request_id, publication=publication)
            if volume:
                selected, absent = channels, []
            else:
                channel_policy = policy_for(definition)
                current_period = channel_policy.business_period(slot)
                selected, absent = source_present_channels(cfg, evidence, current_period)
                if channel_policy.scheduled_report_type(slot) == schedule.WEEKEND_DUAL_REPORT_TYPE:
                    next_period = channel_policy.next_business_period(current_period)
                    next_selected, _ = source_present_channels(cfg, evidence, next_period)
                    selected = [channel for channel in cfg["channels"]
                                if channel in selected or channel in next_selected]
                    absent = [channel for channel in cfg["channels"] if channel not in selected]
                from .app_sequence import delegated_channels
                selected = delegated_channels(cfg, selected)
                for channel in absent:
                    schedule.emit("channel_skipped_no_source_rows", channel=channel, period=current_period)
                if not selected:
                    schedule.emit("all_channels_absent_in_upstream", period=current_period)
                    return 0
            contexts = []
            for channel in selected:
                if volume:
                    context = vr.prepare_context(cfg, state / "immediate" / request_id / "volume")
                    vr.validate_scheduled_context(context, cfg)
                else:
                    index = cfg["channels"].index(channel) + 1
                    context = adapter.prepare(definition, target, channel=channel,
                        state_dir=state / "immediate" / request_id / f"channel-{index}", slot=slot)
                    schedule.validate_context(context, evidence, cfg, slot)
                require_fresh_request(started, slot, evidence, context, schedule.now(),
                                      allow_expired=allow_expired, volume=volume, cfg=cfg)
                schedule.assert_current_revision(context, cfg)
                contexts.append(context)
            if len({context["raw_read_audit"]["rev"] for context in contexts}) != 1:
                raise ValueError("channels are not from the same Base revision")
            items = []
            for context in contexts:
                item = {"channel": context["channel"],
                        "key": keys[0] if volume else channel_request_key(cfg, request_id, context["channel"]),
                        "period": context["period"], "raw_count": context["raw_count"],
                        "delivery_status": "skipped_no_eligible_rows" if context.get("skip_delivery") else "ready",
                        "mentions": sorted(context["mention_info"]["resolved"])}
                if volume:
                    item.update(report_kind="volume", snapshot=[evidence["volume"]["dt"], evidence["volume"]["hour"]],
                                preview={"image_file": str(context["volume_image_path"]),
                                         "markdown": context["markdown"], "rows": context["rows"]})
                else:
                    item.update(report_type=context["report_type"], snapshot=context["snapshot"],
                                preview=adapter.write_preview(context))
                items.append(item)
            summary = {"request_id": request_id, "chat_id": cfg["chat_id"],
                       "chat_name": cfg["chat_name"], "upstream": evidence, "channels": items}
            output = state / "immediate" / request_id / ("preflight.json" if preflight else "send-summary.json")
            output.parent.mkdir(parents=True, exist_ok=True)
            if preflight:
                for context, item in zip(contexts, items):
                    if not context.get("skip_delivery"):
                        schedule.gp.send_markdown(cfg["chat_id"], context["markdown"], item["key"], "bot", dry_run=True, timeout=60)
                summary["status"] = "immediate_preflight_passed_no_send"
                output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                schedule.emit(summary["status"], **{k: v for k, v in summary.items() if k != "status"})
                return 0

            def guard(context):
                require_fresh_request(started, slot, evidence, context, schedule.now(),
                                      allow_expired=allow_expired, volume=volume, cfg=cfg)
                directory = schedule.operator("list-execution-history", cfg, "--limit", "12")
                latest = schedule.validate_history(schedule.read_json(directory / "history.json"), cfg, slot)
                if latest["id"] != evidence["execution_id"]:
                    raise ValueError("Upstream execution changed during one-time preparation")
                if volume:
                    latest_volume = schedule.volume_upstream_ready(cfg, slot)
                    if latest_volume != evidence["volume"]:
                        raise ValueError("Volume upstream execution changed during one-time preparation")
                    verify_publication({**cfg, "upstream": cfg["volume_report"]["upstream"]})

            results = []
            for context, item in zip(contexts, items):
                if context.get("skip_delivery"):
                    item.update(status="skipped_no_eligible_rows", message_id="", receipt={})
                    results.append(True)
                    continue
                prior = db.execute("SELECT status,message_id FROM deliveries WHERE key=?", (item["key"],)).fetchone()
                verdict = resend.decide(prior[0], prior[1]) if prior else resend.RESEND
                if verdict == resend.DONE:
                    schedule.emit("immediate_duplicate_suppressed", channel=context["channel"],
                                  status=prior[0], message_id=prior[1], request_id=request_id)
                    ok = True
                elif verdict == resend.REVERIFY:
                    ok = schedule._reverify_sent_message(db, item["key"], cfg, context, slot, prior)
                else:
                    ok = schedule._deliver_verified(context, cfg, slot, db, evidence, key=item["key"],
                        time_guard=lambda current=context: guard(current))
                row = db.execute("SELECT status,message_id,detail FROM deliveries WHERE key=?", (item["key"],)).fetchone()
                item.update(status=row[0] if row else "not_sent", message_id=row[1] if row else "",
                            receipt=json.loads(row[2]) if row else {})
                results.append(ok)
            summary["status"] = ("completed_with_skips" if all(results) and any(c.get("skip_delivery") for c in contexts)
                                 else "sent_verified" if all(results) else "partial_or_failed")
            output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            schedule.emit("immediate_finished", status=summary["status"], channels=len(items), artifact=str(output))
            return 0 if all(results) else 1
