# 退费科目产品数据集

## 状态

该数据集是市场顾问-用户画像分析看板退费模块中“不同科目退费占比”“不同产品退费占比”“不同年级退费占比”的当前入口。

## 当前入口

- 统一看板文档：`knowledge/dashboards/market_channel_conversion_profile.md`
- 当前 SQL：`resources/raw_sql/data_center_market_2349_20260705.sql`
- 旧口径 SQL 已清理；当前只保留数据中心 2349 的 20260705 版本。

## 调用规则

涉及市场渠道用户画像分析中的科目、产品、年级退款金额结构占比时，优先读取当前 SQL。涉及 GMV 退费率、人头退费率、单科/多科退费率分子分母时，读取 `market_channel_conversion_profile.md` 的“多维退费率数据集”章节。

当前 2349 输出长表结构：

- `analysis_type = 'subject'`：不同科目退款金额占比。
- `analysis_type = 'product'`：不同产品退款金额占比。
- `analysis_type = 'grade'`：不同年级退款金额占比。
- `refund_amount`：当前维度退款金额，正数。
- `total_refund_amount`：同一筛选范围内总退款金额。

旧口径中 `refund_total` 保留负数、且前端隐式占比的逻辑已废弃；当前 SQL 不直接输出行级占比字段，新看板指标应使用 `ifnull(sum(${refund_amount}) / sum(${total_refund_amount}), 0)`。
