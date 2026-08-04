# 青橙退费原因分析指标

## 1. 适用 SQL

`resources/raw_sql/qingcheng_refund_reason_analysis_20260718.sql`

## 2. 计算与输出粒度

```text
order_reason_grain = qici + order_number + refund_reason
output_grain       = qici + channel + org + grade + consultant + uid + refund_reason
```

## 3. 指标定义

| 字段 | 定义 | 聚合规则 | 状态 |
|---|---|---|---|
| `refund_reason` | 财务退款原因；空值归“未获取到退费原因” | 维度 | 已确认：使用财务退款原因字段和当前 SQL 的退款类型范围 |
| `refund_amount` | 订单退款金额按原因权重分摊后的金额（元） | 可 sum | 已确认：按财务原因源金额权重分摊；无权重时等额分摊 |
| `refund_order_count` | 用户—原因涉及的去重订单数 | 当前粒度可 sum；跨原因会重复 | 已从 SQL 入库 |
| `user_total_refund_amount` | 用户同切片全部原因金额之和 | 原因行重复带出，不可 sum | 已从 SQL 入库 |
| `refund_head_key` | 用户总退费金额 >500 元时的用户级键 | `count(distinct ...)` | 已确认：退费正价课人头阈值为 500 元（严格大于 500） |

## 4. 守恒校验

- 每个订单的原因分摊金额合计应等于 `gmv_order.order_refund_amount`。
- 全量原因金额合计应等于目标结果期次范围内的订单退款金额。
- 加入架构表前后金额应守恒；架构只补维度，不应放大行数。

## 5. 状态

退款类型范围 `refund_type in (1, 2)`、原因金额分摊规则和 500 元人头阈值已由业务确认。后续仍需按本文件的订单粒度和金额守恒规则执行，不能因原因维度可执行而省略订单集合限域或重复键检查。
