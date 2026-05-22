# 青橙年季月营收情况 raw

## 1. 来源

`resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql`

入库时间：2026-05-22

## 2. 查询目标

沉淀青橙项目部年/季度/月营收情况 SQL。该 SQL 使用财务业绩扩展明细表作为收入来源，通过员工组织链确认交易发生时员工处于青橙项目部，再按期次、年、季度、月份、课程部门、交易状态、团队架构和年级输出营收、退款、净营收、支付/退款科目数和支付/退款用户数。

## 3. 最终输出粒度

| 维度 | 字段 |
|---|---|
| 课程部门 | `course_first_level_department_name`, `course_second_level_department_name` |
| 交易状态 | `trade_status`，归一为支付/退款/未知 |
| 团队架构 | `leader_employee_email_name`, `dazhuguan`, `xuebu` |
| 年级 | `grade_list` |
| 期次 | `qici` |
| 日期 | `max_trade_date` |
| 年 | `max_year` |
| 季度 | `max_quarter` |
| 月 | `max_month` |

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `dw.dim_employee_chain` | `org_t` | 识别员工在青橙项目部路径下的任职起止时间 |
| `finance_dw.app_finance_performance_extend_details_hf` | `dd_0` / `dd` | 财务业绩扩展明细，提供订单、交易、金额、课程和员工信息 |

## 5. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.dingxi01_qing_zz` | 青橙组织架构补充表，按员工姓名补充主管、大主管、学部 | 已从 SQL 入库，来源/刷新方式待人工确认 |

## 6. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `org_t` | 员工在青橙项目部路径下的任职时间窗口 | `dep_path`, `email_prefix`, `name`, `begin_time`, `end_time` |
| `dd_0` | 财务业绩原始层，计算期次、交易状态金额正负前置字段 | `id`, `order_number`, `user_id1`, `trade_status`, `trade_type`, `trade_time`, `price`, `name`, `qici` |
| `dd` | 将财务业绩限制在员工属于青橙项目部的任职期间 | `trade_time >= begin_time and trade_time <= end_time` |
| `gmv_t` | 调课调班订单处理，按 `name + user_id1` 汇总价格并保留一条 | `name_total_price`, `dup_rn` |
| `gmv_z` | 正常订单处理，按订单和课程维度汇总价格 | `name_total_price` |
| `rd` | 合并正常订单和调课调班结果 | `union all` |
| `rd_0` | 归一交易状态，补充青橙组织架构，计算日期、年、季度、月和金额/科目 | `income`, `refund`, `promit`, `sub` |
| `wa` | 按交易状态生成支付科目和退款科目 | `p_sub`, `r_sub` |
| 最终查询 | 按年/季/月和架构维度聚合 | `income`, `refund`, `promit`, `p_sub`, `r_sub`, `p_payer`, `r_payer` |

## 7. 青橙范围限定

| 位置 | 范围字段 | 取值 |
|---|---|---|
| `org_t` 员工链路 | `array_join(slice(split(path_name, '-'), 1, 3), '-')` | `'高途-H业务线-青橙项目部'` |
| `dd_0` 财务业绩 | `employee_first_level_department_name` | `'H业务线'` |
| `dd_0` 财务业绩 | `employee_second_level_department_name` | `'青橙项目部'` |
| `dd` 任职期间过滤 | `dd_0.trade_time >= ot.begin_time and dd_0.trade_time <= ot.end_time` | 只保留交易发生时在青橙任职的员工 |

## 8. 分区和时间条件

| 表/CTE | dt 条件 | hour 条件 | 其他时间条件 |
|---|---|---|---|
| `dw.dim_employee_chain` | `format_datetime(now() - interval '24' hour, 'YYYYMMdd')` | 无 | 使用组织链当前分区中的 `begin_time` 和 `end_time` |
| `finance_dw.app_finance_performance_extend_details_hf` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | `format_datetime(now() - interval '2' hour, 'HH')` | `qici >= '20250103期'` |

## 9. join 关系

| 左侧 | 右侧 | join key | 用途 |
|---|---|---|---|
| `dd_0` | `org_t ot` | `ot.name = dd_0.name`，并过滤 `trade_time` 在 `begin_time` 和 `end_time` 之间 | 确认交易发生时员工属于青橙项目部 |
| `rd` | `temp_table.dingxi01_qing_zz zz` | `zz.employee_email_name = rd.name` | 补充青橙主管、大主管、学部 |

## 10. 交易类型处理

| 交易类型 | 处理方式 |
|---|---|
| `正常订单` | 在 `gmv_z` 中按订单、用户、交易、课程等维度 `sum(price)` |
| `调课调班` | 在 `gmv_t` 中先按 `name + user_id1` 汇总 `price` 为 `name_total_price`，剔除 0，再按 `row_number()` 保留一条 |

## 11. 营收指标

指标集合沉淀到 `knowledge/metrics/qingcheng_revenue_year_quarter_month_metrics.md`。

| 指标 | 口径简述 |
|---|---|
| `income` | `name_total_price >= 0` 的金额汇总 |
| `refund` | `name_total_price < 0` 的绝对值汇总 |
| `promit` | `name_total_price` 汇总，净营收 |
| `p_sub` | 支付状态下的非选科志愿/定制方案科目数 |
| `r_sub` | 退款状态且退款金额大于 500 的科目数 |
| `p_payer` | 支付状态用户数 |
| `r_payer` | 退款状态且退款金额大于 500 的用户数 |

## 12. 已知风险和待确认事项

- SQL 中存在 Presto 三参数 `date_add('day', n, expr)`，公司查询平台可能按 Hive 两参数函数解析；后续生成新 SQL 时必须改为 `interval` 写法。
- `dd` 使用 `left join org_t` 后在 `where` 中限定 `ot.begin_time/end_time`，实际等价于 inner join；未匹配组织链的财务记录会被剔除。
- `org_t` 按 `name` 与财务表 join，若姓名重名可能误匹配；是否应改用 `email_prefix` 待确认。
- `gmv_t` 调课调班按 `name + user_id1` 去重并按 `id` 保留一条，可能丢失课程/期次维度，需确认是否符合财务口径。
- `rd_0` 中 `trade_status` 是 select 别名，但 group by 使用原始 `trade_status` 字段；Presto 下别名解析行为需确认，生成新 SQL 时建议显式 group by 完整 CASE 表达式。
- `wa` 中 `case when trade_status = '支付' then sum(sub) else 0 end` 使用聚合嵌在 CASE 中，当前 group by 全字段后通常等价于当前行 sub，但可读性较弱。
- `max_trade_date/max_year/max_quarter/max_month` 基于每个 `rd_0` 分组内最大交易时间；最终按这些字段分组，因此不是简单自然月/自然季度全局汇总。

