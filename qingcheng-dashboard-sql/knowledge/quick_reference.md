# 快速参考卡

> 80% 高频青橙取数入口。只用于快速定位，生成 SQL 前仍需读取对应表、指标、看板、join、范围或反向索引文档。

## Text2SQL 最短路径

1. 先确认业务域必须为 `qingcheng`；若业务域未决或属于市场顾问部，停止使用本卡，不能默认套用青橙口径。
2. 读取 `semantic/domain_manifest.json` 定位候选实体和证据位置，再读取 `semantic/generated/contract_index.json` 解析指标、维度、join 与范围别名。
3. 只打开命中的 `semantic/contracts/*.json` 条目及其 `source_path`；`confirmed` 可进入规划，`pending_confirmation` 必须进入待确认项。
4. 若用户只说“顾问”，必须区分 `qingcheng:dimension:section_consultant`（线索分配顾问）与 `qingcheng:dimension:performance_consultant`（业绩归属顾问），不能默认选一个。
5. 使用 `scripts/text2sql.py` 构建并校验 QuerySpec 2.0；至少明确指标契约、维度、过滤、业务范围、时间、计算粒度、输出粒度、候选表、join path、evidence 和 unresolved slots。
6. 从 QuerySpec 生成 QueryPlan，检查基础表、指标表达式、范围、join 风险和 `executable` 状态。
7. 仅对全部 confirmed、无未决槽位且单基础表的 QueryPlan 使用 `compile`；多表 join 回到青橙历史 SQL 和 join 文档人工审阅。
8. 使用 `probe` 生成新鲜度、分布、重复键或 join 风险的有界只读 SQL；probe 不是执行授权，实际运行仍交给 USQL operator。
9. 只读取本卡或 `knowledge/decision_tree.md` 路由出的具体文档；不要全量加载知识库。共享物理目录只能补充中性物理事实。

跨部门对比必须另建一份 `market_consultant` QuerySpec；两边各用各自证据生成并校验 SQL，只在兼容聚合粒度上合并结果。

### P3 看板设计最短路径

1. 先读取最新 `DashboardProfile`，确认 dashboard/draft、组件、模型、relation/filter/field identity 和 profile hash。
2. 按 `QuerySpec -> QueryPlan -> DashboardDatasetSpec -> DashboardDesignSpec` 正向生成青橙设计；每个指标、维度、范围和公式依赖必须携带 `qingcheng:*` confirmed contract ID 与 `source_path`。
3. 使用 `DashboardDesignSpec + DashboardProfile` 生成 `DashboardChangePlan`，依次执行 `design-dashboard -> plan-dashboard-change`；后者默认 dry-run，不调用写接口。
4. component、layout、formula、filter 均可做 P3A 画像、设计、diff 和 dry-run。P3B 只允许 `update_filter_dynamic_default`，且必须稳定定位 `relation_id + filter_id + field_id`；计划含任一 blocked operation 时整次 Apply 零写入。
5. Apply 仅由 operator 的 `apply-dashboard-change` 写 draft；发布必须另用 `publish-dashboard-change --confirm-publish`，消费成功 ApplyReceipt 并校验最新草稿 profile hash。
6. 完整门禁和反向路由见 `knowledge/sql_patterns/dashboard_design_change_workflow.md`；普通 SQL 任务不要加载该文档。

### P2 状态速查

| 状态/场景 | 允许动作 | 禁止动作 |
|---|---|---|
| 单一 `confirmed` 契约命中 | 读取契约来源，构建 QuerySpec 和 QueryPlan | 跳过来源文档直接把 contract index 当口径正文 |
| `pending_confirmation` 契约命中 | 输出待确认项；生成有界 probe 或人工 SQL 计划 | 标记 QueryPlan 可执行、自动 compile 或交给 USQL |
| 同一别名命中多个契约 | 保留 `ambiguous`，要求补充业务语义 | 按表名、历史习惯或另一业务域自动选取 |
| confirmed 且 `automatic_compile=true` 的单表 QueryPlan | compile 后继续做 AST 与青橙规则校验 | 把 confirmed 或编译成功等同于业务正确或执行授权 |
| 一级渠道/二级渠道/`channel_map_1`/`channel_map_2` | 读取 `semantic/contracts/dimension_contracts.json`、`knowledge/sql_patterns/qingcheng_channel_grade_mapping.md` 与 2064 权威 SQL | 使用青橙过程渠道派生维度；不要退回原始 `channel_name_2`，抖音正价退费必须在两级都输出抖音复用；`私域本地化` 从 20260722 期起才归 `本地化` |
| 多表 join QueryPlan | 读取 `knowledge/joins/`、对应 Raw SQL 和风险索引，人工审阅 | 让 P2 单表编译器自动拼 join |

