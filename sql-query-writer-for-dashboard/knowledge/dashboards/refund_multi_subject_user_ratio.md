# 多科用户退费占比看板（已合并）

## 状态

该退费看板已合并到 `market_channel_conversion_profile.md`（市场渠道用户画像分析）中维护，不再作为独立看板入口优先调用。

## 新入口

- 统一看板文档：`knowledge/dashboards/market_channel_conversion_profile.md`
- 新多维退费率 SQL：`resources/raw_sql/refund_rate_multidim.sql`
- 历史 SQL 归档：`resources/raw_sql/refund_multi_subject_user_ratio.sql`

## 调用规则

涉及市场渠道用户画像分析中的退费率、GMV 退费率、人头退费率、单科/多科退费分子分母字段时，优先读取 `market_channel_conversion_profile.md` 的“多维退费率数据集”章节。

历史 SQL 仅作为旧口径追溯资料保留。历史 SQL 中按财务流水、分配规则和架构表回连的口径未与新全链路主表口径完全对齐，复用前需人工确认。
