"""Privacy-preserving artifact for a primary query and one fallback attempt."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .commands.run import RunCommandOutcome
from .engine_fallback import FallbackEngineResolution
from .result_artifact import validate_result_artifact


SCHEMA_VERSION = "1.0.0"
SKILLS_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = SKILLS_ROOT / "_shared" / "text2sql_core" / "schemas" / "query_execution_group.schema.json"


def build_attempt_record(
    outcome: RunCommandOutcome,
    *,
    attempt_no: int,
    role: str,
    transient_error_code: str | None = None,
) -> dict[str, Any]:
    artifact = outcome.result_artifact
    summary = outcome.summary
    return {
        "attempt_no": attempt_no,
        "role": role,
        "engine": summary.selected_engine_key or summary.requested_engine,
        "sql_sha256": artifact["sql_sha256"],
        "query_id": summary.query_id,
        "status": summary.status,
        "ok": summary.ok,
        "result_state": summary.result_state,
        "error_category": summary.error_category,
        "transient_error_code": transient_error_code,
        "elapsed_seconds": summary.elapsed_seconds,
        "result_artifact": {
            "path": str(outcome.result_artifact_path),
            "artifact_id": artifact["artifact_id"],
            "artifact_sha256": artifact["artifact_sha256"],
            "validation_status": artifact["validation"]["status"],
        },
        "query_trace": {
            "path": str(outcome.query_trace_path),
            "trace_id": outcome.query_trace["trace_id"],
        },
        "download": artifact.get("download"),
    }


def build_query_execution_group_artifact(
    *,
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
    if not attempts:
        raise ValueError("QueryExecutionGroupArtifact requires at least one completed attempt")
    sql_hashes = {str(item.get("sql_sha256") or "") for item in attempts}
    if len(sql_hashes) != 1:
        raise ValueError("QueryExecutionGroupArtifact attempts must use one exact SQL SHA-256")
    child_identities = [_child_identity(record) for record in attempts]
    domains = {str(item.get("domain") or "unresolved") for item in child_identities}
    plan_ids = {item.get("plan_id") for item in child_identities}
    if len(domains) != 1 or len(plan_ids) != 1:
        raise ValueError("QueryExecutionGroupArtifact child domain or plan identity drifted")
    engines = [item["engine"] for item in attempts]
    if len(engines) != len(set(engines)):
        raise ValueError("QueryExecutionGroupArtifact attempts must use distinct engines")
    artifact: dict[str, Any] = {
        "artifact_type": "query_execution_group",
        "schema_version": SCHEMA_VERSION,
        "group_id": f"query_group_{uuid.uuid4().hex}",
        "artifact_sha256": "",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "domain": next(iter(domains)),
        "plan_id": next(iter(plan_ids)),
        "sql_sha256": next(iter(sql_hashes)),
        "fallback_policy": {
            "mode": "fallback_once",
            "primary_engine": resolution.primary_engine,
            "fallback_engine": resolution.fallback_engine,
            "max_attempts": 2,
            "eligible_triggers": ["result_unresolved", "engine_transient_error"],
            "empty_result_policy": empty_result_policy,
            "resolution_source": resolution.resolution_source,
            "equivalence_group": resolution.equivalence_group,
            "registry_sha256": resolution.registry_sha256,
        },
        "attempts": attempts,
        "final": {
            "status": final_status,
            "ok": final_ok,
            "selected_attempt": selected_attempt,
            "fallback_trigger": fallback_trigger,
            "eligibility_reason": eligibility_reason,
            "alternate_result_adopted": alternate_result_adopted,
            "cross_engine_consistency": cross_engine_consistency,
        },
    }
    artifact["artifact_sha256"] = query_execution_group_sha256(artifact)
    validate_query_execution_group_artifact(artifact)
    return artifact


def _child_identity(attempt: dict[str, Any]) -> dict[str, Any]:
    artifact_path = Path(attempt["result_artifact"]["path"])
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    validate_result_artifact(payload)
    if payload.get("artifact_id") != attempt["result_artifact"]["artifact_id"]:
        raise ValueError(f"Child ResultArtifact ID reference drifted: {artifact_path}")
    if payload.get("artifact_sha256") != attempt["result_artifact"]["artifact_sha256"]:
        raise ValueError(f"Child ResultArtifact hash reference drifted: {artifact_path}")
    if payload.get("sql_sha256") != attempt.get("sql_sha256"):
        raise ValueError(f"Child ResultArtifact SQL hash reference drifted: {artifact_path}")
    if payload.get("query_id") != attempt.get("query_id"):
        raise ValueError(f"Child ResultArtifact query ID reference drifted: {artifact_path}")
    child_engine = payload.get("engine", {}).get("selected_key") or payload.get("engine", {}).get("requested")
    if child_engine != attempt.get("engine"):
        raise ValueError(f"Child ResultArtifact engine reference drifted: {artifact_path}")
    if payload.get("trace_id") != attempt.get("query_trace", {}).get("trace_id"):
        raise ValueError(f"Child ResultArtifact trace ID reference drifted: {artifact_path}")
    return {
        "domain": payload.get("domain") or "unresolved",
        "plan_id": payload.get("plan_id"),
    }


def query_execution_group_sha256(artifact: dict[str, Any]) -> str:
    payload = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def validate_query_execution_group_artifact(artifact: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(artifact),
        key=lambda item: list(item.path),
    )
    if errors:
        rendered = "; ".join(
            f"{'.'.join(map(str, item.path)) or '<root>'}: {item.message}"
            for item in errors
        )
        raise ValueError(f"QueryExecutionGroupArtifact schema validation failed: {rendered}")
    if artifact.get("artifact_sha256") != query_execution_group_sha256(artifact):
        raise ValueError("QueryExecutionGroupArtifact hash is invalid")
    attempt_numbers = [item["attempt_no"] for item in artifact["attempts"]]
    if attempt_numbers != list(range(1, len(attempt_numbers) + 1)):
        raise ValueError("QueryExecutionGroupArtifact attempt numbers must be sequential")
    if artifact["attempts"][0]["role"] != "primary":
        raise ValueError("QueryExecutionGroupArtifact first attempt must be primary")
    policy = artifact["fallback_policy"]
    attempts = artifact["attempts"]
    if attempts[0]["engine"] != policy["primary_engine"]:
        raise ValueError("QueryExecutionGroupArtifact primary engine does not match policy")
    if any(item["sql_sha256"] != artifact["sql_sha256"] for item in attempts):
        raise ValueError("QueryExecutionGroupArtifact attempt SQL hash drifted")
    if len(attempts) == 2:
        if attempts[1]["engine"] != policy["fallback_engine"]:
            raise ValueError("QueryExecutionGroupArtifact fallback engine does not match policy")
        if attempts[1]["role"] not in {"fallback", "crosscheck"}:
            raise ValueError("QueryExecutionGroupArtifact second attempt has an invalid role")
    final = artifact["final"]
    selected_attempt = final["selected_attempt"]
    if isinstance(selected_attempt, int) and selected_attempt > len(attempts):
        raise ValueError("QueryExecutionGroupArtifact selected attempt does not exist")
    if final["alternate_result_adopted"]:
        if len(attempts) != 2 or selected_attempt != 2 or attempts[1]["role"] != "fallback":
            raise ValueError("Only a successful fallback attempt may be adopted")
    if final["fallback_trigger"] == "success_empty_crosscheck":
        if policy["empty_result_policy"] != "crosscheck-only":
            raise ValueError("Empty crosscheck trigger requires crosscheck-only policy")
        if len(attempts) == 2 and attempts[1]["role"] != "crosscheck":
            raise ValueError("Empty crosscheck trigger requires a crosscheck attempt")
    if final["cross_engine_consistency"] != "not_checked" and policy["empty_result_policy"] != "crosscheck-only":
        raise ValueError("Cross-engine consistency is only valid for crosscheck-only policy")
    _validate_final_semantics(artifact)


def _validate_final_semantics(artifact: dict[str, Any]) -> None:
    attempts = artifact["attempts"]
    final = artifact["final"]
    status = final["status"]
    one_attempt_statuses = {
        "primary_success",
        "primary_empty_verified",
        "primary_failed_not_eligible",
        "fallback_not_started",
    }
    if status in one_attempt_statuses and len(attempts) != 1:
        raise ValueError(f"QueryExecutionGroupArtifact {status} must have one attempt")
    if status not in one_attempt_statuses and len(attempts) != 2:
        raise ValueError(f"QueryExecutionGroupArtifact {status} must have two attempts")
    if status == "primary_success" and (
        not final["ok"] or final["selected_attempt"] != 1 or not attempts[0]["ok"]
    ):
        raise ValueError("primary_success must select a successful primary attempt")
    if status == "primary_empty_verified" and (
        not final["ok"]
        or final["selected_attempt"] != 1
        or attempts[0]["result_state"] != "success_empty_verified"
    ):
        raise ValueError("primary_empty_verified must select a verified-empty primary attempt")
    if status == "primary_failed_not_eligible" and (
        final["ok"] or final["selected_attempt"] is not None
    ):
        raise ValueError("primary_failed_not_eligible cannot select a result")
    if status == "fallback_success" and (
        not final["ok"]
        or final["selected_attempt"] != 2
        or not final["alternate_result_adopted"]
        or not attempts[1]["ok"]
    ):
        raise ValueError("fallback_success must adopt a successful fallback attempt")
    if status in {"fallback_failed", "fallback_not_started"} and (
        final["ok"] or final["selected_attempt"] is not None or final["alternate_result_adopted"]
    ):
        raise ValueError(f"{status} cannot select or adopt a result")
    if status.startswith("crosscheck_") or status == "cross_engine_data_divergence":
        if final["alternate_result_adopted"] or attempts[-1]["role"] != "crosscheck":
            raise ValueError("Crosscheck outcomes cannot adopt the alternate result")
    if status == "crosscheck_empty_consistent" and (
        not final["ok"]
        or final["selected_attempt"] != 1
        or any(item["result_state"] != "success_empty_verified" for item in attempts)
    ):
        raise ValueError("crosscheck_empty_consistent requires two verified-empty attempts")
    if status in {"cross_engine_data_divergence", "crosscheck_inconclusive"} and (
        final["ok"] or final["selected_attempt"] is not None
    ):
        raise ValueError(f"{status} cannot select a result")


def write_query_execution_group_artifact(path: Path, artifact: dict[str, Any]) -> None:
    validate_query_execution_group_artifact(artifact)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(artifact, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
