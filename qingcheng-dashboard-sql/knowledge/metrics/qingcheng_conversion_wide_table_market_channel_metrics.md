# 青橙转化宽表-市场渠道指标

## 1. 来源

`resources/raw_sql/qingcheng_conversion_wide_table_market_channel_20260611.sql`

适用看板：`knowledge/dashboards/qingcheng_conversion_wide_table_market_channel_20260611.md`

## 2. 指标计算粒度

该 SQL 分两层计算：

1. `data` / `data_with_process`：线索明细层，来自 `bdg_ba` 宽表，补充 `is_f_call`。
2. `zhuanhua`：聚合层，按 `period_name + channel_map + lead_purchase_intention_level2_category_name + depart_1 + dept_name + depart + rule_name` 汇总。

最终 SELECT 再补 `channel_1`（渠道大类）、`s_lead`（S 级线索）、`podan`（破单标记）。

输出粒度：**期次-渠道-年级-部门-规则**，不是线索明细。

## 3. 线索量指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `lead_count` | `sum(lead_count)` | 线索总量（来自宽表原始字段） | 已从 SQL 入库，字段含义待表结构确认 |
| `valid_lead_count` | `sum(valid_lead_count)` | 有效线索量（来自宽表原始字段） | 已从 SQL 入库，有效线索定义待表结构确认 |
| `can_renew_ds_count_a` | `sum(valid_lead_count)` | 可续报 DS 数，与 `valid_lead_count` 同值 | 已从 SQL 入库，DS 含义待人工确认 |
| `first_call_in_24h` | `sum(first_call_in_24h)` | 分配后 24 小时内完成首次外呼的线索数 | 已从 SQL 入库，口径：`date_diff('hour', section_assign_time, first_call_time) between 0 and 24 and valid_lead_count > 0` |
| `is_f_call` | `sum(is_f_call)` | 有 F 类外呼记录（来自任务处理表的 call_answer_lead_count）的线索数 | 已从 SQL 入库 |
| `is_friend_lead` | `sum(is_friend_lead)` | 加微线索数：valid_lead_count=1 时取 friend_lead_count，否则 0 | 已从 SQL 入库，friend_lead_count 字段含义待表结构确认 |
| `s_lead` | `case when can_renew_ds_count_a >= 5 then can_renew_ds_count_a else 0 end` | S 级线索：可续报 DS >= 5 时返回 DS 数，否则 0 | 已从 SQL 入库，5 的阈值来源待确认 |

## 4. 支付用户指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `pay_users` | `sum(conversion_lead_count)` | 支付用户数（全部期次） | 已从 SQL 入库 |
| `pay_users_on_period` | `sum(same_lead_period_conversion_lead_count)` | 当期支付用户数 | 已从 SQL 入库 |
| `pay_users_not_on_period` | `sum(conversion_lead_count - same_lead_period_conversion_lead_count)` | 非当期支付用户数 | 已从 SQL 入库 |

## 5. 支付科目指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `pay_user_subs` | `sum(subject_count)` | 支付科目数（全部期次） | 已从 SQL 入库 |
| `pay_user_subs_on_period` | `sum(same_lead_period_subject_count)` | 当期支付科目数 | 已从 SQL 入库 |
| `pay_user_subs_not_on_period` | `sum(subject_count - same_lead_period_subject_count)` | 非当期支付科目数 | 已从 SQL 入库 |
| `pay_user_subs_joint` | `sum(lb_subject_count)` | 联报科目数（lb = 联报） | 已从 SQL 入库 |
| `pay_user_subs_joint_onp` | `sum(same_lead_period_lb_subject_count)` | 当期联报科目数 | 已从 SQL 入库 |
| `pay_user_subs_joint_nonp` | `sum(lb_subject_count - same_lead_period_lb_subject_count)` | 非当期联报科目数 | 已从 SQL 入库 |

## 6. 收入和退款指标