### P3 状态速查

| 状态/对象 | 允许动作 | 禁止动作 |
|---|---|---|
| component / layout / formula / filter | profile、DesignSpec、结构化 diff、dry-run | 把设计成功视为平台写入授权 |
| 已有公共筛选器动态默认项，稳定 identity 完整 | 生成 `update_filter_dynamic_default` 并交 operator dry-run/显式 Apply | 用筛选器序号或显示名定位 |
| 组件字段、布局、公式、数据集重绑、新建/删除 | 保留完整 diff，标记 `blocked_unsupported` | 调用未知写接口或部分执行计划 |
| profile hash 漂移、契约待确认或跨域依赖 | 重新 profile、回到青橙 contract/source 取证 | 继续 Apply 或借市场顾问口径补齐 |

## 高频看板入口

| 用户需求 | 先读 | 再读 | 关键风险 |
|---|---|---|---|
| 青橙过程数据、有效线索、外呼、APP 登录 | `knowledge/dashboards/qingcheng_process_data_raw_20260522.md` | `knowledge/metrics/qingcheng_process_data_metrics.md`、`knowledge/joins/table_relationships.md` | 外呼和 APP 登录补充可能按用户粒度放大线索 |
| 青橙到课、第 1-6 讲到课、有效到课 | `knowledge/dashboards/qingcheng_daoke_raw_20260522.md` | `knowledge/metrics/qingcheng_daoke_metrics.md`、`knowledge/temp_tables/temp_table.dingxi01_qing_daoke.md` | 课次映射表唯一性和渠道/年级/开课时间匹配待确认 |
| 青橙转化、青橙订单、净营收、破单、暑期期次 | `knowledge/dashboards/qingcheng_conversion_raw_20260626.md` | `knowledge/metrics/qingcheng_conversion_metrics.md`、`knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`、`knowledge/sql_patterns/qingcheng_summer_qici_corrections.md` | 业务日历优先于固定周五；service 调课调班链路剔除；团队架构按 `employee_email_name + qici` 回填 |
| 青橙渠道订单明细 / 算绩效明细模板 | `knowledge/dashboards/qingcheng_channel_order_detail_raw_20260627.md` | `knowledge/metrics/qingcheng_channel_order_detail_metrics.md`、`knowledge/joins/table_relationships.md` | `ld` 子查询范围限定、`lead_id + employee` 唯一性以及地域字段扩列同步待确认 |
| 青橙年季月营收 | `knowledge/dashboards/qingcheng_revenue_year_quarter_month_raw_20260522.md` | `knowledge/metrics/qingcheng_revenue_year_quarter_month_metrics.md`、`knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md` | 组织链姓名匹配、调课调班去重和平台函数风险 |
| 青橙团队完成度月/期 | `knowledge/dashboards/qingcheng_team_completion_month_raw_20260522.md` 或 `knowledge/dashboards/qingcheng_team_completion_period_raw_20260522.md` | 对应 metrics、`knowledge/sql_patterns/qingcheng_completion_sql_repair_checklist.md`、`knowledge/temp_tables/temp_table.dingxi01_qing_team_goal.md`、`knowledge/temp_tables/temp_table.dingxi01_qing_team_g_qi.md` | `order_attr.original_paid_time`、`service transfer` 兜底识别内部调课调班、`team_hist` 兜底、`qtg.qici = wa.qici`、只剔除调课调班流水本身 |
| 青橙个人转化、个人完成度、折算后产出 | `knowledge/dashboards/qingcheng_personal_conversion_raw_20260522.md` | `knowledge/metrics/qingcheng_personal_conversion_metrics.md`、`knowledge/sql_patterns/qingcheng_personal_completion_discounted_output_risks.md`、`knowledge/sql_patterns/qingcheng_completion_sql_repair_checklist.md`、`knowledge/temp_tables/temp_table.dingxi01_qing_team_jg.md` | 课程部门空值兜底、调课调班聚合粒度、service transfer 兜底识别、原始支付时间归属、非 H 全量 50% 折算 |
| 青橙转化宽表-市场渠道 | `knowledge/dashboards/qingcheng_conversion_wide_table_market_channel_20260611.md` | `knowledge/metrics/qingcheng_conversion_wide_table_market_channel_metrics.md`、`knowledge/temp_tables/temp_table.shenbaoxin_channel_group.md` | 大 CASE 顺序、F 类外呼 join 语义和渠道分组唯一性待确认 |
| 青橙看板前端指标公式、字段配置、公式与 SQL 联动 | `knowledge/dashboard_web_profiles/edit_metrics/README.md` | `knowledge/metrics/qingcheng_dashboard_metric_formula_linkage.md`、`knowledge/dashboards/data_center_qingcheng_datasets.md` | 前端 `${指标}` 是 BI 模型指标引用，不能直接等同物理 SQL 字段；先查 edit metrics，再回到数据中心源 SQL |

