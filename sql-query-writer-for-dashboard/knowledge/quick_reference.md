# 快速参考卡

> 80% 高频场景入口。只用于快速定位，生成 SQL 前仍需读取对应表、指标、看板、join、权限或踩坑文档。

## Text2SQL 最短路径

1. 先确认业务域必须为 `market_consultant`；若业务域未决或属于青橙，停止使用本卡，不能默认套用市场顾问口径。
2. 读取 `semantic/domain_manifest.json`，按实体别名定位市场顾问候选指标、看板、表、join 和证据路径。
3. 使用 `scripts/text2sql.py` 构建并校验 QuerySpec；至少明确指标、维度、过滤、时间、计算粒度、输出粒度、候选表、join path、evidence 和 unresolved slots。
4. 只读取本卡或 `knowledge/decision_tree.md` 路由出的具体文档；不要全量加载知识库。
5. `unresolved_slots` 含必填项时不得生成或执行生产 SQL。共享物理目录只提供中性表结构，不能补充市场顾问业务口径。

跨部门对比必须另建一份 `qingcheng` QuerySpec；两边各用各自证据生成并校验 SQL，只在兼容聚合粒度上合并结果。

## P3 看板设计最短路径

1. 读取最新 `DashboardProfile`，按 `QuerySpec -> QueryPlan -> DashboardDatasetSpec -> DashboardDesignSpec` 生成市场顾问域内设计；业务依赖必须携带 `market_consultant:*` confirmed contract ID 与 `source_path`。
2. 运行 `design-dashboard -> plan-dashboard-change` 生成 component/layout/formula/filter 的 diff；默认 dry-run，不调用写接口。
3. P3B 当前只允许 stable-ID `update_filter_dynamic_default`。组件字段、布局、公式、数据集重绑、新建和删除必须 `blocked_unsupported`；计划含任一 blocked operation 时整次 Apply 零写入。
4. `apply-dashboard-change` 只写 draft；`publish-dashboard-change --confirm-publish` 必须独立执行并校验成功 ApplyReceipt 与最新草稿 hash。
5. 完整正反向路由和域隔离见 `knowledge/sql_patterns/dashboard_design_change_workflow.md`；普通 SQL 任务不要加载。

## 高频表与 Web 状态

| 表 | 常见场景 | 优先动作 |
|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | 线索、渠道、转化、GMV 全链路 | Web 查询可用；最新分区用 `dt/hour` 汇总排查 |
| `finance_dw.app_finance_performance_extend_details_hf` | 财务业绩、收款、退款、评优 | Web 查询可用 |
| `temp_table.dingxi01_jiagou_zx` | 当前在职架构、顾问名单 | 限定 `zaizhi` 和部门，按顾问去重 |
| `temp_table.dingxi01_jiagou_db` | 期次架构、小组经理 | 同时限定 `qici` 和目标部门 |
| `temp_table.zhangjunyan01_pingyou_jg` | 评优/参评名单/人产 | 仅在评优口径使用 |
| `temp_table.dingxi01_cost` | 渠道成本、GMV 目标 | join 时处理 `grade='0'` 通配 |
| `temp_table.dingxi01_daoke_1_6_t` | 到课手工课次映射 | 最新到课 canonical 仅用于 `manual_*` 和自动/手工对照诊断；主课次按实际开课时间自动排序 |
| `service_dw.dwd_crm_assign_private_detail_hf` | 私海阶段、深沟、双沟 | 市场顾问场景限定到市场部/市场顾问部 |
| `service_dw.dim_crm_assign_rule_lead_detail_hf` | 分配规则、计划组 | 按 `rule_id + plan_id` 关联 |
| `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` | 首 call 任务 | 通过 `account_id` 桥接员工维表 |


## 高频 join key

| key | 用途 | 先读 |
|---|---|---|
| `user_id` / `user_number` | 主线索、私海、学习、APP 活跃关联 | `knowledge/joins/common_join_keys.md` |
| `lead_id` | 线索、规则、收入退费闭环 | `knowledge/joins/common_join_keys.md` |
| `employee_email_prefix` / `employee_email_name` | 顾问、架构、财务流水 | `knowledge/joins/common_join_keys.md` |
| `qici + channel_map_1 + grade_1 + begin_time_slot` | 到课自动课次槽位排序 | `knowledge/dashboards/market_consultant_lead_conversion_attendance.md` |
| `qici + channel_map_1/qudao + grade_1/grade + begin_time` | 到课手工课次诊断映射 | `knowledge/dashboards/market_consultant_lead_conversion_attendance.md` |
| `rule_id + plan_id` / `group_id` | 分配计划与实际量 | `knowledge/dashboards/lead_assign_plan_actual_valid_count.md` |

