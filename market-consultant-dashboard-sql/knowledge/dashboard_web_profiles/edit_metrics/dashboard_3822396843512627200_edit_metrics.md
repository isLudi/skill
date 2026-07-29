# 市场顾问--评优看板 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3822396843512627200`
- dashboard_name: `市场顾问--评优看板`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:10:52`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `1ebd1d9f5bf043be745192c79c306cde134d1e7d59675cecb975f13a2e6e39b7`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3822396843512627200&htmlId=html_3983982204065402880`
- loaded_html_id: `html_3983982204065402880`
- config_html_id: `html_3983982238671138817`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3822396843512627200_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `4` / `85` / `55` / `13`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 4 | 4 | 157 | 55 | 8 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2421` | 评优看板 | 176241 | 1 |
| `2632` | 月度评优 | 176242 | 1 |
| `2643` | 季度评优 | 176243 | 1 |
| `2644` | 半年度评优 | 176244 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmn0g2qvh1` | `unit_3822397039671836672` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=5 | False / False |
| 期次看板 | `node_ocmn0g2qvh3` | `unit_3822404499349848065` | u_pivot | node_ocllzw8twf1 /  | x=0, y=46, w=20, h=31 | False / False |
| 文本框 | `node_ocmnh3hple1` | `unit_3839289622860058624` | u_text | node_ocllzw8twf1 /  | x=0, y=5, w=20, h=16 | False / False |
| 月度看板 | `node_ocmo4cbfvm1` | `unit_3862869318688346115` | u_pivot | node_ocllzw8twf1 /  | x=0, y=77, w=20, h=31 | False / False |
| 季度看板 | `node_ocmo78u4an1` | `unit_3865819236965679107` | u_pivot | node_ocllzw8twf1 /  | x=0, y=108, w=20, h=31 | False / False |
| 年度看板 | `node_ocmo78u4an2` | `unit_3865826671804780546` | u_pivot | node_ocllzw8twf1 /  | x=0, y=139, w=20, h=32 | False / False |
| 测试渠道 | `node_ocmpqljabh1` | `unit_3921968339834413056` | u_table | node_ocllzw8twf1 /  | x=0, y=21, w=20, h=25 | False / False |

## Pivot units

### 期次看板

- unit_id: `unit_3822404499349848065`
- model: `2421` / 评优看板
- dimensions: 顾问 / `employee_email_name`; 主管 / `xiaozu`; 经理 / `jingli`; 部门 / `dept`; 渠道 / `channel`; 年级 / `grade`; 期次 / `qici`; qici; employee_email_name
- measures: 期收款 / `inc`; 期退款 / `ref`; 期净收 / `pt`; 期目标 / `renchan`; 期完成度 / `roi`; 期完成度排名 / `rank_in_roi`; 完成度排名百分比 / `rank_position_roi`; 期退费率 / `refd`; 期退费率排名 / `rank_in_ref`; 退费率排名百分比 / `rank_position_ref`; 完成度得分; 退费率得分; 综合评分; 综合排名
- component: `node_ocmn0g2qvh3` / `PivotTable`

### 月度看板

- unit_id: `unit_3862869318688346115`
- model: `2632` / 月度评优
- dimensions: 顾问 / `employee_email_name`; 主管 / `xiaozu`; 经理 / `jingli`; 部门 / `dept`; 渠道 / `channel`; moth; employee_email_name
- measures: 月营收 / `inc`; 月退费 / `ref`; 月净收 / `pt`; 月目标 / `renchan`; 月完成度 / `roi`; 月完成度排名 / `rank_in_roi`; 月完成度排名百分比 / `rank_position_roi`; 月退费率 / `refd`; 月退费率排名 / `rank_in_ref`; 月退费率排名百分比 / `rank_position_ref`; 综合评分; 综合排名; 出勤率
- component: `node_ocmo4cbfvm1` / `PivotTable`

### 季度看板

- unit_id: `unit_3865819236965679107`
- model: `2643` / 季度评优
- dimensions: 顾问 / `employee_email_name`; 主管 / `xiaozu`; 经理 / `jingli`; 部门 / `dept`; 渠道 / `channel`; quarter; employee_email_name
- measures: 季营收 / `inc`; 季退费 / `ref`; 季净收 / `pt`; 季目标 / `renchan`; 季完成度 / `roi`; 季完成度排名 / `rank_in_roi`; 季完成度排名百分比 / `rank_position_roi`; 季退费率 / `refd`; 季退费率排名 / `rank_in_ref`; 季退费率排名百分比 / `rank_position_ref`; 综合评分; 综合排名; 出勤率
- component: `node_ocmo78u4an1` / `PivotTable`

### 年度看板

