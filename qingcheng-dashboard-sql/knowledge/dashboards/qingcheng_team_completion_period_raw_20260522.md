# 青橙团队完成度【期】raw

## 1. 来源

`resources/raw_sql/data_center_qingcheng_2680.sql`

入库时间：2026-05-22

## 2. 查询目标

沉淀青橙团队期次完成度 SQL。该 SQL 与团队完成度【月】同源，使用财务业绩扩展明细、全退订单行课节数和青橙最新团队架构计算员工期次业绩，再与青橙团队期次目标表合并，输出期次、学部、小组、大组维度的目标、净收、剔除行课阈值净收、退款人数和破单人数。

## 3. 最终输出粒度

| 维度 | 字段 |
|---|---|
| 期次 | `qici` |
| 学部 | `xuebu` |
| 小组 | `xiaozu`，由 `emye_c` 控制是否置为 `'-'` |
| 大组 | `dazu` |
| 目标 | `goal` |
| 目标层级标记 | `emye_c` |

## 4. 与团队完成度【月】的差异

| 项目 | 团队完成度【月】 | 团队完成度【期】 |
|---|---|---|
| 目标表 | `temp_table.dingxi01_qing_team_goal` | `temp_table.dingxi01_qing_team_g_qi` |
| 目标 join | `qg.month = rc.moth` | `qg.qici = rc.qici` |
| 输出时间粒度 | `month` | `qici` |
| 期次到月份映射 | 参与目标 join | 仍在 `wa` 中保留 `moth`，但最终目标 join 不依赖月份 |

## 5. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `dw.dim_employee_chain` | `org_t` | 确认员工在青橙项目部路径下的任职起止时间 |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `order_attr` / `service_base0` | `order_attr` 只提供订单原始支付时间 `original_paid_time`；`transfer_in_amount/transfer_out_amount` 必须保留在 `service_base0` 当前明细行粒度，作为内部调课调班补充识别 |
| `finance_dw.app_finance_performance_extend_details_hf` | `course_transfer_finance_raw` / `course_transfer_finance` | 仅补 service 缺失的课程转移链路，并为内部调课、退 4/点睛退 2 规则提供关联字段；保留独立明细并按真实输出粒度聚合，不使用不完整投影键判定重复 |
| `finance_dw.dm_finance_order_refund_detail_df` | `ord` | 全退订单明细，提供完全退款时已完课课节数 |
| `finance_dw.dim_finance_order_change_df` | `order_change_raw` / `order_change` | 识别调课调班/课程转移主链路订单，覆盖订单号、父订单号、原始订单号和最新子订单号 |

## 6. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.dingxi01_qing_qi_moth` | 期次到月份映射表，保留在 `wa` 层 | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_team_jg` | 青橙最新团队架构表，按员工补充主管 | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_team_g_qi` | 青橙团队期次目标表，提供期次目标和组织层级 | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_team_jg`（`team_hist`） | 组织链时间滞后时，按期次兜底保留已在青橙架构中的顾问订单 | 仅用于完成度任职窗口兜底，不替代正式组织链 |

## 7. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `org_t` | 员工在青橙项目部路径下的任职时间窗口 | `email_prefix`, `name`, `begin_time`, `end_time` |
| `order_attr` | 从订单明细侧按订单和顾问聚合原始支付时间；不聚合 transfer 标记 | `original_order_pay_success_timestamp`, `pay_success_timestamp`, `trade_timestamp`, `original_paid_time` |
| `team_hist` | 组织链时间滞后时，按期次保留已在青橙架构中的顾问 | `qici`, `employee_email_name` |
| `service_base0` | service 主事实，限定青橙业绩范围、课程范围、交易起始日期，并排除试听订单 | `order_number`, `performance_employee_email_name`, `income_amount_yuan`, `refund_amount_yuan`, `transfer_in_amount_yuan`, `transfer_out_amount_yuan` |
| `service_scope` | 按组织链/期次历史窗口保留员工有效 service 流水 | `qici`, `name`, `original_paid_time`, `income_amount_yuan`, `refund_amount_yuan` |
| `course_transfer_finance_raw` / `course_transfer_finance` | finance 仅补 service 缺失的课程转移正向金额；保留每条独立明细，按订单、用户、顾问、交易时间、班级、科目及课程部门等真实输出粒度聚合 | `order_number`, `target_user_number`, `employee_email_name`, `subject`, `income_amount_yuan` |
| `rd` | 合并 service 主事实与 service 缺失的课程转移补充，并保留 `source_type` 区分金额来源 | `source_type`, `income_amount_yuan`, `refund_amount_yuan`, `qici` |
| `ord` | 全退订单课节明细 | `full_refund_chain_finish_lesson_count`, `qici_re` |
| `order_change_raw` / `order_change_order_map` / `order_change` | 调课调班/课程转移主链路订单映射，按订单号聚合后供主交易层和退款层复用；仅作为 service 缺失时的受限补充信号 | `order_number`, `has_order_change`, `transfer_in_amount_yuan`, `transfer_out_amount_yuan`, `refund_type` |
| `re_ke` | 合并全退课节和调课调班类型，按 `qici_re + order_number` 聚合避免回连放大 | `refund_type`, `full_refund_chain_finish_lesson_count` |
| `t4` | 将退款课节数、财务订单变更链路和当前 service 行转入/转出标记回连到交易；只把调课调班流水本身标记为内部变更 | `re_lc`, `service_transfer_in_amount_yuan`, `service_transfer_out_amount_yuan`, `is_internal_order_change` |
| `rd_0` | 用户/交易状态层收入、退款、剔除退 4 退款和科目数 | `income`, `refund_4`, `refund`, `sub` |
| `wa` | 补充月份和净收 | `moth`, `promit_4`, `promit` |
| `renchan` | 人维度期次业绩 | `H_promit`, `n_H_promit`, `promit`, `H_promit_4`, `n_H_promit_4`, `promit_4` |
| 最终查询 | 团队期次目标和人维度业绩合并 | `goal`, `emye_c`, `podan`, `podan_4` |

