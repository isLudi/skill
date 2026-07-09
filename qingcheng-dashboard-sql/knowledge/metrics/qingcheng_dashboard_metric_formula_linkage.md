# Qingcheng dashboard metric formulas and SQL linkage

## Scope

- Current snapshot date: 2026-06-26.
- Frontend metric formulas are captured from read-only dashboard edit-page profiles under `knowledge/dashboard_web_profiles/edit_metrics/`.
- Source SQL files are the latest retained Data Center SQL snapshots under `resources/raw_sql/data_center_qingcheng_*` where a current snapshot exists; otherwise keep the latest canonical retained snapshot.
- Use this document to connect a BI metric symptom to its frontend formula and the SQL column that feeds it.

## Dashboard To SQL Map

| dashboard | dashboard_id | dataset model | edit metrics | rendered profile | source SQL |
|---|---|---|---|---|---|
| `过程数据报表-青橙` | `dashboard_3733927793301065728` | `2064` | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3733927793301065728_edit_metrics.md) | [qingcheng_process_data_report_web_profile.md](../dashboard_web_profiles/qingcheng_process_data_report_web_profile.md) | [data_center_qingcheng_2064_20260625.sql](../../resources/raw_sql/data_center_qingcheng_2064_20260625.sql) |
| `青橙项目部_行课报表` | `dashboard_3765824192103694336` | `2244` | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3765824192103694336_edit_metrics.md) | [qingcheng_attendance_report_web_profile.md](../dashboard_web_profiles/qingcheng_attendance_report_web_profile.md) | [qingcheng_daoke_raw_20260522.sql](../../resources/raw_sql/qingcheng_daoke_raw_20260522.sql) |
| `青橙-全域产品数据看板` | `dashboard_3852445620602875904` | `2576` | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3852445620602875904_edit_metrics.md) | [qingcheng_all_product_dashboard_web_profile.md](../dashboard_web_profiles/qingcheng_all_product_dashboard_web_profile.md) | [qingcheng_revenue_year_quarter_month_raw_20260522.sql](../../resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql) |
| `青橙-全年级营收看板` | `dashboard_3865509979877412864` | `2576` | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3865509979877412864_edit_metrics.md) | [qingcheng_full_grade_revenue_dashboard_web_profile.md](../dashboard_web_profiles/qingcheng_full_grade_revenue_dashboard_web_profile.md) | [qingcheng_revenue_year_quarter_month_raw_20260522.sql](../../resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql) |
| `团队转化完成度-青橙` | `dashboard_3872626876332130305` | `2680`<br>`2677` | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3872626876332130305_edit_metrics.md) | [qingcheng_team_conversion_completion_web_profile.md](../dashboard_web_profiles/qingcheng_team_conversion_completion_web_profile.md) | [qingcheng_team_completion_period_raw_20260522.sql](../../resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql)<br>[qingcheng_team_completion_month_raw_20260522.sql](../../resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql) |
| `个人转化数据-青橙` | `dashboard_3873038327756636161` | `2769` | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3873038327756636161_edit_metrics.md) | [qingcheng_personal_conversion_web_profile.md](../dashboard_web_profiles/qingcheng_personal_conversion_web_profile.md) | [qingcheng_personal_conversion_raw_20260522.sql](../../resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql) |
| `青-抖私-转化` | `dashboard_3884629814875697153` | `2740` | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3884629814875697153_edit_metrics.md) | [qingcheng_dousi_conversion_web_profile.md](../dashboard_web_profiles/qingcheng_dousi_conversion_web_profile.md) | [data_center_qingcheng_2740_20260624.sql](../../resources/raw_sql/data_center_qingcheng_2740_20260624.sql) |
| `转化数据看板` | `dashboard_3885764906392891392` | `2460` | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3885764906392891392_edit_metrics.md) | [qingcheng_conversion_dashboard_web_profile.md](../dashboard_web_profiles/qingcheng_conversion_dashboard_web_profile.md) | [data_center_qingcheng_2460_20260709.sql](../../resources/raw_sql/data_center_qingcheng_2460_20260709.sql) |
| `完成度文字播报_青` | `dashboard_3893277592797257728` | text-only / no pivot model captured | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3893277592797257728_edit_metrics.md) | [qingcheng_completion_broadcast_text_web_profile.md](../dashboard_web_profiles/qingcheng_completion_broadcast_text_web_profile.md) | - |
| `青橙-渠道过程数据-天` | `dashboard_3910621974690701312` | `2064` | [edit metrics](../dashboard_web_profiles/edit_metrics/dashboard_3910621974690701312_edit_metrics.md) | [qingcheng_channel_process_daily_web_profile.md](../dashboard_web_profiles/qingcheng_channel_process_daily_web_profile.md) | [data_center_qingcheng_2064_20260625.sql](../../resources/raw_sql/data_center_qingcheng_2064_20260625.sql) |

