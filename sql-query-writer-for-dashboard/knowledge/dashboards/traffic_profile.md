# 流量画像看板

## 1. 看板名称

流量画像看板

## 2. SQL 来源

- 原始 SQL：`resources/raw_sql/data_center_market_2683_20260705.sql`
- 来源：用户提供的 `D:\Feishu\city_channel.txt` 流量画像城市渠道查询 SQL
- 入库日期：2026-05-09
- 最近更新：2026-05-15，按 `city_channel.txt` 覆盖为省份/城市维度版本

## 3. 查询目的

基于市场顾问线索全链路数据，补充用户近 7 日 APP/PC 登录、最新 APP 渠道、外呼首呼时效、5 分钟长通话、最新私海深沟阶段、首节/有效到课、成交科目数档位、省份、城市、城市等级、成本和目标，用于按期次、渠道、年级、架构、顾问、省市城市等级、登录设备和成交科目档位分析流量画像及转化表现。

该 SQL 继承市场顾问转化/到课类看板的长 `channel_map` 规则，并额外强化：

- `denglu_app`：最近 7 日 APP/PC 登录标记；
- `app_ph`：用户最新 APP 登录渠道 `last_app_channel`；
- `call_c`：外呼次数、接通次数、5 分钟长通话；
- `dd`：财务业绩明细中按用户和期次统计成交科目数档位；
- `daoke_v1`：有效到课标记；
- `province_name`、`city_name`、`city_level_name`：城市渠道画像维度。

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| dw.dim_cstm_active_user_c_appliction_mb_df | denglu_app / app_ph | 取用户最新登录记录、近 7 日 APP/PC 登录标记、最新 APP 渠道 |
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | t1 / data | 主线索、渠道、顾问、转化、收款退款、省份、城市、城市等级和基础画像字段 |
| service_dw.dwd_crm_assign_private_detail_hf | t | 按用户取最新私海阶段，识别深沟/已双沟 |
| service_dw.app_h_crm_lead_employee_workload_detail_hf | call_c | 外呼通话时长、总外呼次数、接通次数、5 分钟长通话 |
| service_dw.dws_service_user_learn_detail_hf | t2 | 行课记录，补充到课时长和有效到课 |
| finance_dw.app_finance_performance_extend_details_hf | dd | 财务业绩明细，按用户-期次统计成交科目数 |
| temp_table.dingxi01_daoke_1_6_t | ke | 期次-渠道-年级-开课时间到课课次映射 |
| temp_table.dingxi01_channel_group | channel_grp | 渠道分组映射，当前 SQL join 后未输出字段 |
| temp_table.dingxi01_cost | ct | 渠道-年级-期次成本和目标 |
| temp_table.dingxi01_jiagou_db | jg | 期次架构映射，当前 SQL join 后未输出字段 |
| temp_table.dingxi01_jiagou_zx | zx | 按员工姓名补充小组 |

## 5. CTE 逻辑

| CTE | 作用 | 关键字段 |
|---|---|---|
| denglu_app | 从 C 端用户应用日表按 `user_number` 取最新登录记录，判断最近 7 日 APP/PC 登录 | `user_number`, `last_event_time`, `appliction_name`, `is_app_denglu` |
| app_ph | 从 APP 应用记录中按 `user_number` 取最新登录设备渠道 | `user_number`, `last_app_channel` |
| data | 读取主全链路表，派生期次、渠道、年级、省份、城市、城市等级、架构维度、基础转化金额指标、首呼时差、好友、深沟和 AB 意向字段 | `period_name`, `channel_map`, `grade_1`, `province_name`, `city_name`, `city_level_name`, `first_call_time_diff_hour` |
| call_c | 聚合用户-线索-顾问维度外呼工作量 | `is_long_call`, `call_duration_1`, `zong_call_ci_1`, `call_status_1` |
| daoke | 将主线索用户与行课记录、到课课次映射表关联，保留到课时长和有效到课字段 | `begin_time`, `live_learn_duration`, `is_valid_live_learn`, `ke_1` |
| dd | 从财务业绩明细按用户、期次、顾问统计去重成交科目数 | `qici`, `user_id`, `subject` |
| base | 汇总画像派生字段：首呼 24/48 小时、长通话、APP 登录、最新 APP 渠道、成交科目档位、到课和有效到课 | `first_call_in_24h`, `is_app_denglu`, `last_app_channel`, `sub`, `daoke1`, `daoke_v1` |
| zhuanhua | 按看板展示维度聚合线索、过程、到课、转化、收款退款指标 | `province_name`, `city_name`, `IP_lead_count`, `can_renew_ds_count_a`, `app_denglu`, `daoke_v1`, `trade_income` |
| final select | 补充达标线索、破单、顾问名、小组、成本和目标 | `s_lead`, `podan`, `name1`, `xiaozu`, `cb_cb`, `gl_gl` |

