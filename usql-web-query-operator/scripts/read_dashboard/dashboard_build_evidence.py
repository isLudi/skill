"""Redacted evidence contracts for P4C sandbox request capture."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from _shared.errors import UsageError

from .dashboard_change import canonical_sha256


BUILD_EVIDENCE_OPERATIONS = {
    "create_dashboard",
    "create_formula",
    "create_metric_group_component",
    "create_pivot_component",
    "create_bar_component",
    "create_pie_component",
    "create_public_filter",
    "create_tab_container",
    "create_text_component",
    "rename_new_component_metrics",
    "style_new_components",
    "assemble_tab_slots",
    "assemble_new_dashboard",
}
SKILL_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_SCHEMA = SKILL_ROOT / "references" / "dashboard_build_evidence.schema.json"


def _has_sandbox_marker(value: str) -> bool:
    lowered = value.casefold()
    return any(marker in lowered for marker in ("sandbox", "test", "p4c", "沙箱", "测试"))


def preflight_build_evidence_capture(
    *,
    operation: str,
    scope: str,
    domain: str,
    confirmed: bool,
    headed: bool,
    sandbox_dashboard_id: str | None,
    expected_dashboard_name: str | None,
    folder_id: str | None,
    folder_path: str | None,
    folder_name: str | None,
    sandbox_subject_id: str | None = None,
    sandbox_subject_name: str | None = None,
) -> None:
    if operation not in BUILD_EVIDENCE_OPERATIONS:
        raise UsageError(f"Unsupported P4C evidence operation: {operation}")
    if scope not in {"dashboard", "folder"}:
        raise UsageError("P4C evidence scope must be dashboard or folder.")
    if domain not in {"market_consultant", "qingcheng"}:
        raise UsageError("P4C evidence capture requires a resolved business domain.")
    if not confirmed or not headed:
        raise UsageError("P4C evidence capture requires --confirm-sandbox-write and --headed.")
    if scope == "folder":
        if operation != "create_dashboard":
            raise UsageError("Folder-scoped P4C evidence is limited to create_dashboard.")
        if not folder_id or not folder_path or not folder_name:
            raise UsageError("Folder-scoped evidence requires exact folder id, path, and name.")
        if not _has_sandbox_marker(f"{folder_path}/{folder_name}"):
            raise UsageError("P4C folder evidence is restricted to a clearly named test/sandbox folder.")
    else:
        if operation == "create_dashboard":
            raise UsageError("create_dashboard evidence must be captured at folder scope.")
        if not sandbox_dashboard_id or not sandbox_dashboard_id.startswith("dashboard_"):
            raise UsageError("Dashboard-scoped evidence requires one exact dashboard_* identity.")
        if not expected_dashboard_name or not _has_sandbox_marker(expected_dashboard_name):
            raise UsageError(
                "The exact dashboard name must be explicitly marked as test/sandbox."
            )
        if operation == "create_formula":
            if not sandbox_subject_id or not sandbox_subject_name:
                raise UsageError(
                    "create_formula evidence requires an exact dedicated sandbox subject id and name."
                )
            if not _has_sandbox_marker(sandbox_subject_name):
                raise UsageError("The formula subject must be explicitly named as a test/sandbox dataset.")


def menu_folder_snapshot(
    menu: Mapping[str, Any],
    *,
    folder_id: str,
    folder_path: str,
    folder_name: str,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []

    def walk(value: Any, path: list[str]) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item, path)
            return
        if not isinstance(value, Mapping):
            return
        name = str(value.get("name") or "").strip()
        node_path = [*path, name] if name else list(path)
        identity = str(value.get("id") or value.get("fileValue") or value.get("key") or "")
        if identity == folder_id and name == folder_name and "/".join(node_path) == folder_path:
            dashboards: list[dict[str, str]] = []

            def collect(children: Any) -> None:
                if isinstance(children, list):
                    for child in children:
                        collect(child)
                    return
                if not isinstance(children, Mapping):
                    return
                child_id = str(
                    children.get("fileValue") or children.get("id") or children.get("key") or ""
                )
                child_name = str(children.get("name") or "")
                if child_id.startswith("dashboard_"):
                    dashboards.append({"dashboard_id": child_id, "dashboard_name": child_name})
                collect(children.get("children") or [])

            collect(value.get("children") or [])
            matches.append(
                {
                    "folder_id": identity,
                    "folder_path": "/".join(node_path),
                    "folder_name": name,
                    "dashboards": sorted(dashboards, key=lambda item: item["dashboard_id"]),
                }
            )
        for child in value.get("children") or []:
            walk(child, node_path)
        for key, child in value.items():
            if key == "children":
                continue
            if isinstance(child, (dict, list)):
                walk(child, path)

    walk(menu, [])
    if len(matches) != 1:
        raise UsageError(
            f"Expected exactly one sandbox folder identity/path match, found {len(matches)}."
        )
    snapshot = matches[0]
    snapshot["snapshot_sha256"] = canonical_sha256(snapshot)
    return snapshot


def build_dashboard_build_evidence(
    *,
    operation: str,
    domain: str,
    scope: str,
    target: Mapping[str, Any],
    started_at: str,
    before_state_sha256: str,
    after_state_sha256: str,
    observations: list[dict[str, Any]],
    blocked_requests: list[dict[str, Any]],
    created_resources: list[dict[str, Any]],
) -> dict[str, Any]:
    def freeze_observation(value: Mapping[str, Any]) -> dict[str, Any]:
        frozen = dict(value)
        frozen["observation_sha256"] = canonical_sha256(frozen)
        return frozen

    immutable_observations = [freeze_observation(item) for item in observations]
    immutable_blocked_requests = [freeze_observation(item) for item in blocked_requests]
    state_changed = before_state_sha256 != after_state_sha256
    successful_observations = [
        item
        for item in immutable_observations
        if isinstance(item.get("response_status"), int)
        and 200 <= int(item["response_status"]) < 300
    ]
    if immutable_blocked_requests:
        status = "blocked_dangerous_request"
    elif state_changed and successful_observations:
        status = "evidence_captured"
    elif state_changed or immutable_observations:
        status = "incomplete"
    else:
        status = "no_effect"
    result = {
        "schema_version": "1.0.0",
        "artifact_type": "DashboardBuildEvidence",
        "operation": operation,
        "domain": domain,
        "scope": scope,
        "target": dict(target),
        "sandbox_confirmed": True,
        "capture_boundary": (
            "One explicitly confirmed sandbox draft action. Publish, delete, permission, "
            "authentication, and move-folder writes are blocked. Payload values are not stored."
        ),
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "before_state_sha256": before_state_sha256,
        "after_state_sha256": after_state_sha256,
        "state_changed": state_changed,
        "observations": immutable_observations,
        "blocked_requests": immutable_blocked_requests,
        "created_resources": created_resources,
        "automatic_delete_attempted": False,
        "registry_promoted": False,
        "status": status,
        "evidence_sha256": "",
    }
    result["evidence_sha256"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "evidence_sha256"}
    )
    schema = json.loads(EVIDENCE_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(result),
        key=lambda item: list(item.path),
    )
    if errors:
        raise UsageError("Invalid DashboardBuildEvidence: " + errors[0].message)
    return result


def verify_dashboard_build_evidence_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if manifest.get("artifact_type") != "DashboardBuildEvidenceManifest":
        raise UsageError("Evidence manifest artifact_type must be DashboardBuildEvidenceManifest.")
    entries = manifest.get("evidence") if isinstance(manifest.get("evidence"), list) else []
    by_operation: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            errors.append("Evidence manifest entries must be objects.")
            continue
        operation = str(entry.get("operation") or "")
        path = Path(str(entry.get("path") or ""))
        if operation in by_operation:
            errors.append(f"duplicate evidence operation: {operation}")
            continue
        if not path.is_file():
            errors.append(f"missing evidence file: {path}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        actual = canonical_sha256(
            {key: value for key, value in payload.items() if key != "evidence_sha256"}
        )
        if payload.get("evidence_sha256") != actual or entry.get("evidence_sha256") != actual:
            errors.append(f"evidence SHA-256 mismatch: {operation}")
        if payload.get("operation") != operation or payload.get("status") != "evidence_captured":
            errors.append(f"evidence is not complete for operation: {operation}")
        selected_observation_sha256 = str(entry.get("selected_observation_sha256") or "")
        successful_observation_hashes = {
            str(item.get("observation_sha256") or "")
            for item in payload.get("observations") or []
            if isinstance(item, Mapping)
            and item.get("blocked") is False
            and isinstance(item.get("response_status"), int)
            and 200 <= int(item["response_status"]) < 300
        }
        if selected_observation_sha256 not in successful_observation_hashes:
            errors.append(f"selected successful request evidence mismatch: {operation}")
        if payload.get("blocked_requests") or payload.get("automatic_delete_attempted") is not False:
            errors.append(f"unsafe evidence bundle: {operation}")
        by_operation[operation] = payload
    missing = sorted(BUILD_EVIDENCE_OPERATIONS - set(by_operation))
    if missing:
        errors.append("missing operations: " + ", ".join(missing))
    return {
        "ok": not errors,
        "artifact_type": "DashboardBuildEvidenceVerification",
        "operation_count": len(by_operation),
        "required_operation_count": len(BUILD_EVIDENCE_OPERATIONS),
        "errors": errors,
        "sandbox_evidence_complete": not errors,
        "production_allowlisted": False,
        "note": (
            "Immutable request evidence is only one promotion gate. Adapter, failure, idempotency, "
            "resume, full readback, and production registry evidence are still required."
        ),
    }


__all__ = [
    "BUILD_EVIDENCE_OPERATIONS",
    "build_dashboard_build_evidence",
    "menu_folder_snapshot",
    "preflight_build_evidence_capture",
    "verify_dashboard_build_evidence_manifest",
]
