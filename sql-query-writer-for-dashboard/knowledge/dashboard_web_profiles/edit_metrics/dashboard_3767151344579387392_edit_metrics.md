# 转化数据 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3767151344579387392`
- dashboard_name: `转化数据`
- captured_at: `2026-06-24 19:29:05`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3767151344579387392&htmlId=html_3959901854956204032`
- loaded_html_id: `html_3959901854956204032`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3767151344579387392_edit_metrics_profile.json`
- pivot_units: `9`
- configured_fields: `346`
- measures: `322`
- custom_formulas: `221`
- text_notes: `0`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2253` | 转化数据_市场顾问 | [data_center_market_2253_20260628.sql](../../../resources/raw_sql/data_center_market_2253_20260628.sql) | 9 |

## Pivot units

### 渠道-部门-转化

- unit_id: `unit_3769948772219289601`
- unit_type: `u_pivot`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 部门 / `depart`; 年级 / `grade_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价

### 渠道-主管-转化_副本

- unit_id: `unit_3923523375308914691`
- unit_type: `u_pivot`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 经理 / `jingli`; 年级 / `grade_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价

### 渠道-主管-转化

- unit_id: `unit_3770180547675414537`
- unit_type: `u_pivot`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价

### 渠道-顾问-转化

- unit_id: `unit_3770181969476136976`
- unit_type: `u_pivot`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 经理 / `jingli`; 主管 / `xiaozu`; 顾问 / `employee_email_name`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度

### 渠道-部门

- unit_id: `unit_3770178971070095368`
- unit_type: `u_pivot`
- model: `2253` / 转化数据_市场顾问
- dimensions: 渠道 / `channel_map`; 年级 / `grade_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 市场线索 / `xiansuo`; 市场单效; 市场净收; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); 当期ltv; gmv(当) / `xb_trade_profit`; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价

### 部门--转化

- unit_id: `unit_3769950646823006217`
- unit_type: `u_pivot`
- model: `2253` / 转化数据_市场顾问
- dimensions: 部门 / `depart`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价

### 经理--转化

