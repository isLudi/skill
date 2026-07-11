# finance_dw.dwd_finance_order_refund_df

## 1. 中文名称

订单退款明细表

## 2. 表用途

用于通过订单号补充退款原因。当前由 `resources/raw_sql/data_center_market_2353.sql` 使用，并对应 `market_channel_conversion_profile.md` 中的退费原因组件；2890 多科退费模型不使用该表。

## 3. 数据粒度

待确认；根据 SQL 推断为订单退款记录粒度，可能一单多条退款记录。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 日期分区 YYYYMMdd | 是 |
## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| 无 | - | - | 否 | SQL 中未使用 department_name 字段；若后续发现部门字段，需补充范围限定 |

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 日期分区 | 分区过滤 | 是 |
| order_number | bigint | 订单编号 | 与财务业绩明细按订单关联 | 是 |
| refund_reason | string | 退款原因 | 退费原因分析维度 | 是 |
| refund_type | bigint | 退款类型 | 当前 2353 使用 `refund_type = '1'`，业务枚举含义待确认 | 是 |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| biz_type | bigint | 业务类型，eg：1-好课｜7-高途 | 数据地图补充 | 否 |
| pay_number | bigint | 支付编号 | 数据地图补充 | 否 |
| op_employ_id | bigint | 操作人的员工号, -1:系统操作 | 数据地图补充 | 否 |
| pay_type | bigint | 流水类型，0,普通订单 1, 定金; 2, 尾款 | 数据地图补充 | 否 |
| data_source | bigint | 退款来源： 1:退款表 ods_gaotu_gaotu_refund_record ods_haoke_orders_refund_record 2:优惠券退费 ods_gaotu_coupon_coupon_order_refund | 数据地图补充 | 否 |
| refund_timestamp | timestamp | 退款成功时间 | 数据地图补充 | 否 |
| create_timestamp | timestamp | 创建时间 | 数据地图补充 | 否 |
| update_timestamp | timestamp | 更新时间 | 数据地图补充 | 否 |
| refund_amount | bigint | 退款金额(分) | 数据地图补充 | 否 |
| refund_order_number | string | 退款单号 | 数据地图补充 | 否 |
| goods_type | bigint | 商品类型，2-课程 \| 50-实物 | 数据地图补充 | 否 |

## 8. 常用过滤条件

- `t.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')`
- `t.refund_type = '1'`

## 9. 常用 join key

- `order_number`：与 `finance_dw.app_finance_performance_extend_details_hf.order_number` 关联补充退费原因。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.order_number,
    t.refund_reason,
    t.refund_type
from finance_dw.dwd_finance_order_refund_df t
where t.dt = 'YYYYMMDD'
limit 20;
```

### 退费原因分布

```sql
select
    t.refund_reason,
    count(*) as cnt
from finance_dw.dwd_finance_order_refund_df t
where t.dt = 'YYYYMMDD'
  and t.refund_type = '1'
group by t.refund_reason
order by cnt desc
limit 100;
```

## 11. 注意事项

- 表结构已结合数据地图与当前 2353 使用字段补充；主键和分区刷新延迟仍待人工确认。
- `refund_type = '1'` 的业务含义待确认，不能擅自解释为全部退款或部分退款。
- 若 `order_number` 在该表不唯一，关联退费原因会放大财务业绩明细结果。
