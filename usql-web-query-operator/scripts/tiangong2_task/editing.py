"""Hash-bound query_sql updates for one exact owned Tiangong2 Python task."""

from __future__ import annotations

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
from .query_quality import build_sql_quality_gate
from .redaction import redact_structure
from .scope import ScopedTask


PLAN_SCHEMA_VERSION = "tiangong2-task-query-update-plan-v2"
RECEIPT_SCHEMA_VERSION = "tiangong2-task-query-update-receipt-v1"
PLAN_OPERATION = "replace_owned_python_task_query_sql"
SAVE_ENDPOINT = "dataDevelop/savePython"
QUERY_ASSIGNMENT_PATTERN = re.compile(r'(?m)^query_sql\s*=\s*"""')
QUERY_CLOSE_PATTERN = re.compile(r'\r?\n"""\r?\n#\.format')
DEFAULT_BEGIN = "# === 默认参数，不需要修改 ==="
DEFAULT_END = "# === end 默认参数，不需要修改 ==="


@dataclass(frozen=True)
class QueryRegions:
    body_start: int
    body_end: int
    default_start: int
    default_end: int
    query_text: str
    default_block: str
    newline: str


def _safe_metadata_sha256(metadata: dict[str, Any]) -> str:
    safe, _ = redact_structure(metadata)
    return sha256_json({"task_metadata": safe})


def _normalized_resource_id(value: Any) -> int:
    if value in (None, "", 0, "0"):
        return 0
    try:
        resource_id = int(value)
    except (TypeError, ValueError) as exc:
        raise UsageError("Tiangong2 Python resourceId is not an integer or null") from exc
    if resource_id < 0:
        raise UsageError("Tiangong2 Python resourceId cannot be negative")
    return resource_id


def _read_python_state(
    client: Tiangong2ReadOnlyClient,
    task: ScopedTask,
) -> tuple[str, int]:
    task_type = int(task.metadata.get("taskType") or task.menu.get("taskType") or 0)
    if task_type != 4:
        raise UsageError("Query-only updates require an exact Tiangong2 PYTHON task")
    spec, content = client.get_task_content(
        menu_id=task.menu_id,
        task_id=task.task_id,
        task_type=task_type,
    )
    if spec.source_kind != "python" or spec.source_keys != ("python",):
        raise UsageError("Tiangong2 PYTHON source registry is not the expected exact adapter")
    source = content.get("python")
    if not isinstance(source, str) or not source:
        raise UsageError(f"No Python source returned for Tiangong2 task {task.menu_id}")
    return source, _normalized_resource_id(content.get("resourceId"))


def extract_query_regions(source: str) -> QueryRegions:
    assignments = list(QUERY_ASSIGNMENT_PATTERN.finditer(source))
    if len(assignments) != 1:
        raise UsageError(
            "Tiangong2 query-only update requires exactly one triple-quoted query_sql assignment"
        )
    body_start = assignments[0].end()
    close = QUERY_CLOSE_PATTERN.search(source, body_start)
    if close is None:
        raise UsageError("Tiangong2 query_sql closing marker was not uniquely recognized")
    later_close = QUERY_CLOSE_PATTERN.search(source, close.end())
    if later_close is not None and later_close.start() < source.find(DEFAULT_BEGIN, close.end()):
        raise UsageError("Tiangong2 query_sql closing marker is ambiguous")
    body_end = close.start()
    if source.count(DEFAULT_BEGIN) != 1 or source.count(DEFAULT_END) != 1:
        raise UsageError("Tiangong2 company default-parameter block is missing or ambiguous")
    default_start = source.find(DEFAULT_BEGIN, body_end)
    default_end_start = source.find(DEFAULT_END, default_start + len(DEFAULT_BEGIN))
    if default_start < 0 or default_end_start < 0:
        raise UsageError("Tiangong2 company default-parameter block markers are missing")
    default_end = default_end_start + len(DEFAULT_END)
    if source[default_end : default_end + 2] == "\r\n":
        default_end += 2
    elif source[default_end : default_end + 1] == "\n":
        default_end += 1
    newline = "\r\n" if "\r\n" in source[:body_start] else "\n"
    return QueryRegions(
        body_start=body_start,
        body_end=body_end,
        default_start=default_start,
        default_end=default_end,
        query_text=source[body_start:body_end],
        default_block=source[default_start:default_end],
        newline=newline,
    )


