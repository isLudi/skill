"""Self-incubated KOC scope; shared format lives in grade_compact."""
from .grade_compact import (
    BOT_OPEN_ID, EXCLUDED_GRADES, GRADE_ORDER, MIN_POST_LEADS, PROFILE, TZ,
    business_date, business_period, enforce_live_calendar, grade_sort_key, scheduled_report_type,
)

CHAT_ID = "oc_b9dc09ba622ca00059bbc472922a803d"
CHANNEL = "自孵化KOC-5元纯课"
CHANNELS = (CHANNEL,)


def enforce_group_scope(chat_id, channel, profile):
    if chat_id == CHAT_ID and (channel != CHANNEL or profile != PROFILE):
        raise ValueError("该固定群仅允许自孵化KOC-5元纯课的分年级精简播报")
