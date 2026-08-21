"""Hash-bound single execution for one exact owned and published Tiangong2 task."""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from _shared.config import TIANGONG2_NEZHA_API_BASE
from _shared.errors import UsageError

from .client import Tiangong2ReadOnlyClient
from .operations import Tiangong2OperationsReadOnlyClient, list_execution_history_bundle
from .publishing import finalize_hash, read_publish_state
from .redaction import redact_structure
from .scope import ScopedTask


PLAN_SCHEMA_VERSION = "tiangong2-task-execution-plan-v1"
RECEIPT_SCHEMA_VERSION = "tiangong2-task-execution-receipt-v1"
PLAN_OPERATION = "execute_owned_published_tiangong2_task_once"
EXECUTE_ENDPOINT = "task/executeOnce"
PERIOD_TIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


def _validate_period_time(value: str) -> str:
    if not PERIOD_TIME_PATTERN.fullmatch(value):
        raise UsageError("Tiangong2 execution period time must use YYYY-MM-DD HH:mm:ss")
    return value


def _execution_ids(history: dict[str, Any]) -> list[int]:
    return sorted(
        {
            int(row.get("id") or 0)
            for row in history.get("executions") or []
            if int(row.get("id") or 0) > 0
        }
    )


def build_execution_plan(
    reader: Tiangong2ReadOnlyClient,
    operations: Tiangong2OperationsReadOnlyClient,
    *,
    task: ScopedTask,
    identity: dict[str, Any],
    period_time: str,
) -> dict[str, Any]:
    period_time = _validate_period_time(period_time)
    if task.nezha_task_id <= 0:
        raise UsageError(f"Task menu {task.menu_id} has no Nezha operations id")
    publish_state = read_publish_state(reader, task)
    if not publish_state["source_matches_latest_published"]:
        raise UsageError("Tiangong2 task execution requires current source to match latest published source")
    history = list_execution_history_bundle(operations, task=task, limit=100)
    payload = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "operation": PLAN_OPERATION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready",
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
        "execution": {
            "period_time": period_time,
            "trigger_successor": False,
            "params": {},
            "disabled_stages": [],
        },
        "baseline": {
            "current_source_sha256": publish_state["current_source_sha256"],
            "current_source_comparison_sha256": publish_state[
                "current_source_comparison_sha256"
            ],
            "task_metadata_sha256": publish_state["task_metadata_sha256"],
            "version_state_sha256": publish_state["version_state_sha256"],
            "latest_published_version_id": publish_state["latest_published_version_id"],
            "baseline_execution_ids": _execution_ids(history),
        },
        "policy": {
            "exact_scoped_identity_required": True,
            "authenticated_owner_required": True,
            "current_source_must_match_latest_published": True,
            "source_metadata_version_and_history_drift_blocked": True,
            "execute_requires_exact_plan_sha256": True,
            "execute_requires_phase_confirmation_or_active_maintenance_session": True,
            "execute_request_is_single_attempt": True,
            "trigger_successor_is_forced_false": True,
            "params_and_disabled_stages_are_forced_empty": True,
            "new_execution_id_readback_required": True,
            "save_edit_submit_publish_and_schedule_changes_not_authorized": True,
        },
    }
    return finalize_hash(payload, "plan_sha256")


def validate_execution_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 execution plan schema")
    if plan.get("operation") != PLAN_OPERATION:
        raise UsageError("Unsupported Tiangong2 execution plan operation")
    supplied = str(plan.get("plan_sha256") or "")
    if not supplied or finalize_hash(plan, "plan_sha256").get("plan_sha256") != supplied:
        raise UsageError("Tiangong2 execution plan SHA-256 validation failed")
    scope = plan.get("scope") or {}
    required_scope = (
        "project_id",
        "folder",
        "menu_id",
        "task_id",
        "nezha_task_id",
        "task_name",
        "owner_name",
    )
    if any(not scope.get(key) for key in required_scope):
        raise UsageError("Tiangong2 execution plan has an incomplete task scope")
    execution = plan.get("execution") or {}
    _validate_period_time(str(execution.get("period_time") or ""))
    if execution.get("trigger_successor") is not False:
        raise UsageError("Tiangong2 execution plan cannot trigger downstream tasks")
    if execution.get("params") != {} or execution.get("disabled_stages") != []:
        raise UsageError("Tiangong2 execution plan cannot inject params or disable stages")


def load_execution_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Tiangong2 execution plan: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Tiangong2 execution plan must be a JSON object")
    validate_execution_plan(payload)
    return payload


@dataclass(frozen=True)
class ExecutionAuthorization:
    plan_sha256: str
    nezha_task_id: int
    identity_name: str
    period_time: str


