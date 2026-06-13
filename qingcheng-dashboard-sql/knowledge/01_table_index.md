# 表索引

本文件只记录青橙项目部 Skill 已核对或待核对的表。不要从其他部门 skill 自动复制表索引。

## 1. 物理表

| 表名 | 中文名称 | 主要用途 | 分区字段 | 小时字段 | 状态 | 详情 |
|---|---|---|---|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | 线索成本 GMV 沟通学习全链路表 | 青橙有效线索主表 | `dt` | `hour` | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md` |
| `dw.dim_employee_chain` | 员工组织链维表 | 员工青橙任职起止时间 | `dt` | 无 | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/dw.dim_employee_chain.md` |
| `service_dw.dm_crm_lead_stats_detail_hf` | 线索统计明细小时表 | 首次接通时间差 | `dt` | `hour` | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/service_dw.dm_crm_lead_stats_detail_hf.md` |
| `service_dw.app_h_crm_lead_employee_workload_detail_hf` | CRM 线索员工工作量明细小时表 | 外呼次数、接通、通时 | `dt` | `hour` | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/service_dw.app_h_crm_lead_employee_workload_detail_hf.md` |
| `service_dw.dws_service_user_learn_detail_hf` | 用户学习明细小时表 | 首节到课、有效到课 | `dt` | `hour` | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/service_dw.dws_service_user_learn_detail_hf.md` |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | CRM 订单线索归因收入退款明细小时表 | 青橙转化、收入、退款、净营收 | `dt` | `hour` | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.md` |
| `dw.dim_cstm_active_user_c_appliction_mb_df` | 用户应用活跃天级维表 | 近 7 天 APP/PC 登录 | `dt` | 无 | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/dw.dim_cstm_active_user_c_appliction_mb_df.md` |
| `dw.dws_user_active_user_c_appliction_hf` | 用户应用活跃小时表 | 近 2 小时 APP/PC 登录 | `dt` | `hour` | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/dw.dws_user_active_user_c_appliction_hf.md` |
| `finance_dw.app_finance_performance_extend_details_hf` | 财务业绩扩展明细小时表 | 年季月营收、团队完成度、个人转化 | `dt` | `hour` | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md` |
| `finance_dw.dim_finance_employee_df` | 员工维表 | 员工账号、在职状态和组织架构补充 | `dt` | 无 | 公共表结构复用，字段待表结构确认 | `knowledge/tables/finance_dw.dim_finance_employee_df.md` |
| `finance_dw.dm_finance_order_refund_detail_df` | 财务订单退款明细日表 | 全退订单行课节数、退 4 阈值 | `dt` | 无 | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/finance_dw.dm_finance_order_refund_detail_df.md` |
| `finance_dw.dim_finance_order_change_df` | 财务订单调课调班维表 | 退款订单调课调班类型 | `dt` | 无 | 已从 SQL 入库，字段待表结构确认 | `knowledge/tables/finance_dw.dim_finance_order_change_df.md` |
| `service_dw.app_h_crm_lead_task_process_info_detail_hf` | CRM 线索任务处理信息明细小时表 | F 类首次外呼标记 | `dt` | `hour` | 新入库，字段待表结构确认 | `knowledge/tables/service_dw.app_h_crm_lead_task_process_info_detail_hf.md` |
| `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` | 顾问首call数据分析表 | 首 call 任务状态和任务量 | `dt` | `hour` | 公共表结构复用，字段待表结构确认 | `knowledge/tables/gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf.md` |
| `service_dw.app_user_attribute_label_gaia_wide_df` | 盖亚系统用户标签数据宽表 | 用户标签、画像和学习意向补充 | `dt` | 无 | 公共表结构复用，字段待表结构确认 | `knowledge/tables/service_dw.app_user_attribute_label_gaia_wide_df.md` |
| `service_dw.dim_crm_assign_rule_lead_detail_hf` | 线索分配规则记录 | 分配规则明细和分配记录排查 | `dt` | `hour` | 公共表结构复用，字段待表结构确认 | `knowledge/tables/service_dw.dim_crm_assign_rule_lead_detail_hf.md` |
| `service_dw.dim_crm_assign_rule_plan_item_info_hf` | 分配规则计划 item 信息表 | 分配计划下的顾问配置 | `dt` | `hour` | 公共表结构复用，字段待表结构确认 | `knowledge/tables/service_dw.dim_crm_assign_rule_plan_item_info_hf.md` |

## 2. 青橙临时表

