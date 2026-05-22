# 青橙转化指标

## 1. 来源

`resources/raw_sql/qingcheng_conversion_raw_20260522.sql`

适用看板：`knowledge/dashboards/qingcheng_conversion_raw_20260522.md`

## 2. 指标计算粒度

该 SQL 分三层计算：

1. `gmv`：订单明细层，来自订单业绩表。
2. `udd`：用户层，按 `qici + qudao + grade_0 + zhuguan + name + uid` 汇总。
3. `ud`：顾问层，按 `qici + qudao + grade_0 + zhuguan + name` 汇总。

最终 `mm` 再与线索量 `bb_dedup` 合并，输出顾问-期次-渠道-年级粒度指标。

## 3. 收入和退款指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `income_amount` | `coalesce(income_amount / 100, 0)` | 订单明细收入，单位元 | 已从 SQL 入库 |
| `refund_amount` | `coalesce(refund_amount / 100, 0)` | 订单明细退款，单位元 | 已从 SQL 入库 |
| `promit_amount` | `income_amount - refund_amount` | 订单明细净营收 | 已从 SQL 入库 |
| `income` | `sum(income_amount)` | 顾问层总营收 | 已从 SQL 入库 |
| `refund` | `sum(refund_amount)` | 顾问层退款金额 | 已从 SQL 入库 |
| `promit` | `sum(promit_amount)` | 顾问层净营收 | 已从 SQL 入库 |
| `p_income` | `sum(case when is_on_period = 1 then income_amount else 0 end)` | 当期收入 | 已从 SQL 入库 |

## 4. 用户和科目指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `pay_user` | `count(distinct case when income > 0 then uid end)` | 支付用户数 | 已从 SQL 入库 |
| `p_pay_user` | `count(distinct case when income > 0 and p_income > 0 then uid end)` | 当期支付用户数 | 已从 SQL 入库 |
| `pay_sub` | 用户层 `count(distinct case when income_amount > 0 and sub != '定制方案' then sub end)` 后顾问层求和 | 支付科目数，不含定制方案 | 已从 SQL 入库 |
| `p_pay_sub` | 用户层 `count(distinct case when income_amount > 0 and is_on_period = 1 and sub != '定制方案' then sub end)` 后顾问层求和 | 当期支付科目数，不含定制方案 | 已从 SQL 入库 |
| `refund_user` | `count(distinct case when refund > 500 then uid end)` | 退款金额大于 500 的用户数 | 已从 SQL 入库 |
| `podan` | `count(distinct case when promit > 0 then uid end)` | 净营收大于 0 的破单用户数 | 已从 SQL 入库 |

## 5. 当期成交和成单周期

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `is_on_period` | `case when dd.qici = prc.qici_lead then 1 else 0 end` | 订单交易期次等于最新线索期次 | 已从 SQL 入库 |
| `sc` | 用户层 `date_diff('day', date(max(section_assign_time)), date(min(case when income_amount > 0 then trade_timestamp end)))`，顾问层 `sum(sc)` | 成单周期天数汇总 | 待人工确认聚合方式 |

## 6. 线索量和成本

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `v_lead` | 线索表中 `valid_lead_count = '1'` 计 1，按顾问-期次-渠道聚合并去重 | 青橙有效线索量 | 已从 SQL 入库 |
| `cost_lead` | `亚飞IP = 120`、`武汉图书 = 5`、其他 `0` | 二级渠道线索成本硬编码 | 已从 SQL 入库，待确认是否最新 |

## 7. 待确认事项

- `bb_dedup` 未按年级去重，可能导致同顾问同渠道多年级线索量只保留一个年级。
- `pay_sub` 和 `p_pay_sub` 在用户层计 distinct 科目，顾问层直接求和；如果同一用户跨渠道/顾问重复，需确认是否符合口径。
- `sc` 顾问层求和是否应改为平均周期、有效用户平均周期或中位数待确认。
- `p_` 前缀当前表示当期，即 `dd.qici = prc.qici_lead`。
- `cost_lead` 是硬编码，不依赖成本表；后续如果成本口径变化必须更新 SQL 和本文档。

