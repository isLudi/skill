"""Edit and publish Taitan public-filter settings."""

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
    updated_detail, changes, applied_plan = apply_dynamic_filter_plan(
        before_detail,
        plan,
        strict_filter_count=getattr(args, "strict_filter_count", False),
    )

    update_response: dict[str, Any] | None = None
    publish_response: dict[str, Any] | None = None
    if not getattr(args, "dry_run", False):
        update_response = update_public_filter_detail(page, dashboard_id, html_id, updated_detail)
        after_config = fetch_edit_config(page, dashboard_id)
        if getattr(args, "publish", True):
            publish_response = publish_dashboard(page, after_config, args.version_description, html_id)

    after_detail = fetch_public_filter_detail(page, dashboard_id, relation_id)
    after_units = collect_leaf_filter_units(after_detail)
    verification = [
        {"filter_index": index, **public_filter_state(after_units[index - 1])}
        for index in sorted(applied_plan)
        if 0 <= index - 1 < len(after_units)
    ]
    if getattr(args, "dry_run", False):
        ok = bool(applied_plan)
    else:
        ok = bool(applied_plan) and all(
            str(item.get("dynamics_filter_value")) == str(applied_plan[item["filter_index"]])
            for item in verification
        )
    if getattr(args, "publish", True) and not getattr(args, "dry_run", False):
        ok = ok and bool(publish_response and publish_response.get("publish_status") == "success")

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
        "published": bool(getattr(args, "publish", True) and not getattr(args, "dry_run", False)),
        "changes": changes,
        "verification": verification,
        "update_response": update_response,
        "publish_response": publish_response,
    }
    output_path = artifacts_dir / safe_filename(str(result["dashboard_name"])) / "edit_public_filters_summary.json"
    write_json(result, output_path)
    result["output_path"] = str(output_path)
    return result
