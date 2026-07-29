# 转化数据 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3767151344579387392`
- dashboard_name: `转化数据`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:09:46`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `903d71e74ee9847e44e70d139f653f7044b5f2efe311755d784b26d2236bccbf`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3767151344579387392&htmlId=html_3983981158352646145`
- loaded_html_id: `html_3983981158352646145`
- config_html_id: `html_3983981193014374401`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3767151344579387392_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `9` / `346` / `322` / `221`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 9 | 9 | 9 | 691 | 322 | 1 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2253` | 转化数据_市场顾问 | 177096 | 9 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 指标卡组 | `node_ocmlhzkrbb1` | `unit_3767152837735378945` | card | node_ocllzw8twf1 /  | x=0, y=12, w=20, h=10 | False / False |
| 全局筛选器 | `node_ocmlhzkrbb4` | `public_filter_relation_3767176899681124353` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=8 | False / False |
|  | `node_ocmlj4bpx42` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=42, w=20, h=45 | False / False |
| 标题图 | `node_ocmlj4bpx45` | `unit_3768302365927813121` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 主管--转化 | `node_ocmlj4bpx4c` | `unit_3768315793457872897` | u_pivot | node_ocmlj4bpx42 / cltk | x=0, y=0, w=10, h=9 | False / False |
| 分渠道转化数据 | `node_ocmlj4bpx4g` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=87, w=20, h=59 | False / False |
| 部门--转化 | `node_ocmlkmxbc42` | `unit_3769950646823006217` | u_pivot | node_ocmlj4bpx42 / 2m5t | x=0, y=0, w=10, h=6 | False / False |
| 经理--转化 | `node_ocmlkmxbc43` | `unit_3770133595114242055` | u_pivot | node_ocmlj4bpx42 / kyya | x=0, y=0, w=10, h=8 | False / False |
| 渠道-部门 | `node_ocmlkmxbc44` | `unit_3770178971070095368` | u_pivot | node_ocmlj4bpx42 / 1gzb | x=0, y=0, w=10, h=8 | False / False |
| 渠道-主管-转化 | `node_ocmlkmxbc45` | `unit_3770180547675414537` | u_pivot | node_ocmlj4bpx4g / 2m5t | x=0, y=0, w=10, h=12 | False / False |
| 渠道-顾问-转化 | `node_ocmlkmxbc46` | `unit_3770181969476136976` | u_pivot | node_ocmlj4bpx4g / e90i | x=0, y=0, w=10, h=12 | False / False |
| 分学部-日度同环比 | `node_ocmovbznhv1` | `unit_3890255989767979009` | u_table | node_ocllzw8twf1 /  | x=0, y=22, w=20, h=20 | False / False |
| 部门-个人 | `node_ocmph02fdt1` | `unit_3912232685751894018` | u_pivot | node_ocmlj4bpx42 / 1mmp | x=0, y=0, w=10, h=8 | False / False |
| 渠道-主管-转化_副本 | `node_ocmps4pv1d1` | `unit_3923523375308914691` | u_pivot | node_ocmlj4bpx4g / 53ut | x=0, y=0, w=10, h=11 | False / False |
| 渠道-部门-转化 | `node_ocmps4pv1d3` | `unit_3769948772219289601` | u_pivot | node_ocmlj4bpx4g / 1gzb | x=0, y=0, w=10, h=11 | False / False |

## Pivot units

### 渠道-部门-转化

- unit_id: `unit_3769948772219289601`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 部门 / `depart`; 年级 / `grade_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价
- component: `node_ocmps4pv1d3` / `PivotTable`

### 渠道-主管-转化_副本

- unit_id: `unit_3923523375308914691`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 经理 / `jingli`; 年级 / `grade_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价
- component: `node_ocmps4pv1d1` / `PivotTable`

### 渠道-主管-转化

- unit_id: `unit_3770180547675414537`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价
- component: `node_ocmlkmxbc45` / `PivotTable`

### 渠道-顾问-转化

- unit_id: `unit_3770181969476136976`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 经理 / `jingli`; 主管 / `xiaozu`; 顾问 / `employee_email_name`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度
- component: `node_ocmlkmxbc46` / `PivotTable`

### 渠道-部门

- unit_id: `unit_3770178971070095368`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 年级 / `grade_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 市场线索 / `xiansuo`; 市场单效; 市场净收; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); 当期ltv; gmv(当) / `xb_trade_profit`; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价
- component: `node_ocmlkmxbc44` / `PivotTable`

### 部门--转化

