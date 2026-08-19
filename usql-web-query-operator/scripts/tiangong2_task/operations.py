"""Read-only Tiangong2 task execution history and stage-log retrieval."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from _shared.config import TIANGONG2_NEZHA_API_BASE
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from .artifacts import validate_artifact_root
from .redaction import redact_structure, redact_text
from .scope import ScopedTask


NEZHA_GET_ENDPOINTS = frozenset(
    {
        "task/getTaskAndSchedule",
        "task/getTaskExecutionDetail",
    }
)
NEZHA_JSON_READ_ENDPOINTS = frozenset(
    {
        "task/listTaskExecutionPeriods",
    }
)
NEZHA_FORM_READ_ENDPOINTS = frozenset(
    {
        "task/listTaskExecutions",
        "stage/getStageLog",
    }
)


class Tiangong2OperationsReadOnlyClient:
    """Exact Nezha read client with no generic request or mutation method."""

    def __init__(self, request_context: Any, *, api_base: str = TIANGONG2_NEZHA_API_BASE) -> None:
        self._request = request_context
        self._api_base = api_base.rstrip("/")
        self.used_endpoints: set[str] = set()

    @staticmethod
    def _json_body(response: Any, endpoint: str) -> dict[str, Any]:
        if not getattr(response, "ok", False):
            raise UsageError(
                f"Tiangong2 operations read failed: HTTP {getattr(response, 'status', '?')} from {endpoint}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise UsageError(f"Tiangong2 operations returned a non-object response from {endpoint}")
        if body.get("status") != "success" or body.get("errorCode") not in (0, None):
            message = str(body.get("error") or "platform returned an error")
            raise UsageError(f"Tiangong2 operations read failed at {endpoint}: {message}")
        return body

    def _get_body(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        if endpoint not in NEZHA_GET_ENDPOINTS:
            raise UsageError(f"Blocked non-allowlisted Tiangong2 operations GET endpoint: {endpoint}")
        self.used_endpoints.add(f"GET nezha/{endpoint}")
        response = self._request.get(
            f"{self._api_base}/{endpoint}",
            params={key: str(value) for key, value in params.items()},
            timeout=45_000,
        )
        return self._json_body(response, f"nezha/{endpoint}")

    def _post_json_body(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        if endpoint not in NEZHA_JSON_READ_ENDPOINTS:
            raise UsageError(f"Blocked non-allowlisted Tiangong2 operations POST endpoint: {endpoint}")
        self.used_endpoints.add(f"POST nezha/{endpoint}")
        response = self._request.post(
            f"{self._api_base}/{endpoint}",
            data=payload,
            timeout=45_000,
        )
        return self._json_body(response, f"nezha/{endpoint}")

    def _post_form_body(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        if endpoint not in NEZHA_FORM_READ_ENDPOINTS:
            raise UsageError(f"Blocked non-allowlisted Tiangong2 operations form endpoint: {endpoint}")
        self.used_endpoints.add(f"POST form/nezha/{endpoint}")
        response = self._request.post(
            f"{self._api_base}/{endpoint}",
            form={key: str(value) for key, value in payload.items()},
            timeout=45_000,
        )
        return self._json_body(response, f"nezha/{endpoint}")

    def get_task_and_schedule(self, task_id: int) -> dict[str, Any]:
        return dict(self._get_body("task/getTaskAndSchedule", {"taskId": task_id}).get("data") or {})

    def list_execution_periods_page(
        self,
        task_id: int,
        *,
        page_no: int,
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        body = self._post_json_body(
            "task/listTaskExecutionPeriods",
            {"pageNo": page_no, "pageSize": page_size, "taskId": task_id},
        )
        return list(body.get("data") or []), dict(body.get("pageQuery") or {})

    def list_task_executions(self, task_id: int, period_time: str) -> list[dict[str, Any]]:
        body = self._post_form_body(
            "task/listTaskExecutions",
            {"taskId": str(task_id), "periodTime": period_time},
        )
        return list(body.get("data") or [])

    def get_execution_detail(self, execution_id: int) -> dict[str, Any]:
        return dict(
            self._get_body(
                "task/getTaskExecutionDetail",
                {"taskExecutionId": execution_id},
            ).get("data")
            or {}
        )

    def get_stage_log_page(self, stage_execution_id: int, begin_pos: int) -> dict[str, Any]:
        return dict(
            self._post_form_body(
                "stage/getStageLog",
                {"stageExecutionId": str(stage_execution_id), "beginPos": str(begin_pos)},
            ).get("data")
            or {}
        )

    def get_complete_stage_log(self, stage_execution_id: int, *, max_pages: int = 100) -> str:
        begin_pos = 0
        chunks: list[str] = []
        for _ in range(max_pages):
            page = self.get_stage_log_page(stage_execution_id, begin_pos)
            if int(page.get("stageExecutionId") or 0) != stage_execution_id:
                raise UsageError(f"Stage-log identity mismatch for stage execution {stage_execution_id}")
            chunks.append(str(page.get("data") or ""))
            if not bool(page.get("hasMore")):
                return "".join(chunks)
            next_pos = int(page.get("nextBeginPos") or -1)
            if next_pos <= begin_pos:
                raise UsageError(f"Stage-log pagination did not advance for {stage_execution_id}")
            begin_pos = next_pos
        raise UsageError(f"Stage-log pagination exceeded {max_pages} pages for {stage_execution_id}")


def _find_period(
    client: Tiangong2OperationsReadOnlyClient,
    *,
    task_id: int,
    execution_id: int,
    max_pages: int = 20,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for page_no in range(1, max_pages + 1):
        rows, page_query = client.list_execution_periods_page(task_id, page_no=page_no)
        matches.extend(
            row
            for row in rows
            if int(row.get("taskExecutionId") or 0) == execution_id
            and int(row.get("taskId") or 0) == task_id
        )
        page_total = int(page_query.get("pageTotal") or 1)
        if matches or page_no >= page_total:
            break
    if len(matches) != 1:
        raise UsageError(
            f"Execution {execution_id} was not uniquely found under Nezha task {task_id}"
        )
    return matches[0]


def fetch_execution_log_bundle(
    client: Tiangong2OperationsReadOnlyClient,
    *,
    task: ScopedTask,
    execution_id: int,
) -> dict[str, Any]:
    """Fetch and bind one execution plus every stage log to an already-scoped owned task."""

    if task.nezha_task_id <= 0:
        raise UsageError(f"Task menu {task.menu_id} has no Nezha operations id")
    schedule = client.get_task_and_schedule(task.nezha_task_id)
    if int(schedule.get("taskId") or 0) != task.nezha_task_id:
        raise UsageError("Nezha task identity mismatch while reading execution logs")
    if str(schedule.get("taskName") or "") != task.task_name:
        raise UsageError("Nezha task name mismatch while reading execution logs")
    period = _find_period(
        client,
        task_id=task.nezha_task_id,
        execution_id=execution_id,
    )
    period_time = str(period.get("periodTime") or "")
    executions = client.list_task_executions(task.nezha_task_id, period_time)
    matches = [
        row
        for row in executions
        if int(row.get("id") or 0) == execution_id
        and int(row.get("taskId") or 0) == task.nezha_task_id
        and str(row.get("taskName") or "") == task.task_name
    ]
    if len(matches) != 1:
        raise UsageError(f"Execution detail row {execution_id} was not uniquely bound to the scoped task")
    execution = matches[0]
    detail = client.get_execution_detail(execution_id)
    if int(detail.get("taskExecutionId") or 0) != execution_id:
        raise UsageError(f"Execution-detail identity mismatch for {execution_id}")
    if str(detail.get("taskName") or "") != task.task_name:
        raise UsageError(f"Execution-detail task name mismatch for {execution_id}")
    stage_rows = list(detail.get("stageExecutions") or [])
    if not stage_rows:
        raise UsageError(f"Execution {execution_id} contains no stage executions")
    stages: list[dict[str, Any]] = []
    for row in stage_rows:
        stage_execution_id = int(row.get("id") or 0)
        if stage_execution_id <= 0 or int(row.get("taskId") or 0) != task.nezha_task_id:
            raise UsageError(f"Execution {execution_id} contains an unbound stage execution")
        stages.append(
            {
                "metadata": dict(row),
                "log": client.get_complete_stage_log(stage_execution_id),
            }
        )
    return {
        "task_schedule": schedule,
        "period": period,
        "execution": execution,
        "execution_detail": {
            key: value for key, value in detail.items() if key != "stageExecutions"
        },
        "stages": stages,
    }


def list_execution_history_bundle(
    client: Tiangong2OperationsReadOnlyClient,
    *,
    task: ScopedTask,
    limit: int = 20,
) -> dict[str, Any]:
    """List the latest exact execution attempts for an already-scoped owned task."""

    if task.nezha_task_id <= 0:
        raise UsageError(f"Task menu {task.menu_id} has no Nezha operations id")
    if limit < 1 or limit > 100:
        raise UsageError("Tiangong2 execution-history limit must be between 1 and 100")
    schedule = client.get_task_and_schedule(task.nezha_task_id)
    if int(schedule.get("taskId") or 0) != task.nezha_task_id:
        raise UsageError("Nezha task identity mismatch while reading execution history")
    if str(schedule.get("taskName") or "") != task.task_name:
        raise UsageError("Nezha task name mismatch while reading execution history")

    period_rows, page_query = client.list_execution_periods_page(
        task.nezha_task_id,
        page_no=1,
        page_size=100,
    )
    bound_periods: list[dict[str, Any]] = []
    for row in period_rows:
        if int(row.get("taskId") or 0) != task.nezha_task_id:
            raise UsageError("Execution-history period escaped the scoped Nezha task")
        row_task_name = str(row.get("taskName") or "")
        if row_task_name and row_task_name != task.task_name:
            raise UsageError("Execution-history period task name mismatch")
        period_time = str(row.get("periodTime") or "")
        if not period_time:
            raise UsageError("Execution-history period is missing periodTime")
        bound_periods.append(dict(row))

    bound_periods.sort(
        key=lambda row: (
            str(row.get("periodTime") or ""),
            int(row.get("taskExecutionId") or row.get("id") or 0),
        ),
        reverse=True,
    )
    executions_by_id: dict[int, dict[str, Any]] = {}
    queried_periods: list[dict[str, Any]] = []
    seen_period_times: set[str] = set()
    for period in bound_periods:
        period_time = str(period["periodTime"])
        if period_time in seen_period_times:
            continue
        seen_period_times.add(period_time)
        queried_periods.append(period)
        for row in client.list_task_executions(task.nezha_task_id, period_time):
            execution_id = int(row.get("id") or 0)
            if execution_id <= 0:
                raise UsageError("Execution-history row is missing a positive execution id")
            if int(row.get("taskId") or 0) != task.nezha_task_id:
                raise UsageError("Execution-history row escaped the scoped Nezha task")
            if str(row.get("taskName") or "") != task.task_name:
                raise UsageError("Execution-history row task name mismatch")
            normalized = dict(row)
            normalized.setdefault("periodTime", period_time)
            executions_by_id[execution_id] = normalized
        if len(executions_by_id) >= limit:
            break

    executions = sorted(
        executions_by_id.values(),
        key=lambda row: (
            str(
                row.get("startTime")
                or row.get("beginTime")
                or row.get("periodTime")
                or ""
            ),
            int(row.get("id") or 0),
        ),
        reverse=True,
    )[:limit]
    return {
        "task_schedule": schedule,
        "period_page": page_query,
        "periods": queried_periods,
        "executions": executions,
    }


def _diagnose_logs(logs: list[str]) -> dict[str, Any]:
    lines = [line for log in logs for line in log.splitlines()]
    pattern = re.compile(
        r"(?i)(执行sql失败|caused by|exception|fatal|failed|error|outofmemory|timeout|broadcast|退出脚本)"
    )
    benign_patterns = (
        re.compile(r'^SLF4J: Failed to load class "org\.slf4j\.impl\.StaticLoggerBinder"\.$'),
    )
    candidates: list[str] = []
    for line in lines:
        stripped = line.strip()
        benign = any(item.search(stripped) for item in benign_patterns)
        if stripped and pattern.search(stripped) and not benign and stripped not in candidates:
            candidates.append(stripped)
        if len(candidates) >= 40:
            break
    joined = "\n".join(lines)
    success_signature = bool(re.search(r"(?m)^exit_code:\s+0\s*$", joined))
    if "SparkFatalException" in joined and "BroadcastExchangeExec" in joined:
        classification = "spark_broadcast_exchange_fatal"
    elif "SparkFatalException" in joined:
        classification = "spark_fatal_exception"
    elif candidates:
        classification = "execution_error_detected"
    elif success_signature:
        classification = "execution_success"
    else:
        classification = "no_registered_error_signature"
    deeper = [
        line
        for line in candidates
        if line.lower().startswith("caused by:") and "SparkFatalException" not in line
    ]
    return {
        "classification": classification,
        "line_count": len(lines),
        "root_cause_candidates": candidates,
        "deeper_nested_cause_exposed": bool(deeper),
        "interpretation_boundary": (
            "The task log identifies the failing Spark stage but does not prove a more specific resource cause."
            if classification == "spark_broadcast_exchange_fatal" and not deeper
            else None
        ),
    }


def execution_status_label(row: dict[str, Any]) -> str:
    description = str(row.get("statusDesc") or "").strip()
    if description:
        return description
    return {
        0: "waiting",
        1: "waiting",
        2: "dispatched",
        3: "running",
        4: "success",
        5: "failed",
        6: "success",
        7: "stage执行失败",
    }.get(int(row.get("status") or 0), str(row.get("status") or "unknown"))


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return (cleaned or "stage")[:80]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_execution_log_bundle(
    *,
    task: ScopedTask,
    identity: dict[str, Any],
    execution_id: int,
    bundle: dict[str, Any],
    used_endpoints: set[str],
    artifact_root: Path,
) -> Path:
    validate_artifact_root(artifact_root)
    ensure_runtime([artifact_root])
    run_dir = safe_artifact_dir(artifact_root)
    stage_records: list[dict[str, Any]] = []
    redacted_logs: list[str] = []
    for stage in bundle["stages"]:
        metadata, _ = redact_structure(stage["metadata"])
        stage_execution_id = int(metadata.get("id") or 0)
        stage_name = str(metadata.get("stageName") or "stage")
        redacted = redact_text(str(stage["log"] or ""))
        log_path = run_dir / f"stage_{stage_execution_id}_{_slug(stage_name)}.log"
        log_path.write_text(redacted.text, encoding="utf-8", newline="\n")
        redacted_logs.append(redacted.text)
        stage_records.append(
            {
                "metadata": metadata,
                "log_file": log_path.name,
                "log_sha256": _sha256_bytes(log_path.read_bytes()),
                "redactions": [dict(item) for item in redacted.findings],
            }
        )
    safe_bundle, structure_findings = redact_structure(
        {
            "task_schedule": bundle["task_schedule"],
            "period": bundle["period"],
            "execution": bundle["execution"],
            "execution_detail": bundle["execution_detail"],
        }
    )
    execution_payload = {
        "schema_version": "tiangong2-execution-log-v1",
        "read_only": True,
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
            "execution_id": execution_id,
        },
        **safe_bundle,
        "stages": stage_records,
        "structure_redactions": structure_findings,
        "diagnostic": _diagnose_logs(redacted_logs),
        "used_endpoints": sorted(used_endpoints),
    }
    execution_path = run_dir / "execution.json"
    execution_path.write_text(
        json.dumps(execution_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    files = []
    for path in sorted(item for item in run_dir.iterdir() if item.is_file()):
        files.append(
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256_bytes(path.read_bytes()),
            }
        )
    manifest = {
        "schema_version": "tiangong2-execution-log-manifest-v1",
        "read_only": True,
        "remote_mutations": 0,
        "execution_id": execution_id,
        "artifact_files": files,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return run_dir


def write_execution_history_bundle(
    *,
    task: ScopedTask,
    identity: dict[str, Any],
    limit: int,
    bundle: dict[str, Any],
    used_endpoints: set[str],
    artifact_root: Path,
) -> Path:
    """Write a redacted, runtime-only execution-history artifact."""

    validate_artifact_root(artifact_root)
    ensure_runtime([artifact_root])
    run_dir = safe_artifact_dir(artifact_root)
    safe_bundle, structure_findings = redact_structure(bundle)
    payload = {
        "schema_version": "tiangong2-execution-history-v1",
        "read_only": True,
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
        },
        "limit": limit,
        **safe_bundle,
        "structure_redactions": structure_findings,
        "used_endpoints": sorted(used_endpoints),
    }
    history_path = run_dir / "history.json"
    history_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    manifest = {
        "schema_version": "tiangong2-execution-history-manifest-v1",
        "read_only": True,
        "remote_mutations": 0,
        "execution_count": len(payload["executions"]),
        "artifact_files": [
            {
                "path": history_path.name,
                "bytes": history_path.stat().st_size,
                "sha256": _sha256_bytes(history_path.read_bytes()),
            }
        ],
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return run_dir
