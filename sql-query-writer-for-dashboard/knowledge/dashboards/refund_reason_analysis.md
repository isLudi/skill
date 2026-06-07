# 退费原因分析看板（已合并）

## 状态

该退费看板已合并到 `market_channel_conversion_profile.md`（市场渠道用户画像分析）中维护，不再作为独立看板入口优先调用。

## 新入口

- 统一看板文档：`knowledge/dashboards/market_channel_conversion_profile.md`
- 新多维退费率 SQL：`resources/raw_sql/refund_rate_multidim.sql`
- 历史 SQL 归档：`resources/raw_sql/refund_reason_analysis.sql`

## 调用规则

涉及市场渠道用户画像分析中的退费率、GMV 退费率、人头退费率、单科/多科退费分子分母字段时，优先读取 `market_channel_conversion_profile.md` 的“多维退费率数据集”章节。

历史退费原因 SQL 仍保留在 raw SQL 中，但它依赖 `finance_dw.dwd_finance_order_refund_df.refund_reason` 和订单号回连。当前新多维退费率 SQL 不输出退费原因；如果业务再次要求退费原因分布，需要明确是否使用旧口径或新增退费原因明细数据集，字段和 join 唯一性均待人工确认。
