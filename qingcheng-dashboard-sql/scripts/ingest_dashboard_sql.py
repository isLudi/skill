#!/usr/bin/env python3
"""Ingest Qingcheng historical dashboard SQL into Markdown knowledge files."""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_SQL = ROOT / "resources" / "raw_sql"
DASHBOARDS = ROOT / "knowledge" / "dashboards"
METRICS = ROOT / "knowledge" / "metrics"
TEMP_TABLES = ROOT / "knowledge" / "temp_tables"
CHANGELOG = ROOT / "knowledge" / "update_log" / "changelog.md"

TABLE_RE = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][\w]*\.[a-zA-Z_][\w]*)\s*(?:as\s+)?([a-zA-Z_][\w]*)?", re.I)
CTE_RE = re.compile(r"(?:with|,)\s*([a-zA-Z_][\w]*)\s+as\s*\(", re.I)
JOIN_KEY_RE = re.compile(r"\bjoin\b.*?\bon\s+(.+?)(?=\b(?:left|right|inner|full|join|where|group|order|limit)\b|$)", re.I | re.S)
WHERE_RE = re.compile(r"\bwhere\s+(.+?)(?=\bgroup\s+by\b|\border\s+by\b|\blimit\b|$)", re.I | re.S)
GROUP_RE = re.compile(r"\bgroup\s+by\s+(.+?)(?=\border\s+by\b|\blimit\b|$)", re.I | re.S)
AGG_RE = re.compile(r"((?:count|sum|avg|min|max)\s*\([^)]+\)\s*(?:as\s+[a-zA-Z_][\w]*)?)", re.I)


def clean_sql(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.M)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    return sql


