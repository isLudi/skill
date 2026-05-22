# 退费科目产品看板

## 1. 来源

- 原始 SQL：`resources/raw_sql/refund_subject_product.sql`
- 来源文件：`E:\2000_work\GAOTU\退费_科目_产品.txt`
- 入库日期：2026-05-09

## 2. 查询目标

按期次、渠道、经理、小组、年级、标准科目、课程产品和顾问统计收款与退款金额，用于分析退费在科目和产品维度上的分布。

## 3. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| finance_dw.app_finance_performance_extend_details_hf | dd / gmv_t / gmv_z / rd | 财务业绩明细，拆分调课调班和正常订单，计算正负金额 |
| service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | n_uid | 获取最新 lead_id 并限定课程/业绩范围 |
| service_dw.dim_crm_assign_rule_lead_detail_hf | rr | 根据分配规则派生渠道 |
| temp_table.dingxi01_jiagou_zx | zx | 补充顾问小组和经理 |

## 4. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| dd | 读取财务业绩明细，按退款状态调整 `real_price_0`，推导 `qici` | `real_price_0`, `price`, `qici`, `subject` |
| gmv_t | 处理 `调课调班`，按顾问汇总 `price` 并取第一条 | `name_total_price`, `dup_rn` |
| gmv_z | 处理 `正常订单`，按班级、用户、金额和顾问去重 | `name_total_price`, `dup_rn` |
| rd | 合并正常订单与调课调班流水 | `name_total_price` |
| n_uid | 从归因流水表取用户最新 lead_id，课程范围非常宽 | `lead_id`, `original_order_user_number`, `performance_employee_email_name` |
| lead_gmv | 补充 `course_name` 产品分类和 lead_id | `course_name`, `lead_id` |
| rule | 按分配规则名派生 `channel_1` 和 `friday_period` | `rule_name`, `channel_1` |
| base | 补充专项架构和 `week_diff` | `xiaozu`, `jingli`, `week_diff` |
| gmv_1 | 按顾问维度汇总总收款和退款 | `income_amount`, `refund_amount` |
| final select | 输出标准科目、课程产品、顾问、收款和退款 | `subject`, `course_name`, `income_amount`, `refund_total` |

## 5. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| rd | n_uid | `rd.user_id1 = n_uid.original_order_user_number` + `rd.name = n_uid.performance_employee_email_name` | left join | 只保留最新 `n_uid.rn = 1` |
| lead_gmv | rr | `lead_gmv.lead_id = rr.lead_id` + `lead_gmv.email_prefix = rr.account_domain` | left join | 补充分配规则和渠道 |
| rule | temp_table.dingxi01_jiagou_zx zx | `zx.employee_email_name = rule.name` | left join | 补充小组/经理 |
| base | gmv_1 | `qici + name + channel_1 + grade_list + jingli + xiaozu` | left join | 补充同粒度收款总额 |

## 6. where 条件

财务业绩明细：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and employee_first_level_department_name = 'H业务线'
and employee_second_level_department_name = '市场部'
and employee_third_level_department_name = '市场顾问部'
and qici > '20260220期'
```

归因流水：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and course_first_level_department_name in ('H业务线','A业务线','EM业务线','LL业务线','TT','TUTU','TT业务线')
and course_second_level_department_name in (<原 SQL 长列表>)
and performance_third_level_department_name = '市场顾问部'
```

## 7. group by 维度

- `qici`
- `channel_1`
- `jingli`
- `xiaozu`
- `grade_list`
- 标准化 `subject`
- `course_name`
- `name`
- `income_amount`

## 8. 聚合指标

| 指标名 | SQL 表达式 | 口径说明 | 状态 |
|---|---|---|---|
| income_amount | `sum(case when name_total_price > 0 then name_total_price else 0 end)` | 同维度总收款 | 来自历史 SQL |
| refund_amount | `sum(case when name_total_price < 0 then abs(name_total_price) else 0 end)` | gmv_1 中退款金额，正数展示 | 来自历史 SQL |
| refund_total | `sum(case when name_total_price < 0 then name_total_price else 0 end)` | 结果层退款金额，保留负数 | 来自历史 SQL |
| subject | `case when base.subject like ... then ... else '其他' end` | 科目标准化 | 来自历史 SQL |
| course_name | 按 `course_second_level_department_name` 映射 | 大班/小班/一对一/本地化/清北/其他 | 来自历史 SQL |

## 9. 可复用 SQL 模式

- 正常订单与调课调班分开处理后 `union all`，避免同一逻辑混用。
- 结果层用 `subject` 标准化展示科目，原字段为 `course_subject`。
- 产品分类来自 `course_second_level_department_name like ...`，不是课程名字段。

## 10. 待确认事项

- `n_uid` 中课程二级部门使用极长白名单，是否应收敛为 H 业务线市场顾问分析范围需业务确认。
- `gmv_t` 对调课调班按 `name` 汇总并取第一条，可能跨用户/订单合并，需确认是否符合该看板口径。
- 结果层 `refund_total` 保留负数，而 `gmv_1.refund_amount` 使用绝对值；前端展示需确认正负号口径。
- 原始 SQL 使用 `group by 1,2,3...`，后续改写建议显式写字段。
