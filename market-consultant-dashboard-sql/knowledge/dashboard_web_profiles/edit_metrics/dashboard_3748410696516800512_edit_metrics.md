# 市场顾问部_行课报表 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3748410696516800512`
- dashboard_name: `市场顾问部_行课报表`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:08:58`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `35047483ede11df34c989d62042dc837b07a2e55af41be6e2a75f959bb64b68b`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3748410696516800512&htmlId=html_3983980401269534721`
- loaded_html_id: `html_3983980401269534721`
- config_html_id: `html_3983980435763613697`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3748410696516800512_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `3` / `49` / `39` / `36`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 3 | 3 | 93 | 39 | 3 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2132` | (内部)到课衰减情况 | 151972 | 3 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 渠道年级行课 | `node_ocmkzipfoe1` | `unit_3748421949431779328` | u_pivot | node_ocllzw8twf1 /  | x=0, y=9, w=20, h=31 | False / False |
| 标题图 | `node_ocmkzipfoe2` | `unit_3748416372584517632` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
|  | `node_ocmkzipfoe3` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=40, w=20, h=54 | False / False |
| 主管行课 | `node_ocmkzipfoe6` | `unit_3748425123565043713` | u_pivot | node_ocmkzipfoe3 / 1bvh | x=0, y=0, w=10, h=12 | False / False |
| 伙伴行课 | `node_ocmkzipfoe7` | `unit_3748430264775114753` | u_pivot | node_ocmkzipfoe3 / 41fr | x=0, y=0, w=10, h=12 | False / False |
| 全局筛选器 | `node_ocmkzipfoe8` | `public_filter_relation_3748432894568730625` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=5 | False / False |

## Pivot units

### 渠道年级行课

- unit_id: `unit_3748421949431779328`
- model: `2132` / (内部)到课衰减情况
- dimensions: 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 部门 / `department`
- measures: 应出勤人数 / `lead`; 课1; 课2; 课3; 课4; 课5; 课6; 课1有效; 课2有效; 课3有效; 课4有效; 课5有效; 课6有效
- component: `node_ocmkzipfoe1` / `PivotTable`

### 主管行课

- unit_id: `unit_3748425123565043713`
- model: `2132` / (内部)到课衰减情况
- dimensions: 主管 / `xiaozu`; department
- measures: 应出勤人数 / `lead`; 课1; 课2; 课3; 课4; 课5; 课6; 课1有效; 课2有效; 课3有效; 课4有效; 课5有效; 课6有效
- component: `node_ocmkzipfoe6` / `PivotTable`

### 伙伴行课

- unit_id: `unit_3748430264775114753`
- model: `2132` / (内部)到课衰减情况
- dimensions: 主管 / `xiaozu`; 顾问 / `employee_email_name`; 渠道 / `channel_map_1`; xiaozu; channel_map_1
- measures: 应出勤人数 / `lead`; 课1; 课2; 课3; 课4; 课5; 课6; 课1有效; 课2有效; 课3有效; 课4有效; 课5有效; 课6有效
- component: `node_ocmkzipfoe7` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 课1 | 课1<br>`customized_967822885842247680` | custom_measure / measure | sum(${ke_1})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029570"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课1有效 | 课1有效<br>`customized_967822885955493889` | custom_measure / measure | sum(${v_ke_1})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029576"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课2 | 课2<br>`customized_967822886064545793` | custom_measure / measure | sum(${ke_2})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029571"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课2有效 | 课2有效<br>`customized_967822886169403392` | custom_measure / measure | sum(${v_ke_2})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029577"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课3 | 课3<br>`customized_967822886274260993` | custom_measure / measure | sum(${ke_3})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029572"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课3有效 | 课3有效<br>`customized_967822886379118592` | custom_measure / measure | sum(${v_ke_3})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029578"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课4 | 课4<br>`customized_967822886483976193` | custom_measure / measure | sum(${ke_4})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029573"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课4有效 | 课4有效<br>`customized_967822886593028097` | custom_measure / measure | sum(${v_ke_4})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029579"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课5 | 课5<br>`customized_967822886706274304` | custom_measure / measure | sum(${ke_5})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029574"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课5有效 | 课5有效<br>`customized_967822886823714816` | custom_measure / measure | sum(${v_ke_5})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029580"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课6 | 课6<br>`customized_967822886941155328` | custom_measure / measure | sum(${ke_6})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029575"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| 课6有效 | 课6有效<br>`customized_967822887046012929` | custom_measure / measure | sum(${v_ke_6})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029581"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 渠道年级行课, 主管行课, 伙伴行课 |
| channel_map_1 | channel_map_1<br>`289671` | dimension / filter |  |  | [] | 伙伴行课 |
| department | department<br>`289674` | dimension / filter |  |  | [] | 主管行课 |
| xiaozu | xiaozu<br>`289673` | dimension / filter |  |  | [] | 伙伴行课 |
| 主管 | xiaozu<br>`289673` | dimension / row_dimension |  |  | [] | 主管行课, 伙伴行课 |
| 年级 | grade_1<br>`289672` | dimension / row_dimension |  |  | [] | 渠道年级行课 |
| 渠道 | channel_map_1<br>`289671` | dimension / row_dimension |  |  | [] | 伙伴行课 |
| 线索渠道 | channel_map_1<br>`289671` | dimension / row_dimension |  |  | [] | 渠道年级行课 |
| 部门 | department<br>`289674` | dimension / row_dimension |  |  | [] | 渠道年级行课 |
| 顾问 | employee_email_name<br>`289698` | dimension / row_dimension |  |  | [] | 伙伴行课 |
| 应出勤人数 | lead<br>`8172915650029568` | measure / measure | sum(8172915650029568) |  | [] | 渠道年级行课, 主管行课, 伙伴行课 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3748432894568730627` | `public_filter_relation_3748432894568730625` | `289670` | qici | in / True | [] |
| `public_filter_3748433929756512258` | `public_filter_relation_3748432894568730625` | `289671` | channel_map_1 | in /  | [] |
| `public_filter_3748434907281002497` | `public_filter_relation_3748432894568730625` | `289672` | grade_1 | in /  | [] |
| `public_filter_3854193547285311490` | `public_filter_relation_3748432894568730625` | `374265` | rule_name | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3748425123565043713` | `289674` | department | in | ["detailFilter"] |
| `unit_3748430264775114753` | `289671` | channel_map_1 | in | ["detailFilter"] |
| `unit_3748430264775114753` | `289673` | xiaozu | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
