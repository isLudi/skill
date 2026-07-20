"""Pure-local contracts for governed P4C dashboard creation sagas.

The module deliberately contains no browser or platform I/O.  Build specs and
plans are review artifacts, never write authority.  Production callers must
still validate the live capability registry and obtain explicit confirmation.
Creation failures are represented as a saga receipt; resources are never
silently described as rolled back because P4C forbids automatic deletion.
"""

from __future__ import annotations

import copy
import html
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from .dashboard_change import artifact_sha256, canonical_sha256


SCHEMA_VERSION = "1.1.0"
SUPPORTED_DOMAINS = {"market_consultant", "qingcheng"}
COMPONENT_TYPES = {
    "metric_group": "card",
    "pivot": "u_pivot",
    "bar": "u_bar",
    "pie": "u_pie",
}
REQUIRED_CAPABILITIES = (
    "create_dashboard",
    "create_formula",
    "create_metric_group_component",
    "create_pivot_component",
    "create_bar_component",
    "create_pie_component",
    "create_public_filter",
    "assemble_new_dashboard",
)
STYLE_KEYS_BY_RESOURCE = {
    "metric_group": set(),
    "pivot": {
        "themeType",
        "pivotTableConfig",
        "headerStyle",
        "bodyStyle",
        "cornerHeaderStyle",
        "rowHeaderStyle",
        "componentOtherConfig",
        "animationAppear",
    },
    "bar": set(),
    "pie": set(),
    "tabs": {"componentOtherConfig"},
    "text": {"themeType"},
}
STYLE_PRESETS = {
    "pivot": {
        "arco_blue": {
            "themeType": "default",
            "pivotTableConfig": {
                "theme": "ARCO",
                "widthMode": "autoWidth",
                "heightMode": "autoHeight",
                "autoWrapText": True,
                "autoFillWidth": True,
                "autoFillHeight": False,
                "maxCharactersNumber": 50,
                "limitMinWidth": 10,
                "cellInnerBorder": True,
            },
            "headerStyle": {
                "padding": "[4, 6, 4, 6]",
                "textAlign": "center",
                "fontSize": 12,
                "borderColor": "",
                "bgColor": "rgba(74,144,226,0.35)",
            },
            "bodyStyle": {
                "padding": "[8, 12, 8, 12]",
                "textAlign": "center",
                "fontSize": 12,
            },
            "cornerHeaderStyle": {
                "bgColor": "rgba(74,144,226,0.26)",
                "padding": "[8, 12, 8, 12]",
                "textAlign": "center",
                "fontSize": 13,
                "lineHeight": 11,
                "fontWeight": 600,
            },
            "rowHeaderStyle": {
                "bgColor": "rgba(74,144,226,0.15)",
                "padding": "[8, 12, 8, 12]",
                "textAlign": "center",
            },
            "componentOtherConfig": {
                "componentPaddingType": "narrow",
                "titleBottomMargin": 0,
                "componentPadding": {
                    "paddingTop": "10px",
                    "paddingRight": "10px",
                    "paddingBottom": "10px",
                    "paddingLeft": "10px",
                },
            },
            "animationAppear": {
                "enable": False,
                "type": "one-by-one",
                "direction": "row",
                "duration": 500,
                "delay": 0,
            },
        }
    },
    "tabs": {
        "wide": {
            "componentOtherConfig": {
                "componentPaddingType": "wide",
                "titleBottomMargin": 14,
                "componentPadding": {
                    "paddingTop": "20px",
                    "paddingRight": "20px",
                    "paddingBottom": "20px",
                    "paddingLeft": "20px",
                },
            }
        }
    },
    "text": {"default": {"themeType": "default"}},
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
LOGICAL_ID_RE = re.compile(r"^[a-z][a-z0-9_\-]*$")


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_value(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"value is not JSON compatible: {type(value).__name__}")


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label} is required")
    return result


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _sha(value: Any, label: str, *, required: bool = True) -> str | None:
    result = _optional_text(value)
    if result is None and not required:
        return None
    if result is None or not SHA256_RE.fullmatch(result):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return result


def _logical_id(value: Any, label: str) -> str:
    result = _text(value, label)
    if not LOGICAL_ID_RE.fullmatch(result):
        raise ValueError(f"{label} must match {LOGICAL_ID_RE.pattern}")
    return result


def _unique(items: Sequence[Mapping[str, Any]], key: str, label: str) -> None:
    values = [str(item.get(key) or "") for item in items]
    duplicates = sorted({value for value in values if value and values.count(value) > 1})
    if duplicates:
        raise ValueError(f"duplicate {label}: {', '.join(duplicates)}")


def _field_ref(value: Any, label: str) -> str:
    if isinstance(value, Mapping):
        value = value.get("field_ref") or value.get("ref")
    return _text(value, label)


def _normalize_measure(value: Any, label: str) -> dict[str, Any]:
    display_name = None
    if isinstance(value, Mapping):
        display_name = _optional_text(value.get("display_name") or value.get("show_name"))
    return {
        "field_ref": _field_ref(value, f"{label}.field_ref"),
        "display_name": display_name,
    }


def _normalize_style(
    value: Any, resource_type: str, label: str, *, preset: Any = None
) -> dict[str, Any]:
    preset_name = _optional_text(preset)
    presets = STYLE_PRESETS.get(resource_type, {})
    if preset_name:
        if preset_name not in presets:
            raise ValueError(
                f"{label} uses unsupported preset {preset_name}; allowed: {', '.join(sorted(presets)) or '<none>'}"
            )
        if value not in (None, {}):
            raise ValueError(f"{label} cannot combine style_preset with a raw style object")
        return copy.deepcopy(presets[preset_name])
    if value in (None, {}):
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    allowed = STYLE_KEYS_BY_RESOURCE[resource_type]
    unknown = sorted(set(str(key) for key in value) - allowed)
    if unknown:
        raise ValueError(f"{label} contains unsupported keys: {', '.join(unknown)}")
    normalized = _json_value(value)
    if normalized not in presets.values():
        raise ValueError(
            f"{label} must exactly match an evidence-backed preset: "
            f"{', '.join(sorted(presets)) or '<none>'}"
        )
    return normalized


def _normalize_filter(item: Mapping[str, Any], label: str) -> dict[str, Any]:
    return {
        "field_ref": _field_ref(item.get("field_ref"), f"{label}.field_ref"),
        "operator": _text(item.get("operator") or "in", f"{label}.operator"),
        "values": _json_value(item.get("values", [])),
        "required": bool(item.get("required", True)),
        "config": _json_value(item.get("config", {})),
    }


