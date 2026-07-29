# 市场顾问-进量节奏 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3791961955008733184`
- dashboard_name: `市场顾问-进量节奏`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:10:06`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `5730b1e3edadb2a155598d21d206e73675a4b0280173e8e3a5692a61e94a2f81`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3791961955008733184&htmlId=html_3983981550880083969`
- loaded_html_id: `html_3983981550880083969`
- config_html_id: `html_3983981585418895360`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3791961955008733184_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `11` / `6` / `3`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 18 | 6 | 3 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2307` | 进量节奏 | 174171 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 分渠道进量节奏 | `node_ocmp7yogse13` | `unit_3903063829110960129` | u_pivot | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=78 | False / False |

## Pivot units

### 分渠道进量节奏

- unit_id: `unit_3903063829110960129`
- model: `2307` / 进量节奏
- dimensions: 渠道小类 / `qudao`; 年级 / `nianji`; group_period_name; qudao; jingli
- measures: 接量人力; 已分配 / `lead`; 分配目标 / `assign_lead_count`; 进量比例; 有效分配 / `valid_lead`; 有效留存
- component: `node_ocmp7yogse13` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 接量人力 | 接量人力<br>`customized_990631547941228545` | custom_measure / measure | count(DISTINCT ${employee_email_name}) |  | [{"needBoundaryValue": false, "orgParamType": 2, "paramId": "321703"}] | 分渠道进量节奏 |
| 有效留存 | 有效留存<br>`customized_990631548058669057` | custom_measure / measure | sum(${valid_lead})/sum(${assign_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8346823364339713"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8343155372615682"}] | 分渠道进量节奏 |
| 进量比例 | 进量比例<br>`customized_990631548293550081` | custom_measure / measure | ifnull (<br>    (<br>      sum(${lead}) / sum(${assign_lead_count})<br>    ),<br>    0<br>) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8346823364339712"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8343155372615682"}] | 分渠道进量节奏 |
| group_period_name | group_period_name<br>`321701` | dimension / filter |  |  | [] | 分渠道进量节奏 |
| jingli | jingli<br>`361906` | dimension / filter |  |  | [] | 分渠道进量节奏 |
| qudao | qudao<br>`361904` | dimension / filter |  |  | [] | 分渠道进量节奏 |
| 年级 | nianji<br>`398440` | dimension / row_dimension |  |  | [] | 分渠道进量节奏 |
| 渠道小类 | qudao<br>`361904` | dimension / row_dimension |  |  | [] | 分渠道进量节奏 |
| 分配目标 | assign_lead_count<br>`8343155372615682` | measure / measure | sum(8343155372615682) |  | [] | 分渠道进量节奏 |
| 已分配 | lead<br>`8346823364339712` | measure / measure | sum(8346823364339712) |  | [] | 分渠道进量节奏 |
| 有效分配 | valid_lead<br>`8346823364339713` | measure / measure | sum(8346823364339713) |  | [] | 分渠道进量节奏 |

## Filters

### Public filters

- 无公共筛选器快照。

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3903063829110960129` | `321701` | group_period_name | in | ["detailFilter"] |
| `unit_3903063829110960129` | `361904` | qudao | in | ["detailFilter"] |
| `unit_3903063829110960129` | `361906` | jingli | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
