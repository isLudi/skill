"""Verified reversible dashboard draft adapters for P4A probes and P4B Apply."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

from _shared.errors import UsageError

from .edit_profile import fetch_edit_dashboard_config, fetch_edit_unit_detail
from .filter_edit import fetch_public_filter_detail, find_public_filter_unit
from .profile import post_json
from .write_capabilities import request_key_paths


API_ROOT = "https://udata.baijia.com/uanalysis-intelligence"
SAVE_DASHBOARD_HTML_API = f"{API_ROOT}/config/save/dashboardHtml"
UPDATE_UNIT_API = f"{API_ROOT}/config/update/unit"
CUSTOM_COLUMN_LIST_API = f"{API_ROOT}/model/customized/column/list"
CUSTOM_COLUMN_SAVE_API = f"{API_ROOT}/model/customized/column/saveAndUpdate"
PUBLIC_FILTER_UPDATE_API = f"{API_ROOT}/config/update/public/relation/unit"

LAYOUT_KEYS = ("i", "x", "y", "w", "h", "minW", "minH", "maxW", "maxH", "static")
FILTER_STATE_KEYS = (
    "dynamicsFilter",
    "dynamicsFilterValue",
    "autoSearchDefaultValue",
    "filterValue",
    "defaultFilterValue",
    "preFilterValueList",
    "preFilterTaskId",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def assert_expected_state(actual_state: Any, expected_sha256: str, label: str) -> None:
    actual_sha256 = canonical_sha256(actual_state)
    if actual_sha256 != expected_sha256:
        raise UsageError(
            f"{label} drifted: expected {expected_sha256}, got {actual_sha256}; no write was attempted."
        )


def _extract_key_values(value: Any, keys: set[str]) -> list[str]:
    result: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key in keys and isinstance(child, str) and child and child not in result:
                    result.append(child)
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return result


def find_layout_item(schema: dict[str, Any], node_id: str) -> dict[str, Any]:
    target = str(node_id).lstrip(".$")
    stack: list[Any] = [schema]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, child in item.items():
                if key in {"layout", "layouts"} and isinstance(child, list):
                    for layout in child:
                        if isinstance(layout, dict) and str(layout.get("i") or "").lstrip(".$") == target:
                            return layout
                stack.append(child)
        elif isinstance(item, list):
            stack.extend(item)
    raise UsageError(f"Stable layout target not found: {node_id}")


def find_component_node(schema: dict[str, Any], component_id: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    stack: list[Any] = [schema]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if str(item.get("id") or "") == str(component_id):
                matches.append(item)
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    if len(matches) != 1:
        raise UsageError(
            f"Stable component target must resolve exactly once: {component_id}"
        )
    return matches[0]


def find_tab_slot(
    schema: dict[str, Any], component_id: str, slot_key: str, slot_id: str
) -> dict[str, Any]:
    node = find_component_node(schema, component_id)
    props = node.get("props") if isinstance(node.get("props"), dict) else {}
    tabs = props.get("list") if isinstance(props.get("list"), list) else []
    matches = []
    for tab in tabs:
        if not isinstance(tab, dict) or str(tab.get("key") or "") != str(slot_key):
            continue
        children = tab.get("children") if isinstance(tab.get("children"), dict) else {}
        if str(children.get("id") or "") == str(slot_id):
            matches.append(tab)
    if len(matches) != 1:
        raise UsageError(
            f"Stable tab slot must resolve exactly once: {component_id}/{slot_key}/{slot_id}"
        )
    return matches[0]


def find_unit_field(detail: dict[str, Any], group: str, field_id: str) -> dict[str, Any]:
    fields = detail.get(group)
    if not isinstance(fields, list):
        raise UsageError(f"Unit field group is missing: {group}")
    matches = [item for item in fields if isinstance(item, dict) and str(item.get("fieldId")) == field_id]
    if len(matches) != 1:
        raise UsageError(f"Stable unit field must resolve exactly once: {group}/{field_id}")
    return matches[0]


def find_filter_formats(value: Any, filter_id: str, field_id: str) -> list[dict[str, Any]]:
    formats: list[dict[str, Any]] = []
    stack: list[Any] = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if str(item.get("filterUnitId") or "") == filter_id and str(item.get("fieldId") or "") == field_id:
                fmt = item.get("format")
                if isinstance(fmt, dict):
                    formats.append(fmt)
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    if not formats:
        raise UsageError(f"Stable public-filter field was not found: {filter_id}/{field_id}")
    return formats


def _formula_projection(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "subjectId": item.get("subjectId"),
        "columnKey": item.get("columnKey"),
        "columnName": item.get("columnName"),
        "columnDesc": item.get("columnDesc") or "",
        "dataType": item.get("dataType"),
        "formula": item.get("formula"),
        "dependencyIndicators": item.get("dependencyIndicators") or [],
        "globalFilterSpecialConfig": item.get("globalFilterSpecialConfig") or [],
    }


def _filter_projection(detail: dict[str, Any], filter_id: str, field_id: str) -> dict[str, Any]:
    formats = find_filter_formats(detail, filter_id, field_id)
    return {
        "filter_id": filter_id,
        "field_id": field_id,
        "copies": [
            {key: copy.deepcopy(fmt.get(key)) for key in FILTER_STATE_KEYS}
            for fmt in formats
        ],
    }


def _theme_projection(schema: dict[str, Any]) -> dict[str, Any]:
    root = (schema.get("componentsTree") or [None])[0]
    if not isinstance(root, dict):
        raise UsageError("Dashboard root theme node was not found.")
    config = schema.get("config") if isinstance(schema.get("config"), dict) else {}
    return {
        "backgroundColor": root.get("props", {}).get("style", {}).get("backgroundColor"),
        "themeType": config.get("themeType"),
        "styleId": config.get("styleId"),
    }


def _formula_item(page: Any, formula_id: str) -> dict[str, Any]:
    data = post_json(page, CUSTOM_COLUMN_LIST_API, {"id": formula_id}).get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    if isinstance(data, dict):
        return data
    raise UsageError(f"Formula readback is empty: {formula_id}")


def _recorded_post(
    page: Any,
    url: str,
    payload: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    started_at = _now()
    response = page.request.post(url, data=payload, timeout=45_000)
    observations.append(
        {
            "method": "POST",
            "host": urlparse(url).netloc,
            "url_path": urlparse(url).path,
            "payload_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            "request_key_paths": request_key_paths(payload),
            "payload_sha256": canonical_sha256(payload),
            "response_status": int(response.status),
            "response_content_type": response.headers.get("content-type"),
            "started_at": started_at,
            "completed_at": _now(),
        }
    )
    if response.status >= 400:
        raise UsageError(f"API failed with HTTP {response.status}: {url}")
    data = response.json()
    if not isinstance(data, dict) or data.get("status") not in (None, "success"):
        status = data.get("status") if isinstance(data, dict) else None
        raise UsageError(f"API returned non-success status {status}: {url}")
    return data


def _write_dashboard_schema(
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    schema: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    current = fetch_edit_dashboard_config(page, dashboard_id, "draft")
    if str(current.get("dashboardName") or "") != dashboard_name:
        raise UsageError("Sandbox dashboard identity drifted before schema write.")
    payload = {
        "dashboardHtmlJson": json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
        "dashboardName": current.get("dashboardName"),
        "description": "",
        "dashboardId": dashboard_id,
        "jsPackages": current.get("jsPackages"),
        "saveUnitList": _extract_key_values(schema, {"unitId"}),
        "allUnitList": _extract_key_values(schema, {"unitId", "filterUnitId"}),
        "clientInfo": current.get("clientInfo"),
        "customHtmlFormat": current.get("customHtmlFormat") or {},
        "htmlId": current.get("htmlId"),
    }
    return _recorded_post(page, SAVE_DASHBOARD_HTML_API, payload, observations)


def _write_unit_detail(
    page: Any,
    dashboard_id: str,
    detail: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    config = fetch_edit_dashboard_config(page, dashboard_id, "draft")
    payload = copy.deepcopy(detail)
    payload.update(
        {
            "dashboardId": dashboard_id,
            "versionId": "draft",
            "clientType": 1,
            "htmlId": config.get("htmlId"),
        }
    )
    return _recorded_post(page, UPDATE_UNIT_API, payload, observations)


def _write_formula(
    page: Any,
    item: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "subjectId": item.get("subjectId"),
        "formula": item.get("formula"),
        "columnDesc": item.get("columnDesc") or "",
        "columnName": item.get("columnName"),
        "dataType": item.get("dataType"),
        "dependency": item.get("dependencyIndicators") or item.get("dependency") or [],
        "columnKey": item.get("columnKey"),
        "globalFilterSpecialConfig": item.get("globalFilterSpecialConfig") or [],
    }
    return _recorded_post(page, CUSTOM_COLUMN_SAVE_API, payload, observations)


def _write_filter_detail(
    page: Any,
    dashboard_id: str,
    detail: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    config = fetch_edit_dashboard_config(page, dashboard_id, "draft")
    payload = copy.deepcopy(detail)
    payload.update(
        {
            "dashboardId": dashboard_id,
            "versionId": "draft",
            "htmlId": config.get("htmlId"),
        }
    )
    return _recorded_post(page, PUBLIC_FILTER_UPDATE_API, payload, observations)


@dataclass(frozen=True)
class ReversibleAdapter:
    operation: str
    read: Callable[[Any, str, Mapping[str, Any]], dict[str, Any]]
    project: Callable[[dict[str, Any], Mapping[str, Any]], dict[str, Any]]
    mutate: Callable[[dict[str, Any], Mapping[str, Any]], dict[str, Any]]
    restore: Callable[[dict[str, Any], dict[str, Any], Mapping[str, Any]], dict[str, Any]]
    write: Callable[[Any, str, str, dict[str, Any], list[dict[str, Any]]], dict[str, Any]]
    after_matches: Callable[[dict[str, Any], dict[str, Any], Mapping[str, Any]], bool]


@dataclass
class AppliedDashboardMutation:
    operation_id: str
    operation: str
    target: dict[str, Any]
    before_raw: dict[str, Any]
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    observations: list[dict[str, Any]]


def _read_schema(page: Any, dashboard_id: str, target: Mapping[str, Any]) -> dict[str, Any]:
    config = fetch_edit_dashboard_config(page, dashboard_id, "draft")
    return json.loads(config["dashboardHtmlJson"])


def _layout_project(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    item = find_layout_item(raw, str(target["node_id"]))
    return {key: item.get(key) for key in LAYOUT_KEYS}


def _layout_mutate(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    item = find_layout_item(raw, str(target["node_id"]))
    patch = target.get("probe_patch")
    if not isinstance(patch, Mapping) or not patch:
        raise UsageError("Layout adapter requires a non-empty probe_patch.")
    unsupported = set(patch) - set(LAYOUT_KEYS)
    if unsupported:
        raise UsageError(f"Unsupported layout probe keys: {sorted(unsupported)}")
    item.update(copy.deepcopy(dict(patch)))
    return raw


def _layout_restore(current: dict[str, Any], before: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    current_item = find_layout_item(current, str(target["node_id"]))
    before_item = find_layout_item(before, str(target["node_id"]))
    for key in LAYOUT_KEYS:
        if key in before_item:
            current_item[key] = copy.deepcopy(before_item[key])
        else:
            current_item.pop(key, None)
    return current


def _read_unit(page: Any, dashboard_id: str, target: Mapping[str, Any]) -> dict[str, Any]:
    return fetch_edit_unit_detail(page, str(target["unit_id"]), dashboard_id, "draft")


def _component_project(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    field = find_unit_field(raw, str(target["field_group"]), str(target["field_id"]))
    return {
        "unit_id": raw.get("unitId"),
        "field_group": target["field_group"],
        "field_id": field.get("fieldId"),
        "show_name": field.get("showName"),
    }


def _component_mutate(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    field = find_unit_field(raw, str(target["field_group"]), str(target["field_id"]))
    field["showName"] = str(target["probe_show_name"])
    return raw


def _component_restore(current: dict[str, Any], before: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    current_field = find_unit_field(current, str(target["field_group"]), str(target["field_id"]))
    before_field = find_unit_field(before, str(target["field_group"]), str(target["field_id"]))
    current_field["showName"] = before_field.get("showName")
    return current


def _component_title_value(schema: dict[str, Any], component_id: str) -> str:
    node = find_component_node(schema, component_id)
    props = node.get("props") if isinstance(node.get("props"), dict) else {}
    settings = props.get("settings") if isinstance(props.get("settings"), dict) else None
    if isinstance(settings, dict) and "componentName" in settings:
        return str(settings.get("componentName") or "")
    if "componentName" in props:
        return str(props.get("componentName") or "")
    if "title" in node:
        return str(node.get("title") or "")
    raise UsageError(f"Component title path was not found: {component_id}")


def _set_component_title(schema: dict[str, Any], component_id: str, title: str) -> None:
    node = find_component_node(schema, component_id)
    props = node.get("props") if isinstance(node.get("props"), dict) else {}
    settings = props.get("settings") if isinstance(props.get("settings"), dict) else None
    if isinstance(settings, dict) and "componentName" in settings:
        settings["componentName"] = title
        return
    if "componentName" in props:
        props["componentName"] = title
        return
    if "title" in node:
        node["title"] = title
        return
    raise UsageError(f"Component title path was not found: {component_id}")


def _read_component_title(page: Any, dashboard_id: str, target: Mapping[str, Any]) -> dict[str, Any]:
    raw: dict[str, Any] = {"schema": _read_schema(page, dashboard_id, target), "unit": None}
    if str(target.get("unit_id") or ""):
        raw["unit"] = _read_unit(page, dashboard_id, target)
    return raw


def _component_title_project(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    component_id = str(target["component_id"])
    unit = raw.get("unit") if isinstance(raw.get("unit"), dict) else None
    return {
        "component_id": component_id,
        "unit_id": str(target.get("unit_id") or "") or None,
        "schema_title": _component_title_value(raw["schema"], component_id),
        "unit_name": str(unit.get("unitName") or "") if unit is not None else None,
    }


def _component_title_mutate(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    title = str(target.get("probe_title") or "").strip()
    if not title:
        raise UsageError("Component-title adapter requires a non-empty probe_title.")
    _set_component_title(raw["schema"], str(target["component_id"]), title)
    if isinstance(raw.get("unit"), dict):
        raw["unit"]["unitName"] = title
    return raw


def _component_title_restore(
    current: dict[str, Any], before: dict[str, Any], target: Mapping[str, Any]
) -> dict[str, Any]:
    component_id = str(target["component_id"])
    _set_component_title(
        current["schema"], component_id, _component_title_value(before["schema"], component_id)
    )
    if isinstance(current.get("unit"), dict) and isinstance(before.get("unit"), dict):
        current["unit"]["unitName"] = before["unit"].get("unitName")
    return current


def _public_filter_title_project(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    find_filter_formats(raw, str(target["filter_id"]), str(target["field_id"]))
    unit = find_public_filter_unit(raw, str(target["filter_id"]))
    return {
        "relation_id": str(target["relation_id"]),
        "filter_id": str(target["filter_id"]),
        "field_id": str(target["field_id"]),
        "title": str(unit.get("unitName") or ""),
    }


def _public_filter_title_mutate(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    title = str(target.get("probe_title") or "").strip()
    if not title:
        raise UsageError("Public-filter title adapter requires a non-empty probe_title.")
    find_filter_formats(raw, str(target["filter_id"]), str(target["field_id"]))
    find_public_filter_unit(raw, str(target["filter_id"]))["unitName"] = title
    return raw


def _public_filter_title_restore(
    current: dict[str, Any], before: dict[str, Any], target: Mapping[str, Any]
) -> dict[str, Any]:
    current_unit = find_public_filter_unit(current, str(target["filter_id"]))
    before_unit = find_public_filter_unit(before, str(target["filter_id"]))
    current_unit["unitName"] = before_unit.get("unitName")
    return current


def _tab_label_project(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    tab = find_tab_slot(
        raw,
        str(target["component_id"]),
        str(target["slot_key"]),
        str(target["slot_id"]),
    )
    return {
        "component_id": str(target["component_id"]),
        "slot_key": str(target["slot_key"]),
        "slot_id": str(target["slot_id"]),
        "label": str(tab.get("label") or ""),
    }


def _tab_label_mutate(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    label = str(target.get("probe_label") or "").strip()
    if not label:
        raise UsageError("Tab-label adapter requires a non-empty probe_label.")
    find_tab_slot(
        raw,
        str(target["component_id"]),
        str(target["slot_key"]),
        str(target["slot_id"]),
    )["label"] = label
    return raw


def _tab_label_restore(
    current: dict[str, Any], before: dict[str, Any], target: Mapping[str, Any]
) -> dict[str, Any]:
    current_tab = find_tab_slot(
        current,
        str(target["component_id"]),
        str(target["slot_key"]),
        str(target["slot_id"]),
    )
    before_tab = find_tab_slot(
        before,
        str(target["component_id"]),
        str(target["slot_key"]),
        str(target["slot_id"]),
    )
    current_tab["label"] = before_tab.get("label")
    return current


def _read_formula(page: Any, dashboard_id: str, target: Mapping[str, Any]) -> dict[str, Any]:
    return _formula_item(page, str(target["formula_id"]))


def _formula_project(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    return _formula_projection(raw)


def _formula_mutate(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    probe_formula = str(target.get("probe_formula") or "")
    if not probe_formula:
        raise UsageError("Formula adapter requires an explicit probe_formula.")
    raw["formula"] = probe_formula
    return raw


def _formula_restore(current: dict[str, Any], before: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    current["formula"] = before.get("formula")
    return current


def _read_filter(page: Any, dashboard_id: str, target: Mapping[str, Any]) -> dict[str, Any]:
    return fetch_public_filter_detail(page, dashboard_id, str(target["relation_id"]))


def _filter_project(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    projected = _filter_projection(raw, str(target["filter_id"]), str(target["field_id"]))
    projected["relation_id"] = str(target["relation_id"])
    return projected


def _filter_mutate(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    for fmt in find_filter_formats(raw, str(target["filter_id"]), str(target["field_id"])):
        fmt["dynamicsFilter"] = True
        fmt["dynamicsFilterValue"] = str(target["probe_value"])
        fmt["autoSearchDefaultValue"] = False
    return raw


def _filter_restore(current: dict[str, Any], before: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    current_formats = find_filter_formats(current, str(target["filter_id"]), str(target["field_id"]))
    before_formats = find_filter_formats(before, str(target["filter_id"]), str(target["field_id"]))
    if len(current_formats) != len(before_formats):
        raise UsageError("Public-filter copy count drifted before recovery.")
    for current_format, before_format in zip(current_formats, before_formats):
        for key in FILTER_STATE_KEYS:
            if key in before_format:
                current_format[key] = copy.deepcopy(before_format.get(key))
            elif key in {"filterValue", "defaultFilterValue", "preFilterValueList"}:
                current_format[key] = []
            else:
                current_format[key] = None
    return current


def _filter_after_matches(expected: dict[str, Any], actual: dict[str, Any], target: Mapping[str, Any]) -> bool:
    expected_copies = expected.get("copies") or []
    actual_copies = actual.get("copies") or []
    authoritative_keys = (
        "dynamicsFilter",
        "dynamicsFilterValue",
        "autoSearchDefaultValue",
    )
    return bool(expected_copies) and len(expected_copies) == len(actual_copies) and all(
        all(expected_item.get(key) == actual_item.get(key) for key in authoritative_keys)
        for expected_item, actual_item in zip(expected_copies, actual_copies)
    )


def _theme_project(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    return _theme_projection(raw)


def _theme_mutate(raw: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    root = (raw.get("componentsTree") or [None])[0]
    if not isinstance(root, dict):
        raise UsageError("Dashboard root theme node was not found.")
    root.setdefault("props", {}).setdefault("style", {})["backgroundColor"] = str(target["probe_value"])
    return raw


def _theme_restore(current: dict[str, Any], before: dict[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    current_root = (current.get("componentsTree") or [None])[0]
    before_root = (before.get("componentsTree") or [None])[0]
    if not isinstance(current_root, dict) or not isinstance(before_root, dict):
        raise UsageError("Dashboard root theme node drifted before recovery.")
    current_root.setdefault("props", {}).setdefault("style", {})["backgroundColor"] = before_root.get(
        "props", {}
    ).get("style", {}).get("backgroundColor")
    return current


def _write_schema_adapter(
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    raw: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    return _write_dashboard_schema(page, dashboard_id, dashboard_name, raw, observations)


def _write_unit_adapter(
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    raw: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    return _write_unit_detail(page, dashboard_id, raw, observations)


def _write_component_title_adapter(
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    raw: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    if isinstance(raw.get("unit"), dict):
        _write_unit_detail(page, dashboard_id, raw["unit"], observations)
    return _write_dashboard_schema(
        page, dashboard_id, dashboard_name, raw["schema"], observations
    )


def _write_formula_adapter(
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    raw: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    return _write_formula(page, raw, observations)


def _write_filter_adapter(
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    raw: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    return _write_filter_detail(page, dashboard_id, raw, observations)


def _exact_after(expected: dict[str, Any], actual: dict[str, Any], target: Mapping[str, Any]) -> bool:
    return expected == actual


ADAPTERS: dict[str, ReversibleAdapter] = {
    "update_layout": ReversibleAdapter(
        "update_layout", _read_schema, _layout_project, _layout_mutate, _layout_restore,
        _write_schema_adapter, _exact_after,
    ),
    "update_component_fields": ReversibleAdapter(
        "update_component_fields", _read_unit, _component_project, _component_mutate,
        _component_restore, _write_unit_adapter, _exact_after,
    ),
    "update_component_filter_label": ReversibleAdapter(
        "update_component_filter_label", _read_unit, _component_project, _component_mutate,
        _component_restore, _write_unit_adapter, _exact_after,
    ),
    "update_component_title": ReversibleAdapter(
        "update_component_title", _read_component_title, _component_title_project,
        _component_title_mutate, _component_title_restore,
        _write_component_title_adapter, _exact_after,
    ),
    "update_formula": ReversibleAdapter(
        "update_formula", _read_formula, _formula_project, _formula_mutate,
        _formula_restore, _write_formula_adapter, _exact_after,
    ),
    "update_filter_dynamic_default": ReversibleAdapter(
        "update_filter_dynamic_default", _read_filter, _filter_project, _filter_mutate,
        _filter_restore, _write_filter_adapter, _filter_after_matches,
    ),
    "update_public_filter_title": ReversibleAdapter(
        "update_public_filter_title", _read_filter, _public_filter_title_project,
        _public_filter_title_mutate, _public_filter_title_restore,
        _write_filter_adapter, _exact_after,
    ),
    "update_tab_label": ReversibleAdapter(
        "update_tab_label", _read_schema, _tab_label_project, _tab_label_mutate,
        _tab_label_restore, _write_schema_adapter, _exact_after,
    ),
    "update_theme": ReversibleAdapter(
        "update_theme", _read_schema, _theme_project, _theme_mutate, _theme_restore,
        _write_schema_adapter, _exact_after,
    ),
}


def _planned_component_show_name(operation: Mapping[str, Any]) -> str:
    target = operation.get("target") if isinstance(operation.get("target"), Mapping) else {}
    after = operation.get("after") if isinstance(operation.get("after"), Mapping) else {}
    fields = after.get("fields") if isinstance(after.get("fields"), Mapping) else {}
    candidates: list[Mapping[str, Any]] = []
    for collection in ("dimensions", "metrics"):
        values = fields.get(collection, []) if isinstance(fields, Mapping) else []
        if isinstance(values, list):
            candidates.extend(item for item in values if isinstance(item, Mapping))
    matches = [item for item in candidates if str(item.get("field_id") or "") == str(target.get("field_id") or "")]
    if len(matches) != 1 or not str(matches[0].get("display_name") or "").strip():
        raise UsageError("Planned component field rename has no unique non-empty target name.")
    return str(matches[0]["display_name"])


def _planned_tab_label(operation: Mapping[str, Any]) -> str:
    target = operation.get("target") if isinstance(operation.get("target"), Mapping) else {}
    after = operation.get("after") if isinstance(operation.get("after"), Mapping) else {}
    config = after.get("config") if isinstance(after.get("config"), Mapping) else {}
    slots = config.get("slots") if isinstance(config.get("slots"), list) else []
    matches = [
        item
        for item in slots
        if isinstance(item, Mapping)
        and str(item.get("key") or "") == str(target.get("slot_key") or "")
        and str(item.get("slot_id") or "") == str(target.get("slot_id") or "")
    ]
    if len(matches) != 1 or not str(matches[0].get("label") or "").strip():
        raise UsageError("Planned tab-label change has no unique non-empty target label.")
    return str(matches[0]["label"])


def planned_operation_target(operation: Mapping[str, Any]) -> dict[str, Any]:
    operation_type = str(operation.get("type") or "")
    target = copy.deepcopy(dict(operation.get("target") or {}))
    before = operation.get("before") if isinstance(operation.get("before"), Mapping) else {}
    after = operation.get("after") if isinstance(operation.get("after"), Mapping) else {}
    if operation_type == "update_layout":
        target["node_id"] = str(target.get("component_id") or "")
        target["probe_patch"] = {
            key: copy.deepcopy(after.get(key))
            for key in ("x", "y", "w", "h")
            if before.get(key) != after.get(key)
        }
    elif operation_type == "update_component_fields":
        target["probe_show_name"] = _planned_component_show_name(operation)
    elif operation_type == "update_component_filter_label":
        target["probe_show_name"] = str(after.get("business_name") or "")
    elif operation_type == "update_component_title":
        target["probe_title"] = str(after.get("title") or "")
    elif operation_type == "update_formula":
        target["probe_formula"] = str(after.get("expression") or "")
    elif operation_type == "update_filter_dynamic_default":
        target["probe_value"] = str(after.get("dynamics_filter_value") or "")
    elif operation_type == "update_public_filter_title":
        target["probe_title"] = str(after.get("title") or "")
    elif operation_type == "update_tab_label":
        target["probe_label"] = _planned_tab_label(operation)
    elif operation_type == "update_theme":
        target["probe_value"] = str(after.get("background_color") or "")
    else:
        raise UsageError(f"No P4B adapter target mapping exists for {operation_type or '<missing>'}.")
    return target


def apply_adapter_target(
    *,
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    operation_id: str,
    operation_type: str,
    target: Mapping[str, Any],
) -> AppliedDashboardMutation:
    if operation_type not in ADAPTERS:
        raise UsageError(f"No verified adapter is registered for {operation_type or '<missing>'}.")
    adapter = ADAPTERS[operation_type]
    target = copy.deepcopy(dict(target))
    observations: list[dict[str, Any]] = []
    before_raw = adapter.read(page, dashboard_id, target)
    before_state = adapter.project(before_raw, target)
    before_hash = canonical_sha256(before_state)
    immediate_raw = adapter.read(page, dashboard_id, target)
    immediate_state = adapter.project(immediate_raw, target)
    assert_expected_state(immediate_state, before_hash, f"{operation_type} immediate pre-write state")
    changed_raw = adapter.mutate(copy.deepcopy(immediate_raw), target)
    expected_after = adapter.project(changed_raw, target)
    if canonical_sha256(expected_after) == before_hash:
        raise UsageError(f"{operation_type} planned mutation does not change the target state.")
    try:
        adapter.write(page, dashboard_id, dashboard_name, changed_raw, observations)
        after_raw = adapter.read(page, dashboard_id, target)
        after_state = adapter.project(after_raw, target)
        if not adapter.after_matches(expected_after, after_state, target):
            raise UsageError(f"{operation_type} post-write readback does not match the ChangePlan target.")
    except Exception as exc:  # noqa: BLE001
        # A transport/API error can be ambiguous: the service may have accepted
        # the write before the client observed the failure. Resolve that state
        # by readback and compensate immediately when the target changed.
        try:
            current_raw = adapter.read(page, dashboard_id, target)
            current_state = adapter.project(current_raw, target)
            if current_state != before_state:
                restore_raw = adapter.restore(
                    copy.deepcopy(current_raw), before_raw, target
                )
                adapter.write(page, dashboard_id, dashboard_name, restore_raw, observations)
                restored_raw = adapter.read(page, dashboard_id, target)
                if not adapter.after_matches(
                    before_state, adapter.project(restored_raw, target), target
                ):
                    raise UsageError("compensating readback did not restore the original state")
        except Exception as recovery_exc:  # noqa: BLE001
            raise UsageError(
                f"{operation_type} failed and immediate compensation was not provable: {recovery_exc}"
            ) from exc
        raise UsageError(f"{operation_type} failed; any observed write was restored: {exc}") from exc
    return AppliedDashboardMutation(
        operation_id=str(operation_id),
        operation=operation_type,
        target=target,
        before_raw=before_raw,
        before_state=before_state,
        after_state=after_state,
        observations=observations,
    )


def apply_planned_operation(
    *,
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    operation: Mapping[str, Any],
) -> AppliedDashboardMutation:
    operation_type = str(operation.get("type") or "")
    return apply_adapter_target(
        page=page,
        dashboard_id=dashboard_id,
        dashboard_name=dashboard_name,
        operation_id=str(operation.get("operation_id") or ""),
        operation_type=operation_type,
        target=planned_operation_target(operation),
    )


def restore_planned_operation(
    *,
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    mutation: AppliedDashboardMutation,
) -> dict[str, Any]:
    adapter = ADAPTERS[mutation.operation]
    observations: list[dict[str, Any]] = []
    current_raw = adapter.read(page, dashboard_id, mutation.target)
    current_state = adapter.project(current_raw, mutation.target)
    if not adapter.after_matches(mutation.after_state, current_state, mutation.target):
        raise UsageError(
            f"{mutation.operation} target drifted after apply; automatic recovery was blocked."
        )
    restore_raw = adapter.restore(
        copy.deepcopy(current_raw), mutation.before_raw, mutation.target
    )
    adapter.write(page, dashboard_id, dashboard_name, restore_raw, observations)
    restored_raw = adapter.read(page, dashboard_id, mutation.target)
    restored_state = adapter.project(restored_raw, mutation.target)
    if not adapter.after_matches(mutation.before_state, restored_state, mutation.target):
        raise UsageError(f"{mutation.operation} recovery readback does not match the original state.")
    return {
        "operation_id": mutation.operation_id,
        "operation": mutation.operation,
        "status": "restored",
        "before_sha256": canonical_sha256(mutation.before_state),
        "restored_sha256": canonical_sha256(restored_state),
        "observations": observations,
    }


def verify_reversible_adapter(
    *,
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    operation: str,
    target: Mapping[str, Any],
) -> dict[str, Any]:
    if operation not in ADAPTERS:
        raise UsageError(f"No reversible adapter is registered for {operation}.")
    adapter = ADAPTERS[operation]
    observations: list[dict[str, Any]] = []
    before_raw = adapter.read(page, dashboard_id, target)
    before_state = adapter.project(before_raw, target)
    before_hash = canonical_sha256(before_state)
    write_calls_before_drift_test = len(observations)
    drift_blocked = False
    try:
        assert_expected_state(before_state, "0" * 64, f"{operation} synthetic drift test")
    except UsageError:
        drift_blocked = len(observations) == write_calls_before_drift_test
    if not drift_blocked:
        raise UsageError(f"{operation} drift preflight did not block before write.")

    immediate_raw = adapter.read(page, dashboard_id, target)
    immediate_state = adapter.project(immediate_raw, target)
    assert_expected_state(immediate_state, before_hash, f"{operation} pre-write state")
    changed_raw = adapter.mutate(copy.deepcopy(immediate_raw), target)
    expected_after_state = adapter.project(changed_raw, target)
    if canonical_sha256(expected_after_state) == before_hash:
        raise UsageError(f"{operation} probe mutation did not change target state.")

    write_succeeded = False
    after_state: dict[str, Any] | None = None
    error: str | None = None
    restored = False
    try:
        adapter.write(page, dashboard_id, dashboard_name, changed_raw, observations)
        write_succeeded = True
        after_raw = adapter.read(page, dashboard_id, target)
        after_state = adapter.project(after_raw, target)
        if not adapter.after_matches(expected_after_state, after_state, target):
            raise UsageError(f"{operation} post-write readback did not match the requested target state.")
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            current_raw = adapter.read(page, dashboard_id, target)
            current_state = adapter.project(current_raw, target)
            if adapter.after_matches(before_state, current_state, target):
                restored = True
            else:
                restore_raw = adapter.restore(copy.deepcopy(current_raw), before_raw, target)
                adapter.write(page, dashboard_id, dashboard_name, restore_raw, observations)
                restored_raw = adapter.read(page, dashboard_id, target)
                restored_state = adapter.project(restored_raw, target)
                restored = adapter.after_matches(before_state, restored_state, target)
                if not restored and error is None:
                    error = f"{operation} recovery readback did not match the original state."
        except Exception as restore_exc:  # noqa: BLE001
            if error is None:
                error = f"Recovery failed: {type(restore_exc).__name__}: {restore_exc}"

    status = "verified_and_restored" if write_succeeded and restored and error is None else "failed"
    return {
        "operation": operation,
        "status": status,
        "before_sha256": before_hash,
        "after_sha256": canonical_sha256(after_state) if after_state is not None else None,
        "restored_sha256": before_hash if restored else None,
        "drift_blocked_without_write": drift_blocked,
        "write_succeeded": write_succeeded,
        "restored": restored,
        "error": error,
        "observations": observations,
    }
