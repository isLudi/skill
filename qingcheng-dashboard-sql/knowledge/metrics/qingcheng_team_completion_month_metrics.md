# 青橙团队完成度【月】指标

## 1. 来源

`resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql`

适用看板：`knowledge/dashboards/qingcheng_team_completion_month_raw_20260522.md`

## 2. 指标计算粒度

该 SQL 分三层计算：

1. `rd_0`：用户/员工/期次/课程部门/交易状态/年级粒度，计算收入、退款、剔除行课阈值退款和科目数。
2. `renchan`：员工-期次-月份-主管粒度，计算 H/非 H 净收、退款人数、破单基础。
3. 最终查询：团队目标月粒度，按 `month + xuebu + xiaozu + dazu + emye_c + goal` 输出。

## 3. 金额指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `income` | `sum(case when name_total_price >= 0 then name_total_price else 0 end)` 后逐层求和 | 收入金额 | 已从 SQL 入库 |
| `refund` | `sum(case when name_total_price < 0 then abs(name_total_price) else 0 end)` 后逐层求和 | 全部退款金额 | 已从 SQL 入库 |
| `promit` | `income - refund`，后逐层求和 | 净收，不剔除行课阈值退款 | 已从 SQL 入库 |
| `refund_4` | 按行课阈值计入的退款金额 | 剔除行课阈值退款 | 已从 SQL 入库 |
| `promit_4` | `income - refund_4`，后逐层求和 | 剔除行课阈值退款后的净收 | 已从 SQL 入库 |

## 4. 行课阈值退款指标

| 场景 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| 一对一 | `course_second_level_department_name = '一对一学部' and course_first_level_department_name = 'H业务线'` 时，所有负金额计入 `refund_4` | 一对一全额计入行课阈值退款 | 已从 SQL 入库 |
| 点睛班课 | `clazz_name like '%点睛%' and name_total_price < 0 and re_lc < 2` | 已完课节数小于 2 计入 `refund_4` | 已从 SQL 入库 |
| 非点睛班课 | `(clazz_name not like '%点睛%' or clazz_name is null) and name_total_price < 0 and re_lc < 4` | 已完课节数小于 4 计入 `refund_4` | 已从 SQL 入库 |

`re_lc` 来自 `finance_dw.dm_finance_order_refund_detail_df.full_refund_chain_finish_lesson_count`，空值按 0。

## 5. H/非 H 折算指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `H_promit` | `sum(case when course_first_level_department_name = 'H业务线' then promit else 0 end)` | H 业务线净收，不剔除退 4 | 已从 SQL 入库 |
| `n_H_promit` | `0.5 * (sum(promit) - H_promit)` | 非 H 净收按 0.5 折算，不剔除退 4 | 已从 SQL 入库 |
| `H_promit_4` | `sum(case when course_first_level_department_name = 'H业务线' then promit_4 else 0 end)` | H 业务线净收，剔除退 4 | 已从 SQL 入库 |
| `n_H_promit_4` | `0.5 * (sum(promit_4) - H_promit_4)` | 非 H 净收按 0.5 折算，剔除退 4 | 已从 SQL 入库 |

## 6. 用户和破单指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `re_payer` | `count(distinct case when refund > 0 then user_id1 end)` | 全部退款用户数 | 已从 SQL 入库 |
| `re_payer_4` | `count(distinct case when refund_4 > 0 then user_id1 end)` | 行课阈值退款用户数 | 已从 SQL 入库 |
| `podan` | `count(distinct case when promit > 0 then name end)` | 净收大于 0 的伙伴数 | 已从 SQL 入库 |
| `podan_4` | `count(distinct case when promit_4 > 0 then name end)` | 剔除退 4 净收大于 0 的伙伴数 | 已从 SQL 入库 |

## 7. 目标和展示字段

| 字段 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `goal` | `cast(qg.goal as decimal)` | 团队月目标 | 已从 SQL 入库，来源待确认 |
| `emye_c` | `cast(qg.emye_c as decimal)` | 目标层级/展示控制字段 | 待人工确认 |
| `xiaozu` | `case when emye_c != '1' then xiaozu1 else '-' end` | 小组展示字段 | 已从 SQL 入库 |

## 8. 待确认事项

- `price` 是否已经是元，当前 SQL 直接使用。
- `refund_4` 名称虽然含 “4”，但点睛阈值是 2 节，非点睛是 4 节，一对一全部计入。
- 2026-06-22 后，`income`、`refund`、`refund_4` 和科目数会先排除主交易层命中的内部调课调班调入/调出流水；识别来自 `dim_finance_order_change_df` 订单号映射，覆盖 `biz_type in (2,7)`。
- 非 H 业绩按 0.5 折算是否适用于所有非 H 课程部门待确认。
- `temp_table.dingxi01_qing_team_goal.goal` 的目标单位需确认是否与 `promit` 同单位。
- `moth` 字段拼写保留历史 SQL，语义为月份。
