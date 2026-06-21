"""Run command orchestration."""

from __future__ import annotations

import argparse
import time

from _shared.browser import import_playwright, launch_context
from _shared.config import QUERY_URL
from _shared.debug import save_debug_artifacts
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from usql_web_query.download import click_download_button, download_allowed
from usql_web_query.editor import set_monaco_sql
from usql_web_query.engine import switch_query_engine
from usql_web_query.error_detection import (
    ImmediatePlatformError,
    _is_platform_failure_details,
    build_repair_guidance,
    classify_error_details,
    extract_error_from_page,
)
from usql_web_query.executor import click_run
from usql_web_query.models import RunSummary
from usql_web_query.page_helpers import create_query_tab, wait_for_query_page
from usql_web_query.query_history import (
    extract_open_query_tab_ids,
    extract_query_history_ids,
    extract_query_history_rows,
    extract_query_id,
    lookup_query_history_row_by_text,
)
from usql_web_query.result_panel import _wait_for_result_panel, extract_result_preview
from usql_web_query.sql_utils import enforce_download_policy_before_run, parse_duration_seconds, read_sql
from usql_web_query.status_poller_api import wait_for_status


def cmd_run(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    sql = read_sql(args.sql_file)
    enforce_download_policy_before_run(sql, download=args.download)
    sync_playwright, _ = import_playwright(include_timeout_error=True)
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            run_started_at = time.monotonic()
            page.goto(QUERY_URL, wait_until="domcontentloaded", timeout=45_000)
            if "cas.baijia.com" in page.url or "login" in page.url.lower():
                raise UsageError("Login state expired. Run the login command again.")
            wait_for_query_page(page)
            if args.new_tab:
                create_query_tab(page)
            selected_engine_label = switch_query_engine(page, args.engine)
            set_monaco_sql(page, sql)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "before_run")
            existing_query_ids = extract_query_history_ids(page)
            current_row = None
            try:
                click_run(page, existing_query_ids, sql)
                status, text, error_details, current_row = wait_for_status(page, args.timeout_ms, existing_query_ids, sql)
            except ImmediatePlatformError as exc:
                error_details = exc.error_details
                status = "Failed"
                text = (error_details.get("detail") or error_details.get("raw_snippet") or "")
            if status == "Timeout":
                page.wait_for_timeout(3000)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "after_run")

            # After Success, the result panel renders at the bottom of the page
            # after log-loading completes. Wait for it to appear.
            if status == "Success":
                _wait_for_result_panel(page)
                if args.debug_artifacts:
                    save_debug_artifacts(page, artifacts_dir, "after_result_panel")

            query_id = (current_row or {}).get("query_id") or extract_query_id(text)
            if status == "Success" and not query_id:
                new_open_query_ids = extract_open_query_tab_ids(page) - existing_query_ids
                if new_open_query_ids:
                    query_id = sorted(new_open_query_ids)[-1]
            if query_id and not current_row:
                current_row = next(
                    (row for row in extract_query_history_rows(page) if row.get("query_id") == query_id),
                    None,
                )
            if query_id and not current_row:
                current_row = lookup_query_history_row_by_text(page, query_id)
            history_engine = (current_row or {}).get("engine") or None
            query_duration_text = (current_row or {}).get("duration_text") or None
            query_duration_seconds = parse_duration_seconds(query_duration_text)
            result_preview = extract_result_preview(page) if status == "Success" else None
            download_path = None
            if status == "Success" and args.download:
                allowed, reason = download_allowed(sql, result_preview)
                if not allowed:
                    raise UsageError(f"Download blocked by local policy: {reason}")
                download_path = click_download_button(page, artifacts_dir, query_id=query_id)
            if status == "Failed":
                error_details = error_details or extract_error_from_page(page)
                error_category, error_category_label = classify_error_details(error_details)
                repair_guidance = build_repair_guidance(error_details)
                error_title = (error_details or {}).get("title") or "unknown error"
                if error_category_label:
                    message = f"Query failed ({error_category_label}): {error_title}"
                else:
                    message = f"Query failed: {error_title}"
            elif status == "Success":
                message = "Query finished."
                error_category = None
                error_category_label = None
                repair_guidance = None
            else:
                message = "Timed out waiting for query status."
                error_category = None
                error_category_label = None
                repair_guidance = None
            elapsed_seconds = round(time.monotonic() - run_started_at, 3)
            summary = RunSummary(
                ok=status == "Success",
                status=status,
                message=message,
                artifacts_dir=str(artifacts_dir),
                query_id=query_id,
                result_preview=result_preview,
                download_path=download_path,
                error_details=error_details,
                requested_engine=args.engine,
                selected_engine_label=selected_engine_label,
                history_engine=history_engine,
                query_duration_text=query_duration_text,
                query_duration_seconds=query_duration_seconds,
                elapsed_seconds=elapsed_seconds,
                error_category=error_category,
                error_category_label=error_category_label,
                repair_guidance=repair_guidance,
            )
        except Exception as exc:
            if args.debug_artifacts:
                try:
                    save_debug_artifacts(page, artifacts_dir, "error")
                except Exception:
                    pass
            error_details = extract_error_from_page(page)
            if _is_platform_failure_details(error_details):
                error_category, error_category_label = classify_error_details(error_details)
                repair_guidance = build_repair_guidance(error_details)
                error_title = error_details.get("title") or "unknown error"
                summary = RunSummary(
                    ok=False,
                    status="Failed",
                    message=f"Query failed ({error_category_label}): {error_title}" if error_category_label else f"Query failed: {error_title}",
                    artifacts_dir=str(artifacts_dir),
                    error_details=error_details,
                    error_category=error_category,
                    error_category_label=error_category_label,
                    repair_guidance=repair_guidance,
                )
            else:
                summary = RunSummary(
                    ok=False,
                    status="Error",
                    message=str(exc),
                    artifacts_dir=str(artifacts_dir),
                    error_details=error_details,
                )
        finally:
            browser.close()

    print(summary.to_json())
    return 0 if summary.ok else 1