def _normalize_layout(
    value: Mapping[str, Any], component_id: str, *, container_ref: str = "root"
) -> dict[str, Any]:
    def number(key: str, default: int) -> int | float:
        raw = value.get(key, default)
        if isinstance(raw, bool):
            raise ValueError(f"component {component_id} layout.{key} cannot be boolean")
        parsed = float(raw)
        return int(parsed) if parsed.is_integer() else parsed

    return {
        "container_ref": container_ref,
        "x": number("x", 0),
        "y": number("y", 0),
        "w": number("w", 6),
        "h": number("h", 6),
    }


def _normalize_dataset(item: Mapping[str, Any], domain: str) -> dict[str, Any]:
    dataset_ref = _logical_id(item.get("dataset_ref"), "dataset.dataset_ref")
    mode = _text(item.get("mode"), f"dataset {dataset_ref}.mode")
    if mode not in {"existing", "create"}:
        raise ValueError(f"dataset {dataset_ref}.mode must be existing or create")
    source_domain = str(item.get("domain") or domain)
    if source_domain != domain:
        raise ValueError(f"dataset {dataset_ref} crosses domain {source_domain} -> {domain}")
    result = {
        "dataset_ref": dataset_ref,
        "mode": mode,
        "domain": source_domain,
        "query_plan_path": _text(
            item.get("query_plan_path"), f"dataset {dataset_ref}.query_plan_path"
        ),
        "query_plan_sha256": _sha(
            item.get("query_plan_sha256"), f"dataset {dataset_ref}.query_plan_sha256"
        ),
        "dataset_spec_path": _text(
            item.get("dataset_spec_path"), f"dataset {dataset_ref}.dataset_spec_path"
        ),
        "dataset_spec_sha256": _sha(
            item.get("dataset_spec_sha256"), f"dataset {dataset_ref}.dataset_spec_sha256"
        ),
        "application_model_id": _optional_text(item.get("application_model_id")),
        "subject_id": _optional_text(item.get("subject_id")),
        "model_type": item.get("model_type"),
        "data_center_creation_plan_path": _optional_text(
            item.get("data_center_creation_plan_path")
        ),
        "data_center_creation_plan_sha256": _sha(
            item.get("data_center_creation_plan_sha256"),
            f"dataset {dataset_ref}.data_center_creation_plan_sha256",
            required=False,
        ),
        "data_center_creation_receipt_path": _optional_text(
            item.get("data_center_creation_receipt_path")
        ),
        "data_center_creation_receipt_sha256": _sha(
            item.get("data_center_creation_receipt_sha256"),
            f"dataset {dataset_ref}.data_center_creation_receipt_sha256",
            required=False,
        ),
        "config": _json_value(item.get("config", {})),
    }
    if mode == "existing" and not (result["application_model_id"] and result["subject_id"]):
        # The exact identity may be supplied by a read-only resolution artifact,
        # so this remains a planning concern rather than a malformed declaration.
        result["identity_resolution_required"] = True
    if mode == "create" and not result["data_center_creation_plan_sha256"]:
        result["creation_plan_required"] = True
    return result


def _normalize_calculated_column(item: Mapping[str, Any]) -> dict[str, Any]:
    logical_id = _logical_id(item.get("logical_id"), "calculated_column.logical_id")
    dependencies = [
        _field_ref(value, f"calculated column {logical_id}.dependencies")
        for value in item.get("dependencies", [])
    ]
    return {
        "logical_id": logical_id,
        "dataset_ref": _logical_id(
            item.get("dataset_ref"), f"calculated column {logical_id}.dataset_ref"
        ),
        "name": _text(item.get("name"), f"calculated column {logical_id}.name"),
        "data_type": _text(item.get("data_type"), f"calculated column {logical_id}.data_type"),
        "formula_template": _text(
            item.get("formula_template") or item.get("formula"),
            f"calculated column {logical_id}.formula_template",
        ),
        "dependencies": sorted(set(dependencies)),
        "config": _json_value(item.get("config", {})),
    }


def _normalize_component(item: Mapping[str, Any]) -> dict[str, Any]:
    component_id = _logical_id(item.get("component_id"), "component.component_id")
    component_type = _text(item.get("type"), f"component {component_id}.type")
    if component_type not in COMPONENT_TYPES:
        raise ValueError(f"unsupported component type: {component_type}")
    container_ref = _optional_text(item.get("container_ref"))
    slot_ref = _optional_text(item.get("slot_ref"))
    if bool(container_ref) != bool(slot_ref):
        raise ValueError(
            f"component {component_id} must declare container_ref and slot_ref together"
        )
    layout_container = f"{container_ref}:{slot_ref}" if container_ref else "root"
    measures = [
        _normalize_measure(value, f"component {component_id}.measures")
        for value in item.get("measures", [])
    ]
    measure_refs = [item["field_ref"] for item in measures]
    if len(measure_refs) != len(set(measure_refs)):
        raise ValueError(f"component {component_id} contains duplicate measures")
    local_filters = [
        _normalize_filter(value, f"component {component_id}.local_filters")
        for value in item.get("local_filters", [])
        if isinstance(value, Mapping)
    ]
    local_filter_refs = [value["field_ref"] for value in local_filters]
    if len(local_filter_refs) != len(set(local_filter_refs)):
        raise ValueError(f"component {component_id} contains duplicate local filters")
    return {
        "component_id": component_id,
        "type": component_type,
        "unit_type": COMPONENT_TYPES[component_type],
        "dataset_ref": _logical_id(
            item.get("dataset_ref"), f"component {component_id}.dataset_ref"
        ),
        "title": str(item.get("title") or ""),
        "dimensions": [
            _field_ref(value, f"component {component_id}.dimensions")
            for value in item.get("dimensions", [])
        ],
        "measures": measures,
        "local_filters": local_filters,
        "display": _json_value(item.get("display", {})),
        "style": _normalize_style(
            item.get("style", {}),
            component_type,
            f"component {component_id}.style",
            preset=item.get("style_preset"),
        ),
        "container_ref": container_ref,
        "slot_ref": slot_ref,
        "layout": _normalize_layout(
            item.get("layout") if isinstance(item.get("layout"), Mapping) else {},
            component_id,
            container_ref=layout_container,
        ),
    }


