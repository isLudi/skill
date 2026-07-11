# 青橙-全年级营收看板 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3865509979877412864`
- dashboard_name: `青橙-全年级营收看板`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:16:10`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `f5aff6726a60ad1469f9d527e5c05db6fa46b9221a7f4d749a4ac93b334ba12b`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3865509979877412864&htmlId=html_3983987315960016897`
- loaded_html_id: `html_3983987315960016897`
- config_html_id: `html_3983987350342017024`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-project\dashboard_3865509979877412864_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `4` / `70` / `48` / `16`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 4 | 4 | 118 | 44 | 14 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2576` | 年季月营收情况 | 156049 | 4 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmnu2f1vr1` | `unit_3865509994020605953` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 期次数据 | `node_ocmnu2f1vr2` | `unit_3865509994020605954` | u_pivot | node_ocllzw8twf1 /  | x=0, y=58, w=20, h=31 | False / False |
| 文本框 | `node_ocmnu2f1vr3` | `unit_3865509994020605956` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=6 | False / False |
| 月度数据 | `node_ocmnu2f1vr4` | `unit_3865509994020605957` | u_pivot | node_ocllzw8twf1 /  | x=0, y=89, w=20, h=37 | False / False |
| 季度数据 | `node_ocmnu2f1vr5` | `unit_3865509994020605961` | u_pivot | node_ocllzw8twf1 /  | x=0, y=126, w=20, h=53 | False / False |
| 年度数据 | `node_ocmnu2f1vr6` | `unit_3865509994020605964` | u_pivot | node_ocllzw8twf1 /  | x=0, y=179, w=20, h=37 | False / False |
| 月度同环比 | `node_ocmnucfuaj1` | `unit_3865509994020605966` | card | node_ocllzw8twf1 /  | x=10, y=10, w=10, h=20 | False / False |
| 期次同环比 | `node_ocmnucfuaj2` | `unit_3865509994020605968` | card | node_ocllzw8twf1 /  | x=0, y=10, w=10, h=20 | False / False |
| 分学部-日度同环比 | `node_ocmnve7fjm1` | `unit_3865509994020605969` | u_table | node_ocllzw8twf1 /  | x=0, y=30, w=20, h=28 | False / False |

## Pivot units

### 期次数据

- unit_id: `unit_3865509994020605954`
- model: `2576` / 年季月营收情况
- dimensions: 年级 / `grade_list`; 期次 / `qici`; qici; xuebu; dazhuguan
- measures: 成交用户数 / `p_payer`; 退费用户数 / `r_payer`; 净用户数; 成交科目数 / `p_sub`; 退费科目数 / `r_sub`; 净科目数 / `净订单数`; 联报率; 营收金额 / `income`; 退费金额 / `refund`; 净营收 / `promit`; 净营收占比 / `promit`; 退费占比
- component: `node_ocmnu2f1vr2` / `PivotTable`

### 月度数据

- unit_id: `unit_3865509994020605957`
- model: `2576` / 年季月营收情况
- dimensions: 年级 / `grade_list`; 月 / `max_month`; max_year; max_month; xuebu; dazhuguan
- measures: 成交用户数 / `p_payer`; 退费用户数 / `r_payer`; 净用户数; 成交科目数 / `p_sub`; 退费科目数 / `r_sub`; 净科目数 / `净订单数`; 联报率; 营收金额 / `income`; 退费金额 / `refund`; 净营收 / `promit`; 净营收占比 / `promit`; 退费占比
- component: `node_ocmnu2f1vr4` / `PivotTable`

### 季度数据

- unit_id: `unit_3865509994020605961`
- model: `2576` / 年季月营收情况
- dimensions: 年级 / `grade_list`; 季 / `max_quarter`; max_year; max_quarter; xuebu; dazhuguan
- measures: 成交用户数 / `p_payer`; 退费用户数 / `r_payer`; 净用户数; 成交科目数 / `p_sub`; 退费科目数 / `r_sub`; 净科目数 / `净订单数`; 联报率; 营收金额 / `income`; 退费金额 / `refund`; 净营收 / `promit`; 净营收占比 / `promit`; 退费占比
- component: `node_ocmnu2f1vr5` / `PivotTable`

