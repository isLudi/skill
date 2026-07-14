"""Hash-bound plans for production Data Center SQL replacement."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from _shared.errors import UsageError

from .data_center import DataCenterDatasetSql


REPLACEMENT_PLAN_SCHEMA_VERSION = "1.0.0"
REPLACEMENT_OPERATION = "replace_data_center_dataset_sql"


def canonical_sql_text(text: str) -> str:
    """Normalize transport-only differences while preserving SQL content."""

    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.rstrip("\n") + "\n"


def load_replacement_sql(path: Path) -> str:
    """Read a replacement SQL file as UTF-8 without accepting a BOM."""

    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise UsageError(f"replacement SQL file does not exist: {resolved}")
    raw = resolved.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise UsageError(f"replacement SQL file must be UTF-8 without BOM: {resolved}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError(f"replacement SQL file is not valid UTF-8: {resolved}") from exc
    if not text.strip():
        raise UsageError(f"replacement SQL file is empty: {resolved}")
    return canonical_sql_text(text)


def sql_sha256(text: str) -> str:
    return hashlib.sha256(canonical_sql_text(text).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DataCenterSqlReplacementPlan:
    schema_version: str
    operation: str
    created_at: str
    status: str
    domain: str
    dataset: dict[str, Any]
    sql_file: str
    current_sql_sha256: str
    current_sql_bytes: int
    replacement_sql_sha256: str
    replacement_sql_bytes: int
    content_change: bool
    allow_noop: bool
    diagnostics: tuple[dict[str, str], ...]
    policy: dict[str, Any]
    plan_sha256: str

    def hash_payload(self) -> dict[str, Any]:
        payload = self.to_json()
        payload.pop("plan_sha256", None)
        return payload

    def computed_sha256(self) -> str:
        return hashlib.sha256(_canonical_json_bytes(self.hash_payload())).hexdigest()

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "created_at": self.created_at,
            "status": self.status,
            "domain": self.domain,
            "dataset": self.dataset,
            "sql_file": self.sql_file,
            "current_sql_sha256": self.current_sql_sha256,
            "current_sql_bytes": self.current_sql_bytes,
            "replacement_sql_sha256": self.replacement_sql_sha256,
            "replacement_sql_bytes": self.replacement_sql_bytes,
            "content_change": self.content_change,
            "allow_noop": self.allow_noop,
            "diagnostics": list(self.diagnostics),
            "policy": self.policy,
            "plan_sha256": self.plan_sha256,
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "DataCenterSqlReplacementPlan":
        if payload.get("schema_version") != REPLACEMENT_PLAN_SCHEMA_VERSION:
            raise UsageError("unsupported Data Center replacement plan schema_version")
        if payload.get("operation") != REPLACEMENT_OPERATION:
            raise UsageError("artifact is not a Data Center SQL replacement plan")
        try:
            plan = cls(
                schema_version=str(payload["schema_version"]),
                operation=str(payload["operation"]),
                created_at=str(payload["created_at"]),
                status=str(payload["status"]),
                domain=str(payload["domain"]),
                dataset=dict(payload["dataset"]),
                sql_file=str(payload["sql_file"]),
                current_sql_sha256=str(payload["current_sql_sha256"]),
                current_sql_bytes=int(payload["current_sql_bytes"]),
                replacement_sql_sha256=str(payload["replacement_sql_sha256"]),
                replacement_sql_bytes=int(payload["replacement_sql_bytes"]),
                content_change=bool(payload["content_change"]),
                allow_noop=bool(payload["allow_noop"]),
                diagnostics=tuple(dict(item) for item in payload.get("diagnostics") or []),
                policy=dict(payload["policy"]),
                plan_sha256=str(payload["plan_sha256"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise UsageError("invalid Data Center replacement plan structure") from exc
        if plan.plan_sha256 != plan.computed_sha256():
            raise UsageError("Data Center replacement plan hash is invalid or the artifact was modified")
        return plan


def build_replacement_plan(
    *,
    domain: str,
    dataset_sql: DataCenterDatasetSql,
    sql_file: Path,
    replacement_sql: str,
    allow_noop: bool,
    created_at: datetime | None = None,
) -> DataCenterSqlReplacementPlan:
    current_sql = canonical_sql_text(dataset_sql.execute_sql)
    replacement_sql = canonical_sql_text(replacement_sql)
    current_hash = sql_sha256(current_sql)
    replacement_hash = sql_sha256(replacement_sql)
    schedule = dataset_sql.detail_payload.get("schedule") or {}
    diagnostics: list[dict[str, str]] = []
    task_id = str(schedule.get("taskId") or "").strip()

    if not dataset_sql.data_source_id:
        diagnostics.append(
            {"code": "MISSING_DATA_SOURCE_ID", "message": "Dataset detail has no dataSourceId."}
        )
    if schedule.get("taskStatus") is not True:
        diagnostics.append(
            {"code": "SCHEDULE_DISABLED", "message": "Dataset synchronization task is not enabled."}
        )
    if schedule.get("isExpire") is True:
        diagnostics.append(
            {"code": "SCHEDULE_EXPIRED", "message": "Dataset synchronization task is expired."}
        )
    if not task_id:
        diagnostics.append(
            {"code": "MISSING_SCHEDULE_TASK_ID", "message": "Dataset has no schedule taskId."}
        )
    if current_hash == replacement_hash and not allow_noop:
        diagnostics.append(
            {
                "code": "NO_CONTENT_CHANGE",
                "message": "Replacement SQL matches the current SQL; use --allow-noop only for an explicit refresh rehearsal.",
            }
        )

    dataset_payload = dataset_sql.dataset.to_json()
    dataset_payload.update(
        {
            "dataSourceId": dataset_sql.data_source_id,
            "modelId": str(dataset_sql.detail_payload.get("modelId") or ""),
            "scheduleTaskId": task_id,
        }
    )
    timestamp = created_at or datetime.now(timezone.utc)
    plan = DataCenterSqlReplacementPlan(
        schema_version=REPLACEMENT_PLAN_SCHEMA_VERSION,
        operation=REPLACEMENT_OPERATION,
        created_at=timestamp.isoformat(),
        status="blocked" if diagnostics else "ready",
        domain=domain,
        dataset=dataset_payload,
        sql_file=str(sql_file.expanduser().resolve()),
        current_sql_sha256=current_hash,
        current_sql_bytes=len(current_sql.encode("utf-8")),
        replacement_sql_sha256=replacement_hash,
        replacement_sql_bytes=len(replacement_sql.encode("utf-8")),
        content_change=current_hash != replacement_hash,
        allow_noop=allow_noop,
        diagnostics=tuple(diagnostics),
        policy={
            "read_only_plan": True,
            "apply_requires_exact_plan_sha256": True,
            "apply_requires_explicit_production_confirmation": True,
            "preview_before_save": True,
            "post_save_sql_readback": True,
            "new_schedule_run_must_succeed": True,
            "automatic_rollback": False,
        },
        plan_sha256="",
    )
    return replace(plan, plan_sha256=plan.computed_sha256())


def write_replacement_plan(path: Path, plan: DataCenterSqlReplacementPlan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(plan.to_json(), ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def load_replacement_plan(path: Path) -> DataCenterSqlReplacementPlan:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise UsageError(f"replacement plan file does not exist: {resolved}")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"replacement plan is not valid UTF-8 JSON: {resolved}") from exc
    if not isinstance(payload, dict):
        raise UsageError("replacement plan root must be an object")
    return DataCenterSqlReplacementPlan.from_json(payload)


@contextmanager
def data_center_replacement_lock(dataset_id: str) -> Iterator[Path]:
    key = hashlib.sha256(dataset_id.casefold().encode("utf-8")).hexdigest()[:20]
    lock_path = Path(tempfile.gettempdir()) / f"codex-data-center-replace-{key}.lock"
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(
            f"another Data Center replacement is active for {dataset_id}: {lock_path}"
        ) from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        yield lock_path
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
