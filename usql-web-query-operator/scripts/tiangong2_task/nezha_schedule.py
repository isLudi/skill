"""Hash-bound updates for one exact owned Nezha periodic schedule."""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from _shared.config import TIANGONG2_NEZHA_API_BASE
from _shared.errors import UsageError

from .operations import Tiangong2OperationsReadOnlyClient
from .publishing import finalize_hash, sha256_json, text_sha256
from .redaction import redact_structure
from .schedule import load_schedule_patch
from .scope import ScopedTask


PLAN_SCHEMA_VERSION = "tiangong2-nezha-schedule-update-plan-v1"
RECEIPT_SCHEMA_VERSION = "tiangong2-nezha-schedule-update-receipt-v1"
PLAN_OPERATION = "update_owned_nezha_task_schedule"
SAVE_ENDPOINT = "task/schedule"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
_TIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
PATCHABLE_FIELDS = frozenset({"firstRunTime", "endRunTime", "runInterval", "timeUnit"})


def _safe(value: Any) -> Any:
    safe, _ = redact_structure(value)
    return safe


def _safe_dict(value: Any, label: str) -> dict[str, Any]:
    safe = _safe(value)
    if not isinstance(safe, dict):
        raise UsageError(f"Nezha {label} redaction did not return an object")
    return safe


def _validate_time(value: Any, field: str, *, allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if not isinstance(value, str) or not _TIME_PATTERN.fullmatch(value):
        raise UsageError(f"Nezha schedule {field} must use YYYY-MM-DD HH:mm:ss")
    try:
        datetime.strptime(value, TIME_FORMAT)
    except ValueError as exc:
        raise UsageError(f"Nezha schedule {field} is not a valid timestamp") from exc


def _validate_patch(patch_file: Path) -> dict[str, Any]:
    patch = load_schedule_patch(patch_file)
    unknown = set(patch["changes"]) - PATCHABLE_FIELDS
    if unknown:
        raise UsageError(
            "Nezha schedule patch contains non-patchable fields: "
            + ", ".join(sorted(unknown))
        )
    for field, value in patch["changes"].items():
        if field in {"firstRunTime", "endRunTime"}:
            _validate_time(value, field, allow_null=field == "endRunTime")
        elif field == "runInterval":
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10000:
                raise UsageError("Nezha schedule runInterval must be an integer from 1 to 10000")
        elif field == "timeUnit":
            if isinstance(value, bool) or not isinstance(value, int) or value not in {1, 2, 3}:
                raise UsageError("Nezha schedule timeUnit must be 1, 2, or 3")
    return patch


def _metadata_sha256(metadata: dict[str, Any]) -> str:
    return sha256_json({"task_metadata": _safe_dict(metadata, "task metadata")})


def _config_projection(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "taskId": int(config.get("taskId") or 0),
        "firstRunTime": config.get("firstRunTime"),
        "endRunTime": config.get("endRunTime"),
        "runInterval": int(config.get("runInterval") or 0),
        "timeUnit": int(config.get("timeUnit") or 0),
        "periodic": bool(config.get("periodic")),
        "status": int(config.get("status") or 0),
    }


def _config_hash(config: dict[str, Any]) -> str:
    return sha256_json(_config_projection(config))


def _effective_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "taskId": int(row.get("taskId") or 0),
        "taskName": str(row.get("taskName") or ""),
        "scheduleId": int(row.get("scheduleId") or 0),
        "scheduleType": str(row.get("scheduleType") or ""),
        "scheduleStatus": int(row.get("scheduleStatus") or 0),
        "firstRunTime": row.get("firstRunTime"),
        "endRunTime": row.get("endRunTime"),
        "scheduleFrequency": row.get("scheduleFrequency"),
        "supervisor": str(row.get("supervisor") or ""),
    }


def _effective_hash(row: dict[str, Any]) -> str:
    return sha256_json(_effective_projection(row))


def _frequency(run_interval: int, time_unit: int) -> str:
    suffixes = {1: "h", 2: "d", 3: "w"}
    try:
        return f"{run_interval}{suffixes[time_unit]}"
    except KeyError as exc:
        raise UsageError("Nezha schedule timeUnit must be hours, days, or weeks") from exc


