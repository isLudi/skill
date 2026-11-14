"""Plan and append one same-model pivot to an existing dashboard draft."""

from __future__ import annotations

import copy
import json
import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import uuid4

from _shared.browser import import_playwright, launch_context
from _shared.config import RUNTIME_DIR
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import safe_artifact_dir

from ..common import write_json
from ..constants import UNIT_VALUE_API
from ..dashboard_change import _core_api, read_json_artifact, require_complete_profile
from ..dashboard_write_adapters import (
    UPDATE_UNIT_API,
    _formula_item,
    _recorded_post,
    _write_dashboard_schema,
    canonical_sha256,
    find_component_node,
    find_layout_item,
)
from ..edit_profile import (
    EDIT_API_ROOT,
    build_edit_url,
    fetch_edit_dashboard_config,
    fetch_edit_unit_detail,
    open_edit_page,
    profile_edit_dashboard,
)
from ..pivot_rebind import FIELD_LIST_GROUPS
from ..profile import (
    default_unit_value_payload,
    extract_component_units,
    fetch_dashboard_config,
    fetch_unit_detail,
    parse_dashboard_html,
    post_json,
)
from ..write_capabilities import capability_by_operation, load_capability_registry

CAPABILITY = "append_same_model_pivot_to_draft"
PLAN_TYPE = "DashboardPivotAppendPlan"
SELECTION_KEYS = (
    "source_dashboard_id", "source_dashboard_name", "source_unit_id", "dashboard_id",
    "expected_dashboard_name", "target_model_unit_id", "target_container_id", "title", "check_value",
)
DISPLAY_KEYS = ("pageSize", "isTotal", "isDownload", "displaySettingType", "fieldMeasureNameSortList")
FIELD_CONFIG_KEYS = (
    "dataType", "changeParamType", "orgParamType", "definition", "dimensionType", "measureType",
    "numberType", "decimalPlaces", "isAggregation", "filterType",
)
FILTER_CONFIG_KEYS = (
    "condition", "isDisplayFilter", "displayFilterName", "multipleFilter", "dynamicsFilter",
    "dynamicsFilterValue", "isSelectAll", "isShowName", "defaultFilterValue",
)
FORMULA_TOKEN = re.compile(r"\$\{[^{}]+\}|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|\w+|[^\s]")


def _need(condition: Any, message: str) -> None:
    if not condition:
        raise UsageError(message)


def _registry_hash() -> str:
    registry = load_capability_registry()
    cap = capability_by_operation(registry, CAPABILITY)
    _need(
        cap["phase"] == "draft"
        and cap["write_policy"] == "allowlisted"
        and cap["maturity"] == "verified"
        and cap["transaction_class"] == "creation_saga"
        and cap["recovery_policy"] == "creation_saga_no_auto_delete"
        and cap["readback_coverage"] == "full"
        and cap["adapter"] == f"{__name__}.cmd_append_pivot_draft"
        and set(cap["write_endpoints"]) == {"config/update/unit", "config/save/dashboardHtml"},
        "The draft pivot append adapter requires its exact verified capability.",
    )
    return registry["registry_sha256"]


def _validate_selection(selection: dict[str, str], domain: str) -> None:
    _need(set(selection) == set(SELECTION_KEYS), "Invalid pivot append selection.")
    _need(all(isinstance(v, str) and v.strip() for v in selection.values()), "Exact append identities and a check value are required.")
    _need(selection["dashboard_id"] != selection["source_dashboard_id"], "Select two distinct dashboards.")
    for key in ("source_dashboard_id", "dashboard_id"):
        dashboard_id = selection[key]
        _need(re.fullmatch(r"dashboard_\d+", dashboard_id), "Dashboard identity must use dashboard_<digits>.")
        resolution, diagnostics = _core_api().validate_dashboard_domain_registration(dashboard_id, domain)
        _need(resolution.get("status") == "registered" and not diagnostics, f"Domain registration failed for {dashboard_id}.")
    for key in ("source_unit_id", "target_model_unit_id"):
        _need(re.fullmatch(r"unit_\d+", selection[key]), "Pivot identity must use unit_<digits>.")
    _need(re.fullmatch(r"node_[a-zA-Z0-9_]+", selection["target_container_id"]), "An exact target container is required.")
    _need(not re.search(r"[<>\x00-\x1f]", selection["title"]), "The new pivot title must be plain text.")


