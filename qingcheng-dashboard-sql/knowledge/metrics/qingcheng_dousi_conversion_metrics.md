# 青橙抖私转化指标

## 1. 来源与粒度

- SQL：`resources/raw_sql/data_center_qingcheng_2740.sql`
- 看板说明：`knowledge/dashboards/qingcheng_dousi_conversion_raw_20260729.md`
- 基础订单集：与 `2460` 相同的 `service_gmv + course_transfer_gmv`
- 最终粒度：`qici + channel_1 + channel_2 + dazu + leader_employee_email_name + grade_list + name`

## 2. 时间分层

`rule_friday_period` 由规则名短期次推导，`trade_friday_period` 由交易时间推导。`week_diff` 按两个周五期次的日期差分层：

| `week_diff` | 条件 | 净营收字段 | 退款字段 |
|---:|---|---|---|
| `0` | 规则周五期次等于交易周五期次 | `gmv_7` | `refund_7` |
| `1` | 交易周五比规则周五晚 7 天 | `gmv_14` | `refund_14` |
| `2` | 交易周五比规则周五晚 14 至 21 天 | `gmv_30` | `refund_30` |
| `4` | 交易周五比规则周五早 7 天 | `gmv_7_h` | `refund_7_p` |
| `3` | 其他情况，包括无法解析规则短期次 | `gmv_n30` | `refund_n30` |

字段名保留看板现有命名，解释时应以以上日期差条件为准，不能只按字段名推断自然日区间。

## 3. 净营收指标

| 指标 | SQL 口径 |
|---|---|
| `gmv_7` | `sum(case when week_diff = 0 then promit_amount else 0 end)` |
| `gmv_14` | `sum(case when week_diff = 1 then promit_amount else 0 end)` |
| `gmv_30` | `sum(case when week_diff = 2 then promit_amount else 0 end)` |
| `gmv_n30` | `sum(case when week_diff = 3 then promit_amount else 0 end)` |
| `gmv_7_h` | `sum(case when week_diff = 4 then promit_amount else 0 end)` |
| `gmv_total` | `sum(promit_amount)` |

闭合式：

```text
gmv_total = gmv_7 + gmv_14 + gmv_30 + gmv_n30 + gmv_7_h
```

## 4. 退款指标

来源订单集中的 `refund_amount` 为正数退款。2740 为保持看板展示口径，对各退款输出统一取负：

| 指标 | SQL 口径 |
|---|---|
| `refund_7` | `-sum(case when week_diff = 0 then refund_amount else 0 end)` |
| `refund_14` | `-sum(case when week_diff = 1 then refund_amount else 0 end)` |
| `refund_30` | `-sum(case when week_diff = 2 then refund_amount else 0 end)` |
| `refund_n30` | `-sum(case when week_diff = 3 then refund_amount else 0 end)` |
| `refund_7_p` | `-sum(case when week_diff = 4 then refund_amount else 0 end)` |
| `refund_total` | `-sum(refund_amount)` |

闭合式：

```text
refund_total = refund_7 + refund_14 + refund_30 + refund_n30 + refund_7_p
```

与 2460 或订单明细的正数退款比较时，应使用 `-refund_total`，或先把两边统一为相同符号。

## 5. 行保留条件

最终只保留：

```sql
coalesce(promit_amount, 0) <> 0
or coalesce(refund_amount, 0) <> 0
```

因此 2740 是有净营收或退款的标准订单结果，不输出金额全部为 0 的组合。

## 6. 2026-07-29 回归基线

| 期次 | 净营收 | 正数退款 |
|---|---:|---:|
| `20260710期` | 3,704,157.93 | 418,871.57 |
| `20260716期` | 2,362,957.14 | 323,155.67 |
| `20260722期` | 2,316,801.90 | 200,325.09 |
| `20260728期` | 938,218.35 | 205,411.65 |

- 共 46 个 `qici + channel_1 + channel_2` 组合。
- 与同版标准订单集逐组合比较，净营收和退款最大差额均为 `0.00`。
- 所有组合的净营收桶与退款桶闭合差均为 `0.00`。
- `20260803期`、`20260809期` 在验证时尚无非零标准订单金额行。
