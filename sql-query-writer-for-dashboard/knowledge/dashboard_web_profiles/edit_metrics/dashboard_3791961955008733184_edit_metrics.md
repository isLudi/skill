# 市场顾问-进量节奏 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3791961955008733184`
- dashboard_name: `市场顾问-进量节奏`
- captured_at: `2026-06-24 19:29:16`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3791961955008733184&htmlId=html_3959902087628849152`
- loaded_html_id: `html_3959902087628849152`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3791961955008733184_edit_metrics_profile.json`
- pivot_units: `1`
- configured_fields: `11`
- measures: `6`
- custom_formulas: `3`
- text_notes: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2307` | 进量节奏 | [lead_assign_plan_actual_valid_count.sql](../../../resources/raw_sql/lead_assign_plan_actual_valid_count.sql) | 1 |

## Pivot units

### 分渠道进量节奏

- unit_id: `unit_3903063829110960129`
- unit_type: `u_pivot`
- model: `2307` / 进量节奏
- dimensions: 渠道小类 / `qudao`; 年级 / `nianji`; group_period_name; qudao; jingli
- measures: 接量人力; 已分配 / `lead`; 分配目标 / `assign_lead_count`; 进量比例; 有效分配 / `valid_lead`; 有效留存

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 接量人力 | 接量人力<br>`customized_985199921158500353` | custom_measure | count(DISTINCT ${employee_email_name}) |  | {'paramId': '321703', 'orgParamType': 2, 'needBoundaryValue': False} | 分渠道进量节奏 |
| 已分配 | lead<br>`8346823364339712` | measure | sum(8346823364339712) |  |  | 分渠道进量节奏 |
| 分配目标 | assign_lead_count<br>`8343155372615682` | measure | sum(8343155372615682) |  |  | 分渠道进量节奏 |
| 进量比例 | 进量比例<br>`customized_985199921506627584` | custom_measure | ifnull (<br>    (<br>      sum(${lead}) / sum(${assign_lead_count})<br>    ),<br>    0<br>) |  | {'paramId': '8346823364339712', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8343155372615682', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道进量节奏 |
| 有效分配 | valid_lead<br>`8346823364339713` | measure | sum(8346823364339713) |  |  | 分渠道进量节奏 |
| 有效留存 | 有效留存<br>`customized_985199921267552257` | custom_measure | sum(${valid_lead})/sum(${assign_lead_count}) |  | {'paramId': '8346823364339713', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8343155372615682', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道进量节奏 |
