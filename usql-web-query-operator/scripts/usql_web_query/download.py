"""Download policy and UI operations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from _shared.errors import UsageError

from .artifact_validation import DownloadArtifactError, validate_download_bytes, validate_download_file
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

def _filename_from_disposition(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    match = re.search(r"filename\*=UTF-8''([^;]+)|filename=\"?([^\";]+)", value)
    if not match:
        return fallback
    filename = match.group(1) or match.group(2) or fallback
    filename = re.sub(r'[<>:"/\\|?*]+', "_", filename).strip()
    return filename or fallback

def _download_via_result_api(
    page: Any,
    artifacts_dir: Path,
    query_id: str | None,
    *,
    expected_rows: int | None = None,
    expected_columns: int | None = None,
) -> str | None:
    if not query_id:
        return None
    request = page.context.request
    check_url = "https://uanalysis.baijia.com/uanalysis-sql/api/result/download/check"
    download_url = "https://uanalysis.baijia.com/uanalysis-sql/api/result/download"
    try:
        check_resp = request.get(check_url, params={"id": query_id}, timeout=60_000)
        check_body = check_resp.json()
        if not check_resp.ok or check_body.get("errorCode") != 0 or not check_body.get("data"):
            return None

        # The platform's Excel artifact can be header-only while the raw CSV
        # artifact contains the full result. Prefer CSV for correctness.
        result_resp = request.get(download_url, params={"id": query_id, "type": "1"}, timeout=60_000)
        result_body = result_resp.json()
        if not result_resp.ok or result_body.get("errorCode") != 0:
            return None
        signed_url = result_body.get("data")
        if not signed_url:
            return None

        file_resp = request.get(signed_url, timeout=120_000)
        content = file_resp.body()
        if not file_resp.ok or not content:
            return None
        validate_download_bytes(
            content,
            expected_format="csv",
            expected_rows=expected_rows,
            expected_columns=expected_columns,
        )
        fallback = f"usql_result_{query_id}.csv"
        filename = _filename_from_disposition(file_resp.headers.get("content-disposition"), fallback)
        if not filename.lower().endswith(".csv"):
            filename = f"{filename}.csv"
        target = artifacts_dir / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target)
    except DownloadArtifactError:
        raise
    except Exception:
        return None

def _validate_saved_excel(
    target: Path,
    *,
    expected_rows: int | None,
    expected_columns: int | None,
) -> str:
    try:
        validate_download_file(
            target,
            expected_format="xlsx",
            expected_rows=expected_rows,
            expected_columns=expected_columns,
        )
    except DownloadArtifactError:
        target.unlink(missing_ok=True)
        raise
    return str(target)


def click_download_button(
    page: Any,
    artifacts_dir: Path,
    query_id: str | None = None,
    *,
    expected_rows: int | None = None,
    expected_columns: int | None = None,
):
    """Download and validate a direct result artifact.

    The result API CSV is preferred. If that path is unavailable, the UI Excel
    artifact is accepted only after workbook structure and row/header checks.
    """
    frame = get_sql_frame(page)
    direct_download = _download_via_result_api(
        page,
        artifacts_dir,
        query_id,
        expected_rows=expected_rows,
        expected_columns=expected_columns,
    )
    if direct_download:
        return direct_download

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
                        return _validate_saved_excel(
                            target,
                            expected_rows=expected_rows,
                            expected_columns=expected_columns,
                        )
                    except DownloadArtifactError:
                        raise
                    except Exception:
                        pass
                    clicked = True
                    break
            except DownloadArtifactError:
                raise
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
    return _validate_saved_excel(
        target,
        expected_rows=expected_rows,
        expected_columns=expected_columns,
    )
