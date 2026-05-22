# 退费原因分析看板

## 1. 来源

- 原始 SQL：`resources/raw_sql/refund_reason_analysis.sql`
- 来源文件：`E:\2000_work\GAOTU\退费原因分析.txt`
- 入库日期：2026-05-09

## 2. 查询目标

按期次、顾问、渠道、经理、小组、年级和退费原因统计退款金额，并补充同维度收款金额，用于分析市场顾问相关订单的退费原因分布。

## 3. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| finance_dw.app_finance_performance_extend_details_hf | dd / ranked_dd / rd | 财务业绩明细，计算正负流水和期次 |
| service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | n_uid | 获取用户最新 lead_id |
| service_dw.dim_crm_assign_rule_lead_detail_hf | rr | 关联规则名并派生渠道 |
| temp_table.dingxi01_jiagou_zx | zx | 补充小组和经理 |
| finance_dw.dwd_finance_order_refund_df | rs | 通过订单号补充 `refund_reason` |

## 4. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| dd | 从财务业绩明细提取订单、交易、顾问和课程字段，推导期次和 `zong_price` | `order_number`, `qici`, `zong_price` |
| ranked_dd | 去重并派生课程产品 | `dup_rn`, `course_name`, `zong_price0` |
| rd | 保留有效流水 | `user_id1`, `name`, `order_number` |
| n_uid | 获取用户-顾问最新 lead_id | `lead_id`, `original_order_user_number`, `performance_employee_email_name` |
| lead_gmv | 补充 lead_id | `lead_id` |
| rule | 关联分配规则，派生 `channel_1` 和 `friday_period` | `rule_name`, `channel_1` |
| base | 补充架构和期次差异 | `xiaozu`, `jingli`, `week_diff` |
| gmv_1 | 按顾问维度汇总收款和退款 | `income_amount`, `refund_amount` |
| final select | 关联退款明细表，按退费原因输出退款金额 | `refund_reason`, `refund_amount` |

## 5. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| rd | n_uid | `rd.user_id1 = n_uid.original_order_user_number` + `rd.name = n_uid.performance_employee_email_name` | left join | 获取最新 lead_id |
| lead_gmv | rr | `lead_gmv.lead_id = rr.lead_id` + `lead_gmv.email_prefix = rr.account_domain` | left join | 补充分配规则 |
| rule | temp_table.dingxi01_jiagou_zx zx | `zx.employee_email_name = rule.name` | left join | 补充小组/经理 |
| base | finance_dw.dwd_finance_order_refund_df rs | `base.order_number = rs.order_number` | left join | 补充退款原因；仅保留 `refund_type = '1'` 的退款明细 |
| base | gmv_1 | `qici + name + channel_1 + grade_list + jingli + xiaozu` | left join | 补充同维度收款总额 |

## 6. where 条件

财务业绩明细：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and employee_first_level_department_name = 'H业务线'
and employee_second_level_department_name = '市场部'
and employee_third_level_department_name = '市场顾问部'
and price <> 0
and qici > '20260206期'
```

退款明细：

```sql
dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
and refund_type = '1'
```

## 7. group by 维度

- `qici`
- `name`
- `channel_1`
- `jingli`
- `xiaozu`
- `grade_list`
- `refund_reason`
- `income_amount`

## 8. 聚合指标

| 指标名 | SQL 表达式 | 口径说明 | 状态 |
|---|---|---|---|
| income_amount | `sum(case when zong_price > 0 then zong_price else 0 end)` | 同维度收款金额 | 来自历史 SQL |
| refund_amount | `sum(case when zong_price < 0 then abs(zong_price) else 0 end)` | 按退费原因聚合的退款金额，正数展示 | 来自历史 SQL |
| refund_reason | `finance_dw.dwd_finance_order_refund_df.refund_reason` | 退款原因 | 表字段来自 SQL 推断，待确认 |

## 9. 可复用 SQL 模式

- `finance_dw.dwd_finance_order_refund_df` 只在退费原因分析中使用，通过 `order_number` 与财务业绩明细关联。
- 退费原因当前限定 `refund_type = '1'`，推断为全部退款或某类退款，真实含义待确认。
- 收款金额在 `gmv_1` 预聚合，再回连结果层，用作退费原因维度的分母/对照指标。

## 10. 待确认事项

- `finance_dw.dwd_finance_order_refund_df` 未在既有字段目录中，当前只根据 SQL 使用字段建立最小表文档；字段类型、粒度、分区和 `refund_type = '1'` 含义均待确认。
- 退款明细使用 `dt = now() - 24 hour`，其他事实表使用 `now() - 2 hour`，分区时间不一致需确认是否为产出延迟。
- 同一订单可能存在多条退款原因记录；`order_number` join 是否唯一需确认。
- 未匹配退款明细时 `refund_reason` 为空，是否需要归为“未知”由前端或业务确认。
