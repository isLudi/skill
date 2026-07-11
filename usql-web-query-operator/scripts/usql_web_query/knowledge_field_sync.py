"""Synchronize Data Map table fields into business SQL skill docs."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from _shared.errors import UsageError

from .data_map import DataMapColumn, iter_cached_columns


SUPPLEMENT_TITLE = "\u6570\u636e\u5730\u56fe\u5b57\u6bb5\u8865\u5145"
SUPPLEMENT_NOTE = (
    "\u6765\u6e90\uff1a\u5929\u5de52\u6570\u636e\u5730\u56fe\u5b57\u6bb5\u4fe1\u606f\u3002"
    "\u8be5\u8865\u5145\u6bb5\u53ea\u8865\u9f50\u5e73\u53f0\u5df2\u767b\u8bb0\u5b57\u6bb5\u3001"
    "\u7c7b\u578b\u548c\u5b57\u6bb5\u8bf4\u660e\uff1b\u5177\u4f53\u4e1a\u52a1\u53e3\u5f84"
    "\u4ecd\u4ee5\u672c Skill \u5df2\u6c89\u6dc0\u7684 SQL \u548c\u6307\u6807\u89c4\u5219\u4e3a\u51c6\u3002"
)
MARKET_USAGE = "\u6570\u636e\u5730\u56fe\u8865\u5145"
COMMON_NO = "\u5426"
QINGCHENG_REMARK = "\u6570\u636e\u5730\u56fe\u8865\u5145\uff0c\u4e1a\u52a1\u53e3\u5f84\u9700\u7ed3\u5408\u9752\u6a59 SQL \u4f7f\u7528\u573a\u666f\u786e\u8ba4"

FIELD_HEADER = "\u5b57\u6bb5\u540d"
TYPE_HEADER = "\u7c7b\u578b"
DESC_HEADER = "\u5b57\u6bb5\u8bf4\u660e"
CN_HEADER = "\u4e2d\u6587\u542b\u4e49"
USAGE_HEADER = "\u5e38\u89c1\u7528\u9014"
COMMON_HEADER = "\u662f\u5426\u5e38\u7528"
REMARK_HEADER = "\u5907\u6ce8"

PLACEHOLDER_TOKENS = {
    "\u5f85\u786e\u8ba4",
    "\u5f85\u4eba\u5de5\u786e\u8ba4",
    "\u5f85\u8865\u5145",
    "\u672a\u77e5",
    "unknown",
    "tbd",
    "todo",
}


@dataclass(frozen=True)
class SkillTarget:
    name: str
    root: Path
    row_style: str


@dataclass
class TableDocSyncResult:
    skill: str
    table: str
    file: str
    found_in_datamap: bool = True
    changed: bool = False
    missing_doc: bool = False
    removed_same_day_sections: int = 0
    type_updates: int = 0
    description_updates: int = 0
    added_fields: int = 0
    missing_fields_after: int = 0
    placeholder_types_after: int = 0
    placeholder_descriptions_after: int = 0
    error: str | None = None

    def to_json(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class SkillSyncResult:
    skill: str
    root: str
    docs_checked: int = 0
    changed_files: int = 0
    type_updates: int = 0
    description_updates: int = 0
    added_fields: int = 0
    missing_fields_after: int = 0
    placeholder_types_after: int = 0
    placeholder_descriptions_after: int = 0
    changelog_updated: bool = False
    changelog_skipped: str | None = None
    maintenance: list[dict[str, Any]] = field(default_factory=list)
    tables: list[TableDocSyncResult] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        data["tables"] = [item.to_json() for item in self.tables]
        return data


def load_catalog(cache_file: Path) -> dict[str, Any]:
    if not cache_file.exists():
        return {}
    return json.loads(cache_file.read_text(encoding="utf-8"))


def save_catalog(cache_file: Path, catalog: dict[str, Any]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def discover_tables(targets: list[SkillTarget], requested_tables: list[str] | None) -> list[str]:
    if requested_tables:
        return sorted(set(requested_tables))
    tables: set[str] = set()
    for target in targets:
        for path in _table_docs_dir(target).glob("*.md"):
            if _is_physical_table_doc(path):
                tables.add(path.stem)
    return sorted(tables)


def sync_skill_target(
    target: SkillTarget,
    catalog: dict[str, Any],
    *,
    requested_tables: list[str] | None,
    write: bool,
    run_date: date,
) -> SkillSyncResult:
    if not target.root.exists():
        raise UsageError(f"Target skill root does not exist: {target.root}")
    result = SkillSyncResult(skill=target.name, root=str(target.root))
    docs = _target_docs(target, requested_tables)
    for table_name, path in docs.items():
        table_result = _sync_table_doc(target, table_name, path, catalog.get(table_name), write=write, run_date=run_date)
        result.tables.append(table_result)
        if table_result.missing_doc or not table_result.found_in_datamap:
            continue
        result.docs_checked += 1
        result.changed_files += int(table_result.changed)
        result.type_updates += table_result.type_updates
        result.description_updates += table_result.description_updates
        result.added_fields += table_result.added_fields
        result.missing_fields_after += table_result.missing_fields_after
        result.placeholder_types_after += table_result.placeholder_types_after
        result.placeholder_descriptions_after += table_result.placeholder_descriptions_after
    return result


def append_changelog(target: SkillTarget, result: SkillSyncResult, *, run_date: date, write: bool) -> None:
    if not write:
        result.changelog_skipped = "dry_run"
        return
    if result.type_updates == 0 and result.description_updates == 0 and result.added_fields == 0:
        result.changelog_skipped = "no_field_changes"
        return
    path = target.root / "knowledge" / "update_log" / "changelog.md"
    if not path.exists():
        result.changelog_skipped = "missing_changelog"
        return
    heading = f"## {run_date.isoformat()} {SUPPLEMENT_TITLE}"
    text = path.read_text(encoding="utf-8")
    if heading in text:
        result.changelog_skipped = "heading_exists"
        return
    scope_note = (
        "\u672c\u6b21\u7ef4\u62a4\u4e25\u683c\u9650\u5b9a\u5728 `qingcheng-dashboard-sql` \u5185\uff0c\u672a\u540c\u6b65\u5230\u5e02\u573a\u987e\u95ee Skill\uff1b"
        if target.name == "qingcheng"
        else ""
    )
    entry = (
        f"\n{heading}\n\n"
        f"- \u4f7f\u7528\u6570\u636e\u5730\u56fe `tableV2/searchTableList`\u3001`normalColumns`\u3001`partitionColumns` \u548c `getDdl` \u63a5\u53e3\u5237\u65b0\u7269\u7406\u8868\u5b57\u6bb5\u4fe1\u606f\u3002\n"
        f"- \u8986\u76d6 `knowledge/tables` \u4e2d {result.docs_checked} \u5f20\u7269\u7406\u8868\u6587\u6863\uff1b\u8ffd\u52a0 {result.added_fields} \u4e2a\u6570\u636e\u5730\u56fe\u5b57\u6bb5\uff0c\u56de\u586b\u7c7b\u578b {result.type_updates} \u5904\u3001\u5b57\u6bb5\u8bf4\u660e {result.description_updates} \u5904\u3002\n"
        f"- \u590d\u626b\u7ed3\u679c\u4e3a\u5b57\u6bb5\u7f3a\u53e3 {result.missing_fields_after}\u3001\u7c7b\u578b\u5360\u4f4d {result.placeholder_types_after}\u3001\u8bf4\u660e\u5360\u4f4d {result.placeholder_descriptions_after}\u3002\n"
        f"- {scope_note}\u672a\u8986\u76d6 `temp_table.*` \u4e34\u65f6\u8868\u6587\u6863\uff1b\u4e34\u65f6\u8868\u5b57\u6bb5\u4ecd\u4ee5\u672c\u5730 Excel\u3001SQL \u4f7f\u7528\u573a\u666f\u548c\u4eba\u5de5\u7ef4\u62a4\u89c4\u5219\u4e3a\u51c6\u3002\n"
    )
    path.write_text(text.rstrip() + "\n" + entry, encoding="utf-8", newline="\n")
    result.changelog_updated = True


def run_maintenance(
    targets: list[SkillTarget],
    *,
    rebuild_indexes: bool,
    build_catalog: bool,
    check_integrity: bool,
    validate_stack: bool,
    enabled: bool,
) -> list[dict[str, Any]]:
    if not enabled:
        return []
    skills_root = Path(__file__).resolve().parents[3]
    commands: list[tuple[str, list[str], Path]] = []
    if rebuild_indexes:
        commands.extend(
            (
                f"build_reverse_indexes:{target.name}",
                [sys.executable, "scripts/build_reverse_indexes.py"],
                target.root,
            )
            for target in targets
        )
    if build_catalog:
        commands.append(
            (
                "build_text2sql_catalog",
                [sys.executable, "scripts/build_text2sql_catalog.py"],
                skills_root,
            )
        )
    if check_integrity:
        commands.extend(
            (
                f"check_skill_integrity:{target.name}",
                [sys.executable, "scripts/check_skill_integrity.py"],
                target.root,
            )
            for target in targets
        )
    if validate_stack:
        commands.append(
            (
                "validate_text2sql_stack",
                [sys.executable, "scripts/validate_text2sql_stack.py"],
                skills_root,
            )
        )
    results: list[dict[str, Any]] = []
    for name, command, cwd in commands:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        )
        item = {
            "name": name,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        results.append(item)
        if completed.returncode != 0:
            raise UsageError(f"Data Map maintenance command failed: {name}")
    return results


def _target_docs(target: SkillTarget, requested_tables: list[str] | None) -> dict[str, Path | None]:
    docs_dir = _table_docs_dir(target)
    if requested_tables:
        return {table: (docs_dir / f"{table}.md") if (docs_dir / f"{table}.md").exists() else None for table in sorted(set(requested_tables))}
    return {path.stem: path for path in sorted(docs_dir.glob("*.md")) if _is_physical_table_doc(path)}


def _sync_table_doc(
    target: SkillTarget,
    table_name: str,
    path: Path | None,
    table_info: dict[str, Any] | None,
    *,
    write: bool,
    run_date: date,
) -> TableDocSyncResult:
    result = TableDocSyncResult(skill=target.name, table=table_name, file=str(path or ""))
    if path is None:
        result.missing_doc = True
        result.error = "table_doc_missing"
        return result
    if not table_info or not table_info.get("found"):
        result.found_in_datamap = False
        result.error = "table_not_found_in_datamap"
        return result

    columns = iter_cached_columns(table_info)
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()
    lines, result.removed_same_day_sections = _remove_same_day_supplements(lines, run_date)
    lines, existing_fields, type_updates, desc_updates = _update_existing_rows(lines, columns)
    result.type_updates = type_updates
    result.description_updates = desc_updates

    missing_columns = [column for column in columns if column.name not in existing_fields]
    result.added_fields = len(missing_columns)
    if missing_columns:
        insertion_index = _find_insert_index(lines)
        before = lines[:insertion_index]
        after = lines[insertion_index:]
        while before and before[-1] == "":
            before.pop()
        supplement = _build_supplement(target.row_style, _next_section_number(lines), missing_columns, run_date)
        lines = [*before, "", *supplement, "", *after]

    coverage = _coverage_after(lines, columns)
    result.missing_fields_after = coverage["missing_fields"]
    result.placeholder_types_after = coverage["placeholder_types"]
    result.placeholder_descriptions_after = coverage["placeholder_descriptions"]

    new_text = "\n".join(lines).rstrip() + "\n"
    result.changed = new_text != original
    if not result.changed:
        result.removed_same_day_sections = 0
        result.type_updates = 0
        result.description_updates = 0
        result.added_fields = 0
    if write and result.changed:
        path.write_text(new_text, encoding="utf-8", newline="\n")
    return result


def _table_docs_dir(target: SkillTarget) -> Path:
    return target.root / "knowledge" / "tables"


def _is_physical_table_doc(path: Path) -> bool:
    if path.suffix != ".md" or path.name.startswith("_") or path.stem.startswith("temp_table."):
        return False
    return path.stem.lower() not in {"readme", "index"}


def _split_markdown_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    return [part.strip() for part in re.split(r"(?<!\\)\|", stripped.strip("|"))]


def _clean_field(cell: str) -> str:
    return cell.strip().strip("`").strip()


def _make_row(parts: list[str]) -> str:
    return "| " + " | ".join(parts) + " |"


def _escape_cell(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "").replace("\r", " ").replace("\n", " ")).strip()
    return text.replace("|", r"\|")


def _is_type_placeholder(cell: str) -> bool:
    text = _clean_field(cell)
    low = text.lower()
    return not text or "?" in text or any(token in low for token in PLACEHOLDER_TOKENS)


def _is_description_placeholder(cell: str) -> bool:
    text = _clean_field(cell)
    low = text.lower()
    return not text or "???" in text or low in PLACEHOLDER_TOKENS


def _remove_same_day_supplements(lines: list[str], run_date: date) -> tuple[list[str], int]:
    title_marker = f"{SUPPLEMENT_TITLE}\uff08{run_date.isoformat()}\uff09"
    output: list[str] = []
    removed = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("### ") and title_marker in line:
            removed += 1
            index += 1
            while index < len(lines) and not lines[index].startswith("### ") and not lines[index].startswith("## "):
                index += 1
            continue
        output.append(line)
        index += 1
    return output, removed


def _update_existing_rows(lines: list[str], columns: list[DataMapColumn]) -> tuple[list[str], set[str], int, int]:
    column_map = {column.name: column for column in columns}
    existing_fields: set[str] = set()
    output: list[str] = []
    type_updates = 0
    description_updates = 0
    for line in lines:
        parts = _split_markdown_row(line)
        if not parts or len(parts) < 3:
            output.append(line)
            continue
        field = _clean_field(parts[0])
        if not field or field in {FIELD_HEADER, "---"} or field.startswith("-"):
            output.append(line)
            continue
        column = column_map.get(field)
        if not column:
            output.append(line)
            continue
        existing_fields.add(field)
        if column.type and _is_type_placeholder(parts[1]):
            parts[1] = _escape_cell(column.type)
            type_updates += 1
        if column.description and _is_description_placeholder(parts[2]):
            parts[2] = _escape_cell(column.description)
            description_updates += 1
        output.append(_make_row(parts))
    return output, existing_fields, type_updates, description_updates


def _build_supplement(row_style: str, section_number: int, columns: list[DataMapColumn], run_date: date) -> list[str]:
    title = f"### 7.{section_number} {SUPPLEMENT_TITLE}\uff08{run_date.isoformat()}\uff09"
    lines = [title, "", f"> {SUPPLEMENT_NOTE}", ""]
    if row_style == "qingcheng":
        lines.extend([f"| {FIELD_HEADER} | {TYPE_HEADER} | {CN_HEADER} | {REMARK_HEADER} |", "|---|---|---|---|"])
        for column in columns:
            lines.append(
                f"| `{_escape_cell(column.name)}` | {_escape_cell(column.type)} | {_escape_cell(column.description)} | {QINGCHENG_REMARK} |"
            )
    else:
        lines.extend(
            [
                f"| {FIELD_HEADER} | {TYPE_HEADER} | {DESC_HEADER} | {USAGE_HEADER} | {COMMON_HEADER} |",
                "|---|---|---|---|---|",
            ]
        )
        for column in columns:
            lines.append(
                f"| {_escape_cell(column.name)} | {_escape_cell(column.type)} | {_escape_cell(column.description)} | {MARKET_USAGE} | {COMMON_NO} |"
            )
    return lines


def _next_section_number(lines: list[str]) -> int:
    numbers: list[int] = []
    in_section = False
    for line in lines:
        if line.startswith("## 7."):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            match = re.match(r"^###\s+7\.(\d+)\b", line)
            if match:
                numbers.append(int(match.group(1)))
    return max(numbers, default=0) + 1


def _find_insert_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        if line.startswith("## 8."):
            return index
    return len(lines)


def _coverage_after(lines: list[str], columns: list[DataMapColumn]) -> dict[str, int]:
    expected = {column.name for column in columns}
    found: set[str] = set()
    placeholder_types = 0
    placeholder_descriptions = 0
    for line in lines:
        parts = _split_markdown_row(line)
        if not parts or len(parts) < 3:
            continue
        field = _clean_field(parts[0])
        if field not in expected:
            continue
        found.add(field)
        placeholder_types += int(_is_type_placeholder(parts[1]))
        placeholder_descriptions += int(_is_description_placeholder(parts[2]))
    return {
        "missing_fields": len(expected - found),
        "placeholder_types": placeholder_types,
        "placeholder_descriptions": placeholder_descriptions,
    }
