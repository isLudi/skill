# 青橙-渠道过程数据-天 edit-page metrics profile

## Snapshot

- generated_at: `2026-06-24 18:52:12`
- dashboard_id: `dashboard_3910621974690701312`
- source command: `usql-web-query-operator/scripts/read_dashboard.py profile-edit-dashboard`
- rendered dashboard profile: [view profile](../qingcheng_channel_process_daily_web_profile.md)
- runtime JSON: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-185201\dashboard_3910621974690701312_edit_metrics_profile.json`
- boundary: read-only extraction from dashboard config, unit details, model field details, and custom formulas; no save/publish/delete/create/update endpoint is called.

## Dataset Models

| model_id | model_name | source SQL |
|---:|---|---|
| 2064 | `青橙-过程数据` | [data_center_qingcheng_2064_20260624.sql](../../../resources/raw_sql/data_center_qingcheng_2064_20260624.sql) |

## Pivot Units

| unit_name | model_id | model_name | dimensions | measure_count | custom_formula_count |
|---|---:|---|---|---:|---:|
| `渠道-整体` | 2064 | `青橙-过程数据` | assign_day, dept_2 | 17 | 14 |
| `渠道-年级` | 2064 | `青橙-过程数据` | assign_day, grade_1 | 17 | 14 |
| `渠道-主管` | 2064 | `青橙-过程数据` | assign_day, grade_1, xiaozu, department | 17 | 14 |
| `伙伴数据` | 2064 | `青橙-过程数据` | assign_day, xiaozu, employee_email_name, grade_1, assign_day | 17 | 14 |

## Measures And Formulas

| display_name | field_or_metric | role | formula_or_definition |
|---|---|---|---|
| `线索量` | `v_lead` | `measure` | `sum(8376585136465920)` |
| `好友率` | `好友率` | `custom_measure` | `sum(${is_friend_lead})/sum(${v_lead})` |
| `APP率` | `APP率` | `custom_measure` | `sum(${is_app_denglu})/sum(${v_lead})` |
| `等待时长(h)` | `用户平均等待时长` | `custom_measure` | `sum(${first_call_time_diff_hour})/sum(${v_lead})` |
| `8min人数` | `is_long_call` | `measure` | `sum(8190136223229952)` |
| `8min` | `8min` | `custom_measure` | `sum(${is_long_call})/sum(${v_lead})` |
| `24h首call率` | `24h触达率` | `custom_measure` | `sum(${first_call_in_24h})/sum(${v_lead})` |
| `48h首call率` | `48h触达率` | `custom_measure` | `sum(${first_call_in_48h})/sum(${v_lead})` |
| `首call率` | `触达率` | `custom_measure` | `sum(${first_call_cnt})/sum(${v_lead})` |
| `24h沟通率` | `24h沟通率` | `custom_measure` | `sum(${first_call_connected_in_24h})/sum(${v_lead})` |
| `48h沟通率` | `48h沟通率` | `custom_measure` | `sum(${first_call_connected_in_48h})/sum(${v_lead})` |
| `沟通率` | `沟通率` | `custom_measure` | `sum(${first_call_connected_cnt})/sum(${v_lead})` |
| `外呼时长(min)` | `线索外呼时长` | `custom_measure` | `sum(${call_duration})/sum(${v_lead})` |
| `外呼频次` | `线索外呼频次` | `custom_measure` | `sum(${zong_call_ci})/sum(${v_lead})` |
| `总通时` | `call_duration` | `measure` | `sum(8116514943100937)` |
| `首节到课` | `首节到课` | `custom_measure` | `sum(${daoke1})/sum(${v_lead})` |
| `首节有效` | `首节有效` | `custom_measure` | `sum(${valid_daoke_1})/sum(${v_lead})` |

## Text Notes Captured From Dashboard

1. 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问<br>2.指标说明：等待时长 = 从分配到首call的总时间间隔/线索数 (平均一个用户多久才被首call); 8min人数 = 通话时长>8min的用户数 (只要有一通电话>8min就算这个用户达标)
2. 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问 ----2.指标计算：8min人数 = 通话时长>8min的用户数；

## SQL Linkage Notes

- Frontend custom measures are calculated after the dataset SQL output is aggregated by the pivot dimensions. When debugging a metric, first verify the raw metric column in the linked source SQL, then verify the frontend formula in this file.
- `${metric}` references in formulas refer to BI model metrics, not physical SQL columns directly. Resolve them through the dataset model and source SQL listed above.
