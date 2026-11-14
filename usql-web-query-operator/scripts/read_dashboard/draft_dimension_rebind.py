"""Replace one period filter and its charts' row dimensions in a Taitan draft."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from _shared.errors import UsageError


OPERATION = "rebind_period_and_date_dimensions_draft"
CHART_TYPES = {"u_pivot", "u_line"}
FILTER_RUNTIME_KEYS = {"preFilterTaskId", "preFilterValueList", "preFilterSuccess"}


def require(condition: Any, message: str) -> None:
    if not condition:
        raise UsageError(message)


def filter_leaf(relation: dict[str, Any], filter_id: str) -> dict[str, Any]:
    pending = [relation]
    matches = []
    while pending:
        node = pending.pop()
        if node.get("unitId") == filter_id:
            matches.append(node)
        pending.extend(node.get("unitList") or [])
    require(len(matches) == 1, "The period filter must resolve to one existing leaf.")
    return matches[0]


def stable_unit(unit: Mapping[str, Any]) -> dict[str, Any]:
    """Ignore generated field instance keys and dynamic filter lookup results."""
    def visit(value: Any) -> Any:
        if isinstance(value, dict):
            transient = FILTER_RUNTIME_KEYS | {"uniqueKeyWithTimeStamp"}
            if value.get("dynamicsFilter") is True:
                transient |= {"filterValue"}
            return {key: visit(item) for key, item in value.items() if key not in transient}
        if isinstance(value, list):
            return [visit(item) for item in value]
        return value

    return visit(dict(unit))


def checked_field(catalog: Mapping[str, dict], field_id: str, data_type: int) -> dict:
    field = catalog.get(field_id) or {}
    require(field.get("key") == field_id and field.get("data_type") == data_type
            and field.get("org_param_type") == 2 and field.get("is_choice") is True
            and field.get("is_aggregation") is False and field.get("definition") == []
            and field.get("filter_type") == ["detailFilter"] and field.get("title"),
            f"Expected an available physical dimension with the reviewed type: {field_id}.")
    return field


def rebind_chart(unit: dict, chart: Mapping, *, dashboard_id: str, model_id: int,
                 subject_id: int, date_field: Mapping, date_label: str) -> dict:
    model = unit.get("dashboardModel") or {}
    require(unit.get("unitId") == chart["unit_id"] and unit.get("unitType") == chart["unit_type"]
            and unit.get("unitType") in CHART_TYPES and unit.get("modelId") == model_id
            and model.get("applicationModelId") == model_id and model.get("subjectId") == subject_id
            and model.get("dashboardId") == dashboard_id, "Chart or model identity drifted.")
    result = deepcopy(unit)
    dims = result.get("unitDimensionList") or []
    require(len(dims) == 1, "Only one existing row dimension may be rebound per chart.")
    old = dims[0]
    old_id = chart["from_field_id"]
    fmt = old.get("format") or {}
    require(old.get("fieldId") == old_id and old.get("fieldType") == 2 and fmt.get("dataType") == 2
            and fmt.get("definition") == [] and fmt.get("dimensionType") == "row"
            and fmt.get("isAggregation") is False and fmt.get("orgParamType") == 2
            and not old.get("filterUnitId") and fmt.get("filterType") == ["detailFilter"],
            "The reviewed source dimension must be a plain text row dimension.")
    require(not any(f.get("fieldId") == old_id for f in result.get("unitFilterList") or []),
            "An existing local filter on the source date requires separate review.")
    new_id = date_field["key"]
    old.update(fieldId=new_id, showName=date_label, sortValue="asc")
    fmt["dataType"] = date_field["data_type"]
    # Taitan's date dimension round-trip clears the text dimension's IN condition.
    fmt["condition"] = ""
    if "uniqueKeyWithTimeStamp" in old:
        key = old["uniqueKeyWithTimeStamp"]
        require(isinstance(key, str) and key.startswith(old_id + "-"), "Unexpected dimension instance key.")
        old["uniqueKeyWithTimeStamp"] = new_id + key[len(old_id):]
    return result


def _target_ids(value: Any) -> set[str]:
    if isinstance(value, str):
        return set(value.split())
    return set(value or [])


def rebind_filter(relation: dict, selection: Mapping, period_field: Mapping) -> dict:
    require(relation.get("unitId") == selection["relation_id"], "Public filter relation identity drifted.")
    result = deepcopy(relation)
    leaf = filter_leaf(result, selection["filter_id"])
    old_id = selection["period_from_field_id"]
    new_id = period_field["key"]
    targets = {chart["unit_id"] for chart in selection["charts"]}
    leaf["unitName"] = selection["period_label"]
    for key in ("relationUnit", "format"):
        binding = leaf.get(key) or {}
        params = binding.get("filterUnitParamList") or []
        dims = (binding.get("unitConfig") or {}).get("unitDimensionList") or []
        require(_target_ids(binding.get("dashboardUnitList")) == targets
                and len(params) == 1 and len(dims) == 1, "The filter target list or field scope drifted.")
        param, dim = params[0], dims[0]
        require(param.get("fieldId") == old_id and dim.get("fieldId") == old_id
                and param.get("modelId") == selection["model_id"]
                and param.get("subjectId") == selection["subject_id"]
                and _target_ids(param.get("unitIdList")) == targets
                and dim.get("filterUnitId") == selection["filter_id"], "Public filter binding identity drifted.")
        for field in (param, dim):
            fmt = field.get("format") or {}
            require(field.get("fieldType") == 2 and fmt.get("dataType") == 2
                    and fmt.get("definition") == [] and fmt.get("orgParamType") == 2,
                    "Only a text period filter can be rebound to another text period field.")
            field.update(fieldId=new_id, showName=period_field["title"])
        fmt = dim["format"]
        require(fmt.get("condition") == "in" and not fmt.get("defaultFilterValue"),
                "Only an existing IN filter without a fixed default can be rebound.")
        fmt["displayFilterName"] = selection["period_label"]
        for key in FILTER_RUNTIME_KEYS:
            fmt.pop(key, None)
        if fmt.get("dynamicsFilter") is True:
            fmt["filterValue"] = []
    return result
