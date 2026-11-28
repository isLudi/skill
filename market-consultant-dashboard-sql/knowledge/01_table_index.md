# 表索引

当前表名按维护账号迁移登记使用。下表保留的旧 Excel 样本行数、字段扫描和重复检查属于迁移前历史证据，不证明新表本次数据完整性；评优来源例外以当前线上 SQL 回读为准。

> 物理表字段由 `usql-web-query-operator sync-datamap-fields` 从天工数据地图同步，临时表继续由本 Skill 的 SQL/表格证据维护。库名前缀或业务口径待确认时，生成生产 SQL 前必须人工确认。除状态栏明确标注权限待开通的表外，其余表已在 Web 查询环境（Playwright）中使用。

| 完整表名 | 中文名 | 数据粒度 | 分区字段 | 小时表 | 库名前缀状态 | 字段校验状态 |
|---|---|---|---|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | 线索成本转化沟通行课全链路数据 | 线索-渠道-转化全链路明细，小时快照粒度待确认。 | dt, hour | 是 | 已确认 | 字段目录已补全；已确认可用期次联合键和渠道组逻辑关联，仍需按具体数据集校验历史覆盖 |
| bdg_ba.dws_crm_order_income_refund_period_detail_hf | 订单业绩收退款流水期归因明细 | 正价课现金流水/MBR 事实源，订单+交易时间+收退款类型粒度 | dt, hour | 是 | 已确认 | 数据地图表 ID 36724；与 GMV 促销流水分支 UNION ALL，禁止金额明细直连 |
| dw.dim_employee_chain | 员工信息表 | 员工-部门路径-任职时间段粒度，字段来自 Word 文档 | dt | 否 | 已确认 | 已根据 `E:\2000_work\GAOTU\员工信息表.docx` 补全 33 个非分区字段，主键唯一性待确认 |
| dw.dim_cstm_active_user_c_appliction_mb_df | c端用户全量表应用粒度 | 用户-应用粒度，待确认 | dt | 否 | 已确认 | 字段目录已补全，口径需人工校验 |
| dw.dws_user_active_user_c_appliction_hf | c端用户活跃表应用粒度_当日小时全量 | 用户-应用-小时粒度，待确认 | dt, hour | 是 | 已确认 | 字段目录已补全，口径需人工校验 |
| fairy_data_center.dwd_service_reach_wide_channel_subtask_prod_v2_di | 触达发送明细宽表 | 通道子任务粒度；`channel_subtask_id` 唯一性待实测 | dt | 否 | 已确认 | 数据地图表 ID 35146，当前返回 50 个普通字段和 1 个分区字段；市场顾问人群、线索挂接、接通及好友指标需另行确认 |
| finance_dw.app_finance_order_income_refund_info_df | 订单收款退款交易信息表 | 收退款交易明细-日全量快照；精确流水唯一键待 USQL 验证 | dt | 否 | 已确认 | 数据地图已登记 86 个非分区字段和 1 个分区字段；与 GMV Communication 候选桥为用户+归属人，禁止未经唯一化直接明细 Join |
| finance_dw.app_finance_performance_extend_details_hf | 业绩归属信息扩展表 | 订单/交易明细-小时快照粒度，字段来自 Word 文档，指标口径需结合历史 SQL 校验 | dt, hour | 是 | 已确认 | 已根据 `E:\2000_work\GAOTU\新建 Microsoft Word 文档.docx` 补全 145 个非分区字段 |
| finance_dw.dwd_finance_order_refund_df | 订单退款明细表 | 待确认；当前 2353 退费原因分析按订单关联该表 | dt | 否 | 已确认 | 已结合数据地图和当前 `resources/raw_sql/data_center_market_2353.sql` 补充字段；主键仍待确认 |
| finance_dw.dim_finance_employee_df | 员工维表 | 员工-日级快照粒度，字段来自 Word 文档 | dt | 否 | 已确认 | 已根据 `E:\2000_work\GAOTU\员工维表.docx` 补全 42 个非分区字段 |
| gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf | 顾问首call数据分析表 | 用户-顾问账号-首call任务-小时快照粒度，字段来自 Word 文档 | dt, hour | 是 | 已确认 | 已根据 `E:\2000_work\GAOTU\顾问首call数据分析表.docx` 补全 19 个非分区字段；2026-05-22 起作为 `is_f_call` 首 call 任务强制来源 |
| da.app_dim_jp_channel_case_version_df | 精品班飞书渠道映射版本表 | 日全量规则版本快照；单分区唯一键待验证 | dt | 否 | 已确认 | 数据地图已登记 8 个非分区字段和 1 个分区字段；仅保存完整 CASE 文本和版本元数据，不能直接 Join 产出 `channel_map` |
| data_lake_ods.ods_ones_business_agent_ai_add_friend_record_rt | 添加好友记录 | 添加好友事件粒度；id 与 task_id + user_id 唯一性待实测 | 无 | 否 | 已确认 | 数据地图表 ID 36507，Iceberg 全量表，12 个字段。业务确认 `source_type=2` 为私海全AI外呼，`3` 为公海全AI外呼。`status=3` 为接口失败，`99` 为已经好友无需添加 |
| data_lake_fuwu.dwd_crm_call_tmk_record_rt | 先驱通话原始记录候选表 | 通话事件粒度，受限样本 `call_id` 唯一 | 无 | 否 | 已确认 | 数据地图表 ID 34742，11 个字段。两批样本按 `call_id` 对应先驱小时表，AI 接通样本时长均为 0。接通与挂断时间缺独立字段 |
| gaotu_hl.dim_mkt_h_lead_channel_df | 市销线索渠道映射表 | 单日快照内 `lead_id` 唯一；跨分区重复 | dt | 否 | 已确认 | 已登记 15 个非分区字段和 1 个分区字段；按单分区 `lead_id` Join 不放大，但市场顾问宽表全量覆盖仅 24.3341%，当前禁止直接替换渠道 CASE |
| gaotu_hl.dim_mkt_h_period_map_df | H业务线标准期名映射表 | 系统期名到标准期名映射快照粒度；`department + source_period_name` 唯一性已验证 | dt | 否 | 已确认 | 已从天工数据地图登记 10 个非分区字段和 1 个分区字段；与全链路宽表的期次 Join 已验证无 1:N 放大 |
| gaotu_hl.dim_mkt_h_period_df | H业务线标准期次映射表 | 标准期次日历快照粒度，联合键和唯一性待验证 | dt | 否 | 已确认 | 已从天工数据地图登记 17 个非分区字段和 1 个分区字段；Join 基数待权限审批后验证 |
| gaotu_hl.ods_mkt_h_channel_group_df | H业务线渠道分类表 | 渠道-渠道大类-适用学部映射粒度；当前快照 `department_name + channel` 唯一性已验证 | dt | 否 | 已确认 | 已从天工数据地图登记 3 个非分区字段和 1 个分区字段；与宽表需先关联派生 `channel_map`，bounded CASE 探针已验证渠道组侧最大匹配行数为 1 |
| gaotu_hl.ods_mkt_h_channel_rule_df | H业务线渠道映射原文表 | 学部-期次-完整 CASE 文本快照；单分区唯一性待验证 | dt | 否 | 已确认 | 数据地图已登记 3 个非分区字段和 1 个分区字段；当前 SQL 查询权限未开通，仅保存规则文本，不能直接 Join 产出 `channel_map` |
| one_dw.dwd_mkt_ai_assistant_asr_record_df | 语音通话 ASR 记录 | 解析任务粒度待确认；同录音 URL 可多条 | dt | 否 | 已确认 | 数据地图登记 11 个字段；20260915 分区探针证实 URL 关联存在 1:N 风险 |
| one_dw.dwd_mkt_tmk_call_record_hf | 先驱通话记录表 | 通话记录小时全量快照粒度；`call_id` 唯一性待实测 | dt, hour | 是 | 已确认 | 数据地图表 ID 22814，23 个普通字段和 2 个分区字段；本表接通=1，2026-11-08 受限样本与原始表接通=33逐通对账一致 |
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
| service_dw.ods_service_ai_ones_business_copilot__call_record_df | AI 途途通话记录表 | 通话事件粒度待确认；`unique_key` 与 `call_id` 唯一性待核 | dt | 否 | 已确认 | 数据地图登记 21 个字段；业务范围需通过线索人群限定，ASR 直连有放大风险 |
| service_dw.ods_service_ai_ones_business_copilot__ai_call_analysis_result_df | 语音分析结果表 | 分析记录粒度待确认；有效 `call_id` 唯一性仅受限样本验证 | dt | 否 | 已确认 | 数据地图登记 16 个字段；`is_del` 是 bigint，候选关联为同分区 `call_id` |
| service_dw.dim_crm_assign_rule_plan_item_info_hf | 分配规则计划 item 信息表 | 待确认；根据 SQL 推断为 rule_id + plan_id + employee_email_name 或计划 item 小时快照粒度 | dt, hour | 是 | 已确认 | 根据 `resources/raw_sql/lead_assign_plan_actual_valid_count.sql` 补充最小字段，真实 DDL 待确认 |
| temp_table.shenbaoxin_channel_group | 渠道分组映射表（申保鑫） | 渠道映射粒度，字段来自 SQL 使用字段推断，待确认 | 无 | 否 | 已确认 | 根据 `resources/raw_sql/h_biz_line_department_conversion.sql` 补充使用字段；2026-06-05 后不再用于到课 raw SQL，真实字段类型和维护来源待确认 |
| temp_table.lvshuai01_daoke_1_6_t | 当前市场到课课次映射表 | 按期次、渠道、年级、开课时间与课次管理；当前唯一性需实测 | 无 | 否 | 生产 SQL 与治理登记已核对 | 登记七个上传列，当前类型、重复与空值未提升为已确认物理契约 |
| temp_table.lvshuai01_jiagou_db | 当前市场期次带班架构映射表 | 市场登记键为 qici + employee_email_prefix；跨部门共用物理表 | 无 | 否 | 生产 SQL 与治理登记已核对 | 本域限定 dept_1 为市场顾问部；当前类型、唯一性及其他部门语义独立核验 |
| temp_table.lvshuai01_channel_group | 当前渠道分组关联表 | 现有登记或SQL关联粒度，唯一性待实测 | 结构待核验 | 待确认 | 实时SQL绑定已核对 | 字段来自本域登记或当前SQL引用，类型与新业务合同未自动确认 |
| temp_table.lvshuai01_cost | 当前市场渠道成本目标表 | 现有登记或SQL关联粒度，唯一性待实测 | 结构待核验 | 待确认 | 实时SQL绑定已核对 | 字段来自本域登记或当前SQL引用，类型与新业务合同未自动确认 |
| temp_table.lvshuai01_jiagou_zx | 当前员工专项架构关联表 | 现有登记或SQL关联粒度，唯一性待实测 | 结构待核验 | 待确认 | 实时SQL绑定已核对 | 字段来自本域登记或当前SQL引用，类型与新业务合同未自动确认 |
| temp_table.lvshuai01_plan_id | 当前市场分配计划组ID表 | 现有登记或SQL关联粒度，唯一性待实测 | 结构待核验 | 待确认 | 实时SQL绑定已核对 | 字段来自本域登记或当前SQL引用，类型与新业务合同未自动确认 |
| temp_table.lvshuai01_jinliang_goal | 当前市场进量目标表 | 现有登记或SQL关联粒度，唯一性待实测 | 结构待核验 | 待确认 | 实时SQL绑定已核对 | 字段来自本域登记或当前SQL引用，类型与新业务合同未自动确认 |
| temp_table.zhangjunyan01_pingyou_jg | 评优架构及新人承接期次表 | 顾问与期次关联；当前唯一性须核验 | 结构待核验 | 按业务范围 | 平台解析已核对；模型 2688 已使用 | 用户已接受新旧数据差异；14 列输出均为 string，当前期次覆盖须核验 |
| temp_table.lvshuai01_ceshiqudao_pingyou | 评优测试渠道指标表 | 期次、渠道、姓名候选粒度；唯一性待核验 | 结构待核验 | 按业务范围 | 平台解析已核对 | 6 列输出均为 string；历史模型先按姓名聚合 |
| temp_table.lvshuai01_jiagou_xinren | 新人入组期次 | 2688 按 prefix+账号聚合 max(new_qici)，不等于评优承接序号 x_qi_count。 | 待核实 | 否 | 线上使用关系已核实 | 保留与评优架构的独立来源和 Join |
