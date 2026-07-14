# 常用 join key

本文件只记录青橙项目部已确认或从青橙历史 SQL 抽取的 join key。

| 左表/CTE | 右表/CTE | join key | join 类型 | 适用场景 | 状态 |
|---|---|---|---|---|---|
| `d_ap` | `h_ap` | `user_number` | left join | 合并 APP/PC 天级和小时级登录 | 已从 SQL 入库 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f` | `service_dw.dm_crm_lead_stats_detail_hf jt` | `lead_id` | left join | 补充首次接通时间差 | 已从 SQL 入库 |
| `data` | `temp_table.dingxi01_jiagou_db jg` | `employee_email_name + qici` | left join | 补充青橙架构 | 已从 SQL 入库，唯一性待确认 |
| `data` | `temp_table.dingxi01_jiagou_db jg` | `employee_email_prefix + qici` | left join | 到课 raw 补充青橙架构 | 已从 SQL 入库，需确认是否为标准 join key |
| `data` | `daoke` | `employee_email_prefix + qici + lead_id` | left join | 匹配首节到课 | 已从 SQL 入库 |
| `call_c` | `data` | `user_number = user_id and section_assign_employee_email_prefix = employee_email_prefix` | left join | 匹配外呼指标 | 已从 SQL 入库 |
| `denglu_app` | `data` | `user_number = user_id` | left join | 匹配 APP/PC 登录 | 已从 SQL 入库 |
| `data` 子集 `t1` | `service_dw.dws_service_user_learn_detail_hf t2` | `qici + user_id = user_number` | left join | 匹配上课明细 | 已从 SQL 入库 |
| `daoke dk` | `temp_table.dingxi01_qing_daoke ke` | `qici + channel_map_2 = qudao + grade_1 = grade + begin_time` | left join | 标记课次，支持第 1 至第 6 讲 | 已从 SQL 入库，唯一性待确认 |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf gmv` | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df ld` | `lead_id + performance_employee_email_name = employee_email_name` | left join | 订单业绩补充青橙渠道、投放计划、分配规则、直属主管和地域字段；青橙渠道订单明细 raw 复用该 join | 已从 SQL 入库，`ld` 唯一性和范围完整性待确认 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f` | `data_lake_fuwu.dwd_crm_leads_rt lrt` | `lead_id = crm_leads_id` | left join | 回查 CRM 原始线索状态、source、模型阶段和 `previous_model_id` | 2026-06-27 小样本验证命中 30/30；`previous_model_id > 0` 自关联命中 30/30 |
| `bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf p` | `data_lake_fuwu.dwd_crm_leads_rt prelead` | `p.lead_id = prelead.crm_leads_id and p.lead_model_type = 1` | left join | 回补青橙 TMK/规划系统潜客阶段顾问、渠道、年级和过程字段 | 2026-07-09 live 验证；以 `dwd` 转移链路为主过滤时覆盖率高于严格青橙截面过滤 |
| `data_lake_fuwu.dwd_crm_leads_rt lead` | `data_lake_fuwu.dwd_crm_leads_rt prelead` | `lead.previous_model_id = prelead.crm_leads_id` | inner/left join | 潜客转正常线索漏斗；`lead.model_type=0`，`prelead.model_type=1` | 2026-07-09 TMK/规划系统意向验证成功，query id `1456961079` |
| `data_lake_fuwu.dwd_crm_leads_rt lead` | `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf o` | `lead.crm_leads_id = o.lead_id` | left join | 转移后正常线索是否成交、成交年级/科目/主讲、成交金额/退费/净金额 | 使用 service 表课程和业绩范围过滤；2026-07-09 当前样本无成交命中 |
| `dwd_transfer` | `service_dw.dwd_crm_assign_private_detail_hf p` | `dwd_transfer.transfer_lead_id = p.lead_id` | left join | TMK 转移后首次承接顾问、私海转手历史和当前私海候选 | 一对多；历史保留 `private_sea_id`，首次按 `assign_time, private_sea_id`，当前候选按活跃状态、分配/更新时间和 ID 排序；144 条转移线索命中 123 条，query id `1466178403` |
| `dd` | `prc` | `lead_id + performance_employee_email_name = employee_email_name + rn = 1` | left join | 判断订单是否属于线索期次 | 已从 SQL 入库 |
| `bb_dedup` | `ud` | `employee_email_name/name + qici + channel_map_2/qudao + grade_1/grade_0 + virtual_direct_leader_email_name/zhuguan` | full outer join | 合并线索量和业绩指标，并保留年级维度 | 已从 SQL 入库，若同维度仍多行则保留 `rn = 1` |
| `mm` | `temp_table.dingxi01_qing_team_jg` | `employee_email_name` | left join | 补充最新团队架构 | 已从 SQL 入库 |
| `finance_dw.app_finance_performance_extend_details_hf dd_0` | `dw.dim_employee_chain org_t` | `name + coalesce(paid_time, trade_time) between begin_time and end_time` | left join 后 where / inner join 过滤 | 确认原始成交时间落在员工属于青橙项目部的任职窗口内，避免历史订单在转岗后退款被误计入青橙 | 已从 SQL 入库，是否应改用 `email_prefix` 待确认 |
| `rd` | `temp_table.dingxi01_qing_zz` | `name = employee_email_name` | left join | 补充青橙直属主管、大主管和学部 | 已从 SQL 入库 |
| `finance_dw.dm_finance_order_refund_detail_df ord` | `finance_dw.dim_finance_order_change_df order_change` | `order_number = order_change.order_number` | left join | 补充退款订单调课调班类型；`order_change` 先展开订单号/父订单号/原始订单号/最新子订单号并按订单号聚合 | 已从 SQL 入库 |
| `rd` 主交易层 | `finance_dw.dim_finance_order_change_df order_change` + service transfer 标记 | `rd.order_number = order_change.order_number`；service transfer 从 `order_attr` 按 `order_number + performance_employee_email_name` 聚合并随 `dd/gmv/rd` 传递 | left join / 字段传递 | 识别内部调课调班调入/调出，避免误入外部收入/退款桶；覆盖 `biz_type in (2,7)`，并用 service `transfer_in_amount/transfer_out_amount` 补充漏链路 | 已从 SQL 入库，service 明细需先聚合后回连避免放大 |
| `rd` | `re_ke` | `order_number + qici = qici_re` | left join | 给财务交易补充全退时调课链路完课课节数 | 已从 SQL 入库 |
| `rd_0` | `temp_table.dingxi01_qing_qi_moth` | `qici` | left join | 期次映射月份 | 已从 SQL 入库 |
| `wa` | `temp_table.dingxi01_qing_team_jg` | `name = employee_email_name` | left join | 补充最新直属主管 | 已从 SQL 入库 |
| `temp_table.dingxi01_qing_team_goal` | `renchan` | `xiaozu = leader_employee_email_name + month = moth` | left join | 月目标与实际业绩合并 | 已从 SQL 入库 |
| `temp_table.dingxi01_qing_team_g_qi` | `renchan` | `xiaozu = leader_employee_email_name + qici` | left join | 期次目标与实际业绩合并 | 已从 SQL 入库 |
| `temp_table.dingxi01_qing_team_jg` | `wa` | `employee_email_name + qici = name + qici` | left join | 个人转化以团队架构为主合并个人业绩 | 已从 SQL 入库，架构唯一性待确认 |
| `temp_table.dingxi01_qing_team_jg` | `temp_table.dingxi01_qing_qi_moth` | `qici` | left join | 个人转化按架构期次补充月份 | 已从 SQL 入库 |
| `data` (CTE) | `f_call0` (CTE, from service_dw.app_h_crm_lead_task_process_info_detail_hf) | `period_name + assign_employee_email_name = employee_email_name + user_id + lead_id = call_answer_lead_count` | left join | 补充线索是否有 F 类首次外呼 | 已从 SQL 入库，`call_answer_lead_count` 作为 `lead_id` 使用语义待确认 |
| `zhuanhua` (CTE) | `temp_table.shenbaoxin_channel_group` | `channel = channel_map` | left join | 补充渠道大类 `channel_group` | 已从 SQL 入库，临时表唯一性待确认 |

## 维护规则

- 从青橙历史 SQL 抽取的 join key 必须在状态中说明。
- 不得从市场顾问部看板 SQL 自动迁移 join 关系。
- 同名字段不代表可 join，必须核对业务语义和数据粒度。
- join 到临时表时必须同步检查 `knowledge/temp_tables/` 的复用边界。
