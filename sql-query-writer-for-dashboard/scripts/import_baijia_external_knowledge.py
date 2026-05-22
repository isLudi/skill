#!/usr/bin/env python3
"""Import Baijia table catalog and row-permission knowledge into this skill.

Inputs default to the reviewed colleague skill exports under Downloads. The
script is intentionally deterministic so the table Markdown can be refreshed
when a newer catalog export is provided.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "knowledge" / "tables"
INDEX = ROOT / "knowledge" / "01_table_index.md"
RANGE_RULES = ROOT / "knowledge" / "03_range_limit_rules.md"
CHANGELOG = ROOT / "knowledge" / "update_log" / "changelog.md"

DEFAULT_CATALOG = Path(r"C:\Users\Ludim\Downloads\baijia-sql-query\data\table_fields_full_20260420_092405.json")
DEFAULT_PERMISSIONS = Path(r"C:\Users\Ludim\Downloads\baijia-data-map\row_permissions.json")
DEFAULT_DATA_MAP_FREQ = Path(r"C:\Users\Ludim\Downloads\baijia-data-map\core_table_frequency.json")


PREFIX_RENAMES = {
    "service_dw.dim_cstm_active_user_c_appliction_mb_df": "dw.dim_cstm_active_user_c_appliction_mb_df",
    "service_dw.dws_user_active_user_c_appliction_hf": "dw.dws_user_active_user_c_appliction_hf",
    "unknown.app_user_attribute_label_gaia_wide_df": "service_dw.app_user_attribute_label_gaia_wide_df",
}

STALE_DUPLICATES = {
    "service_dw.dm_crm_lead_cost_gmv_communication_learn_full_link_df": "bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df",
}

TABLES_TO_IMPORT = [
    # Existing tables with catalog-backed structures.
    "bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df",
    "service_dw.app_h_crm_lead_employee_workload_detail_hf",
    "service_dw.app_h_crm_lead_task_process_info_detail_hf",
    "dw.dim_cstm_active_user_c_appliction_mb_df",
    "service_dw.dm_crm_lead_stats_detail_hf",
    "service_dw.dwd_crm_assign_private_detail_hf",
    "service_dw.dws_service_user_learn_detail_hf",
    "dw.dws_user_active_user_c_appliction_hf",
    "service_dw.app_user_attribute_label_gaia_wide_df",
    # High-frequency tables missing from this skill.
    "service_dw.dm_crm_trace_lead_full_link_data_hf",
    "service_dw.dim_crm_assign_rule_lead_detail_hf",
    "service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf",
    "finance_dw.dim_finance_employee_df",
    "service_dw.dws_service_wechat_call_detail_df",
]

LEVEL_DEFAULTS = {
    "first": "'H业务线'",
    "second": "'精品班学部'",
    "third": "'学习顾问部'",
}


@dataclass
class Field:
    name: str
    typ: str
    desc: str


@dataclass
class TableRecord:
    full_name: str
    zh_name: str
    project: str
    owner: str
    field_count: int
    fields: list[Field]


def md_escape(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def sql_literal_from_recommendation(recommended: str) -> str:
    first_value = recommended.split(",")[0].strip()
    return re.sub(r"\s+\(\d+次\)$", "", first_value)


def first_line(text: str, fallback: str = "待确认") -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("|") and not line.startswith("```"):
            return line
    return fallback


def section(text: str, title: str) -> str:
    pattern = re.escape(title) + r"\n(.*?)(?=\n## \d+\.|\Z)"
    match = re.search(pattern, text, flags=re.S)
    return match.group(1).strip() if match else ""


def markdown_rows(markdown: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in markdown.splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        if re.match(r"^\|\s*-+", line):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if cells and cells[0] not in {"字段名", "完整表名", ""}:
            rows.append(cells)
    return rows


def load_catalog(path: Path) -> dict[str, TableRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    best: dict[str, dict] = {}
    for rec in raw:
        table_name = rec.get("table_name")
        if not table_name:
            continue
        previous = best.get(table_name)
        if previous is None or (rec.get("field_count") or 0) > (previous.get("field_count") or 0):
            best[table_name] = rec

    catalog: dict[str, TableRecord] = {}
    for table_name, rec in best.items():
        fields: list[Field] = []
        seen: set[str] = set()
        for field in rec.get("fields") or []:
            name = (field.get("field_name") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            fields.append(
                Field(
                    name=name,
                    typ=(field.get("field_type") or "待确认").strip() or "待确认",
                    desc=(field.get("field_desc") or "待确认").strip() or "待确认",
                )
            )
        catalog[table_name] = TableRecord(
            full_name=table_name,
            zh_name=(rec.get("table_cn_name") or "待确认").strip() or "待确认",
            project=(rec.get("project") or "待确认").strip() or "待确认",
            owner=(rec.get("owner") or "待确认").strip() or "待确认",
            field_count=rec.get("field_count") or len(fields),
            fields=fields,
        )
    return catalog


def load_permissions(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_frequency(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {item["table"]: item for item in raw.get("tables", [])}


def existing_text(table: str) -> str:
    path = TABLE_DIR / f"{table}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def old_fields(text: str) -> set[str]:
    rows = markdown_rows(section(text, "## 7. 字段清单"))
    return {row[0] for row in rows if row}


def clean_existing_purpose(text: str) -> str:
    purpose = section(text, "## 2. 表用途")
    if not purpose:
        return ""
    stop_markers = ["库名前缀状态：", "data-map 高频统计：", "字段结构来自百家平台字段目录"]
    for marker in stop_markers:
        if marker in purpose:
            purpose = purpose.split(marker, 1)[0]
    return purpose.strip()


def field_map(record: TableRecord) -> dict[str, Field]:
    return {field.name: field for field in record.fields}


def partition_fields(record: TableRecord) -> list[Field]:
    fmap = field_map(record)
    return [fmap[name] for name in ("dt", "hour") if name in fmap]


def is_department_scope_field(name: str) -> bool:
    lower = name.lower()
    return (
        "department_name" in lower
        or lower in {"department", "dept_1", "dept_2", "xiaozu", "xiaozu_z", "jingli"}
    )


def recommended_for_level(field_name: str, permission_fields: dict) -> tuple[str, str]:
    if field_name in permission_fields:
        values = permission_fields[field_name]
        sorted_values = sorted(values.items(), key=lambda item: (-item[1], item[0]))
        return ", ".join(f"'{value}' ({count}次)" for value, count in sorted_values[:3]), "row_permissions 全局历史取值"

    lower = field_name.lower()
    for level, value in LEVEL_DEFAULTS.items():
        if level in lower and ("department" in lower or lower.startswith(("course_", "performance_", "employee_"))):
            return value, f"按 row_permissions 同层级历史取值补充"
    if lower in {"department", "dept_1"}:
        return "'<部门/架构名称>'", "业务架构字段，需按需求填写"
    if lower in {"dept_2", "xiaozu", "xiaozu_z", "jingli"}:
        return "'<小组/经理/架构名称>'", "业务架构字段，需按需求填写"
    return "'<待填写>'", "待人工确认"


def permission_rows(record: TableRecord, permissions: dict) -> list[tuple[str, str, str, str, str, str]]:
    fmap = field_map(record)
    permission_fields = permissions.get("permission_fields", {})
    table_permissions = permissions.get("table_permissions", {}).get(record.full_name, [])
    rows: list[tuple[str, str, str, str, str, str]] = []
    seen: set[str] = set()

    for item in table_permissions:
        name = item.get("field")
        if not name or name in seen or name not in fmap:
            continue
        seen.add(name)
        value = item.get("value")
        count = item.get("count")
        rows.append((name, fmap[name].typ, f"'{value}'", "是", fmap[name].desc, f"row_permissions 表级历史取值，出现 {count} 次"))

    for field in record.fields:
        if field.name in seen:
            continue
        if field.name in permission_fields or is_department_scope_field(field.name):
            recommended, source = recommended_for_level(field.name, permission_fields)
            seen.add(field.name)
            rows.append((field.name, field.typ, recommended, "是", field.desc, source))

    return rows


def common_use(field: Field, partitions: set[str], scope_fields: set[str], old: set[str]) -> tuple[str, str]:
    name = field.name.lower()
    if field.name in partitions:
        return "分区过滤", "是"
    if field.name in scope_fields:
        return "权限/业务范围限定", "是"
    if field.name in old:
        return "原知识库已使用字段", "是"
    if name in {"lead_id", "user_id", "user_number", "trace_id", "order_number", "employee_id"}:
        return "主键/关联键", "是"
    if any(token in name for token in ["amount", "count", "cnt", "duration", "ratio", "price"]):
        return "指标聚合", "是"
    if any(token in name for token in ["channel", "period", "grade", "subject", "department", "employee"]):
        return "常用维度", "是"
    if any(token in name for token in ["time", "date", "timestamp"]):
        return "时间分析", "否"
    return "待按需求确认", "否"


def select_fields_for_sample(record: TableRecord, scope_names: set[str]) -> list[str]:
    preferred = [
        "dt",
        "hour",
        "lead_id",
        "trace_id",
        "user_id",
        "user_number",
        "order_number",
        "employee_email_prefix",
        "employee_email_name",
        "email_prefix",
        "first_level_department_name",
        "second_level_department_name",
        "third_level_department_name",
        "channel_name_1",
        "channel_name_2",
        "period_name",
        "income_amount",
        "refund_amount",
        "lead_count",
    ]
    names = {field.name for field in record.fields}
    selected = [name for name in preferred if name in names]
    for name in scope_names:
        if name in names and name not in selected:
            selected.append(name)
    for field in record.fields:
        if len(selected) >= 16:
            break
        if field.name not in selected:
            selected.append(field.name)
    return selected[:16]


def join_keys(record: TableRecord, existing: str) -> list[tuple[str, str]]:
    candidates = {
        "lead_id": "线索关联/去重",
        "user_id": "用户关联",
        "user_number": "用户关联",
        "trace_id": "留痕/线索链路关联",
        "order_number": "订单关联",
        "original_order_number": "原始订单关联",
        "private_sea_id": "私海记录关联",
        "employee_id": "员工关联",
        "employee_email_prefix": "员工邮箱前缀关联",
        "employee_email_name": "员工姓名关联",
        "email_prefix": "员工邮箱前缀关联",
        "clazz_number": "班级关联",
        "course_number": "课程关联",
    }
    names = {field.name for field in record.fields}
    rows = [(name, desc) for name, desc in candidates.items() if name in names]
    for row in markdown_rows(existing):
        if row and row[0] not in {name for name, _ in rows}:
            rows.append((row[0], row[1] if len(row) > 1 else "原有知识库记录"))
    return rows


def render_table_doc(record: TableRecord, permissions: dict, frequency: dict[str, dict]) -> str:
    previous = existing_text(record.full_name)
    previous_generated = "字段目录来源：`table_fields_full_20260420_092405.json`" in previous
    previous_fields = set() if previous_generated else old_fields(previous)
    zh_name = record.zh_name if record.zh_name != "待确认" else first_line(section(previous, "## 1. 中文名称"))
    grain = first_line(section(previous, "## 3. 数据粒度"), "待确认；字段目录未提供数据粒度")
    previous_purpose = clean_existing_purpose(previous)
    purpose = previous_purpose or f"{zh_name}。字段结构来自百家平台字段目录，业务口径需结合历史 SQL 或业务文档确认。"
    freq = frequency.get(record.full_name)
    partitions = partition_fields(record)
    partition_names = {field.name for field in partitions}
    scope_rows = permission_rows(record, permissions)
    scope_names = {row[0] for row in scope_rows}

    lines: list[str] = [f"# {record.full_name}", ""]
    lines += ["## 1. 中文名称", "", zh_name, ""]
    lines += ["## 2. 表用途", "", purpose, ""]
    lines += ["库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。", ""]
    if freq:
        lines += [f"data-map 高频统计：500 条成功 SQL 中出现 {freq.get('frequency')} 次，占比 {freq.get('percentage')}%。", ""]
    lines += ["## 3. 数据粒度", "", grain, ""]
    lines += ["## 4. 查询引擎", "", "Presto", ""]
    lines += ["## 5. 分区字段", "", "| 字段名 | 类型 | 含义 | 是否必填 |", "|---|---|---|---|"]
    if partitions:
        for field in partitions:
            required = "是"
            desc = field.desc if field.desc != "待确认" else ("天级分区 yyyyMMdd" if field.name == "dt" else "小时分区 HH")
            lines.append(f"| {field.name} | {md_escape(field.typ)} | {md_escape(desc)} | {required} |")
    else:
        lines.append("| 无 | - | 字段目录未识别分区字段 | 否 |")
    lines.append("")

    lines += ["## 6. 强制范围限定字段", "", "| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 | 来源 |", "|---|---|---|---|---|---|"]
    if scope_rows:
        for row in scope_rows:
            lines.append("| " + " | ".join(md_escape(cell) for cell in row) + " |")
    else:
        lines.append("| 无 | - | - | 否 | 未识别 department_name 字段；若查询涉及业务范围仍需人工限定 | 字段目录 |")
    lines += [
        "",
        "说明：",
        "- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。",
        "- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。",
        "",
    ]

    lines += ["## 7. 字段清单", "", "| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |", "|---|---|---|---|---|"]
    for field in record.fields:
        use, common = common_use(field, partition_names, scope_names, previous_fields)
        lines.append(f"| {field.name} | {md_escape(field.typ)} | {md_escape(field.desc)} | {use} | {common} |")
    lines.append("")

    lines += ["## 8. 常用过滤条件", ""]
    if "dt" in partition_names:
        lines.append("- `t.dt = 'YYYYMMDD'`")
    if "hour" in partition_names:
        lines.append("- `t.hour = 'HH'`")
    for name, _typ, recommended, _required, _desc, _source in scope_rows[:20]:
        lines.append(f"- `t.{name} = {sql_literal_from_recommendation(recommended)}`")
    if not partition_names and not scope_rows:
        lines.append("- 待根据业务场景补充过滤条件。")
    lines.append("")

    rows = join_keys(record, section(previous, "## 9. 常用 join key"))
    lines += ["## 9. 常用 join key", ""]
    if rows:
        for name, desc in rows:
            lines.append(f"- `{name}`：{desc}")
    else:
        lines.append("- 待从历史 SQL 或业务文档确认。")
    lines.append("")

    selected = select_fields_for_sample(record, scope_names)
    lines += ["## 10. 常用 SQL 片段", "", "### 简单抽样", "", "```sql"]
    lines.append("select")
    for idx, name in enumerate(selected):
        comma = "," if idx < len(selected) - 1 else ""
        lines.append(f"    t.{name}{comma}")
    lines.append(f"from {record.full_name} t")
    filters: list[str] = []
    if "dt" in partition_names:
        filters.append("t.dt = 'YYYYMMDD'")
    if "hour" in partition_names:
        filters.append("t.hour = 'HH'")
    for name, _typ, recommended, _required, _desc, _source in scope_rows[:3]:
        filters.append(f"t.{name} = {sql_literal_from_recommendation(recommended)}")
    if filters:
        lines.append("where " + filters[0])
        for item in filters[1:]:
            lines.append("  and " + item)
    lines.append("limit 20;")
    lines += ["```", ""]

    old_notes = section(previous, "## 11. 注意事项")
    lines += [
        "## 11. 注意事项",
        "",
        f"- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 {record.field_count}。",
        f"- 所属项目：{record.project}；owner：{record.owner}。",
        "- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。",
    ]
    if record.field_count >= 100:
        lines.append("- 大宽表查询禁止 `select *`，应只选择需要字段。")
    if old_notes:
        lines += ["", "### 历史备注", "", old_notes]
    return "\n".join(lines).rstrip() + "\n"


def render_index(catalog_tables: list[TableRecord], untouched_temp_files: list[Path]) -> str:
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    for record in catalog_tables:
        part_names = [field.name for field in partition_fields(record)]
        old = existing_text(record.full_name)
        grain = first_line(section(old, "## 3. 数据粒度"), "待确认")
        rows.append(
            (
                record.full_name,
                record.zh_name,
                grain,
                ", ".join(part_names) or "无",
                "是" if "hour" in part_names else "否",
                "已确认",
                "字段目录已补全，口径需人工校验",
            )
        )
    for path in untouched_temp_files:
        text = path.read_text(encoding="utf-8")
        name = re.search(r"^#\s+(.+)$", text, flags=re.M)
        full = name.group(1).strip() if name else path.stem
        zh = first_line(section(text, "## 1. 中文名称"))
        grain = first_line(section(text, "## 3. 数据粒度"))
        part_rows = markdown_rows(section(text, "## 5. 分区字段"))
        parts = [row[0] for row in part_rows if row and row[0] not in {"无", "待确认"}]
        rows.append((full, zh, grain, ", ".join(parts) or "无", "是" if "hour" in parts else "否", "已确认" if full.startswith("temp_table.") else "待确认", "保留原整理"))

    lines = [
        "# 表索引",
        "",
        "> 由 `scripts/import_baijia_external_knowledge.py` 根据百家字段目录和既有临时表文档更新。库名前缀或字段口径为待确认时，生成生产 SQL 前必须人工确认。",
        "",
        "| 完整表名 | 中文名 | 数据粒度 | 分区字段 | 小时表 | 库名前缀状态 | 字段校验状态 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda item: item[0]):
        lines.append("| " + " | ".join(md_escape(cell) for cell in row) + " |")
    return "\n".join(lines) + "\n"


def render_range_rules(permissions: dict) -> str:
    permission_fields = permissions.get("permission_fields", {})
    table_permissions = permissions.get("table_permissions", {})
    lines = [
        "# 范围限定规则",
        "",
        "## department_name 字段",
        "",
        "字段名包含 `department_name`，或业务语义为部门、业务线、学部、小组、架构时，必须加过滤条件。",
        "",
        "## 历史真实取值",
        "",
        "> 来源：`baijia-data-map/row_permissions.json`，由百家平台历史 SQL 提取。取值是生成 SQL 的默认参考，不代表所有场景都可省略用户确认。",
        "",
        "| 字段名 | 历史取值 | 使用建议 |",
        "|---|---|---|",
    ]
    for field, values in sorted(permission_fields.items()):
        sorted_values = sorted(values.items(), key=lambda item: (-item[1], item[0]))
        value_text = ", ".join(f"`'{value}'` ({count}次)" for value, count in sorted_values)
        lines.append(f"| {field} | {value_text} | 用户未明确时优先用占位符；探索验证可参考最高频取值 |")

    lines += [
        "",
        "## 表级权限切分",
        "",
        "| 表名 | 字段 | 历史取值 | 出现次数 |",
        "|---|---|---|---|",
    ]
    for table, items in sorted(table_permissions.items()):
        for item in sorted(items, key=lambda x: (-x.get("count", 0), x.get("field", ""))):
            lines.append(f"| {table} | {item.get('field')} | `'{item.get('value')}'` | {item.get('count')} |")

    lines += [
        "",
        "## 必须重点检查的字段",
        "",
        "| 字段名 | 默认占位符 | 说明 |",
        "|---|---|---|",
    ]
    important = [
        ("assign_employee_first_level_department_name", "'<一级部门名称>'", "分配顾问一级部门"),
        ("assign_employee_second_level_department_name", "'<二级部门名称>'", "分配顾问二级部门"),
        ("assign_employee_third_level_department_name", "'<三级部门名称>'", "分配顾问三级部门"),
        ("section_assign_employee_first_level_department_name", "'<一级部门名称>'", "截面分配顾问一级部门"),
        ("section_assign_employee_second_level_department_name", "'<二级部门名称>'", "截面分配顾问二级部门"),
        ("section_assign_employee_third_level_department_name", "'<三级部门名称>'", "截面分配顾问三级部门"),
        ("performance_first_level_department_name", "'<一级部门名称>'", "业绩归属一级部门"),
        ("performance_second_level_department_name", "'<二级部门名称>'", "业绩归属二级部门"),
        ("performance_third_level_department_name", "'<三级部门名称>'", "业绩归属三级部门"),
        ("employee_first_level_department_name", "'<一级部门名称>'", "员工一级部门"),
        ("employee_second_level_department_name", "'<二级部门名称>'", "员工二级部门"),
        ("course_first_level_department_name", "'<一级部门名称>'", "课程一级部门"),
        ("course_second_level_department_name", "'<二级部门名称>'", "课程二级部门"),
        ("goods_first_level_department_name", "'<一级部门名称>'", "商品一级部门"),
        ("mapping_first_level_department_name", "'<一级部门名称>'", "映射一级部门"),
        ("mapping_second_level_department_name", "'<二级部门名称>'", "映射二级部门"),
        ("period_mapping_first_level_department_name", "'<一级部门名称>'", "期次映射一级部门"),
        ("period_mapping_second_level_department_name", "'<二级部门名称>'", "期次映射二级部门"),
        ("virtual_first_department_name", "'<一级部门名称>'", "虚拟一级部门"),
        ("virtual_second_department_name", "'<二级部门名称>'", "虚拟二级部门"),
        ("virtual_third_department_name", "'<三级部门名称>'", "虚拟三级部门"),
        ("virtual_fourth_department_name", "'<四级部门名称>'", "虚拟四级部门"),
        ("virtual_fifth_department_name", "'<五级部门名称>'", "虚拟五级部门/团队"),
        ("first_department_name", "'<一级部门名称>'", "一级部门"),
        ("second_department_name", "'<二级部门名称>'", "二级部门"),
        ("third_department_name", "'<三级部门名称>'", "三级部门"),
        ("first_level_department_name", "'<一级部门名称>'", "一级部门"),
        ("second_level_department_name", "'<二级部门名称>'", "二级部门"),
        ("third_level_department_name", "'<三级部门名称>'", "三级部门"),
    ]
    for row in important:
        lines.append("| " + " | ".join(row) + " |")

    lines += [
        "",
        "## 输出要求",
        "",
        "如果用户没有提供部门取值，SQL 中使用占位符，并在解释里明确“需要替换后执行”。",
    ]
    return "\n".join(lines) + "\n"


def apply_prefix_fixes() -> list[str]:
    notes: list[str] = []
    for old, new in PREFIX_RENAMES.items():
        old_path = TABLE_DIR / f"{old}.md"
        new_path = TABLE_DIR / f"{new}.md"
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
            notes.append(f"重命名表文档 `{old}` -> `{new}`")
    for stale, canonical in STALE_DUPLICATES.items():
        stale_path = TABLE_DIR / f"{stale}.md"
        canonical_path = TABLE_DIR / f"{canonical}.md"
        if stale_path.exists() and canonical_path.exists():
            stale_path.unlink()
            notes.append(f"移除重复且字段目录未确认的表文档 `{stale}`，保留 `{canonical}`")
    return notes


def append_changelog(imported: list[str], notes: list[str]) -> None:
    CHANGELOG.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "",
        f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 百家字段目录与权限整合",
        "",
        f"- 从 `table_fields_full_20260420_092405.json` 补全/新增表文档：{len(imported)} 张。",
        "- 从 `row_permissions.json` 更新真实历史权限切分字段和值。",
        "- 更新 `knowledge/01_table_index.md` 与 `knowledge/03_range_limit_rules.md`。",
    ]
    for note in notes:
        lines.append(f"- {note}。")
    CHANGELOG.open("a", encoding="utf-8").write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Baijia external table catalog and row permissions.")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--permissions", type=Path, default=DEFAULT_PERMISSIONS)
    parser.add_argument("--frequency", type=Path, default=DEFAULT_DATA_MAP_FREQ)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    permissions = load_permissions(args.permissions)
    frequency = load_frequency(args.frequency)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    notes = apply_prefix_fixes()
    imported_records: list[TableRecord] = []
    missing: list[str] = []
    for table in TABLES_TO_IMPORT:
        record = catalog.get(table)
        if not record:
            missing.append(table)
            continue
        imported_records.append(record)
        (TABLE_DIR / f"{table}.md").write_text(render_table_doc(record, permissions, frequency), encoding="utf-8")

    untouched_temp = sorted(
        p
        for p in TABLE_DIR.glob("temp_table.*.md")
        if p.name not in {f"{record.full_name}.md" for record in imported_records}
    )
    INDEX.write_text(render_index(imported_records, untouched_temp), encoding="utf-8")
    RANGE_RULES.write_text(render_range_rules(permissions), encoding="utf-8")
    append_changelog([record.full_name for record in imported_records], notes)

    print(f"Imported {len(imported_records)} table docs.")
    if notes:
        print("Prefix fixes:")
        for note in notes:
            print(f"- {note}")
    if missing:
        print("Missing catalog records:")
        for table in missing:
            print(f"- {table}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
