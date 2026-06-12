"""Dashboard folder discovery through the BI menu API."""

from __future__ import annotations

import re
from typing import Any

from _shared.errors import UsageError

from .constants import DASHBOARD_MENU_API
from .models import DashboardRecord


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
