# 青橙渠道订单明细指标与派生字段

## 1. 来源

`resources/raw_sql/qingcheng_channel_order_detail_raw_20260627.sql`

适用文档：`knowledge/dashboards/qingcheng_channel_order_detail_raw_20260627.md`

## 2. 查询性质

该 SQL 主要用于订单明细抽取，不是聚合指标看板。

本文档只沉淀该 SQL 中有明确派生逻辑或常被当作口径字段使用的金额字段、状态标记和期次标记；其余原样透出的维度字段应以源表字段语义为准，待人工确认。

2026-06-27 模板版新增 `province_name`、`city_name`、`city_level_name` 三个原样透出的地域维度字段；它们不属于派生指标，因此不在本文档单独维护公式。

## 3. 计算粒度

理论上为订单线索归因明细粒度，核心字段为 `lead_id + original_order_user_number + order_number + performance_employee_email_name`。

`ld` 侧如果无法保证 `lead_id + employee_email_name` 唯一，则这些派生字段会随 join 一起被复制。该风险待人工确认。

## 4. 金额派生字段

| 字段 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `income_amount` | `income_amount / 100` | 收入金额，分转元 | 已从 SQL 入库 |
| `refund_amount` | `refund_amount / 100` | 退款金额，分转元 | 已从 SQL 入库 |
| `promit_amount` | `(income_amount - refund_amount) / 100` | 净营收，分转元 | 已从 SQL 入库，字段拼写待人工确认 |

## 5. 订单状态与退款标记

| 字段 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `is_pay_success_order` | 源表直出 | 是否支付成功订单 | 源字段语义待人工确认 |
| `is_part_refund_order` | 源表直出 | 是否部分退款订单 | 源字段语义待人工确认 |
| `is_full_refund_order` | 源表直出 | 是否全额退款订单 | 源字段语义待人工确认 |
| `latest_order_is_pay_success_order` | 源表直出 | 最新订单是否支付成功 | 源字段语义待人工确认 |
| `latest_order_is_part_refund_order` | 源表直出 | 最新订单是否部分退款 | 源字段语义待人工确认 |
| `latest_order_is_full_refund_order` | 源表直出 | 最新订单是否全额退款 | 源字段语义待人工确认 |
| `pay_refund_type` | 源表直出 | 支付/退款类型 | 源字段语义待人工确认 |

## 6. 续费、黑名单和期次标记

| 字段 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `is_renew_class_amount` | 源表直出 | 续费金额标记 | 待人工确认 |
| `is_renew_class_user` | 源表直出 | 续费用户标记 | 待人工确认 |
| `is_blacklist_user` | 源表直出 | 黑名单用户标记 | 待人工确认 |
| `is_same_trade_lead_period` | 源表直出 | 交易期次和线索期次是否一致 | 待人工确认 |

## 7. 时间口径

| 类型 | 口径 | 状态 |
|---|---|---|
| 数据快照时间 | `dt = format_datetime(NOW() - interval '2' hour,'YYYYMMdd')` 且 `hour = format_datetime(NOW() - interval '2' hour,'HH')` | 已从 SQL 入库 |
| 明细筛选时间 | `trade_timestamp > ${begin_trade_time}` 且 `trade_timestamp < ${end_trade_time}` | 用户传入占位符，待运行时替换 |

## 8. 青橙范围限定

| 字段 | 口径 | 状态 |
|---|---|---|
| `performance_second_level_department_name` | `'青橙项目部'` | 已从 SQL 入库 |
| `ld` 侧部门范围 | SQL 未显式限制 | 待人工确认 |

## 9. 适用表

- `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`
- `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`

## 10. 最终输出粒度

明细级，不做聚合输出。

## 11. 冲突说明

该文档仅描述渠道订单明细抽取字段，不等同于 `knowledge/metrics/qingcheng_conversion_metrics.md` 中的顾问级/渠道级聚合指标。

不得把这里的明细字段直接当成青橙转化聚合口径复用。

## 12. 待人工确认

是
