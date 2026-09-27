"""Reviewed scope for the Zhu Doctor video-channel 49-yuan supervisor report."""

from .grade_compact import (
    BOT_OPEN_ID,
    TZ,
    business_date,
    business_period,
    enforce_live_calendar,
    scheduled_report_type,
)


PROFILE = "supervisor-video49"
CHAT_ID = "oc_a9d8b5c199c4602466eab5be43f7db3c"
CHANNEL = "朱博士"
CHANNELS = (CHANNEL,)
INCLUDED_GRADES = ("初一", "初三", "高一", "高二", "高三")
MIN_POST_LEADS = 5


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel != CHANNEL or profile != PROFILE:
        raise ValueError("朱博士-视频号49主管播报的群ID、渠道或报告模板超出固定范围")
