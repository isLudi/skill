#!/usr/bin/env python3
"""Validate generated Presto SQL against Qingcheng dashboard-query rules.

The validator is scope-aware: every physical table is checked against the
``SELECT`` that owns it, so filters inside CTEs are not confused with outer
queries and ``SELECT DISTINCT`` is never compared with another query block's
``GROUP BY``.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import sqlglot
from sqlglot import exp


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIRS = [ROOT / "knowledge" / "tables", ROOT / "knowledge" / "temp_tables"]

NUMERIC_STRING_RE = re.compile(
    r"\b([a-zA-Z_][\w]*(?:count|cnt|num|number|amount|id|sequence)[a-zA-Z_0-9]*)\s*"
    r"(=|>=|<=|>|<)\s*'(\d+(?:\.\d+)?)'",
    re.I,
)
THREE_ARG_DATE_ADD_RE = re.compile(r"\bdate_add\s*\(\s*'[^']+'\s*,", re.I)
DEPARTMENT_FIELD_RE = re.compile(
    r"^(?:[a-zA-Z_][\w]*department_name|department|dept|project_name|team_name)$",
    re.I,
)

CROSS_DOMAIN_MARKERS = [
    "市场顾问部",
    "参评名单",
    "评优",
    "人产",
    "dingxi01_pingyou_jg",
    "dingxi01_jiagou_zx",
]


@dataclass(frozen=True)
class TableKnowledge:
    full_name: str
    fields: set[str]
    partitions: set[str]
    has_hour: bool
    scope_fields: set[str]


@dataclass(frozen=True)
class ScopedTable:
    alias: str
    full_name: str
    knowledge: TableKnowledge | None


def section(text: str, title: str) -> str:
    match = re.search(re.escape(title) + r"\n(.*?)(?=\n##\s|\Z)", text, flags=re.S)
    return match.group(1).strip() if match else ""


def table_rows(markdown_table: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in markdown_table.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        if re.match(r"^\|\s*:?-+", stripped):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if cells and cells[0] not in {"字段名", "字段", "项目"}:
            rows.append(cells)
    return rows


def _field_rows(text: str) -> list[list[str]]:
    """Collect rows only from Markdown tables whose first column is a field."""

    lines = text.splitlines()
    rows: list[list[str]] = []
    index = 0
    while index + 1 < len(lines):
        header = lines[index].strip()
        separator = lines[index + 1].strip()
        if not (header.startswith("|") and separator.startswith("|")):
            index += 1
            continue
        header_cells = [cell.strip().strip("`") for cell in header.strip("|").split("|")]
        if not header_cells or header_cells[0] not in {"字段名", "字段", "field", "Field"}:
            index += 1
            continue
        index += 2
        while index < len(lines) and lines[index].strip().startswith("|"):
            cells = [cell.strip().strip("`") for cell in lines[index].strip().strip("|").split("|")]
            if cells and cells[0] and not re.fullmatch(r":?-+:?", cells[0]):
                rows.append(cells)
            index += 1
    return rows


def _partition_sections(text: str) -> str:
    blocks: list[str] = []
    matches = list(re.finditer(r"^##\s+.*分区.*$", text, flags=re.M))
    for match in matches:
        end_match = re.search(r"^##\s+", text[match.end() :], flags=re.M)
        end = match.end() + end_match.start() if end_match else len(text)
        blocks.append(text[match.end() : end])
    return "\n".join(blocks)


def load_knowledge() -> dict[str, TableKnowledge]:
    knowledge: dict[str, TableKnowledge] = {}
    for table_dir in TABLE_DIRS:
        for path in table_dir.glob("*.md"):
            if path.name.startswith("_"):
                continue
            text = path.read_text(encoding="utf-8")
            title = re.search(r"^#\s+(.+)$", text, flags=re.M)
            full_name = title.group(1).strip() if title else path.stem
            fields = {row[0] for row in _field_rows(text) if row}
            partitions = {
                row[0]
                for row in table_rows(_partition_sections(text))
                if row and row[0] != "无"
            }
            fields |= partitions
            scope_fields = {field for field in fields if DEPARTMENT_FIELD_RE.fullmatch(field)}
            knowledge[full_name.lower()] = TableKnowledge(
                full_name=full_name,
                fields=fields,
                partitions=partitions,
                has_hour="hour" in {item.lower() for item in partitions},
                scope_fields=scope_fields,
            )
    return knowledge


def strip_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.M)
    return re.sub(r"/\*.*?\*/", "", sql, flags=re.S)


def _nearest_select(node: exp.Expression) -> exp.Select | None:
    parent = node.parent
    while parent is not None and not isinstance(parent, exp.Select):
        parent = parent.parent
    return parent if isinstance(parent, exp.Select) else None


def _owned_nodes(select: exp.Select, kind: type[exp.Expression]) -> list[exp.Expression]:
    return [node for node in select.find_all(kind) if _nearest_select(node) is select]


def _table_name(table: exp.Table) -> str:
    return ".".join(part.name for part in table.parts if part.name)


def _scoped_tables(
    select: exp.Select,
    *,
    cte_names: set[str],
    knowledge: dict[str, TableKnowledge],
) -> list[ScopedTable]:
    scoped: list[ScopedTable] = []
    for node in _owned_nodes(select, exp.Table):
        table = node
        assert isinstance(table, exp.Table)
        full_name = _table_name(table)
        if not full_name:
            continue
        if "." not in full_name and full_name.lower() in cte_names:
            continue
        scoped.append(
            ScopedTable(
                alias=table.alias_or_name.lower(),
                full_name=full_name.lower(),
                knowledge=knowledge.get(full_name.lower()),
            )
        )
    return scoped


def _columns_owned_by(select: exp.Select, root: exp.Expression | None = None) -> list[exp.Column]:
    if root is None:
        nodes: Iterable[exp.Column] = select.find_all(exp.Column)
    else:
        nodes = root.find_all(exp.Column)
    return [column for column in nodes if _nearest_select(column) is select]


def _field_is_present(
    columns: Iterable[exp.Column],
    *,
    alias: str,
    field: str,
    allow_unqualified: bool,
) -> bool:
    expected = field.lower()
    for column in columns:
        if column.name.lower() != expected:
            continue
        qualifier = column.table.lower()
        if qualifier == alias or (not qualifier and allow_unqualified):
            return True
    return False


def _normalized_expression(expression: exp.Expression) -> str:
    return re.sub(r"\s+", " ", expression.sql(dialect="presto", pretty=False).strip().lower())


def _check_group_by(select: exp.Select, issues: list[str]) -> None:
    group = select.args.get("group")
    if not isinstance(group, exp.Group):
        return
    group_expressions = list(group.expressions)
    normalized_groups = {_normalized_expression(item) for item in group_expressions}
    positional_groups = {
        int(item.this)
        for item in group_expressions
        if isinstance(item, exp.Literal) and item.is_int
    }
    for position, selected in enumerate(select.expressions, start=1):
        expression = selected.this if isinstance(selected, exp.Alias) else selected
        if isinstance(expression, exp.Star):
            continue
        if next(expression.find_all(exp.AggFunc), None) is not None:
            continue
        if next(expression.find_all(exp.Window), None) is not None:
            continue
        if position in positional_groups:
            continue
        normalized = _normalized_expression(expression)
        alias = selected.alias.lower() if isinstance(selected, exp.Alias) else ""
        if normalized in normalized_groups or (alias and alias in normalized_groups):
            continue
        issues.append(
            "group by 可能不完整，非聚合字段未分组："
            + selected.sql(dialect="presto", pretty=False)
        )


def _parse_statements(cleaned: str, issues: list[str]) -> list[exp.Expression]:
    try:
        return [statement for statement in sqlglot.parse(cleaned, read="presto") if statement is not None]
    except sqlglot.errors.ParseError as exc:
        issues.append(f"SQL AST 解析失败：{exc}")
        return []


def validate(sql: str, exploratory: bool = False, allow_unknown_tables: bool = False) -> list[str]:
    knowledge = load_knowledge()
    cleaned = strip_comments(sql)
    issues: list[str] = []

    for marker in CROSS_DOMAIN_MARKERS:
        if marker in cleaned:
            issues.append(f"疑似混入其他部门或市场顾问部专属口径：{marker}")

    if THREE_ARG_DATE_ADD_RE.search(cleaned):
        issues.append(
            "平台会将 date_add 解析为 Hive 两参数函数；禁止使用 Presto 三参数 "
            "date_add('day', n, expr)，请改用 interval 日期偏移"
        )

    statements = _parse_statements(cleaned, issues)
    for statement in statements:
        cte_names = {cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)}
        for select in statement.find_all(exp.Select):
            scoped_tables = _scoped_tables(select, cte_names=cte_names, knowledge=knowledge)
            all_columns = _columns_owned_by(select)
            where = select.args.get("where")
            where_columns = _columns_owned_by(select, where) if isinstance(where, exp.Where) else []
            group = select.args.get("group")
            group_columns = _columns_owned_by(select, group) if isinstance(group, exp.Group) else []
            allow_unqualified = len(scoped_tables) == 1

            for table in scoped_tables:
                if "." not in table.full_name:
                    issues.append(f"表名未使用完整库名前缀：{table.full_name}")
                if table.knowledge is None:
                    if not allow_unknown_tables:
                        issues.append(f"表未出现在青橙知识库：{table.full_name}")
                else:
                    tk = table.knowledge
                    if "dt" in {item.lower() for item in tk.partitions} and not _field_is_present(
                        where_columns,
                        alias=table.alias,
                        field="dt",
                        allow_unqualified=allow_unqualified,
                    ):
                        issues.append(f"分区表遗漏 dt 条件：{tk.full_name} alias {table.alias}")
                    hour_filtered = _field_is_present(
                        where_columns,
                        alias=table.alias,
                        field="hour",
                        allow_unqualified=allow_unqualified,
                    )
                    hour_explored = bool(group) and _field_is_present(
                        group_columns,
                        alias=table.alias,
                        field="hour",
                        allow_unqualified=allow_unqualified,
                    )
                    if tk.has_hour and not hour_filtered and not hour_explored:
                        issues.append(f"小时表建议补充 hour 条件：{tk.full_name} alias {table.alias}")
                    for field in tk.scope_fields:
                        referenced = _field_is_present(
                            all_columns,
                            alias=table.alias,
                            field=field,
                            allow_unqualified=allow_unqualified,
                        )
                        filtered = _field_is_present(
                            where_columns,
                            alias=table.alias,
                            field=field,
                            allow_unqualified=allow_unqualified,
                        )
                        if referenced and not filtered:
                            issues.append(f"涉及范围字段但未过滤：{table.alias}.{field}")

                    for column in all_columns:
                        if column.table.lower() != table.alias:
                            continue
                        field = column.name
                        if field == "*":
                            continue
                        if tk.fields and field not in tk.fields and field != "rn":
                            issues.append(
                                f"字段未出现在青橙知识库：{table.alias}.{field} -> {tk.full_name}"
                            )

                # Unknown or incompletely documented physical tables still get
                # generic department/project scope checks in their own SELECT.
                for column in all_columns:
                    if column.table.lower() != table.alias:
                        continue
                    field = column.name
                    if not DEPARTMENT_FIELD_RE.fullmatch(field):
                        continue
                    if not _field_is_present(
                        where_columns,
                        alias=table.alias,
                        field=field,
                        allow_unqualified=allow_unqualified,
                    ):
                        marker = f"涉及范围字段但未过滤：{table.alias}.{field}"
                        if marker not in issues:
                            issues.append(marker)

            _check_group_by(select, issues)

    if exploratory and not re.search(r"\blimit\s+\d+\b", cleaned, flags=re.I):
        issues.append("探索型查询遗漏 limit")

    for match in NUMERIC_STRING_RE.finditer(cleaned):
        issues.append(f"疑似字符串数字混用：{match.group(0)}")

    return list(dict.fromkeys(issues))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Presto SQL against Qingcheng internal rules.")
    parser.add_argument("--sql", help="SQL string")
    parser.add_argument("--sql-file", help="SQL file path")
    parser.add_argument("--exploratory", action="store_true", help="Require LIMIT for exploratory query")
    parser.add_argument(
        "--allow-unknown-tables",
        action="store_true",
        help="Do not fail when a table has not been ingested yet",
    )
    args = parser.parse_args()
    if args.sql_file:
        sql = Path(args.sql_file).read_text(encoding="utf-8")
    elif args.sql:
        sql = args.sql
    else:
        sql = input("SQL> ")
    issues = validate(sql, exploratory=args.exploratory, allow_unknown_tables=args.allow_unknown_tables)
    if issues:
        print("SQL rule validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("SQL rule validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
