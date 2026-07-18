"""Read-only profiling for Taitan dashboard edit pages."""

from __future__ import annotations

import hashlib
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from _shared.auth import fill_login_if_present
from _shared.debug import save_debug_artifacts
from _shared.errors import UsageError

from .profile import _walk_dicts, extract_component_units, parse_dashboard_html, post_json


EDIT_DASHBOARD_URL = "https://udata.baijia.com/taitan/"
EDIT_API_ROOT = "https://udata.baijia.com/uanalysis-intelligence"
EDIT_DASHBOARD_CONFIG_API = f"{EDIT_API_ROOT}/config/dashBoard"
EDIT_UNIT_DETAIL_API = f"{EDIT_API_ROOT}/value/unit/detail"
EDIT_UNIT_CONSUMER_DETAIL_API = f"{EDIT_API_ROOT}/value/unit/consumer/detail"
EDIT_PUBLIC_FILTER_DETAIL_API = f"{EDIT_API_ROOT}/value/public/unit/relation/detail"
MODEL_DETAIL_DIM_API = f"{EDIT_API_ROOT}/model/detail/dim"
MODEL_DETAIL_METRIC_API = f"{EDIT_API_ROOT}/model/detail/metric"
MODEL_CUSTOM_COLUMN_API = f"{EDIT_API_ROOT}/model/customized/column/list"
MODEL_SUBJECT_PARAM_LIST_API = f"{EDIT_API_ROOT}/model/subject/paramList"

FIELD_GROUPS = (
    ("row_dimension", "unitDimensionList"),
    ("column_dimension", "unitColumnDimensionList"),
    ("measure", "unitMeasureList"),
    ("aide_measure", "unitAideMeasureList"),
    ("filter", "unitFilterList"),
)

SUPPORTED_DATA_UNIT_TYPES = frozenset({"card", "u_pivot", "u_bar", "u_pie"})

SNAPSHOT_SCHEMA_VERSION = "4.0.0"


