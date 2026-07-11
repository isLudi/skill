# 转化-抖音私信-主管 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3916517219847778305`
- dashboard_name: `转化-抖音私信-主管`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:30:21`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `47fb8a501e07c69a998cbb32792c139b47e83bfcc03a0ca3b01f408381e57258`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3916517219847778305&htmlId=html_3984001924756619265`
- loaded_html_id: `html_3984001924756619265`
- config_html_id: `html_3984001957240754177`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-broadcast\dashboard_3916517219847778305_rich.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `20` / `18` / `11`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 39 | 18 | 1 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2460` | 转化数据 | 172052 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmoqwto591` | `unit_3916517238537596929` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 伙伴数据 | `node_ocmoqwto59j` | `unit_3916517238537596930` | u_pivot | node_ocllzw8twf1 /  | x=0, y=9, w=20, h=21 | False / False |
| 全局筛选器 | `node_ocmoqwto59q` | `public_filter_relation_3916517238537596933` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=5 | False / False |

## Pivot units

### 伙伴数据

- unit_id: `unit_3916517238537596930`
- model: `2460` / 转化数据
- dimensions: 小组 / `xiaozu`; channel_1
- measures: 线索量 / `v_lead`; 人头转化数 / `pay_user`; 人头转化率 / `综合人头转化率`; 订单转化数 / `pay_sub`; 订单转化率 / `综合订单转化率`; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI 1 / `ROI`; 人效; 联报率; 客单价; 成交周期(天) / `平均成交周期(天)`
- component: `node_ocmoqwto59j` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| ROI 1 | ROI<br>`customized_988082716320301057` | custom_measure / measure | ifnull (sum(${promit})/${线索成本},0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052039"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_988082716198666240"}] | 伙伴数据 |
| 人头转化率 | 综合人头转化率<br>`customized_988082717654089729` | custom_measure / measure | ifnull(sum(${pay_user})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052033"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 伙伴数据 |
| 人效 | 人效<br>`customized_988082716563570689` | custom_measure / measure | ifnull(sum(${promit})/${接量人力},0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052039"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_988082716441935872"}] | 伙伴数据 |
| 客单价 | 客单价<br>`customized_988082716811034624` | custom_measure / measure | ifnull(sum(${promit})/sum(${pay_user}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052039"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052033"}] | 伙伴数据 |
| 当期单效 | 当期单效<br>`customized_988082717175939073` | custom_measure / measure | ifnull(sum(${p_income})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052040"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 伙伴数据 |
| 往期营收 | 往期营收<br>`customized_988082717419208705` | custom_measure / measure | sum(${income})-sum(${p_income}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052037"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052040"}] | 伙伴数据 |
| 成交周期(天) | 平均成交周期(天)<br>`customized_988082716932669441` | custom_measure / measure | ifnull(sum(${sc})/sum(${pay_user}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052043"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052033"}] | 伙伴数据 |
| 综合单效 | 综合单效<br>`customized_988082717775724544` | custom_measure / measure | ifnull(sum(${promit})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052039"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 伙伴数据 |
| 联报率 | 联报率<br>`customized_988082718014799873` | custom_measure / measure | ifnull(sum(${pay_sub})/sum(${pay_user}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052035"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052033"}] | 伙伴数据 |
| 订单转化率 | 综合订单转化率<br>`customized_988082717897359361` | custom_measure / measure | ifnull(sum(${pay_sub})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052035"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 伙伴数据 |
| 退费率 | 退费率<br>`customized_988082718132240385` | custom_measure / measure | ifnull(sum(${refund})/sum(${income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052038"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052037"}] | 伙伴数据 |
| channel_1 | channel_1<br>`408280` | dimension / filter |  |  | [] | 伙伴数据 |
| 小组 | xiaozu<br>`388420` | dimension / row_dimension |  |  | [] | 伙伴数据 |
| 人头转化数 | pay_user<br>`8626071195052033` | measure / measure | sum(8626071195052033) |  | [] | 伙伴数据 |
| 净产出 | promit<br>`8626071195052039` | measure / measure | sum(8626071195052039) |  | [] | 伙伴数据 |
| 当期营收 | p_income<br>`8626071195052040` | measure / measure | sum(8626071195052040) |  | [] | 伙伴数据 |
| 线索量 | v_lead<br>`8626071195052032` | measure / measure | sum(8626071195052032) |  | [] | 伙伴数据 |
| 综合营收 | income<br>`8626071195052037` | measure / measure | sum(8626071195052037) |  | [] | 伙伴数据 |
| 订单转化数 | pay_sub<br>`8626071195052035` | measure / measure | sum(8626071195052035) |  | [] | 伙伴数据 |
| 退费金额 | refund<br>`8626071195052038` | measure / measure | sum(8626071195052038) |  | [] | 伙伴数据 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3916517238537596931` | `public_filter_relation_3916517238537596933` | `408276` | qici | in / True | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3916517238537596930` | `408280` | channel_1 | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
