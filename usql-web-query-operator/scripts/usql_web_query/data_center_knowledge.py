"""Write Data Center dataset SQL into business skill knowledge bases."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from _shared.config import DATA_CENTER_DATASET_URL
from _shared.errors import UsageError

from .data_center import DataCenterDatasetSql


@dataclass(frozen=True)
class DataCenterSkillTarget:
    name: str
    root: Path
    dataset_prefix: str
    doc_filename: str
    title: str
    scope_note: str


@dataclass
class DataCenterDatasetWriteResult:
    dataset_name: str
    dataset_id: str
    raw_sql_file: str
    changed: bool
    sql_lines: int
    sql_bytes: int

    def to_json(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class DataCenterSkillSyncResult:
    skill: str
    root: str
    mode: str
    run_date: str
    datasets_seen: int = 0
    raw_sql_changed: int = 0
    index_doc_changed: bool = False
    changelog_updated: bool = False
    changelog_skipped: str | None = None
    changed_files: list[str] = field(default_factory=list)
    maintenance: list[dict[str, Any]] = field(default_factory=list)
    datasets: list[DataCenterDatasetWriteResult] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        data["datasets"] = [item.to_json() for item in self.datasets]
        return data


def sync_data_center_sql(
    target: DataCenterSkillTarget,
    dataset_sqls: list[DataCenterDatasetSql],
    *,
    write: bool,
    run_date: date,
    update_changelog: bool,
    rebuild_indexes: bool,
    check_integrity: bool,
) -> DataCenterSkillSyncResult:
    if not target.root.exists():
        raise UsageError(f"Target skill root does not exist: {target.root}")

    result = DataCenterSkillSyncResult(
        skill=target.name,
        root=str(target.root),
        mode="write" if write else "dry_run",
        run_date=run_date.isoformat(),
        datasets_seen=len(dataset_sqls),
    )

    records = _write_raw_sql_files(target, dataset_sqls, write=write, run_date=run_date)
    result.datasets.extend(records)
    result.raw_sql_changed = sum(1 for item in records if item.changed)
    result.changed_files.extend(item.raw_sql_file for item in records if item.changed)

    doc_path = target.root / "knowledge" / "dashboards" / target.doc_filename
    doc_text = _build_index_doc(target, dataset_sqls, records, run_date=run_date)
    result.index_doc_changed = _write_if_changed(doc_path, doc_text, write=write)
    if result.index_doc_changed:
        result.changed_files.append(_rel_to_root(doc_path, target.root))

    if update_changelog:
        _append_changelog(target, result, run_date=run_date, write=write)

    if write and (result.changed_files or result.changelog_updated):
        result.maintenance = run_maintenance(
            target,
            rebuild_indexes=rebuild_indexes,
            check_integrity=check_integrity,
        )
    return result


def run_maintenance(
    target: DataCenterSkillTarget,
    *,
    rebuild_indexes: bool,
    check_integrity: bool,
) -> list[dict[str, Any]]:
    commands: list[tuple[str, list[str]]] = []
    if rebuild_indexes:
        commands.append(("build_reverse_indexes", [sys.executable, "scripts/build_reverse_indexes.py"]))
    if check_integrity:
        commands.append(("check_skill_integrity", [sys.executable, "scripts/check_skill_integrity.py"]))

    results: list[dict[str, Any]] = []
    for name, command in commands:
        completed = subprocess.run(command, cwd=target.root, text=True, capture_output=True)
        item = {
            "name": name,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        results.append(item)
        if completed.returncode != 0:
            raise UsageError(f"{target.name} maintenance command failed: {name}")
    return results


def _write_raw_sql_files(
    target: DataCenterSkillTarget,
    dataset_sqls: list[DataCenterDatasetSql],
    *,
    write: bool,
    run_date: date,
) -> list[DataCenterDatasetWriteResult]:
    raw_sql_dir = target.root / "resources" / "raw_sql"
    records: list[DataCenterDatasetWriteResult] = []
    for item in dataset_sqls:
        raw_path = raw_sql_dir / _raw_sql_filename(target, item, run_date)
        text = item.execute_sql.rstrip() + "\n"
        changed = _write_if_changed(raw_path, text, write=write)
        records.append(
            DataCenterDatasetWriteResult(
                dataset_name=item.dataset.name,
                dataset_id=item.dataset.id,
                raw_sql_file=_rel_to_root(raw_path, target.root),
                changed=changed,
                sql_lines=len(item.execute_sql.splitlines()),
                sql_bytes=len(item.execute_sql.encode("utf-8")),
            )
        )
    return records


def _raw_sql_filename(target: DataCenterSkillTarget, item: DataCenterDatasetSql, run_date: date) -> str:
    stable_id = item.dataset.file_value or item.dataset.subject_id or item.dataset.id
    stable_id = re.sub(r"[^A-Za-z0-9_]+", "_", stable_id).strip("_")
    return f"data_center_{target.dataset_prefix}_{stable_id}_{run_date:%Y%m%d}.sql"


def _build_index_doc(
    target: DataCenterSkillTarget,
    dataset_sqls: list[DataCenterDatasetSql],
    records: list[DataCenterDatasetWriteResult],
    *,
    run_date: date,
) -> str:
    raw_by_id = {record.dataset_id: record for record in records}
    lines = [
        f"# {target.title}",
        "",
        "## 1. 来源与范围",
        "",
        f"- 同步日期：{run_date.isoformat()}",
        f"- 来源页面：{DATA_CENTER_DATASET_URL}",
        f"- 同步范围：{target.scope_note}",
        "- 维护方式：脚本仅保存数据中心“数据集详情”接口返回的 `executeSql` 源 SQL，不改写业务逻辑。",
        "- SQL 存放：完整源 SQL 存放在 `resources/raw_sql`；本文件只维护数据集到 raw SQL 文件的映射。",
        "",
        "## 2. 数据集清单",
        "",
        "| 序号 | 数据集名称 | 数据集 ID | fileValue | subjectId | 数据源 ID | 所属路径 | 源 SQL 文件 | 行数 |",
        "|---:|---|---|---|---|---|---|---|---:|",
    ]
    for index, item in enumerate(dataset_sqls, start=1):
        record = raw_by_id[item.dataset.id]
        raw_name = Path(record.raw_sql_file).name
        raw_link = f"[{raw_name}](../../resources/raw_sql/{raw_name})"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _md_code(item.dataset.name),
                    _md_code(item.dataset.id),
                    _md_code(item.dataset.file_value),
                    _md_code(item.dataset.subject_id),
                    _md_code(item.data_source_id),
                    _escape_cell(item.dataset.path_text),
                    raw_link,
                    str(record.sql_lines),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 3. 维护说明",
            "",
            "- 若数据中心数据集顺序、名称或 SQL 发生变化，重新运行 `sync-data-center-sql --write` 刷新本文件和对应 raw SQL。",
            "- 若需要解释字段、指标或看板口径，应在读取源 SQL 后再维护 `knowledge/tables`、`knowledge/metrics` 或专题文档；不要只凭数据集名称补口径。",
            "- 青橙与市场顾问业务知识库相互隔离：青橙数据集只写入 `qingcheng-dashboard-sql`，市场顾问数据集只写入 `sql-query-writer-for-dashboard`。",
            "",
        ]
    )
    return "\n".join(lines)


def _append_changelog(
    target: DataCenterSkillTarget,
    result: DataCenterSkillSyncResult,
    *,
    run_date: date,
    write: bool,
) -> None:
    if not write:
        result.changelog_skipped = "dry_run"
        return
    if not result.changed_files:
        result.changelog_skipped = "no_file_changes"
        return
    path = target.root / "knowledge" / "update_log" / "changelog.md"
    if not path.exists():
        result.changelog_skipped = "missing_changelog"
        return
    heading = f"## {run_date.isoformat()} 数据中心数据集源 SQL 同步"
    text = path.read_text(encoding="utf-8")
    if heading in text:
        result.changelog_skipped = "heading_exists"
        return
    entry = (
        f"\n{heading}\n\n"
        f"- 从数据中心 `{DATA_CENTER_DATASET_URL}` 同步数据集源 SQL，范围：{target.scope_note}\n"
        f"- 保存 {result.datasets_seen} 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/{target.doc_filename}`。\n"
        f"- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。\n"
    )
    path.write_text(text.rstrip() + "\n" + entry, encoding="utf-8", newline="\n")
    result.changelog_updated = True


def _write_if_changed(path: Path, text: str, *, write: bool) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    changed = current != text
    if write and changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    return changed


def _rel_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def _escape_cell(value: str) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("|", r"\|")


def _md_code(value: str) -> str:
    return f"`{_escape_cell(value)}`" if value else ""


def result_to_json(results: list[DataCenterSkillSyncResult]) -> str:
    return json.dumps([result.to_json() for result in results], ensure_ascii=False, indent=2)
