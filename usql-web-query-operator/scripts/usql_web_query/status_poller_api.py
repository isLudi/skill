"""API-backed query status polling and log opening."""

from __future__ import annotations

import re
import time
from typing import Any

from .error_detection import _is_platform_failure_details, extract_error_from_page
from .page_helpers import get_sql_frame
from .query_history import (
    _history_matches_sql,
    extract_open_query_tab_ids,
    extract_query_history_rows,
    find_query_history_row,
)
from .result_panel import extract_result_preview


RESULT_API = "https://uanalysis.baijia.com/uanalysis-sql/api/result/list"
LOG_API = "https://uanalysis.baijia.com/uanalysis-sql/api/log/get"


def _non_negative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _result_total_rows(data: dict[str, Any]) -> int | None:
    for key in ("total", "totalCount", "rowCount", "count", "totalNum"):
        parsed = _non_negative_int(data.get(key))
        if parsed is not None:
            return parsed
    pager = data.get("pager")
    if isinstance(pager, dict):
        for key in ("total", "totalCount", "rowCount", "count"):
            parsed = _non_negative_int(pager.get(key))
            if parsed is not None:
                return parsed
    return None


def _result_headers(meta: Any, rows: Any) -> list[str]:
    headers: list[str] = []
    if isinstance(meta, list):
        for index, item in enumerate(meta):
            if isinstance(item, str):
                headers.append(item)
                continue
            if isinstance(item, dict):
                value = next(
                    (
                        item.get(key)
                        for key in ("name", "columnName", "fieldName", "label", "title", "key")
                        if item.get(key) is not None
                    ),
                    None,
                )
                headers.append(str(value) if value is not None else f"column_{index + 1}")
    elif isinstance(meta, dict):
        columns = meta.get("columns") or meta.get("fields")
        if isinstance(columns, list):
            headers = _result_headers(columns, rows)
        elif meta:
            headers = [str(key) for key in meta]
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        row_headers = [str(key) for key in rows[0]]
        if not headers or any(header not in rows[0] for header in headers):
            headers = row_headers
    return headers


