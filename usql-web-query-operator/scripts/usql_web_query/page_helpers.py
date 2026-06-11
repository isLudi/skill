"""SQL page and tab helpers."""

from __future__ import annotations

from typing import Any

from _shared.config import QUERY_URL
from _shared.errors import UsageError


def dismiss_nps_if_present(page: Any) -> bool:
    """Close the NPS satisfaction survey modal if it is open.

    Returns True if a modal was found and closed.
    """
    close_selectors = [
        page.locator(".nps-modal-close-icon"),
        page.locator("[class*='nps-modal-close']"),
        page.locator(".nps-modal .ant-modal-close"),
    ]
    for locator in close_selectors:
        try:
            if locator.count() > 0:
                locator.first.click(timeout=3000)
                page.wait_for_timeout(500)
                return True
        except Exception:
            continue

    # Fallback: the NPS survey might show a satisfaction/result page with a button.
    skip_selectors = [
        page.locator(".nps-result-button"),
        page.get_by_text("跳过"),
        page.get_by_text("Skip"),
        page.get_by_text("关闭"),
    ]
    for locator in skip_selectors:
        try:
            if locator.count() > 0:
                locator.first.click(timeout=3000)
                page.wait_for_timeout(500)
                return True
        except Exception:
            continue
    return False

def get_sql_frame(page: Any) -> Any:
    """Return a FrameLocator for the /sql/ iframe that contains the editor."""
    return page.frame_locator('iframe[src^="/sql/"]')

def _sql_frame_ready(page: Any) -> bool:
    """Return True when the /sql/ iframe body is present and non-empty."""
    try:
        frame = page.frame_locator('iframe[src^="/sql/"]')
        frame.locator("body").wait_for(state="visible", timeout=30_000)
        return True
    except Exception:
        return False

def wait_for_query_page(page: Any) -> None:
    page.wait_for_load_state("domcontentloaded", timeout=30_000)
    page.wait_for_timeout(1500)
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        raise UsageError("Still on login page; login state was not established.")

    # Dismiss NPS survey modal before interacting with the page.
    dismiss_nps_if_present(page)
    page.wait_for_timeout(500)

    page.get_by_text("SQL取数", exact=True).click(timeout=15_000)
    page.wait_for_timeout(1000)

    # The SQL editor lives inside an iframe. Wait for it to load.
    dismiss_nps_if_present(page)
    if not _sql_frame_ready(page):
        page.wait_for_timeout(3000)
        _sql_frame_ready(page)

def create_query_tab(page: Any) -> None:
    candidates = [
        page.get_by_text("+", exact=True),
        page.locator(".ant-tabs-nav-add"),
        page.locator("[aria-label='add']"),
        page.locator("button").filter(has_text="+"),
    ]
    for candidate in candidates:
        try:
            if candidate.count() > 0:
                candidate.first.click(timeout=3000)
                page.wait_for_timeout(800)
                return
        except Exception:
            continue
