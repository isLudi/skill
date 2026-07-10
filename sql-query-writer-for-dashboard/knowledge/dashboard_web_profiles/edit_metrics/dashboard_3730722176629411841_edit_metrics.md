# 外呼过程数据看板 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3730722176629411841`
- dashboard_name: `外呼过程数据看板`
- captured_at: `2026-06-24 19:28:17`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3730722176629411841&htmlId=html_3959901080852160513`
- loaded_html_id: `html_3959901080852160513`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3730722176629411841_edit_metrics_profile.json`
- pivot_units: `3`
- configured_fields: `78`
- measures: `65`
- custom_formulas: `58`
- text_notes: `2`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `2054` | (内部渠道)外呼过程数据 | [data_center_market_2054_20260705.sql](../../../resources/raw_sql/data_center_market_2054_20260705.sql) | 3 |

## Text units

- `unit_3798773484699615233`: 各项指标说明请点击文档： 外呼指标说明文档 <br>总筛选后所有板块数据均被筛选；每天整点-整点15表格抽数随机刷新，报表渲染会慢
- `unit_3798773484699615233`: 各项指标说明请点击文档： 外呼指标说明文档 <br>总筛选后所有板块数据均被筛选；整点-整点15表格抽数随机刷新，报表渲染会慢

## Pivot units

### 总体数据

