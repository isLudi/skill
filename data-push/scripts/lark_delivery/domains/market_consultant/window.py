"""Schedule arithmetic: when a slot opens, and when its retries fall.

Split out of ``scheduler`` along the schedule boundary to keep that module
inside the layout size limit. Nothing here reads the clock — every entry point
takes the instant as an argument — so the arithmetic stays directly testable
and the scheduler's patched clock seam is unaffected.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=8))


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
