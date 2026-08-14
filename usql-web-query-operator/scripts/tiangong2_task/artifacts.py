"""Runtime-only artifact writer for Tiangong2 task exploration."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _shared.config import TIANGONG2_TASK_RUNTIME_DIR
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from .models import ExplorationSnapshot, SourceSnapshot, TaskSnapshot, VersionSnapshot


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def validate_artifact_root(root: Path) -> None:
    if not _within(root, TIANGONG2_TASK_RUNTIME_DIR):
        raise UsageError(
            "Tiangong2 exploration artifacts must stay under the isolated runtime directory: "
            f"{TIANGONG2_TASK_RUNTIME_DIR}"
        )


def _slug(value: str, *, limit: int = 80) -> str:
    cleaned = re.sub(r"[<>:\"/\\|?*\x00-\x1f]+", "_", value.strip())
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._")
    return (cleaned or "unnamed")[:limit]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_record(source: SourceSnapshot, relative_path: Path) -> dict[str, Any]:
    return {
        "source_kind": source.source_kind,
        "extension": source.extension,
        "original_sha256": source.original_sha256,
        "redacted_sha256": source.redacted_sha256,
        "redactions": source.redactions,
        "runtime_file": relative_path.as_posix(),
    }


def _version_record(
    version: VersionSnapshot,
    relative_path: Path | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {"metadata": version.metadata}
    if version.source and relative_path:
        record["source"] = _source_record(version.source, relative_path)
    return record


def _schedule_text(task: TaskSnapshot) -> str:
    if not task.schedule:
        return task.schedule_status
    fields = [
        f"type={task.schedule.get('scheduleType')}",
        f"interval={task.schedule.get('runInterval')}",
        f"unit={task.schedule.get('timeUnit')}",
        f"next={task.schedule.get('nextRunTime')}",
    ]
    return ", ".join(fields)


def _summary_markdown(snapshot: ExplorationSnapshot) -> str:
    type_counts = Counter(task.task_type_name for task in snapshot.tasks)
    folder_counts = Counter(task.path[1] if len(task.path) > 1 else "" for task in snapshot.tasks)
    categories: dict[str, list[TaskSnapshot]] = defaultdict(list)
    finding_counts: Counter[str] = Counter()
    for task in snapshot.tasks:
        categories[task.analysis.get("primary_workflow", "未分类")].append(task)
        finding_counts.update(task.analysis.get("risk_findings", []))
    version_count = sum(len(task.versions) for task in snapshot.tasks)
    version_code_count = sum(
        1 for task in snapshot.tasks for version in task.versions if version.source is not None
    )
    matching_count = sum(task.current_matches_latest_published is True for task in snapshot.tasks)
    differing_count = sum(task.current_matches_latest_published is False for task in snapshot.tasks)
    lines = [
        "# Tiangong2 数据开发任务只读探查报告",
        "",
        f"- 生成时间：`{snapshot.generated_at}`",
        f"- 登录身份：`{snapshot.identity.get('displayName')}` (`{snapshot.identity.get('name')}`)",
        f"- 项目：`{snapshot.project.get('id')}` / `{snapshot.project.get('name')}`",
        f"- 目标文件夹：{', '.join(f'`{name}`' for name in snapshot.requested_folders)}",
        f"- 任务数：`{len(snapshot.tasks)}`；版本元数据：`{version_count}`；已抓取版本代码：`{version_code_count}`",
        "- 远端操作：仅调用白名单读取接口；未运行、保存、提交、发布、创建、修改或删除任务。",
        "- 源码落盘：仅保存脱敏副本；原始值不写入报告，原始源码只保留 SHA-256 绑定。",
        "",
        "## 范围总览",
        "",
        "### 按文件夹",
        "",
    ]
    lines.extend(f"- `{name}`：{count} 个任务" for name, count in sorted(folder_counts.items()))
    lines.extend(["", "### 按任务类型", ""])
    lines.extend(f"- `{name}`：{count}" for name, count in sorted(type_counts.items()))
    lines.extend(
        [
            "",
            "### 当前代码与最新发布版本",
            "",
            f"- 一致：`{matching_count}`",
            f"- 不一致：`{differing_count}`",
            f"- 未比较：`{len(snapshot.tasks) - matching_count - differing_count}`",
            "",
            "## 工作分类",
            "",
            "| 主工作类型 | 任务数 | 代表任务 | 主要系统 | 主要输入表 | 主要写出对象 |",
            "|---|---:|---|---|---|---|",
        ]
    )
    for category, tasks in sorted(categories.items()):
        systems = Counter(
            system for task in tasks for system in task.analysis.get("systems", [])
        )
        inputs = Counter(
            table for task in tasks for table in task.analysis.get("read_tables", [])
        )
        outputs = Counter(
            asset
            for task in tasks
            for asset in [
                *task.analysis.get("write_tables", []),
                *task.analysis.get("created_tables", []),
                *task.analysis.get("created_databases_or_schemas", []),
            ]
        )
        if any("Feishu/Lark" in task.analysis.get("systems", []) for task in tasks):
            outputs["Feishu/Lark"] += 1
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                category,
                len(tasks),
                "、".join(task.path[-1] for task in tasks[:4]),
                "、".join(item for item, _ in systems.most_common(5)) or "-",
                "、".join(item for item, _ in inputs.most_common(5)) or "-",
                "、".join(item for item, _ in outputs.most_common(5)) or "-",
            )
        )
    lines.extend(["", "### 各类任务清单", ""])
    for category, tasks in sorted(categories.items()):
        lines.append(f"### {category}")
        lines.append("")
        lines.extend(f"- `{'/'.join(task.path)}`" for task in tasks)
        lines.append("")
    lines.extend(
        [
            "## 任务明细",
            "",
                "| 路径 | 类型 | 调度原始字段 | 当前/发布 | 主工作类型 | 技术标签 | 写出或创建资产 |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for task in snapshot.tasks:
        outputs = [
            *task.analysis.get("write_tables", []),
            *task.analysis.get("created_tables", []),
            *task.analysis.get("created_databases_or_schemas", []),
        ]
        match = (
            "一致"
            if task.current_matches_latest_published is True
            else "不一致"
            if task.current_matches_latest_published is False
            else "未比较"
        )
        lines.append(
            "| `{}` | `{}` | {} | {} | {} | {} | {} |".format(
                "/".join(task.path).replace("|", "\\|"),
                task.task_type_name,
                _schedule_text(task).replace("|", "\\|"),
                match,
                task.analysis.get("primary_workflow", "未分类"),
                "、".join(task.analysis.get("technical_tags", [])) or "-",
                "、".join(outputs[:8]) or "-",
            )
        )
    lines.extend(["", "## 静态风险信号", ""])
    if finding_counts:
        lines.extend(f"- `{name}`：{count} 个任务" for name, count in sorted(finding_counts.items()))
    else:
        lines.append("- 未检测到已登记风险信号。")
    lines.extend(
        [
            "",
            "风险信号描述的是源码中存在的语句或调用，不代表本次执行过这些操作。疑似硬编码敏感值已在落盘前脱敏。",
            "",
            "## 读取接口证据",
            "",
        ]
    )
    lines.extend(f"- `{endpoint}`" for endpoint in snapshot.read_only_endpoints)
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "本报告基于当前编辑器源码、版本接口、调度配置、资源绑定和项目质量清单的静态读取。表名和工作分类来自词法证据；动态拼接 SQL、运行时分支及外部系统实际状态未执行验证。",
            "",
        ]
    )
    return "\n".join(lines)


def write_artifact_bundle(snapshot: ExplorationSnapshot, artifact_root: Path) -> Path:
    validate_artifact_root(artifact_root)
    ensure_runtime([artifact_root])
    run_dir = safe_artifact_dir(artifact_root)
    inventory_tasks: list[dict[str, Any]] = []

    for task in snapshot.tasks:
        menu_id = int(task.menu.get("id") or 0)
        task_name = str(task.metadata.get("taskName") or task.menu.get("name") or "task")
        source_relative = Path("sources") / f"{menu_id}_{_slug(task_name)}{task.current_source.extension}"
        _write_text(run_dir / source_relative, task.current_source.redacted_text)
        version_records: list[dict[str, Any]] = []
        for version in task.versions:
            version_relative = None
            if version.source:
                version_id = int(version.metadata.get("id") or 0)
                version_name = _slug(str(version.metadata.get("ver") or version_id))
                version_relative = (
                    Path("versions")
                    / f"{menu_id}_{_slug(task_name)}"
                    / f"{version_id}_{version_name}{version.source.extension}"
                )
                _write_text(run_dir / version_relative, version.source.redacted_text)
            version_records.append(_version_record(version, version_relative))
        inventory_tasks.append(
            {
                "menu": task.menu,
                "path": task.path,
                "task_type_name": task.task_type_name,
                "metadata": task.metadata,
                "current_source": _source_record(task.current_source, source_relative),
                "content_metadata": task.content_metadata,
                "schedule": task.schedule,
                "schedule_status": task.schedule_status,
                "resources": task.resources,
                "versions": version_records,
                "analysis": task.analysis,
                "current_matches_latest_published": task.current_matches_latest_published,
                "published_comparison_basis": task.published_comparison_basis,
                "warnings": task.warnings,
            }
        )

    inventory = {
        "schema_version": snapshot.schema_version,
        "generated_at": snapshot.generated_at,
        "target_url": snapshot.target_url,
        "identity": snapshot.identity,
        "login_performed": snapshot.login_performed,
        "project": snapshot.project,
        "requested_folders": snapshot.requested_folders,
        "folder_roots": snapshot.folder_roots,
        "task_type_mapping": snapshot.task_type_mapping,
        "quality_inventory": snapshot.quality_inventory,
        "tasks": inventory_tasks,
        "read_only_endpoints": snapshot.read_only_endpoints,
        "warnings": snapshot.warnings,
    }
    analysis_index = {
        "schema_version": "tiangong2-task-analysis-v1",
        "tasks": [
            {
                "path": task.path,
                "task_type_name": task.task_type_name,
                "analysis": task.analysis,
                "current_matches_latest_published": task.current_matches_latest_published,
                "published_comparison_basis": task.published_comparison_basis,
            }
            for task in snapshot.tasks
        ],
    }
    _write_json(run_dir / "inventory.json", inventory)
    _write_json(run_dir / "analysis.json", analysis_index)
    _write_text(run_dir / "summary.md", _summary_markdown(snapshot))

    artifact_files = []
    for path in sorted(item for item in run_dir.rglob("*") if item.is_file()):
        artifact_files.append(
            {
                "path": path.relative_to(run_dir).as_posix(),
                "sha256": _file_sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    manifest = {
        "schema_version": "tiangong2-task-manifest-v1",
        "generated_at": snapshot.generated_at,
        "project_id": snapshot.project.get("id"),
        "requested_folders": snapshot.requested_folders,
        "task_count": len(snapshot.tasks),
        "read_only": True,
        "remote_mutations": 0,
        "artifact_files": artifact_files,
    }
    _write_json(run_dir / "manifest.json", manifest)
    return run_dir
