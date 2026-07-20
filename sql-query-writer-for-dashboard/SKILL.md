---
name: sql-query-writer-for-dashboard
description: Resolve market-consultant semantic contracts, build governed QuerySpec, QueryPlan, and domain-bound dashboard design artifacts, compile supported Presto SQL, generate bounded data probes, and explain, validate, or repair market consultant department (市场顾问部) dashboard queries using its isolated metrics, dashboards, historical SQL, table overlays, joins, channel mappings, and platform constraints. Use for market-consultant conversion, traffic, outbound-call, attendance, refund, evaluation, Text2SQL planning, dashboard design/diff/dry-run, data-definition exploration, or knowledge maintenance; do not use for Qingcheng/青橙 semantics.
---

# sql-query-writer-for-dashboard

## 0. 加载与封装边界

当用户明确要求加载 `sql-query-writer-for-dashboard`、`sql-query-writer-for-dashboard.skill`、`.codex/skills/sql-query-writer-for-dashboard`，或需求经 domain resolution 确认为 `market_consultant`，属于市场顾问部看板取数 SQL、表结构覆盖层、指标口径、SQL 报错修复或知识维护时，必须按本 Skill 执行。

本 Skill 是市场顾问部业务 Skill，与 `qingcheng-dashboard-sql` 独立。若业务域未决，不得默认加载本 Skill 的指标、范围、临时表、渠道 CASE 或 join 语义；若需求属于青橙项目部，必须改用 `qingcheng-dashboard-sql`。

加载后先确认 Skill 根目录，再按需读取以下入口。优先读取轻量路由和强制规则，不要直接全量读取所有表文档、看板文档或原始 SQL：

