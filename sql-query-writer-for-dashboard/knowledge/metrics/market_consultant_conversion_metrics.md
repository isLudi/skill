# 市场顾问转化看板指标

## 1. 中文名称

市场顾问转化看板指标集合

## 2. 指标定义

指标来自 `resources/raw_sql/market_consultant_conversion.sql` 的 `zhuanhua` CTE 和最终 select。当前状态为“历史看板 SQL 口径”，未与业务指标文档核对。

## 3. SQL 表达式

| 指标名 | SQL 表达式 | 说明 |
|---|---|---|
| lead_count | `sum(case when channel_map = '抖音私域' then merge_assign_lead_count else lead_count end)` | 线索数，抖音私域用合并口径 |
| can_renew_ds_count_a | `sum(case when channel_map = '抖音私域' then merge_valid_lead_count else valid_lead_count end)` | 有效线索数，抖音私域用合并口径 |
| xiansuo | `sum(xiansuo)` | `D:\Feishu\0522.txt` 的 `xiansuo` 0/1 规则聚合值 |
| pay_users | `sum(conversion_lead_count)` | 转化人数 |
| pay_users_on_period | `sum(same_lead_period_conversion_lead_count)` | 当期转化人数 |
| pay_users_not_on_period | `sum(conversion_lead_count - same_lead_period_conversion_lead_count)` | 跨期转化人数 |
| pay_user_subs | `sum(subject_count)` | 转化科目人次 |
| pay_user_subs_on_period | `sum(same_lead_period_subject_count)` | 当期转化科目人次 |
| pay_user_subs_not_on_period | `sum(subject_count - same_lead_period_subject_count)` | 跨期转化科目人次 |
| pay_user_subs_joint | `sum(lb_subject_count)` | 联报人次 |
| pay_user_subs_joint_onp | `sum(same_lead_period_lb_subject_count)` | 当期联报人次 |
| pay_user_subs_joint_nonp | `sum(lb_subject_count - same_lead_period_lb_subject_count)` | 跨期联报人次 |
| trade_income | `sum(income_amount / 100)` | 收款金额，分转元 |
| trade_refund | `sum(in_pay_period_refund_amount / 100 + non_pay_period_refund_amount / 100)` | 当期支付当期退款 + 往期支付当期退款，分转元 |
| trade_profit | `sum(income_amount / 100 - in_pay_period_refund_amount / 100 - non_pay_period_refund_amount / 100)` | 净营收，分转元 |
| xb_trade_income | `sum(same_lead_period_income_amount / 100)` | 当期线索当期收款，分转元 |
| xb_trade_profit | `sum(same_lead_period_income_amount / 100 - same_lead_period_refund_amount / 100)` | 当期线索当期净营收，分转元 |
| kk_trade_income | `sum(income_amount / 100 - same_lead_period_income_amount / 100)` | 跨期收款，分转元 |
| pre_refund | `sum(non_pay_period_refund_amount / 100)` | 往期支付当期退款，分转元 |
| pp_pmit | `sum(case when d_w = '当期' then lead_period_income_amount / 100 - lead_period_refund_amount / 100 else 0 end)` | 当期 GMV；`D:\Feishu\0522.txt` 中 `qici` 规则在本看板落为 `d_w` |
| ww_pmit | `sum(case when d_w = '非当期' then income_amount / 100 - in_pay_period_refund_amount / 100 - non_pay_period_refund_amount / 100 else 0 end)` | 非当期 GMV；`D:\Feishu\0522.txt` 中 `qici` 规则在本看板落为 `d_w` |
| s_lead | `case when can_renew_ds_count_a >= 5 then can_renew_ds_count_a else 0 end` | 达标有效线索数 |
| podan | `case when can_renew_ds_count_a >= 5 and trade_profit > 0 then 1 else 0 end` | 破单标记 |
| cb_cb | `coalesce(ct.cost, 0)` | 单例子成本 |
| gl_gl | `coalesce(ct.goal, 0)` | 单例子目标 |

## 4. 适用表

- `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- `temp_table.dingxi01_cost`
- `temp_table.dingxi01_channel_group`
- `temp_table.dingxi01_jiagou_db`
- `temp_table.dingxi01_jiagou_zx`

## 5. 分母/分子口径

- 当前 SQL 为聚合指标，没有显式比例分母。
- `s_lead` 和 `podan` 使用 `can_renew_ds_count_a >= 5` 阈值。
- 金额类字段均除以 100，推断主表金额字段单位为“分”，需人工确认。

## 6. 时间口径

主表分区：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '3' hour, 'HH')
```

最终过滤：

```sql
period_name > '20260424期'
```

## 7. 范围限定

```sql
section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name = '市场部'
and section_assign_employee_third_level_department_name = '市场顾问部'
and period_mapping_first_level_department_name = 'H业务线'
```

## 8. 待人工确认

是。需要确认金额单位、抖音私域合并口径、`>= 5` 阈值、成本表维护口径、时间偏移口径、`xiansuo` 是否只作为聚合指标输出，以及渠道映射 CASE 是否仍为最新规则。最新渠道 CASE 维护入口见 `knowledge/sql_patterns/channel_mapping_case_when.md`，归档片段为 `resources/raw_sql/market_channel_case_when_0522.sql`。
