"""Privacy-preserving provenance sidecars for Text2SQL planning and execution."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


TRACE_SCHEMA_VERSION = "1.0.0"
TRACE_DOMAINS = frozenset({"market_consultant", "qingcheng", "unresolved"})
TRACE_STAGE_STATUSES = frozenset({"started", "success", "warning", "blocked", "error", "skipped"})
_SHA256_LENGTH = 64


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_json_sha256(value: Any, *, omit_key: str | None = None) -> str:
    payload = value
    if omit_key and isinstance(value, dict):
        payload = {key: item for key, item in value.items() if key != omit_key}
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def catalog_snapshot(skill_root: Path, core_root: Path) -> dict[str, str | None]:
    paths = {
        "domain_manifest_sha256": skill_root / "semantic" / "domain_manifest.json",
        "contract_index_sha256": skill_root / "semantic" / "generated" / "contract_index.json",
        "physical_catalog_sha256": core_root / "catalog" / "physical_catalog.json",
    }
    return {
        name: file_sha256(path) if path.is_file() else None
        for name, path in paths.items()
    }


def create_query_trace(
    *,
    domain: str,
    question_sha256: str | None = None,
    spec: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
    sql_sha256: str | None = None,
    snapshot: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    if domain not in TRACE_DOMAINS:
        raise ValueError(f"unsupported QueryTrace domain: {domain}")
    for name, digest in (("question_sha256", question_sha256), ("sql_sha256", sql_sha256)):
        _validate_sha256(name, digest, allow_none=True)
    now = utc_now()
    trace: dict[str, Any] = {
        "artifact_type": "query_trace",
        "schema_version": TRACE_SCHEMA_VERSION,
        "trace_id": f"trace_{uuid.uuid4().hex}",
        "created_at": now,
        "updated_at": now,
        "domain": domain,
        "references": {
            "spec_id": spec.get("spec_id") if spec else None,
            "spec_sha256": canonical_json_sha256(spec) if spec else None,
            "plan_id": plan.get("plan_id") if plan else None,
            "plan_sha256": canonical_json_sha256(plan) if plan else None,
            "sql_sha256": sql_sha256 or (plan.get("sql_sha256") if plan else None),
        },
        "catalog_snapshot": snapshot or {
            "domain_manifest_sha256": None,
            "contract_index_sha256": None,
            "physical_catalog_sha256": None,
        },
        "stages": [],
        "execution": None,
        "result_artifact": None,
    }
    if question_sha256:
        trace["question_sha256"] = question_sha256
    validate_query_trace(trace)
    return trace


def bind_query_plan(trace: dict[str, Any], plan: dict[str, Any]) -> None:
    _require_domain_match(trace, str(plan.get("domain", "unresolved")))
    references = trace["references"]
    references["plan_id"] = plan.get("plan_id")
    references["plan_sha256"] = canonical_json_sha256(plan)
    if plan.get("sql_sha256"):
        bind_sql_sha256(trace, str(plan["sql_sha256"]))
    _touch(trace)


def bind_plan_reference(
    trace: dict[str, Any],
    *,
    domain: str,
    plan_id: str | None,
    plan_sha256: str,
) -> None:
    _require_domain_match(trace, domain)
    _validate_sha256("plan_sha256", plan_sha256)
    references = trace["references"]
    existing_id = references.get("plan_id")
    existing_hash = references.get("plan_sha256")
    if existing_id and plan_id and existing_id != plan_id:
        raise ValueError("QueryTrace plan_id does not match the supplied QueryPlan")
    if existing_hash and existing_hash != plan_sha256:
        raise ValueError("QueryTrace plan_sha256 does not match the supplied QueryPlan")
    references["plan_id"] = plan_id or existing_id
    references["plan_sha256"] = plan_sha256
    _touch(trace)


def bind_sql_sha256(trace: dict[str, Any], sql_sha256: str) -> None:
    _validate_sha256("sql_sha256", sql_sha256)
    existing = trace["references"].get("sql_sha256")
    if existing and existing != sql_sha256:
        raise ValueError("QueryTrace sql_sha256 does not match the submitted SQL")
    trace["references"]["sql_sha256"] = sql_sha256
    _touch(trace)


def append_trace_stage(
    trace: dict[str, Any],
    *,
    name: str,
    status: str,
    duration_ms: float | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    if not name.strip():
        raise ValueError("QueryTrace stage name is required")
    if status not in TRACE_STAGE_STATUSES:
        raise ValueError(f"unsupported QueryTrace stage status: {status}")
    if duration_ms is not None and duration_ms < 0:
        raise ValueError("QueryTrace stage duration_ms cannot be negative")
    trace["stages"].append(
        {
            "name": name,
            "status": status,
            "recorded_at": utc_now(),
            "duration_ms": round(duration_ms, 3) if duration_ms is not None else None,
            "details": details or {},
        }
    )
    _touch(trace)


def bind_execution(
    trace: dict[str, Any],
    *,
    status: str,
    query_id: str | None,
    engine: str | None,
    elapsed_seconds: float | None,
    policy_report_sha256: str | None,
) -> None:
    _validate_sha256("policy_report_sha256", policy_report_sha256, allow_none=True)
    trace["execution"] = {
        "status": status,
        "query_id": query_id,
        "engine": engine,
        "elapsed_seconds": elapsed_seconds,
        "policy_report_sha256": policy_report_sha256,
    }
    _touch(trace)


def bind_result_artifact(trace: dict[str, Any], *, artifact_id: str, artifact_sha256: str) -> None:
    _validate_sha256("artifact_sha256", artifact_sha256)
    trace["result_artifact"] = {
        "artifact_id": artifact_id,
        "artifact_sha256": artifact_sha256,
    }
    _touch(trace)


def validate_query_trace(trace: dict[str, Any], *, schema_path: Path | None = None) -> None:
    schema_file = schema_path or Path(__file__).resolve().parents[1] / "schemas" / "query_trace.schema.json"
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(trace), key=lambda item: list(item.path))
    if errors:
        rendered = "; ".join(
            f"{'.'.join(map(str, item.path)) or '<root>'}: {item.message}"
            for item in errors
        )
        raise ValueError(f"QueryTrace schema validation failed: {rendered}")


def load_query_trace(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"QueryTrace file not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to load QueryTrace {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("QueryTrace must be a JSON object")
    validate_query_trace(payload)
    return payload


def write_query_trace(path: Path, trace: dict[str, Any]) -> None:
    _touch(trace)
    validate_query_trace(trace)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(trace, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _require_domain_match(trace: dict[str, Any], domain: str) -> None:
    current = trace.get("domain")
    if current == "unresolved" and domain in TRACE_DOMAINS - {"unresolved"}:
        trace["domain"] = domain
        return
    if domain != "unresolved" and current != domain:
        raise ValueError(f"QueryTrace domain {current!r} does not match {domain!r}")


def _touch(trace: dict[str, Any]) -> None:
    trace["updated_at"] = utc_now()


def _validate_sha256(name: str, value: str | None, *, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    if not isinstance(value, str) or len(value) != _SHA256_LENGTH or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a lowercase 64-character SHA-256 digest")
