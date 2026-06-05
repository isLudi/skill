# 快速参考卡

> 80% 高频场景入口。只用于快速定位，生成 SQL 前仍需读取对应表、指标、看板、join、权限或踩坑文档。

## 高频表与 Web 状态

| 表 | 常见场景 | 优先动作 |
|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | 线索、渠道、转化、GMV 全链路 | Web 查询可用；最新分区用 `dt/hour` 汇总排查 |
| `finance_dw.app_finance_performance_extend_details_hf` | 财务业绩、收款、退款、评优 | Web 查询可用 |
| `temp_table.dingxi01_jiagou_zx` | 当前在职架构、顾问名单 | 限定 `zaizhi` 和部门，按顾问去重 |
| `temp_table.dingxi01_jiagou_db` | 期次架构、小组经理 | 同时限定 `qici` 和目标部门 |
| `temp_table.dingxi01_pingyou_jg` | 评优/参评名单/人产 | 仅在评优口径使用 |
| `temp_table.dingxi01_cost` | 渠道成本、GMV 目标 | join 时处理 `grade='0'` 通配 |
| `temp_table.dingxi01_daoke_1_6_t` | 到课课次映射 | 按期次、渠道、年级、开课时间匹配 |
| `service_dw.dwd_crm_assign_private_detail_hf` | 私海阶段、深沟、双沟 | 市场顾问场景限定到市场部/市场顾问部 |
| `service_dw.dim_crm_assign_rule_lead_detail_hf` | 分配规则、计划组 | 按 `rule_id + plan_id` 关联 |
| `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` | 首 call 任务 | 通过 `account_id` 桥接员工维表 |


## 高频 join key

| key | 用途 | 先读 |
|---|---|---|
| `user_id` / `user_number` | 主线索、私海、学习、APP 活跃关联 | `knowledge/joins/common_join_keys.md` |
| `lead_id` | 线索、规则、收入退费闭环 | `knowledge/joins/common_join_keys.md` |
| `employee_email_prefix` / `employee_email_name` | 顾问、架构、财务流水 | `knowledge/joins/common_join_keys.md` |
| `qici + channel + grade` | 成本、到课、期次映射 | `knowledge/pitfalls/common_join_failures.md` |
| `rule_id + plan_id` / `group_id` | 分配计划与实际量 | `knowledge/dashboards/lead_assign_plan_actual_valid_count.md` |

## 常见需求入口

| 用户需求 | 先读 | 再读 |
|---|---|---|
| 市场顾问转化/线索转化 | `knowledge/dashboards/market_consultant_conversion.md` | `knowledge/metrics/market_consultant_conversion_metrics.md` |
| 流量画像/城市渠道 | `knowledge/dashboards/traffic_profile.md` | `knowledge/metrics/traffic_profile_metrics.md` |
| 退费分析 | `knowledge/metrics/refund_analysis_metrics.md` | 相关 `knowledge/dashboards/refund_*.md` |
| 分配计划实际有效量 | `knowledge/dashboards/lead_assign_plan_actual_valid_count.md` | `knowledge/joins/common_join_keys.md` |
| 外呼过程/首 call | `knowledge/dashboards/outbound_call_process_dashboard.md` | `knowledge/sql_patterns/first_call_task_metric_pattern.md`；期次导出模板看 `knowledge/sql_patterns/outbound_call_process_export_template.md` |
| 顾问销售评优/人产 | `knowledge/dashboards/consultant_sales_ranking_evaluation.md` | `knowledge/metrics/consultant_sales_ranking_evaluation_metrics.md` |
| 自助 BI 页面筛选器/字段 ID/组件结构 | `knowledge/dashboard_web_profiles/README.md` | 对应 `knowledge/dashboard_web_profiles/*_web_profile.md` |
| JOIN 断裂/指标为 0 | `knowledge/pitfalls/common_join_failures.md` | 相关表文档 |
| Web 查询执行/下载 | `knowledge/sql_patterns/web_query_playwright.md` | `usql-web-query-operator` Skill |

## 强制前置规则

- 先读 `knowledge/00_global_rules.md` 和 `knowledge/03_range_limit_rules.md` 顶部核心规则，再写生产 SQL。
- 需要最新渠道归因时，读 `knowledge/sql_patterns/channel_mapping_case_when.md`，完整 CASE 用 `resources/raw_sql/market_channel_case_when_0524.sql`。
- 涉及 Web 查询执行、下载、权限问题时，读 `knowledge/sql_patterns/web_permission_guide.md`。
