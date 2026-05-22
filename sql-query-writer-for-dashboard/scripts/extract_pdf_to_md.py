#!/usr/bin/env python3
"""Extract table-schema PDFs into Markdown knowledge files.

The script is intentionally conservative. If fields cannot be extracted with
high confidence, it renders pages for manual review and marks content as
"待人工确认" rather than guessing.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable


try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - optional dependency
    fitz = None

try:
    import pdfplumber
except Exception:  # pragma: no cover - optional dependency
    pdfplumber = None


ROOT = Path(__file__).resolve().parents[1]
RAW_PDFS = ROOT / "resources" / "raw_pdfs"
RENDERED = ROOT / "resources" / "rendered_pages"
TABLE_DIR = ROOT / "knowledge" / "tables"
REPORT = ROOT / "resources" / "pdf_extract_report.md"


@dataclass
class Field:
    name: str
    type: str = "待人工确认"
    desc: str = "待人工确认"
    use: str = "待人工确认"
    common: str = "否"


@dataclass
class TableSeed:
    raw_name: str
    zh_name: str
    database: str
    prefix_status: str
    purpose: str
    grain: str
    partitions: list[Field]
    fields: list[Field] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.database}.{self.raw_name}"

    @property
    def filename(self) -> str:
        return f"{self.full_name}.md"


DEPARTMENT_PLACEHOLDERS = [
    ("first", "'<一级部门名称>'"),
    ("second", "'<二级部门名称>'"),
    ("third", "'<三级部门名称>'"),
]


SEEDS: list[TableSeed] = [
    TableSeed(
        raw_name="app_user_attribute_label_gaia_wide_df",
        zh_name="盖亚系统用户标签数据宽表",
        database="unknown",
        prefix_status="待确认：PDF 未提供库名前缀",
        purpose="用户标签宽表，用于查询用户标签、画像、学习意向等信息。",
        grain="用户-标签粒度，待确认",
        partitions=[Field("dt", "string", "天级别分区 yyyyMMdd", "分区过滤", "是")],
        fields=[
            Field("user_number", "string", "用户ID", "用户关联", "是"),
            Field("type", "string", "标签类型 key为枚举值，value不限", "标签分类", "否"),
            Field("resident", "string", "走读/住校", "用户画像", "否"),
            Field("tutoring", "string", "补习情况", "用户画像", "否"),
            Field("learning_attitude", "string", "学习态度", "用户画像", "否"),
            Field("subject_selection", "string", "学科选择", "用户画像", "否"),
            Field("learning_level", "string", "学习水平", "用户画像", "否"),
            Field("age", "string", "年龄", "用户画像", "否"),
            Field("education", "string", "学历", "用户画像", "否"),
            Field("admission", "string", "录取情况", "用户画像", "否"),
        ],
        notes=["PDF 第 1-4 页为图片型字段表，已人工录入部分清晰字段；完整字段需复核。"],
    ),
    TableSeed(
        raw_name="dwd_crm_assign_private_detail_hf",
        zh_name="crm分配私海记录表",
        database="service_dw",
        prefix_status="已确认：来自用户指定示例 SQL",
        purpose="记录 CRM 线索分配到私海后的阶段、顾问、部门和跟进状态。",
        grain="用户/线索-顾问-小时粒度，待确认",
        partitions=[
            Field("dt", "string", "天级别分区 yyyyMMdd", "分区过滤", "是"),
            Field("hour", "string", "小时级分区 HH", "分区过滤", "是"),
        ],
        fields=[
            Field("private_sea_id", "bigint", "主键id", "明细唯一标识", "是"),
            Field("user_number", "bigint", "用户id", "用户关联/去重", "是"),
            Field("employee_id", "int", "顾问id", "员工维度", "是"),
            Field("team_id", "bigint", "团队id", "团队维度", "否"),
            Field("stage", "int", "线索状态，PDF 描述截断", "阶段分析", "否"),
            Field("stage_name", "string", "线索状态名称，PDF 描述截断", "阶段分析", "否"),
            Field("lead_id", "bigint", "线索id", "线索关联", "是"),
            Field("sale_flow_snapshot_id", "bigint", "销售流程快照", "销售流程", "否"),
            Field("sale_flow_stage", "bigint", "销售阶段id", "阶段分析", "是"),
            Field("sale_flow_stage_sequence", "int", "销售阶段顺序", "阶段排序/最新阶段", "是"),
            Field("assign_time", "string", "线索分配时间", "时间分析", "是"),
            Field("fall_sea_time", "string", "线索掉海时间", "流转分析", "否"),
            Field("private_sea_create_time", "string", "创建时间", "时间分析", "否"),
            Field("private_sea_update_time", "string", "更新时间", "最新记录排序", "是"),
            Field("close_time", "string", "私海关闭时间", "状态分析", "否"),
            Field("close_reason", "bigint", "私海关闭原因", "状态分析", "否"),
            Field("close_reason_desc", "string", "私海关闭原因描述", "状态分析", "否"),
            Field("assign_employee_first_level_department_name", "string", "顾问最新部门信息，1级name", "范围限定", "是"),
            Field("assign_employee_second_level_department_name", "string", "顾问最新部门信息，2级name", "范围限定", "是"),
            Field("assign_employee_third_level_department_name", "string", "顾问最新部门信息，3级name", "范围限定", "是"),
            Field("intention_level_desc", "string", "顾问填写的意向度", "意向分析", "否"),
        ],
        notes=["PDF 第 4-5 页可读字段已录入，页面底部截断字段需人工复核。"],
    ),
    TableSeed(
        raw_name="dm_crm_lead_stats_detail_hf",
        zh_name="线索统计公共明细层",
        database="service_dw",
        prefix_status="待确认：暂按 CRM 常见 service_dw 前缀记录",
        purpose="线索统计公共明细，包含线索状态、来源渠道、部门映射、截面分配和成本等信息。",
        grain="线索-小时粒度，待确认",
        partitions=[
            Field("dt", "string", "天级分区", "分区过滤", "是"),
            Field("hour", "string", "小时分区", "分区过滤", "是"),
        ],
        fields=[
            Field("lead_id", "bigint", "线索id", "线索关联/去重", "是"),
            Field("lead_purchase_intention_id", "bigint", "线索购买意向", "意向分析", "否"),
            Field("lead_purchase_intention_name", "string", "线索意向name", "意向分析", "否"),
            Field("lead_create_time", "string", "线索创建时间", "时间分析", "是"),
            Field("lead_update_time", "string", "线索更新时间", "时间分析", "否"),
            Field("lead_state", "int", "线索状态", "状态分析", "否"),
            Field("lead_state_name", "string", "线索状态名称", "状态分析", "否"),
            Field("user_id", "bigint", "用户id", "用户关联", "是"),
            Field("trace_type", "int", "留痕类型", "行为分析", "否"),
            Field("trace_type_name", "string", "留痕类型名称", "行为分析", "否"),
            Field("first_department_name", "string", "渠道归属一级部门名称", "范围限定", "是"),
            Field("second_department_name", "string", "渠道归属二级部门名称", "范围限定", "是"),
            Field("third_department_name", "string", "渠道归属三级部门名称", "范围限定", "是"),
            Field("lead_period_name", "string", "线索归属期name", "期次维度", "是"),
            Field("channel_name_1", "string", "渠道树一级名称", "渠道维度", "是"),
            Field("section_assign_employee_first_level_department_name", "string", "截面分配顾问一级部门名称", "范围限定", "是"),
            Field("section_assign_employee_second_level_department_name", "string", "截面分配顾问二级部门名称", "范围限定", "是"),
            Field("section_assign_employee_third_level_department_name", "string", "截面分配顾问三级部门名称", "范围限定", "是"),
            Field("section_assign_call_connected_count", "bigint", "截面分配后电话接通次数", "接通次数", "是"),
            Field("section_assign_call_missed_count", "bigint", "截面分配后电话未接通次数", "外呼分析", "否"),
            Field("section_assign_all_call_duration", "bigint", "截面分配后总通话时长(s)", "通话时长", "是"),
            Field("is_lead", "string", "是否计算线索数，取值需确认", "线索数", "是"),
            Field("is_valid_lead", "string", "是否计算有效线索数，取值需确认", "有效线索数", "是"),
            Field("lead_cost", "double", "线索成本", "成本分析", "否"),
        ],
        notes=["PDF 第 6-12 页字段极多，当前只录入可读核心字段；完整字段需人工复核。"],
    ),
    TableSeed(
        raw_name="dm_crm_lead_cost_gmv_communication_learn_full_link_df",
        zh_name="线索成本转化沟通行课全链路数据",
        database="service_dw",
        prefix_status="待确认：暂按 CRM 常见 service_dw 前缀记录",
        purpose="线索成本、转化、沟通、行课全链路明细，用于外呼、沟通、好友、行课、GMV 等看板指标。",
        grain="线索全链路明细，待确认",
        partitions=[Field("dt", "string", "天级分区", "分区过滤", "是")],
        fields=[
            Field("lead_id", "待人工确认", "线索id，字段是否存在需复核", "线索关联", "是"),
            Field("user_number", "待人工确认", "用户id，字段是否存在需复核", "用户关联", "是"),
            Field("lead_cost", "待人工确认", "线索成本，字段是否存在需复核", "成本分析", "否"),
            Field("gmv", "待人工确认", "成交 GMV，字段是否存在需复核", "GMV 分析", "否"),
        ],
        notes=["PDF 第 13-20 页为图片型字段表，未可靠 OCR；字段名需人工校验。"],
    ),
    TableSeed(
        raw_name="dws_user_active_user_c_appliction_hf",
        zh_name="c端用户活跃表应用粒度_当日小时全量",
        database="service_dw",
        prefix_status="待确认：暂按 service_dw 前缀记录",
        purpose="C 端用户在应用粒度的当日小时活跃数据。",
        grain="用户-应用-小时粒度，待确认",
        partitions=[
            Field("dt", "string", "天级分区", "分区过滤", "是"),
            Field("hour", "string", "小时分区", "分区过滤", "是"),
        ],
        fields=[
            Field("user_number", "待人工确认", "用户ID", "用户关联", "是"),
            Field("application_name", "待人工确认", "应用名称", "应用维度", "否"),
        ],
        notes=["PDF 第 21 页字段表为图片型，需人工校验。"],
    ),
    TableSeed(
        raw_name="dim_cstm_active_user_c_appliction_mb_df",
        zh_name="c端用户全量表应用粒度",
        database="service_dw",
        prefix_status="待确认：暂按 service_dw 前缀记录",
        purpose="C 端用户全量应用粒度维表。",
        grain="用户-应用粒度，待确认",
        partitions=[Field("dt", "string", "天级分区", "分区过滤", "是")],
        fields=[
            Field("user_number", "待人工确认", "用户ID", "用户关联", "是"),
            Field("application_name", "待人工确认", "应用名称", "应用维度", "否"),
        ],
        notes=["PDF 第 22 页字段表为图片型，需人工校验。"],
    ),
    TableSeed(
        raw_name="app_h_crm_lead_task_process_info_detail_hf",
        zh_name="高中线索服务跟进明细",
        database="service_dw",
        prefix_status="待确认：暂按 service_dw 前缀记录",
        purpose="高中线索服务任务跟进过程明细。",
        grain="线索-任务-小时粒度，待确认",
        partitions=[
            Field("dt", "string", "天级分区", "分区过滤", "是"),
            Field("hour", "string", "小时分区", "分区过滤", "是"),
        ],
        fields=[
            Field("lead_id", "待人工确认", "线索ID", "线索关联", "是"),
            Field("user_number", "待人工确认", "用户ID", "用户关联", "是"),
            Field("employee_id", "待人工确认", "员工ID", "员工维度", "是"),
        ],
        notes=["PDF 第 23-25 页字段表为图片型，需人工校验。"],
    ),
    TableSeed(
        raw_name="app_h_crm_lead_employee_workload_detail_hf",
        zh_name="高中顾问工作量看板",
        database="service_dw",
        prefix_status="待确认：暂按 service_dw 前缀记录",
        purpose="高中顾问工作量看板明细。",
        grain="顾问-小时粒度，待确认",
        partitions=[
            Field("dt", "string", "天级分区", "分区过滤", "是"),
            Field("hour", "string", "小时分区", "分区过滤", "是"),
        ],
        fields=[
            Field("employee_id", "待人工确认", "员工ID", "员工维度", "是"),
            Field("lead_count", "待人工确认", "线索数，字段是否存在需确认", "工作量指标", "否"),
            Field("call_count", "待人工确认", "外呼次数，字段是否存在需确认", "工作量指标", "否"),
        ],
        notes=["PDF 第 26-27 页字段表为图片型，需人工校验。"],
    ),
    TableSeed(
        raw_name="dws_service_user_learn_detail_hf",
        zh_name="小时级行课数据全量",
        database="service_dw",
        prefix_status="待确认：暂按 service_dw 前缀记录",
        purpose="小时级用户行课数据全量，用于到课、首节到课、行课时长等指标。",
        grain="用户-课程-小时粒度，待确认",
        partitions=[
            Field("dt", "string", "天级分区", "分区过滤", "是"),
            Field("hour", "string", "小时分区", "分区过滤", "是"),
        ],
        fields=[
            Field("user_number", "待人工确认", "用户ID", "用户关联", "是"),
            Field("lead_id", "待人工确认", "线索ID，字段是否存在需确认", "线索关联", "否"),
            Field("course_id", "待人工确认", "课程ID", "课程维度", "否"),
        ],
        notes=["PDF 第 28-29 页字段表为图片型，需人工校验。"],
    ),
    TableSeed(
        raw_name="dingxi01_jiagou_db",
        zh_name="架构映射表",
        database="temp_table",
        prefix_status="已确认：用户指定稳定临时表",
        purpose="架构映射表，用于部门/架构口径补充。",
        grain="映射关系粒度，待确认",
        partitions=[],
        fields=[
            Field("first_department_name", "待人工确认", "一级部门名称", "范围限定/映射", "是"),
            Field("second_department_name", "待人工确认", "二级部门名称", "范围限定/映射", "是"),
            Field("third_department_name", "待人工确认", "三级部门名称", "范围限定/映射", "否"),
        ],
        notes=["用户指定为稳定临时表，字段需从实际表或历史 SQL 补充。"],
    ),
    TableSeed(
        raw_name="dingxi01_daoke_1_6_t",
        zh_name="到课课次映射表",
        database="temp_table",
        prefix_status="已确认：用户指定稳定临时表",
        purpose="到课课次映射表，用于首节到课和课次相关指标。",
        grain="课次映射粒度，待确认",
        partitions=[],
        fields=[
            Field("course_id", "待人工确认", "课程ID", "课程关联", "否"),
            Field("lesson_seq", "待人工确认", "课次", "到课口径", "否"),
        ],
        notes=["用户指定为稳定临时表，字段需从实际表或历史 SQL 补充。"],
    ),
]


def safe_print(text: str) -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(text)


def extract_text_pymupdf(pdf: Path) -> list[str]:
    if fitz is None:
        return []
    doc = fitz.open(str(pdf))
    return [page.get_text("text").replace("\u200b", "") for page in doc]


def extract_text_pdfplumber(pdf: Path) -> list[str]:
    if pdfplumber is None:
        return []
    pages: list[str] = []
    with pdfplumber.open(str(pdf)) as doc:
        for page in doc.pages:
            pages.append((page.extract_text() or "").replace("\u200b", ""))
    return pages


def render_pages(pdf: Path) -> list[Path]:
    rendered: list[Path] = []
    if fitz is None:
        return rendered
    RENDERED.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf))
    stem = re.sub(r"[^\w.-]+", "_", pdf.stem, flags=re.UNICODE).strip("_") or "pdf"
    ascii_stem = "data_map_overview" if "数据地图概览" in pdf.name else stem
    for idx, page in enumerate(doc, start=1):
        target = RENDERED / f"{ascii_stem}_p{idx:02d}.png"
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        pix.save(str(target))
        rendered.append(target)
    return rendered


def find_headings(page_texts: list[str]) -> list[tuple[int, str, str]]:
    pattern = re.compile(r"(\d+)\.?\s*【([^】]+)】\s*([a-zA-Z0-9_]+)")
    found: list[tuple[int, str, str]] = []
    for idx, text in enumerate(page_texts, start=1):
        compact = re.sub(r"\s+", "", text)
        for m in pattern.finditer(compact):
            found.append((idx, m.group(2), m.group(3)))
    return found


def md_table(rows: Iterable[Field]) -> str:
    lines = ["| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |", "|---|---|---|---|---|"]
    for f in rows:
        lines.append(f"| {f.name} | {f.type} | {f.desc} | {f.use} | {f.common} |")
    return "\n".join(lines)


def partition_table(rows: Iterable[Field]) -> str:
    lines = ["| 字段名 | 类型 | 含义 | 是否必填 |", "|---|---|---|---|"]
    for f in rows:
        lines.append(f"| {f.name} | {f.type} | {f.desc} | {f.common if f.common in {'是', '否'} else '是'} |")
    if len(lines) == 2:
        lines.append("| 无 | - | 稳定临时表无固定分区，待确认 | 否 |")
    return "\n".join(lines)


def forced_ranges(fields: Iterable[Field]) -> list[Field]:
    ranges: list[Field] = []
    for f in fields:
        if "department_name" not in f.name:
            continue
        placeholder = "'<待填写>'"
        for token, value in DEPARTMENT_PLACEHOLDERS:
            if token in f.name:
                placeholder = value
                break
        ranges.append(Field(f.name, f.type, f.desc, placeholder, "是"))
    return ranges


def range_table(rows: Iterable[Field]) -> str:
    lines = ["| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |", "|---|---|---|---|---|"]
    for f in rows:
        lines.append(f"| {f.name} | {f.type} | {f.use} | 是 | {f.desc} |")
    if len(lines) == 2:
        lines.append("| 无 | - | - | 否 | 未识别 department_name 字段；若后续补充需重新检查 |")
    return "\n".join(lines)


def snippets(t: TableSeed) -> str:
    full = t.full_name
    has_hour = any(p.name == "hour" for p in t.partitions)
    dept = next((f.name for f in t.fields if "department_name" in f.name), None)
    base_where = "where t.dt = 'YYYYMMDD'"
    if has_hour:
        base_where += "\n  and t.hour = 'HH'"
    if dept:
        base_where += f"\n  and t.{dept} = '<一级部门名称>'"
    latest_order = "private_sea_update_time" if any(f.name == "private_sea_update_time" for f in t.fields) else "待确认更新时间字段"
    key = "user_number" if any(f.name == "user_number" for f in t.fields) else "lead_id"
    return f"""### 简单抽样

