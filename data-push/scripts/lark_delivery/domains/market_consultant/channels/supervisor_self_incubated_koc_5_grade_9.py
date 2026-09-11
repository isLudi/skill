"""Reviewed immutable scope for the grade-9 self-incubated KOC supervisor broadcast."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, enforce_live_calendar,
    scheduled_report_type,
)

PROFILE = "supervisor-detail"
CHAT_ID = "oc_601bde838d4fbda7ac09840a58228f9c"
CHANNELS = ("自孵化KOC-5元纯课",)
INCLUDED_GRADES = ("初三",)


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel not in CHANNELS or profile != PROFILE:
        raise ValueError("自孵化KOC 5元纯课初三主管明细播报的群ID、渠道或报告模板超出固定范围")