def _draft(page: Any, dashboard_id: str, name: str, *, require_edit: bool = False) -> dict:
    config = fetch_edit_dashboard_config(page, dashboard_id, "draft")
    _need(config.get("dashboardId") == dashboard_id and config.get("dashboardName") == name, "Dashboard draft identity drifted.")
    if require_edit:
        _need(config.get("haveEditPermission") is True, "The target draft requires edit access.")
    _need(parse_dashboard_html(config).get("componentsTree"), "Dashboard draft schema is incomplete.")
    return config


def _read_profile(page: Any, dashboard_id: str, domain: str, artifacts: Path) -> tuple[dict, dict]:
    rich = profile_edit_dashboard(
        page, dashboard_id, None, build_edit_url(dashboard_id), "draft", artifacts, False, True, domain
    )
    return rich, require_complete_profile(rich)


def _unit_for_model(page: Any, schema: dict, dashboard_id: str, unit_id: str) -> tuple[dict, dict]:
    components = [c for c in extract_component_units(schema) if c.get("unit_id") == unit_id]
    _need(len(components) == 1 and components[0].get("node_component") == "PivotTable", "The selected pivot must exist in the draft schema.")
    unit = fetch_edit_unit_detail(page, unit_id, dashboard_id, "draft")
    model = unit.get("dashboardModel") or {}
    _need(
        unit.get("unitId") == unit_id and unit.get("unitType") == "u_pivot"
        and model.get("dashboardId") == dashboard_id and model.get("subjectId")
        and model.get("applicationModelId") == unit.get("modelId") and model.get("modelType") == 2,
        "Expected an exact dashboard-scoped SQL model and pivot identity.",
    )
    return unit, find_component_node(schema, components[0]["node_id"])


def _field_catalog(profile: dict, model: dict) -> dict[str, dict]:
    matches = [
        d for d in profile["dataset_fields"]
        if d.get("subject_id") == model["subjectId"] and d.get("model_type") == model["modelType"]
    ]
    _need(len(matches) == 1 and matches[0].get("fields"), "Expected a single live field tree for the selected subject.")
    fields = matches[0]["fields"]
    result = {str(f["key"]): f for f in fields}
    _need(len(result) == len(fields), "The selected subject has ambiguous field identities.")
    return result


def _formula_semantics(formula: dict) -> dict:
    text = formula.get("formula")
    _need(isinstance(text, str) and text.strip(), "The calculated field expression is missing.")
    return {
        "tokens": FORMULA_TOKEN.findall(text),
        "data_type": formula.get("dataType"),
        "indicator_type": formula.get("indicatorType"),
        "dependencies": formula.get("dependencyIndicators") or [],
        "global_filter_config": formula.get("globalFilterSpecialConfig") or [],
    }


