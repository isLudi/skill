#!/usr/bin/env python3
"""Read Baijia dashboard metadata and dashboard pages through Playwright.

This script is intentionally separate from usql_web_query.py:
- usql_web_query.py operates SQL取数 and result downloads.
- read_dashboard.py operates 自助BI dashboard folders and dashboard pages.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _shared.auth import ensure_authenticated, fill_login_if_present
from _shared.browser import import_playwright, launch_browser, launch_context
from _shared.config import DEFAULT_ARTIFACTS, DEFAULT_BROWSER_CHANNEL, DEFAULT_ENV_FILE, DEFAULT_STATE
from _shared.debug import save_debug_artifacts
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir


DASHBOARD_MARKET_URL = "https://uanalysis.baijia.com/dashboard-market"
DASHBOARD_MENU_API = "https://uanalysis.baijia.com/uanalysis-intelligence/data/menu/manage"
DASHBOARD_CONFIG_API = "https://uanalysis.baijia.com/uanalysis-intelligence/config/dashBoard"
UNIT_DETAIL_API = "https://uanalysis.baijia.com/uanalysis-intelligence/value/unit/consumer/detail"
PUBLIC_FILTER_DETAIL_API = "https://uanalysis.baijia.com/uanalysis-intelligence/value/public/unit/relation/detail"
UNIT_VALUE_API = "https://uanalysis.baijia.com/uanalysis-intelligence/value/unit"


@dataclass
class DashboardRecord:
    name: str
    dashboard_id: str | None
    numeric_id: str | None
    file_value: str | None
    parent_id: str | None
    owner: str | None
    folder_path: str | None
    href: str | None = None
    source: str = "menu_manage_api"


@dataclass
class DashboardScanSummary:
    ok: bool
    folder: str
    count: int
    output_path: str
    records: list[DashboardRecord]
    message: str


@dataclass
class DashboardProfileSummary:
    ok: bool
    dashboard_name: str
    dashboard_id: str
    output_path: str
    rendered: bool
    unit_count: int
    value_unit_count: int
    data_ready_unit_count: int
    message: str


def extract_numeric_id(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"(\d{6,})", value)
    return match.group(1) if match else None


def unique_dashboard_records(records: list[DashboardRecord]) -> list[DashboardRecord]:
    seen: set[tuple[str, str | None, str | None]] = set()
    result: list[DashboardRecord] = []
    for record in records:
        key = (record.name, record.dashboard_id, record.folder_path)
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def _node_name(node: dict[str, Any]) -> str:
    return str(node.get("name") or "").strip()


def _is_dashboard_file(node: dict[str, Any]) -> bool:
    file_type = str(node.get("fileType") or "")
    value = str(node.get("fileValue") or node.get("id") or "")
    return node.get("isFile") == 1 or "FILE" in file_type or value.startswith("dashboard_")


def _iter_named_menu_nodes(obj: Any, path: list[str] | None = None):
    path = path or []
    if isinstance(obj, dict):
        name = _node_name(obj)
        next_path = path + [name] if name else path
        if name:
            yield obj, next_path
        for child in obj.get("children") or []:
            yield from _iter_named_menu_nodes(child, next_path)
        for key, value in obj.items():
            if key == "children":
                continue
            if isinstance(value, (dict, list)):
                yield from _iter_named_menu_nodes(value, path)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_named_menu_nodes(item, path)


def _record_from_menu_node(node: dict[str, Any], path: list[str]) -> DashboardRecord:
    file_value = str(node.get("fileValue") or "").strip() or None
    dashboard_id = str(node.get("id") or file_value or node.get("key") or "").strip() or None
    if file_value and file_value.startswith("dashboard_"):
        dashboard_id = file_value
    return DashboardRecord(
        name=_node_name(node),
        dashboard_id=dashboard_id,
        numeric_id=extract_numeric_id(file_value or dashboard_id),
        file_value=file_value,
        parent_id=str(node.get("parentId") or "").strip() or None,
        owner=str(node.get("owner") or "").strip() or None,
        folder_path="/".join(path[:-1]) if len(path) > 1 else None,
    )


def fetch_dashboard_menu(page: Any) -> dict[str, Any]:
    response = page.request.post(
        DASHBOARD_MENU_API,
        data={"menuType": "HOME_AND_DASHBOARD"},
        timeout=30_000,
    )
    if response.status >= 400:
        raise UsageError(f"Dashboard menu API failed with HTTP {response.status}.")
    data = response.json()
    if not isinstance(data, dict):
        raise UsageError("Dashboard menu API returned an unexpected payload.")
    if data.get("status") not in (None, "success"):
        raise UsageError(f"Dashboard menu API returned non-success status: {data.get('status')}")
    return data


def collect_dashboard_records(menu_data: dict[str, Any], folder_name: str) -> list[DashboardRecord]:
    records: list[DashboardRecord] = []
    for folder_node, folder_path in _iter_named_menu_nodes(menu_data):
        if _node_name(folder_node) != folder_name:
            continue
        for node, path in _iter_named_menu_nodes(folder_node.get("children") or [], folder_path):
            if _is_dashboard_file(node):
                records.append(_record_from_menu_node(node, path))
    return unique_dashboard_records(records)


def dashboard_url(dashboard_id: str) -> str:
    return f"{DASHBOARD_MARKET_URL}?id={dashboard_id}&sourceType=1"


def post_json(page: Any, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = page.request.post(url, data=payload, timeout=45_000)
    if response.status >= 400:
        raise UsageError(f"API failed with HTTP {response.status}: {url}")
    data = response.json()
    if not isinstance(data, dict):
        raise UsageError(f"API returned an unexpected payload: {url}")
    if data.get("status") not in (None, "success"):
        raise UsageError(f"API returned non-success status {data.get('status')}: {url}")
    return data


def parse_dashboard_html(config_data: dict[str, Any]) -> dict[str, Any]:
    raw = config_data.get("dashboardHtmlJson") or "{}"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _walk_dicts(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk_dicts(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_dicts(item)


def extract_component_units(dashboard_html: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in _walk_dicts(dashboard_html.get("componentsTree") or []):
        settings = node.get("settings")
        if not isinstance(settings, dict):
            props = node.get("props")
            settings = props.get("settings") if isinstance(props, dict) else None
        if not isinstance(settings, dict):
            continue
        unit_id = settings.get("unitId")
        if not unit_id or unit_id in seen:
            continue
        seen.add(unit_id)
        records.append(
            {
                "node_id": node.get("id"),
                "node_component": node.get("componentName"),
                "node_title": node.get("title"),
                "unit_id": unit_id,
                "component_type": settings.get("componentType"),
                "component_name": settings.get("componentName"),
                "is_show_component_name": settings.get("isShowComponentName"),
                "is_show_update_time": settings.get("isShowUpdateTime"),
                "show_pagination": settings.get("showPagination"),
                "page_size": settings.get("pageSize"),
                "show_download_btn": settings.get("showDownloadBtn"),
                "is_total": settings.get("isTotal"),
                "is_open": settings.get("isOpen"),
                "refresh_key": settings.get("refreshKey"),
            }
        )
    return records


def summarize_field(field: dict[str, Any]) -> dict[str, Any]:
    fmt = field.get("format") if isinstance(field.get("format"), dict) else {}
    return {
        "field_id": field.get("fieldId") or field.get("paramId"),
        "name": field.get("name") or field.get("showName") or fmt.get("displayFilterName"),
        "show_name": field.get("showName"),
        "field_type": field.get("fieldType"),
        "data_type": fmt.get("dataType"),
        "condition": fmt.get("condition"),
        "filter_value": fmt.get("filterValue"),
        "default_filter_value": fmt.get("defaultFilterValue"),
        "pre_filter_values": (fmt.get("preFilterValueList") or [])[:20],
        "pre_filter_value_count": len(fmt.get("preFilterValueList") or []),
        "pre_filter_task_id": fmt.get("preFilterTaskId"),
        "is_select_all": fmt.get("isSelectAll"),
        "multiple_filter": fmt.get("multipleFilter"),
        "dynamics_filter": fmt.get("dynamicsFilter"),
        "dynamics_filter_value": fmt.get("dynamicsFilterValue"),
    }


def summarize_unit_detail(detail: dict[str, Any]) -> dict[str, Any]:
    fmt = detail.get("format") if isinstance(detail.get("format"), dict) else {}
    return {
        "unit_id": detail.get("unitId"),
        "unit_name": detail.get("unitName"),
        "unit_type": detail.get("unitType"),
        "model_id": detail.get("modelId"),
        "model_name": detail.get("modelName"),
        "dashboard_model": detail.get("dashboardModel"),
        "description": detail.get("description"),
        "page_size": fmt.get("pageSize"),
        "is_download": fmt.get("isDownload"),
        "is_total": fmt.get("isTotal"),
        "is_open": fmt.get("isOpen"),
        "display_metric_order": fmt.get("fieldMeasureNameSortList") or [],
        "switch_groups": fmt.get("switchGroups") or [],
        "display_list_count": len(fmt.get("displayList") or []),
        "dimension_fields": [summarize_field(item) for item in detail.get("unitDimensionList") or []],
        "column_dimension_fields": [summarize_field(item) for item in detail.get("unitColumnDimensionList") or []],
        "measure_fields": [summarize_field(item) for item in detail.get("unitMeasureList") or []],
        "aide_measure_fields": [summarize_field(item) for item in detail.get("unitAideMeasureList") or []],
        "filter_fields": [summarize_field(item) for item in detail.get("unitFilterList") or []],
    }


def summarize_public_filter_detail(detail: dict[str, Any]) -> dict[str, Any]:
    filters: list[dict[str, Any]] = []
    seen_filter_ids: set[str] = set()
    for node in _walk_dicts(detail):
        if not isinstance(node, dict):
            continue
        unit_id = node.get("unitId")
        if (
            not unit_id
            or not str(unit_id).startswith("public_filter_")
            or str(unit_id).startswith("public_filter_relation_")
            or unit_id in seen_filter_ids
        ):
            continue
        seen_filter_ids.add(str(unit_id))
        unit_config = (((node.get("relationUnit") or {}).get("unitConfig") or {}))
        dimensions = unit_config.get("unitDimensionList") or []
        filter_params = (node.get("relationUnit") or {}).get("filterUnitParamList") or []
        filters.append(
            {
                "unit_id": unit_id,
                "unit_name": node.get("unitName"),
                "dashboard_units": (node.get("relationUnit") or {}).get("dashboardUnitList") or [],
                "fields": [summarize_field(item) for item in dimensions],
                "filter_params": [summarize_field(item) for item in filter_params],
            }
        )
    return {
        "unit_id": detail.get("unitId"),
        "unit_name": detail.get("unitName"),
        "unit_type": detail.get("unitType"),
        "relation_type": detail.get("relationType"),
        "filters": filters,
    }


def summarize_unit_value(unit_id: str, value_payload: dict[str, Any]) -> dict[str, Any]:
    data = value_payload.get("data")
    unit_value = data.get(unit_id) if isinstance(data, dict) else None
    if not isinstance(unit_value, dict):
        return {
            "unit_id": unit_id,
            "status": "no_unit_payload",
            "raw_status": value_payload.get("status"),
            "error_code": value_payload.get("errorCode"),
        }

    rows = unit_value.get("data") if isinstance(unit_value.get("data"), list) else []
    nested_rows = unit_value.get("nestedData") if isinstance(unit_value.get("nestedData"), list) else []
    series = unit_value.get("series") if isinstance(unit_value.get("series"), list) else []
    x_axis = unit_value.get("xAxis") if isinstance(unit_value.get("xAxis"), dict) else {}
    series_points = 0
    for item in series:
        if isinstance(item, dict) and isinstance(item.get("data"), list):
            series_points += len(item["data"])
    title = unit_value.get("title") if isinstance(unit_value.get("title"), list) else []
    column_title = unit_value.get("columnTitle") if isinstance(unit_value.get("columnTitle"), list) else []
    total_data = unit_value.get("totalData") if isinstance(unit_value.get("totalData"), dict) else {}
    page = unit_value.get("page") if isinstance(unit_value.get("page"), dict) else {}
    data_ready = bool(rows or nested_rows or total_data or series_points or str(unit_value.get("textContent") or "").strip())
    return {
        "unit_id": unit_id,
        "unit_name": unit_value.get("unitName"),
        "status": "data_ready" if data_ready else "loaded_empty",
        "task_ids": unit_value.get("taskIds"),
        "total_task_id": unit_value.get("totalTaskId"),
        "ym_task_ids": unit_value.get("ymTaskIds"),
        "title_fields": [summarize_field(item) for item in title],
        "column_title_fields": [summarize_field(item) for item in column_title],
        "title_count": len(title),
        "column_title_count": len(column_title),
        "data_row_count": len(rows),
        "nested_data_row_count": len(nested_rows),
        "series_count": len(series),
        "series_point_count": series_points,
        "series_names": [item.get("name") for item in series if isinstance(item, dict)],
        "x_axis_field_id": x_axis.get("filedId") or x_axis.get("fieldId"),
        "x_axis_count": len(x_axis.get("data") or []) if isinstance(x_axis.get("data"), list) else 0,
        "first_row_keys": list(rows[0].keys()) if rows and isinstance(rows[0], dict) else [],
        "total_data_keys": list(total_data.keys()),
        "page": page,
        "has_more": unit_value.get("hasMore"),
        "text_content_length": len(str(unit_value.get("textContent") or "")),
    }


def default_unit_value_payload(unit_id: str, page_size: int | None) -> dict[str, Any]:
    return {
        "id": unit_id,
        "pivotFilterValue": [],
        "filterList": [],
        "page": {
            "pageNo": 1,
            "pageSize": page_size or 200,
            "totalSize": 0,
            "hasMore": True,
        },
        "publicFilterList": [],
        "unitRelationFilterList": [],
        "title": [],
        "displayDataList": [],
        "columnTitle": [],
        "paramPublicFilterList": None,
        "isConfig": False,
    }


def fetch_dashboard_config(page: Any, dashboard_id: str) -> dict[str, Any]:
    payload = post_json(page, DASHBOARD_CONFIG_API, {"dashboardId": dashboard_id, "isConfig": False})
    config = payload.get("data")
    if not isinstance(config, dict):
        raise UsageError(f"Dashboard config not found for {dashboard_id}.")
    return config


def fetch_unit_detail(page: Any, unit_id: str) -> dict[str, Any]:
    if unit_id.startswith("public_filter_relation_"):
        payload = post_json(page, PUBLIC_FILTER_DETAIL_API, {"id": unit_id, "isConfig": False})
    else:
        payload = post_json(page, UNIT_DETAIL_API, {"id": unit_id, "isConfig": False})
    detail = payload.get("data")
    if not isinstance(detail, dict):
        raise UsageError(f"Unit detail not found for {unit_id}.")
    return detail


def profile_dashboard(page: Any, dashboard_id: str, dashboard_name: str | None, wait_ms: int, artifacts_dir: Path, debug_artifacts: bool) -> dict[str, Any]:
    opened_url = dashboard_url(dashboard_id)
    page.goto(opened_url, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(wait_ms)
    body_text = page.locator("body").inner_text(timeout=10_000)
    if debug_artifacts:
        save_debug_artifacts(page, artifacts_dir, f"profile_{dashboard_id}")

    config = fetch_dashboard_config(page, dashboard_id)
    dashboard_html = parse_dashboard_html(config)
    component_units = extract_component_units(dashboard_html)

    details: dict[str, Any] = {}
    public_filters: dict[str, Any] = {}
    value_summaries: dict[str, Any] = {}
    errors: list[dict[str, str]] = []

    for component in component_units:
        unit_id = str(component["unit_id"])
        try:
            detail = fetch_unit_detail(page, unit_id)
            if unit_id.startswith("public_filter_relation_"):
                public_filters[unit_id] = summarize_public_filter_detail(detail)
                continue
            detail_summary = summarize_unit_detail(detail)
            details[unit_id] = detail_summary
            value_payload = post_json(
                page,
                UNIT_VALUE_API,
                default_unit_value_payload(unit_id, detail_summary.get("page_size") or component.get("page_size")),
            )
            value_summaries[unit_id] = summarize_unit_value(unit_id, value_payload)
        except Exception as exc:
            errors.append({"unit_id": unit_id, "message": str(exc)})

    dashboard_name = str(config.get("dashboardName") or dashboard_name or dashboard_id)
    value_units = list(value_summaries.values())
    data_ready_count = sum(1 for item in value_units if item.get("status") == "data_ready")
    analytic_unit_ids = [
        unit_id
        for unit_id, detail in details.items()
        if str(detail.get("unit_type") or "") not in {"u_text", "u_material"}
    ]
    analytic_ready_count = sum(
        1
        for unit_id in analytic_unit_ids
        if value_summaries.get(unit_id, {}).get("status") == "data_ready"
    )
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dashboard_id": dashboard_id,
        "dashboard_name": dashboard_name,
        "open_url": opened_url,
        "loaded_url": page.url,
        "page_title": page.title(),
        "rendered": dashboard_name in body_text or str(config.get("dashboardName") or "") in body_text,
        "body_text_head": body_text[:2000],
        "config_summary": {
            "dashboard_name": config.get("dashboardName"),
            "dashboard_level": config.get("dashboardLevel"),
            "package_version": config.get("packageVersion"),
            "owner_list": config.get("ownerList") or [],
            "component_package_count": len(dashboard_html.get("componentsMap") or []),
            "root_component_count": len(dashboard_html.get("componentsTree") or []),
        },
        "components": component_units,
        "unit_details": details,
        "public_filters": public_filters,
        "unit_values": value_summaries,
        "refresh_validation": {
            "unit_count": len(component_units),
            "value_unit_count": len(value_units),
            "data_ready_unit_count": data_ready_count,
            "analytic_unit_count": len(analytic_unit_ids),
            "analytic_data_ready_unit_count": analytic_ready_count,
            "error_count": len(errors),
            "all_value_units_ready": bool(value_units) and data_ready_count == len(value_units),
            "all_analytic_units_ready": bool(analytic_unit_ids) and analytic_ready_count == len(analytic_unit_ids),
        },
        "errors": errors,
    }


def cmd_scan_folder(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_path = args.output or (artifacts_dir / "dashboards.json")

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            page.goto(DASHBOARD_MARKET_URL, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(args.wait_ms)
            records = collect_dashboard_records(fetch_dashboard_menu(page), args.folder)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "scan_folder")
            summary = DashboardScanSummary(
                ok=True,
                folder=args.folder,
                count=len(records),
                output_path=str(output_path),
                records=records,
                message="Dashboard folder scan finished.",
            )
        except Exception as exc:
            if args.debug_artifacts:
                try:
                    save_debug_artifacts(page, artifacts_dir, "scan_folder_error")
                except Exception:
                    pass
            summary = DashboardScanSummary(
                ok=False,
                folder=args.folder,
                count=0,
                output_path=str(output_path),
                records=[],
                message=str(exc),
            )
        finally:
            browser.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        "ok": summary.ok,
        "folder": summary.folder,
        "count": summary.count,
        "output_path": summary.output_path,
        "message": summary.message,
        "records": [record.__dict__ for record in summary.records],
    }
    output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output_data, ensure_ascii=False, indent=2))
    return 0 if summary.ok else 1


def write_profile(profile: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_profile_dashboard(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    dashboard_id = args.dashboard_id
    output_path = args.output or (artifacts_dir / f"{dashboard_id}_profile.json")

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            profile = profile_dashboard(
                page=page,
                dashboard_id=dashboard_id,
                dashboard_name=args.dashboard_name,
                wait_ms=args.wait_ms,
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
            )
            write_profile(profile, output_path)
            summary = DashboardProfileSummary(
                ok=True,
                dashboard_name=profile["dashboard_name"],
                dashboard_id=dashboard_id,
                output_path=str(output_path),
                rendered=bool(profile["rendered"]),
                unit_count=profile["refresh_validation"]["unit_count"],
                value_unit_count=profile["refresh_validation"]["value_unit_count"],
                data_ready_unit_count=profile["refresh_validation"]["data_ready_unit_count"],
                message="Dashboard profile finished.",
            )
        except Exception as exc:
            profile = {
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dashboard_id": dashboard_id,
                "dashboard_name": args.dashboard_name or dashboard_id,
                "ok": False,
                "message": str(exc),
            }
            write_profile(profile, output_path)
            summary = DashboardProfileSummary(
                ok=False,
                dashboard_name=args.dashboard_name or dashboard_id,
                dashboard_id=dashboard_id,
                output_path=str(output_path),
                rendered=False,
                unit_count=0,
                value_unit_count=0,
                data_ready_unit_count=0,
                message=str(exc),
            )
        finally:
            browser.close()

    print(json.dumps(summary.__dict__, ensure_ascii=False, indent=2))
    return 0 if summary.ok else 1


def parse_dashboard_names(values: list[str] | None) -> list[str]:
    if not values:
        return []
    names: list[str] = []
    for value in values:
        for item in re.split(r"[|,]", value):
            item = item.strip()
            if item:
                names.append(item)
    return names


def cmd_profile_folder(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_dir = args.output_dir or artifacts_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    wanted_names = set(parse_dashboard_names(args.names))

    results: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            page.goto(DASHBOARD_MARKET_URL, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(args.wait_ms)
            records = collect_dashboard_records(fetch_dashboard_menu(page), args.folder)
            targets = [record for record in records if not wanted_names or record.name in wanted_names]
            missing = sorted(wanted_names - {record.name for record in targets})
            if missing:
                results.extend({"ok": False, "dashboard_name": name, "message": "Dashboard name not found in folder"} for name in missing)

            for record in targets:
                if not record.dashboard_id:
                    results.append({"ok": False, "dashboard_name": record.name, "message": "Missing dashboard_id"})
                    continue
                profile_dir = output_dir / safe_filename(record.name)
                profile_dir.mkdir(parents=True, exist_ok=True)
                profile_path = profile_dir / "profile.json"
                try:
                    profile = profile_dashboard(
                        page=page,
                        dashboard_id=record.dashboard_id,
                        dashboard_name=record.name,
                        wait_ms=args.dashboard_wait_ms,
                        artifacts_dir=profile_dir,
                        debug_artifacts=args.debug_artifacts,
                    )
                    write_profile(profile, profile_path)
                    profiles.append(profile)
                    results.append(
                        {
                            "ok": True,
                            "dashboard_name": record.name,
                            "dashboard_id": record.dashboard_id,
                            "output_path": str(profile_path),
                            "rendered": profile["rendered"],
                            **profile["refresh_validation"],
                        }
                    )
                except Exception as exc:
                    error_profile = {
                        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "dashboard_id": record.dashboard_id,
                        "dashboard_name": record.name,
                        "ok": False,
                        "message": str(exc),
                    }
                    write_profile(error_profile, profile_path)
                    results.append(
                        {
                            "ok": False,
                            "dashboard_name": record.name,
                            "dashboard_id": record.dashboard_id,
                            "output_path": str(profile_path),
                            "message": str(exc),
                        }
                    )
        finally:
            browser.close()

    consolidated = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "folder": args.folder,
        "output_dir": str(output_dir),
        "target_count": len(results),
        "ok_count": sum(1 for item in results if item.get("ok")),
        "results": results,
        "profiles": profiles,
    }
    consolidated_path = output_dir / "profiles_consolidated.json"
    write_profile(consolidated, consolidated_path)
    print(json.dumps({k: v for k, v in consolidated.items() if k != "profiles"}, ensure_ascii=False, indent=2))
    return 0 if all(item.get("ok") for item in results) else 1


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\\\|?*\\x00-\\x1f]', "_", value).strip(" .")
    return cleaned or "dashboard"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan-folder", help="Scan dashboard names and IDs under a dashboard folder.")
    scan.add_argument("--folder", default="市场顾问数据")
    scan.add_argument("--output", type=Path, default=None)
    scan.add_argument("--headed", action="store_true", help="Show browser window.")
    scan.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    scan.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    scan.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    scan.add_argument("--username", default=None)
    scan.add_argument("--password", default=None)
    scan.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    scan.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    scan.add_argument("--wait-ms", type=int, default=3000, help="Extra wait for lazy BI page refresh.")
    scan.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under the runtime artifacts directory.")
    scan.set_defaults(func=cmd_scan_folder)

    profile = subparsers.add_parser("profile-dashboard", help="Open one dashboard and store its component/filter/value structure.")
    profile.add_argument("--dashboard-id", required=True)
    profile.add_argument("--dashboard-name", default=None)
    profile.add_argument("--output", type=Path, default=None)
    profile.add_argument("--headed", action="store_true", help="Show browser window.")
    profile.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    profile.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    profile.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    profile.add_argument("--username", default=None)
    profile.add_argument("--password", default=None)
    profile.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    profile.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    profile.add_argument("--wait-ms", type=int, default=45_000, help="Wait after opening the dashboard so its data can refresh.")
    profile.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under the runtime artifacts directory.")
    profile.set_defaults(func=cmd_profile_dashboard)

    profile_folder = subparsers.add_parser("profile-folder", help="Profile selected dashboards under a folder.")
    profile_folder.add_argument("--folder", default="市场顾问数据")
    profile_folder.add_argument("--names", action="append", help="Dashboard names to profile. Repeat or separate with | or comma. Omit to profile all.")
    profile_folder.add_argument("--output-dir", type=Path, default=None)
    profile_folder.add_argument("--headed", action="store_true", help="Show browser window.")
    profile_folder.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    profile_folder.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    profile_folder.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    profile_folder.add_argument("--username", default=None)
    profile_folder.add_argument("--password", default=None)
    profile_folder.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    profile_folder.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    profile_folder.add_argument("--wait-ms", type=int, default=5_000, help="Wait after opening the BI page before scanning the folder.")
    profile_folder.add_argument("--dashboard-wait-ms", type=int, default=45_000, help="Wait after opening each dashboard so its data can refresh.")
    profile_folder.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under each dashboard profile directory.")
    profile_folder.set_defaults(func=cmd_profile_folder)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
