# 青橙个人转化指标

## 1. 来源

`resources/raw_sql/data_center_qingcheng_2769.sql`

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
| `income_all` | `sum(case when source_type = 'service' then income_amount_yuan else 0 end)` | service 主事实的全部收入；包含 service 明细中的内部调课调班流水，不由 finance 重复行放大 | 已从 2026-08-05 canonical SQL 入库 |
| `refund_all` | `sum(case when source_type = 'service' then refund_amount_yuan else 0 end)` | service 主事实的全部退款；包含 service 明细中的内部调课调班流水，不由 finance 重复行放大 | 已从 2026-08-05 canonical SQL 入库 |
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

2026-08-05 起，看板金额字段与折算字段分开维护。当前个人看板的金额公式为：

```text
班课营收 = sum(income_all)
班课退费 = sum(refund_all)
班课净收 = sum(income_all) - sum(refund_all)
```

这些字段不剔除调课调班，也不应用退 4/点睛退 2；`income`、`refund`、`refund_4`、`class_refund_4` 和 `promit_4` 继续保留给内部调课识别、退款规则、折算产出及其他历史指标。

看板自定义字段 `折算后产出` 当前公式为：

```text
ifnull(sum(${n_H_promit_4}) * 0.5 + (sum(${H_promit_4}) - sum(${Y_promit_4})), 0)
```

该公式本身只做前端聚合，准确性依赖源 SQL 中以下字段已经正确入桶：

- `H_promit_4`：H 业务线剔除行课阈值退款后的净收。
- `n_H_promit_4`：非 H 业务线剔除行课阈值退款后的原始净收，前端再乘 0.5。
- `Y_promit_4`：H 一对一剔除行课阈值退款后的净收，前端从 H 中扣除。
- `refund_4`：按班课 4 节、点睛班 2 节、一对一全额规则计入的退款。
- `class_refund_4`：班课行课阈值退款，供退 4/点睛退 2 规则类指标使用；当前“班课退费”展示使用 `sum(refund_all)`，不再使用 `sum(class_refund_4)`。

若支付订单流水与看板不一致，优先排查 `course_first_level_department_name` / `course_second_level_department_name` 空值兜底、`gmv_t` 调课调班聚合粒度，以及 service 明细 `transfer_in_amount/transfer_out_amount` 是否补充命中内部调课调班。详细风险、诊断 SQL 和已验证样例见 `knowledge/sql_patterns/qingcheng_personal_completion_discounted_output_risks.md`。

2026-06-22 后补充：`income`、`refund`、`refund_4` 和科目数会先排除主交易层命中的内部调课调班调入/调出流水。该识别以 `dim_finance_order_change_df` 订单号映射为主，覆盖 `biz_type in (2,7)`，用于避免把内部 `调出退款` 当外部退费计入；`income_all/refund_all` 则保留 service 明细的全部收入/退款，用于当前看板金额展示。

2026-07-03 后补充：当 `dim_finance_order_change_df` 漏掉链路，但 service 订单明细同订单已有 `transfer_in_amount/transfer_out_amount` 时，也会作为 `trade_type='调课调班'` 的内部变更补充识别。该规则影响收入侧 `income/p_sub`；退款侧由独立的 `is_internal_refund_order_change` 控制，不能因订单命中变更链路而把 service 真实退款整体清零。

2026-08-05 后补充：service 是正常收入/退款金额主事实，finance 只用于课程转移缺失补充、调课调班识别和 `ord/re_ke` 退 4/点睛退 2 规则。finance 独立明细不得按不完整业务键直接判重；应保留明细并按真实输出粒度聚合，再以 service 同订单同顾问存在性校验防止重复补金额；不得用 finance 直接替代 `income_all/refund_all`。

模板核对结果见 `knowledge/sql_patterns/qingcheng_template_dashboard_amount_reconciliation_20260805.md`：五期个人员工键集合一致，差异由模板保留而看板排除的 `试听` 流水解释，不是 finance 重复行或渠道 join 放大。

2026-06-28 后补充：

- 任职窗口优先按 `order_attr.original_paid_time` 判定，避免历史订单退款串入青橙。
- 若组织链 `begin_time` 滞后，允许 `team_hist` 期次命中兜底保留当前有效订单。
- 命中订单变更链路但本身是正常成交的订单不得排除；`is_internal_order_change` 只用于剔除 `trade_type='调课调班'` 的内部变更流水本身。

## 11. 2026-08-07 调课调班明细粒度修复

本次三份完成度 SQL 统一采用以下规则：

