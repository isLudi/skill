"""Hash-bound plans for production Data Center dataset creation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from _shared.errors import UsageError

from .data_center import DataCenterDataset, DataCenterFolder
from .data_center_replacement import load_replacement_sql, sql_sha256


CREATION_PLAN_SCHEMA_VERSION = "1.0.0"
CREATION_OPERATION = "create_data_center_sql_dataset"
DEFAULT_DATA_SOURCE_NAME = "PRESTO数据源（DORIS加速）"
DEFAULT_DATA_SOURCE_ID = "menu_source_817034371567951872"
DATASET_NAME_PATTERN = re.compile(r"^.{1,50}$", re.DOTALL)


@dataclass(frozen=True)
class DataCenterDatasetCreationPlan:
    schema_version: str
    operation: str
    created_at: str
    status: str
    domain: str
    folder: dict[str, Any]
    dataset_name: str
    sql_file: str
    sql_sha256: str
    sql_bytes: int
    data_source: dict[str, str]
    schedule: dict[str, Any]
    baseline_dataset_ids: tuple[str, ...]
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
            "folder": self.folder,
            "dataset_name": self.dataset_name,
            "sql_file": self.sql_file,
            "sql_sha256": self.sql_sha256,
            "sql_bytes": self.sql_bytes,
            "data_source": self.data_source,
            "schedule": self.schedule,
            "baseline_dataset_ids": list(self.baseline_dataset_ids),
            "diagnostics": list(self.diagnostics),
            "policy": self.policy,
            "plan_sha256": self.plan_sha256,
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "DataCenterDatasetCreationPlan":
        if payload.get("schema_version") != CREATION_PLAN_SCHEMA_VERSION:
            raise UsageError("unsupported Data Center creation plan schema_version")
        if payload.get("operation") != CREATION_OPERATION:
            raise UsageError("artifact is not a Data Center dataset creation plan")
        try:
            plan = cls(
                schema_version=str(payload["schema_version"]),
                operation=str(payload["operation"]),
                created_at=str(payload["created_at"]),
                status=str(payload["status"]),
                domain=str(payload["domain"]),
                folder=dict(payload["folder"]),
                dataset_name=str(payload["dataset_name"]),
                sql_file=str(payload["sql_file"]),
                sql_sha256=str(payload["sql_sha256"]),
                sql_bytes=int(payload["sql_bytes"]),
                data_source=dict(payload["data_source"]),
                schedule=dict(payload["schedule"]),
                baseline_dataset_ids=tuple(str(item) for item in payload["baseline_dataset_ids"]),
                diagnostics=tuple(dict(item) for item in payload.get("diagnostics") or []),
                policy=dict(payload["policy"]),
                plan_sha256=str(payload["plan_sha256"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise UsageError("invalid Data Center creation plan structure") from exc
        if plan.plan_sha256 != plan.computed_sha256():
            raise UsageError("Data Center creation plan hash is invalid or the artifact was modified")
        return plan


def build_creation_plan(
    *,
    domain: str,
    folder: DataCenterFolder,
    datasets: list[DataCenterDataset],
    dataset_name: str,
    sql_file: Path,
    sql_text: str,
    data_source_name: str,
    data_source_id: str,
    schedule_start: date,
    schedule_end: date,
    schedule_hours: tuple[str, ...],
    created_at: datetime | None = None,
) -> DataCenterDatasetCreationPlan:
    diagnostics: list[dict[str, str]] = []
    name = dataset_name.strip()
    if name != dataset_name or not DATASET_NAME_PATTERN.fullmatch(name):
        diagnostics.append(
            {
                "code": "INVALID_DATASET_NAME",
                "message": "Dataset name must be 1-50 characters without leading or trailing whitespace.",
            }
        )
    duplicates = [
        item for item in datasets if item.parent_id == folder.id and item.name == name
    ]
    if duplicates:
        diagnostics.append(
            {
                "code": "DATASET_NAME_ALREADY_EXISTS",
                "message": "Target folder already contains a dataset with the requested name.",
            }
        )
    if not data_source_name.strip() or not data_source_id.strip():
        diagnostics.append(
            {
                "code": "MISSING_DATA_SOURCE",
                "message": "Both Data Center data source name and identity are required.",
            }
        )
    if schedule_start < date.today():
        diagnostics.append(
            {
                "code": "SCHEDULE_START_IN_PAST",
                "message": "Schedule start date cannot precede the planning date.",
            }
        )
    range_days = (schedule_end - schedule_start).days
    if range_days < 0 or range_days > 90:
        diagnostics.append(
            {
                "code": "INVALID_SCHEDULE_RANGE",
                "message": "Schedule date range must be ordered and cannot exceed 90 days.",
            }
        )
    normalized_hours = tuple(dict.fromkeys(schedule_hours))
    invalid_hours = [
        value
        for value in normalized_hours
        if not re.fullmatch(r"(?:\d|1\d|2[0-3]):00", value)
    ]
    if (
        not normalized_hours
        or invalid_hours
        or len(normalized_hours) != len(schedule_hours)
    ):
        diagnostics.append(
            {
                "code": "INVALID_SCHEDULE_HOURS",
                "message": "Hourly schedule values must be unique H:00 entries between 0:00 and 23:00.",
            }
        )

    child_ids = tuple(
        sorted(item.id for item in datasets if item.parent_id == folder.id and item.id)
    )
    timestamp = created_at or datetime.now(timezone.utc)
    plan = DataCenterDatasetCreationPlan(
        schema_version=CREATION_PLAN_SCHEMA_VERSION,
        operation=CREATION_OPERATION,
        created_at=timestamp.isoformat(),
        status="blocked" if diagnostics else "ready",
        domain=domain,
        folder=folder.to_json(),
        dataset_name=name,
        sql_file=str(sql_file.expanduser().resolve()),
        sql_sha256=sql_sha256(sql_text),
        sql_bytes=len(sql_text.encode("utf-8")),
        data_source={"name": data_source_name, "id": data_source_id},
        schedule={
            "taskStatus": True,
            "dateRange": [schedule_start.isoformat(), schedule_end.isoformat()],
            "scheduleType": 1,
            "synchronizationFrequency": {
                "timeUnit": 1,
                "timeHourMinuteList": list(normalized_hours),
            },
            "alarmReceiver": [],
        },
        baseline_dataset_ids=child_ids,
        diagnostics=tuple(diagnostics),
        policy={
            "read_only_plan": True,
            "apply_requires_exact_plan_sha256": True,
            "apply_requires_explicit_production_confirmation": True,
            "create_draft_before_save": True,
            "preview_before_save": True,
            "schedule_configured_before_save": True,
            "post_save_identity_sql_schedule_readback": True,
            "new_schedule_run_must_succeed": True,
            "automatic_delete_or_rollback": False,
        },
        plan_sha256="",
    )
    return replace(plan, plan_sha256=plan.computed_sha256())


def write_creation_plan(path: Path, plan: DataCenterDatasetCreationPlan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(plan.to_json(), ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def load_creation_plan(path: Path) -> DataCenterDatasetCreationPlan:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise UsageError(f"creation plan file does not exist: {resolved}")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"creation plan is not valid UTF-8 JSON: {resolved}") from exc
    if not isinstance(payload, dict):
        raise UsageError("creation plan root must be an object")
    return DataCenterDatasetCreationPlan.from_json(payload)


@contextmanager
def data_center_creation_lock(folder_id: str, dataset_name: str) -> Iterator[Path]:
    raw_key = f"{folder_id}\0{dataset_name.casefold()}"
    key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:20]
    lock_path = Path(tempfile.gettempdir()) / f"codex-data-center-create-{key}.lock"
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(
            f"another Data Center creation is active for {folder_id}/{dataset_name}: {lock_path}"
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


def load_creation_sql(path: Path) -> str:
    """Creation uses the same strict UTF-8/BOM-free SQL loader as replacement."""

    return load_replacement_sql(path)


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
