# 市场顾问转化看板指标

## 1. 中文名称

市场顾问转化看板指标集合

## 2. 指标定义

指标来自 `resources/raw_sql/data_center_market_2253_20260705.sql` 的 `zhuanhua` CTE 和最终 select。当前状态为“历史看板 SQL 口径”，未与业务指标文档核对。

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
| kk_trade_profit | `sum(income_amount / 100 - in_pay_period_refund_amount / 100 - non_pay_period_refund_amount / 100 - same_lead_period_income_amount / 100 + same_lead_period_refund_amount / 100)` | 跨期净营收，即截面净营收减当期线索当期净营收，分转元 |
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

- 当前 SQL 先输出聚合指标，前端展示比例类指标时按下表二次计算。
- `s_lead` 和 `podan` 使用 `can_renew_ds_count_a >= 5` 阈值。
- 金额类字段均除以 100，推断主表金额字段单位为“分”，需人工确认。
- `cb_cb` 为单例子成本，`gl_gl` 为单例子目标；成本/目标类指标应使用 `lead_count * cb_cb`、`lead_count * gl_gl` 聚合。

### 5.1 前端展示派生公式

以下公式为 2026-05-28 根据看板截图和 `D:\Feishu\task_1370386373_1779954054145.xlsx` 数据集校验后维护的展示口径；生成 SQL 或配置看板指标时应使用聚合后的 `sum(...)` / `count(distinct ...)` 口径，避免先行级相除再汇总。

| 展示指标 | 公式 | 说明 |
|---|---|---|
| 人头转化率（当期） | `ifnull(sum(${pay_users_on_period}) / sum(${can_renew_ds_count_a}), 0)` | 当期支付人数 / 退后线索 |
| 人头转化率（截面） | `ifnull(sum(${pay_users}) / sum(${can_renew_ds_count_a}), 0)` | 截面支付人数 / 退后线索 |
| 订单转化率（当期） | `ifnull(sum(${pay_user_subs_on_period}) / sum(${can_renew_ds_count_a}), 0)` | 当期科目人次 / 退后线索 |
| 订单转化率（截面） | `ifnull(sum(${pay_user_subs}) / sum(${can_renew_ds_count_a}), 0)` | 截面科目人次 / 退后线索 |
| 单效（当期） | `ifnull(sum(${xb_trade_profit}) / sum(${can_renew_ds_count_a}), 0)` | 当期净收款 / 退后线索 |
| 单效（截面） | `ifnull(sum(${trade_profit}) / sum(${can_renew_ds_count_a}), 0)` | 截面净收款 / 退后线索 |
| 跨期单效桥接 | `ifnull(sum(${kk_trade_profit}) / sum(${can_renew_ds_count_a}), 0)` | 截面单效与当期单效的差额桥接；当期线索后续跨期支付/退款会沉淀到这里 |
| 破蛋率 | `ifnull(sum(${podan}) / count(distinct ${employee_email_name}), 0)` | 破蛋顾问数 / 接量人力 |
| 拓科率（截面） | `ifnull(sum(${pay_user_subs}) / sum(${pay_users}), 0)` | 科目人次 / 支付用户数 |
| 退费率 | `ifnull(sum(${trade_refund}) / sum(${trade_income}), 0)` | 退款 / 总收款 |
| roi1（mroi） | `ifnull(sum(${trade_profit}) / sum(${lead_count} * ${cb_cb}), 0)` | 净收款 / 市场成本 |
| roi2（smroi） | `ifnull(sum(${trade_profit}) / (sum(${lead_count} * ${cb_cb}) + ${人力成本}), 0)` | 净收款 /（市场成本 + 人力成本）；当前数据集未维护人力成本字段 |
| gmv完成度 | `ifnull(sum(${trade_profit}) / sum(${lead_count} * ${gl_gl}), 0)` | 净收款 / GMV目标 |
| 人产 | `ifnull(sum(${trade_profit}) / count(distinct ${employee_email_name}), 0)` | 净收款 / 接量人力 |

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

是。需要确认金额单位、抖音私域合并口径、`>= 5` 阈值、成本表维护口径、时间偏移口径、`xiansuo` 是否只作为聚合指标输出，以及渠道映射 CASE 是否仍为最新规则。最新渠道 CASE 维护入口见 `knowledge/sql_patterns/channel_mapping_case_when.md`，归档片段为 `resources/raw_sql/market_channel_case_when_0612.sql`。
