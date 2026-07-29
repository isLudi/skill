# 11老板_运营侧数据看板 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3833805337379700736`
- dashboard_name: `11老板_运营侧数据看板`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:11:17`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `6ef1d8f7fdb4ce35b680d39ca9ecf2f4e11ef5b8cbe6419e973722e33101d7f2`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3833805337379700736&htmlId=html_3983982553266200576`
- loaded_html_id: `html_3983982553266200576`
- config_html_id: `html_3983982587726602240`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3833805337379700736_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `14` / `277` / `198` / `144`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 14 | 14 | 14 | 529 | 198 | 18 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2054` | (内部渠道)外呼过程数据 | 160288 | 1 |
| `2132` | (内部)到课衰减情况 | 160287 | 1 |
| `2293` | 运营侧个人数据 | 160286 | 9 |
| `2344` | 分析--分周期转化 | 160290 | 1 |
| `2345` | 进量测试(市场渠道) | 160291 | 1 |
| `2424` | 每日转化数据表 | 160293 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmm36s5ul1` | `unit_3833805476815142913` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=9 | False / False |
| 整体数据 | `node_ocmm36s5ul2` | `unit_3833805476815142914` | card | node_ocllzw8twf1 /  | x=0, y=17, w=20, h=25 | False / False |
| 全局筛选器 | `node_ocmm3gbgtt1` | `public_filter_relation_3833805476815142919` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=9, w=20, h=8 | False / False |
| 分团队转化数据 | `node_ocmm3gbgtt2` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=42, w=20, h=77 | False / False |
| 亚飞 | `node_ocmm5x8gaj1` | `unit_3833805476815142925` | u_pivot | node_ocmm5x8gaj95 / 7uks | x=0, y=0, w=10, h=6 | False / False |
| 分渠道转化数据 | `node_ocmm5x8gaj95` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=127, w=20, h=85 | False / False |
| 春春 | `node_ocmm5x8gaj98` | `unit_3833805476815142926` | u_pivot | node_ocmm5x8gaj95 / h1vx | x=0, y=0, w=10, h=6 | False / False |
| 全局筛选器 | `node_ocmm5xvqp81` | `public_filter_relation_3833805476815142929` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=119, w=20, h=8 | False / False |
| 曹忆 | `node_ocmm5xvur81` | `unit_3833805476815142939` | u_pivot | node_ocmm5x8gaj95 / 3x4n | x=0, y=0, w=10, h=6 | False / False |
| 行课数据 | `node_ocmm6d4ecxf` | `unit_3833805476815142946` | u_pivot | node_ocllzw8twf1 /  | x=0, y=523, w=20, h=66 | False / False |
| 外呼数据 | `node_ocmm6d4ecxg` | `unit_3833805476815142947` | u_pivot | node_ocllzw8twf1 /  | x=0, y=459, w=20, h=64 | False / False |
| 经理 | `node_ocmm7hf7ce2` | `unit_3833805476815142920` | u_pivot | node_ocmm3gbgtt2 / bgug | x=0, y=0, w=10, h=6 | False / False |
| 肖晗IP | `node_ocmm7lie2t1` | `unit_3833805476815142953` | u_pivot | node_ocmm5x8gaj95 / hfgv | x=0, y=0, w=10, h=6 | False / False |
| KOC自孵化 | `node_ocmm7ljy2q1` | `unit_3833805476815142941` | u_pivot | node_ocmm5x8gaj95 / 6nbh | x=0, y=0, w=10, h=6 | False / False |
| 主管 | `node_ocmmelm7j51` | `unit_3833805476815142958` | u_pivot | node_ocmm3gbgtt2 / 7q00 | x=0, y=0, w=10, h=9 | False / False |
| 个人 | `node_ocmmelm7j52` | `unit_3833805476815142959` | u_pivot | node_ocmm3gbgtt2 / eoxn | x=0, y=0, w=10, h=6 | False / False |
| 线索分时间转化数据 | `node_ocmmhhw0ni1` | `unit_3833805476815142960` | u_pivot | node_ocllzw8twf1 /  | x=0, y=316, w=20, h=67 | False / False |
| 进量_转化分析 | `node_ocmmhrhq6y2` | `unit_3833805476815142964` | u_pivot | node_ocllzw8twf1 /  | x=9, y=393, w=11, h=66 | False / False |
| 进量节奏分析 | `node_ocmmhrhq6y4` | `unit_3833805476815142965` | u_line | node_ocllzw8twf1 /  | x=0, y=393, w=9, h=66 | False / False |
| 全局筛选器 | `node_ocmmhrhq6y5` | `public_filter_relation_3833805476815142970` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=383, w=20, h=10 | False / False |
| 周帅IP | `node_ocmmuehfdh1` | `unit_3833805476815142976` | u_pivot | node_ocmm5x8gaj95 / 2tow | x=0, y=0, w=10, h=6 | False / False |
| 收款分时间占比 | `node_ocmn1hi8361` | `unit_3833805476815142977` | u_pivot | node_ocllzw8twf1 /  | x=0, y=220, w=20, h=47 | False / False |
| 日度净收走势 | `node_ocmn1hi8362` | `unit_3833805476815142978` | u_line | node_ocllzw8twf1 /  | x=0, y=267, w=20, h=49 | False / False |
| 全局筛选器 | `node_ocmn1hi8366` | `public_filter_relation_3833805476815142987` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=212, w=20, h=8 | False / False |

