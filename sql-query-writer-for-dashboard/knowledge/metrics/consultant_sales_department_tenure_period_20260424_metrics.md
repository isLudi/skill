# 顾问部门任职期销售指标（20260424期）

## 1. 中文名称

顾问部门任职期销售指标集合（20260424期）

## 2. 指标定义

指标来自 `resources/raw_sql/data_center_market_2742_20260705.sql`。

该指标集合继承 `consultant_sales_department_tenure_metrics.md` 的全部业务口径，仅在最终输出层限制：

```sql
qici = '20260424期'
```

因此它适用于固定期次 `20260424期` 的顾问任职期销售净额分析。

## 3. SQL 表达式

| 指标名 | SQL 表达式 | 说明 |
|---|---|---|
| `name_total_price` | 正常订单：`sum(price)`；调课调班：`round(sum(price) over (partition by name, user_id1), 3)` | 顾问-订单或顾问-用户维度的业绩流水金额 |
| `income` | `sum(case when name_total_price >= 0 then name_total_price else 0 end)` | 正向销售流水金额，当前最终未输出 |
| `refund` | `sum(case when name_total_price < 0 then abs(name_total_price) else 0 end)` | 退款流水金额，取绝对值，当前最终未输出 |
| `promit` | `sum(name_total_price)` | 正负流水合计净额，原 SQL 字段名保留 |
| `sub` | `count(distinct case when subject not in ('选科志愿', '定制方案') then subject end)` | 排除指定科目后的科目数，当前最终未输出 |
| `pmit` | `sum(promit)` | 最终输出的净额汇总 |

## 4. 适用表

- `finance_dw.app_finance_performance_extend_details_hf`
- `dw.dim_employee_chain`
- `temp_table.dingxi01_jiagou_zx`

## 5. 分母/分子口径

- 本 SQL 不计算比率类指标，无分母。
- `pmit` 分子：`20260424期` 内、且交易时间落在顾问目标部门任职期内的 `name_total_price` 正负合计。
- `income`：只计正向金额。
- `refund`：只计负向金额的绝对值。

## 6. 时间和期次口径

财务流水分区：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
```

员工组织链分区：

```sql
dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
```

底层期次范围：

```sql
qici >= '20260403期'
```

最终输出期次：

```sql
qici = '20260424期'
```

部门任职期过滤：

```sql
dd_0.trade_time >= ot.begin_time
and dd_0.trade_time <= ot.end_time
```

## 7. 范围限定

员工组织链路径：

```sql
array_join(slice(split(path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'
```

财务流水员工部门：

```sql
employee_first_level_department_name = 'H业务线'
and employee_second_level_department_name = '市场部'
```

## 8. 待人工确认

- 该指标集合与通用任职期销售指标集合口径一致，仅新增固定期次过滤。
- `org_t.name = dd_0.name` 的姓名关联唯一性仍需确认。
- `end_time` 为空时是否应视为当前仍在目标部门内需确认。
- 是否需要补充 `employee_third_level_department_name = '市场顾问部'` 需确认。
- 是否需要对课程部门字段增加 `course_first_level_department_name`、`course_second_level_department_name` 范围限定需确认。
- `promit`、`pmit` 命名需确认是否为净额/利润口径。
