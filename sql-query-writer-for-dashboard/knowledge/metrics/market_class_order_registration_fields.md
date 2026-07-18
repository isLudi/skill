# 市场顾问指定班级订单与报名类型字段口径

## 1. 适用 SQL

- `resources/raw_sql/market_class_order_detail_20260718.sql`
- `resources/raw_sql/market_class_order_registration_type_20260718.sql`

## 2. 计算与输出粒度

```text
calculation_grain = order_number + clazz_biz_number + transaction_event
output_grain      = order_number + clazz_biz_number
```

## 3. 关键字段

| 字段 | 口径 | 聚合规则 |
|---|---|---|
| `subject` | 从 `course_subject` 归一为语文/数学/英语/物理/化学 | 维度 |
| `paid_performance_amount` | 订单—班级内正向业绩金额汇总 | 可在确认班级金额不重复后汇总 |
| `refund_performance_amount` | 订单—班级内退款业绩金额汇总 | 同上 |
| `net_performance_amount` | 正向业绩减退款业绩 | 同上 |
| `registration_type` | `bind_type in (1,2)` 为暑秋联报，`bind_type=0` 为单秋 | 维度；混合值按联报优先 |
| `classification_basis` | 记录学年、学季和 bind_type 证据 | 诊断字段，不聚合 |
| `performance_detail_id_count` | 财务明细 ID 数 | 仅用于重复/粒度诊断 |
| `service_row_count` | service 源行数 | 仅用于报名类型侧重复诊断 |

## 4. 待确认项

- `registration_type` 是复杂多表模板维度，当前不允许自动编译。
- 其他学年/学季的 `bind_type` 是否保持同一业务解释待确认。
- 订单跨多个班级时，金额如何分摊或去重必须由具体 QuerySpec 明确。
