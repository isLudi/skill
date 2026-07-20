---
name: qingcheng-dashboard-sql
description: Resolve, plan, compile, explain, validate, repair, and maintain governed Presto SQL and domain-bound dashboard designs for Qingcheng project department (青橙项目部), using isolated semantic contracts, metrics, dashboards, temp tables, historical SQL, range rules, and bounded data probes. Use for Qingcheng/青橙 Text2SQL, dashboard取数与设计/diff/dry-run, completion, conversion, attendance, revenue, metric disambiguation, data-definition exploration, and knowledge maintenance; never use market-consultant/市场顾问部 semantics to fill Qingcheng gaps.
---

# qingcheng-dashboard-sql

## 0. 加载与隔离边界

当用户明确要求加载 `qingcheng-dashboard-sql`、`.codex/skills/qingcheng-dashboard-sql`，或需求属于青橙项目部看板取数 SQL、青橙指标口径、青橙临时表、青橙历史看板 SQL 入库、青橙 SQL 报错修复时，必须按本 Skill 执行。

本 Skill 与 `sql-query-writer-for-dashboard` 独立。除非用户明确要求跨部门对比或迁移，不得加载、套用或推断市场顾问部/市场顾问部评优/市场渠道 CASE/市场顾问临时表的业务口径。

加载后先确认 Skill 根目录，再按需读取以下入口：

1. `metadata.json`：确认 `domain_id=qingcheng`、版本、查询引擎、共享 Core、物理目录、隔离策略和健康检查脚本。
2. `semantic/domain_manifest.json`：读取轻量的青橙实体清单、证据路径和隔离声明；它只做域内路由，不替代业务文档。
3. `semantic/generated/contract_index.json`：按指标、维度、join、范围别名定位契约 ID、状态和来源；它是生成索引，不是口径权威。
4. `semantic/contracts/*.json`：只读取命中的契约；`confirmed` 可进入规划，`pending_confirmation` 只能形成待确认项或探查计划。
5. `knowledge/quick_reference.md`：快速定位高频看板、表、临时表和反向索引入口。
6. `knowledge/04_qingcheng_project_profile.md`：确认青橙业务域、隔离规则、临时表策略和待确认基础口径。
7. `knowledge/decision_tree.md`：按用户需求路由到具体表、指标、看板、join、反向索引或 SQL 模板。
8. `knowledge/01_table_index.md`：定位相关表；不要直接全量读取所有表文档。
9. 相关 `knowledge/tables/*.md`、`knowledge/temp_tables/*.md`、`knowledge/metrics/*.md`、`knowledge/dashboards/*.md`、`knowledge/joins/*.md`：只读取与当前 QuerySpec 相关的文件。
10. `knowledge/reverse_index/*.md`：仅在只知道字段、表、指标、raw SQL 或 debug 线索时读取，用于反向定位候选文档。
11. `knowledge/dashboard_web_profiles/README.md` 及对应快照：当问题涉及青橙自助 BI 页面上的筛选器、组件、字段 ID、下载按钮、刷新任务 ID、选择器漂移或前端结构排查时读取。
12. `knowledge/sql_patterns/dashboard_design_change_workflow.md`：仅在设计、diff、dry-run、受控筛选器变更或从 live profile 反查契约/源 SQL 时读取。
13. 其他 `knowledge/sql_patterns/*.md`：生成或修复 SQL 时按命中场景读取。

文件编码规则：

- 本 Skill 内所有 `SKILL.md`、`metadata.json`、`knowledge/**/*.md`、`resources/raw_sql/*`、`docs/**/*.md`、`scripts/*.py` 的读取和写入都必须按 UTF-8 处理。
- 在 PowerShell 中读取中文文件时必须显式设置 UTF-8 输出和读取编码，例如先执行 `$OutputEncoding=[Console]::OutputEncoding=[System.Text.Encoding]::UTF8`，再使用 `Get-Content -Encoding UTF8 -LiteralPath '<path>'` 或 `Select-String -Encoding UTF8`。
- 如果 PowerShell 输出出现乱码、问号、替换字符或疑似 mojibake，不得基于该输出抽取表名、字段、指标或写入知识库；必须用 UTF-8 重新读取源文件并核对中文内容。

封装边界：

