"""Scoped one-time maintenance sessions and exact non-secret Python patches."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from _shared.config import TIANGONG2_DP_API_BASE
from _shared.errors import UsageError

from .client import Tiangong2ReadOnlyClient
from .editing import (
    _normalized_resource_id,
    _read_python_state,
    _safe_metadata_sha256,
    extract_query_regions,
)
from .publishing import finalize_hash, sha256_json, text_sha256
from .redaction import SECRET_KEY, redact_structure, redact_text
from .scope import ScopedTask


SESSION_PLAN_SCHEMA_VERSION = "tiangong2-task-maintenance-session-plan-v1"
SESSION_SCHEMA_VERSION = "tiangong2-task-maintenance-session-v1"
SESSION_PLAN_OPERATION = "authorize_owned_tiangong2_task_maintenance_session"
PATCH_FILE_SCHEMA_VERSION = "tiangong2-python-exact-patch-v1"
PATCH_PLAN_SCHEMA_VERSION = "tiangong2-task-python-patch-plan-v1"
PATCH_RECEIPT_SCHEMA_VERSION = "tiangong2-task-python-patch-receipt-v1"
PATCH_PLAN_OPERATION = "patch_owned_python_task_non_secret_source"
SAVE_ENDPOINT = "dataDevelop/savePython"
ALLOWED_SESSION_OPERATIONS = (
    "query_sql_save",
    "python_patch_save",
    "submit",
    "publish",
    "execute",
)
MAX_SESSION_MINUTES = 240
MAX_SESSION_EXECUTIONS = 5
MAX_PATCH_REPLACEMENTS = 20
MAX_PATCH_SNIPPET_CHARS = 4096
MAX_PATCH_TOTAL_CHARS = 32768
REASON_PATTERN = re.compile(r"^[\w\u4e00-\u9fff，。；：、（）()\- ]{1,200}$")


def _scope_payload(task: ScopedTask) -> dict[str, Any]:
    return {
        "project_id": task.project_id,
        "folder": task.folder_name,
        "menu_id": task.menu_id,
        "task_id": task.task_id,
        "nezha_task_id": task.nezha_task_id,
        "task_name": task.task_name,
        "path": list(task.path),
        "owner_name": task.owner_name,
    }


def _validate_scope(scope: dict[str, Any]) -> None:
    required = (
        "project_id",
        "folder",
        "menu_id",
        "task_id",
        "nezha_task_id",
        "task_name",
        "owner_name",
    )
    if any(scope.get(key) in (None, "", 0) for key in required):
        raise UsageError("Tiangong2 maintenance scope is incomplete")


def _parse_iso_datetime(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise UsageError(f"Tiangong2 maintenance {label} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise UsageError(f"Tiangong2 maintenance {label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _version_ids(reader: Tiangong2ReadOnlyClient, task: ScopedTask) -> list[int]:
    return sorted(
        {
            int(item.get("id") or 0)
            for item in reader.list_versions(task.task_id)
            if int(item.get("id") or 0) > 0
        }
    )


def build_maintenance_session_plan(
    reader: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    identity: dict[str, Any],
    reason: str,
    duration_minutes: int,
    max_executions: int,
    baseline_execution_ids: list[int],
) -> dict[str, Any]:
    reason = reason.strip()
    if not REASON_PATTERN.fullmatch(reason):
        raise UsageError("Tiangong2 maintenance reason is empty, too long, or contains unsupported characters")
    if not 15 <= duration_minutes <= MAX_SESSION_MINUTES:
        raise UsageError(
            f"Tiangong2 maintenance duration must be between 15 and {MAX_SESSION_MINUTES} minutes"
        )
    if not 1 <= max_executions <= MAX_SESSION_EXECUTIONS:
        raise UsageError(
            f"Tiangong2 maintenance execution budget must be between 1 and {MAX_SESSION_EXECUTIONS}"
        )
    source, resource_id = _read_python_state(reader, task)
    regions = extract_query_regions(source)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(minutes=duration_minutes)
    payload = {
        "schema_version": SESSION_PLAN_SCHEMA_VERSION,
        "operation": SESSION_PLAN_OPERATION,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "status": "ready",
        "read_only_plan": True,
        "remote_mutations": 0,
        "identity": {key: identity.get(key) for key in ("id", "name", "displayName")},
        "scope": _scope_payload(task),
        "authorization": {
            "reason": reason,
            "allowed_operations": list(ALLOWED_SESSION_OPERATIONS),
            "max_executions": max_executions,
        },
        "baseline": {
            "current_source_sha256": text_sha256(source),
            "current_query_sha256": text_sha256(regions.query_text.strip("\r\n")),
            "company_default_block_sha256": text_sha256(regions.default_block),
            "task_metadata_sha256": _safe_metadata_sha256(task.metadata),
            "normalized_resource_id": resource_id,
            "version_ids": _version_ids(reader, task),
            "execution_ids": sorted({int(value) for value in baseline_execution_ids}),
        },
        "policy": {
            "exact_owned_task_only": True,
            "one_user_confirmation_covers_allowlisted_phases": True,
            "each_phase_still_requires_an_exact_plan_hash": True,
            "company_default_block_must_remain_byte_identical": True,
            "secret_bearing_patches_are_blocked": True,
            "query_sql_changes_keep_the_sql_quality_gate": True,
            "downstream_trigger_schedule_resource_owner_and_permission_changes_are_blocked": True,
            "session_expiry_and_execution_budget_are_enforced": True,
            "uncertain_remote_mutation_stops_the_session_workflow": True,
        },
    }
    return finalize_hash(payload, "plan_sha256")


def validate_maintenance_session_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != SESSION_PLAN_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 maintenance-session plan schema")
    if plan.get("operation") != SESSION_PLAN_OPERATION:
        raise UsageError("Unsupported Tiangong2 maintenance-session plan operation")
    supplied = str(plan.get("plan_sha256") or "")
    if not supplied or finalize_hash(plan, "plan_sha256").get("plan_sha256") != supplied:
        raise UsageError("Tiangong2 maintenance-session plan SHA-256 validation failed")
    if plan.get("status") != "ready":
        raise UsageError(f"Tiangong2 maintenance-session plan is blocked: {plan.get('status')}")
    _validate_scope(dict(plan.get("scope") or {}))
    authorization = dict(plan.get("authorization") or {})
    if authorization.get("allowed_operations") != list(ALLOWED_SESSION_OPERATIONS):
        raise UsageError("Tiangong2 maintenance-session operation allowlist drifted")
    max_executions = int(authorization.get("max_executions") or 0)
    if not 1 <= max_executions <= MAX_SESSION_EXECUTIONS:
        raise UsageError("Tiangong2 maintenance-session execution budget is invalid")
    created_at = _parse_iso_datetime(str(plan.get("created_at") or ""), "created_at")
    expires_at = _parse_iso_datetime(str(plan.get("expires_at") or ""), "expires_at")
    if expires_at <= created_at or expires_at - created_at > timedelta(minutes=MAX_SESSION_MINUTES):
        raise UsageError("Tiangong2 maintenance-session expiry exceeds the allowed window")


def load_maintenance_session_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Tiangong2 maintenance-session plan: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Tiangong2 maintenance-session plan must be a JSON object")
    validate_maintenance_session_plan(payload)
    return payload


def validate_maintenance_session_activation(
    reader: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
    current_execution_ids: list[int],
) -> dict[str, Any]:
    validate_maintenance_session_plan(plan)
    if datetime.now(timezone.utc) >= _parse_iso_datetime(plan["expires_at"], "expires_at"):
        raise UsageError("Tiangong2 maintenance-session plan expired before activation")
    source, resource_id = _read_python_state(reader, task)
    regions = extract_query_regions(source)
    observed = {
        "current_source_sha256": text_sha256(source),
        "current_query_sha256": text_sha256(regions.query_text.strip("\r\n")),
        "company_default_block_sha256": text_sha256(regions.default_block),
        "task_metadata_sha256": _safe_metadata_sha256(task.metadata),
        "normalized_resource_id": resource_id,
        "version_ids": _version_ids(reader, task),
        "execution_ids": sorted({int(value) for value in current_execution_ids}),
    }
    for field, value in observed.items():
        if value != plan["baseline"].get(field):
            raise UsageError(f"Tiangong2 maintenance-session precondition drifted: {field}")
    return observed


def activate_maintenance_session(
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    confirm_maintenance: bool,
) -> dict[str, Any]:
    validate_maintenance_session_plan(plan)
    if not confirm_maintenance:
        raise UsageError("authorize-task-maintenance-session requires --confirm-maintenance")
    if expected_plan_sha256 != plan["plan_sha256"]:
        raise UsageError(
            "Tiangong2 maintenance-session plan hash mismatch: "
            f"expected={expected_plan_sha256}, actual={plan['plan_sha256']}"
        )
    session = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "authorization_mode": "user_once_exact_task_maintenance",
        "status": "active",
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": plan["expires_at"],
        "source_plan_sha256": plan["plan_sha256"],
        "identity": plan["identity"],
        "scope": plan["scope"],
        "authorization": plan["authorization"],
        "baseline": plan["baseline"],
        "policy": plan["policy"],
    }
    return finalize_hash(session, "session_sha256")


def validate_maintenance_session(session: dict[str, Any]) -> None:
    if session.get("schema_version") != SESSION_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 maintenance-session schema")
    supplied = str(session.get("session_sha256") or "")
    if not supplied or finalize_hash(session, "session_sha256").get("session_sha256") != supplied:
        raise UsageError("Tiangong2 maintenance-session SHA-256 validation failed")
    if session.get("status") != "active":
        raise UsageError(f"Tiangong2 maintenance session is not active: {session.get('status')}")
    if datetime.now(timezone.utc) >= _parse_iso_datetime(session["expires_at"], "expires_at"):
        raise UsageError("Tiangong2 maintenance session expired")
    _validate_scope(dict(session.get("scope") or {}))
    if session.get("authorization", {}).get("allowed_operations") != list(
        ALLOWED_SESSION_OPERATIONS
    ):
        raise UsageError("Tiangong2 maintenance-session operation allowlist drifted")


def load_maintenance_session(path: Path, *, expected_session_sha256: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Tiangong2 maintenance session: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Tiangong2 maintenance session must be a JSON object")
    validate_maintenance_session(payload)
    if expected_session_sha256 != payload["session_sha256"]:
        raise UsageError(
            "Tiangong2 maintenance-session hash mismatch: "
            f"expected={expected_session_sha256}, actual={payload['session_sha256']}"
        )
    return payload


def authorize_phase_with_maintenance_session(
    session: dict[str, Any],
    *,
    phase_plan: dict[str, Any],
    operation: str,
) -> dict[str, Any]:
    validate_maintenance_session(session)
    if operation not in session["authorization"]["allowed_operations"]:
        raise UsageError(f"Tiangong2 maintenance session does not allow operation {operation}")
    session_scope = dict(session["scope"])
    plan_scope = dict(phase_plan.get("scope") or {})
    for field in (
        "project_id",
        "folder",
        "menu_id",
        "task_id",
        "nezha_task_id",
        "task_name",
        "owner_name",
    ):
        if plan_scope.get(field) != session_scope.get(field):
            raise UsageError(f"Tiangong2 maintenance-session scope mismatch: {field}")
    identity_name = str((phase_plan.get("identity") or {}).get("name") or "")
    if identity_name != str((session.get("identity") or {}).get("name") or ""):
        raise UsageError("Tiangong2 maintenance-session identity mismatch")
    if operation == "execute":
        execution_ids = {
            int(value)
            for value in (phase_plan.get("baseline") or {}).get("baseline_execution_ids") or []
        }
        baseline_ids = {int(value) for value in session["baseline"]["execution_ids"]}
        completed_in_session = execution_ids.difference(baseline_ids)
        if len(completed_in_session) >= int(session["authorization"]["max_executions"]):
            raise UsageError("Tiangong2 maintenance-session execution budget is exhausted")
    return {
        "authorization_mode": "maintenance_session",
        "session_sha256": session["session_sha256"],
        "source_plan_sha256": session["source_plan_sha256"],
        "operation": operation,
    }


def validate_live_maintenance_session_source(
    reader: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    session: dict[str, Any],
) -> dict[str, Any]:
    validate_maintenance_session(session)
    source, resource_id = _read_python_state(reader, task)
    regions = extract_query_regions(source)
    observed = {
        "current_source_sha256": text_sha256(source),
        "current_query_sha256": text_sha256(regions.query_text.strip("\r\n")),
        "company_default_block_sha256": text_sha256(regions.default_block),
        "normalized_resource_id": resource_id,
    }
    if (
        observed["company_default_block_sha256"]
        != session["baseline"]["company_default_block_sha256"]
    ):
        raise UsageError("Tiangong2 company default block changed during maintenance session")
    if observed["normalized_resource_id"] != session["baseline"]["normalized_resource_id"]:
        raise UsageError("Tiangong2 resource binding changed during maintenance session")
    return observed


def _load_patch_file(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read UTF-8 Tiangong2 Python patch file: {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != PATCH_FILE_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 Python patch-file schema")
    replacements = payload.get("replacements")
    if not isinstance(replacements, list) or not 1 <= len(replacements) <= MAX_PATCH_REPLACEMENTS:
        raise UsageError("Tiangong2 Python patch must contain 1-20 exact replacements")
    total_chars = 0
    for index, item in enumerate(replacements, start=1):
        if not isinstance(item, dict) or set(item) != {"old", "new", "expected_count"}:
            raise UsageError(f"Tiangong2 Python patch replacement {index} has invalid fields")
        old = item.get("old")
        new = item.get("new")
        if not isinstance(old, str) or not isinstance(new, str) or not old or old == new:
            raise UsageError(f"Tiangong2 Python patch replacement {index} is empty or identical")
        if item.get("expected_count") != 1:
            raise UsageError(f"Tiangong2 Python patch replacement {index} must expect exactly one match")
        if max(len(old), len(new)) > MAX_PATCH_SNIPPET_CHARS:
            raise UsageError(f"Tiangong2 Python patch replacement {index} is too large")
        total_chars += len(old) + len(new)
        if SECRET_KEY.search(old) or SECRET_KEY.search(new):
            raise UsageError(f"Tiangong2 Python patch replacement {index} touches a secret-named region")
        if redact_text(old).findings or redact_text(new).findings:
            raise UsageError(f"Tiangong2 Python patch replacement {index} contains suspected secret material")
    if total_chars > MAX_PATCH_TOTAL_CHARS:
        raise UsageError("Tiangong2 Python patch total size exceeds the safety limit")
    return payload, text_sha256(raw)


def project_python_patch(source: str, patch: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    baseline_regions = extract_query_regions(source)
    try:
        ast.parse(source)
    except SyntaxError as exc:
        raise UsageError(f"Tiangong2 current Python source is not syntax-valid: line {exc.lineno}") from exc
    projected = source
    summary: list[dict[str, Any]] = []
    for index, item in enumerate(patch["replacements"], start=1):
        old = str(item["old"])
        new = str(item["new"])
        count = projected.count(old)
        if count != 1:
            raise UsageError(
                f"Tiangong2 Python patch replacement {index} expected one match but found {count}"
            )
        projected = projected.replace(old, new, 1)
        summary.append(
            {
                "index": index,
                "old_sha256": text_sha256(old),
                "new_sha256": text_sha256(new),
                "old_chars": len(old),
                "new_chars": len(new),
                "match_count": count,
            }
        )
    projected_regions = extract_query_regions(projected)
    if projected_regions.query_text != baseline_regions.query_text:
        raise UsageError("Tiangong2 Python patch cannot change query_sql; use the SQL quality workflow")
    if projected_regions.default_block != baseline_regions.default_block:
        raise UsageError("Tiangong2 Python patch cannot change the company default-parameter block")
    try:
        ast.parse(projected)
    except SyntaxError as exc:
        raise UsageError(f"Tiangong2 projected Python source is not syntax-valid: line {exc.lineno}") from exc
    return projected, summary


def build_python_patch_plan(
    reader: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    identity: dict[str, Any],
    patch_file: Path,
) -> dict[str, Any]:
    source, resource_id = _read_python_state(reader, task)
    patch, patch_file_sha256 = _load_patch_file(patch_file)
    projected, summary = project_python_patch(source, patch)
    regions = extract_query_regions(source)
    payload = {
        "schema_version": PATCH_PLAN_SCHEMA_VERSION,
        "operation": PATCH_PLAN_OPERATION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready",
        "read_only_plan": True,
        "remote_mutations": 0,
        "identity": {key: identity.get(key) for key in ("id", "name", "displayName")},
        "scope": _scope_payload(task),
        "patch": {
            "patch_file": str(patch_file.resolve()),
            "patch_file_sha256": patch_file_sha256,
            "replacement_count": len(summary),
            "replacement_summary": summary,
        },
        "baseline": {
            "current_source_sha256": text_sha256(source),
            "projected_source_sha256": text_sha256(projected),
            "current_query_sha256": text_sha256(regions.query_text.strip("\r\n")),
            "company_default_block_sha256": text_sha256(regions.default_block),
            "task_metadata_sha256": _safe_metadata_sha256(task.metadata),
            "normalized_resource_id": resource_id,
        },
        "policy": {
            "exact_replacements_only": True,
            "patch_text_must_be_non_secret": True,
            "query_sql_unchanged": True,
            "company_default_block_unchanged": True,
            "resource_binding_unchanged": True,
            "projected_python_syntax_required": True,
            "exact_plan_hash_required": True,
            "phase_confirmation_or_active_maintenance_session_required": True,
            "single_save_request": True,
            "full_source_readback_required": True,
        },
    }
    return finalize_hash(payload, "plan_sha256")


def validate_python_patch_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != PATCH_PLAN_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 Python-patch plan schema")
    if plan.get("operation") != PATCH_PLAN_OPERATION:
        raise UsageError("Unsupported Tiangong2 Python-patch plan operation")
    supplied = str(plan.get("plan_sha256") or "")
    if not supplied or finalize_hash(plan, "plan_sha256").get("plan_sha256") != supplied:
        raise UsageError("Tiangong2 Python-patch plan SHA-256 validation failed")
    if plan.get("status") != "ready":
        raise UsageError(f"Tiangong2 Python-patch plan is blocked: {plan.get('status')}")
    _validate_scope(dict(plan.get("scope") or {}))
    if int(plan.get("patch", {}).get("replacement_count") or 0) < 1:
        raise UsageError("Tiangong2 Python-patch plan has no replacements")


def load_python_patch_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Tiangong2 Python-patch plan: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Tiangong2 Python-patch plan must be a JSON object")
    validate_python_patch_plan(payload)
    return payload


@dataclass(frozen=True)
class PythonPatchAuthorization:
    plan_sha256: str
    task_id: int
    identity_name: str
    resource_id: int


def authorize_python_patch(
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    confirmed: bool,
) -> PythonPatchAuthorization:
    validate_python_patch_plan(plan)
    if not confirmed:
        raise UsageError(
            "apply-task-python-patch requires --confirm-save-python-patch or an active maintenance session"
        )
    if expected_plan_sha256 != plan["plan_sha256"]:
        raise UsageError(
            "Tiangong2 Python-patch plan hash mismatch: "
            f"expected={expected_plan_sha256}, actual={plan['plan_sha256']}"
        )
    return PythonPatchAuthorization(
        plan_sha256=plan["plan_sha256"],
        task_id=int(plan["scope"]["task_id"]),
        identity_name=str(plan["scope"]["owner_name"]),
        resource_id=int(plan["baseline"]["normalized_resource_id"]),
    )


class Tiangong2PythonPatchClient:
    """Single-purpose savePython client for one reviewed exact Python patch."""

    def __init__(
        self,
        request_context: Any,
        *,
        authorization: PythonPatchAuthorization,
        dp_api_base: str = TIANGONG2_DP_API_BASE,
    ) -> None:
        if not isinstance(authorization, PythonPatchAuthorization):
            raise UsageError("Tiangong2 Python-patch client requires reviewed authorization")
        self._request = request_context
        self._authorization = authorization
        self._dp_api_base = dp_api_base.rstrip("/")
        self._consumed = False
        self.write_count = 0

    def save_python(self, *, task_id: int, source: str, resource_id: int) -> dict[str, Any]:
        if self._consumed:
            raise UsageError("Tiangong2 Python-patch authorization is single-use")
        if task_id != self._authorization.task_id:
            raise UsageError("Tiangong2 Python-patch task id does not match authorization")
        if resource_id != self._authorization.resource_id:
            raise UsageError("Tiangong2 Python-patch resource id does not match authorization")
        self._consumed = True
        self.write_count = 1
        response = self._request.post(
            f"{self._dp_api_base}/{SAVE_ENDPOINT}",
            form={
                "taskId": str(task_id),
                "python": source,
                "resourceId": str(resource_id),
            },
            timeout=45_000,
        )
        if not getattr(response, "ok", False):
            raise UsageError(
                f"Tiangong2 Python patch failed: HTTP {getattr(response, 'status', '?')} from {SAVE_ENDPOINT}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise UsageError("Tiangong2 Python patch returned a non-object response")
        if body.get("status") != "success" or body.get("errorCode") not in (0, None):
            raise UsageError(
                f"Tiangong2 Python patch failed: {body.get('error') or 'platform returned an error'}"
            )
        safe, _ = redact_structure(body)
        return dict(safe)


def prepare_python_patch(
    reader: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    source, resource_id = _read_python_state(reader, task)
    regions = extract_query_regions(source)
    observed = {
        "current_source_sha256": text_sha256(source),
        "current_query_sha256": text_sha256(regions.query_text.strip("\r\n")),
        "company_default_block_sha256": text_sha256(regions.default_block),
        "task_metadata_sha256": _safe_metadata_sha256(task.metadata),
        "normalized_resource_id": resource_id,
    }
    for field, value in observed.items():
        if value != plan["baseline"].get(field):
            raise UsageError(f"Tiangong2 Python-patch precondition drifted after planning: {field}")
    patch_path = Path(str(plan["patch"]["patch_file"]))
    patch, patch_file_sha256 = _load_patch_file(patch_path)
    if patch_file_sha256 != plan["patch"]["patch_file_sha256"]:
        raise UsageError("Tiangong2 Python patch file hash drifted after planning")
    projected, summary = project_python_patch(source, patch)
    if text_sha256(projected) != plan["baseline"]["projected_source_sha256"]:
        raise UsageError("Tiangong2 projected Python source hash drifted after planning")
    if summary != plan["patch"]["replacement_summary"]:
        raise UsageError("Tiangong2 Python replacement summary drifted after planning")
    return projected, observed


def verify_python_patch_readback(
    reader: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> dict[str, Any]:
    source, resource_id = _read_python_state(reader, task)
    regions = extract_query_regions(source)
    observed = {
        "current_source_sha256": text_sha256(source),
        "current_query_sha256": text_sha256(regions.query_text.strip("\r\n")),
        "company_default_block_sha256": text_sha256(regions.default_block),
        "normalized_resource_id": resource_id,
    }
    expected = plan["baseline"]
    if observed["current_source_sha256"] != expected["projected_source_sha256"]:
        raise UsageError("Tiangong2 Python-patch readback source hash does not match projection")
    for field in (
        "current_query_sha256",
        "company_default_block_sha256",
        "normalized_resource_id",
    ):
        if observed[field] != expected[field]:
            raise UsageError(f"Tiangong2 Python-patch readback changed protected field: {field}")
    return {**observed, "fully_verified": True}
