# 退费科目产品数据集

## 状态

该数据集是市场顾问-用户画像分析看板退费模块中“不同科目退费占比”“不同产品退费占比”“不同年级退费占比”的当前入口。

## 当前入口

- 统一看板文档：`knowledge/dashboards/market_channel_conversion_profile.md`
- 当前 SQL：`resources/raw_sql/data_center_market_2349_refund_amount_share_fixed_20260704.sql`
- 历史 SQL 归档：`resources/raw_sql/refund_subject_product.sql`，仅用于追溯，不作为当前口径。

## 调用规则

涉及市场渠道用户画像分析中的科目、产品、年级退款金额结构占比时，优先读取当前 SQL。涉及 GMV 退费率、人头退费率、单科/多科退费率分子分母时，读取 `market_channel_conversion_profile.md` 的“多维退费率数据集”章节。

当前 2349 输出长表结构：

- `analysis_type = 'subject'`：不同科目退款金额占比。
- `analysis_type = 'product'`：不同产品退款金额占比。
- `analysis_type = 'grade'`：不同年级退款金额占比。
- `refund_amount`：当前维度退款金额，正数。
- `total_refund_amount`：同一筛选范围内总退款金额。
- `refund_amount_ratio`：`refund_amount / total_refund_amount`。

旧口径中 `refund_total` 保留负数、且前端隐式占比的逻辑已废弃；新看板指标应直接使用 `refund_amount_ratio`，或用 `sum(refund_amount) / sum(total_refund_amount)` 重算。
