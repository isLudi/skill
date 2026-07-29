# 外呼过程数据看板 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3730722176629411841`
- dashboard_name: `外呼过程数据看板`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:08:43`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `32143d2aba2007455d72a704c76d9d576bdd3c1602a02b14d3634aa7f361a1e9`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3730722176629411841&htmlId=html_3983980138001408001`
- loaded_html_id: `html_3983980138001408001`
- config_html_id: `html_3983980172545871872`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3730722176629411841_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `3` / `77` / `64` / `57`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 3 | 3 | 154 | 64 | 0 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2054` | (内部渠道)外呼过程数据 | 176200 | 3 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 总体数据 | `node_ocmki2t94b1` | `unit_3730781607175761920` | u_pivot | node_ocllzw8twf1 /  | x=0, y=18, w=20, h=46 | False / False |
| 主管维度 | `node_ocmmd4hmjs1` | `unit_3798743671868997638` | u_pivot | node_ocmmd4hmjs3 / l7qe | x=0, y=0, w=10, h=15 | False / False |
| 个人维度 | `node_ocmmd4hmjs2` | `unit_3798745287165575173` | u_pivot | node_ocmmd4hmjs3 / a7nd | x=0, y=0, w=10, h=14 | False / False |
|  | `node_ocmmd4hmjs3` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=64, w=20, h=68 | False / False |
| 标题图 | `node_ocmmd4hmjsm` | `unit_3798750134270525441` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 全局筛选器 | `node_ocmmd4hmjso` | `public_filter_relation_3798754154607599616` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=10, w=20, h=8 | False / False |
| 文本框 | `node_ocmmd5q7lc1` | `unit_3798773484699615233` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=6 | False / False |

## Pivot units

### 总体数据

- unit_id: `unit_3730781607175761920`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 经理 / `jingli`; 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`
- measures: 人力 / `接量人力`; 退前线索 / `lead_count`; 退后线索 / `valid_lead_count`; 总通时 / `call_duration`; 通时(例均) / `平均通时(例子)`; 通时(人均) / `平均通时(人均)`; 首call; 5min外呼 / `5min外呼率`; 6h外呼 / `6h外呼率`; 12h外呼 / `12h外呼率`; 24h外呼 / `24h外呼率`; 48h外呼 / `48h外呼率`; 24h沟通 / `24h沟通率`; 48h沟通 / `48h沟通率`; 外呼频次; 平均接通时长(min) / `平均接通时长`; 等待时长(h) / `等待时长`; 外呼接通 / `外呼接通率`; 5min比例; 好友 / `好友率`; APP登陆 / `APP登陆率`; 异常; 深沟 / `深沟率`; 双沟 / `双沟率`; 首节到课 / `首节到课率`; 首节有效 / `首节有效率`
- component: `node_ocmki2t94b1` / `PivotTable`

### 主管维度

- unit_id: `unit_3798743671868997638`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `xiaozu`
- measures: 接量人力; 有效例子 / `valid_lead_count`; 例子总通时 / `call_duration`; 平均通时(例子); 平均通时(人均); 24h外呼率; 48h外呼率; 24h沟通率; 48h沟通率; 外呼频次; 平均接通时长(min) / `平均接通时长`; 等待时长(h) / `等待时长`; 外呼接通率; 5min比例; 好友率; APP登陆率; 深沟率; 双沟率; 首节到课率; 首节有效率
- component: `node_ocmmd4hmjs1` / `PivotTable`

### 个人维度

