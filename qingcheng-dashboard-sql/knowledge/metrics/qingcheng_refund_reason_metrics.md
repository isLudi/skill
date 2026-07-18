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
| `refund_reason` | 财务退款原因；空值归“未获取到退费原因” | 维度 | 原始字段已在历史 SQL 使用；枚举待维护 |
| `refund_amount` | 订单退款金额按原因权重分摊后的金额（元） | 可 sum | 分摊权重待业务确认 |
| `refund_order_count` | 用户—原因涉及的去重订单数 | 当前粒度可 sum；跨原因会重复 | 已从 SQL 入库 |
| `user_total_refund_amount` | 用户同切片全部原因金额之和 | 原因行重复带出，不可 sum | 已从 SQL 入库 |
| `refund_head_key` | 用户总退费金额 >500 元时的用户级键 | `count(distinct ...)` | 阈值待确认 |

## 4. 守恒校验

- 每个订单的原因分摊金额合计应等于 `gmv_order.order_refund_amount`。
- 全量原因金额合计应等于目标结果期次范围内的订单退款金额。
- 加入架构表前后金额应守恒；架构只补维度，不应放大行数。

## 5. 状态

`refund_reason` 和原因分摊金额契约保持 `pending_confirmation`，只允许候选解释、probe 或人工 SQL 计划。
