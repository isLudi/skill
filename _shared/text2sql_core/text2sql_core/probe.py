"""Generate bounded SQL probes for grain, freshness, distribution, and joins."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import sqlglot

from .catalog import CatalogBundle


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ProbeQuery:
    kind: str
    domain: str
    tables: list[str]
    sql: str
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "domain": self.domain,
            "tables": self.tables,
            "sql": self.sql,
            "interpretation": self.interpretation,
        }


def _identifier(value: str) -> str:
    if not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"unsafe field identifier: {value}")
    return value


def _table(bundle: CatalogBundle, value: str) -> str:
    lowered = value.lower()
    if not TABLE_RE.fullmatch(lowered) or lowered not in bundle.known_tables():
        raise ValueError(f"table is not registered in {bundle.domain}: {value}")
    return lowered


def _field(bundle: CatalogBundle, table: str, value: str) -> str:
    field = _identifier(value)
    record = bundle.table_record(table) or {}
    columns = {
        str(item.get("name", "")).lower()
        for item in record.get("columns", [])
        if item.get("name")
    }
    if columns and field.lower() not in columns:
        raise ValueError(f"field is not registered for {table}: {field}")
    return field


def _literal(value: str) -> str:
    if not value or "${" in value or "<" in value:
        raise ValueError("probe partition values must be concrete")
    return "'" + value.replace("'", "''") + "'"


def _partition_field(bundle: CatalogBundle, table: str, requested: str | None) -> str:
    if requested:
        return _field(bundle, table, requested)
    record = bundle.table_record(table) or {}
    candidates = list(record.get("partition_candidates", []))
    if "dt" in candidates:
        return "dt"
    raise ValueError("probe requires --partition-field because the catalog has no confirmed dt field")


def generate_probe(
    bundle: CatalogBundle,
    *,
    kind: str,
    table: str,
    start_value: str,
    end_value: str,
    partition_field: str | None = None,
    field: str | None = None,
    keys: list[str] | None = None,
    right_table: str | None = None,
    right_keys: list[str] | None = None,
    right_partition_field: str | None = None,
    limit: int = 100,
) -> ProbeQuery:
    left = _table(bundle, table)
    partition = _partition_field(bundle, left, partition_field)
    start = _literal(start_value)
    end = _literal(end_value)
    safe_limit = max(1, min(int(limit), 1000))
    if kind == "freshness":
        sql = (
            f"select {partition}, count(*) as row_count\n"
            f"from {left}\n"
            f"where {partition} between {start} and {end}\n"
            f"group by {partition}\n"
            f"order by {partition} desc\n"
            f"limit {safe_limit}\n"
        )
        interpretation = "Check missing or unexpectedly small partitions before business filtering."
        tables = [left]
    elif kind == "distribution":
        target = _field(bundle, left, field or "")
        sql = (
            f"select {target}, count(*) as row_count\n"
            f"from {left}\n"
            f"where {partition} between {start} and {end}\n"
            f"group by {target}\n"
            f"order by row_count desc\n"
            f"limit {safe_limit}\n"
        )
        interpretation = "Inspect actual values before choosing a business-scope predicate or mapping."
        tables = [left]
    elif kind == "duplicates":
        key_fields = [_field(bundle, left, value) for value in (keys or [])]
        if not key_fields:
            raise ValueError("duplicates probe requires at least one key")
        joined = ", ".join(key_fields)
        sql = (
            f"select {joined}, count(*) as duplicate_count\n"
            f"from {left}\n"
            f"where {partition} between {start} and {end}\n"
            f"group by {joined}\n"
            f"having count(*) > 1\n"
            f"order by duplicate_count desc\n"
            f"limit {safe_limit}\n"
        )
        interpretation = "Validate the assumed grain before aggregation or joining."
        tables = [left]
    elif kind == "join-cardinality":
        right = _table(bundle, right_table or "")
        left_key_fields = [_field(bundle, left, value) for value in (keys or [])]
        right_key_fields = [_field(bundle, right, value) for value in (right_keys or [])]
        if not left_key_fields or len(left_key_fields) != len(right_key_fields):
            raise ValueError("join-cardinality requires equally sized --keys and --right-keys")
        right_partition = _partition_field(bundle, right, right_partition_field)
        left_group = ", ".join(left_key_fields)
        right_group = ", ".join(right_key_fields)
        conditions = " and ".join(
            f"l.{left_key} = r.{right_key}"
            for left_key, right_key in zip(left_key_fields, right_key_fields)
        )
        sql = (
            "with l as (\n"
            f"    select {left_group}, count(*) as left_rows\n"
            f"    from {left}\n"
            f"    where {partition} between {start} and {end}\n"
            f"    group by {left_group}\n"
            "), r as (\n"
            f"    select {right_group}, count(*) as right_rows\n"
            f"    from {right}\n"
            f"    where {right_partition} between {start} and {end}\n"
            f"    group by {right_group}\n"
            ")\n"
            "select\n"
            "    count(*) as left_key_count,\n"
            "    sum(case when r.right_rows is null then 1 else 0 end) as unmatched_left_keys,\n"
            "    max(coalesce(r.right_rows, 0)) as max_right_rows_per_key,\n"
            "    sum(l.left_rows * coalesce(r.right_rows, 0)) as joined_row_estimate\n"
            "from l\n"
            f"left join r on {conditions}\n"
        )
        interpretation = "Compare key uniqueness, unmatched keys, and estimated row multiplication before using the join."
        tables = [left, right]
    else:
        raise ValueError(f"unsupported probe kind: {kind}")
    sqlglot.parse_one(sql, read="presto")
    return ProbeQuery(kind=kind, domain=bundle.domain, tables=tables, sql=sql, interpretation=interpretation)
