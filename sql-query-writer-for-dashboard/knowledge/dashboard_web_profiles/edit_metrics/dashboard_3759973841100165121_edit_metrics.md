# 运营侧数据看板 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3759973841100165121`
- dashboard_name: `运营侧数据看板`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:09:29`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `65b59cd2ba280c33bd20c414fd3ca9632927403cb2a810b5366fce42b8e0eb1e`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3759973841100165121&htmlId=html_3983980624114888704`
- loaded_html_id: `html_3983980624114888704`
- config_html_id: `html_3983980657652543489`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3759973841100165121_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `17` / `443` / `352` / `261`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 17 | 17 | 17 | 850 | 352 | 25 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `2054` | (内部渠道)外呼过程数据 | 178140 | 1 |
| `2132` | (内部)到课衰减情况 | 178139 | 1 |
| `2293` | 运营侧个人数据 | 178138 | 10 |
| `2310` | 分二级部门转化 | 178141 | 1 |
| `2344` | 分析--分周期转化 | 178142 | 1 |
| `2345` | 进量测试(市场渠道) | 178143 | 1 |
| `2424` | 每日转化数据表 | 178145 | 1 |
| `3039` | 新老人转化对比 | 178148 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 标题图 | `node_ocmm36s5ul1` | `unit_3788658743304962049` | u_material | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=9 | False / False |
| 全局筛选器 | `node_ocmm3gbgtt1` | `public_filter_relation_3788927744572502016` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=9, w=20, h=17 | False / False |
| 分团队转化数据 | `node_ocmm3gbgtt2` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=66, w=20, h=77 | False / False |
| 亚飞 | `node_ocmm5x8gaj1` | `unit_3791433812547198984` | u_pivot | node_ocmm5x8gaj95 / 7uks | x=0, y=0, w=10, h=6 | False / False |
| 分渠道转化数据 | `node_ocmm5x8gaj95` | `` | SingleTabs | node_ocllzw8twf1 /  | x=0, y=151, w=20, h=85 | False / False |
| 全局筛选器 | `node_ocmm5xvqp81` | `public_filter_relation_3791452476511903745` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=143, w=20, h=8 | False / False |
| 行课数据 | `node_ocmm6d4ecxf` | `unit_3791886183119278081` | u_pivot | node_ocllzw8twf1 /  | x=0, y=668, w=20, h=66 | False / False |
| 外呼数据 | `node_ocmm6d4ecxg` | `unit_3791903466230407169` | u_pivot | node_ocllzw8twf1 /  | x=0, y=604, w=20, h=64 | False / False |
| 经理 | `node_ocmm7hf7ce2` | `unit_3788931121683902464` | u_pivot | node_ocmm3gbgtt2 / bgug | x=0, y=0, w=10, h=6 | False / False |
| 同渠道转化数据对比 | `node_ocmm7pjr0m1` | `unit_3793248921101189120` | u_pivot | node_ocllzw8twf1 /  | x=0, y=434, w=20, h=86 | False / False |
| 主管 | `node_ocmmelm7j51` | `unit_3800256717559488520` | u_pivot | node_ocmm3gbgtt2 / 7q00 | x=0, y=0, w=10, h=5 | False / False |
| 个人 | `node_ocmmelm7j52` | `unit_3800257159308951556` | u_pivot | node_ocmm3gbgtt2 / eoxn | x=0, y=0, w=10, h=6 | False / False |
| 线索分时间转化数据 | `node_ocmmhhw0ni1` | `unit_3803175274388676608` | u_pivot | node_ocllzw8twf1 /  | x=0, y=291, w=20, h=67 | False / False |
| 进量_转化分析 | `node_ocmmhrhq6y2` | `unit_3803445342673076224` | u_pivot | node_ocllzw8twf1 /  | x=9, y=538, w=11, h=66 | False / False |
| 进量节奏分析 | `node_ocmmhrhq6y4` | `unit_3803529738811367424` | u_line | node_ocllzw8twf1 /  | x=0, y=538, w=9, h=66 | False / False |
| 全局筛选器 | `node_ocmmhrhq6y5` | `public_filter_relation_3803541065796739073` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=520, w=20, h=18 | False / False |
| 收款分时间占比 | `node_ocmn1hi8361` | `unit_3823452752095543296` | u_pivot | node_ocllzw8twf1 /  | x=0, y=244, w=20, h=47 | False / False |
| 全局筛选器 | `node_ocmn1hi8366` | `public_filter_relation_3823479160974778368` | public_filter_relation | node_ocllzw8twf1 /  | x=0, y=236, w=20, h=8 | False / False |
| B站亚飞 | `node_ocmob4mc0k1` | `unit_3864395442075807750` | u_pivot | node_ocmm5x8gaj95 / 1you | x=0, y=0, w=10, h=6 | False / False |
| 抖私1 | `node_ocmou6ibf71` | `unit_3889082426239688709` | u_pivot | node_ocmm5x8gaj95 / ae6k | x=0, y=0, w=10, h=6 | False / False |
| koc整体 | `node_ocmou6ibf72` | `unit_3889083573032431621` | u_pivot | node_ocmm5x8gaj95 / axeq | x=0, y=0, w=10, h=6 | False / False |
| 自孵化koc | `node_ocmou6ibf73` | `unit_3889084874430734339` | u_pivot | node_ocmm5x8gaj95 / 6nbh | x=0, y=0, w=10, h=6 | False / False |
| koc常规 | `node_ocmou6ibf74` | `unit_3889085855924989958` | u_pivot | node_ocmm5x8gaj95 / h1vx | x=0, y=0, w=10, h=6 | False / False |
| 收款分时间占比_副本 | `node_ocmpf7srft3` | `unit_3910424477630115844` | u_pivot | node_ocmm3gbgtt2 / kkq | x=0, y=0, w=10, h=5 | False / False |
| 整体数据 | `node_ocmqm2rj5n1` | `unit_3953902454021992459` | card | node_ocllzw8twf1 /  | x=0, y=26, w=20, h=40 | False / False |
| 新老人转化对比 | `node_ocmr7ia7k91` | `unit_3975643530358935552` | u_pivot | node_ocllzw8twf1 /  | x=0, y=358, w=20, h=76 | False / False |

## Pivot units

### 进量_转化分析

