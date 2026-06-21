"""Result panel navigation and preview extraction."""

from __future__ import annotations

import time
from typing import Any

from .page_helpers import get_sql_frame


def _wait_for_result_panel(page: Any) -> None:
    """Wait for the result panel to render after query success.

    The platform shows "Success" in query history when the query is accepted,
    then streams execution logs asynchronously. After the log finishes, the
    page AUTO-JUMPS to the result view showing the data table + download button.

    We wait for: log loading spinner gone → auto-jump → result table visible.
    """
    frame = get_sql_frame(page)
    # The platform can be slow — wait up to the full query timeout.
    deadline = time.monotonic() + 600.0  # 10 min max

    scroll_script = "el => { el.scrollTop = el.scrollHeight; }"
    prev_url = ""
    result_seen_at = None
    empty_result_seen_at = None

    while time.monotonic() < deadline:
        # Scroll to keep the bottom (log / result area) visible.
        try:
            frame.locator("body").evaluate(scroll_script)
        except Exception:
            pass

        page.wait_for_timeout(2000)

        for frame_obj in page.frames:
            if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
                continue

            # Detect if the iframe auto-jumped to a result URL.
            cur_url = frame_obj.url
            if cur_url != prev_url:
                prev_url = cur_url

            check = frame_obj.evaluate("""() => {
                function visible(el) {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 &&
                        style.visibility !== 'hidden' && style.display !== 'none';
                }
                function isHistoryTable(headers) {
                    const needles = ['查询ID', '查询时间', '主要内容', '引擎', '持续时间', '状态', '下载状态', '操作'];
                    return headers.some(h => needles.some(n => h.includes(n)));
                }

                // 1. Is the log loading spinner still active?
                const loadingIcons = document.querySelectorAll('.anticon-loading');
                for (const icon of loadingIcons) {
                    if (icon.closest('.antd-pro-src-components-history-infinite-scroll-log-index-logContainer')) {
                        return 'log-loading';
                    }
                }

                // 2. Check for a result data table (not the query-history table).
                const tables = document.querySelectorAll('.ant-table');
                for (const t of tables) {
                    if (!visible(t)) continue;
                    const headers = Array.from(t.querySelectorAll('th')).map(h => h.innerText.trim());
                    if (!headers.some(Boolean) || isHistoryTable(headers)) continue;
                    const rows = Array.from(t.querySelectorAll('tbody tr.ant-table-row')).filter(visible);
                    if (rows.length > 0) {
                        return 'result-table:' + rows.length + 'rows';
                    }
                }

                // 3. Check for result data text anywhere in the body.
                const bt = document.body.innerText;
                if (bt.includes('row_cnt') || bt.includes('lead_cnt')) return 'result-text';

                // 4. Check for a visible empty result table. This can be transient,
                // so Python waits for it to remain stable before returning.
                for (const t of tables) {
                    if (!visible(t)) continue;
                    const headers = Array.from(t.querySelectorAll('th')).map(h => h.innerText.trim());
                    if (isHistoryTable(headers)) continue;
                    const placeholder = t.querySelector('.ant-table-placeholder, .ant-empty-description');
                    if (placeholder && visible(placeholder) && (placeholder.innerText || '').includes('暂无数据')) {
                        return 'result-empty';
                    }
                }

                // 5. Check for collapsed/expandable result panel.
                const collapses = document.querySelectorAll('.ant-collapse-item');
                if (collapses.length > 0) return 'collapse-panels:' + collapses.length;

                // 6. "结果"/"表格" tabs present?
                if (bt.includes('结果') && bt.includes('表格')) return 'result-tabs';

                return 'waiting';
            }""")

            if check.startswith('result-table') or check == 'result-text' or check.startswith('collapse-'):
                page.wait_for_timeout(1000)
                return
            if check in {'result-tabs', 'result-empty'}:
                now = time.monotonic()
                if result_seen_at is None:
                    result_seen_at = now
                if check == 'result-empty':
                    if empty_result_seen_at is None:
                        empty_result_seen_at = now
                    if now - empty_result_seen_at >= 30.0:
                        return
                try:
                    open_result_table(page)
                except Exception:
                    pass
                continue
            if check == 'log-loading':
                continue

    # Timeout: one last attempt.
    try:
        frame.locator("body").evaluate(scroll_script)
        page.wait_for_timeout(3000)
    except Exception:
        pass

