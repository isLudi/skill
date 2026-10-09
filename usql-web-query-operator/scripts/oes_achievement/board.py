"""API adapter for OES achievement-board date filtering and export."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from _shared.errors import UsageError


QUERY_URL = "https://mi.gaotu100.com/performance/management/attribution/list"
EXPORT_URL = "https://mi.gaotu100.com/performance/management/attribution/export"
SHANGHAI = ZoneInfo("Asia/Shanghai")


@dataclass(frozen=True)
class TimeWindow:
    start_ms: int
    end_ms: int

    def __post_init__(self) -> None:
        if self.end_ms < self.start_ms:
            raise UsageError("Invalid OES time window: end precedes start.")

    @classmethod
    def from_dates(cls, start: date, end: date) -> "TimeWindow":
        return cls(int(epoch_ms(start, end_of_day=False)), int(epoch_ms(end, end_of_day=True)))

    @property
    def dates(self) -> tuple[date, date]:
        return (datetime.fromtimestamp(self.start_ms / 1000, SHANGHAI).date(),
                datetime.fromtimestamp(self.end_ms / 1000, SHANGHAI).date())

    def metadata(self) -> dict[str, Any]:
        return {"start_ms": self.start_ms, "end_ms": self.end_ms,
                "start_time": datetime.fromtimestamp(self.start_ms / 1000, SHANGHAI).isoformat(timespec="milliseconds"),
                "end_time": datetime.fromtimestamp(self.end_ms / 1000, SHANGHAI).isoformat(timespec="milliseconds")}


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise UsageError(f"Invalid date {value!r}; expected YYYY-MM-DD.") from exc


def resolve_date_range(single_date: str | None, start_date: str | None, end_date: str | None) -> tuple[date, date]:
    if single_date:
        if start_date or end_date:
            raise UsageError("Use --date by itself, or use --start-date and --end-date together.")
        selected = parse_date(single_date)
        return selected, selected
    if not start_date or not end_date:
        raise UsageError("Provide --date, or both --start-date and --end-date.")
    start, end = parse_date(start_date), parse_date(end_date)
    if end < start:
        raise UsageError("--end-date must not be earlier than --start-date.")
    return start, end


def epoch_ms(value: date, *, end_of_day: bool) -> str:
    clock = time.max if end_of_day else time.min
    return str(int(datetime.combine(value, clock, SHANGHAI).timestamp() * 1000))


def build_payload(start: date, end: date, *, page_num: int, page_size: int, window: TimeWindow | None = None) -> dict[str, Any]:
    return {
        "beginTime": str(window.start_ms) if window else epoch_ms(start, end_of_day=False),
        "endTime": str(window.end_ms) if window else epoch_ms(end, end_of_day=True),
        "employeeName": None,
        "pager": {"pageNum": page_num, "pageSize": page_size},
        "roleSign": 1,
    }


def _post_json(request: Any, url: str, payload: dict[str, Any], timeout_ms: int) -> dict[str, Any]:
    response = request.post(url, data=payload, timeout=timeout_ms)
    if not response.ok:
        raise UsageError(f"OES API failed: POST {url} returned HTTP {response.status}.")
    try:
        body = response.json()
    except Exception as exc:
        raise UsageError(f"OES API returned non-JSON content: POST {url}.") from exc
    if not isinstance(body, dict):
        raise UsageError("OES API response is not a JSON object.")
    if body.get("code") not in (0, "0"):
        raise UsageError(f"OES API rejected the request: POST {url}; code={body.get('code')!r}.")
    return body


def _pager_count(body: dict[str, Any]) -> int:
    pager = body.get("pager")
    if not isinstance(pager, dict) or isinstance(pager.get("count"), bool):
        raise UsageError("OES query pager/count contract changed.")
    raw_count = pager.get("count")
    if not isinstance(raw_count, (int, str)):
        raise UsageError("OES query response has no valid integer row count.")
    try:
        count = int(raw_count)
    except (TypeError, ValueError) as exc:
        raise UsageError("OES query response has no valid row count.") from exc
    if count < 0:
        raise UsageError("OES query returned a negative row count.")
    return count


def inspect_range(request: Any, start: date, end: date, timeout_ms: int, *, window: TimeWindow | None = None) -> dict[str, Any]:
    """Read one tiny page to verify a range and assess the native 10k export limit."""
    body = _post_json(request, QUERY_URL, build_payload(start, end, page_num=1, page_size=1, window=window), timeout_ms)
    count = _pager_count(body)
    data = body.get("data")
    rows = data.get("attribution") if isinstance(data, dict) else None
    if not isinstance(rows, list) or len(rows) != min(count, 1) or any(not isinstance(row, dict) for row in rows):
        raise UsageError("OES range probe did not return the expected one-page row structure.")
    return {"start_date": start.isoformat(), "end_date": end.isoformat(), "days_inclusive": (end - start).days + 1,
            "row_count": count, "count_verified": True, "native_export_limit": 10_000,
            "native_export_complete_possible": count <= 10_000, "export_requested": False}


def query_all(request: Any, start: date, end: date, *, page_size: int, timeout_ms: int, window: TimeWindow | None = None) -> tuple[list[Any], int, list[dict[str, Any]]]:
    rows: list[Any] = []
    metadata: list[dict[str, Any]] = []
    expected_count: int | None = None
    page_num = 1
    while True:
        payload = build_payload(start, end, page_num=page_num, page_size=page_size, window=window)
        body = _post_json(request, QUERY_URL, payload, timeout_ms)
        data = body.get("data") or {}
        page_rows = data.get("attribution") if isinstance(data, dict) else None
        if not isinstance(page_rows, list):
            raise UsageError("OES query response no longer contains data.attribution as a list.")
        count = _pager_count(body)
        if expected_count is None:
            expected_count = count
        elif expected_count != count:
            raise UsageError("OES row count changed during pagination; export was not submitted.")
        if any(not isinstance(row, dict) for row in page_rows):
            raise UsageError("OES query row structure changed.")
        rows.extend(page_rows)
        metadata.append({"method": "POST", "url": QUERY_URL, "status": 200, "page_num": page_num, "rows": len(page_rows)})
        if not page_rows or len(rows) >= expected_count:
            break
        page_num += 1
        if page_num > 10_000:
            raise UsageError("OES pagination exceeded the safety limit.")
    expected_count = expected_count or 0
    if len(rows) != expected_count:
        raise UsageError(f"OES pagination mismatch: expected {expected_count} rows, received {len(rows)}.")
    row_ids = [row["id"] for row in rows if row.get("id") is not None]
    if len(row_ids) != len(set(row_ids)):
        raise UsageError("OES pagination returned duplicate row IDs; export was not submitted.")
    return rows, expected_count, metadata


def request_native_export(request: Any, start: date, end: date, timeout_ms: int, *, window: TimeWindow | None = None) -> dict[str, Any]:
    body = _post_json(request, EXPORT_URL, build_payload(start, end, page_num=1, page_size=10, window=window), timeout_ms)
    return {
        "method": "POST",
        "url": EXPORT_URL,
        "status": 200,
        "code": body.get("code"),
        "message": body.get("data"),
        "source": body.get("source"),
    }


def _cell(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return value


def write_exports(rows: list[Any], output_dir: Path, start: date, end: date) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = f"oes-achievement-{start.isoformat()}-{end.isoformat()}"
    json_path = output_dir / f"{base}.json"
    csv_path = output_dir / f"{base}.csv"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    keys: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            for key in row:
                if key not in keys:
                    keys.append(key)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        if keys:
            writer.writeheader()
            for row in rows:
                writer.writerow({key: _cell(value) for key, value in row.items()})
    return json_path, csv_path
