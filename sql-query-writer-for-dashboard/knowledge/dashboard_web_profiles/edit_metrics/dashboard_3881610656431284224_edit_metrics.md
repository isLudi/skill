# 昆仑山战役-暑期激励数据看板 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3881610656431284224`
- dashboard_name: `昆仑山战役-暑期激励数据看板`
- captured_at: `2026-06-24 19:31:14`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3881610656431284224`
- loaded_html_id: `None`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3881610656431284224_edit_metrics_profile.json`
- pivot_units: `6`
- configured_fields: `56`
- measures: `24`
- custom_formulas: `0`
- text_notes: `3`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2727` | 暑期激励看板 | [data_center_market_2727_20260705.sql](../../../resources/raw_sql/data_center_market_2727_20260705.sql) | 2 |
| `2751` | 暑期激励v2 | [data_center_market_2751_20260705.sql](../../../resources/raw_sql/data_center_market_2751_20260705.sql) | 2 |
| `2842` | 暑期激励v3-月份 | [data_center_market_2842_20260705.sql](../../../resources/raw_sql/data_center_market_2842_20260705.sql) | 2 |

## Text units

- `unit_3881612212014751744`: 天级指标解读(数据更新截止两小时前)：<br>1. 净收款包含当期退费负值，退费为全量退费（含开课2节后退费）     2. 特殊渠道金额会有对应的系数折算，以下排名为参考数据 (主动咨询和亚飞99，测算主动咨询系数0.5，亚飞99系数0.7)
- `unit_3881612212014751744`: 指标解读(数据更新截止两小时前)：<br>1. 净收款包含当期退费负值，退费为全量退费（含开课2节后退费）     2. 特殊渠道金额会有对应的系数折算，以下排名为参考数据 (主动咨询和亚飞99，测算主动咨询系数0.5，亚飞99系数0.7)
- `unit_3890428705223966720`: 期次指标解读：<br>1.净GMV：包含当期退费负值，退费为全量退费（含开课2节后退费）  <br>2.目标完成度：部分渠道的单效目标无法拆开，以下排名为参考数据  <br>3.拓课率：数据一致的情况下，参考目标完成度、净GMV排名情况       <br>4. 参与评比条件：带班量≥20且完成度≥100%  <br>5.特殊渠道金额会有对应的系数折算，以下排名为参考数据（主动咨询和亚飞99，测算主动咨询系数0.5，亚飞99系数0.7）

## Pivot units

### 天级数据-西安

- unit_id: `unit_3890409769709219842`
- unit_type: `u_pivot`
- model: `2727` / 暑期激励看板
- dimensions: 顾问 / `name`; 主管 / `xiaozu`; 经理 / `jingli`; trade_date; dept; jingli
- measures: 排名 / `day_dept_period_rank_no`; 与上一名差值 / `day_dept_period_need_pmit_to_previous`

### 天级数据-郑州

- unit_id: `unit_3890469963619188736`
- unit_type: `u_pivot`
- model: `2727` / 暑期激励看板
- dimensions: 顾问 / `name`; 主管 / `xiaozu`; 经理 / `jingli`; trade_date; dept; jingli
- measures: 排名 / `day_dept_period_rank_no`; 与上一名差值 / `day_dept_period_need_pmit_to_previous`

### 期次数据-西安

- unit_id: `unit_3913361199684935681`
- unit_type: `u_pivot`
- model: `2751` / 暑期激励v2
- dimensions: 顾问 / `name`; 主管 / `zhuguan`; dept; jingli; qici
- measures: 收款目标 / `receive_target`; 目标完成度 / `target_completion_rate`; 排名 / `target_completion_period_dept_rank_no`; 差值 / `target_completion_gap_to_previous`; 拓课率 / `tuoke_rate`

### 月度数据-西安

- unit_id: `unit_3913379858514313219`
- unit_type: `u_pivot`
- model: `2842` / 暑期激励v3-月份
- dimensions: 顾问 / `name`; 主管 / `xiaozu`; dept; natural_month; jingli
- measures: 收款目标 / `receive_target`; 目标完成度 / `target_completion_rate`; 排名 / `target_completion_period_dept_rank_no`; 差值; 拓课率 / `tuoke_rate`

### 月度数据-郑州

- unit_id: `unit_3913387360440238081`
- unit_type: `u_pivot`
- model: `2842` / 暑期激励v3-月份
- dimensions: 顾问 / `name`; 主管 / `xiaozu`; dept; natural_month; jingli
- measures: 收款目标 / `receive_target`; 目标完成度 / `target_completion_rate`; 排名 / `target_completion_period_dept_rank_no`; 差值; 拓课率 / `tuoke_rate`

### 期次数据-郑州

- unit_id: `unit_3913378722861166595`
- unit_type: `u_pivot`
- model: `2751` / 暑期激励v2
- dimensions: 顾问 / `name`; 主管 / `zhuguan`; dept; jingli; qici
- measures: 收款目标 / `receive_target`; 目标完成度 / `target_completion_rate`; 排名 / `target_completion_period_dept_rank_no`; 差值 / `target_completion_gap_to_previous`; 拓课率 / `tuoke_rate`

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 排名 | day_dept_period_rank_no<br>`8727943220193282` | measure | sum(8727943220193282) |  |  | 天级数据-西安<br>天级数据-郑州 |
| 与上一名差值 | day_dept_period_need_pmit_to_previous<br>`8727943220193283` | measure | sum(8727943220193283) |  |  | 天级数据-西安<br>天级数据-郑州 |
| 收款目标 | receive_target<br>`8817105288980484` | measure | sum(8817105288980484) |  |  | 期次数据-西安<br>期次数据-郑州 |
| 目标完成度 | target_completion_rate<br>`8817105288980501` | measure | sum(8817105288980501) |  |  | 期次数据-西安<br>期次数据-郑州 |
| 排名 | target_completion_period_dept_rank_no<br>`8817105288980502` | measure | sum(8817105288980502) |  |  | 期次数据-西安<br>期次数据-郑州 |
| 差值 | target_completion_gap_to_previous<br>`8817105288980503` | measure | sum(8817105288980503) |  |  | 期次数据-西安<br>期次数据-郑州 |
| 拓课率 | tuoke_rate<br>`8817105288980504` | measure | sum(8817105288980504) |  |  | 期次数据-西安<br>期次数据-郑州 |
| 收款目标 | receive_target<br>`8817002150389772` | measure | sum(8817002150389772) |  |  | 月度数据-西安<br>月度数据-郑州 |
| 目标完成度 | target_completion_rate<br>`8817002150389789` | measure | sum(8817002150389789) |  |  | 月度数据-西安<br>月度数据-郑州 |
| 排名 | target_completion_period_dept_rank_no<br>`8817002150389790` | measure | sum(8817002150389790) |  |  | 月度数据-西安<br>月度数据-郑州 |
| 差值 | 差值<br>`8817002150389791` | measure | sum(8817002150389791) |  |  | 月度数据-西安<br>月度数据-郑州 |
| 拓课率 | tuoke_rate<br>`8817002150389792` | measure | sum(8817002150389792) |  |  | 月度数据-西安<br>月度数据-郑州 |
