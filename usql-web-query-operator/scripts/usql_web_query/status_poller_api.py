"""API-backed query status polling and log opening."""

from __future__ import annotations

import re
import time
from typing import Any

from .error_detection import _is_platform_failure_details, extract_error_from_page
from .page_helpers import get_sql_frame
from .query_history import _history_matches_sql, extract_open_query_tab_ids, extract_query_history_rows
from .result_panel import extract_result_preview


RESULT_API = "https://uanalysis.baijia.com/uanalysis-sql/api/result/list"
LOG_API = "https://uanalysis.baijia.com/uanalysis-sql/api/log/get"


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
    if not query_id:
        return None
    try:
        response = page.context.request.post(
            RESULT_API,
            data={"id": query_id, "beginPos": 0, "pageSize": 1},
            timeout=30_000,
        )
        payload = response.json()
    except Exception:
        return None
    if not response.ok or not isinstance(payload, dict):
        return None

    data = payload.get("data")
    if isinstance(data, dict):
        message = data.get("message")
        if message:
            if _looks_like_api_failure(message):
                return "Failed", message, _api_error_result("log_area", str(message), query_id)
            return None
        if "meta" in data and "data" in data:
            return "Success", f"query_id={query_id}", None

    error = payload.get("error")
    if error and _looks_like_api_failure(str(error)):
        return "Failed", str(error), _api_error_result("log_area", str(error), query_id)
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
    return _query_status_from_result_api(page, query_id) or _query_status_from_log_api(page, query_id)


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


def _new_query_id(page: Any, existing_query_ids: set[str], expected_sql: str | None):
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
):
    deadline = time.monotonic() + timeout_ms / 1000
    last_text = ""
    existing_query_ids = existing_query_ids or set()

    while time.monotonic() < deadline:
        query_id, current_row = _new_query_id(page, existing_query_ids, expected_sql)
        if query_id:
            api_status = _query_status_from_api(page, query_id)
            if api_status:
                status, text, error_details = api_status
                if status == "Failed":
                    open_query_log(page, query_id)
                return status, text, error_details, current_row

            row_status = (current_row or {}).get("status")
            current_text = (current_row or {}).get("text", "")
            if current_text:
                last_text = current_text[-2000:]
            if row_status == "Failed":
                open_query_log(page, query_id)
                return "Failed", current_text, extract_error_from_page(page), current_row

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
            return "Failed", combined, error_details, current_row

        if query_id:
            try:
                if extract_result_preview(page, max_rows=1):
                    return "Success", f"query_id={query_id}", None, current_row
            except Exception:
                pass

        if not existing_query_ids:
            if "Success" in combined:
                return "Success", combined, None, None
            if "Failed" in combined or "Fail" in combined or "失败" in combined or "澶辫触" in combined:
                return "Failed", combined, extract_error_from_page(page), None

        page.wait_for_timeout(2000)

    return "Timeout", last_text, None, None