```sql
select *
from {full} t
{base_where}
limit 20;
```

### 最近小时分区抽样

```sql
select *
from {full} t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
limit 20;
```

### 按 dt/hour 统计分区数据量

```sql
select
    t.dt,
    {("t.hour," if has_hour else "'00' as hour,")}
    count(*) as cnt
from {full} t
where t.dt in ('YYYYMMDD')
{("  and t.hour in ('HH')" + chr(10) if has_hour else "")}group by t.dt{", t.hour" if has_hour else ""}
order by t.dt desc{", t.hour desc" if has_hour else ""}
limit 50;
```

### 字段分布探索

```sql
select
    t.{key},
    count(*) as cnt
from {full} t
{base_where}
group by t.{key}
order by cnt desc
limit 50;
```

### 每用户或每线索取最新记录

```sql
select *
from (
    select
        t.*,
        row_number() over (
            partition by t.{key}
            order by t.{latest_order} desc
        ) as rn
    from {full} t
{base_where}
) x
where x.rn = 1
limit 100;
```
"""


def table_markdown(t: TableSeed) -> str:
    notes = "\n".join(f"- {n}" for n in t.notes) or "- 待人工确认。"
    filters = ["- `dt = 'YYYYMMDD'`" if t.partitions else "- 稳定临时表无分区，需使用业务范围条件。"]
    if any(p.name == "hour" for p in t.partitions):
        filters.append("- `hour = 'HH'`")
    for f in forced_ranges(t.fields):
        filters.append(f"- `{f.name} = {f.use}`")
    joins = [f.name for f in t.fields if f.name in {"user_number", "user_id", "lead_id", "employee_id", "course_id"}]
    joins_text = "\n".join(f"- `{j}`" for j in joins) or "- 待确认"
    return f"""# {t.full_name}