| 表名 | 用途 | 刷新方式 | 适用看板 | 状态 | 详情 |
|---|---|---|---|---|---|
| `temp_table.dingxi01_qing_daoke` | 青橙课次映射表，支持第 1 至第 6 讲 | 待人工确认 | 青橙过程数据 raw、青橙到课 raw | 已从 SQL 入库，来源待确认 | `knowledge/temp_tables/temp_table.dingxi01_qing_daoke.md` |
| `temp_table.dingxi01_jiagou_db` | 青橙架构映射表 | 待人工确认 | 青橙过程数据 raw、青橙到课 raw | 已从 SQL 入库，来源待确认；员工 join key 待确认 | `knowledge/temp_tables/temp_table.dingxi01_jiagou_db.md` |
| `temp_table.dingxi01_qing_team_jg` | 青橙团队架构表 | 待人工确认 | 青橙转化 raw、青橙团队完成度【月/期】raw、青橙个人转化 raw | 已从 SQL 入库，来源待确认；不同看板是否使用最新架构或期次架构需区分 | `knowledge/temp_tables/temp_table.dingxi01_qing_team_jg.md` |
| `temp_table.dingxi01_qing_zz` | 青橙组织架构补充表 | 待人工确认 | 青橙年季月营收 raw | 已从 SQL 入库，来源待确认；是否有历史期次待确认 | `knowledge/temp_tables/temp_table.dingxi01_qing_zz.md` |
| `temp_table.dingxi01_qing_qi_moth` | 青橙期次到月份映射表 | 待人工确认 | 青橙团队完成度【月】raw、青橙团队完成度【期】raw、青橙个人转化 raw | 已从 SQL 入库，来源待确认 | `knowledge/temp_tables/temp_table.dingxi01_qing_qi_moth.md` |
| `temp_table.dingxi01_qing_team_goal` | 青橙团队月目标表 | 待人工确认 | 青橙团队完成度【月】raw | 已从 SQL 入库，目标单位和层级待确认 | `knowledge/temp_tables/temp_table.dingxi01_qing_team_goal.md` |
| `temp_table.dingxi01_qing_team_g_qi` | 青橙团队期次目标表 | 待人工确认 | 青橙团队完成度【期】raw | 已从 SQL 入库，目标单位和层级待确认 | `knowledge/temp_tables/temp_table.dingxi01_qing_team_g_qi.md` |
| `temp_table.shenbaoxin_channel_group` | 市场渠道分组映射表 | 待人工确认 | 青橙转化宽表-市场渠道 raw | 新入库，来源/刷新/唯一性待确认 | `knowledge/temp_tables/temp_table.shenbaoxin_channel_group.md` |

## 3. 看板入口

| 看板 | 来源 SQL | 指标文档 | 状态 |
|---|---|---|---|
| 青橙过程数据 raw | `resources/raw_sql/qingcheng_process_data_raw_20260522.sql` | `knowledge/metrics/qingcheng_process_data_metrics.md` | 已入库，部分口径待确认 |
| 青橙到课 raw | `resources/raw_sql/qingcheng_daoke_raw_20260522.sql` | `knowledge/metrics/qingcheng_daoke_metrics.md` | 已入库，部分口径待确认 |
| 青橙转化 raw | `resources/raw_sql/qingcheng_conversion_raw_20260522.sql` | `knowledge/metrics/qingcheng_conversion_metrics.md` | 已入库，raw SQL 存在尾逗号和平台函数风险 |
| 青橙渠道订单明细 raw | `resources/raw_sql/qingcheng_channel_order_detail_raw_20260613.sql` | `knowledge/metrics/qingcheng_channel_order_detail_metrics.md` | 已入库，明细抽取 SQL；`ld` 范围限定和明细粒度稳定性待确认 |
| 青橙年季月营收 raw | `resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql` | `knowledge/metrics/qingcheng_revenue_year_quarter_month_metrics.md` | 已入库，raw SQL 存在平台函数风险 |
| 青橙团队完成度【月】raw | `resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql` | `knowledge/metrics/qingcheng_team_completion_month_metrics.md` | 已入库，raw SQL 存在平台函数风险 |
| 青橙团队完成度【期】raw | `resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql` | `knowledge/metrics/qingcheng_team_completion_period_metrics.md` | 已入库，raw SQL 存在平台函数风险 |
| 青橙个人转化 raw | `resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql` | `knowledge/metrics/qingcheng_personal_conversion_metrics.md` | 已入库，raw SQL 存在平台函数风险 |
| 青橙转化宽表-市场渠道 raw | `resources/raw_sql/qingcheng_conversion_wide_table_market_channel_20260611.sql` | `knowledge/metrics/qingcheng_conversion_wide_table_market_channel_metrics.md` | 已入库，100+ 分支 CASE WHEN 渠道映射，含 AND/OR 优先级风险 |

## 4. 入库规则

- 新表必须先写入 `knowledge/tables/<库名.表名>.md` 或 `knowledge/temp_tables/<库名.表名>.md`。
- 表索引只做入口导航，不承载完整字段说明。
- 如果表来自历史 SQL 解析但尚未核对字段，状态写“字段待表结构确认”。
- 不得把市场顾问部专属临时表写入本索引，除非用户明确确认青橙项目部也复用且口径一致。
