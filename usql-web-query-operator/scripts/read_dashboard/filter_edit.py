"""Legacy public-filter inspection helpers; direct writes are disabled."""

from __future__ import annotations

import copy
import time
from pathlib import Path
from typing import Any

from _shared.errors import UsageError

from .common import safe_filename, write_json
from .edit_profile import (
    EDIT_API_ROOT,
    EDIT_DASHBOARD_CONFIG_API,
    EDIT_PUBLIC_FILTER_DETAIL_API,
    build_edit_url,
    extract_loaded_html_id,
    open_edit_page,
)
from .menu import collect_dashboard_records, fetch_dashboard_menu
from .profile import extract_component_units, parse_dashboard_html, post_json


EDIT_PUBLIC_FILTER_UPDATE_API = f"{EDIT_API_ROOT}/config/update/public/relation/unit"
EDIT_DASHBOARD_SAVE_AND_PUBLISH_API = f"{EDIT_API_ROOT}/version/dashboard/saveAndPublish"
EDIT_DASHBOARD_PUBLISH_WARN_API = f"{EDIT_API_ROOT}/version/dashboard/publishWarn"

QINGCHENG_FILTER_TARGET_NAMES = (
    "主管_过程数据播报-青橙",
    "私域-渠道团队",
    "私域--伙伴推送",
    "图书_SEC伙伴_青橙",
    "主管_过程数据-青橙",
    "公域--伙伴推送",
)


def split_csv_or_pipe(values: list[str] | None) -> list[str]:
    if not values:
        return []
    names: list[str] = []
    for value in values:
        for item in str(value).replace("|", ",").split(","):
            item = item.strip()
            if item:
                names.append(item)
    return names


