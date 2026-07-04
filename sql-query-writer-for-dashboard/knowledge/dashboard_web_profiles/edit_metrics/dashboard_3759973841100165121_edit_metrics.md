# 运营侧数据看板 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3759973841100165121`
- dashboard_name: `运营侧数据看板`
- captured_at: `2026-06-24 19:28:51`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3759973841100165121&htmlId=html_3959901495142821889`
- loaded_html_id: `html_3959901495142821889`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3759973841100165121_edit_metrics_profile.json`
- pivot_units: `16`
- configured_fields: `418`
- measures: `334`
- custom_formulas: `249`
- text_notes: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2345` | 进量测试(市场渠道) | [data_center_market_2345_20260624.sql](../../../resources/raw_sql/data_center_market_2345_20260624.sql) | 1 |
| `2293` | 运营侧个人数据 | [data_center_market_2293_20260704.sql](../../../resources/raw_sql/data_center_market_2293_20260704.sql) | 10 |
| `2310` | 分二级部门转化 | [data_center_market_2310_20260624.sql](../../../resources/raw_sql/data_center_market_2310_20260624.sql) | 1 |
| `2424` | 每日转化数据表 | [data_center_market_2424_20260624.sql](../../../resources/raw_sql/data_center_market_2424_20260624.sql) | 1 |
| `2344` | 分析--分周期转化 | [data_center_market_2344_20260624.sql](../../../resources/raw_sql/data_center_market_2344_20260624.sql) | 1 |
| `2132` | (内部)到课衰减情况 | [data_center_market_2132_20260628.sql](../../../resources/raw_sql/data_center_market_2132_20260628.sql) | 1 |
| `2054` | (内部渠道)外呼过程数据 | [data_center_market_2054_20260624.sql](../../../resources/raw_sql/data_center_market_2054_20260624.sql) | 1 |

## Pivot units

### 进量_转化分析

- unit_id: `unit_3803445342673076224`
- unit_type: `u_pivot`
- model: `2345` / 进量测试(市场渠道)
- dimensions: 分配日期 / `assign_day_new`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 24h外呼 / `24h外呼率`; 48h外呼 / `48h外呼率`; 5min; 好友 / `好友率`; APP; 深沟 / `深沟率`; 课1; 课1有效; 当期单效; 截面单效

### 经理

- unit_id: `unit_3788931121683902464`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli_11`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 接量人力; 人产; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 5min占比; 5min转化率; 20min占比; 20min转化率; 40min占比; 40min转化率; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效; 客单价

### 主管

- unit_id: `unit_3800256717559488520`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli_11`; 主管 / `xiaozu`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 接量人力; 人产; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 5min占比; 5min转化率; 20min占比; 20min转化率; 40min占比; 40min转化率; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效; 客单价

### 个人

- unit_id: `unit_3800257159308951556`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli_11`; 主管 / `xiaozu`; 顾问 / `employee_email_name`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 接量人力; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 5min占比; 5min转化率; 20min占比; 20min转化率; 40min占比; 40min转化率; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效; 客单价

### 收款分时间占比_副本