def _replacement_sql(path: Path) -> str:
    try:
        sql = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise UsageError(f"Unable to read UTF-8 replacement SQL: {path}: {exc}") from exc
    if sql.startswith("\ufeff"):
        raise UsageError("Replacement SQL must be UTF-8 without BOM")
    normalized = sql.strip("\r\n")
    if not normalized.strip():
        raise UsageError("Replacement SQL is empty")
    if '"""' in normalized:
        raise UsageError('Replacement SQL cannot contain Python triple-double-quote delimiters')
    if not re.match(r"(?is)^\s*(WITH|SELECT)\b", normalized):
        raise UsageError("Replacement SQL must begin with WITH or SELECT")
    return normalized


def project_query_update(source: str, replacement_sql: str) -> tuple[str, QueryRegions]:
    regions = extract_query_regions(source)
    projected_body = f"{regions.newline}{replacement_sql}{regions.newline}"
    projected = source[: regions.body_start] + projected_body + source[regions.body_end :]
    projected_regions = extract_query_regions(projected)
    if projected_regions.default_block != regions.default_block:
        raise UsageError("Projected query update changed the company default-parameter block")
    if source[: regions.body_start] != projected[: regions.body_start]:
        raise UsageError("Projected query update changed the Python prefix")
    old_suffix = source[regions.body_end :]
    new_suffix = projected[projected_regions.body_end :]
    if old_suffix != new_suffix:
        raise UsageError("Projected query update changed Python outside query_sql")
    return projected, regions


def build_query_update_plan(
    client: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    identity: dict[str, Any],
    replacement_sql_file: Path,
    sql_review_file: Path,
) -> dict[str, Any]:
    source, resource_id = _read_python_state(client, task)
    replacement_sql = _replacement_sql(replacement_sql_file)
    projected, regions = project_query_update(source, replacement_sql)
    current_query_sha256 = text_sha256(regions.query_text.strip("\r\n"))
    replacement_sql_sha256 = text_sha256(replacement_sql)
    identical = current_query_sha256 == replacement_sql_sha256
    quality_gate = build_sql_quality_gate(
        current_sql=regions.query_text.strip("\r\n"),
        replacement_sql=replacement_sql,
        review_file=sql_review_file,
    )
    if identical:
        status = "blocked_identical_query"
    elif quality_gate["status"] != "passed":
        status = "blocked_sql_quality"
    else:
        status = "ready"
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
        "replacement": {
            "sql_file": str(replacement_sql_file.resolve()),
            "sql_sha256": replacement_sql_sha256,
            "sql_bytes": len(replacement_sql.encode("utf-8")),
        },
        "sql_quality_gate": {
            **quality_gate,
            "gate_sha256": sha256_json(quality_gate),
        },
        "baseline": {
            "current_source_sha256": text_sha256(source),
            "current_query_sha256": current_query_sha256,
            "company_default_block_sha256": text_sha256(regions.default_block),
            "task_metadata_sha256": _safe_metadata_sha256(task.metadata),
            "projected_source_sha256": text_sha256(projected),
            "normalized_resource_id": resource_id,
        },
        "policy": {
            "exact_scoped_identity_required": True,
            "authenticated_owner_required": True,
            "python_task_only": True,
            "query_sql_only": True,
            "company_default_block_must_remain_byte_identical": True,
            "existing_resource_binding_semantics_must_not_change": True,
            "null_resource_is_transported_as_integer_zero": True,
            "source_and_metadata_drift_blocked": True,
            "accuracy_review_is_required_and_sql_hash_bound": True,
            "ordered_output_contract_is_required": True,
            "python_placeholder_contract_must_remain_identical": True,
            "static_sql_minimality_gate_is_required": True,
            "repeated_processing_requires_explicit_accuracy_justification": True,
            "save_requires_exact_plan_sha256": True,
            "save_requires_phase_confirmation_or_active_maintenance_session": True,
            "save_request_is_single_attempt": True,
            "save_requires_full_source_and_default_block_readback": True,
            "publish_is_not_authorized": True,
            "task_execution_is_not_authorized": True,
        },
    }
    return finalize_hash(payload, "plan_sha256")


