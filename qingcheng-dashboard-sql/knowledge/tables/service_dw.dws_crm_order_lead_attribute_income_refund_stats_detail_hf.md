# service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf

## 1. 中文名称

CRM 订单线索归因收入退款明细小时表

## 2. 表用途

在青橙转化 SQL 中作为订单业绩明细主表，提供订单、用户、支付、退款、营收、课程、业绩归属部门和交易时间等字段。

## 3. 数据粒度

待人工确认。当前 SQL 以订单/线索归因明细使用，字段包含 `order_number`、`lead_id`、`original_order_user_number`。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | 待人工确认 | 日期分区 |
| `hour` | 待人工确认 | 小时分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `performance_second_level_department_name` | `'青橙项目部'` | 业绩归属二级部门，青橙转化核心过滤 |
| `course_first_level_department_name` | 多业务线白名单 | 课程一级部门，历史 SQL 使用长白名单 |
| `course_second_level_department_name` | 长白名单，包含 `'青橙项目部'` | 课程二级部门，历史 SQL 使用长白名单 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_id` | 待人工确认 | 线索 ID | join 线索表 |
| `original_order_user_number` | 待人工确认 | 原始订单用户编号 | 转化 SQL 中记为 `uid` |
| `order_number` | 待人工确认 | 订单号 | 订单明细字段 |
| `order_status` | 待人工确认 | 订单状态 | 订单明细字段 |
| `trade_timestamp` | 待人工确认 | 交易时间 | 计算 `qici` 和成单周期 |
| `pay_success_timestamp` | 待人工确认 | 支付成功时间 | 订单明细字段 |
| `income_amount` | 待人工确认 | 收入金额，分 | SQL 除以 100 转元 |
| `refund_amount` | 待人工确认 | 退款金额，分 | SQL 除以 100 转元 |
| `performance_employee_email_name` | 待人工确认 | 业绩归属员工 | join 线索员工和最终顾问维度 |
| `performance_second_level_department_name` | 待人工确认 | 业绩归属二级部门 | 青橙过滤 |
| `mapping_school_subject_name` | 待人工确认 | 映射学科 | 非定制方案科目统计 |
| `course_first_level_department_name` | 待人工确认 | 课程一级部门 | 长白名单过滤 |
| `course_second_level_department_name` | 待人工确认 | 课程二级部门 | 长白名单过滤 |
| `pay_group_period_name` | 待人工确认 | 支付期次 | 当前 SQL 取出但未作为核心逻辑 |
| `trade_group_period_name` | 待人工确认 | 交易期次 | 当前 SQL 取出但未作为核心逻辑 |
| `lead_period_name` | 待人工确认 | 线索期次 | 当前 SQL 取出 |
| `trade_period_name` | 待人工确认 | 交易期次 | 当前 SQL 取出 |
| `pay_period_name` | 待人工确认 | 支付期次 | 当前 SQL 取出 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '2' hour, 'HH')
  and performance_second_level_department_name = '青橙项目部'
  and (income_amount <> 0 or refund_amount <> 0)
```

课程部门白名单来自 `qingcheng_conversion_raw_20260614.sql`，非常长；复用时优先从原始 SQL 拷贝，不要手工删减。

## 9. 常用 join key

- `lead_id`
- `performance_employee_email_name`
- `original_order_user_number`

## 10. 常用 SQL 片段

```sql
coalesce(income_amount / 100, 0) as income_amount,
coalesce(refund_amount / 100, 0) as refund_amount,
coalesce(income_amount / 100, 0) - coalesce(refund_amount / 100, 0) as promit_amount
```

## 11. 注意事项

- 金额字段在原表疑似以分为单位，SQL 除以 100 转为元。
- `promit_amount` 为历史 SQL 字段名，含义为净营收。
- 交易期次 `qici` 由 `trade_timestamp` 按周五期次规则计算，原 SQL 使用三参数 `date_add`，后续生成新 SQL 时需改为 `interval`。
