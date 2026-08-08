# 馒头订单明细模板渠道归因与执行计划优化

## 适用范围

- 业务域：`market_consultant`
- 平台来源：模板取数
- 模板：`馒头_订单明细_支付时间`（ID `8735`）与 `馒头_订单明细_流水时间`（ID `8948`）
- 域归属：两个馒头模板永久属于 `market_consultant`，渠道 CASE 或暑期期次盘点时无需再次声明
- stable raw SQL：[`template_query_market_mantou_order_detail_pay_time.sql`](../../resources/raw_sql/template_query_market_mantou_order_detail_pay_time.sql)、[`template_query_market_mantou_order_detail_trade_time.sql`](../../resources/raw_sql/template_query_market_mantou_order_detail_trade_time.sql)
- 当前 SQL SHA-256：支付时间 `8c98bc59e61535395be51a77dd78b6a5637ec29ce56fba7a7e32a7104c13fc48`；流水时间 `79e98bd31a718e383adb97b238abd1b9527a1f5a4282b26aa8d136172694c84a`

支付时间模板按 `top_paid_time`、流水时间模板按 `trade_time` 派生 `day`，两者都使用半开区间参数：

```sql
where day >= ${day:1}
  and day < ${day:2}
```

## 2026-08-08 当前渠道融合

- 两个模板都从去重后的同一份全链路线索源计算 0808 共享渠道 CASE，完整保留 175 条规则及原始 first-match 顺序。
- 为避免超长 CASE 编译和重复扫描，175 条规则按连续顺序拆为 5 组、每组 35 条，通过 `UNION ALL` 和 `min_by(channel, rule_group)` 选择最早命中组，再以无碰撞长度前缀键回连订单主链。
- 两个模板原有的 40 条 `rule_name` 分类各保留两处，并把 `channel_0808` 作为优先输入；共享 CASE 未命中时才回退原分类，避免机械替换丢失模板特有渠道。
- 发布后真实查询：支付时间 query `386603` 返回 141 行、93 秒；流水时间 query `386605` 返回 243 行、66 秒，均为 `SUCCESS`。两个模板均按原 ID 发布并回读相同 SQL 哈希，已有申请关系不变。

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

## 历史 stage 修复及当前保留结构

当前发布版继续保留核算渠道映射，并把用户与科目统计改成窗口计算：

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

## 历史验证证据

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
5. 两个模板不只是日期字段不同；维护时还要检查核算渠道映射和 `re_lc` 阈值差异，不能直接整段互相覆盖。
6. 每次共享渠道 CASE 更新都必须把 `8735/8948` 一并做规则顺序审计、原 ID 发布、哈希回读和真实查询验收。