def _resolve_fields(page: Any, source: dict, target: dict, source_catalog: dict, target_catalog: dict) -> dict:
    selected = {str(f["fieldId"]) for group in FIELD_LIST_GROUPS for f in source[group]}
    formulas = {}
    for field_id in sorted(selected):
        if not field_id.startswith("customized_"):
            continue
        origin = _formula_item(page, field_id)
        semantics = _formula_semantics(origin)
        _need(
            origin.get("columnKey") == field_id and origin.get("subjectId") == source["dashboardModel"]["subjectId"]
            and origin.get("indicatorType") == "CUSTOMIZED_MEASURE" and not semantics["global_filter_config"],
            "Only subject-owned measures with local formula dependencies are supported.",
        )
        dependencies = {str(d["paramId"]) for d in semantics["dependencies"]}
        _need(dependencies and not any(d.startswith("customized_") for d in dependencies), "Formula dependencies must resolve to physical metrics.")
        selected.update(dependencies)
        candidates = [
            f["key"] for f in target_catalog.values()
            if f.get("org_param_type") == 4 and f.get("title") == origin.get("columnName")
        ]
        _need(len(candidates) == 1, f"Expected one target formula named {origin.get('columnName')!r}.")
        match = _formula_item(page, str(candidates[0]))
        _need(
            match.get("columnKey") == candidates[0] and match.get("subjectId") == target["dashboardModel"]["subjectId"]
            and match.get("columnName") == origin.get("columnName") and _formula_semantics(match) == semantics,
            f"Target formula semantics differ for {origin.get('columnName')!r}.",
        )
        formulas[field_id] = {
            "target_field_id": match["columnKey"], "name": origin["columnName"], "formula": origin["formula"],
            "semantics_sha256": canonical_sha256(semantics),
        }
    field_keys = ("key", "title", "org_param_type", "change_param_type", "data_type", "is_aggregation")
    for field_id in selected - formulas.keys():
        left, right = source_catalog.get(field_id), target_catalog.get(field_id)
        _need(left and right and all(left.get(k) == right.get(k) for k in field_keys), f"Model field binding differs for {field_id}.")
    return formulas


def _local_filter(unit: dict, node: dict, check_value: str) -> dict:
    filters = unit.get("unitFilterList") or []
    controls = node["props"]["settings"].get("filterConfigList") or []
    _need(len(filters) == len(controls) == 1, "Expected one visible pivot-local filter and its control.")
    field, control = filters[0], controls[0]
    fmt, visual = field["format"], control["format"]
    _need(
        field["fieldId"] == control["fieldId"] and field["filterUnitId"] == control["filterUnitId"]
        and re.fullmatch(r"filter_\d+", field["filterUnitId"])
        and field.get("sortValue") == "desc" and fmt.get("orgParamType") == 2 and fmt.get("dataType") == 2
        and fmt.get("condition") == "in" and fmt.get("isDisplayFilter") == 1 and fmt.get("isSelectAll") == 0
        and fmt.get("dynamicsFilter") is True and fmt.get("dynamicsFilterValue") == "1"
        and fmt.get("filterValue") == [check_value] and not fmt.get("defaultFilterValue")
        and all(visual.get(k) == fmt.get(k) for k in ("displayFilterName", "dynamicsFilter", "dynamicsFilterValue")),
        "Expected one visible categorical filter with a verified latest-value default.",
    )
    return field


def _styled_node(source_node: dict, title: str, node_id: str) -> dict:
    _core_api()  # Load the shared package before importing its evidence-backed style preset.
    from text2sql_core.dashboard_build import STYLE_PRESETS

    node = copy.deepcopy(source_node)
    node["id"] = node_id
    props = node["props"]
    preset = STYLE_PRESETS["pivot"]["arco_blue"]
    props["pivotTableConfig"]["theme"] = preset["pivotTableConfig"]["theme"]
    for key in ("headerStyle", "cornerHeaderStyle", "rowHeaderStyle"):
        props[key]["bgColor"] = preset[key]["bgColor"]
    props["settings"].update(componentName=title, isShowComponentName=True)
    return node


def _layout_at_bottom(schema: dict, source_slot: dict, container_id: str, node_id: str) -> dict:
    container = find_component_node(schema, container_id)
    root = schema["componentsTree"]
    _need(
        len(root) == 1 and root[0].get("componentName") == "Page" and container in root[0].get("children", [])
        and container.get("componentName") == "RootContentNew" and container["props"].get("layoutMode") == "magnetic",
        "The target container must be a top-level magnetic page grid.",
    )
    layout = container["props"]["layout"]
    children = container["children"]
    ids = [child["id"] for child in children]
    slots = [slot["i"].removeprefix(".$") for slot in layout]
    _need(len(ids) == len(set(ids)) and sorted(ids) == sorted(slots) and node_id not in ids, "Grid layout and child identities must correspond one to one.")
    for slot in [*layout, source_slot]:
        _need(
            all(type(slot.get(k)) is int for k in ("x", "y", "w", "h"))
            and 0 <= slot["x"] < 24 and slot["y"] >= 0 and slot["h"] > 0 and 0 < slot["w"] <= 24 - slot["x"],
            "The pivot and existing grid slots must have valid bounds.",
        )
    bottom = max((slot["y"] + slot["h"] for slot in layout), default=0)
    return {**source_slot, "i": ".$" + node_id, "y": bottom}


