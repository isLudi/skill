# 表索引

> 物理表字段由 `usql-web-query-operator sync-datamap-fields` 从天工数据地图同步，临时表继续由本 Skill 的 SQL/表格证据维护。库名前缀或业务口径待确认时，生成生产 SQL 前必须人工确认。除状态栏明确标注权限待开通的表外，其余表已在 Web 查询环境（Playwright）中使用。

| 完整表名 | 中文名 | 数据粒度 | 分区字段 | 小时表 | 库名前缀状态 | 字段校验状态 |
|---|---|---|---|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | 线索成本转化沟通行课全链路数据 | 线索-渠道-转化全链路明细，小时快照粒度待确认。 | dt, hour | 是 | 已确认 | 字段目录已补全；已确认可用期次联合键和渠道组逻辑关联，仍需按具体数据集校验历史覆盖 |
| dw.dim_employee_chain | 员工信息表 | 员工-部门路径-任职时间段粒度，字段来自 Word 文档 | dt | 否 | 已确认 | 已根据 `E:\2000_work\GAOTU\员工信息表.docx` 补全 33 个非分区字段，主键唯一性待确认 |
| dw.dim_cstm_active_user_c_appliction_mb_df | c端用户全量表应用粒度 | 用户-应用粒度，待确认 | dt | 否 | 已确认 | 字段目录已补全，口径需人工校验 |
| dw.dws_user_active_user_c_appliction_hf | c端用户活跃表应用粒度_当日小时全量 | 用户-应用-小时粒度，待确认 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验 |
| finance_dw.app_finance_performance_extend_details_hf | 业绩归属信息扩展表 | 订单/交易明细-小时快照粒度，字段来自 Word 文档，指标口径需结合历史 SQL 校验 | dt, hour | 是 | 已确认 | 已根据 `E:\2000_work\GAOTU\新建 Microsoft Word 文档.docx` 补全 145 个非分区字段 |
| finance_dw.dwd_finance_order_refund_df | 订单退款明细表 | 待确认；当前 2353 退费原因分析按订单关联该表 | dt | 否 | 已确认 | 已结合数据地图和当前 `resources/raw_sql/data_center_market_2353.sql` 补充字段；主键仍待确认 |
| finance_dw.dim_finance_employee_df | 员工维表 | 员工-日级快照粒度，字段来自 Word 文档 | dt | 否 | 已确认 | 已根据 `E:\2000_work\GAOTU\员工维表.docx` 补全 42 个非分区字段 |
| gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf | 顾问首call数据分析表 | 用户-顾问账号-首call任务-小时快照粒度，字段来自 Word 文档 | dt, hour | 是 | 已确认 | 已根据 `E:\2000_work\GAOTU\顾问首call数据分析表.docx` 补全 19 个非分区字段；2026-05-22 起作为 `is_f_call` 首 call 任务强制来源 |
| da.app_dim_jp_channel_case_version_df | 精品班飞书渠道映射版本表 | 日全量规则版本快照；单分区唯一键待验证 | dt | 否 | 已确认 | 数据地图已登记 8 个非分区字段和 1 个分区字段；仅保存完整 CASE 文本和版本元数据，不能直接 Join 产出 `channel_map` |
| gaotu_hl.dim_mkt_h_lead_channel_df | 市销线索渠道映射表 | 单日快照内 `lead_id` 唯一；跨分区重复 | dt | 否 | 已确认 | 已登记 15 个非分区字段和 1 个分区字段；按单分区 `lead_id` Join 不放大，但市场顾问宽表全量覆盖仅 24.3341%，当前禁止直接替换渠道 CASE |
| gaotu_hl.dim_mkt_h_period_map_df | H业务线标准期名映射表 | 系统期名到标准期名映射快照粒度；`department + source_period_name` 唯一性已验证 | dt | 否 | 已确认 | 已从天工数据地图登记 10 个非分区字段和 1 个分区字段；与全链路宽表的期次 Join 已验证无 1:N 放大 |
| gaotu_hl.dim_mkt_h_period_df | H业务线标准期次映射表 | 标准期次日历快照粒度，联合键和唯一性待验证 | dt | 否 | 已确认 | 已从天工数据地图登记 17 个非分区字段和 1 个分区字段；Join 基数待权限审批后验证 |
| gaotu_hl.ods_mkt_h_channel_group_df | H业务线渠道分类表 | 渠道-渠道大类-适用学部映射粒度；当前快照 `department_name + channel` 唯一性已验证 | dt | 否 | 已确认 | 已从天工数据地图登记 3 个非分区字段和 1 个分区字段；与宽表需先关联派生 `channel_map`，bounded CASE 探针已验证渠道组侧最大匹配行数为 1 |
| gaotu_hl.ods_mkt_h_channel_rule_df | H业务线渠道映射原文表 | 学部-期次-完整 CASE 文本快照；单分区唯一性待验证 | dt | 否 | 已确认 | 数据地图已登记 3 个非分区字段和 1 个分区字段；当前 SQL 查询权限未开通，仅保存规则文本，不能直接 Join 产出 `channel_map` |
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
| temp_table.dingxi01_pingyou_jg | 评优架构 / 新人承接期次临时表 | 顾问-期次-架构粒度。当前 `pingyou_jg.xlsx` 仅含 `Sheet4`，数据行 5920 行、字段 14 个；`employee_email_name + qici` 唯一。 | 无 | 否 | 已确认 | 2026-07-21 已验证 `x_qi_count` 仅为 1/2/3/4/9，顾问有效序号不重复，模型 2688 使用本表 |
| temp_table.zhangjunyan01_pingyou_jg | 评优架构人产临时表 | 顾问-期次-渠道-年级-架构粒度。来自 `pingyou_jg.xlsx`，数据行 1220 行、字段 14 个，存在 1 个空表头列且已忽略。 | 无 | 否 | 已确认 | 已按 Excel 补全字段、样例和 key 重复检查 |
| temp_table.dingxi01_plan_id | 市场顾问分配计划组 ID 维护表 | 期次-规则组粒度；来自 `plan_id.xlsx`，数据行 51 行、字段 4 个；`qici + group_id` 唯一，`group_id` 单字段跨期重复 | 无 | 否 | 已确认 | 已按 Excel `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\plan_id.xlsx` 补全字段、样例和 key 重复检查 |
