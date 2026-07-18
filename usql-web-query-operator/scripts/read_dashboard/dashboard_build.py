"""Governed P4C dashboard-build planning, saga, and publish helpers."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from _shared.errors import UsageError

from .dashboard_change import (
    canonical_sha256,
    publish_config_sha256,
    read_json_artifact,
    require_complete_profile,
)
from .edit_profile import (
    build_edit_url,
    extract_loaded_html_id,
    open_edit_page,
    profile_edit_dashboard,
)
from .filter_edit import fetch_edit_config, publish_dashboard
from .write_capabilities import capability_by_operation, load_capability_registry


DOMAIN_SKILL_NAMES = {
    "market_consultant": "sql-query-writer-for-dashboard",
    "qingcheng": "qingcheng-dashboard-sql",
}


def _core_api() -> Any:
    skills_root = Path(__file__).resolve().parents[3]
    core_root = skills_root / "_shared" / "text2sql_core"
    if str(core_root) not in sys.path:
        sys.path.insert(0, str(core_root))
    try:
        from text2sql_core import dashboard_build as core
    except ImportError as exc:  # pragma: no cover - validated by stack tests
        raise UsageError(f"Shared Text2SQL dashboard-build core is unavailable: {exc}") from exc
    return core


def _diagnostic_errors(diagnostics: Any) -> list[dict[str, Any]]:
    if not isinstance(diagnostics, list):
        return []
    return [item for item in diagnostics if isinstance(item, dict) and item.get("severity") == "error"]


def normalize_build_spec(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return _core_api().normalize_dashboard_build_spec(value)
    except (KeyError, TypeError, ValueError) as exc:
        raise UsageError(f"Invalid DashboardBuildSpec: {exc}") from exc


def _read_json_path(path_value: str, label: str) -> dict[str, Any]:
    path = Path(path_value).expanduser().resolve()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read {label} from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise UsageError(f"{label} must be a JSON object: {path}")
    return value


def bind_build_upstream_artifacts(
    spec: Mapping[str, Any],
    dataset_resolutions: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Bind real QueryPlan/DatasetSpec and Data Center artifacts to resolutions.

    This is pure local verification.  It never upgrades a resolution to ready
    based only on user-provided status strings.
    """

    normalized = normalize_build_spec(spec)
    if isinstance(dataset_resolutions, Mapping):
        raw_items = dataset_resolutions.get("datasets", dataset_resolutions.get("resolutions", []))
    else:
        raw_items = dataset_resolutions or []
    by_ref = {
        str(item.get("dataset_ref") or ""): copy.deepcopy(dict(item))
        for item in raw_items
        if isinstance(item, Mapping) and item.get("dataset_ref")
    }
    skills_root = Path(__file__).resolve().parents[3]
    output: list[dict[str, Any]] = []

    for dataset in normalized["datasets"]:
        dataset_ref = str(dataset["dataset_ref"])
        resolution = by_ref.get(dataset_ref, {"dataset_ref": dataset_ref})
        errors: list[str] = []
        query_plan: dict[str, Any] = {}
        dataset_spec: dict[str, Any] = {}
        try:
            query_plan = _read_json_path(dataset["query_plan_path"], f"{dataset_ref} QueryPlan")
            query_hash = str(_core_api().canonical_sha256(query_plan))
            resolution["query_plan_sha256"] = query_hash
            resolution["query_plan_status"] = query_plan.get("status")
            if query_plan.get("schema_version") != "2.0.0":
                errors.append("QueryPlan schema_version must be 2.0.0")
            if not query_plan.get("plan_id"):
                errors.append("QueryPlan plan_id is required")
            if query_hash != dataset["query_plan_sha256"]:
                errors.append("QueryPlan file SHA-256 does not match DashboardBuildSpec")
            if query_plan.get("domain") != normalized["domain"]:
                errors.append("QueryPlan domain mismatch")
            if query_plan.get("status") != "executable" or query_plan.get("unresolved_slots"):
                errors.append("QueryPlan is not executable or has unresolved slots")
            if any(
                isinstance(item, Mapping) and item.get("severity") == "error"
                for item in query_plan.get("diagnostics", [])
            ):
                errors.append("QueryPlan contains error diagnostics")
            if not isinstance(query_plan.get("execution_policy"), Mapping):
                errors.append("QueryPlan execution_policy is required")
            sql_sha256 = str(query_plan.get("sql_sha256") or "")
            if len(sql_sha256) != 64 or any(char not in "0123456789abcdef" for char in sql_sha256):
                errors.append("QueryPlan sql_sha256 must be a canonical lowercase SHA-256")
        except UsageError as exc:
            errors.append(str(exc))

        try:
            dataset_spec = _read_json_path(
                dataset["dataset_spec_path"], f"{dataset_ref} DashboardDatasetSpec"
            )
            dataset_spec_hash = str(
                _core_api().artifact_sha256(dataset_spec, "dataset_spec_sha256")
            )
            resolution["dataset_spec_sha256"] = dataset_spec_hash
            resolution["dataset_spec_status"] = dataset_spec.get("status")
            if dataset_spec.get("schema_version") != "2.0.0":
                errors.append("DashboardDatasetSpec schema_version must be 2.0.0")
            if dataset_spec.get("artifact_type") != "dashboard_dataset_spec":
                errors.append("DashboardDatasetSpec artifact_type mismatch")
            if dataset_spec.get("mode") != "read_only_design":
                errors.append("DashboardDatasetSpec must be read_only_design")
            if dataset_spec_hash != dataset["dataset_spec_sha256"]:
                errors.append("DashboardDatasetSpec file SHA-256 does not match DashboardBuildSpec")
            if dataset_spec.get("dataset_spec_sha256") != dataset_spec_hash:
                errors.append("DashboardDatasetSpec self hash is stale")
            if dataset_spec.get("domain") != normalized["domain"]:
                errors.append("DashboardDatasetSpec domain mismatch")
            if dataset_spec.get("status") != "ready":
                errors.append("DashboardDatasetSpec is not ready")
            write_boundary = dataset_spec.get("write_boundary")
            if not isinstance(write_boundary, Mapping) or any(
                write_boundary.get(key) is not False
                for key in ("may_modify_dashboard", "may_publish_dashboard")
            ):
                errors.append("DashboardDatasetSpec write boundary is invalid")
            if query_plan and dataset_spec.get("query_plan_sha256") != _core_api().canonical_sha256(query_plan):
                errors.append("DashboardDatasetSpec does not bind the supplied QueryPlan")
        except UsageError as exc:
            errors.append(str(exc))

        evidence_records: list[Mapping[str, Any]] = []
        for collection in ("fields", "scope_contracts", "default_filters"):
            evidence_records.extend(
                item
                for item in dataset_spec.get(collection, [])
                if isinstance(item, Mapping) and (item.get("contract_id") or item.get("id"))
            )
        contracts_confirmed = bool(evidence_records) and all(
            item.get("contract_status") == "confirmed"
            and item.get("source_domain") == normalized["domain"]
            for item in evidence_records
        )
        source_hashes_valid = contracts_confirmed
        skill_root = skills_root / DOMAIN_SKILL_NAMES[normalized["domain"]]
        for item in evidence_records:
            source_path = str(item.get("source_path") or "")
            source_sha = str(item.get("source_sha256") or "")
            candidate = (skill_root / source_path).resolve()
            try:
                candidate.relative_to(skill_root.resolve())
            except ValueError:
                source_hashes_valid = False
                continue
            if not candidate.is_file() or hashlib.sha256(candidate.read_bytes()).hexdigest() != source_sha:
                source_hashes_valid = False
        resolution["contracts_confirmed"] = contracts_confirmed
        resolution["source_hashes_valid"] = source_hashes_valid
        if not contracts_confirmed:
            errors.append("DashboardDatasetSpec contract evidence is not fully confirmed")
        if not source_hashes_valid:
            errors.append("DashboardDatasetSpec source evidence hashes are stale")

        expected_fields = {
            str(item.get("name") or "")
            for item in dataset_spec.get("fields", [])
            if isinstance(item, Mapping) and item.get("name")
        }
        mapped_fields = {
            str(item.get("field_ref") or item.get("logical_field_ref") or "")
            for item in resolution.get("field_bindings", [])
            if isinstance(item, Mapping)
        }
        resolution["dataset_fields_match"] = bool(expected_fields) and expected_fields == mapped_fields
        if not resolution["dataset_fields_match"]:
            errors.append("DatasetSpec outputs and platform field bindings are not one-to-one")

        if dataset["mode"] == "create":
            plan_path = dataset.get("data_center_creation_plan_path")
            receipt_path = dataset.get("data_center_creation_receipt_path")
            if plan_path:
                try:
                    creation_plan = _read_json_path(plan_path, f"{dataset_ref} Data Center creation plan")
                    plan_sha = str(_core_api().artifact_sha256(creation_plan, "plan_sha256"))
                    resolution["data_center_creation_plan_sha256"] = plan_sha
                    if creation_plan.get("plan_sha256") != plan_sha or creation_plan.get("status") != "ready":
                        errors.append("Data Center creation plan is stale or not ready")
                except UsageError as exc:
                    errors.append(str(exc))
            if receipt_path:
                try:
                    creation_receipt = _read_json_path(
                        receipt_path, f"{dataset_ref} Data Center creation receipt"
                    )
                    receipt_sha = str(_core_api().canonical_sha256(creation_receipt))
                    resolution["data_center_creation_receipt_sha256"] = receipt_sha
                    resolution["data_center_receipt_status"] = creation_receipt.get("status")
                    workflow = creation_receipt.get("workflow") if isinstance(creation_receipt.get("workflow"), Mapping) else {}
                    latest_run = workflow.get("latest_run") if isinstance(workflow.get("latest_run"), Mapping) else {}
                    resolution["first_sync_status"] = latest_run.get("status")
                    if not (
                        creation_receipt.get("ok") is True
                        and creation_receipt.get("fully_verified") is True
                        and latest_run.get("status") == "SUCCESS"
                    ):
                        errors.append("Data Center creation receipt has no fully verified new SUCCESS")
                except UsageError as exc:
                    errors.append(str(exc))
        resolution["domain"] = normalized["domain"]
        resolution["upstream_errors"] = sorted(set(errors))
        output.append(resolution)
    return {"artifact_type": "DashboardDatasetResolutions", "datasets": output}


