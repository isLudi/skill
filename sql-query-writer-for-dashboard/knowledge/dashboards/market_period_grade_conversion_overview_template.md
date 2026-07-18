# H 业务线初中期次×年级转化概览模板

## 1. 定位

- 业务域：`market_consultant`
- 模板编号：M5
- 用途：按期次和初一/初二/初三输出线索、转化、订单、净收款和单效的可加总分子/分母。
- 历史 SQL：`resources/raw_sql/market_period_grade_conversion_overview_20260718.sql`
- 历史结果：`runtime/sql-query-writer-for-dashboard/h_biz_junior_conversion_20250502_20251226.xlsx`
- 复用口径：`knowledge/metrics/h_biz_line_department_conversion_metrics.md`

## 2. 输出字段

| 字段 | 口径 | 下游展示 |
|---|---|---|
| `lead_count` | `sum(lead_count)` | 线索量 |
| `head_conversion_users_num` | `sum(conversion_lead_count)` | 人头转化分子 |
| `head_conversion_leads_den` | `sum(lead_count)` | 人头转化分母 |
| `order_conversion_orders_num` | `sum(order_count)` | 订单转化分子 |
| `order_conversion_leads_den` | `sum(lead_count)` | 订单转化分母 |
| `net_income_amt` | `sum(income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount) / 100` | 净收款，元 |
| `unit_efficiency_profit_num` | 与 `net_income_amt` 同源 | 单效分子 |
| `unit_efficiency_leads_den` | `sum(lead_count)` | 单效分母 |

展示层公式：

```text
人头转化率 = sum(head_conversion_users_num) / sum(head_conversion_leads_den)
订单转化率 = sum(order_conversion_orders_num) / sum(order_conversion_leads_den)
单效 = sum(unit_efficiency_profit_num) / sum(unit_efficiency_leads_den)
```

SQL 不直接输出行级比率，避免跨年级或跨期次时对比率二次聚合。

## 3. QuerySpec 骨架

| 槽位 | 取值/要求 |
|---|---|
| `domain` | `market_consultant` |
| `intent` | H 业务线初中期次×年级转化概览 |
| `dimensions` | `period_name + grade` |
| `time_range` | 期次左闭右闭或左闭右开，必须显式声明 |
| `business_scope` | H 业务线下明确的承接二级部门与虚拟部门集合 |
| `calculation_grain` | 先在线索/顾问/规则层去重，再按 `period_name + grade` 汇总 |
| `output_grain` | `period_name + grade` |
| `candidate_tables` | 市场全链路宽表 |
| `join_path` | 单表人工聚合，无外部 Join |

## 4. 复用参数

- `period_start`、`period_end`。
- `grade_list`；默认初一、初二、初三。
- `section_assign_employee_second_level_department_name` 集合。
- `virtual_third_department_name` 集合。
- 最新可用 `dt/hour` 策略。

历史样例聚合了 H 业务线多个二级部门，不能解释为单一市场顾问部表现。若用户要市场顾问部、精品班学部或其他单部门结果，必须收窄业务范围并在 QuerySpec 中写明。

## 5. 已验证结果与风险

- 历史工作簿有 42 个业务结果行，覆盖 35 个期次和 100,662 条线索。
- 存在 `lead_count=0` 但转化或金额非零的期次—年级组合；这可能来自跨期成交/退款或年级映射差异，展示比率时必须保留零分母保护并单独诊断。
- `lead_count` 在当前市场顾问 contract 中仍为 `pending_confirmation`；M5 只能作为复杂人工 SQL 模板，不能自动编译。
