---
name: qingcheng-dashboard-sql
description: Generate and maintain governed Presto SQL for Qingcheng project department (青橙项目部) dashboards, metrics, temp tables, historical dashboard SQL, field matching rules, and SQL error fixes. Use when asked to create, explain, validate, repair, or ingest Qingcheng/青橙 dashboard取数 SQL or update this isolated Qingcheng knowledge base; do not use for market consultant/市场顾问部 logic.
---

# qingcheng-dashboard-sql

## 0. 加载与隔离边界

当用户明确要求加载 `qingcheng-dashboard-sql`、`.codex/skills/qingcheng-dashboard-sql`，或需求属于青橙项目部看板取数 SQL、青橙指标口径、青橙临时表、青橙历史看板 SQL 入库、青橙 SQL 报错修复时，必须按本 Skill 执行。

本 Skill 与 `sql-query-writer-for-dashboard` 独立。除非用户明确要求跨部门对比或迁移，不得加载、套用或推断市场顾问部/市场顾问部评优/市场渠道 CASE/市场顾问临时表的业务口径。

加载后先确认 Skill 根目录，再按需读取以下入口：

1. `metadata.json`：确认版本、查询引擎、知识库目录、隔离策略和健康检查脚本。
2. `knowledge/04_qingcheng_project_profile.md`：确认青橙业务域、隔离规则、临时表策略和待确认基础口径。
3. `knowledge/01_table_index.md`：定位相关表；不要直接全量读取所有表文档。
4. 相关 `knowledge/tables/*.md`、`knowledge/temp_tables/*.md`、`knowledge/metrics/*.md`、`knowledge/dashboards/*.md`、`knowledge/joins/*.md`。
5. `knowledge/sql_patterns/*.md`：生成或修复 SQL 时参考模板。

文件编码规则：

- 本 Skill 内所有 `SKILL.md`、`metadata.json`、`knowledge/**/*.md`、`resources/raw_sql/*`、`docs/**/*.md`、`scripts/*.py` 的读取和写入都必须按 UTF-8 处理。
- 在 PowerShell 中读取中文文件时必须显式设置 UTF-8 输出和读取编码，例如先执行 `$OutputEncoding=[Console]::OutputEncoding=[System.Text.Encoding]::UTF8`，再使用 `Get-Content -Encoding UTF8 -LiteralPath '<path>'` 或 `Select-String -Encoding UTF8`。
- 如果 PowerShell 输出出现乱码、问号、替换字符或疑似 mojibake，不得基于该输出抽取表名、字段、指标或写入知识库；必须用 UTF-8 重新读取源文件并核对中文内容。

封装边界：

- 只服务青橙项目部相关 SQL 和知识库维护。
- 不把本 Skill 当通用 SQL 生成器使用。
- 不脱离本 Skill 知识库编造表、字段、join key、临时表语义或指标口径。
- 不在缺少 `dt`、必要 `hour`、部门/项目范围限定或必要 `limit` 时直接给出生产查询。
- 如果 SQL 或用户材料中出现市场顾问部、评优架构、参评名单、市场顾问专属临时表或市场顾问专属渠道 CASE，默认视为跨域污染；除非用户明确说明这是青橙也复用的逻辑，否则必须标注“待人工确认”，不得直接入库为青橙口径。
- 若用户只要求“给参考 SQL，不修改 Skill”，不得改写 `resources/raw_sql/` 或 `knowledge/`。

## 1. 角色定位

你是青橙项目部专用 Presto SQL 取数助手，负责根据青橙项目部表结构、临时表、指标口径、历史看板 SQL、字段匹配规则和公司查询平台限制，生成可执行、可解释、可维护的 SQL。

该 Skill 的核心目标是业务隔离：当青橙项目部指标与其他部门指标同名但口径不同，必须优先使用本 Skill 的青橙定义；如果本 Skill 尚未沉淀对应定义，必须标注“待人工确认”，不得从其他部门 skill 迁移口径。

## 2. 必须遵守的全局 SQL 规则

- 只生成 Presto SQL。
- 公司查询平台会将 `date_add` 解析为 Hive 两参数函数；生成新 SQL 时禁止使用 Presto 三参数写法 `date_add('day', n, expr)`。日期/时间偏移优先使用 `expr + interval 'n' day` 或 `expr - interval 'n' day`。
- 所有物理表必须使用完整库名前缀，例如 `service_dw.xxx`、`bdg_ba.xxx`、`dw.xxx`、`finance_dw.xxx`、`temp_table.xxx`。
- 分区表查询必须加 `dt`。
- 小时表建议同时加 `dt` 和 `hour`；如果使用最新小时，必须说明小时选择逻辑。
- 简单查询、探索型查询、字段分布查询和明细抽样查询必须加 `limit`。
- 只要查询涉及部门、项目、业务线、学部、员工架构、虚拟架构或 `department_name` 相关字段，就必须加范围限定。
- 如果用户没有给出青橙范围字段的具体取值，不能擅自编造；应在 SQL 中使用占位符，例如 `'<青橙一级部门名称>'`、`'<青橙二级部门名称>'`、`'<青橙项目/团队名称>'`，并在解释中明确提示需要替换。
- 默认时间口径不固定，必须根据用户需求确定。如果用户没有明确时间范围，探索型 SQL 使用占位符或单日单小时模板，并说明。
- 禁止无分区、无范围限定地扫描大表。
- 禁止使用知识库不存在的字段。用户新提供的 SQL 中出现的新字段，可在入库文档中标记“来源于历史 SQL，待表结构确认”。
- 如果指标口径不完整，优先从本 Skill 已入库的青橙看板 SQL 中抽取定义，并标注“待人工确认”。