def split_csv(fragment: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in fragment:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        if ch == "," and depth == 0:
            item = re.sub(r"\s+", " ", "".join(buf).strip())
            if item:
                parts.append(item)
            buf = []
        else:
            buf.append(ch)
    item = re.sub(r"\s+", " ", "".join(buf).strip())
    if item:
        parts.append(item)
    return parts


def safe_name(name: str) -> str:
    name = re.sub(r"[^\w.-]+", "_", name.strip(), flags=re.U)
    name = name.strip("._")
    return name or "qingcheng_dashboard"


def parse(sql: str) -> dict:
    cleaned = clean_sql(sql)
    tables = [(m.group(1), m.group(2) or "") for m in TABLE_RE.finditer(cleaned)]
    ctes = [m.group(1) for m in CTE_RE.finditer(cleaned)]
    joins = [re.sub(r"\s+", " ", m.group(1).strip()) for m in JOIN_KEY_RE.finditer(cleaned)]
    wheres = [re.sub(r"\s+", " ", m.group(1).strip()) for m in WHERE_RE.finditer(cleaned)]
    groups = []
    for m in GROUP_RE.finditer(cleaned):
        groups.extend(split_csv(m.group(1)))
    aggs = [re.sub(r"\s+", " ", m.group(1).strip()) for m in AGG_RE.finditer(cleaned)]
    temp_tables = sorted({table for table, _ in tables if table.lower().startswith("temp_table.")})
    return {"tables": tables, "ctes": ctes, "joins": joins, "wheres": wheres, "groups": groups, "aggs": aggs, "temp_tables": temp_tables}


def dashboard_md(name: str, source: Path, parsed: dict) -> str:
    table_lines = ["| 表名 | 别名 | 用途 | 状态 |", "|---|---|---|---|"]
    for table, alias in parsed["tables"]:
        table_lines.append(f"| {table} | {alias or '待确认'} | 待人工确认 | 从 SQL 自动解析 |")
    if len(table_lines) == 2:
        table_lines.append("| 待确认 | 待确认 | 未解析到完整库名表 | 待人工确认 |")

    temp_lines = ["| 表名 | 用途 | 口径状态 |", "|---|---|---|"]
    for table in parsed["temp_tables"]:
        temp_lines.append(f"| {table} | 待人工确认 | 待人工确认 |")
    if len(temp_lines) == 2:
        temp_lines.append("| 无 | - | - |")

    cte_lines = ["| CTE | 用途 | 关键字段 |", "|---|---|---|"]
    for cte in parsed["ctes"]:
        cte_lines.append(f"| {cte} | 待人工确认 | 待人工确认 |")
    if len(cte_lines) == 2:
        cte_lines.append("| 无 | - | - |")

    join_lines = ["| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |", "|---|---|---|---|---|"]
    for cond in parsed["joins"]:
        join_lines.append(f"| 待确认 | 待确认 | `{cond}` | 待确认 | 自动解析，需人工确认 |")
    if len(join_lines) == 2:
        join_lines.append("| 无 | 无 | 无 | - | 未解析到 join |")

    metric_lines = ["| 指标名 | SQL 表达式 | 口径说明 | 状态 |", "|---|---|---|---|"]
    for idx, agg in enumerate(parsed["aggs"], start=1):
        metric_lines.append(f"| metric_{idx} | `{agg}` | 从 SQL 自动抽取 | 待人工确认 |")
    if len(metric_lines) == 2:
        metric_lines.append("| 待确认 | 待确认 | 未解析到聚合表达式 | 待人工确认 |")

    return f"""# {name}

## 1. 来源

`{source.name}`

解析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 2. 查询目标

待人工补充。

## 3. 使用表

{chr(10).join(table_lines)}

## 4. 使用临时表

{chr(10).join(temp_lines)}

## 5. CTE 结构

{chr(10).join(cte_lines)}

## 6. join 关系

{chr(10).join(join_lines)}

## 7. where 条件

{chr(10).join(f'- `{w}`' for w in parsed['wheres']) or '- 未解析到 where；需确认是否存在无分区扫描或缺少青橙范围限定风险。'}

## 8. group by 维度

{chr(10).join(f'- `{g}`' for g in parsed['groups']) or '- 未解析到 group by。'}

## 9. 聚合指标

{chr(10).join(metric_lines)}

## 10. 待确认事项

- 自动解析结果需人工确认。
- 指标口径如果未在 `knowledge/metrics/` 中存在，必须补充定义后再用于生产 SQL。
- 临时表语义如果未在 `knowledge/temp_tables/` 中确认，不得跨看板复用。
- 确认没有套用市场顾问部或其他部门专属口径。
"""


def metric_stub(name: str, expr: str, dashboard: str) -> str:
    return f"""# {name}

## 1. 中文名称

待人工确认

## 2. 指标定义

从 `{dashboard}` 自动抽取，口径待人工确认。

## 3. SQL 表达式

```sql
{expr}
```

## 4. 适用表

待人工确认

## 5. 分子口径

待人工确认

## 6. 分母口径

待人工确认

## 7. 时间口径

待人工确认

## 8. 青橙范围限定

待人工确认

## 9. 计算粒度

待人工确认

## 10. 最终输出粒度

待人工确认

## 11. 冲突说明

待人工确认。不得默认复用其他部门同名指标。

## 12. 待人工确认

是
"""


def temp_table_stub(table: str, dashboard: str) -> str:
    return f"""# {table}

## 1. 临时表用途

从 `{dashboard}` 自动解析发现，具体用途待人工确认。

## 2. 来源和刷新方式

| 项目 | 内容 |
|---|---|
| 创建来源 | 待人工确认 |
| 刷新方式 | 待人工确认 |
| 刷新频率 | 待人工确认 |
| 有效期 | 待人工确认 |

## 3. 数据粒度

待人工确认

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| 待人工确认 | 待人工确认 | 待人工确认 | 待人工确认 |

## 5. 适用看板

- `{dashboard}`

## 6. join key

- 待人工确认

## 7. 不可复用边界

- 待人工确认

## 8. 待确认事项

- 确认该临时表是否为青橙项目部专用。
- 确认是否可跨看板复用。
"""


def append_changelog(source: Path, dashboard_name: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## {now}\n\n- 入库青橙看板 SQL `{source.name}`，生成 `{dashboard_name}` 初始看板知识文档和指标/临时表待确认项。\n"
    CHANGELOG.parent.mkdir(parents=True, exist_ok=True)
    if CHANGELOG.exists():
        current = CHANGELOG.read_text(encoding="utf-8")
        CHANGELOG.write_text(current.rstrip() + "\n" + entry, encoding="utf-8")
    else:
        CHANGELOG.write_text("# 更新日志\n" + entry, encoding="utf-8")


def copy_to_raw_sql(path: Path) -> Path:
    RAW_SQL.mkdir(parents=True, exist_ok=True)
    if path.resolve().parent == RAW_SQL.resolve():
        return path
    target = RAW_SQL / path.name
    if target.exists():
        target = RAW_SQL / f"{path.stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}{path.suffix}"
    shutil.copyfile(path, target)
    return target


def ingest_file(path: Path, overwrite: bool = False, copy_raw: bool = True) -> Path:
    source = copy_to_raw_sql(path) if copy_raw else path
    sql = source.read_text(encoding="utf-8")
    parsed = parse(sql)
    DASHBOARDS.mkdir(parents=True, exist_ok=True)
    METRICS.mkdir(parents=True, exist_ok=True)
    TEMP_TABLES.mkdir(parents=True, exist_ok=True)

    name = safe_name(source.stem)
    dashboard_target = DASHBOARDS / f"{name}.md"
    if overwrite or not dashboard_target.exists():
        dashboard_target.write_text(dashboard_md(name, source, parsed), encoding="utf-8")

    for idx, agg in enumerate(parsed["aggs"], start=1):
        metric_path = METRICS / f"{name}_metric_{idx}.md"
        if overwrite or not metric_path.exists():
            metric_path.write_text(metric_stub(f"{name}_metric_{idx}", agg, name), encoding="utf-8")

    for table in parsed["temp_tables"]:
        temp_path = TEMP_TABLES / f"{table}.md"
        if overwrite or not temp_path.exists():
            temp_path.write_text(temp_table_stub(table, name), encoding="utf-8")

    append_changelog(source, name)
    return dashboard_target


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Qingcheng dashboard SQL files.")
    parser.add_argument("--sql-file", action="append", help="Specific SQL file. Defaults to resources/raw_sql/*.sql")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing dashboard/metric/temp-table docs")
    parser.add_argument("--no-copy-raw", action="store_true", help="Do not copy external SQL files into resources/raw_sql")
    args = parser.parse_args()

    files = [Path(p) for p in args.sql_file] if args.sql_file else sorted(RAW_SQL.glob("*.sql"))
    if not files:
        print(f"No SQL files found in {RAW_SQL}")
        return 0

    targets = [ingest_file(path, overwrite=args.overwrite, copy_raw=not args.no_copy_raw) for path in files]
    print(f"Ingested {len(targets)} Qingcheng dashboard SQL file(s).")
    for target in targets:
        print(f"- {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

