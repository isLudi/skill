"""Temporary-table upload workflow for the SQL page."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _shared.config import QUERY_URL
from _shared.errors import UsageError

from usql_web_query.page_helpers import dismiss_nps_if_present


TEMP_TABLE_TEXT = "临时表"
BUILD_TABLE_WIZARD_TEXT = "建表向导"
NEXT_TEXT = "下一步"
PREVIOUS_TEXT = "上一步"
CLOSE_TEXT = "关闭"
START_IMPORT_TEXT = "开始导入"
IMPORT_HISTORY_TEXT = "导入历史"
SUCCESS_TEXT = "成功"
FAILED_TEXT = "失败"

FILE_TYPE_EXTENSIONS = {
    "excel": {".xls", ".xlsx"},
    "csv": {".csv"},
}


@dataclass
class TempTableUploadSummary:
    ok: bool
    status: str
    message: str
    artifacts_dir: str
    file_path: str
    file_name: str
    file_type: str
    target_table: str
    target_mode: str
    import_mode: str
    header_row: bool
    import_history_row: dict[str, str] | None = None
    error_details: dict[str, Any] | None = None
    elapsed_seconds: float | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "ok": self.ok,
                "status": self.status,
                "message": self.message,
                "artifacts_dir": self.artifacts_dir,
                "file_path": self.file_path,
                "file_name": self.file_name,
                "file_type": self.file_type,
                "target_table": self.target_table,
                "target_mode": self.target_mode,
                "import_mode": self.import_mode,
                "header_row": self.header_row,
                "import_history_row": self.import_history_row,
                "error_details": self.error_details,
                "elapsed_seconds": self.elapsed_seconds,
            },
            ensure_ascii=False,
            indent=2,
        )


def infer_file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    for file_type, extensions in FILE_TYPE_EXTENSIONS.items():
        if suffix in extensions:
            return file_type
    raise UsageError(f"Unsupported temp-table upload file type: {path.suffix}")


def validate_upload_file(path: Path, file_type: str) -> None:
    if not path.exists():
        raise UsageError(f"Upload file does not exist: {path}")
    if not path.is_file():
        raise UsageError(f"Upload path is not a file: {path}")
    if path.suffix.lower() not in FILE_TYPE_EXTENSIONS[file_type]:
        expected = ", ".join(sorted(FILE_TYPE_EXTENSIONS[file_type]))
        raise UsageError(f"{file_type} upload expects one of: {expected}; got {path.suffix}")
    max_bytes = 50 * 1024 * 1024
    if path.stat().st_size > max_bytes:
        raise UsageError("Upload file exceeds the platform 50MB limit.")


def infer_target_table(file_path: Path, target_table: str | None) -> str:
    if target_table:
        return target_table.strip()
    stem = re.sub(r"[^0-9A-Za-z_]+", "_", file_path.stem).strip("_")
    if not stem:
        raise UsageError("Could not infer a target table name from the upload file.")
    return stem


def navigate_query_page(page: Any, args: Any, context: Any | None = None) -> None:
    """Open the SQL page with a tolerant load strategy.

    The query page can reset the connection while Playwright waits for
    domcontentloaded. Waiting for commit and then for the SQL iframe is more
    stable for this page.
    """
    page.goto(QUERY_URL, wait_until="commit", timeout=45_000)
    page.wait_for_timeout(3_000)
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        from _shared.auth import fill_login_if_present

        fill_login_if_present(page, getattr(args, "username", None), getattr(args, "password", None))
        page.wait_for_timeout(3_000)
        if context is not None:
            context.storage_state(path=str(args.state_path))
        page.goto(QUERY_URL, wait_until="commit", timeout=45_000)
        page.wait_for_timeout(3_000)
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        raise UsageError("Login failed or requires manual verification. Run the login command again.")


def wait_for_sql_frame(page: Any, timeout_ms: int = 45_000) -> Any:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        dismiss_nps_if_present(page)
        for frame in page.frames:
            if "/sql/" not in frame.url:
                continue
            try:
                frame.locator("body").wait_for(state="visible", timeout=2_000)
                return frame
            except Exception:
                pass
        page.wait_for_timeout(500)
    raise UsageError("Timed out waiting for the SQL iframe.")


def click_modal_button(frame: Any, text: str) -> None:
    modal = active_modal(frame)
    modal.get_by_text(text, exact=True).last.click(timeout=10_000)


def active_modal(frame: Any) -> Any:
    modal = frame.locator(".ant-modal").last
    modal.wait_for(state="visible", timeout=20_000)
    return modal


def click_radio(frame: Any, text: str) -> None:
    modal = active_modal(frame)
    modal.locator(".ant-radio-wrapper", has_text=text).first.click(timeout=10_000)


def set_header_row(frame: Any, header_row: bool) -> None:
    checkbox = active_modal(frame).locator("input[type=checkbox]").first
    checked = checkbox.is_checked(timeout=5_000)
    if checked != header_row:
        checkbox.click(timeout=5_000)


def open_temp_table_panel(frame: Any) -> None:
    frame.get_by_text(TEMP_TABLE_TEXT, exact=True).click(timeout=10_000)
    frame.get_by_text("临时表默认库名", exact=False).wait_for(timeout=15_000)


def open_upload_wizard(frame: Any) -> None:
    frame.locator(".anticon-cloud-upload").first.click(timeout=10_000)
    frame.get_by_text(BUILD_TABLE_WIZARD_TEXT, exact=True).click(timeout=10_000)
    active_modal(frame).get_by_text("类型选择", exact=False).wait_for(timeout=15_000)


def choose_file_type(frame: Any, file_type: str) -> None:
    click_radio(frame, file_type)
    click_modal_button(frame, NEXT_TEXT)
    active_modal(frame).get_by_text("源表信息", exact=False).wait_for(timeout=15_000)


def upload_source_file(frame: Any, file_path: Path, header_row: bool) -> None:
    set_header_row(frame, header_row)
    file_input = active_modal(frame).locator("input[type=file]").first
    file_input.set_input_files(str(file_path), timeout=30_000)
    active_modal(frame).get_by_text(file_path.name, exact=False).wait_for(timeout=60_000)
    frame.wait_for_timeout(1_000)


def advance_to_target_form(frame: Any, file_path: Path) -> None:
    click_modal_button(frame, NEXT_TEXT)
    modal = active_modal(frame)
    modal.get_by_text("源文件预览", exact=False).wait_for(timeout=60_000)
    modal.get_by_text("目标：", exact=True).wait_for(timeout=60_000)
    modal.get_by_text("方式：", exact=True).wait_for(timeout=60_000)


def configure_target_table(frame: Any, target_table: str, target_mode: str, import_mode: str) -> None:
    if target_mode == "new":
        click_radio(frame, "新建表")
        fill_new_table_name(frame, target_table)
    elif target_mode == "reuse":
        click_radio(frame, "复用现有表")
        select_existing_table(frame, target_table)
        choose_import_mode(frame, import_mode)
    else:
        raise UsageError(f"Unsupported target mode: {target_mode}")


def fill_new_table_name(frame: Any, target_table: str) -> None:
    modal = active_modal(frame)
    input_box = modal.locator("input.ant-input").first
    current_prefix = _visible_modal_text(frame)
    value = target_table
    match = re.search(r"表名：\s*([A-Za-z0-9]+_)", current_prefix)
    if match and target_table.startswith(match.group(1)):
        value = target_table[len(match.group(1)) :]
    input_box.fill(value, timeout=10_000)


def select_existing_table(frame: Any, target_table: str) -> None:
    modal = active_modal(frame)
    modal.locator(".ant-select-selector").first.click(timeout=10_000)
    search_input = modal.locator(".ant-select-selection-search-input").first
    search_input.fill(target_table, timeout=10_000)
    frame.wait_for_timeout(800)
    click_exact_dropdown_option(frame, target_table)
    active_modal(frame).locator(".ant-select-selection-item", has_text=target_table).first.wait_for(
        state="visible",
        timeout=10_000,
    )


def choose_import_mode(frame: Any, import_mode: str) -> None:
    if import_mode == "overwrite":
        click_radio(frame, "覆盖")
    elif import_mode == "append":
        click_radio(frame, "追加")
    else:
        raise UsageError(f"Unsupported import mode: {import_mode}")


def click_exact_dropdown_option(frame: Any, text: str) -> None:
    dropdown = frame.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").last
    dropdown.wait_for(state="visible", timeout=10_000)
    options = dropdown.locator(".ant-select-item-option-content")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        count = options.count()
        for index in range(count):
            option = options.nth(index)
            try:
                if option.inner_text(timeout=1_000).strip() == text:
                    option.click(timeout=5_000)
                    return
            except Exception:
                continue
        frame.wait_for_timeout(300)
    raise UsageError(f"Could not find target table in dropdown: {text}")


def advance_to_mapping(frame: Any, target_table: str) -> None:
    click_modal_button(frame, NEXT_TEXT)
    modal = active_modal(frame)
    modal.get_by_text("目标表信息", exact=False).wait_for(timeout=30_000)
    modal.get_by_text(START_IMPORT_TEXT, exact=True).wait_for(timeout=30_000)
    if target_table not in _visible_modal_text(frame):
        raise UsageError(f"Field mapping page did not include target table: {target_table}")


def start_import_and_wait(frame: Any, file_stem: str, target_table: str, timeout_ms: int) -> dict[str, str]:
    click_modal_button(frame, START_IMPORT_TEXT)
    active_modal(frame).get_by_text(IMPORT_HISTORY_TEXT, exact=False).wait_for(timeout=30_000)
    return wait_for_import_history(frame, file_stem, target_table, timeout_ms)


def wait_for_import_history(frame: Any, file_stem: str, target_table: str, timeout_ms: int) -> dict[str, str]:
    deadline = time.monotonic() + timeout_ms / 1000
    latest_matching_row: dict[str, str] | None = None
    while time.monotonic() < deadline:
        rows = extract_import_history_rows(frame)
        if rows:
            latest_matching_row = find_matching_history_row(rows, file_stem, target_table)
            if latest_matching_row:
                status = latest_matching_row.get("状态") or latest_matching_row.get("status") or ""
                if SUCCESS_TEXT in status:
                    return latest_matching_row
                if FAILED_TEXT in status:
                    raise UsageError(f"Temporary table import failed: {latest_matching_row}")
        frame.wait_for_timeout(2_000)
    raise UsageError(f"Timed out waiting for import success. Last matching row: {latest_matching_row}")


def extract_import_history_rows(frame: Any) -> list[dict[str, str]]:
    modal = active_modal(frame)
    table = modal.locator("table").first
    if table.count() == 0:
        return []
    headers = [
        normalize_cell_text(value)
        for value in table.locator("thead th").evaluate_all("els => els.map(e => e.innerText)")
    ]
    body_rows = table.locator("tbody tr")
    rows: list[dict[str, str]] = []
    for row_index in range(body_rows.count()):
        cells = [
            normalize_cell_text(value)
            for value in body_rows.nth(row_index).locator("td").evaluate_all("els => els.map(e => e.innerText)")
        ]
        if not any(cells):
            continue
        row: dict[str, str] = {}
        for cell_index, value in enumerate(cells):
            key = headers[cell_index] if cell_index < len(headers) and headers[cell_index] else f"col_{cell_index}"
            row[key] = value
        rows.append(row)
    return rows


def find_matching_history_row(rows: list[dict[str, str]], file_stem: str, target_table: str) -> dict[str, str] | None:
    for row in rows:
        joined = "\t".join(row.values())
        if file_stem in joined and target_table in joined:
            return row
    for row in rows:
        joined = "\t".join(row.values())
        if file_stem in joined:
            return row
    return rows[0] if rows else None


def close_import_history(frame: Any) -> None:
    modal = active_modal(frame)
    try:
        modal.get_by_text(CLOSE_TEXT, exact=True).click(timeout=5_000)
    except Exception:
        modal.locator(".ant-modal-close").first.click(timeout=5_000)


def normalize_cell_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def _visible_modal_text(frame: Any) -> str:
    return active_modal(frame).inner_text(timeout=10_000)