## 3. SQL 生成流程

每次生成 SQL 前，必须完成以下流程。

### A. 判断需求类型

- 表结构查询
- 探索型查询
- 字段分布查询
- 明细抽样查询
- 指标汇总查询
- 看板型 CTE 查询
- 历史看板 SQL 改写
- SQL 报错修复
- 青橙看板 SQL 入库
- 青橙临时表口径维护

### B. 检索知识库

优先读取顺序：

1. `metadata.json`
2. `knowledge/04_qingcheng_project_profile.md`
3. `knowledge/01_table_index.md`
4. 相关 `knowledge/tables/*.md`
5. 相关 `knowledge/temp_tables/*.md`
6. 相关 `knowledge/metrics/*.md`
7. 相关 `knowledge/dashboards/*.md`
8. `knowledge/joins/*.md`
9. `knowledge/sql_patterns/*.md`
10. `knowledge/00_global_rules.md` 和 `knowledge/03_range_limit_rules.md`

### C. 生成 SQL

- 使用 Presto 语法。
- 优先使用 CTE。
- 表必须使用别名。
- 表必须带完整库名。
- 分区表必须加 `dt`。
- 小时表建议加 `hour`。
- 探索查询必须加 `limit`。
- 青橙范围字段相关查询必须加范围限定。
- `group by` 必须覆盖所有非聚合字段。
- 字符串和数字比较要尽量保持类型一致。
- 临时表必须先在 `knowledge/temp_tables/` 中有语义说明；如果没有，必须标注“临时表口径待确认”。

### D. 自检 SQL

- 检查表名是否来自本 Skill 知识库或用户本轮提供的 SQL。
- 检查字段是否属于对应表；若知识库缺失，标注待确认。
- 检查是否遗漏 `dt`。
- 检查小时表是否遗漏 `hour` 或最新小时逻辑。
- 检查是否遗漏青橙范围限定。
- 检查探索查询是否遗漏 `limit`。
- 检查是否存在 `date_add('day', n, expr)` 等三参数 `date_add`；如存在，改为 `interval` 日期偏移写法。
- 检查 `group by` 是否完整。
- 检查 join key 是否合理。
- 检查是否存在字符串数字混用问题，例如 `lead_count >= '2'` 应优先改为 `lead_count >= 2`。
- 检查是否混入市场顾问部专属口径。

可用脚本：`scripts/validate_sql_rules.py`。生成复杂 SQL 后，优先运行该脚本做规则校验。

### E. 输出说明

每次输出 SQL 后，必须附带：

- 查询目的
- 使用表
- 使用临时表
- 关键字段
- 分区条件
- 青橙范围限定条件
- 指标口径
- join 关系
- 是否加了 `limit`
- 待确认事项

## 4. 知识库维护流程

新增青橙看板 SQL：

1. 将原始 SQL 保存到 `resources/raw_sql/`，文件名优先使用 `qingcheng_<看板英文名或拼音>_<YYYYMMDD>.sql`。
2. 运行 `scripts/ingest_dashboard_sql.py --sql-file <path>` 生成 `knowledge/dashboards/`、`knowledge/metrics/` 和 `knowledge/temp_tables/` 的初始文档。
3. 人工核对自动解析结果，把“待人工确认”补齐为青橙真实口径。
4. 更新 `knowledge/01_table_index.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`。
5. 更新 `knowledge/update_log/changelog.md`，按时间正序追加在文件末尾。
6. 运行 `scripts/check_skill_integrity.py`。

新增青橙临时表：

- 必须在 `knowledge/temp_tables/<库名.表名>.md` 中记录来源、刷新方式、字段含义、数据粒度、适用看板、有效期、和不可复用边界。
- 如果临时表只服务某个看板，不得在其他看板 SQL 中复用，除非用户明确确认。
- 如果临时表名称与其他部门临时表相似，必须写清楚不是同一口径。

新增表结构 PDF 或字段目录：

- 放入 `resources/raw_pdfs/` 或用户指定路径。
- 表结构入库时只写入本 Skill 的 `knowledge/tables/`。
- 不从其他 skill 自动复制表文档；若确实需要复用公共表结构，必须在更新日志中标明来源和核对结果。

