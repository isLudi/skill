# 顾问部门任职期销售统计（20260424期）

## 1. 来源

原始 SQL：`resources/raw_sql/consultant_sales_department_tenure_period_20260424.sql`

入库时间：2026-05-08

来源：用户在对话中提供，标题注释为“伙伴在部门开始时间”。

## 2. 查询目标

用于统计 `20260424期` 市场顾问在指定部门任职时间范围内产生的销售业绩流水。

该 SQL 是 `consultant_sales_department_tenure.sql` 的期次过滤版本，继承同一套底层业务逻辑：

- 从 `dw.dim_employee_chain` 获取顾问在 `高途-H业务线-市场部-市场顾问部` 路径下的部门任职起止时间。
- 从 `finance_dw.app_finance_performance_extend_details_hf` 抽取财务业绩流水，按交易时间推导 `qici`。
- 只保留 `trade_time` 落在顾问部门任职起止时间内的流水。
- 正常订单和调课调班分开处理，调课调班按 `name + user_id1` 汇总去重。
- 关联 `temp_table.dingxi01_jiagou_zx` 补充小组、经理和西安/郑州归属。
- 最终按顾问、支付/退款状态、小组、经理、城市部门、年级和交易日期汇总净额 `pmit`。

与通用版本的差异：

```sql
where qici = '20260424期'
```

## 3. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `dw.dim_employee_chain` | `org_t` 来源表 | 员工组织链，获取顾问在市场顾问部路径下的部门任职起止时间 |
| `finance_dw.app_finance_performance_extend_details_hf` | `dd_0` 来源表 | 财务业绩扩展明细，提供订单、交易、顾问、课程、金额和期次计算字段 |
| `temp_table.dingxi01_jiagou_zx` | `zz` | 员工专项架构映射表，补充小组、经理和部门归属 |

## 4. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `org_t` | 提取顾问在目标组织路径下的最早开始时间和最晚结束时间 | `dep_path`, `email_prefix`, `name`, `begin_time`, `end_time` |
| `dd_0` | 从财务业绩流水抽取订单/退款明细，并按 `trade_time` 推导期次 | `qici`, `name`, `user_id1`, `trade_type`, `trade_status`, `price`, `trade_time` |
| `dd` | 将财务流水按顾问姓名与组织链关联，并限制 `trade_time` 在部门任职起止时间内 | `name`, `trade_time`, `begin_time`, `end_time` |
| `gmv_t` | 处理 `trade_type = '调课调班'`，按 `name + user_id1` 汇总金额并取第一条非 0 记录 | `name_total_price`, `dup_rn` |
| `gmv_z` | 处理 `trade_type = '正常订单'`，按订单、用户、顾问、期次、课程维度汇总金额 | `name_total_price` |
| `rd` | 合并正常订单和调课调班结果 | `qici`, `name`, `trade_status`, `name_total_price` |
| `rd_0` | 关联专项架构，计算支付/退款状态、城市归属、收入、退款、净额、科目数 | `trade_status`, `dept`, `income`, `refund`, `promit`, `sub` |
| final select | 过滤 `20260424期` 并输出顾问-日期-年级-架构粒度净额 | `pmit` |

## 5. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| `dd_0` | `org_t ot` | `ot.name = dd_0.name` | left join + where 限制 | 使用员工姓名匹配组织链，并通过 `trade_time between begin_time and end_time` 限定在部门任职期内 |
| `rd` | `temp_table.dingxi01_jiagou_zx zz` | `zz.employee_email_name = rd.name` | left join | 补充 `xiaozu`、`jingli` 和 `department`，再派生 `dept` |

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
```

底层期次范围：

```sql
qici >= '20260403期'
```

最终输出期次：

```sql
qici = '20260424期'
```

部门任职时间范围：

```sql
dd_0.trade_time >= ot.begin_time
and dd_0.trade_time <= ot.end_time
```

## 7. group by 维度

最终输出维度：

- `qici`
- `name`
- `trade_status`
- `xiaozu`
- `jingli`
- `dept`
- `grade_list`
- `trade_date`
- `years`
- `quarter`
- `month`

## 8. 聚合指标

| 指标名 | SQL 表达式 | 口径说明 | 状态 |
|---|---|---|---|
| `name_total_price` | 正常订单：`sum(price)`；调课调班：`round(sum(price) over (partition by name, user_id1), 3)` | 顾问-订单或顾问-用户维度的业绩流水金额 | 继承通用版本 |
| `income` | `sum(case when name_total_price >= 0 then name_total_price else 0 end)` | 正向流水金额，当前最终未输出 | 继承通用版本 |
| `refund` | `sum(case when name_total_price < 0 then abs(name_total_price) else 0 end)` | 退款流水金额，当前最终未输出 | 继承通用版本 |
| `promit` | `sum(name_total_price)` | 正负流水合计净额，原 SQL 字段名保留 | 继承通用版本，字段命名需确认 |
| `sub` | `count(distinct case when subject not in ('选科志愿', '定制方案') then subject end)` | 排除指定科目后的科目数，当前最终未输出 | 继承通用版本 |
| `pmit` | `sum(promit)` | 最终输出净额 | 继承通用版本 |

## 9. 待确认事项

- 该 SQL 与 `consultant_sales_department_tenure.sql` 仅差异在最终 `qici = '20260424期'` 过滤，底层口径未改变。
- `org_t` 使用 `name` 关联财务流水 `employee_email_name as name`，姓名可能不唯一；如可用 `email_prefix`，建议后续确认是否改为 `email_prefix` 关联。
- `end_time` 对在职员工是否可能为空需确认；若为空，当前 `dd_0.trade_time <= ot.end_time` 会过滤掉该员工流水。
- 财务流水只限定了 `employee_first_level_department_name` 和 `employee_second_level_department_name`，未限定 `employee_third_level_department_name = '市场顾问部'`；是否需要补充需确认。
- 课程部门字段被选出并进入聚合，但未对 `course_first_level_department_name`、`course_second_level_department_name` 做过滤；是否需要课程范围限定需确认。
- `promit`、`pmit` 字段名疑似 `profit`/净额拼写变体，保留原 SQL 命名，展示命名需确认。
