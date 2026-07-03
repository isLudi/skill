# 11老板_运营侧数据看板 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3833805337379700736`
- dashboard_name: `11老板_运营侧数据看板`
- captured_at: `2026-06-24 19:31:52`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3833805337379700736&htmlId=html_3959904579167150081`
- loaded_html_id: `html_3959904579167150081`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3833805337379700736_edit_metrics_profile.json`
- pivot_units: `14`
- configured_fields: `277`
- measures: `198`
- custom_formulas: `144`
- text_notes: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2345` | 进量测试(市场渠道) | [data_center_market_2345_20260624.sql](../../../resources/raw_sql/data_center_market_2345_20260624.sql) | 1 |
| `2293` | 运营侧个人数据 | [data_center_market_2293_20260703.sql](../../../resources/raw_sql/data_center_market_2293_20260703.sql) | 9 |
| `2424` | 每日转化数据表 | [data_center_market_2424_20260624.sql](../../../resources/raw_sql/data_center_market_2424_20260624.sql) | 1 |
| `2344` | 分析--分周期转化 | [data_center_market_2344_20260624.sql](../../../resources/raw_sql/data_center_market_2344_20260624.sql) | 1 |
| `2132` | (内部)到课衰减情况 | [data_center_market_2132_20260628.sql](../../../resources/raw_sql/data_center_market_2132_20260628.sql) | 1 |
| `2054` | (内部渠道)外呼过程数据 | [data_center_market_2054_20260624.sql](../../../resources/raw_sql/data_center_market_2054_20260624.sql) | 1 |

## Pivot units

### 进量_转化分析

- unit_id: `unit_3833805476815142964`
- unit_type: `u_pivot`
- model: `2345` / 进量测试(市场渠道)
- dimensions: 分配日期 / `assign_day_new`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 24h外呼 / `24h外呼率`; 48h外呼 / `48h外呼率`; 5min; 好友 / `好友率`; APP; 深沟 / `深沟率`; 课1; 课1有效; 当期单效; 截面单效

### 经理

- unit_id: `unit_3833805476815142920`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 年级 / `grade_1`
- measures: 退后线索 / `can_renew_ds_count_a`; 接量人力; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效

### 主管

- unit_id: `unit_3833805476815142958`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `zhuguan`; 年级 / `grade_1`
- measures: 退后线索 / `can_renew_ds_count_a`; 接量人力; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人头转化; 订单转化; 人均报科; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效

### 个人

- unit_id: `unit_3833805476815142959`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; 年级 / `grade_1`
- measures: 退后线索 / `can_renew_ds_count_a`; 接量人力; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效

### KOC自孵化

- unit_id: `unit_3833805476815142941`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率

### 春春

- unit_id: `unit_3833805476815142926`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率

### 亚飞

- unit_id: `unit_3833805476815142925`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率

### 曹忆

- unit_id: `unit_3833805476815142939`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `zhuguan`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率

### 肖晗IP

- unit_id: `unit_3833805476815142953`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `zhuguan`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率

### 周帅IP

- unit_id: `unit_3833805476815142976`
- unit_type: `u_pivot`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; channel_map
- measures: 退后线索 / `can_renew_ds_count_a`; 好友率; 深沟率; 首节到课; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率

### 收款分时间占比

- unit_id: `unit_3833805476815142977`
- unit_type: `u_pivot`
- model: `2424` / 每日转化数据表
- dimensions: 期次 / `qici`; 渠道 / `channel_1`
- measures: 总净收 / `gmv_t`; 周2收款 / `gmv_2`; 周2占比; 周3收款 / `gmv_3`; 周3占比; 周4收款 / `gmv_4`; 周4占比; 周5收款 / `gmv_5`; 周5占比; 周6收款 / `gmv_6`; 周6占比; 周7收款 / `gmv_7`; 周7占比; 周1收款 / `gmv_1`; 周1占比

### 线索分时间转化数据

- unit_id: `unit_3833805476815142960`
- unit_type: `u_pivot`
- model: `2344` / 分析--分周期转化
- dimensions: 期次 / `qici`; 渠道 / `channel_1`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_list`; 顾问 / `name`; qici; grade_list; channel_1
- measures: 当期净收款 / `gmv_7`; 当期占比 / `当期收款占比`; 8_14天内收款占比 / `14天内收款占比(不含当期)`; 15_30天内净收款占比 / `30天内净收款占比(不含前14天)`; 非30天内净收款占比; 下期线索当期占比; 净收款 / `gmv_total`; 当期退款 / `refund_7`; 当期退款占比; 8_14天内退款占比 / `14天内退款占比(不含当期)`; 15_30天内退款占比 / `30天内退款占比(不含前14天)`; 非30天内退款占比; 下期线索当期退款占比; 总退款 / `refund_total`