## 常见需求入口

| 用户需求 | 先读 | 再读 |
|---|---|---|
| 市场顾问转化/线索转化 | `knowledge/dashboards/market_consultant_conversion.md` | `knowledge/metrics/market_consultant_conversion_metrics.md` |
| 流量画像/城市渠道 | `knowledge/dashboards/traffic_profile.md` | `knowledge/metrics/traffic_profile_metrics.md` |
| 市场渠道用户画像/成单过程/多维退费率/退费科目产品占比 | `knowledge/dashboards/market_channel_conversion_profile.md` | `knowledge/metrics/market_channel_conversion_profile_metrics.md`；科目/产品/年级退款金额占比读 2349 fixed SQL |
| 市场顾问部模板取数最新代码/AI分析模板 | `knowledge/dashboards/template_query_market_datasets.md` | 读取清单中对应 raw SQL；使用口径必须说明为“模板取数” |
| 市场顾问看板指标含义/前端公式/数据集 SQL 联动 | `knowledge/metrics/market_consultant_dashboard_metric_formula_linkage.md` | 再读 `knowledge/dashboard_web_profiles/edit_metrics/` 中对应看板明细和 `resources/raw_sql/data_center_market_*_*.sql` |
| 运营侧暑期期次、`20260717期` 应归 `20260716期`、7 月后期次不按周五 | `knowledge/sql_patterns/market_summer_qici_corrections.md` | 再读 `knowledge/dashboard_web_profiles/operation_side_dashboard_web_profile.md` 和 `knowledge/dashboards/data_center_market_datasets.md` |
| 退费分析 | `knowledge/metrics/market_channel_conversion_profile_metrics.md` | 唯一入口为 `knowledge/dashboards/market_channel_conversion_profile.md`；按 2349、2890、2353 三个当前模型选择对应字段 |
| 分配计划实际有效量 | `knowledge/dashboards/lead_assign_plan_actual_valid_count.md` | `knowledge/joins/common_join_keys.md` |
| 外呼过程/首 call | `knowledge/dashboards/outbound_call_process_dashboard.md` | `knowledge/sql_patterns/first_call_task_metric_pattern.md`；期次导出模板看 `knowledge/sql_patterns/outbound_call_process_export_template.md` |
| 顾问销售评优/人产 | `knowledge/dashboards/consultant_sales_ranking_evaluation.md` | `knowledge/metrics/consultant_sales_ranking_evaluation_metrics.md` |
| 自助 BI 页面筛选器/字段 ID/组件结构 | `knowledge/dashboard_web_profiles/README.md` | 对应 `knowledge/dashboard_web_profiles/*_web_profile.md` |
| JOIN 断裂/指标为 0 | `knowledge/pitfalls/common_join_failures.md` | 相关表文档 |
| Web 查询执行/下载 | `knowledge/sql_patterns/web_query_playwright.md` | `usql-web-query-operator` Skill |

## 强制前置规则

- 先读 `knowledge/00_global_rules.md` 和 `knowledge/03_range_limit_rules.md` 顶部核心规则，再写生产 SQL。
- 排查平台“模板取数”中存储的最新 SQL 时，先读 `knowledge/dashboards/template_query_market_datasets.md`，不要默认用数据中心或 Web BI canonical SQL 替代；回答时说明使用口径为“模板取数”。
- 生成平台模板取数 SQL 时，日期/时间区间必须使用 `字段名 >= ${字段名:1} and 字段名 < ${字段名:2}`，参数名和过滤列名一致，不能加 `cast()`，详见 `knowledge/sql_patterns/template_parameter_rules.md`。
- 需要最新渠道归因时，读 `knowledge/sql_patterns/channel_mapping_case_when.md`，完整 CASE 用 `resources/raw_sql/market_channel_case_when_0612.sql`。
- 涉及 Web 查询执行、下载、权限问题时，读 `knowledge/sql_patterns/web_permission_guide.md`。
