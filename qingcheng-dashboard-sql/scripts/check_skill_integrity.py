#!/usr/bin/env python3
"""Check the qingcheng-dashboard-sql skill package structure."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "agents",
    "docs",
    "examples",
    "knowledge/tables",
    "knowledge/temp_tables",
    "knowledge/dashboards",
    "knowledge/dashboard_web_profiles",
    "knowledge/metrics",
    "knowledge/joins",
    "knowledge/sql_patterns",
    "knowledge/update_log",
    "resources/raw_sql",
    "resources/raw_pdfs",
    "resources/raw_images",
    "resources/rendered_pages",
    "scripts",
]

REQUIRED_FILES = [
    "SKILL.md",
    "metadata.json",
    "docs/USAGE_PROMPTS.md",
    "knowledge/00_global_rules.md",
    "knowledge/01_table_index.md",
    "knowledge/02_query_engine_presto.md",
    "knowledge/03_range_limit_rules.md",
    "knowledge/04_qingcheng_project_profile.md",
    "knowledge/tables/_table_template.md",
    "knowledge/temp_tables/_temp_table_template.md",
    "knowledge/dashboards/_dashboard_template.md",
    "knowledge/dashboard_web_profiles/README.md",
    "knowledge/metrics/_metric_template.md",
    "knowledge/joins/common_join_keys.md",
    "knowledge/joins/table_relationships.md",
    "knowledge/sql_patterns/dashboard_query_patterns.md",
    "knowledge/sql_patterns/exploratory_query_patterns.md",
    "knowledge/sql_patterns/presto_date_partition_patterns.md",
    "knowledge/sql_patterns/qingcheng_scope_patterns.md",
    "knowledge/update_log/changelog.md",
    "scripts/check_skill_integrity.py",
    "scripts/ingest_dashboard_sql.py",
    "scripts/validate_sql_rules.py",
]

TABLE_SECTIONS = [
    "## 1. 中文名称",
    "## 2. 表用途",
    "## 3. 数据粒度",
    "## 4. 查询引擎",
    "## 5. 分区字段",
    "## 6. 强制范围限定字段",
    "## 7. 字段清单",
    "## 8. 常用过滤条件",
    "## 9. 常用 join key",
    "## 10. 常用 SQL 片段",
    "## 11. 注意事项",
]

TEMP_TABLE_SECTIONS = [
    "## 1. 临时表用途",
    "## 2. 来源和刷新方式",
    "## 3. 数据粒度",
    "## 4. 字段清单",
    "## 5. 适用看板",
    "## 6. join key",
    "## 7. 不可复用边界",
    "## 8. 待确认事项",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"[FAIL] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def check_metadata(failures: list[str]) -> None:
    metadata_path = ROOT / "metadata.json"
    try:
        metadata = json.loads(read_text(metadata_path))
    except Exception as exc:  # noqa: BLE001
        fail(f"metadata.json is not valid JSON: {exc}", failures)
        return

    if metadata.get("name") != "qingcheng-dashboard-sql":
        fail("metadata.name must be qingcheng-dashboard-sql", failures)
    if metadata.get("query_engine") != "Presto":
        fail("metadata.query_engine must be Presto", failures)
    if metadata.get("business_domain") != "青橙项目部":
        fail("metadata.business_domain must be 青橙项目部", failures)
    if metadata.get("entrypoint") != "SKILL.md":
        fail("metadata.entrypoint must be SKILL.md", failures)
    if not metadata.get("forbid_cross_domain_defaulting"):
        fail("metadata.forbid_cross_domain_defaulting must be true", failures)

    for rel in metadata.get("knowledge_dirs", []):
        if not (ROOT / rel).is_dir():
            fail(f"metadata knowledge dir missing: {rel}", failures)
    ok("metadata.json")


def check_markdown_docs(folder: str, sections: list[str], failures: list[str]) -> None:
    doc_dir = ROOT / folder
    files = sorted(p for p in doc_dir.glob("*.md") if not p.name.startswith("_"))
    if not files:
        warn(f"{folder} has no ingested markdown files yet")
        return

    for path in files:
        text = read_text(path)
        missing = [section for section in sections if section not in text]
        if missing:
            fail(f"{path.relative_to(ROOT)} missing sections: {', '.join(missing)}", failures)
        if "待人工确认" in text:
            warn(f"{path.relative_to(ROOT)} contains pending manual-confirmation items")
    ok(f"{folder} docs checked: {len(files)}")


def check_changelog_order(failures: list[str]) -> None:
    changelog_path = ROOT / "knowledge" / "update_log" / "changelog.md"
    text = read_text(changelog_path)
    heading_re = re.compile(r"^## (\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}:\d{2}))?", re.M)
    entries = list(heading_re.finditer(text))
    if not entries:
        fail("knowledge/update_log/changelog.md has no dated headings", failures)
        return

    prev_date: date | None = None
    latest_time_by_date: dict[date, time] = {}
    for match in entries:
        current_date = date.fromisoformat(match.group(1))
        current_time = time.fromisoformat(match.group(2)) if match.group(2) else None
        heading = match.group(0)

        if prev_date is not None and current_date < prev_date:
            fail(
                "knowledge/update_log/changelog.md must be chronological ascending; "
                f"out-of-order heading: {heading}",
                failures,
            )
            return

        if current_time is not None:
            latest_time = latest_time_by_date.get(current_date)
            if latest_time is not None and current_time < latest_time:
                fail(
                    "knowledge/update_log/changelog.md timed headings must be ascending within a date; "
                    f"out-of-order heading: {heading}",
                    failures,
                )
                return
            latest_time_by_date[current_date] = current_time

        prev_date = current_date

    ok("changelog chronological order")


def main() -> int:
    failures: list[str] = []

    for rel in REQUIRED_DIRS:
        if (ROOT / rel).is_dir():
            ok(rel)
        else:
            fail(f"missing dir: {rel}", failures)

    for rel in REQUIRED_FILES:
        if (ROOT / rel).is_file():
            ok(rel)
        else:
            fail(f"missing file: {rel}", failures)

    check_metadata(failures)
    check_markdown_docs("knowledge/tables", TABLE_SECTIONS, failures)
    check_markdown_docs("knowledge/temp_tables", TEMP_TABLE_SECTIONS, failures)
    check_changelog_order(failures)

    if failures:
        print(f"\nSkill integrity check failed: {len(failures)} issue(s).")
        return 1

    print("\nSkill integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
