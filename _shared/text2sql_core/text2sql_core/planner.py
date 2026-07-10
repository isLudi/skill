"""Build a deterministic QueryPlan from a validated QuerySpec and contracts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp

from .catalog import CatalogBundle
from .contracts import ContractRegistry
from .models import Diagnostic, QueryPlan, QuerySpec


FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ALLOWED_FILTER_OPERATORS = {
    "=", "!=", "<>", ">", ">=", "<", "<=", "in", "not in", "like", "between", "is null", "is not null"
}
PLACEHOLDER_MARKERS = ("${", "<待", "<青橙", "<一级", "<二级", "<项目", "<YYYY", "<HH")


def _plan_id(spec: QuerySpec) -> str:
    payload = json.dumps(spec.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "plan_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _filter_field(item: dict[str, Any]) -> str:
    return str(item.get("field", "")).strip()


def _normalized_operator(value: Any) -> str:
    return " ".join(str(value or "=").lower().split())


def _scope_tables(item: dict[str, Any]) -> set[str]:
    return {
        str(table).lower()
        for key in ("candidate_tables", "applies_to_tables")
        for table in item.get(key, [])
    }


def _scope_coverage(item: dict[str, Any]) -> set[str]:
    return {
        *(str(rule.get("field", "")).lower() for rule in item.get("filters", []) if rule.get("field")),
        *(str(field).lower() for field in item.get("partition_requirements", [])),
    }


def _literal_is_concrete(value: Any) -> bool:
    if isinstance(value, str):
        return not (value.strip().startswith("<") and value.strip().endswith(">")) and not any(
            marker in value for marker in PLACEHOLDER_MARKERS
        )
    if value is None or isinstance(value, (bool, int, float)):
        return True
    if isinstance(value, list):
        return bool(value) and all(_literal_is_concrete(item) and not isinstance(item, list) for item in value)
    return False


def build_query_plan(
    spec: QuerySpec,
    *,
    skill_root: Path,
    core_root: Path,
) -> QueryPlan:
    bundle = CatalogBundle.load(skill_root, core_root)
    registry = ContractRegistry.load(skill_root, spec.domain)
    diagnostics = list(bundle.validate_query_spec(spec))
    diagnostics.extend(registry.diagnostics)
    unresolved = list(dict.fromkeys(spec.unresolved_slots))

    metric_rows: list[dict[str, Any]] = []
    metric_contracts: list[dict[str, Any]] = []
    metric_requires_manual = False
    for index, requested in enumerate(spec.metrics):
        contract_id = str(requested.get("id", ""))
        contract = registry.by_id(contract_id)
        if contract is None or contract.get("kind") != "metric":
            diagnostics.append(
                Diagnostic(
                    "PLAN_METRIC_CONTRACT_UNKNOWN",
                    "error",
                    f"metric contract is not registered: {contract_id}",
                    path=f"metrics[{index}].id",
                )
            )
            unresolved.append(f"metric:{contract_id}")
            continue
        if contract.get("status") != "confirmed":
            diagnostics.append(
                Diagnostic(
                    "PLAN_METRIC_PENDING",
                    "error",
                    f"metric contract is not confirmed: {contract_id}",
                    path=f"metrics[{index}].id",
                )
            )
            unresolved.append(f"metric_confirmation:{contract_id}")
            continue
        if requested.get("source_path") != contract.get("source_path"):
            diagnostics.append(
                Diagnostic(
                    "PLAN_METRIC_SOURCE_MISMATCH",
                    "error",
                    f"QuerySpec source does not match contract source for {contract_id}",
                    path=f"metrics[{index}].source_path",
                )
            )
        metric_contracts.append(contract)
        if contract.get("automatic_compile") is not True:
            metric_requires_manual = True
            diagnostics.append(
                Diagnostic(
                    "PLAN_METRIC_MANUAL_RECIPE_REQUIRED",
                    "warning",
                    f"metric {contract_id} is confirmed but not approved for deterministic P2 compilation",
                    path=f"metrics[{index}].id",
                    compat_blocking=False,
                )
            )
        metric_rows.append(
            {
                "id": contract_id,
                "name": contract.get("name"),
                "output_alias": contract.get("output_alias"),
                "aggregation": contract.get("aggregation"),
                "automatic_compile": contract.get("automatic_compile"),
                "candidate_tables": contract.get("candidate_tables", []),
                "source_path": contract.get("source_path"),
            }
        )
    if not metric_contracts:
        diagnostics.append(
            Diagnostic(
                "PLAN_METRIC_REQUIRED",
                "error",
                "P2 compilation requires at least one confirmed metric contract",
                path="metrics",
            )
        )
        unresolved.append("confirmed_metric")

    dimension_rows: list[dict[str, Any]] = []
    dimension_contracts: list[dict[str, Any]] = []
    dimension_requires_manual = False
    for index, requested in enumerate(spec.dimensions):
        contract = registry.resolve_identifier("dimension", requested)
        if contract is None:
            diagnostics.append(
                Diagnostic(
                    "PLAN_DIMENSION_CONTRACT_UNKNOWN",
                    "error",
                    f"dimension contract is not registered or is ambiguous: {requested}",
                    path=f"dimensions[{index}]",
                )
            )
            unresolved.append(f"dimension:{requested}")
            continue
        if contract.get("status") != "confirmed":
            diagnostics.append(
                Diagnostic(
                    "PLAN_DIMENSION_PENDING",
                    "error",
                    f"dimension contract is not confirmed: {contract['id']}",
                    path=f"dimensions[{index}]",
                )
            )
            unresolved.append(f"dimension_confirmation:{contract['id']}")
            continue
        dimension_contracts.append(contract)
        if contract.get("automatic_compile") is False:
            dimension_requires_manual = True
            diagnostics.append(
                Diagnostic(
                    "PLAN_DIMENSION_MANUAL_RECIPE_REQUIRED",
                    "warning",
                    f"dimension {contract['id']} is confirmed but not approved for deterministic P2 compilation",
                    path=f"dimensions[{index}]",
                    compat_blocking=False,
                )
            )
        dimension_rows.append(
            {
                "id": contract["id"],
                "name": contract.get("name"),
                "field": contract.get("field"),
                "output_alias": contract.get("output_alias") or contract.get("field"),
                "table": contract.get("table"),
                "data_type": contract.get("data_type"),
                "automatic_compile": contract.get("automatic_compile", True),
                "source_path": contract.get("source_path"),
            }
        )

    selected_dimension_ids = {str(item["id"]) for item in dimension_rows}
    for contract in metric_contracts:
        allowed = set(map(str, contract.get("allowed_dimensions", [])))
        disallowed = sorted(selected_dimension_ids - allowed)
        if disallowed:
            diagnostics.append(
                Diagnostic(
                    "PLAN_DIMENSION_NOT_ALLOWED",
                    "error",
                    f"metric {contract['id']} does not confirm dimensions: {', '.join(disallowed)}",
                    path="dimensions",
                )
            )
            unresolved.extend(f"dimension_compatibility:{item}" for item in disallowed)

    candidate_sets = [set(map(str.lower, contract.get("candidate_tables", []))) for contract in metric_contracts]
    common_tables = set.intersection(*candidate_sets) if candidate_sets else set()
    requested_tables = {
        str(item.get("name", "")).lower()
        for item in spec.candidate_tables
        if item.get("name")
    }
    if requested_tables:
        common_tables = common_tables & requested_tables if common_tables else requested_tables
    dimension_tables = {str(item.get("table", "")).lower() for item in dimension_contracts if item.get("table")}
    if dimension_tables:
        common_tables = common_tables & dimension_tables if common_tables else dimension_tables
    base_table = sorted(common_tables)[0] if len(common_tables) == 1 else None
    requires_manual_sql = metric_requires_manual or dimension_requires_manual
    if not base_table:
        if metric_rows:
            diagnostics.append(
                Diagnostic(
                    "PLAN_SINGLE_BASE_TABLE_UNRESOLVED",
                    "warning",
                    "confirmed metrics and dimensions do not resolve to one safe base table",
                    compat_blocking=False,
                )
            )
            requires_manual_sql = True
            unresolved.append("single_base_table_or_join_plan")

    table_columns: set[str] = set()
    if base_table:
        table_record = bundle.table_record(base_table) or {}
        table_columns = {
            str(item.get("name", "")).lower()
            for item in table_record.get("columns", [])
            if item.get("name")
        }
        if table_columns:
            for contract in dimension_contracts:
                expression_text = contract.get("sql_expression")
                if expression_text:
                    expression = sqlglot.parse_one(
                        str(expression_text).replace("{base}", "t"),
                        read="presto",
                    )
                    referenced = {str(column.name).lower() for column in expression.find_all(exp.Column)}
                else:
                    referenced = {str(contract.get("field", "")).lower()}
                missing = sorted(field for field in referenced if field and field not in table_columns)
                if missing:
                    diagnostics.append(
                        Diagnostic(
                            "PLAN_DIMENSION_FIELDS_NOT_IN_BASE_TABLE",
                            "error",
                            f"dimension {contract['id']} references fields absent from {base_table}: {', '.join(missing)}",
                            table=base_table,
                        )
                    )
                    unresolved.extend(f"dimension_field:{field}" for field in missing)
            for contract in metric_contracts:
                expression = sqlglot.parse_one(
                    str(contract.get("sql_expression", "")).replace("{base}", "t"),
                    read="presto",
                )
                referenced = {str(column.name).lower() for column in expression.find_all(exp.Column)}
                missing = sorted(referenced - table_columns)
                if missing:
                    diagnostics.append(
                        Diagnostic(
                            "PLAN_METRIC_FIELDS_NOT_IN_BASE_TABLE",
                            "error",
                            f"metric {contract['id']} references fields absent from {base_table}: {', '.join(missing)}",
                            table=base_table,
                        )
                    )
                    unresolved.extend(f"metric_field:{field}" for field in missing)

    joins: list[dict[str, Any]] = []
    for index, requested in enumerate(spec.join_path):
        contract_id = str(requested.get("contract_id", "")).strip()
        if not contract_id:
            joins.append(dict(requested))
            diagnostics.append(
                Diagnostic(
                    "PLAN_JOIN_CONTRACT_REQUIRED",
                    "warning",
                    "join path has no semantic contract and requires manual review",
                    path=f"join_path[{index}]",
                    compat_blocking=False,
                )
            )
            continue
        contract = registry.by_id(contract_id)
        if contract is None or contract.get("kind") != "join":
            diagnostics.append(
                Diagnostic(
                    "PLAN_JOIN_CONTRACT_UNKNOWN",
                    "error",
                    f"join contract is not registered: {contract_id}",
                    path=f"join_path[{index}].contract_id",
                )
            )
            unresolved.append(f"join:{contract_id}")
            continue
        normalized_join = {
            "id": contract_id,
            "status": contract.get("status"),
            "left": contract.get("left_table"),
            "right": contract.get("right_table"),
            "key_pairs": contract.get("key_pairs") or contract.get("keys", []),
            "cardinality": contract.get("cardinality"),
            "source_path": contract.get("source_path"),
        }
        joins.append(normalized_join)
        if contract.get("status") != "confirmed":
            diagnostics.append(
                Diagnostic(
                    "PLAN_JOIN_PENDING",
                    "error",
                    f"join contract is not confirmed: {contract_id}",
                    path=f"join_path[{index}].contract_id",
                )
            )
            unresolved.append(f"join_confirmation:{contract_id}")
        if requested.get("source_path") != contract.get("source_path"):
            diagnostics.append(
                Diagnostic(
                    "PLAN_JOIN_SOURCE_MISMATCH",
                    "error",
                    f"QuerySpec source does not match contract source for {contract_id}",
                    path=f"join_path[{index}].source_path",
                )
            )
        for requested_key, contract_key in (("left", "left_table"), ("right", "right_table")):
            if str(requested.get(requested_key, "")).lower() != str(contract.get(contract_key, "")).lower():
                diagnostics.append(
                    Diagnostic(
                        "PLAN_JOIN_TABLE_MISMATCH",
                        "error",
                        f"QuerySpec {requested_key} table does not match join contract {contract_id}",
                        path=f"join_path[{index}].{requested_key}",
                    )
                )
                unresolved.append(f"join_table:{contract_id}:{requested_key}")
    if joins:
        diagnostics.append(
            Diagnostic(
                "PLAN_JOIN_COMPILATION_REQUIRES_REVIEW",
                "warning",
                "P2 records multi-table join paths but does not auto-compile them without a dedicated recipe",
                compat_blocking=False,
            )
        )
        requires_manual_sql = True
        if base_table:
            adjacency: dict[str, set[str]] = {}
            for join in joins:
                left = str(join.get("left", "")).lower()
                right = str(join.get("right", "")).lower()
                if left and right:
                    adjacency.setdefault(left, set()).add(right)
                    adjacency.setdefault(right, set()).add(left)
            reachable = {base_table}
            frontier = [base_table]
            while frontier:
                current = frontier.pop()
                for neighbor in adjacency.get(current, set()) - reachable:
                    reachable.add(neighbor)
                    frontier.append(neighbor)
            disconnected = sorted(set(adjacency) - reachable)
            if base_table not in adjacency or disconnected:
                diagnostics.append(
                    Diagnostic(
                        "PLAN_JOIN_PATH_DISCONNECTED",
                        "error",
                        f"join path is not fully connected to base table {base_table}",
                        path="join_path",
                        table=base_table,
                    )
                )
                unresolved.append("join_path_from_base_table")

    if spec.calculation_grain != spec.output_grain:
        diagnostics.append(
            Diagnostic(
                "PLAN_GRAIN_MISMATCH_REQUIRES_REVIEW",
                "warning",
                "calculation_grain differs from output_grain; automatic compilation is disabled",
                compat_blocking=False,
            )
        )
        requires_manual_sql = True

    filters = [dict(item) for item in spec.filters] + [dict(item) for item in spec.business_scope]
    required_scope_fields = {
        str(field).lower()
        for contract in metric_contracts
        for field in contract.get("required_scope_fields", [])
    }

    time_field = ""
    if spec.time_range and base_table:
        time_field = str(spec.time_range.get("field", "")).strip()
        if not time_field:
            time_fields = {str(item.get("time_field", "")).strip() for item in metric_contracts if item.get("time_field")}
            if len(time_fields) == 1:
                time_field = next(iter(time_fields))
            else:
                record = bundle.table_record(base_table) or {}
                if "dt" in record.get("partition_candidates", []):
                    time_field = "dt"
        existing_time_fields = {_filter_field(item).lower() for item in filters if _filter_field(item)}
        if time_field and time_field.lower() not in existing_time_fields:
            start = spec.time_range.get("start_value", spec.time_range.get("start"))
            end = spec.time_range.get("end_value", spec.time_range.get("end"))
            if start is None or end is None:
                diagnostics.append(
                    Diagnostic(
                        "PLAN_TIME_VALUES_REQUIRED",
                        "error",
                        "time_range requires start/end values for compilation",
                        path="time_range",
                    )
                )
                unresolved.append("time_range_values")
            else:
                filters.extend(
                    [
                        {"field": time_field, "operator": ">=", "value": start, "role": "time_range"},
                        {"field": time_field, "operator": "<=", "value": end, "role": "time_range"},
                    ]
                )
        elif not time_field:
            diagnostics.append(
                Diagnostic(
                    "PLAN_TIME_FIELD_UNRESOLVED",
                    "error",
                    "time_range is present but no confirmed time field can be selected",
                    path="time_range",
                )
            )
            unresolved.append("time_field")

    selected_scopes: list[dict[str, Any]] = []
    for index, requested in enumerate(spec.scopes):
        contract = registry.resolve_identifier("scope", requested)
        if contract is None:
            diagnostics.append(
                Diagnostic(
                    "PLAN_SCOPE_CONTRACT_UNKNOWN",
                    "error",
                    f"scope contract is not registered or is ambiguous: {requested}",
                    path=f"scopes[{index}]",
                )
            )
            unresolved.append(f"scope:{requested}")
            continue
        if contract.get("status") != "confirmed":
            diagnostics.append(
                Diagnostic(
                    "PLAN_SCOPE_PENDING",
                    "error",
                    f"scope contract is not confirmed: {contract['id']}",
                    path=f"scopes[{index}]",
                )
            )
            unresolved.append(f"scope_confirmation:{contract['id']}")
            continue
        selected_scopes.append(contract)

    if not spec.scopes and base_table and required_scope_fields:
        automatic = [
            item
            for item in registry.values("scope")
            if item.get("status") == "confirmed"
            and base_table in _scope_tables(item)
            and required_scope_fields <= _scope_coverage(item)
        ]
        if len(automatic) == 1:
            selected_scopes = automatic
        elif len(automatic) > 1:
            diagnostics.append(
                Diagnostic(
                    "PLAN_SCOPE_AMBIGUOUS",
                    "error",
                    "multiple confirmed scope contracts cover the requested metric; select one explicitly",
                    path="scopes",
                )
            )
            unresolved.append("scope_contract")

    scope_rows: list[dict[str, Any]] = []
    for contract in selected_scopes:
        applies_to = _scope_tables(contract)
        if base_table and applies_to and base_table not in applies_to:
            diagnostics.append(
                Diagnostic(
                    "PLAN_SCOPE_TABLE_MISMATCH",
                    "error",
                    f"scope {contract['id']} does not apply to base table {base_table}",
                    path="scopes",
                )
            )
            unresolved.append(f"scope_table:{contract['id']}")
            continue
        applied_fields: list[str] = []
        for rule in contract.get("filters", []):
            field = _filter_field(rule)
            if not field:
                continue
            existing = [item for item in filters if _filter_field(item).lower() == field.lower()]
            if "value" in rule:
                required_filter = {
                    "field": field,
                    "operator": rule.get("operator", "="),
                    "value": rule.get("value"),
                    "role": "scope_contract",
                    "contract_id": contract["id"],
                }
                if existing:
                    if not all(
                        _normalized_operator(item.get("operator")) == _normalized_operator(required_filter["operator"])
                        and item.get("value") == required_filter["value"]
                        for item in existing
                    ):
                        diagnostics.append(
                            Diagnostic(
                                "PLAN_SCOPE_FILTER_CONFLICT",
                                "error",
                                f"provided filter conflicts with confirmed scope {contract['id']}: {field}",
                                path="business_scope",
                                field=field,
                            )
                        )
                        unresolved.append(f"scope_conflict:{field}")
                else:
                    filters.append(required_filter)
                applied_fields.append(field)
            elif not existing:
                diagnostics.append(
                    Diagnostic(
                        "PLAN_SCOPE_VALUE_REQUIRED",
                        "error",
                        f"scope {contract['id']} requires a concrete value for {field}",
                        path="business_scope",
                        field=field,
                    )
                )
                unresolved.append(f"scope_value:{contract['id']}:{field}")
        scope_rows.append(
            {
                "id": contract["id"],
                "name": contract.get("name"),
                "source_path": contract.get("source_path"),
                "candidate_tables": sorted(applies_to),
                "applied_fields": sorted(applied_fields),
            }
        )

    filtered_fields = {_filter_field(item).lower() for item in filters if _filter_field(item)}
    applied_scope_ids = {str(item["id"]) for item in scope_rows}
    contract_scope_coverage = set().union(
        *(
            _scope_coverage(item)
            for item in selected_scopes
            if str(item.get("id")) in applied_scope_ids
        )
    ) if applied_scope_ids else set()
    if metric_contracts and not metric_requires_manual and not required_scope_fields <= contract_scope_coverage:
        uncovered = sorted(required_scope_fields - contract_scope_coverage)
        diagnostics.append(
            Diagnostic(
                "PLAN_SCOPE_CONTRACT_COVERAGE_MISSING",
                "error",
                "automatic compilation requires confirmed scope-contract coverage for: " + ", ".join(uncovered),
                path="scopes",
            )
        )
        unresolved.extend(f"scope_contract_coverage:{field}" for field in uncovered)
    missing_scope = sorted(required_scope_fields - filtered_fields)
    if missing_scope:
        diagnostics.append(
            Diagnostic(
                "PLAN_REQUIRED_SCOPE_MISSING",
                "error",
                "required business scope filters are missing: " + ", ".join(missing_scope),
                path="business_scope",
            )
        )
        unresolved.extend(f"business_scope:{field}" for field in missing_scope)

    for index, item in enumerate(filters):
        field = _filter_field(item)
        operator = _normalized_operator(item.get("operator"))
        if operator not in ALLOWED_FILTER_OPERATORS:
            diagnostics.append(
                Diagnostic(
                    "PLAN_FILTER_OPERATOR_UNSUPPORTED",
                    "error",
                    f"filter operator is not supported by the P2 compiler: {operator}",
                    path=f"filters[{index}].operator",
                    field=field,
                )
            )
            unresolved.append(f"filter_operator:{field}")
        elif operator not in {"is null", "is not null"}:
            value = item.get("value")
            shape_valid = (
                isinstance(value, list) and len(value) == 2 and _literal_is_concrete(value)
                if operator == "between"
                else _literal_is_concrete(value)
            )
            if operator in {"in", "not in"}:
                shape_valid = isinstance(value, list) and bool(value) and _literal_is_concrete(value)
            if not shape_valid:
                diagnostics.append(
                    Diagnostic(
                        "PLAN_FILTER_VALUE_UNRESOLVED",
                        "error",
                        f"filter value is unsupported or unresolved for {field}",
                        path=f"filters[{index}].value",
                        field=field,
                    )
                )
                unresolved.append(f"filter_value:{field}")
        if not FIELD_RE.fullmatch(field):
            diagnostics.append(
                Diagnostic(
                    "PLAN_FILTER_FIELD_UNSAFE",
                    "error",
                    f"filter field is not a physical identifier: {field}",
                    path=f"filters[{index}].field",
                    table=base_table,
                )
            )
            unresolved.append(f"filter_field:{field}")
        elif base_table and table_columns and field.lower() not in table_columns:
            diagnostics.append(
                Diagnostic(
                    "PLAN_FILTER_FIELD_NOT_IN_BASE_TABLE",
                    "error",
                    f"filter field {field} is absent from {base_table}",
                    path=f"filters[{index}].field",
                    table=base_table,
                    field=field,
                )
            )
            unresolved.append(f"filter_field:{field}")

    evidence = sorted(
        {
            *(str(item.get("source_path")) for item in spec.evidence if item.get("source_path")),
            *(
                str(item.get("source_path"))
                for item in metric_contracts + dimension_contracts + selected_scopes
                if item.get("source_path")
            ),
        }
    )
    lineage = [
        {
            "output": item.get("output_alias"),
            "role": "measure",
            "contract_id": item["id"],
            "source_path": item.get("source_path"),
            "candidate_tables": item.get("candidate_tables", []),
        }
        for item in metric_rows
    ]
    lineage.extend(
        {
            "output": item.get("output_alias"),
            "role": "dimension",
            "contract_id": item["id"],
            "source_path": item.get("source_path"),
            "candidate_tables": [item.get("table")],
        }
        for item in dimension_rows
    )
    lineage.extend(
        {
            "output": None,
            "role": "scope",
            "contract_id": item["id"],
            "source_path": item.get("source_path"),
            "candidate_tables": item.get("candidate_tables", []),
        }
        for item in scope_rows
    )

    unresolved = list(dict.fromkeys(unresolved))
    has_error = any(item.severity == "error" for item in diagnostics)
    if has_error:
        status = "blocked"
    elif requires_manual_sql:
        status = "requires_manual_sql"
    else:
        status = "executable"
    policy = {
        "allow_download": False,
        "max_direct_download_rows": 1000,
        "requires_preview": True,
        "execution_mode": spec.execution_mode,
    }
    return QueryPlan(
        plan_id=_plan_id(spec),
        domain=spec.domain,
        intent=spec.intent,
        status=status,
        base_table=base_table,
        metrics=metric_rows,
        dimensions=dimension_rows,
        filters=filters,
        scopes=scope_rows,
        joins=joins,
        calculation_grain=spec.calculation_grain,
        output_grain=spec.output_grain,
        evidence=evidence,
        lineage=lineage,
        unresolved_slots=unresolved,
        diagnostics=diagnostics,
        execution_policy=policy,
    )