def authorize_execution(
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    confirm_execute: bool,
) -> ExecutionAuthorization:
    validate_execution_plan(plan)
    if not confirm_execute:
        raise UsageError("execute-task-once requires --confirm-execute")
    if expected_plan_sha256 != plan["plan_sha256"]:
        raise UsageError(
            "Tiangong2 execution plan hash mismatch: "
            f"expected={expected_plan_sha256}, actual={plan['plan_sha256']}"
        )
    if plan.get("status") != "ready":
        raise UsageError(f"Tiangong2 execution plan is blocked: {plan.get('status')}")
    return ExecutionAuthorization(
        plan_sha256=plan["plan_sha256"],
        nezha_task_id=int(plan["scope"]["nezha_task_id"]),
        identity_name=str(plan["scope"]["owner_name"]),
        period_time=str(plan["execution"]["period_time"]),
    )


class Tiangong2ExecuteOnceClient:
    """Single-purpose, single-use executeOnce client with downstream triggering disabled."""

    def __init__(
        self,
        request_context: Any,
        *,
        authorization: ExecutionAuthorization,
        api_base: str = TIANGONG2_NEZHA_API_BASE,
    ) -> None:
        if not isinstance(authorization, ExecutionAuthorization):
            raise UsageError("Tiangong2 execute client requires reviewed authorization")
        self._request = request_context
        self._authorization = authorization
        self._api_base = api_base.rstrip("/")
        self._consumed = False
        self.write_count = 0

    def execute_once(self, *, task_id: int, period_time: str) -> dict[str, Any]:
        if self._consumed:
            raise UsageError("Tiangong2 execution authorization is single-use")
        if task_id != self._authorization.nezha_task_id:
            raise UsageError("Tiangong2 execution task id does not match authorization")
        if period_time != self._authorization.period_time:
            raise UsageError("Tiangong2 execution period time does not match authorization")
        self._consumed = True
        self.write_count = 1
        response = self._request.post(
            f"{self._api_base}/{EXECUTE_ENDPOINT}",
            data={
                "triggerSuccessor": False,
                "periodTime": period_time,
                "params": {},
                "taskId": task_id,
                "disabledStages": [],
            },
            timeout=45_000,
        )
        if not getattr(response, "ok", False):
            raise UsageError(
                f"Tiangong2 execute-once failed: HTTP {getattr(response, 'status', '?')} from {EXECUTE_ENDPOINT}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise UsageError("Tiangong2 execute-once returned a non-object response")
        if body.get("status") != "success" or body.get("errorCode") not in (0, None):
            raise UsageError(
                f"Tiangong2 execute-once failed: {body.get('error') or 'platform returned an error'}"
            )
        safe, _ = redact_structure(body)
        return dict(safe)


def validate_pre_execution_drift(
    reader: Tiangong2ReadOnlyClient,
    operations: Tiangong2OperationsReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> dict[str, Any]:
    current = read_publish_state(reader, task)
    if not current["source_matches_latest_published"]:
        raise UsageError("Tiangong2 current source no longer matches the latest published source")
    baseline = plan["baseline"]
    for field in (
        "current_source_sha256",
        "current_source_comparison_sha256",
        "task_metadata_sha256",
        "version_state_sha256",
        "latest_published_version_id",
    ):
        if current.get(field) != baseline.get(field):
            raise UsageError(f"Tiangong2 execution precondition drifted after planning: {field}")
    history = list_execution_history_bundle(operations, task=task, limit=100)
    current_ids = _execution_ids(history)
    if current_ids != list(baseline["baseline_execution_ids"]):
        raise UsageError("Tiangong2 execution history drifted after planning")
    return current


def wait_for_new_execution(
    operations: Tiangong2OperationsReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
    attempts: int = 15,
    delay_seconds: float = 2.0,
) -> dict[str, Any]:
    baseline_ids = set(int(value) for value in plan["baseline"]["baseline_execution_ids"])
    period_time = str(plan["execution"]["period_time"])
    for attempt in range(1, attempts + 1):
        history = list_execution_history_bundle(operations, task=task, limit=100)
        matches = [
            dict(row)
            for row in history.get("executions") or []
            if int(row.get("id") or 0) not in baseline_ids
            and str(row.get("periodTime") or "") == period_time
        ]
        if len(matches) == 1:
            safe, _ = redact_structure(matches[0])
            return {
                "attempt": attempt,
                "execution_id": int(matches[0]["id"]),
                "execution": safe,
                "fully_verified": True,
            }
        if len(matches) > 1:
            raise UsageError("Tiangong2 execute-once readback found ambiguous new executions")
        if attempt < attempts:
            time.sleep(delay_seconds)
    raise UsageError("Tiangong2 execute-once request was accepted but no exact new execution was read back")


@contextmanager
def task_execution_lock(nezha_task_id: int) -> Iterator[Path]:
    lock_path = Path(tempfile.gettempdir()) / f"codex-tiangong2-execute-once-{nezha_task_id}.lock"
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(f"another Tiangong2 execution is active for task {nezha_task_id}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        yield lock_path
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
