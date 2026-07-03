# finance_dw.dim_finance_order_change_df

## 1. 中文名称

财务订单调课调班维表

## 2. 表用途

在青橙团队完成度【月/期】和个人转化 SQL 中识别订单是否发生调课调班或课程转移。当前用途包括：补充退款行课链路类型，以及在主交易层识别内部调课调班调入/调出流水，避免将其误算为外部支付或外部退款。2026-07-03 起，本表仍是主识别来源，但 service 明细 `transfer_in_amount/transfer_out_amount` 也作为漏链路时的补充识别。

## 3. 数据粒度

待人工确认。当前 SQL 会把 `order_number`、`parent_order_number`、`original_order_number`、`latest_child_order_number` 展开成订单号映射，再按订单号聚合后关联主交易层和退款订单层。

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
| `biz_type` | bigint | 业务类型 | 当前完成度 SQL 覆盖 2 和 7 |

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
  and biz_type in (2, 7)
```

## 9. 常用 join key

- 主交易层：将 `order_number`、`parent_order_number`、`original_order_number`、`latest_child_order_number` 展开为 `join_order_number` 后，按 `rd.order_number = order_change.order_number` 关联。
- 退款行课层：按 `ord.order_number = order_change.order_number` 补充调课调班/课程转移类型。

## 10. 常用 SQL 片段

```sql
case
    when order_change_type = 0 then '调课调班'
    when order_change_type = 1 then '课程转移'
    else cast(order_change_type as varchar)
end as refund_type
```

## 11. 注意事项

- 完成度 SQL 不应只把本表接在退款明细层。若只接 `re_ke/ord`，主交易层的 `调出退款` 会在 `re_lc=0` 时被误算为 4 节内退费。
- `biz_type=7` 也可能承载青橙调课调班链路；后续生成个人/团队完成度 SQL 时不得回退为只过滤 `biz_type=2`。
- 主交易层识别为内部调课调班调入/调出后，应从 `income`、`refund`、`refund_4` 和科目数中排除，不按外部支付/退款入桶。
- 个人完成度/个人转化中的 `gmv_t` 调课调班聚合必须保留订单、课程、期次、科目和课程部门粒度；不要按 `name + user_id1` 粗粒度汇总，否则同一顾问同一用户多笔调课调班可能吃掉退款或错配课程部门。
- 本表漏匹配不代表订单一定不是内部调课调班；若 service 订单明细同订单存在 `transfer_in_amount/transfer_out_amount`，完成度 SQL 会把该 service transfer 作为补充识别，避免正向调入误入外部收入。