def _normalize_container(item: Mapping[str, Any]) -> dict[str, Any]:
    container_id = _logical_id(item.get("container_id"), "container.container_id")
    container_type = _text(item.get("type") or "tabs", f"container {container_id}.type")
    if container_type != "tabs":
        raise ValueError(f"unsupported container type: {container_type}")
    slots: list[dict[str, Any]] = []
    for raw_slot in item.get("slots", []):
        if not isinstance(raw_slot, Mapping):
            raise ValueError(f"container {container_id} slots must be objects")
        slots.append(
            {
                "slot_id": _logical_id(
                    raw_slot.get("slot_id"), f"container {container_id}.slot_id"
                ),
                "label": _text(
                    raw_slot.get("label"), f"container {container_id}.slot.label"
                ),
            }
        )
    if len(slots) != 2:
        raise ValueError(
            f"container {container_id} requires exactly two evidence-backed tab slots"
        )
    _unique(slots, "slot_id", f"container {container_id} slot_id")
    return {
        "container_id": container_id,
        "type": container_type,
        "component_name": "SingleTabs",
        "title": _text(item.get("title"), f"container {container_id}.title"),
        "description": str(item.get("description") or ""),
        "slots": slots,
        "style": _normalize_style(
            item.get("style", {}),
            "tabs",
            f"container {container_id}.style",
            preset=item.get("style_preset"),
        ),
        "layout": _normalize_layout(
            item.get("layout") if isinstance(item.get("layout"), Mapping) else {},
            container_id,
        ),
    }


def _normalize_text_component(item: Mapping[str, Any]) -> dict[str, Any]:
    text_id = _logical_id(item.get("text_id"), "text_component.text_id")
    initial_text = _text(
        item.get("initial_text") or item.get("text"),
        f"text component {text_id}.initial_text",
    )
    content_html = _optional_text(item.get("content_html")) or (
        f"<p>{html.escape(initial_text)}</p>"
    )
    if len(content_html.encode("utf-8")) > 20_000:
        raise ValueError(f"text component {text_id}.content_html exceeds 20 KB")
    return {
        "text_id": text_id,
        "type": "text",
        "component_name": "Text",
        "title": str(item.get("title") or ""),
        "initial_text": initial_text,
        "content_html": content_html,
        "style": _normalize_style(
            item.get("style", {}),
            "text",
            f"text component {text_id}.style",
            preset=item.get("style_preset"),
        ),
        "layout": _normalize_layout(
            item.get("layout") if isinstance(item.get("layout"), Mapping) else {},
            text_id,
        ),
    }


def _normalize_theme(value: Any) -> dict[str, Any]:
    if value in (None, {}):
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("theme must be an object")
    unknown = sorted(set(value) - {"background_color"})
    if unknown:
        raise ValueError(f"theme contains unsupported keys: {', '.join(unknown)}")
    color = _text(value.get("background_color"), "theme.background_color").upper()
    if not re.fullmatch(r"#[0-9A-F]{6}", color):
        raise ValueError("theme.background_color must be #RRGGBB")
    return {"background_color": color}


def _normalize_global_filter(item: Mapping[str, Any]) -> dict[str, Any]:
    filter_id = _logical_id(item.get("filter_id"), "global_filter.filter_id")
    return {
        "filter_id": filter_id,
        "dataset_ref": _logical_id(
            item.get("dataset_ref"), f"global filter {filter_id}.dataset_ref"
        ),
        "title": str(item.get("title") or ""),
        "field_ref": _field_ref(item.get("field_ref"), f"global filter {filter_id}.field_ref"),
        "operator": _text(item.get("operator") or "in", f"global filter {filter_id}.operator"),
        "default_values": _json_value(item.get("default_values", [])),
        "target_component_refs": sorted(
            {
                _logical_id(value, f"global filter {filter_id}.target_component_refs")
                for value in item.get("target_component_refs", [])
            }
        ),
        "config": _json_value(item.get("config", {})),
    }


def _layout_errors(components: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_container: dict[str, list[tuple[str, float, float, float, float]]] = defaultdict(list)
    for component in components:
        component_id = str(component["component_id"])
        layout = component["layout"]
        x, y, w, h = (float(layout[key]) for key in ("x", "y", "w", "h"))
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 24:
            errors.append(f"component {component_id} layout is out of bounds")
        by_container[str(layout.get("container_ref") or "root")].append((component_id, x, y, w, h))
    for container, items in by_container.items():
        for index, left in enumerate(items):
            for right in items[index + 1 :]:
                overlap = (
                    left[1] < right[1] + right[3]
                    and right[1] < left[1] + left[3]
                    and left[2] < right[2] + right[4]
                    and right[2] < left[2] + left[4]
                )
                if overlap:
                    errors.append(
                        f"components {left[0]} and {right[0]} collide in container {container}"
                    )
    return errors


def _formula_cycle_errors(columns: Sequence[Mapping[str, Any]]) -> list[str]:
    ids = {str(item["logical_id"]) for item in columns}
    graph: dict[str, set[str]] = {}
    for item in columns:
        logical_id = str(item["logical_id"])
        graph[logical_id] = {
            dependency.removeprefix("calc:")
            for dependency in item.get("dependencies", [])
            if dependency.removeprefix("calc:") in ids
        }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, path: list[str]) -> list[str] | None:
        if node in visiting:
            start = path.index(node)
            return path[start:] + [node]
        if node in visited:
            return None
        visiting.add(node)
        for dependency in sorted(graph.get(node, set())):
            cycle = visit(dependency, path + [dependency])
            if cycle:
                return cycle
        visiting.remove(node)
        visited.add(node)
        return None

    errors: list[str] = []
    for logical_id in sorted(ids):
        cycle = visit(logical_id, [logical_id])
        if cycle:
            errors.append("calculated column dependency cycle: " + " -> ".join(cycle))
            break
    return errors


