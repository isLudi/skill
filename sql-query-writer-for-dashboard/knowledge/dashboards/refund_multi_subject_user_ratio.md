# 多科用户退费占比看板

## 1. 来源

- 原始 SQL：`resources/raw_sql/refund_multi_subject_user_ratio.sql`
- 来源文件：`E:\2000_work\GAOTU\多科用户退费占比.txt`
- 入库日期：2026-05-09

## 2. 查询目标

按期次、顾问、渠道、经理、小组、年级统计用户购买科目数分层下的退款金额、总退款、总收款和用户数，用于分析单科、多科用户的退费贡献。

## 3. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| finance_dw.app_finance_performance_extend_details_hf | dd / ranked_dd / rd | 财务业绩明细，计算正负流水、期次、课程科目和课程产品 |
| service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | n_uid | 通过原始订单用户和业绩顾问获取最新 lead_id |
| service_dw.dim_crm_assign_rule_lead_detail_hf | rr | 关联分配规则并按规则名派生渠道 `channel_1` 和规则期次 `friday_period` |
| temp_table.dingxi01_jiagou_zx | zx | 按顾问姓名补充小组和经理 |

## 4. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| dd | 从财务业绩明细取订单流水，按 `trade_time` 推导 `qici`，并按交易类型计算 `zong_price` | `qici`, `trade_type`, `zong_price`, `subject` |
| ranked_dd | 对订单流水去重，按课程二级部门派生产品类型 `course_name` | `course_name`, `zong_price0`, `dup_rn` |
| rd | 保留去重后且金额不为 0 的订单流水 | `user_id1`, `name`, `qici`, `zong_price` |
| n_uid | 从归因流水表按用户取最新期次 lead_id | `lead_id`, `original_order_user_number`, `performance_employee_email_name` |
| lead_gmv | 将财务流水补充 lead_id | `lead_id`, `user_id1`, `name` |
| rule | 关联分配规则，按 `rule_name` 派生渠道 `channel_1`，并由规则名前 4 位推导 `friday_period` | `rule_name`, `channel_1`, `friday_period` |
| base | 补充专项架构，并按订单期次与规则期次差异派生 `week_diff` | `xiaozu`, `jingli`, `week_diff` |
| user_subject | 按用户统计购买科目数、退款金额和收款金额 | `subject_count`, `refund_amount`, `income_amount` |
| final select | 按顾问维度输出单科、2-3 科、3 科以上用户退款金额及总收退 | `refund_1`, `refund_2`, `refund_3`, `total_refund`, `total_income` |

## 5. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| rd | n_uid | `rd.user_id1 = n_uid.original_order_user_number` + `rd.name = n_uid.performance_employee_email_name` | left join | 只保留 `n_uid.rn = 1` 的最新用户-顾问 lead_id |
| lead_gmv | rr | `lead_gmv.lead_id = rr.lead_id` + `lead_gmv.email_prefix = rr.account_domain` | left join | 补充分配规则和渠道映射 |
| rule | temp_table.dingxi01_jiagou_zx zx | `zx.employee_email_name = rule.name` | left join | 补充小组和经理；姓名关联唯一性待确认 |

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

归因流水：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and course_first_level_department_name = 'H业务线'
and course_second_level_department_name in ('精品班学部','菁英班学部','市场部','本地化大班学部','一对一学部','青橙项目部')
and performance_third_level_department_name = '市场顾问部'
```

分配规则：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
```

## 7. group by 维度

- `qici`
- `name`
- `channel_1`
- `jingli`
- `xiaozu`
- `grade_list`

## 8. 聚合指标

| 指标名 | SQL 表达式 | 口径说明 | 状态 |
|---|---|---|---|
| subject_count | `count(distinct subject)` | 用户维度购买科目数 | 来自历史 SQL |
| refund_amount | `sum(case when zong_price < 0 then abs(zong_price) else 0 end)` | 用户维度退款金额，取负向流水绝对值 | 来自历史 SQL |
| income_amount | `sum(case when zong_price > 0 then zong_price else 0 end)` | 用户维度收款金额 | 来自历史 SQL |
| refund_1 | `sum(case when subject_count = 1 then refund_amount else 0 end)` | 单科用户退款金额 | 来自历史 SQL |
| refund_2 | `sum(case when subject_count between 2 and 3 then refund_amount else 0 end)` | 2-3 科用户退款金额 | 来自历史 SQL |
| refund_3 | `sum(case when subject_count > 3 then refund_amount else 0 end)` | 3 科以上用户退款金额 | 来自历史 SQL |
| user_count | `count(distinct user_id1)` | 用户数 | 来自历史 SQL |
| total_refund | `sum(refund_amount)` | 总退款金额 | 来自历史 SQL |
| total_income | `sum(income_amount)` | 总收款金额 | 来自历史 SQL |

## 9. 可复用 SQL 模式

- 期次：由 `trade_time` 推导 `qici`，包含 2026 年春节特殊期次硬编码。
- 金额：`zong_price < 0` 视为退款，`zong_price > 0` 视为收款。
- 多科分层：先到用户粒度计算 `count(distinct subject)`，再聚合到顾问维度。
- 渠道：按 `service_dw.dim_crm_assign_rule_lead_detail_hf.rule_name` 的 CASE 派生 `channel_1`，分支顺序敏感。

## 10. 待确认事项

- 原始 SQL 包含三参数 `date_add('day', n, expr)` 历史写法；生成新 SQL 时需改为平台兼容写法。
- `finance_dw.app_finance_performance_extend_details_hf` 只过滤员工部门，选出了课程部门字段但未单独过滤课程部门，复用时需确认是否补充。
- `service_dw.dim_crm_assign_rule_lead_detail_hf` 未加部门过滤字段，依赖主表和 lead_id 范围限制，是否足够需确认。
- `n_uid` 按 `original_order_user_number` 取最新 `rn = 1`，可能忽略同一用户不同顾问/不同期次的 lead_id 差异。
- `temp_table.dingxi01_jiagou_zx` 无 `qici` 字段，补充的是当前专项架构，不代表历史期次架构。
