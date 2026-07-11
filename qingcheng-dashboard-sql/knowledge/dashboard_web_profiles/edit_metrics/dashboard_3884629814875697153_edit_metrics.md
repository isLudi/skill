# 青-抖私-转化 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3884629814875697153`
- dashboard_name: `青-抖私-转化`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:16:57`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `50ec4088e5f1d67d4ef46abba3e3e9c52a7f18d37f0ea48f3a55de6ca8f7b0a2`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3884629814875697153&htmlId=html_3983988432875102208`
- loaded_html_id: `html_3983988432875102208`
- config_html_id: `html_3983988466860257280`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-project\dashboard_3884629814875697153_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `2` / `28` / `16` / `10`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 2 | 2 | 46 | 16 | 7 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2740` | 抖私-转化 | 158117 | 2 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmoqrscvy1` | `unit_3885623155693903872` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 透视表 | `node_ocmoqrscvy2` | `unit_3885634016216997889` | u_pivot | node_ocllzw8twf1 /  | x=0, y=10, w=20, h=34 | False / False |
| 文本框 | `node_ocmor6k2is1` | `unit_3886043646744297473` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=6 | False / False |
| 透视表_副本 | `node_ocmoy908m31` | `unit_3893209576598749188` | u_pivot | node_ocllzw8twf1 /  | x=0, y=44, w=20, h=28 | False / False |

## Pivot units

### 透视表

- unit_id: `unit_3885634016216997889`
- model: `2740` / 抖私-转化
- dimensions: 渠道 / `channel_2`; 年级 / `grade_list`; 顾问 / `name`; qici; grade_list; channel_1; channel_2
- measures: 当期净收款 / `gmv_7`; 当期占比; 8_14天内收款占比; 15_30天内收款占比; 非30天内收款占比; 下期线索当期占比; 净收款 / `gmv_total`; 当期退款 / `refund_7`; 当期退款占比; 8_14天内退款占比; 15_30天内退款占比; 非30天内退款占比; 下期线索当期退款占比; 总退款 / `refund_total`
- component: `node_ocmoqrscvy2` / `PivotTable`

### 透视表_副本

- unit_id: `unit_3893209576598749188`
- model: `2740` / 抖私-转化
- dimensions: 顾问 / `name`; 渠道 / `channel_1`; qici; grade_list; channel_1
- measures: 净收款 / `gmv_total`; 总退款 / `refund_total`
- component: `node_ocmoy908m31` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 15_30天内收款占比 | 15_30天内收款占比<br>`customized_973629924776845312` | custom_measure / measure | ifnull(sum(${gmv_30})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676098"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676101"}] | 透视表 |
| 15_30天内退款占比 | 15_30天内退款占比<br>`customized_973629924877508608` | custom_measure / measure | ifnull(sum(${refund_30})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676104"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676107"}] | 透视表 |
| 8_14天内收款占比 | 8_14天内收款占比<br>`customized_973629924978171904` | custom_measure / measure | ifnull(sum(${gmv_14})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676097"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676101"}] | 透视表 |
| 8_14天内退款占比 | 8_14天内退款占比<br>`customized_973629925074640897` | custom_measure / measure | ifnull(sum(${refund_14})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676103"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676107"}] | 透视表 |
| 下期线索当期占比 | 下期线索当期占比<br>`customized_973629925175304193` | custom_measure / measure | ifnull(sum(${gmv_7_h})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676100"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676101"}] | 透视表 |
| 下期线索当期退款占比 | 下期线索当期退款占比<br>`customized_973629925275967489` | custom_measure / measure | ifnull(sum(${refund_7_p})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676106"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676107"}] | 透视表 |
| 当期占比 | 当期占比<br>`customized_973629925380825088` | custom_measure / measure | ifnull(sum(${gmv_7})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676096"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676101"}] | 透视表 |
| 当期退款占比 | 当期退款占比<br>`customized_973629925481488384` | custom_measure / measure | ifnull(sum(${refund_7})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676102"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676107"}] | 透视表 |
| 非30天内收款占比 | 非30天内收款占比<br>`customized_973629925582151680` | custom_measure / measure | ifnull(sum(${gmv_n30})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676099"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676101"}] | 透视表 |
| 非30天内退款占比 | 非30天内退款占比<br>`customized_973629925687009281` | custom_measure / measure | ifnull(sum(${refund_n30})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676105"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8709020796676107"}] | 透视表 |
| channel_1 | channel_1<br>`431249` | dimension / filter |  |  | [] | 透视表, 透视表_副本 |
| channel_2 | channel_2<br>`441233` | dimension / filter |  |  | [] | 透视表 |
| grade_list | grade_list<br>`431251` | dimension / filter |  |  | [] | 透视表, 透视表_副本 |
| qici | qici<br>`431248` | dimension / filter |  |  | [] | 透视表, 透视表_副本 |
| 年级 | grade_list<br>`431251` | dimension / row_dimension |  |  | [] | 透视表 |
| 渠道 | channel_1<br>`431249` | dimension / column_dimension |  |  | [] | 透视表_副本 |
| 渠道 | channel_2<br>`441233` | dimension / row_dimension |  |  | [] | 透视表 |
| 顾问 | name<br>`431252` | dimension / row_dimension |  |  | [] | 透视表, 透视表_副本 |
| 净收款 | gmv_total<br>`8709020796676101` | measure / measure | sum(8709020796676101) |  | [] | 透视表, 透视表_副本 |
| 当期净收款 | gmv_7<br>`8709020796676096` | measure / measure | sum(8709020796676096) |  | [] | 透视表 |
| 当期退款 | refund_7<br>`8709020796676102` | measure / measure | sum(8709020796676102) |  | [] | 透视表 |
| 总退款 | refund_total<br>`8709020796676107` | measure / measure | sum(8709020796676107) |  | [] | 透视表, 透视表_副本 |

## Filters

### Public filters

- 无公共筛选器快照。

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3885634016216997889` | `431248` | qici | in | ["detailFilter"] |
| `unit_3885634016216997889` | `431249` | channel_1 | in | ["detailFilter"] |
| `unit_3885634016216997889` | `431251` | grade_list | in | ["detailFilter"] |
| `unit_3885634016216997889` | `441233` | channel_2 | in | ["detailFilter"] |
| `unit_3893209576598749188` | `431248` | qici | in | ["detailFilter"] |
| `unit_3893209576598749188` | `431249` | channel_1 | in | ["detailFilter"] |
| `unit_3893209576598749188` | `431251` | grade_list | in | ["detailFilter"] |

## Text units

- `unit_3886043646744297473`: 说明：1.  8_14天收款、退费对应上一期的净收、退款    2.  15_30天收款、退费对应上上一期的净收、退款     3.当期占比 = 当期净收款/期净收款   4.整点-整点15抽取两小时前的数据
- `unit_3886043646744297473`: 说明：1.  8_14天收款、退费对应上一期的净收、退款    2.  15_30天收款、退费对应上上一期的净收、退款

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
