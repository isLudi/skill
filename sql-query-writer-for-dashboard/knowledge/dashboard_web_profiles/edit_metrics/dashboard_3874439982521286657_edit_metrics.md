# 【新人】前期过程转化数据 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3874439982521286657`
- dashboard_name: `【新人】前期过程转化数据`
- captured_at: `2026-06-24 19:30:51`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3874439982521286657&htmlId=html_3959903676694605824`
- loaded_html_id: `html_3959903676694605824`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3874439982521286657_edit_metrics_profile.json`
- pivot_units: `1`
- configured_fields: `19`
- measures: `13`
- custom_formulas: `9`
- text_notes: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2688` | 新人过程转化数据 | [data_center_market_2688_20260624.sql](../../../resources/raw_sql/data_center_market_2688_20260624.sql) | 1 |

## Pivot units

### 新人过程-转化

- unit_id: `unit_3874462234150735872`
- unit_type: `u_pivot`
- model: `2688` / 新人过程转化数据
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; 期次 / `period_name`; 渠道 / `channel`; 承接期次 / `x_qi_count`
- measures: 例子 / `can_renew_ds_count_a`; 24h外呼; 48h外呼; 5min占比; 深沟率; AB意向; 课1到课; 截面人头转化; 净GMV / `trade_profit`; 目标 / `renchan`; 完成度; 退费金额 / `trade_refund`; 退费率

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 例子 | can_renew_ds_count_a<br>`8665335856261122` | measure | sum(8665335856261122) |  |  | 新人过程-转化 |
| 24h外呼 | 24h外呼<br>`customized_973619201136869377` | custom_measure | ifnull(sum(${first_call_24h})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8665335856261123', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8665335856261122', 'orgParamType': 1, 'needBoundaryValue': False} | 新人过程-转化 |
| 48h外呼 | 48h外呼<br>`customized_973619201245921281` | custom_measure | ifnull(sum(${first_call_48h})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8665335856261124', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8665335856261122', 'orgParamType': 1, 'needBoundaryValue': False} | 新人过程-转化 |
| 5min占比 | 5min占比<br>`customized_973619201350778880` | custom_measure | ifnull(sum(${long_call_5})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8665335856261129', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8665335856261122', 'orgParamType': 1, 'needBoundaryValue': False} | 新人过程-转化 |
| 深沟率 | 深沟率<br>`customized_973619201774403585` | custom_measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8665335856261126', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8665335856261122', 'orgParamType': 1, 'needBoundaryValue': False} | 新人过程-转化 |
| AB意向 | AB意向<br>`customized_973619201459830784` | custom_measure | ifnull(sum(${AB_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8665335856261127', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8665335856261122', 'orgParamType': 1, 'needBoundaryValue': False} | 新人过程-转化 |
| 课1到课 | 课1到课<br>`customized_973619201879261184` | custom_measure | ifnull(sum(${daoke_1})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8665335856261131', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8665335856261122', 'orgParamType': 1, 'needBoundaryValue': False} | 新人过程-转化 |
| 截面人头转化 | 截面人头转化<br>`customized_973619201669545984` | custom_measure | ifnull(sum(${pay_users})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8665335856261133', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8665335856261122', 'orgParamType': 1, 'needBoundaryValue': False} | 新人过程-转化 |
| 净GMV | trade_profit<br>`8665335856261144` | measure | sum(8665335856261144) |  |  | 新人过程-转化 |
| 目标 | renchan<br>`8665420527069184` | measure | sum(8665420527069184) |  |  | 新人过程-转化 |
| 完成度 | 完成度<br>`customized_973619201564688385` | custom_measure | ifnull(sum(${trade_profit})/sum(${renchan}),0) |  | {'paramId': '8665335856261144', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8665420527069184', 'orgParamType': 1, 'needBoundaryValue': False} | 新人过程-转化 |
| 退费金额 | trade_refund<br>`8665335856261143` | measure | sum(8665335856261143) |  |  | 新人过程-转化 |
| 退费率 | 退费率<br>`customized_973619201988313088` | custom_measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | {'paramId': '8665335856261143', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8665335856261142', 'orgParamType': 1, 'needBoundaryValue': False} | 新人过程-转化 |
