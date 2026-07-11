# 【暂停】IP_SEC伙伴_青橙 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3946302758716309505`
- dashboard_name: `【暂停】IP_SEC伙伴_青橙`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:31:17`
- menu_status: `paused`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `446becb4a93189ae13016a4835c098650e809dff9b68136318a08424961ffba4`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3946302758716309505&htmlId=html_3984002876508221440`
- loaded_html_id: `html_3984002876508221440`
- config_html_id: `html_3984002911159525377`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-broadcast\dashboard_3946302758716309505_rich.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `19` / `15` / `12`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 36 | 15 | 2 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2064` | 青橙-过程数据 | 177638 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 全局筛选器 | `node_ocml27f2x71` | `public_filter_relation_3946302787589898242` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=8, w=20, h=5 | False / False |
| IP渠道SEC伙伴数据 | `node_ocml27f2x77` | `unit_3946302787589898243` | u_pivot | node_ocllzw8twf1 /  | x=0, y=13, w=20, h=48 | False / False |
| 文本框 | `node_ocmlccg3q11` | `unit_3946302787589898246` | u_text | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=8 | False / False |

## Pivot units

### IP渠道SEC伙伴数据

- unit_id: `unit_3946302787589898243`
- model: `2064` / 青橙-过程数据
- dimensions: 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map_1; department
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 首call率 / `触达率`; 24h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml27f2x77` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 24h沟通率 | 24h沟通率<br>`customized_993898758144733185` | custom_measure / measure | sum(${first_call_connected_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100934"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 24h首call率 | 24h触达率<br>`customized_993898758266368000` | custom_measure / measure | sum(${first_call_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100931"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 8min | 8min<br>`customized_993898758622883841` | custom_measure / measure | sum(${is_long_call})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8190136223229952"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| APP率 | APP率<br>`customized_993898758744518656` | custom_measure / measure | sum(${is_app_denglu})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8149654467340288"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 外呼时长(min) | 线索外呼时长<br>`customized_993898759218475009` | custom_measure / measure | sum(${call_duration})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100937"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 外呼频次 | 线索外呼频次<br>`customized_993898759340109824` | custom_measure / measure | sum(${zong_call_ci})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100938"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 好友率 | 好友率<br>`customized_993898758861959168` | custom_measure / measure | sum(${is_friend_lead})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183691126073344"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 沟通率 | 沟通率<br>`customized_993898758975205377` | custom_measure / measure | sum(${first_call_connected_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100936"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 等待时长(h) | 用户平均等待时长<br>`customized_993898759096840192` | custom_measure / measure | sum(${first_call_time_diff_hour})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100930"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 首call率 | 触达率<br>`customized_993898759453356033` | custom_measure / measure | sum(${first_call_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100933"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 首节到课 | 首节到课<br>`customized_993898759574990848` | custom_measure / measure | sum(${daoke1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465921"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| 首节有效 | 首节有效<br>`customized_993898759692431360` | custom_measure / measure | sum(${valid_daoke_1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183652594509825"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | IP渠道SEC伙伴数据 |
| channel_map_1 | channel_map_1<br>`275417` | dimension / filter |  |  | [] | IP渠道SEC伙伴数据 |
| department | department<br>`275419` | dimension / filter |  |  | [] | IP渠道SEC伙伴数据 |
| 年级 | grade_1<br>`275418` | dimension / row_dimension |  |  | [] | IP渠道SEC伙伴数据 |
| 顾问 | employee_email_name<br>`275421` | dimension / row_dimension |  |  | [] | IP渠道SEC伙伴数据 |
| 8min人数 | is_long_call<br>`8190136223229952` | measure / measure | sum(8190136223229952) |  | [] | IP渠道SEC伙伴数据 |
| 总通时 | call_duration<br>`8116514943100937` | measure / measure | sum(8116514943100937) |  | [] | IP渠道SEC伙伴数据 |
| 线索量 | v_lead<br>`8376585136465920` | measure / measure | sum(8376585136465920) |  | [] | IP渠道SEC伙伴数据 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3946302787589898240` | `public_filter_relation_3946302787589898242` | `275415` | qici | in / True | [] |
| `public_filter_3946302787589898244` | `public_filter_relation_3946302787589898242` | `275417` | channel_map_1 | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3946302787589898243` | `275417` | channel_map_1 | in | ["detailFilter"] |
| `unit_3946302787589898243` | `275419` | department | in | ["detailFilter"] |

## Text units

- `unit_3946302787589898246`: 1.最新数据来自两小时前；<br>2.等待时长 = 从首次线索分配到首次首call的总时间间隔/线索数 (平均一个用户多久才被首call)<br>3.8min人数 = 通话时长>8min的用户数 (只要有一通电话>8min就算这个用户达标)<br>4.外呼频次 = 平均一个用户拨了几次电话
- `unit_3946302787589898246`: 1.最新数据来自两小时前；<br>2.等待时长 = 从分配到首call的总时间间隔/线索数 (平均一个用户多久才被首call)<br>3.8min人数 = 通话时长>8min的用户数 (只要有一通电话>8min就算这个用户达标)<br>4.外呼频次 = 平均一个用户拨了几次电话

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
