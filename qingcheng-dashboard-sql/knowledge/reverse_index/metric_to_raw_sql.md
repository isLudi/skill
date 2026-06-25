# 指标到 raw SQL 反向索引

> 由 `scripts/build_reverse_indexes.py` 自动生成。用于从指标文档快速回到证据 SQL。

| 指标文档 | 来源 raw SQL | 相关表 |
|---|---|---|
| [青橙渠道订单明细指标与派生字段](../metrics/qingcheng_channel_order_detail_metrics.md) | [qingcheng_channel_order_detail_raw_20260613.sql](../../resources/raw_sql/qingcheng_channel_order_detail_raw_20260613.sql) | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` |
| [青橙转化指标](../metrics/qingcheng_conversion_metrics.md) | [qingcheng_conversion_raw_20260615.sql](../../resources/raw_sql/qingcheng_conversion_raw_20260615.sql) | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_1](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_1.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_10](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_10.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_11](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_11.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_12](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_12.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_13](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_13.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_14](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_14.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_15](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_15.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_16](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_16.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_17](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_17.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_18](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_18.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_19](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_19.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_2](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_2.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_20](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_20.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_21](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_21.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_22](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_22.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_3](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_3.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_4](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_4.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_5](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_5.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_6](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_6.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_7](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_7.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_8](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_8.md) | - | - |
| [qingcheng_conversion_wide_table_market_channel_20260611_metric_9](../metrics/qingcheng_conversion_wide_table_market_channel_20260611_metric_9.md) | - | - |
| [青橙转化宽表-市场渠道指标](../metrics/qingcheng_conversion_wide_table_market_channel_metrics.md) | [qingcheng_conversion_wide_table_market_channel_20260611.sql](../../resources/raw_sql/qingcheng_conversion_wide_table_market_channel_20260611.sql) | - |
| [青橙到课指标](../metrics/qingcheng_daoke_metrics.md) | [qingcheng_daoke_raw_20260522.sql](../../resources/raw_sql/qingcheng_daoke_raw_20260522.sql) | - |
| [Qingcheng dashboard metric formulas and SQL linkage](../metrics/qingcheng_dashboard_metric_formula_linkage.md) | `_20260624.sql`<br>[data_center_qingcheng_2064_20260624.sql](../../resources/raw_sql/data_center_qingcheng_2064_20260624.sql)<br>[data_center_qingcheng_2460_20260624.sql](../../resources/raw_sql/data_center_qingcheng_2460_20260624.sql)<br>[data_center_qingcheng_2740_20260624.sql](../../resources/raw_sql/data_center_qingcheng_2740_20260624.sql)<br>[qingcheng_conversion_wide_table_market_channel_20260611.sql](../../resources/raw_sql/qingcheng_conversion_wide_table_market_channel_20260611.sql)<br>... +5 | - |
| [青橙个人转化指标](../metrics/qingcheng_personal_conversion_metrics.md) | [qingcheng_personal_conversion_raw_20260522.sql](../../resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql) | `temp_table.dingxi01_qing_team_jg` |
| [青橙过程数据指标](../metrics/qingcheng_process_data_metrics.md) | [qingcheng_process_data_raw_20260522.sql](../../resources/raw_sql/qingcheng_process_data_raw_20260522.sql) | `service_dw.dm_crm_lead_stats_detail_hf`<br>`temp_table.dingxi01_qing_daoke` |
| [青橙年季月营收指标](../metrics/qingcheng_revenue_year_quarter_month_metrics.md) | [qingcheng_revenue_year_quarter_month_raw_20260522.sql](../../resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql) | - |
| [青橙团队完成度【月】指标](../metrics/qingcheng_team_completion_month_metrics.md) | [qingcheng_team_completion_month_raw_20260522.sql](../../resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql) | - |
| [青橙团队完成度【期】指标](../metrics/qingcheng_team_completion_period_metrics.md) | [qingcheng_team_completion_period_raw_20260522.sql](../../resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql) | `temp_table.dingxi01_qing_qi_moth`<br>`temp_table.dingxi01_qing_team_g_qi`<br>`temp_table.dingxi01_qing_team_goal` |
