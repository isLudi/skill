"""Reviewed immutable scope for the four-channel supervisor-detail broadcast."""
from .grade_compact import (
    BOT_OPEN_ID, TZ, business_date, business_period, enforce_live_calendar,
    scheduled_report_type,
)

PROFILE = "supervisor-detail"
CHAT_ID = "oc_6f06cad338d520a89e1607a18592e56b"
CHANNELS = (
    "KOC-周帅数学",
    "KOC-孟亚飞数学",
    "自孵化KOC-5元纯课",
    "抖音私信",
)


def enforce_group_scope(chat_id, channel, profile):
    if chat_id != CHAT_ID or channel not in CHANNELS or profile != PROFILE:
        raise ValueError("四渠道主管明细播报的群ID、渠道或报告模板超出固定范围")
