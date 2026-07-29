# 精品班初三售卖科目占比指标

## 1. 适用 SQL

`resources/raw_sql/market_jingpin_chusan_subject_share_whole_period_20260718.sql`

## 2. 计算粒度与输出粒度

```text
calculation_grain = channel_group + top_order_number + course_subject
output_grain      = channel_group + sale_subject
```

## 3. 指标定义

| 字段 | 定义 | 聚合规则 |
|---|---|---|
| `subject_sale_count` | 订单—科目净售卖金额 `>0` 的整数计数 | 可 sum |
| `total_sale_subject_count` | 渠道组内 `subject_sale_count` 之和 | 每个科目行重复带出；跨科目不要直接 sum |
| `subject_share` | `subject_sale_count / total_sale_subject_count` | 行级展示值，不可 sum/avg；下游按分子/分母重算 |

## 4. 推荐下游公式

```text
售卖科目占比 = sum(subject_sale_count) / 渠道组总售卖科目数
```

若要让总数可跨科目安全求和，应另输出只在每个渠道组第一行取值的 `total_sale_subject_count_once`，或在 BI 中单独计算渠道组分母。

## 5. 状态

该指标依赖多表净额和订单—科目去重，语义契约保留人工 SQL 门禁，不允许单表自动编译。
