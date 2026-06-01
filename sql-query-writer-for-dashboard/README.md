# sql-query-writer-for-dashboard

## 0. 如何在新对话中调用

推荐在 Codex 新对话开头直接写：

```text
请加载并使用 Codex Skill：sql-query-writer-for-dashboard。

Skill 路径优先使用：
C:\Users\Ludim\.codex\skills\sql-query-writer-for-dashboard

请先读取该 Skill 的 SKILL.md、metadata.json 和 knowledge/01_table_index.md，再按我的需求检索相关的 knowledge/tables、knowledge/metrics、knowledge/dashboards、knowledge/dashboard_web_profiles、knowledge/joins 和 knowledge/sql_patterns。

后续所有 SQL 都必须按公司看板取数规则生成：只生成 Presto SQL；所有物理表带完整库名前缀；分区表加 dt；小时表建议加 hour；探索查询加 limit；涉及 department_name、部门、架构、业务线字段时加范围限定；不得使用知识库不存在的字段；SQL 后解释使用表、字段、join key、分区、范围限定、指标口径、limit 和待确认事项。

我的需求是：
【在这里写你的具体 SQL 需求】
```

更多模板见：

```text
docs/USAGE_PROMPTS.md
```

## 1. Skill 是什么

这是一个公司内部看板取数 SQL 生成 Skill。它基于表结构 PDF、字段知识库、指标口径、历史看板 SQL、join 关系和查询平台约束，生成 Presto SQL，并输出可审核的解释。

## 2. 适用场景

- 简单查看表结构或样本数据。
- 查询字段分布。
- 生成明细抽样 SQL。
- 生成指标汇总 SQL。
- 基于历史看板逻辑生成多 CTE SQL。
- 修复 SQL 报错并说明原因。
- 查询自助 BI 看板页面结构、筛选器、字段 ID、组件单元和刷新任务 ID。

## 3. 不适用场景

- 非 Presto 查询。
- 没有完整库名前缀且无法确认库名的生产查询。
- 缺少分区条件、部门范围限定或指标口径仍不清楚的大表全量扫描。
- 需要实时写入、DDL、DML 或删除数据的操作。

## 4. 如何上传新的表结构 PDF

后续新增表结构时，将 PDF 放入：

```text
resources/raw_pdfs/
```

然后运行或调用：

```bash
python scripts/extract_pdf_to_md.py
python scripts/normalize_schema_md.py
```

## 5. 如何将 PDF 转成 MD

`scripts/extract_pdf_to_md.py` 会尝试用 PyMuPDF 或 pdfplumber 抽取文本；图片型页面会渲染到：

```text
resources/rendered_pages/
```

脚本会生成：

```text
resources/pdf_extract_report.md
knowledge/tables/*.md
```

无法可靠识别的字段会写成“待人工确认”，不会静默丢弃。

## 6. 如何新增看板 SQL

新增看板 SQL 时，将 SQL 文件放入：

```text
resources/raw_sql/
```

然后运行或调用：

```bash
python scripts/ingest_dashboard_sql.py
```

脚本会抽取表、CTE、join key、where 条件、group by 维度和聚合指标，生成 `knowledge/dashboards/看板名称.md`。

## 7. 如何新增指标口径

优先在 `knowledge/metrics/` 里新增一个指标文件，使用 `_metric_template.md` 的结构。

新增指标定义图片时，将图片放入：

```text
resources/raw_images/
```

若图片无法被自动识别，则在 `knowledge/metrics/` 中手工补充，不得擅自猜测指标定义。

## 8. 如何更新 Web BI 看板结构快照

当需要记录自助 BI 页面上的筛选器、字段 ID、组件单元、下载按钮、刷新任务 ID 或图表序列时，使用 `usql-web-query-operator/scripts/read_dashboard.py` 抽取结构，再将摘要维护到：

```text
knowledge/dashboard_web_profiles/
```

该目录只保存页面结构和刷新元数据，不保存返回结果明细行；SQL 业务口径仍以 `knowledge/dashboards/` 和 `knowledge/metrics/` 为准。

## 9. 如何更新表索引

运行：

```bash
python scripts/normalize_schema_md.py
```

脚本会检查表结构 Markdown，并更新：

```text
knowledge/01_table_index.md
```

维护后建议运行结构自检：

```bash
python scripts/check_skill_integrity.py
```

## 10. 如何让 Code X 生成探索型 SQL

示例需求：

```text
帮我简单查看 service_dw.dwd_crm_assign_private_detail_hf 的样本数据。
```

Code X 应使用单日单小时、`department_name` 范围限定和 `limit`，不能无分区扫描。

## 11. 如何让 Code X 生成看板型 SQL

示例需求：

```text
帮我按期次、渠道、员工统计线索数、有效线索数、外呼次数、接通次数。
```

Code X 应先读取 `knowledge/dashboards/`、`knowledge/metrics/` 和 `knowledge/joins/`，优先用多 CTE 结构输出 SQL。口径不完整时必须标记“待人工确认”。

## 12. 如何处理 SQL 报错

把报错 SQL 和错误信息发给 Code X。Code X 应：

- 判断是否为 Presto 语法问题。
- 检查表名是否完整。
- 检查字段是否存在于知识库。
- 检查 `dt`、`hour`、`department_name` 范围限定和 `group by`。
- 输出修复后的 SQL 和原因。

可运行：

```bash
python scripts/validate_sql_rules.py --sql-file path/to/query.sql --exploratory
```

## 13. 常见错误示例

错误：表名不带库名。

```sql
select * from dwd_crm_assign_private_detail_hf limit 20;
```

错误：小时表缺少 `hour`。

```sql
select * from service_dw.dwd_crm_assign_private_detail_hf t where t.dt = '20260115' limit 20;
```

错误：涉及部门字段但缺少范围限定。

```sql
select assign_employee_first_level_department_name, count(*)
from service_dw.dwd_crm_assign_private_detail_hf t
where t.dt = '20260115'
group by assign_employee_first_level_department_name;
```

错误：数字字段用字符串比较。

```sql
where lead_count >= '2'
```
