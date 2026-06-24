# 团队转化完成度-青橙 edit-page metrics profile

## Snapshot

- generated_at: `2026-06-24 18:50:55`
- dashboard_id: `dashboard_3872626876332130305`
- source command: `usql-web-query-operator/scripts/read_dashboard.py profile-edit-dashboard`
- rendered dashboard profile: [view profile](../qingcheng_team_conversion_completion_web_profile.md)
- runtime JSON: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-185042\dashboard_3872626876332130305_edit_metrics_profile.json`
- boundary: read-only extraction from dashboard config, unit details, model field details, and custom formulas; no save/publish/delete/create/update endpoint is called.

## Dataset Models

| model_id | model_name | source SQL |
|---:|---|---|
| 2680 | `团队完成度【期】` | [qingcheng_team_completion_period_raw_20260522.sql](../../../resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql) |
| 2677 | `团队完成度【月】` | [qingcheng_team_completion_month_raw_20260522.sql](../../../resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql) |

## Pivot Units

| unit_name | model_id | model_name | dimensions | measure_count | custom_formula_count |
|---|---:|---|---|---:|---:|
| `小组-期_退4` | 2680 | `团队完成度【期】` | xiaozu, xuebu, xiaozu | 12 | 5 |
| `大组-期_退4` | 2680 | `团队完成度【期】` | dazu | 12 | 5 |
| `学部-期_退4` | 2680 | `团队完成度【期】` | xuebu | 12 | 5 |
| `小组-月` | 2677 | `团队完成度【月】` | xiaozu, xuebu, xiaozu | 12 | 5 |
| `大组-月` | 2677 | `团队完成度【月】` | dazu, xuebu | 12 | 5 |
| `学部-月` | 2677 | `团队完成度【月】` | xuebu | 12 | 5 |

## Measures And Formulas

| display_name | field_or_metric | role | formula_or_definition |
|---|---|---|---|
| `团队人数` | `emye_c` | `measure` | `sum(8703823135205376)` |
| `营收金额` | `income` | `measure` | `sum(8703823135205380)` |
| `退费金额` | `refund` | `measure` | `sum(8703823135205381)` |
| `净金额` | `promit` | `measure` | `sum(8703823135205382)` |
| `破蛋人数` | `podan_4` | `measure` | `sum(8703823135205389)` |
| `破蛋率` | `破蛋率-退4` | `custom_measure` | `ifnull(sum(${podan_4})/sum(${emye_c}),0)` |
| `退费人数` | `re_payer_4` | `measure` | `sum(8703823135205388)` |
| `退费占比` | `退费占比-退4` | `custom_measure` | `ifnull(sum(${refund_4})/sum(${income}),0)` |
| `期人效` | `期人效-退4` | `custom_measure` | `ifnull(sum(${promit_4})/sum(${emye_c}),0)` |
| `折算净收款` | `折算净收款-退4` | `custom_measure` | `ifnull(sum(${n_H_promit_4})*0.5 + sum(${H_promit_4}),0)` |
| `期目标` | `goal` | `measure` | `sum(8703823135205377)` |
| `期目标完成率` | `期目标完成率` | `custom_measure` | `ifnull(${折算净收款}/sum(${goal}),0)` |
| `净收款` | `promit` | `measure` | `sum(8703823135205382)` |
| `期目标完成率` | `期目标完成率-退4` | `custom_measure` | `ifnull(sum(${promit_4})/sum(${goal}),0)` |
| `折算净收款` | `折算净收款` | `custom_measure` | `sum(${H_promit})+sum(${n_H_promit})*0.5` |
| `团队人数` | `emye_c` | `measure` | `sum(8703694032168960)` |
| `营收金额` | `income` | `measure` | `sum(8703521624254466)` |
| `退费金额` | `refund` | `measure` | `sum(8703521624254467)` |
| `净收款` | `promit` | `measure` | `sum(8703521624254468)` |
| `破蛋人数` | `podan` | `measure` | `sum(8658235459921924)` |
| `退费人数` | `re_payer_4` | `measure` | `sum(8703521624254474)` |
| `月人效` | `月人效-退4` | `custom_measure` | `ifnull(sum(${promit_4})/sum(${emye_c}),0)` |
| `月目标` | `goal` | `measure` | `sum(8703694032168961)` |
| `月目标完成率` | `月目标完成率--退4` | `custom_measure` | `ifnull(${折算净收款-退4}/sum(${goal}),0)` |
| `退款金额` | `refund` | `measure` | `sum(8703521624254467)` |
| `折算净收款` | `折算净收款` | `custom_measure` | `sum(${H_promit})+sum(${n_H_promit})` |

## Text Notes Captured From Dashboard

1. 说明：<br>1. 小组、大组均剔除开课4节课后和点睛班开课2节课后退费       2. 一对一产出：退费永久回溯     3. 学部退费全部计算           4. 非H业务线按50%计算      5. 完成度 = 折算净收款/目标      <br>6. 破蛋人数 = 净收 > 0 顾问人数       7.   仅包含订单的课程类型为专题课和系列课的                8. 整点到整点15抽取截至两小时前的数据<br>注：绿色：破蛋率 ≥ 80%，退费占比 ≤ 10%，期目标完成度 ≥ 100%         红色：破蛋率 < 80%，退费占比 > 10%，期目标完成度 < 100%
2. 说明：<br>1. 小组、大组均剔除普通班开课4节课后和点睛班开课2节课后退费     2. 学部退费全部计算       3. 非H业务线按50%计算      4. 完成度 = 折算净收款/目标      <br>5. 破蛋人数 = 净收 > 0 顾问人数       6.   仅包含订单的课程类型为专题课和系列课的                7. 整点到整点15抽取截至两小时前的数据<br>注：绿色：破蛋率 ≥ 80%，退费占比 ≤ 10%，期目标完成度 ≥ 100%         红色：破蛋率 < 80%，退费占比 > 10%，期目标完成度 < 100%

## SQL Linkage Notes

- Frontend custom measures are calculated after the dataset SQL output is aggregated by the pivot dimensions. When debugging a metric, first verify the raw metric column in the linked source SQL, then verify the frontend formula in this file.
- `${metric}` references in formulas refer to BI model metrics, not physical SQL columns directly. Resolve them through the dataset model and source SQL listed above.
- Team completion uses separate monthly and period datasets; validate both `2677` and `2680` before changing shared completion formulas.
