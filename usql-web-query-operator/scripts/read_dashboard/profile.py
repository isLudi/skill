"""Dashboard profiling and raw JSON persistence."""

from __future__ import annotations

import json
import hashlib
import time
from pathlib import Path
from typing import Any

from _shared.debug import save_debug_artifacts
from _shared.errors import UsageError

from .common import safe_filename, write_json
from .constants import (
    DASHBOARD_CONFIG_API,
    DASHBOARD_MARKET_URL,
    PUBLIC_FILTER_DETAIL_API,
    UNIT_DETAIL_API,
    UNIT_VALUE_API,
)
from .models import DashboardProfileSummary, DashboardRecord
from .value_health import ValueProbePolicy, probe_value_targets


def dashboard_url(dashboard_id: str) -> str:
    return f"{DASHBOARD_MARKET_URL}?id={dashboard_id}&sourceType=1"


def post_json(
    page: Any,
    url: str,
    payload: dict[str, Any],
    timeout_ms: int = 45_000,
) -> dict[str, Any]:
    response = page.request.post(url, data=payload, timeout=timeout_ms)
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
        unit_config = ((node.get("relationUnit") or {}).get("unitConfig") or {})
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


def profile_content_sha256(profile: dict[str, Any]) -> str:
    payload = {
        key: profile.get(key)
        for key in (
            "dashboard_id",
            "dashboard_name",
            "config_summary",
            "components",
            "unit_details",
            "public_filters",
        )
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _analytic_targets(profile: dict[str, Any]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    components = {
        str(item.get("unit_id") or ""): item
        for item in profile.get("components") or []
        if isinstance(item, dict)
    }
    for unit_id, detail in (profile.get("unit_details") or {}).items():
        if not isinstance(detail, dict):
            continue
        if str(detail.get("unit_type") or "") in {"u_text", "u_material"}:
            continue
        component = components.get(str(unit_id)) or {}
        targets.append(
            {
                "unit_id": str(unit_id),
                "page_size": detail.get("page_size") or component.get("page_size"),
            }
        )
    return targets


def probe_profile_values(
    page: Any,
    profile: dict[str, Any],
    policy: ValueProbePolicy,
) -> dict[str, Any]:
    dashboard_id = str(profile.get("dashboard_id") or "")
    targets = _analytic_targets(profile)

    def fetch_value(target: dict[str, Any], timeout_ms: int) -> dict[str, Any]:
        unit_id = str(target["unit_id"])
        payload = post_json(
            page,
            UNIT_VALUE_API,
            default_unit_value_payload(unit_id, target.get("page_size")),
            timeout_ms=timeout_ms,
        )
        return summarize_unit_value(unit_id, payload)

    probe = probe_value_targets(
        dashboard_id=dashboard_id,
        targets=targets,
        fetch_value=fetch_value,
        policy=policy,
    )
    values = list(probe["unit_values"].values())
    data_ready_count = sum(1 for item in values if item.get("status") == "data_ready")
    refresh_validation = {
        "mode": "value_health",
        "status": "complete" if not probe["errors"] else "incomplete",
        "unit_count": len(profile.get("components") or []),
        "value_target_count": len(targets),
        "value_unit_count": len(values),
        "data_ready_unit_count": data_ready_count,
        "analytic_unit_count": len(targets),
        "analytic_data_ready_unit_count": data_ready_count,
        "error_count": len(probe["errors"]),
        "all_value_units_ready": bool(targets) and data_ready_count == len(targets),
        "all_analytic_units_ready": bool(targets) and data_ready_count == len(targets),
        "attempted_request_count": probe["attempted_request_count"],
        "cache_hit_count": probe["cache_hit_count"],
        "elapsed_ms": probe["elapsed_ms"],
        "deadline_exceeded": probe["deadline_exceeded"],
        "policy": probe["policy"],
    }
    return {
        "schema_version": "1.0.0",
        "artifact_type": "DashboardValueHealth",
        "ok": not probe["errors"],
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dashboard_id": dashboard_id,
        "dashboard_name": profile.get("dashboard_name"),
        "source_profile_sha256": profile.get("profile_sha256") or profile_content_sha256(profile),
        "unit_values": probe["unit_values"],
        "refresh_validation": refresh_validation,
        "errors": probe["errors"],
    }


def profile_dashboard(
    page: Any,
    dashboard_id: str,
    dashboard_name: str | None,
    folder_name: str | None,
    wait_ms: int,
    artifacts_dir: Path,
    debug_artifacts: bool,
    include_values: bool = True,
    value_policy: ValueProbePolicy | None = None,
) -> dict[str, Any]:
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
        except Exception as exc:  # noqa: BLE001
            errors.append({"unit_id": unit_id, "message": str(exc)})

    dashboard_name = str(config.get("dashboardName") or dashboard_name or dashboard_id)
    analytic_unit_ids = [
        unit_id
        for unit_id, detail in details.items()
        if str(detail.get("unit_type") or "") not in {"u_text", "u_material"}
    ]
    profile = {
        "ok": True,
        "profile_mode": "full" if include_values else "config_only",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_folder": folder_name,
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
        "unit_values": {},
        "refresh_validation": {
            "mode": "not_run",
            "status": "not_run",
            "unit_count": len(component_units),
            "value_target_count": len(analytic_unit_ids),
            "value_unit_count": 0,
            "data_ready_unit_count": 0,
            "analytic_unit_count": len(analytic_unit_ids),
            "analytic_data_ready_unit_count": 0,
            "error_count": 0,
            "all_value_units_ready": None,
            "all_analytic_units_ready": None,
        },
        "errors": errors,
    }
    profile["profile_sha256"] = profile_content_sha256(profile)
    if include_values:
        health = probe_profile_values(page, profile, value_policy or ValueProbePolicy())
        profile["unit_values"] = health["unit_values"]
        profile["refresh_validation"] = health["refresh_validation"]
        profile["value_health"] = {
            "artifact_type": health["artifact_type"],
            "source_profile_sha256": health["source_profile_sha256"],
        }
        profile["errors"].extend(health["errors"])
    return profile


def build_error_profile(
    dashboard_id: str,
    dashboard_name: str,
    folder_name: str | None,
    message: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_folder": folder_name,
        "dashboard_id": dashboard_id,
        "dashboard_name": dashboard_name,
        "message": message,
    }


def build_profile_summary(profile: dict[str, Any], output_path: Path) -> DashboardProfileSummary:
    refresh = profile.get("refresh_validation") or {}
    return DashboardProfileSummary(
        ok=bool(profile.get("ok", True)),
        dashboard_name=str(profile.get("dashboard_name") or profile.get("dashboard_id") or ""),
        dashboard_id=str(profile.get("dashboard_id") or ""),
        output_path=str(output_path),
        rendered=bool(profile.get("rendered")),
        unit_count=int(refresh.get("unit_count") or 0),
        value_unit_count=int(refresh.get("value_unit_count") or 0),
        data_ready_unit_count=int(refresh.get("data_ready_unit_count") or 0),
        message=str(profile.get("message") or ("Dashboard profile finished." if profile.get("ok", True) else "Dashboard profile failed.")),
    )


def profile_records(
    page: Any,
    folder_name: str,
    records: list[DashboardRecord],
    output_dir: Path,
    dashboard_wait_ms: int,
    debug_artifacts: bool,
    include_values: bool = True,
    value_policy: ValueProbePolicy | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    for record in records:
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
                folder_name=folder_name,
                wait_ms=dashboard_wait_ms,
                artifacts_dir=profile_dir,
                debug_artifacts=debug_artifacts,
                include_values=include_values,
                value_policy=value_policy,
            )
            write_json(profile, profile_path)
            artifacts.append({"record": record, "profile": profile, "profile_path": profile_path})
            results.append(
                {
                    "ok": True,
                    "folder": folder_name,
                    "dashboard_name": record.name,
                    "dashboard_id": record.dashboard_id,
                    "output_path": str(profile_path),
                    "rendered": profile["rendered"],
                    **profile["refresh_validation"],
                }
            )
        except Exception as exc:  # noqa: BLE001
            error_profile = build_error_profile(record.dashboard_id, record.name, folder_name, str(exc))
            write_json(error_profile, profile_path)
            artifacts.append({"record": record, "profile": error_profile, "profile_path": profile_path})
            results.append(
                {
                    "ok": False,
                    "folder": folder_name,
                    "dashboard_name": record.name,
                    "dashboard_id": record.dashboard_id,
                    "output_path": str(profile_path),
                    "message": str(exc),
                }
            )
    return results, artifacts
