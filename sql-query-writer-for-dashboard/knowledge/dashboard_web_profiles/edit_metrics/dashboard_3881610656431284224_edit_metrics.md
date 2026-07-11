# 昆仑山战役-暑期激励数据看板 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3881610656431284224`
- dashboard_name: `昆仑山战役-暑期激励数据看板`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:13:08`
- menu_status: `incomplete`
- completeness: `incomplete`
- binding_validation: `incomplete`
- profile_sha256: `915b77a7083f808d895a87fd91bb34579e19fd9c3a2d479f42b19294594e792d`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3881610656431284224`
- loaded_html_id: ``
- config_html_id: `html_3983984574081867776`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3881610656431284224_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `6` / `56` / `24` / `0`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 6 | 4 | 6 | 92 | 24 | 18 | 4 |

### Incomplete diagnostics

- `PIVOT_SELECTED_FIELD_DETAIL_UNRESOLVED` unit=`unit_3913379858514313219` field=`8817002150389791`: Configured pivot field did not resolve to a model field detail.
- `PIVOT_SELECTED_FIELD_DATASET_REFERENCE_DANGLING` unit=`unit_3913379858514313219` field=`8817002150389791`: Configured pivot field is absent from its referenced dataset field tree.
- `PIVOT_SELECTED_FIELD_DETAIL_UNRESOLVED` unit=`unit_3913387360440238081` field=`8817002150389791`: Configured pivot field did not resolve to a model field detail.
- `PIVOT_SELECTED_FIELD_DATASET_REFERENCE_DANGLING` unit=`unit_3913387360440238081` field=`8817002150389791`: Configured pivot field is absent from its referenced dataset field tree.

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2727` | 暑期激励看板 | 163491 | 2 |
| `2751` | 暑期激励v2 | 163492 | 2 |
| `2842` | 暑期激励v3-月份 | 163493 | 2 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmomteg9w1` | `unit_3881611004233035777` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=4 | False / False |
| 文本框 | `node_ocmomteg9w2` | `unit_3881612212014751744` | u_text | node_ocllzw8twf1 /  | x=0, y=4, w=20, h=8 | False / False |
| 天级数据-西安 | `node_ocmovgwdv92` | `unit_3890409769709219842` | u_pivot | node_ocllzw8twf1 /  | x=0, y=12, w=10, h=40 | False / False |
| 文本框_副本 | `node_ocmovgwhmv1` | `unit_3890428705223966720` | u_text | node_ocllzw8twf1 /  | x=0, y=52, w=20, h=15 | False / False |
| 天级数据-郑州 | `node_ocmovjoe581` | `unit_3890469963619188736` | u_pivot | node_ocllzw8twf1 /  | x=10, y=12, w=10, h=40 | False / False |
| 期次数据-西安 | `node_ocmpi40frj17` | `unit_3913361199684935681` | u_pivot | node_ocllzw8twf1 /  | x=0, y=67, w=10, h=35 | False / False |
| 期次数据-郑州 | `node_ocmpi40frj18` | `unit_3913378722861166595` | u_pivot | node_ocllzw8twf1 /  | x=10, y=67, w=10, h=35 | False / False |
| 月度数据-西安 | `node_ocmpi40frj19` | `unit_3913379858514313219` | u_pivot | node_ocllzw8twf1 /  | x=0, y=102, w=10, h=42 | False / False |
| 月度数据-郑州 | `node_ocmpi40frj1a` | `unit_3913387360440238081` | u_pivot | node_ocllzw8twf1 /  | x=10, y=102, w=10, h=42 | False / False |

## Pivot units

### 天级数据-西安

- unit_id: `unit_3890409769709219842`
- model: `2727` / 暑期激励看板
- dimensions: 顾问 / `name`; 主管 / `xiaozu`; 经理 / `jingli`; trade_date; dept; jingli
- measures: 排名 / `day_dept_period_rank_no`; 与上一名差值 / `day_dept_period_need_pmit_to_previous`
- component: `node_ocmovgwdv92` / `PivotTable`

### 天级数据-郑州

- unit_id: `unit_3890469963619188736`
- model: `2727` / 暑期激励看板
- dimensions: 顾问 / `name`; 主管 / `xiaozu`; 经理 / `jingli`; trade_date; dept; jingli
- measures: 排名 / `day_dept_period_rank_no`; 与上一名差值 / `day_dept_period_need_pmit_to_previous`
- component: `node_ocmovjoe581` / `PivotTable`

### 期次数据-西安