## 1. 中文名称

{t.zh_name}

## 2. 表用途

{t.purpose}

库名前缀状态：{t.prefix_status}

## 3. 数据粒度

{t.grain}

## 4. 查询引擎

Presto

## 5. 分区字段

{partition_table(t.partitions)}

## 6. 强制范围限定字段

{range_table(forced_ranges(t.fields))}

说明：
- 对所有 department_name 相关字段，标记为需要范围限定；
- 不知道默认值时，推荐取值写 `'<待填写>'`。

## 7. 字段清单

{md_table(t.fields)}

## 8. 常用过滤条件

{chr(10).join(filters)}

## 9. 常用 join key

{joins_text}

## 10. 常用 SQL 片段

{snippets(t)}

## 11. 注意事项

- 分区限制：查询分区表必须带分区条件。
- department_name 范围限定：涉及部门字段必须过滤；未给取值时使用占位符。
- 字段类型注意事项：PDF 图片 OCR 低置信度字段必须先人工确认。
- 常见报错：字段不存在、库名前缀不正确、小时表遗漏 hour、group by 不完整。
- 待人工确认问题：
{notes}
"""


def write_tables(overwrite: bool) -> list[str]:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for seed in SEEDS:
        path = TABLE_DIR / seed.filename
        if path.exists() and not overwrite:
            continue
        path.write_text(table_markdown(seed), encoding="utf-8")
        written.append(path.name)
    return written


def write_report(pdf_summaries: list[dict], headings: list[tuple[int, str, str]], written: list[str]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PDF 解析报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 成功识别的表",
        "",
        "| 页码 | 中文名 | 表名 |",
        "|---|---|---|",
    ]
    for page, zh, table in headings:
        lines.append(f"| {page} | {zh} | {table} |")
    if not headings:
        lines.append("| - | 未从文本层识别；使用内置种子表清单初始化 | - |")
    lines.extend([
        "",
        "## 成功识别的字段数",
        "",
        "| 表名 | 初始化字段数 | 说明 |",
        "|---|---:|---|",
    ])
    for seed in SEEDS:
        lines.append(f"| {seed.full_name} | {len(seed.fields) + len(seed.partitions)} | 图片型字段页低置信度，需人工校验 |")
    lines.extend([
        "",
        "## 低置信度页面",
        "",
        "| PDF | 页码 | 文本长度 | 图片数 | 说明 |",
        "|---|---:|---:|---:|---|",
    ])
    for item in pdf_summaries:
        if item["text_len"] < 200 or item["images"] > 0:
            lines.append(
                f"| {item['pdf']} | {item['page']} | {item['text_len']} | {item['images']} | 可能为图片型表格或字段跨页，需人工校验 |"
            )
    lines.extend([
        "",
        "## 需要人工校验的内容",
        "",
        "- PDF 中大量字段表为图片型页面，自动抽取无法可靠识别字段名、类型、描述边界。",
        "- 字段名换行、字段类型错位、字段描述错位、跨页字段遗漏均需人工复核。",
        "- 库名前缀除 `service_dw.dwd_crm_assign_private_detail_hf` 和 `temp_table.*` 外均标记为待确认。",
        "- 生成 SQL 前不得使用未确认字段做生产口径。",
        "",
        "## 本次写入的表文件",
        "",
    ])
    lines.extend(f"- `{name}`" for name in written)
    if not written:
        lines.append("- 未覆盖已有表文件；如需重建，使用 `--overwrite`。")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_pdf(pdf: Path) -> tuple[list[str], list[dict]]:
    texts = extract_text_pymupdf(pdf)
    if not texts:
        texts = extract_text_pdfplumber(pdf)
    summaries: list[dict] = []
    image_counts: list[int] = [0] * len(texts)
    if fitz is not None:
        doc = fitz.open(str(pdf))
        image_counts = [len(page.get_images(full=True)) for page in doc]
        if not texts:
            texts = [""] * doc.page_count
    for idx, text in enumerate(texts, start=1):
        images = image_counts[idx - 1] if idx - 1 < len(image_counts) else 0
        summaries.append({"pdf": pdf.name, "page": idx, "text_len": len(text or ""), "images": images})
    return texts, summaries


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract schema PDFs into table Markdown knowledge.")
    parser.add_argument("--pdf", action="append", help="Specific PDF path. Defaults to resources/raw_pdfs/*.pdf")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing table Markdown files")
    parser.add_argument("--no-render", action="store_true", help="Skip rendering image pages")
    args = parser.parse_args()

    pdfs = [Path(p) for p in args.pdf] if args.pdf else sorted(RAW_PDFS.glob("*.pdf"))
    if not pdfs:
        safe_print(f"No PDFs found in {RAW_PDFS}")
        return 1

    all_headings: list[tuple[int, str, str]] = []
    all_summaries: list[dict] = []
    for pdf in pdfs:
        texts, summaries = summarize_pdf(pdf)
        all_headings.extend(find_headings(texts))
        all_summaries.extend(summaries)
        if not args.no_render:
            render_pages(pdf)

    written = write_tables(overwrite=args.overwrite)
    write_report(all_summaries, all_headings, written)
    safe_print(f"Wrote report: {REPORT}")
    safe_print(f"Table files written: {len(written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
