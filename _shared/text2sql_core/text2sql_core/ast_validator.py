"""Presto AST checks that supplement domain-specific platform rules."""

from __future__ import annotations

import re
from pathlib import Path

import sqlglot
from sqlglot import exp

from .catalog import CatalogBundle
from .models import Diagnostic, QuerySpec, ValidationResult


TEMPLATE_PARAMETER_RE = re.compile(r"\$\{[^}]+\}")


def _qualified_table_name(table: exp.Table) -> str:
    parts = [part for part in (table.catalog, table.db, table.name) if part]
    return ".".join(parts).lower()


def _exclusive_table_owners(bundle: CatalogBundle) -> dict[str, str]:
    owners: dict[str, str] = {}
    for entry in bundle.domain_manifest.get("boundary", {}).get("exclusive_temp_tables", []):
        owners[str(entry).lower()] = bundle.domain
    other = bundle.domain_manifest.get("boundary", {}).get("forbidden_temp_tables", [])
    other_domain = "qingcheng" if bundle.domain == "market_consultant" else "market_consultant"
    for entry in other:
        owners[str(entry).lower()] = other_domain
    return owners


def validate_sql_ast(
    sql: str,
    *,
    skill_root: Path,
    core_root: Path,
    expected_domain: str,
    allow_unknown_tables: bool = False,
    query_spec: QuerySpec | None = None,
) -> ValidationResult:
    result = ValidationResult()
    bundle = CatalogBundle.load(skill_root, core_root)
    if bundle.domain != expected_domain:
        result.diagnostics.append(
            Diagnostic(
                "CATALOG_DOMAIN_MISMATCH",
                "error",
                f"catalog domain {bundle.domain!r} does not match {expected_domain!r}",
            )
        )
        return result
    if query_spec is not None:
        result.extend(bundle.validate_query_spec(query_spec))
    parameters = sorted(set(TEMPLATE_PARAMETER_RE.findall(sql)))
    if parameters:
        result.diagnostics.append(
            Diagnostic(
                "UNRESOLVED_TEMPLATE_PARAMETER",
                "error",
                "concrete SQL required; unresolved parameters: " + ", ".join(parameters),
            )
        )
        return result
    try:
        expressions = sqlglot.parse(sql, read="presto")
    except sqlglot.errors.ParseError as exc:
        result.diagnostics.append(Diagnostic("SQL_PARSE_ERROR", "error", str(exc)))
        return result
    ctes = {
        cte.alias_or_name.lower()
        for expression in expressions
        for cte in expression.find_all(exp.CTE)
        if cte.alias_or_name
    }
    result.ctes = sorted(ctes)
    physical_nodes: list[exp.Table] = []
    for expression in expressions:
        for table in expression.find_all(exp.Table):
            name = _qualified_table_name(table)
            if not name or (not table.db and table.name.lower() in ctes):
                continue
            physical_nodes.append(table)
    tables = sorted({_qualified_table_name(table) for table in physical_nodes})
    result.tables = tables
    known_tables = bundle.known_tables()
    owners = _exclusive_table_owners(bundle)
    for table in physical_nodes:
        name = _qualified_table_name(table)
        if not table.db:
            result.diagnostics.append(
                Diagnostic(
                    "UNQUALIFIED_PHYSICAL_TABLE",
                    "error",
                    f"physical table {table.name!r} must include its schema",
                    table=table.name,
                )
            )
        owner = owners.get(name)
        if owner and owner != expected_domain:
            result.diagnostics.append(
                Diagnostic(
                    "CROSS_DOMAIN_TEMP_TABLE",
                    "error",
                    f"{name} belongs to {owner}, not {expected_domain}",
                    table=name,
                )
            )
        if name not in known_tables:
            result.diagnostics.append(
                Diagnostic(
                    "UNKNOWN_PHYSICAL_TABLE",
                    "warning" if allow_unknown_tables else "error",
                    f"{name} is not present in the physical or {expected_domain} domain catalog",
                    table=name,
                    compat_blocking=not allow_unknown_tables,
                )
            )
    alias_to_table: dict[str, str] = {}
    for table in physical_nodes:
        alias = (table.alias_or_name or table.name).lower()
        alias_to_table[alias] = _qualified_table_name(table)
    for expression in expressions:
        for column in expression.find_all(exp.Column):
            qualifier = column.table.lower() if column.table else ""
            table_name = alias_to_table.get(qualifier)
            if not table_name:
                continue
            record = bundle.table_record(table_name) or {}
            known_columns = {str(item["name"]).lower() for item in record.get("columns", [])}
            if known_columns and column.name.lower() not in known_columns:
                result.diagnostics.append(
                    Diagnostic(
                        "UNKNOWN_QUALIFIED_FIELD",
                        "warning",
                        f"{column.sql()} is not documented for {table_name}",
                        table=table_name,
                        field=column.name,
                        compat_blocking=False,
                    )
                )
    if query_spec is not None:
        requested = {str(item.get("name", "")).lower() for item in query_spec.candidate_tables}
        missing = sorted(requested - set(tables))
        if missing:
            result.diagnostics.append(
                Diagnostic(
                    "SPEC_SQL_TABLE_MISMATCH",
                    "error",
                    "QuerySpec candidate tables missing from SQL: " + ", ".join(missing),
                )
            )
    return result
