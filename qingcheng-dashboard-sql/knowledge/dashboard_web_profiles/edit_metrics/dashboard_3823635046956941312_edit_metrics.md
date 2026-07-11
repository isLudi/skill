# 过程-私域-主管 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3823635046956941312`
- dashboard_name: `过程-私域-主管`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:28:58`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `f00b7f0fed52117bb1c158e660d429dc6094bb867df434b206d0cc1a129fcdd0`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3823635046956941312&htmlId=html_3984000534109962240`
- loaded_html_id: `html_3984000534109962240`
- config_html_id: `html_3984000568405913600`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-broadcast\dashboard_3823635046956941312_rich.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `18` / `15` / `12`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 33 | 15 | 2 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2064` | 青橙-过程数据 | 177129 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 全局筛选器 | `node_ocml27f2x71` | `public_filter_relation_3823635066888273922` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=9, w=20, h=5 | False / False |
| 私域-渠道主管数据 | `node_ocml28zcv2o` | `unit_3823635066888273925` | u_pivot | node_ocllzw8twf1 /  | x=0, y=14, w=20, h=30 | False / False |
| 文本框 | `node_ocmlcdxg741` | `unit_3823635066888273928` | u_text | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=9 | False / False |

## Pivot units

### 私域-渠道主管数据

- unit_id: `unit_3823635066888273925`
- model: `2064` / 青橙-过程数据
- dimensions: 主管 / `xiaozu`; channel_map_1; v_lead
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 首call率 / `触达率`; 24h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2o` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 24h沟通率 | 24h沟通率<br>`customized_993545196680196097` | custom_measure / measure | sum(${first_call_connected_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100934"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 24h首call率 | 24h触达率<br>`customized_993545196789248001` | custom_measure / measure | sum(${first_call_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100931"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 8min | 8min<br>`customized_993545197116403713` | custom_measure / measure | sum(${is_long_call})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8190136223229952"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| APP率 | APP率<br>`customized_993545197225455617` | custom_measure / measure | sum(${is_app_denglu})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8149654467340288"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 外呼时长(min) | 线索外呼时长<br>`customized_993545197665857536` | custom_measure / measure | sum(${call_duration})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100937"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 外呼频次 | 线索外呼频次<br>`customized_993545197770715137` | custom_measure / measure | sum(${zong_call_ci})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100938"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 好友率 | 好友率<br>`customized_993545197334507521` | custom_measure / measure | sum(${is_friend_lead})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183691126073344"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 沟通率 | 沟通率<br>`customized_993545197443559425` | custom_measure / measure | sum(${first_call_connected_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100936"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 等待时长(h) | 用户平均等待时长<br>`customized_993545197552611329` | custom_measure / measure | sum(${first_call_time_diff_hour})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100930"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 首call率 | 触达率<br>`customized_993545197879767041` | custom_measure / measure | sum(${first_call_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100933"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 首节到课 | 首节到课<br>`customized_993545197988818945` | custom_measure / measure | sum(${daoke1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465921"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| 首节有效 | 首节有效<br>`customized_993545198097870849` | custom_measure / measure | sum(${valid_daoke_1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183652594509825"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 私域-渠道主管数据 |
| channel_map_1 | channel_map_1<br>`275417` | dimension / filter |  |  | [] | 私域-渠道主管数据 |
| v_lead | v_lead<br>`8376585136465920` | dimension / filter |  |  | [] | 私域-渠道主管数据 |
| 主管 | xiaozu<br>`275420` | dimension / row_dimension |  |  | [] | 私域-渠道主管数据 |
| 8min人数 | is_long_call<br>`8190136223229952` | measure / measure | sum(8190136223229952) |  | [] | 私域-渠道主管数据 |
| 总通时 | call_duration<br>`8116514943100937` | measure / measure | sum(8116514943100937) |  | [] | 私域-渠道主管数据 |
| 线索量 | v_lead<br>`8376585136465920` | measure / measure | sum(8376585136465920) |  | [] | 私域-渠道主管数据 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3823635066888273920` | `public_filter_relation_3823635066888273922` | `275415` | qici | in / True | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3823635066888273925` | `275417` | channel_map_1 | in | ["detailFilter"] |
| `unit_3823635066888273925` | `8376585136465920` | v_lead | >= | ["detailFilter"] |

## Text units

- `unit_3823635066888273928`: 1.最新数据来自两小时前；<br>2.等待时长 = 从首次线索分配到首次首call的总时间间隔/线索数 (平均一个用户多久才被首call)<br>3.8min人数 = 通话时长>8min的用户数 (只要有一通电话>8min就算这个用户达标)<br>4.外呼频次 = 平均一个用户拨了几次电话

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
