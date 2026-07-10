# 市场顾问-用户画像分析 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.
> This file is regenerated from the latest 2026-07-05 profile and replaces the older 2026-06-24 snapshot for this dashboard.

## Snapshot

- dashboard_id: `dashboard_3804681042591760385`
- dashboard_name: `市场顾问-用户画像分析`
- captured_at: `2026-07-05 20:13:32`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3804681042591760385&htmlId=html_3975684262305193985`
- loaded_html_id: `html_3975684262305193985`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260705-201116-edit\20260705-201237\dashboard_3804681042591760385_edit_metrics_profile.json`
- pivot_unit_count: `8`
- configured_field_count: `99`
- measure_count: `74`
- custom_formula_count: `52`
- text_note_count: `0`
- dataset_subject_count: `11`
- error_count: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count | pivot units |
|---|---|---|---:|---|
| `2683` | 前期流量画像-城市 | [data_center_market_2683_20260705.sql](../../../resources/raw_sql/data_center_market_2683_20260705.sql) | 1 | 流量用户画像 |
| `2809` | 成单用户画像整体数据 | [data_center_market_2809_20260705.sql](../../../resources/raw_sql/data_center_market_2809_20260705.sql) | 1 | 多科用户成单表 |
| `2812` | 用户画像成单用户城市标签 | [data_center_market_2812_20260705.sql](../../../resources/raw_sql/data_center_market_2812_20260705.sql) | 1 | 透视表_副本 |
| `2836` | 市场渠道用户成单分析 | [data_center_market_2836_20260705.sql](../../../resources/raw_sql/data_center_market_2836_20260705.sql) | 1 | 1 |
| `2885` | 市场渠道用户成单分析3 | [data_center_market_2885_20260705.sql](../../../resources/raw_sql/data_center_market_2885_20260705.sql) | 1 | 1_副本 |
| `2883` | 市场渠道用户成单分析2 | [data_center_market_2883_20260705.sql](../../../resources/raw_sql/data_center_market_2883_20260705.sql) | 1 | 1_副本_副本 |
| `2344` | 分析--分周期转化 | [data_center_market_2344_20260705.sql](../../../resources/raw_sql/data_center_market_2344_20260705.sql) | 1 | 分周期退费数据占比 |
| `2890` | 多科用户退费 | [data_center_market_2890_20260705.sql](../../../resources/raw_sql/data_center_market_2890_20260705.sql) | 1 | 多科用户退费占比 |

## Pivot units

### 流量用户画像

- unit_id: `unit_3874154854137556993`
- unit_type: `u_pivot`
- model: `2683` / 前期流量画像-城市
- dimensions: 渠道 / `channel_map`; 城市等级 / `city_level_name`
- measures: 等级占比 / `can_renew_ds_count_a`; 退前线索 / `IP_lead_count`; 退后线索 / `can_renew_ds_count_a`; 48h外呼 / `48h外呼`; 5min / `5min`; 深沟 / `深沟`; 当期单效 / `当期单效`; 当期人头转化 / `当期人头转化`; 截面单效 / `截面单效`; 截面人头转化 / `截面人头转化`

### 多科用户成单表

- unit_id: `unit_3901691404520521729`
- unit_type: `u_pivot`
- model: `2809` / 成单用户画像整体数据
- dimensions: 期次 / `period_name`; 渠道 / `channel_map`
- measures: 线索量 / `lead_count`; 正价课人头 / `pay_user_head_count`; 正价课人次 / `pay_subject_person_count`; 拓课率 / `拓课率`; 净收款 / `net_income`; 1科人头 / `subject_1_user_count`; 1科人头占比 / `1科人头占比`; 1科GMV / `subject_1_gmv`; 1科GMV占比 / `1科GMV占比`; 2-3科人头 / `subject_2_3_user_count`; 2-3科人头占比 / `2-3科人头占比`; 2-3科GMV / `subject_2_3_gmv`; 2-3科GMV占比 / `2-3科GMV占比`; 3科以上人头 / `subject_3_plus_user_count`; 3科以上人头占比 / `3科以上人头占比`; 3科以上GMV / `subject_3_plus_gmv`; 3科以上GMV占比 / `3科以上GMV占比`

### 透视表_副本