所有收入/退款指标在聚合时除以 100（分转元），原始 `income_amount`、`refund_amount` 单位为分。

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `trade_income` | `sum(income_amount / 100)` | 交易收入（元），全部期次 | 已从 SQL 入库 |
| `trade_refund` | `sum((in_pay_period_refund_amount + non_pay_period_refund_amount) / 100)` | 交易退款（元），含当期退款+非当期退款 | 已从 SQL 入库 |
| `trade_profit` | `sum((income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount) / 100)` | 交易净营收（元）= 收入 - 当期退款 - 非当期退款 | 已从 SQL 入库 |
| `xb_trade_income` | `sum(same_lead_period_income_amount / 100)` | 当期收入（元），xb = 续报/当期 | 已从 SQL 入库，xb 前缀含义待确认 |
| `xb_trade_profit` | `sum((same_lead_period_income_amount - same_lead_period_refund_amount) / 100)` | 当期净营收（元） | 已从 SQL 入库 |
| `kk_trade_income` | `sum((income_amount - same_lead_period_income_amount) / 100)` | 跨期收入（元），kk = 跨期/阔课 | 已从 SQL 入库，kk 前缀含义待确认 |
| `pre_refund` | `sum(non_pay_period_refund_amount / 100)` | 课前退款（元），取非当期退款金额 | 已从 SQL 入库，"课前"定义待确认 |

## 7. 破单指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `podan` | `case when can_renew_ds_count_a >= 5 and trade_profit > 0 then 1 else 0 end` | 破单标记：可续报 DS >= 5 且有正向净营收时为 1 | 已从 SQL 入库，阈值和条件待确认 |

## 8. 未使用的字段

以下字段在 `data` CTE 中做了 nvl 处理，但在 `zhuanhua` 聚合和最终 SELECT 中未使用：

| 字段 | 备注 |
|---|---|
| `order_count` | 订单数，nvl 后未聚合 |
| `same_lead_period_order_count` | 当期订单数，nvl 后未聚合 |
| `jp_cross_department_refund_amount` | 跨部门退款金额，nvl 后未聚合 |

这些字段是否为冗余字段、或原计划使用但暂未启用，待人工确认。

## 9. 与青橙转化 raw 指标的差异

| 维度 | 本看板（宽表-市场渠道） | 青橙转化 raw |
|---|---|---|
| 渠道体系 | 中台市场渠道 CASE WHEN（100+ 分支），基于 flow_pool_name/department/sku/source_manager 等多字段 | rule_name 简单模糊匹配 + channel_name_1/2 |
| 渠道粒度 | 单一 `channel_map` + 临时表补 `channel_1` | 两级渠道 `channel_map_1` + `channel_map_2` + 最终 `channel_1` 归类 |
| 年级来源 | rule_name 匹配初二/初三/高一/高二/高三，兜底 lead_purchase_intention_level2_category_name | 同 |
| 收入口径 | 直接从宽表取 income_amount/100，退款含 in_pay + non_pay | 从订单业绩表 dws_crm_order_lead_attribute 取，income_amount/100，退款含 pay + non_pay |
| 当期判断 | 使用 `same_lead_period_*` 系列字段（宽表已预计算） | 使用 `dd.qici0 = dd.period` 自行判断 |
| 破单 | `can_renew_ds_count_a >= 5 and trade_profit > 0` | `promit > 0`（净营收 > 0） |
| 线索成本 | 无 | 硬编码：亚飞IP=120，武汉图书=20，抖音私信=130，进校=70 |
| 退款用户 | 无 | `refund > 500` 的用户数 |
| 成单周期 | 无 | `sum(sc)` 聚合 |

**不得将本看板的渠道映射套用到青橙转化 raw，反之亦然。** 两个看板的渠道体系、数据源、指标口径均有差异。

## 10. 待确认事项

- `same_lead_period_*` 系列字段的"当期"定义：是基于线索期次还是交易期次，待表结构确认。
- `lb_subject_count` 中 `lb`（联报）的判定逻辑待确认。
- `non_pay_period_refund_amount` 是否等同于"课前退款"待确认（当前 SQL 中命名为 `pre_refund`）。
- `can_renew_ds_count_a` 与 `valid_lead_count` 同值，为何保留两个相同指标待确认。
- `jp_cross_department_refund_amount` 未参与聚合，是否为重要遗漏待确认。
- `s_lead` 阈值 5 的来源和适用期次范围待确认。
- `podan` 定义为 `can_renew_ds_count_a >= 5` 而非基于支付用户数，此口径与转化 raw 的 `podan = promit > 0` 完全不同，需确认业务含义。