def normalize_dashboard_build_spec(value: Mapping[str, Any]) -> dict[str, Any]:
    domain = _text(value.get("domain"), "domain")
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(f"unsupported dashboard-build domain: {domain}")
    folder = value.get("target_folder") if isinstance(value.get("target_folder"), Mapping) else {}
    datasets = [_normalize_dataset(item, domain) for item in value.get("datasets", [])]
    columns = [
        _normalize_calculated_column(item) for item in value.get("calculated_columns", [])
    ]
    components = [_normalize_component(item) for item in value.get("components", [])]
    containers = [_normalize_container(item) for item in value.get("containers", [])]
    text_components = [
        _normalize_text_component(item) for item in value.get("text_components", [])
    ]
    filters = [_normalize_global_filter(item) for item in value.get("global_filters", [])]
    _unique(datasets, "dataset_ref", "dataset_ref")
    _unique(columns, "logical_id", "calculated column logical_id")
    _unique(columns, "name", "calculated column name")
    _unique(components, "component_id", "component_id")
    _unique(containers, "container_id", "container_id")
    _unique(text_components, "text_id", "text component text_id")
    _unique(filters, "filter_id", "global filter_id")
    dataset_refs = {item["dataset_ref"] for item in datasets}
    component_ids = {item["component_id"] for item in components}
    container_by_id = {item["container_id"]: item for item in containers}
    for item in [*columns, *components, *filters]:
        if item["dataset_ref"] not in dataset_refs:
            raise ValueError(
                f"{item.get('logical_id') or item.get('component_id') or item.get('filter_id')} "
                f"references unknown dataset {item['dataset_ref']}"
            )
    for item in filters:
        missing = sorted(set(item["target_component_refs"]) - component_ids)
        if missing:
            raise ValueError(
                f"global filter {item['filter_id']} references unknown components: {', '.join(missing)}"
            )
        cross_dataset_targets = sorted(
            component["component_id"]
            for component in components
            if component["component_id"] in item["target_component_refs"]
            and component["dataset_ref"] != item["dataset_ref"]
        )
        if cross_dataset_targets:
            raise ValueError(
                f"global filter {item['filter_id']} targets components from another dataset: "
                + ", ".join(cross_dataset_targets)
            )
    slot_members: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for component in components:
        container_ref = component.get("container_ref")
        slot_ref = component.get("slot_ref")
        if not container_ref:
            continue
        container = container_by_id.get(str(container_ref))
        if not container:
            raise ValueError(
                f"component {component['component_id']} references unknown container {container_ref}"
            )
        slot_ids = {slot["slot_id"] for slot in container["slots"]}
        if slot_ref not in slot_ids:
            raise ValueError(
                f"component {component['component_id']} references unknown slot {slot_ref}"
            )
        if component["type"] != "pivot":
            raise ValueError(
                f"container slot component {component['component_id']} must be a pivot"
            )
        if component["local_filters"]:
            raise ValueError(
                f"container slot component {component['component_id']} cannot carry local filters; "
                "the current evidence-backed slot adapter supports pivot fields only"
            )
        slot_members[(str(container_ref), str(slot_ref))].append(component)
    for container in containers:
        for slot in container["slots"]:
            members = slot_members.get((container["container_id"], slot["slot_id"]), [])
            if len(members) != 1:
                raise ValueError(
                    f"container {container['container_id']} slot {slot['slot_id']} must contain "
                    "exactly one evidence-backed pivot"
                )
    metric_usages = [
        measure
        for component in components
        for measure in component.get("measures", [])
    ]
    named_metric_count = sum(bool(item.get("display_name")) for item in metric_usages)
    if named_metric_count not in {0, len(metric_usages)}:
        raise ValueError(
            "metric display-name changes are all-or-none; every planned measure must be named"
        )
    spec = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "dashboard_build_spec",
        "mode": "read_only_declaration",
        "domain": domain,
        "build_id": _logical_id(value.get("build_id"), "build_id"),
        "target_folder": {
            "folder_id": _text(folder.get("folder_id"), "target_folder.folder_id"),
            "folder_path": _text(folder.get("folder_path"), "target_folder.folder_path"),
            "folder_name": _text(
                folder.get("folder_name") or str(folder.get("folder_path") or "").split("/")[-1],
                "target_folder.folder_name",
            ),
        },
        "dashboard_name": _text(value.get("dashboard_name"), "dashboard_name"),
        "datasets": datasets,
        "calculated_columns": columns,
        "components": components,
        "containers": containers,
        "text_components": text_components,
        "global_filters": filters,
        "theme": _normalize_theme(value.get("theme", {})),
        "validation_checks": _json_value(value.get("validation_checks", [])),
        "publish_requested": bool(value.get("publish_requested", False)),
        "write_boundary": {
            "may_plan": True,
            "may_create_draft": False,
            "may_publish": False,
            "requires_exact_plan_sha256": True,
            "requires_production_confirmation": True,
        },
    }
    if not isinstance(spec["validation_checks"], list) or not spec["validation_checks"]:
        raise ValueError("DashboardBuildSpec requires at least one value validation check")
    if spec["publish_requested"]:
        raise ValueError("DashboardBuildSpec.publish_requested must be false")
    layout_entities = [
        *components,
        *(
            {"component_id": f"container:{item['container_id']}", "layout": item["layout"]}
            for item in containers
        ),
        *(
            {"component_id": f"text:{item['text_id']}", "layout": item["layout"]}
            for item in text_components
        ),
    ]
    structural_errors = [*_layout_errors(layout_entities), *_formula_cycle_errors(columns)]
    if structural_errors:
        raise ValueError("; ".join(structural_errors))
    if not datasets:
        raise ValueError("DashboardBuildSpec requires at least one dataset")
    if not components:
        raise ValueError("DashboardBuildSpec requires at least one component")
    spec["dashboard_build_spec_sha256"] = artifact_sha256(
        spec, "dashboard_build_spec_sha256"
    )
    return spec