## 8. 青橙范围限定

| 位置 | 范围字段 | 取值 |
|---|---|---|
| `org_t` 员工链路 | `path_name` | `like '高途-H业务线-青橙项目部%'` |
| `dd_0` 财务业绩 | `employee_first_level_department_name` | `'H业务线'` |
| `dd_0` 财务业绩 | `employee_second_level_department_name` | `'青橙项目部'` |
| `ord` 全退订单 | `course_first_level_department_name` | `'H业务线'` |
| `ord` 全退订单 | `course_second_level_department_name` | `('精品班学部','菁英班学部','一对一学部')` |

## 9. join 关系

| 左侧 | 右侧 | join key | 用途 |
|---|---|---|---|
| `dd_0 a` | `order_attr oa` + `org_t ot` + `team_hist th` | `oa.order_number = a.order_number and oa.performance_employee_email_name = a.name`，再用 `coalesce(oa.original_paid_time, a.paid_time, a.trade_time)` 匹配任职窗口；若 `team_hist.qici` 命中则兜底保留 | 只保留原始成交时间落在青橙期间的营收/退款，同时避免组织链起始时间滞后误删当前有效订单 |
| `ord` | `order_change` | `ord.order_number = order_change.order_number` | 补充调课调班/课程转移类型 |
| `rd` | `order_change` + 当前 service 行 transfer 标记 | `rd.order_number = order_change.order_number`；service 标记来自 `service_base0` 当前行并随 `service_scope -> rd -> t4` 传递 | 主交易层按明细行识别内部调课调班；`order_change` 规则字段仅在 service 缺失且当前行确为实际退款时补充，避免同订单正常支付行被整体剔除；finance 课程转移金额另按真实明细粒度补充 |
| `rd` | `re_ke` | `re_ke.qici_re = rd.qici and re_ke.order_number = rd.order_number` | 给交易补充全退时行课节数 |
| `rd_0` | `temp_table.dingxi01_qing_qi_moth qm` | `qm.qici = rd_0.qici` | 保留期次到月份映射 |
| `wa` | `temp_table.dingxi01_qing_team_jg qtg` | `qtg.employee_email_name = wa.name`，取最新 `qici` | 补充员工主管 |
| `temp_table.dingxi01_qing_team_g_qi qg` | `renchan rc` | `qg.xiaozu = rc.leader_employee_email_name and qg.qici = rc.qici` | 期次目标与实际业绩合并 |

## 10. 指标口径

指标集合沉淀到 `knowledge/metrics/qingcheng_team_completion_period_metrics.md`。

核心指标与团队完成度【月】一致：

- `H_promit`、`n_H_promit`、`promit`
- `H_promit_4`、`n_H_promit_4`、`promit_4`
- `refund`、`refund_4`
- `re_payer`、`re_payer_4`
- `podan`、`podan_4`
- `goal`、`emye_c`

## 11. 已知风险和待确认事项

