"""Download policy and UI operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from _shared.errors import UsageError

from .page_helpers import get_sql_frame
from .result_panel import result_page_has_no_data
from .sql_utils import visible_download_limit


def download_allowed(sql: str, result_preview: dict[str, Any] | None) -> tuple[bool, str]:
    limit = visible_download_limit(sql)
    if limit is not None:
        return (limit <= 1000, f"SQL limit={limit}")
    if result_preview and result_preview.get("no_more") and result_preview.get("row_count_visible", 1001) <= 1000:
        return (True, "result page indicates no more rows and visible rows <= 1000")
    return (False, "no SQL limit and result page did not prove <= 1000 rows")

def click_download_button(page: Any, artifacts_dir: Path):
    """Click the download button and select Excel format from the dropdown.

    The platform shows a dropdown with CSV and Excel options after clicking
    the download icon. We select the Excel (.xlsx) option.
    """
    frame = get_sql_frame(page)
    if result_page_has_no_data(page):
        raise UsageError("Result page shows no data; the platform did not expose a downloadable xlsx result.")

    # Step 1: click the download icon to open the dropdown menu.
    download_selectors = [
        ".anticon-download",
        "[aria-label*='download']",
        "button.ant-btn-link.ant-dropdown-trigger",
    ]
    clicked = False
    for selector in download_selectors:
        for scope in (frame, page):
            locator = scope.locator(selector)
            try:
                if locator.count() > 0:
                    try:
                        with page.expect_download(timeout=5000) as direct_download_info:
                            locator.last.click(timeout=5000)
                        download = direct_download_info.value
                        suggested = download.suggested_filename or "usql_result_download.xlsx"
                        target = artifacts_dir / suggested
                        download.save_as(str(target))
                        return str(target)
                    except Exception:
                        pass
                    clicked = True
                    break
            except Exception:
                continue
        if clicked:
            break

    if not clicked:
        raise UsageError("Could not find the download button.")

    # Step 2: wait for the dropdown menu to appear.
    page.wait_for_timeout(800)

    # Step 3: click the Excel option in the dropdown.
    # The dropdown shows lowercase "csv" and "excel" menu items.
    excel_selectors = [
        frame.get_by_text("excel", exact=True),
        frame.get_by_text("Excel", exact=True),
        frame.get_by_text("xlsx", exact=True),
        frame.get_by_text("XLSX", exact=True),
        page.get_by_text("excel", exact=True),
        page.get_by_text("Excel", exact=True),
        page.get_by_text("xlsx", exact=True),
        page.get_by_text("XLSX", exact=True),
        frame.locator(".ant-dropdown-menu-item:has-text('excel')"),
        frame.locator(".ant-dropdown-menu-item:has-text('Excel')"),
        frame.locator(".ant-dropdown-menu-item:has-text('xlsx')"),
        page.locator(".ant-dropdown-menu-item:has-text('excel')"),
        page.locator(".ant-dropdown-menu-item:has-text('Excel')"),
        page.locator(".ant-dropdown-menu-item:has-text('xlsx')"),
    ]
    excel_clicked = False
    with page.expect_download(timeout=30_000) as download_info:
        for selector in excel_selectors:
            try:
                if selector.count() > 0:
                    selector.last.click(timeout=5000)
                    excel_clicked = True
                    break
            except Exception:
                continue

        if not excel_clicked:
            # Fallback: click the last dropdown menu item (which is "excel").
            for scope in (frame, page):
                menu_items = scope.locator(".ant-dropdown-menu-item")
                try:
                    count = menu_items.count()
                    if count >= 2:
                        menu_items.nth(count - 1).click(timeout=3000)
                        excel_clicked = True
                        break
                except Exception:
                    continue

        if not excel_clicked:
            raise UsageError("Could not find the Excel download option in the dropdown.")

    download = download_info.value
    suggested = download.suggested_filename or "usql_result_download.xlsx"
    target = artifacts_dir / suggested
    download.save_as(str(target))
    return str(target)
