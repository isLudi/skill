"""Resolve Qingcheng retry slots across hour boundaries; no I/O or sending."""

from datetime import datetime, timedelta


def resolve_slot(now: datetime, *, weekdays: list[int], hours: list[int], minute: int,
                 retry_minutes: int, window_minutes: int, error: str) -> datetime:
    if (now.tzinfo is None or now.utcoffset() != timedelta(hours=8)
            or now.weekday() not in weekdays):
        raise ValueError(error)
    current = now.replace(second=0, microsecond=0)
    for hour in hours:
        start = current.replace(hour=hour, minute=minute)
        elapsed = int((current - start).total_seconds() // 60)
        if 0 <= elapsed <= window_minutes and elapsed % retry_minutes == 0:
            return start
    raise ValueError(error)
