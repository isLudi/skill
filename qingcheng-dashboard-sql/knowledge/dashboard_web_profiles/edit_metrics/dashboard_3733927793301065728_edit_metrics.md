# 过程数据报表-青橙 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3733927793301065728`
- dashboard_name: `过程数据报表-青橙`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:14:39`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `4155b4ffa65a15b3f57b7d55d13f925d0f5661fbab1a57da224da7971df0e98d`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3733927793301065728&htmlId=html_3983986118451802112`
- loaded_html_id: `html_3983986118451802112`
- config_html_id: `html_3983986152853655552`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-project\dashboard_3733927793301065728_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `7` / `139` / `119` / `98`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 7 | 7 | 275 | 119 | 3 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2064` | 青橙-过程数据 | 172172 | 7 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 全局筛选器 | `node_ocml27f2x71` | `public_filter_relation_3751145027574013953` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=11, w=20, h=5 | False / False |
| 标题图 | `node_ocml27f2x72` | `unit_3751144765087657984` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 伙伴数据 | `node_ocml27f2x77` | `unit_3751156666810601472` | u_pivot | node_ocllzw8twf1 /  | x=0, y=92, w=20, h=51 | False / False |
| 一级渠道数据 | `node_ocml28zcv28` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=16, w=20, h=33 | False / False |
| 渠道-整体 | `node_ocml28zcv2c` | `unit_3751299765728346112` | u_pivot | node_ocml28zcv28 / 2mql | x=0, y=0, w=10, h=6 | False / False |
| 渠道-年级 | `node_ocml28zcv2d` | `unit_3751309023765233664` | u_pivot | node_ocml28zcv28 / hqd2 | x=0, y=0, w=10, h=6 | False / False |
| 渠道-主管 | `node_ocml28zcv2e` | `unit_3751316651509710849` | u_pivot | node_ocml28zcv28 / al0s | x=0, y=0, w=10, h=19 | False / False |
| 二级渠道数据 | `node_ocml28zcv2f` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=49, w=20, h=43 | False / False |
| 二级-整体 | `node_ocml28zcv2m` | `unit_3751349188973985793` | u_pivot | node_ocml28zcv2f / 2mql | x=0, y=0, w=10, h=8 | False / False |
| 二级-年级 | `node_ocml28zcv2n` | `unit_3751356204584960000` | u_pivot | node_ocml28zcv2f / hqd2 | x=0, y=0, w=10, h=9 | False / False |
| 二级-主管 | `node_ocml28zcv2o` | `unit_3751364262109941760` | u_pivot | node_ocml28zcv2f / jt5i | x=0, y=0, w=10, h=14 | False / False |
| 文本框 | `node_ocml965uuw1` | `unit_3758225654486126593` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=7 | False / False |

## Pivot units

### 渠道-整体

- unit_id: `unit_3751299765728346112`
- model: `2064` / 青橙-过程数据
- dimensions: 渠道 / `channel_map_1`; 部门 / `dept_2`
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2c` / `PivotTable`

### 渠道-年级

- unit_id: `unit_3751309023765233664`
- model: `2064` / 青橙-过程数据
- dimensions: 渠道 / `channel_map_1`; 年级 / `grade_1`
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2d` / `PivotTable`

### 渠道-主管

- unit_id: `unit_3751316651509710849`
- model: `2064` / 青橙-过程数据
- dimensions: 渠道 / `channel_map_1`; 年级 / `grade_1`; 主管 / `xiaozu`; department
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2e` / `PivotTable`

### 二级-整体

- unit_id: `unit_3751349188973985793`
- model: `2064` / 青橙-过程数据
- dimensions: 渠道 / `channel_map_2`; 部门 / `dept_2`
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2m` / `PivotTable`

### 二级-年级

- unit_id: `unit_3751356204584960000`
- model: `2064` / 青橙-过程数据
- dimensions: 渠道 / `channel_map_2`; 年级 / `grade_1`
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2n` / `PivotTable`

### 二级-主管

