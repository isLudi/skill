# finance_dw.dim_finance_order_change_df

## 1. 中文名称

财务订单调课调班维表

## 2. 表用途

在青橙团队完成度【月/期】和个人转化 SQL 中识别父订单是否发生调课调班或课程转移，用于补充退款行课链路类型。

## 3. 数据粒度

待人工确认。当前 SQL 按 `parent_order_number` 关联退款订单。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | 待人工确认 | 日期分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| 无青橙部门字段 | 通过退款订单和财务业绩链路限定 | 单独查询时需谨慎 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `parent_order_number` | 待人工确认 | 父订单编号 | join `ord.order_number` |
| `order_change_type` | 待人工确认 | 调课调班类型 | 0 调课调班，1 课程转移 |
| `latest_child_order_status` | 待人工确认 | 最新子订单状态 | 过滤 2、6、7 |
| `biz_type` | 待人工确认 | 业务类型 | 过滤 2 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and latest_child_order_status in (2, 6, 7)
  and biz_type = 2
```

## 9. 常用 join key

- `parent_order_number = ord.order_number`

## 10. 常用 SQL 片段

```sql
case
    when order_change_type = 0 then '调课调班'
    when order_change_type = 1 then '课程转移'
    else cast(order_change_type as varchar)
end as refund_type
```

## 11. 注意事项

- 当前 SQL 只补充 `refund_type`，后续未直接用于 `refund_4` 计算，但可用于排查调课链路。
