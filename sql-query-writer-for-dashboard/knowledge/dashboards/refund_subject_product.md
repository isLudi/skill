# 退费科目产品看板（已合并）

## 状态

该退费看板已合并到 `market_channel_conversion_profile.md`（市场渠道用户画像分析）中维护，不再作为独立看板入口优先调用。

## 新入口

- 统一看板文档：`knowledge/dashboards/market_channel_conversion_profile.md`
- 新多维退费率 SQL：`resources/raw_sql/refund_rate_multidim.sql`
- 历史 SQL 归档：`resources/raw_sql/refund_subject_product.sql`

## 调用规则

涉及市场渠道用户画像分析中的退费率、GMV 退费率、人头退费率、单科/多科退费分子分母字段时，优先读取 `market_channel_conversion_profile.md` 的“多维退费率数据集”章节。

历史退费科目产品 SQL 仍保留在 raw SQL 中，但它按财务流水拆分正常订单和调课调班，并输出科目/产品明细。当前新多维退费率 SQL 使用全链路主表 `subject_count` 做科目分层，不输出标准科目和课程产品；如需恢复科目或产品维度，需人工确认是否沿用旧财务流水口径。
