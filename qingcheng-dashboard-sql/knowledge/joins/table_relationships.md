# 表关系

本文件记录青橙项目部看板中表与表、表与临时表、CTE 与 CTE 的关系。

## 1. 已确认或已入库关系

| 主表/CTE | 关联表/CTE | 关联条件 | 关系类型 | 数据粒度影响 | 来源 |
|---|---|---|---|---|---|
| `data` | `service_dw.dm_crm_lead_stats_detail_hf jt` | `data.lead_id = jt.lead_id` | 线索补充 | 若 `jt` 一线索多行会放大，需确认唯一性 | `qingcheng_process_data_raw_20260522.sql` |
| `data` | `temp_table.dingxi01_jiagou_db jg` | `data.employee_email_name = jg.employee_email_name and data.qici = jg.qici` | 架构补充 | `jg.department is not null` 会过滤未匹配架构的线索 | `qingcheng_process_data_raw_20260522.sql` |
| `data` | `temp_table.dingxi01_jiagou_db jg` | `data.employee_email_prefix = jg.employee_email_prefix and data.qici = jg.qici` | 架构补充 | `jg.department is not null` 会过滤未匹配架构的线索；与过程数据 raw 的姓名 join key 不一致 | `qingcheng_daoke_raw_20260522.sql` |
| `data` | `call_c` | `call_c.user_number = data.user_id and call_c.section_assign_employee_email_prefix = data.employee_email_prefix` | 外呼补充 | `call_c` 已按用户、线索、员工聚合；join 未使用 `lead_id`，是否可能串线索待确认 | `qingcheng_process_data_raw_20260522.sql` |
| `data` | `call_14d` | `call_14d.record_source = data.record_source and call_14d.process_lead_id = data.process_lead_id and call_14d.user_id = data.user_id and call_14d.employee_email_prefix = data.employee_email_prefix`；`call_14d` 内部用 `call_detail.lead_id = data.process_lead_id` | 14 天外呼补充 | 先在精确线索键粒度聚合分配后 `0-336` 小时的外呼事件，再回连线索；避免同用户同顾问多线索串数，且保持线索分母不变 | `data_center_qingcheng_2064.sql`；query id `1477067724` |
| `data` | `denglu_app` | `denglu_app.user_number = data.user_id` | 登录补充 | 用户级登录标记按线索汇总可能放大 | `qingcheng_process_data_raw_20260522.sql` |
| `data` | `daoke` | `data.employee_email_prefix = daoke.employee_email_prefix and data.qici = daoke.qici and data.lead_id = daoke.lead_id` | 到课补充 | `daoke` 内部按用户上课明细匹配，可能一线索多课 | `qingcheng_process_data_raw_20260522.sql` |
| `daoke` | `temp_table.dingxi01_qing_daoke ke` | `qici + channel_map_2/qudao + grade_1/grade + begin_time` | 课次标记 | 临时表唯一性影响第 1 至第 6 讲到课指标 | `qingcheng_process_data_raw_20260522.sql`, `qingcheng_daoke_raw_20260522.sql` |
| `gmv` | `ld` | `gmv.lead_id = ld.lead_id and ld.employee_email_name = gmv.performance_employee_email_name` | 订单补充线索属性 | 订单明细补充青橙渠道、投放计划、分配规则、主管和地域字段；若 `ld` 同一 `lead_id + employee_email_name` 多行，则渠道订单明细和转化订单明细都可能被放大 | `data_center_qingcheng_2460.sql`, `qingcheng_channel_order_detail_raw_20260627.sql` |
| `f` | `lrt` | `cast(f.lead_id as bigint) = lrt.crm_leads_id` | 原始线索补充 | 用于从青橙主宽表回查 CRM 原始线索状态、归因 source 和模型阶段；2026-06-27 小样本验证命中 30/30 | 数据地图 `data_lake_fuwu.dwd_crm_leads_rt` + query id `1433250612` |
| `dwd_transfer` | `bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf p` | `p.lead_id = dwd_transfer.prelead_id and p.lead_model_type = 1` | 潜客字段回补 | `dwd_transfer` 先由 `dwd_crm_leads_rt` 的 `previous_model_id` 得到；回补 TMK 顾问、渠道、年级时需按 `lead_id` 去重，严格青橙截面过滤会降低历史覆盖 | 2026-07-09 TMK 转移探查，query id `1456978632` |
| `tmk_prelead` | `temp_table.dingxi01_jiagou_db jg` | `tmk_prelead.qici = jg.qici and tmk_prelead.employee_email_name = jg.employee_email_name` | TMK 过程架构补充 | 2026-07-11 样本仅 8 条命中；未命中时可用潜客宽表虚拟三级/四级部门和直属小组长兜底，但必须保留原始组织名称 | query id `1459464455`, `1459472798` |
| `tmk_prelead` | `service_dw.app_h_crm_lead_employee_workload_detail_hf call` | `user_id + prelead_id/lead_id + employee_email_prefix` | TMK 外呼明细补充 | 2026-07-11 H 业务线潜客 99 条中 81 条命中；宽表与明细总外呼次数、接通次数、总通时汇总一致，单次 `call_duration > 480` 用于精确计算 8min 人数 | query id `1459484750` |
| `data_lake_fuwu.dwd_crm_leads_rt lead` | `data_lake_fuwu.dwd_crm_leads_rt prelead` | `lead.previous_model_id = prelead.crm_leads_id` | 潜客转正常线索 | `prelead.model_type=1` 且意向为青橙 TMK/规划系统；`lead.model_type=0` 且 `previous_model_id>0`；一条转移线索可能出现多条上一阶段记录，明细输出需按转移线索 ID 去重 | 2026-07-09 query id `1456961079`, final query id `1457006107` |
| `dwd_transfer` | `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf o` | `dwd_transfer.transfer_lead_id = o.lead_id` | 成交补充 | 只用转移后的正常线索 ID 关联业财；金额字段按分转元；需加 `performance_second_level_department_name='青橙项目部'` 和课程部门白名单 | 2026-07-09 当前 TMK 转移样本成交金额、退费金额、净金额均为 0 |
| `gmv_order` | `finance_dw.dwd_finance_order_refund_df r` | `gmv_order.order_number = r.order_number` | 退费原因补充 | 先按青橙结果期次得到去重订单集合，再读取原因表；同一订单多原因必须先按订单+原因聚合，原因金额只作订单退款分摊权重 | `qingcheng_refund_reason_analysis_20260718.sql`；退款类型与分摊语义待确认 |
| `dwd_transfer` | `service_dw.dwd_crm_assign_private_detail_hf p` | `dwd_transfer.transfer_lead_id = p.lead_id` | 分配历史补充 | 一条正常线索可对应多个 `private_sea_id` 和顾问；直接 join 会放大。历史链路保留全部私海记录，首次/当前候选必须按表文档去重；当前承接顾问由截面表最终确认 | query id `1466169274`, `1466174917`, `1466178403`, `1466187134` |
| `dd` | `prc` | `prc.lead_id = dd.lead_id and prc.employee_email_name = dd.performance_employee_email_name and prc.rn = 1` | 订单补充线索期次 | `prc` 取每个 lead 最新线索期次，0615 起主要用于补充分配时间；当期判断改为 `dd.qici0 = dd.period` | `data_center_qingcheng_2460.sql` |
| `dd` | `order_change` | `dd.order_number = order_change.order_number` | 调课调班识别 | 用于识别内部调课调班/转课链路，配合 service 明细 `transfer_in_amount / transfer_out_amount` 排除内部金额 | `data_center_qingcheng_2460.sql` |
| `dd` | `re_ke` | `re_ke.order_number = dd.order_number` | 退款节次补充 | 用于计算 `refund_4` 和点睛 2 节退费口径，不替代主营收来源 | `data_center_qingcheng_2460.sql` |
| `bb_dedup` | `ud` | `ud.name = bb1.employee_email_name and ud.qici = bb1.qici and ud.qudao = bb1.channel_map_2 and ud.grade_0 = bb1.grade_1 and ud.zhuguan = bb1.virtual_direct_leader_email_name` | 线索量和业绩合并 | full outer join；当前版本已补上年级和主管维度，修复同顾问同渠道跨年级吞数问题 | `data_center_qingcheng_2460.sql` |
| `mm` | `temp_table.dingxi01_qing_team_jg jg` | `mm.employee_email_name = jg.employee_email_name and mm.qici = jg.qici` | 团队架构补充 | 按结果期次回填历史团队架构，避免未来上传新架构后覆盖历史期次归属 | `data_center_qingcheng_2460.sql` |
| `dd_0` | `org_t` | `ot.name = dd_0.name and dd_0.trade_time >= ot.begin_time and dd_0.trade_time <= ot.end_time` | 员工任职期间过滤 | left join 后 where 限定组织时间，未匹配组织链的交易被剔除 | `qingcheng_revenue_year_quarter_month_raw_20260522.sql` |
| `rd` | `temp_table.dingxi01_qing_zz zz` | `zz.employee_email_name = rd.name` | 组织架构补充 | 未按期次 join，若架构表多行会放大 | `qingcheng_revenue_year_quarter_month_raw_20260522.sql` |
| `dd_0` | `org_t` | `ot.name = a.name and coalesce(a.paid_time, a.trade_time) between ot.begin_time and ot.end_time` | 员工任职期间过滤 | inner join，仅保留原始成交时间落在青橙任职窗口内的记录，避免历史订单在转岗后退款被误计入青橙 | `qingcheng_team_completion_month_raw_20260522.sql`, `qingcheng_team_completion_period_raw_20260522.sql`, `qingcheng_personal_conversion_raw_20260522.sql` |
| `ord` | `order_change` | `ord.order_number = order_change.order_number` | 退款订单补充调课调班类型 | `order_change` 已从订单号、父订单号、原始订单号、最新子订单号展开并按订单号聚合 | `qingcheng_team_completion_month_raw_20260522.sql` |
| `rd` | `order_change` + service transfer 标记 | `rd.order_number = order_change.order_number`；service transfer 来自 `order_attr` 按 `order_number + performance_employee_email_name` 聚合后随 `dd/gmv/rd` 传递 | 主交易层识别内部调课调班调入/调出 | 命中 finance 订单变更链路或 service `transfer_in_amount/transfer_out_amount` 补充标记后，不进入 `income`、`refund`、`refund_4` 和科目数，避免 `调出退款` 或正向调入被误算为外部业绩 | `qingcheng_personal_conversion_raw_20260522.sql`, `qingcheng_team_completion_month_raw_20260522.sql`, `qingcheng_team_completion_period_raw_20260522.sql` |
| `rd` | `re_ke` | `re_ke.qici_re = rd.qici and re_ke.order_number = rd.order_number` | 交易补充退款行课节数 | 用 `full_refund_chain_finish_lesson_count` 影响 `refund_4` | `qingcheng_team_completion_month_raw_20260522.sql` |
| `rd_0` | `temp_table.dingxi01_qing_qi_moth qm` | `qm.qici = rd_0.qici` | 期次映射月份 | 若期次缺少月份映射，实际业绩无法匹配月目标 | `qingcheng_team_completion_month_raw_20260522.sql` |
| `wa` | `temp_table.dingxi01_qing_team_jg qtg` | `qtg.employee_email_name = wa.name`，取最新 `qici` | 员工补充直属主管 | 使用最新团队架构，可能产生历史架构漂移 | `qingcheng_team_completion_month_raw_20260522.sql` |
| `temp_table.dingxi01_qing_team_goal qg` | `renchan rc` | `qg.xiaozu = rc.leader_employee_email_name and qg.month = rc.moth` | 月目标与实际合并 | 以目标表为主，即使无实际也保留目标行 | `qingcheng_team_completion_month_raw_20260522.sql` |
| `wa` | `temp_table.dingxi01_qing_team_jg qtg` | `qtg.employee_email_name = wa.name`，取最新 `qici` | 员工补充直属主管 | 使用最新团队架构，可能产生历史架构漂移 | `qingcheng_team_completion_period_raw_20260522.sql` |
| `temp_table.dingxi01_qing_team_g_qi qg` | `renchan rc` | `qg.xiaozu = rc.leader_employee_email_name and qg.qici = rc.qici` | 期次目标与实际合并 | 以期目标表为主，即使无实际也保留目标行 | `qingcheng_team_completion_period_raw_20260522.sql` |
| `temp_table.dingxi01_qing_team_jg qtg` | `wa` | `qtg.employee_email_name = wa.name and qtg.qici = wa.qici` | 个人架构合并业绩 | 以架构表为主，未匹配业绩的人员保留 0 指标；若架构表一人一期多行会放大 | `qingcheng_personal_conversion_raw_20260522.sql` |
| `temp_table.dingxi01_qing_team_jg qtg` | `temp_table.dingxi01_qing_qi_moth qm` | `qm.qici = qtg.qici` | 架构期次补充月份 | 缺少月份映射时 `moth` 为空，但人员行仍保留 | `qingcheng_personal_conversion_raw_20260522.sql` |
| `data` (CTE) | `f_call0` (CTE, from `service_dw.app_h_crm_lead_task_process_info_detail_hf`) | `period_name + employee_email_name = assign_employee_email_name + user_id + lead_id = call_answer_lead_count` | 线索补充 F 类外呼 | join 未使用 `lead_id` 精确匹配（`call_answer_lead_count` 语义非 ID），可能放大；若 `call_answer_lead_count` 不是唯一标识符，同一线索可能匹配多条 F 类外呼 | `qingcheng_conversion_wide_table_market_channel_20260611.sql` |
| `zhuanhua` (CTE) | `temp_table.shenbaoxin_channel_group` | `channel = channel_map` | 渠道大类补充 | 若临时表 channel 不唯一会放大聚合结果 | `qingcheng_conversion_wide_table_market_channel_20260611.sql` |