## Pivot units

### 进量_转化分析

- unit_id: `unit_3833805476815142964`
- model: `2345` / 进量测试(市场渠道)
- dimensions: 分配日期 / `assign_day_new`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 24h外呼 / `24h外呼率`; 48h外呼 / `48h外呼率`; 5min; 好友 / `好友率`; APP; 深沟 / `深沟率`; 课1; 课1有效; 当期单效; 截面单效
- component: `node_ocmmhrhq6y2` / `PivotTable`

### 经理

- unit_id: `unit_3833805476815142920`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 年级 / `grade_1`
- measures: 退后线索 / `can_renew_ds_count_a`; 接量人力; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效
- component: `node_ocmm7hf7ce2` / `PivotTable`

### 主管

- unit_id: `unit_3833805476815142958`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `zhuguan`; 年级 / `grade_1`
- measures: 退后线索 / `can_renew_ds_count_a`; 接量人力; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人头转化; 订单转化; 人均报科; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效
- component: `node_ocmmelm7j51` / `PivotTable`

### 个人

- unit_id: `unit_3833805476815142959`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; 年级 / `grade_1`
- measures: 退后线索 / `can_renew_ds_count_a`; 接量人力; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效
- component: `node_ocmmelm7j52` / `PivotTable`

### KOC自孵化

- unit_id: `unit_3833805476815142941`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率
- component: `node_ocmm7ljy2q1` / `PivotTable`

### 春春

- unit_id: `unit_3833805476815142926`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率
- component: `node_ocmm5x8gaj98` / `PivotTable`

### 亚飞

- unit_id: `unit_3833805476815142925`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率
- component: `node_ocmm5x8gaj1` / `PivotTable`

### 曹忆

- unit_id: `unit_3833805476815142939`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `zhuguan`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率
- component: `node_ocmm5xvur81` / `PivotTable`

### 肖晗IP

- unit_id: `unit_3833805476815142953`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `zhuguan`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率
- component: `node_ocmm7lie2t1` / `PivotTable`

### 周帅IP

- unit_id: `unit_3833805476815142976`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率
- component: `node_ocmmuehfdh1` / `PivotTable`

### 收款分时间占比

