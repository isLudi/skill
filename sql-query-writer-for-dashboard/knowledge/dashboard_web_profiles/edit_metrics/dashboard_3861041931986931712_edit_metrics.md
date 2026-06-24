# 多维度时效分析-抖咨 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3861041931986931712`
- dashboard_name: `多维度时效分析-抖咨`
- captured_at: `2026-06-24 19:30:37`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3861041931986931712&htmlId=html_3959903439716429825`
- loaded_html_id: `html_3959903439716429825`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3861041931986931712_edit_metrics_profile.json`
- pivot_units: `8`
- configured_fields: `46`
- measures: `24`
- custom_formulas: `8`
- text_notes: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2623` | 抖音私信- 分时间段 | [data_center_market_2623_20260624.sql](../../../resources/raw_sql/data_center_market_2623_20260624.sql) | 4 |
| `2625` | 分触达时间段--抖音咨询 | [data_center_market_2625_20260624.sql](../../../resources/raw_sql/data_center_market_2625_20260624.sql) | 4 |

## Pivot units

### 部门

- unit_id: `unit_3861063716424466433`
- unit_type: `u_pivot`
- model: `2623` / 抖音私信- 分时间段
- dimensions: 部门 / `depart`; 时间段 / `assign_day`
- measures: 有效例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效

### 经理

- unit_id: `unit_3861063388582449154`
- unit_type: `u_pivot`
- model: `2623` / 抖音私信- 分时间段
- dimensions: 经理 / `jingli_1`; 时间段 / `assign_day`
- measures: 有效例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效

### 顾问_副本

- unit_id: `unit_3861061473331204097`
- unit_type: `u_pivot`
- model: `2623` / 抖音私信- 分时间段
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 时间段 / `assign_day`
- measures: 有效例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效

### 顾问

- unit_id: `unit_3861044167111950336`
- unit_type: `u_pivot`
- model: `2623` / 抖音私信- 分时间段
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; 时间段 / `assign_day`
- measures: 有效例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效

### 部门

- unit_id: `unit_3861107228588707841`
- unit_type: `u_pivot`
- model: `2625` / 分触达时间段--抖音咨询
- dimensions: 部门 / `depart`; 触达时间 / `first_call_time_range`
- measures: 例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效

### 经理

- unit_id: `unit_3861108524580036608`
- unit_type: `u_pivot`
- model: `2625` / 分触达时间段--抖音咨询
- dimensions: 经理 / `jingli_1`; 触达时间 / `first_call_time_range`
- measures: 例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效

### 主管

- unit_id: `unit_3861106694555324416`
- unit_type: `u_pivot`
- model: `2625` / 分触达时间段--抖音咨询
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 触达时间 / `first_call_time_range`
- measures: 例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效

### 顾问

- unit_id: `unit_3861088496817307649`
- unit_type: `u_pivot`
- model: `2625` / 分触达时间段--抖音咨询
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; 触达时间 / `first_call_time_range`
- measures: 例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 有效例子 | can_renew_ds_count_a<br>`8612993576822785` | measure | sum(8612993576822785) |  |  | 部门<br>经理<br>顾问_副本<br>顾问 |
| 净收 | trade_profit<br>`8612993576822807` | measure | sum(8612993576822807) |  |  | 部门<br>经理<br>顾问_副本<br>顾问 |
| 单效 | 单效<br>`customized_965278615201628161` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8612993576822807', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8612993576822785', 'orgParamType': 1, 'needBoundaryValue': False} | 部门<br>经理<br>顾问_副本<br>顾问<br>主管 |
| 例子 | can_renew_ds_count_a<br>`8613174448580609` | measure | sum(8613174448580609) |  |  | 部门<br>经理<br>主管<br>顾问 |
| 净收 | trade_profit<br>`8613174448580631` | measure | sum(8613174448580631) |  |  | 部门<br>经理<br>主管<br>顾问 |
