# 表关系

本文件记录青橙项目部看板中表与表、表与临时表、CTE 与 CTE 的关系。

## 1. 已确认或已入库关系

| 主表/CTE | 关联表/CTE | 关联条件 | 关系类型 | 数据粒度影响 | 来源 |
|---|---|---|---|---|---|
| `data` | `service_dw.dm_crm_lead_stats_detail_hf jt` | `data.lead_id = jt.lead_id` | 线索补充 | 若 `jt` 一线索多行会放大，需确认唯一性 | `qingcheng_process_data_raw_20260522.sql` |
| `data` | `temp_table.dingxi01_jiagou_db jg` | `data.employee_email_name = jg.employee_email_name and data.qici = jg.qici` | 架构补充 | `jg.department is not null` 会过滤未匹配架构的线索 | `qingcheng_process_data_raw_20260522.sql` |
| `data` | `temp_table.dingxi01_jiagou_db jg` | `data.employee_email_prefix = jg.employee_email_prefix and data.qici = jg.qici` | 架构补充 | `jg.department is not null` 会过滤未匹配架构的线索；与过程数据 raw 的姓名 join key 不一致 | `qingcheng_daoke_raw_20260522.sql` |
| `data` | `call_c` | `call_c.user_number = data.user_id and call_c.section_assign_employee_email_prefix = data.employee_email_prefix` | 外呼补充 | `call_c` 已按用户、线索、员工聚合；join 未使用 `lead_id`，是否可能串线索待确认 | `qingcheng_process_data_raw_20260522.sql` |
| `data` | `denglu_app` | `denglu_app.user_number = data.user_id` | 登录补充 | 用户级登录标记按线索汇总可能放大 | `qingcheng_process_data_raw_20260522.sql` |
| `data` | `daoke` | `data.employee_email_prefix = daoke.employee_email_prefix and data.qici = daoke.qici and data.lead_id = daoke.lead_id` | 到课补充 | `daoke` 内部按用户上课明细匹配，可能一线索多课 | `qingcheng_process_data_raw_20260522.sql` |
| `daoke` | `temp_table.dingxi01_qing_daoke ke` | `qici + channel_map_2/qudao + grade_1/grade + begin_time` | 课次标记 | 临时表唯一性影响第 1 至第 6 讲到课指标 | `qingcheng_process_data_raw_20260522.sql`, `qingcheng_daoke_raw_20260522.sql` |
| `gmv` | `ld` | `gmv.lead_id = ld.lead_id and ld.employee_email_name = gmv.performance_employee_email_name` | 订单补充线索属性 | 订单明细补充青橙渠道、年级和主管；未匹配时渠道为空 | `qingcheng_conversion_raw_20260522.sql` |
| `dd` | `prc` | `prc.lead_id = dd.lead_id and prc.employee_email_name = dd.performance_employee_email_name and prc.rn = 1` | 订单补充线索期次 | `prc` 取每个 lead 最新线索期次，用于 `is_on_period` | `qingcheng_conversion_raw_20260522.sql` |
| `bb_dedup` | `ud` | `ud.name = bb1.employee_email_name and ud.qici = bb1.qici and ud.qudao = bb1.channel_map_2` | 线索量和业绩合并 | full outer join；线索侧先按顾问-期次-渠道去重，可能丢年级 | `qingcheng_conversion_raw_20260522.sql` |
| `mm` | `temp_table.dingxi01_qing_team_jg jg` | `mm.employee_email_name = jg.employee_email_name` | 团队架构补充 | 使用最新 `qici` 架构补历史转化数据，可能产生历史架构漂移 | `qingcheng_conversion_raw_20260522.sql` |
| `dd_0` | `org_t` | `ot.name = dd_0.name and dd_0.trade_time >= ot.begin_time and dd_0.trade_time <= ot.end_time` | 员工任职期间过滤 | left join 后 where 限定组织时间，未匹配组织链的交易被剔除 | `qingcheng_revenue_year_quarter_month_raw_20260522.sql` |
| `rd` | `temp_table.dingxi01_qing_zz zz` | `zz.employee_email_name = rd.name` | 组织架构补充 | 未按期次 join，若架构表多行会放大 | `qingcheng_revenue_year_quarter_month_raw_20260522.sql` |
| `dd_0` | `org_t` | `ot.name = a.name and a.trade_time >= ot.begin_time and (ot.end_time is null or a.trade_time <= ot.end_time)` | 员工任职期间过滤 | inner join，仅保留交易发生时员工属于青橙项目部的记录 | `qingcheng_team_completion_month_raw_20260522.sql` |
| `ord` | `order_change` | `ord.order_number = order_change.parent_order_number` | 退款订单补充调课调班类型 | 当前只生成 `refund_type`，后续未直接参与退款阈值计算 | `qingcheng_team_completion_month_raw_20260522.sql` |
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
| `bb_dedup` | `ud` | `employee_email_name + qici + channel_map_2` | 线索量按 `employee_email_name, qici, channel_map_1, channel_map_2` 去重，但和订单 join 不含 `channel_map_1`、`grade_1`，是否符合转化看板口径待确认 |
| `mm` | `temp_table.dingxi01_qing_team_jg` | `employee_email_name` | 是否应该使用最新架构还是期次架构待确认 |
| `dd_0` | `org_t` | `name + trade_time between begin_time and end_time` | 是否应使用 `email_prefix` 代替 `name`，避免重名误匹配 |
| `rd` | `temp_table.dingxi01_qing_zz` | `employee_email_name` | 架构表是否一员工唯一、是否需要期次/日期字段待确认 |
| `rd` | `re_ke` | `order_number + qici/qici_re` | 全退期次按 `full_refund_timestamp` 计算，和交易期次 `rd.qici` 相等时才匹配；是否符合退费归属口径待确认 |
| `qg` | `renchan` | `xiaozu = leader_employee_email_name and month = moth` | `qg.xiaozu` 字段是否存主管邮箱而非小组名称待确认 |
| `qg` | `renchan` | `xiaozu = leader_employee_email_name and qici = qici` | 期目标表 `xiaozu` 字段是否存主管邮箱而非小组名称待确认 |
| `qtg` | `wa` | `employee_email_name + qici` | 个人转化要求架构表一人一期唯一，否则个人业绩可能被重复计算 |
| `data` | `f_call0` | `period_name + employee_email_name + user_id + lead_id` | `call_answer_lead_count` 字段名为"计数"但作为 `lead_id` 使用，语义矛盾；join 是否精准匹配待确认 |
| `zhuanhua` | `shenbaoxin_channel_group` | `channel = channel_map` | 临时表的 `channel` 字段枚举值是否全覆盖 CASE WHEN 输出的 `channel_map` 值待确认；未匹配时 `channel_1` 为 null |

## 3. 维护规则

- 如果 join 后改变数据粒度，必须说明是否需要去重、窗口函数或先聚合后 join。
- 如果 join 到临时表，必须同步检查 `knowledge/temp_tables/` 的适用边界。
- 用户后续提供修正版 SQL 时，应优先核对本文件中的待确认关系。
