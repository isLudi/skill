"""Conservative Presto compiler for executable single-base-table QueryPlans."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

import sqlglot

from .contracts import ContractRegistry
from .models import QueryPlan


FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?$")
TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")
ALLOWED_OPERATORS = {
    "=",
    "!=",
    "<>",
    ">",
    ">=",
    "<",
    "<=",
    "in",
    "not in",
    "like",
    "between",
    "is null",
    "is not null",
}
PLACEHOLDER_MARKERS = ("${", "<待", "<青橙", "<一级", "<二级", "<项目")


@dataclass(frozen=True)
class CompiledQuery:
    sql: str
    plan: QueryPlan

    def summary(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan.plan_id,
            "domain": self.plan.domain,
            "status": self.plan.status,
            "sql_sha256": self.plan.sql_sha256,
            "tables": [self.plan.base_table] if self.plan.base_table else [],
            "output_fields": [
                item.get("output_alias")
                for item in self.plan.dimensions + self.plan.metrics
            ],
        }


def _literal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        if (value.strip().startswith("<") and value.strip().endswith(">")) or any(
            marker in value for marker in PLACEHOLDER_MARKERS
        ):
            raise ValueError(f"unresolved placeholder value: {value}")
        return "'" + value.replace("'", "''") + "'"
    raise ValueError(f"unsupported filter value type: {type(value).__name__}")


def _qualified_field(field: str, alias: str = "t") -> str:
    if not FIELD_RE.fullmatch(field):
        raise ValueError(f"unsafe field identifier: {field}")
    return field if "." in field else f"{alias}.{field}"


def _render_filter(item: dict[str, Any], alias: str = "t") -> str:
    field = _qualified_field(str(item.get("field", "")), alias)
    operator = " ".join(str(item.get("operator", "=")).lower().split())
    if operator not in ALLOWED_OPERATORS:
        raise ValueError(f"unsupported filter operator: {operator}")
    if operator in {"is null", "is not null"}:
        return f"{field} {operator}"
    value = item.get("value")
    if operator in {"in", "not in"}:
        if not isinstance(value, list) or not value:
            raise ValueError(f"{operator} requires a non-empty list")
        return f"{field} {operator} ({', '.join(_literal(entry) for entry in value)})"
    if operator == "between":
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("between requires exactly two values")
        return f"{field} between {_literal(value[0])} and {_literal(value[1])}"
    return f"{field} {operator} {_literal(value)}"


def compile_query_plan(plan: QueryPlan, registry: ContractRegistry) -> CompiledQuery:
    if not plan.executable:
        raise ValueError(f"QueryPlan is not executable: {plan.status}; unresolved={plan.unresolved_slots}")
    if registry.domain != plan.domain or not registry.ok:
        raise ValueError("semantic contract registry is invalid or belongs to another domain")
    if not plan.base_table or not TABLE_RE.fullmatch(plan.base_table):
        raise ValueError("QueryPlan requires one fully qualified base table")
    if plan.joins:
        raise ValueError("P2 compiler only emits single-base-table SQL; reviewed join recipes remain manual")

    select_items: list[str] = []
    group_items: list[str] = []
    output_aliases: set[str] = set()
    for dimension in plan.dimensions:
        contract = registry.by_id(str(dimension.get("id", "")))
        if not contract or contract.get("kind") != "dimension" or contract.get("status") != "confirmed":
            raise ValueError(f"dimension contract unavailable: {dimension.get('id')}")
        if contract.get("automatic_compile") is False:
            raise ValueError(f"dimension contract requires a manual recipe: {dimension.get('id')}")
        expression = (
            str(contract["sql_expression"]).replace("{base}", "t")
            if contract.get("sql_expression")
            else _qualified_field(str(dimension.get("field", "")), "t")
        )
        output_alias = str(dimension.get("output_alias") or dimension.get("field"))
        if not FIELD_RE.fullmatch(output_alias):
            raise ValueError(f"unsafe dimension output alias: {output_alias}")
        if output_alias.lower() in output_aliases:
            raise ValueError(f"duplicate output alias: {output_alias}")
        output_aliases.add(output_alias.lower())
        select_items.append(f"{expression} as {output_alias}")
        group_items.append(expression)
    for metric in plan.metrics:
        contract = registry.by_id(str(metric.get("id", "")))
        if not contract or contract.get("kind") != "metric" or contract.get("status") != "confirmed":
            raise ValueError(f"metric contract unavailable: {metric.get('id')}")
        expression = str(contract.get("sql_expression", "")).replace("{base}", "t")
        output_alias = str(contract.get("output_alias", ""))
        if not FIELD_RE.fullmatch(output_alias):
            raise ValueError(f"unsafe metric output alias: {output_alias}")
        if output_alias.lower() in output_aliases:
            raise ValueError(f"duplicate output alias: {output_alias}")
        output_aliases.add(output_alias.lower())
        select_items.append(f"{expression} as {output_alias}")
    if not select_items or not plan.metrics:
        raise ValueError("compiled metric SQL requires at least one metric")

    lines = ["select", "    " + ",\n    ".join(select_items), f"from {plan.base_table} t"]
    if plan.filters:
        rendered_filters = [_render_filter(item, "t") for item in plan.filters]
        lines.extend(["where", "    " + "\n    and ".join(rendered_filters)])
    if group_items:
        lines.extend(["group by", "    " + ",\n    ".join(group_items)])
    if plan.execution_policy.get("execution_mode") == "exploratory":
        limit = min(int(plan.execution_policy.get("max_direct_download_rows", 1000)), 1000)
        lines.append(f"limit {limit}")
    sql = "\n".join(lines) + "\n"
    sqlglot.parse_one(sql, read="presto")
    plan.sql_sha256 = hashlib.sha256(sql.encode("utf-8")).hexdigest()
    return CompiledQuery(sql=sql, plan=plan)