def _visible_fields(unit: dict, group: str) -> list[dict]:
    fields = unit[group]
    if group == "unitDimensionList":
        local_filter_id = unit["unitFilterList"][0]["fieldId"]
        return [field for field in fields if field["fieldId"] != local_filter_id]
    return fields


def _unit_config(unit: dict) -> dict:
    config = copy.deepcopy(unit)
    # The platform starts a new task for dynamic filter values on every detail read.
    for field in config.get("unitFilterList") or []:
        (field.get("format") or {}).pop("preFilterTaskId", None)
    return config


def _value_projection(page: Any, unit: dict, check_value: str, *, draft: bool) -> dict:
    filter_field = unit["unitFilterList"][0]
    param_id = filter_field["fieldId"]
    payload = default_unit_value_payload(unit["unitId"], unit["format"]["pageSize"])
    if draft:
        payload.update(isConfig=True, versionId="draft")
    payload["filterList"] = [{
        "paramId": param_id, "filterUnitId": filter_field["filterUnitId"], "filterValue": [check_value],
        "orgParamType": filter_field["format"]["orgParamType"], "isSelectAll": 0,
    }]
    url = f"{EDIT_API_ROOT}/value/unit" if draft else UNIT_VALUE_API
    data = post_json(page, url, payload, timeout_ms=60_000)["data"]
    value = data.get(unit["unitId"]) if isinstance(data, dict) else None
    _need(isinstance(value, dict) and value.get("unitId") == unit["unitId"], "Value API did not return the exact pivot.")
    dimensions = [f["showName"] for f in _visible_fields(unit, "unitDimensionList")]
    measures = [f["showName"] for f in unit["unitMeasureList"]]
    titles = value.get("title") or []
    _need([f.get("name") for f in titles] == dimensions + measures, "Value API did not return the ordered display columns.")
    ids = [str(f.get("paramId") or "") for f in titles]
    _need(all(ids) and len(ids) == len(set(ids)), "Value API returned ambiguous result columns.")
    rows = value.get("data")
    totals = value.get("totalData")
    _need(isinstance(rows, list) and rows and value.get("hasMore") is False and isinstance(totals, dict), "A complete nonempty filtered pivot result with totals is required.")

    def number(raw: Any) -> str | None:
        if raw is None:
            return None
        try:
            numeric = Decimal(str(raw))
        except InvalidOperation as exc:
            raise UsageError("Filtered pivot returned a nonnumeric measure.") from exc
        _need(numeric.is_finite(), "Filtered pivot returned a non-finite measure.")
        return format(numeric.normalize(), "f")

    split = len(dimensions)
    _need(all(set(ids) <= row.keys() for row in rows) and set(ids[split:]) <= totals.keys(), "Filtered pivot has missing metric or dimension cells.")
    values = [
        [row[f] for f in ids[:split]] + [number(row[f]) for f in ids[split:]]
        for row in rows
    ]
    return {
        "check_value": check_value, "columns": dimensions + measures, "row_count": len(rows),
        "rows_sha256": canonical_sha256(sorted(values, key=canonical_sha256)),
        "totals": {name: number(totals[f]) for name, f in zip(measures, ids[split:])},
    }


@dataclass
class LiveAppend:
    plan: dict
    target_schema: dict
    source_unit: dict
    target_model: dict
    node: dict
    filter: dict


