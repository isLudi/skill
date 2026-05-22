# 流量画像指标

## 1. 指标集合名称

流量画像指标集合

## 2. 来源

- 看板 SQL：`resources/raw_sql/traffic_profile.sql`
- 看板文档：`knowledge/dashboards/traffic_profile.md`
- 入库日期：2026-05-09
- 最近更新：2026-05-15，按 `D:\Feishu\city_channel.txt` 同步省份/城市维度和期次参数化过滤

## 3. 适用范围

适用于 H 业务线市场部市场顾问部的流量画像、线索过程、APP 登录、外呼、到课、转化、收款退款、成交科目数和省市城市等级分析。

默认范围来自 SQL：

- `section_assign_employee_first_level_department_name = 'H业务线'`
- `section_assign_employee_second_level_department_name = '市场部'`
- `section_assign_employee_third_level_department_name = '市场顾问部'`
- `period_mapping_first_level_department_name = 'H业务线'`
- `period_mapping_second_level_department_name in ('精品班学部','青橙项目部','一对一学部','本地化大班学部','市场部','菁英班学部')`

## 4. 展示维度

| 字段 | 口径 |
|---|---|
| period_name | 由 `group_period_year + group_period_term` 去掉“期”后按周五规则推导 |
| channel_map | 基于流量池、规则、渠道、投放计划、部门、source 管理人等字段的长 CASE 渠道归因 |
| grade_1 | `rule_name` 包含高一/高二/高三/初二/初三则取对应年级，否则为 `未知` |
| depart_1 | `virtual_third_department_name` |
| depart | `virtual_fourth_department_name` |
| jingli | `virtual_leader_email_name` |
| zhuguan | `virtual_direct_leader_email_name` |
| employee_email_name | 顾问姓名 |
| province_name | 主全链路表省份，口径待人工确认 |
| city_name | 主全链路表城市，口径待人工确认 |
| city_level_name | 主全链路表城市等级 |
| last_app_channel | APP 应用最新登录渠道 |
| sub | 成交科目数档位，`1科` 至 `7科`，其余 `0科` |

## 5. 基础派生字段

| 字段 | SQL 口径 | 说明 |
|---|---|---|
| first_call_time_diff_hour | `date_diff('hour', section_assign_time, first_call_time)` | 首呼距分配小时差 |
| first_call_in_24h | `first_call_time_diff_hour between 0 and 24 and valid_lead_count > 0` | 有效线索 24 小时内首呼 |
| first_call_in_48h | `first_call_time_diff_hour between 0 and 48 and valid_lead_count > 0` | 有效线索 48 小时内首呼 |
| is_friend_lead | `valid_lead_count = 1` 时取 `friend_lead_count`，否则 0 | 好友线索 |
| is_shengou | 最新私海阶段为 `深沟` 或 `已双沟` | 深沟标记 |
| AB_intention_level | `intention_level in ('A','B')` 且深沟/已双沟 | AB 意向深沟 |
| AB_zhuanhua | `intention_level in ('A','B')` 且 `conversion_lead_count = '1'` | AB 意向转化，字段类型待确认 |
| is_long_call | 外呼明细中任一通 `call_duration > 300` | 5 分钟长通话标记 |
| is_app_denglu | 最新登录时间在最近 7 日且应用为 `PC客户端/APP/PC` | APP/PC 近期登录 |
| daoke1 | `曹忆` 看第 3 节到课，其他渠道看第 1 节，且 `live_learn_duration > 0` | 普通到课 |
| daoke_v1 | `曹忆` 看第 3 节有效到课，其他渠道看第 1 节，且 `is_valid_live_learn = '1'` | 有效到课 |

## 6. 聚合指标

