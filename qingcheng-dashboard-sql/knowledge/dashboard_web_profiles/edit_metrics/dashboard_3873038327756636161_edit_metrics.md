# 个人转化数据-青橙 edit-page metrics profile

## Snapshot

- generated_at: `2026-06-24 18:51:10`
- dashboard_id: `dashboard_3873038327756636161`
- source command: `usql-web-query-operator/scripts/read_dashboard.py profile-edit-dashboard`
- rendered dashboard profile: [view profile](../qingcheng_personal_conversion_web_profile.md)
- runtime JSON: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-185100\dashboard_3873038327756636161_edit_metrics_profile.json`
- boundary: read-only extraction from dashboard config, unit details, model field details, and custom formulas; no save/publish/delete/create/update endpoint is called.

## Dataset Models

| model_id | model_name | source SQL |
|---:|---|---|
| 2769 | `青橙个人转化` | [qingcheng_personal_conversion_raw_20260522.sql](../../../resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql) |

## Pivot Units

| unit_name | model_id | model_name | dimensions | measure_count | custom_formula_count |
|---|---:|---|---|---:|---:|
| `期产出` | 2769 | `青橙个人转化` | name, leader_employee_email_name, dazu, xuebu, qici, xuebu, dazu, leader_employee_email_name, data_level | 11 | 6 |
| `月度产出` | 2769 | `青橙个人转化` | name, xuebu, moth, xuebu, dazu, leader_employee_email_name, qici, data_level | 13 | 8 |

## Measures And Formulas

| display_name | field_or_metric | role | formula_or_definition |
|---|---|---|---|
| `净用户数` | `in_payer_4` | `measure` | `sum(8743548131305472)` |
| `班课营收` | `班课营收` | `custom_measure` | `ifnull(sum(${income})-sum(${Y_income_4}),0)` |
| `班课退费` | `班课退费` | `custom_measure` | `ifnull(sum(${refund})-sum(${Y_refund_4}),0)` |
| `班课净收` | `班课净收` | `custom_measure` | `ifnull(${班课营收}-${班课退费},0)` |
| `折算后产出` | `折算后产出` | `custom_measure` | `ifnull(sum(${n_H_promit_4})*0.5 + (sum(${H_promit_4}) - sum(${Y_promit_4})),0)` |
| `一对一营收` | `Y_income_4` | `measure` | `sum(8737961276237833)` |
| `一对一退费` | `Y_refund_4` | `measure` | `sum(8737961276237835)` |
| `一对一净收` | `Y_promit_4` | `measure` | `sum(8737961276237831)` |
| `累计净营收` | `累计净营收` | `custom_measure` | `ifnull(${折算后产出}+sum(${Y_promit_4}),0)` |
| `目标` | `qici_goal` | `measure` | `sum(8931278683858944)` |
| `完成度` | `完成度` | `custom_measure` | `ifnull(${累计净营收} / sum(${qici_goal}), 0)` |
| `档位最高金额` | `档位最高金额` | `custom_measure` | `CASE<br>    WHEN ${折算后产出} >= 0 AND ${折算后产出} < 10000 THEN 10000<br>    WHEN ${折算后产出} >= 10000 AND ${折算后产出} < 40000 THEN 40000<br>    WHEN ${折算后产出} >= 40000 AND ${折算后产出} < 50000 THEN 50000<br>    WHEN ${折算后产出} >= 50000 AND ${折算后产出} < 60000 THEN 60000<br>    WHEN ${折算后产出} >= 60000 AND ${折算后产出} < 70000 THEN 70000<br>    WHEN ${折算后产出} >= 70000 AND ${折算后产出} < 80000 THEN 80000<br>    WHEN ${折算后产出} >= 80000 AND ${折算后产出} < 90000 THEN 90000<br>    WHEN ${折算后产出} >= 90000 AND ${折算后产出} < 100000 THEN 100000<br>    WHEN ${折算后产出} >= 100000 AND ${折算后产出} < 120000 THEN 120000<br>    WHEN ${折算后产出} >= 120000 AND ${折算后产出} < 130000 THEN 130000<br>    WHEN ${折算后产出} >= 130000 AND ${折算后产出} < 140000 THEN 140000<br>    WHEN ${折算后产出} >= 140000 AND ${折算后产出} < 160000 THEN 160000<br>    WHEN ${折算后产出} >= 160000 AND ${折算后产出} < 180000 THEN 180000<br>    WHEN ${折算后产出} >= 180000 AND ${折算后产出} < 200000 THEN 200000<br>    WHEN ${折算后产出} >= 200000 THEN 200000   <br>    ELSE 0<br>END ` |
| `跳档差值` | `跳档差值` | `custom_measure` | `ifnull(${档位最高金额}-${折算后产出},0)` |
| `月度目标` | `moth_goal` | `measure` | `sum(8931278683858945)` |
| `完成度` | `月完成度` | `custom_measure` | `ifnull(${累计净营收} / sum(${moth_goal}),0)` |

## Text Notes Captured From Dashboard

1. 说明：<br>1. 班课产出: 均剔除班课开课4节课后和点睛班开课2节课后退费     2. 一对一产出：退费永久回溯       3.仅包含订单的课程类型为专题课和系列课      4. 整点到整点15抽取截至两小时前的数据<br>注：绿色：折算后产出 ≥ 10000        橙色：0元 < 折算后产出 < 10000元         红色： 折算后产出 ≤ 0元
2. 说明：<br>1. 班课产出: 均剔除班课开课4节课后和点睛班开课2节课后退费     2. 一对一产出：退费永久回溯       3.仅包含订单的课程类型为专题课和系列课      4. 整点到整点15抽取截至两小时前的数据<br>注：绿色：折算后产出 ≥ 10000        橙色：0元 < 折算后产出 < 10000元         红色： 折算后产出 < 0元

## SQL Linkage Notes

- Frontend custom measures are calculated after the dataset SQL output is aggregated by the pivot dimensions. When debugging a metric, first verify the raw metric column in the linked source SQL, then verify the frontend formula in this file.
- `${metric}` references in formulas refer to BI model metrics, not physical SQL columns directly. Resolve them through the dataset model and source SQL listed above.
- Personal completion metrics depend on `H_promit_4`, `n_H_promit_4`, and `Y_promit_4`; the current SQL source must keep finance order change links on the main transaction layer and include `biz_type in (2,7)` paths.
