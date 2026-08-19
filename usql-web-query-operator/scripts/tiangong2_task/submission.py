"""Hash-bound submission of one exact saved and owned Tiangong2 task."""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from _shared.config import TIANGONG2_DP_API_BASE
from _shared.errors import UsageError

from .client import Tiangong2ReadOnlyClient
from .publishing import finalize_hash, read_publish_state, text_sha256
from .redaction import redact_structure
from .scope import ScopedTask


PLAN_SCHEMA_VERSION = "tiangong2-task-submit-plan-v1"
RECEIPT_SCHEMA_VERSION = "tiangong2-task-submit-receipt-v1"
PLAN_OPERATION = "submit_saved_owned_tiangong2_task"
SUBMIT_ENDPOINT = "dataDevelop/taskConfirm"
NOTE_PATTERN = re.compile(r"^[\u4e00-\u9fffA-Za-z0-9_]+$")


def validate_submit_note(note: str) -> str:
    normalized = note.strip()
    if not normalized:
        raise UsageError("Tiangong2 task submit note cannot be empty")
    if len(normalized) > 200:
        raise UsageError("Tiangong2 task submit note cannot exceed 200 characters")
    if not NOTE_PATTERN.fullmatch(normalized):
        raise UsageError(
            "Tiangong2 task submit note may contain only Chinese characters, letters, digits, and underscores"
        )
    return normalized


def _safe_scope(task: ScopedTask) -> dict[str, Any]:
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


def _refresh_task(reader: Tiangong2ReadOnlyClient, task: ScopedTask) -> ScopedTask:
    return replace(task, metadata=reader.get_task(task.menu_id))


def build_submit_plan(
    reader: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    identity: dict[str, Any],
    note: str,
) -> dict[str, Any]:
    note = validate_submit_note(note)
    state = read_publish_state(reader, task)
    already_published = state["source_matches_latest_published"]
    safe_project, _ = redact_structure(task.project)
    safe_metadata, _ = redact_structure(task.metadata)
    payload = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "operation": PLAN_OPERATION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "blocked_already_published" if already_published else "ready",
        "read_only_plan": True,
        "remote_mutations": 0,
        "identity": {key: identity.get(key) for key in ("id", "name", "displayName")},
        "project": safe_project,
        "scope": _safe_scope(task),
        "task_metadata": safe_metadata,
        "submission": {
            "note": note,
            "note_sha256": text_sha256(note),
        },
        "baseline": state,
        "policy": {
            "exact_scoped_identity_required": True,
            "authenticated_owner_required": True,
            "saved_source_hash_must_not_drift": True,
            "task_metadata_hash_must_not_drift": True,
            "version_state_hash_must_not_drift": True,
            "identical_to_latest_published_is_blocked": True,
            "submit_requires_exact_plan_sha256": True,
            "submit_requires_explicit_confirmation": True,
            "submit_request_is_single_attempt": True,
            "submit_note_is_hash_bound": True,
            "save_publish_execute_and_configuration_changes_not_authorized": True,
        },
    }
    return finalize_hash(payload, "plan_sha256")


def validate_submit_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 submit plan schema")
    if plan.get("operation") != PLAN_OPERATION:
        raise UsageError("Unsupported Tiangong2 submit plan operation")
    supplied = str(plan.get("plan_sha256") or "")
    if not supplied or finalize_hash(plan, "plan_sha256").get("plan_sha256") != supplied:
        raise UsageError("Tiangong2 submit plan SHA-256 validation failed")
    scope = plan.get("scope") or {}
    required_scope = (
        "project_id",
        "folder",
        "menu_id",
        "task_id",
        "task_name",
        "owner_name",
    )
    if any(not scope.get(key) for key in required_scope):
        raise UsageError("Tiangong2 submit plan has an incomplete task scope")
    submission = plan.get("submission") or {}
    note = validate_submit_note(str(submission.get("note") or ""))
    if submission.get("note_sha256") != text_sha256(note):
        raise UsageError("Tiangong2 submit note SHA-256 validation failed")


def load_submit_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Tiangong2 submit plan: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Tiangong2 submit plan must be a JSON object")
    validate_submit_plan(payload)
    return payload


@dataclass(frozen=True)
class SubmitAuthorization:
    plan_sha256: str
    task_id: int
    identity_name: str
    note: str


def authorize_submit(
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    confirm_submit: bool,
) -> SubmitAuthorization:
    validate_submit_plan(plan)
    if not confirm_submit:
        raise UsageError("submit-task requires --confirm-submit")
    if expected_plan_sha256 != plan["plan_sha256"]:
        raise UsageError(
            "Tiangong2 submit plan hash mismatch: "
            f"expected={expected_plan_sha256}, actual={plan['plan_sha256']}"
        )
    if plan.get("status") != "ready":
        raise UsageError(f"Tiangong2 submit plan is blocked: {plan.get('status')}")
    return SubmitAuthorization(
        plan_sha256=plan["plan_sha256"],
        task_id=int(plan["scope"]["task_id"]),
        identity_name=str(plan["scope"]["owner_name"]),
        note=str(plan["submission"]["note"]),
    )


