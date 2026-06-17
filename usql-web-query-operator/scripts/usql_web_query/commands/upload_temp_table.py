"""Upload a local CSV/Excel file into the SQL page temporary-table area."""

from __future__ import annotations

import argparse
import time

from _shared.browser import import_playwright, launch_context
from _shared.debug import save_debug_artifacts
from _shared.env import load_env_file
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
    navigate_query_page,
    open_temp_table_panel,
    open_upload_wizard,
    start_import_and_wait,
    upload_source_file,
    validate_upload_file,
    wait_for_sql_frame,
)
from usql_web_query.manual_table_registry import ManualTableRegistry
from usql_web_query.manual_table_validation import validate_manual_table


def cmd_upload_temp_table(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    file_path = args.file.resolve()
    file_type = args.file_type or infer_file_type(file_path)
    validate_upload_file(file_path, file_type)
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

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            navigate_query_page(page, args, context=context)
            frame = wait_for_sql_frame(page)
            open_temp_table_panel(frame)
            open_upload_wizard(frame)
            choose_file_type(frame, file_type)
            upload_source_file(frame, file_path, args.header_row)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "temp_table_after_file_upload")
            advance_to_target_form(frame, file_path)
            configure_target_table(frame, target_table, args.target_mode, args.import_mode)
            advance_to_mapping(frame, target_table)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "temp_table_before_import")
            history_row = start_import_and_wait(frame, file_path.stem, target_table, args.timeout_ms)
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
                error_details={"error_type": type(exc).__name__},
                elapsed_seconds=round(time.monotonic() - started_at, 3),
            )
        finally:
            browser.close()

    print(summary.to_json())
    return 0 if summary.ok else 1
