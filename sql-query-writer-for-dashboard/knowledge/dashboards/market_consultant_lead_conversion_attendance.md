# 市场顾问线索转化到课看板

## 1. 看板名称

市场顾问线索转化到课看板

## 2. SQL 来源

- 原始 SQL：`resources/raw_sql/market_consultant_lead_conversion_attendance.sql`
- 来源：用户提供 SQL
- 入库日期：2026-05-08

## 3. 查询目的

基于线索成本转化沟通行课全链路数据，按期次、渠道、规则、年级、架构、顾问聚合市场顾问线索转化、深沟、AB 意向、首节到课、收款、退款、净收、成本和目标指标。

该看板与 `market_consultant_conversion.sql` 同属市场顾问转化类 SQL，但本版本新增或强化了：

- 区域定向渠道映射；
- 私海最新阶段识别深沟/已双沟；
- AB 意向深沟和 AB 意向转化；
- 结合到课课次映射表计算首节到课，其中 `曹忆` 渠道看第 3 节；
- 成本目标临时表 `temp_table.dingxi01_cost`；
- 新渠道分组临时表 `temp_table.shenbaoxin_channel_group`。

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | t1 / data | 主线索、渠道、顾问、转化、订单、收款退款全链路数据 |
| service_dw.dwd_crm_assign_private_detail_hf | t | 每用户取最新私海阶段，识别深沟/已双沟 |
| service_dw.dws_service_user_learn_detail_hf | t2 | 行课数据，判断到课和有效到课字段来源 |
| temp_table.dingxi01_daoke_1_6_t | ke | 期次-渠道-年级-开课时间到课课次映射 |
| temp_table.shenbaoxin_channel_group | channel_grp | 渠道分组映射，当前 SQL 仅 join，未输出字段 |
| temp_table.dingxi01_cost | ct | 渠道-年级-期次成本和目标 |
| temp_table.dingxi01_jiagou_db | jg | 期次架构映射，当前 SQL 仅 join，未输出字段 |
| temp_table.dingxi01_jiagou_zx | zx | 员工专项架构，补充小组 |

## 5. CTE 逻辑

| CTE | 作用 |
|---|---|
| data | 读取主全链路表，派生 `period_name`、`channel_map`、`grade_1`，补充最新私海阶段和基础指标；渠道 CASE 最新来源见 `resources/raw_sql/market_channel_case_when_0524.sql` |
| daoke | 将线索用户与行课记录、到课课次映射表关联，得到候选到课课次 |
| base | 按渠道计算 `daoke1`；`曹忆` 看第 3 节，其他渠道看第 1 节 |
| zhuanhua | 按期次、渠道、规则、年级、架构、顾问聚合转化和金额指标 |
| final select | 补充 `s_lead`、`podan`、`name1`、小组、成本、目标 |

## 6. join 关系

| 左表/CTE | 左字段 | 右表/CTE | 右字段 | 说明 |
|---|---|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | user_id | service_dw.dwd_crm_assign_private_detail_hf | user_number | 取用户最新私海阶段 |
| data | user_id | service_dw.dws_service_user_learn_detail_hf | user_number | 关联行课记录 |
| data | period_name | 行课派生 qici | qici | 对齐线索期次和课程期次 |
| daoke | period_name, channel_map, grade_1, begin_time | temp_table.dingxi01_daoke_1_6_t | qici, channel, grade, begin_time | 识别第 1 节或第 3 节 |
| zhuanhua | channel_map | temp_table.shenbaoxin_channel_group | channel | 渠道分组映射，当前未输出 |
| zhuanhua | channel_map, grade_1, period_name | temp_table.dingxi01_cost | channel, grade, qici | 补充成本和目标 |
| zhuanhua | period_name, depart, zhuguan, employee_email_name | temp_table.dingxi01_jiagou_db | qici, department, xiaozu, employee_email_name | 架构映射，当前未输出字段 |
| zhuanhua | employee_email_name | temp_table.dingxi01_jiagou_zx | employee_email_name | 补充 `xiaozu` |

## 7. 分区和范围限定

主全链路表：

```sql
t1.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and t1.hour = format_datetime(now() - interval '2' hour, 'HH')
and t1.section_assign_employee_first_level_department_name = 'H业务线'
and t1.section_assign_employee_second_level_department_name = '市场部'
and t1.period_mapping_first_level_department_name = 'H业务线'
and t1.period_mapping_second_level_department_name in ('精品班学部', '青橙项目部', '一对一学部', '本地化大班学部', '市场部', '菁英班学部')
```