class Tiangong2SubmitClient:
    """Single-purpose, single-use taskConfirm client from reviewed authorization."""

    def __init__(
        self,
        request_context: Any,
        *,
        authorization: SubmitAuthorization,
        dp_api_base: str = TIANGONG2_DP_API_BASE,
    ) -> None:
        if not isinstance(authorization, SubmitAuthorization):
            raise UsageError("Tiangong2 submit client requires reviewed authorization")
        self._request = request_context
        self._authorization = authorization
        self._dp_api_base = dp_api_base.rstrip("/")
        self._consumed = False
        self.write_count = 0

    def submit_task(self, *, task_id: int, note: str) -> dict[str, Any]:
        if self._consumed:
            raise UsageError("Tiangong2 submit authorization is single-use")
        note = validate_submit_note(note)
        if task_id != self._authorization.task_id:
            raise UsageError("Tiangong2 submit task id does not match authorization")
        if note != self._authorization.note:
            raise UsageError("Tiangong2 submit note does not match authorization")
        self._consumed = True
        self.write_count = 1
        response = self._request.post(
            f"{self._dp_api_base}/{SUBMIT_ENDPOINT}",
            form={"taskId": str(task_id), "note": note},
            timeout=45_000,
        )
        if not getattr(response, "ok", False):
            raise UsageError(
                f"Tiangong2 submit failed: HTTP {getattr(response, 'status', '?')} from {SUBMIT_ENDPOINT}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise UsageError("Tiangong2 submit returned a non-object response")
        if body.get("status") != "success" or body.get("errorCode") not in (0, None):
            raise UsageError(
                f"Tiangong2 submit failed: {body.get('error') or 'platform returned an error'}"
            )
        safe, _ = redact_structure(body)
        return dict(safe)


def validate_pre_submit_drift(
    reader: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> dict[str, Any]:
    current = read_publish_state(reader, _refresh_task(reader, task))
    baseline = plan["baseline"]
    for field in (
        "current_source_sha256",
        "current_source_comparison_sha256",
        "task_metadata_sha256",
        "version_state_sha256",
        "latest_published_version_id",
    ):
        if current.get(field) != baseline.get(field):
            raise UsageError(f"Tiangong2 submit precondition drifted after planning: {field}")
    if current.get("source_matches_latest_published"):
        raise UsageError("Tiangong2 current source is already the latest published version")
    return current


def verify_submit_readback(
    reader: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
    attempts: int = 6,
    delay_seconds: float = 1.0,
) -> dict[str, Any]:
    """Confirm stable saved source and report any observable submit-state change.

    Tiangong2 does not expose a dedicated submit-status read endpoint. A changed
    task metadata/version hash is strong readback; otherwise the successful
    taskConfirm response plus a fresh, stable source read is recorded honestly
    and the following publish/version readback provides final confirmation.
    """

    baseline = plan["baseline"]
    last_state: dict[str, Any] | None = None
    for attempt in range(1, attempts + 1):
        current = read_publish_state(reader, _refresh_task(reader, task))
        last_state = current
        if current["current_source_sha256"] != baseline["current_source_sha256"]:
            raise UsageError("Tiangong2 saved source changed after submit request")
        if current["current_source_comparison_sha256"] != baseline[
            "current_source_comparison_sha256"
        ]:
            raise UsageError("Tiangong2 normalized source changed after submit request")
        metadata_changed = current["task_metadata_sha256"] != baseline["task_metadata_sha256"]
        version_state_changed = current["version_state_sha256"] != baseline["version_state_sha256"]
        if metadata_changed or version_state_changed:
            return {
                "attempt": attempt,
                "saved_source_unchanged": True,
                "task_metadata_changed": metadata_changed,
                "version_state_changed": version_state_changed,
                "latest_published_version_id": current["latest_published_version_id"],
                "source_matches_latest_published": current["source_matches_latest_published"],
                "submit_state_observed": True,
                "fully_verified": True,
            }
        if attempt < attempts:
            time.sleep(delay_seconds)
    assert last_state is not None
    return {
        "attempt": attempts,
        "saved_source_unchanged": True,
        "task_metadata_changed": False,
        "version_state_changed": False,
        "latest_published_version_id": last_state["latest_published_version_id"],
        "source_matches_latest_published": last_state["source_matches_latest_published"],
        "submit_state_observed": False,
        "fully_verified": False,
        "verification_note": "taskConfirm succeeded; no dedicated submit-state read endpoint is available",
    }


@contextmanager
def task_submit_lock(task_id: int) -> Iterator[Path]:
    lock_path = Path(tempfile.gettempdir()) / f"codex-tiangong2-task-submit-{task_id}.lock"
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(f"another Tiangong2 submit is active for task {task_id}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        yield lock_path
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
