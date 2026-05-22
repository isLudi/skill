# finance_dw.dwd_finance_order_refund_df

## 1. 中文名称

订单退款明细表

## 2. 表用途

用于通过订单号补充退款原因。当前仅在 `resources/raw_sql/refund_reason_analysis.sql` 中出现。

## 3. 数据粒度

待确认；根据 SQL 推断为订单退款记录粒度，可能一单多条退款记录。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string，待确认 | 日期分区 YYYYMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| 无 | - | - | 否 | SQL 中未使用 department_name 字段；若后续发现部门字段，需补充范围限定 |

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string，待确认 | 日期分区 | 分区过滤 | 是 |
| order_number | 待确认 | 订单编号 | 与财务业绩明细按订单关联 | 是 |
| refund_reason | string，待确认 | 退款原因 | 退费原因分析维度 | 是 |
| refund_type | string，待确认 | 退款类型 | 过滤退款类型；历史 SQL 使用 `refund_type = '1'` | 是 |

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

- 表结构来自 `resources/raw_sql/refund_reason_analysis.sql` 使用字段推断，真实 DDL、字段类型、主键、分区刷新延迟均待人工确认。
- `refund_type = '1'` 的业务含义待确认，不能擅自解释为全部退款或部分退款。
- 若 `order_number` 在该表不唯一，关联退费原因会放大财务业绩明细结果。
