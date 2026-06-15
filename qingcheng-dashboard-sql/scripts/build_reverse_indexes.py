#!/usr/bin/env python3
"""Build lightweight reverse indexes for dashboard SQL knowledge."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
RAW_SQL = ROOT / "resources" / "raw_sql"
OUT_DIR = KNOWLEDGE / "reverse_index"

TABLE_RE = re.compile(r"\b[a-zA-Z_][\w]*\.[a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)?\b")
RAW_SQL_RE = re.compile(r"(?:resources/raw_sql/)?([A-Za-z0-9_.-]+\.sql)")
IDENT_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")
HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$")

SKIP_IDENTIFIERS = {
    "as",
    "by",
    "case",
    "cast",
    "coalesce",
    "count",
    "date",
    "date_add",
    "date_diff",
    "day",
    "distinct",
    "else",
    "end",
    "from",
    "group",
    "hour",
    "if",
    "in",
    "interval",
    "join",
    "left",
    "max",
    "min",
    "null",
    "nvl",
    "on",
    "or",
    "regexp_extract",
    "right",
    "select",
    "sum",
    "then",
    "where",
    "with",
}

RISK_KEYWORDS = (
    "待确认",
    "待人工确认",
    "风险",
    "放大",
    "重复",
    "唯一",
    "未带",
    "过滤",
    "错位",
    "漂移",
    "吞",
    "null",
    "空",
    "跨年",
    "硬编码",
    "误匹配",
    "权限",
    "报错",
)

TABLE_PREFIXES = (
    "bdg_ba.",
    "dw.",
    "finance_dw.",
    "gaotu_crm_offline_statistics.",
    "service_dw.",
    "temp_table.",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def iter_md(folder: str) -> list[Path]:
    root = KNOWLEDGE / folder
    if not root.exists():
        return []
    return sorted(
        p
        for p in root.glob("*.md")
        if not p.name.startswith("_") and p.name.lower() != "readme.md"
    )


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            return match.group(2).strip()
    return fallback


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def link(path: Path, label: str | None = None) -> str:
    label = label or rel(path)
    if path.is_relative_to(KNOWLEDGE):
        target = "../" + path.relative_to(KNOWLEDGE).as_posix()
    else:
        target = rel(path)
    return f"[{label}]({target})"


def raw_link(name: str) -> str:
    path = RAW_SQL / name
    if path.exists():
        return f"[{name}](../../resources/raw_sql/{name})"
    return f"`{name}`"


def is_table_name(value: str) -> bool:
    low = value.lower()
    if low.endswith((".md", ".sql", ".xlsx", ".json")):
        return False
    return any(low.startswith(prefix) for prefix in TABLE_PREFIXES)


def clean_cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", " ").strip()


def normalize_risk_line(line: str) -> str:
    if line.startswith("|"):
        parts = [part.strip() for part in line.strip("|").split("|")]
        parts = [part for part in parts if part and set(part) != {"-"}]
        return " / ".join(parts)
    return line


def collect_known_tables() -> set[str]:
    tables: set[str] = set()
    for folder in ("tables", "temp_tables"):
        for path in iter_md(folder):
            tables.add(path.stem)

    index_path = KNOWLEDGE / "01_table_index.md"
    if index_path.exists():
        tables.update(table for table in TABLE_RE.findall(read_text(index_path)) if is_table_name(table))
    return tables


def extract_tables(text: str, known_tables: set[str]) -> set[str]:
    found = set(TABLE_RE.findall(text))
    if known_tables:
        return {table for table in found if table in known_tables}
    return found


def extract_raw_sqls(text: str) -> set[str]:
    names = set(RAW_SQL_RE.findall(text))
    if not names:
        return set()
    raw_names = {p.name for p in RAW_SQL.glob("*.sql")}
    return {name for name in names if name in raw_names or "/" not in name}


def extract_identifiers(text: str) -> set[str]:
    identifiers = set()
    for ident in IDENT_RE.findall(text):
        low = ident.lower()
        if low in SKIP_IDENTIFIERS:
            continue
        if len(ident) <= 1:
            continue
        identifiers.add(ident)
    return identifiers


def collect_dashboards(known_tables: set[str]) -> list[dict[str, object]]:
    dashboards: list[dict[str, object]] = []
    for path in iter_md("dashboards"):
        text = read_text(path)
        dashboards.append(
            {
                "path": path,
                "title": first_heading(text, path.stem),
                "tables": extract_tables(text, known_tables),
                "raw_sqls": extract_raw_sqls(text),
            }
        )
    return dashboards


def collect_metrics(known_tables: set[str]) -> list[dict[str, object]]:
    metrics: list[dict[str, object]] = []
    for path in iter_md("metrics"):
        text = read_text(path)
        metrics.append(
            {
                "path": path,
                "title": first_heading(text, path.stem),
                "fields": extract_identifiers(text),
                "tables": extract_tables(text, known_tables),
                "raw_sqls": extract_raw_sqls(text),
            }
        )
    return metrics


def format_links(paths: list[Path], max_items: int = 6) -> str:
    if not paths:
        return "-"
    items = [link(path, path.stem) for path in paths[:max_items]]
    if len(paths) > max_items:
        items.append(f"... +{len(paths) - max_items}")
    return "<br>".join(items)


def format_raws(raws: set[str], max_items: int = 5) -> str:
    if not raws:
        return "-"
    sorted_raws = sorted(raws)
    items = [raw_link(name) for name in sorted_raws[:max_items]]
    if len(sorted_raws) > max_items:
        items.append(f"... +{len(sorted_raws) - max_items}")
    return "<br>".join(items)


def build_field_to_metrics(metrics: list[dict[str, object]]) -> str:
    field_map: dict[str, list[dict[str, object]]] = defaultdict(list)
    for metric in metrics:
        for field in metric["fields"]:
            field_map[field].append(metric)

    lines = [
        "# 字段到指标反向索引",
        "",
        "> 由 `scripts/build_reverse_indexes.py` 自动生成。字段/标识符只用于候选定位，最终口径以 metrics/dashboard 文档为准。",
        "",
        "| 字段/标识符 | 相关指标文档 | 来源 raw SQL |",
        "|---|---|---|",
    ]
    for field in sorted(field_map, key=str.lower):
        entries = field_map[field]
        paths = [entry["path"] for entry in entries]
        raws: set[str] = set()
        for entry in entries:
            raws.update(entry["raw_sqls"])
        lines.append(f"| `{field}` | {format_links(paths)} | {format_raws(raws)} |")
    return "\n".join(lines) + "\n"


def build_metric_to_raw_sql(metrics: list[dict[str, object]]) -> str:
    lines = [
        "# 指标到 raw SQL 反向索引",
        "",
        "> 由 `scripts/build_reverse_indexes.py` 自动生成。用于从指标文档快速回到证据 SQL。",
        "",
        "| 指标文档 | 来源 raw SQL | 相关表 |",
        "|---|---|---|",
    ]
    for metric in sorted(metrics, key=lambda item: rel(item["path"])):
        tables = "<br>".join(f"`{table}`" for table in sorted(metric["tables"])) or "-"
        lines.append(
            f"| {link(metric['path'], metric['title'])} | {format_raws(metric['raw_sqls'])} | {tables} |"
        )
    return "\n".join(lines) + "\n"


def build_table_to_dashboards(dashboards: list[dict[str, object]], metrics: list[dict[str, object]]) -> str:
    table_map: dict[str, dict[str, set[Path] | set[str]]] = defaultdict(
        lambda: {"dashboards": set(), "metrics": set(), "raw_sqls": set()}
    )
    for dashboard in dashboards:
        for table in dashboard["tables"]:
            table_map[table]["dashboards"].add(dashboard["path"])
            table_map[table]["raw_sqls"].update(dashboard["raw_sqls"])
    for metric in metrics:
        for table in metric["tables"]:
            table_map[table]["metrics"].add(metric["path"])
            table_map[table]["raw_sqls"].update(metric["raw_sqls"])

    lines = [
        "# 表到看板反向索引",
        "",
        "> 由 `scripts/build_reverse_indexes.py` 自动生成。表被引用不代表同一 join/范围口径可跨看板复用。",
        "",
        "| 表 | 看板文档 | 指标文档 | 来源 raw SQL |",
        "|---|---|---|---|",
    ]
    for table in sorted(table_map, key=str.lower):
        entry = table_map[table]
        dashboards_sorted = sorted(entry["dashboards"], key=rel)
        metrics_sorted = sorted(entry["metrics"], key=rel)
        lines.append(
            f"| `{table}` | {format_links(dashboards_sorted)} | {format_links(metrics_sorted)} | {format_raws(entry['raw_sqls'])} |"
        )
    return "\n".join(lines) + "\n"


def risk_sources() -> list[Path]:
    folders = ["joins", "pitfalls", "sql_patterns"]
    paths: list[Path] = []
    for folder in folders:
        root = KNOWLEDGE / folder
        if root.exists():
            paths.extend(sorted(root.glob("*.md")))
    return [p for p in paths if not p.name.startswith("_")]


def build_join_risk_index() -> str:
    lines = [
        "# JOIN 与结果异常风险索引",
        "",
        "> 由 `scripts/build_reverse_indexes.py` 自动生成。用于 debug 空结果、行数放大、指标变 0、范围错位和平台限制。",
        "",
        "| 来源 | 上下文 | 风险线索 |",
        "|---|---|---|",
    ]

    for path in risk_sources():
        current_heading = path.stem
        for raw_line in read_text(path).splitlines():
            heading = HEADING_RE.match(raw_line)
            if heading:
                current_heading = heading.group(2).strip()
                continue
            line = normalize_risk_line(raw_line.strip())
            if not line or line.startswith("|---"):
                continue
            lower_line = line.lower()
            if not any(keyword.lower() in lower_line for keyword in RISK_KEYWORDS):
                continue
            if len(line) > 220:
                line = line[:217] + "..."
            lines.append(f"| {link(path, rel(path))} | {clean_cell(current_heading)} | {clean_cell(line)} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    if not KNOWLEDGE.exists():
        print(f"missing knowledge dir: {KNOWLEDGE}", file=sys.stderr)
        return 1

    known_tables = collect_known_tables()
    dashboards = collect_dashboards(known_tables)
    metrics = collect_metrics(known_tables)

    outputs = {
        "field_to_metrics.md": build_field_to_metrics(metrics),
        "metric_to_raw_sql.md": build_metric_to_raw_sql(metrics),
        "table_to_dashboards.md": build_table_to_dashboards(dashboards, metrics),
        "join_risk_index.md": build_join_risk_index(),
    }
    for name, text in outputs.items():
        write_text(OUT_DIR / name, text)
        print(f"[OK] wrote knowledge/reverse_index/{name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
