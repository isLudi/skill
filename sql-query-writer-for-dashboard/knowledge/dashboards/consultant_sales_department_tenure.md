# 顾问部门任职期销售统计

## 1. 来源

原始 SQL：`resources/raw_sql/consultant_sales_department_tenure.sql`

最近更新：2026-05-08

来源：用户在对话中提供的新版顾问任职期销售排名 SQL。

## 2. 查询目标

用于统计市场顾问在指定部门任职时间范围内产生的销售业绩流水，并在部门内计算顾问净收排名和追赶上一名所需净收差值。

核心逻辑：

- 从 `dw.dim_employee_chain` 获取顾问在 `高途-H业务线-市场部-市场顾问部` 路径下的 `begin_time` 和 `end_time`。
- 从 `finance_dw.app_finance_performance_extend_details_hf` 抽取财务业绩流水，按交易时间推导 `qici`。
- 使用 `email_prefix` 将财务流水与组织链做内连接，替代旧版 `name` 关联。
- 只保留 `trade_time` 落在该顾问部门任职起止时间内的流水。
- 正常订单和调课调班分开处理，调课调班按 `name + user_id1` 汇总去重。
- 关联 `temp_table.dingxi01_jiagou_zx` 补充小组、经理和西安/郑州归属。
- 先按 `qici + trade_date + dept + name` 汇总每日净收，再分别计算：
  - `天-部门-期次` 维度排名和追赶上一名差值；
  - `期次-部门` 维度排名和追赶上一名差值。

该 SQL 与 `consultant_sales_ranking_evaluation.sql` 都基于财务业绩流水计算顾问销售数据，但本 SQL 额外增加员工组织链任职时间过滤，并输出部门内排名和差值，不计算 ROI、退费率和评优分位。

## 3. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `dw.dim_employee_chain` | `org_t` 来源表 | 员工组织链，获取顾问在市场顾问部路径下的部门任职起止时间 |
| `finance_dw.app_finance_performance_extend_details_hf` | `dd_0` 来源表 | 财务业绩扩展明细，提供订单、交易、顾问、课程、金额和期次计算字段 |
| `temp_table.dingxi01_jiagou_zx` | `zz` | 员工专项架构映射表，补充小组、经理和部门归属 |

## 4. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `org_t` | 提取顾问在 `高途-H业务线-市场部-市场顾问部` 组织路径下的最早开始时间和最晚结束时间 | `dep_path`, `email_prefix`, `name`, `begin_time`, `end_time` |
| `dd_0` | 从财务业绩流水抽取订单/退款明细，并按 `trade_time` 推导期次 | `qici`, `email_prefix`, `name`, `user_id1`, `trade_type`, `trade_status`, `price`, `trade_time` |
| `dd` | 使用 `email_prefix` 将财务流水与组织链关联，并限制 `trade_time` 在部门任职起止时间内 | `email_prefix`, `trade_time`, `begin_time`, `end_time` |
| `gmv_t` | 处理 `trade_type = '调课调班'`，按 `name + user_id1` 汇总金额并取第一条非 0 记录 | `name_total_price`, `dup_rn` |
| `gmv_z` | 处理 `trade_type = '正常订单'`，按订单、用户、顾问、期次、课程维度汇总金额 | `name_total_price` |
| `rd` | 合并正常订单和调课调班结果 | `qici`, `name`, `trade_status`, `name_total_price` |
| `rd_0` | 关联专项架构，计算支付/退款状态、城市归属、收入、退款、净额 | `trade_status`, `dept`, `income`, `refund`, `promit` |
| `base_result` | 汇总到 `qici + name + xiaozu + jingli + dept + trade_date` 粒度 | `income`, `refund`, `pmit` |
| `day_rank_raw` | 在 `trade_date + dept + qici` 内按 `pmit desc, name` 计算日维度排名和上一名净收 | `day_dept_period_rank_no`, `day_previous_pmit` |
| `day_ranked` | 计算日维度追赶上一名所需净收差值 | `day_dept_period_need_pmit_to_previous` |
| `period_agg` | 汇总到 `qici + dept + name + xiaozu + jingli` 粒度 | `period_income`, `period_refund`, `period_pmit` |
| `period_rank_raw` | 在 `qici + dept` 内按 `period_pmit desc, name` 计算期次维度排名和上一名净收 | `period_dept_rank_no`, `period_previous_pmit` |
| `period_ranked` | 计算期次维度追赶上一名所需净收差值 | `period_dept_need_pmit_to_previous` |
| final select | 合并日维度和期次维度排名结果 | 排名、差值、日净收、期次净收 |