def _inspect(page: Any, args: Any, selection: dict, registry_hash: str, artifacts: Path) -> LiveAppend:
    s = selection
    source_id, target_id = s["source_dashboard_id"], s["dashboard_id"]
    target_config = _draft(page, target_id, s["expected_dashboard_name"], require_edit=True)
    source_config = _draft(page, source_id, s["source_dashboard_name"])
    source_schema, target_schema = map(parse_dashboard_html, (source_config, target_config))
    source, source_node = _unit_for_model(page, source_schema, source_id, s["source_unit_id"])
    anchor, _ = _unit_for_model(page, target_schema, target_id, s["target_model_unit_id"])
    model, target_model = source["dashboardModel"], anchor["dashboardModel"]
    _need(model["applicationModelId"] == target_model["applicationModelId"], "Source and target must share the same application model.")
    _need(not source["unitColumnDimensionList"] and not source["unitAideMeasureList"] and source["format"].get("isTotal") == 1, "Expected a row-only pivot with totals.")
    _need(not any(c.get("component_name") == s["title"] for c in extract_component_units(target_schema)), "A component already uses the requested title.")
    source_rich, source_profile = _read_profile(page, source_id, args.domain, artifacts)
    target_rich, target_profile = _read_profile(page, target_id, args.domain, artifacts)
    _need(not source_profile["public_filters"], "Source pivot must be independent of dashboard-wide filters.")
    filter_field = _local_filter(source, source_node, s["check_value"])
    source_published = fetch_dashboard_config(page, source_id)
    source_published_schema = parse_dashboard_html(source_published)
    _need(
        source_published.get("dashboardId") == source_id
        and any(c["unit_id"] == source["unitId"] for c in extract_component_units(source_published_schema)),
        "The source pivot must also exist in the published view.",
    )
    source_published_unit = fetch_unit_detail(page, source["unitId"])
    _need(
        source_published_unit.get("unitId") == source["unitId"]
        and source_published_unit.get("modelId") == source["modelId"]
        and source_published_unit["format"].get("isOpen") == 1,
        "The published source pivot must use the same model and an expanded view.",
    )
    formulas = _resolve_fields(page, source, anchor, _field_catalog(source_rich, model), _field_catalog(target_rich, target_model))
    before_hash = canonical_sha256(target_schema)
    node_id = "node_" + canonical_sha256([target_id, s["title"], before_hash])[:14]
    node = _styled_node(source_node, s["title"], node_id)
    slot = _layout_at_bottom(target_schema, find_layout_item(source_schema, source_node["id"]), s["target_container_id"], node_id)
    published = fetch_dashboard_config(page, target_id)
    _need(published.get("dashboardId") == target_id and parse_dashboard_html(published).get("componentsTree"), "Published target identity could not be verified.")
    plan = {
        "artifact_type": PLAN_TYPE, "schema_version": "1.0.0", "domain": args.domain, "selection": s,
        "capability_registry_sha256": registry_hash, "version_id": "draft", "publish": False,
        "source_schema_sha256": canonical_sha256(source_schema), "source_unit_sha256": canonical_sha256(_unit_config(source)),
        "source_published_schema_sha256": canonical_sha256(source_published_schema),
        "source_profile_sha256": source_profile["profile_sha256"], "target_schema_sha256": before_hash,
        "target_profile_sha256": target_profile["profile_sha256"],
        "target_units_sha256": _units_sha256(_snapshot_units(page, target_schema, target_id)),
        "target_published_schema_sha256": canonical_sha256(parse_dashboard_html(published)),
        "model_id": source["modelId"], "target_subject_id": target_model["subjectId"],
        "formula_bindings": formulas, "node_id": node_id, "layout": slot, "style": "arco_blue_header_colors",
        "field_display_names": {group: [f["showName"] for f in _visible_fields(source, group)] for group in FIELD_LIST_GROUPS},
        "local_filter": {"field_id": filter_field["fieldId"], "display_name": filter_field["format"]["displayFilterName"], "dynamic_latest": True},
    }
    return LiveAppend(plan, target_schema, source, target_model, node, filter_field)


def _fresh_field(field: dict, field_id: str) -> dict:
    result = copy.deepcopy(field)
    result["fieldId"] = field_id
    result["uniqueKeyWithTimeStamp"] = f"{field_id}-{int(time.time() * 1000)}-{uuid4().hex[:16]}-1"
    return result


