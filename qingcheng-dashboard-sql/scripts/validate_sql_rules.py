#!/usr/bin/env python3
"""Validate generated Presto SQL against Qingcheng dashboard-query rules."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIRS = [ROOT / "knowledge" / "tables", ROOT / "knowledge" / "temp_tables"]

PHYSICAL_TABLE_RE = re.compile(r"\b(from|join)\s+([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)?)\s*(?:as\s+)?([a-zA-Z_][\w]*)?", re.I)
CTE_RE = re.compile(r"(?:with|,)\s*([a-zA-Z_][\w]*)\s+as\s*\(", re.I)
ALIAS_FIELD_RE = re.compile(r"\b([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\b")
NUMERIC_STRING_RE = re.compile(r"\b([a-zA-Z_][\w]*(?:count|cnt|num|number|amount|id|sequence)[a-zA-Z_0-9]*)\s*(=|>=|<=|>|<)\s*'(\d+(?:\.\d+)?)'", re.I)
AGG_FUNC_RE = re.compile(r"\b(count|sum|avg|min|max)\s*\(", re.I)
THREE_ARG_DATE_ADD_RE = re.compile(r"\bdate_add\s*\(\s*'[^']+'\s*,", re.I)
DEPARTMENT_FIELD_RE = re.compile(r"\b([a-zA-Z_][\w]*department_name|department|dept|project_name|team_name)\b", re.I)

CROSS_DOMAIN_MARKERS = [
    "市场顾问部",
    "参评名单",
    "评优",
    "人产",
    "dingxi01_pingyou_jg",
    "dingxi01_jiagou_zx",
]


@dataclass
class TableKnowledge:
    full_name: str
    fields: set[str]
    partitions: set[str]
    has_hour: bool
    scope_fields: set[str]


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
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if cells and cells[0] not in {"字段名", "项目"}:
            rows.append(cells)
    return rows


def load_knowledge() -> dict[str, TableKnowledge]:
    knowledge: dict[str, TableKnowledge] = {}
    for table_dir in TABLE_DIRS:
        for path in table_dir.glob("*.md"):
            if path.name.startswith("_"):
                continue
            text = path.read_text(encoding="utf-8")
            title = re.search(r"^#\s+(.+)$", text, flags=re.M)
            full_name = title.group(1).strip() if title else path.stem
            fields = {r[0] for r in table_rows(section(text, "## 7. 字段清单")) if r}
            fields |= {r[0] for r in table_rows(section(text, "## 4. 字段清单")) if r}
            partitions = {r[0] for r in table_rows(section(text, "## 5. 分区字段")) if r and r[0] != "无"}
            fields |= partitions
            scope_fields = {
                f
                for f in fields
                if "department_name" in f
                or "department" in f
                or "dept" in f
                or "project" in f
                or "team" in f
            }
            knowledge[full_name.lower()] = TableKnowledge(full_name, fields, partitions, "hour" in partitions, scope_fields)
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


def validate(sql: str, exploratory: bool = False, allow_unknown_tables: bool = False) -> list[str]:
    knowledge = load_knowledge()
    cleaned = strip_comments(sql)
    aliases, raw_tables, ctes = find_tables(sql)
    issues: list[str] = []

    for marker in CROSS_DOMAIN_MARKERS:
        if marker in cleaned:
            issues.append(f"疑似混入其他部门或市场顾问部专属口径：{marker}")

    if THREE_ARG_DATE_ADD_RE.search(cleaned):
        issues.append("平台会将 date_add 解析为 Hive 两参数函数；禁止使用 Presto 三参数 date_add('day', n, expr)，请改用 interval 日期偏移")

    for table in raw_tables:
        if table.lower() in ctes:
            continue
        if "." not in table:
            issues.append(f"表名未使用完整库名前缀：{table}")

    where = where_fragment(sql)
    for alias, table_name in aliases.items():
        tk = knowledge.get(table_name)
        if tk is None:
            if not allow_unknown_tables:
                issues.append(f"表未出现在青橙知识库：{table_name}")
            continue
        if "dt" in tk.partitions and not re.search(rf"\b{re.escape(alias)}\.dt\b|\bdt\b", where, flags=re.I):
            issues.append(f"分区表遗漏 dt 条件：{tk.full_name} alias {alias}")
        hour_filtered = re.search(rf"\b{re.escape(alias)}\.hour\b|\bhour\b", where, flags=re.I)
        hour_explored = re.search(rf"\b{re.escape(alias)}\.hour\b", cleaned, flags=re.I) and re.search(r"\bgroup\s+by\b", cleaned, flags=re.I)
        if tk.has_hour and not hour_filtered and not hour_explored:
            issues.append(f"小时表建议补充 hour 条件：{tk.full_name} alias {alias}")
        for field in tk.scope_fields:
            referenced = re.search(rf"\b{re.escape(alias)}\.{re.escape(field)}\b|\b{re.escape(field)}\b", cleaned, flags=re.I)
            filtered = re.search(rf"\b{re.escape(alias)}\.{re.escape(field)}\b\s*(=|in|like)|\b{re.escape(field)}\b\s*(=|in|like)", where, flags=re.I)
            if referenced and not filtered:
                issues.append(f"涉及范围字段但未过滤：{alias}.{field}")

    for alias, field in ALIAS_FIELD_RE.findall(cleaned):
        table_name = aliases.get(alias.lower())
        if not table_name:
            continue
        tk = knowledge.get(table_name)
        if tk and tk.fields and field not in tk.fields and field not in {"rn"}:
            issues.append(f"字段未出现在青橙知识库：{alias}.{field} -> {tk.full_name}")

    generic_scope_fields = set(DEPARTMENT_FIELD_RE.findall(cleaned))
    for field in generic_scope_fields:
        if field.lower() in {"department", "dept"}:
            continue
        filtered = re.search(rf"\b{re.escape(field)}\b\s*(=|in|like)", where, flags=re.I)
        if not filtered:
            issues.append(f"SQL 涉及疑似部门/项目范围字段但 where 中未过滤：{field}")

    if exploratory and not re.search(r"\blimit\s+\d+\b", cleaned, flags=re.I):
        issues.append("探索型查询遗漏 limit")

    for m in NUMERIC_STRING_RE.finditer(cleaned):
        issues.append(f"疑似字符串数字混用：{m.group(0)}")

    select_items = split_top_level_csv(select_fragment(sql))
    group_text = group_fragment(sql)
    if group_text:
        group_items = {re.sub(r"\s+", " ", x.strip().lower()) for x in split_top_level_csv(group_text)}
        for item in select_items:
            normalized = re.sub(r"\s+as\s+[a-zA-Z_][\w]*$", "", item, flags=re.I).strip()
            normalized = re.sub(r"\s+", " ", normalized.lower())
            if AGG_FUNC_RE.search(item) or normalized in {"*", ""}:
                continue
            if normalized not in group_items:
                issues.append(f"group by 可能不完整，非聚合字段未分组：{item}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Presto SQL against Qingcheng internal rules.")
    parser.add_argument("--sql", help="SQL string")
    parser.add_argument("--sql-file", help="SQL file path")
    parser.add_argument("--exploratory", action="store_true", help="Require LIMIT for exploratory query")
    parser.add_argument("--allow-unknown-tables", action="store_true", help="Do not fail when a table has not been ingested yet")
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
