"""Build a row-redacted ResultArtifact for every governed SQL run."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


RESULT_SCHEMA_VERSION = "1.0.0"
SKILLS_ROOT = Path(__file__).resolve().parents[3]
RESULT_SCHEMA_PATH = SKILLS_ROOT / "_shared" / "text2sql_core" / "schemas" / "result_artifact.schema.json"


def build_result_artifact(
    *,
    trace_id: str,
    domain: str,
    plan_id: str | None,
    sql_sha256: str,
    policy_report_sha256: str,
    ok: bool,
    status: str,
    query_id: str | None,
    requested_engine: str | None,
    selected_engine_label: str | None,
    history_engine: str | None,
    query_duration_seconds: float | None,
    elapsed_seconds: float | None,
    result_preview: dict[str, Any] | None,
    download_path: str | None,
    expected_columns: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    headers = [str(item) for item in (result_preview or {}).get("headers", [])]
    diagnostics = _validate_result(
        ok=ok,
        result_preview=result_preview,
        headers=headers,
        expected_columns=expected_columns,
        download_path=download_path,
    )
    if any(item["severity"] == "error" for item in diagnostics):
        validation_status = "failed"
    elif diagnostics:
        validation_status = "warning"
    else:
        validation_status = "passed"
    download = None
    if download_path:
        path = Path(download_path)
        download = {
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
            "size_bytes": path.stat().st_size if path.is_file() else None,
        }
    artifact: dict[str, Any] = {
        "artifact_type": "result_artifact",
        "schema_version": RESULT_SCHEMA_VERSION,
        "artifact_id": f"result_{uuid.uuid4().hex}",
        "artifact_sha256": "",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "trace_id": trace_id,
        "domain": domain,
        "plan_id": plan_id,
        "sql_sha256": sql_sha256,
        "policy_report_sha256": policy_report_sha256,
        "query_id": query_id,
        "status": status,
        "ok": ok,
        "engine": {
            "requested": requested_engine,
            "selected_label": selected_engine_label,
            "history_value": history_engine,
        },
        "timing": {
            "query_duration_seconds": query_duration_seconds,
            "elapsed_seconds": elapsed_seconds,
        },
        "result": {
            "headers": headers,
            "row_count_visible": (result_preview or {}).get("row_count_visible"),
            "no_more": (result_preview or {}).get("no_more"),
            "preview_sha256": _preview_sha256(result_preview) if result_preview else None,
            "preview_rows_redacted": True,
        },
        "download": download,
        "validation": {
            "status": validation_status,
            "expected_columns": list(dict.fromkeys(str(item) for item in expected_columns if str(item))),
            "diagnostics": diagnostics,
        },
    }
    artifact["artifact_sha256"] = result_artifact_sha256(artifact)
    validate_result_artifact(artifact)
    return artifact


def result_artifact_sha256(artifact: dict[str, Any]) -> str:
    payload = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def validate_result_artifact(artifact: dict[str, Any]) -> None:
    schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(artifact), key=lambda item: list(item.path))
    if errors:
        rendered = "; ".join(
            f"{'.'.join(map(str, item.path)) or '<root>'}: {item.message}"
            for item in errors
        )
        raise ValueError(f"ResultArtifact schema validation failed: {rendered}")
    if artifact.get("artifact_sha256") != result_artifact_sha256(artifact):
        raise ValueError("ResultArtifact hash is invalid")


def write_result_artifact(path: Path, artifact: dict[str, Any]) -> None:
    validate_result_artifact(artifact)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(artifact, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _validate_result(
    *,
    ok: bool,
    result_preview: dict[str, Any] | None,
    headers: list[str],
    expected_columns: tuple[str, ...] | list[str],
    download_path: str | None,
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if ok and result_preview is None:
        diagnostics.append(_diagnostic("RESULT_PREVIEW_MISSING", "warning", "Successful query has no visible result preview metadata."))
    normalized_headers = [item.strip().lower() for item in headers]
    if len(normalized_headers) != len(set(normalized_headers)):
        diagnostics.append(_diagnostic("DUPLICATE_RESULT_COLUMNS", "error", "Result preview contains duplicate column names."))
    expected = {str(item).strip().lower() for item in expected_columns if str(item).strip()}
    missing = sorted(expected - set(normalized_headers))
    if ok and missing:
        diagnostics.append(
            _diagnostic(
                "EXPECTED_RESULT_COLUMNS_MISSING",
                "warning",
                "Result preview is missing expected QueryPlan outputs: " + ", ".join(missing),
            )
        )
    rows = (result_preview or {}).get("rows", [])
    if headers and isinstance(rows, list) and any(isinstance(row, list) and len(row) != len(headers) for row in rows):
        diagnostics.append(_diagnostic("RESULT_ROW_SHAPE_MISMATCH", "error", "One or more preview rows do not match the header width."))
    if download_path and not Path(download_path).is_file():
        diagnostics.append(_diagnostic("DOWNLOAD_ARTIFACT_MISSING", "error", "Run summary points to a missing download artifact."))
    return diagnostics


def _diagnostic(code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _preview_sha256(result_preview: dict[str, Any]) -> str:
    rendered = json.dumps(result_preview, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()
