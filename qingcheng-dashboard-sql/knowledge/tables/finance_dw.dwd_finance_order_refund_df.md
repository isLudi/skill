# finance_dw.dwd_finance_order_refund_df

## 1. 中文名称

财务订单退款原因明细日表

## 2. 表用途

当前青橙知识库仅在退费原因分析模板中使用该表，读取订单号、退费原因、原因源退款金额和退款类型。字段来自已成功产出工作簿的历史 SQL，尚未通过当前数据地图同步完整表结构。

## 3. 数据粒度

历史 SQL 显示同一订单可以有多个退费原因行；候选粒度为“订单—退款事务/原因”。主键、同一原因是否会重复以及退款事务标识字段仍待确认。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | string，待数据地图确认 | 日分区；历史模板使用 `now()-24h` 对应日期 |

## 6. 强制范围限定字段

该表未在历史 SQL 中提供部门字段。青橙范围通过先从青橙订单结果集得到 `order_number`，再 inner join 本表限定；不得无订单集合直接扫描并把全公司退款解释为青橙退款。

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `order_number` | string，待确认 | 订单号 | 关联青橙退款订单集合 |
| `refund_reason` | string，待确认 | 退费原因 | 空值/空串归“未获取到退费原因” |
| `refund_amount` | numeric，待确认 | 原因源退款金额 | 历史 SQL 取绝对值并除以 100 转元 |
| `refund_type` | integer，待确认 | 退款类型 | 历史模板限定 `in (1,2)`，枚举含义待确认 |
| `dt` | string，待确认 | 日分区 | 必填 |

## 8. 常用过滤条件

```sql
where r.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and r.refund_type in (1, 2)
```

复用前应先确认最新可用 `dt` 和退款类型枚举。

## 9. 常用 join key

- `r.order_number = gmv_order.order_number`
- 右侧青橙订单集合必须先去重，避免退款原因行被重复匹配。

## 10. 常用 SQL 片段

```sql
select
    r.order_number,
    coalesce(nullif(trim(r.refund_reason), ''), '未获取到退费原因') as refund_reason,
    cast(abs(coalesce(r.refund_amount, 0)) as double) / 100.0 as reason_source_amount
from finance_dw.dwd_finance_order_refund_df r
join target_orders o
  on r.order_number = o.order_number
where r.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and r.refund_type in (1, 2)
```

## 11. 注意事项

- `refund_amount` 在 Q1 中只作为原因分摊权重，最终原因金额来自青橙订单退款金额，不应直接替代订单退款事实。
- 同一订单多原因会产生多行；汇总前必须先按 `order_number + refund_reason` 聚合。
- 该文档包含待人工确认项，不授权自动编译或无界查询。
