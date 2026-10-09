"""Receipt-bound, one-attempt reconfirmation after a verified schedule save."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _shared.config import TIANGONG2_TASK_RUNTIME_DIR
from _shared.errors import UsageError

from .artifacts import validate_artifact_root
from .publishing import finalize_hash, sha256_json
from .schedule import _schedule_compare_value, validate_schedule_update_plan


SCOPE_FIELDS = ("project_id", "folder", "menu_id", "task_id", "nezha_task_id", "task_name", "owner_name")


def _read_hashed(path: Path, field: str) -> dict[str, Any]:
    validate_artifact_root(path.parent)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"Cannot read resubmission evidence: {path}") from exc
    if not isinstance(value, dict) or not value.get(field) or finalize_hash(value, field)[field] != value[field]:
        raise UsageError(f"Resubmission evidence SHA-256 validation failed: {path}")
    return value


def _same_scope(value: dict[str, Any], scope: dict[str, Any]) -> None:
    if any((value.get("scope") or {}).get(key) != scope.get(key) for key in SCOPE_FIELDS):
        raise UsageError("Resubmission evidence has a different task scope or owner")


def _receipt_and_plan(path: Path, scope: dict[str, Any], schema: str, operation: str) -> tuple[dict, dict]:
    receipt = _read_hashed(path, "receipt_sha256")
    _same_scope(receipt, scope)
    if receipt.get("schema_version") != schema or receipt.get("operation") != operation:
        raise UsageError("Unsupported resubmission evidence receipt")
    if receipt.get("remote_mutation_confirmed") is not True:
        raise UsageError("Resubmission evidence does not prove a confirmed write")
    plan = _read_hashed(Path(receipt.get("plan_file") or ""), "plan_sha256")
    _same_scope(plan, scope)
    if receipt.get("plan_sha256") != plan["plan_sha256"] or plan.get("operation") != operation:
        raise UsageError("Resubmission receipt does not match its original plan")
    return receipt, plan


def _time(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            raise ValueError("timezone required")
        return parsed
    except ValueError as exc:
        raise UsageError("Resubmission evidence has an invalid timestamp") from exc


def claim_path(evidence: dict[str, Any], scope: dict[str, Any]) -> Path:
    # Independent of receipt filenames and output directories: renaming a
    # receipt or generating another plan must not reset the attempt budget.
    key = sha256_json({"scope": {key: scope[key] for key in SCOPE_FIELDS},
                       "schedule_plan_sha256": evidence["schedule_plan_sha256"]})
    return TIANGONG2_TASK_RUNTIME_DIR / "resubmit-claims" / f"{scope['task_id']}-{key}.json"


def load_resubmission_evidence(*, previous_submit_receipt: Path, schedule_save_receipt: Path,
                               scope: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    prior, prior_plan = _receipt_and_plan(
        previous_submit_receipt, scope, "tiangong2-task-submit-receipt-v1", "submit_saved_owned_tiangong2_task")
    schedule, schedule_plan = _receipt_and_plan(
        schedule_save_receipt, scope, "tiangong2-task-schedule-update-receipt-v1", "update_owned_tiangong2_task_schedule")
    validate_schedule_update_plan(schedule_plan)
    if (prior.get("ok") is not True or prior.get("fully_verified") is not True
            or prior.get("manual_attention_required") is not False
            or prior.get("submit_request_sent") is not True
            or (prior.get("readback") or {}).get("saved_source_unchanged") is not True):
        raise UsageError("Resubmission requires a verified previous submit receipt")
    if prior_plan.get("resubmission"):
        raise UsageError("A resubmission receipt cannot recursively authorize another resubmission")
    prior_state = prior_plan.get("baseline") or {}
    for key in ("current_source_sha256", "current_source_comparison_sha256", "latest_published_version_id"):
        if not prior_state.get(key) or prior_state[key] != baseline.get(key):
            raise UsageError(f"Resubmission source or published version differs from previous submit: {key}")
    matches = baseline.get("matching_unpublished_version_ids") or []
    if (baseline.get("source_matches_latest_published") or len(matches) != 1
            or matches[0] in prior_state.get("baseline_version_ids", [])):
        raise UsageError("Resubmission requires exactly one pending version created after the previous submit plan")
    readback = schedule.get("readback") or {}
    if (schedule.get("save_request_sent") is not True
            or readback.get("configuration_fully_verified") is not True
            or schedule.get("status") not in {"success", "saved_effective_scheduler_mismatch"}):
        raise UsageError("Resubmission requires verified development schedule readback")
    saved = readback.get("schedule") or {}
    desired = schedule_plan["desired"]["schedule"]
    if (saved.get("taskId") != scope["task_id"] or saved.get("scheduleType") != 1
            or _schedule_compare_value(saved) != _schedule_compare_value(desired)
            or _schedule_compare_value(schedule_plan["baseline"]["schedule"]) == _schedule_compare_value(desired)):
        raise UsageError("Resubmission schedule evidence must prove a changed periodic schedule")
    if not (_time(prior["completed_at"]) < _time(schedule["started_at"])
            <= _time(schedule["completed_at"]) <= datetime.now(timezone.utc)):
        raise UsageError("Schedule save must follow the verified submit")
    evidence = {
        "mode": "after_verified_schedule_save",
        "previous_submit_receipt_file": str(previous_submit_receipt.resolve()),
        "previous_submit_receipt_sha256": prior["receipt_sha256"],
        "schedule_save_receipt_file": str(schedule_save_receipt.resolve()),
        "schedule_save_receipt_sha256": schedule["receipt_sha256"],
        "schedule_plan_sha256": schedule_plan["plan_sha256"],
        "saved_schedule": _schedule_compare_value(saved),
        "pending_version_id": matches[0],
    }
    if claim_path(evidence, scope).exists():
        raise UsageError("This schedule save already consumed its single resubmission attempt; inspect its receipt")
    return evidence


def validate_resubmission_evidence(evidence: dict[str, Any], *, scope: dict, baseline: dict) -> None:
    if not isinstance(evidence, dict) or evidence.get("mode") != "after_verified_schedule_save":
        raise UsageError("Unsupported resubmission mode")
    current = load_resubmission_evidence(
        previous_submit_receipt=Path(evidence.get("previous_submit_receipt_file") or ""),
        schedule_save_receipt=Path(evidence.get("schedule_save_receipt_file") or ""),
        scope=scope, baseline=baseline)
    if current != evidence:
        raise UsageError("Resubmission evidence changed after planning")


def verify_resubmission_schedule(reader: Any, operations: Any, *, task: Any, evidence: dict) -> dict:
    if operations is None:
        raise UsageError("Resubmission requires live Nezha schedule readback")
    expected = evidence["saved_schedule"]
    if _schedule_compare_value(reader.get_schedule(task.task_id)) != expected:
        raise UsageError("Development schedule changed since the verified save")
    config = operations.get_schedule_config(task.nezha_task_id)
    effective = operations.get_task_and_schedule(task.nezha_task_id)
    frequency = f"{expected['runInterval']}{ {1: 'h', 2: 'd', 3: 'w'}[expected['timeUnit']]}"
    if (config.get("taskId") != task.nezha_task_id or config.get("periodic") is not True
            or any(config.get(k) != expected[k] for k in ("firstRunTime", "endRunTime", "runInterval", "timeUnit"))
            or effective.get("taskId") != task.nezha_task_id or effective.get("taskName") != task.task_name
            or any(effective.get(k) != expected[k] for k in ("firstRunTime", "endRunTime"))
            or effective.get("scheduleFrequency") != frequency):
        raise UsageError("Effective Nezha schedule does not match the verified development schedule")
    return {"fully_verified": True, "nezha_task_id": task.nezha_task_id,
            "schedule_sha256": sha256_json(expected), "schedule_frequency": frequency}


def consume_resubmission_attempt(plan: dict[str, Any]) -> str | None:
    evidence = plan.get("resubmission")
    if evidence is None:
        return None
    validate_resubmission_evidence(evidence, scope=plan["scope"], baseline=plan["baseline"])
    path = claim_path(evidence, plan["scope"])
    validate_artifact_root(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"plan_sha256": plan["plan_sha256"], "scope": plan["scope"],
               "schedule_plan_sha256": evidence["schedule_plan_sha256"],
               "claimed_at": datetime.now(timezone.utc).isoformat(),
               "status": "attempt_reserved_no_automatic_retry"}
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    except FileExistsError as exc:
        raise UsageError("The schedule save already consumed its single resubmission attempt") from exc
    return str(path.resolve())
