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
| `dt` | string | 日期分区 |
## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| 无青橙部门字段 | 通过退款订单和财务业绩链路限定 | 单独查询时需谨慎 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `parent_order_number` | bigint | 父订单编号 | join `ord.order_number` |
| `order_change_type` | bigint | 调课调班类型 | 0 调课调班，1 课程转移 |
| `latest_child_order_status` | bigint | 最新子订单状态 | 过滤 2、6、7 |
| `biz_type` | bigint | 业务类型 | 过滤 2 |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `order_number` | bigint | 订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_number` | bigint | 原始订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_child_order_number` | bigint | 最新子订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `transfer_in_amount` | bigint | 调入金额（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_final_paid_timestamp` | timestamp | 原始订单最后一次支付时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_child_order_final_paid_timestamp` | timestamp | 最新子订单最后一次支付时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_change_chain` | string | 调课链路 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_orginal_order` | string | 是否原始父订单，eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `transfer_in_timestamp` | timestamp | 调入时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `transfer_out_amount` | bigint | 调出金额（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `transfer_out_timestamp` | timestamp | 调出时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

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