def _build_payload(
    current: dict[str, Any],
    changes: dict[str, Any],
    *,
    nezha_task_id: int,
) -> dict[str, Any]:
    observed_task_id = int(current.get("taskId") or 0)
    if observed_task_id != nezha_task_id:
        raise UsageError(
            "Nezha schedule identity mismatch: "
            f"expected taskId={nezha_task_id}, observed={observed_task_id or None}"
        )
    # This is the payload shape used by the retained frontend periodic-schedule
    # action.  Do not send schedule id, nextRunTime, or formatRunInterval: those
    # are platform-owned/derived values.
    payload = {
        "taskId": nezha_task_id,
        "firstRunTime": current.get("firstRunTime"),
        "endRunTime": current.get("endRunTime"),
        "periodic": True,
        "runInterval": int(current.get("runInterval") or 0),
        "timeUnit": int(current.get("timeUnit") or 0),
    }
    payload.update(copy.deepcopy(changes))
    return payload


def _find_schedule_list_row(
    client: Tiangong2OperationsReadOnlyClient,
    *,
    project_id: int,
    task: ScopedTask,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    page_no = 1
    while page_no <= 20:
        rows, page_query = client.list_task_and_schedule_page(
            project_id,
            page_no=page_no,
            page_size=100,
        )
        matches.extend(
            row
            for row in rows
            if int(row.get("taskId") or 0) == task.nezha_task_id
            and str(row.get("taskName") or "") == task.task_name
        )
        page_total = int(page_query.get("pageTotal") or 1)
        if page_no >= page_total:
            break
        page_no += 1
    if len(matches) != 1:
        raise UsageError(
            f"Nezha schedule list did not uniquely identify {task.task_name}: {len(matches)} matches"
        )
    return dict(matches[0])


def build_nezha_schedule_update_plan(
    client: Tiangong2OperationsReadOnlyClient,
    *,
    task: ScopedTask,
    identity: dict[str, Any],
    schedule_patch_file: Path,
) -> dict[str, Any]:
    current = client.get_schedule_config(task.nezha_task_id)
    effective = client.get_task_and_schedule(task.nezha_task_id)
    schedule_list_row = _find_schedule_list_row(client, project_id=task.project_id, task=task)
    patch = _validate_patch(schedule_patch_file)
    desired_payload = _build_payload(
        current,
        patch["changes"],
        nezha_task_id=task.nezha_task_id,
    )
    desired_config = {
        **desired_payload,
        "status": int(current.get("status") or 0),
    }
    desired_frequency = _frequency(
        int(desired_payload["runInterval"]),
        int(desired_payload["timeUnit"]),
    )
    desired_effective = {
        "taskId": task.nezha_task_id,
        "taskName": task.task_name,
        "firstRunTime": desired_payload["firstRunTime"],
        "endRunTime": desired_payload["endRunTime"],
        "scheduleFrequency": desired_frequency,
    }
    config_identical = _config_projection(current) == _config_projection(desired_config)
    effective_identical = all(
        effective.get(key) == value for key, value in desired_effective.items()
    )
    list_identical = all(
        schedule_list_row.get(key) == value for key, value in desired_effective.items()
    )
    status = "blocked_identical_nezha_schedule" if config_identical and effective_identical and list_identical else "ready"
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
            "schema_version": patch["schema_version"],
            "changes": patch["changes"],
        },
        "baseline": {
            "schedule_config_sha256": _config_hash(current),
            "schedule_config": _safe_dict(current, "schedule config"),
            "effective_schedule_sha256": _effective_hash(effective),
            "effective_schedule": _safe_dict(effective, "effective schedule"),
            "schedule_list_sha256": _effective_hash(schedule_list_row),
            "schedule_list_row": _safe_dict(schedule_list_row, "schedule list row"),
            "task_metadata_sha256": _metadata_sha256(task.metadata),
        },
        "desired": {
            "request_payload": _safe_dict(desired_payload, "desired request payload"),
            "request_payload_sha256": sha256_json(desired_payload),
            "schedule_config": _safe_dict(desired_config, "desired schedule config"),
            "effective": desired_effective,
            "schedule_frequency": desired_frequency,
        },
        "policy": {
            "exact_scoped_identity_required": True,
            "authenticated_owner_required": True,
            "schedule_only_patch_fields": sorted(PATCHABLE_FIELDS),
            "periodic_schedule_forced_true": True,
            "derived_next_run_time_is_not_patchable": True,
            "schedule_id_is_not_patchable": True,
            "schedule_config_hash_must_not_drift": True,
            "effective_schedule_hash_must_not_drift": True,
            "schedule_list_readback_required": True,
            "save_requires_exact_plan_sha256": True,
            "save_requires_explicit_schedule_confirmation": True,
            "save_request_is_single_attempt": True,
            "source_submit_publish_and_execution_not_authorized": True,
        },
    }
    return finalize_hash(payload, "plan_sha256")