def _new_filter(live: LiveAppend) -> dict:
    field = _fresh_field(live.filter, live.filter["fieldId"])
    field.pop("filterUnitId")
    fmt = field["format"]
    for key in ("preFilterValueList", "preFilterTaskId"):
        fmt.pop(key, None)
    fmt.update(filterValue=[], options=[])
    return field


def _new_pivot(live: LiveAppend, filter_field: dict) -> dict:
    source = live.source_unit
    mapped = live.plan["formula_bindings"]
    groups = {
        group: [
            _fresh_field(f, mapped.get(f["fieldId"], {}).get("target_field_id", f["fieldId"]))
            for f in _visible_fields(source, group)
        ]
        for group in FIELD_LIST_GROUPS
        if group != "unitFilterList"
    }
    return {
        "unitName": live.plan["selection"]["title"], "unitType": "u_pivot", "modelId": source["modelId"],
        "description": source.get("description") or "", **groups, "unitFilterList": [filter_field],
        "format": {**copy.deepcopy(source["format"]), "isOpen": 1},
    }


def _field_projection(field: dict, *, local_filter: bool = False) -> dict:
    keys = FIELD_CONFIG_KEYS + FILTER_CONFIG_KEYS if local_filter else FIELD_CONFIG_KEYS
    fmt = field.get("format") or {}
    projected = {key: fmt[key] for key in keys if key in fmt}
    return {
        "field_id": field.get("fieldId"), "name": field.get("showName"), "sort": field.get("sortValue"),
        "filter_id": field.get("filterUnitId"), "format": projected,
    }


def _check_pivot(actual: dict, expected: dict, unit_id: str, model: dict, check_value: str) -> None:
    _need(actual.get("unitId") == unit_id and actual.get("dashboardModel") == model, "The new unit is outside the reviewed target subject.")
    for key in ("unitType", "unitName", "modelId"):
        _need(actual.get(key) == expected[key], f"New pivot readback differs on {key}.")
    for group in FIELD_LIST_GROUPS:
        local = group == "unitFilterList"
        _need(
            [_field_projection(f, local_filter=local) for f in actual[group]]
            == [_field_projection(f, local_filter=local) for f in expected[group]],
            f"New pivot binding or display configuration differs in {group}.",
        )
    _need(
        all(actual["format"].get(k) == expected["format"].get(k) for k in DISPLAY_KEYS),
        "New pivot display settings differ from the plan.",
    )
    _need(actual["unitFilterList"][0]["format"].get("filterValue") == [check_value], "New filter default did not resolve to the verified latest value.")


def _append_schema(live: LiveAppend, unit_id: str, filter_field: dict) -> dict:
    schema = copy.deepcopy(live.target_schema)
    container = find_component_node(schema, live.plan["selection"]["target_container_id"])
    node = copy.deepcopy(live.node)
    node["props"]["settings"].update(
        unitId=unit_id, filterConfigList=[copy.deepcopy(filter_field)], refreshKey=f"{int(time.time() * 1000)}_{uuid4().hex[:9]}",
    )
    container["children"].append(node)
    container["props"]["layout"].append(copy.deepcopy(live.plan["layout"]))
    return schema


def _snapshot_units(page: Any, schema: dict, dashboard_id: str) -> dict:
    return {
        item["unit_id"]: fetch_edit_unit_detail(page, item["unit_id"], dashboard_id, "draft")
        for item in extract_component_units(schema)
    }


def _units_sha256(units: dict) -> str:
    return canonical_sha256({unit_id: _unit_config(detail) for unit_id, detail in units.items()})