- unit_id: `unit_3803445342673076224`
- model: `2345` / 进量测试(市场渠道)
- dimensions: 分配日期 / `assign_day_new`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 24h外呼 / `24h外呼率`; 48h外呼 / `48h外呼率`; 5min; 好友 / `好友率`; APP; 深沟 / `深沟率`; 课1; 课1有效; 当期单效; 截面单效
- component: `node_ocmmhrhq6y2` / `PivotTable`

### 经理

- unit_id: `unit_3788931121683902464`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli_11`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 接量人力; 人产; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 5min占比; 5min转化率; 20min占比; 20min转化率; 40min占比; 40min转化率; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效; 客单价
- component: `node_ocmm7hf7ce2` / `PivotTable`

### 主管

- unit_id: `unit_3800256717559488520`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli_11`; 主管 / `xiaozu`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 接量人力; 人产; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 5min占比; 5min转化率; 20min占比; 20min转化率; 40min占比; 40min转化率; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效; 客单价
- component: `node_ocmmelm7j51` / `PivotTable`

### 个人

- unit_id: `unit_3800257159308951556`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli_11`; 主管 / `xiaozu`; 顾问 / `employee_email_name`
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 接量人力; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 5min占比; 5min转化率; 20min占比; 20min转化率; 40min占比; 40min转化率; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率 / `截面退费率`; 单效; 客单价
- component: `node_ocmmelm7j52` / `PivotTable`

### 收款分时间占比_副本

- unit_id: `unit_3910424477630115844`
- model: `2293` / 运营侧个人数据
- dimensions: 期次 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`
- measures: 退前线索 / `can_renew_ds_count_a`; 退后线索 / `s_lead`; 接量人力; 首call率; 48h外呼; 5min; 好友率; 深沟率; 双沟率; 人头转化(当期) / `pay_users_on_period`; 订单转化(当期); 总收款(当期) / `xb_trade_income`; 退款(当期); 净收款(当期) / `xb_trade_profit`; 退费率(当期); 单效(当期); 破蛋率; 人均报科; 5min占比; 5min转化率; 20min占比; 20min转化率; 40min占比; 40min转化率; 人头转化; 订单转化; 总收款 / `trade_income`; 退款 / `trade_refund`; 净收款 / `trade_profit`; 退费率; 单效; 客单价
- component: `node_ocmpf7srft3` / `PivotTable`

### B站亚飞

- unit_id: `unit_3864395442075807750`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率
- component: `node_ocmob4mc0k1` / `PivotTable`

### 抖私1

- unit_id: `unit_3889082426239688709`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 经理 / `jingli`; 年级 / `grade_1`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率
- component: `node_ocmou6ibf71` / `PivotTable`

### koc整体

- unit_id: `unit_3889083573032431621`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率
- component: `node_ocmou6ibf72` / `PivotTable`

### 自孵化koc

- unit_id: `unit_3889084874430734339`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率
- component: `node_ocmou6ibf73` / `PivotTable`

### koc常规

- unit_id: `unit_3889085855924989958`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `zhuguan`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 净收(当期) / `xb_trade_profit`; 单效(当期); 人头转化; 收款 / `trade_income`; 净收 / `trade_profit`; 单效; 人均报科; 截面退费率
- component: `node_ocmou6ibf74` / `PivotTable`

### 亚飞

- unit_id: `unit_3791433812547198984`
- model: `2293` / 运营侧个人数据
- dimensions: 期 / `period_name`; 年级 / `grade_1`; 经理 / `jingli`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期) / `人头(当期)`; 收款(当期) / `xb_trade_income`; 单效(当期); 人头转化; 收款 / `trade_income`; 单效; 人均报科; 截面退费率
- component: `node_ocmm5x8gaj1` / `PivotTable`

### 同渠道转化数据对比

- unit_id: `unit_3793248921101189120`
- model: `2310` / 分二级部门转化
- dimensions: 期次 / `period_name`; 学部 / `dept_name`; 年级 / `lead_purchase_intention_level2_category_name`; 部门 / `depart`; period_name; lead_purchase_intention_level2_category_name; channel_map
- measures: 退前线索 / `lead_count`; 退后线索 / `can_renew_ds_count_a`; 24h外呼; 首call; 好友率; 订单转化(当期); 人头转化(当期); 净收款(当期) / `xb_trade_profit`; 退后单效(当期) / `退前单效(当期)`; 单效(当期); 人均报科; 订单转化; 人头转化; 净收款 / `trade_profit`; 退前单效; 退后单效 / `单效`; 退费率
- component: `node_ocmm7pjr0m1` / `PivotTable`

### 收款分时间占比

- unit_id: `unit_3823452752095543296`
- model: `2424` / 每日转化数据表
- dimensions: 期次 / `qici`; 渠道 / `channel_1`
- measures: 总净收 / `gmv_t`; 周2收款 / `gmv_2`; 周2占比; 周2单效; 周3收款 / `gmv_3`; 周3占比; 周3单效; 周4收款 / `gmv_4`; 周4占比; 周4单效; 周5收款 / `gmv_5`; 周5占比; 周5单效; 周6收款 / `gmv_6`; 周6占比; 周6单效; 周7收款 / `gmv_7`; 周7占比; 周7单效; 周1收款 / `gmv_1`; 周1占比; 周1单效
- component: `node_ocmn1hi8361` / `PivotTable`

### 线索分时间转化数据

- unit_id: `unit_3803175274388676608`
- model: `2344` / 分析--分周期转化
- dimensions: 期次 / `qici`; 渠道 / `channel_1`; 经理 / `jingli`; 年级 / `grade_list`; 主管 / `xiaozu`; qici; grade_list; channel_1
- measures: 当期净收款 / `gmv_7`; 当期占比 / `当期收款占比`; 8_14天内收款占比 / `14天内收款占比(不含当期)`; 15_30天内净收款占比 / `30天内净收款占比(不含前14天)`; 非30天内净收款占比; 下期线索当期占比; 净收款 / `gmv_total`; 当期退款 / `refund_7`; 当期退款占比; 8_14天内退款占比 / `14天内退款占比(不含当期)`; 15_30天内退款占比 / `30天内退款占比(不含前14天)`; 非30天内退款占比; 下期线索当期退款占比; 总退款 / `refund_total`
- component: `node_ocmmhhw0ni1` / `PivotTable`

### 新老人转化对比

