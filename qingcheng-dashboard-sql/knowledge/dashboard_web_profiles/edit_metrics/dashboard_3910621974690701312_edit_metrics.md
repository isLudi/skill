# 青橙-渠道过程数据-天 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3910621974690701312`
- dashboard_name: `青橙-渠道过程数据-天`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:17:52`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `6836e24ffbac574e2572a9f5ec9e5b750da293f2fdc91c7fec6f9423e0ffe505`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3910621974690701312&htmlId=html_3983989365956800512`
- loaded_html_id: `html_3983989365956800512`
- config_html_id: `html_3983989397474783233`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-project\dashboard_3910621974690701312_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `4` / `81` / `68` / `56`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 4 | 4 | 158 | 68 | 3 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2064` | 青橙-过程数据 | 162313 | 4 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 全局筛选器 | `node_ocml27f2x71` | `public_filter_relation_3910621992189337604` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=11, w=20, h=5 | False / False |
| 标题图 | `node_ocml27f2x72` | `unit_3910621992189337601` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 伙伴数据 | `node_ocml27f2x77` | `unit_3910621992189337609` | u_pivot | node_ocllzw8twf1 /  | x=0, y=49, w=20, h=51 | False / False |
| 一级渠道数据 | `node_ocml28zcv28` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=16, w=20, h=33 | False / False |
| 渠道-整体 | `node_ocml28zcv2c` | `unit_3910621992189337610` | u_pivot | node_ocml28zcv28 / 2mql | x=0, y=0, w=10, h=6 | False / False |
| 渠道-年级 | `node_ocml28zcv2d` | `unit_3910621992189337611` | u_pivot | node_ocml28zcv28 / hqd2 | x=0, y=0, w=10, h=6 | False / False |
| 渠道-主管 | `node_ocml28zcv2e` | `unit_3910621992189337612` | u_pivot | node_ocml28zcv28 / al0s | x=0, y=0, w=10, h=19 | False / False |
| 文本框 | `node_ocml965uuw1` | `unit_3910621992189337617` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=7 | False / False |

## Pivot units

### 渠道-整体

- unit_id: `unit_3910621992189337610`
- model: `2064` / 青橙-过程数据
- dimensions: 分配时间 / `assign_day`; 部门 / `dept_2`
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2c` / `PivotTable`

### 渠道-年级

- unit_id: `unit_3910621992189337611`
- model: `2064` / 青橙-过程数据
- dimensions: 分配时间 / `assign_day`; 年级 / `grade_1`
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2d` / `PivotTable`

### 渠道-主管

- unit_id: `unit_3910621992189337612`
- model: `2064` / 青橙-过程数据
- dimensions: 分配时间 / `assign_day`; 年级 / `grade_1`; 主管 / `xiaozu`; department
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2e` / `PivotTable`

### 伙伴数据

- unit_id: `unit_3910621992189337609`
- model: `2064` / 青橙-过程数据
- dimensions: 分配时间 / `assign_day`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; grade_1; assign_day
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml27f2x77` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 24h沟通率 | 24h沟通率<br>`customized_977686986471313408` | custom_measure / measure | sum(${first_call_connected_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100934"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 24h首call率 | 24h触达率<br>`customized_977686986576171009` | custom_measure / measure | sum(${first_call_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100931"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 48h沟通率 | 48h沟通率<br>`customized_977686986681028608` | custom_measure / measure | sum(${first_call_connected_in_48h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100935"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 48h首call率 | 48h触达率<br>`customized_977686986785886209` | custom_measure / measure | sum(${first_call_in_48h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100932"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 8min | 8min<br>`customized_977686986894938113` | custom_measure / measure | sum(${is_long_call})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8190136223229952"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| APP率 | APP率<br>`customized_977686986999795712` | custom_measure / measure | sum(${is_app_denglu})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8149654467340288"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 外呼时长(min) | 线索外呼时长<br>`customized_977686987415031809` | custom_measure / measure | sum(${call_duration})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100937"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 外呼频次 | 线索外呼频次<br>`customized_977686987515695105` | custom_measure / measure | sum(${zong_call_ci})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100938"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 好友率 | 好友率<br>`customized_977686987104653313` | custom_measure / measure | sum(${is_friend_lead})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183691126073344"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 沟通率 | 沟通率<br>`customized_977686987209510912` | custom_measure / measure | sum(${first_call_connected_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100936"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 等待时长(h) | 用户平均等待时长<br>`customized_977686987310174208` | custom_measure / measure | sum(${first_call_time_diff_hour})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100930"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 首call率 | 触达率<br>`customized_977686987637329920` | custom_measure / measure | sum(${first_call_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100933"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 首节到课 | 首节到课<br>`customized_977686987746381824` | custom_measure / measure | sum(${daoke1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465921"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 首节有效 | 首节有效<br>`customized_977686987851239425` | custom_measure / measure | sum(${valid_daoke_1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183652594509825"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| assign_day | assign_day<br>`460871` | dimension / filter |  |  | [] | 伙伴数据 |
| department | department<br>`275419` | dimension / filter |  |  | [] | 渠道-主管 |
| grade_1 | grade_1<br>`275418` | dimension / filter |  |  | [] | 伙伴数据 |
| 主管 | xiaozu<br>`275420` | dimension / row_dimension |  |  | [] | 渠道-主管, 伙伴数据 |
| 分配时间 | assign_day<br>`460871` | dimension / row_dimension |  |  | [] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 年级 | grade_1<br>`275418` | dimension / row_dimension |  |  | [] | 渠道-年级, 渠道-主管 |
| 部门 | dept_2<br>`300907` | dimension / row_dimension |  |  | [] | 渠道-整体 |
| 顾问 | employee_email_name<br>`275421` | dimension / row_dimension |  |  | [] | 伙伴数据 |
| 8min人数 | is_long_call<br>`8190136223229952` | measure / measure | sum(8190136223229952) |  | [] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 总通时 | call_duration<br>`8116514943100937` | measure / measure | sum(8116514943100937) |  | [] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 线索量 | v_lead<br>`8376585136465920` | measure / measure | sum(8376585136465920) |  | [] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3910621992189337602` | `public_filter_relation_3910621992189337604` | `275415` | qici | in / True | [] |
| `public_filter_3910621992189337605` | `public_filter_relation_3910621992189337604` | `275417` | channel_map_1 | in /  | [] |
| `public_filter_3910737914853298177` | `public_filter_relation_3910621992189337604` | `281834` | channel_map_2 | in /  | [] |
| `public_filter_3910738353470111745` | `public_filter_relation_3910621992189337604` | `275418` | grade_1 | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3910621992189337609` | `275418` | grade_1 | in | ["detailFilter"] |
| `unit_3910621992189337609` | `460871` | assign_day | in | ["detailFilter"] |
| `unit_3910621992189337612` | `275419` | department | in | ["detailFilter"] |

## Text units

- `unit_3910621992189337617`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问<br>2.指标说明：等待时长 = 从分配到首call的总时间间隔/线索数 (平均一个用户多久才被首call); 8min人数 = 通话时长>8min的用户数 (只要有一通电话>8min就算这个用户达标)
- `unit_3910621992189337617`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问 ----2.指标计算：8min人数 = 通话时长>8min的用户数；

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
