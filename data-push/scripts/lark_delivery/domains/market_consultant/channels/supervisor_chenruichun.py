"""Reviewed scope for the Chen Ruichun advisor-grain broadcast."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, enforce_live_calendar,
    scheduled_report_type,
)

PROFILE = "supervisor-video49"
CHAT_ID = "oc_510ee233f666207fbda3a4ec473bf388"
CHANNEL = "陈瑞春"
CHANNELS = (CHANNEL,)
INCLUDED_GRADES = ("高一", "高二", "高三")
MIN_POST_LEADS = 6


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel != CHANNEL or profile != PROFILE:
        raise ValueError("陈瑞春顾问粒度播报的群ID、渠道或报告模板超出固定范围")
