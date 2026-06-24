# 青橙项目部_行课报表 edit-page metrics profile

## Snapshot

- generated_at: `2026-06-24 18:50:04`
- dashboard_id: `dashboard_3765824192103694336`
- source command: `usql-web-query-operator/scripts/read_dashboard.py profile-edit-dashboard`
- rendered dashboard profile: [view profile](../qingcheng_attendance_report_web_profile.md)
- runtime JSON: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-184953\dashboard_3765824192103694336_edit_metrics_profile.json`
- boundary: read-only extraction from dashboard config, unit details, model field details, and custom formulas; no save/publish/delete/create/update endpoint is called.

## Dataset Models

| model_id | model_name | source SQL |
|---:|---|---|
| 2244 | `青橙到课` | [qingcheng_daoke_raw_20260522.sql](../../../resources/raw_sql/qingcheng_daoke_raw_20260522.sql) |

## Pivot Units

| unit_name | model_id | model_name | dimensions | measure_count | custom_formula_count |
|---|---:|---|---|---:|---:|
| `主管行课` | 2244 | `青橙到课` | xiaozu, dept_2 | 13 | 12 |
| `伙伴行课` | 2244 | `青橙到课` | employee_email_name, channel_map_2, grade_1, dept_2 | 13 | 12 |
| `渠道部门行课` | 2244 | `青橙到课` | channel_map_2, dept_2 | 13 | 12 |
| `渠道年级行课` | 2244 | `青橙到课` | channel_map_2, grade_1 | 13 | 12 |

## Measures And Formulas

| display_name | field_or_metric | role | formula_or_definition |
|---|---|---|---|
| `应出勤人数` | `lead` | `measure` | `sum(8241056799549440)` |
| `课1` | `课1` | `custom_measure` | `sum(${ke_1})/sum(${lead})` |
| `课1有效` | `课1有效` | `custom_measure` | `sum(${v_ke_1})/sum(${lead})` |
| `课2` | `课2` | `custom_measure` | `sum(${ke_2})/sum(${lead})` |
| `课2有效` | `课2有效` | `custom_measure` | `sum(${v_ke_2})/sum(${lead})` |
| `课3` | `课3` | `custom_measure` | `sum(${ke_3})/sum(${lead})` |
| `课3有效` | `课3有效` | `custom_measure` | `sum(${v_ke_3})/sum(${lead})` |
| `课4` | `课4` | `custom_measure` | `sum(${ke_4})/sum(${lead})` |
| `课4有效` | `课4有效` | `custom_measure` | `sum(${v_ke_4})/sum(${lead})` |
| `课5` | `课5` | `custom_measure` | `sum(${ke_5})/sum(${lead})` |
| `课5有效` | `课5有效` | `custom_measure` | `sum(${v_ke_5})/sum(${lead})` |
| `课6` | `课6` | `custom_measure` | `sum(${ke_6})/sum(${lead})` |
| `课6有效` | `课6有效` | `custom_measure` | `sum(${v_ke_6})/sum(${lead})` |

## Text Notes Captured From Dashboard

- No text note was captured from the edit-page profile.

## SQL Linkage Notes

- Frontend custom measures are calculated after the dataset SQL output is aggregated by the pivot dimensions. When debugging a metric, first verify the raw metric column in the linked source SQL, then verify the frontend formula in this file.
- `${metric}` references in formulas refer to BI model metrics, not physical SQL columns directly. Resolve them through the dataset model and source SQL listed above.
