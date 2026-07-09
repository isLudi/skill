# 青橙转化指标

## 1. 来源

`resources/raw_sql/data_center_qingcheng_2460_20260709.sql`

适用看板：`knowledge/dashboards/qingcheng_conversion_raw_20260626.md`

## 2. 指标计算粒度

该 SQL 分三层计算：

1. `gmv`：订单明细层，来自订单业绩表。
2. `udd`：用户层，按 `qici + qudao + grade_0 + zhuguan + name + uid` 汇总。
3. `ud`：顾问层，按 `qici + qudao + grade_0 + zhuguan + name` 汇总。

最终 `mm` 再与线索量 `bb_dedup` 合并，输出顾问-期次-渠道-年级粒度指标。当前版本已将线索侧和订单侧对齐键扩展到年级和主管，避免同顾问同渠道跨年级吞数。

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

当前 canonical 版本的营收明细以 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 为主：

- 先用 `filled_course_first_level_department_name` / `filled_course_second_level_department_name` 兜底空课程部门。
- 再基于 service 明细自带的 `transfer_in_amount` / `transfer_out_amount`，剔除已在主明细中体现的内部调课调班金额，避免把 `调出退款` 当成外部退费。
- `order_change` 与 `re_ke` 只用于识别内部调课调班链路和计算 `refund_4` / 点睛退 2 节，不直接替代 service 主明细营收。

## 4. 用户和科目指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `pay_user` | `count(distinct case when income > 0 then uid end)` | 支付用户数 | 已从 SQL 入库 |
| `p_pay_user` | `count(distinct case when income > 0 and p_income > 0 then uid end)` | 当期支付用户数 | 已从 SQL 入库 |
| `pay_sub` | 用户层 `count(distinct case when income_amount > 0 and sub != '定制方案' then sub end)` 后顾问层求和 | 支付科目数，不含定制方案 | 已从 SQL 入库 |
| `p_pay_sub` | 用户层 `count(distinct case when income_amount > 0 and is_on_period = 1 and sub != '定制方案' then sub end)` 后顾问层求和 | 当期支付科目数，不含定制方案 | 已从 SQL 入库 |
| `refund_user` | `count(distinct case when refund > 500 then uid end)` | 退款金额大于 500 的用户数 | 已从 SQL 入库 |
| `podan` | `count(distinct case when ((H_promit_4 - Y_promit_4) + n_H_promit_4 * 0.5) > 0 then uid end)` | 折算净收为正的破单用户数 | 已从 SQL 入库 |

## 5. 当期成交和成单周期

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `is_on_period` | `case when dd.qici0 = dd.period then 1 else 0 end` | `rule_name` 提取短期次等于结果期次短码；20260716 热修中 `0717期` 会在结果期次为 `20260716期` 时归一为 `0716期` | 已从 SQL 入库 |
| `sc` | 用户层 `date_diff('day', date(max(section_assign_time)), date(min(case when income_amount > 0 then trade_timestamp end)))`，顾问层 `sum(sc)` | 成单周期天数汇总 | 待人工确认聚合方式 |

`qici` 当前按业务日历优先、`trade_timestamp` 周五逻辑兜底生成：

- `2026-07-14` 至 `2026-07-18`：归为 `20260716期`。
- 周二到周日：归到当周周五期次。
- 周一：回拨到上一周周五期次。
- 线索侧 `bb.qici` 对 `group_period_year + group_period_term` 增加同样的 `2026-07-14` 至 `2026-07-18` 优先分支。

## 6. 线索量和成本

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `v_lead` | 线索表中 `valid_lead_count = '1'` 计 1，按顾问-期次-渠道-年级-主管聚合；`bb_dedup` 只在完全同维度重复时保留 `rn = 1` | 青橙有效线索量 | 已从 SQL 入库，当前版本用于保留真实年级例子数 |
| `cost_lead` | `亚飞IP = 120`、`武汉图书 = 20`、`抖音私信 = 130`、`进校 = 70`、其他 `0` | 二级渠道线索成本硬编码 | 已从 SQL 入库，来源于 2026-06-26 canonical SQL |

## 7. 待确认事项

- 当前版本已修复 `bb_dedup` 未按年级对齐导致的吞数问题；若同顾问同一期次同渠道同年级同主管仍有多行，保留 `rn = 1` 是否合理待人工确认。
- `pay_sub` 和 `p_pay_sub` 在用户层计 distinct 科目，顾问层直接求和；如果同一用户跨渠道/顾问重复，需确认是否符合口径。
- `sc` 顾问层求和是否应改为平均周期、有效用户平均周期或中位数待确认。
- `p_` 前缀当前表示当期，即 `dd.qici0 = dd.period`；20260716 热修必须同步修正 `qici0`，否则 `p_pay_user`、`p_pay_sub`、`p_income` 会被误归为往期。
- 2026-06-26 canonical 版本课程一级部门白名单包含 `H业务线`、`LL业务线`、`TUTU`、`TT`、`A业务线`、`EM业务线`、`KA业务线`、`TT业务线`、`创新中心`；二级部门白名单包含 `创新学部`、`升学规划中心`、`线上考研学部`。
- `cost_lead` 是硬编码，不依赖成本表；后续如果成本口径变化必须更新 SQL 和本文档。
- `jieliang` 为 `case when v_lead > 5 then employee_email_name else '0' end` 的输出标记，业务含义待人工确认。
