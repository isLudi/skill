"""Helpers for sandbox-only pivot field rebinding."""

from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

from _shared.errors import UsageError


FIELD_LIST_GROUPS = (
    "unitDimensionList",
    "unitColumnDimensionList",
    "unitMeasureList",
    "unitAideMeasureList",
    "unitFilterList",
)

FIELD_DISPLAY_KEYS = ("showName",)
FIELD_FORMAT_DISPLAY_KEYS = ("sortValue", "condition")
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

        public_filter_list = check.get("public_filter_list")
        if not isinstance(public_filter_list, list) or not public_filter_list:
            raise UsageError(f"{check_id} requires a non-empty public_filter_list.")
        if any(not isinstance(item, Mapping) for item in public_filter_list):
            raise UsageError(f"{check_id} public_filter_list entries must be objects.")

        check_required_filters = check.get("required_public_filters") or required_public_filters
        if not isinstance(check_required_filters, list) or not check_required_filters:
            raise UsageError(
                f"{check_id} requires required_public_filters to prove the value check is scoped "
                "to a specified period/public filter."
            )
        for required_filter in check_required_filters:
            if not isinstance(required_filter, Mapping):
                raise UsageError(f"{check_id} required_public_filters entries must be objects.")
            if not _public_filter_matches_required(public_filter_list, required_filter):
                raise UsageError(
                    f"{check_id} public_filter_list does not contain required filter/value {dict(required_filter)}."
                )

        row_match = check.get("row_match")
        if not isinstance(row_match, Mapping) or not row_match:
            raise UsageError(f"{check_id} requires a non-empty row_match.")
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
    """Return a stable, low-noise projection of configured pivot fields."""

    projection: dict[str, Any] = {
        "unit_id": detail.get("unitId"),
        "unit_name": detail.get("unitName"),
        "model_id": detail.get("modelId"),
        "groups": {},
    }
    for group in FIELD_LIST_GROUPS:
        projection["groups"][group] = [
            {
                "field_id": _field_id(field),
                "name": field.get("name"),
                "show_name": field.get("showName"),
                "field_type": field.get("fieldType"),
                "org_param_type": field.get("orgParamType"),
            }
            for field in _fields(detail, group)
            if _field_id(field)
        ]
    return projection


def rebuild_pivot_unit_fields(
    *,
    target_detail: Mapping[str, Any],
    source_detail: Mapping[str, Any],
    dimension_field_ids: Iterable[str],
    measure_mode: str = "source_all",
    measure_field_ids: Iterable[str] | None = None,
    required_measure_field_ids: Iterable[str] = (),
    preserve_target_display: bool = True,
) -> dict[str, Any]:
    """Rebuild a target pivot's field lists from a known-good source unit.

    This intentionally updates only field-list groups. The caller owns the
    write boundary, backup, drift checks, and recovery.
    """

    target_model = target_detail.get("modelId")
    source_model = source_detail.get("modelId")
    if target_model not in (None, "") and source_model not in (None, "") and str(target_model) != str(source_model):
        raise UsageError(f"Source/target model mismatch: {source_model} vs {target_model}")

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

    actual_measure_ids = {
        _field_id(field)
        for group in ("unitMeasureList", "unitAideMeasureList")
        for field in _fields(rebuilt, group)
    }
    missing_required = [field_id for field_id in required_measures if field_id not in actual_measure_ids]
    if missing_required:
        raise UsageError(f"Required measure fields are missing after rebuild: {missing_required}")
    return rebuilt
