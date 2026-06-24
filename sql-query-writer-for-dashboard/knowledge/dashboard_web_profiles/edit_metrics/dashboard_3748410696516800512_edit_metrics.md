# 市场顾问部_行课报表 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3748410696516800512`
- dashboard_name: `市场顾问部_行课报表`
- captured_at: `2026-06-24 19:28:30`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3748410696516800512&htmlId=html_3959901298751660033`
- loaded_html_id: `html_3959901298751660033`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3748410696516800512_edit_metrics_profile.json`
- pivot_units: `3`
- configured_fields: `49`
- measures: `39`
- custom_formulas: `36`
- text_notes: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2132` | (内部)到课衰减情况 | [data_center_market_2132_20260624.sql](../../../resources/raw_sql/data_center_market_2132_20260624.sql) | 3 |

## Pivot units

### 渠道年级行课

- unit_id: `unit_3748421949431779328`
- unit_type: `u_pivot`
- model: `2132` / (内部)到课衰减情况
- dimensions: 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 部门 / `department`
- measures: 应出勤人数 / `lead`; 课1; 课2; 课3; 课4; 课5; 课6; 课1有效; 课2有效; 课3有效; 课4有效; 课5有效; 课6有效

### 主管行课

- unit_id: `unit_3748425123565043713`
- unit_type: `u_pivot`
- model: `2132` / (内部)到课衰减情况
- dimensions: 主管 / `xiaozu`; department
- measures: 应出勤人数 / `lead`; 课1; 课2; 课3; 课4; 课5; 课6; 课1有效; 课2有效; 课3有效; 课4有效; 课5有效; 课6有效

### 伙伴行课

- unit_id: `unit_3748430264775114753`
- unit_type: `u_pivot`
- model: `2132` / (内部)到课衰减情况
- dimensions: 主管 / `xiaozu`; 顾问 / `employee_email_name`; 渠道 / `channel_map_1`; xiaozu; channel_map_1
- measures: 应出勤人数 / `lead`; 课1; 课2; 课3; 课4; 课5; 课6; 课1有效; 课2有效; 课3有效; 课4有效; 课5有效; 课6有效

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 应出勤人数 | lead<br>`8172915650029568` | measure | sum(8172915650029568) |  |  | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课1 | 课1<br>`customized_967822885842247680` | custom_measure | sum(${ke_1})/sum(${lead}) |  | {'paramId': '8172915650029570', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课2 | 课2<br>`customized_967822886064545793` | custom_measure | sum(${ke_2})/sum(${lead}) |  | {'paramId': '8172915650029571', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课3 | 课3<br>`customized_967822886274260993` | custom_measure | sum(${ke_3})/sum(${lead}) |  | {'paramId': '8172915650029572', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课4 | 课4<br>`customized_967822886483976193` | custom_measure | sum(${ke_4})/sum(${lead}) |  | {'paramId': '8172915650029573', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课5 | 课5<br>`customized_967822886706274304` | custom_measure | sum(${ke_5})/sum(${lead}) |  | {'paramId': '8172915650029574', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课6 | 课6<br>`customized_967822886941155328` | custom_measure | sum(${ke_6})/sum(${lead}) |  | {'paramId': '8172915650029575', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课1有效 | 课1有效<br>`customized_967822885955493889` | custom_measure | sum(${v_ke_1})/sum(${lead}) |  | {'paramId': '8172915650029576', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课2有效 | 课2有效<br>`customized_967822886169403392` | custom_measure | sum(${v_ke_2})/sum(${lead}) |  | {'paramId': '8172915650029577', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课3有效 | 课3有效<br>`customized_967822886379118592` | custom_measure | sum(${v_ke_3})/sum(${lead}) |  | {'paramId': '8172915650029578', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课4有效 | 课4有效<br>`customized_967822886593028097` | custom_measure | sum(${v_ke_4})/sum(${lead}) |  | {'paramId': '8172915650029579', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课5有效 | 课5有效<br>`customized_967822886823714816` | custom_measure | sum(${v_ke_5})/sum(${lead}) |  | {'paramId': '8172915650029580', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
| 课6有效 | 课6有效<br>`customized_967822887046012929` | custom_measure | sum(${v_ke_6})/sum(${lead}) |  | {'paramId': '8172915650029581', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道年级行课<br>主管行课<br>伙伴行课 |
