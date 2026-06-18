# 青橙项目部数据中心源 SQL 对比与维护

维护日期：2026-06-17

本文件记录数据中心 `data-set/detail` 接口同步到的源 SQL 与本 skill 现有 `resources/raw_sql` 的关系。已确认同源的数据中心版本会覆盖既有 canonical raw SQL；未能确认同源的 SQL 保留 `data_center_*` 文件名，并标注为待人工确认，避免误覆盖不同用途的数据集。

## 维护结论

| 数据集 | 数据中心 id | 关系 | 维护动作 | 维护后的源 SQL | 主要依赖表 | 用途与撰写逻辑 | 冲突/注意事项 |
|---|---:|---|---|---|---|---|---|
| 青橙-过程数据 | 2064 | 一致或极小差异 | 映射到 canonical raw_sql；如有差异以 data_center 为准。 行数 250 -> 252。 | [`qingcheng_process_data_raw_20260522.sql`](../../resources/raw_sql/qingcheng_process_data_raw_20260522.sql) | dw.dim_cstm_active_user_c_appliction_mb_df, dw.dws_user_active_user_c_appliction_hf, bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df, service_dw.dm_crm_lead_stats_detail_hf, service_dw.app_h_crm_lead_employee_workload_detail_hf, service_dw.dws_service_user_learn_detail_hf ... | 生成线索过程明细，按渠道、期次、年级、人员等维度组织后供过程看板复用。 主要 CTE：d_ap, h_ap, denglu_app, data, call_c。 | 内容几乎一致，主要用于消除重复快照。 |
| 青橙到课 | 2244 | 一致或极小差异 | 映射到 canonical raw_sql；如有差异以 data_center 为准。 行数 124 -> 125。 | [`qingcheng_daoke_raw_20260522.sql`](../../resources/raw_sql/qingcheng_daoke_raw_20260522.sql) | bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df, service_dw.dws_service_user_learn_detail_hf, temp_table.dingxi01_qing_daoke, temp_table.dingxi01_jiagou_db | 按期次、课程渠道、年级和人员维度汇总到课/衰减数据，通常依赖线索、班级课次和临时架构表。 主要 CTE：data, daoke。 | 内容几乎一致，主要用于消除重复快照。 |
| 转化数据 | 2460 | 一致或极小差异 | 映射到 canonical raw_sql；如有差异以 data_center 为准。 行数 252 -> 253。 | [`qingcheng_conversion_raw_20260615.sql`](../../resources/raw_sql/qingcheng_conversion_raw_20260615.sql) | service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf, bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df, temp_table.dingxi01_qing_team_jg | 以线索、订单、退款和临时架构为主链路，沉淀渠道/部门/人员/期次维度的转化数据集。 主要 CTE：dd, prc, gmv, udd, ud。 | 内容几乎一致，主要用于消除重复快照。 |
| 年季月营收情况 | 2576 | 一致或极小差异 | 映射到 canonical raw_sql；如有差异以 data_center 为准。 内容一致，未改变 canonical 内容。 | [`qingcheng_revenue_year_quarter_month_raw_20260522.sql`](../../resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql) | dw.dim_employee_chain, finance_dw.app_finance_performance_extend_details_hf, temp_table.dingxi01_qing_zz | 按年、季、月或期次汇总订单营收与退款后收入，服务营收趋势看板。 主要 CTE：org_t, dd_0, dd, gmv_t, gmv_z。 | 内容几乎一致，主要用于消除重复快照。 |
| 团队完成度【月】 | 2677 | 同源更新 | 已用 data_center 最新代码覆盖 canonical raw_sql。 行数 257 -> 271。 | [`qingcheng_team_completion_month_raw_20260522.sql`](../../resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql) | dw.dim_employee_chain, finance_dw.app_finance_performance_extend_details_hf, finance_dw.dm_finance_order_refund_detail_df, finance_dw.dim_finance_order_change_df, temp_table.dingxi01_qing_qi_moth, temp_table.dingxi01_qing_team_jg ... | 基于订单营收、目标表和人员架构计算团队或个人完成度/评优/激励指标。 主要 CTE：org_t, dd_0, dd, gmv_t, gmv_z。 | 与旧知识库同源，存在可解释的代码版本差异。 |
| 团队完成度【期】 | 2680 | 同源更新 | 已用 data_center 最新代码覆盖 canonical raw_sql。 行数 257 -> 270。 | [`qingcheng_team_completion_period_raw_20260522.sql`](../../resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql) | dw.dim_employee_chain, finance_dw.app_finance_performance_extend_details_hf, finance_dw.dm_finance_order_refund_detail_df, finance_dw.dim_finance_order_change_df, temp_table.dingxi01_qing_qi_moth, temp_table.dingxi01_qing_team_jg ... | 基于订单营收、目标表和人员架构计算团队或个人完成度/评优/激励指标。 主要 CTE：org_t, dd_0, dd, gmv_t, gmv_z。 | 与旧知识库同源，存在可解释的代码版本差异。 |
| 抖私-转化 | 2740 | 新增 | 保留 data_center 源 SQL；未强行覆盖旧 raw_sql。 | [`data_center_qingcheng_2740_20260617.sql`](../../resources/raw_sql/data_center_qingcheng_2740_20260617.sql) | dw.dim_employee_chain, finance_dw.app_finance_performance_extend_details_hf, service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf, service_dw.dim_crm_assign_rule_lead_detail_hf, temp_table.dingxi01_qing_team_jg | 以线索、订单、退款和临时架构为主链路，沉淀渠道/部门/人员/期次维度的转化数据集。 主要 CTE：org_t, dd_0, dd, gmv_t, gmv_z。 | 暂无明确同源旧文件，后续如成为固定看板口径再拆入正式专题。 |
| 青橙个人转化 | 2769 | 大幅更新 | 已用 data_center 最新代码覆盖 canonical raw_sql。 行数 261 -> 559。 | [`qingcheng_personal_conversion_raw_20260522.sql`](../../resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql) | dw.dim_employee_chain, finance_dw.app_finance_performance_extend_details_hf, finance_dw.dm_finance_order_refund_detail_df, finance_dw.dim_finance_order_change_df, temp_table.dingxi01_qing_team_jg, temp_table.dingxi01_qing_qi_moth ... | 从线索到订单/退款链路计算个人维度转化与营收，通常关联员工、架构和目标临时表。 主要 CTE：org_t, dd_0, dd, gmv_t, gmv_z。 | 代码结构变化较大，相关指标口径后续以数据中心版本为准并需业务校验。 |
| 转化-宽表-市场渠道 | 2834 | 一致或极小差异 | 映射到 canonical raw_sql；如有差异以 data_center 为准。 行数 348 -> 348。 | [`qingcheng_conversion_wide_table_market_channel_20260611.sql`](../../resources/raw_sql/qingcheng_conversion_wide_table_market_channel_20260611.sql) | bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df, service_dw.app_h_crm_lead_task_process_info_detail_hf, temp_table.shenbaoxin_channel_group | 以线索、订单、退款和临时架构为主链路，沉淀渠道/部门/人员/期次维度的转化数据集。 主要 CTE：data_base, data, f_call0, data_with_process, zhuanhua。 | 内容几乎一致，主要用于消除重复快照。 |

## 口径冲突处理原则

- 同源关系清晰时，以数据中心源 SQL 作为最新版本，继续沿用原 canonical 文件名，减少知识库中同一口径的重复入口。
- 与旧 raw SQL 差异较大的同源数据集已标注“大幅更新”，后续分析 SQL 时优先引用数据中心版本，同时保留业务校验空间。
- 未能确认同源的数据中心 SQL 暂不覆盖已有 raw SQL；如果后续被证明是固定看板口径，再补充到对应指标、表说明或 SQL 模板文档。
- 测试类或直接引用 `temp_table` 的数据集只作为来源记录，不默认进入正式指标口径。

## 同步来源

- 同步摘要：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\data-center\data_center_sql_sync_20260617.json`
- 自动比对摘要：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\data-center\raw_sql_compare_20260617.json`
