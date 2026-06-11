"""SQL input, safety-policy, and text parsing helpers."""

from __future__ import annotations

import re
from pathlib import Path

from _shared.errors import UsageError


def read_sql(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise UsageError(f"SQL file is empty: {path}")
    return text

def visible_download_limit(sql: str) -> int | None:
    matches = re.findall(r"\blimit\s+(\d+)\b", sql, flags=re.I)
    if not matches:
        return None
    return int(matches[-1])

def enforce_download_policy_before_run(sql: str, download: bool) -> None:
    limit = visible_download_limit(sql)
    if download and limit is not None and limit > 1000:
        raise UsageError(
            "Download is blocked by local policy: SQL must visibly contain "
            "LIMIT 1000 or lower, or the result page must prove <= 1000 rows."
        )

def _compact_sql_text(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"--[^\r\n]*", "", text)
    return re.sub(r"\s+", "", text).lower()

def parse_duration_seconds(text: str | None) -> float | None:
    if not text:
        return None
    raw = str(text).strip()
    if not raw:
        return None
    total = 0.0
    matched = False
    for pattern, factor in ((r"(\d+(?:\.\d+)?)\s*小时", 3600), (r"(\d+(?:\.\d+)?)\s*分", 60), (r"(\d+(?:\.\d+)?)\s*秒", 1)):
        match = re.search(pattern, raw)
        if match:
            total += float(match.group(1)) * factor
            matched = True
    if matched:
        return total
    plain_seconds = re.fullmatch(r"(\d+(?:\.\d+)?)\s*s", raw, flags=re.I)
    if plain_seconds:
        return float(plain_seconds.group(1))
    return None