- unit_id: `unit_3975643530358935552`
- model: `3039` / 新老人转化对比
- dimensions: 期次 / `period_name`; 经理 / `manager_name`; 在职时间 / `on_job_time_bucket`; period_name; channel_map; manager_name; grade_1
- measures: 退前线索 / `before_refund_lead_cnt`; 退后线索 / `after_refund_lead_cnt`; 首call率; 48h外呼; 好友率; 5min; 深沟率; 双沟率; 人头转化(当期); 收款(当期) / `current_income_amt`; 净收款(当期) / `current_net_income_amt`; 单效(当期) ; 人头转化; 收款 / `income_amt`; 净收款 / `net_income_amt`; 单效; 人均报科; 截面退费率
- component: `node_ocmr7ia7k91` / `PivotTable`

### 行课数据

- unit_id: `unit_3791886183119278081`
- model: `2132` / (内部)到课衰减情况
- dimensions: 期 / `qici`; 经理 / `jingli`; 主管 / `xiaozu`; 年级 / `grade_1`; 顾问 / `employee_email_name`; qici; department; grade_1; channel_map_1; rule_name
- measures: 退后线索 / `lead`; 课1; 课1有效; 课2; 课2有效; 课3; 课3有效; 课4; 课4有效; 课5; 课5有效; 课6; 课6有效
- component: `node_ocmm6d4ecxf` / `PivotTable`

### 外呼数据

