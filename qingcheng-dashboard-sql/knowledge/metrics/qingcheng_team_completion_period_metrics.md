# 青橙团队完成度【期】指标

## 1. 来源

`resources/raw_sql/data_center_qingcheng_2680.sql`

适用看板：`knowledge/dashboards/qingcheng_team_completion_period_raw_20260522.md`

## 2. 指标计算粒度

该 SQL 分三层计算：

1. `rd_0`：用户/员工/期次/课程部门/交易状态/年级粒度，计算收入、退款、剔除行课阈值退款和科目数。
2. `renchan`：员工-期次-主管粒度，计算 H/非 H 净收、退款人数、破单基础。
3. 最终查询：团队目标期次粒度，按 `qici + xuebu + xiaozu + dazu + emye_c + goal` 输出。

## 3. 与团队完成度【月】指标差异

指标公式与 `qingcheng_team_completion_month_metrics.md` 基本一致，主要差异是目标对齐粒度：

| 项目 | 月度版 | 期次版 |
|---|---|---|
| 目标字段 | `qg.month` | `qg.qici` |
| 实际字段 | `rc.moth` | `rc.qici` |
| 目标表 | `temp_table.dingxi01_qing_team_goal` | `temp_table.dingxi01_qing_team_g_qi` |

## 4. 金额指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `income_all` | `sum(case when source_type = 'service' then income_amount_yuan else 0 end)` | service 主事实的全部收入；当前团队营收金额直接聚合该字段 | 已从 2026-08-05 canonical SQL 入库 |
| `refund_all` | `sum(case when source_type = 'service' then refund_amount_yuan else 0 end)` | service 主事实的全部退款；当前团队退费金额直接聚合该字段 | 已从 2026-08-05 canonical SQL 入库 |
| `income` | `sum(case when name_total_price >= 0 then name_total_price else 0 end)` 后逐层求和 | 收入金额 | 已从 SQL 入库 |
| `refund` | `sum(case when name_total_price < 0 then abs(name_total_price) else 0 end)` 后逐层求和 | 全部退款金额 | 已从 SQL 入库 |
| `promit` | `income - refund`，后逐层求和 | 净收，不剔除行课阈值退款 | 已从 SQL 入库 |
| `refund_4` | 按行课阈值计入的退款金额 | 剔除行课阈值退款 | 已从 SQL 入库 |
| `class_refund_4` | `sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then 0 else refund_4 end)` 后逐层求和 | 班课行课阈值退款；用于替代前端旧公式 `sum(refund)-sum(Y_refund_4)` | 已从 SQL 入库 |
| `promit_4` | `income - refund_4`，后逐层求和 | 剔除行课阈值退款后的净收 | 已从 SQL 入库 |

## 5. H/非 H 折算指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `H_promit` | `sum(case when course_first_level_department_name = 'H业务线' then promit else 0 end)` | H 业务线净收，不剔除退 4 | 已从 SQL 入库 |
| `n_H_promit` | `sum(case when course_first_level_department_name = 'H业务线' then 0 else promit end)` | 非 H 原始净收，不剔除退 4；前端折算净收款再按 0.5 计算 | 已从 SQL 入库 |
| `H_promit_4` | `sum(case when course_first_level_department_name = 'H业务线' then promit_4 else 0 end)` | H 业务线净收，剔除退 4 | 已从 SQL 入库 |
| `n_H_promit_4` | `sum(case when course_first_level_department_name = 'H业务线' then 0 else promit_4 end)` | 非 H 原始净收，剔除退 4；前端折算净收款再按 0.5 计算 | 已从 SQL 入库 |

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
| `goal` | `cast(qg.goal as decimal)` | 团队期次目标 | 已从 SQL 入库，来源待确认 |
| `emye_c` | `cast(qg.emye_c as decimal)` | 目标层级/展示控制字段 | 待人工确认 |
| `xiaozu` | `case when emye_c != '1' then xiaozu1 else '-' end` | 小组展示字段 | 已从 SQL 入库 |

## 8. 待确认事项