- unit_id: `unit_3798745287165575173`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`
- measures: 有效例子 / `valid_lead_count`; 例子总通时 / `call_duration`; 平均通时(例子); 24h外呼率; 48h外呼率; 24h沟通率; 48h沟通率; 外呼频次; 平均接通时长(min) / `平均接通时长`; 等待时长(h) / `等待时长`; 外呼接通率; 5min比例; 好友率; APP登陆率; 深沟率; 双沟率; 首节到课率; 首节有效率
- component: `node_ocmmd4hmjs2` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 12h外呼 | 12h外呼率<br>`customized_992821499672203265` | custom_measure / measure | ifnull(sum(${first_call_in_12h})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647934271842305"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 24h外呼 | 24h外呼率<br>`customized_992821499802226688` | custom_measure / measure | sum(${first_call_in_24h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234626"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 24h外呼率 | 24h外呼率<br>`customized_992821499802226688` | custom_measure / measure | sum(${first_call_in_24h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234626"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 24h沟通 | 24h沟通率<br>`customized_992821499936444416` | custom_measure / measure | sum(${first_call_connected_in_24h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234629"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 24h沟通率 | 24h沟通率<br>`customized_992821499936444416` | custom_measure / measure | sum(${first_call_connected_in_24h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234629"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 48h外呼 | 48h外呼率<br>`customized_992821500062273536` | custom_measure / measure | sum(${first_call_in_48h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234627"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 48h外呼率 | 48h外呼率<br>`customized_992821500062273536` | custom_measure / measure | sum(${first_call_in_48h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234627"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 48h沟通 | 48h沟通率<br>`customized_992821500183908353` | custom_measure / measure | sum(${first_call_connected_in_48h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234630"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 48h沟通率 | 48h沟通率<br>`customized_992821500183908353` | custom_measure / measure | sum(${first_call_connected_in_48h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234630"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 5min外呼 | 5min外呼率<br>`customized_992821500313931776` | custom_measure / measure | ifnull(sum(${first_call_in_5min})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8805620408543232"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 5min比例 | 5min比例<br>`customized_992821500439760896` | custom_measure / measure | sum(${is_long_call})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234635"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据, 主管维度, 个人维度 |
| 6h外呼 | 6h外呼率<br>`customized_992821500565590016` | custom_measure / measure | ifnull(sum(${first_call_in_6h})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647934271842304"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| APP登陆 | APP登陆率<br>`customized_992821500683030528` | custom_measure / measure | sum(${is_app_denglu})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234639"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| APP登陆率 | APP登陆率<br>`customized_992821500683030528` | custom_measure / measure | sum(${is_app_denglu})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234639"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 人力 | 接量人力<br>`customized_992821501773549568` | custom_measure / measure | count(DISTINCT ${employee_email_name}) |  | [{"needBoundaryValue": false, "orgParamType": 2, "paramId": "273598"}] | 总体数据 |
| 双沟 | 双沟率<br>`customized_992821500813053953` | custom_measure / measure | sum(${is_shuanggou})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234641"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 双沟率 | 双沟率<br>`customized_992821500813053953` | custom_measure / measure | sum(${is_shuanggou})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234641"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 外呼接通 | 外呼接通率<br>`customized_992821500934688768` | custom_measure / measure | sum(${call_status})/sum(${zong_call_ci}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234634"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234633"}] | 总体数据 |
| 外呼接通率 | 外呼接通率<br>`customized_992821500934688768` | custom_measure / measure | sum(${call_status})/sum(${zong_call_ci}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234634"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234633"}] | 主管维度, 个人维度 |
| 外呼频次 | 外呼频次<br>`customized_992821501052129280` | custom_measure / measure | sum(${zong_call_ci})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234633"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据, 主管维度, 个人维度 |
| 好友 | 好友率<br>`customized_992821501169569792` | custom_measure / measure | sum(${is_friend_lead})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234638"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 好友率 | 好友率<br>`customized_992821501169569792` | custom_measure / measure | sum(${is_friend_lead})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234638"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 平均接通时长(min) | 平均接通时长<br>`customized_992821501530279936` | custom_measure / measure | sum(${call_duration})/sum(${call_status}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234632"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234634"}] | 总体数据, 主管维度, 个人维度 |
| 平均通时(人均) | 平均通时(人均)<br>`customized_992821501890990080` | custom_measure / measure | sum(${call_duration})/${接量人力} |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234632"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992821501773549568"}] | 主管维度 |
| 平均通时(例子) | 平均通时(例子)<br>`customized_992821502008430592` | custom_measure / measure | sum(${call_duration})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234632"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 异常 | 异常<br>`customized_992821502125871104` | custom_measure / measure | ifnull(sum(${is_yichang})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8489382022047744"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 接量人力 | 接量人力<br>`customized_992821501773549568` | custom_measure / measure | count(DISTINCT ${employee_email_name}) |  | [{"needBoundaryValue": false, "orgParamType": 2, "paramId": "273598"}] | 主管维度 |
| 深沟 | 深沟率<br>`customized_992821502243311616` | custom_measure / measure | sum(${is_shengou})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234640"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 深沟率 | 深沟率<br>`customized_992821502243311616` | custom_measure / measure | sum(${is_shengou})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234640"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 等待时长(h) | 等待时长<br>`customized_992821502482386945` | custom_measure / measure | sum(${first_call_time_diff_hour})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8139340645427200"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据, 主管维度, 个人维度 |
| 通时(人均) | 平均通时(人均)<br>`customized_992821501890990080` | custom_measure / measure | sum(${call_duration})/${接量人力} |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234632"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992821501773549568"}] | 总体数据 |
| 通时(例均) | 平均通时(例子)<br>`customized_992821502008430592` | custom_measure / measure | sum(${call_duration})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234632"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 首call | 首call<br>`customized_992821502595633152` | custom_measure / measure | ifnull(sum(${is_f_call})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8432582790834176"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 首节到课 | 首节到课率<br>`customized_992821502713073664` | custom_measure / measure | sum(${daoke1})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234636"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 首节到课率 | 首节到课率<br>`customized_992821502713073664` | custom_measure / measure | sum(${daoke1})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234636"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 首节有效 | 首节有效率<br>`customized_992821502830514176` | custom_measure / measure | sum(${v_daoke1})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8171822499981312"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 总体数据 |
| 首节有效率 | 首节有效率<br>`customized_992821502830514176` | custom_measure / measure | sum(${v_daoke1})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8171822499981312"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 主管维度, 个人维度 |
| 主管 | xiaozu<br>`273597` | dimension / row_dimension |  |  | [] | 总体数据, 主管维度, 个人维度 |
| 年级 | grade_1<br>`273595` | dimension / row_dimension |  |  | [] | 总体数据, 主管维度, 个人维度 |
| 线索渠道 | channel_map_1<br>`273594` | dimension / row_dimension |  |  | [] | 总体数据, 主管维度, 个人维度 |
| 经理 | jingli<br>`322380` | dimension / row_dimension |  |  | [] | 总体数据, 主管维度 |
| 顾问 | employee_email_name<br>`273598` | dimension / row_dimension |  |  | [] | 总体数据, 个人维度 |
| 例子总通时 | call_duration<br>`8103974494234632` | measure / measure | sum(8103974494234632) |  | [] | 主管维度, 个人维度 |
| 总通时 | call_duration<br>`8103974494234632` | measure / measure | sum(8103974494234632) |  | [] | 总体数据 |
| 有效例子 | valid_lead_count<br>`8103974494234625` | measure / measure | sum(8103974494234625) |  | [] | 主管维度, 个人维度 |
| 退前线索 | lead_count<br>`8465935477925888` | measure / measure | sum(8465935477925888) |  | [] | 总体数据 |
| 退后线索 | valid_lead_count<br>`8103974494234625` | measure / measure | sum(8103974494234625) |  | [] | 总体数据 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3798754154607599618` | `public_filter_relation_3798754154607599616` | `273592` | qici | in / True | [] |
| `public_filter_3798754154624376834` | `public_filter_relation_3798754154607599616` | `273596` | department | in /  | [] |
| `public_filter_3798754154624376836` | `public_filter_relation_3798754154607599616` | `273594` | channel_map_1 | in /  | [] |
| `public_filter_3798754154624376838` | `public_filter_relation_3798754154607599616` | `273595` | grade_1 | in /  | [] |
| `public_filter_3798754154624376840` | `public_filter_relation_3798754154607599616` | `322380` | jingli | in /  | [] |
| `public_filter_3798754154624376842` | `public_filter_relation_3798754154607599616` | `273597` | xiaozu | in /  | [] |
| `public_filter_3798755624913977346` | `public_filter_relation_3798754154607599616` | `273598` | employee_email_name | in /  | [] |
| `public_filter_3839382056232017921` | `public_filter_relation_3798754154607599616` | `273593` | rule_name | in /  | [] |

### Component filters

- 无组件级筛选器快照。

## Text units

- `unit_3798773484699615233`: 各项指标说明请点击文档： 外呼指标说明文档 <br>总筛选后所有板块数据均被筛选；每天整点-整点15表格抽数随机刷新，报表渲染会慢
- `unit_3798773484699615233`: 各项指标说明请点击文档： 外呼指标说明文档 <br>总筛选后所有板块数据均被筛选；整点-整点15表格抽数随机刷新，报表渲染会慢

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
