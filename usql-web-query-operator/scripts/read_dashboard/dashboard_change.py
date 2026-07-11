"""Governed P3 dashboard design, diff, draft-apply, and publish helpers."""

from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path
from typing import Any

from _shared.errors import UsageError

from .edit_profile import (
    build_edit_url,
    extract_loaded_html_id,
    open_edit_page,
    profile_edit_dashboard,
)
from .filter_edit import (
    build_publish_payload,
    fetch_edit_config,
    publish_dashboard,
)
from .dashboard_write_adapters import (
    AppliedDashboardMutation,
    apply_planned_operation,
    restore_planned_operation,
)
from .write_capabilities import capability_by_operation, load_capability_registry


SUPPORTED_DOMAINS = {"market_consultant", "qingcheng"}
SUPPORTED_APPLY_OPERATIONS = {
    "update_component_fields",
    "update_filter_dynamic_default",
    "update_formula",
    "update_layout",
    "update_theme",
}


def _diagnostic_errors(diagnostics: Any) -> list[dict[str, Any]]:
    if not isinstance(diagnostics, list):
        return []
    return [item for item in diagnostics if isinstance(item, dict) and item.get("severity") == "error"]


def _core_api() -> Any:
    skills_root = Path(__file__).resolve().parents[3]
    core_root = skills_root / "_shared" / "text2sql_core"
    if str(core_root) not in sys.path:
        sys.path.insert(0, str(core_root))
    try:
        from text2sql_core import dashboard_change as core
    except ImportError as exc:  # pragma: no cover - exercised by stack validation
        raise UsageError(f"Shared Text2SQL dashboard-change core is unavailable: {exc}") from exc
    return core