- 期次推导已改为 `interval` 写法；后续生成新 SQL 不得回退为 Presto 三参数 `date_add('day', n, expr)`。
- 任职窗口必须使用 `coalesce(paid_time, trade_time)` 作为组织归属锚点，优先按原始支付时间归属，兜底退回 `trade_time`；不要只按退款/交易发生时间过滤，否则会把历史订单在转岗后发生的退款误计入青橙。
- 2026-06-27 已验证样例：顾问 `陈贺新` 于 2025-05-26 进入青橙，`user_id=1606647` 的原单支付在 2023-10、退款发生在 2026-06-25。旧口径按 `trade_time` 会误入团队完成度，现已修正。
- 期次版仍保留 `temp_table.dingxi01_qing_qi_moth` 的 `moth` 字段，但最终 join 目标表不使用月份，是否保留该 join 待确认。
- `temp_table.dingxi01_qing_team_g_qi.xiaozu` 与 `renchan.leader_employee_email_name` join，需确认 `xiaozu` 字段是否存主管邮箱。
- `qg.emye_c != '1'` 时才展示小组，否则小组置为 `'-'`；`emye_c` 业务含义待确认。
- 其他订单处理、调课调班粒度、退费行课阈值风险同团队完成度【月】。`dim_finance_order_change_df` 必须接到 `rd/t4` 主交易层，并覆盖 `biz_type in (2,7)`。
- 内部调课调班识别不能只依赖 `dim_finance_order_change_df`；若 service 明细同订单存在 `transfer_in_amount/transfer_out_amount`，也应作为 `trade_type='调课调班'` 流水的补充剔除信号。
- `temp_table.dingxi01_qing_team_jg` 必须按 `qtg.qici = wa.qici` 回连，不能固定取 `max(qici)`。
- 业务已确认 `H业务线` 按 100% 计入、所有 `非H业务线` 统一按 50% 折算；文档中不再保留“是否所有非 H 都 50% 待确认”。

## 12. 2026-06-28 最终修复补充

- 新增 `order_attr.original_paid_time`，优先按原始成交时间回连组织窗口。
- 增加 `team_hist` 期次兜底，避免组织链开始时间滞后导致当前有效订单被切掉。
- `gmv_z` 改为保留所有非调课调班交易，而不再限制 `trade_type='正常订单'`。
- `is_internal_order_change` 只剔除调课调班流水本身，不再把命中变更链路的正常订单整体剔除。
- 团队架构回连从“固定取最新期次”修正为 `qtg.qici = wa.qici`。

## 13. 2026-07-03 service transfer 补充识别修复

- 历史修复规则（2026-07-03 至 2026-08-06）：团队期次完成度曾同步个人完成度，在 `order_attr` 聚合 service `transfer_in_amount/transfer_out_amount` 并传递到 `t4`；该版本已由 2026-08-07 的明细行规则替代。
- 该规则只在 `trade_type='调课调班'` 时触发，不扩大到正常订单；当前全部营收/退费事实源改为 service 的 `income_amount/refund_amount`，finance 仅补 service 缺失的课程转移和规则字段。
- 验证样例：`李兵建` 小组 `20260703期` 修复后班课营收从截图中的 `18212` 降为 `16200`，折算后产出从 `14581` 降为 `12569`，正好扣除误入的 `2012.34`。

## 14. 2026-08-05 当前金额字段与模板核对

团队期看板当前使用：

```text
营收金额 = sum(income_all)
退费金额 = sum(refund_all)
净金额 = sum(income_all) - sum(refund_all)
折算净收款-退4 = sum(n_H_promit_4) * 0.5 + sum(H_promit_4)
```

`income_all/refund_all` 汇总 service 主事实，保留 service 内部调课调班流水；`income/refund` 和 `refund_4/class_refund_4` 继续服务于内部调课识别和退 4/点睛退 2 规则。五个期次的团队键集合完全一致，当前与渠道模板的少量差异由模板保留而看板排除的试听流水解释，不是 finance 重复行导致。证据见 `knowledge/sql_patterns/qingcheng_template_dashboard_amount_reconciliation_20260805.md`。

## 15. 2026-08-07 调课调班明细粒度与 finance 归因修复

- 团队期 SQL 与个人 SQL 同步修复：取消 `order_attr` 对 transfer 金额的订单级 `max`，改为 service 当前明细行识别并传递；finance raw 层删除基于不完整复合键的 `row_number()=1`，保留独立明细后按真实输出粒度聚合。
- 新增 `service_order_employee`，按 `order_number + employee_email_name` 判断 service 是否已经覆盖调课链路；不再用可能与 service 不一致的 `user_id` 做补充抑制。finance 仅在 service 缺失同订单同顾问链路时补入。
- 这样同一订单中的正常支付行不会因另一行存在 transfer 而从 `income`、`promit`、`H_promit_4` 和折算后产出中被误删；`income_all/refund_all` 仍保持 service 全量金额含义。
- 团队期基线/候选全量回归均为 330 行、键集合完全一致；7 个团队键修正，移除旧 finance 误补 `4,573.3206` 元。`income_all=26,961,943.26`、`refund_all=3,507,394.74` 不变，`income` 和 `promit` 分别为 `26,956,164.18`、`23,806,602.94`。
- 团队期 20260803期受影响金额为 `100.2816` 元；生产 Preview `1534870341`、新抽数 run `163252065`，状态 `SUCCESS`。
