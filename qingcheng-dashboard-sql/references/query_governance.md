# 青橙项目部查询约束

仅在生成、修复或审核本域生产 SQL / QueryPlan 时读取。与当前任务无关的看板或历史专项规则不触发额外工作。文中反引号路径相对本 Skill 根目录。

封装边界：

- 只服务青橙项目部相关 SQL 和知识库维护。
- 不把本 Skill 当通用 SQL 生成器使用。
- 不加载、套用或推断市场顾问指标、评优/人产规则、范围、临时表、渠道 CASE、业务 join、看板或 raw SQL。
- 共享物理目录只能提供表名、字段、类型、分区、物理粒度和候选键；青橙范围、指标和 join 仍以本 Skill 文档为准。
- `semantic/contracts/` 只能引用本 Skill 的青橙文档或 Raw SQL；契约与来源 SHA-256 不一致时必须停止，不能用生成索引覆盖来源。
- 用户只说“顾问”时必须在 `qingcheng:dimension:section_consultant`（线索分配顾问）和 `qingcheng:dimension:performance_consultant`（业绩归属顾问）之间消歧；不得根据当前查询表静默猜测。
- 不脱离本 Skill 知识库编造表、字段、join key、临时表语义或指标口径。
- 青橙相关 Web BI 结构快照、README 索引和调试结论只写入本 Skill 的 `knowledge/dashboard_web_profiles/`，不得写回 `market-consultant-dashboard-sql`。
- 青橙 `DashboardDesignSpec` 中的指标、维度、范围和公式依赖只能引用 `qingcheng:*` 的 `confirmed` contract ID 及其 `source_path`；不得因 live profile 出现同名字段而借用市场顾问口径。
- 看板 `dashboard_id` 必须已由本 Skill 的 `knowledge/dashboard_web_profiles/` 注册并通过源文件 Hash 回查；未注册或同时出现在另一域的看板只允许只读画像，先完成青橙知识同步和 catalog 重建再进入 Design。
- 本 Skill 只提供青橙业务设计约束，不保存看板登录态、不调用写接口。P3A 的组件/布局/公式/筛选器均可设计、diff 和 dry-run；P3B Apply 只允许 operator Registry 当前 verified/allowlisted 的窄操作，并继续阻断泛化组件、筛选器、数据集、新建和删除修改。
- 不在缺少 `dt`、必要 `hour`、部门/项目范围限定或必要 `limit` 时直接给出生产查询。
- 如果 SQL 或用户材料中出现市场顾问部、评优架构、参评名单、市场顾问专属临时表或市场顾问专属渠道 CASE，默认视为跨域污染；除非用户明确说明这是青橙也复用的逻辑，否则必须标注“待人工确认”，不得直接入库为青橙口径。
- 若用户只要求“给参考 SQL，不修改 Skill”，不得改写 `resources/raw_sql/` 或 `knowledge/`。

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

`plan` / `compile` 可用 `--trace-output` 生成不含问题原文、SQL 文本和结果行的 QueryTrace；执行时将同一路径交给 operator `run --trace-file`，由其追加 Policy 与 ResultArtifact Hash。Trace 不授权执行或下载。

编译后的 SQL 仍须经过 AST、青橙平台规则和证据校验。任何执行或下载继续交给 `usql-web-query-operator`，本 Skill 不保存凭证、不管理登录态，也不直接执行 SQL。

### P3A/P3B 看板设计与变更边界

- 正向链路固定为 `QuerySpec -> QueryPlan -> DashboardDatasetSpec -> DashboardDesignSpec -> DashboardChangePlan -> dry-run`。DesignSpec 必须绑定本域 confirmed contract ID、`source_path`、QueryPlan/DatasetSpec hash 和基线 `DashboardProfile` hash。
- 反向链路固定为 `live DashboardProfile -> component/model/relation/filter/field identity -> 字段/公式 -> contract_index -> qingcheng contract -> source_path -> dashboard/metric/raw SQL`；无法唯一反查时保留 `unknown/ambiguous`。
- P3A 可覆盖 component、layout、formula、filter 的画像、设计、diff 与 dry-run，但不写平台。
- P3B 以 operator 的 [dashboard_write_capabilities.json](../../usql-web-query-operator/references/dashboard_write_capabilities.json) 为能力来源；只允许当前 `verified/allowlisted` 且满足稳定身份、单槽位和依赖约束的操作。数据集重绑、泛化创建/删除、跨容器移动或未验证操作仍为 `blocked_unsupported`，不维护另一份操作枚举。
- Apply 只能写 draft，必须消费精确匹配的 ChangePlan/hash，写前后重新 profile；QueryPlan、DesignSpec 和 ChangePlan 都不构成写入或发布授权。同次 apply+publish 禁止，发布必须独立确认。
- 详细字段、风险和路由见 `knowledge/sql_patterns/dashboard_design_change_workflow.md`；业务请求不涉及看板设计/编辑时不要加载该文档。
