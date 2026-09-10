"""Business KOC math scope using the reviewed grade-compact format."""
from .grade_compact import (
    BOT_OPEN_ID, EXCLUDED_GRADES, GRADE_ORDER, MIN_POST_LEADS, PROFILE, TZ,
    business_date, business_period, enforce_live_calendar, grade_sort_key, scheduled_report_type,
)

CHAT_ID = "oc_978fde959e5aad96ec1aa03fe4c20b22"
CHANNELS = ("KOC-周帅数学", "KOC-孟亚飞数学")
CHANNEL = CHANNELS[0]


def enforce_group_scope(chat_id, channel, profile):
    if chat_id == CHAT_ID and (channel not in CHANNELS or profile != PROFILE):
        raise ValueError("该固定群仅允许周帅数学和孟亚飞数学的分年级精简播报")