def read_json_artifact(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read {label} JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise UsageError(f"{label} must be a JSON object: {path}")
    return value


def artifact_domain(value: dict[str, Any]) -> str:
    domain = value.get("domain")
    if not domain and isinstance(value.get("snapshot"), dict):
        dashboard = value["snapshot"].get("dashboard")
        if isinstance(dashboard, dict):
            domain = dashboard.get("domain")
    return str(domain or "unresolved")


def require_resolved_domain(value: dict[str, Any], expected_domain: str | None = None) -> str:
    domain = artifact_domain(value)
    if domain not in SUPPORTED_DOMAINS:
        raise UsageError("Dashboard changes require a resolved market_consultant or qingcheng domain.")
    if expected_domain and domain != expected_domain:
        raise UsageError(f"Dashboard domain mismatch: expected {expected_domain}, got {domain}.")
    return domain


def normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    try:
        return _core_api().normalize_dashboard_profile(profile)
    except (KeyError, TypeError, ValueError) as exc:
        raise UsageError(f"Invalid DashboardProfile: {exc}") from exc


def require_complete_profile(profile: dict[str, Any], label: str = "DashboardProfile") -> dict[str, Any]:
    normalized = normalize_profile(profile)
    if normalized.get("completeness", {}).get("status") != "complete":
        raise UsageError(f"{label} is incomplete; refresh the full profile before design or mutation.")
    return normalized


def artifact_sha256(value: dict[str, Any], field_name: str) -> str:
    return str(_core_api().artifact_sha256(value, field_name))


def canonical_sha256(value: Any) -> str:
    return str(_core_api().canonical_sha256(value))


def publish_config_sha256(
    config: dict[str, Any],
    html_id: str | None,
) -> str:
    """Hash exactly the draft config fields that will enter saveAndPublish."""

    payload = build_publish_payload(config, "<precondition>", html_id)
    return canonical_sha256(payload)


def build_design_spec(
    dataset_spec: dict[str, Any],
    profile: dict[str, Any],
    desired_state: dict[str, Any] | None,
    *,
    query_plan_sha256: str | None,
    design_intent: str,
) -> dict[str, Any]:
    domain = require_resolved_domain(profile)
    require_resolved_domain(dataset_spec, domain)
    normalized_profile = require_complete_profile(profile)
    desired_state = copy.deepcopy(desired_state or {})
    for item in desired_state.get("public_filters") or []:
        if not isinstance(item, dict):
            continue
        if "default_value" in item:
            item["dynamics_filter_value"] = item.get("default_value")
        elif "dynamics_filter_value" in item:
            item["default_value"] = item.get("dynamics_filter_value")
        if "dynamic_default" in item:
            item["dynamics_filter"] = item.get("dynamic_default")
        elif "dynamics_filter" in item:
            item["dynamic_default"] = item.get("dynamics_filter")
        if item.get("dynamic_default") is True:
            item["auto_search_default_value"] = False
    try:
        design = _core_api().build_dashboard_design_spec(
            dataset_spec,
            normalized_profile,
            desired_components=desired_state.get("components"),
            desired_layout=desired_state.get("layout"),
            desired_formulas=desired_state.get("formulas"),
            desired_public_filters=desired_state.get("public_filters"),
            desired_component_filters=desired_state.get("component_filters"),
            desired_theme=desired_state.get("theme"),
            query_plan_sha256=query_plan_sha256,
            design_intent=design_intent,
        )
        return design
    except (KeyError, TypeError, ValueError) as exc:
        raise UsageError(f"Unable to build DashboardDesignSpec: {exc}") from exc


def build_change_plan(profile: dict[str, Any], design_spec: dict[str, Any]) -> dict[str, Any]:
    domain = require_resolved_domain(profile)
    require_resolved_domain(design_spec, domain)
    normalized_profile = require_complete_profile(profile)
    try:
        plan = _core_api().diff_dashboard(normalized_profile, design_spec)
    except (KeyError, TypeError, ValueError) as exc:
        raise UsageError(f"Unable to build DashboardChangePlan: {exc}") from exc
    diagnostics = _core_api().validate_dashboard_change_plan(plan, current_profile=normalized_profile)
    if _diagnostic_errors(diagnostics) and str(plan.get("status") or "") != "blocked":
        raise UsageError("Generated DashboardChangePlan failed shared-core validation.")
    return plan


def _plan_profile_sha256(plan: dict[str, Any]) -> str:
    return str(
        plan.get("base_profile_sha256")
        or plan.get("profile_sha256")
        or plan.get("source_profile_sha256")
        or ""
    )


def preflight_apply_plan(
    plan: dict[str, Any],
    supplied_sha256: str,
    *,
    expected_domain: str | None = None,
) -> list[dict[str, Any]]:
    domain = require_resolved_domain(plan, expected_domain)
    actual_hash = artifact_sha256(plan, "change_plan_sha256")
    embedded_hash = str(plan.get("change_plan_sha256") or "")
    if not supplied_sha256 or supplied_sha256 != actual_hash or embedded_hash != actual_hash:
        raise UsageError("ChangePlan SHA-256 mismatch; regenerate the dry-run plan before apply.")
    if plan.get("blocked_reasons"):
        raise UsageError("ChangePlan is blocked and cannot be applied.")
    if str(plan.get("status") or "") != "ready_for_dry_run":
        raise UsageError(
            f"ChangePlan status must be ready_for_dry_run for apply, got {plan.get('status')}."
        )
    if not _plan_profile_sha256(plan):
        raise UsageError("ChangePlan does not bind a source profile SHA-256.")
    plan_diagnostics = _core_api().validate_dashboard_change_plan(plan)
    if _diagnostic_errors(plan_diagnostics):
        raise UsageError("ChangePlan failed shared-core policy validation; no writes were attempted.")

    operations = plan.get("operations") or []
    if not isinstance(operations, list):
        raise UsageError("ChangePlan operations must be a list.")
    if not operations:
        raise UsageError("A no_changes ChangePlan cannot authorize draft writes or publication.")
    registry = load_capability_registry()
    for operation in operations:
        if not isinstance(operation, dict):
            raise UsageError("ChangePlan operations must be JSON objects.")
        operation_type = str(operation.get("type") or operation.get("operation_type") or "")
        write_status = str(operation.get("write_status") or "")
        if operation_type not in SUPPORTED_APPLY_OPERATIONS or write_status not in {"supported", "supported_apply"}:
            raise UsageError(
                f"Dashboard operation {operation_type or '<missing>'} is blocked_unsupported; no writes were attempted."
            )
        capability = capability_by_operation(registry, operation_type)
        if not (
            capability.get("maturity") == "verified"
            and capability.get("write_policy") == "allowlisted"
            and capability.get("readback_coverage") == "full"
        ):
            raise UsageError(
                f"Dashboard operation {operation_type} is not verified/allowlisted in the live capability registry."
            )
    if artifact_domain(plan) != domain:  # defensive: keep the resolved binding visible
        raise UsageError("ChangePlan domain binding changed during validation.")
    return operations


def _profile_dashboard_id(value: dict[str, Any]) -> str:
    dashboard_id = value.get("dashboard_id")
    if not dashboard_id and isinstance(value.get("snapshot"), dict):
        dashboard = value["snapshot"].get("dashboard")
        if isinstance(dashboard, dict):
            dashboard_id = dashboard.get("dashboard_id")
    if not dashboard_id:
        raise UsageError("Dashboard artifact is missing dashboard_id.")
    return str(dashboard_id)


def _profile_html_id(value: dict[str, Any]) -> str | None:
    html_id = value.get("html_id") or value.get("config_html_id")
    if not html_id and isinstance(value.get("snapshot"), dict):
        dashboard = value["snapshot"].get("dashboard")
        if isinstance(dashboard, dict):
            html_id = dashboard.get("html_id")
    return str(html_id) if html_id else None


def _read_current_profile(
    *,
    page: Any,
    args: Any,
    dashboard_id: str,
    domain: str,
    artifacts_dir: Path,
    edit_url: str,
) -> dict[str, Any]:
    return profile_edit_dashboard(
        page=page,
        dashboard_id=dashboard_id,
        html_id=extract_loaded_html_id(page.url),
        edit_url=edit_url,
        version_id="draft",
        artifacts_dir=artifacts_dir,
        debug_artifacts=bool(getattr(args, "debug_artifacts", False)),
        include_dataset_fields=True,
        domain=domain,
    )


def apply_change_plan_to_draft(
    *,
    page: Any,
    args: Any,
    plan: dict[str, Any],
    supplied_sha256: str,
    artifacts_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    operations = preflight_apply_plan(plan, supplied_sha256, expected_domain=args.domain)
    domain = require_resolved_domain(plan, args.domain)
    dashboard_id = _profile_dashboard_id(plan)
    html_id = _profile_html_id(plan)
    edit_url = build_edit_url(dashboard_id, html_id)
    open_edit_page(page, args, context=None, edit_url=edit_url)
    page.wait_for_timeout(getattr(args, "wait_ms", 3000))
    loaded_html_id = extract_loaded_html_id(page.url) or html_id

    current_raw = _read_current_profile(
        page=page,
        args=args,
        dashboard_id=dashboard_id,
        domain=domain,
        artifacts_dir=artifacts_dir,
        edit_url=edit_url,
    )
    current_profile = require_complete_profile(current_raw, "Current dashboard draft profile")
    if str(current_profile.get("profile_sha256") or "") != _plan_profile_sha256(plan):
        raise UsageError("Dashboard draft profile drifted after dry-run; no writes were attempted.")
    current_diagnostics = _core_api().validate_dashboard_change_plan(plan, current_profile=current_profile)
    if _diagnostic_errors(current_diagnostics):
        raise UsageError("Dashboard draft no longer satisfies the dry-run ChangePlan; no writes were attempted.")

    operation_results: list[dict[str, Any]] = []
    applied_mutations: list[AppliedDashboardMutation] = []
    active_operation: dict[str, Any] | None = None
    try:
        for active_operation in operations:
            mutation = apply_planned_operation(
                page=page,
                dashboard_id=dashboard_id,
                dashboard_name=str(plan.get("dashboard_name") or current_profile.get("dashboard_name") or ""),
                operation=active_operation,
            )
            applied_mutations.append(mutation)
            operation_results.append(
                {"operation_id": mutation.operation_id, "status": "applied"}
            )

        post_raw = _read_current_profile(
            page=page,
            args=args,
            dashboard_id=dashboard_id,
            domain=domain,
            artifacts_dir=artifacts_dir,
            edit_url=edit_url,
        )
        post_profile = require_complete_profile(post_raw, "Post-apply dashboard draft profile")
        receipt = _core_api().build_apply_receipt(
            plan,
            post_profile,
            operation_results=operation_results,
            recovery={
                "attempted": False,
                "status": "not_needed",
                "restored_profile_sha256": None,
                "operations": [],
                "errors": [],
            },
        )
        if not receipt.get("ok"):
            raise UsageError("Full draft readback does not match the ChangePlan target state.")
        _core_api().validate_apply_receipt(receipt, plan, post_profile=post_profile)
        return receipt, current_profile, post_profile
    except Exception as apply_exc:  # noqa: BLE001
        recovery_results: list[dict[str, Any]] = []
        recovery_errors: list[str] = []
        for mutation in reversed(applied_mutations):
            try:
                recovery_results.append(
                    restore_planned_operation(
                        page=page,
                        dashboard_id=dashboard_id,
                        dashboard_name=str(plan.get("dashboard_name") or current_profile.get("dashboard_name") or ""),
                        mutation=mutation,
                    )
                )
            except Exception as recovery_exc:  # noqa: BLE001
                recovery_errors.append(
                    f"{mutation.operation_id}: {type(recovery_exc).__name__}: {recovery_exc}"
                )
        restored_raw = _read_current_profile(
            page=page,
            args=args,
            dashboard_id=dashboard_id,
            domain=domain,
            artifacts_dir=artifacts_dir,
            edit_url=edit_url,
        )
        restored_profile = require_complete_profile(
            restored_raw, "Post-recovery dashboard draft profile"
        )
        profile_restored = (
            str(restored_profile.get("profile_sha256") or "") == _plan_profile_sha256(plan)
        )
        if not profile_restored:
            recovery_errors.append("full dashboard profile hash did not return to the ChangePlan baseline")
        applied_ids = {item["operation_id"] for item in operation_results}
        failed_id = str((active_operation or {}).get("operation_id") or "")
        failed_results = [
            {
                "operation_id": str(operation.get("operation_id") or ""),
                "status": "failed" if str(operation.get("operation_id") or "") in applied_ids or str(operation.get("operation_id") or "") == failed_id else "skipped",
                "message": (
                    "restored after transaction failure"
                    if str(operation.get("operation_id") or "") in applied_ids
                    else str(apply_exc)
                    if str(operation.get("operation_id") or "") == failed_id
                    else "not attempted after transaction failure"
                ),
            }
            for operation in operations
        ]
        recovery = {
            "attempted": bool(applied_mutations),
            "status": "restored" if profile_restored and not recovery_errors else "failed",
            "restored_profile_sha256": restored_profile.get("profile_sha256"),
            "operations": recovery_results,
            "errors": recovery_errors,
        }
        receipt = _core_api().build_apply_receipt(
            plan,
            restored_profile,
            operation_results=failed_results,
            recovery=recovery,
        )
        _core_api().validate_apply_receipt(receipt, plan, post_profile=restored_profile)
        return receipt, current_profile, restored_profile


def preflight_publish_receipt(
    receipt: dict[str, Any],
    change_plan: dict[str, Any],
    supplied_sha256: str,
    *,
    expected_domain: str,
    confirmed: bool,
) -> None:
    require_resolved_domain(receipt, expected_domain)
    actual_hash = artifact_sha256(receipt, "apply_receipt_sha256")
    if (
        not supplied_sha256
        or supplied_sha256 != actual_hash
        or str(receipt.get("apply_receipt_sha256") or "") != actual_hash
    ):
        raise UsageError("ApplyReceipt SHA-256 mismatch; publication is blocked.")
    if not confirmed:
        raise UsageError("Publishing requires --confirm-publish.")
    if not receipt.get("ok") or str(receipt.get("status") or "") != "applied":
        raise UsageError("ApplyReceipt is not successful; publication is blocked.")
    applied = [
        item
        for item in receipt.get("operations") or []
        if isinstance(item, dict) and item.get("status") == "applied"
    ]
    if not applied:
        raise UsageError("Publish requires at least one verified applied operation.")
    receipt_diagnostics = _core_api().validate_apply_receipt(receipt, change_plan)
    if _diagnostic_errors(receipt_diagnostics):
        raise UsageError("ApplyReceipt failed shared-core plan binding; publication is blocked.")


def publish_applied_draft(
    *,
    page: Any,
    args: Any,
    apply_receipt: dict[str, Any],
    change_plan: dict[str, Any],
    supplied_sha256: str,
    artifacts_dir: Path,
) -> dict[str, Any]:
    preflight_publish_receipt(
        apply_receipt,
        change_plan,
        supplied_sha256,
        expected_domain=args.domain,
        confirmed=bool(args.confirm_publish),
    )
    domain = require_resolved_domain(apply_receipt, args.domain)
    dashboard_id = _profile_dashboard_id(apply_receipt)
    html_id = _profile_html_id(apply_receipt)
    edit_url = build_edit_url(dashboard_id, html_id)
    open_edit_page(page, args, context=None, edit_url=edit_url)
    page.wait_for_timeout(getattr(args, "wait_ms", 3000))
    loaded_html_id = extract_loaded_html_id(page.url) or html_id

    current_raw = _read_current_profile(
        page=page,
        args=args,
        dashboard_id=dashboard_id,
        domain=domain,
        artifacts_dir=artifacts_dir,
        edit_url=edit_url,
    )
    current_profile = require_complete_profile(current_raw, "Pre-publish dashboard draft profile")
    expected_profile_hash = str(
        apply_receipt.get("post_profile_sha256")
        or apply_receipt.get("profile_sha256")
        or ""
    )
    if str(current_profile.get("profile_sha256") or "") != expected_profile_hash:
        raise UsageError("Dashboard draft drifted after apply; publication is blocked.")
    apply_diagnostics = _core_api().validate_apply_receipt(
        apply_receipt,
        change_plan,
        post_profile=current_profile,
    )
    if _diagnostic_errors(apply_diagnostics):
        raise UsageError("ApplyReceipt failed plan/readback validation; publication is blocked.")

    config = fetch_edit_config(page, dashboard_id)
    config_hash = publish_config_sha256(config, loaded_html_id)

    # Re-read the full draft immediately before publication. This cannot create
    # a server-side transaction, but it narrows the unprotected window and
    # prevents publishing a config/profile that changed during confirmation.
    immediate_raw = _read_current_profile(
        page=page,
        args=args,
        dashboard_id=dashboard_id,
        domain=domain,
        artifacts_dir=artifacts_dir,
        edit_url=edit_url,
    )
    immediate_profile = require_complete_profile(
        immediate_raw,
        "Immediate pre-publish dashboard draft profile",
    )
    if str(immediate_profile.get("profile_sha256") or "") != expected_profile_hash:
        raise UsageError("Dashboard draft changed immediately before publish; publication is blocked.")
    immediate_config = fetch_edit_config(page, dashboard_id)
    if publish_config_sha256(immediate_config, loaded_html_id) != config_hash:
        raise UsageError("Dashboard publish config changed during confirmation; publication is blocked.")

    publish_result = publish_dashboard(
        page,
        immediate_config,
        args.version_description,
        loaded_html_id,
    )
    platform_status = str(publish_result.get("publish_status") or "unknown")
    post_publish_raw = _read_current_profile(
        page=page,
        args=args,
        dashboard_id=dashboard_id,
        domain=domain,
        artifacts_dir=artifacts_dir,
        edit_url=edit_url,
    )
    post_publish_profile = require_complete_profile(
        post_publish_raw,
        "Post-publish dashboard draft profile",
    )
    receipt = _core_api().build_publish_receipt(
        apply_receipt,
        pre_publish_profile_sha256=str(immediate_profile.get("profile_sha256") or ""),
        confirmed=True,
        version_description=args.version_description,
        publish_status=(
            "publish_requested_unverified" if platform_status == "success" else "failed"
        ),
        post_publish_draft_profile_sha256=str(
            post_publish_profile.get("profile_sha256") or ""
        ),
        readback_performed=True,
        published_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    # A failed API acknowledgement or mismatched post-publish draft readback is
    # preserved as an unsuccessful receipt; it must never be promoted to ok.
    _core_api().validate_publish_receipt(receipt, apply_receipt)
    return receipt