def validate_nezha_schedule_update_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise UsageError("Unsupported Nezha schedule-update plan schema")
    if plan.get("operation") != PLAN_OPERATION:
        raise UsageError("Unsupported Nezha schedule-update plan operation")
    supplied = str(plan.get("plan_sha256") or "")
    if not supplied or finalize_hash(plan, "plan_sha256").get("plan_sha256") != supplied:
        raise UsageError("Nezha schedule-update plan SHA-256 validation failed")
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
        raise UsageError("Nezha schedule-update plan has an incomplete task scope")
    patch = plan.get("patch") or {}
    if not patch.get("file") or not patch.get("sha256") or not isinstance(patch.get("changes"), dict):
        raise UsageError("Nezha schedule-update plan has an incomplete patch binding")
    desired = plan.get("desired") or {}
    if not desired.get("request_payload_sha256") or not isinstance(desired.get("request_payload"), dict):
        raise UsageError("Nezha schedule-update plan has an incomplete request payload binding")
    baseline = plan.get("baseline") or {}
    for key in ("schedule_config_sha256", "effective_schedule_sha256", "schedule_list_sha256", "task_metadata_sha256"):
        if not baseline.get(key):
            raise UsageError(f"Nezha schedule-update plan is missing baseline hash: {key}")


def load_nezha_schedule_update_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Nezha schedule-update plan: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Nezha schedule-update plan must be a JSON object")
    validate_nezha_schedule_update_plan(payload)
    return payload


@dataclass(frozen=True)
class NezhaScheduleUpdateAuthorization:
    plan_sha256: str
    task_id: int
    nezha_task_id: int
    menu_id: int
    identity_name: str
    desired_payload_sha256: str


def authorize_nezha_schedule_update(
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    confirm_save_schedule: bool,
) -> NezhaScheduleUpdateAuthorization:
    validate_nezha_schedule_update_plan(plan)
    if not confirm_save_schedule:
        raise UsageError("apply-nezha-schedule-update requires --confirm-save-nezha-schedule")
    if expected_plan_sha256 != plan["plan_sha256"]:
        raise UsageError(
            "Nezha schedule-update plan hash mismatch: "
            f"expected={expected_plan_sha256}, actual={plan['plan_sha256']}"
        )
    if plan.get("status") != "ready":
        raise UsageError(f"Nezha schedule-update plan is blocked: {plan.get('status')}")
    scope = plan["scope"]
    return NezhaScheduleUpdateAuthorization(
        plan_sha256=plan["plan_sha256"],
        task_id=int(scope["task_id"]),
        nezha_task_id=int(scope["nezha_task_id"]),
        menu_id=int(scope["menu_id"]),
        identity_name=str(scope["owner_name"]),
        desired_payload_sha256=str(plan["desired"]["request_payload_sha256"]),
    )


