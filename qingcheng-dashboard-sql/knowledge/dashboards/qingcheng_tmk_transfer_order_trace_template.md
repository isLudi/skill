# 青橙 TMK 转移、承接与订单链路模板

## 1. 定位

- 业务域：`qingcheng`
- 模板编号：Q2
- 用途：从 TMK/规划系统潜客追踪到转移后的正常线索，补期次、年级、渠道、TMK 顾问直属上级、当前承接顾问和订单金额。
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
7. 输出上限；历史明细模板为 `limit 200`，大结果下载需另走受控模板取数流程。

## 5. 输出字段

- TMK 侧：TMK 顾问、`xiaozu`（TMK 顾问的直属上级带数字员工名）、潜客 ID、用户 ID、渠道、线索年级、源规则、源期次。
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
6. 员工维表按 `email_prefix` 去重后必须一人一行；新增 Join 前后 `transfer_lead_id` 数、订单数和金额必须守恒。
7. `tmk_consultant_name is not null and xiaozu is null` 单独校验；维表未匹配不得通过 inner join 删除原线索。

历史工作簿样本较小；扩大期次范围时仍须复核重复和覆盖。

## 9. Model 3180 架构字段规则

- 来源：`finance_dw.dim_finance_employee_df.leader_employee_email_name` 输出为 `xiaozu`。
- 关联：潜客宽表 `employee_email_prefix = employee_org.email_prefix`，姓名只用于覆盖校验，不作为生产 Join key。
- 员工范围：`first_level_department_name='H业务线' and is_main_job=1`。
- 去重：按邮箱前缀分组，优先在职、最新入职日和较大工号，只保留 `row_number()=1`。
- 保留范围：使用 `left join`；原始 TMK 顾问为空时 `xiaozu` 也可为空，不影响线索、订单和金额。
