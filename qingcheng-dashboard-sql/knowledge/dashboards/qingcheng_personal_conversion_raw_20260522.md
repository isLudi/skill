# 青橙个人转化 raw

## 1. 来源

`resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`

入库时间：2026-05-22

## 2. 查询目标

沉淀青橙个人转化 SQL。该 SQL 使用财务业绩扩展明细计算员工在青橙任职期间产生的收入、退款和净收，结合全退订单行课节数计算“剔除行课阈值退款”后的净收，再以青橙团队架构表为人员期次骨架输出个人维度的转化和产出指标。

该 SQL 与团队完成度【月/期】共用订单处理、调课调班去重、全退课节和 H/非 H 折算口径，但最终不 join 团队目标表，而是 join 个人目标表，输出个人的期次粒度和月度汇总粒度。

## 3. 最终输出粒度

| 维度 | 字段 |
|---|---|
| 粒度标记 | `data_level`，`qici` / `moth` |
| 期次 | `qici` |
| 月份 | `moth`，来自 `temp_table.dingxi01_qing_qi_moth` |
| 个人 | `name`，来自 `employee_email_name` |
| 主管 | `leader_employee_email_name` |
| 大组 | `dazu` |
| 经理 | `jingli` |
| 学部 | `xuebu` |

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `dw.dim_employee_chain` | `org_t` | 确认员工在青橙项目部路径下的任职起止时间 |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `order_attr` | 提供订单原始支付时间 `original_paid_time`，辅助完成度按原始成交窗口归属；同时提供 `transfer_in_amount/transfer_out_amount` 作为内部调课调班补充识别 |
| `finance_dw.app_finance_performance_extend_details_hf` | `dd_0` / `dd` | 财务业绩扩展明细，计算收入、退款和净收 |
| `finance_dw.dm_finance_order_refund_detail_df` | `ord` | 全退订单明细，提供完全退款时已完课课节数 |
| `finance_dw.dim_finance_order_change_df` | `order_change_raw` / `order_change` | 识别调课调班/课程转移主链路订单，覆盖订单号、父订单号、原始订单号和最新子订单号 |

## 5. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.dingxi01_qing_team_jg` | 青橙团队架构表，作为个人期次输出骨架 | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_qi_moth` | 期次到月份映射表，按 `qtg.qici` 补充 `moth` | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_goal` | 青橙个人目标表，提供 `qici_goal` 和 `moth_goal` | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_qing_team_jg`（`team_hist`） | 组织链生效时间滞后时，按期次兜底保留已在青橙架构中的人员订单 | 仅用于完成度任职窗口兜底，不替代正式组织链 |

