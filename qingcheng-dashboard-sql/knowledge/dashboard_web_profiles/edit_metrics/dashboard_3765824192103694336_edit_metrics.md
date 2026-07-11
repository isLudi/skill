# 青橙项目部_行课报表 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3765824192103694336`
- dashboard_name: `青橙项目部_行课报表`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:15:01`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `de1f949478d2dc793e81939b7f11c3b1e92d9e467251708f16983929e4258207`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3765824192103694336&htmlId=html_3983986489822007297`
- loaded_html_id: `html_3983986489822007297`
- config_html_id: `html_3983986524315787265`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-project\dashboard_3765824192103694336_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `4` / `62` / `52` / `48`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 4 | 4 | 122 | 52 | 2 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2244` | 青橙到课 | 170126 | 4 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 渠道部门行课 | `node_ocmkzipfoe1` | `unit_3765824210457968641` | u_pivot | node_ocllzw8twf1 /  | x=0, y=9, w=20, h=33 | False / False |
| 标题图 | `node_ocmkzipfoe2` | `unit_3765824210457968640` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
|  | `node_ocmkzipfoe3` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=86, w=20, h=88 | False / False |
| 主管行课 | `node_ocmkzipfoe6` | `unit_3765824210457968642` | u_pivot | node_ocmkzipfoe3 / 1bvh | x=0, y=0, w=10, h=12 | False / False |
| 伙伴行课 | `node_ocmkzipfoe7` | `unit_3765824210457968645` | u_pivot | node_ocmkzipfoe3 / 41fr | x=0, y=0, w=10, h=18 | False / False |
| 全局筛选器 | `node_ocmkzipfoe8` | `public_filter_relation_3765824210457968649` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=5 | False / False |
| 渠道年级行课 | `node_ocmlhsj23n1` | `unit_3766965643325820932` | u_pivot | node_ocllzw8twf1 /  | x=0, y=42, w=20, h=44 | False / False |

## Pivot units

### 主管行课

- unit_id: `unit_3765824210457968642`
- model: `2244` / 青橙到课
- dimensions: 主管 / `xiaozu`; dept_2
- measures: 应出勤人数 / `lead`; 课1; 课1有效; 课2; 课2有效; 课3; 课3有效; 课4; 课4有效; 课5; 课5有效; 课6; 课6有效
- component: `node_ocmkzipfoe6` / `PivotTable`

### 伙伴行课

- unit_id: `unit_3765824210457968645`
- model: `2244` / 青橙到课
- dimensions: 顾问 / `employee_email_name`; 渠道 / `channel_map_2`; 年级 / `grade_1`; dept_2
- measures: 应出勤人数 / `lead`; 课1; 课1有效; 课2; 课2有效; 课3; 课3有效; 课4; 课4有效; 课5; 课5有效; 课6; 课6有效
- component: `node_ocmkzipfoe7` / `PivotTable`

### 渠道部门行课

- unit_id: `unit_3765824210457968641`
- model: `2244` / 青橙到课
- dimensions: 渠道 / `channel_map_2`; 部门 / `dept_2`
- measures: 应出勤人数 / `lead`; 课1; 课1有效; 课2; 课2有效; 课3; 课3有效; 课4; 课4有效; 课5; 课5有效; 课6; 课6有效
- component: `node_ocmkzipfoe1` / `PivotTable`

### 渠道年级行课

- unit_id: `unit_3766965643325820932`
- model: `2244` / 青橙到课
- dimensions: 渠道 / `channel_map_2`; 年级 / `grade_1`
- measures: 应出勤人数 / `lead`; 课1; 课1有效; 课2; 课2有效; 课3; 课3有效; 课4; 课4有效; 课5; 课5有效; 课6; 课6有效
- component: `node_ocmlhsj23n1` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 课1 | 课1<br>`customized_986290415573741568` | custom_measure / measure | sum(${ke_1})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549442"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课1有效 | 课1有效<br>`customized_986290415691182080` | custom_measure / measure | sum(${v_ke_1})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549448"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课2 | 课2<br>`customized_986290415800233984` | custom_measure / measure | sum(${ke_2})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549443"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课2有效 | 课2有效<br>`customized_986290415917674496` | custom_measure / measure | sum(${v_ke_2})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549449"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课3 | 课3<br>`customized_986290416030920705` | custom_measure / measure | sum(${ke_3})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549444"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课3有效 | 课3有效<br>`customized_986290416139972609` | custom_measure / measure | sum(${v_ke_3})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549450"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课4 | 课4<br>`customized_986290416253218816` | custom_measure / measure | sum(${ke_4})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549445"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课4有效 | 课4有效<br>`customized_986290416370659328` | custom_measure / measure | sum(${v_ke_4})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549451"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课5 | 课5<br>`customized_986290416483905537` | custom_measure / measure | sum(${ke_5})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549446"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课5有效 | 课5有效<br>`customized_986290416592957441` | custom_measure / measure | sum(${v_ke_5})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549452"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课6 | 课6<br>`customized_986290416706203648` | custom_measure / measure | sum(${ke_6})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549447"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 课6有效 | 课6有效<br>`customized_986290416827838465` | custom_measure / measure | sum(${v_ke_6})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549453"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8241056799549440"}] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |
| dept_2 | dept_2<br>`311120` | dimension / filter |  |  | [] | 主管行课, 伙伴行课 |
| 主管 | xiaozu<br>`310150` | dimension / row_dimension |  |  | [] | 主管行课 |
| 年级 | grade_1<br>`310149` | dimension / row_dimension |  |  | [] | 伙伴行课, 渠道年级行课 |
| 渠道 | channel_map_2<br>`310148` | dimension / row_dimension |  |  | [] | 伙伴行课, 渠道部门行课, 渠道年级行课 |
| 部门 | dept_2<br>`311120` | dimension / row_dimension |  |  | [] | 渠道部门行课 |
| 顾问 | employee_email_name<br>`310153` | dimension / row_dimension |  |  | [] | 伙伴行课 |
| 应出勤人数 | lead<br>`8241056799549440` | measure / measure | sum(8241056799549440) |  | [] | 主管行课, 伙伴行课, 渠道部门行课, 渠道年级行课 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3765824210457968647` | `public_filter_relation_3765824210457968649` | `310146` | qici | in / True | [] |
| `public_filter_3765824210457968650` | `public_filter_relation_3765824210457968649` | `310148` | channel_map_2 | in /  | [] |
| `public_filter_3765824210457968652` | `public_filter_relation_3765824210457968649` | `310149` | grade_1 | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3765824210457968642` | `311120` | dept_2 | in | ["detailFilter"] |
| `unit_3765824210457968645` | `311120` | dept_2 | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
