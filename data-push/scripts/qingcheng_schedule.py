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


def delivery_deadline(slot: datetime, calendar: dict) -> datetime:
    """End of the last authorized retry minute, including cross-hour windows."""
    if slot.tzinfo is None or slot.utcoffset() != timedelta(hours=8):
        raise ValueError("Qingcheng delivery slot must use the configured timezone")
    interval = calendar.get("retry_interval_minutes", 2)
    window = calendar.get("retry_window_minutes")
    if window is None:
        window = calendar["deadline_minute"] - calendar["minute"]
    if type(interval) is not int or type(window) is not int or interval <= 0 or window < 0:
        raise ValueError("Invalid Qingcheng delivery window")
    return slot + timedelta(minutes=(window // interval) * interval + 1)


def require_delivery_window(slot: datetime, calendar: dict, *, now: datetime | None = None) -> None:
    current = now or datetime.now(slot.tzinfo)
    if current < slot or current >= delivery_deadline(slot, calendar):
        raise ValueError("Qingcheng delivery missed its authorized batch window")