def _apply(page: Any, args: Any, live: LiveAppend, artifacts: Path, receipt: dict, journal: Path) -> None:
    plan = live.plan
    s = plan["selection"]
    target_id, target_name = s["dashboard_id"], s["expected_dashboard_name"]
    check_value = s["check_value"]
    before_hash = plan["target_schema_sha256"]
    originals = _snapshot_units(page, live.target_schema, target_id)
    def existing_units_match() -> bool:
        return _units_sha256(_snapshot_units(page, live.target_schema, target_id)) == plan["target_units_sha256"]

    _need(_units_sha256(originals) == plan["target_units_sha256"], "Target unit configuration drifted before staging.")
    source_value = _value_projection(page, live.source_unit, check_value, draft=False)
    write_json(
        {"schema": live.target_schema, "units": originals, "plan_sha256": receipt["plan_sha256"]},
        journal.with_name("backup.json"),
    )

    def current_schema() -> tuple[dict, str]:
        config = _draft(page, target_id, target_name, require_edit=True)
        return config, canonical_sha256(parse_dashboard_html(config))

    def create(payload: dict, prefix: str) -> str:
        _need(current_schema()[1] == before_hash, "Target schema drifted before resource creation.")
        config, confirmed_hash = current_schema()
        _need(confirmed_hash == before_hash, "Target schema drifted during the pre-write double-read.")
        resource = {"type": payload["unitType"], "status": "outcome_unknown", "id": None}
        receipt["resources"].append(resource)
        write_json(receipt, journal)
        reply = _recorded_post(page, UPDATE_UNIT_API, {**payload, "clientType": 1, "htmlId": config["htmlId"]}, receipt["writes"])
        new_id = reply.get("data")
        _need(isinstance(new_id, str) and re.fullmatch(prefix + r"_\d+", new_id), "The create endpoint did not return a new stable resource identity.")
        _need(new_id not in originals and new_id not in json.dumps(live.source_unit), "Create returned a pre-existing resource identity.")
        resource.update(status="created", id=new_id)
        write_json(receipt, journal)
        return new_id

    projected_hash = None
    schema_attempted = False
    try:
        field = _new_filter(live)
        filter_id = create(
            {"unitType": "filter", "unitName": field["format"]["displayFilterName"], "unitDimensionList": [field]}, "filter"
        )
        field["filterUnitId"] = filter_id
        pivot = _new_pivot(live, field)
        unit_id = create(pivot, "unit")
        detail = fetch_edit_unit_detail(page, unit_id, target_id, "draft")
        _check_pivot(detail, pivot, unit_id, live.target_model, check_value)
        _need(_value_projection(page, detail, check_value, draft=True) == source_value, "Filtered values differ from the source before saving the draft.")
        schema = _append_schema(live, unit_id, field)
        projected_hash = canonical_sha256(schema)
        _need(existing_units_match(), "Existing units drifted before draft save.")
        schema_attempted = True
        receipt["expected_saved_schema_sha256"] = projected_hash
        write_json(receipt, journal)
        _write_dashboard_schema(page, target_id, target_name, schema, receipt["writes"], expected_schema_sha256=before_hash)
        _need(current_schema()[1] == projected_hash, "Saved draft schema does not match the complete projection.")
        rich, post = _read_profile(page, target_id, args.domain, artifacts)
        _need(len([c for c in post["components"] if c.get("unit_id") == unit_id]) == 1, "Complete draft profile did not resolve the new pivot.")
        detail = fetch_edit_unit_detail(page, unit_id, target_id, "draft")
        _check_pivot(detail, pivot, unit_id, live.target_model, check_value)
        observed_value = _value_projection(page, detail, check_value, draft=True)
        _need(observed_value == source_value, "Saved draft values differ from the filtered source.")
        _need(existing_units_match(), "Existing units drifted during draft verification.")
        published_hash = canonical_sha256(parse_dashboard_html(fetch_dashboard_config(page, target_id)))
        _need(published_hash == plan["target_published_schema_sha256"], "Published schema differs from the pre-write baseline.")
        _need(current_schema()[1] == projected_hash, "Draft drifted during verification.")
        write_json(rich, args.output.with_name("saved-draft-profile.json"))
        receipt.update(
            ok=True, status="saved_draft_verified", post_profile_sha256=post["profile_sha256"],
            draft_schema_sha256=projected_hash, published_schema_sha256=published_hash,
            existing_units_verified=len(originals), value_check=observed_value,
        )
    except Exception as exc:
        receipt["error"] = str(exc)
        receipt["status"] = "apply_failed"
        if schema_attempted:
            try:
                observed = current_schema()[1]
                if observed == projected_hash and existing_units_match():
                    _write_dashboard_schema(
                        page, target_id, target_name, live.target_schema, receipt["writes"], expected_schema_sha256=projected_hash
                    )
                    observed = current_schema()[1]
                _, profile = _read_profile(page, target_id, args.domain, artifacts)
                receipt["recovery"] = (
                    "baseline_verified" if observed == before_hash and profile["profile_sha256"] == plan["target_profile_sha256"]
                    else "draft_requires_review"
                )
            except Exception as recovery_error:
                receipt.update(recovery="draft_requires_review", recovery_error=str(recovery_error))
        receipt["manual_cleanup_required"] = bool(receipt["resources"])
        receipt["possible_orphan_resources"] = copy.deepcopy(receipt["resources"])


