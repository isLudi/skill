# 精品班初三整周期售卖科目占比模板

## 1. 定位

- 业务域：`market_consultant`
- 模板编号：M3
- 默认输出：整周期汇总，不按天拆分。
- 证据 SQL：`resources/raw_sql/market_jingpin_chusan_subject_share_whole_period_20260718.sql`
- 历史验证工作簿：`runtime/market_subject_share/精品班初三售卖科目占比_20250901_20251130_整数口径.xlsx`

## 2. QuerySpec 骨架

| 槽位 | 取值/要求 |
|---|---|
| `domain` | `market_consultant` |
| `intent` | 按渠道组查看整周期售卖科目数和科目占比 |
| `time_range` | `day >= <start> and day < <end_exclusive>` |
| `calculation_grain` | `channel_group + top_order_number + course_subject` |
| `output_grain` | `channel_group + sale_subject` |
| `business_scope` | 精品班、初三、市场顾问归属 |
| `join_path` | 订单归因、财务交易、退款/调课调班、渠道与线索归因的多阶段人工 SQL |

## 3. 整数售卖科目口径

1. 先按 `channel_group + top_order_number + course_subject` 汇总净售卖金额。
2. 净售卖金额 `> 0` 时，该订单—科目计 1 个售卖科目。
3. 再按 `channel_group + sale_subject` 汇总整数计数。
4. `total_sale_subject_count` 是同一渠道组内各科整数计数之和。

不要复用用户/科目金额分摊模板中的 `>=1000` 阈值；该阈值会把 99 元渠道错误过滤为 0。

## 4. 渠道分组

```text
曹忆ip99元 / 曹忆IP99元 -> 精品班曹忆ip99元
其他来源                  -> 精品班其他渠道
```

这是本模板的专用分组，不替代市场顾问全局渠道 CASE。

## 5. 时间与输出粒度

- 时间使用左闭右开，例如 2025-09-01 至 2025-11-30 写为 `day >= '2025-09-01' and day < '2025-12-01'`。
- 默认整周期聚合；除非用户明确要求逐日明细，不增加 `sale_date` 维度。
- 原始 SQL 保留行级 `subject_share` 便于历史对照，但下游 BI/Excel 应使用 `sum(subject_sale_count) / sum(total_sale_subject_count)` 或渠道总数重算，不对行级比率求和/平均。

## 6. 已验证样例

2025-09-01 至 2025-11-30：

- 精品班曹忆 ip99 元组为 0。
- 精品班其他渠道总售卖科目数 4,956：数学 1,518、英语 1,096、化学 1,076、物理 727、语文 539。
- 最终为 2 个渠道组 × 5 个科目，共 10 行。

## 7. 复用风险

- 订单、退款、调课调班和课程科目均会改变净售卖金额；不能只从订单正向流水计数。
- 同一订单同一科目必须先去重；直接数明细行会放大。
- 若改变年级、学部或渠道分组，必须重新检查科目枚举和空值。
- 这是多表人工 SQL，当前不允许自动编译。
