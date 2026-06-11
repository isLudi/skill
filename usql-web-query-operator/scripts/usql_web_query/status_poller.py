"""Query status polling and log opening."""

from __future__ import annotations

import time
from typing import Any

from .error_detection import _is_platform_failure_details, extract_error_from_page
from .page_helpers import get_sql_frame
from .query_history import _history_matches_sql, extract_open_query_tab_ids, extract_query_history_rows
from .result_panel import extract_result_preview


def result_area_visible(page: Any) -> bool:
    for frame_obj in getattr(page, "frames", []):
        try:
            if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
                continue
            visible = frame_obj.evaluate(
                """() => {
                    function isVisible(el) {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0 &&
                            style.visibility !== 'hidden' &&
                            style.display !== 'none';
                    }
                    const bodyText = document.body.innerText || '';
                    if (!bodyText.includes('结果') || !bodyText.includes('表格')) return false;
                    const activeTabs = Array.from(document.querySelectorAll('.ant-tabs-tab-active, [class*=tab][class*=active]'))
                        .map(el => (el.innerText || el.textContent || '').trim())
                        .filter(Boolean);
                    const hasQueryResultTab = activeTabs.some(text => /^查询\s*\d{9,11}/.test(text)) ||
                        /查询\s*\d{9,11}/.test(bodyText);
                    const hasResultTableTab = activeTabs.some(text => text.includes('表格')) || bodyText.includes('表格');
                    if (!hasQueryResultTab || !hasResultTableTab) return false;
                    const hasTable = Array.from(document.querySelectorAll('table, .ant-table, [class*=table]')).some((table) => {
                        if (!isVisible(table)) return false;
                        const text = table.innerText || table.textContent || '';
                        return !(text.includes('查询ID') && text.includes('主要内容'));
                    });
                    const hasDownload = Array.from(document.querySelectorAll('.anticon-download, [aria-label*=download], [class*=download]')).some(isVisible);
                    const hasResultText = /probe_value|row_cnt|lead_id|user_id|total_valid|total_lead/.test(bodyText);
                    return hasTable || hasDownload || hasResultText;
                }"""
            )
            if visible:
                return True
        except Exception:
            continue
    return False

def open_query_log(page: Any, query_id: str | None) -> bool:
    if not query_id:
        return False
    frame = get_sql_frame(page)
    try:
        row = frame.locator(f"tr:has-text('{query_id}')").first
        if row.count() > 0:
            log_link = row.get_by_text("日志", exact=True)
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
                        return text.includes('日志') || /log/i.test(text);
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
        history_rows = extract_query_history_rows(page)
        new_rows = [
            row for row in history_rows
            if row.get("query_id") not in existing_query_ids
            and _history_matches_sql(row.get("text", ""), expected_sql)
        ]
        if new_rows:
            current = new_rows[0]
            status = current.get("status")
            current_text = current.get("text", "")
            last_text = current_text[-2000:]
            if status == "Success":
                return "Success", current_text, None, current
            if status == "Failed":
                open_query_log(page, current.get("query_id"))
                return "Failed", current_text, extract_error_from_page(page), current

        # Check both outer page and iframe for status text.
        body_text = page.locator("body").inner_text(timeout=5000)
        try:
            frame = get_sql_frame(page)
            iframe_text = frame.locator("body").inner_text(timeout=3000)
        except Exception:
            iframe_text = ""
        combined = body_text + iframe_text
        last_text = combined[-2000:]
        new_tab_ids = extract_open_query_tab_ids(page) - existing_query_ids
        if new_tab_ids and ("已无更多" in combined or result_area_visible(page)):
            return "Success", combined, None, None
        if new_tab_ids:
            error_details = extract_error_from_page(page)
            if _is_platform_failure_details(error_details):
                return "Failed", combined, error_details, None
            try:
                if extract_result_preview(page, max_rows=1):
                    return "Success", combined, None, None
            except Exception:
                pass
        # Only use whole-page text as a fallback when no pre-run history IDs
        # were supplied. Otherwise old history rows can produce stale statuses.
        if not existing_query_ids:
            if "Success" in combined:
                return "Success", combined, None, None
            if "Failed" in combined or "Fail" in combined or "失败" in combined:
                return "Failed", combined, extract_error_from_page(page), None
        page.wait_for_timeout(2000)
    page.wait_for_timeout(3000)
    new_tab_ids = extract_open_query_tab_ids(page) - existing_query_ids
    if new_tab_ids and result_area_visible(page):
        return "Success", last_text, None, None
    return "Timeout", last_text, None, None
