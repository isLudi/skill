"""Exact field-list projection for physical-metric ratios on an existing pivot."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import re
from typing import Any

from _shared.errors import UsageError


OPERATION = "configure_pivot_ratio_fields_draft"


def require(condition: Any, message: str) -> None:
    if not condition:
        raise UsageError(message)


def validate_selection(s: dict, sandbox: bool) -> None:
    required = {"domain", "dashboard_id", "dashboard_name", "owner", "model_id", "subject_id",
                "component_id", "unit_id", "unit_name", "denominator", "ratios", "remove_ids",
                "move_to_end_ids", "anchor_id", "header_color", "decimals"}
    require(set(s) == required, "The ratio Selection keys must match the documented contract.")
    require(s["domain"] == "market_consultant", "This adapter is verified for market consultant dashboards.")
    for key, prefix in (("dashboard_id", "dashboard"), ("component_id", "node"), ("unit_id", "unit")):
        suffix = r"[a-zA-Z0-9]+" if key == "component_id" else r"\d+"
        require(isinstance(s[key], str) and re.fullmatch(f"{prefix}_{suffix}", s[key]), f"Invalid {key}.")
    for key in ("dashboard_name", "owner", "unit_name"):
        require(isinstance(s[key], str) and s[key].strip() and not re.search(r"[<>\x00-\x1f]", s[key]),
                f"Invalid {key}.")
    for key in ("model_id", "subject_id"):
        require(type(s[key]) is int and s[key] > 0, f"A positive numeric {key} is required.")
    if sandbox:
        require("沙箱" in s["dashboard_name"] and "测试" in s["dashboard_name"],
                "Sandbox verification needs the exact named test sandbox.")
    require(isinstance(s["header_color"], str) and re.fullmatch(r"#[0-9a-fA-F]{6}", s["header_color"]),
            "A six-digit header color is required.")
    require(type(s["decimals"]) is int and s["decimals"] in (0, 1, 2),
            "Percentage precision must be 0, 1 or 2.")
    ratios = s["ratios"]
    require(isinstance(ratios, list) and 1 <= len(ratios) <= 12, "Provide one to twelve ratios.")
    names = []
    for ratio in ratios:
        require(isinstance(ratio, dict) and set(ratio) == {"name", "numerator"},
                "A ratio must specify exactly its name and physical numerator.")
        name = ratio["name"]
        require(isinstance(name, str) and name.strip() == name and 1 <= len(name) <= 40 and not re.search(r"[<>\x00-\x1f]", name),
                "A ratio name must be plain text.")
        names.append(name)
    require(len(names) == len(set(names)), "Ratio names must be unique.")
    inputs = [s["denominator"], *(r["numerator"] for r in ratios)]
    for value in inputs:
        require(isinstance(value, dict) and set(value) == {"field_id", "field_name"},
                "Each ratio input needs an exact physical ID and name.")
        require(isinstance(value["field_id"], str) and value["field_id"].isdigit()
                and isinstance(value["field_name"], str) and re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", value["field_name"]),
                "Only literal physical metric IDs and identifier names are supported.")
    require(len({f["field_id"] for f in inputs}) == len(inputs), "Ratio input IDs must be distinct.")
    affected = []
    for key in ("remove_ids", "move_to_end_ids"):
        items = s[key]
        require(isinstance(items, list) and all(isinstance(x, str) and re.fullmatch(r"(?:customized_)?\d+", x) for x in items),
                f"Invalid ordered {key}.")
        affected.extend(items)
    require(len(affected) == len(set(affected)), "Removal and move lists must be distinct.")
    anchor = s["anchor_id"]
    require(isinstance(anchor, str) and re.fullmatch(r"(?:customized_)?\d+", anchor) and anchor not in affected,
            "The insertion anchor must be a retained metric ID.")


def formula_definition(ratio: dict, denominator: dict, subject: int) -> dict:
    numerator = ratio["numerator"]
    numerator_name = numerator["field_name"]
    denominator_name = denominator["field_name"]
    return {
        "subjectId": subject,
        "columnKey": None,
        "columnName": ratio["name"],
        "columnDesc": "",
        "dataType": 1,
        "formula": f"ifnull(sum(${{{numerator_name}}})/sum(${{{denominator_name}}}),0)",
        "dependencyIndicators": [
            {"paramId": item["field_id"], "orgParamType": 1, "needBoundaryValue": False}
            for item in (numerator, denominator)
        ],
        "globalFilterSpecialConfig": [],
    }


def formula_matches(actual: dict, expected: dict, field_id: str) -> bool:
    # The server may reorder dependencies or omit false flags on basic metrics.
    def dependencies(item: dict) -> list[tuple]:
        return sorted((str(d.get("paramId")), d.get("orgParamType"), bool(d.get("needBoundaryValue")),
                       set(d) <= {"paramId", "orgParamType", "needBoundaryValue"})
                      for d in item.get("dependencyIndicators") or [])

    return (
        actual.get("columnKey") == field_id
        and actual.get("subjectId") == expected["subjectId"]
        and actual.get("columnName") == expected["columnName"]
        and (actual.get("columnDesc") or "") == expected["columnDesc"]
        and actual.get("dataType") == 1 and actual.get("indicatorType") == "CUSTOMIZED_MEASURE"
        and re.sub(r"\s+", "", str(actual.get("formula") or "")) == expected["formula"]
        and not actual.get("globalFilterSpecialConfig")
        and dependencies(actual) == dependencies(expected)
    )


def projection(unit: dict) -> dict:
    result = deepcopy(unit)
    for group in ("unitDimensionList", "unitColumnDimensionList", "unitMeasureList", "unitAideMeasureList", "unitFilterList"):
        for field in result.get(group) or []:
            field.pop("uniqueKeyWithTimeStamp", None)
            # The dynamic prefilter task identifier is generated on each detail read.
            (field.get("format") or {}).pop("preFilterTaskId", None)
    return result


def replace_ratio_fields(unit: dict, s: dict, added_ids: list[str], template: dict) -> dict:
    before = unit.get("unitMeasureList") or []
    by_id = {f["fieldId"]: f for f in before}
    names = [f["showName"] for f in before]
    display = unit["format"]
    require(len(by_id) == len(before) == len(set(names)) and display.get("fieldMeasureNameSortList") == names,
            "The pivot's measure IDs, names and displayed order must be unambiguous.")
    require(all(not display.get(k) for k in ("displayList", "switchGroups", "switchOrderList", "labelSelectList", "funnelConvertRateList")),
            "Selected display groups or funnel dependencies require a separate review.")
    require(not any(unit.get(k) for k in ("unitColumnDimensionList", "unitAideMeasureList", "unitFilterList")),
            "This adapter requires a row pivot with no auxiliary measures or local filters.")
    removed, moved = set(s["remove_ids"]), s["move_to_end_ids"]
    require({*removed, *moved, s["anchor_id"]} <= set(by_id), "A reviewed metric ID is absent from the pivot.")
    for field_id in removed:
        fmt = by_id[field_id].get("format") or {}
        require(field_id.startswith("customized_") and fmt.get("orgParamType") == 4
                and fmt.get("dataType") == 1 and fmt.get("numberType") == 2
                and fmt.get("isAggregation") is False and fmt.get("filterType") == ["aggregationFilter"],
                "Only existing calculated percentage measures may be removed from the pivot.")
    require(not {r["name"] for r in s["ratios"]}.intersection(names), "A proposed ratio name is already selected in the pivot.")
    require(len(added_ids) == len(set(added_ids)) == len(s["ratios"])
            and not set(added_ids).intersection(by_id)
            and all(re.fullmatch(r"customized_\d+", field_id) for field_id in added_ids),
            "The new formulas need distinct unbound calculated-measure IDs.")
    require(template.get("fieldType") == 1 and template.get("frontRender") == 0,
            "The observed calculated-measure payload is required.")
    template_fmt = template.get("format") or {}
    require(template_fmt.get("orgParamType") == template_fmt.get("changeParamType") == 4
            and template_fmt.get("numberType") == 2 and template_fmt.get("dataType") == 1
            and template_fmt.get("measureType") == "main" and template_fmt.get("isAggregation") is False
            and template_fmt.get("filterType") == ["aggregationFilter"] and not template_fmt.get("definition"),
            "The template must be a percentage calculated measure with no arbitrary definition.")
    result = deepcopy(unit)
    kept = [f for f in result["unitMeasureList"] if f["fieldId"] not in removed.union(moved)]
    insertion = [f["fieldId"] for f in kept].index(s["anchor_id"]) + 1
    result["unitMeasureList"] = (
        kept[:insertion] + [ratio_field(ratio, field_id, s, template) for ratio, field_id in zip(s["ratios"], added_ids, strict=True)]
        + kept[insertion:] + [deepcopy(by_id[field_id]) for field_id in moved]
    )
    result["format"]["fieldMeasureNameSortList"] = [f["showName"] for f in result["unitMeasureList"]]
    return result


def ratio_field(ratio: dict, field_id: str, selection: dict, template: dict) -> dict:
    style = deepcopy(template["format"].get("columnVisualStyle") or {})
    style.setdefault("header", {})["bgColor"] = selection["header_color"]
    # Keep only the observed calculated-measure format keys. The template's
    # existing formula identifier and conditional rules never travel.
    fmt = {k: template["format"][k] for k in (
        "measureType", "dataType", "numberType", "isAggregation", "changeParamType", "orgParamType", "filterType"
    )}
    fmt.update(decimalPlaces=selection["decimals"], columnVisualStyle=style)
    return {
        "fieldId": field_id, "fieldType": 1, "showName": ratio["name"], "frontRender": 0, "format": fmt,
        "uniqueKeyWithTimeStamp": f"{field_id}-pivot-ratio",
    }


def expected_rate(numerator: int, denominator: int) -> Decimal:
    require(0 <= numerator <= denominator, "A ratio numerator is outside the verified count bounds.")
    return Decimal(numerator) / Decimal(denominator) if denominator else Decimal(0)