- unit_id: `unit_3901885938907897856`
- unit_type: `u_pivot`
- model: `2812` / 用户画像成单用户城市标签
- dimensions: 期次 / `period_name`; 城市等级 / `city_level_name`
- measures: 线索量 / `lead_count`; 线索量占比 / `线索量转化占比`; 净收款(截面) / `net_income_section`; 净收款占比 / `净收款占比`; 人均收款 / `人均收款`; 人头转化率(截面) / `人头转化率(截面)`; 单效(截面) / `单效(截面)`; 拓科率(截面) / `拓科率(截面)`

### 1

- unit_id: `unit_3913632965000523776`
- unit_type: `u_pivot`
- model: `2836` / 市场渠道用户成单分析
- dimensions: 首call通时区间 / `bucket_name`
- measures: 对应区间人数 / `对应区间人数`; 人数占比 / `人数占比`; 转化人头数 / `转化人头数`; 人头转化率 / `人头转化率`; 订单转化率 / `订单转化率`; 单效(截面) / `单效(截面)`

### 1_副本

- unit_id: `unit_3913648004741677057`
- unit_type: `u_pivot`
- model: `2885` / 市场渠道用户成单分析3
- dimensions: 上课区间 / `bucket_name`
- measures: 对应区间人数 / `对应区间人数`; 人数占比 / `人数占比`; 转化人头数 / `转化人头数`; 人头转化率 / `人头转化率`; 订单转化率 / `订单转化率`; 单效(截面) / `单效(截面)`

### 1_副本_副本

- unit_id: `unit_3913653568806137857`
- unit_type: `u_pivot`
- model: `2883` / 市场渠道用户成单分析2
- dimensions: 沟通状态 / `bucket_name`
- measures: 对应区间人数 / `对应区间人数`; 人数占比 / `人数占比`; 转化人头数 / `转化人头数`; 人头转化率 / `人头转化率`; 订单转化率 / `订单转化率`; 单效(截面) / `单效(截面)`

### 分周期退费数据占比

- unit_id: `unit_3975526029663846401`
- unit_type: `u_pivot`
- model: `2344` / 分析--分周期转化
- dimensions: 期次 / `qici`; 经理 / `jingli`; 渠道 / `channel_1`; 年级 / `grade_list`; 主管 / `xiaozu`
- measures: 退后线索 / `can_renew_ds_count_a`; 截面净收款 / `gmv_total`; 截面退费 / `refund_total`; 当期退款 / `refund_7`; 当期退款占比 / `当期退款占比`; 8-14天退款占比 / `8-14天退款占比`; 15-30天退款占比 / `15-30天退款占比`; 非30天退款占比 / `非30天退款占比`; 下期线索当期退款占比 / `下期线索当期退款占比`
- filters: qici / `qici`; channel_1 / `channel_1`; jingli / `jingli`; grade_list / `grade_list`

### 多科用户退费占比

