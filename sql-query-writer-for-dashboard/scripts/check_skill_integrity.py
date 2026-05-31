#!/usr/bin/env python3
"""Check the sql-query-writer-for-dashboard skill package structure."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "metadata.json",
    "docs/USAGE_PROMPTS.md",
    "knowledge/00_global_rules.md",
    "knowledge/01_table_index.md",
    "knowledge/02_query_engine_presto.md",
    "knowledge/03_range_limit_rules.md",
    "knowledge/quick_reference.md",
    "knowledge/decision_tree.md",
    "knowledge/joins/common_join_keys.md",
    "knowledge/joins/table_relationships.md",
    "knowledge/update_log/changelog.md",
    "scripts/extract_pdf_to_md.py",
    "scripts/normalize_schema_md.py",
    "scripts/ingest_dashboard_sql.py",
    "scripts/validate_sql_rules.py",
]

REQUIRED_DIRS = [
    "examples",
    "knowledge/tables",
    "knowledge/dashboards",
    "knowledge/metrics",
    "knowledge/joins",
    "knowledge/sql_patterns",
    "resources/raw_pdfs",
    "resources/raw_sql",
    "resources/raw_images",
    "resources/rendered_pages",
    "scripts",
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

    if metadata.get("name") != "sql-query-writer-for-dashboard":
        fail("metadata.name must be sql-query-writer-for-dashboard", failures)
    if metadata.get("query_engine") != "Presto":
        fail("metadata.query_engine must be Presto", failures)
    if metadata.get("entrypoint") != "SKILL.md":
        fail("metadata.entrypoint must be SKILL.md", failures)
    for rel in metadata.get("knowledge_dirs", []):
        if not (ROOT / rel).is_dir():
            fail(f"metadata knowledge dir missing: {rel}", failures)
    ok("metadata.json")


def check_table_docs(failures: list[str]) -> None:
    table_dir = ROOT / "knowledge" / "tables"
    table_files = sorted(p for p in table_dir.glob("*.md") if not p.name.startswith("_") and p.name != "README.md")
    if not table_files:
        fail("knowledge/tables has no table markdown files", failures)
        return

    for path in table_files:
        text = read_text(path)
        missing = [section for section in TABLE_SECTIONS if section not in text]
        if missing:
            fail(f"{path.relative_to(ROOT)} missing sections: {', '.join(missing)}", failures)
        if "Presto" not in text:
            warn(f"{path.relative_to(ROOT)} does not mention Presto")
        if "待人工确认" in text:
            warn(f"{path.relative_to(ROOT)} contains pending manual-confirmation items")
    ok(f"table docs checked: {len(table_files)}")


def check_index_coverage(failures: list[str]) -> None:
    index_text = read_text(ROOT / "knowledge" / "01_table_index.md")
    if "USQL状态" not in index_text and "USQL权限状态" not in index_text:
        fail("knowledge/01_table_index.md must include a USQL status column", failures)
    table_dir = ROOT / "knowledge" / "tables"
    missing = []
    for path in table_dir.glob("*.md"):
        if path.name.startswith("_") or path.name == "README.md":
            continue
        table_name = path.stem
        if table_name not in index_text:
            missing.append(table_name)
    if missing:
        fail(f"tables missing from knowledge/01_table_index.md: {', '.join(sorted(missing))}", failures)
    else:
        ok("table index coverage")


def check_channel_case_latest(failures: list[str]) -> None:
    stale_refs: list[str] = []
    knowledge_dir = ROOT / "knowledge"
    for path in knowledge_dir.rglob("*.md"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("knowledge/update_log/"):
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), start=1):
            if "market_channel_case_when_0522.sql" in line:
                stale_refs.append(f"{rel}:{line_no}")

    if stale_refs:
        fail(
            "non-changelog knowledge docs still reference market_channel_case_when_0522.sql; "
            f"use 0524 or explicitly mark historical old-version usage: {', '.join(stale_refs)}",
            failures,
        )
    else:
        ok("latest channel CASE references")


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
    check_table_docs(failures)
    check_index_coverage(failures)
    check_channel_case_latest(failures)
    check_changelog_order(failures)

    if failures:
        print(f"\nSkill integrity check failed: {len(failures)} issue(s).")
        return 1

    print("\nSkill integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