def open_result_table(page: Any) -> None:
    """The result panel auto-appears at the page bottom after query success.

    We just scroll down to ensure it is in view, then click "结果"/"表格" if needed.
    """
    frame = get_sql_frame(page)
    page.wait_for_timeout(500)

    # Scroll to bottom of the iframe to ensure the result panel is visible.
    try:
        frame.locator("body").evaluate("el => el.scrollTop = el.scrollHeight")
        page.wait_for_timeout(500)
    except Exception:
        pass

    # Try clicking "结果" / "表格" sub-tabs if they exist.
    for label in ("结果", "表格"):
        for scope in (frame, page):
            try:
                locator = scope.get_by_text(label, exact=True)
                if locator.count() > 0:
                    locator.last.click(timeout=3000)
                    page.wait_for_timeout(500)
                    break
            except Exception:
                continue

def extract_result_preview(page: Any, max_rows: int = 5) -> dict[str, Any] | None:
    open_result_table(page)
    body_text = page.locator("body").inner_text(timeout=5000)

    # Collect tables from both the iframe and the outer page.
    all_tables = []
    for frame_obj in page.frames:
        try:
            frame_tables = frame_obj.evaluate(
                """maxRows => {
                    function visible(el) {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                    }
                    return Array.from(document.querySelectorAll('table')).filter(visible).map((table) => {
                        const rows = Array.from(table.querySelectorAll('tr')).filter(visible);
                        const parsed = rows.map((tr) => Array.from(tr.querySelectorAll('th,td')).map((cell) => cell.innerText.trim()));
                        const nonEmpty = parsed.filter((row) => row.some(Boolean));
                        return {
                            headers: nonEmpty[0] || [],
                            rows: nonEmpty.slice(1, maxRows + 1),
                            row_count_visible: Math.max(nonEmpty.length - 1, 0),
                        };
                    });
                }""",
                max_rows,
            )
            all_tables.extend(frame_tables)
        except Exception:
            continue
    ignored_headers = {"查询ID", "查询时间", "主要内容", "引擎", "持续时间", "状态", "下载状态", "操作"}
    candidates = []
    for table in all_tables:
        headers = set(table.get("headers") or [])
        if not headers:
            continue
        if headers & ignored_headers:
            continue
        # Prefer tables that actually have data rows.
        if table.get("rows") and len(table["rows"]) > 0:
            candidates.append(table)
    if not candidates:
        return None
    # Return the last candidate (typically the bottom-most result table).
    result = candidates[-1]
    result["no_more"] = "已无更多" in body_text
    return result

def result_page_has_no_data(page: Any) -> bool:
    for frame_obj in getattr(page, "frames", []):
        try:
            if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
                continue
            if frame_obj.evaluate(
                """() => {
                    function visible(el) {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0 &&
                            style.visibility !== 'hidden' && style.display !== 'none';
                    }
                    function isHistoryTable(headers) {
                        const needles = ['查询ID', '查询时间', '主要内容', '引擎', '持续时间', '状态', '下载状态', '操作'];
                        return headers.some(h => needles.some(n => h.includes(n)));
                    }
                    const text = document.body.innerText || '';
                    if (!text.includes('结果') || !text.includes('表格')) return false;
                    return Array.from(document.querySelectorAll('.ant-table')).some((table) => {
                        if (!visible(table)) return false;
                        const headers = Array.from(table.querySelectorAll('th')).map(h => h.innerText.trim());
                        if (isHistoryTable(headers)) return false;
                        const placeholder = table.querySelector('.ant-table-placeholder, .ant-empty-description');
                        return placeholder && visible(placeholder) && (placeholder.innerText || '').includes('暂无数据');
                    });
                }"""
            ):
                return True
        except Exception:
            continue
    return False