- unit_id: `unit_3935197018570850305`
- unit_type: `u_pivot`
- model: `2890` / 多科用户退费
- dimensions: 期次 / `period_name`; 经理 / `jingli`; 渠道 / `channel_map`
- measures: 退后线索 / `valid_lead_cnt`; GMV退费率(当期) / `GMV退费率(当期)`; 退费金额(截面) / `refund_section_gmv`; GMV退费率(截面) / `GMV退费率(截面)`; 退费人头(截面) / `refund_headcount_section`; 人头退费率(截面) / `人头退费率(截面)`; 1科GMV退费率 / `1科GMV退费率`; 1科人头退费率 / `1科人头退费率`; 2-3科GMV退费率 / `2-3科GMV退费率`; 2-3科人头退费率 / `2-3科人头退费率`; 3科+GMV退费率 / `3科+GMV退费率`; 3科+人头退费率 / `3科+人头退费率`
- filters: period_name / `period_name`; channel_map / `channel_map`; jingli / `jingli`; zhuguan / `zhuguan`

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 等级占比 | can_renew_ds_count_a<br>`8664136735156225` | measure | sum(8664136735156225) |  |  | 流量用户画像 |
| 退前线索 | IP_lead_count<br>`8664136735156224` | measure | sum(8664136735156224) |  |  | 流量用户画像 |
| 48h外呼 | 48h外呼<br>`customized_993907022323519489` | custom_measure | ifnull(sum(${first_call_48h})/sum(${can_renew_ds_count_a}),0) |  | paramId=8664136735156227, orgParamType=1<br>paramId=8664136735156225, orgParamType=1 | 流量用户画像 |
| 5min | 5min<br>`customized_993907022432571393` | custom_measure | ifnull(sum(${long_call_5})/sum(${can_renew_ds_count_a}),0) |  | paramId=8664136735156232, orgParamType=1<br>paramId=8664136735156225, orgParamType=1 | 流量用户画像 |
| 深沟 | 深沟<br>`customized_993907022977830913` | custom_measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | paramId=8664136735156229, orgParamType=1<br>paramId=8664136735156225, orgParamType=1 | 流量用户画像 |
| 当期单效 | 当期单效<br>`customized_993907022659063809` | custom_measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | paramId=8664136735156249, orgParamType=1<br>paramId=8664136735156225, orgParamType=1 | 流量用户画像 |
| 当期人头转化 | 当期人头转化<br>`customized_993907022545817600` | custom_measure | ifnull(sum(${pay_users_on_period})/sum(${can_renew_ds_count_a}),0) |  | paramId=8664136735156237, orgParamType=1<br>paramId=8664136735156225, orgParamType=1 | 流量用户画像 |
| 截面单效 | 截面单效<br>`customized_993907022868779009` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | paramId=8664136735156247, orgParamType=1<br>paramId=8664136735156225, orgParamType=1 | 流量用户画像 |
| 截面人头转化 | 截面人头转化<br>`customized_993907022763921408` | custom_measure | ifnull(sum(${pay_users})/sum(${can_renew_ds_count_a}),0) |  | paramId=8664136735156236, orgParamType=1<br>paramId=8664136735156225, orgParamType=1 | 流量用户画像 |
| 线索量 | lead_count<br>`8771778132928512` | measure | sum(8771778132928512) |  |  | 多科用户成单表 |
| 正价课人头 | pay_user_head_count<br>`8771778132928513` | measure | sum(8771778132928513) |  |  | 多科用户成单表 |
| 正价课人次 | pay_subject_person_count<br>`8771778132928514` | measure | sum(8771778132928514) |  |  | 多科用户成单表 |
| 拓课率 | 拓课率<br>`customized_993907029084737537` | custom_measure | ifnull(sum(${pay_subject_person_count}) / sum(${pay_user_head_count}), 0) |  | paramId=8771778132928514, orgParamType=1<br>paramId=8771778132928513, orgParamType=1 | 多科用户成单表 |
| 净收款 | net_income<br>`8771778132928515` | measure | sum(8771778132928515) |  |  | 多科用户成单表 |
| 1科人头 | subject_1_user_count<br>`8771778132928516` | measure | sum(8771778132928516) |  |  | 多科用户成单表 |
| 1科人头占比 | 1科人头占比<br>`customized_993907028556255233` | custom_measure | ifnull(sum(${subject_1_user_count}) / sum(${pay_user_head_count}), 0) |  | paramId=8771778132928516, orgParamType=1<br>paramId=8771778132928513, orgParamType=1 | 多科用户成单表 |
| 1科GMV | subject_1_gmv<br>`8771778132928517` | measure | sum(8771778132928517) |  |  | 多科用户成单表 |
| 1科GMV占比 | 1科GMV占比<br>`customized_993907028447203329` | custom_measure | ifnull(sum(${subject_1_gmv}) / sum(${net_income}), 0) |  | paramId=8771778132928517, orgParamType=1<br>paramId=8771778132928515, orgParamType=1 | 多科用户成单表 |
| 2-3科人头 | subject_2_3_user_count<br>`8851814501476352` | measure | sum(8851814501476352) |  |  | 多科用户成单表 |
| 2-3科人头占比 | 2-3科人头占比<br>`customized_993907028774359041` | custom_measure | ifnull(sum(${subject_2_3_user_count}) / sum(${pay_user_head_count}), 0) |  | paramId=8851814501476352, orgParamType=1<br>paramId=8771778132928513, orgParamType=1 | 多科用户成单表 |
| 2-3科GMV | subject_2_3_gmv<br>`8851814501476353` | measure | sum(8851814501476353) |  |  | 多科用户成单表 |
| 2-3科GMV占比 | 2-3科GMV占比<br>`customized_993907028665307137` | custom_measure | ifnull(sum(${subject_2_3_gmv}) / sum(${net_income}), 0) |  | paramId=8851814501476353, orgParamType=1<br>paramId=8771778132928515, orgParamType=1 | 多科用户成单表 |
| 3科以上人头 | subject_3_plus_user_count<br>`8851814501476354` | measure | sum(8851814501476354) |  |  | 多科用户成单表 |
| 3科以上人头占比 | 3科以上人头占比<br>`customized_993907028984074241` | custom_measure | ifnull(sum(${subject_3_plus_user_count}) / sum(${pay_user_head_count}), 0) |  | paramId=8851814501476354, orgParamType=1<br>paramId=8771778132928513, orgParamType=1 | 多科用户成单表 |
| 3科以上GMV | subject_3_plus_gmv<br>`8851814501476355` | measure | sum(8851814501476355) |  |  | 多科用户成单表 |
| 3科以上GMV占比 | 3科以上GMV占比<br>`customized_993907028879216640` | custom_measure | ifnull(sum(${subject_3_plus_gmv}) / sum(${net_income}), 0) |  | paramId=8851814501476355, orgParamType=1<br>paramId=8771778132928515, orgParamType=1 | 多科用户成单表 |
| 线索量 | lead_count<br>`8771948635645952` | measure | sum(8771948635645952) |  |  | 透视表_副本 |
| 线索量占比 | 线索量转化占比<br>`customized_993907032398237697` | custom_measure | ifnull(sum(${lead_count}) / sum(${total_lead_count_in_period}),0) |  | paramId=8771948635645952, orgParamType=1<br>paramId=8852007839754240, orgParamType=1 | 透视表_副本 |
| 净收款(截面) | net_income_section<br>`8771948635645954` | measure | sum(8771948635645954) |  |  | 透视表_副本 |
| 净收款占比 | 净收款占比<br>`customized_993907032075276288` | custom_measure | ifnull(sum(${net_income_section}) / sum(${total_net_income_in_period}),0) |  | paramId=8771948635645954, orgParamType=1<br>paramId=8852090697181184, orgParamType=1 | 透视表_副本 |
| 人均收款 | 人均收款<br>`customized_993907031861366785` | custom_measure | ifnull(sum(${net_income_section}) / sum(${pay_user_head_count}), 0) |  | paramId=8771948635645954, orgParamType=1<br>paramId=8852007839754243, orgParamType=1 | 透视表_副本 |
| 人头转化率(截面) | 人头转化率(截面)<br>`customized_993907031966224384` | custom_measure | ifnull(sum(${pay_user_head_count}) / sum(${lead_count}), 0) |  | paramId=8852007839754243, orgParamType=1<br>paramId=8771948635645952, orgParamType=1 | 透视表_副本 |
| 单效(截面) | 单效(截面)<br>`customized_993907032184328192` | custom_measure | ifnull(sum(${net_income_section}) / sum(${lead_count}), 0) |  | paramId=8771948635645954, orgParamType=1<br>paramId=8771948635645952, orgParamType=1 | 透视表_副本 |
| 拓科率(截面) | 拓科率(截面)<br>`customized_993907032289185793` | custom_measure | ifnull((sum(${pay_subject_person_count}) - sum(${pay_user_head_count}))/sum(${pay_user_head_count}), 0) |  | paramId=8851950263101442, orgParamType=1<br>paramId=8852007839754243, orgParamType=1<br>paramId=8852007839754243, orgParamType=1 | 透视表_副本 |
| 对应区间人数 | 对应区间人数<br>`customized_993907035837566977` | custom_measure | sum(${bucket_user_cnt}) |  | paramId=8891975891183616, orgParamType=1 | 1 |
| 人数占比 | 人数占比<br>`customized_993907035627851777` | custom_measure | ifnull(sum(${bucket_user_cnt}) / sum(${total_lead_cnt}), 0) |  | paramId=8891975891183616, orgParamType=1<br>paramId=8892181476435969, orgParamType=1 | 1 |
| 转化人头数 | 转化人头数<br>`customized_993907036051476480` | custom_measure | sum(${conversion_user_cnt}) |  | paramId=8891975891183619, orgParamType=1 | 1 |
| 人头转化率 | 人头转化率<br>`customized_993907035510411265` | custom_measure | ifnull(sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}), 0) |  | paramId=8891975891183619, orgParamType=1<br>paramId=8891975891183616, orgParamType=1 | 1 |
| 订单转化率 | 订单转化率<br>`customized_993907035942424576` | custom_measure | ifnull(sum(${order_cnt}) / sum(${bucket_user_cnt}), 0) |  | paramId=8891975891183620, orgParamType=1<br>paramId=8891975891183616, orgParamType=1 | 1 |
| 单效(截面) | 单效(截面)<br>`customized_993907035732709376` | custom_measure | ifnull(sum(${section_profit_amt}) / sum(${bucket_user_cnt}), 0) |  | paramId=8891975891183622, orgParamType=1<br>paramId=8891975891183616, orgParamType=1 | 1 |
| 对应区间人数 | 对应区间人数<br>`customized_993907043047575552` | custom_measure | sum(${bucket_user_cnt}) |  | paramId=8896261596014593, orgParamType=1 | 1_副本 |
| 人数占比 | 人数占比<br>`customized_993907042846248960` | custom_measure | ifnull(sum(${bucket_user_cnt}) / sum(${total_lead_cnt}), 0) |  | paramId=8896261596014593, orgParamType=1<br>paramId=8896261596014595, orgParamType=1 | 1_副本 |
| 转化人头数 | 转化人头数<br>`customized_993907043244707841` | custom_measure | sum(${conversion_user_cnt}) |  | paramId=8896261596014599, orgParamType=1 | 1_副本 |
| 人头转化率 | 人头转化率<br>`customized_993907042741391361` | custom_measure | sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}) |  | paramId=8896261596014599, orgParamType=1<br>paramId=8896261596014593, orgParamType=1 | 1_副本 |
| 订单转化率 | 订单转化率<br>`customized_993907043148238848` | custom_measure | sum(${order_cnt}) / sum(${bucket_user_cnt}) |  | paramId=8896261596014600, orgParamType=1<br>paramId=8896261596014593, orgParamType=1 | 1_副本 |
| 单效(截面) | 单效(截面)<br>`customized_993907042946912256` | custom_measure | sum(${section_profit_amt}) / sum(${bucket_user_cnt}) |  | paramId=8896261596014602, orgParamType=1<br>paramId=8896261596014593, orgParamType=1 | 1_副本 |
| 对应区间人数 | 对应区间人数<br>`customized_993907039398531072` | custom_measure | sum(${bucket_user_cnt}) |  | paramId=8892319738718209, orgParamType=1 | 1_副本_副本 |
| 人数占比 | 人数占比<br>`customized_993907039184621569` | custom_measure | ifnull(sum(${bucket_user_cnt}) / sum(${total_lead_cnt}), 0) |  | paramId=8892319738718209, orgParamType=1<br>paramId=8892319738718211, orgParamType=1 | 1_副本_副本 |
| 转化人头数 | 转化人头数<br>`customized_993907039708909568` | custom_measure | sum(${conversion_user_cnt}) |  | paramId=8892319738718215, orgParamType=1 | 1_副本_副本 |
| 人头转化率 | 人头转化率<br>`customized_993907039079763968` | custom_measure | sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}) |  | paramId=8892319738718215, orgParamType=1<br>paramId=8892319738718209, orgParamType=1 | 1_副本_副本 |
| 订单转化率 | 订单转化率<br>`customized_993907039604051969` | custom_measure | sum(${order_cnt}) / sum(${bucket_user_cnt}) |  | paramId=8892319738718216, orgParamType=1<br>paramId=8892319738718209, orgParamType=1 | 1_副本_副本 |
| 单效(截面) | 单效(截面)<br>`customized_993907039289479168` | custom_measure | sum(${section_profit_amt}) / sum(${bucket_user_cnt}) |  | paramId=8892319738718218, orgParamType=1<br>paramId=8892319738718209, orgParamType=1 | 1_副本_副本 |
| 退后线索 | can_renew_ds_count_a<br>`9060600883668992` | measure | sum(9060600883668992) |  |  | 分周期退费数据占比 |
| 截面净收款 | gmv_total<br>`8456155560699909` | measure | sum(8456155560699909) |  |  | 分周期退费数据占比 |
| 截面退费 | refund_total<br>`8456155560699915` | measure | sum(8456155560699915) |  |  | 分周期退费数据占比 |
| 当期退款 | refund_7<br>`8456155560699910` | measure | sum(8456155560699910) |  |  | 分周期退费数据占比 |
| 当期退款占比 | 当期退款占比<br>`customized_993907057413066753` | custom_measure | ifnull(sum(${refund_7}) / sum(${refund_total}), 0) |  | paramId=8456155560699910, orgParamType=1<br>paramId=8456155560699915, orgParamType=1 | 分周期退费数据占比 |
| 8-14天退款占比 | 8-14天退款占比<br>`customized_993907057199157248` | custom_measure | ifnull(sum(${refund_14}) / sum(${refund_total}), 0) |  | paramId=8456155560699911, orgParamType=1<br>paramId=8456155560699915, orgParamType=1 | 分周期退费数据占比 |
| 15-30天退款占比 | 15-30天退款占比<br>`customized_993907057094299649` | custom_measure | ifnull(sum(${refund_30}) / sum(${refund_total}), 0) |  | paramId=8456155560699912, orgParamType=1<br>paramId=8456155560699915, orgParamType=1 | 分周期退费数据占比 |
| 非30天退款占比 | 非30天退款占比<br>`customized_993907057522118657` | custom_measure | ifnull(sum(${refund_n30}) / sum(${refund_total}), 0) |  | paramId=8456155560699913, orgParamType=1<br>paramId=8456155560699915, orgParamType=1 | 分周期退费数据占比 |
| 下期线索当期退款占比 | 下期线索当期退款占比<br>`customized_993907057304014849` | custom_measure | ifnull(sum(${refund_7_p}) / sum(${refund_total}), 0) |  | paramId=8456155560699914, orgParamType=1<br>paramId=8456155560699915, orgParamType=1 | 分周期退费数据占比 |
| 退后线索 | valid_lead_cnt<br>`8902653441370112` | measure | sum(8902653441370112) |  |  | 多科用户退费占比 |
| GMV退费率(当期) | GMV退费率(当期)<br>`customized_993907049510998017` | custom_measure | ifnull(SUM(${refund_current_gmv}) / SUM(${net_income_current_gmv}), 0) |  | paramId=8902653441370114, orgParamType=1<br>paramId=8902653441370115, orgParamType=1 | 多科用户退费占比 |
| 退费金额(截面) | refund_section_gmv<br>`8902653441370116` | measure | sum(8902653441370116) |  |  | 多科用户退费占比 |
| GMV退费率(截面) | GMV退费率(截面)<br>`customized_993907049611661313` | custom_measure | ifnull(sum(${refund_section_gmv}) / sum(${net_income_section_gmv}), 0) |  | paramId=8902653441370116, orgParamType=1<br>paramId=8902653441370117, orgParamType=1 | 多科用户退费占比 |
| 退费人头(截面) | refund_headcount_section<br>`8902653441370118` | measure | sum(8902653441370118) |  |  | 多科用户退费占比 |
| 人头退费率(截面) | 人头退费率(截面)<br>`customized_993907049712324609` | custom_measure | ifnull(sum(${refund_headcount_section}) / sum(${total_headcount}), 0) |  | paramId=8902653441370118, orgParamType=1<br>paramId=8902653441370113, orgParamType=1 | 多科用户退费占比 |
| 1科GMV退费率 | 1科GMV退费率<br>`customized_993907048881852417` | custom_measure | ifnull(sum(${refund_1_subject_gmv}) / sum(${net_income_1_subject_gmv}), 0) |  | paramId=8902653441370119, orgParamType=1<br>paramId=8902653441370120, orgParamType=1 | 多科用户退费占比 |
| 1科人头退费率 | 1科人头退费率<br>`customized_993907048990904321` | custom_measure | ifnull(sum(${refund_1_subject_headcount}) / sum(${total_headcount}), 0) |  | paramId=8902653441370121, orgParamType=1<br>paramId=8902653441370113, orgParamType=1 | 多科用户退费占比 |
| 2-3科GMV退费率 | 2-3科GMV退费率<br>`customized_993907049095761920` | custom_measure | ifnull(sum(${refund_2_3_subject_gmv}) / sum(${net_income_2_3_subject_gmv}), 0) |  | paramId=8902653441370122, orgParamType=1<br>paramId=8902653441370123, orgParamType=1 | 多科用户退费占比 |
| 2-3科人头退费率 | 2-3科人头退费率<br>`customized_993907049200619521` | custom_measure | ifnull(sum(${refund_2_3_subject_headcount}) / sum(${total_headcount}), 0) |  | paramId=8902653441370124, orgParamType=1<br>paramId=8902653441370113, orgParamType=1 | 多科用户退费占比 |
| 3科+GMV退费率 | 3科+GMV退费率<br>`customized_993907049301282817` | custom_measure | ifnull(sum(${refund_3plus_subject_gmv}) / sum(${net_income_3plus_subject_gmv}),0) |  | paramId=8902653441370125, orgParamType=1<br>paramId=8902653441370126, orgParamType=1 | 多科用户退费占比 |
| 3科+人头退费率 | 3科+人头退费率<br>`customized_993907049406140416` | custom_measure | ifnull(sum(${refund_3plus_subject_headcount}) / sum(${total_headcount}), 0) |  | paramId=8902653441370127, orgParamType=1<br>paramId=8902653441370113, orgParamType=1 | 多科用户退费占比 |

