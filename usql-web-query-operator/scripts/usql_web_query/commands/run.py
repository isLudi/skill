"""Run command orchestration."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.config import QUERY_URL
from _shared.debug import save_debug_artifacts
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from usql_web_query.artifact_validation import DownloadArtifactError
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
from usql_web_query.query_contract import (
    enforce_query_plan_download_policy,
    load_query_plan_contract,
)
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
from usql_web_query.commands.template_download import download_concrete_sql_via_template_csv


def _download_result_with_template_fallback(
    *,
    page: Any,
    artifacts_dir: Path,
    query_id: str | None,
    expected_rows: int | None,
    expected_columns: int | None,
    state_path: Path,
    sql: str,
    username: str | None,
    password: str | None,
    timeout_ms: int,
) -> tuple[str, dict[str, Any] | None]:
    try:
        path = click_download_button(
            page,
            artifacts_dir,
            query_id=query_id,
            expected_rows=expected_rows,
            expected_columns=expected_columns,
        )
        return str(path), None
    except DownloadArtifactError as exc:
        fallback_path, fallback = download_concrete_sql_via_template_csv(
            page=page,
            state_path=state_path,
            sql=sql,
            artifacts_dir=artifacts_dir,
            username=username,
            password=password,
            timeout_ms=timeout_ms,
        )
        fallback["reason"] = f"{exc.code}: {exc}"
        return str(fallback_path), fallback


def cmd_run(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    sql = read_sql(args.sql_file)
    query_plan_contract = None
    query_plan_path = getattr(args, "query_plan", None)
    if query_plan_path is not None:
        query_plan_contract = load_query_plan_contract(query_plan_path, sql)
        enforce_query_plan_download_policy(query_plan_contract, download=args.download)
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
            download_fallback = None
            if status == "Success" and args.download:
                allowed, reason = download_allowed(sql, result_preview)
                if not allowed:
                    raise UsageError(f"Download blocked by local policy: {reason}")
                expected_rows = None
                expected_columns = None
                if result_preview:
                    visible_rows = result_preview.get("row_count_visible")
                    if isinstance(visible_rows, int) and visible_rows > 0:
                        expected_rows = visible_rows
                    headers = result_preview.get("headers")
                    if isinstance(headers, list) and headers:
                        expected_columns = len(headers)
                download_path, download_fallback = _download_result_with_template_fallback(
                    page=page,
                    artifacts_dir=artifacts_dir,
                    query_id=query_id,
                    expected_rows=expected_rows,
                    expected_columns=expected_columns,
                    state_path=args.state_path,
                    sql=sql,
                    username=getattr(args, "username", None),
                    password=getattr(args, "password", None),
                    timeout_ms=args.timeout_ms,
                )
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
                download_fallback=download_fallback,
                query_plan_contract=query_plan_contract.to_summary() if query_plan_contract else None,
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
                    query_plan_contract=query_plan_contract.to_summary() if query_plan_contract else None,
                )
            else:
                summary = RunSummary(
                    ok=False,
                    status="Error",
                    message=str(exc),
                    artifacts_dir=str(artifacts_dir),
                    error_details=error_details,
                    query_plan_contract=query_plan_contract.to_summary() if query_plan_contract else None,
                )
        finally:
            browser.close()

    print(summary.to_json())
    return 0 if summary.ok else 1