def validate_dashboard_build_spec(value: Mapping[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    try:
        normalized = normalize_dashboard_build_spec(value)
    except (KeyError, TypeError, ValueError) as exc:
        return [{"severity": "error", "code": "BUILD_SPEC_INVALID", "message": str(exc)}]
    embedded = str(value.get("dashboard_build_spec_sha256") or "")
    if embedded and embedded != normalized["dashboard_build_spec_sha256"]:
        diagnostics.append(
            {
                "severity": "error",
                "code": "BUILD_SPEC_HASH_MISMATCH",
                "message": "DashboardBuildSpec SHA-256 is stale or tampered.",
            }
        )
    return diagnostics


def _resolution_by_ref(
    dataset_resolutions: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None,
) -> dict[str, Mapping[str, Any]]:
    if isinstance(dataset_resolutions, Mapping):
        items = dataset_resolutions.get("datasets", dataset_resolutions.get("resolutions", []))
    else:
        items = dataset_resolutions or []
    result: dict[str, Mapping[str, Any]] = {}
    for item in items if isinstance(items, Sequence) else []:
        if not isinstance(item, Mapping):
            continue
        dataset_ref = str(item.get("dataset_ref") or "")
        if dataset_ref:
            if dataset_ref in result:
                raise ValueError(f"duplicate dataset resolution: {dataset_ref}")
            result[dataset_ref] = item
    return result


def _field_binding_map(resolution: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in resolution.get("field_bindings", []):
        if not isinstance(item, Mapping):
            continue
        field_ref = str(item.get("field_ref") or item.get("logical_field_ref") or "")
        if field_ref:
            grouped[field_ref].append(_json_value(item))
    errors = [f"duplicate field binding: {field_ref}" for field_ref, rows in grouped.items() if len(rows) != 1]
    return {field_ref: rows[0] for field_ref, rows in grouped.items() if len(rows) == 1}, errors


def _used_field_refs(spec: Mapping[str, Any], dataset_ref: str) -> set[str]:
    refs: set[str] = set()
    for column in spec.get("calculated_columns", []):
        if column.get("dataset_ref") == dataset_ref:
            refs.update(
                dependency for dependency in column.get("dependencies", []) if not dependency.startswith("calc:")
            )
    for component in spec.get("components", []):
        if component.get("dataset_ref") != dataset_ref:
            continue
        refs.update(component.get("dimensions", []))
        refs.update(
            str(value.get("field_ref") or "")
            for value in component.get("measures", [])
            if isinstance(value, Mapping)
            and not str(value.get("field_ref") or "").startswith("calc:")
        )
        refs.update(item["field_ref"] for item in component.get("local_filters", []))
    for item in spec.get("global_filters", []):
        if item.get("dataset_ref") == dataset_ref:
            refs.add(str(item["field_ref"]))
    return refs


def build_dashboard_build_plan(
    build_spec: Mapping[str, Any],
    dataset_resolutions: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    *,
    folder_snapshot_sha256: str | None = None,
    dashboard_name_available: bool | None = None,
) -> dict[str, Any]:
    spec = normalize_dashboard_build_spec(build_spec)
    supplied_hash = str(build_spec.get("dashboard_build_spec_sha256") or "")
    if supplied_hash and supplied_hash != spec["dashboard_build_spec_sha256"]:
        raise ValueError("DashboardBuildSpec SHA-256 mismatch")
    resolutions = _resolution_by_ref(dataset_resolutions)
    pending_reasons: list[str] = []
    blocked_reasons: list[str] = []
    resolved_datasets: list[dict[str, Any]] = []
    field_maps: dict[str, dict[str, dict[str, Any]]] = {}

    for dataset in spec["datasets"]:
        dataset_ref = dataset["dataset_ref"]
        resolution = resolutions.get(dataset_ref)
        if resolution is None:
            reason = f"dataset {dataset_ref} requires a current read-only platform resolution"
            if dataset["mode"] == "create":
                pending_reasons.append(reason)
            else:
                blocked_reasons.append(reason)
            resolved_datasets.append(
                {"dataset_ref": dataset_ref, "status": "pending" if dataset["mode"] == "create" else "blocked"}
            )
            continue
        resolution_domain = str(resolution.get("domain") or spec["domain"])
        if resolution_domain != spec["domain"]:
            blocked_reasons.append(f"dataset {dataset_ref} resolution crosses domain")
        blocked_reasons.extend(
            f"dataset {dataset_ref}: {message}"
            for message in resolution.get("upstream_errors", [])
        )
        status = str(resolution.get("status") or "")
        if dataset["mode"] == "existing" and status != "ready":
            blocked_reasons.append(f"dataset {dataset_ref} platform resolution is not ready")
        if dataset["mode"] == "create":
            receipt_status = str(resolution.get("data_center_receipt_status") or "")
            sync_status = str(resolution.get("first_sync_status") or "")
            receipt_sha = _optional_text(resolution.get("data_center_creation_receipt_sha256"))
            plan_sha = _optional_text(resolution.get("data_center_creation_plan_sha256"))
            if (
                receipt_status not in {"created", "success", "applied"}
                or sync_status != "SUCCESS"
                or not dataset.get("data_center_creation_receipt_sha256")
            ):
                pending_reasons.append(
                    f"dataset {dataset_ref} is pending Data Center creation receipt and first SUCCESS"
                )
                status = "pending_dataset_creation"
            elif receipt_sha != dataset.get("data_center_creation_receipt_sha256"):
                blocked_reasons.append(f"dataset {dataset_ref} Data Center receipt SHA-256 mismatch")
            if plan_sha != dataset.get("data_center_creation_plan_sha256"):
                blocked_reasons.append(f"dataset {dataset_ref} Data Center creation plan SHA-256 mismatch")
        if resolution.get("query_plan_sha256") != dataset["query_plan_sha256"]:
            blocked_reasons.append(f"dataset {dataset_ref} QueryPlan SHA-256 mismatch")
        if resolution.get("dataset_spec_sha256") != dataset["dataset_spec_sha256"]:
            blocked_reasons.append(f"dataset {dataset_ref} DashboardDatasetSpec SHA-256 mismatch")
        if resolution.get("query_plan_status") != "executable":
            blocked_reasons.append(f"dataset {dataset_ref} QueryPlan is not executable")
        if resolution.get("dataset_spec_status") != "ready":
            blocked_reasons.append(f"dataset {dataset_ref} DashboardDatasetSpec is not ready")
        if resolution.get("contracts_confirmed") is not True:
            blocked_reasons.append(f"dataset {dataset_ref} has unconfirmed semantic contracts")
        if resolution.get("source_hashes_valid") is not True:
            blocked_reasons.append(f"dataset {dataset_ref} source hashes are not current")
        if resolution.get("dataset_fields_match") is not True:
            blocked_reasons.append(
                f"dataset {dataset_ref} DashboardDatasetSpec fields do not map one-to-one"
            )
        identity = {
            "application_model_id": _optional_text(resolution.get("application_model_id")),
            "subject_id": _optional_text(resolution.get("subject_id")),
            "model_type": resolution.get("model_type"),
        }
        if not identity["application_model_id"] or not identity["subject_id"]:
            blocked_reasons.append(f"dataset {dataset_ref} has no exact model/subject identity")
        for identity_key in ("application_model_id", "subject_id", "model_type"):
            declared = dataset.get(identity_key)
            if declared not in (None, "") and identity[identity_key] != declared:
                blocked_reasons.append(
                    f"dataset {dataset_ref} {identity_key} conflicts with the declared identity"
                )
        bindings, binding_errors = _field_binding_map(resolution)
        blocked_reasons.extend(f"dataset {dataset_ref}: {message}" for message in binding_errors)
        sorted_bindings = sorted(
            bindings.values(), key=lambda item: str(item.get("field_ref") or item.get("logical_field_ref") or "")
        )
        binding_sha = canonical_sha256(sorted_bindings)
        if resolution.get("field_binding_sha256") != binding_sha:
            blocked_reasons.append(f"dataset {dataset_ref} field_binding_sha256 drifted")
        field_tree = resolution.get("field_tree")
        if not isinstance(field_tree, list):
            field_tree = []
            blocked_reasons.append(f"dataset {dataset_ref} has no complete field tree")
        sorted_field_tree = sorted(
            (_json_value(item) for item in field_tree if isinstance(item, Mapping)),
            key=lambda item: str(item.get("field_id") or item.get("key") or ""),
        )
        schema_sha = canonical_sha256(sorted_field_tree)
        if resolution.get("dataset_schema_sha256") != schema_sha:
            blocked_reasons.append(f"dataset {dataset_ref} dataset_schema_sha256 drifted")
        field_ids_to_refs: dict[str, set[str]] = defaultdict(set)
        for field_ref, binding in bindings.items():
            field_id = str(binding.get("field_id") or "")
            if field_id:
                field_ids_to_refs[field_id].add(field_ref)
        for field_id, refs in sorted(field_ids_to_refs.items()):
            if len(refs) > 1:
                blocked_reasons.append(
                    f"dataset {dataset_ref} field_id {field_id} maps to multiple logical refs"
                )
        for field_ref in sorted(_used_field_refs(spec, dataset_ref)):
            binding = bindings.get(field_ref)
            if binding is None:
                blocked_reasons.append(f"dataset {dataset_ref} missing field binding {field_ref}")
                continue
            if not str(binding.get("field_id") or ""):
                blocked_reasons.append(f"dataset {dataset_ref} field {field_ref} has no field_id")
        dimension_groups = {"dimension", "row_dimension", "column_dimension"}
        measure_groups = {"metric", "measure", "aide_measure", "calculated", "formula"}
        filter_groups = {*dimension_groups, "filter"}
        for component in spec["components"]:
            if component["dataset_ref"] != dataset_ref:
                continue
            for field_ref in component["dimensions"]:
                group = str(bindings.get(field_ref, {}).get("field_group") or "").lower()
                if group and group not in dimension_groups:
                    blocked_reasons.append(
                        f"dataset {dataset_ref} field {field_ref} is type-incompatible with dimension"
                    )
            for measure in component["measures"]:
                field_ref = str(measure["field_ref"])
                if field_ref.startswith("calc:"):
                    continue
                group = str(bindings.get(field_ref, {}).get("field_group") or "").lower()
                if group and group not in measure_groups:
                    blocked_reasons.append(
                        f"dataset {dataset_ref} field {field_ref} is type-incompatible with measure"
                    )
            for local_filter in component["local_filters"]:
                field_ref = local_filter["field_ref"]
                group = str(bindings.get(field_ref, {}).get("field_group") or "").lower()
                if group and group not in filter_groups:
                    blocked_reasons.append(
                        f"dataset {dataset_ref} field {field_ref} is type-incompatible with local filter"
                    )
        for global_filter in spec["global_filters"]:
            if global_filter["dataset_ref"] != dataset_ref:
                continue
            field_ref = global_filter["field_ref"]
            group = str(bindings.get(field_ref, {}).get("field_group") or "").lower()
            if group and group not in filter_groups:
                blocked_reasons.append(
                    f"dataset {dataset_ref} field {field_ref} is type-incompatible with global filter"
                )
        field_maps[dataset_ref] = bindings
        resolved_datasets.append(
            {
                "dataset_ref": dataset_ref,
                "mode": dataset["mode"],
                "status": status or "ready",
                **identity,
                "query_plan_sha256": dataset["query_plan_sha256"],
                "dataset_spec_sha256": dataset["dataset_spec_sha256"],
                "data_center_creation_plan_sha256": dataset.get(
                    "data_center_creation_plan_sha256"
                ),
                "data_center_creation_receipt_sha256": dataset.get(
                    "data_center_creation_receipt_sha256"
                ),
                "dataset_schema_sha256": schema_sha,
                "field_binding_sha256": binding_sha,
                "field_bindings": sorted_bindings,
                "config": copy.deepcopy(dataset.get("config") or {}),
            }
        )

    if dashboard_name_available is not True:
        blocked_reasons.append("target dashboard name is no longer unique in the target folder")
    if folder_snapshot_sha256 is None or not SHA256_RE.fullmatch(str(folder_snapshot_sha256)):
        blocked_reasons.append("a current folder_snapshot_sha256 is required")

    resolved_columns: list[dict[str, Any]] = []
    for column in spec["calculated_columns"]:
        dependency_ids: list[str] = []
        for dependency in column["dependencies"]:
            if dependency.startswith("calc:"):
                dependency_ids.append(dependency)
                continue
            binding = field_maps.get(column["dataset_ref"], {}).get(dependency)
            if binding and binding.get("field_id"):
                dependency_ids.append(str(binding["field_id"]))
        resolved = {
            **copy.deepcopy(column),
            "dependency_field_ids": dependency_ids,
        }
        resolved["definition_sha256"] = canonical_sha256(resolved)
        resolved_columns.append(resolved)

    resolved_components: list[dict[str, Any]] = []
    for component in spec["components"]:
        bindings = field_maps.get(component["dataset_ref"], {})

        def resolve(ref: str) -> dict[str, Any]:
            if ref.startswith("calc:"):
                return {"field_ref": ref, "calculated_column_ref": ref.removeprefix("calc:")}
            return copy.deepcopy(bindings.get(ref, {"field_ref": ref, "unresolved": True}))

        resolved_measures: list[dict[str, Any]] = []
        for measure in component["measures"]:
            resolved_measure = resolve(str(measure["field_ref"]))
            resolved_measure["display_name"] = measure.get("display_name")
            resolved_measures.append(resolved_measure)
        resolved_components.append(
            {
                **copy.deepcopy(component),
                "dimensions": [resolve(ref) for ref in component["dimensions"]],
                "measures": resolved_measures,
                "local_filters": [
                    {**copy.deepcopy(item), "field": resolve(item["field_ref"])}
                    for item in component["local_filters"]
                ],
            }
        )

    resolved_filters: list[dict[str, Any]] = []
    for item in spec["global_filters"]:
        binding = field_maps.get(item["dataset_ref"], {}).get(item["field_ref"])
        resolved_filters.append(
            {
                **copy.deepcopy(item),
                "field": copy.deepcopy(binding or {"field_ref": item["field_ref"], "unresolved": True}),
            }
        )

    if blocked_reasons:
        status = "blocked"
    elif pending_reasons:
        status = "pending_dataset_creation"
    else:
        status = "ready"
    required_capabilities = {"create_dashboard", "assemble_new_dashboard"}
    required_capabilities.update(
        OPERATION
        for component_type, OPERATION in {
            "metric_group": "create_metric_group_component",
            "pivot": "create_pivot_component",
            "bar": "create_bar_component",
            "pie": "create_pie_component",
        }.items()
        if any(item["type"] == component_type for item in spec["components"])
    )
    if spec["calculated_columns"]:
        required_capabilities.add("create_formula")
    if spec["global_filters"]:
        required_capabilities.add("create_public_filter")
    if any(
        measure.get("display_name")
        for component in spec["components"]
        for measure in component["measures"]
    ):
        required_capabilities.add("rename_new_component_metrics")
    if spec["containers"]:
        required_capabilities.update({"create_tab_container", "assemble_tab_slots"})
    if spec["text_components"]:
        required_capabilities.add("create_text_component")
    if (
        any(item.get("style") for item in spec["components"])
        or any(item.get("style") for item in spec["containers"])
        or spec["text_components"]
    ):
        required_capabilities.add("style_new_components")

    plan = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "dashboard_build_plan",
        "mode": "read_only_plan",
        "domain": spec["domain"],
        "build_id": spec["build_id"],
        "dashboard_build_spec_sha256": spec["dashboard_build_spec_sha256"],
        "status": status,
        "target_folder": copy.deepcopy(spec["target_folder"]),
        "folder_snapshot_sha256": folder_snapshot_sha256,
        "dashboard_name": spec["dashboard_name"],
        "dashboard_name_available": dashboard_name_available,
        "datasets": resolved_datasets,
        "calculated_columns": resolved_columns,
        "components": resolved_components,
        "containers": copy.deepcopy(spec["containers"]),
        "text_components": copy.deepcopy(spec["text_components"]),
        "global_filters": resolved_filters,
        "theme": copy.deepcopy(spec["theme"]),
        "validation_checks": copy.deepcopy(spec["validation_checks"]),
        "required_capabilities": sorted(required_capabilities),
        "production_adapter": "taitan_dashboard_build_v1",
        "pending_reasons": sorted(set(pending_reasons)),
        "blocked_reasons": sorted(set(blocked_reasons)),
        "transaction_class": "creation_saga",
        "recovery_policy": "creation_saga_no_auto_delete",
        "write_boundary": {
            "authorizes_data_center_apply": False,
            "authorizes_dashboard_apply": False,
            "authorizes_publish": False,
            "requires_exact_plan_sha256": True,
            "requires_production_confirmation": True,
        },
    }
    plan["target_state_sha256"] = canonical_sha256(
        {
            key: plan[key]
            for key in (
                "datasets",
                "calculated_columns",
                "components",
                "containers",
                "text_components",
                "global_filters",
                "theme",
            )
        }
    )
    plan["dashboard_build_plan_sha256"] = artifact_sha256(
        plan, "dashboard_build_plan_sha256"
    )
    return plan


def validate_dashboard_build_plan(value: Mapping[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if value.get("artifact_type") != "dashboard_build_plan":
        diagnostics.append({"severity": "error", "code": "BUILD_PLAN_TYPE", "message": "artifact_type must be dashboard_build_plan"})
        return diagnostics
    actual = artifact_sha256(value, "dashboard_build_plan_sha256")
    if value.get("dashboard_build_plan_sha256") != actual:
        diagnostics.append({"severity": "error", "code": "BUILD_PLAN_HASH_MISMATCH", "message": "DashboardBuildPlan SHA-256 is stale or tampered."})
    status = str(value.get("status") or "")
    if status not in {"ready", "pending_dataset_creation", "blocked"}:
        diagnostics.append({"severity": "error", "code": "BUILD_PLAN_STATUS", "message": f"unsupported plan status: {status}"})
    if value.get("write_boundary", {}).get("authorizes_dashboard_apply") is not False:
        diagnostics.append({"severity": "error", "code": "BUILD_PLAN_AUTHORITY", "message": "DashboardBuildPlan must not authorize apply."})
    if value.get("recovery_policy") != "creation_saga_no_auto_delete":
        diagnostics.append({"severity": "error", "code": "BUILD_PLAN_RECOVERY_POLICY", "message": "P4C must use creation_saga_no_auto_delete."})
    return diagnostics


def build_dashboard_build_receipt(
    plan: Mapping[str, Any],
    *,
    operation_results: Sequence[Mapping[str, Any]],
    created_resources: Sequence[Mapping[str, Any]],
    reused_resources: Sequence[Mapping[str, Any]] = (),
    orphaned_resources: Sequence[Mapping[str, Any]] = (),
    dashboard_id: str | None = None,
    html_id: str | None = None,
    post_profile_sha256: str | None = None,
    value_checks: Sequence[Mapping[str, Any]] = (),
    global_filter_checks: Sequence[Mapping[str, Any]] = (),
    failure: str | None = None,
) -> dict[str, Any]:
    diagnostics = validate_dashboard_build_plan(plan)
    if any(item["severity"] == "error" for item in diagnostics):
        raise ValueError("invalid DashboardBuildPlan")
    operations = [_json_value(item) for item in operation_results]
    failed = [item for item in operations if str(item.get("status") or "") == "failed"]
    all_applied = bool(operations) and all(
        str(item.get("status") or "") in {"applied", "reused"} for item in operations
    )
    value_by_component = {
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
    verified_values = len(value_by_component) == len(plan.get("components") or []) and all(
        value_by_component.get(str(component["component_id"]), {}).get("ok") is True
        and value_by_component[str(component["component_id"])].get("response_shape")
        == expected_shapes[str(component["type"])]
        for component in plan.get("components") or []
    )
    filter_by_id = {
        str(item.get("filter_id") or ""): item
        for item in global_filter_checks
        if isinstance(item, Mapping)
    }
    verified_filters = len(filter_by_id) == len(plan.get("global_filters") or []) and all(
        filter_by_id.get(str(global_filter["filter_id"]), {}).get("ok") is True
        and filter_by_id[str(global_filter["filter_id"])].get("public_filter_list_applied")
        is True
        and filter_by_id[str(global_filter["filter_id"])].get("assertions_passed") is True
        for global_filter in plan.get("global_filters") or []
    )
    ok = bool(
        plan.get("status") == "ready"
        and all_applied
        and dashboard_id
        and post_profile_sha256
        and SHA256_RE.fullmatch(str(post_profile_sha256))
        and verified_values
        and verified_filters
        and not failure
    )
    status = "applied" if ok else "failed"
    orphans = [_json_value(item) for item in orphaned_resources]
    if not ok and not orphans:
        orphans = [_json_value(item) for item in created_resources]
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "dashboard_build_receipt",
        "domain": plan["domain"],
        "build_id": plan["build_id"],
        "dashboard_build_plan_sha256": plan["dashboard_build_plan_sha256"],
        "target_state_sha256": plan["target_state_sha256"],
        "status": status,
        "ok": ok,
        "dashboard_id": _optional_text(dashboard_id),
        "html_id": _optional_text(html_id),
        "dashboard_name": plan["dashboard_name"],
        "target_folder": copy.deepcopy(plan["target_folder"]),
        "operation_results": operations,
        "created_resources": [_json_value(item) for item in created_resources],
        "reused_resources": [_json_value(item) for item in reused_resources],
        "orphaned_resources": orphans,
        "manual_cleanup_required": bool(orphans),
        "failure": _optional_text(failure) or (str(failed[0].get("message") or "operation failed") if failed else None),
        "post_profile_sha256": _optional_text(post_profile_sha256),
        "verification": {
            "profile_readback_performed": bool(post_profile_sha256),
            "target_state_matches": bool(ok),
            "component_value_checks": [_json_value(item) for item in value_checks],
            "global_filter_checks": [_json_value(item) for item in global_filter_checks],
        },
        "transaction_class": "creation_saga",
        "recovery": {
            "policy": "creation_saga_no_auto_delete",
            "automatic_delete_attempted": False,
            "rolled_back": False,
        },
        "publish_boundary": {
            "published": False,
            "publish_authorized": False,
            "requires_separate_publish_confirmation": True,
        },
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    receipt["dashboard_build_receipt_sha256"] = artifact_sha256(
        receipt, "dashboard_build_receipt_sha256"
    )
    return receipt


def validate_dashboard_build_receipt(
    value: Mapping[str, Any],
    plan: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if value.get("artifact_type") != "dashboard_build_receipt":
        return [{"severity": "error", "code": "BUILD_RECEIPT_TYPE", "message": "artifact_type must be dashboard_build_receipt"}]
    if value.get("dashboard_build_receipt_sha256") != artifact_sha256(value, "dashboard_build_receipt_sha256"):
        diagnostics.append({"severity": "error", "code": "BUILD_RECEIPT_HASH_MISMATCH", "message": "DashboardBuildReceipt SHA-256 is stale or tampered."})
    if plan and value.get("dashboard_build_plan_sha256") != plan.get("dashboard_build_plan_sha256"):
        diagnostics.append({"severity": "error", "code": "BUILD_RECEIPT_PLAN_MISMATCH", "message": "DashboardBuildReceipt does not bind the supplied plan."})
    if value.get("publish_boundary", {}).get("published") is not False:
        diagnostics.append({"severity": "error", "code": "BUILD_RECEIPT_PUBLISHED", "message": "Apply receipt cannot claim publication."})
    if value.get("recovery", {}).get("automatic_delete_attempted") is not False:
        diagnostics.append({"severity": "error", "code": "BUILD_RECEIPT_AUTO_DELETE", "message": "P4C recovery must not automatically delete resources."})
    if value.get("status") == "applied" and not value.get("ok"):
        diagnostics.append({"severity": "error", "code": "BUILD_RECEIPT_STATUS", "message": "Applied receipt must be ok."})
    return diagnostics


def build_dashboard_build_publish_receipt(
    plan: Mapping[str, Any],
    build_receipt: Mapping[str, Any],
    *,
    version_description: str,
    publish_payload_sha256: str,
    pre_publish_profile_sha256: str,
    post_publish_draft_profile_sha256: str,
    platform_response_status: str = "success",
) -> dict[str, Any]:
    if validate_dashboard_build_plan(plan):
        errors = [item for item in validate_dashboard_build_plan(plan) if item["severity"] == "error"]
        if errors:
            raise ValueError("invalid DashboardBuildPlan")
    receipt_errors = [
        item
        for item in validate_dashboard_build_receipt(build_receipt, plan)
        if item["severity"] == "error"
    ]
    if receipt_errors or build_receipt.get("status") != "applied" or not build_receipt.get("ok"):
        raise ValueError("publish requires a successful DashboardBuildReceipt")
    description = _text(version_description, "version_description")
    for label, value in (
        ("publish_payload_sha256", publish_payload_sha256),
        ("pre_publish_profile_sha256", pre_publish_profile_sha256),
        ("post_publish_draft_profile_sha256", post_publish_draft_profile_sha256),
    ):
        _sha(value, label)
    if pre_publish_profile_sha256 != build_receipt.get("post_profile_sha256"):
        raise ValueError("draft profile drifted after DashboardBuildReceipt")
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "dashboard_build_publish_receipt",
        "domain": plan["domain"],
        "build_id": plan["build_id"],
        "dashboard_id": build_receipt["dashboard_id"],
        "dashboard_build_plan_sha256": plan["dashboard_build_plan_sha256"],
        "dashboard_build_receipt_sha256": build_receipt["dashboard_build_receipt_sha256"],
        "version_description": description,
        "publish_payload_sha256": publish_payload_sha256,
        "pre_publish_profile_sha256": pre_publish_profile_sha256,
        "post_publish_draft_profile_sha256": post_publish_draft_profile_sha256,
        "platform_response_status": platform_response_status,
        "publish_status": "publish_requested_unverified",
        "verification_status": "draft_only_unverified_published_version",
        "fully_verified": False,
        "confirmed": True,
        "transaction_class": "separate_publish",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    result["dashboard_build_publish_receipt_sha256"] = artifact_sha256(
        result, "dashboard_build_publish_receipt_sha256"
    )
    return result


def validate_dashboard_build_publish_receipt(
    value: Mapping[str, Any],
    build_receipt: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if value.get("artifact_type") != "dashboard_build_publish_receipt":
        return [{"severity": "error", "code": "BUILD_PUBLISH_RECEIPT_TYPE", "message": "artifact_type must be dashboard_build_publish_receipt"}]
    if value.get("dashboard_build_publish_receipt_sha256") != artifact_sha256(value, "dashboard_build_publish_receipt_sha256"):
        diagnostics.append({"severity": "error", "code": "BUILD_PUBLISH_RECEIPT_HASH_MISMATCH", "message": "DashboardBuildPublishReceipt SHA-256 is stale or tampered."})
    if build_receipt and value.get("dashboard_build_receipt_sha256") != build_receipt.get("dashboard_build_receipt_sha256"):
        diagnostics.append({"severity": "error", "code": "BUILD_PUBLISH_RECEIPT_BINDING", "message": "Publish receipt does not bind the supplied build receipt."})
    if value.get("publish_status") != "publish_requested_unverified" or value.get("fully_verified") is not False:
        diagnostics.append({"severity": "error", "code": "BUILD_PUBLISH_VERIFICATION", "message": "Published-version readback is unavailable and must remain explicitly unverified."})
    return diagnostics


__all__ = [
    "COMPONENT_TYPES",
    "REQUIRED_CAPABILITIES",
    "SCHEMA_VERSION",
    "build_dashboard_build_plan",
    "build_dashboard_build_publish_receipt",
    "build_dashboard_build_receipt",
    "normalize_dashboard_build_spec",
    "validate_dashboard_build_plan",
    "validate_dashboard_build_publish_receipt",
    "validate_dashboard_build_receipt",
    "validate_dashboard_build_spec",
]