## 6. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `org_t` | 员工在青橙项目部路径下的任职时间窗口 | `email_prefix`, `name`, `begin_time`, `end_time` |
| `order_attr` | 从订单明细侧按订单和顾问聚合原始支付时间及 service 转入/转出金额 | `original_order_pay_success_timestamp`, `pay_success_timestamp`, `trade_timestamp`, `transfer_in_amount`, `transfer_out_amount` |
| `team_hist` | 组织链时间滞后时，按期次保留已在青橙架构中的顾问 | `qici`, `employee_email_name` |
| `dd_0` | 财务业绩原始层，生成标准科目、期次和基础订单字段 | `order_number`, `user_id1`, `trade_status`, `trade_type`, `trade_time`, `price`, `subject`, `qici` |
| `dd` | 优先按 `original_paid_time` 判定原始成交是否落在青橙任职期间；若组织链滞后，则允许 `team_hist` 期次命中兜底保留 | `coalesce(oa.original_paid_time, paid_time, trade_time)` |
| `gmv_t` | 调课调班订单，按订单/课程/用户/期次/科目/课程部门粒度汇总，避免同一顾问同一用户多笔调课调班被揉成一条 | `order_number`, `qici`, `subject`, `course_first_level_department_name`, `name_total_price` |
| `gmv_z` | 非调课调班订单，按订单和课程维度汇总金额 | `trade_type <> '调课调班'`, `name_total_price` |
| `rd` | 合并正常订单和调课调班结果 | `union all` |
| `ord` | 全退订单课节明细 | `full_refund_chain_finish_lesson_count`, `qici_re` |
| `order_change_raw` / `order_change_order_map` / `order_change` | 调课调班/课程转移主链路订单映射，按订单号聚合后供主交易层和退款层复用 | `order_number`, `has_order_change`, `transfer_in_amount_yuan`, `transfer_out_amount_yuan`, `refund_type` |
| `re_ke` | 合并全退课节和调课调班类型，按 `qici_re + order_number` 聚合避免回连放大 | `refund_type`, `full_refund_chain_finish_lesson_count` |
| `t4` | 将退款课节数、财务订单变更链路和 service 转入/转出标记回连到财务交易，只把调课调班流水本身标记为内部变更 | `re_lc`, `main_has_order_change`, `main_transfer_in_amount_yuan`, `main_transfer_out_amount_yuan`, `service_transfer_in_amount_yuan`, `service_transfer_out_amount_yuan`, `is_internal_order_change` |
| `rd_0` | 用户/交易状态层收入、退款、剔除退 4 退款和支付/退款科目数 | `income`, `refund_4`, `refund`, `p_sub`, `r_sub` |
| `wa` | 计算净收、剔除退 4 净收和净科目基础字段 | `promit`, `promit_4`, `jing_sub` |
| `renchan` | 以团队架构表为主，聚合个人期次指标 | `employee_email_name`, `leader_employee_email_name`, `H_promit`, `Y_promit_4`, `in_payer_4`, `j_sub` |
| `goal_qici` / `goal_moth` | 从个人目标表聚合期次目标和月目标 | `qici_goal`, `moth_goal` |
| `final_base` | 汇总个人期次基础指标并回连目标 | `qici_goal`, `moth_goal` |
| 最终查询 | 双粒度输出个人期次/月度转化指标 | `data_level`, `qici`, `moth`, `name`, `leader_employee_email_name`, `dazu`, `jingli`, `xuebu` |

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
| `dd_0 a` | `order_attr oa` + `org_t ot` + `team_hist th` | `oa.order_number = a.order_number and oa.performance_employee_email_name = a.name`，再用 `coalesce(oa.original_paid_time, a.paid_time, a.trade_time)` 匹配任职窗口；若 `team_hist.qici` 命中则兜底保留 | 只保留原始成交时间落在青橙期间的营收/退款，同时避免组织链起始时间滞后误删当前有效订单 |
| `ord` | `order_change` | `ord.order_number = order_change.order_number` | 补充调课调班/课程转移类型 |
| `rd` | `re_ke` | `re_ke.qici_re = rd.qici and re_ke.order_number = rd.order_number` | 给交易补充全退时行课节数 |
| `rd` | `order_change` + service transfer 标记 | `rd.order_number = order_change.order_number`；service 标记来自 `order_attr` 按 `order_number + performance_employee_email_name` 聚合后随 `dd/gmv/rd` 传递 | 主交易层识别内部调课调班调入/调出流水；当 `dim_finance_order_change_df` 漏链路但 service 明细有 `transfer_in_amount/transfer_out_amount` 时也避免误入外部收入/退款桶 |
| `temp_table.dingxi01_qing_team_jg qtg` | `wa` | `qtg.employee_email_name = wa.name and qtg.qici = wa.qici` | 以架构表为主，合并个人期次业绩 |
| `temp_table.dingxi01_qing_team_jg qtg` | `temp_table.dingxi01_qing_qi_moth qm` | `qm.qici = qtg.qici` | 给个人期次补充月份 |

## 10. 与团队完成度【月/期】的差异

| 项目 | 团队完成度【月/期】 | 个人转化 |
|---|---|---|
| 最终主表 | 目标表 `qing_team_goal` 或 `qing_team_g_qi` | 架构表 `qing_team_jg` |
| 目标字段 | 输出 `goal`, `emye_c` | 不输出目标 |
| 输出粒度 | 团队/月或团队/期 | 个人/期，同时带月份 |
| 破单 | 统计有净收的员工数 | 每个人维度 `podan` 理论上为 0 或 1 |
| 额外指标 | 团队完成度不拆一对一 H 指标 | 个人转化输出 `Y_promit_4`, `Y_income_4`, `Y_refund_4`, `H_income_4`, `H_refund_4`, `in_payer_4`, `j_sub` |

## 11. 指标口径

指标集合沉淀到 `knowledge/metrics/qingcheng_personal_conversion_metrics.md`。

核心指标包括：

- `income`、`refund`、`promit`
- `H_promit`、`n_H_promit`
- `H_promit_4`、`n_H_promit_4`
- `Y_promit_4`、`Y_income_4`、`Y_refund_4`
- `H_income_4`、`H_refund_4`
- `re_payer`、`re_payer_4`、`in_payer_4`
- `j_sub`、`podan`

## 12. 已知风险和待确认事项

- 期次推导已改为 `interval` 写法；后续生成新 SQL 不得回退为 Presto 三参数 `date_add('day', n, expr)`。
- `org_t` 和财务表按 `name` join，若重名可能误匹配；是否应改用 `email_prefix` 待确认。
- 历史版本 `gmv_t` 曾按 `name + user_id1` 去重，可能弱化课程/期次维度；2026-06-21 已改为订单/课程粒度，后续生成新 SQL 不得回退。
- `rd_0` 计算了 `r_sub`，但后续未输出；是否需要净科目抵扣退款科目待确认。
- `wa.jing_sub` 直接取 `p_sub`，当前 `j_sub` 实际为支付科目求和，不扣减退款科目；“净科目数”命名待确认。
- `renchan` 以 `temp_table.dingxi01_qing_team_jg` 为主表，未匹配业绩的架构人员会保留并输出 0 指标。
- `temp_table.dingxi01_qing_team_jg` 是否一人一期唯一待确认；若不唯一，会放大个人业绩。
- 业务已确认 `H业务线` 按 100% 计入、所有 `非H业务线` 统一按 50% 折算；后续文档和 SQL 不得再回退成“仅小初 50%”。
- 命中 `dim_finance_order_change_df` 的正常订单绩效必须保留；只能剔除 `trade_type='调课调班'` 的内部变更流水本身。
- 内部调课调班识别不能只依赖 `dim_finance_order_change_df`；若 service 明细同订单存在 `transfer_in_amount/transfer_out_amount`，也应作为 `trade_type='调课调班'` 流水的补充剔除信号。

