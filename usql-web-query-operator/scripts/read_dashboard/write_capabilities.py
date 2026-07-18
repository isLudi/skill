"""P4A dashboard write capability registry and sandbox probe helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from jsonschema import Draft202012Validator

from _shared.errors import UsageError


SKILL_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = SKILL_ROOT / "references" / "dashboard_write_capabilities.json"
REGISTRY_SCHEMA = SKILL_ROOT / "references" / "dashboard_write_capability_registry.schema.json"
PROBE_SCHEMA = SKILL_ROOT / "references" / "dashboard_write_probe.schema.json"

MANUAL_PROBE_OPERATIONS = {
    "bind_dataset",
    "create_pivot_component",
    "update_component_fields",
    "create_formula",
    "update_formula",
    "create_public_filter",
    "update_filter_dynamic_default",
    "update_component_filter",
    "update_layout",
    "update_theme",
}
DANGEROUS_URL_FRAGMENTS = (
    "saveandpublish",
    "/delete",
    "/permission/",
    "/permissions/",
    "/auth/",
)


def canonical_sha256(payload: Mapping[str, Any], hash_field: str) -> str:
    body = dict(payload)
    body.pop(hash_field, None)
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_capability_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(REGISTRY_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: list(item.path))
    if errors:
        raise UsageError("Invalid dashboard capability registry: " + "; ".join(error.message for error in errors[:5]))
    expected = canonical_sha256(payload, "registry_sha256")
    if payload.get("registry_sha256") != expected:
        raise UsageError("Dashboard capability registry SHA-256 is stale.")
    operations: set[str] = set()
    for capability in payload["capabilities"]:
        operation = str(capability["operation"])
        if operation in operations:
            raise UsageError(f"Duplicate dashboard capability operation: {operation}")
        operations.add(operation)
        if capability["write_policy"] == "allowlisted" and capability["maturity"] != "verified":
            raise UsageError(f"Allowlisted capability must be verified: {operation}")
        if capability["write_policy"] == "allowlisted" and capability["readback_coverage"] != "full":
            raise UsageError(f"Allowlisted capability must have full readback: {operation}")
        if capability["write_policy"] == "allowlisted" and not capability.get("adapter"):
            raise UsageError(f"Allowlisted capability must have a production adapter: {operation}")
        transaction_class = str(capability.get("transaction_class") or "")
        recovery_policy = str(capability.get("recovery_policy") or "")
        if transaction_class == "creation_saga" and recovery_policy != "creation_saga_no_auto_delete":
            raise UsageError(f"Creation-saga capability must forbid automatic delete: {operation}")
        if capability["write_policy"] == "separate_confirmation" and (
            transaction_class != "separate_publish" or recovery_policy != "separate_publish"
        ):
            raise UsageError(f"Separate-confirmation capability must use separate_publish: {operation}")
        if capability["write_policy"] == "allowlisted" and transaction_class not in {
            "compensating_restore",
            "creation_saga",
        }:
            raise UsageError(f"Allowlisted capability has unsupported transaction class: {operation}")
        if capability["write_policy"] == "sandbox_only":
            if capability["maturity"] != "sandbox_verified":
                raise UsageError(f"Sandbox-only capability must be sandbox_verified: {operation}")
            if capability["readback_coverage"] != "full" or not capability.get("adapter"):
                raise UsageError(f"Sandbox-only capability requires a full-readback adapter: {operation}")
            if not capability.get("evidence"):
                raise UsageError(f"Sandbox-only capability requires immutable evidence: {operation}")
        if capability["maturity"] == "sandbox_verified" and capability["write_policy"] != "sandbox_only":
            raise UsageError(f"sandbox_verified capability must remain sandbox_only: {operation}")
        for evidence in capability["evidence"]:
            source = SKILL_ROOT / evidence["source_path"]
            if not source.is_file():
                raise UsageError(f"Capability evidence is missing: {evidence['source_path']}")
            actual = hashlib.sha256(source.read_bytes()).hexdigest()
            if evidence["source_sha256"] != actual:
                raise UsageError(f"Capability evidence SHA-256 is stale: {evidence['source_path']}")
    return payload


def capability_by_operation(registry: Mapping[str, Any], operation: str) -> dict[str, Any]:
    matches = [item for item in registry.get("capabilities", []) if item.get("operation") == operation]
    if len(matches) != 1:
        raise UsageError(f"Dashboard capability is not registered exactly once: {operation}")
    return dict(matches[0])


def registry_summary(registry: Mapping[str, Any]) -> dict[str, Any]:
    capabilities = list(registry.get("capabilities") or [])
    return {
        "ok": True,
        "artifact_type": registry.get("artifact_type"),
        "platform": registry.get("platform"),
        "registry_sha256": registry.get("registry_sha256"),
        "capability_count": len(capabilities),
        "by_maturity": _count_by(capabilities, "maturity"),
        "by_write_policy": _count_by(capabilities, "write_policy"),
        "allowlisted_operations": sorted(
            str(item["operation"]) for item in capabilities if item.get("write_policy") == "allowlisted"
        ),
        "sandbox_only_operations": sorted(
            str(item["operation"])
            for item in capabilities
            if item.get("write_policy") == "sandbox_only"
        ),
        "separate_confirmation_operations": sorted(
            str(item["operation"])
            for item in capabilities
            if item.get("write_policy") == "separate_confirmation"
        ),
        "blocked_operations": sorted(
            str(item["operation"]) for item in capabilities if item.get("write_policy") == "blocked"
        ),
    }


def preflight_manual_probe(
    registry: Mapping[str, Any],
    *,
    operation: str,
    dashboard_id: str,
    expected_dashboard_name: str,
    domain: str,
    headed: bool,
    confirmed: bool,
) -> dict[str, Any]:
    capability = capability_by_operation(registry, operation)
    if operation not in MANUAL_PROBE_OPERATIONS:
        raise UsageError(f"Operation is not eligible for sandbox manual capture: {operation}")
    if not confirmed:
        raise UsageError("Sandbox write evidence capture requires --confirm-sandbox-write.")
    if not headed:
        raise UsageError("Sandbox write evidence capture requires --headed for a visible manual action.")
    if domain not in {"market_consultant", "qingcheng"}:
        raise UsageError("Sandbox write evidence capture requires a resolved business domain.")
    if not dashboard_id.startswith("dashboard_") or not dashboard_id.removeprefix("dashboard_").isdigit():
        raise UsageError("Sandbox dashboard ID must use dashboard_<digits>.")
    lowered_name = expected_dashboard_name.casefold()
    if not any(marker in lowered_name for marker in ("p4a", "sandbox", "test", "沙箱", "测试")):
        raise UsageError("Sandbox dashboard name must contain P4A, sandbox, test, 沙箱, or 测试.")
    return capability


def request_key_paths(value: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.append(path)
            paths.extend(request_key_paths(value[key], path))
    elif isinstance(value, list) and value:
        path = f"{prefix}[]" if prefix else "[]"
        paths.append(path)
        paths.extend(request_key_paths(value[0], path))
    return sorted(set(paths))


def request_observation(request: Any, *, blocked: bool = False) -> dict[str, Any]:
    raw = request.post_data or ""
    try:
        candidate = request.post_data_json if raw else None
        parsed = candidate() if callable(candidate) else candidate
    except Exception:  # noqa: BLE001
        parsed = None
    url = urlparse(request.url)
    return {
        "method": str(request.method),
        "url_path": url.path,
        "host": url.netloc,
        "payload_bytes": len(raw.encode("utf-8")),
        "request_key_paths": request_key_paths(parsed),
        "response_status": None,
        "response_content_type": None,
        "blocked": blocked,
    }


def is_dangerous_request(request: Any) -> bool:
    if str(request.method).upper() in {"GET", "HEAD", "OPTIONS"}:
        return False
    lowered = str(request.url).lower()
    return any(fragment in lowered for fragment in DANGEROUS_URL_FRAGMENTS)


def build_probe_artifact(
    *,
    operation: str,
    domain: str,
    dashboard_id: str,
    dashboard_name: str,
    started_at: str,
    before_profile_sha256: str,
    after_profile_sha256: str,
    observations: list[dict[str, Any]],
    blocked_requests: list[dict[str, Any]],
) -> dict[str, Any]:
    changed = before_profile_sha256 != after_profile_sha256
    if blocked_requests:
        status = "blocked_dangerous_request"
    elif observations and changed:
        status = "evidence_captured"
    elif observations or changed:
        status = "incomplete"
    else:
        status = "no_effect"
    payload = {
        "schema_version": "1.0.0",
        "artifact_type": "DashboardWriteProbe",
        "operation": operation,
        "domain": domain,
        "sandbox_dashboard_id": dashboard_id,
        "sandbox_dashboard_name": dashboard_name,
        "sandbox_confirmed": True,
        "capture_boundary": (
            "Manual action in an explicitly confirmed sandbox. Unknown requests are observed only; "
            "publish, delete, permission, and auth writes are blocked. Registry promotion is never automatic."
        ),
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "before_profile_sha256": before_profile_sha256,
        "after_profile_sha256": after_profile_sha256,
        "profile_changed": changed,
        "observations": observations,
        "blocked_requests": blocked_requests,
        "status": status,
        "probe_sha256": "",
    }
    payload["probe_sha256"] = canonical_sha256(payload, "probe_sha256")
    schema = json.loads(PROBE_SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(payload))
    if errors:
        raise UsageError("Invalid DashboardWriteProbe artifact: " + errors[0].message)
    return payload


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))
