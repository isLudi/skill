# 转化数据看板 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3885764906392891392`
- dashboard_name: `转化数据看板`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:17:18`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `9b711e349c0a62878637a444b40d34f0870fc2956ae819dcfcad1f4f265a48d9`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3885764906392891392&htmlId=html_3983988768738189313`
- loaded_html_id: `html_3983988768738189313`
- config_html_id: `html_3983988803383140352`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-project\dashboard_3885764906392891392_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `9` / `239` / `216` / `126`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 9 | 9 | 9 | 465 | 216 | 7 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2460` | 转化数据 | 173805 | 9 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmoqwto591` | `unit_3885765321595432960` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 部门-总 | `node_ocmoqwto595` | `unit_3885799917415424001` | u_pivot | node_ocmoqwto597 / 758s | x=0, y=0, w=10, h=6 | False / False |
| 渠道-总 | `node_ocmoqwto596` | `unit_3885802565373767680` | u_pivot | node_ocmoqwto597 / e8at | x=0, y=0, w=10, h=6 | False / False |
|  | `node_ocmoqwto597` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=22, w=20, h=32 | False / False |
| 一级渠道-年级 | `node_ocmoqwto59b` | `unit_3885804389298036736` | u_pivot | node_ocmoqwto59e / e8at | x=0, y=0, w=10, h=10 | False / False |
| 一级渠道-主管 | `node_ocmoqwto59c` | `unit_3885807778524864512` | u_pivot | node_ocmoqwto59e / 758s | x=0, y=0, w=10, h=10 | False / False |
| 一级渠道-年级_副本_副本 | `node_ocmoqwto59d` | `unit_3885809281027678208` | u_pivot | node_ocmoqwto59l / e8at | x=0, y=0, w=10, h=11 | False / False |
| 一级渠道 | `node_ocmoqwto59e` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=54, w=20, h=51 | False / False |
| 二级渠道-年级 | `node_ocmoqwto59h` | `unit_3885812440113995776` | u_pivot | node_ocmoqwto59l / 758s | x=0, y=0, w=10, h=11 | False / False |
| 二级渠道-主管 | `node_ocmoqwto59i` | `unit_3885812858531909632` | u_pivot | node_ocmoqwto59l / a5io | x=0, y=0, w=10, h=11 | False / False |
| 伙伴数据 | `node_ocmoqwto59j` | `unit_3885813531449008129` | u_pivot | node_ocllzw8twf1 /  | x=0, y=162, w=20, h=54 | False / False |
| 二级渠道 | `node_ocmoqwto59l` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=105, w=20, h=57 | False / False |
| 指标卡组 | `node_ocmoqwto59p` | `unit_3885824427184324609` | card | node_ocllzw8twf1 /  | x=0, y=11, w=20, h=11 | False / False |
| 全局筛选器 | `node_ocmoqwto59q` | `public_filter_relation_3885825940437295104` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=7 | False / False |
| 渠道-大组 | `node_ocmpl68wj33` | `unit_3916477914471084040` | u_pivot | node_ocmoqwto597 / h15o | x=0, y=0, w=10, h=5 | False / False |

## Pivot units

### 渠道-总

- unit_id: `unit_3885802565373767680`
- model: `2460` / 转化数据
- dimensions: 渠道 / `channel_1`
- measures: 线索量 / `v_lead`; 当期人头转化数 / `p_pay_user`; 当期人头转化率; 综合人头转化数 / `pay_user`; 综合人头转化率; 当期订单转化数 / `p_pay_sub`; 当期订单转化率; 综合订单转化数 / `pay_sub`; 综合订单转化率; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费人数 / `refund_user`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI; 人效; 联报率; 客单价; 破蛋率; 平均成交周期(天)
- component: `node_ocmoqwto596` / `PivotTable`

### 部门-总

