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
| `class_refund_4` | `sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then 0 else refund_4 end)` 后逐层求和 | 班课行课阈值退款；用于替代前端旧公式 `sum(refund)-sum(Y_refund_4)` | 已从 SQL 入库 |
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
| `n_H_promit` | `sum(case when course_first_level_department_name = 'H业务线' then 0 else promit end)` | 非 H 原始净收，不剔除退 4；前端/下游再按 0.5 折算 | 已从 SQL 入库 |
| `H_promit_4` | `sum(case when course_first_level_department_name = 'H业务线' then promit_4 else 0 end)` | H 业务线净收，剔除退 4 | 已从 SQL 入库 |
| `n_H_promit_4` | `sum(case when course_first_level_department_name = 'H业务线' then 0 else promit_4 end)` | 非 H 原始净收，剔除退 4；前端/下游再按 0.5 折算 | 已从 SQL 入库 |

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
- 业务已确认 `H业务线` 按 100% 计入、所有 `非H业务线` 统一按 50% 折算；SQL 输出保留非 H 原始净收，前端公式再乘 0.5。

## 10. 折算后产出前端公式与源指标风险

看板自定义字段 `折算后产出` 当前公式为：

```text
ifnull(sum(${n_H_promit_4}) * 0.5 + (sum(${H_promit_4}) - sum(${Y_promit_4})), 0)
```

该公式本身只做前端聚合，准确性依赖源 SQL 中以下字段已经正确入桶：

- `H_promit_4`：H 业务线剔除行课阈值退款后的净收。
- `n_H_promit_4`：非 H 业务线剔除行课阈值退款后的原始净收，前端再乘 0.5。
- `Y_promit_4`：H 一对一剔除行课阈值退款后的净收，前端从 H 中扣除。
- `refund_4`：按班课 4 节、点睛班 2 节、一对一全额规则计入的退款。
- `class_refund_4`：班课行课阈值退款；班课退费前端公式应使用 `sum(class_refund_4)`，不再使用 `sum(refund)-sum(Y_refund_4)`。

若支付订单流水与看板不一致，优先排查 `course_first_level_department_name` / `course_second_level_department_name` 空值兜底、`gmv_t` 调课调班聚合粒度，以及 service 明细 `transfer_in_amount/transfer_out_amount` 是否补充命中内部调课调班。详细风险、诊断 SQL 和已验证样例见 `knowledge/sql_patterns/qingcheng_personal_completion_discounted_output_risks.md`。

2026-06-22 后补充：`income`、`refund`、`refund_4` 和科目数会先排除主交易层命中的内部调课调班调入/调出流水。该识别以 `dim_finance_order_change_df` 订单号映射为主，覆盖 `biz_type in (2,7)`，用于避免把内部 `调出退款` 当外部退费计入。

2026-07-03 后补充：当 `dim_finance_order_change_df` 漏掉链路，但 service 订单明细同订单已有 `transfer_in_amount/transfer_out_amount` 时，也会作为 `trade_type='调课调班'` 的内部变更补充识别。该规则影响 `income`、`refund`、`refund_4`、`p_sub/r_sub` 及其后续 `promit_4/H_promit_4/n_H_promit_4/Y_promit_4` 入桶。

2026-06-28 后补充：

- 任职窗口优先按 `order_attr.original_paid_time` 判定，避免历史订单退款串入青橙。
- 若组织链 `begin_time` 滞后，允许 `team_hist` 期次命中兜底保留当前有效订单。
- 命中订单变更链路但本身是正常成交的订单不得排除；`is_internal_order_change` 只用于剔除 `trade_type='调课调班'` 的内部变更流水本身。