def plan_dashboard_build(
    spec: Mapping[str, Any],
    dataset_resolutions: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None,
    *,
    folder_snapshot_sha256: str | None = None,
    dashboard_name_available: bool | None = None,
) -> dict[str, Any]:
    try:
        return _core_api().build_dashboard_build_plan(
            spec,
            dataset_resolutions,
            folder_snapshot_sha256=folder_snapshot_sha256,
            dashboard_name_available=dashboard_name_available,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise UsageError(f"Unable to build DashboardBuildPlan: {exc}") from exc


def _require_exact_hash(value: Mapping[str, Any], field: str, supplied: str, label: str) -> str:
    actual = str(_core_api().artifact_sha256(value, field))
    if not supplied or supplied != actual or str(value.get(field) or "") != actual:
        raise UsageError(f"{label} SHA-256 mismatch; regenerate and review the artifact.")
    return actual


def preflight_apply_build_plan(
    plan: Mapping[str, Any],
    supplied_sha256: str,
    *,
    expected_domain: str,
    confirmed: bool,
    registry_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Reject stale or unsupported builds before Playwright is imported."""

    _require_exact_hash(plan, "dashboard_build_plan_sha256", supplied_sha256, "DashboardBuildPlan")
    errors = _diagnostic_errors(_core_api().validate_dashboard_build_plan(plan))
    if errors:
        raise UsageError("DashboardBuildPlan failed shared-core validation; no browser was opened.")
    if str(plan.get("domain") or "") != expected_domain:
        raise UsageError("DashboardBuildPlan domain mismatch.")
    if str(plan.get("status") or "") != "ready":
        raise UsageError(
            f"DashboardBuildPlan status must be ready, got {plan.get('status')}; no browser was opened."
        )
    if not confirmed:
        raise UsageError("Dashboard build Apply requires --confirm-production-write.")
    registry = load_capability_registry(registry_path) if registry_path else load_capability_registry()
    capabilities: list[dict[str, Any]] = []
    for operation in plan.get("required_capabilities") or []:
        capability = capability_by_operation(registry, str(operation))
        if not (
            capability.get("maturity") == "verified"
            and capability.get("write_policy") == "allowlisted"
            and capability.get("readback_coverage") == "full"
            and capability.get("transaction_class") == "creation_saga"
            and capability.get("recovery_policy") == "creation_saga_no_auto_delete"
            and capability.get("adapter")
        ):
            raise UsageError(
                f"Dashboard build capability {operation} is not production verified/allowlisted "
                "for creation_saga_no_auto_delete; no browser was opened."
            )
        capabilities.append(capability)
    return capabilities


def preflight_publish_build(
    plan: Mapping[str, Any],
    plan_sha256: str,
    build_receipt: Mapping[str, Any],
    receipt_sha256: str,
    *,
    expected_domain: str,
    confirmed: bool,
    version_description: str,
) -> None:
    _require_exact_hash(plan, "dashboard_build_plan_sha256", plan_sha256, "DashboardBuildPlan")
    _require_exact_hash(
        build_receipt,
        "dashboard_build_receipt_sha256",
        receipt_sha256,
        "DashboardBuildReceipt",
    )
    if str(plan.get("domain") or "") != expected_domain or str(build_receipt.get("domain") or "") != expected_domain:
        raise UsageError("Dashboard build publish domain mismatch.")
    errors = _diagnostic_errors(
        _core_api().validate_dashboard_build_receipt(build_receipt, plan)
    )
    if errors:
        raise UsageError("DashboardBuildReceipt failed shared-core validation.")
    if not build_receipt.get("ok") or build_receipt.get("status") != "applied":
        raise UsageError("Publish requires a successful DashboardBuildReceipt.")
    if not confirmed:
        raise UsageError("Publishing requires --confirm-publish.")
    if not str(version_description or "").strip():
        raise UsageError("Publishing requires a non-empty --version-description.")
    capability = capability_by_operation(load_capability_registry(), "publish_dashboard")
    if not (
        capability.get("write_policy") == "separate_confirmation"
        and capability.get("transaction_class") == "separate_publish"
        and capability.get("recovery_policy") == "separate_publish"
    ):
        raise UsageError("Dashboard publish capability is not registered as separate_publish.")


class DashboardBuildAdapter(Protocol):
    """Verified platform adapter contract used by the creation saga.

    Implementations must make ``ensure_*`` idempotent: exact existing resources
    return ``status=reused``; same-name different-state resources must raise.
    """

    def verify_target_folder(self, plan: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def verify_dataset_bindings(
        self, plan: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]: ...

    def ensure_dashboard_shell(
        self, plan: Mapping[str, Any], resume_resources: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    def ensure_calculated_column(
        self,
        plan: Mapping[str, Any],
        column: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...

    def ensure_component(
        self,
        plan: Mapping[str, Any],
        component: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...

    def ensure_global_filter(
        self,
        plan: Mapping[str, Any],
        global_filter: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...

    def assemble_dashboard(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    def read_complete_profile(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    def verify_profile_target(
        self,
        plan: Mapping[str, Any],
        profile: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...

    def check_component_values(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]: ...

    def check_global_filters(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]: ...


def _resource_result(
    operation_id: str,
    operation_type: str,
    result: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    status = str(result.get("status") or "")
    if status not in {"applied", "reused"}:
        raise UsageError(f"{operation_id} adapter returned unsupported status {status or '<missing>'}.")
    resource = result.get("resource") if isinstance(result.get("resource"), Mapping) else None
    operation = {
        "operation_id": operation_id,
        "operation_type": operation_type,
        "status": status,
        "resource_id": str((resource or {}).get("resource_id") or "") or None,
    }
    return operation, copy.deepcopy(dict(resource)) if resource else None, status == "reused"


def execute_dashboard_build_saga(
    plan: Mapping[str, Any],
    adapter: DashboardBuildAdapter,
    *,
    resume_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute the fixed P4C order without any automatic delete compensation."""

    errors = _diagnostic_errors(_core_api().validate_dashboard_build_plan(plan))
    if errors or plan.get("status") != "ready":
        raise UsageError("Only a validated ready DashboardBuildPlan may enter the creation saga.")
    if resume_receipt:
        receipt_errors = _diagnostic_errors(
            _core_api().validate_dashboard_build_receipt(resume_receipt, plan)
        )
        if receipt_errors:
            raise UsageError("Resume receipt is stale or does not bind the build plan.")

    created: list[dict[str, Any]] = []
    reused: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []
    resource_map: dict[str, Any] = {}
    if resume_receipt:
        for resource in [
            *(resume_receipt.get("created_resources") or []),
            *(resume_receipt.get("reused_resources") or []),
        ]:
            if isinstance(resource, Mapping) and resource.get("logical_id"):
                resource_map[str(resource["logical_id"])] = copy.deepcopy(dict(resource))

    dashboard_id: str | None = None
    html_id: str | None = None
    post_profile_sha256: str | None = None
    value_checks: Sequence[Mapping[str, Any]] = ()
    filter_checks: Sequence[Mapping[str, Any]] = ()

    def record(
        operation_id: str,
        operation_type: str,
        result: Mapping[str, Any],
        logical_id: str,
    ) -> None:
        operation, resource, was_reused = _resource_result(
            operation_id, operation_type, result
        )
        operations.append(operation)
        if resource:
            resource.setdefault("logical_id", logical_id)
            resource_map[logical_id] = resource
            (reused if was_reused else created).append(resource)

    try:
        folder_readback = adapter.verify_target_folder(plan)
        if not (
            folder_readback.get("ok") is True
            and folder_readback.get("dashboard_name_available") is True
            and folder_readback.get("folder_snapshot_sha256")
            == plan.get("folder_snapshot_sha256")
        ):
            raise UsageError("Target folder identity or dashboard-name uniqueness drifted before creation.")
        operations.append(
            {
                "operation_id": "step_00_folder_readback",
                "operation_type": "folder_and_name_readback",
                "status": "applied",
                "resource_id": str(plan.get("target_folder", {}).get("folder_id") or "") or None,
            }
        )

        dataset_readbacks = {
            str(item.get("dataset_ref") or ""): item
            for item in adapter.verify_dataset_bindings(plan)
            if isinstance(item, Mapping) and item.get("dataset_ref")
        }
        for dataset in plan.get("datasets") or []:
            current = dataset_readbacks.get(str(dataset.get("dataset_ref") or ""))
            if not current or current.get("ok") is not True:
                raise UsageError(f"Dataset {dataset.get('dataset_ref')} readback is missing or failed.")
            for key in (
                "application_model_id",
                "subject_id",
                "model_type",
                "dataset_schema_sha256",
                "field_binding_sha256",
            ):
                if current.get(key) != dataset.get(key):
                    raise UsageError(
                        f"Dataset {dataset.get('dataset_ref')} {key} drifted before creation."
                    )
        operations.append(
            {
                "operation_id": "step_00_dataset_readback",
                "operation_type": "dataset_schema_and_binding_readback",
                "status": "applied",
                "resource_id": None,
            }
        )

        shell_result = adapter.ensure_dashboard_shell(plan, resource_map)
        record("step_01_dashboard_shell", "create_dashboard", shell_result, "dashboard")
        dashboard_resource = resource_map.get("dashboard", {})
        dashboard_id = str(dashboard_resource.get("dashboard_id") or dashboard_resource.get("resource_id") or "") or None
        html_id = str(dashboard_resource.get("html_id") or "") or None

        for index, column in enumerate(plan.get("calculated_columns") or [], start=1):
            logical_id = str(column["logical_id"])
            result = adapter.ensure_calculated_column(plan, column, resource_map)
            record(f"step_02_formula_{index:03d}", "create_formula", result, f"formula:{logical_id}")

        for index, component in enumerate(plan.get("components") or [], start=1):
            logical_id = str(component["component_id"])
            operation_type = {
                "metric_group": "create_metric_group_component",
                "pivot": "create_pivot_component",
                "bar": "create_bar_component",
                "pie": "create_pie_component",
            }[str(component["type"])]
            result = adapter.ensure_component(plan, component, resource_map)
            record(f"step_03_component_{index:03d}", operation_type, result, f"component:{logical_id}")

        for index, global_filter in enumerate(plan.get("global_filters") or [], start=1):
            logical_id = str(global_filter["filter_id"])
            result = adapter.ensure_global_filter(plan, global_filter, resource_map)
            record(f"step_04_filter_{index:03d}", "create_public_filter", result, f"filter:{logical_id}")

        assemble_result = adapter.assemble_dashboard(plan, resource_map)
        record("step_05_assemble", "assemble_new_dashboard", assemble_result, "dashboard_html")

        profile = require_complete_profile(
            dict(adapter.read_complete_profile(plan, resource_map)),
            "Post-build DashboardProfile",
        )
        target_verification = adapter.verify_profile_target(plan, profile, resource_map)
        if target_verification.get("ok") is not True:
            mismatches = target_verification.get("mismatches") or ["unknown target mismatch"]
            raise UsageError(
                "Post-build DashboardProfile does not match the planned target: "
                + "; ".join(str(item) for item in mismatches)
            )
        post_profile_sha256 = str(profile.get("profile_sha256") or "") or None
        operations.append(
            {
                "operation_id": "step_06_profile_readback",
                "operation_type": "profile_readback",
                "status": "applied",
                "resource_id": dashboard_id,
            }
        )
        value_checks = adapter.check_component_values(plan, resource_map)
        checks_by_component = {
            str(item.get("component_id") or ""): item
            for item in value_checks
            if isinstance(item, Mapping)
        }
        expected_shapes = {
            "metric_group": "metric_group",
            "pivot": "pivot",
            "bar": "chart",
            "pie": "chart",
        }
        if len(checks_by_component) != len(plan.get("components") or []) or not all(
            checks_by_component.get(str(component["component_id"]), {}).get("ok") is True
            and checks_by_component[str(component["component_id"])].get("response_shape")
            == expected_shapes[str(component["type"])]
            for component in plan.get("components") or []
        ):
            raise UsageError("Component value validation did not pass for every planned component.")
        operations.append(
            {
                "operation_id": "step_07_component_values",
                "operation_type": "component_value_validation",
                "status": "applied",
                "resource_id": dashboard_id,
            }
        )
        filter_checks = adapter.check_global_filters(plan, resource_map)
        checks_by_filter = {
            str(item.get("filter_id") or ""): item
            for item in filter_checks
            if isinstance(item, Mapping)
        }
        if len(checks_by_filter) != len(plan.get("global_filters") or []) or not all(
            checks_by_filter.get(str(global_filter["filter_id"]), {}).get("ok") is True
            and checks_by_filter[str(global_filter["filter_id"])].get(
                "public_filter_list_applied"
            )
            is True
            and checks_by_filter[str(global_filter["filter_id"])].get(
                "assertions_passed"
            )
            is True
            for global_filter in plan.get("global_filters") or []
        ):
            raise UsageError("Global-filter value validation did not pass for every planned filter.")
        operations.append(
            {
                "operation_id": "step_08_global_filter_values",
                "operation_type": "global_filter_value_validation",
                "status": "applied",
                "resource_id": dashboard_id,
            }
        )
    except Exception as exc:  # noqa: BLE001
        operations.append(
            {
                "operation_id": f"failed_after_{len(operations):03d}",
                "operation_type": "creation_saga",
                "status": "failed",
                "message": str(exc),
            }
        )
        return _core_api().build_dashboard_build_receipt(
            plan,
            operation_results=operations,
            created_resources=created,
            reused_resources=reused,
            orphaned_resources=created,
            dashboard_id=dashboard_id,
            html_id=html_id,
            post_profile_sha256=post_profile_sha256,
            value_checks=value_checks,
            global_filter_checks=filter_checks,
            failure=str(exc),
        )

    return _core_api().build_dashboard_build_receipt(
        plan,
        operation_results=operations,
        created_resources=created,
        reused_resources=reused,
        orphaned_resources=(),
        dashboard_id=dashboard_id,
        html_id=html_id,
        post_profile_sha256=post_profile_sha256,
        value_checks=value_checks,
        global_filter_checks=filter_checks,
    )


def publish_dashboard_build(
    *,
    page: Any,
    args: Any,
    plan: Mapping[str, Any],
    build_receipt: Mapping[str, Any],
    artifacts_dir: Path,
) -> dict[str, Any]:
    preflight_publish_build(
        plan,
        args.build_plan_sha256,
        build_receipt,
        args.build_receipt_sha256,
        expected_domain=args.domain,
        confirmed=bool(args.confirm_publish),
        version_description=args.version_description,
    )
    dashboard_id = str(build_receipt.get("dashboard_id") or "")
    html_id = str(build_receipt.get("html_id") or "") or None
    edit_url = build_edit_url(dashboard_id, html_id)
    open_edit_page(page, args, context=None, edit_url=edit_url)
    page.wait_for_timeout(getattr(args, "wait_ms", 3000))
    loaded_html_id = extract_loaded_html_id(page.url) or html_id

    def read_profile(label: str) -> dict[str, Any]:
        raw = profile_edit_dashboard(
            page=page,
            dashboard_id=dashboard_id,
            html_id=loaded_html_id,
            edit_url=edit_url,
            version_id="draft",
            artifacts_dir=artifacts_dir,
            debug_artifacts=bool(getattr(args, "debug_artifacts", False)),
            include_dataset_fields=True,
            domain=args.domain,
        )
        return require_complete_profile(raw, label)

    expected_profile_sha256 = str(build_receipt.get("post_profile_sha256") or "")
    first_profile = read_profile("Pre-publish dashboard build profile")
    if first_profile.get("profile_sha256") != expected_profile_sha256:
        raise UsageError("Dashboard build draft drifted after Apply; publication is blocked.")
    first_config = fetch_edit_config(page, dashboard_id)
    payload_sha256 = publish_config_sha256(first_config, loaded_html_id)
    immediate_profile = read_profile("Immediate pre-publish dashboard build profile")
    immediate_config = fetch_edit_config(page, dashboard_id)
    if immediate_profile.get("profile_sha256") != expected_profile_sha256:
        raise UsageError("Dashboard build draft changed immediately before publish.")
    if publish_config_sha256(immediate_config, loaded_html_id) != payload_sha256:
        raise UsageError("Dashboard build publish payload changed during confirmation.")
    publish_result = publish_dashboard(
        page,
        immediate_config,
        args.version_description,
        loaded_html_id,
    )
    if str(publish_result.get("publish_status") or "") != "success":
        raise UsageError("Platform did not acknowledge the dashboard build publish request.")
    post_profile = read_profile("Post-publish dashboard build draft profile")
    return _core_api().build_dashboard_build_publish_receipt(
        plan,
        build_receipt,
        version_description=args.version_description,
        publish_payload_sha256=payload_sha256,
        pre_publish_profile_sha256=str(immediate_profile["profile_sha256"]),
        post_publish_draft_profile_sha256=str(post_profile["profile_sha256"]),
        platform_response_status="success",
    )


__all__ = [
    "DashboardBuildAdapter",
    "bind_build_upstream_artifacts",
    "execute_dashboard_build_saga",
    "normalize_build_spec",
    "plan_dashboard_build",
    "preflight_apply_build_plan",
    "preflight_publish_build",
    "publish_dashboard_build",
    "read_json_artifact",
]
