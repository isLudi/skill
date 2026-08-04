"""Query-history extraction helpers."""

from __future__ import annotations

import re
from typing import Any

from .sql_utils import _compact_sql_text


def _history_matches_sql(row_text: str, sql: str | None) -> bool:
    if not sql:
        return True
    expected = _compact_sql_text(sql)
    actual = _compact_sql_text(row_text)
    if not expected or not actual:
        return False
    return expected[:120] in actual or expected[:80] in actual


def extract_query_history_rows(page: Any) -> list[dict[str, str]]:
    """Extract visible query-history rows from the SQL iframe.

    The page often contains previous Success/Failed rows. Status polling should
    prefer rows whose query ID was not present before the current run.
    """
    rows: list[dict[str, str]] = []
    for frame_obj in getattr(page, "frames", []):
        try:
            if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
                continue
            frame_rows = frame_obj.evaluate(
                """() => {
                    function visible(el) {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0 &&
                            style.visibility !== 'hidden' &&
                            style.display !== 'none';
                    }
                    function headerIndex(headers, patterns) {
                        return headers.findIndex(text => patterns.some(pattern => pattern.test(text)));
                    }
                    const output = [];
                    for (const table of Array.from(document.querySelectorAll('table'))) {
                        const headers = Array.from(table.querySelectorAll('thead th'))
                            .map(cell => (cell.innerText || cell.textContent || '').trim());
                        const idIndex = headerIndex(headers, [/查询\\s*ID/i, /^ID$/i]);
                        const engineIndex = headerIndex(headers, [/引擎/, /engine/i]);
                        const durationIndex = headerIndex(headers, [/持续时间/, /duration/i]);
                        const statusIndex = headerIndex(headers, [/状态/, /status/i]);
                        if (idIndex < 0 || (statusIndex < 0 && engineIndex < 0)) continue;
                        const bodyRows = Array.from(table.querySelectorAll('tbody tr')).filter(visible);
                        for (const row of bodyRows) {
                            const cells = Array.from(row.querySelectorAll('td'))
                                .map((cell) => (cell.innerText || cell.textContent || '').trim());
                            const text = cells.join('\\n');
                            const idText = idIndex >= 0 ? cells[idIndex] || '' : text;
                            const idMatch = idText.match(/\\b(\\d{9,11})\\b/) || text.match(/\\b(\\d{9,11})\\b/);
                            if (!idMatch) continue;
                            let status = '';
                            const statusText = statusIndex >= 0 ? cells[statusIndex] || '' : text;
                            if (/\\bSuccess\\b/.test(statusText)) status = 'Success';
                            else if (/\\bFail(?:ed)?\\b|失败/.test(statusText)) status = 'Failed';
                            else if (/\\bRunning\\b|运行中|执行中|查询中/.test(statusText)) status = 'Running';
                            else if (/\\bQueued\\b|等待|排队/.test(statusText)) status = 'Queued';
                            const detectedEngine = cells.find(cell => /presto|doris|lakehouse/i.test(cell)) || '';
                            output.push({
                                query_id: idMatch ? idMatch[1] : '',
                                status,
                                engine: engineIndex >= 0 ? cells[engineIndex] || detectedEngine : detectedEngine,
                                duration_text: durationIndex >= 0 ? cells[durationIndex] || '' : '',
                                text,
                            });
                        }
                    }
                    return output;
                }"""
            )
            rows.extend(frame_rows)
        except Exception:
            continue
    return rows


def extract_query_history_ids(page: Any) -> set[str]:
    return (
        {row["query_id"] for row in extract_query_history_rows(page) if row.get("query_id")}
        | extract_open_query_tab_ids(page)
    )


def find_query_history_row(page: Any, query_id: str | None) -> dict[str, str] | None:
    if not query_id:
        return None
    return next(
        (row for row in extract_query_history_rows(page) if row.get("query_id") == query_id),
        None,
    )


def lookup_query_history_row_by_text(page: Any, query_id: str | None) -> dict[str, str] | None:
    if not query_id:
        return None
    for frame_obj in getattr(page, "frames", []):
        try:
            if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
                continue
            body_text = frame_obj.locator("body").inner_text(timeout=5000)
        except Exception:
            continue
        for raw_line in body_text.splitlines():
            line = raw_line.strip()
            if not line.startswith(query_id):
                continue
            cells = line.split("\t")
            if len(cells) < 5:
                continue
            status = ""
            if re.search(r"\bSuccess\b", line):
                status = "Success"
            elif re.search(r"\bFail(?:ed)?\b|失败", line):
                status = "Failed"
            elif re.search(r"\bRunning\b|运行中|执行中|查询中", line):
                status = "Running"
            elif re.search(r"\bQueued\b|等待|排队", line):
                status = "Queued"
            return {
                "query_id": query_id,
                "status": status,
                "engine": cells[-5] if len(cells) >= 5 else "",
                "duration_text": cells[-4] if len(cells) >= 4 else "",
                "text": line,
            }
    return None


def extract_open_query_tab_ids(page: Any) -> set[str]:
    query_ids: set[str] = set()
    for frame_obj in getattr(page, "frames", []):
        try:
            if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
                continue
            text = frame_obj.locator("body").inner_text(timeout=3000)
            query_ids.update(re.findall(r"查询\s*(\d{9,11})", text))
        except Exception:
            continue
    return query_ids


def extract_query_id(text: str) -> str | None:
    match = re.search(r"\b(\d{9,11})\b", text)
    return match.group(1) if match else None
