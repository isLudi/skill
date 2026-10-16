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


def prepare_query_sql(sql: str) -> str:
    """Remove only ordinary prefix comments, before any plan/hash is bound.

    The SQL gateway can reject a leading comment as sql[] permission denial.
    Never rewrite the statement, internal comments, literals, or SQL hints.
    """
    cursor = 1 if sql.startswith("\ufeff") else 0
    while True:
        while cursor < len(sql) and sql[cursor].isspace():
            cursor += 1
        if sql.startswith(("--+", "--!"), cursor):
            raise UsageError("Leading SQL hints/directives require manual review; not removed.")
        if sql.startswith("--", cursor):
            end = re.search(r"[\r\n]", sql[cursor:])
            if end is None:
                raise UsageError("SQL contains only leading comments; no query was prepared.")
            cursor += end.end()
        elif sql.startswith("/*", cursor):
            if sql[cursor + 2:cursor + 3] in {"+", "!"}:
                raise UsageError("Leading SQL hints/directives require manual review; not removed.")
            depth = 1
            end = cursor + 2
            while depth and end < len(sql):
                if sql.startswith("/*", end):
                    depth += 1
                    end += 2
                elif sql.startswith("*/", end):
                    depth -= 1
                    end += 2
                else:
                    end += 1
            if depth:
                raise UsageError("Unterminated leading SQL comment; no query was prepared.")
            cursor = end
        else:
            break
    if not sql[cursor:].strip():
        raise UsageError("SQL contains no statement after its leading comments.")
    return sql[cursor:]


def enforce_query_prefix(sql: str) -> None:
    if sql.removeprefix("\ufeff").lstrip().startswith(("--", "/*")):
        raise UsageError(
            "Leading SQL comments can trigger the gateway's sql[] permission error. "
            "Use prepare-sql --sql-file SOURCE --output PREPARED, review the copy, "
            "and bind any QueryPlan to the prepared file before run. "
            "The operator will not silently change an approved SQL hash."
        )

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
