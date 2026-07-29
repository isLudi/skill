#!/usr/bin/env python3
"""Ingest historical dashboard SQL into Markdown knowledge files."""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_SQL = ROOT / "resources" / "raw_sql"
DASHBOARDS = ROOT / "knowledge" / "dashboards"
METRICS = ROOT / "knowledge" / "metrics"
JOINS = ROOT / "knowledge" / "joins" / "table_relationships.md"


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
    return [re.sub(r"\s+", " ", x.strip()) for x in fragment.split(",") if x.strip()]


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
    return {"tables": tables, "ctes": ctes, "joins": joins, "wheres": wheres, "groups": groups, "aggs": aggs}


def dashboard_md(name: str, source: Path, parsed: dict) -> str:
    table_lines = ["| 表名 | 别名 | 用途 |", "|---|---|---|"]
    for table, alias in parsed["tables"]:
        table_lines.append(f"| {table} | {alias or '待确认'} | 待人工确认 |")
    if len(table_lines) == 2:
        table_lines.append("| 待确认 | 待确认 | 未解析到完整库名表 |")

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

## 4. CTE 结构

{chr(10).join(cte_lines)}

## 5. join 关系

{chr(10).join(join_lines)}

## 6. where 条件

{chr(10).join(f'- `{w}`' for w in parsed['wheres']) or '- 未解析到 where；需确认是否存在无分区扫描风险。'}

## 7. group by 维度

{chr(10).join(f'- `{g}`' for g in parsed['groups']) or '- 未解析到 group by。'}

## 8. 聚合指标

{chr(10).join(metric_lines)}

## 9. 可复用 SQL 模式

- 待人工整理。

## 10. 待确认事项

- 自动解析结果需人工确认。
- 指标口径如果未在 `knowledge/metrics/` 中存在，必须补充定义后再用于生产 SQL。
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

## 5. 分母/分子口径

待人工确认

## 6. 时间口径

待人工确认

## 7. 范围限定

待人工确认

## 8. 待人工确认

是
"""


def ingest_file(path: Path, overwrite: bool = False) -> Path:
    sql = path.read_text(encoding="utf-8")
    parsed = parse(sql)
    DASHBOARDS.mkdir(parents=True, exist_ok=True)
    METRICS.mkdir(parents=True, exist_ok=True)
    name = path.stem
    target = DASHBOARDS / f"{name}.md"
    if overwrite or not target.exists():
        target.write_text(dashboard_md(name, path, parsed), encoding="utf-8")
    for idx, agg in enumerate(parsed["aggs"], start=1):
        metric_path = METRICS / f"{name}_metric_{idx}.md"
        if overwrite or not metric_path.exists():
            metric_path.write_text(metric_stub(f"{name}_metric_{idx}", agg, name), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest dashboard SQL files.")
    parser.add_argument("--sql-file", action="append", help="Specific SQL file. Defaults to resources/raw_sql/*.sql")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing dashboard/metric docs")
    args = parser.parse_args()
    files = [Path(p) for p in args.sql_file] if args.sql_file else sorted(RAW_SQL.glob("*.sql"))
    if not files:
        print(f"No SQL files found in {RAW_SQL}")
        return 0
    targets = [ingest_file(path, args.overwrite) for path in files]
    print(f"Ingested {len(targets)} dashboard SQL files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
