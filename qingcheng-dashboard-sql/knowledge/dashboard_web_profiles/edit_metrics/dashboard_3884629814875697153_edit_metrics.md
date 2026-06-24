# 青-抖私-转化 edit-page metrics profile

## Snapshot

- generated_at: `2026-06-24 18:51:26`
- dashboard_id: `dashboard_3884629814875697153`
- source command: `usql-web-query-operator/scripts/read_dashboard.py profile-edit-dashboard`
- rendered dashboard profile: [view profile](../qingcheng_dousi_conversion_web_profile.md)
- runtime JSON: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-185115\dashboard_3884629814875697153_edit_metrics_profile.json`
- boundary: read-only extraction from dashboard config, unit details, model field details, and custom formulas; no save/publish/delete/create/update endpoint is called.

## Dataset Models

| model_id | model_name | source SQL |
|---:|---|---|
| 2740 | `抖私-转化` | [data_center_qingcheng_2740_20260624.sql](../../../resources/raw_sql/data_center_qingcheng_2740_20260624.sql) |

## Pivot Units

| unit_name | model_id | model_name | dimensions | measure_count | custom_formula_count |
|---|---:|---|---|---:|---:|
| `透视表` | 2740 | `抖私-转化` | channel_2, grade_list, name, qici, grade_list, channel_1, channel_2 | 14 | 10 |
| `透视表_副本` | 2740 | `抖私-转化` | name, channel_1, qici, grade_list, channel_1 | 2 | 0 |

## Measures And Formulas

| display_name | field_or_metric | role | formula_or_definition |
|---|---|---|---|
| `当期净收款` | `gmv_7` | `measure` | `sum(8709020796676096)` |
| `当期占比` | `当期占比` | `custom_measure` | `ifnull(sum(${gmv_7})/sum(${gmv_total}),0)` |
| `8_14天内收款占比` | `8_14天内收款占比` | `custom_measure` | `ifnull(sum(${gmv_14})/sum(${gmv_total}),0)` |
| `15_30天内收款占比` | `15_30天内收款占比` | `custom_measure` | `ifnull(sum(${gmv_30})/sum(${gmv_total}),0)` |
| `非30天内收款占比` | `非30天内收款占比` | `custom_measure` | `ifnull(sum(${gmv_n30})/sum(${gmv_total}),0)` |
| `下期线索当期占比` | `下期线索当期占比` | `custom_measure` | `ifnull(sum(${gmv_7_h})/sum(${gmv_total}),0)` |
| `净收款` | `gmv_total` | `measure` | `sum(8709020796676101)` |
| `当期退款` | `refund_7` | `measure` | `sum(8709020796676102)` |
| `当期退款占比` | `当期退款占比` | `custom_measure` | `ifnull(sum(${refund_7})/sum(${refund_total}),0)` |
| `8_14天内退款占比` | `8_14天内退款占比` | `custom_measure` | `ifnull(sum(${refund_14})/sum(${refund_total}),0)` |
| `15_30天内退款占比` | `15_30天内退款占比` | `custom_measure` | `ifnull(sum(${refund_30})/sum(${refund_total}),0)` |
| `非30天内退款占比` | `非30天内退款占比` | `custom_measure` | `ifnull(sum(${refund_n30})/sum(${refund_total}),0)` |
| `下期线索当期退款占比` | `下期线索当期退款占比` | `custom_measure` | `ifnull(sum(${refund_7_p})/sum(${refund_total}),0)` |
| `总退款` | `refund_total` | `measure` | `sum(8709020796676107)` |

## Text Notes Captured From Dashboard

1. 说明：1.  8_14天收款、退费对应上一期的净收、退款    2.  15_30天收款、退费对应上上一期的净收、退款     3.当期占比 = 当期净收款/期净收款   4.整点-整点15抽取两小时前的数据
2. 说明：1.  8_14天收款、退费对应上一期的净收、退款    2.  15_30天收款、退费对应上上一期的净收、退款

## SQL Linkage Notes

- Frontend custom measures are calculated after the dataset SQL output is aggregated by the pivot dimensions. When debugging a metric, first verify the raw metric column in the linked source SQL, then verify the frontend formula in this file.
- `${metric}` references in formulas refer to BI model metrics, not physical SQL columns directly. Resolve them through the dataset model and source SQL listed above.