私海阶段表：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and assign_employee_first_level_department_name = 'H业务线'
and assign_employee_second_level_department_name = '市场部'
and assign_employee_third_level_department_name = '市场顾问部'
```

行课表：

```sql
dt = date_format(now() - interval '2' hour, '%Y%m%d')
and hour = date_format(now() - interval '2' hour, '%H')
and course_first_level_department_name = 'H业务线'
and course_second_level_department_name in ('精品班学部', '市场部', '青橙项目部')
and is_need_attend = 1
```

## 8. group by 维度

- `period_name`
- `channel_map`
- `rule_name`
- `grade_1`
- `depart_1`
- `depart`
- `jingli`
- `zhuguan`
- `employee_email_name`

## 9. 聚合指标

| 指标 | SQL 口径 |
|---|---|
| IP_lead_count | `sum(lead_count)` |
| can_renew_ds_count_a | `sum(valid_lead_count)` |
| friend_lead | `sum(is_friend_lead)` |
| shengou_lead | `sum(is_shengou)` |
| AB_lead | `sum(AB_intention_level)` |
| AB_zhuan | `sum(AB_zhuanhua)` |
| daoke_1 | `sum(daoke1)` |
| pay_users | `sum(conversion_lead_count)` |
| pay_users_on_period | `sum(same_lead_period_conversion_lead_count)` |
| pay_users_not_on_period | `sum(conversion_lead_count - same_lead_period_conversion_lead_count)` |
| pay_user_subs | `sum(subject_count)` |
| pay_user_subs_on_period | `sum(same_lead_period_subject_count)` |
| pay_user_subs_not_on_period | `sum(subject_count - same_lead_period_subject_count)` |
| pay_user_subs_joint | `sum(lb_subject_count)` |
| pay_user_subs_joint_onp | `sum(same_lead_period_lb_subject_count)` |
| pay_user_subs_joint_nonp | `sum(lb_subject_count - same_lead_period_lb_subject_count)` |
| trade_income | `sum(income_amount / 100)` |
| trade_refund | `sum(in_pay_period_refund_amount / 100 + non_pay_period_refund_amount / 100)` |
| trade_profit | `sum(income_amount / 100 - in_pay_period_refund_amount / 100 - non_pay_period_refund_amount / 100)` |
| xb_trade_income | `sum(same_lead_period_income_amount / 100)` |
| xb_trade_profit | `sum(same_lead_period_income_amount / 100 - same_lead_period_refund_amount / 100)` |
| kk_trade_income | `sum(income_amount / 100 - same_lead_period_income_amount / 100)` |
| pre_refund | `sum(non_pay_period_refund_amount / 100)` |
| s_lead | `case when can_renew_ds_count_a >= 5 then can_renew_ds_count_a else 0 end` |
| podan | `case when can_renew_ds_count_a >= 5 and trade_income > 0 then 1 else 0 end` |
| cb_cb | `coalesce(ct.cost, 0)` |
| gl_gl | `coalesce(ct.goal, 0)` |

## 10. 待确认事项

- `temp_table.shenbaoxin_channel_group` 的完整字段、维护来源和 `channel` 唯一性待确认。
- `temp_table.dingxi01_jiagou_db` 在最终 SQL 中被 join 但未输出字段，需确认是否仅用于过滤/防止脏架构，还是应输出 `jg` 字段。
- `temp_table.dingxi01_daoke_1_6_t` 本 SQL 使用 `channel` 字段关联，历史外呼看板存在使用 `qudao` 的口径；需确认当前看板应使用哪个字段。
- `AB_zhuanhua` 中 `conversion_lead_count = '1'` 存在数值/字符串混用风险，建议确认字段类型后统一为 `conversion_lead_count = 1` 或显式 cast。
- `channel_map` CASE 规则非常长，属于看板核心业务口径；后续改写 SQL 时不得简化或遗漏规则，除非用户明确要求。最新渠道 CASE 已归档为 `resources/raw_sql/market_channel_case_when_0524.sql`，说明见 `knowledge/sql_patterns/channel_mapping_case_when.md`。
- 金额字段除以 100 的口径沿用历史 SQL，是否均为“分”单位需结合字段文档和财务口径确认。
