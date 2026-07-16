# 馒头订单明细支付时间模板执行计划优化

## 适用范围

- 业务域：`market_consultant`
- 平台来源：模板取数
- 模板名称：`馒头_订单明细_支付时间`
- 模板 ID：`8735`
- 当前发布版本：2026-07-16 20:01:40
- 当前 raw SQL：[`template_query_market_mantou_order_detail_pay_time_20260716.sql`](../../resources/raw_sql/template_query_market_mantou_order_detail_pay_time_20260716.sql)
- 当前 SQL SHA-256：`3781532fd35d262d615e1cabf9076567b5cbf92764ff7665af3139eed98c6aa0`

本模板按 `top_paid_time` 派生的 `day` 使用半开区间参数：

```sql
where day >= ${day:1}
  and day < ${day:2}
```

## 历史故障

2026-07-16 旧版模板执行失败：

```text
Number of stages in the query (197) exceeds the allowed maximum (130)
```

该故障不是日期格式、日期范围或结果数据量错误。旧版在动态核算渠道链路中新增：

- `cs_keyed`
- `hesuanqudao`
- `hq0_match`
- `hq_match`

随后又让重 CTE `cs` 被主查询、`user_stats`、`subject_stats`、`lianbao_stats` 重复引用。Presto 普通 CTE 不会自动物化，而是可能在每个引用位置重新内联；动态渠道非等值匹配和多层 JOIN 因此被反复展开，最终达到 197 stages。

## 当前修复

当前发布版保留核算渠道映射，只把用户与科目统计改成窗口计算：

```sql
,cs_stats as (
    select
        c.*,
        sum(valid_price) over (
            partition by user_id
        ) as user_t_price,
        count(*) over (
            partition by user_id
        ) * 1.0 as user_count,
        sum(valid_price) over (
            partition by user_id, course_subject
        ) as subject_t_price,
        count(*) over (
            partition by user_id, course_subject
        ) * 1.0 as subject_count
    from cs c
)
```

`count(distinct course_subject)` 仍由单独的 `lianbao_stats` 聚合完成，因此重 CTE `cs` 的引用由四次降为两次。最终查询从 `cs_stats` 输出，不再 JOIN `user_stats` 和 `subject_stats`。

## 验证证据

- 使用原始 Presto 执行。
- 验证日期区间：`2026-07-15` 至 `2026-07-16`。
- SQL 取数 query ID：`1477690051`。
- 执行状态：`Success`。
- 线上回读确认模板状态为 `published`，发布时间为 `2026-07-16 20:01:40`。
- 线上 `sqlDetail` 与验证成功版本逐字节一致。

## 后续维护规则

1. 不要把用户、科目和联报三套统计全部恢复为独立读取 `cs` 的 CTE。
2. 新增渠道映射 JOIN 后，必须统计每个重 CTE 的引用次数；同一个重 CTE 被引用三次及以上时，优先改为窗口计算、条件聚合或一次聚合后复用。
3. 缩短 `${day:1}` 至 `${day:2}` 只能减少扫描数据量，不能解决静态 stage 数超限。
4. `set session use_mark_distinct = false` 不是本模板的主修复路径。旧版只有少量 `DISTINCT`，核心问题是重 CTE 多次内联。
5. 本模板与 `馒头_订单明细_流水时间` 不只是日期字段不同；维护时还要检查核算渠道映射和 `re_lc` 阈值差异，不能直接整段互相覆盖。
