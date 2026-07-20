# 个人转化数据-青橙 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3873038327756636161`
- dashboard_name: `个人转化数据-青橙`
- domain: `qingcheng`
- captured_at: `2026-07-18 22:25:37`
- menu_status: `1`
- profile_sha256: `5de1b435126ded6b9f52ec6adb6bf23829167c3d732f53823711e075b900f6e3`
- raw_profile: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-profile-20260718-class-refund\20260718-222526-23512-db63c873\dashboard_3873038327756636161_edit_metrics_profile.json`

## Model coverage

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2769` | 青橙个人转化 |  | 2 |

## Components and layout

| title | node_id | unit_id | type | parent / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 期产出 | `node_ocmodyldc81` | `unit_3873038340305993729` | u_pivot | node_ocllzw8twf1 /  | x=0, y=14, w=20, h=45 | False / False |
|  | `node_ocmodyldp41` | `unit_3873038340305993730` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 月度产出 | `node_ocmoy2u7kq1` | `unit_3893056410852823041` | u_pivot | node_ocllzw8twf1 /  | x=0, y=59, w=20, h=60 | False / False |
| 文本框 | `node_ocmoy9yi2l1` | `unit_3893236780015427585` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=10 | False / False |

## Pivot units

### 期产出

- unit_id: `unit_3873038340305993729`
- model: `2769` / 青橙个人转化
- dimensions: 顾问 / `name`; 小组 / `leader_employee_email_name`; 大组 / `dazu`; 学部 / `xuebu`; qici; xuebu; dazu; leader_employee_email_name
- measures: 净用户数 / `in_payer_4`; 班课营收; 班课退费; 班课净收; 折算后产出; 一对一营收 / `Y_income_4`; 一对一退费 / `Y_refund_4`; 一对一净收 / `Y_promit_4`; 累计净营收; 目标 / `qici_goal`; 完成度
- component: `node_ocmodyldc81` / `期产出`

### 月度产出

