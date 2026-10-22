"""Reviewed Jiangsu and Anhui grade-9 supervisor requests in their shared group."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, enforce_live_calendar,
    scheduled_report_type,
)
__all__ = ["BOT_OPEN_ID", "TZ", "business_date", "business_period", "enforce_live_calendar",
           "scheduled_report_type", "enforce_group_scope"]

PROFILE = "supervisor-detail"
CHAT_ID = "oc_b5dee8b192c11bb8a131ce40c41d5236"
CHANNELS = ("江苏本地化", "安徽本地化")
SOURCE_CHANNEL_VALUES = {"江苏本地化": "西安图书直播间-挂链", "安徽本地化": "西安直播安徽"}
INCLUDED_GRADES = ("初三",)
MIN_POST_LEADS = 5


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel not in CHANNELS or profile != PROFILE:
        raise ValueError("本地化初三主管播报的群ID、渠道或模板超出已登记范围")
