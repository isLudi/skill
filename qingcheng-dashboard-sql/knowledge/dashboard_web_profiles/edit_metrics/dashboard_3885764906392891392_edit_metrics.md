# 转化数据看板 edit-page metrics profile

## Snapshot

- generated_at: `2026-06-24 18:51:43`
- dashboard_id: `dashboard_3885764906392891392`
- source command: `usql-web-query-operator/scripts/read_dashboard.py profile-edit-dashboard`
- rendered dashboard profile: [view profile](../qingcheng_conversion_dashboard_web_profile.md)
- runtime JSON: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-185131\dashboard_3885764906392891392_edit_metrics_profile.json`
- boundary: read-only extraction from dashboard config, unit details, model field details, and custom formulas; no save/publish/delete/create/update endpoint is called.

## Dataset Models

| model_id | model_name | source SQL |
|---:|---|---|
| 2460 | `转化数据` | [data_center_qingcheng_2460_20260709.sql](../../../resources/raw_sql/data_center_qingcheng_2460_20260709.sql) |

## Pivot Units

| unit_name | model_id | model_name | dimensions | measure_count | custom_formula_count |
|---|---:|---|---|---:|---:|
| `渠道-总` | 2460 | `转化数据` | channel_1 | 24 | 14 |
| `部门-总` | 2460 | `转化数据` | dept_2 | 24 | 14 |
| `渠道-大组` | 2460 | `转化数据` | dazu | 24 | 14 |
| `一级渠道-年级` | 2460 | `转化数据` | channel_1, grade_1 | 24 | 14 |
| `一级渠道-主管` | 2460 | `转化数据` | channel_1, xiaozu | 24 | 14 |
| `一级渠道-年级_副本_副本` | 2460 | `转化数据` | channel_map_2, dept_2, channel_map_2 | 24 | 14 |
| `二级渠道-年级` | 2460 | `转化数据` | channel_map_2, grade_1, channel_map_2 | 24 | 14 |
| `二级渠道-主管` | 2460 | `转化数据` | channel_map_2, xiaozu, channel_map_2 | 24 | 14 |
| `伙伴数据` | 2460 | `转化数据` | employee_email_name, channel_map_2, grade_1, grade_1, channel_map_2 | 24 | 14 |

## Measures And Formulas

| display_name | field_or_metric | role | formula_or_definition |
|---|---|---|---|
| `线索量` | `v_lead` | `measure` | `sum(8626071195052032)` |
| `当期人头转化数` | `p_pay_user` | `measure` | `sum(8626071195052034)` |
| `当期人头转化率` | `当期人头转化率` | `custom_measure` | `ifnull(sum(${p_pay_user})/sum(${v_lead}),0)` |
| `综合人头转化数` | `pay_user` | `measure` | `sum(8626071195052033)` |
| `综合人头转化率` | `综合人头转化率` | `custom_measure` | `ifnull(sum(${pay_user})/sum(${v_lead}),0)` |
| `当期订单转化数` | `p_pay_sub` | `measure` | `sum(8626071195052036)` |
| `当期订单转化率` | `当期订单转化率` | `custom_measure` | `ifnull(sum(${p_pay_sub})/sum(${v_lead}),0)` |
| `综合订单转化数` | `pay_sub` | `measure` | `sum(8626071195052035)` |
| `综合订单转化率` | `综合订单转化率` | `custom_measure` | `ifnull(sum(${pay_sub})/sum(${v_lead}),0)` |
| `当期单效` | `当期单效` | `custom_measure` | `ifnull(sum(${p_income})/sum(${v_lead}),0)` |
| `综合单效` | `综合单效` | `custom_measure` | `ifnull(sum(${promit})/sum(${v_lead}),0)` |
| `当期营收` | `p_income` | `measure` | `sum(8626071195052040)` |
| `往期营收` | `往期营收` | `custom_measure` | `sum(${income})-sum(${p_income})` |
| `综合营收` | `income` | `measure` | `sum(8626071195052037)` |
| `退费人数` | `refund_user` | `measure` | `sum(8626071195052041)` |
| `退费金额` | `refund` | `measure` | `sum(8626071195052038)` |
| `退费率` | `退费率` | `custom_measure` | `ifnull(sum(${refund})/sum(${income}),0)` |
| `净产出` | `promit` | `measure` | `sum(8626071195052039)` |
| `ROI` | `ROI` | `custom_measure` | `ifnull (sum(${promit})/${线索成本},0)` |
| `人效` | `人效` | `custom_measure` | `ifnull(sum(${promit})/${接量人力},0)` |
| `联报率` | `联报率` | `custom_measure` | `ifnull(sum(${pay_sub})/sum(${pay_user}),0)` |
| `客单价` | `客单价` | `custom_measure` | `ifnull(sum(${promit})/sum(${pay_user}),0)` |
| `破蛋率` | `破蛋率` | `custom_measure` | `ifnull(sum(${podan})/sum(${v_lead}),0)` |
| `平均成交周期(天)` | `平均成交周期(天)` | `custom_measure` | `ifnull(sum(${sc})/sum(${pay_user}),0)` |

## Text Notes Captured From Dashboard

- No text note was captured from the edit-page profile.

## SQL Linkage Notes

- Frontend custom measures are calculated after the dataset SQL output is aggregated by the pivot dimensions. When debugging a metric, first verify the raw metric column in the linked source SQL, then verify the frontend formula in this file.
- `${metric}` references in formulas refer to BI model metrics, not physical SQL columns directly. Resolve them through the dataset model and source SQL listed above.