- unit_id: `unit_3885799917415424001`
- model: `2460` / 转化数据
- dimensions: 部门 / `dept_2`
- measures: 线索量 / `v_lead`; 当期人头转化数 / `p_pay_user`; 当期人头转化率; 综合人头转化数 / `pay_user`; 综合人头转化率; 当期订单转化数 / `p_pay_sub`; 当期订单转化率; 综合订单转化数 / `pay_sub`; 综合订单转化率; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费人数 / `refund_user`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI; 人效; 联报率; 客单价; 破蛋率; 平均成交周期(天)
- component: `node_ocmoqwto595` / `PivotTable`

### 渠道-大组

- unit_id: `unit_3916477914471084040`
- model: `2460` / 转化数据
- dimensions: 大组 / `dazu`
- measures: 线索量 / `v_lead`; 当期人头转化数 / `p_pay_user`; 当期人头转化率; 综合人头转化数 / `pay_user`; 综合人头转化率; 当期订单转化数 / `p_pay_sub`; 当期订单转化率; 综合订单转化数 / `pay_sub`; 综合订单转化率; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费人数 / `refund_user`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI; 人效; 联报率; 客单价; 破蛋率; 平均成交周期(天)
- component: `node_ocmpl68wj33` / `PivotTable`

### 一级渠道-年级

- unit_id: `unit_3885804389298036736`
- model: `2460` / 转化数据
- dimensions: 一级渠道 / `channel_1`; 年级 / `grade_1`
- measures: 线索量 / `v_lead`; 当期人头转化数 / `p_pay_user`; 当期人头转化率; 综合人头转化数 / `pay_user`; 综合人头转化率; 当期订单转化数 / `p_pay_sub`; 当期订单转化率; 综合订单转化数 / `pay_sub`; 综合订单转化率; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费人数 / `refund_user`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI; 人效; 联报率; 客单价; 破蛋率; 平均成交周期(天)
- component: `node_ocmoqwto59b` / `PivotTable`

### 一级渠道-主管

- unit_id: `unit_3885807778524864512`
- model: `2460` / 转化数据
- dimensions: 一级渠道 / `channel_1`; 主管 / `xiaozu`
- measures: 线索量 / `v_lead`; 当期人头转化数 / `p_pay_user`; 当期人头转化率; 综合人头转化数 / `pay_user`; 综合人头转化率; 当期订单转化数 / `p_pay_sub`; 当期订单转化率; 综合订单转化数 / `pay_sub`; 综合订单转化率; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费人数 / `refund_user`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI; 人效; 联报率; 客单价; 破蛋率; 平均成交周期(天)
- component: `node_ocmoqwto59c` / `PivotTable`

### 一级渠道-年级_副本_副本

- unit_id: `unit_3885809281027678208`
- model: `2460` / 转化数据
- dimensions: 二级渠道 / `channel_map_2`; 部门 / `dept_2`; channel_map_2
- measures: 线索量 / `v_lead`; 当期人头转化数 / `p_pay_user`; 当期人头转化率; 综合人头转化数 / `pay_user`; 综合人头转化率; 当期订单转化数 / `p_pay_sub`; 当期订单转化率; 综合订单转化数 / `pay_sub`; 综合订单转化率; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费人数 / `refund_user`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI; 人效; 联报率; 客单价; 破蛋率; 平均成交周期(天)
- component: `node_ocmoqwto59d` / `PivotTable`

### 二级渠道-年级

- unit_id: `unit_3885812440113995776`
- model: `2460` / 转化数据
- dimensions: 二级渠道 / `channel_map_2`; 年级 / `grade_1`; channel_map_2
- measures: 线索量 / `v_lead`; 当期人头转化数 / `p_pay_user`; 当期人头转化率; 综合人头转化数 / `pay_user`; 综合人头转化率; 当期订单转化数 / `p_pay_sub`; 当期订单转化率; 综合订单转化数 / `pay_sub`; 综合订单转化率; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费人数 / `refund_user`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI; 人效; 联报率; 客单价; 破蛋率; 平均成交周期(天)
- component: `node_ocmoqwto59h` / `PivotTable`

### 二级渠道-主管

