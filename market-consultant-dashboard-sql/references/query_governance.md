# 市场顾问部查询约束

仅在生成、修复或审核本域生产 SQL / QueryPlan 时读取。与当前任务无关的看板或历史专项规则不触发额外工作。文中反引号路径相对本 Skill 根目录。

封装边界：

- 只服务市场顾问部业务 SQL 和知识维护，不把本 Skill 当通用 SQL 生成器使用。
- 不加载、套用或推断青橙指标、范围、临时表、渠道/期次映射、业务 join、看板或 raw SQL。
- 共享物理目录只能提供表名、字段、类型、分区、物理粒度和候选键；市场顾问范围、指标和 join 仍以本 Skill 文档为准。
- 市场顾问 `DashboardDesignSpec` 中的指标、维度、范围和公式依赖只能引用 `market_consultant:*` 的 `confirmed` contract ID 及其 `source_path`；不得因 live profile 出现同名字段而借用青橙口径。
- 看板 `dashboard_id` 必须已由本 Skill 的 `knowledge/dashboard_web_profiles/` 注册并通过源文件 Hash 回查；未注册或同时出现在另一域的看板只允许只读画像，先完成市场顾问知识同步和 catalog 重建再进入 Design。
- 本 Skill 只提供市场顾问业务设计约束，不保存看板登录态、不调用写接口。P3A 的组件/布局/公式/筛选器均可设计、diff 和 dry-run；P3B Apply 只允许 operator Registry 当前 verified/allowlisted 的窄操作，并继续阻断泛化组件、筛选器、数据集、新建和删除修改。
- 不脱离知识库编造表、字段、join key 或指标口径。
- 不在缺少 `dt`、`hour`、部门范围限定或必要 `limit` 时直接给出生产查询。
- `confirmed` contract 只有在当前 QuerySpec 同时满足时间、范围、粒度、证据和 Join 门禁后才能进入 QueryPlan；`pending_confirmation` contract 只能用于候选解释、定向取证或只读 Probe，不得编译生产 SQL。
- 只编译 `status=executable` 且 `unresolved_slots=[]` 的 QueryPlan。P2 确定性编译只覆盖 `automatic_compile=true`、单基础表的已注册指标和维度；复杂公式、多阶段聚合与多表看板仍须受 QueryPlan 约束并定向读取业务 SQL，不能伪装成自动编译覆盖。
- 复杂 SQL 或 SQL 修复后，先运行 `scripts/text2sql.py validate-sql` 做 Presto AST、QuerySpec 与域边界校验，再运行 `scripts/validate_sql_rules.py` 补充平台专属规则；结构与知识维护按 [仓库维护验证](../../references/maintenance-verification.md) 选择受影响检查。
- 若用户只要求“给参考 SQL，不修改 Skill”，不得改写 `resources/raw_sql/` 或 `knowledge/`。
- 生成排名、比率、目标、差值等非明细粒度指标时，必须先声明“指标计算粒度”和“最终输出粒度”。如果两者不一致，例如指标按 `期次-部门-顾问` 排名而最终输出为 `日-期次-部门-顾问`，必须提示前端聚合风险，并优先给出期次粒度最终查询或 `*_once` 防重复字段方案。
- `temp_table.zhangjunyan01_pingyou_jg` 只在用户明确要求“评优/参评名单/评优架构/人产”口径时使用。该表含 `qici`，join 后会把结果限制在该临时表已维护期次内；如果最新期次缺失，不得默认用它过滤最新数据。
- 当用户不要求严格评优参评名单、只需要市场顾问在职架构范围时，可考虑用 `temp_table.dingxi01_jiagou_zx` 作为顾问名单替代来源。使用时必须限定 `cast(zaizhi as varchar) = '1'`、`department in ('郑州顾问部', '西安一部', '西安二部')`，并用 `row_number()` 按 `employee_email_name` 去重，同时说明口径由“参评顾问”变为“在职架构顾问”。
- 排查“某期次/经理/顾问查不到”时，先判断 SQL 是事实主表驱动还是名单/架构表驱动；临时架构表有目标期次不代表事实主表已经产出该期数据。详细流程参考 `knowledge/sql_patterns/dashboard_query_patterns.md` 的“结果缺失与未来期次排查”。

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

生成生产 SQL 前，按 ID / 别名通过 `semantic/generated/contract_index.json -> semantic/contracts/*.json -> source_path` 定向取证，需要候选实体时再读 manifest，再用 `scripts/text2sql.py` 构建并校验 QuerySpec。脚本参数和子命令以 `scripts/text2sql.py --help` 为准；不要绕过脚本自行把未决请求标记为可执行。

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
- `plan` / `compile` 可用 `--trace-output` 生成不含问题原文、SQL 文本和结果行的 QueryTrace；执行时将同一路径交给 operator `run --trace-file`，由其追加 Policy 与 ResultArtifact Hash。Trace 不授权执行或下载。
- `probe` 只验证分区新鲜度、字段分布、候选键重复和 Join 基数等物理事实；必须使用具体且有界的分区范围。Probe 结果不得自动升级 contract 状态或改写业务口径。
- 看板设计先从可执行 QueryPlan 派生 `DashboardDatasetSpec`；P3 再生成域内 `DashboardDesignSpec` 与 `DashboardChangePlan`，但任何工件都不授权平台写入。
- 完整分支和门禁见 `references/quick_reference.md` 与 `references/decision_tree.md`。

### P3A/P3B 看板设计与变更边界

- 正向链路固定为 `QuerySpec -> QueryPlan -> DashboardDatasetSpec -> DashboardDesignSpec -> DashboardChangePlan -> dry-run`。DesignSpec 必须绑定本域 confirmed contract ID、`source_path`、QueryPlan/DatasetSpec hash 和基线 `DashboardProfile` hash。
- 反向链路固定为 `live DashboardProfile -> component/model/relation/filter/field identity -> 字段/公式 -> contract_index -> market_consultant contract -> source_path -> dashboard/metric/raw SQL`；无法唯一反查时保留 `unknown/ambiguous`。
- P3A 可覆盖 component、layout、formula、filter 的画像、设计、diff 与 dry-run，但不写平台。
- P3B 以 operator 的 [dashboard_write_capabilities.json](../../usql-web-query-operator/references/dashboard_write_capabilities.json) 为能力来源；只允许当前 `verified/allowlisted` 且满足稳定身份、单槽位和依赖约束的操作。数据集重绑、泛化创建/删除、跨容器移动或未验证操作仍为 `blocked_unsupported`，不维护另一份操作枚举。
- Apply 只能写 draft，必须消费精确匹配的 ChangePlan/hash，写前后重新 profile；QueryPlan、DesignSpec 和 ChangePlan 都不构成写入或发布授权。同次 apply+publish 禁止，发布必须独立确认。
- 详细字段、风险和路由见 `knowledge/sql_patterns/dashboard_design_change_workflow.md`；业务请求不涉及看板设计/编辑时不要加载该文档。