- 只服务青橙项目部相关 SQL 和知识库维护。
- 不把本 Skill 当通用 SQL 生成器使用。
- 不加载、套用或推断市场顾问指标、评优/人产规则、范围、临时表、渠道 CASE、业务 join、看板或 raw SQL。
- 共享物理目录只能提供表名、字段、类型、分区、物理粒度和候选键；青橙范围、指标和 join 仍以本 Skill 文档为准。
- `semantic/contracts/` 只能引用本 Skill 的青橙文档或 Raw SQL；契约与来源 SHA-256 不一致时必须停止，不能用生成索引覆盖来源。
- 用户只说“顾问”时必须在 `qingcheng:dimension:section_consultant`（线索分配顾问）和 `qingcheng:dimension:performance_consultant`（业绩归属顾问）之间消歧；不得根据当前查询表静默猜测。
- 不脱离本 Skill 知识库编造表、字段、join key、临时表语义或指标口径。
- 青橙相关 Web BI 结构快照、README 索引和调试结论只写入本 Skill 的 `knowledge/dashboard_web_profiles/`，不得写回 `sql-query-writer-for-dashboard`。
- 青橙 `DashboardDesignSpec` 中的指标、维度、范围和公式依赖只能引用 `qingcheng:*` 的 `confirmed` contract ID 及其 `source_path`；不得因 live profile 出现同名字段而借用市场顾问口径。
- 看板 `dashboard_id` 必须已由本 Skill 的 `knowledge/dashboard_web_profiles/` 注册并通过源文件 Hash 回查；未注册或同时出现在另一域的看板只允许只读画像，先完成青橙知识同步和 catalog 重建再进入 Design。
- 本 Skill 只提供青橙业务设计约束，不保存看板登录态、不调用写接口。P3A 的组件/布局/公式/筛选器均可设计、diff 和 dry-run；P3B Apply 只允许 operator Registry 已验证的九类窄操作，并继续阻断泛化组件、筛选器、数据集、新建和删除修改。
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

## 3. QuerySpec 门禁

生成生产 SQL 前，先用 `semantic/domain_manifest.json` 确认域，再用 `semantic/generated/contract_index.json` 解析别名，只读取命中的 `semantic/contracts/*.json` 及其 `source_path`。然后通过 `scripts/text2sql.py` 构建 QuerySpec 和 QueryPlan。脚本参数以 `scripts/text2sql.py --help` 为准；不要绕过脚本自行把未决请求或 pending 契约标记为可执行。

QuerySpec 至少包含：

- `schema_version`：P2 使用 `2.0.0`；`domain` 必须为 `qingcheng`。
- `intent`、`metrics`、`dimensions`、`filters`、`time_range`。
- `metrics` 优先保存 `qingcheng:metric:*` ID、名称和青橙来源；维度必须解析为 `qingcheng:dimension:*` 契约。
- `business_scope` 与 `execution_mode`：区分生产范围和受限探索。
- `calculation_grain` 与 `output_grain`。
- `candidate_tables`、`join_path`。
- `evidence`：必须指向本 Skill 的 manifest、metrics、dashboards、tables、temp_tables、joins 或 raw SQL。
- `unresolved_slots`：记录未确认的业务域、指标版本、范围、时间、粒度、表、临时表或 join。

执行门禁：

- `domain` 未决或不是 `qingcheng` 时，不得生成青橙生产 SQL。
- `unresolved_slots` 含必填项时，只能输出待确认项或受限探索 SQL，不得交给 USQL 执行。
- 只有 `confirmed` 指标、维度、join 和范围契约可进入 QueryPlan；任一 `pending_confirmation` 必须进入 `unresolved_slots`。confirmed 指标仍须 `automatic_compile=true` 才能进入确定性编译，否则保留为人工 SQL 计划。
- 同名指标必须用 `domain + contract_id` 解析，不能借用市场顾问定义补齐。
- “顾问”同时命中线索分配顾问和业绩归属顾问时，必须要求补充语义或使用完整契约 ID；不得任选其一。
- 跨部门对比必须分别形成 `qingcheng` 与 `market_consultant` 两份 QuerySpec；各自校验、各自生成 SQL，在兼容粒度聚合后再比较。
- manifest 与现有 Markdown/Raw SQL 不一致时，停止并报告冲突；不得静默覆盖既有业务知识。

### P2 渐进披露与输出边界

按以下顺序推进，不得跳级加载或执行：