## 2. 待确认关系

| 主表 | 关联表 | 关联条件 | 疑问 |
|---|---|---|---|
| `data` | `call_c` | `user_id + employee_email_prefix` | `call_c` 聚合含 `lead_id`，但 join 未带 `lead_id`；是否会把同用户同顾问多线索外呼复制到多条线索待确认 |
| `data` | `denglu_app` | `user_id = user_number` | APP 登录是用户级，最终按线索汇总可能不是去重用户数 |
| `data` | `temp_table.dingxi01_jiagou_db` | `employee_email_name + qici` | 架构表是否一人一期唯一待确认 |
| `data` | `temp_table.dingxi01_jiagou_db` | `employee_email_prefix + qici` | 到课 raw 使用邮箱前缀 join；需确认和 `employee_email_name` 哪个是标准架构 key |
| `daoke` | `temp_table.dingxi01_qing_daoke` | `qici + channel_map_2 + grade_1 + begin_time` | 首节课映射表是否唯一待确认 |
| `bb_dedup` | `ud` | `employee_email_name + qici + channel_map_2 + grade_1 + virtual_direct_leader_email_name` | 当前版本已补齐年级和主管维度；若同一维度组合仍有多行，`row_number()` 保留一条是否合理待确认 |
| `dd_0` | `org_t` | `name + coalesce(paid_time, trade_time) between begin_time and end_time` | 是否应使用 `email_prefix` 代替 `name`，避免重名误匹配；同时不能只按 `trade_time` 过滤，否则历史订单在转岗后退款会串入青橙 |
| `rd` | `temp_table.dingxi01_qing_zz` | `employee_email_name` | 架构表是否一员工唯一、是否需要期次/日期字段待确认 |
| `rd` | `re_ke` | `order_number + qici/qici_re` | 全退期次按 `full_refund_timestamp` 计算，和交易期次 `rd.qici` 相等时才匹配；是否符合退费归属口径待确认 |
| `gmv` | `ld` | `lead_id + performance_employee_email_name = employee_email_name` | `ld` 子查询只按 `dt/hour` 过滤，没有显式 `青橙项目部` 范围限定；是否完全安全依赖订单侧业绩部门过滤待确认 |
| `qg` | `renchan` | `xiaozu = leader_employee_email_name and month = moth` | `qg.xiaozu` 字段是否存主管邮箱而非小组名称待确认 |
| `qg` | `renchan` | `xiaozu = leader_employee_email_name and qici = qici` | 期目标表 `xiaozu` 字段是否存主管邮箱而非小组名称待确认 |
| `qtg` | `wa` | `employee_email_name + qici` | 个人转化要求架构表一人一期唯一，否则个人业绩可能被重复计算 |
| `data` | `f_call0` | `period_name + employee_email_name + user_id + lead_id` | `call_answer_lead_count` 字段名为"计数"但作为 `lead_id` 使用，语义矛盾；join 是否精准匹配待确认 |
| `zhuanhua` | `shenbaoxin_channel_group` | `channel = channel_map` | 临时表的 `channel` 字段枚举值是否全覆盖 CASE WHEN 输出的 `channel_map` 值待确认；未匹配时 `channel_1` 为 null |

## 3. 维护规则

- 如果 join 后改变数据粒度，必须说明是否需要去重、窗口函数或先聚合后 join。
- 如果 join 到临时表，必须同步检查 `knowledge/temp_tables/` 的适用边界。
- 用户后续提供修正版 SQL 时，应优先核对本文件中的待确认关系。
- 青橙个人完成度/个人转化的 `gmv_t` 属于先聚合后 union 的特殊链路，调课调班必须按订单/课程粒度聚合；若按人员/用户粒度聚合，会改变退款和课程部门入桶结果。