## 高频排查入口

| 用户需求 | 先读 | 再读 | 关键风险 |
|---|---|---|---|
| 追溯某批 `lead_id` 的原始来源 / 原始分配线索 | `knowledge/sql_patterns/qingcheng_lead_origin_trace.md` | `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`、`knowledge/tables/service_dw.dm_crm_lead_stats_detail_hf.md` | 不要把 `rule_name` 当原始来源；`rule_name like '%公开课%'` 可能为 0；窗口别名不要写成 `rn` |
| 个人/团队完成度与订单流水不一致 | `knowledge/sql_patterns/qingcheng_completion_sql_repair_checklist.md` | `knowledge/sql_patterns/qingcheng_personal_completion_discounted_output_risks.md`、`knowledge/dashboards/qingcheng_personal_conversion_raw_20260522.md`、`knowledge/metrics/qingcheng_personal_conversion_metrics.md`、`knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md` | 不要只看前端公式；先查原始支付时间、空课程部门、调课调班链路、service 明细 transfer 兜底和期次架构 join |
| 看板展示值与 SQL 输出字段看似一致但仍对不上 | `knowledge/metrics/qingcheng_dashboard_metric_formula_linkage.md` | 对应 `knowledge/dashboard_web_profiles/edit_metrics/<dashboard_id>_edit_metrics.md` 和当前 retained snapshot（如 `resources/raw_sql/data_center_qingcheng_2064.sql`） | 先判断差异来自 SQL 输出、前端自定义公式、透视表维度聚合，还是转化口径与 finance 完成度口径不同 |

## 高频表与临时表

| 表 | 常见场景 | 优先动作 |
|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | 青橙线索、渠道、转化主表 | 先确认 `dt/hour`、青橙范围字段和最新分区；若是追溯原始来源，先读 `knowledge/sql_patterns/qingcheng_lead_origin_trace.md` |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | 青橙订单、收入、退款、净营收 | 用订单侧业绩部门过滤时，说明是否依赖订单侧范围兜底 |
| `finance_dw.app_finance_performance_extend_details_hf` | 年季月营收、团队完成度、个人转化 | 先确认金额单位、交易类型和任职期间 join |
| `temp_table.dingxi01_qing_team_jg` | 青橙团队架构 | 转化 raw / 个人转化使用期次架构；团队完成度月/期是否取最新架构要单独确认 |
| `temp_table.dingxi01_jiagou_db` | 过程/到课架构补充 | 姓名 key 和邮箱前缀 key 不一致时先查 join 风险 |
| `temp_table.dingxi01_qing_daoke` | 到课课次映射 | 检查 `qici + qudao + grade + begin_time` 唯一性 |
| `temp_table.shenbaoxin_channel_group` | 青橙转化宽表渠道大类 | 来源、字段结构和 `channel` 唯一性均待确认 |

## 反向定位入口

| 已知线索 | 读取 |
|---|---|
| 已知字段或指标别名，想找影响哪些指标 | `knowledge/reverse_index/field_to_metrics.md` |
| 已知表，想找哪些看板或 raw SQL 使用 | `knowledge/reverse_index/table_to_dashboards.md` |
| 已知指标文档，想找来源 raw SQL | `knowledge/reverse_index/metric_to_raw_sql.md` |
| SQL 结果异常、join 后变 0、行数放大 | `knowledge/reverse_index/join_risk_index.md`，再读 `knowledge/joins/table_relationships.md` |

## 强制前置规则

- 先读 `knowledge/04_qingcheng_project_profile.md`，确认青橙隔离边界。
- 先读 `knowledge/00_global_rules.md` 和 `knowledge/03_range_limit_rules.md`，再写生产 SQL。
- 涉及字段、指标、看板反向追溯时，先读 `knowledge/reverse_index/`，再进入具体文档。
- 遇到 `待人工确认` 不得用市场顾问侧口径补齐，除非用户明确确认青橙复用。
