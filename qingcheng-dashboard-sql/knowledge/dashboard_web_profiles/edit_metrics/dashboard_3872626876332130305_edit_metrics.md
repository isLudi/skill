# 团队转化完成度-青橙 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3872626876332130305`
- dashboard_name: `团队转化完成度-青橙`
- domain: `qingcheng`
- captured_at: `2026-07-18 22:26:05`
- menu_status: `1`
- profile_sha256: `4154ddbdc045bc1a2696981417cb09db0ee70ff78d5dfeb433ff7e4252efb977`
- raw_profile: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-profile-20260718-class-refund\20260718-222553-22428-75ebca4f\dashboard_3872626876332130305_edit_metrics_profile.json`

## Model coverage

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2677` | 团队完成度【月】 |  | 3 |
| `2680` | 团队完成度【期】 |  | 3 |

## Components and layout

| title | node_id | unit_id | type | parent / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
|  | `node_ocmodyldp41` | `unit_3872636709627731969` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
|  | `node_ocmopf8cdy3` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=84, w=20, h=53 | False / False |
|  | `node_ocmopf8k6l4` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=20, w=20, h=59 | False / False |
| 全局筛选器 | `node_ocmopf8k6l8` | `public_filter_relation_3884310637094973441` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=15, w=20, h=5 | False / False |
| 全局筛选器 | `node_ocmopf8k6l9` | `public_filter_relation_3884310962329395200` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=79, w=20, h=5 | False / False |
| 小组-期_退4 | `node_ocmoprqx1n1` | `unit_3884268636652077057` | u_pivot | node_ocmopf8k6l4 / 8n34 | x=0, y=0, w=10, h=12 | False / False |
| 小组-月 | `node_ocmoprqx1n3` | `unit_3872631539138375680` | u_pivot | node_ocmopf8cdy3 / ks4v | x=0, y=0, w=10, h=11 | False / False |
| 大组-期_退4 | `node_ocmopt186p1` | `unit_3884652049659666436` | u_pivot | node_ocmopf8k6l4 / jiu1 | x=0, y=0, w=10, h=8 | False / False |
| 学部-期_退4 | `node_ocmopt186p2` | `unit_3884652097619013635` | u_pivot | node_ocmopf8k6l4 / 29o8 | x=0, y=0, w=10, h=9 | False / False |
| 大组-月 | `node_ocmopt1cz41` | `unit_3884667936917241860` | u_pivot | node_ocmopf8cdy3 / jiu1 | x=0, y=0, w=10, h=9 | False / False |
| 学部-月 | `node_ocmopt1cz42` | `unit_3884668794603847684` | u_pivot | node_ocmopf8cdy3 / 29o8 | x=0, y=0, w=10, h=9 | False / False |
| 文本框 | `node_ocmopukdd11` | `unit_3884690273524596737` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=11 | False / False |

## Pivot units

### 小组-期_退4

- unit_id: `unit_3884268636652077057`
- model: `2680` / 团队完成度【期】
- dimensions: 小组 / `xiaozu`; 学部 / `xuebu`; xiaozu
- measures: 团队人数 / `emye_c`; 营收金额 / `income`; 退费金额 / `refund`; 净金额 / `promit`; 破蛋人数 / `podan_4`; 破蛋率 / `破蛋率-退4`; 退费人数 / `re_payer_4`; 退费占比 / `退费占比-退4`; 期人效 / `期人效-退4`; 折算净收款 / `折算净收款-退4`; 期目标 / `goal`; 期目标完成率
- component: `node_ocmoprqx1n1` / `小组-期_退4`

### 大组-期_退4