- unit_id: `unit_3893056410852823041`
- model: `2769` / 青橙个人转化
- dimensions: 顾问 / `name`; 部门 / `xuebu`; moth; xuebu; dazu; leader_employee_email_name; qici; data_level
- measures: 净用户数 / `in_payer_4`; 班课营收; 班课退费; 班课净收; 折算后产出; 档位最高金额; 跳档差值; 一对一营收 / `Y_income_4`; 一对一退费 / `Y_refund_4`; 一对一净收 / `Y_promit_4`; 累计净营收; 月度目标 / `moth_goal`; 完成度 / `月完成度`
- component: `node_ocmoy2u7kq1` / `月度产出`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 顾问 | name<br>`437991` | dimension / row_dimension |  |  |  | 期产出 |
| 小组 | leader_employee_email_name<br>`437992` | dimension / row_dimension |  |  |  | 期产出 |
| 大组 | dazu<br>`437993` | dimension / row_dimension |  |  |  | 期产出 |
| 学部 | xuebu<br>`437995` | dimension / row_dimension |  |  |  | 期产出 |
| 净用户数 | in_payer_4<br>`8743548131305472` | measure / measure | sum(8743548131305472) |  |  | 期产出 |
| 班课营收 | 班课营收<br>`customized_998715889501208577` | custom_measure / measure | ifnull(sum(${income})-sum(${Y_income_4}),0) |  | [{"paramId": "8737961276237826", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8737961276237833", "orgParamType": 1, "needBoundaryValue": false}] | 期产出 |
| 班课退费 | 班课退费<br>`customized_998715889606066176` | custom_measure / measure | ifnull(sum(${class_refund_4}), 0) |  | [{"paramId": "9135722004047872", "orgParamType": 1, "needBoundaryValue": false}] | 期产出 |
| 班课净收 | 班课净收<br>`customized_998715889710923777` | custom_measure / measure | ifnull(${班课营收}-${班课退费},0) |  | [{"paramId": "customized_998715889501208577", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715889606066176", "orgParamType": 4, "needBoundaryValue": false}] | 期产出 |
| 折算后产出 | 折算后产出<br>`customized_998715888951754752` | custom_measure / measure | ifnull(sum(${n_H_promit_4})*0.5 + (sum(${H_promit_4}) - sum(${Y_promit_4})),0) |  | [{"paramId": "8737961276237837", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8737961276237832", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8737961276237831", "orgParamType": 1, "needBoundaryValue": false}] | 期产出 |
| 一对一营收 | Y_income_4<br>`8737961276237833` | measure / measure | sum(8737961276237833) |  |  | 期产出 |
| 一对一退费 | Y_refund_4<br>`8737961276237835` | measure / measure | sum(8737961276237835) |  |  | 期产出 |
| 一对一净收 | Y_promit_4<br>`8737961276237831` | measure / measure | sum(8737961276237831) |  |  | 期产出 |
| 累计净营收 | 累计净营收<br>`customized_998715889060806656` | custom_measure / measure | ifnull(${折算后产出}+sum(${Y_promit_4}),0) |  | [{"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "8737961276237831", "orgParamType": 1, "needBoundaryValue": false}] | 期产出 |
| 目标 | qici_goal<br>`8931278683858944` | measure / measure | sum(8931278683858944) |  |  | 期产出 |
| 完成度 | 完成度<br>`customized_998715889178247168` | custom_measure / measure | ifnull(${累计净营收} / sum(${qici_goal}), 0) |  | [{"paramId": "customized_998715889060806656", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "8931278683858944", "orgParamType": 1, "needBoundaryValue": false}] | 期产出 |
| qici | qici<br>`437989` | dimension / filter |  |  |  | 期产出 |
| xuebu | xuebu<br>`437995` | dimension / filter |  |  |  | 期产出 |
| dazu | dazu<br>`437993` | dimension / filter |  |  |  | 期产出 |
| leader_employee_email_name | leader_employee_email_name<br>`437992` | dimension / filter |  |  |  | 期产出 |
| 部门 | xuebu<br>`437995` | dimension / row_dimension |  |  |  | 月度产出 |
| 档位最高金额 | 档位最高金额<br>`customized_998715889396350976` | custom_measure / measure | CASE<br>    WHEN ${折算后产出} >= 0 AND ${折算后产出} < 10000 THEN 10000<br>    WHEN ${折算后产出} >= 10000 AND ${折算后产出} < 40000 THEN 40000<br>    WHEN ${折算后产出} >= 40000 AND ${折算后产出} < 50000 THEN 50000<br>    WHEN ${折算后产出} >= 50000 AND ${折算后产出} < 60000 THEN 60000<br>    WHEN ${折算后产出} >= 60000 AND ${折算后产出} < 70000 THEN 70000<br>    WHEN ${折算后产出} >= 70000 AND ${折算后产出} < 80000 THEN 80000<br>    WHEN ${折算后产出} >= 80000 AND ${折算后产出} < 90000 THEN 90000<br>    WHEN ${折算后产出} >= 90000 AND ${折算后产出} < 100000 THEN 100000<br>    WHEN ${折算后产出} >= 100000 AND ${折算后产出} < 120000 THEN 120000<br>    WHEN ${折算后产出} >= 120000 AND ${折算后产出} < 130000 THEN 130000<br>    WHEN ${折算后产出} >= 130000 AND ${折算后产出} < 140000 THEN 140000<br>    WHEN ${折算后产出} >= 140000 AND ${折算后产出} < 160000 THEN 160000<br>    WHEN ${折算后产出} >= 160000 AND ${折算后产出} < 180000 THEN 180000<br>    WHEN ${折算后产出} >= 180000 AND ${折算后产出} < 200000 THEN 200000<br>    WHEN ${折算后产出} >= 200000 THEN 200000   <br>    ELSE 0<br>END  |  | [{"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}] | 月度产出 |
| 跳档差值 | 跳档差值<br>`customized_998715889815781376` | custom_measure / measure | ifnull(${档位最高金额}-${折算后产出},0) |  | [{"paramId": "customized_998715889396350976", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "customized_998715888951754752", "orgParamType": 4, "needBoundaryValue": false}] | 月度产出 |
| 月度目标 | moth_goal<br>`8931278683858945` | measure / measure | sum(8931278683858945) |  |  | 月度产出 |
| 完成度 | 月完成度<br>`customized_998715889287299072` | custom_measure / measure | ifnull(${累计净营收} / sum(${moth_goal}),0) |  | [{"paramId": "customized_998715889060806656", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "8931278683858945", "orgParamType": 1, "needBoundaryValue": false}] | 月度产出 |
| moth | moth<br>`437990` | dimension / filter |  |  |  | 月度产出 |
| data_level | data_level<br>`496578` | dimension / filter |  |  |  | 月度产出 |

## Dataset fields

### subject `183774`

| key | title | path | org_param_type | data_type |
|---|---|---|---|---|
| `437989` | qici | 维度 / qici | 2 | 2 |
| `437990` | moth | 维度 / moth | 2 | 2 |
| `437991` | name | 维度 / name | 2 | 2 |
| `437992` | leader_employee_email_name | 维度 / leader_employee_email_name | 2 | 2 |
| `437993` | dazu | 维度 / dazu | 2 | 2 |
| `437994` | jingli | 维度 / jingli | 2 | 2 |
| `437995` | xuebu | 维度 / xuebu | 2 | 2 |
| `496578` | data_level | 维度 / data_level | 2 | 2 |
| `8737961276237824` | H_promit | 指标 / H_promit | 1 | 1 |
| `8737961276237825` | n_H_promit | 指标 / n_H_promit | 1 | 1 |
| `8737961276237826` | income | 指标 / income | 1 | 1 |
| `8737961276237827` | refund | 指标 / refund | 1 | 1 |
| `8737961276237828` | promit | 指标 / promit | 1 | 1 |
| `8737961276237829` | re_payer | 指标 / re_payer | 1 | 1 |
| `8737961276237830` | podan | 指标 / podan | 1 | 1 |
| `8737961276237831` | Y_promit_4 | 指标 / Y_promit_4 | 1 | 1 |
| `8737961276237832` | H_promit_4 | 指标 / H_promit_4 | 1 | 1 |
| `8737961276237833` | Y_income_4 | 指标 / Y_income_4 | 1 | 1 |
| `8737961276237834` | H_income_4 | 指标 / H_income_4 | 1 | 1 |
| `8737961276237835` | Y_refund_4 | 指标 / Y_refund_4 | 1 | 1 |
| `8737961276237836` | H_refund_4 | 指标 / H_refund_4 | 1 | 1 |
| `8737961276237837` | n_H_promit_4 | 指标 / n_H_promit_4 | 1 | 1 |
| `8743548131305472` | in_payer_4 | 指标 / in_payer_4 | 1 | 1 |
| `8743548131305473` | j_sub | 指标 / j_sub | 1 | 1 |
| `8931278683858944` | qici_goal | 指标 / qici_goal | 1 | 1 |
| `8931278683858945` | moth_goal | 指标 / moth_goal | 1 | 1 |
| `9135722004047872` | class_refund_4 | 指标 / class_refund_4 | 1 | 1 |
| `customized_998715889178247168` | 完成度 | 指标 / 自定义指标 / 完成度 | 4 | 1 |
| `customized_998715888951754752` | 折算后产出 | 指标 / 自定义指标 / 折算后产出 | 4 | 1 |
| `customized_998715889287299072` | 月完成度 | 指标 / 自定义指标 / 月完成度 | 4 | 1 |
| `customized_998715889396350976` | 档位最高金额 | 指标 / 自定义指标 / 档位最高金额 | 4 | 1 |
| `customized_998715889710923777` | 班课净收 | 指标 / 自定义指标 / 班课净收 | 4 | 1 |
| `customized_998715889501208577` | 班课营收 | 指标 / 自定义指标 / 班课营收 | 4 | 1 |
| `customized_998715889606066176` | 班课退费 | 指标 / 自定义指标 / 班课退费 | 4 | 1 |
| `customized_998715889060806656` | 累计净营收 | 指标 / 自定义指标 / 累计净营收 | 4 | 1 |
| `customized_998715889815781376` | 跳档差值 | 指标 / 自定义指标 / 跳档差值 | 4 | 1 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3873038340305993729` | `437989` | qici | in | ["detailFilter"] |
| `unit_3873038340305993729` | `437992` | leader_employee_email_name | in | ["detailFilter"] |
| `unit_3873038340305993729` | `437993` | dazu | in | ["detailFilter"] |
| `unit_3873038340305993729` | `437995` | xuebu | in | ["detailFilter"] |
| `unit_3893056410852823041` | `437989` | qici | in | ["detailFilter"] |
| `unit_3893056410852823041` | `437990` | moth | = | ["detailFilter"] |
| `unit_3893056410852823041` | `437992` | leader_employee_email_name | in | ["detailFilter"] |
| `unit_3893056410852823041` | `437993` | dazu | in | ["detailFilter"] |
| `unit_3893056410852823041` | `437995` | xuebu | in | ["detailFilter"] |
| `unit_3893056410852823041` | `496578` | data_level | in | ["detailFilter"] |

## Text units

- `unit_3893236780015427585`: 说明：<br>1. 班课产出: 均剔除班课开课4节课后和点睛班开课2节课后退费     2. 一对一产出：退费永久回溯       3.仅包含订单的课程类型为专题课和系列课      4. 整点到整点15抽取截至两小时前的数据<br>注：绿色：折算后产出 ≥ 10000        橙色：0元 < 折算后产出 < 10000元         红色： 折算后产出 ≤ 0元
- `unit_3893236780015427585`: 说明：<br>1. 班课产出: 均剔除班课开课4节课后和点睛班开课2节课后退费     2. 一对一产出：退费永久回溯       3.仅包含订单的课程类型为专题课和系列课      4. 整点到整点15抽取截至两小时前的数据<br>注：绿色：折算后产出 ≥ 10000        橙色：0元 < 折算后产出 < 10000元         红色： 折算后产出 < 0元

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
