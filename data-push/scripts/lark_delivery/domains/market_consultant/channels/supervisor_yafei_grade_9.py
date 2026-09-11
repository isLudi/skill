"""Reviewed immutable scope for the grade-9 Yafei supervisor broadcast."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, enforce_live_calendar,
    scheduled_report_type,
)

PROFILE = "supervisor-detail"
CHAT_ID = "oc_3c652da1589558f0b0585d2bdb2f8cb9"
CHANNELS = ("B站信息流-亚飞",)
INCLUDED_GRADES = ("初三",)


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel not in CHANNELS or profile != PROFILE:
        raise ValueError("亚飞B站初三主管明细播报的群ID、渠道或报告模板超出固定范围")
