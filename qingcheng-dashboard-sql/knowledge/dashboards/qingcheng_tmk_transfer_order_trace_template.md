# 青橙 TMK 转移、承接与订单链路模板

## 1. 定位

- 业务域：`qingcheng`
- 模板编号：Q2
- 用途：从 TMK/规划系统潜客追踪到转移后的正常线索，补期次、年级、过程渠道、TMK 顾问直属上级、当前承接顾问、成交线索标记和订单金额。
- 当前数据中心 SQL：`resources/raw_sql/data_center_qingcheng_3180.sql`
- 历史追溯 SQL：`resources/raw_sql/qingcheng_tmk_transfer_order_trace_20260718.sql`
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
  --> 员工维表按 TMK 顾问邮箱前缀补直属上级 xiaozu
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
5. 员工维表使用 `current_timestamp - interval '1' day` 的 `dt`；不得直接套用 TMK 当日小时快照日期，因为员工维表通常为 T-1 分区。
6. SEC 范围；如果改为其他团队，必须重新确认架构字段与来源范围。
7. 生产数据中心模型不加结果上限；临时查询或下载大结果仍需走受控取数流程。

## 5. 当前最终输出

- 粒度与主键：一行一个 `transfer_lead_id`；`lead_count=1`，可按任意看板维度求和得到线索量。
- TMK 与渠道：`tmk_consultant_name`、`xiaozu`、`lead_channel`、`channel_map_1`（一级渠道）、`channel_map_2`（二级渠道）、`raw_rule_name`、`tmk_assign_time` 及 TMK 组织字段。
- 承接信息：`first_receiver_name`、`current_consultant_name`、`current_consultant_source`、`first_receiver_department`。
- 成交与金额：`deal_lead_count`、成交年级/科目/主讲、`deal_amount`、`refund_amount`、`net_amount`、业绩顾问及匹配订单数。
- 辅助字段：期次、分配日、用户/潜客 ID、年级来源和转移前后购买意向。

`channel_map_1`、`channel_map_2` 复用 current model `2064`“青橙-过程数据”的已确认过程渠道契约：

- `qingcheng:dimension:process_channel_level_1`
- `qingcheng:dimension:process_channel_level_2`

TMK 特殊二级渠道先按规则名与潜客购买意向识别 `武汉图书`、`西安图书`、`公域学霸`、`抖音正价退费`、`SEC招生退费`、`SEC首期掉海`、`SEC未加好友`，再使用与 model `2064` 相同的一级渠道归并规则。

## 6. 成交线索与金额

- `deal_lead_count`：当前转移线索只要归因后的 `has_deal=1` 就记 1，否则记 0；由于最终粒度是一行一个 `transfer_lead_id`，按维度求和即为成交线索数/析出数。
- `matched_order_count`：用于观察命中的订单条数，不可替代成交线索数。
- `deal_amount`、`refund_amount`、`net_amount`：未命中订单时保持空值，不用 0 掩盖下游尚无订单记录。
- 看板比率必须分别汇总 `lead_count`、`deal_lead_count`、`net_amount` 后再相除，禁止汇总或平均行级比率。

## 7. 最终输出精简

下列诊断、快照或内部归因字段仍可在 CTE 内参与计算，但不再从最终 `select` 输出：

| 已删除字段 | 中文含义 |
|---|---|
| `transfer_lead_create_time` | 转移后正常线索的创建时间；当前链路中为预留空字段 |
| `transfer_lead_period_name` | 转移后正常线索所属期次；当前链路中为预留空字段 |
| `lead_snapshot_key` | 正常线索快照分区键；当前链路中为预留空字段 |
| `app_snapshot_key` | 潜客小时宽表使用的 `dt+hour` 快照键 |
| `private_snapshot_key` | 私海/当前承接截面使用的 `dt+hour` 快照键 |
| `finance_snapshot_key` | 订单归因表使用的 `dt+hour` 快照键 |
| `qici_source` | 期次取值来源标记 |
| `deal_attribution_type` | 订单命中采用的归因类型 |
| `deal_time_relation` | 订单交易时间相对首次承接时间的关系 |
| `transfer_deal_status` | 转移线索是否成交的文本标记；由数值字段 `deal_lead_count` 替代 |
| `current_private_is_active` | 当前私海候选记录是否仍处于有效状态 |
| `private_history_count` | 该线索私海分配历史记录数 |
| `first_receiver_time` | 首次承接时间 |
| `current_private_assign_time` | 当前私海候选记录的分配时间 |
| `current_private_candidate` | 按当前私海排序选出的候选顾问姓名 |

## 8. 当前承接与历史承接

- 当前模板使用 `dm_crm_lead_cost_gmv_communication_learn_full_link_df` 最新截面中的承接顾问。
- 若需要“首次承接/转手历史”，按已确认 Join 契约另接 `service_dw.dwd_crm_assign_private_detail_hf`，并按 `assign_time + private_sea_id` 去重；不能直接 join 私海历史明细。

## 9. 校验顺序

1. 潜客数与正常转移线索数。
2. `previous_model_id` 回连覆盖率和重复率。
3. 潜客小时宽表、当前承接截面、期次截面、业财表各阶段命中率。
4. 订单 join 前后转移线索数守恒。
5. 校验 `sum(deal_lead_count)` 不大于 `sum(lead_count)`，且每条线索的两个计数字段分别只能为 0/1 与 1。
6. 员工维表按 `email_prefix` 去重后必须一人一行；新增 Join 前后 `transfer_lead_id` 数、订单数和金额必须守恒。
7. `tmk_consultant_name is not null and xiaozu is null` 单独校验；维表未匹配不得通过 inner join 删除原线索。
8. 对照 current model `2064` 的规则样本，逐项核对 `channel_map_1/channel_map_2`，不得在 TMK 明细中维护第二套渠道归因。

历史工作簿样本较小；扩大期次范围时仍须复核重复和覆盖。

## 10. Model 3180 架构字段规则

- 来源：`finance_dw.dim_finance_employee_df.leader_employee_email_name` 输出为 `xiaozu`。
- 关联：潜客宽表 `employee_email_prefix = employee_org.email_prefix`，姓名只用于覆盖校验，不作为生产 Join key。
- 员工范围：`first_level_department_name='H业务线' and is_main_job=1`。
- 去重：按邮箱前缀分组，优先在职、最新入职日和较大工号，只保留 `row_number()=1`。
- 保留范围：使用 `left join`；原始 TMK 顾问为空时 `xiaozu` 也可为空，不影响线索、订单和金额。