def validate_query_update_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 query-update plan schema")
    if plan.get("operation") != PLAN_OPERATION:
        raise UsageError("Unsupported Tiangong2 query-update plan operation")
    supplied = str(plan.get("plan_sha256") or "")
    if not supplied or finalize_hash(plan, "plan_sha256").get("plan_sha256") != supplied:
        raise UsageError("Tiangong2 query-update plan SHA-256 validation failed")
    scope = plan.get("scope") or {}
    required_scope = ("project_id", "folder", "menu_id", "task_id", "task_name", "owner_name")
    if any(not scope.get(key) for key in required_scope):
        raise UsageError("Tiangong2 query-update plan has an incomplete task scope")
    replacement = plan.get("replacement") or {}
    if not replacement.get("sql_file") or not replacement.get("sql_sha256"):
        raise UsageError("Tiangong2 query-update plan has an incomplete replacement binding")
    quality_gate = plan.get("sql_quality_gate") or {}
    supplied_gate_sha256 = str(quality_gate.get("gate_sha256") or "")
    if not supplied_gate_sha256:
        raise UsageError("Tiangong2 query-update plan has no SQL quality-gate binding")
    gate_without_hash = {key: value for key, value in quality_gate.items() if key != "gate_sha256"}
    if sha256_json(gate_without_hash) != supplied_gate_sha256:
        raise UsageError("Tiangong2 query-update SQL quality-gate SHA-256 validation failed")


def load_query_update_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read Tiangong2 query-update plan: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UsageError("Tiangong2 query-update plan must be a JSON object")
    validate_query_update_plan(payload)
    return payload


@dataclass(frozen=True)
class QueryUpdateAuthorization:
    plan_sha256: str
    task_id: int
    menu_id: int
    identity_name: str
    resource_id: int


def authorize_query_update(
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    confirm_save_query: bool,
) -> QueryUpdateAuthorization:
    validate_query_update_plan(plan)
    if not confirm_save_query:
        raise UsageError("apply-task-query-update requires --confirm-save-query")
    if expected_plan_sha256 != plan["plan_sha256"]:
        raise UsageError(
            "Tiangong2 query-update plan hash mismatch: "
            f"expected={expected_plan_sha256}, actual={plan['plan_sha256']}"
        )
    if plan.get("status") != "ready":
        raise UsageError(f"Tiangong2 query-update plan is blocked: {plan.get('status')}")
    scope = plan["scope"]
    return QueryUpdateAuthorization(
        plan_sha256=plan["plan_sha256"],
        task_id=int(scope["task_id"]),
        menu_id=int(scope["menu_id"]),
        identity_name=str(scope["owner_name"]),
        resource_id=int(plan["baseline"]["normalized_resource_id"]),
    )


class Tiangong2QueryUpdateClient:
    """Single-purpose writer that can save one reviewed Python source exactly once."""

    def __init__(
        self,
        request_context: Any,
        *,
        authorization: QueryUpdateAuthorization,
        dp_api_base: str = TIANGONG2_DP_API_BASE,
    ) -> None:
        if not isinstance(authorization, QueryUpdateAuthorization):
            raise UsageError("Tiangong2 query-update client requires reviewed authorization")
        self._request = request_context
        self._authorization = authorization
        self._dp_api_base = dp_api_base.rstrip("/")
        self._consumed = False
        self.write_count = 0

    def save_python(self, *, task_id: int, source: str, resource_id: int) -> dict[str, Any]:
        if self._consumed:
            raise UsageError("Tiangong2 query-update authorization is single-use")
        if task_id != self._authorization.task_id:
            raise UsageError("Tiangong2 query-update task id does not match authorization")
        if resource_id != self._authorization.resource_id:
            raise UsageError("Tiangong2 query-update resource id does not match authorization")
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
                f"Tiangong2 query update failed: HTTP {getattr(response, 'status', '?')} from {SAVE_ENDPOINT}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise UsageError("Tiangong2 query update returned a non-object response")
        if body.get("status") != "success" or body.get("errorCode") not in (0, None):
            raise UsageError(
                f"Tiangong2 query update failed: {body.get('error') or 'platform returned an error'}"
            )
        safe, _ = redact_structure(body)
        return dict(safe)


