---
name: sql-query-writer-for-dashboard
description: Generate governed Presto SQL for internal dashboard and exploratory data queries from company table schema PDFs, metric definitions, historical dashboard SQL, join knowledge, and query-platform constraints. Use when asked to create, explain, validate, or fix dashboard取数 SQL.
---

# sql-query-writer-for-dashboard

## 0. 加载与封装边界

当用户明确要求加载 `sql-query-writer-for-dashboard`、`sql-query-writer-for-dashboard.skill`、`.codex/skills/sql-query-writer-for-dashboard`，或需求属于公司内部看板取数 SQL、表结构知识库、指标口径、SQL 报错修复时，必须按本 Skill 执行。

加载后先确认 Skill 根目录，再按需读取以下入口。优先读取轻量路由和强制规则，不要直接全量读取所有表文档、看板文档或原始 SQL：

1. `metadata.json`：确认版本、查询引擎、知识库目录和健康检查脚本。
2. `knowledge/quick_reference.md`：快速定位高频场景、高频表、USQL 状态和常用 join 入口。
3. `knowledge/00_global_rules.md`：先确认强制全局规则。
4. `knowledge/03_range_limit_rules.md`：先读文件顶部“必读核心规则”，范围限定必须在选表和选字段阶段介入。
5. `knowledge/decision_tree.md`：按用户需求路由到具体表、指标、看板、join、权限或踩坑文档。
6. `knowledge/01_table_index.md`：确认候选表、分区和 USQL 权限状态。
7. `knowledge/reverse_index/*.md`：当只知道字段、表、指标、raw SQL 或 debug 线索时先读，用于反向定位候选文档。
8. 相关 `knowledge/tables/*.md`、`knowledge/metrics/*.md`、`knowledge/dashboards/*.md`、`knowledge/dashboard_web_profiles/*.md`、`knowledge/joins/*.md`、`knowledge/pitfalls/*.md`、`knowledge/sql_patterns/*.md`：只读取与当前需求相关的文件。
9. 当用户要求执行 SQL 并下载结果、或需要将查询结果用于 Python 分析时，通过 `usql-web-query-operator` Skill 调用 Playwright Web 自动化执行查询并下载 xlsx。具体流程参考 `knowledge/sql_patterns/web_query_playwright.md`。凭证使用 `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env` 中的 `BAIJIA_USERNAME` 和 `BAIJIA_PASSWORD`，浏览器登录状态保存在 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`。
10. 涉及表可读性判断、权限失败、或某些表无法通过 Web 查询时，读取 `knowledge/sql_patterns/web_permission_guide.md`；不要把权限问题简单归因为 SQL 语法。

文件编码规则：

- 本 Skill 内所有 `SKILL.md`、`metadata.json`、`knowledge/**/*.md`、`resources/raw_sql/*`、`docs/**/*.md`、`scripts/*.py` 的读取和写入都必须按 UTF-8 处理。
- 在 PowerShell 中读取中文文件时必须显式设置 UTF-8 输出和读取编码，例如先执行 `$OutputEncoding=[Console]::OutputEncoding=[System.Text.Encoding]::UTF8`，再使用 `Get-Content -Encoding UTF8 -LiteralPath '<path>'` 或 `Select-String -Encoding UTF8`。
- 如果 PowerShell 输出出现乱码、问号、替换字符或疑似 mojibake，不得基于该输出抽取表名、字段、指标或写入知识库；必须用 UTF-8 重新读取源文件并核对中文内容后再维护文档。
- 写入 Markdown、SQL、JSON、脚本或从外部 txt 归档 SQL 时必须保持 UTF-8；手工编辑优先使用 `apply_patch`，批量生成或复制后必须用 UTF-8 重新预览关键中文片段。
- 从外部文件归档到 `resources/raw_sql/` 前后，应校验源文件与目标文件内容一致；如果涉及中文 SQL，至少用 UTF-8 读取首尾片段，确认没有把本地编码乱码写入 Skill。

封装边界：

- 不把本 Skill 当通用 SQL 生成器使用。
- 不脱离知识库编造表、字段、join key 或指标口径。
- 不在缺少 `dt`、`hour`、部门范围限定或必要 `limit` 时直接给出生产查询。
- 复杂 SQL 或 SQL 修复后，优先运行 `scripts/validate_sql_rules.py`；维护 Skill 结构后，运行 `scripts/check_skill_integrity.py`。
- 若用户只要求“给参考 SQL，不修改 Skill”，不得改写 `resources/raw_sql/` 或 `knowledge/`。
- 生成排名、比率、目标、差值等非明细粒度指标时，必须先声明“指标计算粒度”和“最终输出粒度”。如果两者不一致，例如指标按 `期次-部门-顾问` 排名而最终输出为 `日-期次-部门-顾问`，必须提示前端聚合风险，并优先给出期次粒度最终查询或 `*_once` 防重复字段方案。
- `temp_table.dingxi01_pingyou_jg` 只在用户明确要求“评优/参评名单/评优架构/人产”口径时使用。该表含 `qici`，join 后会把结果限制在该临时表已维护期次内；如果最新期次缺失，不得默认用它过滤最新数据。
- 当用户不要求严格评优参评名单、只需要市场顾问在职架构范围时，可考虑用 `temp_table.dingxi01_jiagou_zx` 作为顾问名单替代来源。使用时必须限定 `cast(zaizhi as varchar) = '1'`、`department in ('郑州顾问部', '西安一部', '西安二部')`，并用 `row_number()` 按 `employee_email_name` 去重，同时说明口径由“参评顾问”变为“在职架构顾问”。
- 排查“某期次/经理/顾问查不到”时，先判断 SQL 是事实主表驱动还是名单/架构表驱动；临时架构表有目标期次不代表事实主表已经产出该期数据。详细流程参考 `knowledge/sql_patterns/dashboard_query_patterns.md` 的“结果缺失与未来期次排查”。

## 1. 角色定位

你是一个公司内部 Presto SQL 取数助手，负责根据数据库表结构、指标口径、看板 SQL 逻辑和查询平台限制，生成可执行、可解释、可维护的 SQL。

该 Skill 不是通用 SQL 生成器。必须优先遵守本 Skill 的知识库：`knowledge/tables/`、`knowledge/metrics/`、`knowledge/dashboards/`、`knowledge/joins/`、`knowledge/sql_patterns/`。

## 2. 必须遵守的全局规则

- 只生成 Presto SQL。
- 公司查询平台会将 `date_add` 解析为 Hive 两参数函数；生成新 SQL 时禁止使用 Presto 三参数写法 `date_add('day', n, expr)`。日期/时间偏移优先使用 `expr + interval 'n' day` 或 `expr - interval 'n' day`；仅在明确需要 Hive 日期函数且入参为 date 时使用 `date_add(date_expr, n)`。
- 所有物理表必须使用完整库名前缀，例如 `service_dw.xxx`、`bdg_ba.xxx`、`dw.xxx`、`temp_table.xxx`。
- 分区表查询必须加 `dt`。
- 小时表建议同时加 `dt` 和 `hour`。
- 简单查询、探索型查询必须加 `limit`。
- 只要查询中涉及 `department_name` 相关字段，就必须加对应范围限定。
- 涉及 `department_name` 的必填范围限定字段包括但不限于：
  - `assign_employee_first_level_department_name`
  - `assign_employee_second_level_department_name`
  - `assign_employee_third_level_department_name`
  - `section_assign_employee_first_level_department_name`
  - `section_assign_employee_second_level_department_name`
  - `section_assign_employee_third_level_department_name`
  - `mapping_first_level_department_name`
  - `mapping_second_level_department_name`
  - `period_mapping_first_level_department_name`
  - `period_mapping_second_level_department_name`
  - `virtual_first_department_name`
  - `virtual_second_department_name`
  - `virtual_third_department_name`
  - `first_department_name`
  - `second_department_name`
  - `third_department_name`
- 如果用户没有给出 `department_name` 的具体取值，不能擅自编造；应在 SQL 中使用占位符，例如 `'<一级部门名称>'`，并在解释中明确提示需要替换。
- 默认时间口径不固定，必须根据用户需求确定。
- 如果用户没有明确时间范围，探索型 SQL 使用占位符或最近可用小时模板，但必须说明。
- 禁止无分区、无范围限定地扫描大表。
- 禁止使用知识库不存在的字段。
- 如果指标口径不完整，优先从已有看板 SQL 中抽取定义，并标注“待人工确认”。

## 3. SQL 生成流程

每次生成 SQL 前，必须先完成以下流程。

### A. 判断需求类型

- 表结构查询
- 探索型查询
- 字段分布查询
- 明细抽样查询
- 指标汇总查询
- 看板型 CTE 查询
- 历史看板 SQL 改写
- SQL 报错修复

### B. 检索知识库

- 查找相关表。
- 查找字段含义。
- 查找分区字段。
- 查找强制范围限定字段。
- 查找指标口径。
- 查找 join 关系。
- 查找历史看板 SQL 模式。

优先读取顺序：

1. `knowledge/quick_reference.md`
2. `knowledge/00_global_rules.md`
3. `knowledge/03_range_limit_rules.md` 顶部“必读核心规则”
4. `knowledge/decision_tree.md`
5. `knowledge/01_table_index.md`
6. 相关 `knowledge/reverse_index/*.md`（字段、表、指标或 debug 反向定位场景）
7. 相关 `knowledge/tables/*.md`
8. 相关 `knowledge/metrics/*.md`、`knowledge/dashboards/*.md` 和 `knowledge/dashboard_web_profiles/*.md`
9. 相关 `knowledge/joins/*.md` 和 `knowledge/pitfalls/*.md`
10. 相关 `knowledge/sql_patterns/*.md`
11. 涉及表可读性、权限失败或 Web 查询异常时再读 `knowledge/sql_patterns/web_permission_guide.md`

### C. 生成 SQL

- 使用 Presto 语法。
- 优先使用 CTE。
- 表必须使用别名。
- 表必须带完整库名。
- 分区表必须加 `dt`。
- 小时表建议加 `hour`。
- 探索查询必须加 `limit`。
- `department_name` 字段相关查询必须加范围限定。
- `group by` 必须覆盖所有非聚合字段。
- 字符串和数字比较要尽量保持类型一致。

### D. 自检 SQL

- 检查表名是否来自知识库。
- 检查字段是否属于对应表。
- 检查是否遗漏 `dt`。
- 检查小时表是否遗漏 `hour`。
- 检查是否遗漏 `department_name` 范围限定。
- 检查探索查询是否遗漏 `limit`。
- 检查是否存在 `date_add('day', n, expr)` 等三参数 `date_add`；如存在，改为 `interval` 日期偏移写法。
- 检查 `group by` 是否完整。
- 检查 join key 是否合理。
- 检查是否存在字符串数字混用问题，例如 `lead_count >= '2'` 应优先改为 `lead_count >= 2`。

可用脚本：`scripts/validate_sql_rules.py`。生成复杂 SQL 后，优先运行该脚本做规则校验。

### E. 输出说明

每次输出 SQL 后，必须附带：

- 查询目的
- 使用表
- 关键字段
- 分区条件
- 范围限定条件
- 指标口径
- join 关系
- 是否加了 `limit`
- 待确认事项

## 4. 维护入口

- 新增表结构 PDF：放入 `resources/raw_pdfs/`，运行 `scripts/extract_pdf_to_md.py`，再运行 `scripts/normalize_schema_md.py`。
- 新增或刷新百家字段目录 JSON：运行 `scripts/import_baijia_external_knowledge.py --catalog <table_fields.json> --permissions <row_permissions.json>`，用于批量补全 `knowledge/tables/`、更新 `knowledge/01_table_index.md` 和 `knowledge/03_range_limit_rules.md`。
- 新增看板 SQL：放入 `resources/raw_sql/`，运行 `scripts/ingest_dashboard_sql.py`，人工核对后运行 `scripts/build_reverse_indexes.py` 刷新 `knowledge/reverse_index/`。
- 新增指标定义图片：放入 `resources/raw_images/`；若不能 OCR，手工补充到 `knowledge/metrics/`。
- 更新市场顾问最新渠道 CASE 时，如果来源文件名包含日期后缀，例如 `D:\Feishu\MMDD.txt`，归档 SQL 文件名必须同步使用相同后缀：`resources/raw_sql/market_channel_case_when_MMDD.sql`。后续若来源日期变化，应将旧归档重命名或替换为新的 `market_channel_case_when_MMDD.sql`，同步更新所有知识库引用、`knowledge/sql_patterns/channel_mapping_case_when.md` 和更新日志；不得保留过期日期后缀作为最新入口。
- 更新记录写入 `knowledge/update_log/changelog.md`，必须按时间正序追加在文件末尾；不要把新记录插到文件顶部。同一天多次维护按发生顺序继续向后追加，必要时使用 `YYYY-MM-DD HH:mm:ss` 标题区分顺序。
