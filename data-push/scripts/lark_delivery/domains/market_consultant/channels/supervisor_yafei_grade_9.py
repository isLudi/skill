"""Reviewed immutable scope for the grade-9 Yafei supervisor broadcast."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, next_business_period,
)

PROFILE = "supervisor-detail"
CHAT_ID = "oc_3c652da1589558f0b0585d2bdb2f8cb9"
CHANNELS = ("B站信息流-亚飞",)
INCLUDED_GRADES = ("初三",)
WEEKEND_REPORT_TYPE = "result_and_next_process"


def scheduled_report_type(at=None):
    return WEEKEND_REPORT_TYPE if business_date(at).weekday() >= 4 else "process"


def enforce_live_calendar(period, report_type, at=None):
    day = business_date(at)
    allowed = {scheduled_report_type(day)}
    if day.weekday() >= 4:
        allowed.add("result")
    if period != business_period(day) or report_type not in allowed:
        raise ValueError("亚飞B站主管播报当前日历仅允许当前期次的规定播报类型")


def enforce_component_calendar(period, report_type, at=None):
    day = business_date(at)
    current = business_period(day)
    expected_period = current
    expected_type = "process"
    if day.weekday() >= 4:
        expected_period = current if report_type == "result" else next_business_period(current)
        expected_type = report_type
    if period != expected_period or report_type != expected_type:
        raise ValueError("亚飞B站主管播报组件期次或类型不符合当前日历")


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel not in CHANNELS or profile != PROFILE:
        raise ValueError("亚飞B站初三主管明细播报的群ID、渠道或报告模板超出固定范围")