## 13. 2026-06-21 折算后产出修复记录

- 当前生产 SQL 与 `resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql` 已对齐到 573 行版本，数据中心数据集为 `青橙个人转化`，`fileValue=2769`。
- 修复点 1：`dd_0` 对空 `course_first_level_department_name` / `course_second_level_department_name` 增加兜底。`grade_list` 命中小学或初中时归为 `小初业务线`，否则兜底为 `H业务线`；H 业务线二级部门为空时兜底为 `精品班学部`。
- 修复点 2：`gmv_t` 调课调班不再按 `name + user_id1` 粗粒度去重，改为订单、课程、用户、交易时间、科目、期次和课程部门粒度汇总。
- 修复点 3：青橙任职窗口统一使用 `coalesce(paid_time, trade_time)` 作为开始/结束边界锚点，优先按原始支付时间归属组织窗口，兜底退回 `trade_time`。
- 修复点 4：新增排错样例：`user_id=1606647` 的历史订单在 2026-06-25 退款，但原始支付时间在 2023-10，且顾问 `陈贺新` 于 2025-05-26 才进入青橙；旧口径会误把该退款计入青橙，现已修正。
- 已验证风险样例与诊断 SQL 见 `knowledge/sql_patterns/qingcheng_personal_completion_discounted_output_risks.md`。

## 14. 2026-06-22 调课调班主交易链路修复记录

- `dim_finance_order_change_df` 不再只按 `parent_order_number` 接到退款明细层，而是把 `order_number`、`parent_order_number`、`original_order_number`、`latest_child_order_number` 展开为订单号映射后接到 `rd/t4` 主交易层。
- `biz_type` 覆盖范围从 `biz_type = 2` 改为 `biz_type in (2, 7)`，避免漏掉 `biz_type=7` 的青橙调课调班链路。
- `re_ke` 按 `qici_re + order_number` 聚合后再回连，避免一笔交易被多条退款/调课链路行放大。
- 主交易层识别为内部调课调班调入/调出时，不进入 `income`、`refund`、`refund_4` 和科目数，避免把调出退款误算为 4 节内外部退费。
- 已验证样例：`谷锦茜` 在 `20260619期` 修复后 `income=9200`、`refund=4800`、`H_promit_4=4400`、前端折算后产出 `4400`。

## 15. 2026-06-28 任职窗口和内部调课调班最终修复

- 新增 `order_attr`：从 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 提取 `original_order_pay_success_timestamp / pay_success_timestamp / trade_timestamp`，生成 `original_paid_time`。
- `dd` 不再只按 `coalesce(paid_time, trade_time)` 判定组织窗口，而是优先按 `coalesce(oa.original_paid_time, paid_time, trade_time)`。
- 新增 `team_hist` 兜底：组织链开始时间滞后时，只要顾问已在该期次青橙架构中出现，就允许该期订单保留。
- `gmv_z` 从 `trade_type = '正常订单'` 调整为 `coalesce(trade_type, '') <> '调课调班'`，避免误排除应保留的正常绩效订单。
- `is_internal_order_change` 调整为“只剔除调课调班流水本身”；命中订单变更链路但本身是正常成交的订单不再排除。
- 已验证样例：`李孟笛06` 在错误版本中 `20260626期` 被压到 `9150`；修复后该期恢复到 `22550`。

## 16. 2026-07-03 service transfer 补充识别修复

- 错误原因：部分 `trade_type='调课调班'` 正向调入流水在 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 已有 `transfer_in_amount`，但未命中 `finance_dw.dim_finance_order_change_df` 展开的订单号映射。旧 SQL 只按 finance 订单变更维表或负金额剔除，导致调出退款被剔除、正向调入被保留。
- 修复规则：`order_attr` 按 `order_number + performance_employee_email_name` 聚合 `transfer_in_amount/transfer_out_amount`，随 `dd -> gmv_t/gmv_z -> rd -> t4` 传递；`is_internal_order_change` 在 `trade_type='调课调班'` 且 service 转入/转出金额非 0 时也置 1。
- 边界：service transfer 只作为内部调课调班识别信号，不替代 `finance_dw.app_finance_performance_extend_details_hf` 作为完成度金额事实源；正常订单即使命中订单变更链路仍保持绩效。
- 已验证样例：`李兵建` `20260703期` 两笔 service transfer 正向调入 `962.34` 和 `1050.00` 修复前误入个人班课营收/折算后产出，修复后个人 `class_income=0`、`discounted_output=0`。
