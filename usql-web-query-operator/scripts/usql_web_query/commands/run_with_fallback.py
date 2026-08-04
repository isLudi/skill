"""Explicit two-attempt query execution with one governed engine fallback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from usql_web_query.commands.run import RunCommandOutcome, execute_run
from usql_web_query.engine_fallback import (
    FallbackEngineResolution,
    decide_fallback,
    resolve_fallback_engine,
)
from usql_web_query.query_contract import load_query_plan_contract
from usql_web_query.query_execution_group import (
    build_attempt_record,
    build_query_execution_group_artifact,
    write_query_execution_group_artifact,
)
from usql_web_query.sql_utils import read_sql


ROW_RESULT_STATES = {
    "success_with_rows",
    "success_ui_missing_recovered",
    "success_with_rows_ui",
}


def _attempt_args(
    args: argparse.Namespace,
    *,
    engine: str,
    attempts_root: Path,
    download: bool,
) -> argparse.Namespace:
    values = dict(vars(args))
    values.update(
        {
            "engine": engine,
            "artifacts_dir": attempts_root,
            "download": download,
            "policy_report": None,
            "trace_file": None,
            "result_artifact": None,
        }
    )
    return argparse.Namespace(**values)


def _write_group(
    *,
    path: Path,
    resolution: FallbackEngineResolution,
    empty_result_policy: str,
    attempts: list[dict[str, Any]],
    final_status: str,
    final_ok: bool,
    selected_attempt: int | None,
    fallback_trigger: str | None,
    eligibility_reason: str,
    alternate_result_adopted: bool,
    cross_engine_consistency: str,
) -> dict[str, Any]:
    artifact = build_query_execution_group_artifact(
        resolution=resolution,
        empty_result_policy=empty_result_policy,
        attempts=attempts,
        final_status=final_status,
        final_ok=final_ok,
        selected_attempt=selected_attempt,
        fallback_trigger=fallback_trigger,
        eligibility_reason=eligibility_reason,
        alternate_result_adopted=alternate_result_adopted,
        cross_engine_consistency=cross_engine_consistency,
    )
    write_query_execution_group_artifact(path, artifact)
    return artifact


def _public_attempt(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "attempt_no": record["attempt_no"],
        "role": record["role"],
        "engine": record["engine"],
        "query_id": record["query_id"],
        "status": record["status"],
        "ok": record["ok"],
        "result_state": record["result_state"],
        "transient_error_code": record["transient_error_code"],
        "result_artifact": record["result_artifact"],
    }


def _emit_summary(
    *,
    artifact: dict[str, Any],
    artifact_path: Path,
    group_dir: Path,
    outcomes: list[RunCommandOutcome],
    fallback_start_error: str | None = None,
) -> None:
    selected_no = artifact["final"]["selected_attempt"]
    selected = (
        outcomes[selected_no - 1].summary.to_dict()
        if isinstance(selected_no, int) and selected_no <= len(outcomes)
        else None
    )
    diagnostic = outcomes[-1].summary.to_dict() if not artifact["final"]["ok"] else None
    if diagnostic is not None and artifact["fallback_policy"]["empty_result_policy"] == "crosscheck-only":
        diagnostic["result_preview"] = None
        diagnostic["download_path"] = None
        diagnostic["crosscheck_only"] = True
        diagnostic["alternate_result_adopted"] = False
    payload = {
        "ok": artifact["final"]["ok"],
        "status": artifact["final"]["status"],
        "artifacts_dir": str(group_dir),
        "execution_group_artifact": {
            "path": str(artifact_path),
            "group_id": artifact["group_id"],
            "artifact_sha256": artifact["artifact_sha256"],
        },
        "attempts": [_public_attempt(item) for item in artifact["attempts"]],
        "selected_result": selected,
        "diagnostic_result": diagnostic,
        "fallback_start_error": fallback_start_error,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_run_with_fallback(args: argparse.Namespace) -> int:
    sql = read_sql(args.sql_file)
    domain = None
    if args.query_plan is not None:
        domain = load_query_plan_contract(args.query_plan, sql).domain
    resolution = resolve_fallback_engine(
        args.engine,
        requested_fallback=args.fallback_engine,
        domain=domain,
    )
    ensure_runtime([args.artifacts_dir])
    group_dir = safe_artifact_dir(args.artifacts_dir / "fallback-groups")
    attempts_root = group_dir / "attempts"
    ensure_runtime([attempts_root])
    artifact_path = args.group_artifact or group_dir / "query_execution_group.json"

    primary = execute_run(
        _attempt_args(
            args,
            engine=resolution.primary_engine,
            attempts_root=attempts_root,
            download=args.download,
        )
    )
    outcomes = [primary]
    decision = decide_fallback(primary.summary)
    primary_record = build_attempt_record(
        primary,
        attempt_no=1,
        role="primary",
        transient_error_code=decision.transient_error_code,
    )
    attempts = [primary_record]

    should_crosscheck = (
        primary.summary.result_state == "success_empty_verified"
        and args.empty_result_policy == "crosscheck-only"
    )
    if primary.summary.ok and not should_crosscheck:
        final_status = (
            "primary_empty_verified"
            if primary.summary.result_state == "success_empty_verified"
            else "primary_success"
        )
        artifact = _write_group(
            path=artifact_path,
            resolution=resolution,
            empty_result_policy=args.empty_result_policy,
            attempts=attempts,
            final_status=final_status,
            final_ok=True,
            selected_attempt=1,
            fallback_trigger=None,
            eligibility_reason=(
                "verified_empty_stop"
                if primary.summary.result_state == "success_empty_verified"
                else "primary_succeeded"
            ),
            alternate_result_adopted=False,
            cross_engine_consistency="not_checked",
        )
        _emit_summary(
            artifact=artifact,
            artifact_path=artifact_path,
            group_dir=group_dir,
            outcomes=outcomes,
        )
        return 0

    fallback_trigger = "success_empty_crosscheck" if should_crosscheck else decision.trigger
    if not should_crosscheck and not decision.eligible:
        artifact = _write_group(
            path=artifact_path,
            resolution=resolution,
            empty_result_policy=args.empty_result_policy,
            attempts=attempts,
            final_status="primary_failed_not_eligible",
            final_ok=False,
            selected_attempt=None,
            fallback_trigger=None,
            eligibility_reason=decision.reason_code,
            alternate_result_adopted=False,
            cross_engine_consistency="not_checked",
        )
        _emit_summary(
            artifact=artifact,
            artifact_path=artifact_path,
            group_dir=group_dir,
            outcomes=outcomes,
        )
        return 1

    try:
        fallback = execute_run(
            _attempt_args(
                args,
                engine=resolution.fallback_engine,
                attempts_root=attempts_root,
                download=False if should_crosscheck else args.download,
            )
        )
    except UsageError as exc:
        artifact = _write_group(
            path=artifact_path,
            resolution=resolution,
            empty_result_policy=args.empty_result_policy,
            attempts=attempts,
            final_status="fallback_not_started",
            final_ok=False,
            selected_attempt=None,
            fallback_trigger=fallback_trigger,
            eligibility_reason=(
                "explicit_crosscheck_only" if should_crosscheck else decision.reason_code
            ),
            alternate_result_adopted=False,
            cross_engine_consistency="inconclusive" if should_crosscheck else "not_checked",
        )
        _emit_summary(
            artifact=artifact,
            artifact_path=artifact_path,
            group_dir=group_dir,
            outcomes=outcomes,
            fallback_start_error=str(exc),
        )
        return 1

    outcomes.append(fallback)
    fallback_decision = decide_fallback(fallback.summary)
    attempts.append(
        build_attempt_record(
            fallback,
            attempt_no=2,
            role="crosscheck" if should_crosscheck else "fallback",
            transient_error_code=fallback_decision.transient_error_code,
        )
    )

    if should_crosscheck:
        if fallback.summary.result_state == "success_empty_verified" and fallback.summary.ok:
            final_status = "crosscheck_empty_consistent"
            final_ok = True
            selected_attempt = 1
            consistency = "consistent_empty"
        elif fallback.summary.result_state in ROW_RESULT_STATES and fallback.summary.ok:
            final_status = "cross_engine_data_divergence"
            final_ok = False
            selected_attempt = None
            consistency = "divergent"
        else:
            final_status = "crosscheck_inconclusive"
            final_ok = False
            selected_attempt = None
            consistency = "inconclusive"
        artifact = _write_group(
            path=artifact_path,
            resolution=resolution,
            empty_result_policy=args.empty_result_policy,
            attempts=attempts,
            final_status=final_status,
            final_ok=final_ok,
            selected_attempt=selected_attempt,
            fallback_trigger=fallback_trigger,
            eligibility_reason="explicit_crosscheck_only",
            alternate_result_adopted=False,
            cross_engine_consistency=consistency,
        )
        _emit_summary(
            artifact=artifact,
            artifact_path=artifact_path,
            group_dir=group_dir,
            outcomes=outcomes,
        )
        return 0 if final_ok else 1

    fallback_ok = fallback.summary.ok
    artifact = _write_group(
        path=artifact_path,
        resolution=resolution,
        empty_result_policy=args.empty_result_policy,
        attempts=attempts,
        final_status="fallback_success" if fallback_ok else "fallback_failed",
        final_ok=fallback_ok,
        selected_attempt=2 if fallback_ok else None,
        fallback_trigger=fallback_trigger,
        eligibility_reason=decision.reason_code,
        alternate_result_adopted=fallback_ok,
        cross_engine_consistency="not_checked",
    )
    _emit_summary(
        artifact=artifact,
        artifact_path=artifact_path,
        group_dir=group_dir,
        outcomes=outcomes,
    )
    return 0 if fallback_ok else 1