- unit_id: `unit_3865826671804780546`
- model: `2644` / 半年度评优
- dimensions: 顾问 / `employee_email_name`; 主管 / `xiaozu`; 经理 / `jingli`; 部门 / `dept`; 渠道 / `channel`; half_year; employee_email_name
- measures: 年营收 / `inc`; 年退费 / `ref`; 年净收 / `pt`; 年目标 / `renchan`; 年完成度 / `roi`; 年完成度排名 / `rank_in_roi`; 年完成度排名百分比 / `rank_position_roi`; 年退费率 / `refd`; 年退费率排名 / `rank_in_ref`; 年退费率排名百分比 / `rank_position_ref`; 综合评分; 综合排名; 出勤率; 是否参与测试渠道 / `is_join_test_channel`; 是否gmv达标 / `is_test_gmv_rate_over_80`
- component: `node_ocmo78u4an2` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 出勤率 | 出勤率<br>`customized_992836161599979521` | custom_measure / measure | sum(${consultant_period_count}) / sum(${total_period_count})<br> |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8890577443252224"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8890577443252225"}] | 月度看板 |
| 出勤率 | 出勤率<br>`customized_992836164645044225` | custom_measure / measure | sum(${consultant_period_count}) / sum(${total_period_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8890579525003264"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8890579525003265"}] | 季度看板 |
| 出勤率 | 出勤率<br>`customized_992836167690108929` | custom_measure / measure | sum(${consultant_period_count}) / sum(${total_period_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8886386762934272"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8886386762934273"}] | 年度看板 |
| 完成度得分 | 完成度得分<br>`customized_992836158680743937` | custom_measure / measure | 80*(1-sum(${rank_position_roi})) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8462044074960904"}] | 期次看板 |
| 综合排名 | 综合排名<br>`customized_992836159087591424` | custom_measure / measure | row_number() over (order by(${综合评分})desc) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836158991122433"}] | 期次看板 |
| 综合排名 | 综合排名<br>`customized_992836162128461825` | custom_measure / measure | row_number() over (order by(${综合评分})desc) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836162027798529"}] | 月度看板 |
| 综合排名 | 综合排名<br>`customized_992836165181915137` | custom_measure / measure | row_number() over (order by(${综合评分})desc) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836165072863233"}] | 季度看板 |
| 综合排名 | 综合排名<br>`customized_992836168210202625` | custom_measure / measure | row_number() over (order by(${综合评分})desc) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836168105345024"}] | 年度看板 |
| 综合评分 | 综合评分<br>`customized_992836158991122433` | custom_measure / measure | ${完成度得分}+${退费率得分} |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836158680743937"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836158877876224"}] | 期次看板 |
| 综合评分 | 综合评分<br>`customized_992836162027798529` | custom_measure / measure | ${完成度得分}+${退费率得分} |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836161709031425"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836161922940928"}] | 月度看板 |
| 综合评分 | 综合评分<br>`customized_992836165072863233` | custom_measure / measure | ${完成度得分}+${退费率得分} |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836164758290432"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836164963811329"}] | 季度看板 |
| 综合评分 | 综合评分<br>`customized_992836168105345024` | custom_measure / measure | ${完成度得分}+${退费率得分} |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836167799160833"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_992836168000487425"}] | 年度看板 |
| 退费率得分 | 退费率得分<br>`customized_992836158877876224` | custom_measure / measure | 10*(1-sum(${rank_position_ref})) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8462044074960905"}] | 期次看板 |
| employee_email_name | employee_email_name<br>`380315` | dimension / filter |  |  | [] | 期次看板 |
| employee_email_name | employee_email_name<br>`407356` | dimension / filter |  |  | [] | 月度看板 |
| employee_email_name | employee_email_name<br>`409849` | dimension / filter |  |  | [] | 季度看板 |
| employee_email_name | employee_email_name<br>`409861` | dimension / filter |  |  | [] | 年度看板 |
| half_year | half_year<br>`409860` | dimension / filter |  |  | [] | 年度看板 |
| moth | moth<br>`407355` | dimension / filter |  |  | [] | 月度看板 |
| qici | qici<br>`364758` | dimension / filter |  |  | [] | 期次看板 |
| quarter | quarter<br>`409848` | dimension / filter |  |  | [] | 季度看板 |
| 主管 | xiaozu<br>`364762` | dimension / row_dimension |  |  | [] | 期次看板 |
| 主管 | xiaozu<br>`407359` | dimension / row_dimension |  |  | [] | 月度看板 |
| 主管 | xiaozu<br>`409852` | dimension / row_dimension |  |  | [] | 季度看板 |
| 主管 | xiaozu<br>`409864` | dimension / row_dimension |  |  | [] | 年度看板 |
| 年级 | grade<br>`364765` | dimension / row_dimension |  |  | [] | 期次看板 |
| 期次 | qici<br>`364758` | dimension / row_dimension |  |  | [] | 期次看板 |
| 渠道 | channel<br>`364763` | dimension / row_dimension |  |  | [] | 期次看板 |
| 渠道 | channel<br>`407360` | dimension / row_dimension |  |  | [] | 月度看板 |
| 渠道 | channel<br>`409853` | dimension / row_dimension |  |  | [] | 季度看板 |
| 渠道 | channel<br>`409865` | dimension / row_dimension |  |  | [] | 年度看板 |
| 经理 | jingli<br>`364761` | dimension / row_dimension |  |  | [] | 期次看板 |
| 经理 | jingli<br>`407358` | dimension / row_dimension |  |  | [] | 月度看板 |
| 经理 | jingli<br>`409851` | dimension / row_dimension |  |  | [] | 季度看板 |
| 经理 | jingli<br>`409863` | dimension / row_dimension |  |  | [] | 年度看板 |
| 部门 | dept<br>`364760` | dimension / row_dimension |  |  | [] | 期次看板 |
| 部门 | dept<br>`407357` | dimension / row_dimension |  |  | [] | 月度看板 |
| 部门 | dept<br>`409850` | dimension / row_dimension |  |  | [] | 季度看板 |
| 部门 | dept<br>`409862` | dimension / row_dimension |  |  | [] | 年度看板 |
| 顾问 | employee_email_name<br>`380315` | dimension / row_dimension |  |  | [] | 期次看板 |
| 顾问 | employee_email_name<br>`407356` | dimension / row_dimension |  |  | [] | 月度看板 |
| 顾问 | employee_email_name<br>`409849` | dimension / row_dimension |  |  | [] | 季度看板 |
| 顾问 | employee_email_name<br>`409861` | dimension / row_dimension |  |  | [] | 年度看板 |
| 季净收 | pt<br>`8631604093937666` | measure / measure | sum(8631604093937666) |  | [] | 季度看板 |
| 季完成度 | roi<br>`8631604093937668` | measure / measure | sum(8631604093937668) |  | [] | 季度看板 |
| 季完成度排名 | rank_in_roi<br>`8631604093937670` | measure / measure | sum(8631604093937670) |  | [] | 季度看板 |
| 季完成度排名百分比 | rank_position_roi<br>`8631604093937672` | measure / measure | sum(8631604093937672) |  | [] | 季度看板 |
| 季目标 | renchan<br>`8631604093937664` | measure / measure | sum(8631604093937664) |  | [] | 季度看板 |
| 季营收 | inc<br>`8631604093937665` | measure / measure | sum(8631604093937665) |  | [] | 季度看板 |
| 季退费 | ref<br>`8631604093937667` | measure / measure | sum(8631604093937667) |  | [] | 季度看板 |
| 季退费率 | refd<br>`8631604093937669` | measure / measure | sum(8631604093937669) |  | [] | 季度看板 |
| 季退费率排名 | rank_in_ref<br>`8631604093937671` | measure / measure | sum(8631604093937671) |  | [] | 季度看板 |
| 季退费率排名百分比 | rank_position_ref<br>`8631604093937673` | measure / measure | sum(8631604093937673) |  | [] | 季度看板 |
| 完成度排名百分比 | rank_position_roi<br>`8462044074960904` | measure / measure | sum(8462044074960904) |  | [] | 期次看板 |
| 年净收 | pt<br>`8631641028585474` | measure / measure | sum(8631641028585474) |  | [] | 年度看板 |
| 年完成度 | roi<br>`8631641028585476` | measure / measure | sum(8631641028585476) |  | [] | 年度看板 |
| 年完成度排名 | rank_in_roi<br>`8631641028585478` | measure / measure | sum(8631641028585478) |  | [] | 年度看板 |
| 年完成度排名百分比 | rank_position_roi<br>`8631641028585480` | measure / measure | sum(8631641028585480) |  | [] | 年度看板 |
| 年目标 | renchan<br>`8631641028585472` | measure / measure | sum(8631641028585472) |  | [] | 年度看板 |
| 年营收 | inc<br>`8631641028585473` | measure / measure | sum(8631641028585473) |  | [] | 年度看板 |
| 年退费 | ref<br>`8631641028585475` | measure / measure | sum(8631641028585475) |  | [] | 年度看板 |
| 年退费率 | refd<br>`8631641028585477` | measure / measure | sum(8631641028585477) |  | [] | 年度看板 |
| 年退费率排名 | rank_in_ref<br>`8631641028585479` | measure / measure | sum(8631641028585479) |  | [] | 年度看板 |
| 年退费率排名百分比 | rank_position_ref<br>`8631641028585481` | measure / measure | sum(8631641028585481) |  | [] | 年度看板 |
| 是否gmv达标 | is_test_gmv_rate_over_80<br>`8886386762934276` | measure / measure | max(8886386762934276) |  | [] | 年度看板 |
| 是否参与测试渠道 | is_join_test_channel<br>`8886386762934275` | measure / measure | max(8886386762934275) |  | [] | 年度看板 |
| 月净收 | pt<br>`8620264811161602` | measure / measure | sum(8620264811161602) |  | [] | 月度看板 |
| 月完成度 | roi<br>`8620264811161604` | measure / measure | sum(8620264811161604) |  | [] | 月度看板 |
| 月完成度排名 | rank_in_roi<br>`8620264811161606` | measure / measure | sum(8620264811161606) |  | [] | 月度看板 |
| 月完成度排名百分比 | rank_position_roi<br>`8620264811161608` | measure / measure | sum(8620264811161608) |  | [] | 月度看板 |
| 月目标 | renchan<br>`8620264811161600` | measure / measure | sum(8620264811161600) |  | [] | 月度看板 |
| 月营收 | inc<br>`8620264811161601` | measure / measure | sum(8620264811161601) |  | [] | 月度看板 |
| 月退费 | ref<br>`8620264811161603` | measure / measure | sum(8620264811161603) |  | [] | 月度看板 |
| 月退费率 | refd<br>`8620264811161605` | measure / measure | sum(8620264811161605) |  | [] | 月度看板 |
| 月退费率排名 | rank_in_ref<br>`8620264811161607` | measure / measure | sum(8620264811161607) |  | [] | 月度看板 |
| 月退费率排名百分比 | rank_position_ref<br>`8620264811161609` | measure / measure | sum(8620264811161609) |  | [] | 月度看板 |
| 期净收 | pt<br>`8462044074960896` | measure / measure | sum(8462044074960896) |  | [] | 期次看板 |
| 期完成度 | roi<br>`8462044074960899` | measure / measure | sum(8462044074960899) |  | [] | 期次看板 |
| 期完成度排名 | rank_in_roi<br>`8462044074960902` | measure / measure | sum(8462044074960902) |  | [] | 期次看板 |
| 期收款 | inc<br>`8462044074960897` | measure / measure | sum(8462044074960897) |  | [] | 期次看板 |
| 期目标 | renchan<br>`8465690708633600` | measure / measure | sum(8465690708633600) |  | [] | 期次看板 |
| 期退款 | ref<br>`8462044074960898` | measure / measure | sum(8462044074960898) |  | [] | 期次看板 |
| 期退费率 | refd<br>`8462044074960900` | measure / measure | sum(8462044074960900) |  | [] | 期次看板 |
| 期退费率排名 | rank_in_ref<br>`8462044074960903` | measure / measure | sum(8462044074960903) |  | [] | 期次看板 |
| 退费率排名百分比 | rank_position_ref<br>`8462044074960905` | measure / measure | sum(8462044074960905) |  | [] | 期次看板 |

