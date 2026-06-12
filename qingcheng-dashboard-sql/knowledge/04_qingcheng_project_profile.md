# 青橙项目部业务域档案

## 1. 业务域

本 Skill 仅维护青橙项目部相关 SQL、看板、指标、临时表、字段匹配规则和 join 关系。

## 2. 隔离目标

青橙项目部必须在不同对话中与市场顾问部明确隔离。即使两个部门使用相同数据库表，也不得默认共享指标计算、字段匹配、临时表、名单口径或看板逻辑。

## 3. 当前已知基础信息

| 项目 | 当前值 | 状态 |
|---|---|---|
| 业务部门名称 | 青橙项目部 | 已知 |
| 查询引擎 | Presto | 已知 |
| 核心看板 | 青橙过程数据 raw、青橙到课 raw、青橙转化 raw、青橙年季月营收 raw、青橙团队完成度【月】raw、青橙团队完成度【期】raw、青橙个人转化 raw | 已入库 |
| 核心事实表 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | 已从 SQL 入库，字段待确认 |
| 核心临时表 | `temp_table.dingxi01_qing_daoke`, `temp_table.dingxi01_jiagou_db`, `temp_table.dingxi01_qing_team_jg`, `temp_table.dingxi01_qing_zz`, `temp_table.dingxi01_qing_qi_moth`, `temp_table.dingxi01_qing_team_goal`, `temp_table.dingxi01_qing_team_g_qi` | 已从 SQL 入库，来源/刷新方式待确认 |
| 核心范围字段 | `section_assign_employee_second_level_department_name`, `virtual_second_department_name` | 已从 SQL 入库 |
| 核心范围取值 | `青橙项目部` | 已从 SQL 入库 |
| Web BI 结构快照 | `knowledge/dashboard_web_profiles/README.md` | 执行 `profile-all` 后维护；只允许写入本 Skill |

## 4. 临时表策略

- 青橙项目部临时表统一维护在 `knowledge/temp_tables/`。
- 每张临时表必须记录来源、刷新方式、数据粒度、字段含义、适用看板、有效期和不可复用边界。
- 临时表数量较多时，优先保持“一表一文档”，不要把多个临时表混写到同一文件。
- 如果临时表是某个看板专用表，必须写明“仅限该看板复用”。

## 5. Web BI 结构快照边界

- 青橙项目部的筛选器、组件、字段 ID、下载按钮、刷新任务 ID 和选择器漂移排查记录，统一维护在 `knowledge/dashboard_web_profiles/`。
- 这些 Web BI 结构快照属于青橙知识库资产，不得混写到市场顾问侧 skill。
- Web BI 快照只补充前端结构，不替代本 Skill 已入库的 SQL、指标、临时表和 join 口径。

## 6. 指标冲突处理

当青橙指标与其他部门指标同名但口径不同：

1. 只使用本 Skill 的青橙口径。
2. 如果本 Skill 没有定义，先从青橙历史看板 SQL 中抽取并标注“待人工确认”。
3. 不从其他部门 Skill 自动迁移定义。
4. 输出 SQL 时说明指标计算粒度和最终输出粒度。

## 7. 已入库过程数据口径

来源：`resources/raw_sql/qingcheng_process_data_raw_20260522.sql`

| 口径 | 文档 |
|---|---|
| 看板结构 | `knowledge/dashboards/qingcheng_process_data_raw_20260522.md` |
| 指标集合 | `knowledge/metrics/qingcheng_process_data_metrics.md` |
| 渠道/年级映射 | `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md` |
| join 关系 | `knowledge/joins/table_relationships.md` |

## 8. 已入库到课口径

来源：`resources/raw_sql/qingcheng_daoke_raw_20260522.sql`

| 口径 | 文档 |
|---|---|
| 看板结构 | `knowledge/dashboards/qingcheng_daoke_raw_20260522.md` |
| 指标集合 | `knowledge/metrics/qingcheng_daoke_metrics.md` |
| 渠道/年级映射 | `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md` |
| 临时表课次语义 | `knowledge/temp_tables/temp_table.dingxi01_qing_daoke.md` |
| join 关系 | `knowledge/joins/table_relationships.md` |

## 9. 已入库转化口径

来源：`resources/raw_sql/qingcheng_conversion_raw_20260522.sql`

