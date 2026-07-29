# 【新人】前期过程转化数据 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3874439982521286657`
- dashboard_name: `【新人】前期过程转化数据`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:12:50`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `0c731358676217a8dbe3aa902a5f1c53487a3d3f6afcd96ae0e5b4416d242ba1`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3874439982521286657&htmlId=html_3983984322358726656`
- loaded_html_id: `html_3983984322358726656`
- config_html_id: `html_3983984322151923712`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3874439982521286657_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `19` / `13` / `9`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 38 | 13 | 0 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2688` | 新人过程转化数据 | 179080 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmofqxo4y1` | `unit_3874440144128913408` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 全局筛选器 | `node_ocmofqxo4y3` | `public_filter_relation_3874444624579076097` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=8 | False / False |
| 新人过程-转化 | `node_ocmofqxo4y4` | `unit_3874462234150735872` | u_pivot | node_ocllzw8twf1 /  | x=0, y=12, w=20, h=74 | False / False |

## Pivot units

### 新人过程-转化

- unit_id: `unit_3874462234150735872`
- model: `2688` / 新人过程转化数据
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; 期次 / `period_name`; 渠道 / `channel`; 承接期次 / `x_qi_count`
- measures: 例子 / `can_renew_ds_count_a`; 24h外呼; 48h外呼; 5min占比; 深沟率; AB意向; 课1到课; 截面人头转化; 净GMV / `trade_profit`; 目标 / `renchan`; 完成度; 退费金额 / `trade_refund`; 退费率
- component: `node_ocmofqxo4y4` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 24h外呼 | 24h外呼<br>`customized_995438272143302657` | custom_measure / measure | ifnull(sum(${first_call_24h})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261123"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261122"}] | 新人过程-转化 |
| 48h外呼 | 48h外呼<br>`customized_995438272260743169` | custom_measure / measure | ifnull(sum(${first_call_48h})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261124"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261122"}] | 新人过程-转化 |
| 5min占比 | 5min占比<br>`customized_995438272373989376` | custom_measure / measure | ifnull(sum(${long_call_5})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261129"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261122"}] | 新人过程-转化 |
| AB意向 | AB意向<br>`customized_995438272483041280` | custom_measure / measure | ifnull(sum(${AB_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261127"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261122"}] | 新人过程-转化 |
| 完成度 | 完成度<br>`customized_995438272596287489` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${renchan}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261144"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665420527069184"}] | 新人过程-转化 |
| 截面人头转化 | 截面人头转化<br>`customized_995438272705339393` | custom_measure / measure | ifnull(sum(${pay_users})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261133"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261122"}] | 新人过程-转化 |
| 深沟率 | 深沟率<br>`customized_995438272814391297` | custom_measure / measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261126"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261122"}] | 新人过程-转化 |
| 课1到课 | 课1到课<br>`customized_995438272927637504` | custom_measure / measure | ifnull(sum(${daoke_1})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261131"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261122"}] | 新人过程-转化 |
| 退费率 | 退费率<br>`customized_995438273040883713` | custom_measure / measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261143"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8665335856261142"}] | 新人过程-转化 |
| 主管 | xiaozu<br>`418294` | dimension / row_dimension |  |  | [] | 新人过程-转化 |
| 承接期次 | x_qi_count<br>`419801` | dimension / row_dimension |  |  | [] | 新人过程-转化 |
| 期次 | period_name<br>`418286` | dimension / row_dimension |  |  | [] | 新人过程-转化 |
| 渠道 | channel<br>`418296` | dimension / row_dimension |  |  | [] | 新人过程-转化 |
| 经理 | jingli_1<br>`418295` | dimension / row_dimension |  |  | [] | 新人过程-转化 |
| 顾问 | employee_email_name<br>`418291` | dimension / row_dimension |  |  | [] | 新人过程-转化 |
| 例子 | can_renew_ds_count_a<br>`8665335856261122` | measure / measure | sum(8665335856261122) |  | [] | 新人过程-转化 |
| 净GMV | trade_profit<br>`8665335856261144` | measure / measure | sum(8665335856261144) |  | [] | 新人过程-转化 |
| 目标 | renchan<br>`8665420527069184` | measure / measure | sum(8665420527069184) |  | [] | 新人过程-转化 |
| 退费金额 | trade_refund<br>`8665335856261143` | measure / measure | sum(8665335856261143) |  | [] | 新人过程-转化 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3874467006280187906` | `public_filter_relation_3874444624579076097` | `418288` | depart | in /  | [] |
| `public_filter_3874468094368301057` | `public_filter_relation_3874444624579076097` | `419801` | x_qi_count | in /  | [] |
| `public_filter_3874468094368301059` | `public_filter_relation_3874444624579076097` | `418291` | employee_email_name | in /  | [] |
| `public_filter_3894456876603875330` | `public_filter_relation_3874444624579076097` | `418295` | jingli_1 | in /  | [] |
| `public_filter_3894457220948746242` | `public_filter_relation_3874444624579076097` | `418294` | xiaozu | in /  | [] |
| `public_filter_3981707352826519553` | `public_filter_relation_3874444624579076097` | `418286` | period_name | in /  | [] |

### Component filters

- 无组件级筛选器快照。

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
