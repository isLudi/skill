"""Reviewed scope for private-domain, APP and the merged TMK supervisor report."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, enforce_live_calendar,
    scheduled_report_type,
)

PROFILE = "supervisor-detail"
CHAT_ID = "oc_b43002a3c802ee5ae2d5b2f10d7d50a2"
CHANNELS = (
    "集团私域",
    "app",
    "人工外呼",
)
SOURCE_CHANNEL_VALUES = {
    "集团私域": "集团私域",
    "app": "app",
    "人工外呼": ["人工外呼", "唐山TMK"],
}


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel not in CHANNELS or profile != PROFILE:
        raise ValueError("集团私域、APP与人工外呼合并主管播报的群ID、渠道或报告模板超出固定范围")