class Tiangong2NezhaScheduleUpdateClient:
    """Single-purpose writer for one reviewed Nezha periodic-schedule payload."""

    def __init__(
        self,
        request_context: Any,
        *,
        authorization: NezhaScheduleUpdateAuthorization,
        api_base: str = TIANGONG2_NEZHA_API_BASE,
    ) -> None:
        if not isinstance(authorization, NezhaScheduleUpdateAuthorization):
            raise UsageError("Nezha schedule-update client requires reviewed authorization")
        self._request = request_context
        self._authorization = authorization
        self._api_base = api_base.rstrip("/")
        self._consumed = False
        self.write_count = 0

    def save_schedule(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        if self._consumed:
            raise UsageError("Nezha schedule-update authorization is single-use")
        task_id = int(payload.get("taskId") or 0)
        if task_id != self._authorization.nezha_task_id:
            raise UsageError("Nezha schedule-update task id does not match authorization")
        if sha256_json(payload) != self._authorization.desired_payload_sha256:
            raise UsageError("Nezha schedule-update payload does not match the reviewed plan")
        self._consumed = True
        self.write_count = 1
        response = self._request.post(
            f"{self._api_base}/{SAVE_ENDPOINT}",
            data=payload,
            timeout=45_000,
        )
        if not getattr(response, "ok", False):
            raise UsageError(
                f"Nezha schedule update failed: HTTP {getattr(response, 'status', '?')} from {SAVE_ENDPOINT}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise UsageError("Nezha schedule update returned a non-object response")
        if body.get("status") != "success" or body.get("errorCode") not in (0, None):
            raise UsageError(
                f"Nezha schedule update failed: {body.get('error') or 'platform returned an error'}"
            )
        return _safe_dict(body, "schedule update response")


def prepare_nezha_schedule_update(
    client: Tiangong2OperationsReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = client.get_schedule_config(task.nezha_task_id)
    effective = client.get_task_and_schedule(task.nezha_task_id)
    schedule_list_row = _find_schedule_list_row(client, project_id=task.project_id, task=task)
    baseline = plan["baseline"]
    if _config_hash(current) != baseline["schedule_config_sha256"]:
        raise UsageError("Nezha schedule-update precondition drifted: schedule_config_sha256")
    if _effective_hash(effective) != baseline["effective_schedule_sha256"]:
        raise UsageError("Nezha schedule-update precondition drifted: effective_schedule_sha256")
    if _effective_hash(schedule_list_row) != baseline["schedule_list_sha256"]:
        raise UsageError("Nezha schedule-update precondition drifted: schedule_list_sha256")
    if _metadata_sha256(task.metadata) != baseline["task_metadata_sha256"]:
        raise UsageError("Nezha schedule-update precondition drifted: task_metadata_sha256")
    patch_path = Path(str(plan["patch"]["file"]))
    try:
        patch_bytes = patch_path.read_bytes()
    except OSError as exc:
        raise UsageError(f"Unable to reread Nezha schedule patch: {patch_path}: {exc}") from exc
    if text_sha256(patch_bytes.decode("utf-8")) != plan["patch"]["sha256"]:
        raise UsageError("Nezha schedule patch hash drifted after planning")
    patch = _validate_patch(patch_path)
    payload = _build_payload(current, patch["changes"], nezha_task_id=task.nezha_task_id)
    if sha256_json(payload) != plan["desired"]["request_payload_sha256"]:
        raise UsageError("Nezha projected schedule payload drifted after planning")
    return payload, {
        "schedule_config": _safe_dict(current, "schedule config"),
        "effective_schedule": _safe_dict(effective, "effective schedule"),
        "schedule_list_row": _safe_dict(schedule_list_row, "schedule list row"),
        "schedule_config_sha256": _config_hash(current),
        "effective_schedule_sha256": _effective_hash(effective),
        "schedule_list_sha256": _effective_hash(schedule_list_row),
    }


def verify_nezha_schedule_readback(
    client: Tiangong2OperationsReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> dict[str, Any]:
    desired = plan["desired"]
    desired_payload = desired["request_payload"]
    expected_frequency = str(desired["schedule_frequency"])
    config = client.get_schedule_config(task.nezha_task_id)
    config_matches = all(
        config.get(key) == desired_payload.get(key)
        for key in ("taskId", "firstRunTime", "endRunTime", "runInterval", "timeUnit", "periodic")
    ) and int(config.get("status") or 0) == int(desired["schedule_config"].get("status") or 0)
    effective = client.get_task_and_schedule(task.nezha_task_id)
    effective_matches = all(
        effective.get(key) == value
        for key, value in desired["effective"].items()
    ) and str(effective.get("scheduleFrequency") or "") == expected_frequency
    schedule_list_row = _find_schedule_list_row(client, project_id=task.project_id, task=task)
    schedule_list_matches = all(
        schedule_list_row.get(key) == value
        for key, value in desired["effective"].items()
    ) and str(schedule_list_row.get("scheduleFrequency") or "") == expected_frequency
    return {
        "read_only": True,
        "scheduler": "nezha",
        "task_id": int(effective.get("taskId") or 0),
        "task_name": str(effective.get("taskName") or ""),
        "schedule_config": _safe_dict(config, "schedule config"),
        "effective_scheduler": _safe_dict(effective, "effective scheduler"),
        "schedule_list_row": _safe_dict(schedule_list_row, "schedule list row"),
        "schedule_config_matches": config_matches,
        "effective_scheduler_matches": effective_matches,
        "schedule_list_matches": schedule_list_matches,
        "fully_verified": config_matches and effective_matches and schedule_list_matches,
    }


@contextmanager
def nezha_schedule_update_lock(nezha_task_id: int) -> Iterator[Path]:
    lock_path = Path(tempfile.gettempdir()) / f"codex-tiangong2-nezha-schedule-update-{nezha_task_id}.lock"
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(f"another Nezha schedule update is active for task {nezha_task_id}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        yield lock_path
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