- unit_id: `unit_3769950646823006217`
- model: `2253` / 转化数据_市场顾问
- dimensions: 部门 / `depart`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价
- component: `node_ocmlkmxbc42` / `PivotTable`

### 经理--转化

- unit_id: `unit_3770133595114242055`
- model: `2253` / 转化数据_市场顾问
- dimensions: 经理 / `jingli_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价
- component: `node_ocmlkmxbc43` / `PivotTable`

### 主管--转化

- unit_id: `unit_3768315793457872897`
- model: `2253` / 转化数据_市场顾问
- dimensions: 经理 / `jingli`; 主管 / `xiaozu`; channel_map
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价
- component: `node_ocmlj4bpx4c` / `PivotTable`

### 部门-个人

- unit_id: `unit_3912232685751894018`
- model: `2253` / 转化数据_市场顾问
- dimensions: 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `name1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 市场线索 / `xiansuo`; 市场单效; 市场净收; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); 当期ltv; gmv(当) / `xb_trade_profit`; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价
- component: `node_ocmph02fdt1` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| M成本 | M成本<br>`customized_993531083224276993` | custom_measure / measure | sum(${can_renew_ds_count_a}*${cb_cb}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}, {"needBoundaryValue": false, "orgParamType": 2, "paramId": "312827"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| ROI | ROI<br>`customized_993531083333328897` | custom_measure / measure | sum(${trade_profit})/${M成本} |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866765"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_993531083224276993"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| gmv完成度 | gmv完成度<br>`customized_993531083111030784` | custom_measure / measure | sum(${trade_profit})/${gmv目标} |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866765"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_993531082997784577"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| gmv目标 | gmv目标<br>`customized_993531082997784577` | custom_measure / measure | sum(${s_lead}*${gl_gl}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8256669137135616"}, {"needBoundaryValue": false, "orgParamType": 2, "paramId": "312828"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| smROI | smROI<br>`customized_993531083555627008` | custom_measure / measure | sum(${trade_profit})/(${M成本}+${接量人力}*3000) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866765"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_993531083224276993"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_993531083446575104"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 人均产能 | 人均产能<br>`customized_993531083664678912` | custom_measure / measure | ifnull(sum(${trade_profit})/${接量人力},0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866765"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_993531083446575104"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 人头转化 | 人头<br>`customized_993531083874394112` | custom_measure / measure | sum(${pay_users})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866754"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 人头转化(当) | 当期人头转化率<br>`customized_993531084633563137` | custom_measure / measure | ifnull(sum(${pay_users_on_period})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866755"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 单效(例会) | 单效<br>`customized_993531083979251713` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866765"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8495554035410944"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 客单价 | 客单价<br>`customized_993531084193161216` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${pay_users}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866765"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866754"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 市场净收 | 市场净收<br>`customized_993531084298018817` | custom_measure / measure | ifnull(sum(${pp_pmit})+sum(${ww_pmit}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8732188523915264"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8732188523915265"}] | 渠道-部门, 部门-个人 |
| 市场单效 | 市场单效<br>`customized_993531084411265024` | custom_measure / measure | ifnull(${市场净收}/sum(${xiansuo}),0) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_993531084298018817"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8812529818298368"}] | 渠道-部门, 部门-个人 |
| 当期ltv | 当期ltv<br>`customized_993531084524511233` | custom_measure / measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8330318168483840"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 截面ltv | 截面ltv<br>`customized_993531084964913152` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866765"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 拓课率 | 人均报科<br>`customized_993531083769536513` | custom_measure / measure | ifnull(sum(${pay_user_subs})/sum(${pay_users}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866757"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866754"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 拓课率(当) | 拓课率(当)<br>`customized_993531085082353664` | custom_measure / measure | ifnull(sum(${pay_user_subs_on_period})/sum(${pay_users_on_period}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866758"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866755"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 接量人力 | 接量人力<br>`customized_993531083446575104` | custom_measure / measure | count(distinct ${name1})-1 |  | [{"needBoundaryValue": false, "orgParamType": 2, "paramId": "312977"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 破蛋率 | 破蛋率<br>`customized_993531085191405568` | custom_measure / measure | ifnull(sum(${podan})/${接量人力},0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8256417855072256"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_993531083446575104"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 线索留存 | 线索留存<br>`customized_993531085300457472` | custom_measure / measure | ifnull(sum(${can_renew_ds_count_a})/sum(${lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8495554035410944"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 联报率 | 联报率<br>`customized_993531085409509376` | custom_measure / measure | ifnull(sum(${pay_user_subs_joint})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866760"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 联报率(当) | 当期联报率<br>`customized_993531084742615041` | custom_measure / measure | ifnull(sum(${pay_user_subs_joint_onp})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866761"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 订单转化 | 订单转化<br>`customized_993531085526949888` | custom_measure / measure | ifnull(sum(${pay_user_subs})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866757"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 订单转化(当) | 当期订单转化率<br>`customized_993531084851666945` | custom_measure / measure | ifnull(sum(${pay_user_subs_on_period})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866758"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866753"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 课单价 | 课单价<br>`customized_993531085640196097` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${pay_user_subs}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866765"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866757"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 退款(当) | 退款(当)<br>`customized_993531085749248001` | custom_measure / measure | sum(${xb_trade_income})-sum(${xb_trade_profit}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866766"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8330318168483840"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 退费率 | 退费率<br>`customized_993531085862494208` | custom_measure / measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866764"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866763"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 退费率(当) | 退费率(当)<br>`customized_993531085971546112` | custom_measure / measure | ifnull(${退款(当)}/sum(${xb_trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_993531085749248001"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8246056497866766"}] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| channel_map | channel_map<br>`311321` | dimension / filter |  |  | [] | 主管--转化 |
| 主管 | zhuguan<br>`311390` | dimension / row_dimension |  |  | [] | 部门-个人 |
| 主管 | xiaozu<br>`313017` | dimension / row_dimension |  |  | [] | 渠道-主管-转化, 渠道-顾问-转化, 主管--转化 |
| 年级 | grade_1<br>`349838` | dimension / row_dimension |  |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-部门 |
| 渠道 | channel_map<br>`311321` | dimension / row_dimension |  |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门 |
| 经理 | jingli<br>`311389` | dimension / row_dimension |  |  | [] | 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 主管--转化, 部门-个人 |
| 经理 | jingli_1<br>`388722` | dimension / row_dimension |  |  | [] | 经理--转化 |
| 部门 | depart<br>`311388` | dimension / row_dimension |  |  | [] | 渠道-部门-转化, 部门--转化 |
| 顾问 | employee_email_name<br>`311323` | dimension / row_dimension |  |  | [] | 渠道-顾问-转化 |
| 顾问 | name1<br>`312977` | dimension / row_dimension |  |  | [] | 部门-个人 |
| gmv(当) | xb_trade_profit<br>`8330318168483840` | measure / measure | sum(8330318168483840) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 人头 | pay_users<br>`8246056497866754` | measure / measure | sum(8246056497866754) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 人头(当) | pay_users_on_period<br>`8246056497866755` | measure / measure | sum(8246056497866755) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 市场线索 | xiansuo<br>`8812529818298368` | measure / measure | sum(8812529818298368) |  | [] | 渠道-部门, 部门-个人 |
| 截面gmv | trade_profit<br>`8246056497866765` | measure / measure | sum(8246056497866765) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 联报人次 | pay_user_subs_joint<br>`8246056497866760` | measure / measure | sum(8246056497866760) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 联报人次(当) | pay_user_subs_joint_onp<br>`8246056497866761` | measure / measure | sum(8246056497866761) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 订单 | pay_user_subs<br>`8246056497866757` | measure / measure | sum(8246056497866757) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 订单(当) | pay_user_subs_on_period<br>`8246056497866758` | measure / measure | sum(8246056497866758) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 退前线索 | lead_count<br>`8495554035410944` | measure / measure | sum(8495554035410944) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 退后线索 | can_renew_ds_count_a<br>`8246056497866753` | measure / measure | sum(8246056497866753) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |
| 退费金额 | trade_refund<br>`8246056497866764` | measure / measure | sum(8246056497866764) |  | [] | 渠道-部门-转化, 渠道-主管-转化_副本, 渠道-主管-转化, 渠道-顾问-转化, 渠道-部门, 部门--转化, 经理--转化, 主管--转化, 部门-个人 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3767176899681124355` | `public_filter_relation_3767176899681124353` | `311320` | period_name | in / True | [] |
| `public_filter_3767277498321739778` | `public_filter_relation_3767176899681124353` | `311321` | channel_map | in /  | [] |
| `public_filter_3768354657116901378` | `public_filter_relation_3767176899681124353` | `311389` | jingli | in /  | [] |
| `public_filter_3768759311096791042` | `public_filter_relation_3767176899681124353` | `349838` | grade_1 | in /  | [] |
| `public_filter_3833532216408592385` | `public_filter_relation_3767176899681124353` | `374091` | rule_name | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3768315793457872897` | `311321` | channel_map | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
