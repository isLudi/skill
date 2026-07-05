# 顾问部门任职期销售指标

## 1. 中文名称

顾问部门任职期销售指标集合

## 2. 指标定义

指标来自 `resources/raw_sql/data_center_market_2727_20260705.sql`。该 SQL 用财务业绩流水计算顾问销售净额，通过员工组织链限制交易时间必须落在顾问位于 `高途-H业务线-市场部-市场顾问部` 的部门任职时间范围内，并输出部门内排名和追赶上一名净收差值。

该指标集合与 `consultant_sales_ranking_evaluation_metrics.md` 均使用 `finance_dw.app_finance_performance_extend_details_hf` 的销售流水，但本集合不计算 ROI、退费率和评优分位。

## 3. 基础金额指标

| 指标名 | SQL 表达式 | 说明 |
|---|---|---|
| `name_total_price` | 正常订单：`sum(price)`；调课调班：`round(sum(price) over (partition by name, user_id1), 3)` | 顾问-订单或顾问-用户维度的业绩流水金额 |
| `income` | `sum(case when name_total_price >= 0 then name_total_price else 0 end)`，再在 `base_result` 中 `sum(income)` | 正向销售流水金额 |
| `refund` | `sum(case when name_total_price < 0 then abs(name_total_price) else 0 end)`，再在 `base_result` 中 `sum(refund)` | 退款流水金额，取绝对值 |
| `promit` | `sum(name_total_price)` | 正负流水合计净额，原 SQL 字段名保留 |
| `pmit` | `sum(promit)` | 日维度最终输出净额 |
| `period_income` | `sum(income)` | 期次-部门-顾问正向销售流水金额 |
| `period_refund` | `sum(refund)` | 期次-部门-顾问退款金额 |
| `period_pmit` | `sum(pmit)` | 期次-部门-顾问净收金额 |

## 4. 排名指标

| 指标名 | SQL 表达式 | 说明 |
|---|---|---|
| `day_dept_period_rank_scope` | `'天-部门-期次'` | 日维度排名范围标签 |
| `day_dept_period_rank_no` | `row_number() over (partition by trade_date, dept, qici order by pmit desc, name)` | 在同一天、同部门、同期次内按日净收降序排名 |
| `day_dept_period_need_pmit_to_previous` | `case when lag(pmit) is null then 0 else lag(pmit) - pmit end` | 日维度追赶上一名所需净收；第一名为 0 |
| `period_dept_rank_scope` | `'期次-部门'` | 期次维度排名范围标签 |
| `period_dept_rank_no` | `row_number() over (partition by qici, dept order by period_pmit desc, name)` | 在同期次、同部门内按期次净收降序排名 |
| `period_dept_need_pmit_to_previous` | `case when lag(period_pmit) is null then 0 else lag(period_pmit) - period_pmit end` | 期次维度追赶上一名所需净收；第一名为 0 |

## 5. 排名规则

当前使用 `row_number()`：

- 不允许并列排名。
- 排序主键为净收降序。
- 净收相同时，按 `name` 升序打散顺序。

示例：

| 顾问 | pmit | 排名 | 需追赶上一名 |
|---|---:|---:|---:|
| A | 10000 | 1 | 0 |
| B | 8000 | 2 | 2000 |
| C | 8000 | 3 | 0 |
| D | 5000 | 4 | 3000 |

说明：B 和 C 净收相同，但 `row_number()` 不并列；C 的上一名 B 净收也是 8000，所以差值为 0。

## 6. 适用表

- `finance_dw.app_finance_performance_extend_details_hf`
- `dw.dim_employee_chain`
- `temp_table.dingxi01_jiagou_zx`

## 7. 分母/分子口径

- 本 SQL 不计算比率类指标，无分母。
- `pmit` 分子：任职期内 `name_total_price` 的正负合计。
- `income`：只计正向金额。
- `refund`：只计负向金额的绝对值。
- `day_dept_period_need_pmit_to_previous`：上一名日净收减当前顾问日净收。
- `period_dept_need_pmit_to_previous`：上一名期次净收减当前顾问期次净收。

## 8. 时间口径

财务流水分区：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
```

员工组织链分区：

```sql
dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
```

期次推导：

```sql
concat(
    date_format(
        date_add(
            'day',
            4,
            date_trunc('week', date_add('day', -1, cast(trade_time as timestamp)))
        ),
        '%Y%m%d'
    ),
    '期'
)
```

部门任职期过滤：

```sql
dd_0.trade_time >= ot.begin_time
and dd_0.trade_time <= ot.end_time
```

## 9. 范围限定

员工组织链路径：

```sql
array_join(slice(split(path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'
```

财务流水员工部门：

```sql
employee_first_level_department_name = 'H业务线'
and employee_second_level_department_name = '市场部'
and employee_third_level_department_name = '市场顾问部'
```

期次范围：

```sql
qici >= '20260403期'
```

## 10. 待人工确认

- `dw.dim_employee_chain` 字段已根据 `E:\2000_work\GAOTU\员工信息表.docx` 补全；主键唯一性和行权限范围仍需确认。
- `end_time` 为空时是否应视为当前仍在部门内需确认。
- `temp_table.dingxi01_jiagou_zx.employee_email_name = rd.name` 仍使用姓名关联，姓名唯一性需确认。
- `dept` 派生逻辑目前只识别西安和郑州。
- `promit`、`pmit` 命名需确认是否为净额/利润口径。
- 当前排名不允许并列；如业务希望并列，需将 `row_number()` 改为 `rank()` 或 `dense_rank()`。