def canonical_sha256(value: Any) -> str:
    """Hash a JSON-compatible value without depending on display formatting."""

    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_layout_item(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    normalized = {
        key: value.get(key)
        for key in ("x", "y", "w", "h", "minW", "minH", "maxW", "maxH", "static")
        if value.get(key) is not None
    }
    return normalized or None


def _layout_map(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, dict):
            continue
        node_id = str(item.get("i") or "").lstrip(".$")
        if node_id:
            result[node_id] = item
    return result


def extract_design_components(dashboard_html: dict[str, Any]) -> list[dict[str, Any]]:
    """Return stable component identities, container paths, and normalized layouts."""

    records: list[dict[str, Any]] = []
    seen: set[str] = set()

    def visit_embedded(
        value: Any,
        parent_node_id: str | None,
        container_path: list[str],
        layouts: dict[str, dict[str, Any]],
    ) -> None:
        if isinstance(value, list):
            for item in value:
                visit_embedded(item, parent_node_id, container_path, layouts)
            return
        if not isinstance(value, dict):
            return
        if value.get("id") and value.get("componentName"):
            visit_node(value, parent_node_id, container_path, layouts)
            return
        for item in value.values():
            if isinstance(item, (dict, list)):
                visit_embedded(item, parent_node_id, container_path, layouts)

    def visit_node(
        node: dict[str, Any],
        parent_node_id: str | None,
        container_path: list[str],
        layouts: dict[str, dict[str, Any]],
    ) -> None:
        node_id = str(node.get("id") or "")
        if not node_id or node_id in seen:
            return
        seen.add(node_id)
        props = node.get("props") if isinstance(node.get("props"), dict) else {}
        settings = props.get("settings") if isinstance(props.get("settings"), dict) else {}
        if not settings and isinstance(node.get("settings"), dict):
            settings = node["settings"]
        layout = _normalize_layout_item(layouts.get(node_id))
        tab_tokens = [item for item in container_path if str(item).startswith("tab:")]
        tab_id = tab_tokens[-1].split(":", 2)[1] if tab_tokens else None
        records.append(
            {
                "component_id": node_id,
                "node_id": node_id,
                "parent_node_id": parent_node_id,
                "container_id": parent_node_id,
                "tab_id": tab_id,
                "container_path": list(container_path),
                "node_component": node.get("componentName"),
                "type": settings.get("componentType") or node.get("componentName") or "unknown",
                "node_title": node.get("title"),
                "title": settings.get("componentName") or node.get("title") or "",
                "unit_id": settings.get("unitId"),
                "component_type": settings.get("componentType"),
                "component_name": settings.get("componentName") or props.get("componentName"),
                "hidden": bool(node.get("hidden", False)),
                "locked": bool(node.get("isLocked", False)),
                "layout": layout,
            }
        )

        child_layouts = _layout_map(props.get("layout"))
        visit_embedded(node.get("children") or [], node_id, container_path + [node_id], child_layouts)

        tabs = props.get("list") if isinstance(props.get("list"), list) else []
        for index, tab in enumerate(tabs):
            if not isinstance(tab, dict):
                continue
            tab_key = str(tab.get("key") or index)
            tab_label = str(tab.get("label") or tab_key)
            tab_path = container_path + [node_id, f"tab:{tab_key}:{tab_label}"]
            tab_layouts = _layout_map(tab.get("layouts"))
            children = tab.get("children")
            if isinstance(children, dict) and "value" in children:
                children = children.get("value")
            visit_embedded(children or [], node_id, tab_path, tab_layouts)

        for key, item in props.items():
            if key in {"settings", "layout", "list"}:
                continue
            if isinstance(item, (dict, list)):
                visit_embedded(item, node_id, container_path + [node_id], {})

    visit_embedded(dashboard_html.get("componentsTree") or [], None, [], {})
    return sorted(records, key=lambda item: str(item.get("node_id") or ""))


def _formula_id_for_field(unit_id: str, field: dict[str, Any]) -> str:
    field_id = str(field.get("field_id") or "")
    return field_id or f"{unit_id}:{field.get('group')}:{field.get('business_name')}"


def build_formula_snapshot(pivot_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for unit in pivot_units:
        unit_id = str(unit.get("unit_id") or "")
        component = unit.get("component") if isinstance(unit.get("component"), dict) else {}
        component_id = str(component.get("component_id") or component.get("node_id") or unit_id)
        for field in unit.get("fields") or []:
            if not isinstance(field, dict):
                continue
            formula = str(field.get("formula") or "").strip()
            if not formula:
                continue
            field_id = str(field.get("field_id") or "")
            formula_id = _formula_id_for_field(unit_id, field)
            existing = grouped.get(formula_id)
            if existing is None:
                existing = {
                    "formula_id": formula_id,
                    "field_id": field_id,
                    "name": field.get("business_name") or field.get("show_name") or "",
                    "expression": formula,
                    "formula": formula,
                    "dependencies": field.get("dependencies") or [],
                    "scope": "component",
                    "shared": False,
                    "component_ids": [],
                    "config": {
                        "group": field.get("group"),
                        "role": field.get("role"),
                    },
                }
                grouped[formula_id] = existing
            if component_id and component_id not in existing["component_ids"]:
                existing["component_ids"].append(component_id)
            if existing["expression"] != formula:
                existing["shared"] = True
                existing["config"]["expression_conflict"] = True
    for item in grouped.values():
        item["component_ids"].sort()
        item["shared"] = bool(item["shared"] or len(item["component_ids"]) > 1)
    return sorted(grouped.values(), key=lambda item: item["formula_id"])


def _collect_public_filter_units(detail: dict[str, Any]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, dict):
            return
        unit_id = str(value.get("unitId") or "")
        if unit_id.startswith("public_filter_") and not unit_id.startswith("public_filter_relation_"):
            units.append(value)
            return
        walk(value.get("unitList") or [])

    walk(detail.get("unitList") or [])
    return units


def _configured_public_filter_fields(unit: dict[str, Any]) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for root_name in ("format", "relationUnit"):
        root = unit.get(root_name)
        if not isinstance(root, dict):
            continue
        unit_config = root.get("unitConfig")
        if not isinstance(unit_config, dict):
            continue
        for field_group in ("unitDimensionList", "unitMeasureList"):
            for field in unit_config.get(field_group) or []:
                if not isinstance(field, dict):
                    continue
                field_id = str(field.get("fieldId") or field.get("paramId") or "")
                identity = (field_group, field_id)
                if identity in seen:
                    continue
                seen.add(identity)
                fields.append(field)
    return fields


def build_public_filter_snapshot(public_filters: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation_id, detail in sorted(public_filters.items()):
        if not isinstance(detail, dict):
            continue
        for order_index, unit in enumerate(_collect_public_filter_units(detail), start=1):
            filter_id = str(unit.get("unitId") or "")
            fields = _configured_public_filter_fields(unit)
            if not fields:
                rows.append(
                    {
                        "relation_id": relation_id,
                        "filter_id": filter_id,
                        "field_id": "",
                        "order_index": order_index,
                        "filter_name": unit.get("unitName"),
                        "title": unit.get("unitName") or "",
                        "field_name": "",
                    }
                )
                continue
            for field in fields:
                fmt = field.get("format") if isinstance(field.get("format"), dict) else {}
                rows.append(
                    {
                        "relation_id": relation_id,
                        "filter_id": filter_id,
                        "field_id": str(field.get("fieldId") or field.get("paramId") or ""),
                        "order_index": order_index,
                        "filter_name": unit.get("unitName"),
                        "title": unit.get("unitName") or "",
                        "show_name": field.get("showName") or field.get("name"),
                        "field_name": field.get("showName") or field.get("name") or "",
                        "condition": fmt.get("condition"),
                        "operator": fmt.get("condition") or "",
                        "values": fmt.get("filterValue") or [],
                        "default_value": fmt.get("dynamicsFilterValue"),
                        "dynamic_default": fmt.get("dynamicsFilter"),
                        "multiple_filter": fmt.get("multipleFilter"),
                        "dynamics_filter": fmt.get("dynamicsFilter"),
                        "dynamics_filter_value": fmt.get("dynamicsFilterValue"),
                        "auto_search_default_value": fmt.get("autoSearchDefaultValue"),
                    }
                )
    return sorted(rows, key=lambda item: (str(item["relation_id"]), str(item["filter_id"]), str(item["field_id"])))


def build_component_filter_snapshot(pivot_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for unit in pivot_units:
        for field in unit.get("fields") or []:
            if not isinstance(field, dict) or field.get("group") != "filter":
                continue
            rows.append(
                {
                    "component_filter_key": f"{unit.get('unit_id') or ''}::{field.get('field_id') or ''}",
                    "scope": "component",
                    "unit_id": str(unit.get("unit_id") or ""),
                    "field_id": str(field.get("field_id") or ""),
                    "business_name": field.get("business_name") or field.get("show_name"),
                    "condition": field.get("condition"),
                    "filter_type": field.get("filter_type") or [],
                    "write_status": "blocked_unsupported",
                }
            )
    return sorted(rows, key=lambda item: (item["unit_id"], item["field_id"]))


def _pivot_dataset_identity(unit: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    dashboard_model = unit.get("dashboard_model") if isinstance(unit.get("dashboard_model"), dict) else {}
    subject_id = dashboard_model.get("subjectId") or unit.get("subject_id")
    application_model_id = dashboard_model.get("applicationModelId") or unit.get("model_id")
    if subject_id not in (None, ""):
        dataset_id = f"subject_{subject_id}"
    elif application_model_id not in (None, ""):
        dataset_id = f"model_{application_model_id}"
    else:
        return None, {}
    return dataset_id, {
        "subject_id": subject_id,
        "application_model_id": application_model_id,
        "model_type": dashboard_model.get("modelType") or unit.get("model_type"),
    }


def _data_unit_dataset_identity(unit: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    """Return the stable dataset identity shared by all supported data units.

    The historical helper name is retained because external callers and old
    fixtures still describe this as a pivot identity.  Taitan exposes the same
    dashboardModel structure for card, pivot, bar, and pie units.
    """

    return _pivot_dataset_identity(unit)


def build_dataset_snapshot(
    pivot_units: list[dict[str, Any]],
    dataset_fields: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for unit in pivot_units:
        dataset_id, source = _pivot_dataset_identity(unit)
        if not dataset_id:
            continue
        item = grouped.setdefault(
            dataset_id,
            {
                "dataset_id": dataset_id,
                "name": str(unit.get("model_name") or dataset_id),
                "source": source,
                "config": {"component_ids": [], "unit_ids": []},
            },
        )
        component = unit.get("component") if isinstance(unit.get("component"), dict) else {}
        component_id = str(component.get("component_id") or component.get("node_id") or "")
        unit_id = str(unit.get("unit_id") or "")
        if component_id and component_id not in item["config"]["component_ids"]:
            item["config"]["component_ids"].append(component_id)
        if unit_id and unit_id not in item["config"]["unit_ids"]:
            item["config"]["unit_ids"].append(unit_id)

    for dataset in dataset_fields or []:
        if not isinstance(dataset, dict) or dataset.get("subject_id") in (None, ""):
            continue
        dataset_id = f"subject_{dataset['subject_id']}"
        grouped.setdefault(
            dataset_id,
            {
                "dataset_id": dataset_id,
                "name": dataset_id,
                "source": {
                    "subject_id": dataset.get("subject_id"),
                    "application_model_id": None,
                    "model_type": dataset.get("model_type"),
                },
                "config": {"component_ids": [], "unit_ids": []},
            },
        )
    for item in grouped.values():
        item["config"]["component_ids"].sort()
        item["config"]["unit_ids"].sort()
    return sorted(grouped.values(), key=lambda item: item["dataset_id"])


def enrich_component_snapshot(
    components: list[dict[str, Any]],
    pivot_units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_unit_id = {str(item.get("unit_id") or ""): item for item in components if item.get("unit_id")}
    for unit in pivot_units:
        unit_id = str(unit.get("unit_id") or "")
        component = by_unit_id.get(unit_id)
        if component is None:
            continue
        dimensions: list[dict[str, Any]] = []
        metrics: list[dict[str, Any]] = []
        formula_ids: list[str] = []
        filter_ids: list[str] = []
        for field in unit.get("fields") or []:
            if not isinstance(field, dict):
                continue
            field_id = str(field.get("field_id") or "")
            field_ref = {
                "field_id": field_id,
                "group": field.get("group"),
                "role": field.get("role"),
                "business_name": field.get("business_name") or field.get("show_name") or "",
                "sort_value": field.get("sort_value"),
            }
            if field.get("group") in {"row_dimension", "column_dimension"}:
                dimensions.append(field_ref)
            elif field.get("group") in {"measure", "aide_measure"}:
                metrics.append(field_ref)
            elif field.get("group") == "filter" and field_id:
                filter_ids.append(f"{unit_id}::{field_id}")
            if str(field.get("formula") or "").strip():
                formula_ids.append(_formula_id_for_field(unit_id, field))
        dataset_id, model_identity = _pivot_dataset_identity(unit)
        component["dataset_id"] = dataset_id
        component["fields"] = {
            "dimensions": sorted(dimensions, key=lambda item: (item["group"], item["field_id"])),
            "metrics": sorted(metrics, key=lambda item: (item["group"], item["field_id"])),
        }
        component["formula_ids"] = sorted(set(formula_ids))
        component["filter_ids"] = sorted(set(filter_ids))
        component["config"] = {
            "model_identity": model_identity,
            "model_id": unit.get("model_id"),
            "model_name": unit.get("model_name"),
            "model_type": unit.get("model_type"),
        }
    return components


def build_data_unit_snapshot(data_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a compact, stable identity/binding view for supported data units."""

    rows: list[dict[str, Any]] = []
    for unit in data_units:
        unit_id = str(unit.get("unit_id") or "")
        if not unit_id:
            continue
        component = unit.get("component") if isinstance(unit.get("component"), dict) else {}
        dataset_id, model_identity = _data_unit_dataset_identity(unit)
        field_groups: dict[str, list[str]] = {
            group_name: [] for group_name, _field_key in FIELD_GROUPS
        }
        formula_ids: list[str] = []
        for field in unit.get("fields") or []:
            if not isinstance(field, dict):
                continue
            group = str(field.get("group") or "")
            field_id = str(field.get("field_id") or "")
            if group in field_groups and field_id:
                field_groups[group].append(field_id)
            if str(field.get("formula") or "").strip():
                formula_ids.append(_formula_id_for_field(unit_id, field))
        rows.append(
            {
                "unit_id": unit_id,
                "unit_type": str(unit.get("unit_type") or ""),
                "component_id": str(
                    component.get("component_id") or component.get("node_id") or ""
                ),
                "dataset_id": dataset_id,
                "model_identity": model_identity,
                "field_groups": {
                    key: sorted(set(values)) for key, values in field_groups.items()
                },
                "formula_ids": sorted(set(formula_ids)),
                "component_filter_ids": sorted(
                    f"{unit_id}::{field_id}"
                    for field_id in field_groups.get("filter", [])
                ),
            }
        )
    return sorted(rows, key=lambda item: item["unit_id"])


def _is_editable_data_component(component: dict[str, Any]) -> bool:
    """Recognize configured supported data units without treating containers as data units."""

    if not str(component.get("unit_id") or "").strip():
        return False
    component_type = str(component.get("component_type") or "").strip().lower()
    node_component = str(component.get("node_component") or "").strip().lower()
    if component_type in SUPPORTED_DATA_UNIT_TYPES:
        return True
    return any(
        marker in node_component
        for marker in ("pivot", "barchart", "piechart", "metriccard", "cardgroup")
    )


def _is_editable_pivot_component(component: dict[str, Any]) -> bool:
    """Backward-compatible pivot-only predicate used by legacy callers."""

    if not str(component.get("unit_id") or "").strip():
        return False
    component_type = str(component.get("component_type") or "").strip().lower()
    node_component = str(component.get("node_component") or "").strip().lower()
    return component_type == "u_pivot" or "pivot" in node_component


def _binding_error(code: str, message: str, **references: Any) -> dict[str, Any]:
    error: dict[str, Any] = {
        "category": "binding",
        "code": code,
        "message": message,
    }
    error.update(
        {
            key: value
            for key, value in references.items()
            if value not in (None, "", [])
        }
    )
    return error


def _dependency_field_id(dependency: Any) -> str | None:
    if isinstance(dependency, (str, int)):
        value = str(dependency).strip()
        return value or None
    if not isinstance(dependency, dict):
        return None
    for key in ("paramId", "fieldId", "field_id", "key", "id"):
        value = dependency.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def validate_data_component_bindings(
    *,
    component_units: list[dict[str, Any]],
    data_units: list[dict[str, Any]],
    snapshot: dict[str, Any],
    dataset_fields: list[dict[str, Any]],
    include_dataset_fields: bool,
) -> dict[str, Any]:
    """Validate stable references for card, pivot, bar, and pie data components.

    Existing ``PIVOT_*`` diagnostic codes are intentionally retained for
    compatibility with downstream automation.  They now apply to every
    supported data unit and include ``unit_type`` where the source exposes it.
    """

    errors: list[dict[str, Any]] = []
    components = {
        str(item.get("component_id") or ""): item
        for item in snapshot.get("components") or []
        if isinstance(item, dict) and item.get("component_id")
    }
    components_by_unit = {
        str(item.get("unit_id") or ""): item
        for item in components.values()
        if item.get("unit_id")
    }
    formulas = {
        str(item.get("formula_id") or ""): item
        for item in snapshot.get("formulas") or []
        if isinstance(item, dict) and item.get("formula_id")
    }
    component_filters = {
        str(item.get("component_filter_key") or ""): item
        for item in snapshot.get("component_filters") or []
        if isinstance(item, dict) and item.get("component_filter_key")
    }
    datasets = {
        str(item.get("dataset_id") or ""): item
        for item in snapshot.get("datasets") or []
        if isinstance(item, dict) and item.get("dataset_id")
    }
    pivot_by_unit: dict[str, dict[str, Any]] = {}
    for unit in data_units:
        unit_id = str(unit.get("unit_id") or "")
        if not unit_id:
            errors.append(
                _binding_error(
                    "PIVOT_UNIT_ID_UNRESOLVED",
                    "Editable pivot detail has no stable unit_id.",
                )
            )
            continue
        if unit_id in pivot_by_unit:
            errors.append(
                _binding_error(
                    "PIVOT_UNIT_ID_DUPLICATE",
                    "Editable pivot unit_id is duplicated in the profile.",
                    unit_id=unit_id,
                )
            )
            continue
        pivot_by_unit[unit_id] = unit

    expected_pivot_ids = {
        str(component.get("unit_id") or "")
        for component in component_units
        if isinstance(component, dict) and _is_editable_data_component(component)
    }
    for unit_id in sorted(expected_pivot_ids - set(pivot_by_unit)):
        errors.append(
            _binding_error(
                "PIVOT_UNIT_DETAIL_UNRESOLVED",
                "Configured pivot component did not resolve to a pivot unit detail.",
                unit_id=unit_id,
            )
        )

    dataset_tree_by_subject = {
        str(item.get("subject_id")): item
        for item in dataset_fields
        if isinstance(item, dict) and item.get("subject_id") not in (None, "")
    }
    selected_field_reference_count = 0
    formula_reference_count = 0
    component_filter_reference_count = 0
    dataset_reference_count = 0
    validated_pivot_ids: set[str] = set()

    for unit_id, unit in sorted(pivot_by_unit.items()):
        unit_error_count = len(errors)
        source_component = unit.get("component") if isinstance(unit.get("component"), dict) else {}
        source_component_id = str(
            source_component.get("component_id") or source_component.get("node_id") or ""
        )
        component = components_by_unit.get(unit_id)
        if component is None:
            errors.append(
                _binding_error(
                    "PIVOT_COMPONENT_UNRESOLVED",
                    "Pivot unit is not bound to a normalized dashboard component.",
                    unit_id=unit_id,
                    component_id=source_component_id,
                )
            )
            component = {}
        component_id = str(component.get("component_id") or source_component_id or "")
        if source_component_id and component_id and source_component_id != component_id:
            errors.append(
                _binding_error(
                    "PIVOT_COMPONENT_ID_MISMATCH",
                    "Pivot detail and normalized component disagree on component identity.",
                    unit_id=unit_id,
                    component_id=component_id,
                    source_component_id=source_component_id,
                )
            )

        dataset_id, model_identity = _data_unit_dataset_identity(unit)
        component_dataset_id = str(component.get("dataset_id") or "")
        if not dataset_id or not any(
            model_identity.get(key) not in (None, "")
            for key in ("subject_id", "application_model_id")
        ):
            errors.append(
                _binding_error(
                    "PIVOT_DATASET_IDENTITY_UNRESOLVED",
                    "Pivot unit has no resolvable subject/application-model identity.",
                    unit_id=unit_id,
                    component_id=component_id,
                )
            )
        else:
            dataset_reference_count += 1
            if component_dataset_id != dataset_id:
                errors.append(
                    _binding_error(
                        "PIVOT_DATASET_REFERENCE_MISMATCH",
                        "Pivot component dataset_id does not match its model identity.",
                        unit_id=unit_id,
                        component_id=component_id,
                        dataset_id=dataset_id,
                        component_dataset_id=component_dataset_id,
                    )
                )
            dataset = datasets.get(dataset_id)
            if dataset is None:
                errors.append(
                    _binding_error(
                        "PIVOT_DATASET_REFERENCE_DANGLING",
                        "Pivot component references a dataset absent from the profile.",
                        unit_id=unit_id,
                        component_id=component_id,
                        dataset_id=dataset_id,
                    )
                )
            else:
                dataset_config = (
                    dataset.get("config") if isinstance(dataset.get("config"), dict) else {}
                )
                if unit_id not in {
                    str(value) for value in dataset_config.get("unit_ids") or []
                }:
                    errors.append(
                        _binding_error(
                            "PIVOT_DATASET_UNIT_BACKREF_MISSING",
                            "Referenced dataset does not include the pivot unit back-reference.",
                            unit_id=unit_id,
                            component_id=component_id,
                            dataset_id=dataset_id,
                        )
                    )
                if component_id and component_id not in {
                    str(value) for value in dataset_config.get("component_ids") or []
                }:
                    errors.append(
                        _binding_error(
                            "PIVOT_DATASET_COMPONENT_BACKREF_MISSING",
                            "Referenced dataset does not include the component back-reference.",
                            unit_id=unit_id,
                            component_id=component_id,
                            dataset_id=dataset_id,
                        )
                    )

        fields = [item for item in unit.get("fields") or [] if isinstance(item, dict)]
        fields_by_id: dict[str, list[dict[str, Any]]] = {}
        for field in fields:
            field_id = str(field.get("field_id") or "")
            if not field_id:
                errors.append(
                    _binding_error(
                        "PIVOT_SELECTED_FIELD_ID_UNRESOLVED",
                        "Configured pivot field has no stable field_id.",
                        unit_id=unit_id,
                        component_id=component_id,
                        field_group=field.get("group"),
                    )
                )
                continue
            fields_by_id.setdefault(field_id, []).append(field)
            detail = field.get("detail") if isinstance(field.get("detail"), dict) else {}
            if detail.get("detail_type") in {None, "", "unknown", "error"}:
                errors.append(
                    _binding_error(
                        "PIVOT_SELECTED_FIELD_DETAIL_UNRESOLVED",
                        "Configured pivot field did not resolve to a model field detail.",
                        unit_id=unit_id,
                        component_id=component_id,
                        field_id=field_id,
                        detail_type=detail.get("detail_type"),
                    )
                )

        selected_refs = [
            item for item in unit.get("selected_fields") or [] if isinstance(item, dict)
        ]
        selected_field_reference_count += len(selected_refs)
        selected_ref_ids: set[str] = set()
        for selected in selected_refs:
            field_id = str(selected.get("key") or "")
            if field_id:
                selected_ref_ids.add(field_id)
            if not field_id or field_id not in fields_by_id:
                errors.append(
                    _binding_error(
                        "PIVOT_SELECTED_FIELD_REFERENCE_DANGLING",
                        "Selected-field reference does not resolve to a configured pivot field.",
                        unit_id=unit_id,
                        component_id=component_id,
                        field_id=field_id,
                    )
                )
        for field_id in sorted(set(fields_by_id) - selected_ref_ids):
            errors.append(
                _binding_error(
                    "PIVOT_SELECTED_FIELD_BACKREF_MISSING",
                    "Configured pivot field is absent from selected_fields.",
                    unit_id=unit_id,
                    component_id=component_id,
                    field_id=field_id,
                )
            )

        component_field_refs: list[dict[str, Any]] = []
        component_fields = component.get("fields") if isinstance(component.get("fields"), dict) else {}
        for collection in ("dimensions", "metrics"):
            component_field_refs.extend(
                item
                for item in component_fields.get(collection) or []
                if isinstance(item, dict)
            )
        selected_field_reference_count += len(component_field_refs)
        component_field_ref_ids: set[str] = set()
        for field_ref in component_field_refs:
            field_id = str(field_ref.get("field_id") or "")
            if field_id:
                component_field_ref_ids.add(field_id)
            if not field_id or field_id not in fields_by_id:
                errors.append(
                    _binding_error(
                        "PIVOT_COMPONENT_FIELD_REFERENCE_DANGLING",
                        "Component field reference does not resolve to its pivot field.",
                        unit_id=unit_id,
                        component_id=component_id,
                        field_id=field_id,
                    )
                )
        expected_component_field_ids = {
            field_id
            for field_id, grouped_fields in fields_by_id.items()
            if any(
                field.get("group")
                in {"row_dimension", "column_dimension", "measure", "aide_measure"}
                for field in grouped_fields
            )
        }
        for field_id in sorted(expected_component_field_ids - component_field_ref_ids):
            errors.append(
                _binding_error(
                    "PIVOT_COMPONENT_FIELD_BACKREF_MISSING",
                    "Configured pivot field is absent from normalized component fields.",
                    unit_id=unit_id,
                    component_id=component_id,
                    field_id=field_id,
                )
            )

        component_formula_ids = {
            str(value) for value in component.get("formula_ids") or [] if str(value)
        }
        expected_formula_ids = {
            _formula_id_for_field(unit_id, field)
            for field in fields
            if str(field.get("formula") or "").strip()
        }
        formula_reference_count += len(component_formula_ids)
        for formula_id in sorted(expected_formula_ids - component_formula_ids):
            errors.append(
                _binding_error(
                    "PIVOT_FORMULA_COMPONENT_REF_MISSING",
                    "Configured pivot formula is absent from the component formula references.",
                    unit_id=unit_id,
                    component_id=component_id,
                    formula_id=formula_id,
                )
            )
        for formula_id in sorted(component_formula_ids - expected_formula_ids):
            errors.append(
                _binding_error(
                    "PIVOT_FORMULA_FIELD_REFERENCE_DANGLING",
                    "Component formula reference does not resolve to a configured pivot formula field.",
                    unit_id=unit_id,
                    component_id=component_id,
                    formula_id=formula_id,
                )
            )
        for formula_id in sorted(component_formula_ids | expected_formula_ids):
            formula = formulas.get(formula_id)
            if formula is None:
                errors.append(
                    _binding_error(
                        "PIVOT_FORMULA_REFERENCE_DANGLING",
                        "Pivot formula reference does not resolve to a formula artifact.",
                        unit_id=unit_id,
                        component_id=component_id,
                        formula_id=formula_id,
                    )
                )
                continue
            if component_id and component_id not in {
                str(value) for value in formula.get("component_ids") or []
            }:
                errors.append(
                    _binding_error(
                        "PIVOT_FORMULA_COMPONENT_BACKREF_MISSING",
                        "Formula artifact does not include the component back-reference.",
                        unit_id=unit_id,
                        component_id=component_id,
                        formula_id=formula_id,
                    )
                )

        component_filter_ids = {
            str(value) for value in component.get("filter_ids") or [] if str(value)
        }
        expected_filter_ids = {
            f"{unit_id}::{field_id}"
            for field_id, grouped_fields in fields_by_id.items()
            if any(field.get("group") == "filter" for field in grouped_fields)
        }
        component_filter_reference_count += len(component_filter_ids)
        for filter_key in sorted(expected_filter_ids - component_filter_ids):
            errors.append(
                _binding_error(
                    "PIVOT_COMPONENT_FILTER_REF_MISSING",
                    "Configured pivot filter field is absent from component filter references.",
                    unit_id=unit_id,
                    component_id=component_id,
                    component_filter_key=filter_key,
                )
            )
        for filter_key in sorted(component_filter_ids - expected_filter_ids):
            errors.append(
                _binding_error(
                    "PIVOT_COMPONENT_FILTER_FIELD_DANGLING",
                    "Component filter reference does not resolve to a configured pivot filter field.",
                    unit_id=unit_id,
                    component_id=component_id,
                    component_filter_key=filter_key,
                )
            )
        for filter_key in sorted(component_filter_ids | expected_filter_ids):
            component_filter = component_filters.get(filter_key)
            if component_filter is None:
                errors.append(
                    _binding_error(
                        "PIVOT_COMPONENT_FILTER_REFERENCE_DANGLING",
                        "Pivot component-filter reference has no matching filter artifact.",
                        unit_id=unit_id,
                        component_id=component_id,
                        component_filter_key=filter_key,
                    )
                )
                continue
            field_id = str(component_filter.get("field_id") or "")
            if (
                str(component_filter.get("unit_id") or "") != unit_id
                or field_id not in fields_by_id
                or not any(field.get("group") == "filter" for field in fields_by_id[field_id])
            ):
                errors.append(
                    _binding_error(
                        "PIVOT_COMPONENT_FILTER_TARGET_DANGLING",
                        "Component-filter artifact does not resolve to a filter field on the pivot.",
                        unit_id=unit_id,
                        component_id=component_id,
                        field_id=field_id,
                        component_filter_key=filter_key,
                    )
                )

        subject_id = model_identity.get("subject_id")
        dataset_tree = (
            dataset_tree_by_subject.get(str(subject_id))
            if include_dataset_fields and subject_id not in (None, "")
            else None
        )
        if include_dataset_fields and subject_id not in (None, ""):
            if dataset_tree is None or dataset_tree.get("error"):
                errors.append(
                    _binding_error(
                        "PIVOT_DATASET_FIELD_TREE_UNRESOLVED",
                        "Subject-backed pivot dataset field tree is unavailable.",
                        unit_id=unit_id,
                        component_id=component_id,
                        dataset_id=dataset_id,
                        subject_id=subject_id,
                    )
                )
            else:
                dataset_field_ids = {
                    str(item.get("key"))
                    for item in dataset_tree.get("fields") or []
                    if isinstance(item, dict) and item.get("key") not in (None, "")
                }
                for field_id in sorted(fields_by_id):
                    if field_id not in dataset_field_ids:
                        errors.append(
                            _binding_error(
                                "PIVOT_SELECTED_FIELD_DATASET_REFERENCE_DANGLING",
                                "Configured pivot field is absent from its referenced dataset field tree.",
                                unit_id=unit_id,
                                component_id=component_id,
                                dataset_id=dataset_id,
                                field_id=field_id,
                            )
                        )
                for formula_id in sorted(expected_formula_ids):
                    formula = formulas.get(formula_id) or {}
                    for dependency in formula.get("dependencies") or []:
                        dependency_id = _dependency_field_id(dependency)
                        if not dependency_id:
                            errors.append(
                                _binding_error(
                                    "PIVOT_FORMULA_DEPENDENCY_ID_UNRESOLVED",
                                    "Formula dependency has no resolvable field identity.",
                                    unit_id=unit_id,
                                    component_id=component_id,
                                    formula_id=formula_id,
                                )
                            )
                        elif dependency_id not in dataset_field_ids:
                            errors.append(
                                _binding_error(
                                    "PIVOT_FORMULA_DEPENDENCY_DANGLING",
                                    "Formula dependency is absent from the referenced dataset field tree.",
                                    unit_id=unit_id,
                                    component_id=component_id,
                                    dataset_id=dataset_id,
                                    formula_id=formula_id,
                                    field_id=dependency_id,
                                )
                            )

        if len(errors) == unit_error_count:
            validated_pivot_ids.add(unit_id)

    for component_id, component in components.items():
        dataset_id = str(component.get("dataset_id") or "")
        if dataset_id and dataset_id not in datasets:
            errors.append(
                _binding_error(
                    "COMPONENT_DATASET_REFERENCE_DANGLING",
                    "Dashboard component references a dataset absent from the profile.",
                    component_id=component_id,
                    dataset_id=dataset_id,
                )
            )
        for formula_id in component.get("formula_ids") or []:
            if str(formula_id) not in formulas:
                errors.append(
                    _binding_error(
                        "COMPONENT_FORMULA_REFERENCE_DANGLING",
                        "Dashboard component references a formula absent from the profile.",
                        component_id=component_id,
                        formula_id=str(formula_id),
                    )
                )
        for filter_key in component.get("filter_ids") or []:
            if str(filter_key) not in component_filters:
                errors.append(
                    _binding_error(
                        "COMPONENT_FILTER_REFERENCE_DANGLING",
                        "Dashboard component references a component filter absent from the profile.",
                        component_id=component_id,
                        component_filter_key=str(filter_key),
                    )
                )

    return {
        "status": "complete" if not errors else "incomplete",
        "editable_data_component_count": len(pivot_by_unit),
        "expected_data_component_count": len(expected_pivot_ids),
        "validated_data_component_count": len(validated_pivot_ids),
        "editable_pivot_count": len(pivot_by_unit),
        "expected_pivot_count": len(expected_pivot_ids),
        "validated_pivot_count": len(validated_pivot_ids),
        "ignored_non_data_component_count": sum(
            1
            for component in component_units
            if isinstance(component, dict) and not _is_editable_data_component(component)
        ),
        "dataset_reference_count": dataset_reference_count,
        "selected_field_reference_count": selected_field_reference_count,
        "formula_reference_count": formula_reference_count,
        "component_filter_reference_count": component_filter_reference_count,
        "dataset_field_tree_checked": bool(include_dataset_fields),
        "error_count": len(errors),
        "errors": errors,
    }


def validate_pivot_bindings(
    *,
    component_units: list[dict[str, Any]],
    pivot_units: list[dict[str, Any]],
    snapshot: dict[str, Any],
    dataset_fields: list[dict[str, Any]],
    include_dataset_fields: bool,
) -> dict[str, Any]:
    """Compatibility wrapper for callers that still provide pivot-only profiles."""

    return validate_data_component_bindings(
        component_units=component_units,
        data_units=pivot_units,
        snapshot=snapshot,
        dataset_fields=dataset_fields,
        include_dataset_fields=include_dataset_fields,
    )


def build_dashboard_snapshot(
    *,
    dashboard_id: str,
    dashboard_name: str,
    version_id: str,
    html_id: str | None,
    domain: str,
    dashboard_html: dict[str, Any],
    pivot_units: list[dict[str, Any]],
    public_filters: dict[str, Any],
    dataset_fields: list[dict[str, Any]] | None = None,
    data_units: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    effective_data_units = data_units if data_units is not None else pivot_units
    components = enrich_component_snapshot(extract_design_components(dashboard_html), effective_data_units)
    root = (dashboard_html.get("componentsTree") or [None])[0]
    root_style = (
        root.get("props", {}).get("style", {})
        if isinstance(root, dict)
        else {}
    )
    dashboard_config = (
        dashboard_html.get("config")
        if isinstance(dashboard_html.get("config"), dict)
        else {}
    )
    return {
        "dashboard": {
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_name,
            "version_id": version_id,
            "html_id": html_id,
            "domain": domain,
        },
        "components": components,
        "data_units": build_data_unit_snapshot(effective_data_units),
        "layout": [
            {
                "node_id": item["node_id"],
                "component_id": item["component_id"],
                "parent_node_id": item.get("parent_node_id"),
                "container_id": item.get("container_id"),
                "tab_id": item.get("tab_id"),
                "container_path": item.get("container_path") or [],
                **(item.get("layout") or {}),
            }
            for item in components
            if item.get("layout")
        ],
        "formulas": build_formula_snapshot(effective_data_units),
        "public_filters": build_public_filter_snapshot(public_filters),
        "component_filters": build_component_filter_snapshot(effective_data_units),
        "datasets": build_dataset_snapshot(effective_data_units, dataset_fields),
        "theme": {
            "background_color": root_style.get("backgroundColor"),
            "theme_type": dashboard_config.get("themeType"),
            "style_id": dashboard_config.get("styleId"),
        },
    }


class _PlainTextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"br", "p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n", text)
        return text.strip()


def html_to_text(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parser = _PlainTextHTMLParser()
    try:
        parser.feed(raw)
        text = parser.text()
    except Exception:  # noqa: BLE001
        text = re.sub(r"<[^>]+>", " ", raw)
        text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_edit_url(edit_url: str | None) -> dict[str, str | None]:
    if not edit_url:
        return {"dashboard_id": None, "html_id": None}
    query = parse_qs(urlparse(edit_url).query)
    return {
        "dashboard_id": (query.get("dashboardId") or [None])[0],
        "html_id": (query.get("htmlId") or [None])[0],
    }


def build_edit_url(dashboard_id: str, html_id: str | None = None) -> str:
    query: dict[str, str] = {"dashboardId": dashboard_id}
    if html_id:
        query["htmlId"] = html_id
    return f"{EDIT_DASHBOARD_URL}?{urlencode(query)}"


def extract_loaded_html_id(url: str) -> str | None:
    return parse_edit_url(url).get("html_id")


def canonical_dashboard_id(value: str) -> str:
    """Return the API dashboard identifier accepted by Taitan read endpoints."""

    dashboard_id = str(value or "").strip()
    if dashboard_id.isdigit():
        return f"dashboard_{dashboard_id}"
    return dashboard_id


def open_edit_page(page: Any, args: Any, context: Any | None, edit_url: str) -> None:
    page.goto(edit_url, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(getattr(args, "wait_ms", 3000))
    if fill_login_if_present(page, getattr(args, "username", None), getattr(args, "password", None)):
        page.wait_for_load_state("domcontentloaded", timeout=45_000)
        page.wait_for_timeout(3000)
        if context is not None:
            context.storage_state(path=str(args.state_path))
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        raise UsageError("Login failed or requires manual verification.")


def fetch_edit_dashboard_config(page: Any, dashboard_id: str, version_id: str) -> dict[str, Any]:
    payload = post_json(
        page,
        EDIT_DASHBOARD_CONFIG_API,
        {"dashboardId": dashboard_id, "isConfig": True, "versionId": version_id},
    )
    config = payload.get("data")
    if not isinstance(config, dict):
        raise UsageError(f"Dashboard edit config not found for {dashboard_id}.")
    if not config.get("htmlId") or "dashboardHtmlJson" not in config:
        raise UsageError(
            f"Dashboard edit config is incomplete for {dashboard_id}; "
            "verify that the dashboard ID is current and uses the dashboard_ prefix."
        )
    return config


def fetch_edit_unit_detail(page: Any, unit_id: str, dashboard_id: str, version_id: str) -> dict[str, Any]:
    if unit_id.startswith("public_filter_relation_"):
        payload = post_json(
            page,
            EDIT_PUBLIC_FILTER_DETAIL_API,
            {"id": unit_id, "isConfig": True, "versionId": version_id},
        )
    else:
        try:
            payload = post_json(
                page,
                EDIT_UNIT_DETAIL_API,
                {"id": unit_id, "dashboardId": dashboard_id, "versionId": version_id},
            )
        except Exception:
            payload = post_json(
                page,
                EDIT_UNIT_CONSUMER_DETAIL_API,
                {"id": unit_id, "isConfig": True, "versionId": version_id},
            )
    detail = payload.get("data")
    if not isinstance(detail, dict):
        raise UsageError(f"Edit unit detail not found for {unit_id}.")
    return detail


def render_definition(definition: Any) -> str:
    if definition in (None, "", []):
        return ""
    if isinstance(definition, list):
        return "".join(render_definition(item) for item in definition)
    if isinstance(definition, dict):
        label = str(definition.get("label") or definition.get("value") or "")
        params = definition.get("functionParams")
        if isinstance(params, list) and params:
            return f"{label}({', '.join(render_definition(item) for item in params)})"
        return label
    return str(definition)


def field_role(group_name: str, org_param_type: Any) -> str:
    if group_name in {"row_dimension", "column_dimension", "filter"}:
        return "dimension"
    if str(org_param_type) == "4":
        return "custom_measure"
    if group_name in {"measure", "aide_measure"}:
        return "measure"
    return "unknown"


def summarize_configured_field(field: dict[str, Any], group_name: str) -> dict[str, Any]:
    fmt = field.get("format") if isinstance(field.get("format"), dict) else {}
    field_id = field.get("fieldId") or field.get("paramId")
    org_param_type = fmt.get("orgParamType") or field.get("fieldType")
    definition = fmt.get("definition")
    return {
        "field_id": str(field_id) if field_id is not None else "",
        "show_name": field.get("showName") or field.get("name"),
        "group": group_name,
        "role": field_role(group_name, org_param_type),
        "field_type": field.get("fieldType"),
        "org_param_type": org_param_type,
        "change_param_type": fmt.get("changeParamType"),
        "data_type": fmt.get("dataType"),
        "measure_type": fmt.get("measureType"),
        "dimension_type": fmt.get("dimensionType"),
        "number_type": fmt.get("numberType"),
        "decimal_places": fmt.get("decimalPlaces"),
        "sort_value": field.get("sortValue"),
        "filter_type": fmt.get("filterType") or [],
        "condition": fmt.get("condition"),
        "definition": definition,
        "definition_text": render_definition(definition),
    }


def selected_field_payload(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for field in fields:
        key = str(field.get("field_id") or "")
        if not key:
            continue
        change_param_type = field.get("change_param_type")
        org_param_type = field.get("org_param_type")
        identity = (key, str(change_param_type), str(org_param_type))
        if identity in seen:
            continue
        seen.add(identity)
        selected.append(
            {
                "key": key,
                "changeParamType": change_param_type,
                "orgParamType": org_param_type,
            }
        )
    return selected


def fetch_field_detail(page: Any, field: dict[str, Any], model_type: int | None) -> dict[str, Any]:
    field_id = str(field.get("field_id") or "")
    if not field_id:
        return {}
    org_param_type = field.get("org_param_type")
    if field_id.startswith("customized_") or str(org_param_type) == "4":
        payload = post_json(page, MODEL_CUSTOM_COLUMN_API, {"id": field_id})
    elif str(org_param_type) == "2":
        payload = post_json(page, MODEL_DETAIL_DIM_API, {"id": field_id, "modelType": model_type or 2})
    else:
        payload = post_json(page, MODEL_DETAIL_METRIC_API, {"id": field_id, "modelType": model_type or 2})
    return normalize_field_detail(field_id, payload.get("data"))


def normalize_field_detail(field_id: str, data: Any) -> dict[str, Any]:
    item: dict[str, Any] = {}
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            item = first
    elif isinstance(data, dict):
        item = data
    if not item:
        return {"field_id": field_id, "detail_type": "unknown"}
    if "columnKey" in item or "formula" in item:
        return {
            "field_id": field_id,
            "detail_type": "customized_column",
            "column_key": item.get("columnKey"),
            "column_name": item.get("columnName"),
            "column_desc": item.get("columnDesc"),
            "formula": item.get("formula"),
            "indicator_type": item.get("indicatorType"),
            "dependency_indicators": item.get("dependencyIndicators") or [],
            "data_type": item.get("dataType"),
            "owner": item.get("owner") or item.get("createName") or item.get("updateName"),
            "subject_id": item.get("subjectId"),
            "create_time": item.get("createTime"),
            "update_time": item.get("updateTime"),
        }
    if "metricId" in item:
        models = item.get("modelsList") if isinstance(item.get("modelsList"), list) else []
        return {
            "field_id": field_id,
            "detail_type": "metric",
            "metric_id": item.get("metricId"),
            "name_en": item.get("nameEn"),
            "name_cn": item.get("nameCn"),
            "metric_type": item.get("type"),
            "owner": item.get("owner"),
            "models": [
                {
                    "id": model.get("id"),
                    "col_data_field": model.get("colDataField"),
                    "query_sql": model.get("querySql"),
                }
                for model in models
                if isinstance(model, dict)
            ],
            "metric_versions": item.get("metricVersionList") or [],
        }
    if "nameEn" in item or "dimsModelsVoList" in item:
        models = item.get("dimsModelsVoList") if isinstance(item.get("dimsModelsVoList"), list) else []
        return {
            "field_id": field_id,
            "detail_type": "dimension",
            "id": item.get("id"),
            "name_en": item.get("nameEn"),
            "name_cn": item.get("nameCn"),
            "data_type_code": item.get("dataTypeCode"),
            "owner": item.get("owner"),
            "models": [
                {
                    "id": model.get("id"),
                    "col_data_field": model.get("colDataField"),
                    "query_sql": model.get("querySql"),
                }
                for model in models
                if isinstance(model, dict)
            ],
        }
    return {"field_id": field_id, "detail_type": "unknown", "keys": sorted(item.keys())}


def merge_field_detail(field: dict[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    merged = dict(field)
    merged["detail"] = detail
    merged["formula"] = detail.get("formula") or field.get("definition_text") or ""
    merged["business_name"] = (
        detail.get("column_name")
        or detail.get("name_cn")
        or detail.get("name_en")
        or field.get("show_name")
    )
    merged["description"] = detail.get("column_desc") or ""
    merged["dependencies"] = detail.get("dependency_indicators") or []
    return merged


def summarize_edit_unit(
    page: Any,
    unit_detail: dict[str, Any],
    field_detail_cache: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    model_type = None
    dashboard_model = unit_detail.get("dashboardModel") if isinstance(unit_detail.get("dashboardModel"), dict) else {}
    if isinstance(dashboard_model, dict):
        model_type = dashboard_model.get("modelType")

    configured_fields: list[dict[str, Any]] = []
    for group_name, field_key in FIELD_GROUPS:
        for field in unit_detail.get(field_key) or []:
            if isinstance(field, dict):
                configured_fields.append(summarize_configured_field(field, group_name))

    merged_fields: list[dict[str, Any]] = []
    for field in configured_fields:
        field_id = str(field.get("field_id") or "")
        cache_key = (field_id, str(field.get("org_param_type") or ""))
        detail = field_detail_cache.get(cache_key)
        if detail is None:
            try:
                detail = fetch_field_detail(page, field, model_type)
            except Exception as exc:  # noqa: BLE001
                detail = {"field_id": field_id, "detail_type": "error", "message": str(exc)}
            field_detail_cache[cache_key] = detail
        merged_fields.append(merge_field_detail(field, detail))

    return {
        "unit_id": unit_detail.get("unitId"),
        "unit_name": unit_detail.get("unitName"),
        "unit_type": unit_detail.get("unitType"),
        "model_id": unit_detail.get("modelId"),
        "model_name": unit_detail.get("modelName"),
        "model_type": model_type,
        "description": unit_detail.get("description"),
        "dashboard_model": dashboard_model,
        "format_summary": summarize_unit_format(unit_detail.get("format") if isinstance(unit_detail.get("format"), dict) else {}),
        "selected_fields": selected_field_payload(merged_fields),
        "fields": merged_fields,
        "field_count": len(merged_fields),
        "measure_count": sum(1 for field in merged_fields if field.get("group") in {"measure", "aide_measure"}),
        "custom_formula_count": sum(1 for field in merged_fields if field.get("detail", {}).get("formula")),
    }


def summarize_unit_format(fmt: dict[str, Any]) -> dict[str, Any]:
    return {
        "display_setting_type": fmt.get("displaySettingType"),
        "page_size": fmt.get("pageSize"),
        "is_download": fmt.get("isDownload"),
        "is_open": fmt.get("isOpen"),
        "is_total": fmt.get("isTotal"),
        "field_measure_name_sort_list": fmt.get("fieldMeasureNameSortList") or [],
        "switch_order_list": fmt.get("switchOrderList") or [],
        "switch_groups": fmt.get("switchGroups") or [],
        "display_list_count": len(fmt.get("displayList") or []),
    }


def extract_text_notes(dashboard_html: dict[str, Any], unit_details: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_note(source: str, unit_id: str | None, value: Any) -> None:
        text = html_to_text(value)
        if not text or text in seen:
            return
        seen.add(text)
        notes.append({"source": source, "unit_id": unit_id, "text": text})

    for node in _walk_dicts(dashboard_html):
        settings = node.get("settings") if isinstance(node, dict) else None
        if not isinstance(settings, dict):
            props = node.get("props") if isinstance(node, dict) else None
            settings = props.get("settings") if isinstance(props, dict) else None
        if not isinstance(settings, dict):
            continue
        unit_id = settings.get("unitId")
        rich = settings.get("richTextFormat") if isinstance(settings.get("richTextFormat"), dict) else {}
        textbox = rich.get("textBoxConfig") if isinstance(rich.get("textBoxConfig"), dict) else {}
        add_note("dashboard_html.richTextFormat.textBoxConfig.textContent", unit_id, textbox.get("textContent"))
        add_note("dashboard_html.richTextFormat.textBoxConfig.tempTextContent", unit_id, textbox.get("tempTextContent"))

    for unit_id, detail in unit_details.items():
        fmt = detail.get("format") if isinstance(detail.get("format"), dict) else {}
        textbox = fmt.get("textBoxConfig") if isinstance(fmt.get("textBoxConfig"), dict) else {}
        add_note("unit_detail.format.textBoxConfig.textContent", unit_id, textbox.get("textContent"))
        add_note("unit_detail.format.textBoxConfig.tempTextContent", unit_id, textbox.get("tempTextContent"))
    return notes


def discover_subject_ids(*objects: Any) -> list[int]:
    subject_ids: set[int] = set()
    for obj in objects:
        for node in _walk_dicts(obj):
            value = node.get("subjectId") if isinstance(node, dict) else None
            if value is None and isinstance(node, dict):
                value = node.get("subject_id")
            if value is None:
                continue
            try:
                subject_ids.add(int(value))
            except (TypeError, ValueError):
                continue
    return sorted(subject_ids)


def flatten_param_tree(tree: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def walk(node: Any, parents: list[str]) -> None:
        if not isinstance(node, dict):
            return
        title = str(node.get("title") or node.get("name") or node.get("key") or "")
        path = parents + ([title] if title else [])
        children = node.get("children") if isinstance(node.get("children"), list) else []
        if node.get("isLeaf") or not children:
            key = node.get("key")
            if key not in {None, "dimension", "metric"}:
                rows.append(
                    {
                        "key": key,
                        "title": title,
                        "path": " / ".join(path),
                        "org_param_type": node.get("orgParamType"),
                        "change_param_type": node.get("changeParamType"),
                        "data_type": node.get("dataType"),
                        "is_choice": node.get("isChoice"),
                        "is_aggregation": node.get("isAggregation"),
                        "definition": node.get("definition"),
                        "definition_text": render_definition(node.get("definition")),
                        "filter_type": node.get("filterType") or [],
                    }
                )
        for child in children:
            walk(child, path)

    walk(tree, [])
    return rows


def fetch_dataset_fields(
    page: Any,
    dashboard_id: str,
    subject_ids: list[int],
    model_types: list[int],
    selected_fields: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    datasets: list[dict[str, Any]] = []
    if not subject_ids:
        return datasets
    model_type = model_types[0] if model_types else 2
    for subject_id in subject_ids:
        try:
            payload = post_json(
                page,
                MODEL_SUBJECT_PARAM_LIST_API,
                {
                    "modelType": model_type,
                    "dashboardId": dashboard_id,
                    "subjectId": subject_id,
                    "selected": selected_fields,
                },
            )
            tree = payload.get("data")
            datasets.append(
                {
                    "subject_id": subject_id,
                    "model_type": model_type,
                    "field_count": len(flatten_param_tree(tree)),
                    "fields": flatten_param_tree(tree),
                }
            )
        except Exception as exc:  # noqa: BLE001
            datasets.append({"subject_id": subject_id, "model_type": model_type, "error": str(exc)})
    return datasets


def profile_edit_dashboard(
    page: Any,
    dashboard_id: str,
    html_id: str | None,
    edit_url: str,
    version_id: str,
    artifacts_dir: Path,
    debug_artifacts: bool,
    include_dataset_fields: bool,
    domain: str = "unresolved",
) -> dict[str, Any]:
    config = fetch_edit_dashboard_config(page, dashboard_id, version_id)
    dashboard_html = parse_dashboard_html(config)
    component_units = extract_component_units(dashboard_html)

    unit_details: dict[str, dict[str, Any]] = {}
    public_filters: dict[str, Any] = {}
    data_units: list[dict[str, Any]] = []
    pivot_units: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    field_detail_cache: dict[tuple[str, str], dict[str, Any]] = {}

    for component in component_units:
        unit_id = str(component.get("unit_id") or "")
        if not unit_id:
            continue
        try:
            detail = fetch_edit_unit_detail(page, unit_id, dashboard_id, version_id)
            unit_details[unit_id] = detail
            if unit_id.startswith("public_filter_relation_"):
                public_filters[unit_id] = detail
                continue
            unit_type = str(detail.get("unitType") or "").lower()
            if unit_type in SUPPORTED_DATA_UNIT_TYPES:
                data_profile = summarize_edit_unit(page, detail, field_detail_cache)
                data_profile["component"] = component
                data_units.append(data_profile)
                if unit_type == "u_pivot":
                    pivot_units.append(data_profile)
        except Exception as exc:  # noqa: BLE001
            errors.append({"category": "unit", "unit_id": unit_id, "message": str(exc)})

    all_selected_fields: list[dict[str, Any]] = []
    model_types: set[int] = set()
    for unit in data_units:
        all_selected_fields.extend(unit.get("selected_fields") or [])
        model_type = unit.get("model_type")
        if model_type is not None:
            try:
                model_types.add(int(model_type))
            except (TypeError, ValueError):
                pass

    subject_ids = discover_subject_ids(public_filters, field_detail_cache, data_units)
    dataset_fields = (
        fetch_dataset_fields(page, dashboard_id, subject_ids, sorted(model_types), all_selected_fields)
        if include_dataset_fields
        else []
    )
    for unit in data_units:
        for field in unit.get("fields") or []:
            if not isinstance(field, dict):
                continue
            detail = field.get("detail") if isinstance(field.get("detail"), dict) else {}
            if detail.get("detail_type") == "error":
                errors.append(
                    {
                        "category": "field",
                        "unit_id": unit.get("unit_id"),
                        "field_id": field.get("field_id"),
                        "message": str(detail.get("message") or "Field detail fetch failed."),
                    }
                )
    for dataset in dataset_fields:
        if isinstance(dataset, dict) and dataset.get("error"):
            errors.append(
                {
                    "category": "dataset",
                    "subject_id": dataset.get("subject_id"),
                    "message": str(dataset.get("error")),
                }
            )
    text_notes = extract_text_notes(dashboard_html, unit_details)
    dashboard_name = str(config.get("dashboardName") or dashboard_id)
    measure_count = sum(int(unit.get("measure_count") or 0) for unit in data_units)
    configured_field_count = sum(int(unit.get("field_count") or 0) for unit in data_units)
    formula_count = sum(int(unit.get("custom_formula_count") or 0) for unit in data_units)
    snapshot = build_dashboard_snapshot(
        dashboard_id=dashboard_id,
        dashboard_name=dashboard_name,
        version_id=version_id,
        html_id=str(config.get("htmlId") or html_id or "") or None,
        domain=domain,
        dashboard_html=dashboard_html,
        pivot_units=pivot_units,
        data_units=data_units,
        public_filters=public_filters,
        dataset_fields=dataset_fields,
    )
    binding_validation = validate_data_component_bindings(
        component_units=component_units,
        data_units=data_units,
        snapshot=snapshot,
        dataset_fields=dataset_fields,
        include_dataset_fields=include_dataset_fields,
    )
    errors.extend(binding_validation["errors"])
    required_sections = [
        "components",
        "data_units",
        "layout",
        "formulas",
        "public_filters",
        "component_filters",
        "datasets",
        "theme",
    ]
    completeness = {
        "status": "complete" if not errors else "incomplete",
        "required": required_sections,
        "observed": list(required_sections),
        "missing": [],
        "reasons": [
            ":".join(
                str(value)
                for value in (
                    item.get("category"),
                    item.get("unit_id") or item.get("subject_id") or "unknown",
                    item.get("field_id") or "",
                    item.get("message"),
                )
                if value not in (None, "")
            )
            for item in errors
        ],
        "details": {
            "unit": {
                "attempted": sum(1 for item in component_units if item.get("unit_id")),
                "succeeded": len(unit_details),
                "error_count": sum(item.get("category") == "unit" for item in errors),
            },
            "field": {
                "attempted": configured_field_count,
                "error_count": sum(item.get("category") == "field" for item in errors),
            },
            "dataset": {
                "requested": bool(include_dataset_fields),
                "attempted": len(subject_ids) if include_dataset_fields else 0,
                "succeeded": sum(
                    1 for item in dataset_fields if isinstance(item, dict) and not item.get("error")
                ),
                "error_count": sum(item.get("category") == "dataset" for item in errors),
            },
            "bindings": {
                key: value
                for key, value in binding_validation.items()
                if key != "errors"
            },
            "errors": errors,
        },
    }

    profile = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "artifact_type": "DashboardProfile",
        "ok": True,
        "complete": not errors,
        "completeness": completeness,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "taitan_edit_readonly",
        "readonly_boundary": (
            "This profile only calls read endpoints for dashboard config, unit details, "
            "model field details, and custom formulas. It does not call save, publish, "
            "delete, create, or update endpoints."
        ),
        "input": {
            "edit_url": edit_url,
            "dashboard_id": dashboard_id,
            "html_id": html_id,
            "version_id": version_id,
        },
        "loaded_url": page.url,
        "loaded_html_id": extract_loaded_html_id(page.url),
        "dashboard_id": dashboard_id,
        "dashboard_name": dashboard_name,
        "domain": domain,
        "version_id": version_id,
        "config_html_id": config.get("htmlId"),
        "config_summary": {
            "dashboard_level": config.get("dashboardLevel"),
            "package_version": config.get("packageVersion"),
            "owner_list": config.get("ownerList") or [],
            "have_edit_permission": config.get("haveEditPermission"),
            "component_package_count": len(dashboard_html.get("componentsMap") or []),
            "component_unit_count": len(component_units),
        },
        "components": component_units,
        "component_snapshot": snapshot["components"],
        "data_unit_snapshot": snapshot["data_units"],
        "layout": snapshot["layout"],
        "formulas": snapshot["formulas"],
        "public_filters": snapshot["public_filters"],
        "component_filters": snapshot["component_filters"],
        "datasets": snapshot["datasets"],
        "theme": snapshot["theme"],
        "binding_validation": binding_validation,
        "snapshot": snapshot,
        "profile_sha256": canonical_sha256(snapshot),
        "data_units": data_units,
        "pivot_units": pivot_units,
        "public_filter_unit_count": len(public_filters),
        "subject_ids": subject_ids,
        "dataset_fields": dataset_fields,
        "text_notes": text_notes,
        "summary": {
            "data_unit_count": len(data_units),
            "data_unit_counts_by_type": {
                unit_type: sum(1 for item in data_units if item.get("unit_type") == unit_type)
                for unit_type in sorted(SUPPORTED_DATA_UNIT_TYPES)
            },
            "pivot_unit_count": len(pivot_units),
            "configured_field_count": configured_field_count,
            "measure_count": measure_count,
            "custom_formula_count": formula_count,
            "text_note_count": len(text_notes),
            "dataset_subject_count": len(dataset_fields),
            "error_count": len(errors),
            "complete": not errors,
        },
        "errors": errors,
    }
    if debug_artifacts:
        save_debug_artifacts(page, artifacts_dir, f"edit_profile_{dashboard_id}")
    return profile


def build_edit_profile_summary(profile: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = profile.get("summary") or {}
    return {
        "ok": bool(profile.get("ok") and profile.get("complete")),
        "complete": bool(profile.get("complete")),
        "dashboard_name": profile.get("dashboard_name"),
        "dashboard_id": profile.get("dashboard_id"),
        "domain": profile.get("domain"),
        "output_path": str(output_path),
        "data_unit_count": summary.get("data_unit_count", 0),
        "data_unit_counts_by_type": summary.get("data_unit_counts_by_type", {}),
        "pivot_unit_count": summary.get("pivot_unit_count", 0),
        "configured_field_count": summary.get("configured_field_count", 0),
        "measure_count": summary.get("measure_count", 0),
        "custom_formula_count": summary.get("custom_formula_count", 0),
        "text_note_count": summary.get("text_note_count", 0),
        "profile_sha256": profile.get("profile_sha256"),
        "message": (
            "Dashboard edit metric profile finished."
            if profile.get("ok") and profile.get("complete")
            else profile.get("message") or "Dashboard profile is incomplete; inspect completeness.errors."
        ),
    }


def build_edit_error_profile(
    dashboard_id: str,
    edit_url: str,
    version_id: str,
    message: str,
    domain: str = "unresolved",
) -> dict[str, Any]:
    return {
        "ok": False,
        "complete": False,
        "completeness": {
            "status": "incomplete",
            "required": [
                "components",
                "data_units",
                "layout",
                "formulas",
                "public_filters",
                "component_filters",
                "datasets",
            ],
            "observed": [],
            "missing": [
                "components",
                "data_units",
                "layout",
                "formulas",
                "public_filters",
                "component_filters",
                "datasets",
            ],
            "reasons": [message],
            "details": {"errors": [{"category": "profile", "message": message}]},
        },
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "taitan_edit_readonly",
        "input": {"edit_url": edit_url, "dashboard_id": dashboard_id, "version_id": version_id},
        "dashboard_id": dashboard_id,
        "domain": domain,
        "message": message,
    }