### 行课数据

- unit_id: `unit_3833805476815142946`
- unit_type: `u_pivot`
- model: `2132` / (内部)到课衰减情况
- dimensions: 期 / `qici`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; qici; department; grade_1; channel_map_1; rule_name
- measures: 退后线索 / `lead`; 课1; 课1有效; 课2; 课2有效; 课3; 课3有效; 课4; 课4有效; 课5; 课5有效; 课6; 课6有效

### 外呼数据

- unit_id: `unit_3833805476815142947`
- unit_type: `u_pivot`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 期次 / `qici`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; qici; department; grade_1; channel_map_1
- measures: 退前线索 / `lead_count`; 退后线索 / `valid_lead_count`; 总通时 / `call_duration`; 首call; 24h外呼率; 24h沟通率; 48h外呼率; 48h沟通率; 外呼率; 沟通率; 外呼频次; 平均接通时长(min); 外呼接通率; 5min比例; 好友率; APP登录率; 深沟率; 双沟率

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 退前线索 | lead_count<br>`8590324328392704` | measure | sum(8590324328392704) |  |  | 进量_转化分析 |
| 退后线索 | can_renew_ds_count_a<br>`8387973858551809` | measure | sum(8387973858551809) |  |  | 进量_转化分析 |
| 24h外呼 | 24h外呼率<br>`customized_975473879651495937` | custom_measure | ifnull(sum(${first_call_24h})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8388293899741184', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 48h外呼 | 48h外呼率<br>`customized_975473879764742144` | custom_measure | ifnull(sum(${first_call_48h})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8388293899741185', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 5min | 5min<br>`customized_975473879869599745` | custom_measure | ifnull(sum(${long_call_5})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8392152286717952', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 好友 | 好友率<br>`customized_975473880079314945` | custom_measure | ifnull(sum(${friend_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551810', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| APP | APP<br>`customized_975473879974457344` | custom_measure | ifnull(sum(${app_denglu})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8392152286717953', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 深沟 | 深沟率<br>`customized_975473880494551040` | custom_measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551811', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 课1 | 课1<br>`customized_975473880603602944` | custom_measure | ifnull(sum(${daoke_1})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551814', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 课1有效 | 课1有效<br>`customized_975473880708460545` | custom_measure | ifnull(sum(${daoke_v1})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8392152286717954', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 当期单效 | 当期单效<br>`customized_975473880188366849` | custom_measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551828', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 截面单效 | 截面单效<br>`customized_975473880289030145` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8387973858551826', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8387973858551809', 'orgParamType': 1, 'needBoundaryValue': False} | 进量_转化分析 |
| 退后线索 | can_renew_ds_count_a<br>`8337294278879233` | measure | sum(8337294278879233) |  |  | 经理<br>主管<br>个人<br>KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 接量人力 | 接量人力<br>`customized_975473862391934976` | custom_measure | count(DISTINCT${employee_email_name})-1 |  | {'paramId': '319197', 'orgParamType': 2, 'needBoundaryValue': False} | 经理<br>主管<br>个人 |
| 人头转化(当期) | 人头(当期)<br>`customized_975473861750206465` | custom_measure | ifnull(sum(${pay_users_on_period})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879239', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 订单转化(当期) | 订单转化(当期)<br>`customized_975473862811365376` | custom_measure | ifnull(sum(${pay_user_subs_on_period})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879242', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人 |
| 总收款(当期) | xb_trade_income<br>`8337294278879250` | measure | sum(8337294278879250) |  |  | 经理<br>主管<br>个人 |
| 退款(当期) | 退款(当期)<br>`customized_975473862941388801` | custom_measure | ifnull(sum(${xb_trade_income})-sum(${xb_trade_profit}),0) |  | {'paramId': '8337294278879250', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879251', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人 |
| 净收款(当期) | xb_trade_profit<br>`8337294278879251` | measure | sum(8337294278879251) |  |  | 经理<br>主管<br>个人 |
| 退费率(当期) | 退费率(当期)<br>`customized_975473863046246400` | custom_measure | ifnull(${退款(当期)}/sum(${xb_trade_income}),0) |  | {'paramId': 'customized_975473862941388801', 'orgParamType': 4, 'needBoundaryValue': False}<br>{'paramId': '8337294278879250', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人 |
| 单效(当期) | 单效(当期)<br>`customized_975473862068973569` | custom_measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879251', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 破蛋率 | 破蛋率<br>`customized_975473862605844481` | custom_measure | ifnull(sum(${podan})/${接量人力},0) |  | {'paramId': '8337294278879255', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_975473862391934976', 'orgParamType': 4, 'needBoundaryValue': False} | 经理<br>主管<br>个人 |
| 人均报科 | 人均报科<br>`customized_975473861641154561` | custom_measure | ifnull(sum(${pay_user_subs})/sum(${pay_users}),0) |  | {'paramId': '8337294278879241', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879238', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 人头转化 | 人头转化<br>`customized_975473861863452672` | custom_measure | ifnull(sum(${pay_users})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879238', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 订单转化 | 订单转化<br>`customized_975473862706507777` | custom_measure | ifnull(sum(${pay_user_subs})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879241', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人 |
| 总收款 | trade_income<br>`8337294278879247` | measure | sum(8337294278879247) |  |  | 经理<br>主管<br>个人 |
| 退款 | trade_refund<br>`8337294278879248` | measure | sum(8337294278879248) |  |  | 经理<br>主管<br>个人 |
| 净收款 | trade_profit<br>`8337294278879249` | measure | sum(8337294278879249) |  |  | 经理<br>主管<br>个人 |
| 退费率 | 截面退费率<br>`customized_975473862287077377` | custom_measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | {'paramId': '8337294278879248', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879247', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人 |
| 单效 | 单效<br>`customized_975473861968310273` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8337294278879249', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | 经理<br>主管<br>个人<br>KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 好友率 | 好友率<br>`customized_975473862182219776` | custom_measure | sum(${friend_lead})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8337294278879234', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 深沟率 | 深沟率<br>`customized_975473862500986880` | custom_measure | sum(${shengou_lead})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8337294278879235', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 首节到课 | 首节到课<br>`customized_975473863155298304` | custom_measure | sum(${daoke_1})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8337294278879237', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879233', 'orgParamType': 1, 'needBoundaryValue': False} | KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 收款(当期) | xb_trade_income<br>`8337294278879250` | measure | sum(8337294278879250) |  |  | KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 收款 | trade_income<br>`8337294278879247` | measure | sum(8337294278879247) |  |  | KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 截面退费率 | 截面退费率<br>`customized_975473862287077377` | custom_measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | {'paramId': '8337294278879248', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8337294278879247', 'orgParamType': 1, 'needBoundaryValue': False} | KOC自孵化<br>春春<br>亚飞<br>曹忆<br>肖晗IP<br>周帅IP |
| 总净收 | gmv_t<br>`8466748058200071` | measure | sum(8466748058200071) |  |  | 收款分时间占比 |
| 周2收款 | gmv_2<br>`8466748058200065` | measure | sum(8466748058200065) |  |  | 收款分时间占比 |
| 周2占比 | 周2占比<br>`customized_975473885477384192` | custom_measure | ifnull(sum(${gmv_2})/sum(${gmv_t}),0) |  | {'paramId': '8466748058200065', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周3收款 | gmv_3<br>`8466748058200066` | measure | sum(8466748058200066) |  |  | 收款分时间占比 |
| 周3占比 | 周3占比<br>`customized_975473885590630401` | custom_measure | ifnull(sum(${gmv_3})/sum(${gmv_t}),0) |  | {'paramId': '8466748058200066', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周4收款 | gmv_4<br>`8466748058200067` | measure | sum(8466748058200067) |  |  | 收款分时间占比 |
| 周4占比 | 周4占比<br>`customized_975473885703876608` | custom_measure | ifnull(sum(${gmv_4})/sum(${gmv_t}),0) |  | {'paramId': '8466748058200067', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周5收款 | gmv_5<br>`8466748058200068` | measure | sum(8466748058200068) |  |  | 收款分时间占比 |
| 周5占比 | 周5占比<br>`customized_975473885808734209` | custom_measure | ifnull(sum(${gmv_5})/sum(${gmv_t}),0) |  | {'paramId': '8466748058200068', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周6收款 | gmv_6<br>`8466748058200069` | measure | sum(8466748058200069) |  |  | 收款分时间占比 |
| 周6占比 | 周6占比<br>`customized_975473885913591808` | custom_measure | ifnull(sum(${gmv_6})/sum(${gmv_t}),0) |  | {'paramId': '8466748058200069', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周7收款 | gmv_7<br>`8466748058200070` | measure | sum(8466748058200070) |  |  | 收款分时间占比 |
| 周7占比 | 周7占比<br>`customized_975473886018449409` | custom_measure | ifnull(sum(${gmv_7})/sum(${gmv_t}),0) |  | {'paramId': '8466748058200070', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 周1收款 | gmv_1<br>`8466748058200064` | measure | sum(8466748058200064) |  |  | 收款分时间占比 |
| 周1占比 | 周1占比<br>`customized_975473885359943680` | custom_measure | ifnull(sum(${gmv_1})/sum(${gmv_t}),0) |  | {'paramId': '8466748058200064', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8466748058200071', 'orgParamType': 1, 'needBoundaryValue': False} | 收款分时间占比 |
| 当期净收款 | gmv_7<br>`8456155560699904` | measure | sum(8456155560699904) |  |  | 线索分时间转化数据 |
| 当期占比 | 当期收款占比<br>`customized_975473876925198337` | custom_measure | ifnull(sum(${gmv_7})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699904', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 8_14天内收款占比 | 14天内收款占比(不含当期)<br>`customized_975473876296052737` | custom_measure | ifnull(sum(${gmv_14})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699905', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 15_30天内净收款占比 | 30天内净收款占比(不含前14天)<br>`customized_975473876505767937` | custom_measure | ifnull(sum(${gmv_30})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699906', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 非30天内净收款占比 | 非30天内净收款占比<br>`customized_975473877139107840` | custom_measure | ifnull(sum(${gmv_n30})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699907', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 下期线索当期占比 | 下期线索当期占比<br>`customized_975473876715483137` | custom_measure | ifnull(sum(${gmv_7_h})/sum(${gmv_total}),0) |  | {'paramId': '8456155560699908', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699909', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 净收款 | gmv_total<br>`8456155560699909` | measure | sum(8456155560699909) |  |  | 线索分时间转化数据 |
| 当期退款 | refund_7<br>`8456155560699910` | measure | sum(8456155560699910) |  |  | 线索分时间转化数据 |
| 当期退款占比 | 当期退款占比<br>`customized_975473877030055936` | custom_measure | ifnull(sum(${refund_7})/sum(${refund_total}),0) |  | {'paramId': '8456155560699910', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 8_14天内退款占比 | 14天内退款占比(不含当期)<br>`customized_975473876405104641` | custom_measure | ifnull(sum(${refund_14})/sum(${refund_total}),0) |  | {'paramId': '8456155560699911', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 15_30天内退款占比 | 30天内退款占比(不含前14天)<br>`customized_975473876610625536` | custom_measure | ifnull(sum(${refund_30})/sum(${refund_total}),0) |  | {'paramId': '8456155560699912', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 非30天内退款占比 | 非30天内退款占比<br>`customized_975473877256548352` | custom_measure | ifnull(sum(${refund_n30})/sum(${refund_total}),0) |  | {'paramId': '8456155560699913', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 下期线索当期退款占比 | 下期线索当期退款占比<br>`customized_975473876820340736` | custom_measure | ifnull(sum(${refund_7_p})/sum(${refund_total}),0) |  | {'paramId': '8456155560699914', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8456155560699915', 'orgParamType': 1, 'needBoundaryValue': False} | 线索分时间转化数据 |
| 总退款 | refund_total<br>`8456155560699915` | measure | sum(8456155560699915) |  |  | 线索分时间转化数据 |
| 退后线索 | lead<br>`8172915650029568` | measure | sum(8172915650029568) |  |  | 行课数据 |
| 课1 | 课1<br>`customized_975473865533468673` | custom_measure | sum(${ke_1})/sum(${lead}) |  | {'paramId': '8172915650029570', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课1有效 | 课1有效<br>`customized_975473865638326272` | custom_measure | sum(${v_ke_1})/sum(${lead}) |  | {'paramId': '8172915650029576', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课2 | 课2<br>`customized_975473865743183873` | custom_measure | sum(${ke_2})/sum(${lead}) |  | {'paramId': '8172915650029571', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课2有效 | 课2有效<br>`customized_975473865843847169` | custom_measure | sum(${v_ke_2})/sum(${lead}) |  | {'paramId': '8172915650029577', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课3 | 课3<br>`customized_975473865948704768` | custom_measure | sum(${ke_3})/sum(${lead}) |  | {'paramId': '8172915650029572', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课3有效 | 课3有效<br>`customized_975473866053562369` | custom_measure | sum(${v_ke_3})/sum(${lead}) |  | {'paramId': '8172915650029578', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课4 | 课4<br>`customized_975473866158419968` | custom_measure | sum(${ke_4})/sum(${lead}) |  | {'paramId': '8172915650029573', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课4有效 | 课4有效<br>`customized_975473866263277569` | custom_measure | sum(${v_ke_4})/sum(${lead}) |  | {'paramId': '8172915650029579', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课5 | 课5<br>`customized_975473866368135168` | custom_measure | sum(${ke_5})/sum(${lead}) |  | {'paramId': '8172915650029574', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课5有效 | 课5有效<br>`customized_975473866472992769` | custom_measure | sum(${v_ke_5})/sum(${lead}) |  | {'paramId': '8172915650029580', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课6 | 课6<br>`customized_975473866577850368` | custom_measure | sum(${ke_6})/sum(${lead}) |  | {'paramId': '8172915650029575', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 课6有效 | 课6有效<br>`customized_975473866678513664` | custom_measure | sum(${v_ke_6})/sum(${lead}) |  | {'paramId': '8172915650029581', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8172915650029568', 'orgParamType': 1, 'needBoundaryValue': False} | 行课数据 |
| 退前线索 | lead_count<br>`8465935477925888` | measure | sum(8465935477925888) |  |  | 外呼数据 |
| 退后线索 | valid_lead_count<br>`8103974494234625` | measure | sum(8103974494234625) |  |  | 外呼数据 |
| 总通时 | call_duration<br>`8103974494234632` | measure | sum(8103974494234632) |  |  | 外呼数据 |
| 首call | 首call<br>`customized_975473870554050560` | custom_measure | ifnull(sum(${is_f_call})/sum(${valid_lead_count}),0) |  | {'paramId': '8432582790834176', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 24h外呼率 | 24h外呼率<br>`customized_975473869077655552` | custom_measure | sum(${first_call_in_24h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234626', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 24h沟通率 | 24h沟通率<br>`customized_975473869190901761` | custom_measure | sum(${first_call_connected_in_24h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234629', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 48h外呼率 | 48h外呼率<br>`customized_975473869291565057` | custom_measure | sum(${first_call_in_48h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234627', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 48h沟通率 | 48h沟通率<br>`customized_975473869396422656` | custom_measure | sum(${first_call_connected_in_48h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234630', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 外呼率 | 外呼率<br>`customized_975473869916516352` | custom_measure | ifnull(sum(${first_call_cnt})/sum(${valid_lead_count}),0) |  | {'paramId': '8103974494234628', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 沟通率 | 沟通率<br>`customized_975473870340141057` | custom_measure | ifnull(sum(${first_call_connected_cnt})/sum(${valid_lead_count}),0) |  | {'paramId': '8103974494234631', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 外呼频次 | 外呼频次<br>`customized_975473870017179648` | custom_measure | sum(${zong_call_ci})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234633', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 平均接通时长(min) | 平均接通时长(min)<br>`customized_975473870235283456` | custom_measure | sum(${call_duration})/sum(${call_status}) |  | {'paramId': '8103974494234632', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234634', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 外呼接通率 | 外呼接通率<br>`customized_975473869811658753` | custom_measure | sum(${call_status})/sum(${zong_call_ci}) |  | {'paramId': '8103974494234634', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234633', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 5min比例 | 5min比例<br>`customized_975473869505474560` | custom_measure | sum(${is_long_call})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234635', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 好友率 | 好友率<br>`customized_975473870126231552` | custom_measure | sum(${is_friend_lead})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234638', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| APP登录率 | APP登录率<br>`customized_975473869606137856` | custom_measure | sum(${is_app_denglu})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234639', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 深沟率 | 深沟率<br>`customized_975473870444998656` | custom_measure | sum(${is_shengou})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234640', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
| 双沟率 | 双沟率<br>`customized_975473869706801152` | custom_measure | sum(${is_shuanggou})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234641', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 外呼数据 |