### 年度数据

- unit_id: `unit_3865509994020605964`
- model: `2576` / 年季月营收情况
- dimensions: 年级 / `grade_list`; 年 / `max_year`; max_year; xuebu; dazhuguan
- measures: 成交用户数 / `p_payer`; 退费用户数 / `r_payer`; 净用户数; 成交科目数 / `p_sub`; 退费科目数 / `r_sub`; 净科目数 / `净订单数`; 联报率; 营收金额 / `income`; 退费金额 / `refund`; 净营收 / `promit`; 净营收占比 / `promit`; 退费占比
- component: `node_ocmnu2f1vr6` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 净用户数 | 净用户数<br>`customized_971057786303950848` | custom_measure / measure | sum(${p_payer}-${r_payer}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579513187461121"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579513187461123"}] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 净科目数 | 净订单数<br>`customized_971057786425585665` | custom_measure / measure | sum(${p_sub}-${r_sub}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579513187461120"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579513187461122"}] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 联报率 | 联报率<br>`customized_971057786673049600` | custom_measure / measure | ifnull(${净订单数}/${净用户数},0) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_971057786425585665"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_971057786303950848"}] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 退费占比 | 退费占比<br>`customized_971057786794684417` | custom_measure / measure | ifnull(sum(${refund})/sum(${income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579419051943940"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8579419051943939"}] | 期次数据, 月度数据, 季度数据, 年度数据 |
| dazhuguan | dazhuguan<br>`396624` | dimension / filter |  |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| max_month | max_month<br>`395244` | dimension / filter |  |  | [] | 月度数据 |
| max_quarter | max_quarter<br>`395243` | dimension / filter |  |  | [] | 季度数据 |
| max_year | max_year<br>`395242` | dimension / filter |  |  | [] | 月度数据, 季度数据, 年度数据 |
| qici | qici<br>`395130` | dimension / filter |  |  | [] | 期次数据 |
| xuebu | xuebu<br>`396625` | dimension / filter |  |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
| 季 | max_quarter<br>`395243` | dimension / row_dimension |  |  | [] | 季度数据 |
| 年 | max_year<br>`395242` | dimension / row_dimension |  |  | [] | 年度数据 |
| 年级 | grade_list<br>`409310` | dimension / row_dimension |  |  | [] | 期次数据, 月度数据, 季度数据, 年度数据 |
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
| `unit_3865509994020605954` | `395130` | qici | in | ["detailFilter"] |
| `unit_3865509994020605954` | `396624` | dazhuguan | in | ["detailFilter"] |
| `unit_3865509994020605954` | `396625` | xuebu | in | ["detailFilter"] |
| `unit_3865509994020605957` | `395242` | max_year | in | ["detailFilter"] |
| `unit_3865509994020605957` | `395244` | max_month | in | ["detailFilter"] |
| `unit_3865509994020605957` | `396624` | dazhuguan | in | ["detailFilter"] |
| `unit_3865509994020605957` | `396625` | xuebu | in | ["detailFilter"] |
| `unit_3865509994020605961` | `395242` | max_year | in | ["detailFilter"] |
| `unit_3865509994020605961` | `395243` | max_quarter | in | ["detailFilter"] |
| `unit_3865509994020605961` | `396624` | dazhuguan | in | ["detailFilter"] |
| `unit_3865509994020605961` | `396625` | xuebu | in | ["detailFilter"] |
| `unit_3865509994020605964` | `395242` | max_year | in | ["detailFilter"] |
| `unit_3865509994020605964` | `396624` | dazhuguan | in | ["detailFilter"] |
| `unit_3865509994020605964` | `396625` | xuebu | in | ["detailFilter"] |

## Text units

- `unit_3865509994020605956`: 退费用户/科目数：<500元不计入 ；  净营收占比= 各学部净营收/净营收总计； 数据更新周期：每小时更新两小时前数据 ； 看板取数周期：按照自然月/季度/年

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
