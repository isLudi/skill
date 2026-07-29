# 到课数据-顾问维度 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3706108893345009664`
- dashboard_name: `到课数据-顾问维度`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:08:29`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `a00eb83a33b613a86d798c7e67d05c35af81f434bf1c1d97fa4f2416118b6dbf`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3706108893345009664&htmlId=html_3983979582843506689`
- loaded_html_id: `html_3983979582843506689`
- config_html_id: `html_3983979617431597057`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3706108893345009664_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `23` / `13` / `6`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 37 | 13 | 5 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `1938` | 到课数据散装 | 125721 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 分渠道到课数据 | `node_ocmjttcwpn2` | `unit_3706154500070973441` | u_pivot | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=67 | False / False |

## Pivot units

### 分渠道到课数据

- unit_id: `unit_3706154500070973441`
- model: `1938` / 到课数据散装
- dimensions: 部门 / `department`; 渠道 / `channel_map_1`; 年级 / `grade_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; qici; department; channel_map_1; xiaozu; employee_email_name
- measures: 带班 / `valid_lead_count`; 首日到课 / `learn_count1`; 首日到课率; 首日有效到课 / `valid_learn_count1`; 首日有效到课率; ab到课 / `ab_learn_count`; ab到课率; ab有效到课 / `ab_valid_learn_count`; ab有效到课率; 深沟到课 / `shengou_learn_count`; 深沟到课率; 双沟到课 / `shuangou_learn_count`; 双沟到课率
- component: `node_ocmjttcwpn2` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| ab到课率 | ab到课率<br>`customized_939645319055011840` | custom_measure / measure | sum(${ab_learn_count})/sum(${ab_intention_level}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095944"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095941"}] | 分渠道到课数据 |
| ab有效到课率 | ab有效到课率<br>`customized_939645319168258049` | custom_measure / measure | sum(${ab_valid_learn_count})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095945"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095938"}] | 分渠道到课数据 |
| 双沟到课率 | 双沟到课率<br>`customized_939645319281504256` | custom_measure / measure | sum(${shuangou_learn_count})/sum(${shuanggou}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095948"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095940"}] | 分渠道到课数据 |
| 深沟到课率 | 深沟到课率<br>`customized_939645319411527681` | custom_measure / measure | sum(${shengou_learn_count})/sum(${shengou}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095946"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095939"}] | 分渠道到课数据 |
| 首日到课率 | 首日到课率<br>`customized_939645319868706816` | custom_measure / measure | sum(${learn_count1})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095942"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095938"}] | 分渠道到课数据 |
| 首日有效到课率 | 首日有效到课率<br>`customized_939645319977758720` | custom_measure / measure | sum(${valid_learn_count1})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095943"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8007791581095938"}] | 分渠道到课数据 |
| channel_map_1 | channel_map_1<br>`257738` | dimension / filter |  |  | [] | 分渠道到课数据 |
| department | department<br>`257774` | dimension / filter |  |  | [] | 分渠道到课数据 |
| employee_email_name | employee_email_name<br>`257741` | dimension / filter |  |  | [] | 分渠道到课数据 |
| qici | qici<br>`298395` | dimension / filter |  |  | [] | 分渠道到课数据 |
| xiaozu | xiaozu<br>`257740` | dimension / filter |  |  | [] | 分渠道到课数据 |
| 主管 | xiaozu<br>`257740` | dimension / row_dimension |  |  | [] | 分渠道到课数据 |
| 年级 | grade_1<br>`257739` | dimension / row_dimension |  |  | [] | 分渠道到课数据 |
| 渠道 | channel_map_1<br>`257738` | dimension / row_dimension |  |  | [] | 分渠道到课数据 |
| 部门 | department<br>`257774` | dimension / row_dimension |  |  | [] | 分渠道到课数据 |
| 顾问 | employee_email_name<br>`257741` | dimension / row_dimension |  |  | [] | 分渠道到课数据 |
| ab到课 | ab_learn_count<br>`8007791581095944` | measure / measure | sum(8007791581095944) |  | [] | 分渠道到课数据 |
| ab有效到课 | ab_valid_learn_count<br>`8007791581095945` | measure / measure | sum(8007791581095945) |  | [] | 分渠道到课数据 |
| 双沟到课 | shuangou_learn_count<br>`8007791581095948` | measure / measure | sum(8007791581095948) |  | [] | 分渠道到课数据 |
| 带班 | valid_lead_count<br>`8007791581095938` | measure / measure | sum(8007791581095938) |  | [] | 分渠道到课数据 |
| 深沟到课 | shengou_learn_count<br>`8007791581095946` | measure / measure | sum(8007791581095946) |  | [] | 分渠道到课数据 |
| 首日到课 | learn_count1<br>`8007791581095942` | measure / measure | sum(8007791581095942) |  | [] | 分渠道到课数据 |
| 首日有效到课 | valid_learn_count1<br>`8007791581095943` | measure / measure | sum(8007791581095943) |  | [] | 分渠道到课数据 |

## Filters

### Public filters

- 无公共筛选器快照。

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3706154500070973441` | `257738` | channel_map_1 | in | ["detailFilter"] |
| `unit_3706154500070973441` | `257740` | xiaozu | in | ["detailFilter"] |
| `unit_3706154500070973441` | `257741` | employee_email_name | in | ["detailFilter"] |
| `unit_3706154500070973441` | `257774` | department | in | ["detailFilter"] |
| `unit_3706154500070973441` | `298395` | qici | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
