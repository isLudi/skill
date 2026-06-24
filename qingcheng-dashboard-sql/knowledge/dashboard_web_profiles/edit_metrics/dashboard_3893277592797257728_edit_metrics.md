# 完成度文字播报_青 edit-page metrics profile

## Snapshot

- generated_at: `2026-06-24 18:51:56`
- dashboard_id: `dashboard_3893277592797257728`
- source command: `usql-web-query-operator/scripts/read_dashboard.py profile-edit-dashboard`
- rendered dashboard profile: [view profile](../qingcheng_completion_broadcast_text_web_profile.md)
- runtime JSON: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-185147\dashboard_3893277592797257728_edit_metrics_profile.json`
- boundary: read-only extraction from dashboard config, unit details, model field details, and custom formulas; no save/publish/delete/create/update endpoint is called.

## Dataset Models

| model_id | model_name | source SQL |
|---:|---|---|
| - | Text-only broadcast dashboard; data is consumed through embedded text components rather than pivot units. | - |

## Pivot Units

| unit_name | model_id | model_name | dimensions | measure_count | custom_formula_count |
|---|---:|---|---|---:|---:|
| - | - | - | - | 0 | 0 |

## Measures And Formulas

| display_name | field_or_metric | role | formula_or_definition |
|---|---|---|---|
| - | - | - | - |

## Text Notes Captured From Dashboard

1. 🔈团队完成度看板已更新~<br>当前推送期次👉${430609}<br>每一次的进步都是大家跑出来战绩，祝本期爆单💰！！！
2. 🔈评优看板已更新~<br>当前推送期次👉${364758}<br>评优排名方式👉市场顾问部所有带班伙伴通排(排除主管)<br>优秀值得掌声，成长更需关注💕伙伴们上期辛苦啦~<br>昨天的最好表现是今天的最低要求，祝本期爆单💰！！！

## SQL Linkage Notes

- Frontend custom measures are calculated after the dataset SQL output is aggregated by the pivot dimensions. When debugging a metric, first verify the raw metric column in the linked source SQL, then verify the frontend formula in this file.
- `${metric}` references in formulas refer to BI model metrics, not physical SQL columns directly. Resolve them through the dataset model and source SQL listed above.