1. `domain_manifest`：只确认 `qingcheng` 域、候选实体和证据位置。
2. `contract_index`：解析指标、维度、join、范围别名并发现歧义；它不包含完整业务口径。
3. `contracts + source_path`：只读取命中的契约及对应青橙 Markdown/Raw SQL，核对状态、SHA-256、粒度、范围和风险。
4. `QuerySpec`：记录明确需求和未决槽位；pending 契约与歧义必须保留为未决。
5. `QueryPlan`：确定基础表、指标表达式、维度、过滤、范围、join、证据和可执行状态。
6. `compile`：仅对全部 confirmed、指标 `automatic_compile=true`、无未决槽位且单基础表的 QueryPlan 自动编译；复杂公式、多阶段聚合和多表 join 只输出计划并回到历史 SQL/Join 文档人工审阅。
7. `probe`：生成带具体分区和边界的只读探查 SQL，用于新鲜度、分布、重复键、粒度或 join 放大检查；生成探查 SQL 不等于授权 USQL 执行。

编译后的 SQL 仍须经过 AST、青橙平台规则和证据校验。任何执行或下载继续交给 `usql-web-query-operator`，本 Skill 不保存凭证、不管理登录态，也不直接执行 SQL。

### P3A/P3B 看板设计与变更边界

- 正向链路固定为 `QuerySpec -> QueryPlan -> DashboardDatasetSpec -> DashboardDesignSpec -> DashboardChangePlan -> dry-run`。DesignSpec 必须绑定本域 confirmed contract ID、`source_path`、QueryPlan/DatasetSpec hash 和基线 `DashboardProfile` hash。
- 反向链路固定为 `live DashboardProfile -> component/model/relation/filter/field identity -> 字段/公式 -> contract_index -> qingcheng contract -> source_path -> dashboard/metric/raw SQL`；无法唯一反查时保留 `unknown/ambiguous`。
- P3A 可覆盖 component、layout、formula、filter 的画像、设计、diff 与 dry-run，但不写平台。
- P3B 只把以下九类 `verified/allowlisted` 操作交给 `usql-web-query-operator`：`update_component_fields`、`update_component_filter_label`、`update_component_title`、`update_public_filter_title`、`update_tab_label`、`update_layout`、`update_formula`、`update_filter_dynamic_default`、`update_theme`。每类必须使用对应稳定 ID 且只改一个已验证槽位；字段增删/排序、筛选条件/值/关系、Tab 成员、跨容器移动、公式依赖、数据集重绑、新建和删除仍为 `blocked_unsupported`。
- Apply 只能写 draft，必须消费精确匹配的 ChangePlan/hash，写前后重新 profile；QueryPlan、DesignSpec 和 ChangePlan 都不构成写入或发布授权。同次 apply+publish 禁止，发布必须独立确认。
- 详细字段、风险和路由见 `knowledge/sql_patterns/dashboard_design_change_workflow.md`；业务请求不涉及看板设计/编辑时不要加载该文档。

## 4. SQL 生成流程

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
2. `semantic/domain_manifest.json`
3. `semantic/generated/contract_index.json`
4. 命中的单个 `semantic/contracts/*.json` 条目及其 `source_path`
5. `knowledge/quick_reference.md`
6. `knowledge/04_qingcheng_project_profile.md`
7. `knowledge/decision_tree.md`
8. `knowledge/01_table_index.md`
9. 相关 `knowledge/reverse_index/*.md`（字段、表、指标或 debug 反向定位场景）
10. 相关 `knowledge/tables/*.md`
11. 相关 `knowledge/temp_tables/*.md`
12. 相关 `knowledge/metrics/*.md`
13. 相关 `knowledge/dashboards/*.md`
14. `knowledge/dashboard_web_profiles/README.md` 及对应快照（仅当问题涉及 Web BI 前端结构时）
15. `knowledge/joins/*.md`
16. `knowledge/sql_patterns/*.md`
17. `knowledge/00_global_rules.md` 和 `knowledge/03_range_limit_rules.md`

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

- 检查 QuerySpec 的 `domain`、必填槽位和 evidence 是否均属于青橙项目部。
- 检查所有 contract ID 都以 `qingcheng:` 开头、来源哈希未漂移且状态为 `confirmed`；`pending_confirmation` 不得被编译。
- 检查“顾问”是否已明确为线索分配顾问或业绩归属顾问。
- 检查 QueryPlan 的基础表、计算粒度、输出粒度、范围和 join 风险是否与 QuerySpec 一致；多表 join 不得由 P2 单表编译器自动拼接。
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

