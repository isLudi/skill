# 青橙 TMK 转移与订单追踪字段

## 1. 适用 SQL

`resources/raw_sql/qingcheng_tmk_transfer_order_trace_20260718.sql`

## 2. 计算与输出粒度

```text
calculation_grain = transfer_lead_id
output_grain      = transfer_lead_id
```

## 3. 关键字段

| 字段 | 定义 | 聚合规则 |
|---|---|---|
| `线索数量` | 每个去重 `transfer_lead_id` 计 1 | 可 sum |
| `转移线索是否成交` | `是 / 否 / 业财未回补` 三态 | 维度，不可将未回补计为否 |
| `成交金额` | 转移后正常线索在业财表的收入金额，分转元 | 业财命中后可 sum；未回补保持空 |
| `退费金额` | 转移后正常线索在业财表的退款金额，分转元 | 同上 |
| `净金额` | 成交金额减退费金额 | 同上 |
| `线索承接顾问` | 转移后正常线索当前截面承接顾问 | 维度；首次承接需另查私海历史 |

## 4. Join 契约

- `previous_model_id -> crm_leads_id`：`qingcheng:join:transferred_lead_to_prelead`。
- `transfer_lead_id -> private_assignment.lead_id`：`qingcheng:join:transferred_lead_to_private_assignment_history`，仅用于首次承接/转手历史，必须去重。

## 5. 状态

转移链路 Join 已确认；完整 TMK 明细仍是多表人工 SQL，不允许自动编译。
