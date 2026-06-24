# 到课数据-顾问维度 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3706108893345009664`
- dashboard_name: `到课数据-顾问维度`
- captured_at: `2026-06-24 19:28:05`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3706108893345009664&htmlId=html_3959900639554478080`
- loaded_html_id: `html_3959900639554478080`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3706108893345009664_edit_metrics_profile.json`
- pivot_units: `1`
- configured_fields: `23`
- measures: `13`
- custom_formulas: `6`
- text_notes: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `1938` | 到课数据散装 | - | 1 |

## Pivot units

### 分渠道到课数据

- unit_id: `unit_3706154500070973441`
- unit_type: `u_pivot`
- model: `1938` / 到课数据散装
- dimensions: 部门 / `department`; 渠道 / `channel_map_1`; 年级 / `grade_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; qici; department; channel_map_1; xiaozu; employee_email_name
- measures: 带班 / `valid_lead_count`; 首日到课 / `learn_count1`; 首日到课率; 首日有效到课 / `valid_learn_count1`; 首日有效到课率; ab到课 / `ab_learn_count`; ab到课率; ab有效到课 / `ab_valid_learn_count`; ab有效到课率; 深沟到课 / `shengou_learn_count`; 深沟到课率; 双沟到课 / `shuangou_learn_count`; 双沟到课率

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 带班 | valid_lead_count<br>`8007791581095938` | measure | sum(8007791581095938) |  |  | 分渠道到课数据 |
| 首日到课 | learn_count1<br>`8007791581095942` | measure | sum(8007791581095942) |  |  | 分渠道到课数据 |
| 首日到课率 | 首日到课率<br>`customized_939645319868706816` | custom_measure | sum(${learn_count1})/sum(${valid_lead_count}) |  | {'paramId': '8007791581095942', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8007791581095938', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道到课数据 |
| 首日有效到课 | valid_learn_count1<br>`8007791581095943` | measure | sum(8007791581095943) |  |  | 分渠道到课数据 |
| 首日有效到课率 | 首日有效到课率<br>`customized_939645319977758720` | custom_measure | sum(${valid_learn_count1})/sum(${valid_lead_count}) |  | {'paramId': '8007791581095943', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8007791581095938', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道到课数据 |
| ab到课 | ab_learn_count<br>`8007791581095944` | measure | sum(8007791581095944) |  |  | 分渠道到课数据 |
| ab到课率 | ab到课率<br>`customized_939645319055011840` | custom_measure | sum(${ab_learn_count})/sum(${ab_intention_level}) |  | {'paramId': '8007791581095944', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8007791581095941', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道到课数据 |
| ab有效到课 | ab_valid_learn_count<br>`8007791581095945` | measure | sum(8007791581095945) |  |  | 分渠道到课数据 |
| ab有效到课率 | ab有效到课率<br>`customized_939645319168258049` | custom_measure | sum(${ab_valid_learn_count})/sum(${valid_lead_count}) |  | {'paramId': '8007791581095945', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8007791581095938', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道到课数据 |
| 深沟到课 | shengou_learn_count<br>`8007791581095946` | measure | sum(8007791581095946) |  |  | 分渠道到课数据 |
| 深沟到课率 | 深沟到课率<br>`customized_939645319411527681` | custom_measure | sum(${shengou_learn_count})/sum(${shengou}) |  | {'paramId': '8007791581095946', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8007791581095939', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道到课数据 |
| 双沟到课 | shuangou_learn_count<br>`8007791581095948` | measure | sum(8007791581095948) |  |  | 分渠道到课数据 |
| 双沟到课率 | 双沟到课率<br>`customized_939645319281504256` | custom_measure | sum(${shuangou_learn_count})/sum(${shuanggou}) |  | {'paramId': '8007791581095948', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8007791581095940', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道到课数据 |
