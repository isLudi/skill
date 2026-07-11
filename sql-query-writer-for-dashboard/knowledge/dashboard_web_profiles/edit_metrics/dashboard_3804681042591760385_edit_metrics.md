# 市场顾问-用户画像分析 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3804681042591760385`
- dashboard_name: `市场顾问-用户画像分析`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:10:32`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `1ce760295064cf5ce7e74b85ae788135256ae7b59409e9f16ca02bdca4edb574`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3804681042591760385&htmlId=html_3983981771025235969`
- loaded_html_id: `html_3983981771025235969`
- config_html_id: `html_3983981805640077312`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3804681042591760385_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `8` / `99` / `74` / `52`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 8 | 8 | 182 | 73 | 8 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2344` | 分析--分周期转化 | 177789 | 1 |
| `2683` | 前期流量画像-城市 | 177778 | 1 |
| `2809` | 成单用户画像整体数据 | 177780 | 1 |
| `2812` | 用户画像成单用户城市标签 | 177781 | 1 |
| `2836` | 市场渠道用户成单分析 | 177782 | 1 |
| `2883` | 市场渠道用户成单分析2 | 177783 | 1 |
| `2885` | 市场渠道用户成单分析3 | 177784 | 1 |
| `2890` | 多科用户退费 | 177786 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 不同科目退费占比(%) | `node_ocmmize8ry1` | `unit_3804745414220034049` | u_bar | node_ocllzw8twf1 /  | x=0, y=145, w=10, h=28 | False / False |
| 标题图 | `node_ocmmize8ry3` | `unit_3804755797370580993` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 不同产品退费占比(%) | `node_ocmmize8ry4` | `unit_3804761632267427840` | u_bar | node_ocllzw8twf1 /  | x=10, y=117, w=10, h=28 | False / False |
| 退费原因占比 | `node_ocmmize8ry7` | `unit_3804774188543500288` | u_pie | node_ocllzw8twf1 /  | x=10, y=145, w=10, h=28 | False / False |
| 全局筛选器 | `node_ocmmize8ry8` | `public_filter_relation_3804782665266020352` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=8, w=20, h=5 | False / False |
|   | `node_ocmnbqoblc1` | `unit_3833856102394322945` | u_material | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=4 | False / False |
| 标题图 | `node_ocmnbqoblc3` | `unit_3833864070902894593` | u_material | node_ocllzw8twf1 /  | x=0, y=173, w=20, h=4 | False / False |
| undefined_副本 | `node_ocmofgp2ub1` | `unit_3874151640555405313` | u_material | node_ocllzw8twf1 /  | x=0, y=222, w=20, h=5 | False / False |
| 流量用户画像 | `node_ocmofgp2ub2` | `unit_3874154854137556993` | u_pivot | node_ocllzw8twf1 /  | x=0, y=182, w=20, h=40 | False / False |
| 全局筛选器_副本 | `node_ocmofgp2ub3` | `public_filter_relation_3874159861500256261` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=177, w=20, h=5 | False / False |
| 全局筛选器 | `node_ocmp6jy4n21` | `public_filter_relation_3901640697883406336` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=227, w=20, h=5 | False / False |
| 指标卡组 | `node_ocmp6jy4n22` | `unit_3901639638629822464` | card | node_ocllzw8twf1 /  | x=0, y=232, w=20, h=10 | False / False |
| 多科用户成单表 | `node_ocmp6lvuig1` | `unit_3901691404520521729` | u_pivot | node_ocllzw8twf1 /  | x=0, y=242, w=20, h=35 | False / False |
| 成单用户城市占比 | `node_ocmp6lvuig2` | `unit_3901733362643238912` | u_pie | node_ocllzw8twf1 /  | x=0, y=277, w=8, h=24 | False / False |
| 透视表_副本 | `node_ocmp6o1w4a2` | `unit_3901885938907897856` | u_pivot | node_ocllzw8twf1 /  | x=8, y=277, w=12, h=24 | False / False |
| undefined_副本 | `node_ocmpgjc3ch1` | `unit_3911760818112954369` | u_material | node_ocllzw8twf1 /  | x=0, y=306, w=20, h=5 | False / False |
| 成单用户首call通时占比 | `node_ocmpgjc3ch2` | `unit_3911763282149220353` | u_pie | node_ocllzw8twf1 /  | x=0, y=311, w=7, h=25 | False / False |
| 1 | `node_ocmpid69ak1` | `unit_3913632965000523776` | u_pivot | node_ocllzw8twf1 /  | x=0, y=336, w=7, h=21 | False / False |
| 成单用户上课时长占比 | `node_ocmpid69ak2` | `unit_3913644842373492738` | u_pie | node_ocllzw8twf1 /  | x=7, y=311, w=6, h=25 | False / False |
| 1_副本 | `node_ocmpid69ak3` | `unit_3913648004741677057` | u_pivot | node_ocllzw8twf1 /  | x=7, y=336, w=6, h=21 | False / False |
| 深沟成单用户占比 | `node_ocmpid69ak4` | `unit_3913651535506427905` | u_pie | node_ocllzw8twf1 /  | x=13, y=311, w=7, h=25 | False / False |
| 1_副本_副本 | `node_ocmpid69ak5` | `unit_3913653568806137857` | u_pivot | node_ocllzw8twf1 /  | x=13, y=336, w=7, h=21 | False / False |
| 全局筛选器_副本_副本 | `node_ocmpqxas8e1` | `public_filter_relation_3922299105533534211` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=301, w=20, h=5 | False / False |
| 指标卡组 | `node_ocmq21sgsl1` | `unit_3933611388482850816` | card | node_ocllzw8twf1 /  | x=0, y=13, w=20, h=18 | False / False |
| 多科用户退费占比 | `node_ocmq3mvezw1` | `unit_3935197018570850305` | u_pivot | node_ocllzw8twf1 /  | x=0, y=69, w=20, h=42 | False / False |
| 不同年级退费占比(%) | `node_ocmr62almp1` | `unit_3974176882858893319` | u_bar | node_ocllzw8twf1 /  | x=0, y=117, w=10, h=28 | False / False |
| 全局筛选器_副本 | `node_ocmr6ad8zv1` | `public_filter_relation_3974405357886758917` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=111, w=20, h=6 | False / False |
| 分周期退费数据占比 | `node_ocmr7dw7071` | `unit_3975526029663846401` | u_pivot | node_ocllzw8twf1 /  | x=0, y=31, w=20, h=38 | False / False |

## Pivot units

### 流量用户画像

- unit_id: `unit_3874154854137556993`
- model: `2683` / 前期流量画像-城市
- dimensions: 渠道 / `channel_map`; 城市等级 / `city_level_name`
- measures: 等级占比 / `can_renew_ds_count_a`; 退前线索 / `IP_lead_count`; 退后线索 / `can_renew_ds_count_a`; 48h外呼; 5min; 深沟; 当期单效; 当期人头转化; 截面单效; 截面人头转化
- component: `node_ocmofgp2ub2` / `PivotTable`

### 多科用户成单表

- unit_id: `unit_3901691404520521729`
- model: `2809` / 成单用户画像整体数据
- dimensions: 期次 / `period_name`; 渠道 / `channel_map`
- measures: 线索量 / `lead_count`; 正价课人头 / `pay_user_head_count`; 正价课人次 / `pay_subject_person_count`; 拓课率; 净收款 / `net_income`; 1科人头 / `subject_1_user_count`; 1科人头占比; 1科GMV / `subject_1_gmv`; 1科GMV占比; 2-3科人头 / `subject_2_3_user_count`; 2-3科人头占比; 2-3科GMV / `subject_2_3_gmv`; 2-3科GMV占比; 3科以上人头 / `subject_3_plus_user_count`; 3科以上人头占比; 3科以上GMV / `subject_3_plus_gmv`; 3科以上GMV占比
- component: `node_ocmp6lvuig1` / `PivotTable`

### 透视表_副本

- unit_id: `unit_3901885938907897856`
- model: `2812` / 用户画像成单用户城市标签
- dimensions: 期次 / `period_name`; 城市等级 / `city_level_name`
- measures: 线索量 / `lead_count`; 线索量占比 / `线索量转化占比`; 净收款(截面) / `net_income_section`; 净收款占比; 人均收款; 人头转化率(截面); 单效(截面); 拓科率(截面)
- component: `node_ocmp6o1w4a2` / `PivotTable`

### 1

- unit_id: `unit_3913632965000523776`
- model: `2836` / 市场渠道用户成单分析
- dimensions: 首call通时区间 / `bucket_name`
- measures: 对应区间人数; 人数占比; 转化人头数; 人头转化率; 订单转化率; 单效(截面)
- component: `node_ocmpid69ak1` / `PivotTable`

### 1_副本

- unit_id: `unit_3913648004741677057`
- model: `2885` / 市场渠道用户成单分析3
- dimensions: 上课区间 / `bucket_name`
- measures: 对应区间人数; 人数占比; 转化人头数; 人头转化率; 订单转化率; 单效(截面)
- component: `node_ocmpid69ak3` / `PivotTable`

### 1_副本_副本

- unit_id: `unit_3913653568806137857`
- model: `2883` / 市场渠道用户成单分析2
- dimensions: 沟通状态 / `bucket_name`
- measures: 对应区间人数; 人数占比; 转化人头数; 人头转化率; 订单转化率; 单效(截面)
- component: `node_ocmpid69ak5` / `PivotTable`

### 分周期退费数据占比

- unit_id: `unit_3975526029663846401`
- model: `2344` / 分析--分周期转化
- dimensions: 期次 / `qici`; 经理 / `jingli`; 渠道 / `channel_1`; 年级 / `grade_list`; 主管 / `xiaozu`; qici; channel_1; jingli; grade_list
- measures: 退后线索 / `can_renew_ds_count_a`; 截面净收款 / `gmv_total`; 截面退费 / `refund_total`; 当期退款 / `refund_7`; 当期退款占比; 8-14天退款占比; 15-30天退款占比; 非30天退款占比; 下期线索当期退款占比
- component: `node_ocmr7dw7071` / `PivotTable`

### 多科用户退费占比

- unit_id: `unit_3935197018570850305`
- model: `2890` / 多科用户退费
- dimensions: 期次 / `period_name`; 经理 / `jingli`; 渠道 / `channel_map`; period_name; channel_map; jingli; zhuguan
- measures: 退后线索 / `valid_lead_cnt`; GMV退费率(当期); 退费金额(截面) / `refund_section_gmv`; GMV退费率(截面); 退费人头(截面) / `refund_headcount_section`; 人头退费率(截面); 1科GMV退费率; 1科人头退费率; 2-3科GMV退费率; 2-3科人头退费率; 3科+GMV退费率; 3科+人头退费率
- component: `node_ocmq3mvezw1` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 15-30天退款占比 | 15-30天退款占比<br>`customized_993969563126947840` | custom_measure / measure | ifnull(sum(${refund_30}) / sum(${refund_total}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699912"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 分周期退费数据占比 |
| 1科GMV占比 | 1科GMV占比<br>`customized_993969534165278721` | custom_measure / measure | ifnull(sum(${subject_1_gmv}) / sum(${net_income}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928517"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928515"}] | 多科用户成单表 |
| 1科GMV退费率 | 1科GMV退费率<br>`customized_993969554285355008` | custom_measure / measure | ifnull(sum(${refund_1_subject_gmv}) / sum(${net_income_1_subject_gmv}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370119"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370120"}] | 多科用户退费占比 |
| 1科人头占比 | 1科人头占比<br>`customized_993969534286913536` | custom_measure / measure | ifnull(sum(${subject_1_user_count}) / sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928516"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928513"}] | 多科用户成单表 |
| 1科人头退费率 | 1科人头退费率<br>`customized_993969554411184128` | custom_measure / measure | ifnull(sum(${refund_1_subject_headcount}) / sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370121"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9061546048972800"}] | 多科用户退费占比 |
| 2-3科GMV占比 | 2-3科GMV占比<br>`customized_993969534412742656` | custom_measure / measure | ifnull(sum(${subject_2_3_gmv}) / sum(${net_income}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8851814501476353"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928515"}] | 多科用户成单表 |
| 2-3科GMV退费率 | 2-3科GMV退费率<br>`customized_993969554524430337` | custom_measure / measure | ifnull(sum(${refund_2_3_subject_gmv}) / sum(${net_income_2_3_subject_gmv}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370122"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370123"}] | 多科用户退费占比 |
| 2-3科人头占比 | 2-3科人头占比<br>`customized_993969534538571776` | custom_measure / measure | ifnull(sum(${subject_2_3_user_count}) / sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8851814501476352"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928513"}] | 多科用户成单表 |
| 2-3科人头退费率 | 2-3科人头退费率<br>`customized_993969554658648065` | custom_measure / measure | ifnull(sum(${refund_2_3_subject_headcount}) / sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370124"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9061546048972800"}] | 多科用户退费占比 |
| 3科+GMV退费率 | 3科+GMV退费率<br>`customized_993969554780282880` | custom_measure / measure | ifnull(sum(${refund_3plus_subject_gmv}) / sum(${net_income_3plus_subject_gmv}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370125"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370126"}] | 多科用户退费占比 |
| 3科+人头退费率 | 3科+人头退费率<br>`customized_993969554897723392` | custom_measure / measure | ifnull(sum(${refund_3plus_subject_headcount}) / sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370127"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9061546048972800"}] | 多科用户退费占比 |
| 3科以上GMV占比 | 3科以上GMV占比<br>`customized_993969534668595201` | custom_measure / measure | ifnull(sum(${subject_3_plus_gmv}) / sum(${net_income}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8851814501476355"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928515"}] | 多科用户成单表 |
| 3科以上人头占比 | 3科以上人头占比<br>`customized_993969534794424321` | custom_measure / measure | ifnull(sum(${subject_3_plus_user_count}) / sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8851814501476354"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928513"}] | 多科用户成单表 |
| 48h外呼 | 48h外呼<br>`customized_993969527391477760` | custom_measure / measure | ifnull(sum(${first_call_48h})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156227"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156225"}] | 流量用户画像 |
| 5min | 5min<br>`customized_993969527529889793` | custom_measure / measure | ifnull(sum(${long_call_5})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156232"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156225"}] | 流量用户画像 |
| 8-14天退款占比 | 8-14天退款占比<br>`customized_993969563244388352` | custom_measure / measure | ifnull(sum(${refund_14}) / sum(${refund_total}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699911"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 分周期退费数据占比 |
| GMV退费率(当期) | GMV退费率(当期)<br>`customized_993969555023552512` | custom_measure / measure | ifnull(SUM(${refund_current_gmv}) / SUM(${net_income_current_gmv}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370114"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370115"}] | 多科用户退费占比 |
| GMV退费率(截面) | GMV退费率(截面)<br>`customized_993969555145187329` | custom_measure / measure | ifnull(sum(${refund_section_gmv}) / sum(${net_income_section_gmv}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370116"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370117"}] | 多科用户退费占比 |
| 下期线索当期退款占比 | 下期线索当期退款占比<br>`customized_993969563361828864` | custom_measure / measure | ifnull(sum(${refund_7_p}) / sum(${refund_total}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699914"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 分周期退费数据占比 |
| 人均收款 | 人均收款<br>`customized_993969537751408640` | custom_measure / measure | ifnull(sum(${net_income_section}) / sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771948635645954"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8852007839754243"}] | 透视表_副本 |
| 人头转化率 | 人头转化率<br>`customized_993969541253652481` | custom_measure / measure | ifnull(sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8891975891183619"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8891975891183616"}] | 1 |
| 人头转化率 | 人头转化率<br>`customized_993969544541986817` | custom_measure / measure | sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718215"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718209"}] | 1_副本_副本 |
| 人头转化率 | 人头转化率<br>`customized_993969547951955968` | custom_measure / measure | sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014599"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014593"}] | 1_副本 |
| 人头转化率(截面) | 人头转化率(截面)<br>`customized_993969537877237760` | custom_measure / measure | ifnull(sum(${pay_user_head_count}) / sum(${lead_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8852007839754243"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771948635645952"}] | 透视表_副本 |
| 人头退费率(截面) | 人头退费率(截面)<br>`customized_993969555271016449` | custom_measure / measure | ifnull(sum(${refund_headcount_section}) / sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8902653441370118"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9061546048972800"}] | 多科用户退费占比 |
| 人数占比 | 人数占比<br>`customized_993969541379481601` | custom_measure / measure | ifnull(sum(${bucket_user_cnt}) / sum(${total_lead_cnt}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8891975891183616"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892181476435969"}] | 1 |
| 人数占比 | 人数占比<br>`customized_993969544676204545` | custom_measure / measure | ifnull(sum(${bucket_user_cnt}) / sum(${total_lead_cnt}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718209"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718211"}] | 1_副本_副本 |
| 人数占比 | 人数占比<br>`customized_993969548077785088` | custom_measure / measure | ifnull(sum(${bucket_user_cnt}) / sum(${total_lead_cnt}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014593"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014595"}] | 1_副本 |
| 净收款占比 | 净收款占比<br>`customized_993969537994678272` | custom_measure / measure | ifnull(sum(${net_income_section}) / sum(${total_net_income_in_period}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771948635645954"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8852090697181184"}] | 透视表_副本 |
| 单效(截面) | 单效(截面)<br>`customized_993969538112118784` | custom_measure / measure | ifnull(sum(${net_income_section}) / sum(${lead_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771948635645954"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771948635645952"}] | 透视表_副本 |
| 单效(截面) | 单效(截面)<br>`customized_993969541505310721` | custom_measure / measure | ifnull(sum(${section_profit_amt}) / sum(${bucket_user_cnt}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8891975891183622"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8891975891183616"}] | 1 |
| 单效(截面) | 单效(截面)<br>`customized_993969544793645057` | custom_measure / measure | sum(${section_profit_amt}) / sum(${bucket_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718218"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718209"}] | 1_副本_副本 |
| 单效(截面) | 单效(截面)<br>`customized_993969548203614208` | custom_measure / measure | sum(${section_profit_amt}) / sum(${bucket_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014602"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014593"}] | 1_副本 |
| 对应区间人数 | 对应区间人数<br>`customized_993969541631139841` | custom_measure / measure | sum(${bucket_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8891975891183616"}] | 1 |
| 对应区间人数 | 对应区间人数<br>`customized_993969544915279872` | custom_measure / measure | sum(${bucket_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718209"}] | 1_副本_副本 |
| 对应区间人数 | 对应区间人数<br>`customized_993969548329443328` | custom_measure / measure | sum(${bucket_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014593"}] | 1_副本 |
| 当期人头转化 | 当期人头转化<br>`customized_993969527651524608` | custom_measure / measure | ifnull(sum(${pay_users_on_period})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156237"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156225"}] | 流量用户画像 |
| 当期单效 | 当期单效<br>`customized_993969527777353728` | custom_measure / measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156249"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156225"}] | 流量用户画像 |
| 当期退款占比 | 当期退款占比<br>`customized_993969563479269376` | custom_measure / measure | ifnull(sum(${refund_7}) / sum(${refund_total}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699910"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 分周期退费数据占比 |
| 截面人头转化 | 截面人头转化<br>`customized_993969527936737280` | custom_measure / measure | ifnull(sum(${pay_users})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156236"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156225"}] | 流量用户画像 |
| 截面单效 | 截面单效<br>`customized_993969528070955008` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156247"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156225"}] | 流量用户画像 |
| 拓科率(截面) | 拓科率(截面)<br>`customized_993969538237947904` | custom_measure / measure | ifnull((sum(${pay_subject_person_count}) - sum(${pay_user_head_count}))/sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8851950263101442"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8852007839754243"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8852007839754243"}] | 透视表_副本 |
| 拓课率 | 拓课率<br>`customized_993969534916059136` | custom_measure / measure | ifnull(sum(${pay_subject_person_count}) / sum(${pay_user_head_count}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928514"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771778132928513"}] | 多科用户成单表 |
| 深沟 | 深沟<br>`customized_993969528200978433` | custom_measure / measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156229"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8664136735156225"}] | 流量用户画像 |
| 线索量占比 | 线索量转化占比<br>`customized_993969538359582721` | custom_measure / measure | ifnull(sum(${lead_count}) / sum(${total_lead_count_in_period}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8771948635645952"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8852007839754240"}] | 透视表_副本 |
| 订单转化率 | 订单转化率<br>`customized_993969541744386048` | custom_measure / measure | ifnull(sum(${order_cnt}) / sum(${bucket_user_cnt}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8891975891183620"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8891975891183616"}] | 1 |
| 订单转化率 | 订单转化率<br>`customized_993969545154355201` | custom_measure / measure | sum(${order_cnt}) / sum(${bucket_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718216"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718209"}] | 1_副本_副本 |
| 订单转化率 | 订单转化率<br>`customized_993969548451078145` | custom_measure / measure | sum(${order_cnt}) / sum(${bucket_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014600"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014593"}] | 1_副本 |
| 转化人头数 | 转化人头数<br>`customized_993969541861826560` | custom_measure / measure | sum(${conversion_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8891975891183619"}] | 1 |
| 转化人头数 | 转化人头数<br>`customized_993969545280184321` | custom_measure / measure | sum(${conversion_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8892319738718215"}] | 1_副本_副本 |
| 转化人头数 | 转化人头数<br>`customized_993969548581101568` | custom_measure / measure | sum(${conversion_user_cnt}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8896261596014599"}] | 1_副本 |
| 非30天退款占比 | 非30天退款占比<br>`customized_993969563600904193` | custom_measure / measure | ifnull(sum(${refund_n30}) / sum(${refund_total}), 0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699913"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 分周期退费数据占比 |
| channel_1 | channel_1<br>`335528` | dimension / filter |  |  | [] | 分周期退费数据占比 |
| channel_map | channel_map<br>`484093` | dimension / filter |  |  | [] | 多科用户退费占比 |
| grade_list | grade_list<br>`335531` | dimension / filter |  |  | [] | 分周期退费数据占比 |
| jingli | jingli<br>`363804` | dimension / filter |  |  | [] | 分周期退费数据占比 |
| jingli | jingli<br>`484095` | dimension / filter |  |  | [] | 多科用户退费占比 |
| period_name | period_name<br>`484092` | dimension / filter |  |  | [] | 多科用户退费占比 |
| qici | qici<br>`335527` | dimension / filter |  |  | [] | 分周期退费数据占比 |
| zhuguan | zhuguan<br>`484096` | dimension / filter |  |  | [] | 多科用户退费占比 |
| 上课区间 | bucket_name<br>`482446` | dimension / row_dimension |  |  | [] | 1_副本 |
| 主管 | xiaozu<br>`363805` | dimension / row_dimension |  |  | [] | 分周期退费数据占比 |
| 城市等级 | city_level_name<br>`415765` | dimension / row_dimension |  |  | [] | 流量用户画像 |
| 城市等级 | city_level_name<br>`449971` | dimension / row_dimension |  |  | [] | 透视表_副本 |
| 年级 | grade_list<br>`335531` | dimension / row_dimension |  |  | [] | 分周期退费数据占比 |
| 期次 | qici<br>`335527` | dimension / row_dimension |  |  | [] | 分周期退费数据占比 |
| 期次 | period_name<br>`449728` | dimension / row_dimension |  |  | [] | 多科用户成单表 |
| 期次 | period_name<br>`449968` | dimension / row_dimension |  |  | [] | 透视表_副本 |
| 期次 | period_name<br>`484092` | dimension / row_dimension |  |  | [] | 多科用户退费占比 |
| 沟通状态 | bucket_name<br>`482081` | dimension / row_dimension |  |  | [] | 1_副本_副本 |
| 渠道 | channel_1<br>`335528` | dimension / row_dimension |  |  | [] | 分周期退费数据占比 |
| 渠道 | channel_map<br>`415758` | dimension / row_dimension |  |  | [] | 流量用户画像 |
| 渠道 | channel_map<br>`449729` | dimension / row_dimension |  |  | [] | 多科用户成单表 |
| 渠道 | channel_map<br>`484093` | dimension / row_dimension |  |  | [] | 多科用户退费占比 |
| 经理 | jingli<br>`363804` | dimension / row_dimension |  |  | [] | 分周期退费数据占比 |
| 经理 | jingli<br>`484095` | dimension / row_dimension |  |  | [] | 多科用户退费占比 |
| 首call通时区间 | bucket_name<br>`461594` | dimension / row_dimension |  |  | [] | 1 |
| 1科GMV | subject_1_gmv<br>`8771778132928517` | measure / measure | sum(8771778132928517) |  | [] | 多科用户成单表 |
| 1科人头 | subject_1_user_count<br>`8771778132928516` | measure / measure | sum(8771778132928516) |  | [] | 多科用户成单表 |
| 2-3科GMV | subject_2_3_gmv<br>`8851814501476353` | measure / measure | sum(8851814501476353) |  | [] | 多科用户成单表 |
| 2-3科人头 | subject_2_3_user_count<br>`8851814501476352` | measure / measure | sum(8851814501476352) |  | [] | 多科用户成单表 |
| 3科以上GMV | subject_3_plus_gmv<br>`8851814501476355` | measure / measure | sum(8851814501476355) |  | [] | 多科用户成单表 |
| 3科以上人头 | subject_3_plus_user_count<br>`8851814501476354` | measure / measure | sum(8851814501476354) |  | [] | 多科用户成单表 |
| 净收款 | net_income<br>`8771778132928515` | measure / measure | sum(8771778132928515) |  | [] | 多科用户成单表 |
| 净收款(截面) | net_income_section<br>`8771948635645954` | measure / measure | sum(8771948635645954) |  | [] | 透视表_副本 |
| 当期退款 | refund_7<br>`8456155560699910` | measure / measure | sum(8456155560699910) |  | [] | 分周期退费数据占比 |
| 截面净收款 | gmv_total<br>`8456155560699909` | measure / measure | sum(8456155560699909) |  | [] | 分周期退费数据占比 |
| 截面退费 | refund_total<br>`8456155560699915` | measure / measure | sum(8456155560699915) |  | [] | 分周期退费数据占比 |
| 正价课人头 | pay_user_head_count<br>`8771778132928513` | measure / measure | sum(8771778132928513) |  | [] | 多科用户成单表 |
| 正价课人次 | pay_subject_person_count<br>`8771778132928514` | measure / measure | sum(8771778132928514) |  | [] | 多科用户成单表 |
| 等级占比 | can_renew_ds_count_a<br>`8664136735156225` | measure / measure | sum(8664136735156225) |  | [] | 流量用户画像 |
| 线索量 | lead_count<br>`8771778132928512` | measure / measure | sum(8771778132928512) |  | [] | 多科用户成单表 |
| 线索量 | lead_count<br>`8771948635645952` | measure / measure | sum(8771948635645952) |  | [] | 透视表_副本 |
| 退前线索 | IP_lead_count<br>`8664136735156224` | measure / measure | sum(8664136735156224) |  | [] | 流量用户画像 |
| 退后线索 | can_renew_ds_count_a<br>`8664136735156225` | measure / measure | sum(8664136735156225) |  | [] | 流量用户画像 |
| 退后线索 | valid_lead_cnt<br>`8902653441370112` | measure / measure | sum(8902653441370112) |  | [] | 多科用户退费占比 |
| 退后线索 | can_renew_ds_count_a<br>`9060600883668992` | measure / measure | sum(9060600883668992) |  | [] | 分周期退费数据占比 |
| 退费人头(截面) | refund_headcount_section<br>`8902653441370118` | measure / measure | sum(8902653441370118) |  | [] | 多科用户退费占比 |
| 退费金额(截面) | refund_section_gmv<br>`8902653441370116` | measure / measure | sum(8902653441370116) |  | [] | 多科用户退费占比 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3804782665266020354` | `public_filter_relation_3804782665266020352` | `482447` | period_name | in / True | [] |
| `public_filter_3804784163314511874` | `public_filter_relation_3804782665266020352` | `482448` | channel_map | in /  | [] |
| `public_filter_3804784566616104961` | `public_filter_relation_3804782665266020352` | `482449` | grade_name | in /  | [] |
| `public_filter_3933593272914776065` | `public_filter_relation_3804782665266020352` | `482450` | jingli | in /  | [] |
| `public_filter_3874159861500256258` | `public_filter_relation_3874159861500256261` | `415757` | period_name | in / True | [] |
| `public_filter_3874159861500256259` | `public_filter_relation_3874159861500256261` | `415758` | channel_map | in /  | [] |
| `public_filter_3874159861500256260` | `public_filter_relation_3874159861500256261` | `415759` | grade_1 | in /  | [] |
| `public_filter_3901640697883406338` | `public_filter_relation_3901640697883406336` | `449728` | period_name | in / True | [] |
| `public_filter_3901641729796685826` | `public_filter_relation_3901640697883406336` | `449729` | channel_map | in /  | [] |
| `public_filter_3901642134286589953` | `public_filter_relation_3901640697883406336` | `449730` | grade_name | in /  | [] |
| `public_filter_3901642604540227585` | `public_filter_relation_3901640697883406336` | `449731` | manager_name | in /  | [] |
| `public_filter_3922299105533534209` | `public_filter_relation_3922299105533534211` | `461592` | grade_name | in /  | [] |
| `public_filter_3922299105533534213` | `public_filter_relation_3922299105533534211` | `461590` | channel_map | in /  | [] |
| `public_filter_3922299105533534214` | `public_filter_relation_3922299105533534211` | `461589` | period_name | in / True | [] |
| `public_filter_3974405357886758912` | `public_filter_relation_3974405357886758917` | `337135` | qici | in / True | [] |
| `public_filter_3974405357886758914` | `public_filter_relation_3974405357886758917` | `337139` | grade_list | in /  | [] |
| `public_filter_3974405357886758916` | `public_filter_relation_3974405357886758917` | `337137` | jingli | in /  | [] |
| `public_filter_3974407181974626305` | `public_filter_relation_3974405357886758917` | `337138` | xiaozu | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3935197018570850305` | `484092` | period_name | in | ["detailFilter"] |
| `unit_3935197018570850305` | `484093` | channel_map | in | ["detailFilter"] |
| `unit_3935197018570850305` | `484095` | jingli | in | ["detailFilter"] |
| `unit_3935197018570850305` | `484096` | zhuguan | in | ["detailFilter"] |
| `unit_3975526029663846401` | `335527` | qici | in | ["detailFilter"] |
| `unit_3975526029663846401` | `335528` | channel_1 | in | ["detailFilter"] |
| `unit_3975526029663846401` | `335531` | grade_list | in | ["detailFilter"] |
| `unit_3975526029663846401` | `363804` | jingli | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
