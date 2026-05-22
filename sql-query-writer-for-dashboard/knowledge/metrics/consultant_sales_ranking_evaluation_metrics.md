# 顾问销售评优指标

## 1. 中文名称

顾问销售评优指标集合

## 2. 指标定义

指标来自 `resources/raw_sql/consultant_sales_ranking_evaluation.sql`。该 SQL 通过财务业绩流水和评优架构人产临时表计算顾问销售评优指标，支持期次、月度、季度、半年四种聚合周期。

## 3. SQL 表达式

| 指标名 | SQL 表达式 | 说明 |
|---|---|---|
| `name_total_price` | 正常订单：`sum(price)`；调课调班：`round(sum(price) over (partition by name, user_id1), 3)` | 顾问-用户或订单维度的销售流水金额 |
| `pt` | `sum(name_total_price)` | 净收，正负流水合计 |
| `inc` | `sum(case when name_total_price > 0 then name_total_price else 0 end)` | 总营收，只计正向流水 |
| `ref` | `sum(case when name_total_price < 0 then name_total_price else 0 end)` | 退款金额，负数 |
| `renchan` | `cast(pg.renchan as decimal)`，跨周期时 `sum(renchan)` | 人产分母，业务含义待确认 |
| `roi` | `round(coalesce(pt / renchan, 0), 4)` 或 `round(coalesce(sum(pt) / sum(renchan), 0), 4)` | 净收 / 人产 |
| `refd` | `round(coalesce(-ref / nullif(inc, 0), 0), 4)` 或周期聚合版本 | 退费率，退款绝对值 / 总营收 |
| `ceshi` | `case when channel like '%抖音私域%' then 10 else 0 end` | 测试渠道过程标记 |
| `rank_in_roi` | `rank() over (partition by 周期 order by roi desc)` | 周期内 ROI 排名 |
| `rank_in_ref` | `row_number() over (partition by 周期 order by case when inc > 0 then 1 else 2 end, case when inc > 0 then refd else null end, case when inc = 0 and ref = 0 then 1 else 2 end, case when inc = 0 and ref < 0 then abs(ref) else null end)` | 周期内退费排名 |
| `rank_position_roi` | `round(rank_in_roi * 1.0 / nullif(count(*) over (partition by 周期), 0), 5)` | ROI 排名位置百分比 |
| `rank_position_ref` | `round(rank_in_ref * 1.0 / nullif(count(*) over (partition by 周期), 0), 5)` | 退费排名位置百分比 |
| `cs_channel_rank` | `case when channel like '%抖音私域%' or channel like '%抖音私信%' then 10 else 0 end` | 抖音私域/私信渠道标记 |
| `cs_80_rank` | `case when (channel like '%抖音私域%' or channel like '%抖音私信%') and roi >= 0.8 then 2 else 0 end` | 抖音私域/私信渠道 ROI 达到 0.8 的标记 |

## 4. 适用表

- `finance_dw.app_finance_performance_extend_details_hf`
- `temp_table.dingxi01_pingyou_jg`

## 5. 分母/分子口径

- ROI 分子：`pt`，即净收。
- ROI 分母：`renchan`，来自评优临时表。
- 退费率分子：`-ref`，即退款金额绝对值。
- 退费率分母：`inc`，即总营收。
- 排名分母：同一周期内参与评优的顾问数，来自 `count(*) over (partition by 周期)`。

## 6. 时间口径

财务流水分区：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
```

评优期次范围：

```sql
qici >= '20260320期'
```

周期转换：

- 期次：直接使用 `qici`。
- 月度：`substring(qici, 1, 6)`，原 SQL 命名为 `moth`。
- 季度：按 `substring(qici, 1, 6)` 映射到 `YYYYQn`。
- 半年：4-9 月归上半年，10-12 月归当年下半年，1-3 月归上一年下半年。

## 7. 范围限定

财务流水：

```sql
employee_first_level_department_name = 'H业务线'
and employee_second_level_department_name = '市场部'
and employee_third_level_department_name = '市场顾问部'
```

评优临时表：

```sql
pg.zaizhi = '1'
and pg.is_emp = '是'
```

## 8. 待人工确认

- `renchan` 是人产目标、产能还是分母权重需业务确认。
- `renchan` 在月度、季度、半年聚合时直接 `sum` 是否符合评优口径需确认。
- 调课调班按 `name + user_id1` 去重是否覆盖所有退款/调班场景需确认。
- `pt`、`inc`、`ref` 是否都应使用 `price` 而不是 `real_price_0` 或 `transfer_price` 需确认。
- 该指标集合与 `market_consultant_conversion_metrics.md` 均涉及顾问销售表现，但本指标集合以财务流水评优排名为主，不直接替代转化看板 GMV 口径。
