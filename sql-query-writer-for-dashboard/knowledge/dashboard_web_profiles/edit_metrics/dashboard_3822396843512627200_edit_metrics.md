# 市场顾问--评优看板 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3822396843512627200`
- dashboard_name: `市场顾问--评优看板`
- captured_at: `2026-06-24 19:29:56`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3822396843512627200&htmlId=html_3959902637995909120`
- loaded_html_id: `html_3959902637995909120`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3822396843512627200_edit_metrics_profile.json`
- pivot_units: `4`
- configured_fields: `85`
- measures: `55`
- custom_formulas: `13`
- text_notes: `2`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2421` | 评优看板 | [consultant_sales_ranking_evaluation_period_clean.sql](../../../resources/raw_sql/consultant_sales_ranking_evaluation_period_clean.sql) | 1 |
| `2632` | 月度评优 | [consultant_sales_ranking_evaluation_month_clean.sql](../../../resources/raw_sql/consultant_sales_ranking_evaluation_month_clean.sql) | 1 |
| `2643` | 季度评优 | [consultant_sales_ranking_evaluation_quarter_clean.sql](../../../resources/raw_sql/consultant_sales_ranking_evaluation_quarter_clean.sql) | 1 |
| `2644` | 半年度评优 | [consultant_sales_ranking_evaluation_year_clean.sql](../../../resources/raw_sql/consultant_sales_ranking_evaluation_year_clean.sql) | 1 |

## Text units

- `unit_3839289622860058624`: 【月度看板】 <br>绩效期次前两位为评优归属月份：例如0501期为5月，0529期为5月，0605期为6月，与绩效月定义不同。 <br>【季度看板】与【年度看板】 <br>因人员名单差异，本看板数据仅作周期性数据参考，非晋升直接数据排名。 <br>【口径说明】<br>参与看板排名的人员有动态变化，而晋升名单范围与半年度/年度绩效考核等名单范围需要以集团公布节点的名单为准，届时具体排名将根据集团名单及集团公布需参考的数据周期、在相应节点重新计算。
- `unit_3839289622860058624`: 本期测试渠道：抖音私信(抖音私域)<br>【月度看板】 <br>绩效期次前两位为评优归属月份：例如0501期为5月，0529期为5月，0605期为6月，与绩效月定义不同。 <br>【季度看板】与【年度看板】 <br>因人员名单差异，本看板数据仅作周期性数据参考，非晋升直接数据排名。 <br>【口径说明】<br>参与看板排名的人员有动态变化，而晋升名单范围与半年度/年度绩效考核等名单范围需要以集团公布节点的名单为准，届时具体排名将根据集团名单及集团公布需参考的数据周期、在相应节点重新计算。

## Pivot units

### 期次看板

- unit_id: `unit_3822404499349848065`
- unit_type: `u_pivot`
- model: `2421` / 评优看板
- dimensions: 顾问 / `employee_email_name`; 主管 / `xiaozu`; 经理 / `jingli`; 部门 / `dept`; 渠道 / `channel`; 年级 / `grade`; 期次 / `qici`; qici; employee_email_name
- measures: 期收款 / `inc`; 期退款 / `ref`; 期净收 / `pt`; 期目标 / `renchan`; 期完成度 / `roi`; 期完成度排名 / `rank_in_roi`; 完成度排名百分比 / `rank_position_roi`; 期退费率 / `refd`; 期退费率排名 / `rank_in_ref`; 退费率排名百分比 / `rank_position_ref`; 完成度得分; 退费率得分; 综合评分; 综合排名

### 月度看板

- unit_id: `unit_3862869318688346115`
- unit_type: `u_pivot`
- model: `2632` / 月度评优
- dimensions: 顾问 / `employee_email_name`; 主管 / `xiaozu`; 经理 / `jingli`; 部门 / `dept`; 渠道 / `channel`; moth; employee_email_name
- measures: 月营收 / `inc`; 月退费 / `ref`; 月净收 / `pt`; 月目标 / `renchan`; 月完成度 / `roi`; 月完成度排名 / `rank_in_roi`; 月完成度排名百分比 / `rank_position_roi`; 月退费率 / `refd`; 月退费率排名 / `rank_in_ref`; 月退费率排名百分比 / `rank_position_ref`; 综合评分; 综合排名; 出勤率

### 季度看板

- unit_id: `unit_3865819236965679107`
- unit_type: `u_pivot`
- model: `2643` / 季度评优
- dimensions: 顾问 / `employee_email_name`; 主管 / `xiaozu`; 经理 / `jingli`; 部门 / `dept`; 渠道 / `channel`; quarter; employee_email_name
- measures: 季营收 / `inc`; 季退费 / `ref`; 季净收 / `pt`; 季目标 / `renchan`; 季完成度 / `roi`; 季完成度排名 / `rank_in_roi`; 季完成度排名百分比 / `rank_position_roi`; 季退费率 / `refd`; 季退费率排名 / `rank_in_ref`; 季退费率排名百分比 / `rank_position_ref`; 综合评分; 综合排名; 出勤率

### 年度看板

- unit_id: `unit_3865826671804780546`
- unit_type: `u_pivot`
- model: `2644` / 半年度评优
- dimensions: 顾问 / `employee_email_name`; 主管 / `xiaozu`; 经理 / `jingli`; 部门 / `dept`; 渠道 / `channel`; half_year; employee_email_name
- measures: 年营收 / `inc`; 年退费 / `ref`; 年净收 / `pt`; 年目标 / `renchan`; 年完成度 / `roi`; 年完成度排名 / `rank_in_roi`; 年完成度排名百分比 / `rank_position_roi`; 年退费率 / `refd`; 年退费率排名 / `rank_in_ref`; 年退费率排名百分比 / `rank_position_ref`; 综合评分; 综合排名; 出勤率; 是否参与测试渠道 / `is_join_test_channel`; 是否gmv达标 / `is_test_gmv_rate_over_80`

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 期收款 | inc<br>`8462044074960897` | measure | sum(8462044074960897) |  |  | 期次看板 |
| 期退款 | ref<br>`8462044074960898` | measure | sum(8462044074960898) |  |  | 期次看板 |
| 期净收 | pt<br>`8462044074960896` | measure | sum(8462044074960896) |  |  | 期次看板 |
| 期目标 | renchan<br>`8465690708633600` | measure | sum(8465690708633600) |  |  | 期次看板 |
| 期完成度 | roi<br>`8462044074960899` | measure | sum(8462044074960899) |  |  | 期次看板 |
| 期完成度排名 | rank_in_roi<br>`8462044074960902` | measure | sum(8462044074960902) |  |  | 期次看板 |
| 完成度排名百分比 | rank_position_roi<br>`8462044074960904` | measure | sum(8462044074960904) |  |  | 期次看板 |
| 期退费率 | refd<br>`8462044074960900` | measure | sum(8462044074960900) |  |  | 期次看板 |
| 期退费率排名 | rank_in_ref<br>`8462044074960903` | measure | sum(8462044074960903) |  |  | 期次看板 |
| 退费率排名百分比 | rank_position_ref<br>`8462044074960905` | measure | sum(8462044074960905) |  |  | 期次看板 |
| 完成度得分 | 完成度得分<br>`customized_983026979952394240` | custom_measure | 80*(1-sum(${rank_position_roi})) |  | {'paramId': '8462044074960904', 'orgParamType': 1, 'needBoundaryValue': False} | 期次看板 |
| 退费率得分 | 退费率得分<br>`customized_983026980187275264` | custom_measure | 10*(1-sum(${rank_position_ref})) |  | {'paramId': '8462044074960905', 'orgParamType': 1, 'needBoundaryValue': False} | 期次看板 |
| 综合评分 | 综合评分<br>`customized_983026980300521473` | custom_measure | ${完成度得分}+${退费率得分} |  | {'paramId': 'customized_983026979952394240', 'orgParamType': 4, 'needBoundaryValue': False}<br>{'paramId': 'customized_983026980187275264', 'orgParamType': 4, 'needBoundaryValue': False} | 期次看板<br>月度看板<br>季度看板<br>年度看板 |
| 综合排名 | 综合排名<br>`customized_983026980413767680` | custom_measure | row_number() over (order by(${综合评分})desc) |  | {'paramId': 'customized_983026980300521473', 'orgParamType': 4, 'needBoundaryValue': False} | 期次看板<br>月度看板<br>季度看板<br>年度看板 |
| 月营收 | inc<br>`8620264811161601` | measure | sum(8620264811161601) |  |  | 月度看板 |
| 月退费 | ref<br>`8620264811161603` | measure | sum(8620264811161603) |  |  | 月度看板 |
| 月净收 | pt<br>`8620264811161602` | measure | sum(8620264811161602) |  |  | 月度看板 |
| 月目标 | renchan<br>`8620264811161600` | measure | sum(8620264811161600) |  |  | 月度看板 |
| 月完成度 | roi<br>`8620264811161604` | measure | sum(8620264811161604) |  |  | 月度看板 |
| 月完成度排名 | rank_in_roi<br>`8620264811161606` | measure | sum(8620264811161606) |  |  | 月度看板 |
| 月完成度排名百分比 | rank_position_roi<br>`8620264811161608` | measure | sum(8620264811161608) |  |  | 月度看板 |
| 月退费率 | refd<br>`8620264811161605` | measure | sum(8620264811161605) |  |  | 月度看板 |
| 月退费率排名 | rank_in_ref<br>`8620264811161607` | measure | sum(8620264811161607) |  |  | 月度看板 |
| 月退费率排名百分比 | rank_position_ref<br>`8620264811161609` | measure | sum(8620264811161609) |  |  | 月度看板 |
| 出勤率 | 出勤率<br>`customized_983026983207174144` | custom_measure | sum(${consultant_period_count}) / sum(${total_period_count})<br> |  | {'paramId': '8890577443252224', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8890577443252225', 'orgParamType': 1, 'needBoundaryValue': False} | 月度看板 |
| 季营收 | inc<br>`8631604093937665` | measure | sum(8631604093937665) |  |  | 季度看板 |
| 季退费 | ref<br>`8631604093937667` | measure | sum(8631604093937667) |  |  | 季度看板 |
| 季净收 | pt<br>`8631604093937666` | measure | sum(8631604093937666) |  |  | 季度看板 |
| 季目标 | renchan<br>`8631604093937664` | measure | sum(8631604093937664) |  |  | 季度看板 |
| 季完成度 | roi<br>`8631604093937668` | measure | sum(8631604093937668) |  |  | 季度看板 |
| 季完成度排名 | rank_in_roi<br>`8631604093937670` | measure | sum(8631604093937670) |  |  | 季度看板 |
| 季完成度排名百分比 | rank_position_roi<br>`8631604093937672` | measure | sum(8631604093937672) |  |  | 季度看板 |
| 季退费率 | refd<br>`8631604093937669` | measure | sum(8631604093937669) |  |  | 季度看板 |
| 季退费率排名 | rank_in_ref<br>`8631604093937671` | measure | sum(8631604093937671) |  |  | 季度看板 |
| 季退费率排名百分比 | rank_position_ref<br>`8631604093937673` | measure | sum(8631604093937673) |  |  | 季度看板 |
| 出勤率 | 出勤率<br>`customized_983026986365485057` | custom_measure | sum(${consultant_period_count}) / sum(${total_period_count}) |  | {'paramId': '8890579525003264', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8890579525003265', 'orgParamType': 1, 'needBoundaryValue': False} | 季度看板<br>年度看板 |
| 年营收 | inc<br>`8631641028585473` | measure | sum(8631641028585473) |  |  | 年度看板 |
| 年退费 | ref<br>`8631641028585475` | measure | sum(8631641028585475) |  |  | 年度看板 |
| 年净收 | pt<br>`8631641028585474` | measure | sum(8631641028585474) |  |  | 年度看板 |
| 年目标 | renchan<br>`8631641028585472` | measure | sum(8631641028585472) |  |  | 年度看板 |
| 年完成度 | roi<br>`8631641028585476` | measure | sum(8631641028585476) |  |  | 年度看板 |
| 年完成度排名 | rank_in_roi<br>`8631641028585478` | measure | sum(8631641028585478) |  |  | 年度看板 |
| 年完成度排名百分比 | rank_position_roi<br>`8631641028585480` | measure | sum(8631641028585480) |  |  | 年度看板 |
| 年退费率 | refd<br>`8631641028585477` | measure | sum(8631641028585477) |  |  | 年度看板 |
| 年退费率排名 | rank_in_ref<br>`8631641028585479` | measure | sum(8631641028585479) |  |  | 年度看板 |
| 年退费率排名百分比 | rank_position_ref<br>`8631641028585481` | measure | sum(8631641028585481) |  |  | 年度看板 |
| 是否参与测试渠道 | is_join_test_channel<br>`8886386762934275` | measure | max(8886386762934275) |  |  | 年度看板 |
| 是否gmv达标 | is_test_gmv_rate_over_80<br>`8886386762934276` | measure | max(8886386762934276) |  |  | 年度看板 |
