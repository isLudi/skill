#!/usr/bin/env python3
"""Validate generated Presto SQL against dashboard-query rules."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "knowledge" / "tables"


PHYSICAL_TABLE_RE = re.compile(r"\b(from|join)\s+([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)?)\s*(?:as\s+)?([a-zA-Z_][\w]*)?", re.I)
CTE_RE = re.compile(r"(?:with|,)\s*([a-zA-Z_][\w]*)\s+as\s*\(", re.I)
ALIAS_FIELD_RE = re.compile(r"\b([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\b")
NUMERIC_STRING_RE = re.compile(r"\b([a-zA-Z_][\w]*(?:count|cnt|num|number|amount|id|sequence)[a-zA-Z_0-9]*)\s*(=|>=|<=|>|<)\s*'(\d+(?:\.\d+)?)'", re.I)
AGG_FUNC_RE = re.compile(r"\b(count|sum|avg|min|max)\s*\(", re.I)
THREE_ARG_DATE_ADD_RE = re.compile(r"\bdate_add\s*\(\s*'[^']+'\s*,", re.I)


@dataclass
class TableKnowledge:
    full_name: str
    fields: set[str]
    partitions: set[str]
    has_hour: bool
    department_fields: set[str]


def section(text: str, title: str) -> str:
    m = re.search(re.escape(title) + r"\n(.*?)(?=\n## \d+\.|\Z)", text, flags=re.S)
    return m.group(1).strip() if m else ""


def table_rows(markdown_table: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in markdown_table.splitlines():
        if not (line.strip().startswith("|") and line.strip().endswith("|")):
            continue
        if re.match(r"^\|\s*-+", line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] != "字段名":
            rows.append(cells)
    return rows


def load_knowledge() -> dict[str, TableKnowledge]:
    knowledge: dict[str, TableKnowledge] = {}
    for path in TABLE_DIR.glob("*.md"):
        if path.name.startswith("_") or path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        title = re.search(r"^#\s+(.+)$", text, flags=re.M)
        full_name = title.group(1).strip() if title else path.stem
        fields = {r[0] for r in table_rows(section(text, "## 7. 字段清单")) if r}
        partitions = {r[0] for r in table_rows(section(text, "## 5. 分区字段")) if r and r[0] != "无"}
        fields |= partitions
        department_fields = {f for f in fields if "department_name" in f}
        knowledge[full_name.lower()] = TableKnowledge(full_name, fields, partitions, "hour" in partitions, department_fields)
    return knowledge


def strip_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.M)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    return sql


def find_tables(sql: str) -> tuple[dict[str, str], list[str], set[str]]:
    cleaned = strip_comments(sql)
    ctes = set(m.group(1).lower() for m in CTE_RE.finditer(cleaned))
    aliases: dict[str, str] = {}
    raw_tables: list[str] = []
    for m in PHYSICAL_TABLE_RE.finditer(cleaned):
        table = m.group(2)
        alias = m.group(3) or table.split(".")[-1]
        raw_tables.append(table)
        if table.lower() not in ctes and "." in table:
            aliases[alias.lower()] = table.lower()
    return aliases, raw_tables, ctes


def where_fragment(sql: str) -> str:
    m = re.search(r"\bwhere\s+(.+?)(?=\bgroup\s+by\b|\border\s+by\b|\blimit\b|$)", strip_comments(sql), flags=re.I | re.S)
    return m.group(1) if m else ""


def select_fragment(sql: str) -> str:
    m = re.search(r"\bselect\s+(.+?)\bfrom\b", strip_comments(sql), flags=re.I | re.S)
    return m.group(1) if m else ""


def group_fragment(sql: str) -> str:
    m = re.search(r"\bgroup\s+by\s+(.+?)(?=\border\s+by\b|\blimit\b|$)", strip_comments(sql), flags=re.I | re.S)
    return m.group(1) if m else ""


def split_top_level_csv(fragment: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in fragment:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        if ch == "," and depth == 0:
            item = "".join(buf).strip()
            if item:
                parts.append(item)
            buf = []
        else:
            buf.append(ch)
    item = "".join(buf).strip()
    if item:
        parts.append(item)
    return parts


def _own_columns(expression: exp.Expression | None, select: exp.Select) -> list[exp.Column]:
    if expression is None:
        return []
    return [column for column in expression.find_all(exp.Column) if column.find_ancestor(exp.Select) is select]


def _matches_column(column: exp.Column, alias: str, field: str, scope: Scope) -> bool:
    if column.name.lower() != field.lower():
        return False
    if column.table:
        return column.table.lower() == alias.lower()
    # An unqualified field cannot prove a filter for both sides of a Join.
    return len(scope.selected_sources) == 1


def _normalized(expression: exp.Expression, scope: Scope) -> str:
    value = expression.this if isinstance(expression, exp.Alias) else expression
    value = value.copy()
    for node in value.walk():
        node.comments = []
        if isinstance(node, exp.Column) and not node.table and len(scope.selected_sources) == 1:
            node.set('table', exp.to_identifier(next(iter(scope.selected_sources))))
    return value.sql(dialect='presto', normalize=True)


def _regular_aggregate(node: exp.Expression, select: exp.Select) -> bool:
    if not isinstance(node, exp.AggFunc) or node.find_ancestor(exp.Select) is not select:
        return False
    window = node.find_ancestor(exp.Window)
    # SUM(x) OVER is a window operation; SUM(SUM(x)) OVER contains a regular inner SUM.
    return window is None or window.this is not node


def _group_issues(scope: Scope) -> list[str]:
    select = scope.expression
    if not isinstance(select, exp.Select):
        return []
    group = select.args.get('group')
    aggregating = any(_regular_aggregate(node, select) for item in select.expressions for node in item.walk())
    if group is None and not aggregating:
        return []
    aliases = {item.alias.lower(): item.this for item in select.expressions if isinstance(item, exp.Alias)}
    grouped: set[str] = set()
    for item in group.expressions if group else []:
        if isinstance(item, exp.Literal) and item.is_int and 1 <= int(item.this) <= len(select.expressions):
            item = select.expressions[int(item.this) - 1]
        elif isinstance(item, exp.Column) and not item.table and item.name.lower() in aliases:
            item = aliases[item.name.lower()]
        grouped.add(_normalized(item, scope))

    def covered(node: exp.Expression) -> bool:
        if _normalized(node, scope) in grouped or _regular_aggregate(node, select):
            return True
        if isinstance(node, exp.Query):
            return True  # The nested query is checked in its own scope.
        if isinstance(node, exp.Column) or isinstance(node, exp.Star):
            return False
        return all(covered(child) for child in node.iter_expressions())

    return [
        f"group by 可能不完整，非聚合字段未分组：{item.sql(dialect='presto')}"
        for item in select.expressions if not covered(item.this if isinstance(item, exp.Alias) else item)
    ]


def validate(sql: str, exploratory: bool = False) -> list[str]:
    knowledge = load_knowledge()
    cleaned = strip_comments(sql)
    issues: list[str] = []
    try:
        statements = sqlglot.parse(sql, read='presto')
        if len(statements) != 1 or statements[0] is None:
            return ['SQL 必须是单条完整语句']
        tree = statements[0]
        scopes = list(traverse_scope(tree))
    except (sqlglot.errors.ParseError, sqlglot.errors.OptimizeError) as error:
        return [f'SQL AST 解析失败：{error}']

    for scope in scopes:
        select = scope.expression
        if not isinstance(select, exp.Select):
            continue
        try:
            physical = {alias: source for alias, (_, source) in scope.selected_sources.items() if isinstance(source, exp.Table)}
        except sqlglot.errors.OptimizeError as error:
            issues.append(f'SQL 查询块来源解析失败：{error}')
            continue
        where = select.args.get('where')
        where_columns = _own_columns(where, select)
        local_columns = _own_columns(select, select)
        predicates = [
            node for node in where.walk() if isinstance(node, (exp.EQ, exp.In, exp.Like, exp.ILike))
            and node.find_ancestor(exp.Select) is select
        ] if where else []
        group = select.args.get('group')
        group_columns = _own_columns(group, select)
        for alias, table in physical.items():
            full_name = '.'.join(part for part in [table.catalog, table.db, table.name] if part).lower()
            if not table.db:
                issues.append(f'表名未使用完整库名前缀：{full_name}')
            tk = knowledge.get(full_name)
            if tk is None:
                issues.append(f'表未出现在知识库：{full_name}')
                continue
            if 'dt' in tk.partitions and not any(_matches_column(column, alias, 'dt', scope) for column in where_columns):
                issues.append(f'分区表遗漏 dt 条件：{tk.full_name} alias {alias}')
            hour_filtered = any(_matches_column(column, alias, 'hour', scope) for column in where_columns)
            hour_explored = any(_matches_column(column, alias, 'hour', scope) for column in group_columns)
            if tk.has_hour and not hour_filtered and not hour_explored:
                issues.append(f'小时表建议补充 hour 条件：{tk.full_name} alias {alias}')
            for field in sorted(tk.department_fields):
                referenced = any(_matches_column(column, alias, field, scope) for column in local_columns)
                filtered = any(
                    _matches_column(column, alias, field, scope)
                    for predicate in predicates for column in _own_columns(predicate, select)
                )
                if referenced and not filtered:
                    issues.append(f'涉及 department_name 字段但未过滤：{alias}.{field}')
            for column in local_columns:
                if column.table.lower() == alias.lower() and not column.is_star and column.name not in tk.fields | {'rn'}:
                    issues.append(f'字段未出现在知识库：{alias}.{column.name} -> {tk.full_name}')
        issues.extend(_group_issues(scope))

    if exploratory and tree.args.get('limit') is None:
        issues.append('探索型查询遗漏 limit')
    for match in NUMERIC_STRING_RE.finditer(cleaned):
        issues.append(f'疑似字符串数字混用：{match.group(0)}')
    if THREE_ARG_DATE_ADD_RE.search(cleaned):
        issues.append("平台会将 date_add 解析为 Hive 两参数函数；禁止使用 Presto 三参数 date_add('day', n, expr)，请改用 interval 日期偏移")
    return list(dict.fromkeys(issues))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Presto SQL against internal rules.")
    parser.add_argument("--sql", help="SQL string")
    parser.add_argument("--sql-file", help="SQL file path")
    parser.add_argument("--exploratory", action="store_true", help="Require LIMIT for exploratory query")
    args = parser.parse_args()
    if args.sql_file:
        sql = Path(args.sql_file).read_text(encoding="utf-8")
    elif args.sql:
        sql = args.sql
    else:
        sql = input("SQL> ")
    issues = validate(sql, exploratory=args.exploratory)
    if issues:
        print("SQL rule validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("SQL rule validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
