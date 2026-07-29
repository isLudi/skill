# KOC渠道播报数据 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3952506916510425088`
- dashboard_name: `KOC渠道播报数据`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:13:21`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `b220f27133548f95da621812df2a7c23becf62c35d635672d34762a40a09addb`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3952506916510425088&htmlId=html_3983984833988145152`
- loaded_html_id: `html_3983984833988145152`
- config_html_id: `html_3983984868297551873`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3952506916510425088_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `15` / `9` / `9`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 26 | 10 | 3 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2293` | 运营侧个人数据 | 178778 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmm36s5ul1` | `unit_3952507097704357888` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=9 | False / False |
| 经理 | `node_ocmm7hf7ce2` | `unit_3952507097704357895` | u_pivot | node_ocllzw8twf1 /  | x=0, y=9, w=20, h=96 | False / False |

## Pivot units

### 经理

- unit_id: `unit_3952507097704357895`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 渠道 / `channel_map`; 经理 / `jingli_11`; channel_map; 总退后线索; period_rank
- measures: 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 截面单效 / `单效`; 当期单效 / `单效(当期)`
- component: `node_ocmm7hf7ce2` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 48h外呼 | 48h外呼<br>`customized_995352756151390208` | custom_measure / measure | ifnull(sum(${first_call_in_48h})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8511077494122496"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理 |
| 5min | 5min<br>`customized_995352756277219328` | custom_measure / measure | ifnull(sum(${is_long_call})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8511077494122497"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理 |
| 双沟率 | 双沟率<br>`customized_995352757787168768` | custom_measure / measure | ifnull(sum(${shuanggou_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8511181621389312"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理 |
| 好友率 | 好友率<br>`customized_995352758047215616` | custom_measure / measure | sum(${friend_lead})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879234"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理 |
| 当期单效 | 单效(当期)<br>`customized_995352757661339648` | custom_measure / measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879251"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理 |
| 截面单效 | 单效<br>`customized_995352757531316225` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879249"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理 |
| 深沟率 | 深沟率<br>`customized_995352758667972608` | custom_measure / measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879235"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理 |
| 首call率 | 首call率<br>`customized_995352759678799873` | custom_measure / measure | ifnull(sum(${is_f_call})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8511077494122498"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理 |
| channel_map | channel_map<br>`319191` | dimension / filter |  |  | [] | 经理 |
| period_rank | period_rank<br>`8970420150429696` | dimension / filter |  |  | [] | 经理 |
| 总退后线索 | 总退后线索<br>`customized_995352758424702976` | dimension / filter | sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理 |
| 期 | period_name<br>`319190` | dimension / row_dimension |  |  | [] | 经理 |
| 渠道 | channel_map<br>`319191` | dimension / row_dimension |  |  | [] | 经理 |
| 经理 | jingli_11<br>`386283` | dimension / row_dimension |  |  | [] | 经理 |
| 退后线索 | can_renew_ds_count_a<br>`8337294278879233` | measure / measure | sum(8337294278879233) |  | [] | 经理 |

## Filters

### Public filters

- 无公共筛选器快照。

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3952507097704357895` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3952507097704357895` | `8970420150429696` | period_rank | <= | ["detailFilter"] |
| `unit_3952507097704357895` | `customized_995352758424702976` | 总退后线索 | > | ["aggregationFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