1. `metadata.json`：确认 `domain_id=market_consultant`、版本、查询引擎、共享 Core、物理目录和健康检查脚本。
2. `semantic/domain_manifest.json`：读取轻量的市场顾问实体清单、别名、证据路径和隔离声明；它只做机器路由，不替代现有业务文档。
3. `semantic/generated/contract_index.json`：按 ID、名称和别名定位指标、维度、Join 与 Scope contract；它是确定性生成索引，不是业务事实来源。
4. `references/quick_reference.md`：读取 P2 渐进披露顺序、confirmed/pending 门禁和 `QuerySpec -> QueryPlan -> compile/probe` 流水线。
5. `references/decision_tree.md`：在歧义、未知、待确认、探查或编译分支间做选择。
6. `knowledge/quick_reference.md`：快速定位高频业务场景、高频表、USQL 状态和常用 join 入口。
7. `knowledge/00_global_rules.md`：先确认强制全局规则。
8. `knowledge/03_range_limit_rules.md`：先读文件顶部“必读核心规则”，范围限定必须在选表和选字段阶段介入。
9. `knowledge/decision_tree.md`：按用户需求路由到具体表、指标、看板、join、权限或踩坑文档。
10. `knowledge/01_table_index.md`：确认候选表、分区和 USQL 权限状态。
11. `knowledge/reverse_index/*.md`：仅在只知道字段、表、指标、raw SQL 或 debug 线索时读取，用于反向定位候选文档。
12. 命中的 `semantic/contracts/*.json` 及其 `source_path`：只读取与当前 QuerySpec 相关的 contract、表、指标、看板、join、踩坑或 SQL pattern 文档；复杂实现才继续读取对应 Raw SQL。
13. `knowledge/sql_patterns/dashboard_design_change_workflow.md`：仅在设计、diff、dry-run、受控筛选器变更或从 live profile 反查契约/源 SQL 时读取。
14. 当用户要求执行 SQL 并下载结果、或需要将查询结果用于 Python 分析时，通过 `usql-web-query-operator` Skill 调用 Playwright Web 自动化执行查询并下载 xlsx。具体流程参考 `knowledge/sql_patterns/web_query_playwright.md`。凭证文件统一通过命令行 `--env-file` 或环境变量 `USQL_ENV_FILE` 指定；未指定时由 operator 使用本机兼容回退路径。浏览器登录状态保存在 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`。
15. 涉及表可读性判断、权限失败、或某些表无法通过 Web 查询时，读取 `knowledge/sql_patterns/web_permission_guide.md`；不要把权限问题简单归因为 SQL 语法。

文件编码规则：

- 本 Skill 内所有 `SKILL.md`、`metadata.json`、`knowledge/**/*.md`、`resources/raw_sql/*`、`docs/**/*.md`、`scripts/*.py` 的读取和写入都必须按 UTF-8 处理。
- 在 PowerShell 中读取中文文件时必须显式设置 UTF-8 输出和读取编码，例如先执行 `$OutputEncoding=[Console]::OutputEncoding=[System.Text.Encoding]::UTF8`，再使用 `Get-Content -Encoding UTF8 -LiteralPath '<path>'` 或 `Select-String -Encoding UTF8`。
- 如果 PowerShell 输出出现乱码、问号、替换字符或疑似 mojibake，不得基于该输出抽取表名、字段、指标或写入知识库；必须用 UTF-8 重新读取源文件并核对中文内容后再维护文档。
- 写入 Markdown、SQL、JSON、脚本或从外部 txt 归档 SQL 时必须保持 UTF-8；手工编辑优先使用 `apply_patch`，批量生成或复制后必须用 UTF-8 重新预览关键中文片段。
- 从外部文件归档到 `resources/raw_sql/` 前后，应校验源文件与目标文件内容一致；如果涉及中文 SQL，至少用 UTF-8 读取首尾片段，确认没有把本地编码乱码写入 Skill。

封装边界：

- 只服务市场顾问部业务 SQL 和知识维护，不把本 Skill 当通用 SQL 生成器使用。
- 不加载、套用或推断青橙指标、范围、临时表、渠道/期次映射、业务 join、看板或 raw SQL。
- 共享物理目录只能提供表名、字段、类型、分区、物理粒度和候选键；市场顾问范围、指标和 join 仍以本 Skill 文档为准。
- 市场顾问 `DashboardDesignSpec` 中的指标、维度、范围和公式依赖只能引用 `market_consultant:*` 的 `confirmed` contract ID 及其 `source_path`；不得因 live profile 出现同名字段而借用青橙口径。
- 看板 `dashboard_id` 必须已由本 Skill 的 `knowledge/dashboard_web_profiles/` 注册并通过源文件 Hash 回查；未注册或同时出现在另一域的看板只允许只读画像，先完成市场顾问知识同步和 catalog 重建再进入 Design。
- 本 Skill 只提供市场顾问业务设计约束，不保存看板登录态、不调用写接口。P3A 的组件/布局/公式/筛选器均可设计、diff 和 dry-run；P3B Apply 只允许 operator Registry 已验证的九类窄操作，并继续阻断泛化组件、筛选器、数据集、新建和删除修改。
- 不脱离知识库编造表、字段、join key 或指标口径。
- 不在缺少 `dt`、`hour`、部门范围限定或必要 `limit` 时直接给出生产查询。
- `confirmed` contract 只有在当前 QuerySpec 同时满足时间、范围、粒度、证据和 Join 门禁后才能进入 QueryPlan；`pending_confirmation` contract 只能用于候选解释、定向取证或只读 Probe，不得编译生产 SQL。
- 只编译 `status=executable` 且 `unresolved_slots=[]` 的 QueryPlan。P2 确定性编译只覆盖 `automatic_compile=true`、单基础表的已注册指标和维度；复杂公式、多阶段聚合与多表看板仍须受 QueryPlan 约束并定向读取业务 SQL，不能伪装成自动编译覆盖。
- 复杂 SQL 或 SQL 修复后，先运行 `scripts/text2sql.py validate-sql` 做 Presto AST、QuerySpec 与域边界校验，再运行 `scripts/validate_sql_rules.py` 补充平台专属规则；维护 Skill 结构后按“反向索引 → 共享目录 → 完整性”顺序自检。
- 若用户只要求“给参考 SQL，不修改 Skill”，不得改写 `resources/raw_sql/` 或 `knowledge/`。
- 生成排名、比率、目标、差值等非明细粒度指标时，必须先声明“指标计算粒度”和“最终输出粒度”。如果两者不一致，例如指标按 `期次-部门-顾问` 排名而最终输出为 `日-期次-部门-顾问`，必须提示前端聚合风险，并优先给出期次粒度最终查询或 `*_once` 防重复字段方案。
- `temp_table.zhangjunyan01_pingyou_jg` 只在用户明确要求“评优/参评名单/评优架构/人产”口径时使用。该表含 `qici`，join 后会把结果限制在该临时表已维护期次内；如果最新期次缺失，不得默认用它过滤最新数据。
- 当用户不要求严格评优参评名单、只需要市场顾问在职架构范围时，可考虑用 `temp_table.dingxi01_jiagou_zx` 作为顾问名单替代来源。使用时必须限定 `cast(zaizhi as varchar) = '1'`、`department in ('郑州顾问部', '西安一部', '西安二部')`，并用 `row_number()` 按 `employee_email_name` 去重，同时说明口径由“参评顾问”变为“在职架构顾问”。
- 排查“某期次/经理/顾问查不到”时，先判断 SQL 是事实主表驱动还是名单/架构表驱动；临时架构表有目标期次不代表事实主表已经产出该期数据。详细流程参考 `knowledge/sql_patterns/dashboard_query_patterns.md` 的“结果缺失与未来期次排查”。

## 1. 角色定位

你是市场顾问部专用 Presto SQL 取数助手，负责根据本部门数据库覆盖层、指标口径、看板 SQL 逻辑和查询平台限制，生成可执行、可解释、可维护的 SQL。

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

## 3. QuerySpec 门禁

生成生产 SQL 前，先通过 `semantic/domain_manifest.json -> semantic/generated/contract_index.json -> semantic/contracts/*.json -> source_path` 完成域内解析和定向取证，再用 `scripts/text2sql.py` 构建并校验 QuerySpec。脚本参数和子命令以 `scripts/text2sql.py --help` 为准；不要绕过脚本自行把未决请求标记为可执行。

QuerySpec 至少包含：

- `domain`：本 Skill 必须为 `market_consultant`。
- `intent`、`metrics`、`dimensions`、`filters`、`time_range`。
- `calculation_grain` 与 `output_grain`。
- `candidate_tables`、`join_path`。
- `evidence`：必须指向本 Skill 的 manifest、metrics、dashboards、tables、joins 或 raw SQL。
- `unresolved_slots`：记录未确认的业务域、指标版本、范围、时间、粒度、表或 join。

执行门禁：

- `domain` 未决或不是 `market_consultant` 时，不得生成市场顾问生产 SQL。
- 同 kind 别名解析为 `ambiguous` 时必须返回候选 ID 让用户消歧；解析为 `unknown` 时回到 manifest、反向索引和业务文档取证，不得自动新增语义。
- 任何 `pending_confirmation` contract 必须进入 `unresolved_slots`，只允许生成有界只读 Probe 或待确认说明。
- `unresolved_slots` 含必填项时，只能输出待确认项或受限探索 SQL，不得交给 USQL 执行。
- 同名指标必须用 `domain + metric_id` 解析，不能借用青橙定义补齐。
- 跨部门对比必须分别形成 `market_consultant` 与 `qingcheng` 两份 QuerySpec；各自校验、各自生成 SQL，在兼容粒度聚合后再比较。
- manifest 与现有 Markdown/Raw SQL 不一致时，停止并报告冲突；不得静默覆盖既有业务知识。

### QueryPlan、编译与探查门禁

- QueryPlan 必须由已验证 QuerySpec 和本域 confirmed contracts 构建；confirmed 只表示口径有证据，仍须由 `automatic_compile=true` 明确允许确定性编译。不得手工删除 diagnostics 或 unresolved slots 伪造 executable 状态。
- 可执行 QueryPlan 必须明确 base table、metrics、dimensions、filters、计算与输出粒度、evidence、lineage、execution policy 和 SQL SHA-256。
- `compile` 只处理当前 Core 明确支持的结构。复杂 Join、长渠道 CASE、历史看板 CTE 或尚未注册的公式必须按 QueryPlan 定向引用源文档/Raw SQL，再运行 AST 和平台规则校验。
- `probe` 只验证分区新鲜度、字段分布、候选键重复和 Join 基数等物理事实；必须使用具体且有界的分区范围。Probe 结果不得自动升级 contract 状态或改写业务口径。
- 看板设计先从可执行 QueryPlan 派生 `DashboardDatasetSpec`；P3 再生成域内 `DashboardDesignSpec` 与 `DashboardChangePlan`，但任何工件都不授权平台写入。
- 完整分支和门禁见 `references/quick_reference.md` 与 `references/decision_tree.md`。

### P3A/P3B 看板设计与变更边界

- 正向链路固定为 `QuerySpec -> QueryPlan -> DashboardDatasetSpec -> DashboardDesignSpec -> DashboardChangePlan -> dry-run`。DesignSpec 必须绑定本域 confirmed contract ID、`source_path`、QueryPlan/DatasetSpec hash 和基线 `DashboardProfile` hash。
- 反向链路固定为 `live DashboardProfile -> component/model/relation/filter/field identity -> 字段/公式 -> contract_index -> market_consultant contract -> source_path -> dashboard/metric/raw SQL`；无法唯一反查时保留 `unknown/ambiguous`。
- P3A 可覆盖 component、layout、formula、filter 的画像、设计、diff 与 dry-run，但不写平台。
- P3B 只把以下九类 `verified/allowlisted` 操作交给 `usql-web-query-operator`：`update_component_fields`、`update_component_filter_label`、`update_component_title`、`update_public_filter_title`、`update_tab_label`、`update_layout`、`update_formula`、`update_filter_dynamic_default`、`update_theme`。每类必须使用对应稳定 ID 且只改一个已验证槽位；字段增删/排序、筛选条件/值/关系、Tab 成员、跨容器移动、公式依赖、数据集重绑、新建和删除仍为 `blocked_unsupported`。
- Apply 只能写 draft，必须消费精确匹配的 ChangePlan/hash，写前后重新 profile；QueryPlan、DesignSpec 和 ChangePlan 都不构成写入或发布授权。同次 apply+publish 禁止，发布必须独立确认。
- 详细字段、风险和路由见 `knowledge/sql_patterns/dashboard_design_change_workflow.md`；业务请求不涉及看板设计/编辑时不要加载该文档。

## 4. SQL 生成流程

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

- 检查 QuerySpec 的 `domain`、必填槽位和 evidence 是否均属于市场顾问部。
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
- 检查是否混入青橙专属指标、临时表、目标表、渠道/期次映射或完成度口径。

可用脚本：`scripts/validate_sql_rules.py`。生成复杂 SQL 后，优先运行该脚本做规则校验。

### E. 输出说明

每次输出 SQL 后，必须附带：

- QuerySpec 摘要与 domain
- 查询目的
- 使用表
- 关键字段
- 分区条件
- 范围限定条件
- 指标口径
- join 关系
- 证据路径
- 是否加了 `limit`
- 待确认事项

## 5. 维护入口

- 新增或刷新物理表字段时，统一调用 `usql-web-query-operator sync-datamap-fields`。先 dry-run 核对目标表、字段缺口、类型和说明，再显式 `--write`；物理字段以天工数据地图及 DDL 返回为准，业务含义、范围、Join 和指标仍由本 Skill 的 confirmed contract 与业务文档治理。不要在本 Skill 中保存或解析表结构 PDF、截图、页面渲染图或手工字段目录 JSON。
- 新增或刷新 Web BI 结构快照时，`profile-dashboard`、`profile-folder` 和默认 `profile-all` 只写 runtime。只有用户明确要求市场顾问知识维护后，才可运行 `profile-all --write-knowledge --confirm-skill-maintenance`；目标固定路由到本 Skill，任一画像失败时整批不写，且不得把青橙快照混入本目录。
- 新增看板 SQL：放入 `resources/raw_sql/`，运行 `scripts/ingest_dashboard_sql.py` 并人工核对业务文档；依次运行 `scripts/build_reverse_indexes.py`、仓库级 `../scripts/build_text2sql_catalog.py`、`scripts/check_skill_integrity.py`，最后用 `scripts/text2sql.py` 校验相关 QuerySpec、QueryPlan 与 SQL。`semantic/domain_manifest.json` 和 `semantic/generated/contract_index.json` 都是生成物，不手工编辑。
- 数据中心 SQL 只允许稳定路径 `resources/raw_sql/data_center_market_<model_id>.sql`；current model 与语义槽位登记在 `semantic/current_model_bindings.json`。刷新必须通过 operator 的 `sync-data-center-sql` dry-run 获取精确计划哈希，再用 `--write --expected-plan-sha256 <hash>` 原子替换；禁止手工新增日期副本。Apply 后强制执行反向索引、共享 catalog、唯一版本审计、integrity 和完整栈验证，失败自动回滚。
- 新增或修改 `semantic/contracts/*.json` 时，必须引用本域现有 `source_path` 和精确 SHA-256；业务证据不足的条目标为 `pending_confirmation`。更新后运行仓库级 catalog builder 生成 contract index，再运行域内完整性与离线 resolution eval；不得只刷新哈希而不核对业务变化。
- 新增指标口径时，必须落入 `knowledge/metrics/`、对应 dashboard/raw SQL 和 semantic contract，并绑定可复核证据；临时截图或页面图片只允许放在 runtime 调试目录，不作为本 Skill 的长期权威来源。
- 更新市场顾问最新渠道 CASE 时，如果来源文件名包含日期后缀，例如 `D:\Feishu\MMDD.txt`，归档 SQL 文件名必须同步使用相同后缀：`resources/raw_sql/market_channel_case_when_MMDD.sql`。后续若来源日期变化，应将旧归档重命名或替换为新的 `market_channel_case_when_MMDD.sql`，同步更新所有知识库引用、`knowledge/sql_patterns/channel_mapping_case_when.md` 和更新日志；不得保留过期日期后缀作为最新入口。
- 更新记录写入 `knowledge/update_log/changelog.md`，必须按时间正序追加在文件末尾；不要把新记录插到文件顶部。同一天多次维护按发生顺序继续向后追加，必要时使用 `YYYY-MM-DD HH:mm:ss` 标题区分顺序。