- unit_id: `unit_3884652049659666436`
- model: `2680` / 团队完成度【期】
- dimensions: 大组 / `dazu`
- measures: 团队人数 / `emye_c`; 营收金额 / `income`; 退费金额 / `refund`; 净收款 / `promit`; 期目标 / `goal`; 破蛋人数 / `podan_4`; 破蛋率 / `破蛋率-退4`; 退费人数 / `re_payer_4`; 退费占比 / `退费占比-退4`; 期人效 / `期人效-退4`; 折算净收款 / `折算净收款-退4`; 期目标完成率 / `期目标完成率-退4`
- component: `node_ocmopt186p1` / `大组-期_退4`

### 学部-期_退4

- unit_id: `unit_3884652097619013635`
- model: `2680` / 团队完成度【期】
- dimensions: 学部 / `xuebu`
- measures: 团队人数 / `emye_c`; 营收金额 / `income`; 退费金额 / `refund`; 净收款 / `promit`; 期目标 / `goal`; 破蛋人数 / `podan_4`; 破蛋率 / `破蛋率-退4`; 退费人数 / `re_payer_4`; 退费占比 / `退费占比-退4`; 期人效 / `期人效-退4`; 折算净收款; 期目标完成率 / `期目标完成率-退4`
- component: `node_ocmopt186p2` / `学部-期_退4`

### 小组-月

- unit_id: `unit_3872631539138375680`
- model: `2677` / 团队完成度【月】
- dimensions: 小组 / `xiaozu`; 学部 / `xuebu`; xiaozu
- measures: 团队人数 / `emye_c`; 营收金额 / `income`; 退费金额 / `refund`; 净收款 / `promit`; 破蛋人数 / `podan`; 破蛋率 / `破蛋率-退4`; 退费人数 / `re_payer_4`; 退费占比 / `退费占比-退4`; 月人效 / `月人效-退4`; 折算净收款 / `折算净收款-退4`; 月目标 / `goal`; 月目标完成率 / `月目标完成率--退4`
- component: `node_ocmoprqx1n3` / `小组-月`

### 大组-月

- unit_id: `unit_3884667936917241860`
- model: `2677` / 团队完成度【月】
- dimensions: 大组 / `dazu`; 学部 / `xuebu`
- measures: 团队人数 / `emye_c`; 营收金额 / `income`; 退费金额 / `refund`; 净收款 / `promit`; 月目标 / `goal`; 破蛋人数 / `podan`; 破蛋率 / `破蛋率-退4`; 退费人数 / `re_payer_4`; 退费占比 / `退费占比-退4`; 月人效 / `月人效-退4`; 折算净收款 / `折算净收款-退4`; 月目标完成率 / `月目标完成率--退4`
- component: `node_ocmopt1cz41` / `大组-月`

### 学部-月

