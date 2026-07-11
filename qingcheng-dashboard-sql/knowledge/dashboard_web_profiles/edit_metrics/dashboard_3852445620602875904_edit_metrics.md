# 青橙-全域产品数据看板 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3852445620602875904`
- dashboard_name: `青橙-全域产品数据看板`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:15:36`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `543b4f7016f52edab1e24eed14576260f5111f85ca4747b0a13b298f04668f1b`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3852445620602875904&htmlId=html_3983986735476035585`
- loaded_html_id: `html_3983986735476035585`
- config_html_id: `html_3983986770135732225`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-project\dashboard_3852445620602875904_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `4` / `74` / `48` / `16`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 4 | 4 | 126 | 44 | 14 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2576` | 年季月营收情况 | 156048 | 4 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmnu2f1vr1` | `unit_3852445866631221248` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 期次数据 | `node_ocmnu2f1vr2` | `unit_3852450245030936577` | u_pivot | node_ocllzw8twf1 /  | x=0, y=58, w=20, h=31 | False / False |
| 文本框 | `node_ocmnu2f1vr3` | `unit_3852612515549360128` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=6 | False / False |
| 月度数据 | `node_ocmnu2f1vr4` | `unit_3852623536924274690` | u_pivot | node_ocllzw8twf1 /  | x=0, y=89, w=20, h=37 | False / False |
| 季度数据 | `node_ocmnu2f1vr5` | `unit_3852642117420830723` | u_pivot | node_ocllzw8twf1 /  | x=0, y=126, w=20, h=53 | False / False |
| 年度数据 | `node_ocmnu2f1vr6` | `unit_3852643066481041410` | u_pivot | node_ocllzw8twf1 /  | x=0, y=179, w=20, h=37 | False / False |
| 月度同环比 | `node_ocmnucfuaj1` | `unit_3852731598764421121` | card | node_ocllzw8twf1 /  | x=10, y=10, w=10, h=20 | False / False |
| 期次同环比 | `node_ocmnucfuaj2` | `unit_3852748093415362561` | card | node_ocllzw8twf1 /  | x=0, y=10, w=10, h=20 | False / False |
| 分学部-日度同环比 | `node_ocmnve7fjm1` | `unit_3853811811253604352` | u_table | node_ocllzw8twf1 /  | x=0, y=30, w=20, h=28 | False / False |

## Pivot units

### 期次数据

- unit_id: `unit_3852450245030936577`
- model: `2576` / 年季月营收情况
- dimensions: 业务线 / `course_first_level_department_name`; 学部 / `course_second_level_department_name`; 期次 / `qici`; qici; xuebu; dazhuguan
- measures: 成交用户数 / `p_payer`; 退费用户数 / `r_payer`; 净用户数; 成交科目数 / `p_sub`; 退费科目数 / `r_sub`; 净科目数 / `净订单数`; 联报率; 营收金额 / `income`; 退费金额 / `refund`; 净营收 / `promit`; 净营收占比 / `promit`; 退费占比
- component: `node_ocmnu2f1vr2` / `PivotTable`

### 月度数据

- unit_id: `unit_3852623536924274690`
- model: `2576` / 年季月营收情况
- dimensions: 业务线 / `course_first_level_department_name`; 学部 / `course_second_level_department_name`; 月 / `max_month`; max_year; max_month; xuebu; dazhuguan
- measures: 成交用户数 / `p_payer`; 退费用户数 / `r_payer`; 净用户数; 成交科目数 / `p_sub`; 退费科目数 / `r_sub`; 净科目数 / `净订单数`; 联报率; 营收金额 / `income`; 退费金额 / `refund`; 净营收 / `promit`; 净营收占比 / `promit`; 退费占比
- component: `node_ocmnu2f1vr4` / `PivotTable`

### 季度数据

- unit_id: `unit_3852642117420830723`
- model: `2576` / 年季月营收情况
- dimensions: 业务线 / `course_first_level_department_name`; 学部 / `course_second_level_department_name`; 季 / `max_quarter`; max_year; max_quarter; xuebu; dazhuguan
- measures: 成交用户数 / `p_payer`; 退费用户数 / `r_payer`; 净用户数; 成交科目数 / `p_sub`; 退费科目数 / `r_sub`; 净科目数 / `净订单数`; 联报率; 营收金额 / `income`; 退费金额 / `refund`; 净营收 / `promit`; 净营收占比 / `promit`; 退费占比
- component: `node_ocmnu2f1vr5` / `PivotTable`

### 年度数据