| 指标名 | 中文含义 | SQL 口径 | 待确认 |
|---|---|---|---|
| IP_lead_count | IP 线索数/线索数 | `sum(lead_count)` | 否 |
| can_renew_ds_count_a | 有效线索数 | `sum(valid_lead_count)` | 否 |
| first_call_24h | 24 小时内首呼有效线索数 | `sum(first_call_in_24h)` | 首呼时间字段类型待确认 |
| first_call_48h | 48 小时内首呼有效线索数 | `sum(first_call_in_48h)` | 首呼时间字段类型待确认 |
| friend_lead | 好友线索数 | `sum(is_friend_lead)` | `friend_lead_count` 口径待确认 |
| shengou_lead | 深沟线索数 | `sum(is_shengou)` | 私海最新阶段口径待确认 |
| AB_lead | AB 意向深沟线索数 | `sum(AB_intention_level)` | `intention_level` 来源口径待确认 |
| AB_zhuan | AB 意向转化线索数 | `sum(AB_zhuanhua)` | `conversion_lead_count` 类型需确认 |
| long_call_5 | 5 分钟长通话用户/线索数 | `sum(is_long_call)` | `call_c` join 未带 `lead_id`，去重风险待确认 |
| app_denglu | 近 7 日登录 APP/PC 数 | `sum(is_app_denglu)` | 最新登录记录是否按产品线隔离待确认 |
| daoke_1 | 首节到课数 | `sum(daoke1)` | `曹忆` 第 3 节特殊规则需确认 |
| daoke_v1 | 首节有效到课数 | `sum(daoke_v1)` | `is_valid_live_learn` 字段类型需确认 |
| pay_users | 转化人数 | `sum(conversion_lead_count)` | 否 |
| pay_users_on_period | 当期线索当期转化人数 | `sum(same_lead_period_conversion_lead_count)` | 否 |
| pay_users_not_on_period | 非当期转化人数 | `sum(conversion_lead_count - same_lead_period_conversion_lead_count)` | 否 |
| pay_user_subs | 转化科目人次 | `sum(subject_count)` | 否 |
| pay_user_subs_on_period | 当期转化科目人次 | `sum(same_lead_period_subject_count)` | 否 |
| pay_user_subs_not_on_period | 非当期转化科目人次 | `sum(subject_count - same_lead_period_subject_count)` | 否 |
| pay_user_subs_joint | 联报人次 | `sum(lb_subject_count)` | 否 |
| pay_user_subs_joint_onp | 当期联报人次 | `sum(same_lead_period_lb_subject_count)` | 否 |
| pay_user_subs_joint_nonp | 非当期联报人次 | `sum(lb_subject_count - same_lead_period_lb_subject_count)` | 否 |
| trade_income | 收款金额 | `sum(income_amount / 100)` | 金额单位待确认 |
| trade_refund | 退款金额 | `sum(in_pay_period_refund_amount / 100 + non_pay_period_refund_amount / 100)` | 金额单位待确认 |
| trade_profit | 净收金额 | `sum(income_amount / 100 - in_pay_period_refund_amount / 100 - non_pay_period_refund_amount / 100)` | 金额单位待确认 |
| xb_trade_income | 当期线索当期收款 | `sum(same_lead_period_income_amount / 100)` | 金额单位待确认 |
| xb_trade_profit | 当期线索当期净收 | `sum(same_lead_period_income_amount / 100 - same_lead_period_refund_amount / 100)` | 金额单位待确认 |
| kk_trade_income | 跨期收款 | `sum(income_amount / 100 - same_lead_period_income_amount / 100)` | 金额单位待确认 |
| pre_refund | 往期支付当期退款 | `sum(non_pay_period_refund_amount / 100)` | 金额单位待确认 |

## 7. 结果层指标

| 指标名 | 中文含义 | SQL 口径 | 待确认 |
|---|---|---|---|
| s_lead | 达标有效线索数 | `case when can_renew_ds_count_a >= 5 then can_renew_ds_count_a else 0 end` | 阈值待确认 |
| podan | 破单标记 | `case when can_renew_ds_count_a >= 5 and trade_income > 0 then 1 else 0 end` | 注释与代码不一致 |
| name1 | 达标顾问名 | `case when can_renew_ds_count_a >= 5 then employee_email_name else '未知' end` | 否 |
| xiaozu | 小组 | `temp_table.dingxi01_jiagou_zx.xiaozu` | 姓名关联唯一性待确认 |
| cb_cb | 单例子成本 | `coalesce(temp_table.dingxi01_cost.cost, 0)` | 成本表维护口径待确认 |
| gl_gl | 单例子目标 | `coalesce(temp_table.dingxi01_cost.goal, 0)` | 目标表维护口径待确认 |

## 8. 成交科目档位

| 档位 | SQL 来源 |
|---|---|
| 1科-7科 | `finance_dw.app_finance_performance_extend_details_hf` 按 `qici + user_id + employee_email_name` 统计 `count(distinct subject)` 后映射 |
| 0科 | 无成交科目、未匹配财务明细或科目数不在 1-7 之间 |

科目归一化规则：英语/英文归为英语，语文、数学、物理、化学、历史、政治、生物、地理、日语分别归为标准科目，其他保留原 `course_subject`。

## 9. 待确认事项

- 该指标集合来自历史 SQL，未单独经过业务指标文档确认。
- APP 登录使用 `dw.dim_cstm_active_user_c_appliction_mb_df` 最新记录判断最近 7 日登录，需确认该日表是否足以覆盖小时内最新活跃。
- 省份、城市、城市等级均来自 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`，字段口径需人工确认。
- 当前 `city_channel.txt` 版本使用 `${period_name1}`、`${period_name2}` 做期次半开区间过滤，执行前必须由前端或查询参数替换。
- `podan` 使用收款 `trade_income > 0`，不是净收 `trade_profit > 0`。
- 成交科目数 `dd.subject` 的数值/字符串比较、财务明细与主线索 join 粒度均需确认。
