"""Hash-bound schedule updates for one exact owned Tiangong2 task."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from _shared.config import TIANGONG2_DP_API_BASE
from _shared.errors import UsageError

from .client import Tiangong2ReadOnlyClient
from .publishing import finalize_hash, sha256_json, text_sha256
from .redaction import redact_structure
from .scope import ScopedTask


PATCH_SCHEMA_VERSION = "tiangong2-task-schedule-patch-v1"
PLAN_SCHEMA_VERSION = "tiangong2-task-schedule-update-plan-v1"
RECEIPT_SCHEMA_VERSION = "tiangong2-task-schedule-update-receipt-v1"
PLAN_OPERATION = "update_owned_tiangong2_task_schedule"
SAVE_ENDPOINT = "task/saveScheduleConfig"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
_TIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

# The editor sends the complete current schedule object.  Only these fields are
# accepted from a patch file; executor, retry, dependency, and concurrency
# settings remain the exact values returned by the read precondition.
PATCHABLE_FIELDS = frozenset(
    {
        "scheduleType",
        "firstRunTime",
        "endRunTime",
        "runInterval",
        "timeUnit",
    }
)


def _safe_schedule(schedule: dict[str, Any]) -> dict[str, Any]:
    safe, _ = redact_structure(schedule)
    if not isinstance(safe, dict):
        raise UsageError("Tiangong2 schedule redaction did not return an object")
    return safe


def schedule_state_sha256(schedule: dict[str, Any]) -> str:
    return text_sha256(
        json.dumps(
            _safe_schedule(schedule),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _schedule_compare_value(schedule: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(schedule)
    # nextRunTime is derived by the platform and is not a user-controlled
    # schedule setting.  The browser preserves the current value in the save
    # payload; comparisons omit it because the platform may recalculate it.
    value.pop("nextRunTime", None)
    return value


def _validate_time(value: Any, field: str, *, allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if not isinstance(value, str) or not _TIME_PATTERN.fullmatch(value):
        raise UsageError(f"Tiangong2 schedule {field} must use YYYY-MM-DD HH:mm:ss")
    try:
        datetime.strptime(value, TIME_FORMAT)
    except ValueError as exc:
        raise UsageError(f"Tiangong2 schedule {field} is not a valid timestamp") from exc


def _validate_change_value(field: str, value: Any) -> None:
    if field in {"firstRunTime", "endRunTime"}:
        _validate_time(value, field, allow_null=field == "endRunTime")
    elif field == "scheduleType":
        if isinstance(value, bool) or not isinstance(value, int) or value not in {0, 1}:
            raise UsageError("Tiangong2 schedule scheduleType must be 0 or 1")
    elif field == "runInterval":
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10000:
            raise UsageError("Tiangong2 schedule runInterval must be an integer from 1 to 10000")
    elif field == "timeUnit":
        if isinstance(value, bool) or not isinstance(value, int) or value not in {1, 2, 3}:
            raise UsageError("Tiangong2 schedule timeUnit must be 1, 2, or 3")
    else:
        raise UsageError(f"Tiangong2 schedule field is not patchable: {field}")


def load_schedule_patch(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Tiangong2 schedule patch: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Tiangong2 schedule patch must be a JSON object")
    if payload.get("schema_version") != PATCH_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 schedule patch schema")
    changes = payload.get("changes")
    if not isinstance(changes, dict) or not changes:
        raise UsageError("Tiangong2 schedule patch requires a non-empty changes object")
    unknown = set(changes) - PATCHABLE_FIELDS
    if unknown:
        raise UsageError(
            "Tiangong2 schedule patch contains non-patchable fields: "
            + ", ".join(sorted(unknown))
        )
    for field, value in changes.items():
        _validate_change_value(str(field), value)
    return {
        "schema_version": PATCH_SCHEMA_VERSION,
        "changes": {str(key): changes[key] for key in sorted(changes)},
    }


def _safe_metadata_sha256(metadata: dict[str, Any]) -> str:
    safe, _ = redact_structure(metadata)
    return sha256_json({"task_metadata": safe})


def _build_payload(current: dict[str, Any], changes: dict[str, Any], task_id: int) -> dict[str, Any]:
    observed_task_id = int(current.get("taskId") or 0)
    if observed_task_id != task_id:
        raise UsageError(
            "Tiangong2 schedule identity mismatch: "
            f"expected taskId={task_id}, observed={observed_task_id or None}"
        )
    payload = copy.deepcopy(current)
    payload.update(copy.deepcopy(changes))
    payload["taskId"] = task_id
    # Match the observed editor behavior: send the complete object and keep
    # the current derived value.  Do not let a patch file control nextRunTime.
    return payload


def build_schedule_update_plan(
    client: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    identity: dict[str, Any],
    schedule_patch_file: Path,
) -> dict[str, Any]:
    current = client.get_schedule(task.task_id)
    patch = load_schedule_patch(schedule_patch_file)
    current_task_id = int(current.get("taskId") or 0)
    desired = _build_payload(current, patch["changes"], task.task_id)
    identical = _schedule_compare_value(current) == _schedule_compare_value(desired)
    if current_task_id != task.task_id:
        status = "blocked_unconfigured_schedule"
    elif identical:
        status = "blocked_identical_schedule"
    else:
        status = "ready"
    safe_current = _safe_schedule(current)
    safe_desired = _safe_schedule(desired)
    payload = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "operation": PLAN_OPERATION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "read_only_plan": True,
        "remote_mutations": 0,
        "identity": {key: identity.get(key) for key in ("id", "name", "displayName")},
        "scope": {
            "project_id": task.project_id,
            "folder": task.folder_name,
            "menu_id": task.menu_id,
            "task_id": task.task_id,
            "nezha_task_id": task.nezha_task_id,
            "task_name": task.task_name,
            "path": list(task.path),
            "owner_name": task.owner_name,
        },
        "patch": {
            "file": str(schedule_patch_file.resolve()),
            "sha256": text_sha256(schedule_patch_file.read_bytes().decode("utf-8")),
            "changes": patch["changes"],
        },
        "baseline": {
            "task_id": current_task_id or None,
            "schedule_state_sha256": schedule_state_sha256(current),
            "schedule": safe_current,
            "task_metadata_sha256": _safe_metadata_sha256(task.metadata),
        },
        "desired": {
            "schedule_state_sha256": schedule_state_sha256(desired),
            "schedule": safe_desired,
            "save_payload_sha256": sha256_json(desired),
        },
        "policy": {
            "exact_scoped_identity_required": True,
            "authenticated_owner_required": True,
            "schedule_only_patch_fields": sorted(PATCHABLE_FIELDS),
            "executor_retry_dependency_concurrency_and_resource_settings_preserved": True,
            "task_id_must_match_current_task": True,
            "schedule_state_hash_must_not_drift": True,
            "task_metadata_hash_must_not_drift": True,
            "save_requires_exact_plan_sha256": True,
            "save_requires_explicit_schedule_confirmation": True,
            "save_request_is_single_attempt": True,
            "save_requires_schedule_readback": True,
            "effective_scheduler_readback_required": True,
            "effective_scheduler_readback_is_read_only": True,
            "derived_next_run_time_is_preserved_not_patchable": True,
            "code_version_submit_publish_and_execution_not_authorized": True,
        },
    }
    return finalize_hash(payload, "plan_sha256")


def validate_schedule_update_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 schedule-update plan schema")
    if plan.get("operation") != PLAN_OPERATION:
        raise UsageError("Unsupported Tiangong2 schedule-update plan operation")
    supplied = str(plan.get("plan_sha256") or "")
    if not supplied or finalize_hash(plan, "plan_sha256").get("plan_sha256") != supplied:
        raise UsageError("Tiangong2 schedule-update plan SHA-256 validation failed")
    scope = plan.get("scope") or {}
    required_scope = ("project_id", "folder", "menu_id", "task_id", "task_name", "owner_name")
    if any(not scope.get(key) for key in required_scope):
        raise UsageError("Tiangong2 schedule-update plan has an incomplete task scope")
    patch = plan.get("patch") or {}
    if not patch.get("file") or not patch.get("sha256") or not isinstance(patch.get("changes"), dict):
        raise UsageError("Tiangong2 schedule-update plan has an incomplete patch binding")
    baseline = plan.get("baseline") or {}
    desired = plan.get("desired") or {}
    if not baseline.get("schedule_state_sha256") or not desired.get("save_payload_sha256"):
        raise UsageError("Tiangong2 schedule-update plan has incomplete schedule hashes")


def load_schedule_update_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Tiangong2 schedule-update plan: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Tiangong2 schedule-update plan must be a JSON object")
    validate_schedule_update_plan(payload)
    return payload


@dataclass(frozen=True)
class ScheduleUpdateAuthorization:
    plan_sha256: str
    task_id: int
    menu_id: int
    identity_name: str
    desired_payload_sha256: str


def authorize_schedule_update(
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    confirm_save_schedule: bool,
) -> ScheduleUpdateAuthorization:
    validate_schedule_update_plan(plan)
    if not confirm_save_schedule:
        raise UsageError("apply-task-schedule-update requires --confirm-save-schedule")
    if expected_plan_sha256 != plan["plan_sha256"]:
        raise UsageError(
            "Tiangong2 schedule-update plan hash mismatch: "
            f"expected={expected_plan_sha256}, actual={plan['plan_sha256']}"
        )
    if plan.get("status") != "ready":
        raise UsageError(f"Tiangong2 schedule-update plan is blocked: {plan.get('status')}")
    scope = plan["scope"]
    return ScheduleUpdateAuthorization(
        plan_sha256=plan["plan_sha256"],
        task_id=int(scope["task_id"]),
        menu_id=int(scope["menu_id"]),
        identity_name=str(scope["owner_name"]),
        desired_payload_sha256=str(plan["desired"]["save_payload_sha256"]),
    )


class Tiangong2ScheduleUpdateClient:
    """Single-purpose writer for one reviewed schedule payload."""

    def __init__(
        self,
        request_context: Any,
        *,
        authorization: ScheduleUpdateAuthorization,
        dp_api_base: str = TIANGONG2_DP_API_BASE,
    ) -> None:
        if not isinstance(authorization, ScheduleUpdateAuthorization):
            raise UsageError("Tiangong2 schedule-update client requires reviewed authorization")
        self._request = request_context
        self._authorization = authorization
        self._dp_api_base = dp_api_base.rstrip("/")
        self._consumed = False
        self.write_count = 0

    def save_schedule(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        if self._consumed:
            raise UsageError("Tiangong2 schedule-update authorization is single-use")
        task_id = int(payload.get("taskId") or 0)
        if task_id != self._authorization.task_id:
            raise UsageError("Tiangong2 schedule-update task id does not match authorization")
        if sha256_json(payload) != self._authorization.desired_payload_sha256:
            raise UsageError("Tiangong2 schedule-update payload does not match the reviewed plan")
        self._consumed = True
        self.write_count = 1
        response = self._request.post(
            f"{self._dp_api_base}/{SAVE_ENDPOINT}",
            data=payload,
            timeout=45_000,
        )
        if not getattr(response, "ok", False):
            raise UsageError(
                f"Tiangong2 schedule update failed: HTTP {getattr(response, 'status', '?')} from {SAVE_ENDPOINT}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise UsageError("Tiangong2 schedule update returned a non-object response")
        if body.get("status") != "success" or body.get("errorCode") not in (0, None):
            raise UsageError(
                f"Tiangong2 schedule update failed: {body.get('error') or 'platform returned an error'}"
            )
        safe, _ = redact_structure(body)
        return dict(safe)


def prepare_schedule_update(
    client: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = client.get_schedule(task.task_id)
    current_task_id = int(current.get("taskId") or 0)
    if current_task_id != task.task_id:
        raise UsageError("Tiangong2 schedule-update precondition is unconfigured or bound to another task")
    baseline = plan["baseline"]
    if schedule_state_sha256(current) != baseline["schedule_state_sha256"]:
        raise UsageError("Tiangong2 schedule-update precondition drifted: schedule_state_sha256")
    if _safe_metadata_sha256(task.metadata) != baseline["task_metadata_sha256"]:
        raise UsageError("Tiangong2 schedule-update precondition drifted: task_metadata_sha256")
    patch_path = Path(str(plan["patch"]["file"]))
    try:
        patch_bytes = patch_path.read_bytes()
    except OSError as exc:
        raise UsageError(f"Unable to reread Tiangong2 schedule patch: {patch_path}: {exc}") from exc
    if text_sha256(patch_bytes.decode("utf-8")) != plan["patch"]["sha256"]:
        raise UsageError("Tiangong2 schedule patch hash drifted after planning")
    patch = load_schedule_patch(patch_path)
    payload = _build_payload(current, patch["changes"], task.task_id)
    if sha256_json(payload) != plan["desired"]["save_payload_sha256"]:
        raise UsageError("Tiangong2 projected schedule payload drifted after planning")
    return payload, {
        "task_id": current_task_id,
        "schedule_state_sha256": schedule_state_sha256(current),
        "task_metadata_sha256": _safe_metadata_sha256(task.metadata),
    }


def verify_schedule_update_readback(
    client: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> dict[str, Any]:
    current = client.get_schedule(task.task_id)
    observed_task_id = int(current.get("taskId") or 0)
    if observed_task_id != task.task_id:
        raise UsageError("Tiangong2 schedule readback task id does not match the scoped task")
    actual = _schedule_compare_value(current)
    desired = _schedule_compare_value(plan["desired"]["schedule"])
    if actual != desired:
        raise UsageError("Tiangong2 schedule readback does not match the reviewed schedule projection")
    return {
        "task_id": observed_task_id,
        "schedule_state_sha256": schedule_state_sha256(current),
        "schedule": _safe_schedule(current),
        "configuration_fully_verified": True,
    }


def verify_effective_scheduler_readback(
    operations_client: Any,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """Compare the saved development schedule with the Nezha effective view.

    The development schedule endpoint and the Nezha scheduler are separate
    surfaces.  This read-only check deliberately does not attempt to repair a
    mismatch through an undocumented endpoint.
    """

    if task.nezha_task_id <= 0:
        raise UsageError("Tiangong2 task has no Nezha scheduler id for effective readback")
    observed = operations_client.get_task_and_schedule(task.nezha_task_id)
    observed_task_id = int(observed.get("taskId") or 0)
    observed_name = str(observed.get("taskName") or "")
    if observed_task_id != task.nezha_task_id:
        raise UsageError("Nezha effective schedule task id does not match the scoped task")
    if observed_name != task.task_name:
        raise UsageError("Nezha effective schedule task name does not match the scoped task")

    desired = plan["desired"]["schedule"]
    desired_first = str(desired.get("firstRunTime") or "")
    desired_interval = int(desired.get("runInterval") or 0)
    desired_unit = int(desired.get("timeUnit") or 0)
    expected_frequency = f"{desired_interval}h" if desired_unit == 1 else None
    observed_first = str(observed.get("firstRunTime") or "")
    observed_frequency = str(observed.get("scheduleFrequency") or "")
    first_matches = observed_first == desired_first
    frequency_matches = expected_frequency is None or observed_frequency == expected_frequency
    safe_observed = _safe_schedule(observed)
    return {
        "read_only": True,
        "scheduler": "nezha",
        "task_id": observed_task_id,
        "task_name": observed_name,
        "observed": safe_observed,
        "expected": {
            "firstRunTime": desired_first,
            "scheduleFrequency": expected_frequency,
            "runInterval": desired_interval,
            "timeUnit": desired_unit,
        },
        "first_run_time_matches": first_matches,
        "frequency_matches": frequency_matches,
        "fully_verified": first_matches and frequency_matches,
        "verification_note": (
            "Nezha effective schedule matches the reviewed development schedule."
            if first_matches and frequency_matches
            else "Development schedule was saved, but Nezha effective schedule did not match; manual synchronization is required."
        ),
    }


@contextmanager
def task_schedule_update_lock(menu_id: int) -> Iterator[Path]:
    lock_path = Path(tempfile.gettempdir()) / f"codex-tiangong2-schedule-update-{menu_id}.lock"
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(f"another Tiangong2 schedule update is active for menu {menu_id}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        yield lock_path
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