- unit_id: `unit_3833805476815142977`
- model: `2424` / 每日转化数据表
- dimensions: 期次 / `qici`; 渠道 / `channel_1`
- measures: 总净收 / `gmv_t`; 周2收款 / `gmv_2`; 周2占比; 周3收款 / `gmv_3`; 周3占比; 周4收款 / `gmv_4`; 周4占比; 周5收款 / `gmv_5`; 周5占比; 周6收款 / `gmv_6`; 周6占比; 周7收款 / `gmv_7`; 周7占比; 周1收款 / `gmv_1`; 周1占比
- component: `node_ocmn1hi8361` / `PivotTable`

### 线索分时间转化数据

- unit_id: `unit_3833805476815142960`
- model: `2344` / 分析--分周期转化
- dimensions: 期次 / `qici`; 渠道 / `channel_1`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_list`; 顾问 / `name`; qici; grade_list; channel_1
- measures: 当期净收款 / `gmv_7`; 当期占比 / `当期收款占比`; 8_14天内收款占比 / `14天内收款占比(不含当期)`; 15_30天内净收款占比 / `30天内净收款占比(不含前14天)`; 非30天内净收款占比; 下期线索当期占比; 净收款 / `gmv_total`; 当期退款 / `refund_7`; 当期退款占比; 8_14天内退款占比 / `14天内退款占比(不含当期)`; 15_30天内退款占比 / `30天内退款占比(不含前14天)`; 非30天内退款占比; 下期线索当期退款占比; 总退款 / `refund_total`
- component: `node_ocmmhhw0ni1` / `PivotTable`

### 行课数据

- unit_id: `unit_3833805476815142946`
- model: `2132` / (内部)到课衰减情况
- dimensions: 期 / `qici`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; qici; department; grade_1; channel_map_1; rule_name
- measures: 退后线索 / `lead`; 课1; 课1有效; 课2; 课2有效; 课3; 课3有效; 课4; 课4有效; 课5; 课5有效; 课6; 课6有效
- component: `node_ocmm6d4ecxf` / `PivotTable`

### 外呼数据

- unit_id: `unit_3833805476815142947`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 期次 / `qici`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; qici; department; grade_1; channel_map_1
- measures: 退前线索 / `lead_count`; 退后线索 / `valid_lead_count`; 总通时 / `call_duration`; 首call; 24h外呼率; 24h沟通率; 48h外呼率; 48h沟通率; 外呼率; 沟通率; 外呼频次; 平均接通时长(min); 外呼接通率; 5min比例; 好友率; APP登录率; 深沟率; 双沟率
- component: `node_ocmm6d4ecxg` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 15_30天内净收款占比 | 30天内净收款占比(不含前14天)<br>`customized_975473876505767937` | custom_measure / measure | ifnull(sum(${gmv_30})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699906"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 15_30天内退款占比 | 30天内退款占比(不含前14天)<br>`customized_975473876610625536` | custom_measure / measure | ifnull(sum(${refund_30})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699912"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| 24h外呼 | 24h外呼率<br>`customized_975473879651495937` | custom_measure / measure | ifnull(sum(${first_call_24h})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8388293899741184"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 24h外呼率 | 24h外呼率<br>`customized_975473869077655552` | custom_measure / measure | sum(${first_call_in_24h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234626"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 24h沟通率 | 24h沟通率<br>`customized_975473869190901761` | custom_measure / measure | sum(${first_call_connected_in_24h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234629"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 48h外呼 | 48h外呼率<br>`customized_975473879764742144` | custom_measure / measure | ifnull(sum(${first_call_48h})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8388293899741185"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 48h外呼率 | 48h外呼率<br>`customized_975473869291565057` | custom_measure / measure | sum(${first_call_in_48h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234627"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 48h沟通率 | 48h沟通率<br>`customized_975473869396422656` | custom_measure / measure | sum(${first_call_connected_in_48h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234630"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 5min | 5min<br>`customized_975473879869599745` | custom_measure / measure | ifnull(sum(${long_call_5})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8392152286717952"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 5min比例 | 5min比例<br>`customized_975473869505474560` | custom_measure / measure | sum(${is_long_call})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234635"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 8_14天内收款占比 | 14天内收款占比(不含当期)<br>`customized_975473876296052737` | custom_measure / measure | ifnull(sum(${gmv_14})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699905"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 8_14天内退款占比 | 14天内退款占比(不含当期)<br>`customized_975473876405104641` | custom_measure / measure | ifnull(sum(${refund_14})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699911"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| APP | APP<br>`customized_975473879974457344` | custom_measure / measure | ifnull(sum(${app_denglu})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8392152286717953"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| APP登录率 | APP登录率<br>`customized_975473869606137856` | custom_measure / measure | sum(${is_app_denglu})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234639"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 下期线索当期占比 | 下期线索当期占比<br>`customized_975473876715483137` | custom_measure / measure | ifnull(sum(${gmv_7_h})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699908"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 下期线索当期退款占比 | 下期线索当期退款占比<br>`customized_975473876820340736` | custom_measure / measure | ifnull(sum(${refund_7_p})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699914"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| 人均报科 | 人均报科<br>`customized_975473861641154561` | custom_measure / measure | ifnull(sum(${pay_user_subs})/sum(${pay_users}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879241"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879238"}] | 经理, 主管, 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 人头转化 | 人头转化<br>`customized_975473861863452672` | custom_measure / measure | ifnull(sum(${pay_users})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879238"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 人头转化(当期) | 人头(当期)<br>`customized_975473861750206465` | custom_measure / measure | ifnull(sum(${pay_users_on_period})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879239"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 单效 | 单效<br>`customized_975473861968310273` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879249"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 单效(当期) | 单效(当期)<br>`customized_975473862068973569` | custom_measure / measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879251"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 双沟率 | 双沟率<br>`customized_975473869706801152` | custom_measure / measure | sum(${is_shuanggou})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234641"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 周1占比 | 周1占比<br>`customized_975473885359943680` | custom_measure / measure | ifnull(sum(${gmv_1})/sum(${gmv_t}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200064"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周2占比 | 周2占比<br>`customized_975473885477384192` | custom_measure / measure | ifnull(sum(${gmv_2})/sum(${gmv_t}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200065"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周3占比 | 周3占比<br>`customized_975473885590630401` | custom_measure / measure | ifnull(sum(${gmv_3})/sum(${gmv_t}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200066"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周4占比 | 周4占比<br>`customized_975473885703876608` | custom_measure / measure | ifnull(sum(${gmv_4})/sum(${gmv_t}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200067"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周5占比 | 周5占比<br>`customized_975473885808734209` | custom_measure / measure | ifnull(sum(${gmv_5})/sum(${gmv_t}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200068"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周6占比 | 周6占比<br>`customized_975473885913591808` | custom_measure / measure | ifnull(sum(${gmv_6})/sum(${gmv_t}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200069"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周7占比 | 周7占比<br>`customized_975473886018449409` | custom_measure / measure | ifnull(sum(${gmv_7})/sum(${gmv_t}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200070"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 外呼接通率 | 外呼接通率<br>`customized_975473869811658753` | custom_measure / measure | sum(${call_status})/sum(${zong_call_ci}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234634"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234633"}] | 外呼数据 |
| 外呼率 | 外呼率<br>`customized_975473869916516352` | custom_measure / measure | ifnull(sum(${first_call_cnt})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234628"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 外呼频次 | 外呼频次<br>`customized_975473870017179648` | custom_measure / measure | sum(${zong_call_ci})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234633"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 好友 | 好友率<br>`customized_975473880079314945` | custom_measure / measure | ifnull(sum(${friend_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551810"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 好友率 | 好友率<br>`customized_975473862182219776` | custom_measure / measure | sum(${friend_lead})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879234"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 好友率 | 好友率<br>`customized_975473870126231552` | custom_measure / measure | sum(${is_friend_lead})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234638"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 平均接通时长(min) | 平均接通时长(min)<br>`customized_975473870235283456` | custom_measure / measure | sum(${call_duration})/sum(${call_status}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234632"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234634"}] | 外呼数据 |
| 当期单效 | 当期单效<br>`customized_975473880188366849` | custom_measure / measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551828"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 当期占比 | 当期收款占比<br>`customized_975473876925198337` | custom_measure / measure | ifnull(sum(${gmv_7})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699904"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 当期退款占比 | 当期退款占比<br>`customized_975473877030055936` | custom_measure / measure | ifnull(sum(${refund_7})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699910"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| 截面单效 | 截面单效<br>`customized_975473880289030145` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551826"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 截面退费率 | 截面退费率<br>`customized_975473862287077377` | custom_measure / measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879248"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879247"}] | KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 接量人力 | 接量人力<br>`customized_975473862391934976` | custom_measure / measure | count(DISTINCT${employee_email_name})-1 |  | [{"needBoundaryValue": false, "orgParamType": 2, "paramId": "319197"}] | 经理, 主管, 个人 |
| 沟通率 | 沟通率<br>`customized_975473870340141057` | custom_measure / measure | ifnull(sum(${first_call_connected_cnt})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234631"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 深沟 | 深沟率<br>`customized_975473880494551040` | custom_measure / measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551811"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 深沟率 | 深沟率<br>`customized_975473862500986880` | custom_measure / measure | sum(${shengou_lead})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879235"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 深沟率 | 深沟率<br>`customized_975473870444998656` | custom_measure / measure | sum(${is_shengou})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234640"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 破蛋率 | 破蛋率<br>`customized_975473862605844481` | custom_measure / measure | ifnull(sum(${podan})/${接量人力},0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879255"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_975473862391934976"}] | 经理, 主管, 个人 |
| 订单转化 | 订单转化<br>`customized_975473862706507777` | custom_measure / measure | ifnull(sum(${pay_user_subs})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879241"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人 |
| 订单转化(当期) | 订单转化(当期)<br>`customized_975473862811365376` | custom_measure / measure | ifnull(sum(${pay_user_subs_on_period})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879242"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人 |
| 课1 | 课1<br>`customized_975473865533468673` | custom_measure / measure | sum(${ke_1})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029570"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课1 | 课1<br>`customized_975473880603602944` | custom_measure / measure | ifnull(sum(${daoke_1})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551814"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 课1有效 | 课1有效<br>`customized_975473865638326272` | custom_measure / measure | sum(${v_ke_1})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029576"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课1有效 | 课1有效<br>`customized_975473880708460545` | custom_measure / measure | ifnull(sum(${daoke_v1})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8392152286717954"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 课2 | 课2<br>`customized_975473865743183873` | custom_measure / measure | sum(${ke_2})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029571"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课2有效 | 课2有效<br>`customized_975473865843847169` | custom_measure / measure | sum(${v_ke_2})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029577"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课3 | 课3<br>`customized_975473865948704768` | custom_measure / measure | sum(${ke_3})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029572"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课3有效 | 课3有效<br>`customized_975473866053562369` | custom_measure / measure | sum(${v_ke_3})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029578"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课4 | 课4<br>`customized_975473866158419968` | custom_measure / measure | sum(${ke_4})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029573"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课4有效 | 课4有效<br>`customized_975473866263277569` | custom_measure / measure | sum(${v_ke_4})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029579"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课5 | 课5<br>`customized_975473866368135168` | custom_measure / measure | sum(${ke_5})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029574"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课5有效 | 课5有效<br>`customized_975473866472992769` | custom_measure / measure | sum(${v_ke_5})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029580"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课6 | 课6<br>`customized_975473866577850368` | custom_measure / measure | sum(${ke_6})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029575"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课6有效 | 课6有效<br>`customized_975473866678513664` | custom_measure / measure | sum(${v_ke_6})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029581"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 退款(当期) | 退款(当期)<br>`customized_975473862941388801` | custom_measure / measure | ifnull(sum(${xb_trade_income})-sum(${xb_trade_profit}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879250"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879251"}] | 经理, 主管, 个人 |
| 退费率 | 截面退费率<br>`customized_975473862287077377` | custom_measure / measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879248"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879247"}] | 经理, 主管, 个人 |
| 退费率(当期) | 退费率(当期)<br>`customized_975473863046246400` | custom_measure / measure | ifnull(${退款(当期)}/sum(${xb_trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_975473862941388801"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879250"}] | 经理, 主管, 个人 |
| 非30天内净收款占比 | 非30天内净收款占比<br>`customized_975473877139107840` | custom_measure / measure | ifnull(sum(${gmv_n30})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699907"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 非30天内退款占比 | 非30天内退款占比<br>`customized_975473877256548352` | custom_measure / measure | ifnull(sum(${refund_n30})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699913"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| 首call | 首call<br>`customized_975473870554050560` | custom_measure / measure | ifnull(sum(${is_f_call})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8432582790834176"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 首节到课 | 首节到课<br>`customized_975473863155298304` | custom_measure / measure | sum(${daoke_1})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879237"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| channel_1 | channel_1<br>`335528` | dimension / filter |  |  | [] | 线索分时间转化数据 |
| channel_map | channel_map<br>`319191` | dimension / filter |  |  | [] | KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| channel_map_1 | channel_map_1<br>`273594` | dimension / filter |  |  | [] | 外呼数据 |
| channel_map_1 | channel_map_1<br>`289671` | dimension / filter |  |  | [] | 行课数据 |
| department | department<br>`273596` | dimension / filter |  |  | [] | 外呼数据 |
| department | department<br>`289674` | dimension / filter |  |  | [] | 行课数据 |
| grade_1 | grade_1<br>`273595` | dimension / filter |  |  | [] | 外呼数据 |
| grade_1 | grade_1<br>`289672` | dimension / filter |  |  | [] | 行课数据 |
| grade_list | grade_list<br>`335531` | dimension / filter |  |  | [] | 线索分时间转化数据 |
| qici | qici<br>`273592` | dimension / filter |  |  | [] | 外呼数据 |
| qici | qici<br>`289670` | dimension / filter |  |  | [] | 行课数据 |
| qici | qici<br>`335527` | dimension / filter |  |  | [] | 线索分时间转化数据 |
| rule_name | rule_name<br>`374265` | dimension / filter |  |  | [] | 行课数据 |
| 主管 | xiaozu<br>`273597` | dimension / row_dimension |  |  | [] | 外呼数据 |
| 主管 | xiaozu<br>`289673` | dimension / row_dimension |  |  | [] | 行课数据 |
| 主管 | zhuguan<br>`319196` | dimension / row_dimension |  |  | [] | 主管, 个人, 曹忆, 肖晗IP |
| 主管 | xiaozu<br>`319199` | dimension / row_dimension |  |  | [] | KOC自孵化, 春春, 亚飞, 周帅IP |
| 主管 | xiaozu<br>`363805` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 分配日期 | assign_day_new<br>`335861` | dimension / row_dimension |  |  | [] | 进量_转化分析 |
| 年级 | grade_1<br>`273595` | dimension / row_dimension |  |  | [] | 外呼数据 |
| 年级 | grade_1<br>`289672` | dimension / row_dimension |  |  | [] | 行课数据 |
| 年级 | grade_1<br>`319192` | dimension / row_dimension |  |  | [] | 经理, 主管, 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 年级 | grade_list<br>`335531` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 期 | qici<br>`289670` | dimension / row_dimension |  |  | [] | 行课数据 |
| 期 | period_name<br>`319190` | dimension / row_dimension |  |  | [] | 经理, 主管, 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 期次 | qici<br>`273592` | dimension / row_dimension |  |  | [] | 外呼数据 |
| 期次 | qici<br>`335527` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 期次 | qici<br>`365768` | dimension / row_dimension |  |  | [] | 收款分时间占比 |
| 渠道 | channel_1<br>`335528` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 渠道 | channel_1<br>`365769` | dimension / row_dimension |  |  | [] | 收款分时间占比 |
| 经理 | jingli<br>`319195` | dimension / row_dimension |  |  | [] | 经理, 主管, 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 经理 | jingli<br>`322380` | dimension / row_dimension |  |  | [] | 外呼数据 |
| 经理 | jingli<br>`322444` | dimension / row_dimension |  |  | [] | 行课数据 |
| 经理 | jingli<br>`363804` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 顾问 | employee_email_name<br>`273598` | dimension / row_dimension |  |  | [] | 外呼数据 |
| 顾问 | employee_email_name<br>`289698` | dimension / row_dimension |  |  | [] | 行课数据 |
| 顾问 | employee_email_name<br>`319197` | dimension / row_dimension |  |  | [] | 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 顾问 | name<br>`335532` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 净收款 | trade_profit<br>`8337294278879249` | measure / measure | sum(8337294278879249) |  | [] | 经理, 主管, 个人 |
| 净收款 | gmv_total<br>`8456155560699909` | measure / measure | sum(8456155560699909) |  | [] | 线索分时间转化数据 |
| 净收款(当期) | xb_trade_profit<br>`8337294278879251` | measure / measure | sum(8337294278879251) |  | [] | 经理, 主管, 个人 |
| 周1收款 | gmv_1<br>`8466748058200064` | measure / measure | sum(8466748058200064) |  | [] | 收款分时间占比 |
| 周2收款 | gmv_2<br>`8466748058200065` | measure / measure | sum(8466748058200065) |  | [] | 收款分时间占比 |
| 周3收款 | gmv_3<br>`8466748058200066` | measure / measure | sum(8466748058200066) |  | [] | 收款分时间占比 |
| 周4收款 | gmv_4<br>`8466748058200067` | measure / measure | sum(8466748058200067) |  | [] | 收款分时间占比 |
| 周5收款 | gmv_5<br>`8466748058200068` | measure / measure | sum(8466748058200068) |  | [] | 收款分时间占比 |
| 周6收款 | gmv_6<br>`8466748058200069` | measure / measure | sum(8466748058200069) |  | [] | 收款分时间占比 |
| 周7收款 | gmv_7<br>`8466748058200070` | measure / measure | sum(8466748058200070) |  | [] | 收款分时间占比 |
| 当期净收款 | gmv_7<br>`8456155560699904` | measure / measure | sum(8456155560699904) |  | [] | 线索分时间转化数据 |
| 当期退款 | refund_7<br>`8456155560699910` | measure / measure | sum(8456155560699910) |  | [] | 线索分时间转化数据 |
| 总净收 | gmv_t<br>`8466748058200071` | measure / measure | sum(8466748058200071) |  | [] | 收款分时间占比 |
| 总收款 | trade_income<br>`8337294278879247` | measure / measure | sum(8337294278879247) |  | [] | 经理, 主管, 个人 |
| 总收款(当期) | xb_trade_income<br>`8337294278879250` | measure / measure | sum(8337294278879250) |  | [] | 经理, 主管, 个人 |
| 总退款 | refund_total<br>`8456155560699915` | measure / measure | sum(8456155560699915) |  | [] | 线索分时间转化数据 |
| 总通时 | call_duration<br>`8103974494234632` | measure / measure | sum(8103974494234632) |  | [] | 外呼数据 |
| 收款 | trade_income<br>`8337294278879247` | measure / measure | sum(8337294278879247) |  | [] | KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 收款(当期) | xb_trade_income<br>`8337294278879250` | measure / measure | sum(8337294278879250) |  | [] | KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 退前线索 | lead_count<br>`8465935477925888` | measure / measure | sum(8465935477925888) |  | [] | 外呼数据 |
| 退前线索 | lead_count<br>`8590324328392704` | measure / measure | sum(8590324328392704) |  | [] | 进量_转化分析 |
| 退后线索 | valid_lead_count<br>`8103974494234625` | measure / measure | sum(8103974494234625) |  | [] | 外呼数据 |
| 退后线索 | lead<br>`8172915650029568` | measure / measure | sum(8172915650029568) |  | [] | 行课数据 |
| 退后线索 | can_renew_ds_count_a<br>`8337294278879233` | measure / measure | sum(8337294278879233) |  | [] | 经理, 主管, 个人, KOC自孵化, 春春, 亚飞, 曹忆, 肖晗IP, 周帅IP |
| 退后线索 | can_renew_ds_count_a<br>`8387973858551809` | measure / measure | sum(8387973858551809) |  | [] | 进量_转化分析 |
| 退款 | trade_refund<br>`8337294278879248` | measure / measure | sum(8337294278879248) |  | [] | 经理, 主管, 个人 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3833805476815142917` | `public_filter_relation_3833805476815142919` | `311320` | period_name | in / 2 | [] |
| `public_filter_3833805476815142921` | `public_filter_relation_3833805476815142919` | `311322` | lead_purchase_intention_level2_category_name | in /  | [] |
| `public_filter_3833805476815142923` | `public_filter_relation_3833805476815142919` | `311321` | channel_map | in /  | [] |
| `public_filter_3833805476815142988` | `public_filter_relation_3833805476815142919` | `374091` | rule_name | in /  | [] |
| `public_filter_3833805476815142927` | `public_filter_relation_3833805476815142929` | `319190` | period_name | in /  | [] |
| `public_filter_3833805476815142930` | `public_filter_relation_3833805476815142929` | `319194` | depart | in /  | [] |
| `public_filter_3833805476815142932` | `public_filter_relation_3833805476815142929` | `319195` | jingli | in /  | [] |
| `public_filter_3833805476815142934` | `public_filter_relation_3833805476815142929` | `319192` | grade_1 | in /  | [] |
| `public_filter_3833805476815142966` | `public_filter_relation_3833805476815142970` | `335728` | period_name | in / True | [] |
| `public_filter_3833805476815142968` | `public_filter_relation_3833805476815142970` | `335729` | channel_map | in /  | [] |
| `public_filter_3833805476815142971` | `public_filter_relation_3833805476815142970` | `335730` | grade_1 | in /  | [] |
| `public_filter_3833805476815142973` | `public_filter_relation_3833805476815142970` | `335733` | jingli | in /  | [] |
| `public_filter_3833805476815142979` | `public_filter_relation_3833805476815142987` | `365654` | qici | in /  | [] |
| `public_filter_3833805476815142981` | `public_filter_relation_3833805476815142987` | `365769` | channel_1 | in /  | [] |
| `public_filter_3833805476815142983` | `public_filter_relation_3833805476815142987` | `365657` | grade_list | in /  | [] |
| `public_filter_3833805476815142985` | `public_filter_relation_3833805476815142987` | `365656` | jingli | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3833805476815142925` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3833805476815142926` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3833805476815142939` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3833805476815142941` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3833805476815142946` | `289670` | qici | in | ["detailFilter"] |
| `unit_3833805476815142946` | `289671` | channel_map_1 | in | ["detailFilter"] |
| `unit_3833805476815142946` | `289672` | grade_1 | in | ["detailFilter"] |
| `unit_3833805476815142946` | `289674` | department | in | ["detailFilter"] |
| `unit_3833805476815142946` | `374265` | rule_name | in | ["detailFilter"] |
| `unit_3833805476815142947` | `273592` | qici | in | ["detailFilter"] |
| `unit_3833805476815142947` | `273594` | channel_map_1 | in | ["detailFilter"] |
| `unit_3833805476815142947` | `273595` | grade_1 | in | ["detailFilter"] |
| `unit_3833805476815142947` | `273596` | department | in | ["detailFilter"] |
| `unit_3833805476815142953` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3833805476815142960` | `335527` | qici | in | ["detailFilter"] |
| `unit_3833805476815142960` | `335528` | channel_1 | in | ["detailFilter"] |
| `unit_3833805476815142960` | `335531` | grade_list | in | ["detailFilter"] |
| `unit_3833805476815142976` | `319191` | channel_map | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
