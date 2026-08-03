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
    exact_sql_sha256,
    enforce_query_plan_download_policy,
    load_query_plan_contract,
)
from usql_web_query.query_trace_bridge import (
    append_trace_stage,
    bind_execution,
    bind_result_artifact,
    prepare_query_trace,
    write_query_trace,
)
from usql_web_query.result_artifact import build_result_artifact, write_result_artifact
from usql_web_query.query_history import (
    extract_open_query_tab_ids,
    extract_query_history_ids,
    extract_query_history_rows,
    extract_query_id,
    lookup_query_history_row_by_text,
)
from usql_web_query.result_panel import _wait_for_result_panel, extract_result_preview
from usql_web_query.sql_utils import enforce_download_policy_before_run, parse_duration_seconds, read_sql
from usql_web_query.sql_policy import analyze_sql_policy, enforce_sql_policy, write_policy_report
from usql_web_query.status_poller_api import wait_for_status


def _download_result(
    *,
    page: Any,
    artifacts_dir: Path,
    query_id: str | None,
    expected_rows: int | None,
    expected_columns: int | None,
) -> str:
    try:
        path = click_download_button(
            page,
            artifacts_dir,
            query_id=query_id,
            expected_rows=expected_rows,
            expected_columns=expected_columns,
        )
        return str(path)
    except DownloadArtifactError as exc:
        raise UsageError(
            f"Direct download artifact rejected ({exc.code}): {exc}. "
            "No Template Query writes were attempted. If a temporary Template Query write is explicitly "
            "authorized, rerun the concrete SQL with `template-download`; that command always enforces "
            "offline -> delete cleanup."
        ) from exc


def cmd_run(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    sql = read_sql(args.sql_file)
    query_plan_contract = None
    query_plan_path = getattr(args, "query_plan", None)
    if query_plan_path is not None:
        query_plan_contract = load_query_plan_contract(query_plan_path, sql)
        enforce_query_plan_download_policy(query_plan_contract, download=args.download)
    enforce_download_policy_before_run(sql, download=args.download)
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    policy_report = analyze_sql_policy(
        sql,
        mode=getattr(args, "policy_mode", "enforce"),
        required_partition_fields=getattr(args, "required_partition_field", []),
        require_limit=(
            bool(getattr(args, "require_limit", False))
            or bool(
                query_plan_contract
                and query_plan_contract.execution_policy.get("execution_mode") == "exploratory"
            )
        ),
    )
    policy_report_path = getattr(args, "policy_report", None) or artifacts_dir / "sql_policy_report.json"
    write_policy_report(policy_report_path, policy_report)
    trace, trace_path = prepare_query_trace(
        requested_path=getattr(args, "trace_file", None),
        artifacts_dir=artifacts_dir,
        sql_sha256=exact_sql_sha256(sql),
        query_plan_contract=query_plan_contract,
    )
    append_trace_stage(
        trace,
        name="sql_policy",
        status="success" if policy_report["allowed"] else "blocked",
        details={
            "mode": policy_report["mode"],
            "report_sha256": policy_report["report_sha256"],
            "diagnostic_codes": [item["code"] for item in policy_report["diagnostics"]],
        },
    )
    write_query_trace(trace_path, trace)
    try:
        enforce_sql_policy(policy_report)
    except UsageError:
        append_trace_stage(
            trace,
            name="execute",
            status="skipped",
            details={"reason": "sql_policy_blocked"},
        )
        write_query_trace(trace_path, trace)
        raise
    sync_playwright, _ = import_playwright(include_timeout_error=True)

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
                expected_rows = None
                expected_columns = None
                if result_preview:
                    visible_rows = result_preview.get("row_count_visible")
                    if isinstance(visible_rows, int) and visible_rows > 0:
                        expected_rows = visible_rows
                    headers = result_preview.get("headers")
                    if isinstance(headers, list) and headers:
                        expected_columns = len(headers)
                download_path = _download_result(
                    page=page,
                    artifacts_dir=artifacts_dir,
                    query_id=query_id,
                    expected_rows=expected_rows,
                    expected_columns=expected_columns,
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

    result_artifact_path = getattr(args, "result_artifact", None) or artifacts_dir / "result_artifact.json"
    result_artifact = build_result_artifact(
        trace_id=trace["trace_id"],
        domain=query_plan_contract.domain if query_plan_contract else trace["domain"],
        plan_id=query_plan_contract.plan_id if query_plan_contract else None,
        sql_sha256=exact_sql_sha256(sql),
        policy_report_sha256=policy_report["report_sha256"],
        ok=summary.ok,
        status=summary.status,
        query_id=summary.query_id,
        requested_engine=summary.requested_engine,
        selected_engine_label=summary.selected_engine_label,
        history_engine=summary.history_engine,
        query_duration_seconds=summary.query_duration_seconds,
        elapsed_seconds=summary.elapsed_seconds,
        result_preview=summary.result_preview,
        download_path=summary.download_path,
        expected_columns=query_plan_contract.expected_columns if query_plan_contract else (),
    )
    write_result_artifact(result_artifact_path, result_artifact)
    bind_execution(
        trace,
        status=summary.status,
        query_id=summary.query_id,
        engine=summary.history_engine or summary.selected_engine_label or summary.requested_engine,
        elapsed_seconds=summary.elapsed_seconds,
        policy_report_sha256=policy_report["report_sha256"],
    )
    append_trace_stage(
        trace,
        name="execute",
        status="success" if summary.ok else "error",
        duration_ms=(summary.elapsed_seconds * 1000) if summary.elapsed_seconds is not None else None,
        details={
            "status": summary.status,
            "result_validation_status": result_artifact["validation"]["status"],
        },
    )
    bind_result_artifact(
        trace,
        artifact_id=result_artifact["artifact_id"],
        artifact_sha256=result_artifact["artifact_sha256"],
    )
    write_query_trace(trace_path, trace)
    summary.provenance = {
        "query_trace": {
            "path": str(trace_path),
            "trace_id": trace["trace_id"],
        },
        "sql_policy_report": {
            "path": str(policy_report_path),
            "report_sha256": policy_report["report_sha256"],
            "mode": policy_report["mode"],
            "allowed": policy_report["allowed"],
        },
        "result_artifact": {
            "path": str(result_artifact_path),
            "artifact_id": result_artifact["artifact_id"],
            "artifact_sha256": result_artifact["artifact_sha256"],
            "validation_status": result_artifact["validation"]["status"],
        },
    }
    print(summary.to_json())
    return 0 if summary.ok else 1