## Dataset Logic Linkage

| model | source SQL | key output columns | frontend formula dependency | debugging notes |
|---|---|---|---|---|
| `2064 Qingcheng process data` | [data_center_qingcheng_2064_20260625.sql](../../resources/raw_sql/data_center_qingcheng_2064_20260625.sql) | `v_lead`, `is_friend_lead`, APP and first-call/communication fields, attendance fields | Rates are generally `sum(flag_or_count) / sum(v_lead)` after pivot grouping. | Lead volume and manpower rows can appear with blank org fields when the base lead has no matched receiver/org mapping; verify source join before adding frontend filters. The 2026-06-25 snapshot adds `channel_map_1 = '抖音复用'` for `%抖音正价退费%` and refines `channel_map_2` Qingcheng IP branches into `IP星义/IP朱博士/IP春春/IP郭艺/IP亚飞`. |
| `2244 Qingcheng attendance` | [qingcheng_daoke_raw_20260522.sql](../../resources/raw_sql/qingcheng_daoke_raw_20260522.sql) | `lead`, `ke_1` to `ke_6`, `v_ke_1` to `v_ke_6` | Attendance and valid-attendance ratios are computed as course count divided by `lead`. | Confirm period, grade, and channel filters before comparing with process dashboards. |
| `2460 Conversion data` | [data_center_qingcheng_2460_20260709.sql](../../resources/raw_sql/data_center_qingcheng_2460_20260709.sql) | `v_lead`, `pay_user`, `p_pay_user`, `pay_sub`, `p_pay_sub`, `income`, `refund`, `promit`, `p_income`, `refund_user`, `podan`, `sc`, `cost_lead` | Conversion rate, order rate, ROI, manpower efficiency, customer price, and current/past-period revenue are frontend aggregations over these SQL outputs. | This dataset is lead-attribution oriented and can differ from finance-performance completion datasets. Current retained logic uses business-calendar qici overrides before `trade_timestamp` Friday-period fallback, service main-detail revenue with internal transfer-chain exclusion, discounted `podan`, and team-org backfill on `employee_email_name + qici`. |
| `2576 Year/season/month revenue` | [qingcheng_revenue_year_quarter_month_raw_20260522.sql](../../resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql) | `income`, `refund`, `promit`, `p_payer`, `r_payer`, `p_sub`, `r_sub` | Revenue dashboards calculate net users, net subjects, joint-purchase rate, and refund ratios at the frontend. | Use this for product/time revenue views, not consultant completion payouts. |
| `2677 Team completion monthly` | [qingcheng_team_completion_month_raw_20260522.sql](../../resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql) | `emye_c`, `goal`, `income`, `refund`, `promit`, `promit_4`, `H_promit_4`, `n_H_promit_4`, `refund_4`, `podan_4` | Completion formulas use adjusted Qingcheng net receipts. SQL outputs raw non-H net fields and the frontend applies the 50% non-H discount. | Keep finance order-change links on the main transaction layer, use `order_attr.original_paid_time` for org attribution, and do not rely only on refund detail links. |
| `2680 Team completion period` | [qingcheng_team_completion_period_raw_20260522.sql](../../resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql) | `emye_c`, `goal`, `income`, `refund`, `promit`, `promit_4`, `H_promit_4`, `n_H_promit_4`, `refund_4`, `podan_4` | Period completion uses the same metric family as monthly completion with period grain. SQL outputs raw non-H net fields and the frontend applies the 50% non-H discount. | Must cover order-change `biz_type in (2,7)` paths, preserve transfer/change-chain amount, and join team org by `employee_email_name + qici`. |
| `2740 Dousi conversion` | [data_center_qingcheng_2740_20260624.sql](../../resources/raw_sql/data_center_qingcheng_2740_20260624.sql) | `gmv_7`, `gmv_14`, `gmv_30`, `gmv_n30`, `gmv_7_h`, `gmv_total`, `refund_*` | Frontend formulas split GMV and refunds into 7-day, 8-14-day, 15-30-day, and over-30-day buckets. | Validate bucket denominators `gmv_total` and `refund_total` before interpreting ratios. |
| `2769 Personal conversion` | [qingcheng_personal_conversion_raw_20260522.sql](../../resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql) | `income`, `refund`, `promit`, `H_promit_4`, `n_H_promit_4`, `Y_promit_4`, `Y_income_4`, `Y_refund_4`, `qici_goal`, `moth_goal` | Key formula: adjusted output = `sum(n_H_promit_4) * 0.5 + (sum(H_promit_4) - sum(Y_promit_4))`; cumulative net revenue adds back `sum(Y_promit_4)`. SQL outputs raw non-H net fields and the frontend applies the 50% non-H discount. | This is finance-performance attribution; it intentionally differs from lead conversion attribution when orders belong to non-H or cross-department lines. Org attribution must prefer `order_attr.original_paid_time`; normal orders on an order-change chain must remain included. |
| `2834 Conversion wide market channel` | [qingcheng_conversion_wide_table_market_channel_20260611.sql](../../resources/raw_sql/qingcheng_conversion_wide_table_market_channel_20260611.sql) | Market-channel dimensions and lead/order attribution fields | Used for channel-level decomposition and historical lead-source tracing. | Useful for finding original lead source when Qingcheng IP rule names mask raw channel fields. |

