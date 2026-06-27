# 青橙渠道订单明细 raw

## 1. 来源

`resources/raw_sql/qingcheng_channel_order_detail_raw_20260627.sql`

入库时间：2026-06-27

## 2. 查询目标

沉淀青橙项目部用于查询订单明细算绩效的 SQL。该 SQL 以订单归因收入退款明细表为主，补充线索侧渠道字段、投放计划、直属主管、分配规则和地域字段，输出交易时间区间内的订单、支付、退款、课程、顾问组织、期次与地域字段，主要用于明细排查、渠道订单核对和模板取数。

## 3. 最终输出粒度

理论上为订单线索归因明细粒度，核心识别字段为 `lead_id + original_order_user_number + order_number + performance_employee_email_name`。

由于 `ld` 子查询仅做 `select distinct`，如果同一 `lead_id + employee_email_name` 在 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 仍存在多条不同渠道或规则记录，最终明细可能被放大。该粒度稳定性待人工确认。

## 4. 使用表

| 表名 | 别名/子查询 | 用途 |
|---|---|---|
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `gmv` | 订单归因、支付、退款、课程、顾问组织和期次字段主表 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `ld` | 补充线索侧渠道、流量池、获客方式、投放计划、分配规则和直属主管 |

## 5. 使用临时表

本 SQL 未使用 `temp_table.*` 临时表。

补充说明见 `knowledge/temp_tables/_no_temp_table_usage_cases.md`。

## 6. 子查询结构

| 子查询/层级 | 用途 | 关键字段 |
|---|---|---|
| `gmv` | 读取订单归因收入退款明细小时表当前小时快照 | `lead_id`, `original_order_user_number`, `order_number`, `trade_timestamp`, `income_amount`, `refund_amount`, `performance_employee_email_name` |
| `ld` | 读取线索宽表当前小时快照并去重，补充渠道、规则和地域字段 | `lead_id`, `employee_email_name`, `channel_name_1`, `channel_name_2`, `channel_name_3`, `flow_pool_name`, `get_customer_way_name`, `put_plan_name`, `rule_name`, `virtual_direct_leader_email_name`, `province_name`, `city_name`, `city_level_name` |
| 最终查询 | 左连接订单明细和线索属性，并按交易时间、青橙业绩部门过滤 | 订单字段 + 渠道字段 + 金额派生字段 |

## 7. 关键输出字段

| 字段组 | 字段 | 来源 | 说明 |
|---|---|---|---|
| 主键和用户 | `lead_id`, `original_order_user_number`, `order_number`, `original_order_number`, `latest_order_number` | `gmv` | 订单和线索识别字段 |
| 渠道字段 | `channel_name_1`, `channel_name_2`, `channel_name_3`, `flow_pool_name`, `get_customer_way_name`, `put_plan_name`, `rule_name` | `ld` | 线索侧渠道与分配规则字段 |
| 地域字段 | `province_name`, `city_name`, `city_level_name` | `ld` | 线索侧地域字段；2026-06-27 模板版新增 |
| 订单状态 | `order_status`, `is_pay_success_order`, `is_part_refund_order`, `is_full_refund_order`, `latest_order_is_pay_success_order`, `latest_order_is_part_refund_order`, `latest_order_is_full_refund_order`, `pay_refund_type` | `gmv` | 状态语义待人工确认，以历史 SQL 原字段名保留 |
| 支付退款时间 | `pay_success_timestamp`, `full_refund_timestamp`, `original_order_pay_success_timestamp`, `latest_order_full_refund_timestamp`, `trade_timestamp` | `gmv` | 支付、退款和交易时间 |
| 顾问组织 | `performance_employee_email_name`, `performance_city_name`, `performance_talent_type_name`, `performance_first_level_department_name`, `performance_second_level_department_name`, `performance_third_level_department_name`, `performance_department_path_json`, `virtual_direct_leader_email_name` | `gmv` + `ld` | 订单业绩归属员工与直属主管 |
| 课程字段 | `clazz_biz_number`, `clazz_type`, `clazz_begin_timestamp`, `clazz_end_timestamp`, `main_teacher_number`, `main_teacher_email_name`, `course_*`, `school_*`, `grade_name` | `gmv` | 课程与班级信息 |
| 金额字段 | `income_amount`, `refund_amount`, `promit_amount` | `gmv` 派生 | 分转元后的收入、退款和净营收 |
| 期次字段 | `pay_group_period_name`, `trade_group_period_name`, `lead_period_name`, `trade_period_name`, `pay_period_name`, `trade_period_*`, `pay_period_*`, `is_same_trade_lead_period` | `gmv` | 历史 SQL 直接输出的期次与映射字段，完整语义待人工确认 |
| 其他标记 | `is_renew_class_amount`, `is_renew_class_user`, `is_blacklist_user` | `gmv` | 历史 SQL 直接输出，业务口径待人工确认 |