## Filters

### Public filters

- 无公共筛选器快照。

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3822404499349848065` | `364758` | qici | = | ["detailFilter"] |
| `unit_3822404499349848065` | `380315` | employee_email_name | in | ["detailFilter"] |
| `unit_3862869318688346115` | `407355` | moth | = | ["detailFilter"] |
| `unit_3862869318688346115` | `407356` | employee_email_name | in | ["detailFilter"] |
| `unit_3865819236965679107` | `409848` | quarter | = | ["detailFilter"] |
| `unit_3865819236965679107` | `409849` | employee_email_name | in | ["detailFilter"] |
| `unit_3865826671804780546` | `409860` | half_year | = | ["detailFilter"] |
| `unit_3865826671804780546` | `409861` | employee_email_name | in | ["detailFilter"] |

## Text units

- `unit_3839289622860058624`: 【月度看板】 <br>绩效期次前两位为评优归属月份：例如0501期为5月，0529期为5月，0605期为6月，与绩效月定义不同。 <br>【季度看板】与【年度看板】 <br>因人员名单差异，本看板数据仅作周期性数据参考，非晋升直接数据排名。 <br>【口径说明】<br>参与看板排名的人员有动态变化，而晋升名单范围与半年度/年度绩效考核等名单范围需要以集团公布节点的名单为准，届时具体排名将根据集团名单及集团公布需参考的数据周期、在相应节点重新计算。
- `unit_3839289622860058624`: 本期测试渠道：抖音私信(抖音私域)<br>【月度看板】 <br>绩效期次前两位为评优归属月份：例如0501期为5月，0529期为5月，0605期为6月，与绩效月定义不同。 <br>【季度看板】与【年度看板】 <br>因人员名单差异，本看板数据仅作周期性数据参考，非晋升直接数据排名。 <br>【口径说明】<br>参与看板排名的人员有动态变化，而晋升名单范围与半年度/年度绩效考核等名单范围需要以集团公布节点的名单为准，届时具体排名将根据集团名单及集团公布需参考的数据周期、在相应节点重新计算。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