- `order_attr` 只按订单和顾问聚合 `original_paid_time`，不再 `max(transfer_in_amount/transfer_out_amount)`。
- `service_base0` 从当前 service 明细行直接识别 transfer，并将行级 transfer 金额传到 `t4`；因此同订单的正常支付行不会被另一条调课调班行的标记误伤。
- finance 订单变更只在 service 缺失时受限补充：当前来源必须是 service、命中变更金额且当前行是实际退款（`trade_status like '%退%'`、`refund_amount_yuan > 0`）。finance 课程转移明细保留独立行，按真实输出粒度聚合；同订单同顾问已有 service 链路时不再补金额。
- `income_all/refund_all` 仍只汇总 service 主事实；`income/refund`、`refund_4/class_refund_4`、`H_promit_4/n_H_promit_4/Y_promit_4` 保持原有内部调课、退 4/点睛退 2 和 H/非 H 业务含义。

20260803期 `张地43` 的行级回归查询 `1534542940`：修复后 `income_all=19,800`、`refund_all=0`、`income=19,800`、`H_promit_4=19,800`、个人折算后产出 `19,800`；旧版因订单级 transfer 回灌曾只剩 `7,800`。生产替换及三份数据中心 `SUCCESS` 证据见 `knowledge/update_log/changelog.md`。

## 12. 2026-08-07 service 真实退款补回与退款侧调课调班修复

本次个人转化 SQL 将调课调班识别拆成收入侧和退款侧两个 flag：

- `income_all/refund_all` 仍直接汇总 service 的 `income_amount/refund_amount`，看板上的班课营收、班课退费和班课净收业务含义不变；
- `income/p_sub` 使用 `is_internal_order_change`，只排除当前明细行确有 `transfer_in/transfer_out` 的内部调课调班流水；
- `refund/r_sub/refund_4` 使用 `is_internal_refund_order_change`。service 当前行 `refund_amount > 0` 时不再因 `order_change` 命中而按订单整体置零；先按 finance 退款事件与 transfer pool 分配内部部分，再以 service 退款余额进入退款字段；
- `refund_4/class_refund_4` 的业务规则不变：班课 `re_lc < 4`、点睛班 `re_lc < 2`、H 一对一退款全额计入；`promit_4 = income - refund_4`，H/非 H 折算仍由原 `H_promit_4/n_H_promit_4/Y_promit_4` 规则计算。

候选回归 query `1535081501`（20260803期、五名异常顾问）结果：刘孟佳 `refund=4,550`、`class_refund_4=2,525.48`；王东亚01 `refund=13,505.26`、`class_refund_4=9,207.41`；樊盼盼 `refund=3,637.74`、`class_refund_4=2,625.48`；白君辉 `refund=2,481.81`、`class_refund_4=2,481.81`；宋佳鑫04 `refund=6,686.06`、`class_refund_4=5,198.78`。这证明 service 真实退款已补回，同时 4 节/点睛 2 节扣减仍生效。生产 Preview `1535088666`、run `163259511` 均为 `SUCCESS`。

## 13. 2026-08-07 finance 退款事件金额级分配

当前生产版在保留 service 主金额的前提下，进一步区分调课调班订单中的内部退款和真实退款：

- `income_all` / `refund_all` 仍直接汇总 service 的 `income_amount_yuan` / `refund_amount_yuan`，看板班课营收、班课退费、班课净收业务含义不变。
- `finance_refund_event_allocated` 先在 finance 真实退款事件粒度聚合负价明细；不使用不完整复合键 `row_number()=1`，也不把 finance 直接加到 `income_all/refund_all`。
- 使用 `order_change` 的 transfer pool 计算 `internal_refund_amount_yuan`：精确匹配时按事件全额分配，不精确时按订单退款事件金额比例分配并封顶；`t4` 用 service 退款减去该内部分配额的非负余额计算 `refund/refund_4`。
- `ord/re_ke` 的班课 4 节、点睛班 2 节、H 一对一全额退款规则保持不变；`H_promit_4`、`n_H_promit_4`、`Y_promit_4` 仍按原业务分类，非 H 由前端乘 0.5。

20260803期定向结果：王东亚01 `H_income_4=64,000`、`refund_all=13,505.26`、`H_refund_4=6,772.61`、`H_promit_4=57,227.39`；张昊62 `15,000 / 2,210 / 12,790`；付金艳 `9,700 / 0 / 9,700`；张地43 `19,800 / 0 / 19,800`。个人、团队期、团队月回归 query 分别为 `1535361544`、`1535375732`、`1535381004`。

三份生产替换均完成保存后 SQL 哈希回读、预览和新抽数 `SUCCESS`：个人 model `2769`（Preview `1535390346`，run `163273845`），团队期 model `2680`（Preview `1535392792`，run `163273846`），团队月 model `2677`（Preview `1535395486`，run `163273848`）。
