# H业务线二级部门转化指标集合

## 1. 来源

看板文档：`knowledge/dashboards/h_biz_line_department_conversion.md`

原始 SQL：`resources/raw_sql/h_biz_line_department_conversion.sql`

入库时间：2026-05-24

## 2. 指标计算粒度

- 聚合粒度：`period_name + channel_map + rule_name + lead_purchase_intention_level2_category_name + depart_1 + dept_name + depart`
- 最终输出粒度：同上
- 粒度特点：部门级别聚合，非顾问个体级别；无 `employee_email_name` / `jingli` / `zhuguan`

## 3. 线索和有效线索指标

| 指标名 | 字段/表达式 | 单位 | 说明 | 状态 |
|---|---|---|---|---|
| lead_count | `sum(lead_count)` | 个 | 线索数 | 待确认 |
| can_renew_ds_count_a | `sum(valid_lead_count)` | 个 | 有效线索数 | 待确认 |
| valid_lead_count | `sum(valid_lead_count)` | 个 | 有效线索数（与 `can_renew_ds_count_a` 同口径） | 命名重复，待确认 |
| first_call_in_24h | `sum(first_call_in_24h)` | 个 | 24 小时内完成首呼的有效线索数 | 待确认 |
| is_f_call | `sum(is_f_call)` | 个 | 已完成首 call 任务的有效线索数；通过 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf.first_call_status = 3` + `finance_dw.dim_finance_employee_df.account_id` 桥接 | 待确认 |
| is_friend_lead | `sum(is_friend_lead)` | 个 | 有效线索中已加微数 | 待确认 |

## 4. 转化指标

| 指标名 | 字段/表达式 | 单位 | 说明 | 状态 |
|---|---|---|---|---|
| pay_users | `sum(conversion_lead_count)` | 人 | 转化人数 | 待确认 |
| pay_users_on_period | `sum(same_lead_period_conversion_lead_count)` | 人 | 当期线索当期转化人数 | 待确认 |
| pay_users_not_on_period | `sum(conversion_lead_count - same_lead_period_conversion_lead_count)` | 人 | 跨期转化人数 | 待确认 |
| pay_user_subs | `sum(subject_count)` | 人次 | 转化科目人次 | 待确认 |
| pay_user_subs_on_period | `sum(same_lead_period_subject_count)` | 人次 | 当期转化科目人次 | 待确认 |
| pay_user_subs_not_on_period | `sum(subject_count - same_lead_period_subject_count)` | 人次 | 跨期转化科目人次 | 待确认 |
| pay_user_subs_joint | `sum(lb_subject_count)` | 人次 | 联报人次 | 待确认 |
| pay_user_subs_joint_onp | `sum(same_lead_period_lb_subject_count)` | 人次 | 当期联报人次 | 待确认 |
| pay_user_subs_joint_nonp | `sum(lb_subject_count - same_lead_period_lb_subject_count)` | 人次 | 跨期联报人次 | 待确认 |

## 5. 金额指标

所有金额原始单位为**分**，输出时 `/ 100` 转为**元**。

| 指标名 | 字段/表达式 | 单位 | 说明 | 状态 |
|---|---|---|---|---|
| trade_income | `sum(income_amount / 100)` | 元 | 收款金额 | 待确认 |
| trade_refund | `sum(in_pay_period_refund_amount / 100 + non_pay_period_refund_amount / 100)` | 元 | 当期支付当期退款 + 往期支付当期退款 | 待确认 |
| trade_profit | `sum(income_amount / 100 - in_pay_period_refund_amount / 100 - non_pay_period_refund_amount / 100)` | 元 | 净营收 | 待确认 |
| xb_trade_income | `sum(same_lead_period_income_amount / 100)` | 元 | 当期线索当期收款 | 待确认 |
| xb_trade_profit | `sum(same_lead_period_income_amount / 100 - same_lead_period_refund_amount / 100)` | 元 | 当期线索当期净营收 | 待确认 |
| kk_trade_income | `sum(income_amount / 100 - same_lead_period_income_amount / 100)` | 元 | 跨期收款 | 待确认 |
| pre_refund | `sum(non_pay_period_refund_amount / 100)` | 元 | 往期支付当期退款 | 待确认 |

## 6. 派生指标

| 指标名 | 字段/表达式 | 单位 | 说明 | 状态 |
|---|---|---|---|---|
| channel_1 | `channel_grp.channel_group` | 文本 | 渠道分组，来自 `temp_table.shenbaoxin_channel_group` | 待确认字段存在性 |
| s_lead | `case when can_renew_ds_count_a >= 5 then can_renew_ds_count_a else 0 end` | 个 | 有效线索门槛（>=5 算入） | 阈值 5 待确认 |
| podan | `case when can_renew_ds_count_a >= 5 and trade_profit > 0 then 1 else 0 end` | 0/1 | 有效线索达 5 且净营收为正则破单 | 阈值 5 待确认 |

## 7. 与市场顾问转化看板的指标差异

| 指标 | 市场顾问转化看板 | 本看板 | 说明 |
|---|---|---|---|
| `d_w`（当期/非当期） | 有 | 无 | 本看板不含此逻辑 |
| `xiansuo`（线索标记） | 有 | 无 | 本看板不含此逻辑 |
| `pp_pmit` / `ww_pmit` | 有 | 无 | 本看板不含当期/非当期利润拆分 |
| `is_f_call` | 无 | 有 | 本看板含首 call 任务标记 |
| `is_friend_lead` | 有（coalesce 写法） | 有（nvl 写法） | 函数不同但口径相同 |
| `first_call_in_24h` | 有（24h 首呼） | 有（24h 首呼） | 口径相同 |
| `merge_assign_lead_count` / `merge_valid_lead_count` | 有（抖音私域） | 无 | 本看板不含抖音私域特殊处理 |
| `lead_period_income_amount` / `lead_period_refund_amount` | 有 | 无 | 本看板不含线索期收入 |
| `sx_qi` / `jingli_1` | 有 | 无 | 本看板不含规则期次提取和经理 |
| 部门聚合粒度 | 顾问个体级别 | 部门级别 | 本看板不含顾问和经理维度 |

## 8. 待确认事项

- `valid_lead_count` 和 `can_renew_ds_count_a` 为同一聚合重复输出；需确认是前端需求还是 SQL 冗余。
- `lead_purchase_intention_level2_category_name` 用作年级维度但其字段名仍为商品品类名；需确认前端是否需要改名。
- 金额单位是否全部为分、`/ 100` 是否在历史 SQL 中已统一，需业务确认。
- 所有指标口径来自数据集 SQL 推断，未经业务口径文档确认。
