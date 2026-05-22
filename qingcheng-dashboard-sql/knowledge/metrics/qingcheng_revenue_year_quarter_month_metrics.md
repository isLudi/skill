# 青橙年季月营收指标

## 1. 来源

`resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql`

适用看板：`knowledge/dashboards/qingcheng_revenue_year_quarter_month_raw_20260522.md`

## 2. 指标计算粒度

该 SQL 先处理订单明细，再按用户和交易状态聚合，最终输出到：

```text
课程一级部门 + 课程二级部门 + 交易状态 + 主管 + 大主管 + 学部 + 年级
+ 期次 + 最大交易日期 + 年 + 季度 + 月
```

## 3. 金额指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `name_total_price` | 正常订单 `sum(price)`；调课调班按 `name + user_id1` 窗口汇总 `sum(price)` 后保留一条 | 订单处理后的金额 | 已从 SQL 入库 |
| `income` | `sum(case when name_total_price >= 0 then name_total_price else 0 end)` 后最终 `sum(income)` | 收入金额 | 已从 SQL 入库 |
| `refund` | `sum(case when name_total_price < 0 then abs(name_total_price) else 0 end)` 后最终 `sum(refund)` | 退款金额，取负金额绝对值 | 已从 SQL 入库 |
| `promit` | `sum(name_total_price)` 后最终 `sum(promit)` | 净营收 | 已从 SQL 入库 |

## 4. 科目指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `sub` | `count(distinct case when subject not in ('选科志愿','定制方案') then subject end)` | 非选科志愿/定制方案科目数 | 已从 SQL 入库 |
| `p_sub` | `trade_status = '支付'` 时 `sum(sub)` | 支付科目数 | 已从 SQL 入库 |
| `r_sub` | `trade_status = '退款' and refund > 500` 时 `sum(sub)` | 大额退款科目数 | 已从 SQL 入库 |

## 5. 用户指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `p_payer` | `count(distinct case when trade_status = '支付' then user_id1 end)` | 支付用户数 | 已从 SQL 入库 |
| `r_payer` | `count(distinct case when trade_status = '退款' and refund > 500 then user_id1 end)` | 大额退款用户数 | 已从 SQL 入库 |

## 6. 时间维度

| 字段 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `qici` | 按 `trade_time` 计算周五期次 | 交易期次 | 已从 SQL 入库 |
| `max_trade_date` | `date(max(cast(trade_time as timestamp)))` | 分组内最大交易日期 | 已从 SQL 入库 |
| `max_year` | `year(max(trade_time)) || '年'` | 年维度 | 已从 SQL 入库 |
| `max_quarter` | `'Q' || quarter(max(trade_time))` | 季度维度 | 已从 SQL 入库 |
| `max_month` | `month(max(trade_time)) || '月'` | 月维度 | 已从 SQL 入库 |

## 7. 交易状态

| 原始条件 | 输出 |
|---|---|
| `trade_status like '%退款%'` | `退款` |
| `trade_status like '%支付%'` | `支付` |
| 其他 | `未知` |

## 8. 待确认事项

- `price` 是否已经是元，还是需要除以 100，需与财务表确认；本 SQL 直接使用 `price`。
- `real_price_0` 在 `dd_0` 中计算但后续未使用。
- 调课调班只保留 `name + user_id1` 的一条记录，是否会影响年/月/课程维度待确认。
- `promit` 为历史 SQL 命名，含义为净营收。
- `r_sub` 和 `r_payer` 只统计退款金额大于 500 的情况。