def _result_rows(rows: Any, headers: list[str], max_rows: int) -> list[list[Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[list[Any]] = []
    for row in rows[:max(max_rows, 0)]:
        if isinstance(row, dict):
            normalized.append([row.get(header) for header in headers])
        elif isinstance(row, list):
            normalized.append(row)
        elif isinstance(row, tuple):
            normalized.append(list(row))
        else:
            normalized.append([row])
    return normalized


def fetch_query_result_evidence(
    page: Any,
    query_id: str | None,
    *,
    max_rows: int = 5,
    request_timeout_ms: int = 30_000,
) -> dict[str, Any]:
    """Read exact-query result metadata and a bounded preview from the result API."""
    evidence: dict[str, Any] = {
        "state": "result_api_unavailable",
        "source": "result_api",
        "http_status": None,
        "error_code": None,
        "meta_count": None,
        "row_count_page": None,
        "total_rows": None,
        "preview": None,
        "failure_message": None,
    }
    if not query_id:
        return evidence
    try:
        response = page.context.request.post(
            RESULT_API,
            data={"id": query_id, "beginPos": 0, "pageSize": max(max_rows, 1)},
            timeout=max(min(request_timeout_ms, 30_000), 1),
        )
        evidence["http_status"] = int(response.status)
        payload = response.json()
    except Exception:
        return evidence
    if not response.ok or not isinstance(payload, dict):
        evidence["state"] = "result_api_error"
        return evidence
    evidence["error_code"] = payload.get("errorCode")
    if payload.get("errorCode") not in (None, 0):
        evidence["state"] = "result_api_error"
        evidence["failure_message"] = str(payload.get("error") or payload.get("message") or "")[:4000] or None
        return evidence
    root_error = payload.get("error")
    if root_error and _looks_like_api_failure(str(root_error)):
        evidence["state"] = "result_api_failed"
        evidence["failure_message"] = str(root_error)[:4000]
        return evidence
    data = payload.get("data")
    if not isinstance(data, dict):
        evidence["state"] = "result_api_pending"
        return evidence
    message = data.get("message")
    if message and _looks_like_api_failure(str(message)):
        evidence["state"] = "result_api_failed"
        evidence["failure_message"] = str(message)[:4000]
        return evidence
    if "meta" not in data or "data" not in data:
        evidence["state"] = "result_api_pending"
        return evidence
    meta = data.get("meta")
    raw_rows = data.get("data")
    headers = _result_headers(meta, raw_rows)
    rows = _result_rows(raw_rows, headers, max_rows)
    raw_row_count = len(raw_rows) if isinstance(raw_rows, list) else 0
    total_rows = _result_total_rows(data)
    evidence.update(
        {
            "state": (
                "success_with_rows"
                if raw_row_count > 0
                else "success_empty_verified"
                if total_rows == 0
                else "success_empty_candidate"
            ),
            "meta_count": len(meta) if isinstance(meta, list) else len(headers),
            "row_count_page": raw_row_count,
            "total_rows": total_rows,
            "preview": {
                "headers": headers,
                "rows": rows,
                "row_count_visible": raw_row_count,
                "no_more": (
                    total_rows <= raw_row_count
                    if total_rows is not None
                    else raw_row_count < max(max_rows, 1)
                ),
            },
        }
    )
    return evidence


def wait_for_query_result_evidence(
    page: Any,
    query_id: str | None,
    *,
    timeout_ms: int = 30_000,
    poll_interval_ms: int = 500,
    max_rows: int = 5,
) -> dict[str, Any]:
    deadline = time.monotonic() + max(timeout_ms, 0) / 1000
    remaining_ms = max(int((deadline - time.monotonic()) * 1000), 1)
    latest = fetch_query_result_evidence(
        page,
        query_id,
        max_rows=max_rows,
        request_timeout_ms=remaining_ms,
    )
    terminal_states = {
        "success_with_rows",
        "success_empty_verified",
        "result_api_failed",
        "result_api_error",
    }
    while latest.get("state") not in terminal_states and time.monotonic() < deadline:
        page.wait_for_timeout(max(poll_interval_ms, 50))
        remaining_ms = max(int((deadline - time.monotonic()) * 1000), 1)
        latest = fetch_query_result_evidence(
            page,
            query_id,
            max_rows=max_rows,
            request_timeout_ms=remaining_ms,
        )
    return latest


def result_area_visible(page: Any) -> bool:
    """Return true only when a real result data table is visible."""
    try:
        return bool(extract_result_preview(page, max_rows=1))
    except Exception:
        return False


def _api_error_result(source: str, detail: str, query_id: str | None = None) -> dict[str, Any]:
    cleaned = re.sub(r"\n{3,}", "\n\n", (detail or "").replace("\r\n", "\n")).strip()
    title = cleaned.splitlines()[0][:500] if cleaned else "query failed"
    if query_id:
        title = f"{query_id}: {title}"
    return {
        "source": source,
        "title": title,
        "detail": cleaned[:4000] or None,
        "raw_snippet": cleaned[:2000],
        "all_candidates": [cleaned[:2000]] if cleaned else [],
    }


def _looks_like_api_failure(text: str | None) -> bool:
    if not text:
        return False
    return bool(re.search(
        r"PRESTO_.*ERROR|Query failed|Exception|SQLException|PrestoException|"
        r"mismatched input|does not exist|not found|unknown|invalid|syntax|"
        r"Number of stages|exceeds the allowed maximum|cannot|denied|failed|"
        r"错误|异常|失败",
        text,
        flags=re.I,
    ))


def _query_status_from_result_api(page: Any, query_id: str | None):
    evidence = fetch_query_result_evidence(page, query_id, max_rows=1)
    if evidence["state"] == "result_api_failed":
        detail = evidence.get("failure_message") or f"query result API reported failure for query_id={query_id}"
        return "Failed", detail, _api_error_result("log_area", detail, query_id)
    if evidence["state"] in {"success_with_rows", "success_empty_verified"}:
        return "Success", f"query_id={query_id}", None
    return None


def _query_status_from_log_api(page: Any, query_id: str | None):
    if not query_id:
        return None
    try:
        response = page.context.request.get(
            LOG_API,
            params={"id": query_id, "beginPos": 0},
            timeout=30_000,
        )
        payload = response.json()
    except Exception:
        return None
    if not response.ok or not isinstance(payload, dict):
        return None

    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    log_text = str(data.get("data") or "")
    if _looks_like_api_failure(log_text):
        return "Failed", log_text, _api_error_result("log_area", log_text, query_id)

    task_status = data.get("taskStatus")
    if task_status in {3, "3"} and ("rowAffectInfo" in log_text or "进度percentage : 100%" in log_text):
        return "Success", f"query_id={query_id}", None
    if task_status in {-1, 4, 5, "-1", "4", "5"}:
        return "Failed", log_text, _api_error_result("log_area", log_text, query_id)
    return None


def _query_status_from_api(page: Any, query_id: str | None):
    result_status = _query_status_from_result_api(page, query_id)
    if result_status:
        return (*result_status, "result_api")
    log_status = _query_status_from_log_api(page, query_id)
    if log_status:
        return (*log_status, "log_api")
    return None


def _row_with_completion_source(
    row: dict[str, Any] | None,
    query_id: str | None,
    source: str,
) -> dict[str, Any]:
    resolved = dict(row or {})
    if query_id:
        resolved.setdefault("query_id", query_id)
    resolved["completion_source"] = source
    return resolved


def open_query_log(page: Any, query_id: str | None) -> bool:
    if not query_id:
        return False
    frame = get_sql_frame(page)
    try:
        row = frame.locator(f"tr:has-text('{query_id}')").first
        if row.count() > 0:
            for label in ("日志", "鏃ュ織"):
                log_link = row.get_by_text(label, exact=True)
                if log_link.count() > 0:
                    log_link.last.click(timeout=5000)
                    page.wait_for_timeout(1500)
                    return True
            links = row.locator("a,button")
            if links.count() > 0:
                links.last.click(timeout=5000)
                page.wait_for_timeout(1500)
                return True
            cells = row.locator("td")
            if cells.count() > 0:
                cells.nth(cells.count() - 1).click(timeout=5000)
                page.wait_for_timeout(1500)
                return True
    except Exception:
        pass

    for frame_obj in getattr(page, "frames", []):
        try:
            if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
                continue
            clicked = frame_obj.evaluate(
                """queryId => {
                    function visible(el) {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0 &&
                            style.visibility !== 'hidden' &&
                            style.display !== 'none';
                    }
                    const rows = Array.from(document.querySelectorAll('tr')).filter(visible);
                    const row = rows.find(item => (item.innerText || item.textContent || '').includes(queryId));
                    if (!row) return false;
                    const targets = Array.from(row.querySelectorAll('a,button,span')).filter((el) => {
                        const text = (el.innerText || el.textContent || '').trim();
                        return text.includes('日志') || text.includes('鏃ゅ織') || /log/i.test(text);
                    });
                    const target = targets[0] || row.querySelector('td:last-child a, td:last-child button, td:last-child span');
                    if (!target) return false;
                    target.click();
                    return true;
                }""",
                query_id,
            )
            if clicked:
                page.wait_for_timeout(1500)
                return True
        except Exception:
            continue
    return False


def _matching_new_history_row(page: Any, existing_query_ids: set[str], expected_sql: str | None):
    for row in extract_query_history_rows(page):
        if row.get("query_id") in existing_query_ids:
            continue
        if not _history_matches_sql(row.get("text", ""), expected_sql):
            continue
        return row
    return None


def _new_query_id(
    page: Any,
    existing_query_ids: set[str],
    expected_sql: str | None,
    exact_query_id: str | None = None,
):
    if exact_query_id:
        row = find_query_history_row(page, exact_query_id)
        return exact_query_id, row or {"query_id": exact_query_id, "text": f"query_id={exact_query_id}"}
    row = _matching_new_history_row(page, existing_query_ids, expected_sql)
    if row and row.get("query_id"):
        return row.get("query_id"), row
    new_tab_ids = extract_open_query_tab_ids(page) - existing_query_ids
    if new_tab_ids:
        query_id = sorted(new_tab_ids)[-1]
        return query_id, {"query_id": query_id, "text": f"query_id={query_id}"}
    return None, None


def wait_for_status(
    page: Any,
    timeout_ms: int,
    existing_query_ids: set[str] | None = None,
    expected_sql: str | None = None,
    *,
    exact_query_id: str | None = None,
):
    deadline = time.monotonic() + timeout_ms / 1000
    last_text = ""
    existing_query_ids = existing_query_ids or set()

    while time.monotonic() < deadline:
        query_id, current_row = _new_query_id(
            page,
            existing_query_ids,
            expected_sql,
            exact_query_id=exact_query_id,
        )
        if query_id:
            api_status = _query_status_from_api(page, query_id)
            if api_status:
                status, text, error_details, completion_source = api_status
                if status == "Failed":
                    open_query_log(page, query_id)
                return (
                    status,
                    text,
                    error_details,
                    _row_with_completion_source(current_row, query_id, completion_source),
                )

            row_status = (current_row or {}).get("status")
            current_text = (current_row or {}).get("text", "")
            if current_text:
                last_text = current_text[-2000:]
            if row_status == "Failed":
                open_query_log(page, query_id)
                return (
                    "Failed",
                    current_text,
                    extract_error_from_page(page),
                    _row_with_completion_source(current_row, query_id, "history"),
                )
            if row_status == "Success":
                return (
                    "Success",
                    current_text or f"query_id={query_id}",
                    None,
                    _row_with_completion_source(current_row, query_id, "history"),
                )

        body_text = page.locator("body").inner_text(timeout=5000)
        try:
            frame = get_sql_frame(page)
            iframe_text = frame.locator("body").inner_text(timeout=3000)
        except Exception:
            iframe_text = ""
        combined = body_text + iframe_text
        last_text = combined[-2000:]

        error_details = extract_error_from_page(page)
        if query_id and _is_platform_failure_details(error_details):
            return (
                "Failed",
                combined,
                error_details,
                _row_with_completion_source(current_row, query_id, "ui_error"),
            )

        if query_id:
            try:
                if extract_result_preview(page, max_rows=1, query_id=query_id):
                    return (
                        "Success",
                        f"query_id={query_id}",
                        None,
                        _row_with_completion_source(current_row, query_id, "ui_result"),
                    )
            except Exception:
                pass

        if not existing_query_ids and not exact_query_id:
            if "Success" in combined:
                return (
                    "Success",
                    combined,
                    None,
                    _row_with_completion_source(None, query_id, "legacy_ui"),
                )
            if "Failed" in combined or "Fail" in combined or "失败" in combined or "澶辫触" in combined:
                return (
                    "Failed",
                    combined,
                    extract_error_from_page(page),
                    _row_with_completion_source(None, query_id, "legacy_ui"),
                )

        page.wait_for_timeout(2000)

    return "Timeout", last_text, None, None
