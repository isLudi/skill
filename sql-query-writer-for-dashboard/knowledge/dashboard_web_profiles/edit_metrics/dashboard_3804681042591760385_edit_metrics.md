# 市场顾问-用户画像分析 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3804681042591760385`
- dashboard_name: `市场顾问-用户画像分析`
- captured_at: `2026-06-24 19:29:38`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3804681042591760385&htmlId=html_3959902371902693376`
- loaded_html_id: `html_3959902371902693376`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3804681042591760385_edit_metrics_profile.json`
- pivot_units: `7`
- configured_fields: `74`
- measures: `62`
- custom_formulas: `46`
- text_notes: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2683` | 前期流量画像-城市 | [traffic_profile.sql](../../../resources/raw_sql/traffic_profile.sql) | 1 |
| `2809` | 成单用户画像整体数据 | [market_channel_conversion_profile_overall_dataset_fixed.sql](../../../resources/raw_sql/market_channel_conversion_profile_overall_dataset_fixed.sql) | 1 |
| `2812` | 用户画像成单用户城市标签 | [data_center_market_2812_20260624.sql](../../../resources/raw_sql/data_center_market_2812_20260624.sql) | 1 |
| `2836` | 市场渠道用户成单分析 | [data_center_market_2836_20260624.sql](../../../resources/raw_sql/data_center_market_2836_20260624.sql) | 1 |
| `2885` | 市场渠道用户成单分析3 | [data_center_market_2885_20260624.sql](../../../resources/raw_sql/data_center_market_2885_20260624.sql) | 1 |
| `2883` | 市场渠道用户成单分析2 | [market_channel_conversion_profile_deep_stage_dataset.sql](../../../resources/raw_sql/market_channel_conversion_profile_deep_stage_dataset.sql) | 1 |
| `2890` | 多科用户退费 | [refund_rate_multidim.sql](../../../resources/raw_sql/refund_rate_multidim.sql) | 1 |

## Pivot units

### 流量用户画像

- unit_id: `unit_3874154854137556993`
- unit_type: `u_pivot`
- model: `2683` / 前期流量画像-城市
- dimensions: 渠道 / `channel_map`; 城市等级 / `city_level_name`
- measures: 等级占比 / `can_renew_ds_count_a`; 退前线索 / `IP_lead_count`; 退后线索 / `can_renew_ds_count_a`; 48h外呼; 5min; 深沟; 当期单效; 当期人头转化; 截面单效; 截面人头转化

### 多科用户成单表

- unit_id: `unit_3901691404520521729`
- unit_type: `u_pivot`
- model: `2809` / 成单用户画像整体数据
- dimensions: 期次 / `period_name`; 渠道 / `channel_map`
- measures: 线索量 / `lead_count`; 正价课人头 / `pay_user_head_count`; 正价课人次 / `pay_subject_person_count`; 净收款 / `net_income`; 1科人头 / `subject_1_user_count`; 1科人头占比; 1科GMV / `subject_1_gmv`; 1科GMV占比; 2-3科人头 / `subject_2_3_user_count`; 2-3科人头占比; 2-3科GMV / `subject_2_3_gmv`; 2-3科GMV占比; 3科以上人头 / `subject_3_plus_user_count`; 3科以上人头占比; 3科以上GMV / `subject_3_plus_gmv`; 3科以上GMV占比

### 透视表_副本

- unit_id: `unit_3901885938907897856`
- unit_type: `u_pivot`
- model: `2812` / 用户画像成单用户城市标签
- dimensions: 期次 / `period_name`; 城市等级 / `city_level_name`
- measures: 线索量 / `lead_count`; 线索量占比 / `线索量转化占比`; 净收款(截面) / `net_income_section`; 净收款占比; 人均收款; 人头转化率(截面); 单效(截面); 拓科率(截面)

### 1

- unit_id: `unit_3913632965000523776`
- unit_type: `u_pivot`
- model: `2836` / 市场渠道用户成单分析
- dimensions: 通时区间 / `bucket_name`
- measures: 对应区间人数; 人数占比; 转化人头数; 人头转化率; 订单转化率; 单效(截面)

### 1_副本

- unit_id: `unit_3913648004741677057`
- unit_type: `u_pivot`
- model: `2885` / 市场渠道用户成单分析3
- dimensions: 上课区间 / `bucket_name`
- measures: 对应区间人数; 人数占比; 转化人头数; 人头转化率; 订单转化率; 单效(截面)

### 1_副本_副本

- unit_id: `unit_3913653568806137857`
- unit_type: `u_pivot`
- model: `2883` / 市场渠道用户成单分析2
- dimensions: 沟通状态 / `bucket_name`
- measures: 对应区间人数; 人数占比; 转化人头数; 人头转化率; 订单转化率; 单效(截面)

### 多科用户退费占比

- unit_id: `unit_3935197018570850305`
- unit_type: `u_pivot`
- model: `2890` / 多科用户退费
- dimensions: 渠道 / `channel_map`; 经理 / `jingli`; 主管 / `zhuguan`
- measures: 退后线索 / `valid_lead_cnt`; GMV退费率(当期); GMV退费率(截面); 人头退费率(截面); 1科GMV退费率; 1科人头退费率; 2-3科GMV退费率; 2-3科人头退费率; 3科+GMV退费率; 3科+人头退费率

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 等级占比 | can_renew_ds_count_a<br>`8664136735156225` | measure | sum(8664136735156225) |  |  | 流量用户画像 |
| 退前线索 | IP_lead_count<br>`8664136735156224` | measure | sum(8664136735156224) |  |  | 流量用户画像 |
| 退后线索 | can_renew_ds_count_a<br>`8664136735156225` | measure | sum(8664136735156225) |  |  | 流量用户画像 |
| 48h外呼 | 48h外呼<br>`customized_985317045428367361` | custom_measure | ifnull(sum(${first_call_48h})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8664136735156227', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8664136735156225', 'orgParamType': 1, 'needBoundaryValue': False} | 流量用户画像 |
| 5min | 5min<br>`customized_985317045545807873` | custom_measure | ifnull(sum(${long_call_5})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8664136735156232', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8664136735156225', 'orgParamType': 1, 'needBoundaryValue': False} | 流量用户画像 |
| 深沟 | 深沟<br>`customized_985317046141399041` | custom_measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8664136735156229', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8664136735156225', 'orgParamType': 1, 'needBoundaryValue': False} | 流量用户画像 |
| 当期单效 | 当期单效<br>`customized_985317045780688897` | custom_measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8664136735156249', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8664136735156225', 'orgParamType': 1, 'needBoundaryValue': False} | 流量用户画像 |
| 当期人头转化 | 当期人头转化<br>`customized_985317045663248385` | custom_measure | ifnull(sum(${pay_users_on_period})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8664136735156237', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8664136735156225', 'orgParamType': 1, 'needBoundaryValue': False} | 流量用户画像 |
| 截面单效 | 截面单效<br>`customized_985317046019764224` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8664136735156247', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8664136735156225', 'orgParamType': 1, 'needBoundaryValue': False} | 流量用户画像 |
| 截面人头转化 | 截面人头转化<br>`customized_985317045902323712` | custom_measure | ifnull(sum(${pay_users})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8664136735156236', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8664136735156225', 'orgParamType': 1, 'needBoundaryValue': False} | 流量用户画像 |
| 线索量 | lead_count<br>`8771778132928512` | measure | sum(8771778132928512) |  |  | 多科用户成单表 |
| 正价课人头 | pay_user_head_count<br>`8771778132928513` | measure | sum(8771778132928513) |  |  | 多科用户成单表 |
| 正价课人次 | pay_subject_person_count<br>`8771778132928514` | measure | sum(8771778132928514) |  |  | 多科用户成单表 |
| 净收款 | net_income<br>`8771778132928515` | measure | sum(8771778132928515) |  |  | 多科用户成单表 |
| 1科人头 | subject_1_user_count<br>`8771778132928516` | measure | sum(8771778132928516) |  |  | 多科用户成单表 |
| 1科人头占比 | 1科人头占比<br>`customized_985317051812098049` | custom_measure | ifnull(sum(${subject_1_user_count}) / sum(${pay_user_head_count}), 0) |  | {'paramId': '8771778132928516', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8771778132928513', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户成单表 |
| 1科GMV | subject_1_gmv<br>`8771778132928517` | measure | sum(8771778132928517) |  |  | 多科用户成单表 |
| 1科GMV占比 | 1科GMV占比<br>`customized_985317051682074624` | custom_measure | ifnull(sum(${subject_1_gmv}) / sum(${net_income}), 0) |  | {'paramId': '8771778132928517', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8771778132928515', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户成单表 |
| 2-3科人头 | subject_2_3_user_count<br>`8851814501476352` | measure | sum(8851814501476352) |  |  | 多科用户成单表 |
| 2-3科人头占比 | 2-3科人头占比<br>`customized_985317052046979073` | custom_measure | ifnull(sum(${subject_2_3_user_count}) / sum(${pay_user_head_count}), 0) |  | {'paramId': '8851814501476352', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8771778132928513', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户成单表 |
| 2-3科GMV | subject_2_3_gmv<br>`8851814501476353` | measure | sum(8851814501476353) |  |  | 多科用户成单表 |
| 2-3科GMV占比 | 2-3科GMV占比<br>`customized_985317051929538561` | custom_measure | ifnull(sum(${subject_2_3_gmv}) / sum(${net_income}), 0) |  | {'paramId': '8851814501476353', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8771778132928515', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户成单表 |
| 3科以上人头 | subject_3_plus_user_count<br>`8851814501476354` | measure | sum(8851814501476354) |  |  | 多科用户成单表 |
| 3科以上人头占比 | 3科以上人头占比<br>`customized_985317052286054400` | custom_measure | ifnull(sum(${subject_3_plus_user_count}) / sum(${pay_user_head_count}), 0) |  | {'paramId': '8851814501476354', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8771778132928513', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户成单表 |
| 3科以上GMV | subject_3_plus_gmv<br>`8851814501476355` | measure | sum(8851814501476355) |  |  | 多科用户成单表 |
| 3科以上GMV占比 | 3科以上GMV占比<br>`customized_985317052168613888` | custom_measure | ifnull(sum(${subject_3_plus_gmv}) / sum(${net_income}), 0) |  | {'paramId': '8851814501476355', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8771778132928515', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户成单表 |
| 线索量 | lead_count<br>`8771948635645952` | measure | sum(8771948635645952) |  |  | 透视表_副本 |
| 线索量占比 | 线索量转化占比<br>`customized_985317055716995072` | custom_measure | ifnull(sum(${lead_count}) / sum(${total_lead_count_in_period}),0) |  | {'paramId': '8771948635645952', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8852007839754240', 'orgParamType': 1, 'needBoundaryValue': False} | 透视表_副本 |
| 净收款(截面) | net_income_section<br>`8771948635645954` | measure | sum(8771948635645954) |  |  | 透视表_副本 |
| 净收款占比 | 净收款占比<br>`customized_985317055335313409` | custom_measure | ifnull(sum(${net_income_section}) / sum(${total_net_income_in_period}),0) |  | {'paramId': '8771948635645954', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8852090697181184', 'orgParamType': 1, 'needBoundaryValue': False} | 透视表_副本 |
| 人均收款 | 人均收款<br>`customized_985317055071072256` | custom_measure | ifnull(sum(${net_income_section}) / sum(${pay_user_head_count}), 0) |  | {'paramId': '8771948635645954', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8852007839754243', 'orgParamType': 1, 'needBoundaryValue': False} | 透视表_副本 |
| 人头转化率(截面) | 人头转化率(截面)<br>`customized_985317055209484289` | custom_measure | ifnull(sum(${pay_user_head_count}) / sum(${lead_count}), 0) |  | {'paramId': '8852007839754243', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8771948635645952', 'orgParamType': 1, 'needBoundaryValue': False} | 透视表_副本 |
| 单效(截面) | 单效(截面)<br>`customized_985317055461142529` | custom_measure | ifnull(sum(${net_income_section}) / sum(${lead_count}), 0) |  | {'paramId': '8771948635645954', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8771948635645952', 'orgParamType': 1, 'needBoundaryValue': False} | 透视表_副本 |
| 拓科率(截面) | 拓科率(截面)<br>`customized_985317055591165952` | custom_measure | ifnull((sum(${pay_subject_person_count}) - sum(${pay_user_head_count}))/sum(${pay_user_head_count}), 0) |  | {'paramId': '8851950263101442', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8852007839754243', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8852007839754243', 'orgParamType': 1, 'needBoundaryValue': False} | 透视表_副本 |
| 对应区间人数 | 对应区间人数<br>`customized_985317058606870529` | custom_measure | sum(${bucket_user_cnt}) |  | {'paramId': '8891975891183616', 'orgParamType': 1, 'needBoundaryValue': False} | 1<br>1_副本<br>1_副本_副本 |
| 人数占比 | 人数占比<br>`customized_985317058371989505` | custom_measure | ifnull(sum(${bucket_user_cnt}) / sum(${total_lead_cnt}), 0) |  | {'paramId': '8891975891183616', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8892181476435969', 'orgParamType': 1, 'needBoundaryValue': False} | 1<br>1_副本<br>1_副本_副本 |
| 转化人头数 | 转化人头数<br>`customized_985317058854334464` | custom_measure | sum(${conversion_user_cnt}) |  | {'paramId': '8891975891183619', 'orgParamType': 1, 'needBoundaryValue': False} | 1<br>1_副本<br>1_副本_副本 |
| 人头转化率 | 人头转化率<br>`customized_985317058250354688` | custom_measure | ifnull(sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}), 0) |  | {'paramId': '8891975891183619', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8891975891183616', 'orgParamType': 1, 'needBoundaryValue': False} | 1 |
| 订单转化率 | 订单转化率<br>`customized_985317058728505344` | custom_measure | ifnull(sum(${order_cnt}) / sum(${bucket_user_cnt}), 0) |  | {'paramId': '8891975891183620', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8891975891183616', 'orgParamType': 1, 'needBoundaryValue': False} | 1 |
| 单效(截面) | 单效(截面)<br>`customized_985317058493624320` | custom_measure | ifnull(sum(${section_profit_amt}) / sum(${bucket_user_cnt}), 0) |  | {'paramId': '8891975891183622', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8891975891183616', 'orgParamType': 1, 'needBoundaryValue': False} | 1 |
| 人头转化率 | 人头转化率<br>`customized_985317065242259457` | custom_measure | sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}) |  | {'paramId': '8896261596014599', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8896261596014593', 'orgParamType': 1, 'needBoundaryValue': False} | 1_副本<br>1_副本_副本 |
| 订单转化率 | 订单转化率<br>`customized_985317065716215808` | custom_measure | sum(${order_cnt}) / sum(${bucket_user_cnt}) |  | {'paramId': '8896261596014600', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8896261596014593', 'orgParamType': 1, 'needBoundaryValue': False} | 1_副本<br>1_副本_副本 |
| 单效(截面) | 单效(截面)<br>`customized_985317065477140481` | custom_measure | sum(${section_profit_amt}) / sum(${bucket_user_cnt}) |  | {'paramId': '8896261596014602', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8896261596014593', 'orgParamType': 1, 'needBoundaryValue': False} | 1_副本<br>1_副本_副本 |
| 退后线索 | valid_lead_cnt<br>`8902653441370112` | measure | sum(8902653441370112) |  |  | 多科用户退费占比 |
| GMV退费率(当期) | GMV退费率(当期)<br>`customized_985317071957340160` | custom_measure | ifnull(SUM(${refund_current_gmv}) / SUM(${net_income_current_gmv}), 0) |  | {'paramId': '8902653441370114', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8902653441370115', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户退费占比 |
| GMV退费率(截面) | GMV退费率(截面)<br>`customized_985317072074780672` | custom_measure | ifnull(sum(${refund_section_gmv}) / sum(${net_income_section_gmv}), 0) |  | {'paramId': '8902653441370116', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8902653441370117', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户退费占比 |
| 人头退费率(截面) | 人头退费率(截面)<br>`customized_985317072196415489` | custom_measure | ifnull(sum(${refund_headcount_section}) / sum(${total_headcount}), 0) |  | {'paramId': '8902653441370118', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8902653441370113', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户退费占比 |
| 1科GMV退费率 | 1科GMV退费率<br>`customized_985317071231725569` | custom_measure | ifnull(sum(${refund_1_subject_gmv}) / sum(${net_income_1_subject_gmv}), 0) |  | {'paramId': '8902653441370119', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8902653441370120', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户退费占比 |
| 1科人头退费率 | 1科人头退费率<br>`customized_985317071361748992` | custom_measure | ifnull(sum(${refund_1_subject_headcount}) / sum(${total_headcount}), 0) |  | {'paramId': '8902653441370121', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8902653441370113', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户退费占比 |
| 2-3科GMV退费率 | 2-3科GMV退费率<br>`customized_985317071487578112` | custom_measure | ifnull(sum(${refund_2_3_subject_gmv}) / sum(${net_income_2_3_subject_gmv}), 0) |  | {'paramId': '8902653441370122', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8902653441370123', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户退费占比 |
| 2-3科人头退费率 | 2-3科人头退费率<br>`customized_985317071605018624` | custom_measure | ifnull(sum(${refund_2_3_subject_headcount}) / sum(${total_headcount}), 0) |  | {'paramId': '8902653441370124', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8902653441370113', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户退费占比 |
| 3科+GMV退费率 | 3科+GMV退费率<br>`customized_985317071718264833` | custom_measure | ifnull(sum(${refund_3plus_subject_gmv}) / sum(${net_income_3plus_subject_gmv}),0) |  | {'paramId': '8902653441370125', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8902653441370126', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户退费占比 |
| 3科+人头退费率 | 3科+人头退费率<br>`customized_985317071835705345` | custom_measure | ifnull(sum(${refund_3plus_subject_headcount}) / sum(${total_headcount}), 0) |  | {'paramId': '8902653441370127', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8902653441370113', 'orgParamType': 1, 'needBoundaryValue': False} | 多科用户退费占比 |