def cmd_append_pivot_draft(args: Any) -> int:
    registry_hash = _registry_hash()
    if args.command == "apply-pivot-append":
        plan = read_json_artifact(args.plan, PLAN_TYPE)
        plan_hash = canonical_sha256(plan)
        _need(
            args.confirm_production_write and plan_hash == args.plan_sha256 and plan.get("artifact_type") == PLAN_TYPE
            and plan.get("schema_version") == "1.0.0" and plan.get("version_id") == "draft" and plan.get("publish") is False
            and plan.get("domain") == args.domain and plan.get("capability_registry_sha256") == registry_hash,
            "Apply requires the reviewed draft-only plan, exact hash, current capability and confirmation.",
        )
        selection = plan.get("selection")
        _need(isinstance(selection, dict) and selection.get("dashboard_id") == args.dashboard_id
              and selection.get("expected_dashboard_name") == args.expected_dashboard_name, "Reviewed and requested target identities differ.")
    else:
        plan = None
        selection = {key: getattr(args, key) for key in SELECTION_KEYS}
    _validate_selection(selection, args.domain)
    artifacts = safe_artifact_dir(args.artifacts_dir)
    load_env_file(args.env_file)
    with import_playwright()() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            open_edit_page(page, args, context, build_edit_url(selection["dashboard_id"]))
            live = _inspect(page, args, selection, registry_hash, artifacts)
            if plan is None:
                value = _value_projection(page, live.source_unit, selection["check_value"], draft=False)
                write_json(live.plan, args.output)
                result = {"ok": True, "plan_sha256": canonical_sha256(live.plan), "value_check": value, "write_calls": 0}
            else:
                drift = sorted(key for key in live.plan.keys() | plan.keys() if live.plan.get(key) != plan.get(key))
                _need(not drift, "Source or target drifted since planning: " + ", ".join(drift))
                journal = RUNTIME_DIR / "pivot-append-attempts" / args.dashboard_id / plan_hash / "attempt.json"
                journal.parent.mkdir(parents=True, exist_ok=True)
                result = {
                    "artifact_type": "DashboardPivotAppendReceipt", "domain": args.domain, "ok": False,
                    "dashboard_id": args.dashboard_id, "plan_sha256": plan_hash, "published": False,
                    "status": "attempt_started", "resources": [], "writes": [], "journal": str(journal),
                }
                try:
                    with journal.open("x", encoding="utf-8") as handle:
                        json.dump(result, handle, ensure_ascii=False, indent=2)
                except FileExistsError as exc:
                    raise UsageError(f"An attempt already exists for this plan. Review {journal} before taking further action.") from exc
                try:
                    _apply(page, args, live, artifacts, result, journal)
                except Exception as exc:
                    result.update(status="pre_write_failed", error=str(exc))
                write_json(result, journal)
                write_json(result, args.output)
        finally:
            browser.close()
    print(json.dumps({key: value for key, value in result.items() if key != "writes"}, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1
