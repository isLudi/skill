# 青橙团队完成度【月】raw

## 1. 来源

`resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql`

入库时间：2026-05-22

## 2. 查询目标

沉淀青橙团队月度完成度 SQL。该 SQL 使用财务业绩扩展明细计算青橙员工在部门期间产生的收入和退款，结合全退订单行课节数计算“剔除行课退费阈值”的净收，再按人员聚合到主管/月度层，并与青橙团队月目标表合并，输出学部、小组、大组、目标、净收、退款人数和破单人数等月度完成度指标。

## 3. 最终输出粒度

| 维度 | 字段 |
|---|---|
| 月份 | `month` |
| 学部 | `xuebu` |
| 小组 | `xiaozu`，由 `emye_c` 控制是否置为 `'-'` |
| 大组 | `dazu` |
| 目标 | `goal` |
| 目标层级标记 | `emye_c` |

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `dw.dim_employee_chain` | `org_t` | 确认员工在青橙项目部路径下的任职起止时间 |
| `finance_dw.app_finance_performance_extend_details_hf` | `dd_0` / `dd` | 财务业绩扩展明细，计算收入、退款和净收 |
| `finance_dw.dm_finance_order_refund_detail_df` | `ord` | 全退订单明细，提供完全退款时已完课课节数 |
| `finance_dw.dim_finance_order_change_df` | `order_change_raw` / `order_change` | 识别调课调班/课程转移主链路订单，覆盖订单号、父订单号、原始订单号和最新子订单号 |

## 5. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.dingxi01_qing_qi_moth` | 期次到月份映射表，按 `qici` 补充 `moth` | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_team_jg` | 青橙最新团队架构表，按员工补充主管 | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_team_goal` | 青橙团队月目标表，提供月度目标和组织层级 | 已从 SQL 入库，来源/刷新方式待人工确认 |

## 6. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `org_t` | 员工在青橙项目部路径下的任职时间窗口 | `email_prefix`, `name`, `begin_time`, `end_time` |
| `dd_0` | 财务业绩原始层，生成标准科目、期次和基础订单字段 | `order_number`, `user_id1`, `trade_status`, `trade_type`, `trade_time`, `price`, `subject`, `qici` |
| `dd` | 只保留员工在青橙任职期间产生的交易 | `trade_time >= begin_time and (end_time is null or trade_time <= end_time)` |
| `gmv_t` | 调课调班订单，按订单/课程/用户/期次/科目/课程部门粒度汇总，避免同一顾问同一用户多笔调课调班被揉成一条 | `order_number`, `qici`, `subject`, `course_first_level_department_name`, `name_total_price` |
| `gmv_z` | 正常订单，按订单和课程维度汇总金额 | `name_total_price` |
| `rd` | 合并正常订单和调课调班结果 | `union all` |
| `ord` | 全退订单课节明细 | `full_refund_chain_finish_lesson_count`, `qici_re` |
| `order_change_raw` / `order_change_order_map` / `order_change` | 调课调班/课程转移主链路订单映射，按订单号聚合后供主交易层和退款层复用 | `order_number`, `has_order_change`, `transfer_in_amount_yuan`, `transfer_out_amount_yuan`, `refund_type` |
| `re_ke` | 合并全退课节和调课调班类型，按 `qici_re + order_number` 聚合避免回连放大 | `refund_type`, `full_refund_chain_finish_lesson_count` |
| `t4` | 将退款课节数回连到财务交易 | `re_lc` |
| `rd_0` | 用户/交易状态层收入、退款、剔除退 4 退款和科目数 | `income`, `refund_4`, `refund`, `sub` |
| `wa` | 补充月份和净收 | `moth`, `promit_4`, `promit` |
| `renchan` | 人维度月度业绩 | `H_promit`, `n_H_promit`, `promit`, `H_promit_4`, `n_H_promit_4`, `promit_4` |
| 最终查询 | 团队目标和人维度业绩合并 | `goal`, `emye_c`, `podan`, `podan_4` |

## 7. 青橙范围限定

| 位置 | 范围字段 | 取值 |
|---|---|---|
| `org_t` 员工链路 | `path_name` | `like '高途-H业务线-青橙项目部%'` |
| `dd_0` 财务业绩 | `employee_first_level_department_name` | `'H业务线'` |
| `dd_0` 财务业绩 | `employee_second_level_department_name` | `'青橙项目部'` |
| `ord` 全退订单 | `course_first_level_department_name` | `'H业务线'` |
| `ord` 全退订单 | `course_second_level_department_name` | `('精品班学部','菁英班学部','一对一学部')` |

## 8. 分区和时间条件

