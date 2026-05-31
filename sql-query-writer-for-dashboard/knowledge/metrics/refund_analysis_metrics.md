# 退费分析指标

## 1. 指标集合名称

退费分析指标集合

## 2. 来源

- `resources/raw_sql/refund_multi_subject_user_ratio.sql`
- `resources/raw_sql/refund_subject_product.sql`
- `resources/raw_sql/refund_reason_analysis.sql`
- 入库日期：2026-05-09

## 3. 适用范围

适用于 H 业务线市场部市场顾问部相关的顾问退费分析，包括多科用户退费占比、退费科目产品分布和退费原因分析。

## 4. 基础口径

| 字段/指标 | SQL 口径 | 说明 |
|---|---|---|
| qici | 由 `trade_time` 按春节特殊期次和周五规则推导 | 期次硬编码覆盖 2026-01-20 至 2026-03-02 部分日期 |
| course_name | 按 `course_second_level_department_name` 映射为大班/小班/一对一/本地化/清北/其他 | 产品分类，不是课程名称 |
| channel_1 | 按 `service_dw.dim_crm_assign_rule_lead_detail_hf.rule_name` CASE 派生 | 渠道规则来自历史 SQL，待业务确认 |
| friday_period | 从规则名前 4 位 MMDD 推导周五期次，月份 >= 6 归 2025，否则归 2026 | 用于 `week_diff` |
| week_diff | 订单期次 `qici` 与规则期次 `friday_period` 的周差分层 | 0=同周期，1=后一周，2=后 2-3 周，3=其他 |

## 5. 金额指标

| 指标名 | 中文含义 | SQL 口径 | 来源 |
|---|---|---|---|
| zong_price | 订单总金额 | 正常订单按 `employee_email_name + user_id + clazz_name + trade_status` 汇总 `price`；调课调班按 `employee_email_name + user_id` 汇总 `price` | 多科/退费原因 SQL |
| name_total_price | 顾问订单金额 | `退费_科目_产品` 中正常订单取 `real_price_0`，调课调班按 `name` 汇总 `price` | 退费科目产品 SQL |
| income_amount | 收款金额 | `sum(case when 金额字段 > 0 then 金额字段 else 0 end)` | 三份 SQL |
| refund_amount | 退款金额 | 多数 CTE 使用 `sum(case when 金额字段 < 0 then abs(金额字段) else 0 end)` | 三份 SQL |
| refund_total | 退款金额 | `退费_科目_产品` 结果层使用 `sum(case when name_total_price < 0 then name_total_price else 0 end)`，保留负数 | 退费科目产品 SQL |
| total_refund | 总退款 | `sum(refund_amount)` | 多科用户退费占比 SQL |
| total_income | 总收款 | `sum(income_amount)` | 多科用户退费占比 SQL |

## 6. 多科用户指标

| 指标名 | 中文含义 | SQL 口径 | 待确认 |
|---|---|---|---|
| subject_count | 用户购买科目数 | `count(distinct subject)`，在 `qici + name + channel_1 + jingli + xiaozu + grade_list + user_id1` 粒度计算 | 科目字段是否需标准化后再去重待确认 |
| refund_1 | 单科用户退款金额 | `sum(case when subject_count = 1 then refund_amount else 0 end)` | 否 |
| refund_2 | 2-3 科用户退款金额 | `sum(case when subject_count between 2 and 3 then refund_amount else 0 end)` | 分层名称待业务确认 |
| refund_3 | 3 科以上用户退款金额 | `sum(case when subject_count > 3 then refund_amount else 0 end)` | 与 `refund_2` 在 3 科上是否重叠：SQL 中不重叠，`refund_3` 实际为 4 科及以上 |
| user_count | 用户数 | `count(distinct user_id1)` | 否 |

## 7. 科目和产品指标

| 字段/指标 | SQL 口径 | 说明 |
|---|---|---|
| subject | `case when base.subject like '%数学%' then '数学' ... else '其他' end` | 标准科目，覆盖数学、语文、英语、物理、生物、化学、地理、政治、历史、学习分享、定制方案 |
| course_name | `course_second_level_department_name` 映射 | 大班/小班/一对一/本地化/清北/其他 |
| refund_total | 按标准科目和产品聚合负向退款金额 | 保留负数 |

## 8. 退费原因指标

| 字段/指标 | SQL 口径 | 说明 |
|---|---|---|
| refund_reason | `finance_dw.dwd_finance_order_refund_df.refund_reason` | 通过 `order_number` 关联退款明细 |
| refund_amount | `sum(case when zong_price < 0 then abs(zong_price) else 0 end)` | 按退费原因聚合，正数展示 |

## 9. 待确认事项

- 三份 SQL 均使用历史三参数 `date_add`，作为原始 SQL 归档；生成新 SQL 时需改写。
- 金额单位沿用财务业绩扩展表 `price/real_price`，与归因流水分单位口径不同，不应直接混合。
- 退费科目产品 SQL 中 `refund_total` 为负数，多科和退费原因 SQL 中退款金额为正数，前端展示需统一口径。
- 分配规则渠道 CASE 来自历史 SQL，不等同于 `market_channel_case_when_0524.sql` 的最新渠道映射。
- `finance_dw.dwd_finance_order_refund_df` 表结构待确认。
