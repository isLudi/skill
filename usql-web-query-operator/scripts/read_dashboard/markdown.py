"""Markdown rendering for dashboard web profiles and index files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import format_task_ids, markdown_cell
from .constants import DASHBOARD_FILENAME_OVERRIDES
from .models import DashboardKnowledgeEntry, DashboardRecord


README_HEADER = """# Web BI 看板结构快照

本目录存放通过 `usql-web-query-operator/scripts/read_dashboard.py` 从自助 BI 页面抽取的看板结构摘要。

- 只保存页面结构、组件单元、筛选器、字段/指标、刷新任务 ID 和行数/序列计数。
- 不保存查询结果明细行，不替代 `knowledge/dashboards/*.md` 中的 SQL 业务口径。
- 当用户问题涉及“页面上有哪些筛选器/组件/字段/下载按钮/刷新任务”时，先读本目录；当问题涉及 SQL 口径、表、join、指标公式时，再读 dashboards/metrics/tables。

## 已入库快照

| 文件夹 | 看板 | 文件 | dashboard_id | 状态 |
|---|---|---|---|---|
"""

DASHBOARDS_README_SECTION_RE = re.compile(
    r"## Web BI 结构快照\n\n.*?(?=\n## |\Z)",
    re.S,
)


def dashboard_filename(record: DashboardRecord) -> str:
    if record.dashboard_id and record.dashboard_id in DASHBOARD_FILENAME_OVERRIDES:
        return DASHBOARD_FILENAME_OVERRIDES[record.dashboard_id]
    if record.dashboard_id:
        return f"{record.dashboard_id}_web_profile.md"
    normalized = re.sub(r"[^a-z0-9]+", "_", record.name.lower()).strip("_")
    return f"{normalized or 'dashboard'}_web_profile.md"


def _stringify_default_value(field: dict[str, Any]) -> str:
    for key in ("default_filter_value", "dynamics_filter_value", "filter_value"):
        value = field.get(key)
        if value not in (None, "", []):
            if isinstance(value, list):
                return ",".join(str(item) for item in value[:5])
            return str(value)
    values = field.get("pre_filter_values") or []
    if values:
        return ",".join(str(item) for item in values[:5])
    return ""


def _public_filter_rows(profile: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    public_filters = profile.get("public_filters") or {}
    for relation in public_filters.values():
        for item in relation.get("filters") or []:
            fields = item.get("fields") or item.get("filter_params") or []
            for field in fields or [{}]:
                label = item.get("unit_name") or field.get("show_name") or field.get("name") or item.get("unit_id") or ""
                field_name = field.get("show_name") or field.get("name") or ""
                field_id = field.get("field_id") or ""
                default_value = _stringify_default_value(field)
                unit_count = len(item.get("dashboard_units") or [])
                rows.append(
                    "| {label} | {field_name} | {field_id} | {default_value} | {unit_count} |".format(
                        label=markdown_cell(label),
                        field_name=markdown_cell(field_name),
                        field_id=markdown_cell(field_id),
                        default_value=markdown_cell(default_value),
                        unit_count=unit_count,
                    )
                )
    return rows


def _component_rows(profile: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    details = profile.get("unit_details") or {}
    values = profile.get("unit_values") or {}
    for component in profile.get("components") or []:
        unit_id = str(component.get("unit_id") or "")
        detail = details.get(unit_id) or {}
        value_summary = values.get(unit_id) or {}
        name = (
            detail.get("unit_name")
            or component.get("node_title")
            or component.get("component_name")
            or component.get("node_component")
            or unit_id
        )
        page_size = detail.get("page_size") if detail else component.get("page_size")
        download = detail.get("is_download") if detail else component.get("show_download_btn")
        page_bits: list[str] = []
        if page_size not in (None, ""):
            page_bits.append(f"page={page_size}")
        if download not in (None, ""):
            page_bits.append(f"download={download}")
        task_bits: list[str] = []
        task_ids = format_task_ids(value_summary.get("task_ids"))
        if task_ids:
            task_bits.append(f"task={task_ids}")
        row_count = value_summary.get("data_row_count")
        if row_count is not None:
            task_bits.append(f"rows={row_count}")
        total_rows = ((value_summary.get("page") or {}).get("totalSize"))
        if total_rows not in (None, ""):
            task_bits.append(f"total={total_rows}")
        status = value_summary.get("status") or ("filter_relation" if unit_id.startswith("public_filter_relation_") else "unprofiled")
        rows.append(
            "| {name} | {unit_id} | {unit_type} | {model} | {page_info} | {status} | {tasks} |".format(
                name=markdown_cell(name),
                unit_id=markdown_cell(unit_id),
                unit_type=markdown_cell(detail.get("unit_type") or component.get("component_type") or ""),
                model=markdown_cell(
                    (
                        f"{detail.get('model_id')} {detail.get('model_name')}".strip()
                        if detail.get("model_id") or detail.get("model_name")
                        else ""
                    )
                ),
                page_info="<br>".join(page_bits),
                status=markdown_cell(status),
                tasks="<br>".join(task_bits),
            )
        )
    return rows


def _field_list(fields: list[dict[str, Any]]) -> str:
    if not fields:
        return ""
    parts: list[str] = []
    for field in fields:
        name = field.get("show_name") or field.get("name") or field.get("field_id") or ""
        field_id = field.get("field_id")
        if field_id:
            parts.append(f"{name}（id={field_id}）")
        else:
            parts.append(str(name))
    return "、".join(part for part in parts if part)


def render_profile_markdown(profile: dict[str, Any], source_profile_path: Path) -> str:
    dashboard_name = str(profile.get("dashboard_name") or profile.get("dashboard_id") or "Dashboard")
    lines = [
        f"# {dashboard_name} Web BI 结构快照",
        "",
        "> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。",
        "> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。",
        "",
        "## 1. 来源",
        "",
        f"- 文件夹：`{profile.get('source_folder') or ''}`",
        f"- dashboard_id：`{profile.get('dashboard_id') or ''}`",
        f"- 打开入口：`{profile.get('open_url') or ''}`",
        f"- profile 时间：{profile.get('generated_at') or ''}",
        f"- 原始结构 profile：`{source_profile_path}`",
        f"- 页面渲染：{'成功' if profile.get('rendered') else '失败'}",
    ]
    if not profile.get("ok", True):
        lines.extend(
            [
                f"- 采集结果：失败",
                "",
                "## 2. 失败信息",
                "",
                f"- {profile.get('message') or 'Unknown error'}",
            ]
        )
        return "\n".join(lines) + "\n"

    refresh = profile.get("refresh_validation") or {}
    lines.extend(
        [
            "",
            "## 2. 刷新验证",
            "",
            "| 项目 | 数值 |",
            "|---|---:|",
        ]
    )
    for key in (
        "unit_count",
        "value_unit_count",
        "data_ready_unit_count",
        "analytic_unit_count",
        "analytic_data_ready_unit_count",
        "error_count",
        "all_analytic_units_ready",
    ):
        if key in refresh:
            lines.append(f"| `{key}` | {refresh.get(key)} |")

    lines.extend(["", "## 3. 全局筛选器", "", "| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |", "|---|---|---|---|---|"])
    filter_rows = _public_filter_rows(profile)
    lines.extend(filter_rows or ["|  |  |  |  |  |"])

    lines.extend(["", "## 4. 组件和单元", "", "| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |", "|---|---|---|---|---|---|---|"])
    component_rows = _component_rows(profile)
    lines.extend(component_rows or ["|  |  |  |  |  |  |  |"])

    lines.extend(["", "## 5. 分析单元字段结构", ""])
    details = profile.get("unit_details") or {}
    value_summaries = profile.get("unit_values") or {}
    components_by_unit = {str(item.get("unit_id")): item for item in profile.get("components") or []}
    emitted = 0
    for unit_id, detail in details.items():
        if str(detail.get("unit_type") or "") in {"u_text", "u_material"}:
            continue
        emitted += 1
        component = components_by_unit.get(unit_id) or {}
        title = detail.get("unit_name") or component.get("node_title") or unit_id
        value_summary = value_summaries.get(unit_id) or {}
        lines.extend(
            [
                f"### {title}",
                "",
                "- unit_id：`{unit_id}`；类型：`{unit_type}`；模型：`{model_id}` / {model_name}".format(
                    unit_id=unit_id,
                    unit_type=detail.get("unit_type") or "",
                    model_id=detail.get("model_id") or "",
                    model_name=detail.get("model_name") or "",
                ),
                "- 刷新：{status}；task_ids：`{task_ids}`；行数：{rows}；序列：{series_count} / {series_points} 点".format(
                    status=value_summary.get("status") or "unknown",
                    task_ids=format_task_ids(value_summary.get("task_ids")),
                    rows=value_summary.get("data_row_count", 0),
                    series_count=value_summary.get("series_count", 0),
                    series_points=value_summary.get("series_point_count", 0),
                ),
            ]
        )
        dimension_fields = (detail.get("dimension_fields") or []) + (detail.get("column_dimension_fields") or [])
        measure_fields = (detail.get("measure_fields") or []) + (detail.get("aide_measure_fields") or [])
        filter_fields = detail.get("filter_fields") or []
        dimension_text = _field_list(dimension_fields)
        measure_text = _field_list(measure_fields)
        filter_text = _field_list(filter_fields)
        if dimension_text:
            lines.append(f"- 维度/表头字段：{dimension_text}")
        if measure_text:
            lines.append(f"- 指标/序列字段：{measure_text}")
        if filter_text:
            lines.append(f"- 单元筛选字段：{filter_text}")
        lines.append("")
    if not emitted:
        lines.append("- 未返回可分析单元字段结构。")
        lines.append("")

    errors = profile.get("errors") or []
    if errors:
        lines.extend(["## 6. 采集异常", ""])
        for item in errors:
            lines.append(f"- `{item.get('unit_id')}`：{item.get('message')}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_profile_markdown(profile: dict[str, Any], source_profile_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_profile_markdown(profile, source_profile_path), encoding="utf-8")


def build_readme(entries: list[DashboardKnowledgeEntry]) -> str:
    lines = [README_HEADER.rstrip()]
    for entry in sorted(entries, key=lambda item: (item.folder, item.dashboard_name)):
        status = "✅ 成功" if entry.ok else f"❌ 失败：{entry.message}"
        lines.append(
            "| {folder} | {dashboard_name} | `{filename}` | `{dashboard_id}` | {status} |".format(
                folder=markdown_cell(entry.folder),
                dashboard_name=markdown_cell(entry.dashboard_name),
                filename=entry.filename,
                dashboard_id=entry.dashboard_id,
                status=markdown_cell(status),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def write_readme(entries: list[DashboardKnowledgeEntry], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_readme(entries), encoding="utf-8")


def update_dashboards_readme(readme_path: Path) -> None:
    original = readme_path.read_text(encoding="utf-8")
    replacement = """## Web BI 结构快照

当问题涉及自助 BI 页面上的筛选器、组件、字段 ID、下载按钮、刷新任务 ID 或行数/序列计数时，读取 `knowledge/dashboard_web_profiles/README.md` 及对应看板快照。该目录只记录 Web 前端结构，不替代本目录中的 SQL 业务口径。

`knowledge/dashboard_web_profiles/README.md` 由 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 统一重建，覆盖 `市场顾问数据` 和 `青橙项目部` 文件夹下当前已同步的看板清单。
"""
    updated = DASHBOARDS_README_SECTION_RE.sub(replacement, original)
    if updated == original:
        updated = original.rstrip() + "\n\n" + replacement
    readme_path.write_text(updated.rstrip() + "\n", encoding="utf-8")
