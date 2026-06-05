# 表索引

> 由 `scripts/import_baijia_external_knowledge.py` 根据百家字段目录和既有临时表文档更新。库名前缀或字段口径为待确认时，生成生产 SQL 前必须人工确认。所有表在 Web 查询环境（Playwright）中均可正常使用。

| 完整表名 | 中文名 | 数据粒度 | 分区字段 | 小时表 | 库名前缀状态 | 字段校验状态 |
|---|---|---|---|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | 线索成本转化沟通行课全链路数据 | 线索-渠道-转化全链路明细，小时快照粒度待确认。 | dt, hour | 是 | 已确认 | 字段目录已补全；已记录流量画像 `city_channel` 省市维度，口径需人工校验 |
| dw.dim_employee_chain | 员工信息表 | 员工-部门路径-任职时间段粒度，字段来自 Word 文档 | dt | 否 | 已确认 | 已根据 `E:\2000_work\GAOTU\员工信息表.docx` 补全 33 个非分区字段，主键唯一性待确认 |
| dw.dim_cstm_active_user_c_appliction_mb_df | c端用户全量表应用粒度 | 用户-应用粒度，待确认 | dt | 否 | 已确认 | 字段目录已补全，口径需人工校验 |
| dw.dws_user_active_user_c_appliction_hf | c端用户活跃表应用粒度_当日小时全量 | 用户-应用-小时粒度，待确认 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验 |
| finance_dw.app_finance_performance_extend_details_hf | 业绩归属信息扩展表 | 订单/交易明细-小时快照粒度，字段来自 Word 文档，指标口径需结合历史 SQL 校验 | dt, hour | 是 | 已确认 | 已根据 `E:\2000_work\GAOTU\新建 Microsoft Word 文档.docx` 补全 145 个非分区字段 |
| finance_dw.dwd_finance_order_refund_df | 订单退款明细表 | 待确认；根据退费原因分析 SQL 推断为订单退款记录粒度 | dt | 否 | 已确认 | 根据 `resources/raw_sql/refund_reason_analysis.sql` 补充最小字段，真实 DDL 待确认 |
| finance_dw.dim_finance_employee_df | 员工维表 | 员工-日级快照粒度，字段来自 Word 文档 | dt | 否 | 已确认 | 已根据 `E:\2000_work\GAOTU\员工维表.docx` 补全 42 个非分区字段 |
| gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf | 顾问首call数据分析表 | 用户-顾问账号-首call任务-小时快照粒度，字段来自 Word 文档 | dt, hour | 是 | 已确认 | 已根据 `E:\2000_work\GAOTU\顾问首call数据分析表.docx` 补全 19 个非分区字段；2026-05-22 起作为 `is_f_call` 首 call 任务强制来源 |
| service_dw.app_h_crm_lead_employee_workload_detail_hf | 高中顾问工作量看板 | 顾问-小时粒度，待确认 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验 |
| service_dw.app_h_crm_lead_task_process_info_detail_hf | 高中线索服务跟进明细 | 线索-任务-小时粒度，待确认 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验；禁止再用 `call_answer_lead_count` 作为首 call 任务指标来源 |
| service_dw.app_user_attribute_label_gaia_wide_df | 盖亚系统用户标签数据宽表 | 用户-标签粒度，待确认 | dt | 否 | 已确认 | 字段目录已补全，口径需人工校验 |
| service_dw.dim_crm_assign_rule_lead_detail_hf | 线索分配规则记录 | 待确认；字段目录未提供数据粒度 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验 |
| service_dw.dm_crm_lead_stats_detail_hf | 线索统计公共明细层 | 线索-小时粒度，待确认 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验 |
| service_dw.dm_crm_trace_lead_full_link_data_hf | 线索留痕宽表 | 待确认；字段目录未提供数据粒度 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验 |
| service_dw.dwd_crm_assign_private_detail_hf | crm分配私海记录表 | 用户/线索-顾问-小时粒度，待确认 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验 |
| service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | 归因流水粒度统计明细表 | 订单-流水-业绩归属-小时快照粒度，字段来自 Word 文档 | dt, hour | 是 | 已确认 | 已根据 `E:\2000_work\GAOTU\归因流水粒度统计明细表.docx` 补全 184 个非分区字段 |
| service_dw.dws_service_user_learn_detail_hf | 小时级行课数据全量 | 用户-课程-小时粒度，待确认 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验 |
| service_dw.dws_service_wechat_call_detail_df | 沟通电话微信明细表 | 待确认；字段目录未提供数据粒度 | dt | 否 | 已确认 | 字段目录已补全，口径需人工校验 |
| service_dw.dim_crm_assign_rule_plan_item_info_hf | 分配规则计划 item 信息表 | 待确认；根据 SQL 推断为 rule_id + plan_id + employee_email_name 或计划 item 小时快照粒度 | dt, hour | 是 | 已确认 | 根据 `resources/raw_sql/lead_assign_plan_actual_valid_count.sql` 补充最小字段，真实 DDL 待确认 |
| temp_table.dingxi01_channel_group | 渠道分组映射表 | 渠道映射粒度，待确认。理论上一行对应一个 `channel`。 | 无 | 否 | 已确认 | 保留原整理 |
| temp_table.shenbaoxin_channel_group | 渠道分组映射表（申保鑫） | 渠道映射粒度，字段来自 SQL 使用字段推断，待确认 | 无 | 否 | 已确认 | 根据 `resources/raw_sql/h_biz_line_department_conversion.sql` 补充使用字段；2026-06-05 后不再用于到课 raw SQL，真实字段类型和维护来源待确认 |
| temp_table.dingxi01_cost | 渠道成本目标表 | 渠道-年级-期次粒度，待确认。 | 无 | 否 | 已确认 | 保留原整理 |
| temp_table.dingxi01_daoke_1_6_t | 到课课次映射表 | 渠道-期次-年级-开课时间-课次粒度。来自 `daoke_t_one_six.xlsx`，数据行 2862 行、字段 7 个，存在 1 条空行；join key 存在重复，使用前建议去重。 | 无 | 否 | 已确认 | 已按 Excel 补全字段、样例和 key 重复检查 |
| temp_table.dingxi01_jiagou_db | 架构映射表 | 顾问-期次-架构映射粒度。来自 `jiagou_xian_zhengzhou.xlsx`，数据行 5017 行、字段 10 个，存在 7 条空行；join key 存在少量重复。 | 无 | 否 | 已确认 | 已按 Excel 补全字段、样例和 key 重复检查 |
| temp_table.dingxi01_jiagou_zx | 员工专项架构映射表 | 顾问-专项架构粒度。来自 `jiagou2026_zx.xlsx`，数据行 885 行、字段 7 个；无 qici 字段，跨期使用需确认。 | 无 | 否 | 已确认 | 已按 Excel 补全字段、样例和 key 重复检查 |
| temp_table.dingxi01_pingyou_jg | 评优架构人产临时表 | 顾问-期次-渠道-年级-架构粒度。来自 `pingyou_jg.xlsx`，数据行 1220 行、字段 14 个，存在 1 个空表头列且已忽略。 | 无 | 否 | 已确认 | 已按 Excel 补全字段、样例和 key 重复检查 |
| temp_table.dingxi01_plan_id | 市场顾问分配计划组 ID 维护表 | 期次-规则组粒度；来自 `plan_id.xlsx`，数据行 51 行、字段 4 个；`qici + group_id` 唯一，`group_id` 单字段跨期重复 | 无 | 否 | 已确认 | 已按 Excel `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\plan_id.xlsx` 补全字段、样例和 key 重复检查 |
