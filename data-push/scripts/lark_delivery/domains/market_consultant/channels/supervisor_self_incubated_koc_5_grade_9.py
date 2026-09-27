"""Reviewed immutable scope for the grade-9 self-incubated KOC supervisor broadcast."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, next_business_period,
)

PROFILE = "supervisor-detail"
CHAT_ID = "oc_601bde838d4fbda7ac09840a58228f9c"
CHANNELS = ("KOC-孟亚飞数学", "自孵化KOC-5元纯课")
INCLUDED_GRADES = ("初三",)
WEEKEND_REPORT_TYPE = "result_and_next_process"
WEEKEND_NEXT_PROCESS_MIN_POST_LEADS = 5


def scheduled_report_type(at=None):
    return WEEKEND_REPORT_TYPE if business_date(at).weekday() >= 4 else "process"


def enforce_live_calendar(period, report_type, at=None):
    if period != business_period(at) or report_type != scheduled_report_type(at):
        raise ValueError("KOC初中主管播报的期次或类型不符合当前自然周日历")


def enforce_component_calendar(period, report_type, at=None):
    day = business_date(at)
    current = business_period(day)
    if day.weekday() < 4 or report_type not in {"result", "process"}:
        raise ValueError("KOC初中双期组件仅限周五至周日的转化或过程数据")
    expected = current if report_type == "result" else next_business_period(current)
    if period != expected:
        raise ValueError("KOC初中双期组件期次不符合当前自然周日历")


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel not in CHANNELS or profile != PROFILE:
        raise ValueError("KOC初中沟通群初三主管明细播报的群ID、渠道或报告模板超出固定范围")
