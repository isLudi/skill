# 青橙 TMK 转移与订单追踪字段

## 1. 适用 SQL

- 当前生产数据中心 SQL：`resources/raw_sql/data_center_qingcheng_3180.sql`
- 历史追溯 SQL：`resources/raw_sql/qingcheng_tmk_transfer_order_trace_20260718.sql`
- 数据集：`TMK线索转移明细` / model `3180`

## 2. 计算与输出粒度

```text
calculation_grain = transfer_lead_id
output_grain      = transfer_lead_id
```

## 3. 关键字段

| 字段 | 定义 | 聚合规则 |
|---|---|---|
| `lead_count`（线索量） | 每个去重 `transfer_lead_id` 固定计 1 | `sum` |
| `deal_lead_count`（成交线索数/析出数） | 归因后的 `has_deal=1` 计 1，否则计 0；每条线索最多计 1 | `sum` |
| `deal_amount`（成交金额） | 转移后正常线索归因订单的收入金额，分转元后汇总到线索 | `sum`；未命中订单保持空 |
| `refund_amount`（退费金额） | 转移后正常线索归因订单的退款金额，分转元后汇总到线索 | 同上 |
| `net_amount`（净产出） | `deal_amount - refund_amount`，已汇总到线索 | `sum`；未命中订单保持空 |
| `channel_map_1`（一级渠道） | 与 current model `2064` 过程渠道一级归因一致 | 维度 |
| `channel_map_2`（二级渠道） | 与 current model `2064` 过程渠道二级归因一致 | 维度 |
| `current_consultant_name`（线索承接顾问） | 转移后正常线索当前截面承接顾问 | 维度；首次承接需另查私海历史 |

## 4. 看板派生指标

| 指标 | 公式 | 聚合规则 |
|---|---|---|
| 线索析出率 | `sum(deal_lead_count) / nullif(sum(lead_count), 0)` | 比率分子分母分别求和后相除 |
| 全量单效 | `sum(net_amount) / nullif(sum(lead_count), 0)` | 净产出与线索量分别求和后相除 |
| 后转单效 | `sum(net_amount) / nullif(sum(deal_lead_count), 0)` | 净产出与析出数分别求和后相除 |

这里“析出数”与“成交线索数”均指 `sum(deal_lead_count)`。三个指标都必须在看板当前筛选与分组粒度重算，禁止先计算行级值后再求和或平均。分母为 0 时返回空值，由看板展示层决定是否显示为 0。

## 5. Join 契约

- `previous_model_id -> crm_leads_id`：`qingcheng:join:transferred_lead_to_prelead`。
- `transfer_lead_id -> private_assignment.lead_id`：`qingcheng:join:transferred_lead_to_private_assignment_history`，仅用于首次承接/转手历史，必须去重。

## 6. 状态

转移链路 Join、`lead_count`、`deal_lead_count` 和三个派生指标口径已确认；完整 TMK 明细仍是多表人工 SQL，不允许自动编译。一级/二级渠道复用 `qingcheng:dimension:process_channel_level_1/2`，不得另建平行归因规则。
