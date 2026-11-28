"""Helpers for sandbox-only pivot field rebinding."""

from __future__ import annotations

import copy
import re
from typing import Any, Iterable, Mapping

from _shared.errors import UsageError


FIELD_LIST_GROUPS = (
    "unitDimensionList",
    "unitColumnDimensionList",
    "unitMeasureList",
    "unitAideMeasureList",
    "unitFilterList",
)

FIELD_DISPLAY_KEYS = ("showName", "sortValue")
FIELD_FORMAT_DISPLAY_KEYS = ("sortValue", "condition")
MEASURE_NUMBER_FORMAT_KEYS = ("numberType", "numberUnit", "decimalPlaces", "columnVisualStyle")
PIVOT_SYNC_FORMAT_KEYS = (
    "displaySettingType", "switchGroups", "isDownload", "displayList",
    "switchOrderList", "pageSize", "isOpen", "isTotal",
    "funnelConvertRateList", "labelSelectList", "freezeRow",
    "fieldMeasureNameSortList",
)
FILTERED_VALUE_CHECKS_KEY = "filtered_value_checks"

PUBLIC_FILTER_FIELD_KEYS = ("fieldId", "field_id", "paramId", "param_id", "name", "field_name")
PUBLIC_FILTER_VALUE_KEYS = (
    "filterValue",
    "filter_value",
    "defaultFilterValue",
    "default_filter_value",
    "value",
    "values",
    "selectedValues",
    "selected_values",
)


def _field_id(field: Mapping[str, Any]) -> str:
    return str(field.get("fieldId") or field.get("paramId") or "").strip()


def _fields(detail: Mapping[str, Any], group: str) -> list[dict[str, Any]]:
    value = detail.get(group)
    if value is None:
        return []
    if not isinstance(value, list):
        raise UsageError(f"Unit field group must be a list: {group}")
    return [item for item in value if isinstance(item, dict)]