## High-Frequency Frontend Formulas

### Conversion Dashboards

- Current-period order user rate: `sum(p_pay_user) / sum(v_lead)`.
- Overall order user rate: `sum(pay_user) / sum(v_lead)`.
- Current-period subject rate: `sum(p_pay_sub) / sum(v_lead)`.
- Overall subject rate: `sum(pay_sub) / sum(v_lead)`.
- Past-period revenue: `sum(income) - sum(p_income)`.
- ROI: `sum(promit) / lead_cost`.
- Podan rate: `sum(podan) / sum(v_lead)`, where `podan` is already a discounted-net-receipt user count rather than simple `promit > 0`.

### Personal Completion

- Class-course revenue: `sum(income) - sum(Y_income_4)`.
- Class-course refund: `sum(refund) - sum(Y_refund_4)`.
- Class-course net receipt: class-course revenue minus class-course refund.
- Adjusted output: `sum(n_H_promit_4) * 0.5 + (sum(H_promit_4) - sum(Y_promit_4))`.
- Cumulative net revenue: adjusted output plus `sum(Y_promit_4)`.

### Team Completion

- Adjusted net receipt excluding post-course refunds: `sum(n_H_promit_4) * 0.5 + sum(H_promit_4)`.
- Completion rate: adjusted net receipt divided by the configured target at current pivot grain.

### Dousi Conversion

- 7-day GMV ratio: `sum(gmv_7) / sum(gmv_total)`.
- 8-14-day GMV ratio: `sum(gmv_14) / sum(gmv_total)`.
- 7-day refund ratio: `sum(refund_7) / sum(refund_total)`.

## Debugging Order

1. Start from the rendered dashboard profile to confirm component, filter, and dataset model routing.
2. Open the matching edit metrics profile to inspect frontend custom formula and selected dimensions.
3. Open the linked Data Center SQL snapshot to trace the SQL output columns that feed the BI model metrics.
4. If a metric differs between dashboards, compare grain and attribution first: lead-conversion datasets and finance-performance datasets are intentionally different.
5. For completion metrics, re-check course-change chain preservation, post-course refund exclusion, H-stage 50% discount, and `biz_type in (2,7)` coverage before changing formulas.

## Known Cross-Dashboard Semantics

- Conversion data is lead-attribution oriented and is based on lead/order attribution paths; personal and team completion are finance-performance oriented and can include Qingcheng-attributed performance outside the conversion lead path.
- Personal and team completion metrics require the SQL layer to keep full transfer/change-chain amounts from `dim_finance_order_change_df` on the main transaction layer. Joining that table only inside refund detail logic causes adjusted output to be understated.
- Frontend `${metric}` references are BI model metrics. Do not rewrite SQL solely from a frontend formula until the metric ID/name is resolved against the linked source SQL.