## 6. join 关系

| 左表/CTE | 左字段 | 右表/CTE | 右字段 | 说明 |
|---|---|---|---|---|
| data | `user_id` | service_dw.dwd_crm_assign_private_detail_hf | `user_number` | 取最新私海阶段 |
| base | `user_id`, `employee_email_prefix` | call_c | `user_number`, `section_assign_employee_email_prefix` | 补充长通话；原 SQL 未使用 `lead_id` join，需确认多线索用户是否会放大 |
| base | `user_id` | denglu_app | `user_number` | 补充近 7 日登录标记 |
| base | `user_id` | app_ph | `user_number` | 补充最新 APP 渠道 |
| base | `period_name`, `user_id` | dd | `qici`, `user_id` | 补充成交科目档位；`dd` 同时按 `employee_email_name` 分组但 join 未使用该字段 |
| data | `user_id`, `period_name` | service_dw.dws_service_user_learn_detail_hf | `user_number`, 派生 `qici` | 关联用户当期行课记录 |
| daoke | `period_name`, `channel_map`, `grade_1`, `begin_time` | temp_table.dingxi01_daoke_1_6_t | `qici`, `channel`, `grade`, `begin_time` | 识别第 1 节/第 3 节到课 |
| zhuanhua | `channel_map` | temp_table.dingxi01_channel_group | `channel` | 渠道分组，当前未输出字段 |
| zhuanhua | `channel_map`, `grade_1`, `period_name` | temp_table.dingxi01_cost | `channel`, `grade`, `qici` | 补充成本 `cost` 和目标 `goal` |
| zhuanhua | `period_name`, `depart`, `zhuguan`, `employee_email_name` | temp_table.dingxi01_jiagou_db | `qici`, `department`, `xiaozu`, `employee_email_name` | 架构映射，当前未输出字段 |
| zhuanhua | `employee_email_name` | temp_table.dingxi01_jiagou_zx | `employee_email_name` | 补充 `xiaozu` |

## 7. 分区和范围限定

APP 登录日表：

```sql
dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
and product_name in ('高途', '规划精品')
```

主全链路表：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name = '市场部'
and section_assign_employee_third_level_department_name = '市场顾问部'
and period_mapping_first_level_department_name = 'H业务线'
and period_mapping_second_level_department_name in ('精品班学部','青橙项目部','一对一学部','本地化大班学部','市场部','菁英班学部')
```

私海阶段表：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and assign_employee_first_level_department_name = 'H业务线'
and assign_employee_second_level_department_name = '市场部'
and assign_employee_third_level_department_name = '市场顾问部'
```

外呼工作量表：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
```

行课表：

```sql
dt = date_format(now() - interval '2' hour, '%Y%m%d')
and hour = date_format(now() - interval '2' hour, '%H')
and course_first_level_department_name = 'H业务线'
and course_second_level_department_name in ('精品班学部','市场部','青橙项目部')
and is_need_attend = 1
```

财务业绩明细：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and employee_first_level_department_name = 'H业务线'
and employee_second_level_department_name = '市场部'
and employee_third_level_department_name = '市场顾问部'
and real_price <> 0
```

结果范围：

```sql
period_name >= ${period_name1}
and period_name < ${period_name2}
```

## 8. group by 维度