- unit_id: `unit_3913361199684935681`
- model: `2751` / 暑期激励v2
- dimensions: 顾问 / `name`; 主管 / `zhuguan`; dept; jingli; qici
- measures: 收款目标 / `receive_target`; 目标完成度 / `target_completion_rate`; 排名 / `target_completion_period_dept_rank_no`; 差值 / `target_completion_gap_to_previous`; 拓课率 / `tuoke_rate`
- component: `node_ocmpi40frj17` / `PivotTable`

### 月度数据-西安

- unit_id: `unit_3913379858514313219`
- model: `2842` / 暑期激励v3-月份
- dimensions: 顾问 / `name`; 主管 / `xiaozu`; dept; natural_month; jingli
- measures: 收款目标 / `receive_target`; 目标完成度 / `target_completion_rate`; 排名 / `target_completion_period_dept_rank_no`; 差值; 拓课率 / `tuoke_rate`
- component: `node_ocmpi40frj19` / `PivotTable`

### 月度数据-郑州

- unit_id: `unit_3913387360440238081`
- model: `2842` / 暑期激励v3-月份
- dimensions: 顾问 / `name`; 主管 / `xiaozu`; dept; natural_month; jingli
- measures: 收款目标 / `receive_target`; 目标完成度 / `target_completion_rate`; 排名 / `target_completion_period_dept_rank_no`; 差值; 拓课率 / `tuoke_rate`
- component: `node_ocmpi40frj1a` / `PivotTable`

### 期次数据-郑州

- unit_id: `unit_3913378722861166595`
- model: `2751` / 暑期激励v2
- dimensions: 顾问 / `name`; 主管 / `zhuguan`; dept; jingli; qici
- measures: 收款目标 / `receive_target`; 目标完成度 / `target_completion_rate`; 排名 / `target_completion_period_dept_rank_no`; 差值 / `target_completion_gap_to_previous`; 拓课率 / `tuoke_rate`
- component: `node_ocmpi40frj18` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| dept | dept<br>`427433` | dimension / filter |  |  | [] | 天级数据-西安, 天级数据-郑州 |
| dept | dept<br>`435530` | dimension / filter |  |  | [] | 期次数据-西安, 期次数据-郑州 |
| dept | dept<br>`462993` | dimension / filter |  |  | [] | 月度数据-西安, 月度数据-郑州 |
| jingli | jingli<br>`427432` | dimension / filter |  |  | [] | 天级数据-西安, 天级数据-郑州 |
| jingli | jingli<br>`435533` | dimension / filter |  |  | [] | 期次数据-西安, 期次数据-郑州 |
| jingli | jingli<br>`462996` | dimension / filter |  |  | [] | 月度数据-西安, 月度数据-郑州 |
| natural_month | natural_month<br>`462990` | dimension / filter |  |  | [] | 月度数据-西安, 月度数据-郑州 |
| qici | qici<br>`463215` | dimension / filter |  |  | [] | 期次数据-西安, 期次数据-郑州 |
| trade_date | trade_date<br>`427435` | dimension / filter |  |  | [] | 天级数据-西安, 天级数据-郑州 |
| 主管 | xiaozu<br>`427431` | dimension / row_dimension |  |  | [] | 天级数据-西安, 天级数据-郑州 |
| 主管 | xiaozu<br>`462995` | dimension / row_dimension |  |  | [] | 月度数据-西安, 月度数据-郑州 |
| 主管 | zhuguan<br>`463253` | dimension / row_dimension |  |  | [] | 期次数据-西安, 期次数据-郑州 |
| 经理 | jingli<br>`427432` | dimension / row_dimension |  |  | [] | 天级数据-西安, 天级数据-郑州 |
| 顾问 | name<br>`427429` | dimension / row_dimension |  |  | [] | 天级数据-西安, 天级数据-郑州 |
| 顾问 | name<br>`435531` | dimension / row_dimension |  |  | [] | 期次数据-西安, 期次数据-郑州 |
| 顾问 | name<br>`462994` | dimension / row_dimension |  |  | [] | 月度数据-西安, 月度数据-郑州 |
| 与上一名差值 | day_dept_period_need_pmit_to_previous<br>`8727943220193283` | measure / measure | sum(8727943220193283) |  | [] | 天级数据-西安, 天级数据-郑州 |
| 差值 | 差值<br>`8817002150389791` | measure / measure | sum(8817002150389791) |  | [] | 月度数据-西安, 月度数据-郑州 |
| 差值 | target_completion_gap_to_previous<br>`8817105288980503` | measure / measure | sum(8817105288980503) |  | [] | 期次数据-西安, 期次数据-郑州 |
| 拓课率 | tuoke_rate<br>`8817002150389792` | measure / measure | sum(8817002150389792) |  | [] | 月度数据-西安, 月度数据-郑州 |
| 拓课率 | tuoke_rate<br>`8817105288980504` | measure / measure | sum(8817105288980504) |  | [] | 期次数据-西安, 期次数据-郑州 |
| 排名 | day_dept_period_rank_no<br>`8727943220193282` | measure / measure | sum(8727943220193282) |  | [] | 天级数据-西安, 天级数据-郑州 |
| 排名 | target_completion_period_dept_rank_no<br>`8817002150389790` | measure / measure | sum(8817002150389790) |  | [] | 月度数据-西安, 月度数据-郑州 |
| 排名 | target_completion_period_dept_rank_no<br>`8817105288980502` | measure / measure | sum(8817105288980502) |  | [] | 期次数据-西安, 期次数据-郑州 |
| 收款目标 | receive_target<br>`8817002150389772` | measure / measure | sum(8817002150389772) |  | [] | 月度数据-西安, 月度数据-郑州 |
| 收款目标 | receive_target<br>`8817105288980484` | measure / measure | sum(8817105288980484) |  | [] | 期次数据-西安, 期次数据-郑州 |
| 目标完成度 | target_completion_rate<br>`8817002150389789` | measure / measure | sum(8817002150389789) |  | [] | 月度数据-西安, 月度数据-郑州 |
| 目标完成度 | target_completion_rate<br>`8817105288980501` | measure / measure | sum(8817105288980501) |  | [] | 期次数据-西安, 期次数据-郑州 |