## 8. 青橙范围限定

| 位置 | 范围字段 | 取值 | 状态 |
|---|---|---|---|
| 最终 where | `performance_second_level_department_name` | `'青橙项目部'` | 已从 SQL 入库 |
| 最终 where | `trade_timestamp` | `${begin_trade_time}` 到 `${end_trade_time}` | 用户传入时间占位符，待运行时替换 |
| `gmv` 子查询 | `dt`, `hour` | `now() - interval '2' hour` | 已从 SQL 入库 |
| `ld` 子查询 | `dt`, `hour` | `now() - interval '2' hour` | 已从 SQL 入库 |

`ld` 子查询没有显式 `青橙项目部` 部门范围过滤，是否完全依赖 `lead_id + performance_employee_email_name` join 和最终业绩部门过滤即可保证青橙口径，待人工确认。

## 9. 分区和小时条件

| 表/子查询 | dt 条件 | hour 条件 | 说明 |
|---|---|---|---|
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `format_datetime(NOW() - interval '2' hour,'YYYYMMdd')` | `format_datetime(NOW() - interval '2' hour,'HH')` | 订单归因收入退款明细 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `format_datetime(NOW() - interval '2' hour,'YYYYMMdd')` | `format_datetime(NOW() - interval '2' hour,'HH')` | 线索宽表补充渠道属性 |

## 10. join 关系

| 左侧 | 右侧 | join key | join 类型 | 用途 |
|---|---|---|---|---|
| `gmv` | `ld` | `gmv.lead_id = ld.lead_id and ld.employee_email_name = gmv.performance_employee_email_name` | `left join` | 给订单明细补充线索侧渠道、流量池、投放计划、分配规则、直属主管和地域字段 |

## 11. 关联指标

金额与标记字段沉淀到 `knowledge/metrics/qingcheng_channel_order_detail_metrics.md`。

## 12. 已知风险和待确认事项

- 本 SQL 为明细抽取 SQL，不含 `group by`；不能直接复用为青橙聚合看板指标 SQL。
- `ld` 子查询缺少明确的青橙部门范围过滤，是否存在跨部门同 `lead_id` 或同顾问姓名映射污染，待人工确认。
- `select distinct lead_id, ... , employee_email_name` 只能去除完全重复行，不能保证 `lead_id + employee_email_name` 唯一；若不唯一会放大订单明细。
- 2026-06-27 模板版新增 `province_name`、`city_name`、`city_level_name` 三个字段；若后续模板继续扩列，需同步检查 dashboard 文档和字段说明是否遗漏。
- `${begin_trade_time}`、`${end_trade_time}` 是模板占位符，不是可直接执行的 Presto 字面量。
- `promit_amount` 为历史 SQL 字段名，疑似 `profit_amount`/净营收拼写，当前仅保留原名。
- `is_renew_class_amount`、`is_renew_class_user`、`is_blacklist_user`、`is_same_trade_lead_period` 的最终业务语义待人工确认。