| 口径 | 文档 |
|---|---|
| 看板结构 | `knowledge/dashboards/qingcheng_conversion_raw_20260522.md` |
| 指标集合 | `knowledge/metrics/qingcheng_conversion_metrics.md` |
| 订单业绩表 | `knowledge/tables/service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.md` |
| 团队架构临时表 | `knowledge/temp_tables/temp_table.dingxi01_qing_team_jg.md` |
| 渠道/成本映射 | `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md` |
| join 关系 | `knowledge/joins/table_relationships.md` |

## 10. 已入库年季月营收口径

来源：`resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql`

| 口径 | 文档 |
|---|---|
| 看板结构 | `knowledge/dashboards/qingcheng_revenue_year_quarter_month_raw_20260522.md` |
| 指标集合 | `knowledge/metrics/qingcheng_revenue_year_quarter_month_metrics.md` |
| 财务业绩表 | `knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md` |
| 员工组织链表 | `knowledge/tables/dw.dim_employee_chain.md` |
| 青橙组织临时表 | `knowledge/temp_tables/temp_table.dingxi01_qing_zz.md` |
| 范围口径 | `knowledge/03_range_limit_rules.md` |
| join 关系 | `knowledge/joins/table_relationships.md` |

## 11. 已入库团队完成度【月】口径

来源：`resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql`

| 口径 | 文档 |
|---|---|
| 看板结构 | `knowledge/dashboards/qingcheng_team_completion_month_raw_20260522.md` |
| 指标集合 | `knowledge/metrics/qingcheng_team_completion_month_metrics.md` |
| 退款课节表 | `knowledge/tables/finance_dw.dm_finance_order_refund_detail_df.md` |
| 调课调班维表 | `knowledge/tables/finance_dw.dim_finance_order_change_df.md` |
| 期次月份映射 | `knowledge/temp_tables/temp_table.dingxi01_qing_qi_moth.md` |
| 团队月目标 | `knowledge/temp_tables/temp_table.dingxi01_qing_team_goal.md` |
| 范围口径 | `knowledge/03_range_limit_rules.md` |
| join 关系 | `knowledge/joins/table_relationships.md` |

## 12. 已入库团队完成度【期】口径

来源：`resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql`

| 口径 | 文档 |
|---|---|
| 看板结构 | `knowledge/dashboards/qingcheng_team_completion_period_raw_20260522.md` |
| 指标集合 | `knowledge/metrics/qingcheng_team_completion_period_metrics.md` |
| 期次团队目标 | `knowledge/temp_tables/temp_table.dingxi01_qing_team_g_qi.md` |
| 退款课节表 | `knowledge/tables/finance_dw.dm_finance_order_refund_detail_df.md` |
| 调课调班维表 | `knowledge/tables/finance_dw.dim_finance_order_change_df.md` |
| 范围口径 | `knowledge/03_range_limit_rules.md` |
| join 关系 | `knowledge/joins/table_relationships.md` |

## 13. 已入库个人转化口径

来源：`resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`

| 口径 | 文档 |
|---|---|
| 看板结构 | `knowledge/dashboards/qingcheng_personal_conversion_raw_20260522.md` |
| 指标集合 | `knowledge/metrics/qingcheng_personal_conversion_metrics.md` |
| 个人架构骨架 | `knowledge/temp_tables/temp_table.dingxi01_qing_team_jg.md` |
| 期次月份映射 | `knowledge/temp_tables/temp_table.dingxi01_qing_qi_moth.md` |
| 退款课节表 | `knowledge/tables/finance_dw.dm_finance_order_refund_detail_df.md` |
| 调课调班维表 | `knowledge/tables/finance_dw.dim_finance_order_change_df.md` |
| 范围口径 | `knowledge/03_range_limit_rules.md` |
| join 关系 | `knowledge/joins/table_relationships.md` |

## 14. 入库资料优先级

1. 用户明确提供的青橙看板 SQL。
2. 用户明确提供的青橙指标说明。
3. 用户明确提供的青橙临时表说明。
4. 用户明确提供的青橙表结构或字段目录。
5. 本 Skill 已入库知识。

任何来自其他部门的资料，都必须经用户明确确认后才能作为青橙口径。
