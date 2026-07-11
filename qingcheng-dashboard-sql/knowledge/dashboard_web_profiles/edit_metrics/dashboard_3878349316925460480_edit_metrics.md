# 过程-抖音私信-伙伴 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3878349316925460480`
- dashboard_name: `过程-抖音私信-伙伴`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:29:46`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `017eba428bd6c24f8b15558473fb7cf2deac379c6b0e1181445aad755bae5233`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3878349316925460480&htmlId=html_3984001353053122561`
- loaded_html_id: `html_3984001353053122561`
- config_html_id: `html_3984001387885707265`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-broadcast\dashboard_3878349316925460480_rich.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `18` / `15` / `12`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 35 | 15 | 1 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2064` | 青橙-过程数据 | 177025 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 全局筛选器 | `node_ocml27f2x71` | `public_filter_relation_3878349334709309442` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=8, w=20, h=5 | False / False |
| 抖音私信-渠道伙伴数据 | `node_ocml27f2x77` | `unit_3878349334709309443` | u_pivot | node_ocllzw8twf1 /  | x=0, y=13, w=20, h=29 | False / False |
| 文本框 | `node_ocmlccg3q11` | `unit_3878349334709309446` | u_text | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=8 | False / False |

## Pivot units

### 抖音私信-渠道伙伴数据

- unit_id: `unit_3878349334709309443`
- model: `2064` / 青橙-过程数据
- dimensions: 顾问 / `employee_email_name`; 年级 / `grade_1`; channel_map_2
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 首call率 / `触达率`; 24h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml27f2x77` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 24h沟通率 | 24h沟通率<br>`customized_993518983081308160` | custom_measure / measure | sum(${first_call_connected_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100934"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 24h首call率 | 24h触达率<br>`customized_993518983190360064` | custom_measure / measure | sum(${first_call_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100931"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 8min | 8min<br>`customized_993518983517515776` | custom_measure / measure | sum(${is_long_call})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8190136223229952"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| APP率 | APP率<br>`customized_993518983626567680` | custom_measure / measure | sum(${is_app_denglu})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8149654467340288"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 外呼时长(min) | 线索外呼时长<br>`customized_993518984071163904` | custom_measure / measure | sum(${call_duration})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100937"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 外呼频次 | 线索外呼频次<br>`customized_993518984180215808` | custom_measure / measure | sum(${zong_call_ci})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100938"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 好友率 | 好友率<br>`customized_993518983735619584` | custom_measure / measure | sum(${is_friend_lead})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183691126073344"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 沟通率 | 沟通率<br>`customized_993518983857254401` | custom_measure / measure | sum(${first_call_connected_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100936"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 等待时长(h) | 用户平均等待时长<br>`customized_993518983966306305` | custom_measure / measure | sum(${first_call_time_diff_hour})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100930"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 首call率 | 触达率<br>`customized_993518984289267712` | custom_measure / measure | sum(${first_call_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100933"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 首节到课 | 首节到课<br>`customized_993518984402513921` | custom_measure / measure | sum(${daoke1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465921"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| 首节有效 | 首节有效<br>`customized_993518984515760128` | custom_measure / measure | sum(${valid_daoke_1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183652594509825"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 抖音私信-渠道伙伴数据 |
| channel_map_2 | channel_map_2<br>`281834` | dimension / filter |  |  | [] | 抖音私信-渠道伙伴数据 |
| 年级 | grade_1<br>`275418` | dimension / row_dimension |  |  | [] | 抖音私信-渠道伙伴数据 |
| 顾问 | employee_email_name<br>`275421` | dimension / row_dimension |  |  | [] | 抖音私信-渠道伙伴数据 |
| 8min人数 | is_long_call<br>`8190136223229952` | measure / measure | sum(8190136223229952) |  | [] | 抖音私信-渠道伙伴数据 |
| 总通时 | call_duration<br>`8116514943100937` | measure / measure | sum(8116514943100937) |  | [] | 抖音私信-渠道伙伴数据 |
| 线索量 | v_lead<br>`8376585136465920` | measure / measure | sum(8376585136465920) |  | [] | 抖音私信-渠道伙伴数据 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3878349334709309440` | `public_filter_relation_3878349334709309442` | `275415` | qici | in / True | [] |
| `public_filter_3878349334709309444` | `public_filter_relation_3878349334709309442` | `275417` | channel_map_1 | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3878349334709309443` | `281834` | channel_map_2 | in | ["detailFilter"] |

## Text units

- `unit_3878349334709309446`: 1.最新数据来自两小时前；<br>2.等待时长 = 从首次线索分配到首次首call的总时间间隔/线索数 (平均一个用户多久才被首call)<br>3.8min人数 = 通话时长>8min的用户数 (只要有一通电话>8min就算这个用户达标)<br>4.外呼频次 = 平均一个用户拨了几次电话
- `unit_3878349334709309446`: 1.最新数据来自两小时前；<br>2.等待时长 = 从分配到首call的总时间间隔/线索数 (平均一个用户多久才被首call)<br>3.8min人数 = 通话时长>8min的用户数 (只要有一通电话>8min就算这个用户达标)<br>4.外呼频次 = 平均一个用户拨了几次电话

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