def collect_leaf_filter_units(detail: dict[str, Any]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            unit_id = str(node.get("unitId") or "")
            child_units = node.get("unitList")
            if unit_id.startswith("public_filter_") and not unit_id.startswith("public_filter_relation_"):
                units.append(node)
                return
            if isinstance(child_units, list):
                for child in child_units:
                    walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(detail.get("unitList") or [])
    return units


def _field_lists_from_filter_unit(unit: dict[str, Any]) -> list[list[dict[str, Any]]]:
    lists: list[list[dict[str, Any]]] = []
    for root in (unit.get("format"), unit.get("relationUnit")):
        if not isinstance(root, dict):
            continue
        unit_config = root.get("unitConfig")
        if not isinstance(unit_config, dict):
            continue
        for key in ("unitDimensionList", "unitMeasureList"):
            values = unit_config.get(key)
            if isinstance(values, list):
                lists.append(values)
    return lists


def find_public_filter_unit(detail: dict[str, Any], filter_id: str) -> dict[str, Any]:
    matches = [unit for unit in collect_leaf_filter_units(detail) if str(unit.get("unitId") or "") == str(filter_id)]
    if len(matches) != 1:
        raise UsageError(f"Expected exactly one public filter {filter_id}, found {len(matches)}.")
    return matches[0]


def public_filter_field_state(unit: dict[str, Any], field_id: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for fields in _field_lists_from_filter_unit(unit):
        for field in fields:
            if not isinstance(field, dict):
                continue
            candidate_id = str(field.get("fieldId") or field.get("paramId") or "")
            if candidate_id == str(field_id):
                matches.append(field)
    if not matches:
        raise UsageError(f"Filter {unit.get('unitId')} does not contain field {field_id}.")
    field = matches[0]
    fmt = field.get("format") if isinstance(field.get("format"), dict) else {}
    return {
        "unit_id": unit.get("unitId"),
        "filter_id": unit.get("unitId"),
        "unit_name": unit.get("unitName"),
        "field_id": str(field.get("fieldId") or field.get("paramId") or ""),
        "show_name": field.get("showName") or field.get("name"),
        "operator": fmt.get("condition") or "",
        "values": copy.deepcopy(fmt.get("filterValue") or []),
        "dynamic_default": fmt.get("dynamicsFilter"),
        "default_value": fmt.get("dynamicsFilterValue"),
        "dynamics_filter": fmt.get("dynamicsFilter"),
        "dynamics_filter_value": fmt.get("dynamicsFilterValue"),
        "auto_search_default_value": fmt.get("autoSearchDefaultValue"),
    }


def assert_stable_public_filter_preconditions(
    detail: dict[str, Any],
    relation_id: str,
    operations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    detail_relation_id = str(detail.get("unitId") or detail.get("id") or relation_id)
    if detail_relation_id != str(relation_id):
        raise UsageError(f"Public filter relation drift: expected {relation_id}, got {detail_relation_id}.")
    states: list[dict[str, Any]] = []
    for operation in operations:
        target = operation.get("target") if isinstance(operation.get("target"), dict) else {}
        if str(target.get("relation_id") or "") != str(relation_id):
            raise UsageError("Public-filter precondition relation_id does not match the fetched relation.")
        filter_id = str(target.get("filter_id") or "")
        field_id = str(target.get("field_id") or "")
        unit = find_public_filter_unit(detail, filter_id)
        actual = public_filter_field_state(unit, field_id)
        expected = operation.get("before") if isinstance(operation.get("before"), dict) else {}
        checks = {
            "filter_id": filter_id,
            "field_id": field_id,
            "operator": expected.get("operator"),
            "values": expected.get("values"),
            "dynamics_filter": expected.get("dynamics_filter"),
            "dynamics_filter_value": expected.get("dynamics_filter_value"),
            "auto_search_default_value": expected.get("auto_search_default_value"),
        }
        mismatches = {
            key: {"expected": value, "actual": actual.get(key)}
            for key, value in checks.items()
            if actual.get(key) != value
        }
        if mismatches:
            raise UsageError(
                f"Public-filter target state drifted before apply for {operation.get('operation_id')}: "
                f"{sorted(mismatches)}."
            )
        states.append(actual)
    return states


def set_dynamic_filter_value_by_ids(unit: dict[str, Any], field_id: str, value: str) -> None:
    changed = False
    for fields in _field_lists_from_filter_unit(unit):
        for field in fields:
            if not isinstance(field, dict):
                continue
            candidate_id = str(field.get("fieldId") or field.get("paramId") or "")
            if candidate_id != str(field_id):
                continue
            fmt = field.setdefault("format", {})
            if not isinstance(fmt, dict):
                field["format"] = fmt = {}
            fmt["dynamicsFilter"] = True
            fmt["dynamicsFilterValue"] = str(value)
            fmt["autoSearchDefaultValue"] = False
            changed = True
    if not changed:
        raise UsageError(f"Filter {unit.get('unitId')} does not contain editable field {field_id}.")


def apply_stable_public_filter_operations(
    detail: dict[str, Any],
    relation_id: str,
    operations: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Apply only exact relation/filter/field-targeted dynamic-default changes."""

    detail_relation_id = str(detail.get("unitId") or detail.get("id") or relation_id)
    if detail_relation_id != str(relation_id):
        raise UsageError(f"Public filter relation drift: expected {relation_id}, got {detail_relation_id}.")
    updated = copy.deepcopy(detail)
    results: list[dict[str, Any]] = []
    for operation in operations:
        operation_type = str(operation.get("type") or operation.get("operation_type") or "")
        if operation_type != "update_filter_dynamic_default":
            raise UsageError(f"Unsupported dashboard operation for apply: {operation_type or '<missing>'}.")
        target = operation.get("target") if isinstance(operation.get("target"), dict) else {}
        target_relation_id = str(target.get("relation_id") or "")
        filter_id = str(target.get("filter_id") or target.get("unit_id") or "")
        field_id = str(target.get("field_id") or "")
        if target_relation_id != str(relation_id) or not filter_id or not field_id:
            raise UsageError(
                "Public-filter apply requires exact relation_id, filter_id, and field_id targets."
            )
        unit = find_public_filter_unit(updated, filter_id)
        before = public_filter_field_state(unit, field_id)
        after = operation.get("after") if isinstance(operation.get("after"), dict) else {}
        dynamic_default = after.get("dynamics_filter")
        if dynamic_default is not True:
            raise UsageError(
                f"Operation {operation.get('operation_id')} must enable a verified dynamic default; disabling is unsupported."
            )
        requested_value = after.get("dynamics_filter_value")
        if requested_value in (None, ""):
            values = after.get("values")
            if isinstance(values, list) and len(values) == 1:
                requested_value = values[0]
        if requested_value in (None, ""):
            raise UsageError(
                f"Operation {operation.get('operation_id')} is missing after.default_value."
            )
        set_dynamic_filter_value_by_ids(unit, field_id, str(requested_value))
        verified_after = public_filter_field_state(unit, field_id)
        results.append(
            {
                "operation_id": operation.get("operation_id"),
                "type": operation_type,
                "target": dict(target),
                "before": before,
                "after": verified_after,
                "ok": (
                    bool(verified_after.get("dynamics_filter"))
                    and str(verified_after.get("dynamics_filter_value")) == str(requested_value)
                    and verified_after.get("auto_search_default_value") is False
                ),
                "status": "prepared",
            }
        )
    return updated, results


def public_filter_state(unit: dict[str, Any]) -> dict[str, Any]:
    first_field: dict[str, Any] | None = None
    for fields in _field_lists_from_filter_unit(unit):
        if fields:
            first_field = fields[0]
            break
    fmt = first_field.get("format") if isinstance(first_field, dict) and isinstance(first_field.get("format"), dict) else {}
    return {
        "unit_id": unit.get("unitId"),
        "unit_name": unit.get("unitName"),
        "field_id": first_field.get("fieldId") if isinstance(first_field, dict) else None,
        "show_name": first_field.get("showName") if isinstance(first_field, dict) else None,
        "dynamics_filter": fmt.get("dynamicsFilter"),
        "dynamics_filter_value": fmt.get("dynamicsFilterValue"),
        "auto_search_default_value": fmt.get("autoSearchDefaultValue"),
    }


def set_dynamic_filter_value(unit: dict[str, Any], value: str) -> None:
    changed = False
    for fields in _field_lists_from_filter_unit(unit):
        for field in fields:
            if not isinstance(field, dict):
                continue
            fmt = field.setdefault("format", {})
            if not isinstance(fmt, dict):
                field["format"] = fmt = {}
            fmt["dynamicsFilter"] = True
            fmt["dynamicsFilterValue"] = str(value)
            fmt["autoSearchDefaultValue"] = False
            changed = True
    if not changed:
        raise UsageError(f"Filter unit {unit.get('unitId') or unit.get('unitName')} has no editable field config.")


def apply_dynamic_filter_plan(
    detail: dict[str, Any],
    plan: dict[int, str],
    strict_filter_count: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[int, str]]:
    updated = copy.deepcopy(detail)
    units = collect_leaf_filter_units(updated)
    if not units:
        raise UsageError(f"No public filter units found under relation {detail.get('unitId')}.")

    changes: list[dict[str, Any]] = []
    applied_plan: dict[int, str] = {}
    for one_based_index, value in sorted(plan.items()):
        if one_based_index < 1 or one_based_index > len(units):
            message = f"Requested filter index {one_based_index}, but only {len(units)} public filters were found."
            if strict_filter_count:
                raise UsageError(message)
            changes.append(
                {
                    "filter_index": one_based_index,
                    "skipped": True,
                    "message": message,
                    "before": None,
                    "after": None,
                }
            )
            continue
        unit = units[one_based_index - 1]
        before = public_filter_state(unit)
        set_dynamic_filter_value(unit, value)
        after = public_filter_state(unit)
        changes.append({"filter_index": one_based_index, "before": before, "after": after})
        applied_plan[one_based_index] = str(value)
    return updated, changes, applied_plan


def extract_schema_ids(schema: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in keys and value not in (None, ""):
                    text = str(value)
                    if text not in seen:
                        seen.add(text)
                        found.append(text)
                if isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(schema)
    return found


def build_publish_payload(config: dict[str, Any], version_description: str, html_id: str | None) -> dict[str, Any]:
    dashboard_html_json = config.get("dashboardHtmlJson")
    if not dashboard_html_json:
        raise UsageError("Dashboard config does not include dashboardHtmlJson; cannot publish.")
    schema = parse_dashboard_html(config)
    owner_list = config.get("ownerList") if isinstance(config.get("ownerList"), list) else []
    payload = {
        "dashboardId": config.get("dashboardId"),
        "dashboardName": config.get("dashboardName") or config.get("dashboardId"),
        "description": config.get("description") or "",
        "isGrayscale": 0,
        "grayscaleUsers": "",
        "versionDescription": version_description,
        "dashboardHtmlJson": dashboard_html_json,
        "saveUnitList": extract_schema_ids(schema, {"unitId"}),
        "clientInfo": config.get("clientInfo") or {"clientType": "pc"},
        "allUnitList": extract_schema_ids(schema, {"unitId", "filterUnitId"}),
        "jsPackages": config.get("jsPackages"),
        "owner": ",".join(str(item) for item in owner_list if str(item).strip()),
        "customHtmlFormat": config.get("customHtmlFormat") or {},
    }
    if html_id:
        payload["htmlId"] = html_id
    return payload


def find_public_filter_relation_ids(config: dict[str, Any]) -> list[str]:
    return [
        str(component["unit_id"])
        for component in extract_component_units(parse_dashboard_html(config))
        if str(component.get("unit_id") or "").startswith("public_filter_relation_")
    ]


def fetch_edit_config(page: Any, dashboard_id: str) -> dict[str, Any]:
    config = post_json(
        page,
        EDIT_DASHBOARD_CONFIG_API,
        {"dashboardId": dashboard_id, "isConfig": True, "versionId": "draft"},
    ).get("data")
    if not isinstance(config, dict):
        raise UsageError(f"Dashboard edit config not found for {dashboard_id}.")
    return config


def fetch_public_filter_detail(page: Any, dashboard_id: str, relation_id: str) -> dict[str, Any]:
    detail = post_json(
        page,
        EDIT_PUBLIC_FILTER_DETAIL_API,
        {"id": relation_id, "dashboardId": dashboard_id, "versionId": "draft"},
    ).get("data")
    if not isinstance(detail, dict):
        raise UsageError(f"Public filter relation detail not found for {relation_id}.")
    return detail


def update_public_filter_detail(
    page: Any,
    dashboard_id: str,
    html_id: str | None,
    detail: dict[str, Any],
) -> dict[str, Any]:
    payload = copy.deepcopy(detail)
    payload["dashboardId"] = dashboard_id
    payload["versionId"] = "draft"
    if html_id:
        payload["htmlId"] = html_id
    return post_json(page, EDIT_PUBLIC_FILTER_UPDATE_API, payload)


def publish_dashboard(page: Any, config: dict[str, Any], version_description: str, html_id: str | None) -> dict[str, Any]:
    dashboard_id = str(config.get("dashboardId") or "")
    if not dashboard_id:
        raise UsageError("Missing dashboardId in edit config.")
    # Mirrors the UI's warning check before clicking the publish confirmation.
    warn = post_json(page, EDIT_DASHBOARD_PUBLISH_WARN_API, {"id": dashboard_id})
    payload = build_publish_payload(config, version_description, html_id)
    response = post_json(page, EDIT_DASHBOARD_SAVE_AND_PUBLISH_API, payload)
    return {
        "publish_warn": warn.get("data"),
        "publish_status": response.get("status"),
        "publish_error_code": response.get("errorCode"),
        "publish_response_keys": sorted(response.keys()),
    }


def resolve_dashboard_targets(
    page: Any,
    folder_name: str,
    names: list[str],
    dashboard_ids: list[str],
) -> list[dict[str, str | None]]:
    targets: list[dict[str, str | None]] = []
    if names:
        records = collect_dashboard_records(fetch_dashboard_menu(page), folder_name)
        by_name = {record.name: record for record in records}
        missing = [name for name in names if name not in by_name]
        if missing:
            raise UsageError(f"Dashboard names not found under {folder_name}: {', '.join(missing)}")
        for name in names:
            record = by_name[name]
            targets.append({"dashboard_name": record.name, "dashboard_id": record.dashboard_id, "folder": folder_name})
    for dashboard_id in dashboard_ids:
        targets.append({"dashboard_name": None, "dashboard_id": dashboard_id, "folder": folder_name})
    if not targets:
        raise UsageError("No dashboards requested. Pass --name, --dashboard-id, or --target-set qingcheng-required.")
    seen: set[str] = set()
    deduped: list[dict[str, str | None]] = []
    for target in targets:
        dashboard_id = str(target.get("dashboard_id") or "")
        if not dashboard_id or dashboard_id in seen:
            continue
        seen.add(dashboard_id)
        deduped.append(target)
    return deduped


def edit_dashboard_public_filters(
    page: Any,
    args: Any,
    dashboard_id: str,
    dashboard_name: str | None,
    folder_name: str | None,
    plan: dict[int, str],
    artifacts_dir: Path,
) -> dict[str, Any]:
    if (
        not getattr(args, "dry_run", True)
        or getattr(args, "publish", False)
        or getattr(args, "confirm_publish", False)
    ):
        raise UsageError(
            "Legacy edit-public-filters is read-only. Use the stable-ID P3 plan/apply/publish commands."
        )
    edit_url = build_edit_url(dashboard_id, getattr(args, "html_id", None))
    open_edit_page(page, args, context=None, edit_url=edit_url)
    page.wait_for_timeout(getattr(args, "wait_ms", 3000))
    html_id = extract_loaded_html_id(page.url)

    before_config = fetch_edit_config(page, dashboard_id)
    relation_ids = find_public_filter_relation_ids(before_config)
    if not relation_ids:
        raise UsageError(f"No public filter relation component found in {dashboard_id}.")
    relation_id = relation_ids[0]
    before_detail = fetch_public_filter_detail(page, dashboard_id, relation_id)
    _updated_detail, changes, applied_plan = apply_dynamic_filter_plan(
        before_detail,
        plan,
        strict_filter_count=getattr(args, "strict_filter_count", False),
    )

    after_detail = fetch_public_filter_detail(page, dashboard_id, relation_id)
    after_units = collect_leaf_filter_units(after_detail)
    verification = [
        {"filter_index": index, **public_filter_state(after_units[index - 1])}
        for index in sorted(applied_plan)
        if 0 <= index - 1 < len(after_units)
    ]
    ok = bool(applied_plan)

    result = {
        "ok": ok,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dashboard_id": dashboard_id,
        "dashboard_name": before_config.get("dashboardName") or dashboard_name or dashboard_id,
        "folder": folder_name,
        "edit_url": edit_url,
        "loaded_url": page.url,
        "html_id": html_id,
        "relation_id": relation_id,
        "plan": plan,
        "applied_plan": applied_plan,
        "dry_run": bool(getattr(args, "dry_run", False)),
        "published": False,
        "changes": changes,
        "verification": verification,
        "update_response": None,
        "publish_response": None,
    }
    output_path = artifacts_dir / safe_filename(str(result["dashboard_name"])) / "edit_public_filters_summary.json"
    write_json(result, output_path)
    result["output_path"] = str(output_path)
    return result