- 期次目标表 `temp_table.dingxi01_qing_team_g_qi.goal` 的单位需确认是否与 `promit` 同单位。
- `temp_table.dingxi01_qing_team_g_qi.xiaozu` 是否存主管邮箱，而不是小组名称。
- 期次版是否仍需要 `temp_table.dingxi01_qing_qi_moth` join 待确认。
- 退款阈值、H/非 H 折算、调课调班去重与月度版一致，所有待确认事项同样适用。
- 2026-06-22 后，`income`、`refund`、`refund_4` 和科目数会先排除主交易层命中的内部调课调班调入/调出流水；识别以 `dim_finance_order_change_df` 订单号映射为主，覆盖 `biz_type in (2,7)`。
- 2026-07-03 后，若 `dim_finance_order_change_df` 漏掉链路，但 service 订单明细同订单已有 `transfer_in_amount/transfer_out_amount`，也作为 `trade_type='调课调班'` 的内部变更补充识别；该规则不扩大到正常订单。
- 业务已确认 `H业务线` 按 100% 计入、所有 `非H业务线` 统一按 50% 折算；SQL 输出保留非 H 原始净收，前端公式再乘 0.5。
- 2026-06-28 起，任职窗口优先按 `order_attr.original_paid_time` 判定，并允许 `team_hist` 期次兜底；团队架构必须按 `qtg.qici = wa.qici` 回连，不能再固定取 `max(qici)`。

## 9. 2026-08-05 当前金额口径

团队期看板当前公式为：

```text
营收金额 = sum(income_all)
退费金额 = sum(refund_all)
净金额/净收款 = sum(income_all) - sum(refund_all)
折算净收款-退4 = sum(n_H_promit_4) * 0.5 + sum(H_promit_4)
```

`income_all/refund_all` 不剔除调课调班；`income/refund` 仍是内部调课识别后的 legacy/rule 金额，供 `promit`、退款人数和退 4 规则链使用。`refund_4`、`class_refund_4` 不能替代当前“全部退费金额”。service 是金额主事实，finance 只补 service 缺失的课程转移链路并参与规则字段；finance 独立明细保留后按真实输出粒度聚合，不能用不完整投影键判定重复。

个人与团队五期模板核对证据见 `knowledge/sql_patterns/qingcheng_template_dashboard_amount_reconciliation_20260805.md`。

## 10. 2026-08-07 调课调班明细粒度与 finance 归因修复

- `order_attr` 只保留原始支付时间，transfer 标记改由 `service_base0` 当前明细行直接传递到 `t4`，不再按订单级 `max` 回灌。
- finance raw 层删除不完整复合键的 `row_number()=1`，保留独立明细并按真实输出粒度聚合；`service_order_employee` 按 `order_number + employee_email_name` 抑制 service 已覆盖链路的重复补入。
- 期次基线/候选均为 330 行且键集合一致，移除旧 finance 误补 `4,573.3206` 元；`income_all/refund_all` 不变。生产 Preview `1534870341`、run `163252065` 为 `SUCCESS`。

## 11. 2026-08-07 service 真实退款补回与退款侧调课调班修复

团队完成度【期】与个人转化统一采用收入侧/退款侧分离的调课调班判定：`income/p_sub` 只剔除当前 service 明细行有 transfer 金额的内部流水；`refund/r_sub/refund_4` 不因订单命中 `order_change` 而整体清零，先按 finance 退款事件与 transfer pool 分配内部部分，再使用 service 退款余额。`order_change` 只作 service 缺失、零金额异常和退款内部分配的链路依据。

## 12. 2026-08-07 退款事件金额级分配

当前期次版与个人版共用 `finance_refund_event_allocated`：finance 负退款明细先按真实退款事件粒度聚合，再以 `order_change` transfer pool 分配内部退款金额。精确匹配时按事件全额分配；不精确时按事件金额比例分配并封顶。service 的 `refund_all` 保持原始全部退款，`refund/refund_4` 只使用 `greatest(service refund - internal allocation, 0)` 的余额，防止同一订单的真实退款被内部调课链路整单清零。`ord/re_ke` 的班课 4 节、点睛 2 节和 H 一对一规则不变。

20260803期个人基表与团队期基表的四名异常顾问金额一致；回归 query `1535375732` 返回王东亚01 `H_income_4=64,000`、`H_refund_4=6,772.61`、`H_promit_4=57,227.39`，张昊62 `15,000 / 2,210 / 12,790`，付金艳 `9,700 / 0 / 9,700`，张地43 `19,800 / 0 / 19,800`。

班课开课 4 节、点睛班开课 2 节、H 一对一全额退款规则仍由 `re_ke/ord` 的 `re_lc` 驱动，`refund_4/class_refund_4` 和 `promit_4` 口径未改变；看板营收/退费/净金额仍为 `sum(income_all)`、`sum(refund_all)`、`sum(income_all)-sum(refund_all)`。候选回归 query `1535084952` 与个人五名顾问结果一致。生产 Preview `1535090729`、run `163259517` 均为 `SUCCESS`。