- unit_id: `unit_3730781607175761920`
- unit_type: `u_pivot`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 经理 / `jingli`; 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`
- measures: 人力 / `接量人力`; 退前线索 / `lead_count`; 退后线索 / `valid_lead_count`; 总通时 / `call_duration`; 通时(例均) / `平均通时(例子)`; 通时(人均) / `平均通时(人均)`; 首call; 5min外呼 / `5min外呼率`; 6h外呼 / `6h外呼率`; 12h外呼 / `12h外呼率`; 24h外呼 / `24h外呼率`; 48h外呼 / `48h外呼率`; 24h沟通 / `24h沟通率`; 48h沟通 / `48h沟通率`; 外呼频次; 平均接通时长(min) / `平均接通时长`; 等待时长(h) / `等待时长`; 外呼接通 / `外呼接通率`; 5min比例; 好友 / `好友率`; APP登陆 / `APP登陆率`; 异常; 深沟 / `深沟率`; 双沟 / `双沟率`; 已回收; 首节到课 / `首节到课率`; 首节有效 / `首节有效率`

### 主管维度

- unit_id: `unit_3798743671868997638`
- unit_type: `u_pivot`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `xiaozu`
- measures: 接量人力; 有效例子 / `valid_lead_count`; 例子总通时 / `call_duration`; 平均通时(例子); 平均通时(人均); 24h外呼率; 48h外呼率; 24h沟通率; 48h沟通率; 外呼频次; 平均接通时长(min) / `平均接通时长`; 等待时长(h) / `等待时长`; 外呼接通率; 5min比例; 好友率; APP登陆率; 深沟率; 双沟率; 首节到课率; 首节有效率

### 个人维度

- unit_id: `unit_3798745287165575173`
- unit_type: `u_pivot`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`
- measures: 有效例子 / `valid_lead_count`; 例子总通时 / `call_duration`; 平均通时(例子); 24h外呼率; 48h外呼率; 24h沟通率; 48h沟通率; 外呼频次; 平均接通时长(min) / `平均接通时长`; 等待时长(h) / `等待时长`; 外呼接通率; 5min比例; 好友率; APP登陆率; 深沟率; 双沟率; 首节到课率; 首节有效率

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 人力 | 接量人力<br>`customized_987830636118806528` | custom_measure | count(DISTINCT ${employee_email_name}) |  | {'paramId': '273598', 'orgParamType': 2, 'needBoundaryValue': False} | 总体数据 |
| 退前线索 | lead_count<br>`8465935477925888` | measure | sum(8465935477925888) |  |  | 总体数据 |
| 退后线索 | valid_lead_count<br>`8103974494234625` | measure | sum(8103974494234625) |  |  | 总体数据 |
| 总通时 | call_duration<br>`8103974494234632` | measure | sum(8103974494234632) |  |  | 总体数据 |
| 通时(例均) | 平均通时(例子)<br>`customized_987830636328521728` | custom_measure | sum(${call_duration})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234632', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 通时(人均) | 平均通时(人均)<br>`customized_987830636223664129` | custom_measure | sum(${call_duration})/${接量人力} |  | {'paramId': '8103974494234632', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_987830636118806528', 'orgParamType': 4, 'needBoundaryValue': False} | 总体数据 |
| 首call | 首call<br>`customized_987830636852809729` | custom_measure | ifnull(sum(${is_f_call})/sum(${valid_lead_count}),0) |  | {'paramId': '8432582790834176', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 5min外呼 | 5min外呼率<br>`customized_987830634847932417` | custom_measure | ifnull(sum(${first_call_in_5min})/sum(${valid_lead_count}),0) |  | {'paramId': '8805620408543232', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 6h外呼 | 6h外呼率<br>`customized_987830635061841920` | custom_measure | ifnull(sum(${first_call_in_6h})/sum(${valid_lead_count}),0) |  | {'paramId': '8647934271842304', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 12h外呼 | 12h外呼率<br>`customized_987830634315255808` | custom_measure | ifnull(sum(${first_call_in_12h})/sum(${valid_lead_count}),0) |  | {'paramId': '8647934271842305', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 24h外呼 | 24h外呼率<br>`customized_987830634424307712` | custom_measure | sum(${first_call_in_24h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234626', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 48h外呼 | 48h外呼率<br>`customized_987830634638217217` | custom_measure | sum(${first_call_in_48h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234627', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 24h沟通 | 24h沟通率<br>`customized_987830634529165313` | custom_measure | sum(${first_call_connected_in_24h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234629', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 48h沟通 | 48h沟通率<br>`customized_987830634743074816` | custom_measure | sum(${first_call_connected_in_48h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234630', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 外呼频次 | 外呼频次<br>`customized_987830635485466625` | custom_measure | sum(${zong_call_ci})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234633', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据<br>主管维度<br>个人维度 |
| 平均接通时长(min) | 平均接通时长<br>`customized_987830635909091328` | custom_measure | sum(${call_duration})/sum(${call_status}) |  | {'paramId': '8103974494234632', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234634', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据<br>主管维度<br>个人维度 |
| 等待时长(h) | 等待时长<br>`customized_987830636743757825` | custom_measure | sum(${first_call_time_diff_hour})/sum(${valid_lead_count}) |  | {'paramId': '8139340645427200', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据<br>主管维度<br>个人维度 |
| 外呼接通 | 外呼接通率<br>`customized_987830635376414721` | custom_measure | sum(${call_status})/sum(${zong_call_ci}) |  | {'paramId': '8103974494234634', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234633', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 5min比例 | 5min比例<br>`customized_987830634952790016` | custom_measure | sum(${is_long_call})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234635', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据<br>主管维度<br>个人维度 |
| 好友 | 好友率<br>`customized_987830635590324224` | custom_measure | sum(${is_friend_lead})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234638', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| APP登陆 | APP登陆率<br>`customized_987830635166699521` | custom_measure | sum(${is_app_denglu})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234639', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 异常 | 异常<br>`customized_987830636433379329` | custom_measure | ifnull(sum(${is_yichang})/sum(${valid_lead_count}),0) |  | {'paramId': '8489382022047744', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 深沟 | 深沟率<br>`customized_987830636538236928` | custom_measure | sum(${is_shengou})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234640', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 双沟 | 双沟率<br>`customized_987830635271557120` | custom_measure | sum(${is_shuanggou})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234641', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 已回收 | 已回收<br>`customized_987830635804233729` | custom_measure | ifnull(sum(${yi_huishou})/sum(${valid_lead_count}),0) |  | {'paramId': '8692525273278464', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 首节到课 | 首节到课率<br>`customized_987830636957667328` | custom_measure | sum(${daoke1})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234636', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 首节有效 | 首节有效率<br>`customized_987830637062524929` | custom_measure | sum(${v_daoke1})/sum(${valid_lead_count}) |  | {'paramId': '8171822499981312', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 总体数据 |
| 接量人力 | 接量人力<br>`customized_987830636118806528` | custom_measure | count(DISTINCT ${employee_email_name}) |  | {'paramId': '273598', 'orgParamType': 2, 'needBoundaryValue': False} | 主管维度 |
| 有效例子 | valid_lead_count<br>`8103974494234625` | measure | sum(8103974494234625) |  |  | 主管维度<br>个人维度 |
| 例子总通时 | call_duration<br>`8103974494234632` | measure | sum(8103974494234632) |  |  | 主管维度<br>个人维度 |
| 平均通时(例子) | 平均通时(例子)<br>`customized_987830636328521728` | custom_measure | sum(${call_duration})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234632', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 平均通时(人均) | 平均通时(人均)<br>`customized_987830636223664129` | custom_measure | sum(${call_duration})/${接量人力} |  | {'paramId': '8103974494234632', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': 'customized_987830636118806528', 'orgParamType': 4, 'needBoundaryValue': False} | 主管维度 |
| 24h外呼率 | 24h外呼率<br>`customized_987830634424307712` | custom_measure | sum(${first_call_in_24h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234626', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 48h外呼率 | 48h外呼率<br>`customized_987830634638217217` | custom_measure | sum(${first_call_in_48h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234627', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 24h沟通率 | 24h沟通率<br>`customized_987830634529165313` | custom_measure | sum(${first_call_connected_in_24h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234629', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 48h沟通率 | 48h沟通率<br>`customized_987830634743074816` | custom_measure | sum(${first_call_connected_in_48h})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234630', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 外呼接通率 | 外呼接通率<br>`customized_987830635376414721` | custom_measure | sum(${call_status})/sum(${zong_call_ci}) |  | {'paramId': '8103974494234634', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234633', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 好友率 | 好友率<br>`customized_987830635590324224` | custom_measure | sum(${is_friend_lead})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234638', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| APP登陆率 | APP登陆率<br>`customized_987830635166699521` | custom_measure | sum(${is_app_denglu})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234639', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 深沟率 | 深沟率<br>`customized_987830636538236928` | custom_measure | sum(${is_shengou})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234640', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 双沟率 | 双沟率<br>`customized_987830635271557120` | custom_measure | sum(${is_shuanggou})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234641', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 首节到课率 | 首节到课率<br>`customized_987830636957667328` | custom_measure | sum(${daoke1})/sum(${valid_lead_count}) |  | {'paramId': '8103974494234636', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
| 首节有效率 | 首节有效率<br>`customized_987830637062524929` | custom_measure | sum(${v_daoke1})/sum(${valid_lead_count}) |  | {'paramId': '8171822499981312', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8103974494234625', 'orgParamType': 1, 'needBoundaryValue': False} | 主管维度<br>个人维度 |
