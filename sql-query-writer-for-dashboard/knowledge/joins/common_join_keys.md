# 常用 join key

| join key | 常见表 | 用途 | 注意事项 |
|---|---|---|---|
| user_number | service_dw.dwd_crm_assign_private_detail_hf, service_dw.app_user_attribute_label_gaia_wide_df, service_dw.dws_service_user_learn_detail_hf, dw.dim_cstm_active_user_c_appliction_mb_df | 用户维度关联 | 类型需确认，部分表可能为 bigint/string |
| user_id | service_dw.dm_crm_lead_stats_detail_hf, service_dw.dm_crm_trace_lead_full_link_data_hf, bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | 用户维度关联 | 与 user_number 不一定等价 |
| lead_id | service_dw.dm_crm_lead_stats_detail_hf, service_dw.dm_crm_trace_lead_full_link_data_hf, service_dw.dim_crm_assign_rule_lead_detail_hf, service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf, bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | 线索维度关联 | 需确认去重口径；宽表可能需要先按分区去重 |
| lead_id + account_domain | service_dw.dim_crm_assign_rule_lead_detail_hf, finance_dw.app_finance_performance_extend_details_hf | 退费分析规则关联 | 退费分析 SQL 用 `lead_gmv.lead_id = rr.lead_id` 且 `lead_gmv.email_prefix = rr.account_domain` 补充分配规则；`account_domain` 是否稳定等于邮箱前缀需确认 |
| trace_id | service_dw.dm_crm_trace_lead_full_link_data_hf, service_dw.dim_crm_assign_rule_lead_detail_hf | 留痕/分配规则关联 | 与 lead_id 共同使用时需确认一对多关系 |
| rule_id, plan_id | service_dw.dim_crm_assign_rule_lead_detail_hf, service_dw.dim_crm_assign_rule_plan_item_info_hf | 分配规则和计划 item 关联 | 小时分区必须对齐；需检查当前分区下是否一对多放大 |
| group_id | service_dw.dim_crm_assign_rule_lead_detail_hf, temp_table.dingxi01_plan_id | 分配规则组过滤 | `temp_table.dingxi01_plan_id` 来自 `plan_id.xlsx`；`group_id` 单字段不全局唯一，若输出期次/组名应同时用 `qici` 或先去重 |
| qici + group_id | temp_table.dingxi01_plan_id | 分配规则组期次映射 | 该表推荐唯一键；`qici` 为 MMDD期，不含年份，跨年需加 `year` |
| order_number | service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf, finance_dw.app_finance_performance_extend_details_hf, finance_dw.dwd_finance_order_refund_df | 订单维度关联 | 金额类字段通常为分，聚合前确认是否需要除以 100；退款原因表按 `order_number` 关联时需检查一单多条退款记录 |
| private_sea_id | dwd_crm_assign_private_detail_hf | 私海记录主键 | 可用于 CRM 私海明细内部去重 |
| employee_id | service_dw.dwd_crm_assign_private_detail_hf, service_dw.app_h_crm_lead_employee_workload_detail_hf, dw.dim_employee_chain | 顾问/员工关联 | 部门范围限定不可省略；`dw.dim_employee_chain.employee_id` 来自员工信息表 |
| account_id | gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf, finance_dw.dim_finance_employee_df | 顾问账号维度关联 | 首 call 表用 `account_id` 统计任务；员工维表可补充员工姓名、邮箱前缀和组织架构 |
| email_prefix | finance_dw.dim_finance_employee_df, dw.dim_employee_chain, finance_dw.app_finance_performance_extend_details_hf | 员工邮箱前缀 | 常与业务表中的 `employee_email_prefix`、`performance_employee_email_prefix` 关联；组织链与财务流水如可用 `email_prefix`，优先于姓名关联 |
| employee_email_prefix | service_dw.dwd_crm_assign_private_detail_hf, temp_table.dingxi01_jiagou_db, bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | 员工邮箱前缀关联 | Excel 中存在少量数字型值，建议按字符串比较 |
| user_number + section_assign_employee_email_prefix | service_dw.app_h_crm_lead_employee_workload_detail_hf, bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | 流量画像外呼工作量关联 | `traffic_profile.sql` 中 `call_c` 聚合含 `lead_id`，但 join 到主线索只用 `user_id + employee_email_prefix`；多线索用户需确认是否会放大 |
| performance_employee_email_prefix | service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | 业绩归属员工关联 | 可与 `finance_dw.dim_finance_employee_df.email_prefix` 关联补充入离职/新老顾问信息 |
| original_order_user_number + performance_employee_email_name | service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf, finance_dw.app_finance_performance_extend_details_hf | 退费分析从财务流水补 lead_id | 退费分析 SQL 按用户和顾问姓名匹配，并用 `row_number() over(partition by original_order_user_number order by qici desc)` 取最新，可能忽略顾问/期次差异 |
| dt, hour | 小时表 | 分区对齐 | 小时表建议同时对齐 dt 和 hour |
| lead_period_number | dm_crm_lead_stats_detail_hf | 期次关联 | 需确认是否与期次映射表一致 |
| biz_number | gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf | 顾问首 call 任务期 number | 与 `qici`/`period_name` 不是同一字段，使用前需确认期次映射 |
| qici | temp_table.dingxi01_jiagou_db, temp_table.dingxi01_daoke_1_6_t, temp_table.dingxi01_pingyou_jg | 期次范围和临时映射表关联 | 临时表无分区，查询时建议必须限定期次 |
| substr(qici, -5) | temp_table.dingxi01_jiagou_db | 期次尾号关联 | `lead_assign_plan_actual_valid_count.sql` 用规则名拆出的期次片段匹配该字段；跨年份可能重复，优先确认能否改用完整期次 |
| qudao, grade | temp_table.dingxi01_daoke_1_6_t | 渠道-年级开课时间/课次映射 | 需确认目标看板渠道字段是否与 qudao 同口径 |
| channel, grade, begin_time | temp_table.dingxi01_daoke_1_6_t | 渠道-年级-开课时间课次映射 | 市场顾问线索转化到课看板使用 `channel_map = channel`；与 `qudao` 口径差异需确认 |
| dept_1, dept_2, department | temp_table.dingxi01_jiagou_db | 架构范围映射 | 虽不含 department_name，但属于部门/架构范围字段，必须控制范围 |
| path_name | dw.dim_employee_chain | 员工组织链路径范围 | 虽不含 department_name，但属于部门/架构字段，必须通过完整路径或层级派生字段限定 |
| job_number / display_number | dw.dim_employee_chain, finance_dw.dim_finance_employee_df | 员工编号关联 | 两类编号口径需确认；跨表使用前检查是否同一编号体系 |
| leader | dw.dim_employee_chain | 直属上级邮箱前缀关联 | 可与同表 `email_prefix` 自关联，用于补充直属上级信息 |
| channel | temp_table.dingxi01_channel_group, temp_table.shenbaoxin_channel_group, temp_table.dingxi01_cost | 渠道映射和成本目标 | 常与派生字段 channel_map 关联；`temp_table.shenbaoxin_channel_group` 字段结构和唯一性待确认 |
| channel, grade, qici | temp_table.dingxi01_cost | 渠道-年级-期次成本目标 | 应唯一；不唯一会导致看板行数放大 |
| qici + user_id | finance_dw.app_finance_performance_extend_details_hf, bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | 流量画像成交科目档位关联 | `traffic_profile.sql` 的 `dd` 先按 `qici + user_id + employee_email_name` 聚合，最终 join 未带 `employee_email_name`，需确认用户多顾问成交风险 |
| user_id + period_name | bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df, service_dw.dws_service_user_learn_detail_hf | 流量画像用户当期行课关联 | 行课表需由 `begin_time` 派生 `qici` 后与主表 `period_name` 对齐；同一用户当期多节课需再结合 `begin_time + ke_1` 或使用 `exists` 防止放大 |
| employee_email_name / name | temp_table.dingxi01_jiagou_db, temp_table.dingxi01_jiagou_zx, temp_table.dingxi01_pingyou_jg, bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df, finance_dw.app_finance_performance_extend_details_hf, dw.dim_employee_chain | 员工架构/财务流水/组织链映射 | 姓名可能不唯一，优先确认是否可用邮箱前缀替代；`consultant_sales_department_tenure.sql` 暂用 `org_t.name = dd_0.name` |
