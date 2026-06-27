# 未使用临时表的 SQL 记录

本文件记录已入库但未使用 `temp_table.*` 的青橙 SQL，避免为了满足目录结构而伪造临时表文档。

| SQL / 看板 | 来源文件 | 结论 | 说明 | 更新时间 |
|---|---|---|---|---|
| 青橙渠道订单明细 raw | `resources/raw_sql/qingcheng_channel_order_detail_raw_20260627.sql` | 未使用青橙临时表 | 仅使用 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 和 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 两张物理表；2026-06-27 模板版新增地域字段，但仍未补接团队/组织临时表 | 2026-06-27 |
