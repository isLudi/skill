# 多维度时效分析-抖咨 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3861041931986931712`
- dashboard_name: `多维度时效分析-抖咨`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:12:25`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `8ca31a4aa2b2f4e3adbc08b86fd2615d1d5f9f49f6fb4a415cadb74bc6de9f9d`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3861041931986931712&htmlId=html_3983983399720726529`
- loaded_html_id: `html_3983983399720726529`
- config_html_id: `html_3983983433868713984`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3861041931986931712_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `8` / `46` / `24` / `8`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 8 | 8 | 92 | 24 | 0 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2623` | 抖音私信- 分时间段 | 148192 | 4 |
| `2625` | 分触达时间段--抖音咨询 | 148193 | 4 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 顾问 | `node_ocmo2jh7831` | `unit_3861044167111950336` | u_pivot | node_ocmo2jh7834e / 17o | x=0, y=0, w=10, h=6 | False / False |
| 按点分时间段 | `node_ocmo2jh7834e` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=9, w=20, h=35 | False / False |
| 全局筛选器 | `node_ocmo2jh7834j` | `public_filter_relation_3861067180758081537` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=5 | False / False |
| 标题图 | `node_ocmo2jh7834k` | `unit_3861068961718165504` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 顾问_副本 | `node_ocmo2jh7835` | `unit_3861061473331204097` | u_pivot | node_ocmo2jh7834e / 3xy5 | x=0, y=0, w=10, h=6 | False / False |
| 经理 | `node_ocmo2jh7836` | `unit_3861063388582449154` | u_pivot | node_ocmo2jh7834e / l1cd | x=0, y=0, w=10, h=6 | False / False |
| 部门 | `node_ocmo2jh7837` | `unit_3861063716424466433` | u_pivot | node_ocmo2jh7834e / bm44 | x=0, y=0, w=10, h=6 | False / False |
| 顾问 | `node_ocmo2l2ll73` | `unit_3861088496817307649` | u_pivot | node_ocmo2l2ll77 / zgt | x=0, y=0, w=10, h=8 | False / False |
| 主管 | `node_ocmo2l2ll74` | `unit_3861106694555324416` | u_pivot | node_ocmo2l2ll77 / 6rpj | x=0, y=0, w=10, h=7 | False / False |
| 部门 | `node_ocmo2l2ll75` | `unit_3861107228588707841` | u_pivot | node_ocmo2l2ll77 / 37gh | x=0, y=0, w=10, h=7 | False / False |
| 经理 | `node_ocmo2l2ll76` | `unit_3861108524580036608` | u_pivot | node_ocmo2l2ll77 / ejft | x=0, y=0, w=10, h=7 | False / False |
| 触达时间段 | `node_ocmo2l2ll77` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=44, w=20, h=39 | False / False |

## Pivot units

### 部门

- unit_id: `unit_3861063716424466433`
- model: `2623` / 抖音私信- 分时间段
- dimensions: 部门 / `depart`; 时间段 / `assign_day`
- measures: 有效例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效
- component: `node_ocmo2jh7837` / `PivotTable`

### 经理

- unit_id: `unit_3861063388582449154`
- model: `2623` / 抖音私信- 分时间段
- dimensions: 经理 / `jingli_1`; 时间段 / `assign_day`
- measures: 有效例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效
- component: `node_ocmo2jh7836` / `PivotTable`

### 顾问_副本

- unit_id: `unit_3861061473331204097`
- model: `2623` / 抖音私信- 分时间段
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 时间段 / `assign_day`
- measures: 有效例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效
- component: `node_ocmo2jh7835` / `PivotTable`

### 顾问

- unit_id: `unit_3861044167111950336`
- model: `2623` / 抖音私信- 分时间段
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; 时间段 / `assign_day`
- measures: 有效例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效
- component: `node_ocmo2jh7831` / `PivotTable`

### 部门

- unit_id: `unit_3861107228588707841`
- model: `2625` / 分触达时间段--抖音咨询
- dimensions: 部门 / `depart`; 触达时间 / `first_call_time_range`
- measures: 例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效
- component: `node_ocmo2l2ll75` / `PivotTable`

### 经理

- unit_id: `unit_3861108524580036608`
- model: `2625` / 分触达时间段--抖音咨询
- dimensions: 经理 / `jingli_1`; 触达时间 / `first_call_time_range`
- measures: 例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效
- component: `node_ocmo2l2ll76` / `PivotTable`

### 主管

- unit_id: `unit_3861106694555324416`
- model: `2625` / 分触达时间段--抖音咨询
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 触达时间 / `first_call_time_range`
- measures: 例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效
- component: `node_ocmo2l2ll74` / `PivotTable`

### 顾问

- unit_id: `unit_3861088496817307649`
- model: `2625` / 分触达时间段--抖音咨询
- dimensions: 经理 / `jingli_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; 触达时间 / `first_call_time_range`
- measures: 例子 / `can_renew_ds_count_a`; 净收 / `trade_profit`; 单效
- component: `node_ocmo2l2ll73` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 单效 | 单效<br>`customized_965278615201628161` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8612993576822807"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8612993576822785"}] | 部门, 经理, 顾问_副本, 顾问 |
| 单效 | 单效<br>`customized_965278617529466880` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8613174448580631"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8613174448580609"}] | 部门, 经理, 主管, 顾问 |
| 主管 | xiaozu<br>`405164` | dimension / row_dimension |  |  | [] | 顾问_副本, 顾问 |
| 主管 | xiaozu<br>`405281` | dimension / row_dimension |  |  | [] | 主管, 顾问 |
| 时间段 | assign_day<br>`405161` | dimension / column_dimension |  |  | [] | 部门, 经理, 顾问_副本, 顾问 |
| 经理 | jingli_1<br>`405165` | dimension / row_dimension |  |  | [] | 经理, 顾问_副本, 顾问 |
| 经理 | jingli_1<br>`405282` | dimension / row_dimension |  |  | [] | 经理, 主管, 顾问 |
| 触达时间 | first_call_time_range<br>`405279` | dimension / column_dimension |  |  | [] | 部门, 经理, 主管, 顾问 |
| 部门 | depart<br>`405157` | dimension / row_dimension |  |  | [] | 部门 |
| 部门 | depart<br>`405275` | dimension / row_dimension |  |  | [] | 部门 |
| 顾问 | employee_email_name<br>`405160` | dimension / row_dimension |  |  | [] | 顾问 |
| 顾问 | employee_email_name<br>`405278` | dimension / row_dimension |  |  | [] | 顾问 |
| 例子 | can_renew_ds_count_a<br>`8613174448580609` | measure / measure | sum(8613174448580609) |  | [] | 部门, 经理, 主管, 顾问 |
| 净收 | trade_profit<br>`8612993576822807` | measure / measure | sum(8612993576822807) |  | [] | 部门, 经理, 顾问_副本, 顾问 |
| 净收 | trade_profit<br>`8613174448580631` | measure / measure | sum(8613174448580631) |  | [] | 部门, 经理, 主管, 顾问 |
| 有效例子 | can_renew_ds_count_a<br>`8612993576822785` | measure / measure | sum(8612993576822785) |  | [] | 部门, 经理, 顾问_副本, 顾问 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3861067180758081539` | `public_filter_relation_3861067180758081537` | `405153` | period_name | in / True | [] |

### Component filters

- 无组件级筛选器快照。

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
