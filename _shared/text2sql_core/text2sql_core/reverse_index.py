"""Build deterministic reverse indexes for one domain skill.

The caller must pass an explicit skill root.  This keeps discovery and writes
inside one business domain even though the implementation is shared.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Sequence


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

OUTPUT_NAMES = (
    "field_to_metrics.md",
    "metric_to_raw_sql.md",
    "table_to_dashboards.md",
    "join_risk_index.md",
)


class ReverseIndexBuilder:
    """Render reverse indexes from exactly one skill root."""

    def __init__(self, skill_root: Path) -> None:
        self.root = Path(skill_root).resolve()
        self.knowledge = self.root / "knowledge"
        self.raw_sql = self.root / "resources" / "raw_sql"
        self.out_dir = self.knowledge / "reverse_index"
        self._raw_names = {
            path.name.lower(): path.name
            for path in self.raw_sql.glob("*.sql")
            if path.is_file()
        }

    @staticmethod
    def read_text(path: Path) -> str:
        # utf-8-sig consumes a leading BOM; lstrip also repairs duplicated BOMs.
        return path.read_text(encoding="utf-8-sig").lstrip("\ufeff")

    @staticmethod
    def write_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    def iter_md(self, folder: str) -> list[Path]:
        root = self.knowledge / folder
        if not root.exists():
            return []
        return sorted(
            path
            for path in root.glob("*.md")
            if not path.name.startswith("_") and path.name.lower() != "readme.md"
        )

    @staticmethod
    def first_heading(text: str, fallback: str) -> str:
        for line in text.lstrip("\ufeff").splitlines():
            match = HEADING_RE.match(line.lstrip("\ufeff"))
            if match:
                return match.group(2).strip().lstrip("\ufeff")
        return fallback

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def link(self, path: Path, label: str | None = None) -> str:
        label = label or self.rel(path)
        if path.is_relative_to(self.knowledge):
            target = "../" + path.relative_to(self.knowledge).as_posix()
        else:
            target = self.rel(path)
        return f"[{label}]({target})"

    def raw_link(self, name: str) -> str:
        canonical = self._raw_names.get(name.lower())
        if canonical is None:
            raise ValueError(f"raw SQL is outside this skill or does not exist: {name}")
        return f"[{canonical}](../../resources/raw_sql/{canonical})"

    @staticmethod
    def is_table_name(value: str) -> bool:
        low = value.lower()
        if low.endswith((".md", ".sql", ".xlsx", ".json")):
            return False
        return any(low.startswith(prefix) for prefix in TABLE_PREFIXES)

    @staticmethod
    def clean_cell(value: str) -> str:
        return value.replace("|", r"\|").replace("\n", " ").strip()

    @staticmethod
    def normalize_risk_line(line: str) -> str:
        if line.startswith("|"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            parts = [part for part in parts if part and set(part) != {"-"}]
            return " / ".join(parts)
        return line

    def collect_known_tables(self) -> set[str]:
        tables: set[str] = set()
        for folder in ("tables", "temp_tables"):
            for path in self.iter_md(folder):
                tables.add(path.stem)
        index_path = self.knowledge / "01_table_index.md"
        if index_path.exists():
            tables.update(
                table
                for table in TABLE_RE.findall(self.read_text(index_path))
                if self.is_table_name(table)
            )
        return tables

    @staticmethod
    def extract_tables(text: str, known_tables: set[str]) -> set[str]:
        found = set(TABLE_RE.findall(text))
        if known_tables:
            return {table for table in found if table in known_tables}
        return found

    def extract_raw_sqls(self, text: str) -> set[str]:
        # Only canonical filenames present under this skill are valid evidence.
        found: set[str] = set()
        for candidate in RAW_SQL_RE.findall(text):
            canonical = self._raw_names.get(candidate.lower())
            if canonical is not None:
                found.add(canonical)
        return found

    @staticmethod
    def extract_identifiers(text: str) -> set[str]:
        identifiers: set[str] = set()
        for ident in IDENT_RE.findall(text):
            if ident.lower() in SKIP_IDENTIFIERS or len(ident) <= 1:
                continue
            identifiers.add(ident)
        return identifiers

    def collect_dashboards(self, known_tables: set[str]) -> list[dict[str, object]]:
        dashboards: list[dict[str, object]] = []
        for path in self.iter_md("dashboards"):
            text = self.read_text(path)
            dashboards.append(
                {
                    "path": path,
                    "title": self.first_heading(text, path.stem),
                    "tables": self.extract_tables(text, known_tables),
                    "raw_sqls": self.extract_raw_sqls(text),
                }
            )
        return dashboards

    def collect_metrics(self, known_tables: set[str]) -> list[dict[str, object]]:
        metrics: list[dict[str, object]] = []
        for path in self.iter_md("metrics"):
            text = self.read_text(path)
            metrics.append(
                {
                    "path": path,
                    "title": self.first_heading(text, path.stem),
                    "fields": self.extract_identifiers(text),
                    "tables": self.extract_tables(text, known_tables),
                    "raw_sqls": self.extract_raw_sqls(text),
                }
            )
        return metrics

    def format_links(self, paths: list[Path], max_items: int = 6) -> str:
        if not paths:
            return "-"
        items = [self.link(path, path.stem) for path in paths[:max_items]]
        if len(paths) > max_items:
            items.append(f"... +{len(paths) - max_items}")
        return "<br>".join(items)

    def format_raws(self, raws: set[str], max_items: int = 5) -> str:
        if not raws:
            return "-"
        sorted_raws = sorted(raws, key=str.lower)
        items = [self.raw_link(name) for name in sorted_raws[:max_items]]
        if len(sorted_raws) > max_items:
            items.append(f"... +{len(sorted_raws) - max_items}")
        return "<br>".join(items)

    def build_field_to_metrics(self, metrics: list[dict[str, object]]) -> str:
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
            lines.append(f"| `{field}` | {self.format_links(paths)} | {self.format_raws(raws)} |")
        return "\n".join(lines) + "\n"

    def build_metric_to_raw_sql(self, metrics: list[dict[str, object]]) -> str:
        lines = [
            "# 指标到 raw SQL 反向索引",
            "",
            "> 由 `scripts/build_reverse_indexes.py` 自动生成。用于从指标文档快速回到证据 SQL。",
            "",
            "| 指标文档 | 来源 raw SQL | 相关表 |",
            "|---|---|---|",
        ]
        for metric in sorted(metrics, key=lambda item: self.rel(item["path"])):
            tables = "<br>".join(f"`{table}`" for table in sorted(metric["tables"])) or "-"
            lines.append(
                f"| {self.link(metric['path'], metric['title'])} | "
                f"{self.format_raws(metric['raw_sqls'])} | {tables} |"
            )
        return "\n".join(lines) + "\n"

    def build_table_to_dashboards(
        self,
        dashboards: list[dict[str, object]],
        metrics: list[dict[str, object]],
    ) -> str:
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
            dashboards_sorted = sorted(entry["dashboards"], key=self.rel)
            metrics_sorted = sorted(entry["metrics"], key=self.rel)
            lines.append(
                f"| `{table}` | {self.format_links(dashboards_sorted)} | "
                f"{self.format_links(metrics_sorted)} | {self.format_raws(entry['raw_sqls'])} |"
            )
        return "\n".join(lines) + "\n"

    def risk_sources(self) -> list[Path]:
        paths: list[Path] = []
        for folder in ("joins", "pitfalls", "sql_patterns"):
            root = self.knowledge / folder
            if root.exists():
                paths.extend(sorted(root.glob("*.md")))
        return [path for path in paths if not path.name.startswith("_")]

    def build_join_risk_index(self) -> str:
        lines = [
            "# JOIN 与结果异常风险索引",
            "",
            "> 由 `scripts/build_reverse_indexes.py` 自动生成。用于 debug 空结果、行数放大、指标变 0、范围错位和平台限制。",
            "",
            "| 来源 | 上下文 | 风险线索 |",
            "|---|---|---|",
        ]
        for path in self.risk_sources():
            current_heading = path.stem
            for raw_line in self.read_text(path).splitlines():
                heading = HEADING_RE.match(raw_line.lstrip("\ufeff"))
                if heading:
                    current_heading = heading.group(2).strip().lstrip("\ufeff")
                    continue
                line = self.normalize_risk_line(raw_line.strip())
                if not line or line.startswith("|---"):
                    continue
                lower_line = line.lower()
                if not any(keyword.lower() in lower_line for keyword in RISK_KEYWORDS):
                    continue
                if len(line) > 220:
                    line = line[:217] + "..."
                lines.append(
                    f"| {self.link(path, self.rel(path))} | {self.clean_cell(current_heading)} | "
                    f"{self.clean_cell(line)} |"
                )
        return "\n".join(lines) + "\n"

    def render(self) -> dict[str, str]:
        if not self.knowledge.exists():
            raise FileNotFoundError(f"missing knowledge dir: {self.knowledge}")
        known_tables = self.collect_known_tables()
        dashboards = self.collect_dashboards(known_tables)
        metrics = self.collect_metrics(known_tables)
        return {
            "field_to_metrics.md": self.build_field_to_metrics(metrics),
            "metric_to_raw_sql.md": self.build_metric_to_raw_sql(metrics),
            "table_to_dashboards.md": self.build_table_to_dashboards(dashboards, metrics),
            "join_risk_index.md": self.build_join_risk_index(),
        }

    def stale_outputs(self, outputs: dict[str, str] | None = None) -> list[str]:
        outputs = outputs or self.render()
        stale: list[str] = []
        for name in OUTPUT_NAMES:
            path = self.out_dir / name
            expected = outputs[name].encode("utf-8")
            if not path.exists() or path.read_bytes() != expected:
                stale.append(name)
        return stale

    def write(self, outputs: dict[str, str] | None = None) -> None:
        outputs = outputs or self.render()
        for name in OUTPUT_NAMES:
            self.write_text(self.out_dir / name, outputs[name])
            print(f"[OK] wrote knowledge/reverse_index/{name}")


def render_reverse_indexes(skill_root: Path) -> dict[str, str]:
    return ReverseIndexBuilder(skill_root).render()


def build_reverse_indexes(skill_root: Path, *, check: bool = False) -> int:
    builder = ReverseIndexBuilder(skill_root)
    try:
        outputs = builder.render()
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if check:
        stale = builder.stale_outputs(outputs)
        if stale:
            for name in stale:
                print(f"[STALE] knowledge/reverse_index/{name}")
            return 1
        print("[OK] reverse indexes are current")
        return 0
    builder.write(outputs)
    return 0


def main_for_skill(skill_root: Path, argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build reverse indexes for one Text2SQL skill.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check generated content without writing reverse-index Markdown files.",
    )
    args = parser.parse_args(argv)
    return build_reverse_indexes(skill_root, check=args.check)


__all__ = [
    "ReverseIndexBuilder",
    "build_reverse_indexes",
    "main_for_skill",
    "render_reverse_indexes",
]
