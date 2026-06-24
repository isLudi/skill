# 青橙-全年级营收看板 edit-page metrics profile

## Snapshot

- generated_at: `2026-06-24 18:50:37`
- dashboard_id: `dashboard_3865509979877412864`
- source command: `usql-web-query-operator/scripts/read_dashboard.py profile-edit-dashboard`
- rendered dashboard profile: [view profile](../qingcheng_full_grade_revenue_dashboard_web_profile.md)
- runtime JSON: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-185025\dashboard_3865509979877412864_edit_metrics_profile.json`
- boundary: read-only extraction from dashboard config, unit details, model field details, and custom formulas; no save/publish/delete/create/update endpoint is called.

## Dataset Models

| model_id | model_name | source SQL |
|---:|---|---|
| 2576 | `年季月营收情况` | [qingcheng_revenue_year_quarter_month_raw_20260522.sql](../../../resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql) |

## Pivot Units

| unit_name | model_id | model_name | dimensions | measure_count | custom_formula_count |
|---|---:|---|---|---:|---:|
| `期次数据` | 2576 | `年季月营收情况` | grade_list, qici, qici, xuebu, dazhuguan | 12 | 4 |
| `月度数据` | 2576 | `年季月营收情况` | grade_list, max_month, max_year, max_month, xuebu, dazhuguan | 12 | 4 |
| `季度数据` | 2576 | `年季月营收情况` | grade_list, max_quarter, max_year, max_quarter, xuebu, dazhuguan | 12 | 4 |
| `年度数据` | 2576 | `年季月营收情况` | grade_list, max_year, max_year, xuebu, dazhuguan | 12 | 4 |

## Measures And Formulas

| display_name | field_or_metric | role | formula_or_definition |
|---|---|---|---|
| `成交用户数` | `p_payer` | `measure` | `sum(8579513187461121)` |
| `退费用户数` | `r_payer` | `measure` | `sum(8579513187461123)` |
| `净用户数` | `净用户数` | `custom_measure` | `sum(${p_payer}-${r_payer})` |
| `成交科目数` | `p_sub` | `measure` | `sum(8579513187461120)` |
| `退费科目数` | `r_sub` | `measure` | `sum(8579513187461122)` |
| `净科目数` | `净订单数` | `custom_measure` | `sum(${p_sub}-${r_sub})` |
| `联报率` | `联报率` | `custom_measure` | `ifnull(${净订单数}/${净用户数},0)` |
| `营收金额` | `income` | `measure` | `sum(8579419051943939)` |
| `退费金额` | `refund` | `measure` | `sum(8579419051943940)` |
| `净营收` | `promit` | `measure` | `sum(8579419051943941)` |
| `净营收占比` | `promit` | `measure` | `sum(8579419051943941)` |
| `退费占比` | `退费占比` | `custom_measure` | `ifnull(sum(${refund})/sum(${income}),0)` |

## Text Notes Captured From Dashboard

1. 退费用户/科目数：<500元不计入 ；  净营收占比= 各学部净营收/净营收总计； 数据更新周期：每小时更新两小时前数据 ； 看板取数周期：按照自然月/季度/年

## SQL Linkage Notes

- Frontend custom measures are calculated after the dataset SQL output is aggregated by the pivot dimensions. When debugging a metric, first verify the raw metric column in the linked source SQL, then verify the frontend formula in this file.
- `${metric}` references in formulas refer to BI model metrics, not physical SQL columns directly. Resolve them through the dataset model and source SQL listed above.