- unit_id: `unit_3852643066481041410`
- model: `2576` / 年季月营收情况
- dimensions: 业务线 / `course_first_level_department_name`; 学部 / `course_second_level_department_name`; 年 / `max_year`; max_year; xuebu; dazhuguan
- measures: 成交用户数 / `p_payer`; 退费用户数 / `r_payer`; 净用户数; 成交科目数 / `p_sub`; 退费科目数 / `r_sub`; 净科目数 / `净订单数`; 联报率; 营收金额 / `income`; 退费金额 / `refund`; 净营收 / `promit`; 净营收占比 / `promit`; 退费占比
- component: `node_ocmnu2f1vr6` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 净用户数 | 净用户数<br>`customized_971057250162847744` | custom_measure / measure | sum(${p_payer}-${r_payer}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579513187461121"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579513187461123"}] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 净科目数 | 净订单数<br>`customized_971057250280288256` | custom_measure / measure | sum(${p_sub}-${r_sub}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579513187461120"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579513187461122"}] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 联报率 | 联报率<br>`customized_971057250515169280` | custom_measure / measure | ifnull(${净订单数}/${净用户数},0) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_971057250280288256"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_971057250162847744"}] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 退费占比 | 退费占比<br>`customized_971057250632609792` | custom_measure / measure | ifnull(sum(${refund})/sum(${income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579419051943940"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579419051943939"}] | 期次数据, 月度数据, 季度数据, 年度数据 |
| dazhuguan | dazhuguan<br>`396624` | dimension / filter |  |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| max_month | max_month<br>`395244` | dimension / filter |  |  | [] | 月度数据 |
| max_quarter | max_quarter<br>`395243` | dimension / filter |  |  | [] | 季度数据 |
| max_year | max_year<br>`395242` | dimension / filter |  |  | [] | 月度数据, 季度数据, 年度数据 |
| qici | qici<br>`395130` | dimension / filter |  |  | [] | 期次数据 |
| xuebu | xuebu<br>`396625` | dimension / filter |  |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 业务线 | course_first_level_department_name<br>`395127` | dimension / row_dimension |  |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 季 | max_quarter<br>`395243` | dimension / row_dimension |  |  | [] | 季度数据 |
| 学部 | course_second_level_department_name<br>`395128` | dimension / row_dimension |  |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 年 | max_year<br>`395242` | dimension / row_dimension |  |  | [] | 年度数据 |
| 月 | max_month<br>`395244` | dimension / row_dimension |  |  | [] | 月度数据 |
| 期次 | qici<br>`395130` | dimension / row_dimension |  |  | [] | 期次数据 |
| 净营收 | promit<br>`8579419051943941` | measure / measure | sum(8579419051943941) |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 净营收占比 | promit<br>`8579419051943941` | measure / measure | sum(8579419051943941) |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 成交用户数 | p_payer<br>`8579513187461121` | measure / measure | sum(8579513187461121) |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 成交科目数 | p_sub<br>`8579513187461120` | measure / measure | sum(8579513187461120) |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 营收金额 | income<br>`8579419051943939` | measure / measure | sum(8579419051943939) |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 退费用户数 | r_payer<br>`8579513187461123` | measure / measure | sum(8579513187461123) |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 退费科目数 | r_sub<br>`8579513187461122` | measure / measure | sum(8579513187461122) |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 退费金额 | refund<br>`8579419051943940` | measure / measure | sum(8579419051943940) |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |

## Filters

### Public filters

- 无公共筛选器快照。

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3852450245030936577` | `395130` | qici | in | ["detailFilter"] |
| `unit_3852450245030936577` | `396624` | dazhuguan | in | ["detailFilter"] |
| `unit_3852450245030936577` | `396625` | xuebu | in | ["detailFilter"] |
| `unit_3852623536924274690` | `395242` | max_year | in | ["detailFilter"] |
| `unit_3852623536924274690` | `395244` | max_month | in | ["detailFilter"] |
| `unit_3852623536924274690` | `396624` | dazhuguan | in | ["detailFilter"] |
| `unit_3852623536924274690` | `396625` | xuebu | in | ["detailFilter"] |
| `unit_3852642117420830723` | `395242` | max_year | in | ["detailFilter"] |
| `unit_3852642117420830723` | `395243` | max_quarter | in | ["detailFilter"] |
| `unit_3852642117420830723` | `396624` | dazhuguan | in | ["detailFilter"] |
| `unit_3852642117420830723` | `396625` | xuebu | in | ["detailFilter"] |
| `unit_3852643066481041410` | `395242` | max_year | in | ["detailFilter"] |
| `unit_3852643066481041410` | `396624` | dazhuguan | in | ["detailFilter"] |
| `unit_3852643066481041410` | `396625` | xuebu | in | ["detailFilter"] |

## Text units

- `unit_3852612515549360128`: 退费用户/科目数：<500元不计入 ；  净营收占比= 各学部净营收/净营收总计； 数据更新周期：每小时更新两小时前数据 ； 看板取数周期：按照自然月/季度/年
- `unit_3852612515549360128`: 退费用户/科目数：<500元不计入 ； 净营收占比= 各学部净营收/净营收总计；自然年(季度,月)：按最近一次交易时间计算；数据更新周期：每小时更新两小时前数据

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