- unit_id: `unit_3885812858531909632`
- model: `2460` / 转化数据
- dimensions: 二级渠道 / `channel_map_2`; 主管 / `xiaozu`; channel_map_2
- measures: 线索量 / `v_lead`; 当期人头转化数 / `p_pay_user`; 当期人头转化率; 综合人头转化数 / `pay_user`; 综合人头转化率; 当期订单转化数 / `p_pay_sub`; 当期订单转化率; 综合订单转化数 / `pay_sub`; 综合订单转化率; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费人数 / `refund_user`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI; 人效; 联报率; 客单价; 破蛋率; 平均成交周期(天)
- component: `node_ocmoqwto59i` / `PivotTable`

### 伙伴数据

- unit_id: `unit_3885813531449008129`
- model: `2460` / 转化数据
- dimensions: 伙伴数据 / `employee_email_name`; 渠道 / `channel_map_2`; 年级 / `grade_1`; grade_1; channel_map_2; xiaozu; employee_email_name
- measures: 线索量 / `v_lead`; 当期人头转化数 / `p_pay_user`; 当期人头转化率; 综合人头转化数 / `pay_user`; 综合人头转化率; 当期订单转化数 / `p_pay_sub`; 当期订单转化率; 综合订单转化数 / `pay_sub`; 综合订单转化率; 当期单效; 综合单效; 当期营收 / `p_income`; 往期营收; 综合营收 / `income`; 退费人数 / `refund_user`; 退费金额 / `refund`; 退费率; 净产出 / `promit`; ROI; 人效; 联报率; 客单价; 破蛋率; 平均成交周期(天)
- component: `node_ocmoqwto59j` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| ROI | ROI<br>`customized_990268902395158529` | custom_measure / measure | ifnull (sum(${promit})/${线索成本},0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052039"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_990268902277718017"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 人效 | 人效<br>`customized_990268902621650945` | custom_measure / measure | ifnull(sum(${promit})/${接量人力},0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052039"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_990268902508404736"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 客单价 | 客单价<br>`customized_990268902852337664` | custom_measure / measure | ifnull(sum(${promit})/sum(${pay_user}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052039"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052033"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 平均成交周期(天) | 平均成交周期(天)<br>`customized_990268902969778176` | custom_measure / measure | ifnull(sum(${sc})/sum(${pay_user}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052043"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052033"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 当期人头转化率 | 当期人头转化率<br>`customized_990268903083024385` | custom_measure / measure | ifnull(sum(${p_pay_user})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052034"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 当期单效 | 当期单效<br>`customized_990268903208853505` | custom_measure / measure | ifnull(sum(${p_income})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052040"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 当期订单转化率 | 当期订单转化率<br>`customized_990268903326294017` | custom_measure / measure | ifnull(sum(${p_pay_sub})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052036"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 往期营收 | 往期营收<br>`customized_990268903447928832` | custom_measure / measure | sum(${income})-sum(${p_income}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052037"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052040"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 破蛋率 | 破蛋率<br>`customized_990268903565369344` | custom_measure / measure | ifnull(sum(${podan})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052042"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 综合人头转化率 | 综合人头转化率<br>`customized_990268903678615553` | custom_measure / measure | ifnull(sum(${pay_user})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052033"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 综合单效 | 综合单效<br>`customized_990268903791861760` | custom_measure / measure | ifnull(sum(${promit})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052039"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 综合订单转化率 | 综合订单转化率<br>`customized_990268903905107969` | custom_measure / measure | ifnull(sum(${pay_sub})/sum(${v_lead}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052035"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052032"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 联报率 | 联报率<br>`customized_990268904018354176` | custom_measure / measure | ifnull(sum(${pay_sub})/sum(${pay_user}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052035"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052033"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 退费率 | 退费率<br>`customized_990268904131600385` | custom_measure / measure | ifnull(sum(${refund})/sum(${income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052038"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8626071195052037"}] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| channel_map_2 | channel_map_2<br>`374753` | dimension / filter |  |  | [] | 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| employee_email_name | employee_email_name<br>`408278` | dimension / filter |  |  | [] | 伙伴数据 |
| grade_1 | grade_1<br>`408277` | dimension / filter |  |  | [] | 伙伴数据 |
| xiaozu | xiaozu<br>`388420` | dimension / filter |  |  | [] | 伙伴数据 |
| 一级渠道 | channel_1<br>`408280` | dimension / row_dimension |  |  | [] | 一级渠道-年级, 一级渠道-主管 |
| 主管 | xiaozu<br>`388420` | dimension / row_dimension |  |  | [] | 一级渠道-主管, 二级渠道-主管 |
| 二级渠道 | channel_map_2<br>`374753` | dimension / row_dimension |  |  | [] | 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管 |
| 伙伴数据 | employee_email_name<br>`408278` | dimension / row_dimension |  |  | [] | 伙伴数据 |
| 大组 | dazu<br>`439812` | dimension / row_dimension |  |  | [] | 渠道-大组 |
| 年级 | grade_1<br>`408277` | dimension / row_dimension |  |  | [] | 一级渠道-年级, 二级渠道-年级, 伙伴数据 |
| 渠道 | channel_map_2<br>`374753` | dimension / row_dimension |  |  | [] | 伙伴数据 |
| 渠道 | channel_1<br>`408280` | dimension / row_dimension |  |  | [] | 渠道-总 |
| 部门 | dept_2<br>`408282` | dimension / row_dimension |  |  | [] | 部门-总, 一级渠道-年级_副本_副本 |
| 净产出 | promit<br>`8626071195052039` | measure / measure | sum(8626071195052039) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 当期人头转化数 | p_pay_user<br>`8626071195052034` | measure / measure | sum(8626071195052034) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 当期营收 | p_income<br>`8626071195052040` | measure / measure | sum(8626071195052040) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 当期订单转化数 | p_pay_sub<br>`8626071195052036` | measure / measure | sum(8626071195052036) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 线索量 | v_lead<br>`8626071195052032` | measure / measure | sum(8626071195052032) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 综合人头转化数 | pay_user<br>`8626071195052033` | measure / measure | sum(8626071195052033) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 综合营收 | income<br>`8626071195052037` | measure / measure | sum(8626071195052037) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 综合订单转化数 | pay_sub<br>`8626071195052035` | measure / measure | sum(8626071195052035) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 退费人数 | refund_user<br>`8626071195052041` | measure / measure | sum(8626071195052041) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |
| 退费金额 | refund<br>`8626071195052038` | measure / measure | sum(8626071195052038) |  | [] | 渠道-总, 部门-总, 渠道-大组, 一级渠道-年级, 一级渠道-主管, 一级渠道-年级_副本_副本, 二级渠道-年级, 二级渠道-主管, 伙伴数据 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3885825940437295106` | `public_filter_relation_3885825940437295104` | `408276` | qici | in / True | [] |
| `public_filter_3893071470464278529` | `public_filter_relation_3885825940437295104` | `408280` | channel_1 | in /  | [] |
| `public_filter_3893071470464278531` | `public_filter_relation_3885825940437295104` | `408277` | grade_1 | in /  | [] |
| `public_filter_3893072013679071233` | `public_filter_relation_3885825940437295104` | `408282` | dept_2 | in /  | [] |
| `public_filter_3893393842294693889` | `public_filter_relation_3885825940437295104` | `439812` | dazu | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3885809281027678208` | `374753` | channel_map_2 | in | ["detailFilter"] |
| `unit_3885812440113995776` | `374753` | channel_map_2 | in | ["detailFilter"] |
| `unit_3885812858531909632` | `374753` | channel_map_2 | in | ["detailFilter"] |
| `unit_3885813531449008129` | `374753` | channel_map_2 | in | ["detailFilter"] |
| `unit_3885813531449008129` | `388420` | xiaozu | in | ["detailFilter"] |
| `unit_3885813531449008129` | `408277` | grade_1 | in | ["detailFilter"] |
| `unit_3885813531449008129` | `408278` | employee_email_name | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