## 5. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| `dd_0` | `org_t ot` | `ot.email_prefix = dd_0.email_prefix` | inner join + where 限制 | 使用邮箱前缀匹配组织链，并通过 `trade_time between begin_time and end_time` 限定在部门任职期内 |
| `rd` | `temp_table.dingxi01_jiagou_zx zz` | `zz.employee_email_name = rd.name` | left join | 补充 `xiaozu`、`jingli` 和 `department`，再派生 `dept` |
| `day_ranked d` | `period_ranked p` | `qici + dept + name` | left join | 将期次-部门排名结果补回到每日结果 |

## 6. where 条件

员工组织链分区和路径范围：

```sql
dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
and array_join(slice(split(path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'
```

财务流水分区：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
```

财务流水员工部门范围：

```sql
employee_first_level_department_name = 'H业务线'
and employee_second_level_department_name = '市场部'
and employee_third_level_department_name = '市场顾问部'
```

期次范围：

```sql
qici >= '20260403期'
```

部门任职时间范围：

```sql
dd_0.trade_time >= ot.begin_time
and dd_0.trade_time <= ot.end_time
```

## 7. group by 和排序维度

基础日汇总粒度：

- `qici`
- `name`
- `xiaozu`
- `jingli`
- `dept`
- `trade_date`

日维度排名分区：

- `trade_date`
- `dept`
- `qici`

期次维度排名分区：

- `qici`
- `dept`

排名排序规则：

```sql
order by pmit desc, name
order by period_pmit desc, name
```

使用 `row_number()`，不允许并列排名。净收相同的顾问按 `name` 字典序打散。

## 8. 输出字段和指标

| 字段/指标 | SQL 表达式 | 口径说明 |
|---|---|---|
| `income` | `sum(income)` | 日维度正向流水金额 |
| `refund` | `sum(refund)` | 日维度退款金额，取绝对值 |
| `pmit` | `sum(promit)` | 日维度净收金额 |
| `day_dept_period_rank_scope` | `'天-部门-期次'` | 日维度排名范围标签 |
| `day_dept_period_rank_no` | `row_number() over (partition by trade_date, dept, qici order by pmit desc, name)` | 日-部门-期次内排名 |
| `day_dept_period_need_pmit_to_previous` | `lag(pmit) - pmit`，第一名为 0 | 日维度追赶上一名所需净收差值 |
| `period_dept_rank_scope` | `'期次-部门'` | 期次维度排名范围标签 |
| `period_dept_rank_no` | `row_number() over (partition by qici, dept order by period_pmit desc, name)` | 期次-部门内排名 |
| `period_dept_need_pmit_to_previous` | `lag(period_pmit) - period_pmit`，第一名为 0 | 期次维度追赶上一名所需净收差值 |
| `period_income` | `sum(income)` | 期次-部门-顾问正向流水金额 |
| `period_refund` | `sum(refund)` | 期次-部门-顾问退款金额 |
| `period_pmit` | `sum(pmit)` | 期次-部门-顾问净收金额 |

## 9. 可复用 SQL 模式

- 部门任职期过滤：先从组织链提取 `begin_time/end_time`，再用交易时间筛选财务流水。
- 推荐员工关联：使用 `email_prefix` 关联组织链和财务流水，优先于姓名关联。
- 财务流水期次：按 `trade_time` 的周五规则推导 `qici`。
- 调课调班处理：对 `trade_type = '调课调班'` 按 `name + user_id1` 汇总，排除金额为 0 后保留第一条。
- 正常订单处理：对 `trade_type = '正常订单'` 按订单和顾问明细维度汇总。
- 部门内排名：使用 `row_number()`，按净收降序排序，姓名作为稳定兜底排序。
- 追赶上一名差值：使用 `lag(pmit)` 或 `lag(period_pmit)`，第一名差值设为 0。

## 10. 待确认事项

- `end_time` 对在职员工是否可能为空需确认；若为空，当前 `dd_0.trade_time <= ot.end_time` 会过滤掉该员工流水。
- `temp_table.dingxi01_jiagou_zx.employee_email_name = rd.name` 仍使用姓名关联，姓名唯一性需确认。
- `dept` 仅派生为西安/郑州/未知，若后续有其他城市或部门，需补充 CASE。
- `promit`、`pmit` 字段名疑似 `profit`/净额拼写变体，保留原 SQL 命名，展示命名需确认。
- 当前最终结果不输出 `trade_status`、`grade_list`、`subject/sub`，与旧版输出不同；若看板仍需要这些字段，需要在 `base_result` 和排名层补回。
- 当前排名使用 `row_number()`，不允许并列；如果业务希望并列同名次，应改为 `rank()` 或 `dense_rank()`。