- unit_id: `unit_3884668794603847684`
- model: `2677` / 团队完成度【月】
- dimensions: 学部 / `xuebu`
- measures: 团队人数 / `emye_c`; 营收金额 / `income`; 退款金额 / `refund`; 净收款 / `promit`; 月目标 / `goal`; 破蛋人数 / `podan`; 破蛋率 / `破蛋率-退4`; 退费人数 / `re_payer_4`; 退费占比 / `退费占比-退4`; 月人效 / `月人效-退4`; 折算净收款; 月目标完成率 / `月目标完成率--退4`
- component: `node_ocmopt1cz42` / `学部-月`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 小组 | xiaozu<br>`414770` | dimension / row_dimension |  |  |  | 小组-期_退4 |
| 学部 | xuebu<br>`414767` | dimension / row_dimension |  |  |  | 小组-期_退4 |
| 团队人数 | emye_c<br>`8703823135205376` | measure / measure | sum(8703823135205376) |  |  | 小组-期_退4 |
| 营收金额 | income<br>`8703823135205380` | measure / measure | sum(8703823135205380) |  |  | 小组-期_退4 |
| 退费金额 | refund<br>`8703823135205381` | measure / measure | sum(8703823135205381) |  |  | 小组-期_退4 |
| 净金额 | promit<br>`8703823135205382` | measure / measure | sum(8703823135205382) |  |  | 小组-期_退4 |
| 破蛋人数 | podan_4<br>`8703823135205389` | measure / measure | sum(8703823135205389) |  |  | 小组-期_退4 |
| 破蛋率 | 破蛋率-退4<br>`customized_987303565706842113` | custom_measure / measure | ifnull(sum(${podan_4})/sum(${emye_c}),0) |  | [{"paramId": "8703823135205389", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703823135205376", "orgParamType": 1, "needBoundaryValue": false}] | 小组-期_退4 |
| 退费人数 | re_payer_4<br>`8703823135205388` | measure / measure | sum(8703823135205388) |  |  | 小组-期_退4 |
| 退费占比 | 退费占比-退4<br>`customized_987303565924945921` | custom_measure / measure | ifnull(sum(${refund_4})/sum(${income}),0) |  | [{"paramId": "8703823135205386", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703823135205380", "orgParamType": 1, "needBoundaryValue": false}] | 小组-期_退4 |
| 期人效 | 期人效-退4<br>`customized_987303565258051584` | custom_measure / measure | ifnull(sum(${promit_4})/sum(${emye_c}),0) |  | [{"paramId": "8703823135205387", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703823135205376", "orgParamType": 1, "needBoundaryValue": false}] | 小组-期_退4 |
| 折算净收款 | 折算净收款-退4<br>`customized_987303565027364865` | custom_measure / measure | ifnull(sum(${n_H_promit_4})*0.5 + sum(${H_promit_4}),0) |  | [{"paramId": "8703823135205385", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703823135205384", "orgParamType": 1, "needBoundaryValue": false}] | 小组-期_退4 |
| 期目标 | goal<br>`8703823135205377` | measure / measure | sum(8703823135205377) |  |  | 小组-期_退4 |
| 期目标完成率 | 期目标完成率<br>`customized_987303565371297793` | custom_measure / measure | ifnull(${折算净收款}/sum(${goal}),0) |  | [{"paramId": "customized_987303564905730048", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "8703823135205377", "orgParamType": 1, "needBoundaryValue": false}] | 小组-期_退4 |
| xiaozu | xiaozu<br>`414770` | dimension / filter |  |  |  | 小组-期_退4 |
| 大组 | dazu<br>`414769` | dimension / row_dimension |  |  |  | 大组-期_退4 |
| 净收款 | promit<br>`8703823135205382` | measure / measure | sum(8703823135205382) |  |  | 大组-期_退4 |
| 期目标完成率 | 期目标完成率-退4<br>`customized_987303565484544000` | custom_measure / measure | ifnull(sum(${promit_4})/sum(${goal}),0) |  | [{"paramId": "8703823135205387", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703823135205377", "orgParamType": 1, "needBoundaryValue": false}] | 大组-期_退4 |
| 折算净收款 | 折算净收款<br>`customized_987303564905730048` | custom_measure / measure | sum(${H_promit})+sum(${n_H_promit})*0.5 |  | [{"paramId": "8703823135205378", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703823135205379", "orgParamType": 1, "needBoundaryValue": false}] | 学部-期_退4 |
| 小组 | xiaozu<br>`414316` | dimension / row_dimension |  |  |  | 小组-月 |
| 学部 | xuebu<br>`414313` | dimension / row_dimension |  |  |  | 小组-月 |
| 团队人数 | emye_c<br>`8703694032168960` | measure / measure | sum(8703694032168960) |  |  | 小组-月 |
| 营收金额 | income<br>`8703521624254466` | measure / measure | sum(8703521624254466) |  |  | 小组-月 |
| 退费金额 | refund<br>`8703521624254467` | measure / measure | sum(8703521624254467) |  |  | 小组-月 |
| 净收款 | promit<br>`8703521624254468` | measure / measure | sum(8703521624254468) |  |  | 小组-月 |
| 破蛋人数 | podan<br>`8658235459921924` | measure / measure | sum(8658235459921924) |  |  | 小组-月 |
| 破蛋率 | 破蛋率-退4<br>`customized_987303561843888128` | custom_measure / measure | ifnull(sum(${podan_4})/sum(${emye_c}),0) |  | [{"paramId": "8703521624254475", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703694032168960", "orgParamType": 1, "needBoundaryValue": false}] | 小组-月 |
| 退费人数 | re_payer_4<br>`8703521624254474` | measure / measure | sum(8703521624254474) |  |  | 小组-月 |
| 退费占比 | 退费占比-退4<br>`customized_987303562070380544` | custom_measure / measure | ifnull(sum(${refund_4})/sum(${income}),0) |  | [{"paramId": "8703521624254472", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703521624254466", "orgParamType": 1, "needBoundaryValue": false}] | 小组-月 |
| 月人效 | 月人效-退4<br>`customized_987303561403486209` | custom_measure / measure | ifnull(sum(${promit_4})/sum(${emye_c}),0) |  | [{"paramId": "8703521624254473", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703694032168960", "orgParamType": 1, "needBoundaryValue": false}] | 小组-月 |
| 折算净收款 | 折算净收款-退4<br>`customized_987303561181188096` | custom_measure / measure | ifnull(sum(${n_H_promit_4})*0.5 + sum(${H_promit_4}),0) |  | [{"paramId": "8703521624254471", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703521624254470", "orgParamType": 1, "needBoundaryValue": false}] | 小组-月 |
| 月目标 | goal<br>`8703694032168961` | measure / measure | sum(8703694032168961) |  |  | 小组-月 |
| 月目标完成率 | 月目标完成率--退4<br>`customized_987303561621590017` | custom_measure / measure | ifnull(${折算净收款-退4}/sum(${goal}),0) |  | [{"paramId": "customized_987303561181188096", "orgParamType": 4, "needBoundaryValue": false}, {"paramId": "8703694032168961", "orgParamType": 1, "needBoundaryValue": false}] | 小组-月 |
| xiaozu | xiaozu<br>`414316` | dimension / filter |  |  |  | 小组-月 |
| 大组 | dazu<br>`414315` | dimension / row_dimension |  |  |  | 大组-月 |
| 退款金额 | refund<br>`8703521624254467` | measure / measure | sum(8703521624254467) |  |  | 学部-月 |
| 折算净收款 | 折算净收款<br>`customized_987303561072136192` | custom_measure / measure | sum(${H_promit})+sum(${n_H_promit}) |  | [{"paramId": "8703521624254464", "orgParamType": 1, "needBoundaryValue": false}, {"paramId": "8703521624254465", "orgParamType": 1, "needBoundaryValue": false}] | 学部-月 |

## Dataset fields

### subject `170782`

| key | title | path | org_param_type | data_type |
|---|---|---|---|---|
| `414311` | month | 维度 / month | 2 | 2 |
| `414313` | xuebu | 维度 / xuebu | 2 | 2 |
| `414315` | dazu | 维度 / dazu | 2 | 2 |
| `414316` | xiaozu | 维度 / xiaozu | 2 | 2 |
| `462229` | xiaozu1 | 维度 / xiaozu1 | 2 | 2 |
| `8703521624254475` | podan_4 | 维度 / 转化维度 / podan_4 | 1 | 1 |
| `8658235459921924` | podan | 指标 / podan | 1 | 1 |
| `8703521624254464` | H_promit | 指标 / H_promit | 1 | 1 |
| `8703521624254465` | n_H_promit | 指标 / n_H_promit | 1 | 1 |
| `8703521624254466` | income | 指标 / income | 1 | 1 |
| `8703521624254467` | refund | 指标 / refund | 1 | 1 |
| `8703521624254468` | promit | 指标 / promit | 1 | 1 |
| `8703521624254469` | re_payer | 指标 / re_payer | 1 | 1 |
| `8703521624254470` | H_promit_4 | 指标 / H_promit_4 | 1 | 1 |
| `8703521624254471` | n_H_promit_4 | 指标 / n_H_promit_4 | 1 | 1 |
| `8703521624254472` | refund_4 | 指标 / refund_4 | 1 | 1 |
| `8703521624254473` | promit_4 | 指标 / promit_4 | 1 | 1 |
| `8703521624254474` | re_payer_4 | 指标 / re_payer_4 | 1 | 1 |
| `8703694032168960` | emye_c | 指标 / emye_c | 1 | 1 |
| `8703694032168961` | goal | 指标 / goal | 1 | 1 |
| `8818693728200704` | Y_promit_4 | 指标 / Y_promit_4 | 1 | 1 |
| `8818693728200705` | Y_income_4 | 指标 / Y_income_4 | 1 | 1 |
| `9135729846740992` | class_refund_4 | 指标 / class_refund_4 | 1 | 1 |
| `customized_987303561072136192` | 折算净收款 | 指标 / 自定义指标 / 折算净收款 | 4 | 1 |
| `customized_987303561181188096` | 折算净收款-退4 | 指标 / 自定义指标 / 折算净收款-退4 | 4 | 1 |
| `customized_987303561294434305` | 月人效 | 指标 / 自定义指标 / 月人效 | 4 | 1 |
| `customized_987303561403486209` | 月人效-退4 | 指标 / 自定义指标 / 月人效-退4 | 4 | 1 |
| `customized_987303561512538113` | 月目标完成率 | 指标 / 自定义指标 / 月目标完成率 | 4 | 1 |
| `customized_987303561621590017` | 月目标完成率--退4 | 指标 / 自定义指标 / 月目标完成率--退4 | 4 | 1 |
| `customized_987303561730641921` | 破蛋率 | 指标 / 自定义指标 / 破蛋率 | 4 | 1 |
| `customized_987303561843888128` | 破蛋率-退4 | 指标 / 自定义指标 / 破蛋率-退4 | 4 | 1 |
| `customized_987303561957134337` | 退费占比 | 指标 / 自定义指标 / 退费占比 | 4 | 1 |
| `customized_987303562070380544` | 退费占比-退4 | 指标 / 自定义指标 / 退费占比-退4 | 4 | 1 |

### subject `170783`

| key | title | path | org_param_type | data_type |
|---|---|---|---|---|
| `414767` | xuebu | 维度 / xuebu | 2 | 2 |
| `414769` | dazu | 维度 / dazu | 2 | 2 |
| `414770` | xiaozu | 维度 / xiaozu | 2 | 2 |
| `430609` | qici | 维度 / qici | 2 | 2 |
| `462234` | xiaozu1 | 维度 / xiaozu1 | 2 | 2 |
| `8659858843854852` | re_payer | 指标 / re_payer | 1 | 1 |
| `8703823135205376` | emye_c | 指标 / emye_c | 1 | 1 |
| `8703823135205377` | goal | 指标 / goal | 1 | 1 |
| `8703823135205378` | H_promit | 指标 / H_promit | 1 | 1 |
| `8703823135205379` | n_H_promit | 指标 / n_H_promit | 1 | 1 |
| `8703823135205380` | income | 指标 / income | 1 | 1 |
| `8703823135205381` | refund | 指标 / refund | 1 | 1 |
| `8703823135205382` | promit | 指标 / promit | 1 | 1 |
| `8703823135205383` | podan | 指标 / podan | 1 | 1 |
| `8703823135205384` | H_promit_4 | 指标 / H_promit_4 | 1 | 1 |
| `8703823135205385` | n_H_promit_4 | 指标 / n_H_promit_4 | 1 | 1 |
| `8703823135205386` | refund_4 | 指标 / refund_4 | 1 | 1 |
| `8703823135205387` | promit_4 | 指标 / promit_4 | 1 | 1 |
| `8703823135205388` | re_payer_4 | 指标 / re_payer_4 | 1 | 1 |
| `8703823135205389` | podan_4 | 指标 / podan_4 | 1 | 1 |
| `8818572174583808` | Y_promit_4 | 指标 / Y_promit_4 | 1 | 1 |
| `8818572174583809` | Y_income_4 | 指标 / Y_income_4 | 1 | 1 |
| `9135726488676352` | class_refund_4 | 指标 / class_refund_4 | 1 | 1 |
| `customized_987303564905730048` | 折算净收款 | 指标 / 自定义指标 / 折算净收款 | 4 | 1 |
| `customized_987303565027364865` | 折算净收款-退4 | 指标 / 自定义指标 / 折算净收款-退4 | 4 | 1 |
| `customized_987303565144805377` | 期人效 | 指标 / 自定义指标 / 期人效 | 4 | 1 |
| `customized_987303565258051584` | 期人效-退4 | 指标 / 自定义指标 / 期人效-退4 | 4 | 1 |
| `customized_987303565371297793` | 期目标完成率 | 指标 / 自定义指标 / 期目标完成率 | 4 | 1 |
| `customized_987303565484544000` | 期目标完成率-退4 | 指标 / 自定义指标 / 期目标完成率-退4 | 4 | 1 |
| `customized_987303565601984512` | 破蛋率 | 指标 / 自定义指标 / 破蛋率 | 4 | 1 |
| `customized_987303565706842113` | 破蛋率-退4 | 指标 / 自定义指标 / 破蛋率-退4 | 4 | 1 |
| `customized_987303565815894017` | 退费占比 | 指标 / 自定义指标 / 退费占比 | 4 | 1 |
| `customized_987303565924945921` | 退费占比-退4 | 指标 / 自定义指标 / 退费占比-退4 | 4 | 1 |
| `customized_987303566033997825` | 退费均值 | 指标 / 自定义指标 / 退费均值 | 4 | 1 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3884310637094973443` | `public_filter_relation_3884310637094973441` | `430609` | qici | in / 1 | ["node_ocmoprqx1n1", "node_ocmopt186p1", "node_ocmopt186p2"] |
| `public_filter_3884310962329395202` | `public_filter_relation_3884310962329395200` | `414311` | month | in / 1 | ["node_ocmoprqx1n3", "node_ocmopt1cz41", "node_ocmopt1cz42"] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3872631539138375680` | `414316` | xiaozu | in | ["detailFilter"] |
| `unit_3884268636652077057` | `414770` | xiaozu | in | ["detailFilter"] |

## Text units

- `unit_3884690273524596737`: 说明：<br>1. 小组、大组均剔除开课4节课后和点睛班开课2节课后退费       2. 一对一产出：退费永久回溯     3. 学部退费全部计算           4. 非H业务线按50%计算      5. 完成度 = 折算净收款/目标      <br>6. 破蛋人数 = 净收 > 0 顾问人数       7.   仅包含订单的课程类型为专题课和系列课的                8. 整点到整点15抽取截至两小时前的数据<br>注：绿色：破蛋率 ≥ 80%，退费占比 ≤ 10%，期目标完成度 ≥ 100%         红色：破蛋率 < 80%，退费占比 > 10%，期目标完成度 < 100%
- `unit_3884690273524596737`: 说明：<br>1. 小组、大组均剔除普通班开课4节课后和点睛班开课2节课后退费     2. 学部退费全部计算       3. 非H业务线按50%计算      4. 完成度 = 折算净收款/目标      <br>5. 破蛋人数 = 净收 > 0 顾问人数       6.   仅包含订单的课程类型为专题课和系列课的                7. 整点到整点15抽取截至两小时前的数据<br>注：绿色：破蛋率 ≥ 80%，退费占比 ≤ 10%，期目标完成度 ≥ 100%         红色：破蛋率 < 80%，退费占比 > 10%，期目标完成度 < 100%

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
