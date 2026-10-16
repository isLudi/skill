"""Sandbox-only pivot field rebinding with full pre-write backups."""

from __future__ import annotations

import copy
import json
import re
import time
from pathlib import Path
from typing import Any, Callable

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import safe_filename, write_json
from ..constants import UNIT_VALUE_API
from ..dashboard_change import require_complete_profile
from ..dashboard_write_adapters import (
    _formula_item, _write_dashboard_schema, _write_formula, _write_unit_detail, canonical_sha256,
)
from ..edit_profile import (
    build_edit_url,
    fetch_edit_dashboard_config,
    fetch_edit_unit_detail,
    fetch_dataset_fields,
    open_edit_page,
    profile_edit_dashboard,
)
from ..pivot_rebind import (
    FIELD_LIST_GROUPS,
    assert_filtered_value_response,
    normalize_filtered_value_checks,
    project_unit_field_state,
    rebuild_pivot_unit_fields,
)
from ..profile import (
    default_unit_value_payload,
    extract_component_units,
    fetch_dashboard_config,
    parse_dashboard_html,
    post_json,
)
from ..write_capabilities import DEFAULT_REGISTRY, capability_by_operation, load_capability_registry
SANDBOX_MARKERS = ("p4a", "sandbox", "test", "沙箱", "测试")
COPY_UNIT_API = "https://udata.baijia.com/uanalysis-intelligence/config/copy/unit"
PIVOT_COMPONENT_STYLE_KEYS = (
    "themeType",
    "pivotTableConfig",
    "componentOtherConfig",
    "frameStyle",
    "headerStyle",
    "bodyStyle",
    "cornerHeaderStyle",
    "rowHeaderStyle",
    "animationAppear",
)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read pivot rebind manifest: {exc}") from exc
    if not isinstance(value, dict) or value.get("artifact_type") != "DashboardPivotFieldRebindManifest":
        raise UsageError("Pivot rebind manifest has an invalid artifact_type.")
    if value.get("schema_version") != "1.0.0":
        raise UsageError("Pivot rebind manifest schema_version must be 1.0.0.")
    return value


def _require_sandbox(dashboard_id: str, expected_name: str) -> None:
    if not dashboard_id.startswith("dashboard_") or not dashboard_id.removeprefix("dashboard_").isdigit():
        raise UsageError("Sandbox dashboard ID must use dashboard_<digits>.")
    lowered_name = expected_name.casefold()
    if not any(marker in lowered_name for marker in SANDBOX_MARKERS):
        raise UsageError("Sandbox dashboard name must contain P4A, sandbox, test, 沙箱, or 测试.")


def _component_unit_ids(config: dict[str, Any]) -> list[str]:
    dashboard_html = parse_dashboard_html(config)
    unit_ids: list[str] = []
    for component in extract_component_units(dashboard_html):
        unit_id = str(component.get("unit_id") or "")
        if unit_id and unit_id not in unit_ids:
            unit_ids.append(unit_id)
    return unit_ids


def _backup_dashboard(
    *,
    page: Any,
    dashboard_id: str,
    expected_name: str | None,
    domain: str,
    artifacts_dir: Path,
    label: str,
) -> dict[str, Any]:
    edit_config = fetch_edit_dashboard_config(page, dashboard_id, "draft")
    live_name = str(edit_config.get("dashboardName") or "")
    if expected_name and live_name != expected_name:
        raise UsageError(f"Dashboard backup name mismatch for {dashboard_id}: expected {expected_name}, got {live_name}.")
    unit_details: dict[str, Any] = {}
    unit_errors: list[dict[str, str]] = []
    for unit_id in _component_unit_ids(edit_config):
        try:
            unit_details[unit_id] = fetch_edit_unit_detail(page, unit_id, dashboard_id, "draft")
        except Exception as exc:  # noqa: BLE001
            unit_errors.append({"unit_id": unit_id, "message": str(exc)})
    published_config: dict[str, Any] | None = None
    published_error: str | None = None
    try:
        published_config = fetch_dashboard_config(page, dashboard_id)
    except Exception as exc:  # noqa: BLE001
        published_error = str(exc)
    backup = {
        "schema_version": "1.0.0",
        "artifact_type": "DashboardFullConfigBackup",
        "domain": domain,
        "dashboard_id": dashboard_id,
        "dashboard_name": live_name,
        "label": label,
        "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "edit_config": edit_config,
        "unit_details": unit_details,
        "unit_errors": unit_errors,
        "published_config": published_config,
        "published_error": published_error,
        "backup_sha256": "",
    }
    backup["backup_sha256"] = canonical_sha256({key: value for key, value in backup.items() if key != "backup_sha256"})
    output_path = (
        artifacts_dir
        / "dashboard-config-backups"
        / f"{safe_filename(label)}_{safe_filename(dashboard_id)}.json"
    )
    write_json(backup, output_path)
    return {
        "label": label,
        "dashboard_id": dashboard_id,
        "dashboard_name": live_name,
        "backup_sha256": backup["backup_sha256"],
        "output_path": str(output_path),
        "unit_count": len(unit_details),
        "unit_error_count": len(unit_errors),
        "published_config_captured": published_config is not None,
        "published_error": published_error,
    }


def _manifest_backups(
    manifest: dict[str, Any],
    dashboard_id: str,
    dashboard_name: str,
    *,
    target_label: str,
) -> list[dict[str, str]]:
    backups = [
        item
        for item in manifest.get("backup_dashboards") or []
        if isinstance(item, dict)
    ]
    backups.append(
        {
            "label": target_label,
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_name,
        }
    )
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(backups):
        dashboard_id = str(item.get("dashboard_id") or "").strip()
        dashboard_name = str(item.get("dashboard_name") or "").strip()
        label = str(item.get("label") or f"backup_{index + 1}").strip()
        if not dashboard_id:
            raise UsageError("Every backup dashboard entry requires dashboard_id.")
        key = (label, dashboard_id)
        if key in seen:
            continue
        seen.add(key)
        result.append({"label": label, "dashboard_id": dashboard_id, "dashboard_name": dashboard_name})
    return result


