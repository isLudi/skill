"""Shared reviewed calendar and ordering for market grade-compact reports."""
from datetime import date, datetime, timedelta, timezone

TZ = timezone(timedelta(hours=8))
PROFILE = "grade-compact"
BOT_OPEN_ID = "ou_f3907e865135732c15a1dfce27828411"
EXCLUDED_GRADES = ("初二",)
MIN_POST_LEADS = 10
GRADE_ORDER = ("初一", "初二", "初三", "高一", "高二", "高三")


def business_date(at=None):
    at = at or datetime.now(TZ)
    if isinstance(at, datetime):
        if at.tzinfo is None:
            raise ValueError("播报时间必须带时区")
        return at.astimezone(TZ).date()
    if isinstance(at, date):
        return at
    raise ValueError("无效的播报日期")


def business_period(at=None):
    day = business_date(at)
    friday = day - timedelta(days=day.weekday()) + timedelta(days=4)
    return friday.strftime("%Y%m%d") + "期"


def scheduled_report_type(at=None):
    return "both" if business_date(at).weekday() >= 4 else "process"


def grade_sort_key(grade):
    return (GRADE_ORDER.index(grade), "") if grade in GRADE_ORDER else (len(GRADE_ORDER), grade)


def enforce_live_calendar(period, report_type, at=None):
    if period != business_period(at):
        raise ValueError("正式群播报只能使用当前自然周的周五期次，不得用Base最大期次替代")
    if scheduled_report_type(at) == "process" and report_type != "process":
        raise ValueError("周一至周四仅推送当期过程数据；转化数据仅周五至周日推送")
