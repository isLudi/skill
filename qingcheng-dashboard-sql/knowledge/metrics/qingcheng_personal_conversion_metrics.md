# 青橙个人转化指标

## 1. 来源

`resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`

适用看板：`knowledge/dashboards/qingcheng_personal_conversion_raw_20260522.md`

## 2. 指标计算粒度

该 SQL 分三层计算：

1. `rd_0`：用户/员工/期次/课程部门/交易状态/年级粒度，计算收入、全部退款、行课阈值退款、支付科目数和退款科目数。
2. `renchan`：以 `temp_table.dingxi01_qing_team_jg` 为主表，按个人-期次-主管-大组-经理-学部粒度聚合。
3. 最终查询：个人期次粒度输出，并带月份 `moth`。

最终粒度：

```text
qici + moth + name + leader_employee_email_name + dazu + jingli + xuebu
```

## 3. 金额基础指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `income` | `sum(case when name_total_price >= 0 then name_total_price else 0 end)` 后逐层求和 | 收入金额 | 已从 SQL 入库 |
| `refund` | `sum(case when name_total_price < 0 then abs(name_total_price) else 0 end)` 后逐层求和 | 全部退款金额 | 已从 SQL 入库 |
| `promit` | `income - refund`，后逐层求和 | 净收，不剔除行课阈值退款 | 已从 SQL 入库 |
| `refund_4` | 按行课阈值计入的退款金额 | 剔除行课阈值退款 | 已从 SQL 入库 |
| `promit_4` | `income - refund_4` | 剔除行课阈值退款后的净收 | 已从 SQL 入库 |

## 4. 行课阈值退款指标

| 场景 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| 一对一 | `course_second_level_department_name = '一对一学部' and course_first_level_department_name = 'H业务线'` 时，所有负金额计入 `refund_4` | 一对一负金额全额计入行课阈值退款 | 已从 SQL 入库 |
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

## 6. H 一对一拆分指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `Y_promit_4` | `sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then promit_4 else 0 end)` | H 一对一剔除退 4 净收 | 已从 SQL 入库 |
| `Y_income_4` | `sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then income else 0 end)` | H 一对一收入 | 已从 SQL 入库 |
| `Y_refund_4` | `sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then refund_4 else 0 end)` | H 一对一行课阈值退款 | 已从 SQL 入库 |
| `H_income_4` | `sum(case when course_first_level_department_name = 'H业务线' then income else 0 end)` | H 业务线收入 | 已从 SQL 入库 |
| `H_refund_4` | `sum(case when course_first_level_department_name = 'H业务线' then refund_4 else 0 end)` | H 业务线行课阈值退款 | 已从 SQL 入库 |

## 7. 用户和科目指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `re_payer` | `count(distinct case when refund > 0 then user_id1 end)` | 全部退款用户数 | 已从 SQL 入库 |
| `re_payer_4` | `count(distinct case when refund_4 > 0 then user_id1 end)` | 行课阈值退款用户数 | 已从 SQL 入库 |
| `in_payer_4` | `count(distinct case when promit_4 > 0 then user_id1 end)` | 剔除退 4 后净收大于 0 的用户数 | 已从 SQL 入库 |
| `p_sub` | `count(distinct case when subject not in ('选科志愿','定制方案') and name_total_price > 0 then subject end)` | 支付科目数 | 已从 SQL 入库 |
| `r_sub` | `count(distinct case when subject not in ('选科志愿','定制方案') and name_total_price < 0 then subject end)` | 退款科目数；当前后续未输出 | 已从 SQL 入库 |
| `j_sub` | `sum(jing_sub)`，其中 `jing_sub = p_sub` | 当前实际为支付科目求和，命名为净科目数 | 已从 SQL 入库，命名待确认 |
| `podan` | `count(distinct case when promit > 0 then employee_email_name end)` | 个人维度下净收大于 0 的破单标记，通常为 0 或 1 | 已从 SQL 入库 |

## 8. 组织维度字段

| 字段 | 来源 | 说明 | 状态 |
|---|---|---|---|
| `qici` | `temp_table.dingxi01_qing_team_jg.qici` | 架构期次，也是个人输出期次 | 已从 SQL 入库 |
| `moth` | `temp_table.dingxi01_qing_qi_moth.moth` | 期次映射月份 | 已从 SQL 入库 |
| `name` | `qtg.employee_email_name as name` | 个人姓名/邮箱名 | 已从 SQL 入库 |
| `leader_employee_email_name` | `temp_table.dingxi01_qing_team_jg` | 直属主管 | 已从 SQL 入库，语义待确认 |
| `dazu` | `temp_table.dingxi01_qing_team_jg` | 大组 | 已从 SQL 入库，语义待确认 |
| `jingli` | `temp_table.dingxi01_qing_team_jg` | 经理 | 已从 SQL 入库，语义待确认 |
| `xuebu` | `temp_table.dingxi01_qing_team_jg` | 学部 | 已从 SQL 入库，语义待确认 |

## 9. 待确认事项

- `j_sub` 当前没有扣减 `r_sub`，是否应定义为“支付科目数”而非“净科目数”待确认。
- 个人转化以 `temp_table.dingxi01_qing_team_jg` 为主表，需确认该表是否一人一期唯一。
- `podan` 在个人粒度下通常等价于个人是否净收大于 0 的 0/1 标记，是否需要保留 `count(distinct ...)` 形式待确认。
- H 一对一拆分字段名称使用 `Y_` 前缀，当前按 SQL 理解为“一对一”，命名来源待确认。
- `price` 是否已经是元，当前 SQL 直接使用。
- 非 H 业绩按 0.5 折算是否适用于所有非 H 课程部门待确认。