def _operation_list(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    operations = manifest.get("operations")
    if not isinstance(operations, list) or not operations:
        raise UsageError("Pivot rebind manifest requires a non-empty operations list.")
    for operation in operations:
        if not isinstance(operation, dict):
            raise UsageError("Pivot rebind operations must be JSON objects.")
        for key in ("operation_id", "target_unit_id", "source_unit_id", "dimension_field_ids"):
            if operation.get(key) in (None, "", []):
                raise UsageError(f"Pivot rebind operation requires {key}.")
    return operations


def _source_dimension_field_ids(source_detail: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for field in source_detail.get("unitDimensionList") or []:
        if not isinstance(field, dict):
            continue
        field_id = str(field.get("fieldId") or field.get("paramId") or "").strip()
        if field_id:
            result.append(field_id)
    return result


def _restore_units(
    *,
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    completed: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    restored: list[dict[str, Any]] = []
    for item in reversed(completed):
        current = fetch_edit_unit_detail(page, item["target_unit_id"], dashboard_id, "draft")
        current_state = project_unit_field_state(current)
        allowed_states = item.get("allowed_current_states") or [item["before_state"]]
        if current_state not in allowed_states:
            raise UsageError(
                f"Recovery stopped because {item['operation_id']} changed outside the attempted states."
            )
        if current_state == item["before_state"]:
            restored.append(
                {
                    "operation_id": item["operation_id"],
                    "target_unit_id": item["target_unit_id"],
                    "status": "already_restored",
                    "observations": [],
                }
            )
            continue
        observations: list[dict[str, Any]] = []
        _write_unit_detail(page, dashboard_id, item["before_raw"], observations)
        readback = fetch_edit_unit_detail(page, item["target_unit_id"], dashboard_id, "draft")
        restored_state = project_unit_field_state(readback)
        ok = restored_state == item["before_state"]
        restored.append(
            {
                "operation_id": item["operation_id"],
                "target_unit_id": item["target_unit_id"],
                "status": "restored" if ok else "restore_mismatch",
                "observations": observations,
            }
        )
        if not ok:
            raise UsageError(f"Recovery failed for {item['operation_id']} on {dashboard_name}.")
    return restored


def _read_stable_unit_projection(
    *, page: Any, dashboard_id: str, unit_id: str, expected_state: dict[str, Any], label: str,
) -> dict[str, Any]:
    latest: dict[str, Any] | None = None
    for _ in range(2):
        latest = fetch_edit_unit_detail(page, unit_id, dashboard_id, "draft")
        if project_unit_field_state(latest) != expected_state:
            raise UsageError(f"{label} unit projection drifted during the pre-write double-read.")
    assert latest is not None
    return latest


def _restore_schema_if_expected(
    *, page: Any, dashboard_id: str, dashboard_name: str, original_schema: dict[str, Any],
    attempted_schema: dict[str, Any], observations: list[dict[str, Any]],
) -> str:
    original_sha256 = canonical_sha256(original_schema)
    attempted_sha256 = canonical_sha256(attempted_schema)
    current_config = fetch_edit_dashboard_config(page, dashboard_id, "draft")
    current_schema = parse_dashboard_html(current_config)
    current_sha256 = canonical_sha256(current_schema)
    if current_sha256 == original_sha256:
        return "already_restored"
    if current_sha256 != attempted_sha256:
        raise UsageError("Dashboard schema drifted after the attempted write; recovery did not overwrite it.")
    _write_dashboard_schema(
        page, dashboard_id, dashboard_name, original_schema, observations,
        expected_schema_sha256=attempted_sha256,
    )
    restored = parse_dashboard_html(fetch_edit_dashboard_config(page, dashboard_id, "draft"))
    if canonical_sha256(restored) != original_sha256:
        raise UsageError("Dashboard schema recovery readback did not match the original schema.")
    return "restored"


def _replace_component_unit_id(schema: dict[str, Any], old_unit_id: str, new_unit_id: str) -> int:
    replacements = 0

    def walk(value: Any) -> None:
        nonlocal replacements
        if isinstance(value, dict):
            replaced_node = False
            settings = value.get("settings")
            if isinstance(settings, dict) and str(settings.get("unitId") or "") == old_unit_id:
                settings["unitId"] = new_unit_id
                replaced_node = True
            props = value.get("props")
            if isinstance(props, dict):
                prop_settings = props.get("settings")
                if isinstance(prop_settings, dict) and str(prop_settings.get("unitId") or "") == old_unit_id:
                    prop_settings["unitId"] = new_unit_id
                    replaced_node = True
            if replaced_node:
                replacements += 1
            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema.get("componentsTree") or [])
    return replacements


def _count_component_unit_refs(schema: dict[str, Any], unit_id: str) -> int:
    return sum(
        1
        for component in extract_component_units(schema)
        if str(component.get("unit_id") or "") == unit_id
    )


def _pivot_component_node(schema: dict[str, Any], unit_id: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            props = value.get("props") if isinstance(value.get("props"), dict) else {}
            settings = props.get("settings") if isinstance(props.get("settings"), dict) else {}
            if (
                str(value.get("componentName") or "") == "PivotTable"
                and str(settings.get("unitId") or "") == unit_id
            ):
                matches.append(value)
            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema.get("componentsTree") or [])
    if len(matches) != 1:
        raise UsageError(f"Expected exactly one PivotTable component for {unit_id}, got {len(matches)}.")
    return matches[0]


def project_pivot_component_style(schema: dict[str, Any], unit_id: str) -> dict[str, Any]:
    node = _pivot_component_node(schema, unit_id)
    props = node.get("props") if isinstance(node.get("props"), dict) else {}
    return {
        "unit_id": unit_id,
        "node_id": str(node.get("id") or ""),
        "styles": {
            key: copy.deepcopy(props.get(key))
            for key in PIVOT_COMPONENT_STYLE_KEYS
            if key in props
        },
    }


def sync_pivot_component_style(
    *, target_schema: dict[str, Any], target_unit_id: str,
    source_schema: dict[str, Any], source_unit_id: str,
) -> dict[str, Any]:
    rebuilt = copy.deepcopy(target_schema)
    target_node = _pivot_component_node(rebuilt, target_unit_id)
    source_node = _pivot_component_node(source_schema, source_unit_id)
    target_props = target_node.setdefault("props", {})
    source_props = source_node.get("props") if isinstance(source_node.get("props"), dict) else {}
    for key in PIVOT_COMPONENT_STYLE_KEYS:
        if key in source_props:
            target_props[key] = copy.deepcopy(source_props[key])
        else:
            target_props.pop(key, None)
    return rebuilt


def _verify_exact_schema_readback(
    expected_schema: dict[str, Any], actual_schema: dict[str, Any],
) -> dict[str, str]:
    expected_sha256 = canonical_sha256(expected_schema)
    actual_sha256 = canonical_sha256(actual_schema)
    if actual_sha256 != expected_sha256:
        raise UsageError("Dashboard draft schema readback did not match the complete expected schema.")
    return {
        "status": "matched",
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
    }


def _profile_complete_with_retry(
    *,
    page: Any,
    label: str,
    attempts: int = 3,
    retry_wait_ms: int = 2_000,
    diagnostics_dir: Path | None = None,
    **profile_kwargs: Any,
) -> tuple[dict[str, Any], int]:
    """Require a complete profile, tolerating bounded post-save API settling."""

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        raw = profile_edit_dashboard(page=page, **profile_kwargs)
        try:
            return require_complete_profile(raw, label), attempt
        except UsageError as exc:
            last_error = exc
            if diagnostics_dir is not None:
                write_json(raw, diagnostics_dir / f"post-profile-incomplete-attempt-{attempt}.json")
            if attempt < attempts:
                page.wait_for_timeout(retry_wait_ms)
    raise UsageError(f"{label} remained incomplete after {attempts} attempts: {last_error}")


def _formula_manifest_projection(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "columnKey": item.get("columnKey"),
        "columnName": item.get("columnName"),
        "columnDesc": item.get("columnDesc") or "",
        "dataType": item.get("dataType"),
        "formula": item.get("formula"),
        "dependencyIndicators": item.get("dependencyIndicators") or [],
        "globalFilterSpecialConfig": item.get("globalFilterSpecialConfig") or [],
    }


def _remap_formula_references(value: Any, mapped: dict[str, str], source_custom_ids: set[str]) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            param_id = str(child or "") if key == "paramId" else ""
            if param_id in source_custom_ids:
                if param_id not in mapped:
                    raise UsageError(f"Custom formula dependency is not ordered before its consumer: {param_id}")
                result[key] = mapped[param_id]
            else:
                result[key] = _remap_formula_references(child, mapped, source_custom_ids)
        return result
    if isinstance(value, list):
        return [_remap_formula_references(item, mapped, source_custom_ids) for item in value]
    if isinstance(value, str) and any(custom_id in value for custom_id in source_custom_ids):
        raise UsageError("Formula dependency contains an unsupported source-specific custom field reference.")
    return copy.deepcopy(value)


def _formula_comparison_projection(item: dict[str, Any]) -> dict[str, Any]:
    projected = copy.deepcopy(item)
    projected.pop("columnKey", None)
    return projected


def _materialize_custom_formulas(
    *, page: Any, dashboard_id: str, source_detail: dict[str, Any], target_detail: dict[str, Any],
    operation: dict[str, Any], observations: list[dict[str, Any]], formula_results: list[dict[str, Any]],
    pre_write_check: Callable[[], None] | None = None,
) -> dict[str, Any]:
    catalog = operation.get("source_custom_formulas") or []
    if not catalog:
        custom_ids = [
            str(field.get("fieldId")) for field in source_detail.get("unitMeasureList") or []
            if str(field.get("fieldId") or "").startswith("customized_")
        ]
        if custom_ids:
            raise UsageError("Source custom formulas require an explicit reviewed source_custom_formulas catalog.")
        return source_detail
    dashboard_model = target_detail.get("dashboardModel") or {}
    subject_id = int(dashboard_model.get("subjectId") or 0)
    model_type = int(dashboard_model.get("modelType") or 2)
    if subject_id != int(operation.get("target_subject_id") or 0):
        raise UsageError("Target pivot subject identity drifted before formula creation.")
    expected_by_id = {str(item["source_field_id"]): item for item in catalog}
    source_custom_ids = [
        str(field.get("fieldId")) for field in source_detail.get("unitMeasureList") or []
        if str(field.get("fieldId") or "").startswith("customized_")
    ]
    if source_custom_ids != list(expected_by_id):
        raise UsageError("Source custom formula order no longer matches the reviewed manifest.")
    source_custom_id_set = set(source_custom_ids)
    mapped: dict[str, str] = {}
    for source_id in source_custom_ids:
        expected = expected_by_id[source_id]
        live_source = _formula_manifest_projection(_formula_item(page, source_id))
        if canonical_sha256(live_source) != str(expected.get("source_formula_sha256") or ""):
            raise UsageError(f"Source custom formula drifted: {source_id}")
        if any(custom_id in str(live_source.get("formula") or "") for custom_id in source_custom_id_set):
            raise UsageError("Formula text contains source-specific custom field IDs; manual remapping is required.")
        fields_result = fetch_dataset_fields(page, dashboard_id, [subject_id], [model_type], [])
        fields = fields_result[0].get("fields") if fields_result and not fields_result[0].get("error") else None
        if not isinstance(fields, list):
            raise UsageError("Target dataset field tree readback failed during formula materialization.")
        matches = [item for item in fields if item.get("title") == live_source["columnName"]]
        if len(matches) > 1:
            raise UsageError(f"Target calculated-column name is ambiguous: {live_source['columnName']}")
        expected_target_formula = copy.deepcopy(live_source)
        for key in ("dependencyIndicators", "globalFilterSpecialConfig"):
            expected_target_formula[key] = _remap_formula_references(
                expected_target_formula[key], mapped, source_custom_id_set
            )
        result = {
            "source_field_id": source_id,
            "target_field_id": None,
            "name": live_source["columnName"],
            "status": "reused" if matches else "create_pending",
        }
        formula_results.append(result)
        status = "reused"
        if matches:
            target_id = str(matches[0].get("key") or "")
            if not target_id:
                raise UsageError(f"Target calculated-column identity is missing: {live_source['columnName']}")
            existing = _formula_manifest_projection(_formula_item(page, target_id))
            if _formula_comparison_projection(existing) != _formula_comparison_projection(expected_target_formula):
                raise UsageError(f"Same-name target formula or dependency definition differs: {live_source['columnName']}")
        else:
            payload = {
                "subjectId": subject_id, "columnKey": None,
                "columnName": live_source["columnName"], "columnDesc": live_source["columnDesc"],
                "dataType": live_source["dataType"], "formula": live_source["formula"],
                "dependencyIndicators": expected_target_formula["dependencyIndicators"],
                "globalFilterSpecialConfig": expected_target_formula["globalFilterSpecialConfig"],
            }
            try:
                if pre_write_check is not None:
                    pre_write_check()
                _write_formula(page, payload, observations)
            except Exception:
                result["status"] = "create_outcome_unknown"
                raise
            result["status"] = "create_acknowledged"
            page.wait_for_timeout(500)
            refreshed = fetch_dataset_fields(page, dashboard_id, [subject_id], [model_type], [])
            refreshed_fields = refreshed[0].get("fields") if refreshed and not refreshed[0].get("error") else []
            matches = [item for item in refreshed_fields if item.get("title") == live_source["columnName"]]
            if len(matches) != 1:
                result["status"] = "created_unreadable"
                raise UsageError(f"Created formula was not uniquely readable: {live_source['columnName']}")
            target_id = str(matches[0].get("key") or "")
            if not target_id:
                result["status"] = "created_unreadable"
                raise UsageError(f"Created formula identity is missing: {live_source['columnName']}")
            status = "created"
        target_formula = _formula_item(page, target_id)
        target_projection = _formula_manifest_projection(target_formula)
        if _formula_comparison_projection(target_projection) != _formula_comparison_projection(expected_target_formula):
            if status == "created":
                result["status"] = "created_readback_mismatch"
            raise UsageError(f"Target formula/dependency readback mismatch: {live_source['columnName']}")
        mapped[source_id] = target_id
        result.update({"target_field_id": target_id, "status": status})

    remapped = copy.deepcopy(source_detail)
    for field in remapped.get("unitMeasureList") or []:
        source_id = str(field.get("fieldId") or "")
        if source_id in mapped:
            field["fieldId"] = mapped[source_id]
            field["uniqueKeyWithTimeStamp"] = f"{mapped[source_id]}-{int(time.time() * 1000)}"
    return remapped


def _orphaned_formula_resources(formula_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    uncertain = {
        "create_outcome_unknown",
        "create_acknowledged",
        "created_unreadable",
        "created_readback_mismatch",
    }
    return [
        {
            "resource_type": "custom_formula",
            "resource_id": item.get("target_field_id"),
            "name": item.get("name"),
            "status": item.get("status"),
            "manual_cleanup_required": True,
        }
        for item in formula_results
        if item.get("status") in uncertain or item.get("status") == "created"
    ]


def _field_rebound_copy(
    *,
    copied_detail: dict[str, Any],
    source_detail: dict[str, Any],
    target_detail: dict[str, Any],
    operation: dict[str, Any],
) -> dict[str, Any]:
    target_field_projection = rebuild_pivot_unit_fields(
        target_detail=target_detail,
        source_detail=source_detail,
        dimension_field_ids=operation["dimension_field_ids"],
        measure_mode=str(operation.get("measure_mode") or "source_all"),
        measure_field_ids=operation.get("measure_field_ids"),
        required_measure_field_ids=operation.get("required_measure_field_ids") or [],
        preserve_target_display=operation.get("preserve_target_display", True) is not False,
        dimension_show_names=operation.get("dimension_show_names") or {},
        sync_source_format=operation.get("sync_source_format") is True,
    )
    rebound = copy.deepcopy(copied_detail)
    for group in FIELD_LIST_GROUPS:
        rebound[group] = copy.deepcopy(target_field_projection.get(group) or [])
    for key in ("unitName", "description", "format"):
        if key in target_detail:
            rebound[key] = copy.deepcopy(target_detail.get(key))
    return rebound


def _run_filtered_value_checks(
    *,
    page: Any,
    checks: list[dict[str, Any]],
    operation_unit_ids: dict[str, str],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for check in checks:
        unit_id = str(check.get("unit_id") or "").strip()
        operation_id = str(check.get("operation_id") or "").strip()
        if not unit_id:
            unit_id = operation_unit_ids.get(operation_id, "")
        if not unit_id:
            raise UsageError(f"{check['check_id']} could not resolve a unit_id for value/unit validation.")

        payload = default_unit_value_payload(unit_id, check.get("page_size") or 200)
        payload["publicFilterList"] = copy.deepcopy(check["public_filter_list"])
        for key, value in (check.get("payload_overrides") or {}).items():
            payload[key] = copy.deepcopy(value)

        value_payload = post_json(page, UNIT_VALUE_API, payload, timeout_ms=60_000)
        result = assert_filtered_value_response(check=check, unit_id=unit_id, value_payload=value_payload)
        result.update(
            {
                "operation_id": operation_id or None,
                "public_filter_sha256": canonical_sha256(check["public_filter_list"]),
                "required_public_filters": copy.deepcopy(check["required_public_filters"]),
            }
        )
        results.append(result)
    return results


def _execution_mode(args: Any, manifest: dict[str, Any], registry_path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    production = bool(getattr(args, "confirm_production_write", False))
    sandbox = bool(getattr(args, "confirm_sandbox_write", False))
    if production and sandbox:
        raise UsageError("Choose exactly one pivot rebind execution mode.")
    if not production and not sandbox:
        raise UsageError("Pivot rebind requires an explicit write confirmation.")

    dashboard_id = str(
        getattr(args, "dashboard_id", None)
        or getattr(args, "sandbox_dashboard_id", None)
        or manifest.get("dashboard_id")
        or ""
    ).strip()
    expected_name = str(getattr(args, "expected_dashboard_name", None) or manifest.get("dashboard_name") or "").strip()
    if not dashboard_id or not expected_name:
        raise UsageError("Pivot rebind requires dashboard id and expected dashboard name.")
    if manifest.get("dashboard_id") and str(manifest["dashboard_id"]) != dashboard_id:
        raise UsageError("Manifest dashboard_id does not match the command dashboard id.")
    if manifest.get("dashboard_name") and str(manifest["dashboard_name"]) != expected_name:
        raise UsageError("Manifest dashboard_name does not match --expected-dashboard-name.")

    if production:
        if manifest.get("production_draft_sync") is not True:
            raise UsageError("Production draft sync requires production_draft_sync=true in the reviewed manifest.")
        operations = _operation_list(manifest)
        if len(operations) != 1:
            raise UsageError("Production draft sync supports exactly one existing pivot per operation.")
        if any(operation.get("rebuild_by_copy") is True for operation in operations):
            raise UsageError("Production draft sync cannot copy or replace unit identities.")
        manifest_sha256 = str(getattr(args, "manifest_sha256", "") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", manifest_sha256):
            raise UsageError("Production draft sync requires --manifest-sha256 with the reviewed manifest hash.")
        actual_manifest_sha256 = canonical_sha256(manifest)
        if manifest_sha256 != actual_manifest_sha256:
            raise UsageError("Production draft sync manifest hash mismatch; no write was attempted.")
        expected_profile_sha256 = str(manifest.get("expected_profile_sha256") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_profile_sha256):
            raise UsageError("Production draft sync requires an exact expected_profile_sha256.")
        for operation in _operation_list(manifest):
            for key in ("expected_before_sha256", "expected_source_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", str(operation.get(key) or "").lower()):
                    raise UsageError(f"Production draft sync requires exact {key} for {operation['operation_id']}.")
            if operation.get("sync_component_style") is True:
                for key in ("expected_target_style_sha256", "expected_source_style_sha256"):
                    if not re.fullmatch(r"[0-9a-f]{64}", str(operation.get(key) or "").lower()):
                        raise UsageError(f"Production component-style sync requires exact {key} for {operation['operation_id']}.")
        registry = load_capability_registry(registry_path)
        capability = capability_by_operation(registry, "sync_existing_pivot_fields_from_same_model_source")
        expected_adapter = "read_dashboard.commands.rebind_pivot_fields_sandbox.cmd_rebind_pivot_fields_sandbox[production_draft]"
        if (
            capability.get("write_policy") != "allowlisted"
            or capability.get("maturity") != "verified"
            or capability.get("phase") != "draft"
            or capability.get("transaction_class") != "compensating_restore"
            or capability.get("recovery_policy") != "compensating_restore"
            or capability.get("readback_coverage") != "full"
            or capability.get("adapter") != expected_adapter
        ):
            raise UsageError("Production pivot draft sync is not enabled by a verified allowlisted capability.")
        expected_write_endpoints = {
            "config/save/dashboardHtml",
            "config/update/unit",
            "model/customized/column/saveAndUpdate",
        }
        if set(capability.get("write_endpoints") or []) != expected_write_endpoints:
            raise UsageError("Production pivot draft sync registry write endpoints do not match the adapter.")
        expected_readback_endpoints = {
            "model/customized/column/list",
            "model/subject/param/list",
            "value/unit/consumer/detail",
            "config/dashBoard",
        }
        if set(capability.get("readback_endpoints") or []) != expected_readback_endpoints:
            raise UsageError("Production pivot draft sync registry readback endpoints do not match the adapter.")
        return {
            "name": "production_draft",
            "dashboard_id": dashboard_id,
            "expected_name": expected_name,
            "target_backup_label": "production_draft_prewrite",
            "receipt_artifact_type": "DashboardPivotFieldSyncDraftReceipt",
            "requires_allowlist": True,
            "capability": "sync_existing_pivot_fields_from_same_model_source",
            "registry_sha256": str(registry.get("registry_sha256") or ""),
            "manifest_sha256": actual_manifest_sha256,
        }

    _require_sandbox(dashboard_id, expected_name)
    return {
        "name": "sandbox",
        "dashboard_id": dashboard_id,
        "expected_name": expected_name,
        "target_backup_label": "sandbox_prewrite",
        "receipt_artifact_type": "DashboardPivotFieldRebindSandboxReceipt",
        "requires_allowlist": False,
    }


def cmd_rebind_pivot_fields_sandbox(args) -> int:
    manifest = _load_manifest(args.target_manifest)
    domain = str(manifest.get("domain") or "")
    if domain != args.domain:
        raise UsageError("Pivot rebind manifest domain does not match --domain.")
    mode = _execution_mode(args, manifest, getattr(args, "registry", DEFAULT_REGISTRY))
    sandbox_dashboard_id = mode["dashboard_id"]
    expected_name = mode["expected_name"]
    operations = _operation_list(manifest)
    filtered_value_checks = normalize_filtered_value_checks(
        manifest,
        operations,
        require=False,
    )

    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_path = args.output or (artifacts_dir / f"pivot-field-rebind-{mode['name']}-receipt.json")

    with sync_playwright() as playwright:
        browser, context = launch_context(
            playwright,
            args.state_path,
            args.headed,
            args.browser_channel,
            args.executable_path,
        )
        page = context.new_page()
        completed: list[dict[str, Any]] = []
        copied_unit_results: list[dict[str, Any]] = []
        formula_results: list[dict[str, Any]] = []
        component_style_results: list[dict[str, Any]] = []
        filtered_value_results: list[dict[str, Any]] = []
        operation_results: list[dict[str, Any]] = []
        backup_results: list[dict[str, Any]] = []
        dashboard_schema_result: dict[str, Any] | None = None
        original_schema: dict[str, Any] | None = None
        working_schema: dict[str, Any] | None = None
        schema_written = False
        pre_profile: dict[str, Any] | None = None
        post_profile: dict[str, Any] | None = None
        post_profile_attempts = 0
        expected_current_unit_states: dict[str, dict[str, Any]] = {}
        source_unit_states: dict[tuple[str, str], dict[str, Any]] = {}
        recovery: dict[str, Any] = {"attempted": False, "status": "not_needed", "operations": [], "error": None}
        try:
            edit_url = build_edit_url(sandbox_dashboard_id)
            open_edit_page(page, args, context=context, edit_url=edit_url)
            config = fetch_edit_dashboard_config(page, sandbox_dashboard_id, "draft")
            if str(config.get("dashboardName") or "") != expected_name:
                raise UsageError("Live dashboard name does not match expected_dashboard_name.")
            if config.get("haveEditPermission") is not True:
                raise UsageError("Current identity does not have confirmed edit permission on the target dashboard.")

            for backup_target in _manifest_backups(
                manifest,
                sandbox_dashboard_id,
                expected_name,
                target_label=mode["target_backup_label"],
            ):
                backup_results.append(_backup_dashboard(
                    page=page,
                    dashboard_id=backup_target["dashboard_id"],
                    expected_name=backup_target.get("dashboard_name") or None,
                    domain=domain,
                    artifacts_dir=artifacts_dir,
                    label=backup_target["label"],
                ))
            if not backup_results:
                raise UsageError("No configuration backups were written; refusing to edit dashboard.")
            if any(item["unit_error_count"] for item in backup_results):
                raise UsageError("Configuration backup had unit detail errors; refusing to edit dashboard.")

            pre_raw = profile_edit_dashboard(
                page=page,
                dashboard_id=sandbox_dashboard_id,
                html_id=str(config.get("htmlId") or "") or None,
                edit_url=edit_url,
                version_id="draft",
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
                include_dataset_fields=True,
                domain=domain,
            )
            pre_profile = require_complete_profile(pre_raw, f"Pre-rebind {mode['name']} profile")
            expected_profile = str(manifest.get("expected_profile_sha256") or "")
            if expected_profile and str(pre_profile.get("profile_sha256") or "") != expected_profile:
                raise UsageError(f"{mode['name']} profile SHA-256 does not match the manifest expected_profile_sha256.")

            original_schema = parse_dashboard_html(config)
            working_schema = copy.deepcopy(original_schema)
            for operation in operations:
                target_unit_id = str(operation["target_unit_id"])
                source_unit_id = str(operation["source_unit_id"])
                before_raw = fetch_edit_unit_detail(page, target_unit_id, sandbox_dashboard_id, "draft")
                source_dashboard_id = str(operation.get("source_dashboard_id") or sandbox_dashboard_id)
                source_raw = fetch_edit_unit_detail(page, source_unit_id, source_dashboard_id, "draft")
                before_state = project_unit_field_state(before_raw)
                source_state = project_unit_field_state(source_raw)
                if mode["name"] == "production_draft":
                    target_model_id = str(before_raw.get("modelId") or "")
                    source_model_id = str(source_raw.get("modelId") or "")
                    if not target_model_id or target_model_id != source_model_id:
                        raise UsageError("Production pivot source and target must have the same non-empty model identity.")
                expected_before_sha256 = str(operation.get("expected_before_sha256") or "")
                expected_source_sha256 = str(operation.get("expected_source_sha256") or "")
                if mode["name"] == "production_draft" and (not expected_before_sha256 or not expected_source_sha256):
                    raise UsageError("Production draft sync requires exact source and target unit projection hashes.")
                if expected_before_sha256 and canonical_sha256(before_state) != expected_before_sha256:
                    raise UsageError(f"Target unit projection drifted: {operation['operation_id']}")
                if expected_source_sha256 and canonical_sha256(source_state) != expected_source_sha256:
                    raise UsageError(f"Source unit projection drifted: {operation['operation_id']}")
                if mode["name"] == "production_draft":
                    before_raw = _read_stable_unit_projection(
                        page=page, dashboard_id=sandbox_dashboard_id, unit_id=target_unit_id,
                        expected_state=before_state, label=f"Target {operation['operation_id']}",
                    )
                    source_raw = _read_stable_unit_projection(
                        page=page, dashboard_id=source_dashboard_id, unit_id=source_unit_id,
                        expected_state=source_state, label=f"Source {operation['operation_id']}",
                    )
                expected_current_unit_states[target_unit_id] = before_state
                source_unit_states[(source_dashboard_id, source_unit_id)] = source_state

                if operation.get("sync_component_style") is True:
                    source_config = fetch_edit_dashboard_config(page, source_dashboard_id, "draft")
                    source_schema = parse_dashboard_html(source_config)
                    target_style_before = project_pivot_component_style(working_schema, target_unit_id)
                    source_style = project_pivot_component_style(source_schema, source_unit_id)
                    expected_target_style_sha256 = str(operation.get("expected_target_style_sha256") or "")
                    expected_source_style_sha256 = str(operation.get("expected_source_style_sha256") or "")
                    if mode["name"] == "production_draft" and (
                        not expected_target_style_sha256 or not expected_source_style_sha256
                    ):
                        raise UsageError("Production component-style sync requires exact source and target style hashes.")
                    if expected_target_style_sha256 and canonical_sha256(target_style_before) != expected_target_style_sha256:
                        raise UsageError(f"Target component style drifted: {operation['operation_id']}")
                    if expected_source_style_sha256 and canonical_sha256(source_style) != expected_source_style_sha256:
                        raise UsageError(f"Source component style drifted: {operation['operation_id']}")
                    working_schema = sync_pivot_component_style(
                        target_schema=working_schema, target_unit_id=target_unit_id,
                        source_schema=source_schema, source_unit_id=source_unit_id,
                    )
                    component_style_results.append({
                        "operation_id": str(operation["operation_id"]),
                        "target_unit_id": target_unit_id,
                        "source_unit_id": source_unit_id,
                        "before_sha256": canonical_sha256(target_style_before),
                        "source_sha256": canonical_sha256(source_style),
                        "expected_after": project_pivot_component_style(working_schema, target_unit_id),
                    })

                if operation.get("sync_unit_fields", True) is False:
                    operation_results.append({
                        "operation_id": str(operation["operation_id"]),
                        "target_unit_id": target_unit_id,
                        "source_unit_id": source_unit_id,
                        "source_dashboard_id": source_dashboard_id,
                        "status": "component_style_planned",
                        "before_sha256": canonical_sha256(before_state),
                        "after_sha256": canonical_sha256(before_state),
                        "projection_changed": False,
                        "observations": [],
                    })
                    continue
                observations: list[dict[str, Any]] = []

                def check_formula_write_baseline() -> None:
                    if mode["name"] != "production_draft":
                        return
                    _read_stable_unit_projection(
                        page=page, dashboard_id=sandbox_dashboard_id, unit_id=target_unit_id,
                        expected_state=expected_current_unit_states[target_unit_id],
                        label=f"Target {operation['operation_id']}",
                    )
                    _read_stable_unit_projection(
                        page=page, dashboard_id=source_dashboard_id, unit_id=source_unit_id,
                        expected_state=source_unit_states[(source_dashboard_id, source_unit_id)],
                        label=f"Source {operation['operation_id']}",
                    )

                source_for_rebuild = _materialize_custom_formulas(
                    page=page, dashboard_id=sandbox_dashboard_id, source_detail=source_raw,
                    target_detail=before_raw, operation=operation, observations=observations,
                    formula_results=formula_results,
                    pre_write_check=check_formula_write_baseline,
                )

                if operation.get("rebuild_by_copy") is True:
                    copy_response = post_json(page, COPY_UNIT_API, {"id": source_unit_id}, timeout_ms=60_000)
                    new_unit_id = str(copy_response.get("data") or "").strip()
                    if not new_unit_id.startswith("unit_"):
                        raise UsageError(f"Copy unit did not return a stable unit id: {copy_response}")
                    copied_raw = fetch_edit_unit_detail(page, new_unit_id, sandbox_dashboard_id, "draft")
                    rebuilt_raw = _field_rebound_copy(
                        copied_detail=copied_raw,
                        source_detail=source_for_rebuild,
                        target_detail=before_raw,
                        operation=operation,
                    )
                    expected_after_state = project_unit_field_state(rebuilt_raw)
                    _write_unit_detail(page, sandbox_dashboard_id, rebuilt_raw, observations)
                    page.wait_for_timeout(max(0, int(getattr(args, "touch_wait_ms", 1_000))))
                    after_raw = fetch_edit_unit_detail(page, new_unit_id, sandbox_dashboard_id, "draft")
                    after_state = project_unit_field_state(after_raw)
                    if after_state != expected_after_state:
                        raise UsageError(f"Copied unit rebind readback mismatch: {operation['operation_id']}")
                    replacement_count = _replace_component_unit_id(working_schema, target_unit_id, new_unit_id)
                    if replacement_count != 1:
                        raise UsageError(
                            f"Expected exactly one component reference for {target_unit_id}, got {replacement_count}."
                        )
                    copied_unit_result = {
                        "operation_id": str(operation["operation_id"]),
                        "target_unit_id": target_unit_id,
                        "source_unit_id": source_unit_id,
                        "source_dashboard_id": source_dashboard_id,
                        "new_unit_id": new_unit_id,
                        "copy_status": copy_response.get("status"),
                        "replacement_count": replacement_count,
                        "after_sha256": canonical_sha256(after_state),
                        "observations": observations,
                    }
                    copied_unit_results.append(copied_unit_result)
                    operation_results.append(
                        {
                            **copied_unit_result,
                            "status": "copied_and_rebound",
                            "before_sha256": canonical_sha256(before_state),
                            "projection_changed": True,
                            "rebuild_by_copy": True,
                        }
                    )
                    continue

                recovery_record: dict[str, Any] | None = None

                def register_recovery(expected_state: dict[str, Any]) -> None:
                    nonlocal recovery_record
                    if recovery_record is None:
                        recovery_record = {
                            "operation_id": str(operation["operation_id"]),
                            "target_unit_id": target_unit_id,
                            "before_raw": before_raw,
                            "before_state": before_state,
                            "allowed_current_states": [before_state],
                        }
                        completed.append(recovery_record)
                    if expected_state not in recovery_record["allowed_current_states"]:
                        recovery_record["allowed_current_states"].append(expected_state)

                touch_state: dict[str, Any] | None = None
                touch_projection_changed = False
                if operation.get("touch_before_final") is True:
                    if mode["name"] == "production_draft":
                        source_raw = _read_stable_unit_projection(
                            page=page, dashboard_id=source_dashboard_id, unit_id=source_unit_id,
                            expected_state=source_state, label=f"Source {operation['operation_id']}",
                        )
                        touch_target_raw = _read_stable_unit_projection(
                            page=page, dashboard_id=sandbox_dashboard_id, unit_id=target_unit_id,
                            expected_state=expected_current_unit_states[target_unit_id],
                            label=f"Target {operation['operation_id']}",
                        )
                    else:
                        touch_target_raw = before_raw
                    touch_dimension_ids = operation.get("touch_dimension_field_ids") or _source_dimension_field_ids(source_raw)
                    touch_raw = rebuild_pivot_unit_fields(
                        target_detail=touch_target_raw,
                        source_detail=source_for_rebuild,
                        dimension_field_ids=touch_dimension_ids,
                        measure_mode=str(operation.get("measure_mode") or "source_all"),
                        measure_field_ids=operation.get("measure_field_ids"),
                        required_measure_field_ids=operation.get("required_measure_field_ids") or [],
                        preserve_target_display=operation.get("preserve_target_display", True) is not False,
                        dimension_show_names=operation.get("dimension_show_names") or {},
                        sync_source_format=operation.get("sync_source_format") is True,
                    )
                    expected_touch_state = project_unit_field_state(touch_raw)
                    register_recovery(expected_touch_state)
                    _write_unit_detail(page, sandbox_dashboard_id, touch_raw, observations)
                    page.wait_for_timeout(max(0, int(getattr(args, "touch_wait_ms", 1_000))))
                    touch_readback = fetch_edit_unit_detail(page, target_unit_id, sandbox_dashboard_id, "draft")
                    touch_state = project_unit_field_state(touch_readback)
                    if touch_state != expected_touch_state:
                        raise UsageError(f"Unit touch readback mismatch: {operation['operation_id']}")
                    touch_projection_changed = before_state != touch_state
                    expected_current_unit_states[target_unit_id] = expected_touch_state

                if mode["name"] == "production_draft":
                    source_raw = _read_stable_unit_projection(
                        page=page, dashboard_id=source_dashboard_id, unit_id=source_unit_id,
                        expected_state=source_state, label=f"Source {operation['operation_id']}",
                    )
                    target_write_before = _read_stable_unit_projection(
                        page=page, dashboard_id=sandbox_dashboard_id, unit_id=target_unit_id,
                        expected_state=expected_current_unit_states[target_unit_id],
                        label=f"Target {operation['operation_id']}",
                    )
                else:
                    target_write_before = before_raw if touch_state is None else touch_readback

                rebuilt_raw = rebuild_pivot_unit_fields(
                    target_detail=target_write_before,
                    source_detail=source_for_rebuild,
                    dimension_field_ids=operation["dimension_field_ids"],
                    measure_mode=str(operation.get("measure_mode") or "source_all"),
                    measure_field_ids=operation.get("measure_field_ids"),
                    required_measure_field_ids=operation.get("required_measure_field_ids") or [],
                    preserve_target_display=operation.get("preserve_target_display", True) is not False,
                    dimension_show_names=operation.get("dimension_show_names") or {},
                    sync_source_format=operation.get("sync_source_format") is True,
                )
                expected_after_state = project_unit_field_state(rebuilt_raw)
                register_recovery(expected_after_state)
                _write_unit_detail(page, sandbox_dashboard_id, rebuilt_raw, observations)
                expected_current_unit_states[target_unit_id] = expected_after_state
                page.wait_for_timeout(max(0, int(getattr(args, "touch_wait_ms", 1_000))))
                after_raw = fetch_edit_unit_detail(page, target_unit_id, sandbox_dashboard_id, "draft")
                after_state = project_unit_field_state(after_raw)
                if after_state != expected_after_state:
                    raise UsageError(f"Unit rebind readback mismatch: {operation['operation_id']}")
                operation_results.append(
                    {
                        "operation_id": str(operation["operation_id"]),
                        "target_unit_id": target_unit_id,
                        "source_unit_id": source_unit_id,
                        "source_dashboard_id": source_dashboard_id,
                        "status": "saved",
                        "before_sha256": canonical_sha256(before_state),
                        "touch_sha256": canonical_sha256(touch_state) if touch_state is not None else None,
                        "after_sha256": canonical_sha256(after_state),
                        "touch_projection_changed": touch_projection_changed,
                        "projection_changed": before_state != after_state,
                        "observations": observations,
                    }
                )

            if copied_unit_results or component_style_results:
                schema_observations: list[dict[str, Any]] = []
                if mode["name"] == "production_draft":
                    for target_unit_id, expected_state in expected_current_unit_states.items():
                        _read_stable_unit_projection(
                            page=page, dashboard_id=sandbox_dashboard_id, unit_id=target_unit_id,
                            expected_state=expected_state, label=f"Target {target_unit_id}",
                        )
                    for style_result in component_style_results:
                        operation = next(
                            item for item in operations
                            if str(item["operation_id"]) == style_result["operation_id"]
                        )
                        source_dashboard_id = str(operation.get("source_dashboard_id") or sandbox_dashboard_id)
                        for _ in range(2):
                            source_config = fetch_edit_dashboard_config(page, source_dashboard_id, "draft")
                            source_style = project_pivot_component_style(
                                parse_dashboard_html(source_config), style_result["source_unit_id"]
                            )
                            if canonical_sha256(source_style) != style_result["source_sha256"]:
                                raise UsageError(f"Source component style drifted before write: {style_result['operation_id']}")
                schema_written = True
                _write_dashboard_schema(
                    page, sandbox_dashboard_id, expected_name, working_schema, schema_observations,
                    expected_schema_sha256=canonical_sha256(original_schema)
                    if mode["name"] == "production_draft" else None,
                )
                latest_config = fetch_edit_dashboard_config(page, sandbox_dashboard_id, "draft")
                latest_schema = parse_dashboard_html(latest_config)
                schema_readback = (
                    _verify_exact_schema_readback(working_schema, latest_schema)
                    if mode["name"] == "production_draft" else None
                )
                verification = []
                for item in copied_unit_results:
                    old_count = _count_component_unit_refs(latest_schema, item["target_unit_id"])
                    new_count = _count_component_unit_refs(latest_schema, item["new_unit_id"])
                    verification.append(
                        {
                            "target_unit_id": item["target_unit_id"],
                            "new_unit_id": item["new_unit_id"],
                            "old_reference_count": old_count,
                            "new_reference_count": new_count,
                        }
                    )
                bad_verification = [
                    item for item in verification if item["old_reference_count"] != 0 or item["new_reference_count"] != 1
                ]
                if bad_verification:
                    raise UsageError(f"Dashboard schema unit reference verification failed: {bad_verification}")
                style_verification = []
                for item in component_style_results:
                    actual = project_pivot_component_style(latest_schema, item["target_unit_id"])
                    ok = actual == item["expected_after"]
                    style_verification.append({
                        "operation_id": item["operation_id"],
                        "target_unit_id": item["target_unit_id"],
                        "before_sha256": item["before_sha256"],
                        "source_sha256": item["source_sha256"],
                        "after_sha256": canonical_sha256(actual),
                        "status": "matched" if ok else "mismatch",
                    })
                    if not ok:
                        raise UsageError(f"Component style readback mismatch: {item['operation_id']}")
                dashboard_schema_result = {
                    "status": "saved",
                    "observations": schema_observations,
                    "schema_readback": schema_readback,
                    "verification": verification,
                    "style_verification": style_verification,
                }

            post_profile, post_profile_attempts = _profile_complete_with_retry(
                page=page,
                label=f"Post-rebind {mode['name']} profile",
                diagnostics_dir=artifacts_dir,
                dashboard_id=sandbox_dashboard_id,
                html_id=str(config.get("htmlId") or "") or None,
                edit_url=edit_url,
                version_id="draft",
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
                include_dataset_fields=True,
                domain=domain,
            )
            operation_unit_ids = {
                str(operation["operation_id"]): str(operation["target_unit_id"])
                for operation in operations
            }
            for item in copied_unit_results:
                operation_unit_ids[str(item["operation_id"])] = str(item["new_unit_id"])
            filtered_value_results = _run_filtered_value_checks(
                page=page,
                checks=filtered_value_checks,
                operation_unit_ids=operation_unit_ids,
            )
            if args.restore_after_apply:
                recovery["attempted"] = True
                if schema_written and original_schema is not None and working_schema is not None:
                    schema_recovery_observations: list[dict[str, Any]] = []
                    schema_status = _restore_schema_if_expected(
                        page=page, dashboard_id=sandbox_dashboard_id, dashboard_name=expected_name,
                        original_schema=original_schema, attempted_schema=working_schema,
                        observations=schema_recovery_observations,
                    )
                    schema_written = False
                    recovery["schema"] = {
                        "status": schema_status,
                        "observations": schema_recovery_observations,
                    }
                recovery["operations"] = _restore_units(
                    page=page,
                    dashboard_id=sandbox_dashboard_id,
                    dashboard_name=expected_name,
                    completed=completed,
                )
                recovery["status"] = "restored"
        except Exception as exc:  # noqa: BLE001
            if schema_written and original_schema is not None and working_schema is not None:
                recovery["attempted"] = True
                try:
                    schema_recovery_observations = []
                    schema_status = _restore_schema_if_expected(
                        page=page, dashboard_id=sandbox_dashboard_id, dashboard_name=expected_name,
                        original_schema=original_schema, attempted_schema=working_schema,
                        observations=schema_recovery_observations,
                    )
                    schema_written = False
                    recovery["schema"] = {
                        "status": schema_status,
                        "observations": schema_recovery_observations,
                    }
                    recovery["status"] = "restored"
                except Exception as recovery_exc:  # noqa: BLE001
                    recovery["schema"] = {
                        "status": "failed",
                        "error": f"{type(recovery_exc).__name__}: {recovery_exc}",
                    }
                    recovery["status"] = "failed"
            if completed:
                recovery["attempted"] = True
                try:
                    recovery["operations"] = _restore_units(
                        page=page,
                        dashboard_id=sandbox_dashboard_id,
                        dashboard_name=expected_name,
                        completed=completed,
                    )
                    recovery["status"] = "restored"
                except Exception as recovery_exc:  # noqa: BLE001
                    recovery["status"] = "failed"
                    recovery["error"] = f"{type(recovery_exc).__name__}: {recovery_exc}"
            failure_receipt = {
                "schema_version": "1.0.0",
                "artifact_type": mode["receipt_artifact_type"],
                "execution_mode": mode["name"],
                "domain": domain,
                "dashboard_id": sandbox_dashboard_id,
                "dashboard_name": expected_name,
                "manifest_sha256": mode.get("manifest_sha256") or canonical_sha256(manifest),
                "capability": mode.get("capability"),
                "registry_sha256": mode.get("registry_sha256"),
                "pre_profile_sha256": str((pre_profile or {}).get("profile_sha256") or ""),
                "post_profile_sha256": str((post_profile or {}).get("profile_sha256") or ""),
                "backups": backup_results,
                "operations": operation_results,
                "formulas": formula_results,
                "orphaned_resources": _orphaned_formula_resources(formula_results),
                "component_styles": component_style_results,
                "dashboard_schema": dashboard_schema_result,
                "recovery": recovery,
                "output_path": str(output_path),
                "status": "recovery_failed" if recovery["status"] == "failed" else "failed",
                "failure": {"type": type(exc).__name__},
                "receipt_sha256": "",
            }
            failure_receipt["receipt_sha256"] = canonical_sha256(
                {key: value for key, value in failure_receipt.items() if key != "receipt_sha256"}
            )
            try:
                write_json(failure_receipt, output_path)
            except Exception as receipt_exc:  # noqa: BLE001
                raise UsageError(
                    f"Pivot rebind failed: {exc}; recovery={recovery['status']}; "
                    f"failure receipt write failed ({type(receipt_exc).__name__})."
                ) from exc
            raise UsageError(
                f"Pivot rebind failed: {exc}; recovery={recovery['status']}; failure_receipt={output_path}"
            ) from exc
        finally:
            browser.close()

    receipt = {
        "schema_version": "1.0.0",
        "artifact_type": mode["receipt_artifact_type"],
        "execution_mode": mode["name"],
        "domain": domain,
        "dashboard_id": sandbox_dashboard_id,
        "dashboard_name": expected_name,
        "manifest_sha256": mode.get("manifest_sha256") or canonical_sha256(manifest),
        "capability": mode.get("capability"),
        "registry_sha256": mode.get("registry_sha256"),
        "pre_profile_sha256": str(pre_profile.get("profile_sha256") or ""),
        "post_profile_sha256": str(post_profile.get("profile_sha256") or ""),
        "post_profile_attempts": post_profile_attempts,
        "backups": backup_results,
        "operations": operation_results,
        "formulas": formula_results,
        "orphaned_resources": (
            _orphaned_formula_resources(formula_results)
            if recovery["status"] == "restored"
            else []
        ),
        "component_styles": component_style_results,
        "copied_units": copied_unit_results,
        "filtered_value_checks": filtered_value_results,
        "dashboard_schema": dashboard_schema_result,
        "recovery": recovery,
        "status": "restored" if recovery["status"] == "restored" else "applied",
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = canonical_sha256({key: value for key, value in receipt.items() if key != "receipt_sha256"})
    write_json(receipt, output_path)
    summary = {
        "ok": True,
        "status": receipt["status"],
        "dashboard_id": sandbox_dashboard_id,
        "dashboard_name": expected_name,
        "operation_count": len(operation_results),
        "projection_changed_count": sum(1 for item in operation_results if item.get("projection_changed")),
        "filtered_value_check_count": len(filtered_value_results),
        "pre_profile_sha256": receipt["pre_profile_sha256"],
        "post_profile_sha256": receipt["post_profile_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "output_path": str(output_path),
        "backup_paths": [item["output_path"] for item in backup_results],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0