## Dataset field tree summary

| subject_id | field_count | sampled fields |
|---|---:|---|
| `177646` | 12 | qici, channel_1, jingli, xiaozu, grade_list, subject, course_name, analysis_type, dim_value, refund_amount, total_refund_amount, 退费率 |
| `177648` | 10 | qici, name, channel_1, jingli, xiaozu, grade_list, refund_reason, income_amount, refund_amount, 退费原因 |
| `177649` | 53 | period_name, channel_map, grade_1, depart_1, depart, jingli, zhuguan, employee_email_name, city_level_name, last_app_channel, sub, name1, xiaozu, cb_cb, gl_gl, IP_lead_count, can_renew_ds_count_a, first_call_24h, first_call_48h, friend_lead |
| `177651` | 29 | period_name, channel_map, grade_name, manager_name, valid_lead_count, trade_income, net_trade_income, regular_course_user_count, regular_course_order_count, avg_income_per_regular_course_user, lead_count, pay_user_head_count, pay_subject_person_count, net_income, subject_1_user_count, subject_1_gmv, subject_2_3_user_count, subject_2_3_gmv, subject_3_plus_user_count, subject_3_plus_gmv |
| `177652` | 15 | period_name, city_level_name, lead_count, net_income_section, pay_subject_person_count, total_lead_count_in_period, valid_lead_count, pay_user_head_count, total_net_income_in_period, 人均收款, 人头转化率(截面), 净收款占比, 单效(截面), 拓科率(截面), 线索量转化占比 |
| `177653` | 26 | period_name, channel_map, channel_group, grade_name, analysis_type, bucket_name, bucket_sort, bucket_user_cnt, total_valid_lead_cnt, total_valid_lead_cnt_once, conversion_user_cnt, order_cnt, trade_income_amt, section_profit_amt, head_conversion_rate, order_conversion_rate, section_unit_efficiency, bucket_valid_lead_cnt, total_lead_cnt, total_lead_cnt_once |
| `177654` | 27 | period_name, channel_map, channel_group, grade_name, analysis_type, bucket_name, bucket_sort, bucket_user_cnt, bucket_valid_lead_cnt, total_lead_cnt, total_valid_lead_cnt, total_lead_cnt_once, total_valid_lead_cnt_once, conversion_user_cnt, order_cnt, trade_income_amt, section_profit_amt, head_conversion_rate, order_conversion_rate, section_unit_efficiency |
| `177655` | 26 | period_name, channel_map, channel_group, grade_name, analysis_type, bucket_name, bucket_sort, bucket_user_cnt, bucket_valid_lead_cnt, total_lead_cnt, total_valid_lead_cnt, total_lead_cnt_once, total_valid_lead_cnt_once, conversion_user_cnt, order_cnt, trade_income_amt, section_profit_amt, head_conversion_rate, order_conversion_rate, section_unit_efficiency |
| `177656` | 11 | period_name, channel_map, grade_name, jingli, 有效线索量, 收款, 净收款, GMV退费, 退费人头, GMV退费率, 人头退费率 |
| `177657` | 31 | period_name, channel_map, grade_name, jingli, zhuguan, employee_email_name, valid_lead_cnt, total_headcount, refund_current_gmv, net_income_current_gmv, refund_section_gmv, net_income_section_gmv, refund_headcount_section, refund_1_subject_gmv, net_income_1_subject_gmv, refund_1_subject_headcount, refund_2_3_subject_gmv, net_income_2_3_subject_gmv, refund_2_3_subject_headcount, refund_3plus_subject_gmv |
| `177660` | 24 | qici, channel_1, grade_list, name, jingli, xiaozu, gmv_7, gmv_14, gmv_30, gmv_n30, gmv_7_h, gmv_total, refund_7, refund_14, refund_30, refund_n30, refund_7_p, refund_total, can_renew_ds_count_a, 15-30天退款占比 |

## Errors

- None.