def _index_fields(detail: Mapping[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    indexed: dict[str, dict[str, dict[str, Any]]] = {}
    for group in FIELD_LIST_GROUPS:
        grouped: dict[str, dict[str, Any]] = {}
        for field in _fields(detail, group):
            field_id = _field_id(field)
            if not field_id:
                continue
            if field_id in grouped:
                raise UsageError(f"Duplicate field id in {group}: {field_id}")
            grouped[field_id] = field
        indexed[group] = grouped
    return indexed


def _first_field(indexed: Mapping[str, Mapping[str, dict[str, Any]]], field_id: str) -> dict[str, Any] | None:
    for group in FIELD_LIST_GROUPS:
        field = indexed.get(group, {}).get(field_id)
        if isinstance(field, dict):
            return field
    return None


def _copy_field(
    *,
    source: Mapping[str, Mapping[str, dict[str, Any]]],
    target: Mapping[str, Mapping[str, dict[str, Any]]],
    group: str,
    field_id: str,
    preserve_target_display: bool,
) -> dict[str, Any]:
    field = source.get(group, {}).get(field_id) or _first_field(source, field_id)
    if field is None:
        field = target.get(group, {}).get(field_id) or _first_field(target, field_id)
    if field is None:
        raise UsageError(f"Field id is absent from source and target unit details: {field_id}")
    copied = copy.deepcopy(field)
    if preserve_target_display:
        target_field = target.get(group, {}).get(field_id) or _first_field(target, field_id)
        if isinstance(target_field, dict):
            for key in FIELD_DISPLAY_KEYS:
                if target_field.get(key) not in (None, ""):
                    copied[key] = copy.deepcopy(target_field.get(key))
            source_format = copied.get("format")
            target_format = target_field.get("format")
            if isinstance(source_format, dict) and isinstance(target_format, dict):
                for key in FIELD_FORMAT_DISPLAY_KEYS:
                    if target_format.get(key) not in (None, ""):
                        source_format[key] = copy.deepcopy(target_format.get(key))
    return copied


def _ordered_unique(values: Iterable[str], label: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            raise UsageError(f"{label} contains an empty field id.")
        if text in seen:
            raise UsageError(f"{label} contains duplicate field id: {text}")
        seen.add(text)
        result.append(text)
    return result


def _inherit_measure_formats(
    unit: dict[str, Any], target_measures: Mapping[str, dict[str, Any]], template_ids: list[str]
) -> None:
    measures = _fields(unit, "unitMeasureList")
    if len(template_ids) != len(measures) or any(item not in target_measures for item in template_ids):
        raise UsageError("Measure formats require one reviewed target measure ID for each resulting column.")

    renamed: dict[str, str] = {}
    for measure, template_id in zip(measures, template_ids):
        template = target_measures[template_id]
        old_format = template.get("format")
        new_format = measure.get("format")
        if not isinstance(old_format, Mapping) or not isinstance(new_format, dict):
            raise UsageError("Reviewed measure formatting requires both columns to expose formats.")
        identity = ("dataType", "measureType", "orgParamType", "changeParamType")
        if old_format.get("dataType") != 1 or any(old_format.get(key) != new_format.get(key) for key in identity):
            raise UsageError("A measure format template must match the destination measure type.")
        for key in MEASURE_NUMBER_FORMAT_KEYS:
            if key in old_format:
                new_format[key] = copy.deepcopy(old_format[key])
            else:
                new_format.pop(key, None)
        old_name = template.get("showName")
        new_name = measure.get("showName")
        if isinstance(old_name, str) and isinstance(new_name, str) and old_name != new_name:
            renamed[old_name] = new_name

    format_settings = unit.get("format")
    order = format_settings.get("fieldMeasureNameSortList") if isinstance(format_settings, dict) else None
    if renamed and isinstance(order, list):
        selected = [field.get("showName") for field in measures]
        mapped_order = [renamed.get(item, item) for item in order if isinstance(item, str)]
        format_settings["fieldMeasureNameSortList"] = list(dict.fromkeys(
            [item for item in mapped_order if item in selected]
            + [item for item in selected if isinstance(item, str)]
        ))


def _cell_value(value: Any) -> Any:
    if isinstance(value, dict):
        for key in ("value", "data", "text", "label", "name", "showValue"):
            if key in value:
                return value[key]
    return value


def _contains_value(value: Any, expected: str) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_value(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(_contains_value(item, expected) for item in value)
    return str(value) == expected


def _public_filter_matches_required(payload: Any, required: Mapping[str, Any]) -> bool:
    expected_field_ids = {
        str(required.get(key)).strip()
        for key in ("field_id", "fieldId", "param_id", "paramId")
        if str(required.get(key) or "").strip()
    }
    expected_field_names = {
        str(required.get(key)).strip()
        for key in ("field_name", "name")
        if str(required.get(key) or "").strip()
    }
    expected_values = [str(value) for value in required.get("expected_values") or []]
    if not expected_values:
        raise UsageError("required_public_filters entries require non-empty expected_values.")

    def walk(value: Any) -> bool:
        if isinstance(value, Mapping):
            observed_tokens = {
                str(value.get(key)).strip()
                for key in PUBLIC_FILTER_FIELD_KEYS
                if str(value.get(key) or "").strip()
            }
            field_matches = bool(observed_tokens & (expected_field_ids | expected_field_names))
            if field_matches:
                value_payload = {key: value.get(key) for key in PUBLIC_FILTER_VALUE_KEYS if key in value}
                if all(_contains_value(value_payload, expected) for expected in expected_values):
                    return True
            return any(walk(child) for child in value.values())
        if isinstance(value, list):
            return any(walk(child) for child in value)
        return False

    return walk(payload)


def normalize_filtered_value_checks(
    manifest: Mapping[str, Any],
    operations: Iterable[Mapping[str, Any]],
    *,
    require: bool,
) -> list[dict[str, Any]]:
    """Validate manifest-driven value checks that must include public filters."""

    raw_checks = manifest.get(FILTERED_VALUE_CHECKS_KEY)
    if raw_checks in (None, []):
        if require:
            raise UsageError(
                "Production pivot rebind requires filtered_value_checks with explicit public filters; "
                "unfiltered value/unit checks are not accepted."
            )
        return []
    if not isinstance(raw_checks, list):
        raise UsageError("filtered_value_checks must be a list.")

    operation_ids = {str(item.get("operation_id") or "") for item in operations if isinstance(item, Mapping)}
    required_public_filters = manifest.get("required_public_filters") or []
    if not isinstance(required_public_filters, list):
        raise UsageError("required_public_filters must be a list when present.")

    normalized: list[dict[str, Any]] = []
    covered_operation_ids: set[str] = set()
    for index, check in enumerate(raw_checks):
        if not isinstance(check, Mapping):
            raise UsageError("filtered_value_checks entries must be JSON objects.")
        check_id = str(check.get("check_id") or f"filtered_value_check_{index + 1}").strip()
        operation_id = str(check.get("operation_id") or "").strip()
        unit_id = str(check.get("unit_id") or "").strip()
        if bool(operation_id) == bool(unit_id):
            raise UsageError(f"{check_id} requires exactly one of operation_id or unit_id.")
        if operation_id and operation_id not in operation_ids:
            raise UsageError(f"{check_id} references an unknown operation_id: {operation_id}")
        if operation_id:
            covered_operation_ids.add(operation_id)

        row_match = check.get("row_match")
        if not isinstance(row_match, Mapping) or not row_match:
            raise UsageError(f"{check_id} requires a non-empty row_match.")
        public_filter_list = check.get("public_filter_list") or []
        check_required_filters = check.get("required_public_filters") or required_public_filters
        component_period_filter = check.get("component_period_filter")
        if component_period_filter is None:
            _validate_public_filter_check(check_id, public_filter_list, check_required_filters)
        else:
            if public_filter_list or check.get("payload_overrides"):
                raise UsageError(f"{check_id} requires an isolated component period filter.")
            _validate_component_period_filter(check_id, component_period_filter, row_match)

        measure_field_id = str(check.get("measure_field_id") or "").strip()
        if not measure_field_id:
            raise UsageError(f"{check_id} requires measure_field_id.")
        if "expected_value" not in check:
            raise UsageError(f"{check_id} requires expected_value.")
        normalized.append(
            {
                "check_id": check_id,
                "operation_id": operation_id or None,
                "unit_id": unit_id or None,
                "page_size": check.get("page_size"),
                "public_filter_list": copy.deepcopy(public_filter_list),
                "required_public_filters": copy.deepcopy(check_required_filters),
                "component_period_filter": copy.deepcopy(component_period_filter),
                "row_match": {str(key): str(value) for key, value in row_match.items()},
                "measure_field_id": measure_field_id,
                "expected_value": check.get("expected_value"),
                "tolerance": float(check.get("tolerance", 0)),
                "payload_overrides": copy.deepcopy(check.get("payload_overrides") or {}),
            }
        )

    if require:
        missing = sorted(operation_ids - covered_operation_ids)
        if missing:
            raise UsageError(f"Production pivot rebind requires a filtered value check for every operation: {missing}")
    return normalized


def _validate_public_filter_check(check_id: str, public_filters: Any, required_filters: Any) -> None:
    if not isinstance(public_filters, list) or not public_filters:
        raise UsageError(f"{check_id} requires a non-empty public_filter_list or component_period_filter.")
    if any(not isinstance(item, Mapping) for item in public_filters):
        raise UsageError(f"{check_id} public_filter_list entries must be objects.")
    if not isinstance(required_filters, list) or not required_filters:
        raise UsageError(
            f"{check_id} requires required_public_filters to prove the value check is scoped "
            "to a specified period/public filter."
        )
    for required_filter in required_filters:
        if not isinstance(required_filter, Mapping):
            raise UsageError(f"{check_id} required_public_filters entries must be objects.")
        if not _public_filter_matches_required(public_filters, required_filter):
            raise UsageError(
                f"{check_id} public_filter_list does not contain required filter/value {dict(required_filter)}."
            )


def _validate_component_period_filter(
    check_id: str, period_filter: Any, row_match: Mapping[str, Any]
) -> None:
    if not isinstance(period_filter, Mapping) or set(period_filter) != {"field_id", "filter_unit_id", "value"}:
        raise UsageError(f"{check_id} requires the exact component filter ID, field ID and period value.")
    field_id = period_filter["field_id"]
    filter_id = period_filter["filter_unit_id"]
    value = period_filter["value"]
    if (
        not isinstance(field_id, str) or not field_id.isdigit()
        or not isinstance(filter_id, str) or not re.fullmatch(r"filter_\d+", filter_id)
        or not isinstance(value, str) or not value.strip() or row_match.get(field_id) != value
    ):
        raise UsageError(f"{check_id} component filter must match the exact expected row and period selection.")


def assert_filtered_value_response(
    *,
    check: Mapping[str, Any],
    unit_id: str,
    value_payload: Mapping[str, Any],
) -> dict[str, Any]:
    data = value_payload.get("data")
    unit_payload = data.get(unit_id) if isinstance(data, Mapping) else None
    if not isinstance(unit_payload, Mapping):
        raise UsageError(f"{check['check_id']} value/unit response did not contain {unit_id}.")
    rows = unit_payload.get("data")
    if not isinstance(rows, list):
        rows = []
    row_match = check.get("row_match") or {}
    matched_rows = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if all(str(_cell_value(row.get(field_id))) == str(expected) for field_id, expected in row_match.items()):
            matched_rows.append(row)
    if len(matched_rows) != 1:
        raise UsageError(
            f"{check['check_id']} expected exactly one row matching {row_match}, got {len(matched_rows)}."
        )
    row = matched_rows[0]
    measure_field_id = str(check["measure_field_id"])
    actual_value = _cell_value(row.get(measure_field_id))
    expected_value = check.get("expected_value")
    tolerance = float(check.get("tolerance") or 0)
    try:
        actual_num = float(actual_value)
        expected_num = float(expected_value)
        ok = abs(actual_num - expected_num) <= tolerance
    except (TypeError, ValueError):
        ok = str(actual_value) == str(expected_value)
    if not ok:
        raise UsageError(
            f"{check['check_id']} expected {measure_field_id}={expected_value}, got {actual_value}."
        )
    return {
        "check_id": check["check_id"],
        "unit_id": unit_id,
        "status": "passed",
        "row_match": copy.deepcopy(dict(row_match)),
        "measure_field_id": measure_field_id,
        "expected_value": expected_value,
        "actual_value": actual_value,
        "task_ids": unit_payload.get("taskIds"),
        "total_task_id": unit_payload.get("totalTaskId"),
    }


def project_unit_field_state(detail: Mapping[str, Any]) -> dict[str, Any]:
    """Return the complete write-relevant projection of configured pivot fields.

    Volatile field keys and filter-value task IDs are excluded. Formulas,
    selected filter values, number formats, and display settings are retained.
    """

    projection: dict[str, Any] = {
        "unit_id": detail.get("unitId"),
        "unit_name": detail.get("unitName"),
        "model_id": detail.get("modelId"),
        "dashboard_model": copy.deepcopy(detail.get("dashboardModel")),
        "format": {},
        "groups": {},
    }
    detail_format = detail.get("format")
    if isinstance(detail_format, Mapping):
        projection["format"] = {
            key: copy.deepcopy(detail_format.get(key))
            for key in PIVOT_SYNC_FORMAT_KEYS
            if key in detail_format
        }
    for group in FIELD_LIST_GROUPS:
        projection["groups"][group] = [
            {
                "field_id": _field_id(field),
                **{key: copy.deepcopy(value) for key, value in field.items() if key != "uniqueKeyWithTimeStamp"},
            }
            for field in _fields(detail, group)
            if _field_id(field)
        ]
    for field in projection["groups"]["unitFilterList"]:
        field_format = field.get("format")
        if isinstance(field_format, dict):
            field_format.pop("preFilterTaskId", None)
    return projection


def replace_pivot_measure_fields(
    *,
    target_detail: Mapping[str, Any],
    expected_model_id: str,
    expected_before_field_ids: Iterable[str],
    after_field_ids: Iterable[str],
    field_catalog: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Add/reorder pivot measures while preserving every existing payload.

    This is intentionally a pure, narrow primitive.  The caller must bind it
    to a full unit read, perform an immediate pre-write drift check, write the
    complete returned unit, and restore the complete original unit on any
    ambiguous failure. Each field_catalog entry separates a same-model proof
    (model_id) from a complete known-good unit-field payload. The function
    never guesses platform format/render/default keys.
    """

    model_id = str(target_detail.get("modelId") or "").strip()
    expected_model = str(expected_model_id or "").strip()
    if not expected_model or model_id != expected_model:
        raise UsageError(
            f"Pivot model mismatch: expected {expected_model or '<missing>'}, got {model_id or '<missing>'}"
        )

    before_ids = _ordered_unique(expected_before_field_ids, "expected_before_field_ids")
    after_ids = _ordered_unique(after_field_ids, "after_field_ids")
    current_fields = _fields(target_detail, "unitMeasureList")
    current_ids = [_field_id(field) for field in current_fields]
    if any(not field_id for field_id in current_ids):
        raise UsageError("unitMeasureList contains a measure without a stable field id.")
    if current_ids != before_ids:
        raise UsageError(
            "Pivot measure order drifted; exact expected_before_field_ids no longer match the unit."
        )
    if set(before_ids) - set(after_ids):
        raise UsageError("Pivot measure replacement cannot remove existing measures.")
    if before_ids == after_ids:
        raise UsageError("Pivot measure replacement must add or reorder at least one measure.")

    existing = dict(zip(current_ids, current_fields, strict=True))
    additions = set(after_ids) - set(before_ids)
    for field_id in additions:
        candidate = field_catalog.get(field_id)
        if not isinstance(candidate, Mapping):
            raise UsageError(f"Added measure is absent from the model field catalog: {field_id}")
        candidate_model = str(candidate.get("model_id") or "").strip()
        payload = candidate.get("payload")
        if not isinstance(payload, Mapping):
            raise UsageError(f"Added measure lacks a complete field payload: {field_id}")
        if _field_id(payload) != field_id:
            raise UsageError(f"Field catalog identity mismatch for added measure: {field_id}")
        if candidate_model != expected_model:
            raise UsageError(
                f"Added measure {field_id} belongs to model {candidate_model or '<missing>'}, "
                f"not {expected_model}."
            )
        required_payload_keys = {
            "fieldId", "fieldType", "format", "frontRender", "showName", "uniqueKeyWithTimeStamp"
        }
        missing_keys = sorted(required_payload_keys - set(payload))
        if missing_keys or not isinstance(payload.get("format"), Mapping):
            raise UsageError(
                f"Added measure {field_id} has an incomplete unit-field payload: {missing_keys}"
            )
        payload_format = payload["format"]
        if (
            not field_id.isdigit()
            or str(payload_format.get("orgParamType") or "") != "1"
            or str(payload_format.get("changeParamType") or "") != "1"
        ):
            raise UsageError(f"Added measure {field_id} is not a verified atomic metric payload.")

    rebuilt = copy.deepcopy(dict(target_detail))
    rebuilt["unitMeasureList"] = [
        copy.deepcopy(existing[field_id])
        if field_id in existing
        else copy.deepcopy(dict(field_catalog[field_id]["payload"]))
        for field_id in after_ids
    ]
    return rebuilt


def rebuild_pivot_unit_fields(
    *,
    target_detail: Mapping[str, Any],
    source_detail: Mapping[str, Any],
    dimension_field_ids: Iterable[str],
    measure_mode: str = "source_all",
    measure_field_ids: Iterable[str] | None = None,
    required_measure_field_ids: Iterable[str] = (),
    preserve_target_display: bool = True,
    dimension_show_names: Mapping[str, str] | None = None,
    dimension_sort_values: Mapping[str, str] | None = None,
    measure_show_names: Mapping[str, str] | None = None,
    sync_source_format: bool = False,
    target_measure_format_ids: Iterable[str] | None = None,
    append_source_measure_names: Iterable[str] = (),
    insert_before_field_id: str | None = None,
    append_measure_format: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Rebuild a target pivot's field lists from a known-good source unit.

    This updates field-list groups and, when explicitly requested, a narrow
    allowlist of pivot display settings. The caller owns the write boundary,
    backup, drift checks, and recovery.
    """

    target_model = target_detail.get("modelId")
    source_model = source_detail.get("modelId")
    if target_model not in (None, "") and source_model not in (None, "") and str(target_model) != str(source_model):
        raise UsageError(f"Source/target model mismatch: {source_model} vs {target_model}")

    if measure_mode == "append_source":
        # Existing pivots can select the same physical field twice (for example
        # a count and its percentage calculation). Keep those instances intact.
        dimensions = _ordered_unique(dimension_field_ids, "dimension_field_ids")
        if dimensions != [_field_id(f) for f in _fields(target_detail, "unitDimensionList")]:
            raise UsageError("Append-only sync must retain the complete existing dimension order.")
        if (
            sync_source_format or target_measure_format_ids or measure_show_names
            or dimension_show_names or dimension_sort_values or measure_field_ids
            or preserve_target_display is not True
        ):
            raise UsageError("Append-only sync retains existing field formats and names.")
        names = _ordered_unique(append_source_measure_names, "append_source_measure_names")
        if not names or not insert_before_field_id:
            raise UsageError("Append-only sync requires selected source measures and one insertion anchor.")
        new_format = dict(append_measure_format or {})
        if set(new_format) - {"numberType", "decimalPlaces"} or (
            "numberType" in new_format and (
                type(new_format["numberType"]) is not int or new_format["numberType"] not in (1, 2)
            )
        ) or (
            "decimalPlaces" in new_format and (
                type(new_format["decimalPlaces"]) is not int or not 0 <= new_format["decimalPlaces"] <= 6
            )
        ):
            raise UsageError("Appended number formats require numeric/percent type and zero to six decimals.")
        before = _fields(target_detail, "unitMeasureList")
        positions = [i for i, f in enumerate(before) if _field_id(f) == insert_before_field_id]
        if len(positions) != 1:
            raise UsageError("Append-only insertion anchor must match exactly one existing measure.")
        existing_ids = {_field_id(f) for f in before}
        existing_names = {f.get("showName") for f in before}
        added = []
        for name in names:
            matches = [f for f in _fields(source_detail, "unitMeasureList") if f.get("showName") == name]
            if len(matches) != 1 or name in existing_names or _field_id(matches[0]) in existing_ids:
                raise UsageError("Appended source measures must have unique unselected names and identities.")
            entry = copy.deepcopy(matches[0])
            if new_format:
                if entry.get("fieldType") != 1 or entry.get("format", {}).get("dataType") != 1:
                    raise UsageError("Only appended numeric measures can receive a number format.")
                entry["format"].update(new_format)
            added.append(entry)
        if len({_field_id(f) for f in added}) != len(added):
            raise UsageError("Appended source measure identities must be distinct.")
        result = copy.deepcopy(dict(target_detail))
        anchor = positions[0]
        result["unitMeasureList"][anchor:anchor] = added
        order = result.get("format", {}).get("fieldMeasureNameSortList")
        if order != [f.get("showName") for f in before]:
            raise UsageError("Append-only sync requires an exact current displayed measure order.")
        result["format"]["fieldMeasureNameSortList"] = [f.get("showName") for f in result["unitMeasureList"]]
        actual_ids = {_field_id(f) for f in result["unitMeasureList"]}
        if not set(required_measure_field_ids).issubset(actual_ids):
            raise UsageError("Required measure fields are missing after append.")
        return result

    dimensions = _ordered_unique(dimension_field_ids, "dimension_field_ids")
    explicit_measures = _ordered_unique(measure_field_ids or [], "measure_field_ids")
    required_measures = _ordered_unique(required_measure_field_ids, "required_measure_field_ids")
    if measure_mode not in {"source_all", "target_all", "explicit"}:
        raise UsageError("measure_mode must be one of source_all, target_all, or explicit.")
    if measure_mode == "explicit" and not explicit_measures:
        raise UsageError("measure_mode=explicit requires measure_field_ids.")

    target_index = _index_fields(target_detail)
    source_index = _index_fields(source_detail)
    rebuilt = copy.deepcopy(dict(target_detail))
    rebuilt["unitDimensionList"] = [
        _copy_field(
            source=source_index,
            target=target_index,
            group="unitDimensionList",
            field_id=field_id,
            preserve_target_display=preserve_target_display,
        )
        for field_id in dimensions
    ]
    show_names = {str(key): str(value).strip() for key, value in (dimension_show_names or {}).items()}
    unknown_show_names = sorted(set(show_names) - set(dimensions))
    if unknown_show_names:
        raise UsageError(f"dimension_show_names contains fields outside dimension_field_ids: {unknown_show_names}")
    if any(not value for value in show_names.values()):
        raise UsageError("dimension_show_names cannot contain an empty display name.")
    for field in rebuilt["unitDimensionList"]:
        field_id = _field_id(field)
        if field_id in show_names:
            field["showName"] = show_names[field_id]
    sort_values = dict(dimension_sort_values or {})
    if set(sort_values) - set(dimensions) or any(value not in {"asc", "desc"} for value in sort_values.values()):
        raise UsageError("Dimension sort overrides require selected dimension IDs and asc/desc values.")
    for field in rebuilt["unitDimensionList"]:
        if _field_id(field) in sort_values:
            field["sortValue"] = sort_values[_field_id(field)]
    rebuilt["unitColumnDimensionList"] = []

    if measure_mode == "source_all":
        measure_ids = [_field_id(field) for field in _fields(source_detail, "unitMeasureList") if _field_id(field)]
        aide_measure_ids = [_field_id(field) for field in _fields(source_detail, "unitAideMeasureList") if _field_id(field)]
    elif measure_mode == "target_all":
        measure_ids = [_field_id(field) for field in _fields(target_detail, "unitMeasureList") if _field_id(field)]
        aide_measure_ids = [_field_id(field) for field in _fields(target_detail, "unitAideMeasureList") if _field_id(field)]
    else:
        measure_ids = explicit_measures
        aide_measure_ids = []

    rebuilt["unitMeasureList"] = [
        _copy_field(
            source=source_index,
            target=target_index,
            group="unitMeasureList",
            field_id=field_id,
            preserve_target_display=preserve_target_display,
        )
        for field_id in _ordered_unique(measure_ids, "unitMeasureList")
    ]
    rebuilt["unitAideMeasureList"] = [
        _copy_field(
            source=source_index,
            target=target_index,
            group="unitAideMeasureList",
            field_id=field_id,
            preserve_target_display=preserve_target_display,
        )
        for field_id in _ordered_unique(aide_measure_ids, "unitAideMeasureList")
    ]

    measure_names = dict(measure_show_names or {})
    if measure_names and not target_measure_format_ids:
        raise UsageError("Measure display names require reviewed target measure formats.")
    selected_measure_ids = {_field_id(field) for field in rebuilt["unitMeasureList"]}
    if set(measure_names) - selected_measure_ids or any(
        not isinstance(value, str) or not value.strip() for value in measure_names.values()
    ):
        raise UsageError("Measure display names require selected measure IDs and non-empty strings.")
    for field in rebuilt["unitMeasureList"]:
        field_id = _field_id(field)
        if field_id in measure_names:
            field["showName"] = measure_names[field_id].strip()
    if measure_names:
        labels = [field.get("showName") for field in rebuilt["unitMeasureList"]]
        if len(labels) != len(set(labels)):
            raise UsageError("Reviewed measure labels must retain unique display names.")

    actual_measure_ids = {
        _field_id(field)
        for group in ("unitMeasureList", "unitAideMeasureList")
        for field in _fields(rebuilt, group)
    }
    missing_required = [field_id for field_id in required_measures if field_id not in actual_measure_ids]
    if missing_required:
        raise UsageError(f"Required measure fields are missing after rebuild: {missing_required}")

    format_ids = _ordered_unique(target_measure_format_ids or [], "target_measure_format_ids")
    if format_ids:
        if sync_source_format:
            raise UsageError("Target measure formats cannot be combined with source format synchronization.")
        _inherit_measure_formats(rebuilt, target_index["unitMeasureList"], format_ids)

    if sync_source_format:
        source_format = source_detail.get("format")
        if not isinstance(source_format, Mapping):
            raise UsageError("Source unit format must be an object when sync_source_format=true.")
        target_format = rebuilt.get("format")
        if target_format is None:
            target_format = {}
            rebuilt["format"] = target_format
        if not isinstance(target_format, dict):
            raise UsageError("Target unit format must be an object when sync_source_format=true.")
        for key in PIVOT_SYNC_FORMAT_KEYS:
            if key in source_format:
                target_format[key] = copy.deepcopy(source_format[key])
            else:
                target_format.pop(key, None)
    return rebuilt