可用脚本：`scripts/validate_sql_rules.py`。生成复杂 SQL 后，优先运行该脚本做规则校验。该检查器按 AST 中每个 `SELECT`/CTE 的物理表作用域核对 `dt`、`hour` 和部门/项目过滤；外层查询不得替代内层物理表过滤，`SELECT DISTINCT` 也不会与其他查询块的 `GROUP BY` 混检。

### E. 输出说明

每次输出 SQL 后，必须附带：

- QuerySpec 摘要与 domain
- 命中的 contract ID、状态和来源路径
- QueryPlan 状态；若不可执行，列出 unresolved slots 和阻断原因
- 查询目的
- 使用表
- 使用临时表
- 关键字段
- 分区条件
- 青橙范围限定条件
- 指标口径
- join 关系
- 证据路径
- 是否加了 `limit`
- 若生成 probe，说明探查种类、边界和需要人工解释的结果
- 待确认事项

## 5. 知识库维护流程

新增青橙看板 SQL：

1. 普通青橙专题 SQL 保存到 `resources/raw_sql/`，可使用 `qingcheng_<看板英文名或拼音>_<YYYYMMDD>.sql`；数据中心 SQL 例外，只允许稳定路径 `data_center_qingcheng_<model_id>.sql`。
2. 运行 `scripts/ingest_dashboard_sql.py --sql-file <path>` 生成 `knowledge/dashboards/`、`knowledge/metrics/` 和 `knowledge/temp_tables/` 的初始文档。
3. 人工核对自动解析结果，把“待人工确认”补齐为青橙真实口径。
4. 更新 `knowledge/01_table_index.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`。
5. 更新 `knowledge/update_log/changelog.md`，按时间正序追加在文件末尾。
6. 数据中心 current model 与语义槽位登记在 `semantic/current_model_bindings.json`；刷新必须通过 operator 的 `sync-data-center-sql` dry-run 获取精确计划哈希，再用 `--write --expected-plan-sha256 <hash>` 原子替换。禁止日期副本；Apply 后强制执行反向索引、共享 catalog、唯一版本审计、integrity 和完整栈验证，失败自动回滚。
7. 运行 `scripts/build_reverse_indexes.py` 刷新 `knowledge/reverse_index/`。
8. 若业务定义已明确且需要进入 P2 规划，更新对应 `semantic/contracts/*.json`，同步当前 `source_path` SHA-256；证据不足的契约只能标为 `pending_confirmation`。
9. 运行 `../scripts/build_text2sql_catalog.py` 重建结构化清单、`semantic/generated/contract_index.json` 和共享中性物理目录；`semantic/domain_manifest.json` 与 `semantic/generated/` 均为生成物，不手工编辑。
10. 人工核对 domain manifest、contract index、契约状态和来源引用；不得从市场顾问 manifest 或 contracts 复制业务语义。
11. 运行 `semantic/evals/resolution_cases.json` 的离线别名解析评测，确认已知别名、预期歧义和 unknown 用例均符合预期。
12. 使用 `scripts/text2sql.py` 校验 QuerySpec、QueryPlan、编译 SQL 或 probe，再运行 `scripts/check_skill_integrity.py`。

新增青橙临时表：

- 必须在 `knowledge/temp_tables/<库名.表名>.md` 中记录来源、刷新方式、字段含义、数据粒度、适用看板、有效期、和不可复用边界。
- 如果临时表只服务某个看板，不得在其他看板 SQL 中复用，除非用户明确确认。
- 如果临时表名称与其他部门临时表相似，必须写清楚不是同一口径。

新增表结构 PDF 或字段目录：

- 放入 `resources/raw_pdfs/` 或用户指定路径。
- 表结构入库时只写入本 Skill 的 `knowledge/tables/`。
- 不从其他 skill 自动复制表文档；若确实需要复用公共表结构，必须在更新日志中标明来源和核对结果。

新增或刷新青橙 Web BI 结构快照：

- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 或对应单看板/文件夹命令采集。
- 所有青橙快照、README 索引和相关说明只写入本 Skill 的 `knowledge/dashboard_web_profiles/`。
- 不得把 `青橙项目部` 文件夹下的结构快照写入 `sql-query-writer-for-dashboard`。