- unit_id: `unit_3910424477630115844`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期次 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`
- measures: 退前线索 / `can_renew_ds_count_a`; 退后线索 / `s_lead`; 接量人力; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 人头转化(当期) / `pay_users_on_period`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 5min占比; 5min转化率; 20min占比; 20min转化率; 40min占比; 40min转化率; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率; 单效; 客单价

### B站亚飞

- unit_id: `unit_3864395442075807750`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率

### 抖私1

- unit_id: `unit_3889082426239688709`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 年级 / `grade_1`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率

### koc整体

- unit_id: `unit_3889083573032431621`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率

### 自孵化koc

- unit_id: `unit_3889084874430734339`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率

### koc常规

- unit_id: `unit_3889085855924989958`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率

### 亚飞

- unit_id: `unit_3791433812547198984`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率

### 同渠道分部门(不可外传)

- unit_id: `unit_3793248921101189120`
- unit_type: `u_pivot`
- model: `2310` / 分二级部门转化
- dimensions: 期次 / `period_name`; 学部 / `dept_name`; 年级 / `lead_purchase_intention_level2_category_name`; 部门 / `depart`; period_name; lead_purchase_intention_level2_category_name; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 24h外呼; 首call; 好友率; 订单转化(当期); 人头转化(当期); 净收款(当期) / `xb_trade_profit`; 退前单效(当期); 单效(当期); 人均报科; 订单转化; 人头转化; 净收款 / `trade_profit`; 退前单效; 退后单效 / `单效`; 退费率

### 收款分时间占比

- unit_id: `unit_3823452752095543296`
- unit_type: `u_pivot`
- model: `2424` / 每日转化数据表
- dimensions: 期次 / `qici`; 渠道 / `channel_1`
- measures: 总净收 / `gmv_t`; 周2收款 / `gmv_2`; 周2占比; 周2单效; 周3收款 / `gmv_3`; 周3占比; 周3单效; 周4收款 / `gmv_4`; 周4占比; 周4单效; 周5收款 / `gmv_5`; 周5占比; 周5单效; 周6收款 / `gmv_6`; 周6占比; 周6单效; 周7收款 / `gmv_7`; 周7占比; 周7单效; 周1收款 / `gmv_1`; 周1占比; 周1单效

### 线索分时间转化数据

- unit_id: `unit_3803175274388676608`
- unit_type: `u_pivot`
- model: `2344` / 分析--分周期转化
- dimensions: 期次 / `qici`; 渠道 / `channel_1`; 经理 / `jingli`; 年级 / `grade_list`; 主管 / `xiaozu`; qici; grade_list; channel_1
- measures: 当期净收款 / `gmv_7`; 当期占比 / `当期收款占比`; 8_14天内收款占比 / `14天内收款占比(不含当期)`; 15_30天内净收款占比 / `30天内净收款占比(不含前14天)`; 非30天内净收款占比; 下期线索当期占比; 净收款 / `gmv_total`; 当期退款 / `refund_7`; 当期退款占比; 8_14天内退款占比 / `14天内退款占比(不含当期)`; 15_30天内退款占比 / `30天内退款占比(不含前14天)`; 非30天内退款占比; 下期线索当期退款占比; 总退款 / `refund_total`

### 行课数据

- unit_id: `unit_3791886183119278081`
- unit_type: `u_pivot`
- model: `2132` / (内部)到课衰减情况
- dimensions: 期 / `qici`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; qici; department; grade_1; channel_map_1; rule_name
- measures: 退后线索 / `lead`; 课1; 课1有效; 课2; 课2有效; 课3; 课3有效; 课4; 课4有效; 课5; 课5有效; 课6; 课6有效

### 外呼数据

- unit_id: `unit_3791903466230407169`
- unit_type: `u_pivot`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 期次 / `qici`; 经理 / `jingli`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; qici; grade_1; channel_map_1; jingli
- measures: 退前线索 / `lead_count`; 退后线索 / `valid_lead_count`; 总通时 / `call_duration`; 首call; 6h外呼; 12h外呼; 24h外呼 / `24h外呼率`; 48h外呼 / `48h外呼率`; 48h沟通 / `48h沟通率`; 外呼率; 沟通率; 外呼频次; 平均接通时长(min); 外呼接通率; 5min比例; 好友率; APP登录率; 深沟率; 双沟率; 已回收

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 退前线索 | lead_count<br>`8590324328392704` | measure | sum(8590324328392704) |  |  | 进量_转化分析 |
| 退后线索 | can_renew_ds_count_a<br>`8387973858551809` | measure | sum(8387973858551809) |  |  | 进量_转化分析 |
| 24h外呼 | 24h外呼率<br>`customized_989093197117075457` | custom_measure | ifnull(sum(${first_call_24h})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8388293899741184', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 48h外呼 | 48h外呼率<br>`customized_989093197221933056` | custom_measure | ifnull(sum(${first_call_48h})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8388293899741185', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 5min | 5min<br>`customized_989093197322596352` | custom_measure | ifnull(sum(${long_call_5})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8392152286717952', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 好友 | 好友率<br>`customized_989093197519728641` | custom_measure | ifnull(sum(${friend_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551810', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| APP | APP<br>`customized_989093197419065345` | custom_measure | ifnull(sum(${app_denglu})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8392152286717953', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 深沟 | 深沟率<br>`customized_989093197909798912` | custom_measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551811', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 课1 | 课1<br>`customized_989093198010462208` | custom_measure | ifnull(sum(${daoke_1})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551814', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 课1有效 | 课1有效<br>`customized_989093198106931201` | custom_measure | ifnull(sum(${daoke_v1})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8392152286717954', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 当期单效 | 当期单效<br>`customized_989093197616197632` | custom_measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551828', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 截面单效 | 截面单效<br>`customized_989093197712666625` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551826', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 退前线索 | lead_count<br>`8590283478886400` | measure | sum(8590283478886400) |  |  | 经理<br>主管<br>个人<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 退后线索 | can_renew_ds_count_a<br>`8337294278879233` | measure | sum(8337294278879233) |  |  | 经理<br>主管<br>个人<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 接量人力 | 接量人力<br>`customized_989093173113073664` | custom_measure | count(DISTINCT ${employee_email_name})-1 |  | {'paramId': '319197', 'orgParamType': 2, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 人产 | 人产<br>`customized_989093173209542657` | custom_measure | sum(${trade_profit}) / ${接量人力} |  | {'paramId': '8337294278879249', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_989093173113073664', 'orgParamType': 4, 'needBoundaryValue': False} | 经理<br>主管 |
| 首call率 | 首call率<br>`customized_989093175826788353` | custom_measure | ifnull(sum(${is_f_call})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8511077494122498', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 48h外呼 | 48h外呼<br>`customized_989093172517482496` | custom_measure | ifnull(sum(${first_call_in_48h})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8511077494122496', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 5min | 5min<br>`customized_989093172618145792` | custom_measure | ifnull(sum(${is_long_call})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8511077494122497', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 好友率 | 好友率<br>`customized_989093174086152192` | custom_measure | sum(${friend_lead})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8337294278879234', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 深沟率 | 深沟率<br>`customized_989093174786600961` | custom_measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879235', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 双沟率 | 双沟率<br>`customized_989093173893214208` | custom_measure | ifnull(sum(${shuanggou_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8511181621389312', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 人头转化(当期) | 人头(当期)<br>`customized_989093173402480641` | custom_measure | ifnull(sum(${pay_users_on_period})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879239', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 订单转化(当期) | 订单转化(当期)<br>`customized_989093175298306049` | custom_measure | ifnull(sum(${pay_user_subs_on_period})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879242', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 总收款(当期) | xb_trade_income<br>`8337294278879250` | measure | sum(8337294278879250) |  |  | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 退款(当期) | 退款(当期)<br>`customized_989093175503826944` | custom_measure | ifnull(sum(${xb_trade_income})-sum(${xb_trade_profit}),0) |  | {'paramId': '8337294278879250', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879251', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 净收款(当期) | xb_trade_profit<br>`8337294278879251` | measure | sum(8337294278879251) |  |  | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 退费率(当期) | 退费率(当期)<br>`customized_989093175721930752` | custom_measure | ifnull(${退款(当期)}/sum(${xb_trade_income}),0) |  | {'paramId': 'customized_989093175503826944', 'orgParamType': 4, 'needBoundaryValue': False}<br>{'paramId': '8337294278879250', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 单效(当期) | 单效(当期)<br>`customized_989093173792550912` | custom_measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879251', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞<br>同渠道分部门(不可外传) |
| 破蛋率 | 破蛋率<br>`customized_989093174983733248` | custom_measure | ifnull(sum(${podan})/${接量人力},0) |  | {'paramId': '8337294278879255', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_989093173113073664', 'orgParamType': 4, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 人均报科 | 人均报科<br>`customized_989093173306011648` | custom_measure | ifnull(sum(${pay_user_subs})/sum(${pay_users}),0) |  | {'paramId': '8337294278879241', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879238', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 5min占比 | 5min占比<br>`customized_989093172714614785` | custom_measure | ifnull(sum(${is_5m_call})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8648461290792960', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 5min转化率 | 5min转化率<br>`customized_989093172815278081` | custom_measure | ifnull(sum(${call_5m_z})/sum(${is_5m_call}),0) |  | {'paramId': '8648461290792961', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8648461290792960', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 20min占比 | 20min占比<br>`customized_989093172114829312` | custom_measure | ifnull(sum(${is_20m_call})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8647872988538880', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 20min转化率 | 20min转化率<br>`customized_989093172219686913` | custom_measure | ifnull(sum(${call_20m_z})/sum(${is_20m_call}),0) |  | {'paramId': '8647872988538883', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8647872988538880', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 40min占比 | 40min占比<br>`customized_989093172320350209` | custom_measure | ifnull(sum(${is_40m_call})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8647872988538881', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 40min转化率 | 40min转化率<br>`customized_989093172421013505` | custom_measure | ifnull(sum(${call_40m_z})/sum(${is_40m_call}),0) |  | {'paramId': '8647872988538884', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8647872988538881', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 人头转化 | 人头转化<br>`customized_989093173498949632` | custom_measure | ifnull(sum(${pay_users})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879238', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 订单转化 | 订单转化<br>`customized_989093175193448448` | custom_measure | ifnull(sum(${pay_user_subs})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879241', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 总收款 | trade_income<br>`8337294278879247` | measure | sum(8337294278879247) |  |  | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 退款 | trade_refund<br>`8337294278879248` | measure | sum(8337294278879248) |  |  | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 净收款 | trade_profit<br>`8337294278879249` | measure | sum(8337294278879249) |  |  | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 退费率 | 截面退费率<br>`customized_989093174480416768` | custom_measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | {'paramId': '8337294278879248', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879247', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人 |
| 单效 | 单效<br>`customized_989093173691887616` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879249', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本<br>B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 客单价 | 客单价<br>`customized_989093174283284481` | custom_measure | ifnull(sum(${trade_profit})/sum(${pay_users}),0) |  | {'paramId': '8337294278879249', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879238', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>收款分时间占比_副本 |
| 退前线索 | can_renew_ds_count_a<br>`8337294278879233` | measure | sum(8337294278879233) |  |  | 收款分时间占比_副本 |
| 退后线索 | s_lead<br>`8337294278879254` | measure | sum(8337294278879254) |  |  | 收款分时间占比_副本 |
| 人头转化(当期) | pay_users_on_period<br>`8337294278879239` | measure | sum(8337294278879239) |  |  | 收款分时间占比_副本 |
| 退费率 | 退费率<br>`customized_989093175617073153` | custom_measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | {'paramId': '8337294278879248', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879247', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比_副本 |
| 收款(当期) | xb_trade_income<br>`8337294278879250` | measure | sum(8337294278879250) |  |  | B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 净收(当期) | xb_trade_profit<br>`8337294278879251` | measure | sum(8337294278879251) |  |  | B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规 |
| 收款 | trade_income<br>`8337294278879247` | measure | sum(8337294278879247) |  |  | B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 净收 | trade_profit<br>`8337294278879249` | measure | sum(8337294278879249) |  |  | B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规 |
| 截面退费率 | 截面退费率<br>`customized_989093174480416768` | custom_measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | {'paramId': '8337294278879248', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879247', 'orgParamType': 1, 'needBoundaryValue': False} | B站亚飞<br>抖私1<br>koc整体<br>自孵化koc<br>koc常规<br>亚飞 |
| 退前线索 | lead_count<br>`8590289567967232` | measure | sum(8590289567967232) |  |  | 同渠道分部门(不可外传) |
| 退后线索 | can_renew_ds_count_a<br>`8348161562273793` | measure | sum(8348161562273793) |  |  | 同渠道分部门(不可外传) |
| 24h外呼 | 24h外呼<br>`customized_989093188535529473` | custom_measure | ifnull (<br>    sum(${first_call_in_24h}) / sum(${valid_lead_count}),<br>    0<br>) |  | {'paramId': '8807171058198528', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8807171058198529', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 首call | 首call<br>`customized_989093189705740288` | custom_measure | ifnull(sum(${is_f_call})/sum(${valid_lead_count}),0) |  | {'paramId': '8807171058198530', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8807171058198529', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传)<br>外呼数据 |
| 好友率 | 好友率<br>`customized_989093189126926336` | custom_measure | ifnull(sum(${is_friend_lead})/sum(${valid_lead_count}),0) |  | {'paramId': '8807171058198531', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8807171058198529', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 订单转化(当期) | 订单转化(当期)<br>`customized_989093189319864320` | custom_measure | sum(${pay_user_subs_on_period})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8348161562273798', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8348161562273793', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 人头转化(当期) | 人头转化(当期)<br>`customized_989093188833325056` | custom_measure | sum(${pay_users_not_on_period})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8348161562273796', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8348161562273793', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 净收款(当期) | xb_trade_profit<br>`8348161562273807` | measure | sum(8348161562273807) |  |  | 同渠道分部门(不可外传) |
| 退前单效(当期) | 退前单效(当期)<br>`customized_989093189508608001` | custom_measure | ifnull(sum(${xb_trade_profit})/sum(${lead_count}),0) |  | {'paramId': '8348161562273807', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8590289567967232', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 人均报科 | 人均报科<br>`customized_989093188636192769` | custom_measure | sum(${pay_user_subs})/sum(${pay_users}) |  | {'paramId': '8348161562273797', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8348161562273794', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 订单转化 | 订单转化<br>`customized_989093189223395329` | custom_measure | sum(${pay_user_subs})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8348161562273797', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8348161562273793', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 人头转化 | 人头转化<br>`customized_989093188736856065` | custom_measure | sum(${pay_users})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8348161562273794', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8348161562273793', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 净收款 | trade_profit<br>`8348161562273805` | measure | sum(8348161562273805) |  |  | 同渠道分部门(不可外传) |
| 退前单效 | 退前单效<br>`customized_989093189412139008` | custom_measure | ifnull(sum(${trade_profit})/sum(${lead_count}),0) |  | {'paramId': '8348161562273805', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8590289567967232', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 退后单效 | 单效<br>`customized_989093188929794049` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8348161562273805', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8348161562273793', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 退费率 | 退费率<br>`customized_989093189605076992` | custom_measure | sum(${trade_refund})/sum(${trade_income}) |  | {'paramId': '8348161562273804', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8348161562273803', 'orgParamType': 1, 'needBoundaryValue': False} | 同渠道分部门(不可外传) |
| 总净收 | gmv_t<br>`8466748058200071` | measure | sum(8466748058200071) |  |  | 收款分时间占比 |
| 周2收款 | gmv_2<br>`8466748058200065` | measure | sum(8466748058200065) |  |  | 收款分时间占比 |
| 周2占比 | 周2占比<br>`customized_989093203500806145` | custom_measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_2}) / sum(${gmv_t})<br>end |  | {'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200065', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周2单效 | 周2单效<br>`customized_989093203408531457` | custom_measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_2_z}) / sum(${v_lead_c})<br>end |  | {'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8648107429619713', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周3收款 | gmv_3<br>`8466748058200066` | measure | sum(8466748058200066) |  |  | 收款分时间占比 |
| 周3占比 | 周3占比<br>`customized_989093203697938432` | custom_measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_3}) / sum(${gmv_t})<br>end |  | {'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200066', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周3单效 | 周3单效<br>`customized_989093203597275136` | custom_measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_3_z}) / sum(${v_lead_c})<br>end |  | {'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8648107429619714', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周4收款 | gmv_4<br>`8466748058200067` | measure | sum(8466748058200067) |  |  | 收款分时间占比 |
| 周4占比 | 周4占比<br>`customized_989093203890876416` | custom_measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_4}) / sum(${gmv_t})<br>end |  | {'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200067', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周4单效 | 周4单效<br>`customized_989093203794407425` | custom_measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_4_z}) / sum(${v_lead_c})<br>end |  | {'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8648107429619715', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周5收款 | gmv_5<br>`8466748058200068` | measure | sum(8466748058200068) |  |  | 收款分时间占比 |
| 周5占比 | 周5占比<br>`customized_989093204083814400` | custom_measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_5}) / sum(${gmv_t})<br>end |  | {'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200068', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周5单效 | 周5单效<br>`customized_989093203987345409` | custom_measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_5_z}) / sum(${v_lead_c})<br>end |  | {'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8648107429619716', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周6收款 | gmv_6<br>`8466748058200069` | measure | sum(8466748058200069) |  |  | 收款分时间占比 |
| 周6占比 | 周6占比<br>`customized_989093204276752384` | custom_measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_6}) / sum(${gmv_t})<br>end |  | {'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200069', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周6单效 | 周6单效<br>`customized_989093204180283393` | custom_measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_6_z}) / sum(${v_lead_c})<br>end |  | {'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8648107429619717', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周7收款 | gmv_7<br>`8466748058200070` | measure | sum(8466748058200070) |  |  | 收款分时间占比 |
| 周7占比 | 周7占比<br>`customized_989093204465496065` | custom_measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_7}) / sum(${gmv_t})<br>end |  | {'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200070', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周7单效 | 周7单效<br>`customized_989093204373221377` | custom_measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_7_z}) / sum(${v_lead_c})<br>end |  | {'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8648107429619718', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周1收款 | gmv_1<br>`8466748058200064` | measure | sum(8466748058200064) |  |  | 收款分时间占比 |
| 周1占比 | 周1占比<br>`customized_989093203312062464` | custom_measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_1}) / sum(${gmv_t})<br>end |  | {'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200064', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周1单效 | 周1单效<br>`customized_989093203207204865` | custom_measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_1_z}) / sum(${v_lead_c})<br>end |  | {'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8648107429619712', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8625186871404544', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 当期净收款 | gmv_7<br>`8456155560699904` | measure | sum(8456155560699904) |  |  | 线索分时间转化数据 |
| 当期占比 | 当期收款占比<br>`customized_989093193027629056` | custom_measure | ifnull(sum(${gmv_7})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699904', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 8_14天内收款占比 | 14天内收款占比(不含当期)<br>`customized_989093192440426496` | custom_measure | ifnull(sum(${gmv_14})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699905', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 15_30天内净收款占比 | 30天内净收款占比(不含前14天)<br>`customized_989093192637558785` | custom_measure | ifnull(sum(${gmv_30})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699906', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 非30天内净收款占比 | 非30天内净收款占比<br>`customized_989093193224761345` | custom_measure | ifnull(sum(${gmv_n30})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699907', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 下期线索当期占比 | 下期线索当期占比<br>`customized_989093192834691072` | custom_measure | ifnull(sum(${gmv_7_h})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699908', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 净收款 | gmv_total<br>`8456155560699909` | measure | sum(8456155560699909) |  |  | 线索分时间转化数据 |
| 当期退款 | refund_7<br>`8456155560699910` | measure | sum(8456155560699910) |  |  | 线索分时间转化数据 |
| 当期退款占比 | 当期退款占比<br>`customized_989093193128292352` | custom_measure | ifnull(sum(${refund_7})/sum(${refund_total}),0) |  | {'paramId': '8456155560699910', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 8_14天内退款占比 | 14天内退款占比(不含当期)<br>`customized_989093192541089792` | custom_measure | ifnull(sum(${refund_14})/sum(${refund_total}),0) |  | {'paramId': '8456155560699911', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 15_30天内退款占比 | 30天内退款占比(不含前14天)<br>`customized_989093192734027776` | custom_measure | ifnull(sum(${refund_30})/sum(${refund_total}),0) |  | {'paramId': '8456155560699912', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 非30天内退款占比 | 非30天内退款占比<br>`customized_989093193321230336` | custom_measure | ifnull(sum(${refund_n30})/sum(${refund_total}),0) |  | {'paramId': '8456155560699913', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 下期线索当期退款占比 | 下期线索当期退款占比<br>`customized_989093192931160065` | custom_measure | ifnull(sum(${refund_7_p})/sum(${refund_total}),0) |  | {'paramId': '8456155560699914', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 总退款 | refund_total<br>`8456155560699915` | measure | sum(8456155560699915) |  |  | 线索分时间转化数据 |
| 退后线索 | lead<br>`8172915650029568` | measure | sum(8172915650029568) |  |  | 行课数据 |
| 课1 | 课1<br>`customized_989093179060596736` | custom_measure | sum(${ke_1})/sum(${lead}) |  | {'paramId': '8172915650029570', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课1有效 | 课1有效<br>`customized_989093179169648640` | custom_measure | sum(${v_ke_1})/sum(${lead}) |  | {'paramId': '8172915650029576', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课2 | 课2<br>`customized_989093179278700544` | custom_measure | sum(${ke_2})/sum(${lead}) |  | {'paramId': '8172915650029571', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课2有效 | 课2有效<br>`customized_989093179383558145` | custom_measure | sum(${v_ke_2})/sum(${lead}) |  | {'paramId': '8172915650029577', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课3 | 课3<br>`customized_989093179484221441` | custom_measure | sum(${ke_3})/sum(${lead}) |  | {'paramId': '8172915650029572', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课3有效 | 课3有效<br>`customized_989093179580690432` | custom_measure | sum(${v_ke_3})/sum(${lead}) |  | {'paramId': '8172915650029578', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课4 | 课4<br>`customized_989093179677159425` | custom_measure | sum(${ke_4})/sum(${lead}) |  | {'paramId': '8172915650029573', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课4有效 | 课4有效<br>`customized_989093179773628416` | custom_measure | sum(${v_ke_4})/sum(${lead}) |  | {'paramId': '8172915650029579', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课5 | 课5<br>`customized_989093179870097409` | custom_measure | sum(${ke_5})/sum(${lead}) |  | {'paramId': '8172915650029574', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课5有效 | 课5有效<br>`customized_989093179970760705` | custom_measure | sum(${v_ke_5})/sum(${lead}) |  | {'paramId': '8172915650029580', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课6 | 课6<br>`customized_989093180071424001` | custom_measure | sum(${ke_6})/sum(${lead}) |  | {'paramId': '8172915650029575', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课6有效 | 课6有效<br>`customized_989093180172087297` | custom_measure | sum(${v_ke_6})/sum(${lead}) |  | {'paramId': '8172915650029581', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 退前线索 | lead_count<br>`8465935477925888` | measure | sum(8465935477925888) |  |  | 外呼数据 |
| 退后线索 | valid_lead_count<br>`8103974494234625` | measure | sum(8103974494234625) |  |  | 外呼数据 |
| 总通时 | call_duration<br>`8103974494234632` | measure | sum(8103974494234632) |  |  | 外呼数据 |
| 6h外呼 | 6h外呼<br>`customized_989093183997292545` | custom_measure | ifnull(sum(${first_call_in_6h})/sum(${valid_lead_count}),0) |  | {'paramId': '8647934271842304', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 12h外呼 | 12h外呼<br>`customized_989093183405895680` | custom_measure | ifnull(sum(${first_call_in_12h})/sum(${valid_lead_count}),0) |  | {'paramId': '8647934271842305', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 24h外呼 | 24h外呼率<br>`customized_989093183510753281` | custom_measure | sum(${first_call_in_24h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234626', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 48h外呼 | 48h外呼率<br>`customized_989093183703691265` | custom_measure | sum(${first_call_in_48h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234627', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 48h沟通 | 48h沟通率<br>`customized_989093183804354561` | custom_measure | sum(${first_call_connected_in_48h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234630', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 外呼率 | 外呼率<br>`customized_989093184391557121` | custom_measure | ifnull(sum(${first_call_cnt})/sum(${valid_lead_count}),0) |  | {'paramId': '8103974494234628', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 沟通率 | 沟通率<br>`customized_989093184978759681` | custom_measure | ifnull(sum(${first_call_connected_cnt})/sum(${valid_lead_count}),0) |  | {'paramId': '8103974494234631', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 外呼频次 | 外呼频次<br>`customized_989093184488026112` | custom_measure | sum(${zong_call_ci})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234633', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 平均接通时长(min) | 平均接通时长(min)<br>`customized_989093184882290688` | custom_measure | sum(${call_duration})/sum(${call_status}) |  | {'paramId': '8103974494234632', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234634', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 外呼接通率 | 外呼接通率<br>`customized_989093184290893825` | custom_measure | sum(${call_status})/sum(${zong_call_ci}) |  | {'paramId': '8103974494234634', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234633', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 5min比例 | 5min比例<br>`customized_989093183900823552` | custom_measure | sum(${is_long_call})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234635', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 好友率 | 好友率<br>`customized_989093184584495105` | custom_measure | sum(${is_friend_lead})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234638', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| APP登录率 | APP登录率<br>`customized_989093184093761536` | custom_measure | sum(${is_app_denglu})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234639', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 深沟率 | 深沟率<br>`customized_989093185075228672` | custom_measure | sum(${is_shengou})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234640', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 双沟率 | 双沟率<br>`customized_989093184194424832` | custom_measure | sum(${is_shuanggou})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234641', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 已回收 | 已回收<br>`customized_989093184781627392` | custom_measure | ifnull(sum(${yi_huishou})/sum(${valid_lead_count}),0) |  | {'paramId': '8692525273278464', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
