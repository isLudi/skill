# 青橙团队完成度【期】raw

## 1. 来源

`resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql`

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
| `finance_dw.app_finance_performance_extend_details_hf` | `dd_0` / `dd` | 财务业绩扩展明细，计算收入、退款和净收 |
| `finance_dw.dm_finance_order_refund_detail_df` | `ord` | 全退订单明细，提供完全退款时已完课课节数 |
| `finance_dw.dim_finance_order_change_df` | `order_change_raw` / `order_change` | 识别调课调班/课程转移主链路订单，覆盖订单号、父订单号、原始订单号和最新子订单号 |

## 6. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.dingxi01_qing_qi_moth` | 期次到月份映射表，保留在 `wa` 层 | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_team_jg` | 青橙最新团队架构表，按员工补充主管 | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_team_g_qi` | 青橙团队期次目标表，提供期次目标和组织层级 | 已从 SQL 入库，来源/刷新方式待人工确认 |

## 7. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `org_t` | 员工在青橙项目部路径下的任职时间窗口 | `email_prefix`, `name`, `begin_time`, `end_time` |
| `dd_0` | 财务业绩原始层，生成标准科目、期次和基础订单字段 | `order_number`, `user_id1`, `trade_status`, `trade_type`, `trade_time`, `price`, `subject`, `qici` |
| `dd` | 只保留员工原始成交时间落在青橙任职期间的交易；退款晚发生但原单早于入组时间的记录要排除 | `coalesce(paid_time, trade_time) >= begin_time and (end_time is null or coalesce(paid_time, trade_time) <= end_time)` |
| `gmv_t` | 调课调班订单，按订单/课程/用户/期次/科目/课程部门粒度汇总，避免同一顾问同一用户多笔调课调班被揉成一条 | `order_number`, `qici`, `subject`, `course_first_level_department_name`, `name_total_price` |
| `gmv_z` | 正常订单，按订单和课程维度汇总金额 | `name_total_price` |
| `rd` | 合并正常订单和调课调班结果 | `union all` |
| `ord` | 全退订单课节明细 | `full_refund_chain_finish_lesson_count`, `qici_re` |
| `order_change_raw` / `order_change_order_map` / `order_change` | 调课调班/课程转移主链路订单映射，按订单号聚合后供主交易层和退款层复用 | `order_number`, `has_order_change`, `transfer_in_amount_yuan`, `transfer_out_amount_yuan`, `refund_type` |
| `re_ke` | 合并全退课节和调课调班类型，按 `qici_re + order_number` 聚合避免回连放大 | `refund_type`, `full_refund_chain_finish_lesson_count` |
| `t4` | 将退款课节数回连到财务交易 | `re_lc` |
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
| `dd_0 a` | `org_t ot` | `ot.name = a.name and coalesce(a.paid_time, a.trade_time) between ot.begin_time and ot.end_time` | 只保留原始成交时间落在青橙期间的营收/退款，避免历史订单在转岗后退款被误计入青橙 |
| `ord` | `order_change` | `ord.order_number = order_change.order_number` | 补充调课调班/课程转移类型 |
| `rd` | `order_change` | `rd.order_number = order_change.order_number` | 主交易层识别内部调课调班调入/调出流水，避免误入外部收入/退款桶 |
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