- unit_id: `unit_3751364262109941760`
- model: `2064` / 青橙-过程数据
- dimensions: 渠道 / `channel_map_2`; 年级 / `grade_1`; 主管 / `xiaozu`
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml28zcv2o` / `PivotTable`

### 伙伴数据

- unit_id: `unit_3751156666810601472`
- model: `2064` / 青橙-过程数据
- dimensions: 渠道 / `channel_map_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; grade_1; channel_map_2
- measures: 线索量 / `v_lead`; 好友率; APP率; 等待时长(h) / `用户平均等待时长`; 8min人数 / `is_long_call`; 8min; 24h首call率 / `24h触达率`; 48h首call率 / `48h触达率`; 首call率 / `触达率`; 24h沟通率; 48h沟通率; 沟通率; 外呼时长(min) / `线索外呼时长`; 外呼频次 / `线索外呼频次`; 总通时 / `call_duration`; 首节到课; 首节有效
- component: `node_ocml27f2x77` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 24h沟通率 | 24h沟通率<br>`customized_988147206690455552` | custom_measure / measure | sum(${first_call_connected_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100934"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 24h首call率 | 24h触达率<br>`customized_988147206791118848` | custom_measure / measure | sum(${first_call_in_24h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100931"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 48h沟通率 | 48h沟通率<br>`customized_988147206900170752` | custom_measure / measure | sum(${first_call_connected_in_48h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100935"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 48h首call率 | 48h触达率<br>`customized_988147207000834048` | custom_measure / measure | sum(${first_call_in_48h})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100932"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 8min | 8min<br>`customized_988147207105691649` | custom_measure / measure | sum(${is_long_call})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8190136223229952"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| APP率 | APP率<br>`customized_988147207210549248` | custom_measure / measure | sum(${is_app_denglu})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8149654467340288"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 外呼时长(min) | 线索外呼时长<br>`customized_988147207642562561` | custom_measure / measure | sum(${call_duration})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100937"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 外呼频次 | 线索外呼频次<br>`customized_988147207747420160` | custom_measure / measure | sum(${zong_call_ci})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100938"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 好友率 | 好友率<br>`customized_988147207315406849` | custom_measure / measure | sum(${is_friend_lead})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183691126073344"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 沟通率 | 沟通率<br>`customized_988147207424458753` | custom_measure / measure | sum(${first_call_connected_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100936"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 等待时长(h) | 用户平均等待时长<br>`customized_988147207529316352` | custom_measure / measure | sum(${first_call_time_diff_hour})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100930"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 首call率 | 触达率<br>`customized_988147207860666369` | custom_measure / measure | sum(${first_call_cnt})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8116514943100933"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 首节到课 | 首节到课<br>`customized_988147207969718273` | custom_measure / measure | sum(${daoke1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465921"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 首节有效 | 首节有效<br>`customized_988147208078770177` | custom_measure / measure | sum(${valid_daoke_1})/sum(${v_lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8183652594509825"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8376585136465920"}] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| channel_map_2 | channel_map_2<br>`281834` | dimension / filter |  |  | [] | 伙伴数据 |
| department | department<br>`275419` | dimension / filter |  |  | [] | 渠道-主管 |
| grade_1 | grade_1<br>`275418` | dimension / filter |  |  | [] | 伙伴数据 |
| 主管 | xiaozu<br>`275420` | dimension / row_dimension |  |  | [] | 渠道-主管, 二级-主管, 伙伴数据 |
| 年级 | grade_1<br>`275418` | dimension / row_dimension |  |  | [] | 渠道-年级, 渠道-主管, 二级-年级, 二级-主管 |
| 渠道 | channel_map_1<br>`275417` | dimension / row_dimension |  |  | [] | 渠道-整体, 渠道-年级, 渠道-主管, 伙伴数据 |
| 渠道 | channel_map_2<br>`281834` | dimension / row_dimension |  |  | [] | 二级-整体, 二级-年级, 二级-主管 |
| 部门 | dept_2<br>`300907` | dimension / row_dimension |  |  | [] | 渠道-整体, 二级-整体 |
| 顾问 | employee_email_name<br>`275421` | dimension / row_dimension |  |  | [] | 伙伴数据 |
| 8min人数 | is_long_call<br>`8190136223229952` | measure / measure | sum(8190136223229952) |  | [] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 总通时 | call_duration<br>`8116514943100937` | measure / measure | sum(8116514943100937) |  | [] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |
| 线索量 | v_lead<br>`8376585136465920` | measure / measure | sum(8376585136465920) |  | [] | 渠道-整体, 渠道-年级, 渠道-主管, 二级-整体, 二级-年级, 二级-主管, 伙伴数据 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3751145027574013955` | `public_filter_relation_3751145027574013953` | `275415` | qici | in / True | [] |
| `public_filter_3751147693080416257` | `public_filter_relation_3751145027574013953` | `275417` | channel_map_1 | in /  | [] |
| `public_filter_3751149362816593921` | `public_filter_relation_3751145027574013953` | `275418` | grade_1 | in /  | [] |
| `public_filter_3951349398708027394` | `public_filter_relation_3751145027574013953` | `275419` | department | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3751156666810601472` | `275418` | grade_1 | in | ["detailFilter"] |
| `unit_3751156666810601472` | `281834` | channel_map_2 | in | ["detailFilter"] |
| `unit_3751316651509710849` | `275419` | department | in | ["detailFilter"] |

## Text units

- `unit_3758225654486126593`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问<br>2.指标说明：等待时长 = 从分配到首call的总时间间隔/线索数 (平均一个用户多久才被首call); 8min人数 = 通话时长>8min的用户数 (只要有一通电话>8min就算这个用户达标)
- `unit_3758225654486126593`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问 ----2.指标计算：8min人数 = 通话时长>8min的用户数；

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
