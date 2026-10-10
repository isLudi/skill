"""Reviewed APP grade-9 advisor scope and business calendar."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, next_business_period,
)

PROFILE = "supervisor-advisor-detail"
CHAT_ID = "oc_3c652da1589558f0b0585d2bdb2f8cb9"
CHANNEL = "app"
CHANNELS = (CHANNEL,)
INCLUDED_GRADES = ("初三",)
MIN_POST_LEADS = 5
WEEKEND_REPORT_TYPE = "result_and_next_process"


def scheduled_report_type(at=None):
    return WEEKEND_REPORT_TYPE if business_date(at).weekday() >= 4 else "process"


def enforce_live_calendar(period, report_type, at=None):
    day = business_date(at)
    allowed = {scheduled_report_type(day)}
    if day.weekday() >= 4:
        allowed.add("result")
    if period != business_period(day) or report_type not in allowed:
        raise ValueError("APP初三顾问播报必须使用当前期次和规定的播报类型")


def enforce_component_calendar(period, report_type, at=None):
    day = business_date(at)
    current = business_period(day)
    allowed = {(current, "process")}
    if day.weekday() >= 4:
        allowed = {(current, "result"), (next_business_period(current), "process")}
    if (period, report_type) not in allowed:
        raise ValueError("APP初三顾问消息组件不符合当前业务日历")


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel != CHANNEL or profile != PROFILE:
        raise ValueError("APP初三顾问播报的目标群、渠道或模板超出固定范围")