def prepare_query_update(
    client: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    source, resource_id = _read_python_state(client, task)
    regions = extract_query_regions(source)
    baseline = plan["baseline"]
    observed = {
        "current_source_sha256": text_sha256(source),
        "current_query_sha256": text_sha256(regions.query_text.strip("\r\n")),
        "company_default_block_sha256": text_sha256(regions.default_block),
        "task_metadata_sha256": _safe_metadata_sha256(task.metadata),
        "normalized_resource_id": resource_id,
    }
    for field, value in observed.items():
        if value != baseline.get(field):
            raise UsageError(f"Tiangong2 query-update precondition drifted after planning: {field}")
    replacement_path = Path(str(plan["replacement"]["sql_file"]))
    replacement_sql = _replacement_sql(replacement_path)
    if text_sha256(replacement_sql) != plan["replacement"]["sql_sha256"]:
        raise UsageError("Tiangong2 replacement SQL hash drifted after planning")
    planned_quality_gate = plan["sql_quality_gate"]
    observed_quality_gate = build_sql_quality_gate(
        current_sql=regions.query_text.strip("\r\n"),
        replacement_sql=replacement_sql,
        review_file=Path(str(planned_quality_gate["review_file"])),
    )
    if sha256_json(observed_quality_gate) != planned_quality_gate["gate_sha256"]:
        raise UsageError("Tiangong2 SQL quality review or static analysis drifted after planning")
    if observed_quality_gate["status"] != "passed":
        raise UsageError("Tiangong2 SQL quality gate is no longer passed")
    projected, projected_regions = project_query_update(source, replacement_sql)
    if text_sha256(projected) != baseline["projected_source_sha256"]:
        raise UsageError("Tiangong2 projected source hash drifted after planning")
    if text_sha256(projected_regions.default_block) != baseline["company_default_block_sha256"]:
        raise UsageError("Tiangong2 projected company default block hash changed")
    return projected, observed


def verify_query_update_readback(
    client: Tiangong2ReadOnlyClient,
    *,
    task: ScopedTask,
    plan: dict[str, Any],
) -> dict[str, Any]:
    source, resource_id = _read_python_state(client, task)
    regions = extract_query_regions(source)
    observed = {
        "current_source_sha256": text_sha256(source),
        "current_query_sha256": text_sha256(regions.query_text.strip("\r\n")),
        "company_default_block_sha256": text_sha256(regions.default_block),
        "normalized_resource_id": resource_id,
    }
    if observed["current_source_sha256"] != plan["baseline"]["projected_source_sha256"]:
        raise UsageError("Tiangong2 saved source readback hash does not match the reviewed projection")
    if observed["current_query_sha256"] != plan["replacement"]["sql_sha256"]:
        raise UsageError("Tiangong2 saved query_sql readback hash does not match replacement SQL")
    if (
        observed["company_default_block_sha256"]
        != plan["baseline"]["company_default_block_sha256"]
    ):
        raise UsageError("Tiangong2 company default-parameter block changed after save")
    if observed["normalized_resource_id"] != plan["baseline"]["normalized_resource_id"]:
        raise UsageError("Tiangong2 Python resource binding semantics changed after save")
    return {**observed, "fully_verified": True}


@contextmanager
def task_query_update_lock(menu_id: int) -> Iterator[Path]:
    lock_path = Path(tempfile.gettempdir()) / f"codex-tiangong2-query-update-{menu_id}.lock"
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(f"another Tiangong2 query update is active for menu {menu_id}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        yield lock_path
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