- `period_name`
- `channel_map`
- `grade_1`
- `depart_1`
- `depart`
- `jingli`
- `zhuguan`
- `employee_email_name`
- `province_name`
- `city_name`
- `city_level_name`
- `last_app_channel`
- `sub`

## 9. 聚合指标

| 指标 | SQL 口径 |
|---|---|
| IP_lead_count | `sum(lead_count)` |
| can_renew_ds_count_a | `sum(valid_lead_count)` |
| first_call_24h | `sum(first_call_in_24h)` |
| first_call_48h | `sum(first_call_in_48h)` |
| friend_lead | `sum(is_friend_lead)` |
| shengou_lead | `sum(is_shengou)` |
| AB_lead | `sum(AB_intention_level)` |
| AB_zhuan | `sum(AB_zhuanhua)` |
| long_call_5 | `sum(is_long_call)` |
| app_denglu | `sum(is_app_denglu)` |
| daoke_1 | `sum(daoke1)` |
| daoke_v1 | `sum(daoke_v1)` |
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
| name1 | `case when can_renew_ds_count_a >= 5 then employee_email_name else '未知' end` |
| cb_cb | `coalesce(ct.cost, 0)` |
| gl_gl | `coalesce(ct.goal, 0)` |

## 10. 可复用 SQL 模式

- 最新登录：按 `user_number` 使用 `row_number() over (partition by user_number order by try(date_parse(last_event_time, ...)) desc)` 取最新记录。
- 首呼时效：`date_diff('hour', section_assign_time, first_call_time)` 后判断 24/48 小时内，且 `valid_lead_count > 0`。
- 私海阶段：对 `service_dw.dwd_crm_assign_private_detail_hf` 按 `private_sea_update_time desc` 取最新阶段，`450/470` 映射深沟/已双沟。
- 到课：`曹忆` 渠道看 `ke_1 = '3'`，其他渠道看 `ke_1 = '1'`；普通到课用 `live_learn_duration > 0`，有效到课用 `is_valid_live_learn = '1'`。
- 成交科目档位：财务表按 `course_subject` 归一化后 `count(distinct subject)`，最终映射到 `1科` 至 `7科`，其他为 `0科`。

## 11. 待确认事项

- 原始 SQL 包含 Presto 三参数 `date_add('day', n, expr)`；当前作为历史 SQL 原样归档。生成新 SQL 时需按平台兼容规则改为 `interval` 或二参数兼容写法。
- `data` CTE 中同层 `select` 的部分 `channel_map` 条件引用 `period_name` 别名；需确认执行环境是否允许，或改为外层 CTE 引用。
- `validate_sql_rules.py` 会把派生别名 `channel_map`、`grade_1` 误判为 `t1` 物理字段；生成新 SQL 时应在外层 CTE 使用这些派生字段，不能当作主表原始字段。
- 当前 `city_channel.txt` 版本主全链路表和其他小时表均使用 `now() - 2 hour` 分区；若复用旧版 `hour = now() - 3 hour` 写法，需确认是否为产出延迟口径。
- `province_name`、`city_name`、`city_level_name` 来自主全链路表，城市层级和省市归属口径待人工确认。
- `call_c` 聚合包含 `lead_id`，但 `base` join 只使用 `user_number + employee_email_prefix`，多线索用户可能造成重复匹配。
- `dd` CTE 按 `qici + user_id + employee_email_name` 聚合，但 join 到 `base` 时未使用 `employee_email_name`，需确认是否可能重复。
- `dd.subject` 是 `count(distinct subject)`，结果层用字符串 `'1'`、`'2'` 比较，字段类型需确认。
- `AB_zhuanhua` 中 `conversion_lead_count = '1'` 存在数值/字符串混用风险。
- `podan` 代码使用 `can_renew_ds_count_a >= 5 and trade_income > 0`，注释写“线索量>10且有净营收且带班”，代码和注释不一致。
- `channel_grp`、`jg` 被 join 但未输出字段；需确认是否仅为历史遗留。
- `temp_table.dingxi01_cost`、`temp_table.dingxi01_jiagou_db`、`temp_table.dingxi01_jiagou_zx` 若 join key 不唯一，会放大结果行。
