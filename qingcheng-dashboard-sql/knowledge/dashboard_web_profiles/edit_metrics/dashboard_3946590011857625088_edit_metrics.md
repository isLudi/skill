# 【暂停】IP-主管-青橙 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3946590011857625088`
- dashboard_name: `【暂停】IP-主管-青橙`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:31:37`
- menu_status: `paused`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `4ec2b9dfd3c6dfba5b7384997d68d6f9c8c06e81a22ccb551b2100ef80b53c35`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3946590011857625088&htmlId=html_3984003203680710657`
- loaded_html_id: `html_3984003203680710657`
- config_html_id: `html_3984003238300667904`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-broadcast\dashboard_3946590011857625088_rich.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `20` / `17` / `14`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 38 | 17 | 2 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2064` | 青橙-过程数据 | 176476 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 全局筛选器 | `node_ocml27f2x71` | `public_filter_relation_3946590031168200708` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=11, w=20, h=5 | False / False |
| 标题图 | `node_ocml27f2x72` | `unit_3946590031168200705` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 文本框 | `node_ocml965uuw1` | `unit_3946590031168200721` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=7 | False / False |
| 二级-主管 | `node_ocmqevbxdq4` | `unit_3946590031168200720` | u_pivot | node_ocllzw8twf1 /  | x=0, y=16, w=20, h=44 | False / False |

## Pivot units

### 二级-主管

- unit_id: `unit_3946590031168200720`
- model: `2064` / 青橙-过程数据
- dimensions: 主管 / `xiaozu`; channel_map_1; department
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长 / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocmqevbxdq4` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 24h沟通率 | 24h沟通率<br>`customized_992884307209654273` | custom_measure / measure | sum(${first_call_connected_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100934"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 24h首call率 | 24h触达率<br>`customized_992884307318706177` | custom_measure / measure | sum(${first_call_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100931"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 48h沟通率 | 48h沟通率<br>`customized_992884307431952384` | custom_measure / measure | sum(${first_call_connected_in_48h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100935"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 48h首call率 | 48h触达率<br>`customized_992884307553587201` | custom_measure / measure | sum(${first_call_in_48h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100932"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 8min | 8min<br>`customized_992884307662639105` | custom_measure / measure | sum(${is_long_call})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8190136223229952"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| APP率 | APP率<br>`customized_992884307771691009` | custom_measure / measure | sum(${is_app_denglu})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8149654467340288"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 外呼时长 | 线索外呼时长<br>`customized_992884308203704320` | custom_measure / measure | sum(${call_duration})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100937"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 外呼频次 | 线索外呼频次<br>`customized_992884308308561921` | custom_measure / measure | sum(${zong_call_ci})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100938"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 好友率 | 好友率<br>`customized_992884307880742913` | custom_measure / measure | sum(${is_friend_lead})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183691126073344"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 沟通率 | 沟通率<br>`customized_992884307985600512` | custom_measure / measure | sum(${first_call_connected_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100936"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 等待时长(h) | 用户平均等待时长<br>`customized_992884308094652416` | custom_measure / measure | sum(${first_call_time_diff_hour})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100930"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 首call率 | 触达率<br>`customized_992884308417613825` | custom_measure / measure | sum(${first_call_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100933"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 首节到课 | 首节到课<br>`customized_992884308526665729` | custom_measure / measure | sum(${daoke1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465921"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| 首节有效 | 首节有效<br>`customized_992884308644106241` | custom_measure / measure | sum(${valid_daoke_1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183652594509825"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 二级-主管 |
| channel_map_1 | channel_map_1<br>`275417` | dimension / filter |  |  | [] | 二级-主管 |
| department | department<br>`275419` | dimension / filter |  |  | [] | 二级-主管 |
| 主管 | xiaozu<br>`275420` | dimension / row_dimension |  |  | [] | 二级-主管 |
| 8min人数 | is_long_call<br>`8190136223229952` | measure / measure | sum(8190136223229952) |  | [] | 二级-主管 |
| 总通时 | call_duration<br>`8116514943100937` | measure / measure | sum(8116514943100937) |  | [] | 二级-主管 |
| 线索量 | v_lead<br>`8376585136465920` | measure / measure | sum(8376585136465920) |  | [] | 二级-主管 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3946590031168200706` | `public_filter_relation_3946590031168200708` | `275415` | qici | in / True | [] |
| `public_filter_3946590031168200709` | `public_filter_relation_3946590031168200708` | `275417` | channel_map_1 | in /  | [] |
| `public_filter_3946590031168200711` | `public_filter_relation_3946590031168200708` | `275418` | grade_1 | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3946590031168200720` | `275417` | channel_map_1 | in | ["detailFilter"] |
| `unit_3946590031168200720` | `275419` | department | in | ["detailFilter"] |

## Text units

- `unit_3946590031168200721`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问<br>2.指标说明：等待时长 = 从分配到首call的总时间间隔/线索数 (平均一个用户多久才被首call); 8min人数 = 通话时长>8min的用户数 (只要有一通电话>8min就算这个用户达标)
- `unit_3946590031168200721`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问 ----2.指标计算：8min人数 = 通话时长>8min的用户数；

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