- unit_id: `unit_3791903466230407169`
- model: `2054` / (内部渠道)外呼过程数据
- dimensions: 期次 / `qici`; 经理 / `jingli`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; qici; grade_1; channel_map_1; jingli
- measures: 退前线索 / `lead_count`; 退后线索 / `valid_lead_count`; 总通时 / `call_duration`; 首call; 6h外呼; 12h外呼; 24h外呼 / `24h外呼率`; 48h外呼 / `48h外呼率`; 48h沟通 / `48h沟通率`; 外呼率; 沟通率; 外呼频次; 平均接通时长(min); 外呼接通率; 5min比例; 好友率; APP登录率; 深沟率; 双沟率; 已回收
- component: `node_ocmm6d4ecxg` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 12h外呼 | 12h外呼<br>`customized_994353436365496321` | custom_measure / measure | ifnull(sum(${first_call_in_12h})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647934271842305"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 15_30天内净收款占比 | 30天内净收款占比(不含前14天)<br>`customized_994353446020784129` | custom_measure / measure | ifnull(sum(${gmv_30})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699906"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 15_30天内退款占比 | 30天内退款占比(不含前14天)<br>`customized_994353446134030336` | custom_measure / measure | ifnull(sum(${refund_30})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699912"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| 20min占比 | 20min占比<br>`customized_994353424550141952` | custom_measure / measure | ifnull(sum(${is_20m_call})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647872988538880"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 20min转化率 | 20min转化率<br>`customized_994353424654999553` | custom_measure / measure | ifnull(sum(${call_20m_z})/sum(${is_20m_call}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647872988538883"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647872988538880"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 24h外呼 | 24h外呼率<br>`customized_994353436474548225` | custom_measure / measure | sum(${first_call_in_24h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234626"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 24h外呼 | 24h外呼<br>`customized_994353441910366209` | custom_measure / measure | ifnull (<br>    sum(${first_call_in_24h}) / sum(${valid_lead_count}),<br>    0<br>) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8807171058198528"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8807171058198529"}] | 同渠道转化数据对比 |
| 24h外呼 | 24h外呼率<br>`customized_994353449443336193` | custom_measure / measure | ifnull(sum(${first_call_24h})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8388293899741184"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 40min占比 | 40min占比<br>`customized_994353424768245760` | custom_measure / measure | ifnull(sum(${is_40m_call})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647872988538881"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 40min转化率 | 40min转化率<br>`customized_994353424877297664` | custom_measure / measure | ifnull(sum(${call_40m_z})/sum(${is_40m_call}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647872988538884"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647872988538881"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 48h外呼 | 48h外呼<br>`customized_994353424982155265` | custom_measure / measure | ifnull(sum(${first_call_in_48h})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8511077494122496"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 48h外呼 | 48h外呼率<br>`customized_994353436688457728` | custom_measure / measure | sum(${first_call_in_48h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234627"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 48h外呼 | 48h外呼率<br>`customized_994353449564971008` | custom_measure / measure | ifnull(sum(${first_call_48h})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8388293899741185"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 48h外呼 | 48h外呼<br>`customized_994353464626716673` | custom_measure / measure | ifnull(sum(${call_48h_num}) / sum(${call_48h_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823813"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823814"}] | 新老人转化对比 |
| 48h沟通 | 48h沟通率<br>`customized_994353436793315329` | custom_measure / measure | sum(${first_call_connected_in_48h})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234630"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 5min | 5min<br>`customized_994353425091207169` | custom_measure / measure | ifnull(sum(${is_long_call})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8511077494122497"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 5min | 5min<br>`customized_994353449690800128` | custom_measure / measure | ifnull(sum(${long_call_5})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8392152286717952"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 5min | 5min<br>`customized_994353464752545793` | custom_measure / measure | ifnull(sum(${call_5min_num}) / sum(${call_5min_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823817"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823818"}] | 新老人转化对比 |
| 5min占比 | 5min占比<br>`customized_994353425200259073` | custom_measure / measure | ifnull(sum(${is_5m_call})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648461290792960"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 5min比例 | 5min比例<br>`customized_994353436902367233` | custom_measure / measure | sum(${is_long_call})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234635"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 5min转化率 | 5min转化率<br>`customized_994353425305116672` | custom_measure / measure | ifnull(sum(${call_5m_z})/sum(${is_5m_call}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648461290792961"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648461290792960"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 6h外呼 | 6h外呼<br>`customized_994353437007224832` | custom_measure / measure | ifnull(sum(${first_call_in_6h})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8647934271842304"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 8_14天内收款占比 | 14天内收款占比(不含当期)<br>`customized_994353445794291713` | custom_measure / measure | ifnull(sum(${gmv_14})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699905"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 8_14天内退款占比 | 14天内退款占比(不含当期)<br>`customized_994353445911732225` | custom_measure / measure | ifnull(sum(${refund_14})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699911"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| APP | APP<br>`customized_994353449816629248` | custom_measure / measure | ifnull(sum(${app_denglu})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8392152286717953"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| APP登录率 | APP登录率<br>`customized_994353437116276736` | custom_measure / measure | sum(${is_app_denglu})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234639"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 下期线索当期占比 | 下期线索当期占比<br>`customized_994353446259859456` | custom_measure / measure | ifnull(sum(${gmv_7_h})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699908"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 下期线索当期退款占比 | 下期线索当期退款占比<br>`customized_994353446377299968` | custom_measure / measure | ifnull(sum(${refund_7_p})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699914"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| 人产 | 人产<br>`customized_994353425728741377` | custom_measure / measure | sum(${trade_profit}) / ${接量人力} |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879249"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_994353425623883776"}] | 经理, 主管 |
| 人均报科 | 人均报科<br>`customized_994353425837793281` | custom_measure / measure | ifnull(sum(${pay_user_subs})/sum(${pay_users}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879241"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879238"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 人均报科 | 人均报科<br>`customized_994353442015223808` | custom_measure / measure | sum(${pay_user_subs})/sum(${pay_users}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273797"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273794"}] | 同渠道转化数据对比 |
| 人均报科 | 人均报科<br>`customized_994353464874180608` | custom_measure / measure | ifnull(sum(${avg_subject_num}) / sum(${avg_subject_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823835"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823836"}] | 新老人转化对比 |
| 人头转化 | 人头转化<br>`customized_994353426055897089` | custom_measure / measure | ifnull(sum(${pay_users})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879238"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 人头转化 | 人头转化<br>`customized_994353442128470017` | custom_measure / measure | sum(${pay_users})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273794"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273793"}] | 同渠道转化数据对比 |
| 人头转化 | 人头转化<br>`customized_994353464991621120` | custom_measure / measure | ifnull(sum(${head_conversion_num}) / sum(${head_conversion_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823829"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823830"}] | 新老人转化对比 |
| 人头转化(当期) | 人头(当期)<br>`customized_994353425946845185` | custom_measure / measure | ifnull(sum(${pay_users_on_period})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879239"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 人头转化(当期) | 人头转化(当期)<br>`customized_994353442233327616` | custom_measure / measure | sum(${pay_users_not_on_period})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273796"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273793"}] | 同渠道转化数据对比 |
| 人头转化(当期) | 人头转化(当期)<br>`customized_994353465100673024` | custom_measure / measure | ifnull(sum(${current_head_conversion_num})/sum(${current_head_conversion_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823823"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823824"}] | 新老人转化对比 |
| 单效 | 单效<br>`customized_994353426278195200` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879249"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 单效 | 单效<br>`customized_994353465213919233` | custom_measure / measure | ifnull(sum(${unit_efficiency_num}) / sum(${unit_efficiency_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823833"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823834"}] | 新老人转化对比 |
| 单效(当期) | 单效(当期)<br>`customized_994353426387247104` | custom_measure / measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879251"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 单效(当期) | 单效(当期)<br>`customized_994353442443042816` | custom_measure / measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273807"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273793"}] | 同渠道转化数据对比 |
| 单效(当期)  | 单效(当期) <br>`customized_994353465322971137` | custom_measure / measure | ifnull(sum(${current_unit_efficiency_num})/sum(${current_unit_efficiency_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823827"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823828"}] | 新老人转化对比 |
| 双沟率 | 双沟率<br>`customized_994353426492104705` | custom_measure / measure | ifnull(sum(${shuanggou_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8511181621389312"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 双沟率 | 双沟率<br>`customized_994353437221134337` | custom_measure / measure | sum(${is_shuanggou})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234641"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 双沟率 | 双沟率<br>`customized_994353465436217344` | custom_measure / measure | ifnull(sum(${double_communication_num}) / sum(${double_communication_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823821"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823822"}] | 新老人转化对比 |
| 周1单效 | 周1单效<br>`customized_994353455659294721` | custom_measure / measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_1_z}) / sum(${v_lead_c})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648107429619712"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}] | 收款分时间占比 |
| 周1占比 | 周1占比<br>`customized_994353455776735233` | custom_measure / measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_1}) / sum(${gmv_t})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200064"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周2单效 | 周2单效<br>`customized_994353455885787137` | custom_measure / measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_2_z}) / sum(${v_lead_c})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648107429619713"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}] | 收款分时间占比 |
| 周2占比 | 周2占比<br>`customized_994353455994839041` | custom_measure / measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_2}) / sum(${gmv_t})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200065"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周3单效 | 周3单效<br>`customized_994353456103890945` | custom_measure / measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_3_z}) / sum(${v_lead_c})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648107429619714"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}] | 收款分时间占比 |
| 周3占比 | 周3占比<br>`customized_994353456212942849` | custom_measure / measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_3}) / sum(${gmv_t})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200066"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周4单效 | 周4单效<br>`customized_994353456321994753` | custom_measure / measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_4_z}) / sum(${v_lead_c})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648107429619715"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}] | 收款分时间占比 |
| 周4占比 | 周4占比<br>`customized_994353456431046657` | custom_measure / measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_4}) / sum(${gmv_t})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200067"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周5单效 | 周5单效<br>`customized_994353456540098561` | custom_measure / measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_5_z}) / sum(${v_lead_c})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648107429619716"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}] | 收款分时间占比 |
| 周5占比 | 周5占比<br>`customized_994353456649150465` | custom_measure / measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_5}) / sum(${gmv_t})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200068"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周6单效 | 周6单效<br>`customized_994353456762396672` | custom_measure / measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_6_z}) / sum(${v_lead_c})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648107429619717"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}] | 收款分时间占比 |
| 周6占比 | 周6占比<br>`customized_994353456867254273` | custom_measure / measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_6}) / sum(${gmv_t})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200069"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 周7单效 | 周7单效<br>`customized_994353456976306177` | custom_measure / measure | case<br>    when ifnull(sum(${v_lead_c}), 0) = 0 then 0<br>    else sum(${gmv_7_z}) / sum(${v_lead_c})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8648107429619718"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8625186871404544"}] | 收款分时间占比 |
| 周7占比 | 周7占比<br>`customized_994353457081163776` | custom_measure / measure | case<br>    when ifnull(sum(${gmv_t}), 0) = 0 then 0<br>    else sum(${gmv_7}) / sum(${gmv_t})<br>end |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200070"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8466748058200071"}] | 收款分时间占比 |
| 外呼接通率 | 外呼接通率<br>`customized_994353437330186241` | custom_measure / measure | sum(${call_status})/sum(${zong_call_ci}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234634"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234633"}] | 外呼数据 |
| 外呼率 | 外呼率<br>`customized_994353437439238145` | custom_measure / measure | ifnull(sum(${first_call_cnt})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234628"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 外呼频次 | 外呼频次<br>`customized_994353437560872960` | custom_measure / measure | sum(${zong_call_ci})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234633"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 好友 | 好友率<br>`customized_994353449925681152` | custom_measure / measure | ifnull(sum(${friend_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551810"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 好友率 | 好友率<br>`customized_994353426722791424` | custom_measure / measure | sum(${friend_lead})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879234"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 好友率 | 好友率<br>`customized_994353437669924864` | custom_measure / measure | sum(${is_friend_lead})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234638"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 好友率 | 好友率<br>`customized_994353442556289025` | custom_measure / measure | ifnull(sum(${is_friend_lead})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8807171058198531"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8807171058198529"}] | 同渠道转化数据对比 |
| 好友率 | 好友率<br>`customized_994353465541074945` | custom_measure / measure | ifnull(sum(${friend_num}) / sum(${friend_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823815"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823816"}] | 新老人转化对比 |
| 客单价 | 客单价<br>`customized_994353426949283840` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${pay_users}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879249"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879238"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 已回收 | 已回收<br>`customized_994353437875445761` | custom_measure / measure | ifnull(sum(${yi_huishou})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8692525273278464"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 平均接通时长(min) | 平均接通时长(min)<br>`customized_994353437980303360` | custom_measure / measure | sum(${call_duration})/sum(${call_status}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234632"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234634"}] | 外呼数据 |
| 当期单效 | 当期单效<br>`customized_994353450038927361` | custom_measure / measure | ifnull(sum(${xb_trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551828"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 当期占比 | 当期收款占比<br>`customized_994353446482157569` | custom_measure / measure | ifnull(sum(${gmv_7})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699904"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 当期退款占比 | 当期退款占比<br>`customized_994353446591209473` | custom_measure / measure | ifnull(sum(${refund_7})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699910"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| 截面单效 | 截面单效<br>`customized_994353450147979265` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551826"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 截面退费率 | 截面退费率<br>`customized_994353427171581953` | custom_measure / measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879248"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879247"}] | B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 截面退费率 | 截面退费率<br>`customized_994353465650126849` | custom_measure / measure | ifnull(sum(${section_refund_rate_num}) / sum(${section_refund_rate_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823837"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823838"}] | 新老人转化对比 |
| 接量人力 | 接量人力<br>`customized_994353425623883776` | custom_measure / measure | count(DISTINCT ${employee_email_name})-1 |  | [{"needBoundaryValue": false, "orgParamType": 2, "paramId": "319197"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 沟通率 | 沟通率<br>`customized_994353438085160961` | custom_measure / measure | ifnull(sum(${first_call_connected_cnt})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234631"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 深沟 | 深沟率<br>`customized_994353450353500160` | custom_measure / measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551811"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 深沟率 | 深沟率<br>`customized_994353427490349057` | custom_measure / measure | ifnull(sum(${shengou_lead})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879235"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 深沟率 | 深沟率<br>`customized_994353438194212865` | custom_measure / measure | sum(${is_shengou})/sum(${valid_lead_count}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234640"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 深沟率 | 深沟率<br>`customized_994353465754984448` | custom_measure / measure | ifnull(sum(${deep_communication_num}) / sum(${deep_communication_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823819"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823820"}] | 新老人转化对比 |
| 破蛋率 | 破蛋率<br>`customized_994353427704258560` | custom_measure / measure | ifnull(sum(${podan})/${接量人力},0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879255"}, {"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_994353425623883776"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 订单转化 | 订单转化<br>`customized_994353427922362368` | custom_measure / measure | ifnull(sum(${pay_user_subs})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879241"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 订单转化 | 订单转化<br>`customized_994353442661146624` | custom_measure / measure | sum(${pay_user_subs})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273797"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273793"}] | 同渠道转化数据对比 |
| 订单转化(当期) | 订单转化(当期)<br>`customized_994353428031414272` | custom_measure / measure | ifnull(sum(${pay_user_subs_on_period})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879242"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 订单转化(当期) | 订单转化(当期)<br>`customized_994353442766004225` | custom_measure / measure | sum(${pay_user_subs_on_period})/sum(${can_renew_ds_count_a}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273798"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273793"}] | 同渠道转化数据对比 |
| 课1 | 课1<br>`customized_994353431319748608` | custom_measure / measure | sum(${ke_1})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029570"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课1 | 课1<br>`customized_994353450454163456` | custom_measure / measure | ifnull(sum(${daoke_1})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551814"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 课1有效 | 课1有效<br>`customized_994353431432994817` | custom_measure / measure | sum(${v_ke_1})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029576"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课1有效 | 课1有效<br>`customized_994353450567409665` | custom_measure / measure | ifnull(sum(${daoke_v1})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8392152286717954"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8387973858551809"}] | 进量_转化分析 |
| 课2 | 课2<br>`customized_994353431546241024` | custom_measure / measure | sum(${ke_2})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029571"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课2有效 | 课2有效<br>`customized_994353431659487233` | custom_measure / measure | sum(${v_ke_2})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029577"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课3 | 课3<br>`customized_994353431768539137` | custom_measure / measure | sum(${ke_3})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029572"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课3有效 | 课3有效<br>`customized_994353431881785344` | custom_measure / measure | sum(${v_ke_3})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029578"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课4 | 课4<br>`customized_994353431986642945` | custom_measure / measure | sum(${ke_4})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029573"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课4有效 | 课4有效<br>`customized_994353432095694849` | custom_measure / measure | sum(${v_ke_4})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029579"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课5 | 课5<br>`customized_994353432204746753` | custom_measure / measure | sum(${ke_5})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029574"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课5有效 | 课5有效<br>`customized_994353432309604352` | custom_measure / measure | sum(${v_ke_5})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029580"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课6 | 课6<br>`customized_994353432418656256` | custom_measure / measure | sum(${ke_6})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029575"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 课6有效 | 课6有效<br>`customized_994353432527708160` | custom_measure / measure | sum(${v_ke_6})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029581"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8172915650029568"}] | 行课数据 |
| 退前单效 | 退前单效<br>`customized_994353442870861824` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273805"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8590289567967232"}] | 同渠道转化数据对比 |
| 退后单效 | 单效<br>`customized_994353442338185217` | custom_measure / measure | ifnull(sum(${trade_profit})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273805"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273793"}] | 同渠道转化数据对比 |
| 退后单效(当期) | 退前单效(当期)<br>`customized_994353442979913728` | custom_measure / measure | ifnull(sum(${xb_trade_profit})/sum(${lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273807"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8590289567967232"}] | 同渠道转化数据对比 |
| 退款(当期) | 退款(当期)<br>`customized_994353428245323777` | custom_measure / measure | ifnull(sum(${xb_trade_income})-sum(${xb_trade_profit}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879250"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879251"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 退费率 | 截面退费率<br>`customized_994353427171581953` | custom_measure / measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879248"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879247"}] | 经理, 主管, 个人 |
| 退费率 | 退费率<br>`customized_994353428345987073` | custom_measure / measure | ifnull(sum(${trade_refund})/sum(${trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879248"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879247"}] | 收款分时间占比_副本 |
| 退费率 | 退费率<br>`customized_994353443088965632` | custom_measure / measure | sum(${trade_refund})/sum(${trade_income}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273804"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8348161562273803"}] | 同渠道转化数据对比 |
| 退费率(当期) | 退费率(当期)<br>`customized_994353428446650369` | custom_measure / measure | ifnull(${退款(当期)}/sum(${xb_trade_income}),0) |  | [{"needBoundaryValue": false, "orgParamType": 4, "paramId": "customized_994353428245323777"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879250"}] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 非30天内净收款占比 | 非30天内净收款占比<br>`customized_994353446691872769` | custom_measure / measure | ifnull(sum(${gmv_n30})/sum(${gmv_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699907"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699909"}] | 线索分时间转化数据 |
| 非30天内退款占比 | 非30天内退款占比<br>`customized_994353446796730368` | custom_measure / measure | ifnull(sum(${refund_n30})/sum(${refund_total}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699913"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8456155560699915"}] | 线索分时间转化数据 |
| 首call | 首call<br>`customized_994353438303264769` | custom_measure / measure | ifnull(sum(${is_f_call})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8432582790834176"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8103974494234625"}] | 外呼数据 |
| 首call | 首call<br>`customized_994353443189628928` | custom_measure / measure | ifnull(sum(${is_f_call})/sum(${valid_lead_count}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8807171058198530"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8807171058198529"}] | 同渠道转化数据对比 |
| 首call率 | 首call率<br>`customized_994353428551507968` | custom_measure / measure | ifnull(sum(${is_f_call})/sum(${can_renew_ds_count_a}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8511077494122498"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8337294278879233"}] | 经理, 主管, 个人, 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 首call率 | 首call率<br>`customized_994353465859842049` | custom_measure / measure | ifnull(sum(${first_call_num}) / sum(${first_call_den}),0) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823811"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "9060630168823812"}] | 新老人转化对比 |
| channel_1 | channel_1<br>`335528` | dimension / filter |  |  | [] | 线索分时间转化数据 |
| channel_map | channel_map<br>`319191` | dimension / filter |  |  | [] | B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| channel_map | channel_map<br>`322467` | dimension / filter |  |  | [] | 同渠道转化数据对比 |
| channel_map | channel_map<br>`519163` | dimension / filter |  |  | [] | 新老人转化对比 |
| channel_map_1 | channel_map_1<br>`273594` | dimension / filter |  |  | [] | 外呼数据 |
| channel_map_1 | channel_map_1<br>`289671` | dimension / filter |  |  | [] | 行课数据 |
| department | department<br>`289674` | dimension / filter |  |  | [] | 行课数据 |
| grade_1 | grade_1<br>`273595` | dimension / filter |  |  | [] | 外呼数据 |
| grade_1 | grade_1<br>`289672` | dimension / filter |  |  | [] | 行课数据 |
| grade_1 | grade_1<br>`519164` | dimension / filter |  |  | [] | 新老人转化对比 |
| grade_list | grade_list<br>`335531` | dimension / filter |  |  | [] | 线索分时间转化数据 |
| jingli | jingli<br>`322380` | dimension / filter |  |  | [] | 外呼数据 |
| lead_purchase_intention_level2_category_name | lead_purchase_intention_level2_category_name<br>`322468` | dimension / filter |  |  | [] | 同渠道转化数据对比 |
| manager_name | manager_name<br>`519165` | dimension / filter |  |  | [] | 新老人转化对比 |
| period_name | period_name<br>`322466` | dimension / filter |  |  | [] | 同渠道转化数据对比 |
| period_name | period_name<br>`519162` | dimension / filter |  |  | [] | 新老人转化对比 |
| qici | qici<br>`273592` | dimension / filter |  |  | [] | 外呼数据 |
| qici | qici<br>`289670` | dimension / filter |  |  | [] | 行课数据 |
| qici | qici<br>`335527` | dimension / filter |  |  | [] | 线索分时间转化数据 |
| rule_name | rule_name<br>`374265` | dimension / filter |  |  | [] | 行课数据 |
| 主管 | xiaozu<br>`273597` | dimension / row_dimension |  |  | [] | 外呼数据 |
| 主管 | xiaozu<br>`289673` | dimension / row_dimension |  |  | [] | 行课数据 |
| 主管 | zhuguan<br>`319196` | dimension / row_dimension |  |  | [] | B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规 |
| 主管 | xiaozu<br>`319199` | dimension / row_dimension |  |  | [] | 主管, 个人, 亚飞 |
| 主管 | xiaozu<br>`363805` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 分配日期 | assign_day_new<br>`335861` | dimension / row_dimension |  |  | [] | 进量_转化分析 |
| 在职时间 | on_job_time_bucket<br>`519169` | dimension / row_dimension |  |  | [] | 新老人转化对比 |
| 学部 | dept_name<br>`322470` | dimension / row_dimension |  |  | [] | 同渠道转化数据对比 |
| 年级 | grade_1<br>`289672` | dimension / row_dimension |  |  | [] | 行课数据 |
| 年级 | grade_1<br>`319192` | dimension / row_dimension |  |  | [] | 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 年级 | lead_purchase_intention_level2_category_name<br>`322468` | dimension / row_dimension |  |  | [] | 同渠道转化数据对比 |
| 年级 | grade_list<br>`335531` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 期 | qici<br>`289670` | dimension / row_dimension |  |  | [] | 行课数据 |
| 期 | period_name<br>`319190` | dimension / row_dimension |  |  | [] | 经理, 主管, 个人, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 期次 | qici<br>`273592` | dimension / row_dimension |  |  | [] | 外呼数据 |
| 期次 | period_name<br>`319190` | dimension / row_dimension |  |  | [] | 收款分时间占比_副本 |
| 期次 | period_name<br>`322466` | dimension / row_dimension |  |  | [] | 同渠道转化数据对比 |
| 期次 | qici<br>`335527` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 期次 | qici<br>`365768` | dimension / row_dimension |  |  | [] | 收款分时间占比 |
| 期次 | period_name<br>`519162` | dimension / row_dimension |  |  | [] | 新老人转化对比 |
| 渠道 | channel_1<br>`335528` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 渠道 | channel_1<br>`365769` | dimension / row_dimension |  |  | [] | 收款分时间占比 |
| 经理 | jingli<br>`319195` | dimension / row_dimension |  |  | [] | 收款分时间占比_副本, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 经理 | jingli<br>`322380` | dimension / row_dimension |  |  | [] | 外呼数据 |
| 经理 | jingli<br>`322444` | dimension / row_dimension |  |  | [] | 行课数据 |
| 经理 | jingli<br>`363804` | dimension / row_dimension |  |  | [] | 线索分时间转化数据 |
| 经理 | jingli_11<br>`386283` | dimension / row_dimension |  |  | [] | 经理, 主管, 个人 |
| 经理 | manager_name<br>`519165` | dimension / row_dimension |  |  | [] | 新老人转化对比 |
| 部门 | depart<br>`322471` | dimension / row_dimension |  |  | [] | 同渠道转化数据对比 |
| 顾问 | employee_email_name<br>`273598` | dimension / row_dimension |  |  | [] | 外呼数据 |
| 顾问 | employee_email_name<br>`289698` | dimension / row_dimension |  |  | [] | 行课数据 |
| 顾问 | employee_email_name<br>`319197` | dimension / row_dimension |  |  | [] | 个人, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 人头转化(当期) | pay_users_on_period<br>`8337294278879239` | measure / measure | sum(8337294278879239) |  | [] | 收款分时间占比_副本 |
| 净收 | trade_profit<br>`8337294278879249` | measure / measure | sum(8337294278879249) |  | [] | B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规 |
| 净收(当期) | xb_trade_profit<br>`8337294278879251` | measure / measure | sum(8337294278879251) |  | [] | B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规 |
| 净收款 | trade_profit<br>`8337294278879249` | measure / measure | sum(8337294278879249) |  | [] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 净收款 | trade_profit<br>`8348161562273805` | measure / measure | sum(8348161562273805) |  | [] | 同渠道转化数据对比 |
| 净收款 | gmv_total<br>`8456155560699909` | measure / measure | sum(8456155560699909) |  | [] | 线索分时间转化数据 |
| 净收款 | net_income_amt<br>`9060630168823832` | measure / measure | sum(9060630168823832) |  | [] | 新老人转化对比 |
| 净收款(当期) | xb_trade_profit<br>`8337294278879251` | measure / measure | sum(8337294278879251) |  | [] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 净收款(当期) | xb_trade_profit<br>`8348161562273807` | measure / measure | sum(8348161562273807) |  | [] | 同渠道转化数据对比 |
| 净收款(当期) | current_net_income_amt<br>`9060630168823826` | measure / measure | sum(9060630168823826) |  | [] | 新老人转化对比 |
| 周1收款 | gmv_1<br>`8466748058200064` | measure / measure | sum(8466748058200064) |  | [] | 收款分时间占比 |
| 周2收款 | gmv_2<br>`8466748058200065` | measure / measure | sum(8466748058200065) |  | [] | 收款分时间占比 |
| 周3收款 | gmv_3<br>`8466748058200066` | measure / measure | sum(8466748058200066) |  | [] | 收款分时间占比 |
| 周4收款 | gmv_4<br>`8466748058200067` | measure / measure | sum(8466748058200067) |  | [] | 收款分时间占比 |
| 周5收款 | gmv_5<br>`8466748058200068` | measure / measure | sum(8466748058200068) |  | [] | 收款分时间占比 |
| 周6收款 | gmv_6<br>`8466748058200069` | measure / measure | sum(8466748058200069) |  | [] | 收款分时间占比 |
| 周7收款 | gmv_7<br>`8466748058200070` | measure / measure | sum(8466748058200070) |  | [] | 收款分时间占比 |
| 当期净收款 | gmv_7<br>`8456155560699904` | measure / measure | sum(8456155560699904) |  | [] | 线索分时间转化数据 |
| 当期退款 | refund_7<br>`8456155560699910` | measure / measure | sum(8456155560699910) |  | [] | 线索分时间转化数据 |
| 总净收 | gmv_t<br>`8466748058200071` | measure / measure | sum(8466748058200071) |  | [] | 收款分时间占比 |
| 总收款 | trade_income<br>`8337294278879247` | measure / measure | sum(8337294278879247) |  | [] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 总收款(当期) | xb_trade_income<br>`8337294278879250` | measure / measure | sum(8337294278879250) |  | [] | 经理, 主管, 个人, 收款分时间占比_副本 |
| 总退款 | refund_total<br>`8456155560699915` | measure / measure | sum(8456155560699915) |  | [] | 线索分时间转化数据 |
| 总通时 | call_duration<br>`8103974494234632` | measure / measure | sum(8103974494234632) |  | [] | 外呼数据 |
| 收款 | trade_income<br>`8337294278879247` | measure / measure | sum(8337294278879247) |  | [] | B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 收款 | income_amt<br>`9060630168823831` | measure / measure | sum(9060630168823831) |  | [] | 新老人转化对比 |
| 收款(当期) | xb_trade_income<br>`8337294278879250` | measure / measure | sum(8337294278879250) |  | [] | B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 收款(当期) | current_income_amt<br>`9060630168823825` | measure / measure | sum(9060630168823825) |  | [] | 新老人转化对比 |
| 退前线索 | can_renew_ds_count_a<br>`8337294278879233` | measure / measure | sum(8337294278879233) |  | [] | 收款分时间占比_副本 |
| 退前线索 | lead_count<br>`8465935477925888` | measure / measure | sum(8465935477925888) |  | [] | 外呼数据 |
| 退前线索 | lead_count<br>`8590283478886400` | measure / measure | sum(8590283478886400) |  | [] | 经理, 主管, 个人, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 退前线索 | lead_count<br>`8590289567967232` | measure / measure | sum(8590289567967232) |  | [] | 同渠道转化数据对比 |
| 退前线索 | lead_count<br>`8590324328392704` | measure / measure | sum(8590324328392704) |  | [] | 进量_转化分析 |
| 退前线索 | before_refund_lead_cnt<br>`9060630168823809` | measure / measure | sum(9060630168823809) |  | [] | 新老人转化对比 |
| 退后线索 | valid_lead_count<br>`8103974494234625` | measure / measure | sum(8103974494234625) |  | [] | 外呼数据 |
| 退后线索 | lead<br>`8172915650029568` | measure / measure | sum(8172915650029568) |  | [] | 行课数据 |
| 退后线索 | can_renew_ds_count_a<br>`8337294278879233` | measure / measure | sum(8337294278879233) |  | [] | 经理, 主管, 个人, B站亚飞, 抖私1, koc整体, 自孵化koc, koc常规, 亚飞 |
| 退后线索 | s_lead<br>`8337294278879254` | measure / measure | sum(8337294278879254) |  | [] | 收款分时间占比_副本 |
| 退后线索 | can_renew_ds_count_a<br>`8348161562273793` | measure / measure | sum(8348161562273793) |  | [] | 同渠道转化数据对比 |
| 退后线索 | can_renew_ds_count_a<br>`8387973858551809` | measure / measure | sum(8387973858551809) |  | [] | 进量_转化分析 |
| 退后线索 | after_refund_lead_cnt<br>`9060630168823810` | measure / measure | sum(9060630168823810) |  | [] | 新老人转化对比 |
| 退款 | trade_refund<br>`8337294278879248` | measure / measure | sum(8337294278879248) |  | [] | 经理, 主管, 个人, 收款分时间占比_副本 |

## Filters

### Public filters

| filter_id | relation_id | field_id | show_name | condition / default | linked components |
|---|---|---|---|---|---|
| `public_filter_3788927744572502018` | `public_filter_relation_3788927744572502016` | `319190` | period_name | in /  | [] |
| `public_filter_3788990810988818433` | `public_filter_relation_3788927744572502016` | `319192` | grade_1 | in /  | [] |
| `public_filter_3790506971007373314` | `public_filter_relation_3788927744572502016` | `319191` | channel_map | in /  | [] |
| `public_filter_3830999348405465089` | `public_filter_relation_3788927744572502016` | `374215` | rule_name | in /  | [] |
| `public_filter_3963942876590977026` | `public_filter_relation_3788927744572502016` | `319195` | jingli | in /  | [] |
| `public_filter_3791452476511903747` | `public_filter_relation_3791452476511903745` | `319190` | period_name | in /  | [] |
| `public_filter_3791455441184706562` | `public_filter_relation_3791452476511903745` | `319194` | depart | in /  | [] |
| `public_filter_3791455441184706564` | `public_filter_relation_3791452476511903745` | `319195` | jingli | in /  | [] |
| `public_filter_3791456040351399937` | `public_filter_relation_3791452476511903745` | `319192` | grade_1 | in /  | [] |
| `public_filter_3803541065796739075` | `public_filter_relation_3803541065796739073` | `335728` | period_name | in / True | [] |
| `public_filter_3803541065796739077` | `public_filter_relation_3803541065796739073` | `335729` | channel_map | in /  | [] |
| `public_filter_3804529822347145217` | `public_filter_relation_3803541065796739073` | `335730` | grade_1 | in /  | [] |
| `public_filter_3804529822347145219` | `public_filter_relation_3803541065796739073` | `335733` | jingli | in /  | [] |
| `public_filter_3841221227389956097` | `public_filter_relation_3803541065796739073` | `386424` | rule_name | in /  | [] |
| `public_filter_3861508403877335041` | `public_filter_relation_3823479160974778368` | `365768` | qici | in /  | [] |
| `public_filter_3861510439711043586` | `public_filter_relation_3823479160974778368` | `365769` | channel_1 | in /  | [] |
| `public_filter_3861510439711043590` | `public_filter_relation_3823479160974778368` | `365770` | jingli | in /  | [] |
| `public_filter_3910308776237477890` | `public_filter_relation_3823479160974778368` | `459235` | grade | in /  | [] |

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3791433812547198984` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3791886183119278081` | `289670` | qici | in | ["detailFilter"] |
| `unit_3791886183119278081` | `289671` | channel_map_1 | in | ["detailFilter"] |
| `unit_3791886183119278081` | `289672` | grade_1 | in | ["detailFilter"] |
| `unit_3791886183119278081` | `289674` | department | in | ["detailFilter"] |
| `unit_3791886183119278081` | `374265` | rule_name | in | ["detailFilter"] |
| `unit_3791903466230407169` | `273592` | qici | in | ["detailFilter"] |
| `unit_3791903466230407169` | `273594` | channel_map_1 | in | ["detailFilter"] |
| `unit_3791903466230407169` | `273595` | grade_1 | in | ["detailFilter"] |
| `unit_3791903466230407169` | `322380` | jingli | in | ["detailFilter"] |
| `unit_3793248921101189120` | `322466` | period_name | in | ["detailFilter"] |
| `unit_3793248921101189120` | `322467` | channel_map | in | ["detailFilter"] |
| `unit_3793248921101189120` | `322468` | lead_purchase_intention_level2_category_name | in | ["detailFilter"] |
| `unit_3803175274388676608` | `335527` | qici | in | ["detailFilter"] |
| `unit_3803175274388676608` | `335528` | channel_1 | in | ["detailFilter"] |
| `unit_3803175274388676608` | `335531` | grade_list | in | ["detailFilter"] |
| `unit_3864395442075807750` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3889082426239688709` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3889083573032431621` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3889084874430734339` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3889085855924989958` | `319191` | channel_map | in | ["detailFilter"] |
| `unit_3975643530358935552` | `519162` | period_name | in | ["detailFilter"] |
| `unit_3975643530358935552` | `519163` | channel_map | in | ["detailFilter"] |
| `unit_3975643530358935552` | `519164` | grade_1 | in | ["detailFilter"] |
| `unit_3975643530358935552` | `519165` | manager_name | in | ["detailFilter"] |

## Text units

- 无文字组件内容。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
