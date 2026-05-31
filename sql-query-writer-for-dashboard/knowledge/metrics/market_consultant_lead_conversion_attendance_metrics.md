# 市场顾问线索转化到课指标

## 1. 指标集合名称

市场顾问线索转化到课指标集合

## 2. 来源

- 看板 SQL：`resources/raw_sql/market_consultant_lead_conversion_attendance.sql`
- 看板文档：`knowledge/dashboards/market_consultant_lead_conversion_attendance.md`
- 入库日期：2026-05-08

## 3. 适用范围

适用于 H 业务线市场部相关线索转化、到课、深沟、AB 意向、订单收款退款和成本目标分析。

默认范围来自 SQL：

- `section_assign_employee_first_level_department_name = 'H业务线'`
- `section_assign_employee_second_level_department_name = '市场部'`
- `period_mapping_first_level_department_name = 'H业务线'`
- `period_mapping_second_level_department_name in ('精品班学部', '青橙项目部', '一对一学部', '本地化大班学部', '市场部', '菁英班学部')`

## 4. 基础派生字段

| 字段 | 口径 |
|---|---|
| period_name | 由 `group_period_year + group_period_term` 去掉“期”后按周五规则推导 |
| channel_map | 基于 `flow_pool_name`、`rule_name`、渠道、投放计划、部门等字段的长 CASE 渠道归因；最新 CASE 归档见 `resources/raw_sql/market_channel_case_when_0524.sql` |
| grade_1 | `rule_name` 中包含高一/高二/高三/初二/初三则取对应年级，否则为 `未知` |
| is_friend_lead | `valid_lead_count = 1` 时取 `friend_lead_count`，否则 0 |
| is_shengou | 最新私海阶段为 `深沟` 或 `已双沟` 时为 1 |
| AB_intention_level | 意向等级为 A/B 且最新私海阶段为 `深沟` 或 `已双沟` 时为 1 |
| AB_zhuanhua | 意向等级为 A/B 且转化线索数为 1 时为 1，字段类型待确认 |
| daoke1 | `曹忆` 渠道看第 3 节到课，其他渠道看第 1 节到课，且 `live_learn_duration > 0` |

## 5. 聚合指标

| 指标名 | 中文含义 | SQL 口径 | 待确认 |
|---|---|---|---|
| IP_lead_count | IP 线索数/线索数 | `sum(lead_count)` | 否 |
| can_renew_ds_count_a | 有效线索数 | `sum(valid_lead_count)` | 否 |
| friend_lead | 好友线索数 | `sum(is_friend_lead)` | `friend_lead_count` 字段口径待确认 |
| shengou_lead | 深沟线索数 | `sum(is_shengou)` | 最新私海阶段是否按用户粒度取最新待确认 |
| AB_lead | AB 意向深沟线索数 | `sum(AB_intention_level)` | 意向等级字段 `intention_level` 来源口径待确认 |
| AB_zhuan | AB 意向转化线索数 | `sum(AB_zhuanhua)` | `conversion_lead_count` 类型需确认 |
| daoke_1 | 首节到课数 | `sum(daoke1)` | `曹忆` 第 3 节特殊规则需业务确认 |
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

## 6. 结果层指标

| 指标名 | 中文含义 | SQL 口径 |
|---|---|---|
| s_lead | 达标有效线索数 | `case when can_renew_ds_count_a >= 5 then can_renew_ds_count_a else 0 end` |
| podan | 破单标记 | `case when can_renew_ds_count_a >= 5 and trade_income > 0 then 1 else 0 end` |
| name1 | 达标顾问名 | `case when can_renew_ds_count_a >= 5 then employee_email_name else '未知' end` |
| xiaozu | 小组 | 来自 `temp_table.dingxi01_jiagou_zx.xiaozu` |
| cb_cb | 单例子成本 | `coalesce(temp_table.dingxi01_cost.cost, 0)` |
| gl_gl | 单例子目标 | `coalesce(temp_table.dingxi01_cost.goal, 0)` |

## 7. 到课判断

| 渠道 | 课次条件 | 到课条件 |
|---|---|---|
| 曹忆 | `ke_1 = '3'` | `live_learn_duration > 0` |
| 其他渠道 | `ke_1 = '1'` | `live_learn_duration > 0` |

有效到课字段 `is_valid_live_learn` 在 `daoke` CTE 中被保留，但当前 SQL 最终指标未使用。若需要有效到课率，应另行定义 `is_valid_live_learn = '1'` 的聚合口径。

## 8. 成本目标

| 指标 | 来源表 | join key |
|---|---|---|
| cb_cb | temp_table.dingxi01_cost.cost | `channel = channel_map`、`grade = grade_1`、`qici = period_name` |
| gl_gl | temp_table.dingxi01_cost.goal | `channel = channel_map`、`grade = grade_1`、`qici = period_name` |

## 9. 待确认事项

- `channel_map` 是核心渠道归因口径，后续新增渠道应追加规则并记录变更。最新渠道 CASE 维护入口见 `knowledge/sql_patterns/channel_mapping_case_when.md`。
- `AB_zhuanhua` 字段存在字符串数字比较，需要确认 `conversion_lead_count` 类型。
- `temp_table.shenbaoxin_channel_group` 当前只确认 join key，字段清单和唯一性待确认。
- `temp_table.dingxi01_daoke_1_6_t.channel` 与 `qudao` 两种口径需确认当前看板使用哪一个。
- 结果层 `podan` 使用 `trade_income > 0`，不是 `trade_profit > 0`；该口径与部分历史转化看板不完全一致，需业务确认。
