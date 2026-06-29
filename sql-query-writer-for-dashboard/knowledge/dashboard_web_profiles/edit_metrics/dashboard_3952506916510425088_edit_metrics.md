# KOC渠道播报数据 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3952506916510425088`
- dashboard_name: `KOC渠道播报数据`
- captured_at: `2026-06-24 19:31:25`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3952506916510425088&htmlId=html_3959904240955252736`
- loaded_html_id: `html_3959904240955252736`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3952506916510425088_edit_metrics_profile.json`
- pivot_units: `1`
- configured_fields: `15`
- measures: `9`
- custom_formulas: `9`
- text_notes: `2`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2293` | 运营侧个人数据 | [data_center_market_2293_20260628.sql](../../../resources/raw_sql/data_center_market_2293_20260628.sql) | 1 |

## Text units

- `unit_3954147729620205569`: ${504041}<br>${504119}
- `unit_3954147729620205569`: 期次：${504041}<br>${504119}

## Pivot units

### 经理

- unit_id: `unit_3952507097704357895`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 渠道 / `channel_map`; 经理 / `jingli_11`; channel_map; 总退后线索; period_rank
- measures: 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 截面单效 / `单效`; 当期单效 / `单效(当期)`

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 退后线索 | can_renew_ds_count_a<br>`8337294278879233` | measure | sum(8337294278879233) |  |  | 经理 |
| 首call率 | 首call率<br>`customized_988807126647185408` | custom_measure | ifnull(sum(${is_f_call})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8511077494122498', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理 |
| 48h外呼 | 48h外呼<br>`customized_988807123618897920` | custom_measure | ifnull(sum(${first_call_in_48h})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8511077494122496', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理 |
| 5min | 5min<br>`customized_988807123723755521` | custom_measure | ifnull(sum(${is_long_call})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8511077494122497', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理 |
| 好友率 | 好友率<br>`customized_988807125212733440` | custom_measure | sum(${friend_lead})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8337294278879234', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理 |
| 深沟率 | 深沟率<br>`customized_988807125757992960` | custom_measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879235', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理 |
| 双沟率 | 双沟率<br>`customized_988807125011406848` | custom_measure | ifnull(sum(${shuanggou_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8511181621389312', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理 |
| 截面单效 | 单效<br>`customized_988807124805885953` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879249', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理 |
| 当期单效 | 单效(当期)<br>`customized_988807124906549249` | custom_measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879251', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理 |
