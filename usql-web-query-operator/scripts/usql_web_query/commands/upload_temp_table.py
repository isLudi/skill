"""Upload a local CSV/Excel file into the SQL page temporary-table area."""

from __future__ import annotations

import argparse
import hashlib
import re
import time
from urllib.parse import urlparse

from _shared.browser import import_playwright, launch_context
from _shared.debug import save_debug_artifacts
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from usql_web_query.temp_table_upload import (
    TempTableUploadSummary,
    advance_to_mapping,
    advance_to_target_form,
    choose_file_type,
    close_import_history,
    configure_target_table,
    infer_file_type,
    infer_target_table,
    install_reuse_request_guard,
    matching_table_ids,
    navigate_query_page,
    open_temp_table_panel,
    open_upload_wizard,
    start_import_and_wait,
    upload_source_file,
    validate_mapping_fields,
    validate_upload_file,
    wait_for_sql_frame,
)
from usql_web_query.manual_table_registry import ManualTableRegistry
from usql_web_query.manual_table_validation import validate_manual_table
from usql_web_query.query_auth import query_credentials, verify_query_identity


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_file_unchanged(path, expected):
    actual = file_sha256(path)
    if actual != expected:
        raise UsageError("Temporary-table input file SHA-256 changed before import.")
    return actual


def assert_import_row_count(history_row, expected):
    if expected is None:
        return
    value = str(history_row.get("数据量") or history_row.get("row_count") or "").replace(",", "").strip()
    if not value.isdigit() or int(value) != expected:
        raise UsageError(f"Import history row count does not match expected {expected}: {value!r}")


def cmd_upload_temp_table(args: argparse.Namespace) -> int:
    username, password = query_credentials(args.env_file, args.username, args.password)
    expected_account = args.expected_account or username
    if args.expected_account and username and args.expected_account.casefold() != username.casefold():
        raise UsageError("Configured USQL account does not match the expected upload account.")
    args.username, args.password = username, password
    file_path = args.file.resolve()
    file_type = args.file_type or infer_file_type(file_path)
    validate_upload_file(file_path, file_type)
    if args.expected_file_sha256 and not re.fullmatch(r"[0-9a-fA-F]{64}", args.expected_file_sha256):
        raise UsageError("Expected input file SHA-256 must be 64 hexadecimal characters.")
    if args.expected_data_rows is not None and args.expected_data_rows < 0:
        raise UsageError("Expected data row count must be nonnegative.")
    source_sha256 = file_sha256(file_path)
    if args.expected_file_sha256 and source_sha256 != args.expected_file_sha256.lower():
        raise UsageError("Temporary-table input file SHA-256 does not match the reviewed input.")
    registry = ManualTableRegistry.load(args.registry_path)
    registered_target, manual_entry = registry.infer_target_table(file_path, args.target_table)
    target_table = registered_target or infer_target_table(file_path, args.target_table)
    manual_entry_summary = manual_entry.as_summary() if manual_entry else None
    validation_result = (
        validate_manual_table(file_path, manual_entry)
        if args.validate_manual_table
        else {"checked": False, "ok": True, "status": "skipped", "message": "Manual-table validation disabled.", "issues": []}
    )
    if args.strict_validation and validation_result.get("error_count", 0):
        raise UsageError(f"Manual-table validation failed for {file_path}: {validation_result.get('error_count')} error(s).")

    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    started_at = time.monotonic()
    identity = None
    write_stage = "before_import"
    target_ids: set[str] = set()
    target_table_id = None
    reuse_guard = None

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            def observe_table_list(response):
                if not urlparse(response.url).path.endswith("/tempTable/listTables"):
                    return
                try:
                    target_ids.update(matching_table_ids(response.json(), target_table))
                except Exception:
                    return

            page.on("response", observe_table_list)
            navigate_query_page(page, args, context=context)
            identity = verify_query_identity(page, expected_account)
            frame = wait_for_sql_frame(page)
            open_temp_table_panel(frame)
            open_upload_wizard(frame)
            choose_file_type(frame, file_type)
            upload_source_file(frame, file_path, args.header_row)
            assert_file_unchanged(file_path, source_sha256)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "temp_table_after_file_upload")
            advance_to_target_form(frame, file_path)
            configure_target_table(frame, target_table, args.target_mode, args.import_mode)
            advance_to_mapping(frame, target_table)
            display_alias = None
            if args.target_mode == "reuse":
                if len(target_ids) != 1:
                    raise UsageError("Could not uniquely bind the selected reuse table to a live table ID.")
                target_table_id = next(iter(target_ids))
                if identity and identity.get("account"):
                    display_alias = f"{identity['account']}_{target_table}"
                reuse_guard = install_reuse_request_guard(context, target_table_id, args.import_mode)
            validate_mapping_fields(frame, target_table, verified_display_alias=display_alias)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "temp_table_before_import")
            verify_query_identity(page, expected_account)
            assert_file_unchanged(file_path, source_sha256)
            write_stage = "import_requested"
            history_row = start_import_and_wait(frame, file_path.stem, target_table, args.timeout_ms)
            write_stage = "import_history_observed"
            if reuse_guard is not None and (reuse_guard["attempts"] != 1 or reuse_guard["error"]):
                raise UsageError("Reuse import request was not uniquely verified against the target table ID.")
            assert_import_row_count(history_row, args.expected_data_rows)
            if not args.keep_history_open:
                close_import_history(frame)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "temp_table_after_import")
            summary = TempTableUploadSummary(
                ok=True,
                status="Success",
                message="Temporary table import finished.",
                artifacts_dir=str(artifacts_dir),
                file_path=str(file_path),
                file_name=file_path.name,
                file_type=file_type,
                target_table=target_table,
                target_mode=args.target_mode,
                import_mode=args.import_mode,
                header_row=args.header_row,
                manual_table_entry=manual_entry_summary,
                validation_result=validation_result,
                import_history_row=history_row,
                elapsed_seconds=round(time.monotonic() - started_at, 3),
                identity=identity,
                file_sha256=source_sha256,
                target_table_id=target_table_id,
            )
        except Exception as exc:  # noqa: BLE001
            if args.debug_artifacts:
                try:
                    save_debug_artifacts(page, artifacts_dir, "temp_table_error")
                except Exception:
                    pass
            summary = TempTableUploadSummary(
                ok=False,
                status="Error",
                message=str(exc),
                artifacts_dir=str(artifacts_dir),
                file_path=str(file_path),
                file_name=file_path.name,
                file_type=file_type,
                target_table=target_table,
                target_mode=args.target_mode,
                import_mode=args.import_mode,
                header_row=args.header_row,
                manual_table_entry=manual_entry_summary,
                validation_result=validation_result,
                error_details={"error_type": type(exc).__name__, "write_stage": write_stage,
                               "reuse_guard": reuse_guard},
                elapsed_seconds=round(time.monotonic() - started_at, 3),
                identity=identity,
                file_sha256=source_sha256,
                target_table_id=target_table_id,
            )
        finally:
            browser.close()

    print(summary.to_json())
    return 0 if summary.ok else 1
