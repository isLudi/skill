# 青橙 TMK 转移、承接与订单链路模板

## 1. 定位

- 业务域：`qingcheng`
- 模板编号：Q2
- 用途：从 TMK/规划系统潜客追踪到转移后的正常线索，补期次、年级、渠道、当前承接顾问和订单金额。
- 证据 SQL：`resources/raw_sql/qingcheng_tmk_transfer_order_trace_20260718.sql`
- 关联观测台账：`knowledge/sql_patterns/qingcheng_tmk_transfer_latency_observation_log.md`
- 复用已确认 Join：
  - `qingcheng:join:transferred_lead_to_prelead`
  - `qingcheng:join:transferred_lead_to_private_assignment_history`

## 2. QuerySpec 骨架

| 槽位 | 取值/要求 |
|---|---|
| `domain` | `qingcheng` |
| `intent` | TMK 潜客转正常线索、承接顾问与订单追踪 |
| `time_range` | 业务期次日历 + 最小期次；不得默认沿用历史种子 |
| `calculation_grain` | `transfer_lead_id` |
| `output_grain` | 一行一个转移后的正常线索 |
| `business_scope` | 青橙项目部，架构 `dept_2='SEC'` |
| `join_path` | 潜客 DWD -> 正常线索 DWD -> 潜客小时宽表 -> SEC 架构 -> 当前承接截面 -> 期次截面 -> 订单归因 |

## 3. 主链路

```text
dwd_crm_leads_rt(model_type=1 潜客)
  -- normal.previous_model_id = prelead.crm_leads_id -->
dwd_crm_leads_rt(model_type=0 正常线索)
  --> 潜客小时宽表补 TMK 顾问、渠道、期次、年级
  --> 期次架构限定 SEC
  --> 当前线索截面补承接顾问
  --> 线索统计截面补转移后期次
  --> service 订单归因表按 transfer_lead_id 补成交、收入、退款、净额
```

订单必须用转移后的正常 `transfer_lead_id` 关联，不能使用潜客 ID。

## 4. 调用时必须替换的参数

1. `biz_qici_seed`：业务确认的期次中心日及 ±2 天窗口；历史样例列出 2026-07-16 至 2026-08-21。
2. 架构最小期次 `qici >= '20260427期'`。
3. TMK/规划系统 `purchase_intention_name` 枚举。
4. 最新小时表的 `dt/hour` 偏移，确保潜客、承接、期次和订单快照相容。
5. SEC 范围；如果改为其他团队，必须重新确认架构字段与来源范围。
6. 输出上限；历史明细模板为 `limit 200`，大结果下载需另走受控模板取数流程。

## 5. 输出字段

- TMK 侧：TMK 顾问、潜客 ID、用户 ID、渠道、线索年级、源规则、源期次。
- 转移侧：转移后的正常 `lead_id`、转移期次、线索创建时间、当前承接顾问。
- 订单侧：是否有业财回补、成交年级/科目/主讲、收入、退款、净金额。

## 6. 成交状态三态

复用模板必须区分：

| 状态 | 含义 |
|---|---|
| `是` | 业财已命中且 `has_deal=1` |
| `否` | 业财已命中但未满足成交条件 |
| `业财未回补` | 业财表没有目标线索行；不能解释为未成交 |

金额在“业财未回补”时保持空值；不要用 0 掩盖未产出。

## 7. 当前承接与历史承接

- 当前模板使用 `dm_crm_lead_cost_gmv_communication_learn_full_link_df` 最新截面中的承接顾问。
- 若需要“首次承接/转手历史”，按已确认 Join 契约另接 `service_dw.dwd_crm_assign_private_detail_hf`，并按 `assign_time + private_sea_id` 去重；不能直接 join 私海历史明细。

## 8. 校验顺序

1. 潜客数与正常转移线索数。
2. `previous_model_id` 回连覆盖率和重复率。
3. 潜客小时宽表、当前承接截面、期次截面、业财表各阶段命中率。
4. 订单 join 前后转移线索数守恒。
5. 未回补与明确未成交分开统计。

历史工作簿样本较小；扩大期次范围时仍须复核重复和覆盖。
