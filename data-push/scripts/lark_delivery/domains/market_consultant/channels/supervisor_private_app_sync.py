"""Reviewed immutable scope for the private-domain and APP supervisor broadcast."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, enforce_live_calendar,
    scheduled_report_type,
)

PROFILE = "supervisor-detail"
CHAT_ID = "oc_b43002a3c802ee5ae2d5b2f10d7d50a2"
CHANNELS = (
    "集团私域",
    "app",
)


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel not in CHANNELS or profile != PROFILE:
        raise ValueError("集团私域与APP主管明细播报的群ID、渠道或报告模板超出固定范围")