- unit_id: `unit_3770133595114242055`
- unit_type: `u_pivot`
- model: `2253` / 转化数据_市场顾问
- dimensions: 经理 / `jingli_1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价

### 主管--转化

- unit_id: `unit_3768315793457872897`
- unit_type: `u_pivot`
- model: `2253` / 转化数据_市场顾问
- dimensions: 经理 / `jingli`; 主管 / `xiaozu`; channel_map
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); gmv(当) / `xb_trade_profit`; 当期ltv; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价

### 部门-个人

- unit_id: `unit_3912232685751894018`
- unit_type: `u_pivot`
- model: `2253` / 转化数据_市场顾问
- dimensions: 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `name1`
- measures: 接量人力; 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 市场线索 / `xiansuo`; 市场单效; 市场净收; 线索留存; 人头(当) / `pay_users_on_period`; 人头转化(当) / `当期人头转化率`; 订单(当) / `pay_user_subs_on_period`; 订单转化(当) / `当期订单转化率`; 联报人次(当) / `pay_user_subs_joint_onp`; 联报率(当) / `当期联报率`; 拓课率(当); 当期ltv; gmv(当) / `xb_trade_profit`; 退款(当); 退费率(当); 人头 / `pay_users`; 人头转化 / `人头`; 订单 / `pay_user_subs`; 订单转化; 联报人次 / `pay_user_subs_joint`; 联报率; 拓课率 / `人均报科`; 截面gmv / `trade_profit`; 截面ltv; 退费金额 / `trade_refund`; 退费率; 单效(例会) / `单效`; gmv目标; gmv完成度; 人均产能; M成本; ROI; smROI; 破蛋率; 课单价; 客单价

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 接量人力 | 接量人力<br>`customized_983500441281945600` | custom_measure | count(distinct ${name1})-1 |  | {'paramId': '312977', 'orgParamType': 2, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 退前线索 | lead_count<br>`8495554035410944` | measure | sum(8495554035410944) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 退后线索 | can_renew_ds_count_a<br>`8246056497866753` | measure | sum(8246056497866753) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 线索留存 | 线索留存<br>`customized_983500443177771008` | custom_measure | ifnull(sum(${can_renew_ds_count_a})/sum(${lead_count}),0) |  | {'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8495554035410944', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 人头(当) | pay_users_on_period<br>`8246056497866755` | measure | sum(8246056497866755) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 人头转化(当) | 当期人头转化率<br>`customized_983500442510876673` | custom_measure | ifnull(sum(${pay_users_on_period})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8246056497866755', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 订单(当) | pay_user_subs_on_period<br>`8246056497866758` | measure | sum(8246056497866758) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 订单转化(当) | 当期订单转化率<br>`customized_983500442733174784` | custom_measure | ifnull(sum(${pay_user_subs_on_period})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8246056497866758', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 联报人次(当) | pay_user_subs_joint_onp<br>`8246056497866761` | measure | sum(8246056497866761) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 联报率(当) | 当期联报率<br>`customized_983500442619928577` | custom_measure | ifnull(sum(${pay_user_subs_joint_onp})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8246056497866761', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 拓课率(当) | 拓课率(当)<br>`customized_983500442951278592` | custom_measure | ifnull(sum(${pay_user_subs_on_period})/sum(${pay_users_on_period}),0) |  | {'paramId': '8246056497866758', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866755', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| gmv(当) | xb_trade_profit<br>`8330318168483840` | measure | sum(8330318168483840) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 当期ltv | 当期ltv<br>`customized_983500442401824769` | custom_measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8330318168483840', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 退款(当) | 退款(当)<br>`customized_983500443622367232` | custom_measure | sum(${xb_trade_income})-sum(${xb_trade_profit}) |  | {'paramId': '8246056497866766', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8330318168483840', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 退费率(当) | 退费率(当)<br>`customized_983500443844665345` | custom_measure | ifnull(${退款(当)}/sum(${xb_trade_income}),0) |  | {'paramId': 'customized_983500443622367232', 'orgParamType': 4, 'needBoundaryValue': False}<br>{'paramId': '8246056497866766', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 人头 | pay_users<br>`8246056497866754` | measure | sum(8246056497866754) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 人头转化 | 人头<br>`customized_983500441730736129` | custom_measure | sum(${pay_users})/sum(${can_renew_ds_count_a}) |  | {'paramId': '8246056497866754', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 订单 | pay_user_subs<br>`8246056497866757` | measure | sum(8246056497866757) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 订单转化 | 订单转化<br>`customized_983500443404263424` | custom_measure | ifnull(sum(${pay_user_subs})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8246056497866757', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 联报人次 | pay_user_subs_joint<br>`8246056497866760` | measure | sum(8246056497866760) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 联报率 | 联报率<br>`customized_983500443286822912` | custom_measure | ifnull(sum(${pay_user_subs_joint})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8246056497866760', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 拓课率 | 人均报科<br>`customized_983500441621684225` | custom_measure | ifnull(sum(${pay_user_subs})/sum(${pay_users}),0) |  | {'paramId': '8246056497866757', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866754', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 截面gmv | trade_profit<br>`8246056497866765` | measure | sum(8246056497866765) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 截面ltv | 截面ltv<br>`customized_983500442842226688` | custom_measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | {'paramId': '8246056497866765', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 退费金额 | trade_refund<br>`8246056497866764` | measure | sum(8246056497866764) |  |  | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 退费率 | 退费率<br>`customized_983500443735613441` | custom_measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | {'paramId': '8246056497866764', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866763', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 单效(例会) | 单效<br>`customized_983500441839788033` | custom_measure | ifnull(sum(${trade_profit})/sum(${lead_count}),0) |  | {'paramId': '8246056497866765', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8495554035410944', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| gmv目标 | gmv目标<br>`customized_983500440824766465` | custom_measure | sum(${s_lead}*${gl_gl}) |  | {'paramId': '8256669137135616', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '312828', 'orgParamType': 2, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| gmv完成度 | gmv完成度<br>`customized_983500440938012672` | custom_measure | sum(${trade_profit})/${gmv目标} |  | {'paramId': '8246056497866765', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_983500440824766465', 'orgParamType': 4, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-顾问-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 人均产能 | 人均产能<br>`customized_983500441508438016` | custom_measure | ifnull(sum(${trade_profit})/${接量人力},0) |  | {'paramId': '8246056497866765', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_983500441281945600', 'orgParamType': 4, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| M成本 | M成本<br>`customized_983500441055453184` | custom_measure | sum(${can_renew_ds_count_a}*${cb_cb}) |  | {'paramId': '8246056497866753', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '312827', 'orgParamType': 2, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| ROI | ROI<br>`customized_983500441168699393` | custom_measure | sum(${trade_profit})/${M成本} |  | {'paramId': '8246056497866765', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_983500441055453184', 'orgParamType': 4, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| smROI | smROI<br>`customized_983500441390997504` | custom_measure | sum(${trade_profit})/(${M成本}+${接量人力}*3000) |  | {'paramId': '8246056497866765', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_983500441055453184', 'orgParamType': 4, 'needBoundaryValue': False}<br>{'paramId': 'customized_983500441281945600', 'orgParamType': 4, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 破蛋率 | 破蛋率<br>`customized_983500443060330496` | custom_measure | ifnull(sum(${podan})/${接量人力},0) |  | {'paramId': '8256417855072256', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_983500441281945600', 'orgParamType': 4, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 课单价 | 课单价<br>`customized_983500443513315328` | custom_measure | ifnull(sum(${trade_profit})/sum(${pay_user_subs}),0) |  | {'paramId': '8246056497866765', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866757', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 客单价 | 客单价<br>`customized_983500442062086144` | custom_measure | ifnull(sum(${trade_profit})/sum(${pay_users}),0) |  | {'paramId': '8246056497866765', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8246056497866754', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门-转化<br>渠道-主管-转化_副本<br>渠道-主管-转化<br>渠道-部门<br>部门--转化<br>经理--转化<br>主管--转化<br>部门-个人 |
| 市场线索 | xiansuo<br>`8812529818298368` | measure | sum(8812529818298368) |  |  | 渠道-部门<br>部门-个人 |
| 市场单效 | 市场单效<br>`customized_983500442284384257` | custom_measure | ifnull(${市场净收}/sum(${xiansuo}),0) |  | {'paramId': 'customized_983500442171138048', 'orgParamType': 4, 'needBoundaryValue': False}<br>{'paramId': '8812529818298368', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门<br>部门-个人 |
| 市场净收 | 市场净收<br>`customized_983500442171138048` | custom_measure | ifnull(sum(${pp_pmit})+sum(${ww_pmit}),0) |  | {'paramId': '8732188523915264', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8732188523915265', 'orgParamType': 1, 'needBoundaryValue': False} | 渠道-部门<br>部门-个人 |
