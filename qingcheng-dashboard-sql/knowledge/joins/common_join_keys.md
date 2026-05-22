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
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf gmv` | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df ld` | `lead_id + performance_employee_email_name = employee_email_name` | left join | 订单业绩补充青橙渠道、年级和主管 | 已从 SQL 入库 |
| `dd` | `prc` | `lead_id + performance_employee_email_name = employee_email_name + rn = 1` | left join | 判断订单是否属于线索期次 | 已从 SQL 入库 |
| `bb_dedup` | `ud` | `employee_email_name/name + qici + channel_map_2/qudao` | full outer join | 合并线索量和业绩指标 | 已从 SQL 入库，去重规则待确认 |
| `mm` | `temp_table.dingxi01_qing_team_jg` | `employee_email_name` | left join | 补充最新团队架构 | 已从 SQL 入库 |

## 维护规则

- 从青橙历史 SQL 抽取的 join key 必须在状态中说明。
- 不得从市场顾问部看板 SQL 自动迁移 join 关系。
- 同名字段不代表可 join，必须核对业务语义和数据粒度。
- join 到临时表时必须同步检查 `knowledge/temp_tables/` 的复用边界。