| 表/CTE | dt 条件 | hour 条件 | 其他时间条件 |
|---|---|---|---|
| `dw.dim_employee_chain` | `format_datetime(now() - interval '24' hour, 'YYYYMMdd')` | 无 | 组织路径以青橙开头 |
| `finance_dw.app_finance_performance_extend_details_hf` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | `format_datetime(now() - interval '2' hour, 'HH')` | `qici > '20260424期'` |
| `finance_dw.dm_finance_order_refund_detail_df` | `format_datetime(now() - interval '24' hour, 'YYYYMMdd')` | 无 | 只取全退且退款金额非 0 |
| `finance_dw.dim_finance_order_change_df` | `format_datetime(now() - interval '24' hour, 'YYYYMMdd')` | 无 | `latest_child_order_status in (2,6,7)` and `biz_type in (2,7)` |

## 9. join 关系

| 左侧 | 右侧 | join key | 用途 |
|---|---|---|---|
| `dd_0 a` | `org_t ot` | `ot.name = a.name and a.trade_time >= ot.begin_time and (ot.end_time is null or a.trade_time <= ot.end_time)` | 只保留员工在青橙期间产生的营收/退款 |
| `ord` | `order_change` | `ord.order_number = order_change.order_number` | 补充调课调班/课程转移类型 |
| `rd` | `order_change` | `rd.order_number = order_change.order_number` | 主交易层识别内部调课调班调入/调出流水，避免误入外部收入/退款桶 |
| `rd` | `re_ke` | `re_ke.qici_re = rd.qici and re_ke.order_number = rd.order_number` | 给交易补充全退时行课节数 |
| `rd_0` | `temp_table.dingxi01_qing_qi_moth qm` | `qm.qici = rd_0.qici` | 期次映射到月份 |
| `wa` | `temp_table.dingxi01_qing_team_jg qtg` | `qtg.employee_email_name = wa.name`，取最新 `qici` | 补充员工主管 |
| `temp_table.dingxi01_qing_team_goal qg` | `renchan rc` | `qg.xiaozu = rc.leader_employee_email_name and qg.month = rc.moth` | 月目标与实际业绩合并 |

## 10. 退款课节阈值

`refund_4` 是剔除行课阈值后的退款金额：

| 场景 | 计入 `refund_4` 的条件 |
|---|---|
| 一对一学部且 H 业务线 | `name_total_price < 0` 的全部退款金额 |
| 班课，班级名包含 `点睛` | `name_total_price < 0 and re_lc < 2` |
| 班课，非点睛或班级名为空 | `name_total_price < 0 and re_lc < 4` |

其中 `re_lc = coalesce(full_refund_chain_finish_lesson_count, 0)`。

## 11. 团队完成度指标

指标集合沉淀到 `knowledge/metrics/qingcheng_team_completion_month_metrics.md`。

| 指标 | 口径简述 |
|---|---|
| `H_promit` | H 业务线净收，不剔除退 4 |
| `n_H_promit` | 非 H 净收按 0.5 折算，不剔除退 4 |
| `promit` | 总净收，不剔除退 4 |
| `H_promit_4` | H 业务线净收，剔除行课阈值退款 |
| `n_H_promit_4` | 非 H 净收按 0.5 折算，剔除行课阈值退款 |
| `promit_4` | 总净收，剔除行课阈值退款 |
| `goal` | 团队月目标 |
| `podan` / `podan_4` | 净收/剔除退 4 净收大于 0 的伙伴数 |

## 12. 已知风险和待确认事项

- 期次推导已改为 `interval` 写法；后续生成新 SQL 不得回退为 Presto 三参数 `date_add('day', n, expr)`。
- `org_t` 使用 `path_name like '高途-H业务线-青橙项目部%'`，比年季月营收 SQL 的前三层精确匹配更宽。
- 任职窗口必须使用 `trade_time >= begin_time` 和 `trade_time <= end_time`，与期次计算和退款发生时间保持一致；不要改回 `paid_time >= begin_time`，否则会纳入少量支付时间与交易/退款发生时间不一致的记录。
- `org_t` 和财务表按 `name` join，若重名可能误匹配；是否应改用 `email_prefix` 待确认。
- `gmv_t` 调课调班已改为订单/课程粒度；后续生成新 SQL 不得回退为 `name + user_id1` 粗粒度去重。
- 与订单明细核对时，不要只使用 service 订单明细表原始 `income_amount/refund_amount`，该表部分调课调班链路金额可能缺失或为 0；若做明细侧核对，需要按 `transfer_in_amount/transfer_out_amount` 补充，并用 finance 明细补齐 service 缺失事件。
- `dim_finance_order_change_df` 必须接到 `rd/t4` 主交易层，并覆盖 `biz_type in (2,7)`；不要只接到退款明细层，否则 `调出退款` 可能在 `re_lc=0` 时误入 4 节内退款。
- `temp_table.dingxi01_qing_qi_moth` 字段名为 `moth`，疑似 month 拼写，保留历史 SQL 口径。
- `qg.emye_c != '1'` 时才展示小组，否则小组置为 `'-'`；`emye_c` 业务含义待确认。
- 最终查询中 `group by` 包含 `leader_employee_email_name`，但该字段不在最终 select 明确输出，仅影响聚合粒度；待确认是否必要。
