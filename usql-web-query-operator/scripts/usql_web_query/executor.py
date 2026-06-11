"""Query submission operations."""

from __future__ import annotations

import time
from typing import Any

from _shared.errors import UsageError

from .error_detection import ImmediatePlatformError, _is_immediate_platform_error, extract_error_from_page
from .page_helpers import dismiss_nps_if_present, get_sql_frame
from .query_history import _history_matches_sql, extract_open_query_tab_ids, extract_query_history_rows


def _query_submission_detected(page: Any, existing_query_ids: set[str] | None, expected_sql: str | None = None) -> bool:
    if existing_query_ids is None:
        return True
    if any(query_id not in existing_query_ids for query_id in extract_open_query_tab_ids(page)):
        return True
    return any(
        row.get("query_id") not in existing_query_ids
        for row in extract_query_history_rows(page)
        if row.get("query_id") and _history_matches_sql(row.get("text", ""), expected_sql)
    )

def _after_click_submitted(
    page: Any,
    existing_query_ids: set[str] | None,
    expected_sql: str | None = None,
    wait_ms: int = 3000,
) -> bool:
    deadline = time.monotonic() + max(wait_ms, 0) / 1000
    poll_ms = 250
    while True:
        if _query_submission_detected(page, existing_query_ids, expected_sql):
            return True
        error_details = extract_error_from_page(page)
        if _is_immediate_platform_error(error_details):
            raise ImmediatePlatformError(error_details)
        if time.monotonic() >= deadline:
            break
        page.wait_for_timeout(poll_ms)
    final_error_details = extract_error_from_page(page)
    if _is_immediate_platform_error(final_error_details):
        raise ImmediatePlatformError(final_error_details)
    return False

def _submit_with_shortcut(page: Any, existing_query_ids: set[str] | None, expected_sql: str | None = None) -> bool:
    """Submit the selected SQL with the platform shortcut.

    The SQL page supports Ctrl+E for execution. Focusing CodeMirror and
    selecting all first keeps the behavior aligned with the run-button path.
    """
    for frame_obj in page.frames:
        if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
            continue
        try:
            focused = frame_obj.evaluate(
                """() => {
                    const cmEl = document.querySelector('.CodeMirror');
                    if (!cmEl || !cmEl.CodeMirror) return false;
                    const cm = cmEl.CodeMirror;
                    cm.focus();
                    cm.execCommand('selectAll');
                    return true;
                }"""
            )
            if focused:
                page.keyboard.press("Control+E")
                return _after_click_submitted(page, existing_query_ids, expected_sql, wait_ms=5000)
        except Exception:
            continue
    return False

def click_run(page: Any, existing_query_ids: set[str] | None = None, expected_sql: str | None = None) -> None:
    # The run button is inside the /sql/ iframe (CodeMirror editor toolbar).
    frame = get_sql_frame(page)
    dismiss_nps_if_present(page)

    if _submit_with_shortcut(page, existing_query_ids, expected_sql):
        return

    preferred_button_selectors = [
        ".antd-pro-src-components-editor-index-optBtnGroup button:has(.anticon-play-circle)",
        "button.antd-pro-src-components-editor-index-editorBtn:has(.anticon-play-circle)",
        "button:has([aria-label='play-circle'])",
        "button:has(.anticon-play-circle)",
        "button:has(svg[data-icon='play-circle'])",
    ]
    for selector in preferred_button_selectors:
        locator = frame.locator(selector)
        try:
            if locator.count() > 0:
                locator.first.click(timeout=5000)
                if _after_click_submitted(page, existing_query_ids, expected_sql):
                    return
        except Exception:
            continue

    for frame_obj in page.frames:
        if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
            continue
        try:
            center = frame_obj.evaluate(
                """() => {
                    const icon = document.querySelector('[aria-label="play-circle"], [aria-label*="play"], .anticon-play-circle, .anticon-caret-right');
                    if (!icon) return null;
                    const target = icon.closest('button, [role="button"], [class*="editorBtn"]') || icon.parentElement;
                    if (!target) return null;
                    const rect = target.getBoundingClientRect();
                    return {
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                    };
                }"""
            )
            iframe_box = page.locator('iframe[src^="/sql/"]').first.bounding_box()
            if center and iframe_box:
                page.mouse.click(iframe_box["x"] + center["x"], iframe_box["y"] + center["y"])
                if _after_click_submitted(page, existing_query_ids, expected_sql):
                    return
        except Exception:
            continue

    selectors = [
        "[aria-label='play-circle']",
        "[aria-label*='play']",
        ".anticon-play-circle",
        ".anticon-caret-right",
        "[title*='运行']",
        "[aria-label*='运行']",
        "button:has-text('运行')",
    ]
    for selector in selectors:
        for scope in (frame, page):
            locator = scope.locator(selector)
            try:
                if locator.count() > 0:
                    locator.first.click(timeout=3000)
                    if _after_click_submitted(page, existing_query_ids, expected_sql):
                        return
            except Exception:
                continue

    # Last resort: dispatch DOM events. This can be ignored by React because it
    # is not a trusted user action, so keep it after Playwright mouse clicks.
    for frame_obj in page.frames:
        if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
            continue
        try:
            clicked = frame_obj.evaluate(
                """() => {
                    const icon = document.querySelector('[aria-label="play-circle"], [aria-label*="play"], .anticon-play-circle, .anticon-caret-right');
                    if (!icon) return false;
                    const target = icon.closest('button, [role="button"], [class*="editorBtn"]') || icon.parentElement;
                    if (!target) return false;
                    target.dispatchEvent(new MouseEvent('mouseover', {bubbles: true, cancelable: true, view: window}));
                    target.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window}));
                    target.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window}));
                    target.click();
                    return true;
                }"""
            )
            if clicked:
                if _after_click_submitted(page, existing_query_ids, expected_sql):
                    return
        except Exception:
            continue

    raise UsageError("Run button was found, but no new query was submitted. Rerun with --headed --debug-artifacts.")
