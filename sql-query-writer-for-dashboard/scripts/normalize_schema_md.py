#!/usr/bin/env python3
"""Normalize table Markdown files and refresh the table index."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "knowledge" / "tables"
INDEX = ROOT / "knowledge" / "01_table_index.md"
CHANGELOG = ROOT / "knowledge" / "update_log" / "changelog.md"


REQUIRED_SECTIONS = [
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


@dataclass
class TableInfo:
    full_name: str
    zh_name: str
    grain: str
    partitions: list[str]
    has_hour: bool
    prefix_status: str
    field_status: str


def section(text: str, title: str) -> str:
    pattern = re.escape(title) + r"\n(.*?)(?=\n## \d+\.|\Z)"
    m = re.search(pattern, text, flags=re.S)
    return m.group(1).strip() if m else ""


def parse_table_rows(markdown_table: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in markdown_table.splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        if re.match(r"^\|\s*-+", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and cells[0] not in {"字段名", ""}:
            rows.append(cells)
    return rows


def existing_range_fields(text: str) -> list[tuple[str, str, str]]:
    fields = []
    for row in parse_table_rows(section(text, "## 6. 强制范围限定字段")):
        if len(row) >= 5 and row[0] not in {"无", "待确认"}:
            fields.append((row[0], row[1], row[4], row[2], row[3]))
    return fields


def department_fields(text: str) -> list[tuple[str, str, str]]:
    fields = []
    for row in parse_table_rows(section(text, "## 7. 字段清单")):
        if len(row) < 3:
            continue
        field_name = row[0].lower()
        is_scope_field = (
            "department_name" in field_name
            or field_name == "department"
            or field_name.startswith("dept_")
            or field_name in {"xiaozu", "xiaozu_z", "jingli"}
        )
        if is_scope_field:
            fields.append((row[0], row[1], row[2]))
    return fields


def placeholder_for(field_name: str) -> str:
    if "first" in field_name:
        return "'<一级部门名称>'"
    if "second" in field_name:
        return "'<二级部门名称>'"
    if "third" in field_name:
        return "'<三级部门名称>'"
    if field_name in {"dept_1", "department"}:
        return "'<一级/业务部门名称>'"
    if field_name == "dept_2":
        return "'<二级/区域部门名称>'"
    if field_name == "qici":
        return "'<期次>'"
    if field_name in {"qudao", "channel"}:
        return "'<渠道名称>'"
    if field_name == "grade":
        return "'<年级>'"
    if field_name in {"xiaozu", "xiaozu_z"}:
        return "'<小组/小组长>'"
    if field_name == "jingli":
        return "'<经理名称>'"
    return "'<待填写>'"


def range_table(fields: list[tuple[str, str, str]]) -> str:
    lines = ["| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |", "|---|---|---|---|---|"]
    seen: set[str] = set()
    for item in fields:
        name, typ, desc = item[:3]
        recommended = item[3] if len(item) >= 4 else placeholder_for(name)
        required = item[4] if len(item) >= 5 else "是"
        if name in seen:
            continue
        seen.add(name)
        lines.append(f"| {name} | {typ} | {recommended} | {required} | {desc} |")
    if len(lines) == 2:
        lines.append("| 无 | - | - | 否 | 未识别 department_name 字段；若后续补充需重新检查 |")
    return "\n".join(lines)


def normalize_one(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False
    for title in REQUIRED_SECTIONS:
        if title not in text:
            text += f"\n\n{title}\n\n待补充\n"
            changed = True

    fields = existing_range_fields(text) + department_fields(text)
    replacement = (
        "## 6. 强制范围限定字段\n\n"
        + range_table(fields)
        + "\n\n说明：\n"
        + "- 对所有 department_name 相关字段，标记为需要范围限定；\n"
        + "- 不知道默认值时，推荐取值写 `'<待填写>'`。"
    )
    pattern = r"## 6\. 强制范围限定字段\n.*?(?=\n## 7\. 字段清单)"
    new_text, n = re.subn(pattern, replacement + "\n\n", text, flags=re.S)
    if n and new_text != text:
        text = new_text
        changed = True

    if changed:
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return changed


def info_from_file(path: Path) -> TableInfo:
    text = path.read_text(encoding="utf-8")
    full_name = re.search(r"^#\s+(.+)$", text, flags=re.M)
    full = full_name.group(1).strip() if full_name else path.stem
    zh = section(text, "## 1. 中文名称").splitlines()[0].strip() if section(text, "## 1. 中文名称") else "待确认"
    grain = section(text, "## 3. 数据粒度").splitlines()[0].strip() if section(text, "## 3. 数据粒度") else "待确认"
    part_rows = parse_table_rows(section(text, "## 5. 分区字段"))
    partitions = [r[0] for r in part_rows if r and r[0] not in {"无", "待确认"}]
    has_hour = "hour" in partitions
    prefix = "已确认" if "库名前缀状态：已确认" in text or full.startswith("temp_table.") else "待确认" if full.startswith("unknown.") or "库名前缀状态：待确认" in text else "待确认"
    field_status = "需人工校验" if "待人工确认" in text or "低置信度" in text else "已整理"
    return TableInfo(full, zh, grain, partitions, has_hour, prefix, field_status)


def update_index() -> None:
    files = sorted(p for p in TABLE_DIR.glob("*.md") if not p.name.startswith("_") and p.name != "README.md")
    rows = [info_from_file(p) for p in files]
    lines = [
        "# 表索引",
        "",
        "> 由 `scripts/normalize_schema_md.py` 自动更新。库名前缀或字段口径为待确认时，生成生产 SQL 前必须人工确认。",
        "",
        "| 完整表名 | 中文名 | 数据粒度 | 分区字段 | 小时表 | 库名前缀状态 | 字段校验状态 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.full_name} | {row.zh_name} | {row.grain} | {', '.join(row.partitions) or '无'} | {'是' if row.has_hour else '否'} | {row.prefix_status} | {row.field_status} |"
        )
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_changelog(changed: list[Path]) -> None:
    CHANGELOG.parent.mkdir(parents=True, exist_ok=True)
    entry = [
        "",
        f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"- 规范化表结构文件：{len(changed)} 个。",
        "- 更新 `knowledge/01_table_index.md`。",
    ]
    with CHANGELOG.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(entry) + "\n")


def main() -> int:
    changed: list[Path] = []
    for path in sorted(TABLE_DIR.glob("*.md")):
        if path.name.startswith("_") or path.name == "README.md":
            continue
        if normalize_one(path):
            changed.append(path)
    update_index()
    append_changelog(changed)
    print(f"Normalized {len(changed)} table files; updated {INDEX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
