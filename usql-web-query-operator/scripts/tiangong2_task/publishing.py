"""Hash-bound Tiangong2 task publication planning, authorization, and readback."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from _shared.config import TIANGONG2_DP_API_BASE
from _shared.errors import UsageError

from .client import Tiangong2ReadOnlyClient
from .explorer import _normalized_editor_source
from .redaction import redact_structure
from .scope import ScopedTask


PLAN_SCHEMA_VERSION = "tiangong2-task-publish-plan-v2"
RECEIPT_SCHEMA_VERSION = "tiangong2-task-publish-receipt-v1"
PLAN_OPERATION = "publish_saved_tiangong2_task"
PUBLISH_ENDPOINT = "dataDevelop/publishTask"


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def finalize_hash(payload: dict[str, Any], field: str) -> dict[str, Any]:
    finalized = dict(payload)
    finalized.pop(field, None)
    finalized[field] = sha256_json(finalized)
    return finalized


def _source_text(client: Tiangong2ReadOnlyClient, task: ScopedTask) -> tuple[str, str]:
    task_type = int(task.metadata.get("taskType") or task.menu.get("taskType") or 0)
    spec, content = client.get_task_content(
        menu_id=task.menu_id,
        task_id=task.task_id,
        task_type=task_type,
    )
    if not spec.source_keys:
        source = json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True)
    else:
        source = next(
            (content.get(key) for key in spec.source_keys if isinstance(content.get(key), str)),
            None,
        )
        if source is None:
            raise UsageError(f"No source field found in {spec.endpoint}: expected {list(spec.source_keys)}")
    return spec.source_kind, source


def _comparison_sha256(source_kind: str, source: str) -> str:
    return text_sha256(_normalized_editor_source(source_kind, source))


def _safe_versions(versions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe, _ = redact_structure(versions)
    return list(safe)


def _version_state(versions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    safe = _safe_versions(versions)
    return safe, sha256_json({"versions": safe})


def _latest_published(versions: list[dict[str, Any]]) -> dict[str, Any] | None:
    published = [item for item in versions if str(item.get("status") or "") == "已发布"]
    if not published:
        return None
    return sorted(
        published,
        key=lambda item: (
            str(item.get("publishTime") or item.get("updateTime") or item.get("createTime") or ""),
            int(item.get("id") or 0),
        ),
        reverse=True,
    )[0]


def _unpublished_versions(versions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [item for item in versions if str(item.get("status") or "") == "未发布"],
        key=lambda item: int(item.get("id") or 0),
    )


def _version_code_comparison_sha256(
    client: Tiangong2ReadOnlyClient,
    *,
    source_kind: str,
    version: dict[str, Any] | None,
) -> str | None:
    if version is None:
        return None
    version_id = int(version.get("id") or 0)
    if version_id <= 0:
        raise UsageError("Tiangong2 version is missing its id")
    code = client.get_version_code(version_id).get("code")
    if not isinstance(code, str):
        raise UsageError(f"Tiangong2 version {version_id} has no code readback")
    return _comparison_sha256(source_kind, code)


def _task_metadata_sha256(metadata: dict[str, Any]) -> str:
    safe, _ = redact_structure(metadata)
    return sha256_json({"task_metadata": safe})


def read_publish_state(client: Tiangong2ReadOnlyClient, task: ScopedTask) -> dict[str, Any]:
    source_kind, current_source = _source_text(client, task)
    versions = client.list_versions(task.task_id)
    safe_versions, version_state_sha256 = _version_state(versions)
    latest = _latest_published(versions)
    latest_hash = _version_code_comparison_sha256(
        client,
        source_kind=source_kind,
        version=latest,
    )
    current_compare_hash = _comparison_sha256(source_kind, current_source)
    unpublished_sources = [
        {
            "version_id": int(version.get("id") or 0),
            "source_comparison_sha256": _version_code_comparison_sha256(
                client,
                source_kind=source_kind,
                version=version,
            ),
        }
        for version in _unpublished_versions(versions)
    ]
    matching_unpublished_version_ids = [
        int(item["version_id"])
        for item in unpublished_sources
        if item["source_comparison_sha256"] == current_compare_hash
    ]
    return {
        "source_kind": source_kind,
        "current_source_sha256": text_sha256(current_source),
        "current_source_comparison_sha256": current_compare_hash,
        "task_metadata_sha256": _task_metadata_sha256(task.metadata),
        "versions": safe_versions,
        "version_state_sha256": version_state_sha256,
        "baseline_version_ids": sorted(int(item.get("id") or 0) for item in versions if int(item.get("id") or 0) > 0),
        "latest_published_version_id": int(latest.get("id") or 0) if latest else None,
        "latest_published_source_comparison_sha256": latest_hash,
        "source_matches_latest_published": bool(latest_hash and latest_hash == current_compare_hash),
        "unpublished_version_sources": unpublished_sources,
        "matching_unpublished_version_ids": matching_unpublished_version_ids,
    }


def build_publish_plan(
    client: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    identity: dict[str, Any],
) -> dict[str, Any]:
    state = read_publish_state(client, task)
    already_published = state["source_matches_latest_published"]
    matching_unpublished = state["matching_unpublished_version_ids"]
    if already_published:
        status = "blocked_already_published"
    elif not matching_unpublished:
        status = "blocked_no_submitted_version"
    elif len(matching_unpublished) > 1:
        status = "blocked_ambiguous_submitted_versions"
    else:
        status = "ready"
    target_version_id = matching_unpublished[0] if len(matching_unpublished) == 1 else None
    safe_project, _ = redact_structure(task.project)
    safe_metadata, _ = redact_structure(task.metadata)
    payload = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "operation": PLAN_OPERATION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "read_only_plan": True,
        "remote_mutations": 0,
        "identity": {key: identity.get(key) for key in ("id", "name", "displayName")},
        "project": safe_project,
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
        "task_metadata": safe_metadata,
        "publish_target": {
            "version_id": target_version_id,
            "source_comparison_sha256": (
                state["current_source_comparison_sha256"] if target_version_id else None
            ),
        },
        "baseline": state,
        "policy": {
            "exact_scoped_identity_required": True,
            "exact_project_folder_menu_name_required": True,
            "authenticated_owner_required": True,
            "current_source_hash_must_not_drift": True,
            "task_metadata_hash_must_not_drift": True,
            "version_state_hash_must_not_drift": True,
            "identical_to_latest_published_is_blocked": True,
            "one_matching_unpublished_version_required": True,
            "target_unpublished_version_is_hash_bound": True,
            "publish_requires_exact_plan_sha256": True,
            "publish_requires_phase_confirmation_or_active_maintenance_session": True,
            "publish_request_is_single_attempt": True,
            "publish_requires_version_and_source_readback": True,
            "task_execution_is_not_authorized": True,
        },
    }
    return finalize_hash(payload, "plan_sha256")


def validate_publish_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 publish plan schema")
    if plan.get("operation") != PLAN_OPERATION:
        raise UsageError("Unsupported Tiangong2 publish plan operation")
    supplied = str(plan.get("plan_sha256") or "")
    if not supplied or finalize_hash(plan, "plan_sha256").get("plan_sha256") != supplied:
        raise UsageError("Tiangong2 publish plan SHA-256 validation failed")
    scope = plan.get("scope") or {}
    if any(not scope.get(key) for key in ("project_id", "folder", "menu_id", "task_id", "task_name", "owner_name")):
        raise UsageError("Tiangong2 publish plan has an incomplete task scope")
    if plan.get("status") not in {
        "ready",
        "blocked_already_published",
        "blocked_no_submitted_version",
        "blocked_ambiguous_submitted_versions",
    }:
        raise UsageError("Tiangong2 publish plan has an unsupported status")
    target = plan.get("publish_target")
    if not isinstance(target, dict):
        raise UsageError("Tiangong2 publish plan requires a publish target")
    if plan.get("status") == "ready":
        target_id = int(target.get("version_id") or 0)
        matching_ids = [
            int(item)
            for item in (plan.get("baseline") or {}).get(
                "matching_unpublished_version_ids",
                [],
            )
        ]
        if target_id <= 0 or matching_ids != [target_id]:
            raise UsageError("Tiangong2 ready publish plan requires one exact unpublished version")
        if target.get("source_comparison_sha256") != (plan.get("baseline") or {}).get(
            "current_source_comparison_sha256"
        ):
            raise UsageError("Tiangong2 publish target source hash does not match current source")


def load_publish_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Tiangong2 publish plan: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Tiangong2 publish plan must be a JSON object")
    validate_publish_plan(payload)
    return payload


def write_hashed_json(path: Path, payload: dict[str, Any], *, hash_field: str) -> dict[str, Any]:
    finalized = finalize_hash(payload, hash_field)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(finalized, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return finalized


@dataclass(frozen=True)
class PublishAuthorization:
    plan_sha256: str
    menu_id: int
    identity_name: str


def authorize_publish(
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    confirm_publish: bool,
) -> PublishAuthorization:
    validate_publish_plan(plan)
    if not confirm_publish:
        raise UsageError("publish-task requires --confirm-publish")
    if expected_plan_sha256 != plan["plan_sha256"]:
        raise UsageError(
            "Tiangong2 publish plan hash mismatch: "
            f"expected={expected_plan_sha256}, actual={plan['plan_sha256']}"
        )
    if plan.get("status") != "ready":
        raise UsageError(f"Tiangong2 publish plan is blocked: {plan.get('status')}")
    scope = plan["scope"]
    return PublishAuthorization(
        plan_sha256=plan["plan_sha256"],
        menu_id=int(scope["menu_id"]),
        identity_name=str(scope["owner_name"]),
    )


class Tiangong2PublishClient:
    """Single-purpose, single-use write client created only from reviewed authorization."""

    def __init__(
        self,
        request_context: Any,
        *,
        authorization: PublishAuthorization,
        dp_api_base: str = TIANGONG2_DP_API_BASE,
    ) -> None:
        if not isinstance(authorization, PublishAuthorization):
            raise UsageError("Tiangong2 publish client requires a reviewed PublishAuthorization")
        self._request = request_context
        self._authorization = authorization
        self._dp_api_base = dp_api_base.rstrip("/")
        self._consumed = False
        self.write_count = 0

    def publish_task(self, menu_id: int) -> dict[str, Any]:
        if self._consumed:
            raise UsageError("Tiangong2 publish authorization is single-use")
        if menu_id != self._authorization.menu_id:
            raise UsageError("Tiangong2 publish menu id does not match the reviewed authorization")
        self._consumed = True
        self.write_count = 1
        response = self._request.post(
            f"{self._dp_api_base}/{PUBLISH_ENDPOINT}",
            form={"id": str(menu_id)},
            timeout=45_000,
        )
        if not getattr(response, "ok", False):
            raise UsageError(
                f"Tiangong2 publish failed: HTTP {getattr(response, 'status', '?')} from {PUBLISH_ENDPOINT}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise UsageError("Tiangong2 publish returned a non-object response")
        if body.get("status") != "success" or body.get("errorCode") not in (0, None):
            raise UsageError(
                f"Tiangong2 publish failed: {body.get('error') or 'platform returned an error'}"
            )
        safe, _ = redact_structure(body)
        return dict(safe)


@contextmanager
def task_publish_lock(menu_id: int) -> Iterator[Path]:
    """Prevent concurrent local publishers from racing one reviewed task state."""

    lock_path = Path(tempfile.gettempdir()) / f"codex-tiangong2-task-publish-{menu_id}.lock"
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(f"another Tiangong2 publish is active for menu {menu_id}: {lock_path}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        yield lock_path
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def validate_pre_publish_drift(
    client: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> dict[str, Any]:
    current = read_publish_state(client, task)
    baseline = plan["baseline"]
    for field in (
        "current_source_sha256",
        "current_source_comparison_sha256",
        "task_metadata_sha256",
        "version_state_sha256",
    ):
        if current.get(field) != baseline.get(field):
            raise UsageError(f"Tiangong2 publish precondition drifted after planning: {field}")
    if current.get("source_matches_latest_published"):
        raise UsageError("Tiangong2 current source is already the latest published version")
    target_id = int(plan["publish_target"]["version_id"])
    if current.get("matching_unpublished_version_ids") != [target_id]:
        raise UsageError("Tiangong2 publish target version is no longer the unique matching draft")
    return current


def verify_publish_readback(
    client: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
    attempts: int = 6,
    delay_seconds: float = 1.0,
) -> dict[str, Any]:
    baseline = plan["baseline"]
    target_version_id = int(plan["publish_target"]["version_id"])
    for attempt in range(1, attempts + 1):
        current = read_publish_state(client, task)
        if (
            current["version_state_sha256"] != baseline["version_state_sha256"]
            and current["source_matches_latest_published"]
            and current["latest_published_version_id"] == target_version_id
            and current["latest_published_source_comparison_sha256"]
            == baseline["current_source_comparison_sha256"]
        ):
            return {
                "attempt": attempt,
                "version_state_changed": True,
                "latest_published_version_id": current["latest_published_version_id"],
                "latest_published_source_comparison_sha256": current[
                    "latest_published_source_comparison_sha256"
                ],
                "source_matches_latest_published": True,
                "fully_verified": True,
            }
        if attempt < attempts:
            time.sleep(delay_seconds)
    raise UsageError("Tiangong2 publish was requested but version/source readback was not verified")