## Filters

### Public filters

- 无公共筛选器快照。

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3890409769709219842` | `427432` | jingli | in | ["detailFilter"] |
| `unit_3890409769709219842` | `427433` | dept | in | ["detailFilter"] |
| `unit_3890409769709219842` | `427435` | trade_date |  | ["detailFilter"] |
| `unit_3890469963619188736` | `427432` | jingli | in | ["detailFilter"] |
| `unit_3890469963619188736` | `427433` | dept | in | ["detailFilter"] |
| `unit_3890469963619188736` | `427435` | trade_date |  | ["detailFilter"] |
| `unit_3913361199684935681` | `435530` | dept | in | ["detailFilter"] |
| `unit_3913361199684935681` | `435533` | jingli | in | ["detailFilter"] |
| `unit_3913361199684935681` | `463215` | qici | = | ["detailFilter"] |
| `unit_3913378722861166595` | `435530` | dept | in | ["detailFilter"] |
| `unit_3913378722861166595` | `435533` | jingli | in | ["detailFilter"] |
| `unit_3913378722861166595` | `463215` | qici | = | ["detailFilter"] |
| `unit_3913379858514313219` | `462990` | natural_month | in | ["detailFilter"] |
| `unit_3913379858514313219` | `462993` | dept | in | ["detailFilter"] |
| `unit_3913379858514313219` | `462996` | jingli | in | ["detailFilter"] |
| `unit_3913387360440238081` | `462990` | natural_month | in | ["detailFilter"] |
| `unit_3913387360440238081` | `462993` | dept | in | ["detailFilter"] |
| `unit_3913387360440238081` | `462996` | jingli | in | ["detailFilter"] |

## Text units

- `unit_3881612212014751744`: 天级指标解读(数据更新截止两小时前)：<br>1. 净收款包含当期退费负值，退费为全量退费（含开课2节后退费）     2. 特殊渠道金额会有对应的系数折算，以下排名为参考数据 (主动咨询和亚飞99，测算主动咨询系数0.5，亚飞99系数0.7)
- `unit_3881612212014751744`: 指标解读(数据更新截止两小时前)：<br>1. 净收款包含当期退费负值，退费为全量退费（含开课2节后退费）     2. 特殊渠道金额会有对应的系数折算，以下排名为参考数据 (主动咨询和亚飞99，测算主动咨询系数0.5，亚飞99系数0.7)
- `unit_3890428705223966720`: 期次指标解读：<br>1.净GMV：包含当期退费负值，退费为全量退费（含开课2节后退费）  <br>2.目标完成度：部分渠道的单效目标无法拆开，以下排名为参考数据  <br>3.拓课率：数据一致的情况下，参考目标完成度、净GMV排名情况       <br>4. 参与评比条件：带班量≥20且完成度≥100%  <br>5.特殊渠道金额会有对应的系数折算，以下排名为参考数据（主动咨询和亚飞99，测算主动咨询系数0.5，亚飞99系数0.7）

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
