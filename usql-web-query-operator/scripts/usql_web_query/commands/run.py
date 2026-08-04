"""Run command orchestration."""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
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
from usql_web_query.engine import recognize_engine_value, switch_query_engine
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
    extract_query_history_ids,
    extract_query_id,
    find_query_history_row,
    lookup_query_history_row_by_text,
)
from usql_web_query.result_panel import _wait_for_result_panel, extract_result_preview
from usql_web_query.result_resolution import resolve_result_state
from usql_web_query.sql_utils import enforce_download_policy_before_run, parse_duration_seconds, read_sql
from usql_web_query.sql_policy import analyze_sql_policy, enforce_sql_policy, write_policy_report
from usql_web_query.status_poller_api import wait_for_query_result_evidence, wait_for_status


@dataclass(frozen=True)
class RunCommandOutcome:
    exit_code: int
    summary: RunSummary
    result_artifact_path: Path
    result_artifact: dict[str, Any]
    query_trace_path: Path
    query_trace: dict[str, Any]


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


def execute_run(args: argparse.Namespace, *, emit_summary: bool = False) -> RunCommandOutcome:
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
        engine_evidence = None
        editor_evidence = None
        submission_evidence = None
        result_evidence = None
        result_state = None
        ui_result_state = None
        completion_source = None
        try:
            run_started_at = time.monotonic()
            page.goto(QUERY_URL, wait_until="domcontentloaded", timeout=45_000)
            if "cas.baijia.com" in page.url or "login" in page.url.lower():
                raise UsageError("Login state expired. Run the login command again.")
            wait_for_query_page(page)
            if args.new_tab:
                create_query_tab(page)
            engine_evidence = switch_query_engine(
                page,
                args.engine,
                timeout_ms=args.engine_ready_timeout_ms,
            )
            selected_engine_label = engine_evidence.selected_label
            editor_evidence = set_monaco_sql(
                page,
                sql,
                timeout_ms=args.editor_ready_timeout_ms,
            )
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "before_run")
            existing_query_ids = extract_query_history_ids(page)
            current_row = None
            try:
                submission_evidence = click_run(
                    page,
                    existing_query_ids,
                    sql,
                    acknowledgement_timeout_ms=args.submission_ack_timeout_ms,
                )
                if (
                    submission_evidence.submitted_sql_sha256 is not None
                    and submission_evidence.submitted_sql_sha256 != editor_evidence.sql_sha256
                ):
                    raise UsageError(
                        "Submitted request SQL hash differs from the verified editor hash: "
                        f"editor={editor_evidence.sql_sha256}, "
                        f"request={submission_evidence.submitted_sql_sha256}, "
                        f"query_id={submission_evidence.query_id}"
                    )
                submitted_engine_key = recognize_engine_value(submission_evidence.submitted_engine)
                if submitted_engine_key and submitted_engine_key != engine_evidence.selected_key:
                    raise UsageError(
                        "Submitted request engine differs from the verified selector engine: "
                        f"selected={engine_evidence.selected_key}, request={submitted_engine_key}, "
                        f"query_id={submission_evidence.query_id}"
                    )
                status, text, error_details, current_row = wait_for_status(
                    page,
                    args.timeout_ms,
                    existing_query_ids,
                    sql,
                    exact_query_id=submission_evidence.query_id,
                )
                completion_source = (current_row or {}).get("completion_source")
            except ImmediatePlatformError as exc:
                error_details = exc.error_details
                status = "Failed"
                text = (error_details.get("detail") or error_details.get("raw_snippet") or "")
            if status == "Timeout":
                page.wait_for_timeout(3000)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "after_run")

            query_id = (
                submission_evidence.query_id
                if submission_evidence is not None
                else (current_row or {}).get("query_id") or extract_query_id(text)
            )

            # The exact-query result API is the primary result source. The UI is
            # secondary evidence and can be absent even when API rows exist.
            result_preview = None
            if status == "Success":
                result_evidence = wait_for_query_result_evidence(
                    page,
                    query_id,
                    timeout_ms=args.result_api_timeout_ms,
                    max_rows=5,
                )
                api_state = result_evidence.get("state")
                ui_wait_ms = 5_000 if api_state in {
                    "success_with_rows",
                    "success_empty_candidate",
                    "success_empty_verified",
                } else args.result_ui_timeout_ms
                ui_result_state = _wait_for_result_panel(
                    page,
                    query_id=query_id,
                    timeout_ms=min(max(args.timeout_ms, 0), ui_wait_ms),
                )
                ui_preview = extract_result_preview(page, query_id=query_id)
                result_state, result_preview, result_evidence = resolve_result_state(
                    result_evidence,
                    ui_preview,
                    completion_source=completion_source,
                )
                if args.debug_artifacts:
                    save_debug_artifacts(page, artifacts_dir, "after_result_panel")
            if query_id:
                current_row = find_query_history_row(page, query_id) or current_row
            if query_id and not current_row:
                current_row = lookup_query_history_row_by_text(page, query_id)
            history_engine = (current_row or {}).get("engine") or None
            query_duration_text = (current_row or {}).get("duration_text") or None
            query_duration_seconds = parse_duration_seconds(query_duration_text)
            download_path = None
            if status == "Success" and args.download and result_state not in {
                "success_empty_verified",
                "result_unresolved",
            }:
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
                if result_state == "success_empty_verified":
                    message = "Query finished with 0 rows verified by the exact-query result API."
                elif result_state == "success_ui_missing_recovered":
                    message = "Query finished; API rows were recovered while the UI result panel was unavailable."
                elif result_state in {"success_with_rows", "success_with_rows_ui"}:
                    message = "Query finished with result rows."
                else:
                    message = (
                        "Query execution succeeded, but the result state could not be verified "
                        "for the bound query ID."
                    )
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
                ok=status == "Success" and result_state != "result_unresolved",
                status=status,
                message=message,
                artifacts_dir=str(artifacts_dir),
                query_id=query_id,
                result_preview=result_preview,
                download_path=download_path,
                error_details=error_details,
                requested_engine=args.engine,
                selected_engine_label=selected_engine_label,
                selected_engine_key=engine_evidence.selected_key if engine_evidence else None,
                history_engine=history_engine,
                query_duration_text=query_duration_text,
                query_duration_seconds=query_duration_seconds,
                elapsed_seconds=elapsed_seconds,
                error_category=error_category,
                error_category_label=error_category_label,
                repair_guidance=repair_guidance,
                editor_evidence=editor_evidence.to_summary() if editor_evidence else None,
                submission_evidence=submission_evidence.to_summary() if submission_evidence else None,
                result_state=result_state,
                result_evidence=result_evidence,
                ui_result_state=ui_result_state,
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
                    query_id=submission_evidence.query_id if submission_evidence else None,
                    error_details=error_details,
                    requested_engine=args.engine,
                    selected_engine_label=engine_evidence.selected_label if engine_evidence else None,
                    selected_engine_key=engine_evidence.selected_key if engine_evidence else None,
                    error_category=error_category,
                    error_category_label=error_category_label,
                    repair_guidance=repair_guidance,
                    editor_evidence=editor_evidence.to_summary() if editor_evidence else None,
                    submission_evidence=submission_evidence.to_summary() if submission_evidence else None,
                    result_state=result_state,
                    result_evidence=result_evidence,
                    ui_result_state=ui_result_state,
                    query_plan_contract=query_plan_contract.to_summary() if query_plan_contract else None,
                )
            else:
                summary = RunSummary(
                    ok=False,
                    status="Error",
                    message=str(exc),
                    artifacts_dir=str(artifacts_dir),
                    query_id=submission_evidence.query_id if submission_evidence else None,
                    error_details=error_details,
                    requested_engine=args.engine,
                    selected_engine_label=engine_evidence.selected_label if engine_evidence else None,
                    selected_engine_key=engine_evidence.selected_key if engine_evidence else None,
                    editor_evidence=editor_evidence.to_summary() if editor_evidence else None,
                    submission_evidence=submission_evidence.to_summary() if submission_evidence else None,
                    result_state=result_state,
                    result_evidence=result_evidence,
                    ui_result_state=ui_result_state,
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
        selected_engine_key=summary.selected_engine_key,
        query_duration_seconds=summary.query_duration_seconds,
        elapsed_seconds=summary.elapsed_seconds,
        result_preview=summary.result_preview,
        editor_evidence=summary.editor_evidence,
        submission_evidence=summary.submission_evidence,
        result_state=summary.result_state,
        result_evidence=summary.result_evidence,
        ui_result_state=summary.ui_result_state,
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
            "result_state": summary.result_state,
            "query_id_source": (summary.submission_evidence or {}).get("query_id_source"),
            "editor_sql_sha256": (summary.editor_evidence or {}).get("sql_sha256"),
            "submitted_sql_sha256": (summary.submission_evidence or {}).get("submitted_sql_sha256"),
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
    if emit_summary:
        print(summary.to_json())
    return RunCommandOutcome(
        exit_code=0 if summary.ok else 1,
        summary=summary,
        result_artifact_path=result_artifact_path,
        result_artifact=result_artifact,
        query_trace_path=trace_path,
        query_trace=trace,
    )


def cmd_run(args: argparse.Namespace) -> int:
    return execute_run(args, emit_summary=True).exit_code
