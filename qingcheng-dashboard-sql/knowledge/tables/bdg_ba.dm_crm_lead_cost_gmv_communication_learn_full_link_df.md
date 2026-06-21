# bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df

## 1. 中文名称

线索成本 GMV 沟通学习全链路表

## 2. 表用途

在青橙过程数据 SQL 中作为有效线索主表，提供线索、用户、分配、规则、渠道、年级、顾问、部门和期次字段。

## 3. 数据粒度

待人工确认。当前 SQL 按 `lead_id` 使用，并通过 `select distinct f.*` 进入基础层。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | string | 日期分区 |
| `hour` | string | 小时分区 |
## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `section_assign_employee_first_level_department_name` | `'H业务线'` | 截面分配员工一级部门 |
| `section_assign_employee_second_level_department_name` | `'青橙项目部'` | 截面分配员工二级部门 |
| `period_mapping_first_level_department_name` | `'H业务线'` | 期次映射一级部门 |
| `period_mapping_second_level_department_name` | `('精品班学部','青橙项目部')` | 期次映射二级部门 |
| `virtual_second_department_name` | `'青橙项目部'` | 虚拟二级部门，最终 prc 层过滤 |

## 7. 字段清单

### 7.1 核心标识和期次字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_id` | bigint | 线索 ID | join 首次接通、到课、F 类外呼 |
| `user_id` | bigint | 用户编号 | join APP 登录、外呼、上课、F 类外呼 |
| `employee_email_prefix` | string | 员工邮箱前缀 | join 外呼、到课 |
| `employee_email_name` | string | 员工姓名/邮箱名 | join 架构、F 类外呼 |
| `group_period_year` | string | 期次年份 | 计算 `qici` / `period_name` |
| `group_period_term` | string | 期次期号 | 计算 `qici` / `period_name` |

### 7.2 时间字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `section_assign_time` | string | 截面分配时间 | 计算分配日期和首次触达时间差 |
| `first_call_time` | string | 首次触达时间 | 计算 `first_call_time_diff_hour` 和 `first_call_in_24h` |
| `lead_create_time` | string | 线索创建时间 | 市场渠道 CASE WHEN 中使用（如 KOC 菁英初三 2026-04-15 条件） |

### 7.3 渠道和投放字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `rule_name` | string | 分配规则名称 | 青橙渠道和年级映射、市场渠道 CASE WHEN |
| `channel_name_1` | string | 一级渠道名称 | 市场渠道 CASE WHEN |
| `channel_name_2` | string | 二级渠道名称 | 市场渠道 CASE WHEN |
| `channel_name_3` | string | 三级渠道名称 | 市场渠道 CASE WHEN |
| `flow_pool_name` | string | 流量池名称 | 市场渠道 CASE WHEN（核心字段） |
| `put_plan_name` | string | 投放计划名称 | 市场渠道 CASE WHEN（核心字段） |
| `ad_account_name` | string | 广告账户名称 | 市场渠道 CASE WHEN |
| `channel_provider_name` | string | 渠道供应商名称 | 市场渠道 CASE WHEN |
| `source_manager_name` | string | 来源负责人姓名 | 市场渠道 CASE WHEN（核心字段，区分进校/创新/商务/KOC） |
| `source_put_plan_name` | string | 来源投放计划名称 | 市场渠道 CASE WHEN |
| `channel_second_provider_name` | string | 二级渠道供应商名称 | 市场渠道 CASE WHEN |
| `get_customer_way_name` | string | 获客方式名称 | 市场渠道 CASE WHEN |
| `page_id_name` | string | 落地页 ID/名称 | 市场渠道 CASE WHEN（B 站信息流细分） |
| `sku_id_name` | string | SKU ID/名称 | 市场渠道 CASE WHEN（核心字段，区分名师/IP/产品） |
| `flow_original_order_activity_price` | double | 原始订单活动价格 | 市场渠道 CASE WHEN（价格分层，区分信息流19/低价单/5元朱汉祺等） |
| `flow_order_price` | string | 订单价格 | 市场渠道 CASE WHEN |
| `flow_orders_income_amount` | double | 订单收入金额 | 市场渠道 CASE WHEN |

### 7.3A lead_id 来源追溯提示（2026-06-21）

- 对某批 `lead_id` 做“原始来源 / 原始分配线索”排查时，优先区分两类字段：
  - 当前归因/展示结果：`rule_name`、`period_name`、`group_period_name`、`sku_id_name`
  - 更接近原始来源的候选字段：`trace_type_name`、`final_new_source`、`channel_name_1/2/3`、`flow_pool_name`、`put_plan_name`、`source_put_plan_name`、`source_manager_name`、`get_customer_way_name`
- 已验证样例：`20260619期 + 青橙IP + 公开课` 切片共 2230 条 `lead_id`，其中 `rule_name like '%公开课%'` 为 0，但 `period_name` / `lead_period_name` 可命中 `公开课`。
- 因此不能只依赖 `rule_name` 或 `sku_id_name` 判断线索原始来源。优先走 `knowledge/sql_patterns/qingcheng_lead_origin_trace.md` 的“抽样 20-50 条 → 一行一 lead_id 全量导出”流程。

### 7.4 部门和架构字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `first_department_name` | string | 一级部门名称 | 市场渠道 CASE WHEN（区分市场部/TT 业务线/KM 等） |
| `second_department_name` | string | 二级部门名称 | 市场渠道 CASE WHEN（区分市场二部/市场四部/战略客户部/微信生态部） |
| `third_department_name` | string | 三级部门名称 | 市场渠道 CASE WHEN（核心字段，区分直播部/图书营销部/私域运营部/投放部/线上商务部/KOC孵化部等） |
| `virtual_second_department_name` | string | 虚拟二级部门 | 青橙过滤、市场渠道 CASE WHEN |
| `virtual_third_department_name` | string | 虚拟三级部门 | 输出为 `depart_1` |
| `virtual_fourth_department_name` | string | 虚拟四级部门 | 输出为 `depart`；市场渠道 CASE WHEN（区分郑州学习顾问部等） |
| `virtual_fifth_department_name` | string | 虚拟五级部门 | 市场渠道 CASE WHEN（区分罗江博团队等） |
| `virtual_leader_email_name` | string | 虚拟经理邮箱名 | 输出为 `jingli` |
| `virtual_direct_leader_email_name` | string | 虚拟直属主管邮箱名 | 输出为 `zhuguan` |

### 7.5 线索量指标字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_count` | bigint | 线索数量 | nvl 后聚合 |
| `valid_lead_count` | bigint | 有效线索数量 | nvl 后聚合；同时用于 `can_renew_ds_count_a`、`first_call_in_24h` 条件、`is_friend_lead` 条件 |
| `friend_lead_count` | bigint | 加微线索数量 | 仅当 `valid_lead_count = 1` 时取值，否则为 0 |

### 7.6 转化量指标字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `conversion_lead_count` | bigint | 转化线索数（支付用户数） | nvl 后聚合为 `pay_users` |
| `same_lead_period_conversion_lead_count` | bigint | 同期线索转化数 | nvl 后聚合为 `pay_users_on_period` |
| `subject_count` | bigint | 科目数（支付科目数） | nvl 后聚合为 `pay_user_subs` |
| `same_lead_period_subject_count` | bigint | 同期科目数 | nvl 后聚合为 `pay_user_subs_on_period` |
| `lb_subject_count` | bigint | 联报科目数 | nvl 后聚合为 `pay_user_subs_joint`；lb = 联报 |
| `same_lead_period_lb_subject_count` | bigint | 同期联报科目数 | nvl 后聚合为 `pay_user_subs_joint_onp` |
| `order_count` | bigint | 订单数量 | nvl 处理但未参与最终聚合（可能冗余） |
| `same_lead_period_order_count` | bigint | 同期订单数量 | nvl 处理但未参与最终聚合（可能冗余） |

### 7.7 收入和退款字段（原始单位：分）

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `income_amount` | double | 收入金额（分） | nvl 后除以 100 聚合为 `trade_income` |
| `in_pay_period_refund_amount` | double | 当期退款金额（分） | nvl 后除以 100，参与 `trade_refund` |
| `non_pay_period_refund_amount` | double | 非当期退款金额（分） | nvl 后除以 100，参与 `trade_refund` 和 `pre_refund` |
| `same_lead_period_income_amount` | double | 同期收入金额（分） | nvl 后除以 100 聚合为 `xb_trade_income` |
| `same_lead_period_refund_amount` | double | 同期退款金额（分） | nvl 后除以 100，参与 `xb_trade_profit` |
| `jp_cross_department_refund_amount` | double | 跨部门退款金额（分） | nvl 处理但未参与最终聚合（可能冗余或遗漏） |

### 7.8 意向/年级字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_purchase_intention_level1_category_name` | string | 购买意向一级分类 | 市场渠道 CASE WHEN（区分规划系统等） |
| `lead_purchase_intention_level2_category_name` | string | 购买意向二级分类/年级 | 年级兜底；市场渠道 CASE WHEN |
| `lead_purchase_intention_name` | string | 购买意向名称 | 市场渠道 CASE WHEN（区分 AI 定制等） |

### 7.9 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `gy_trace_id` | bigint | 线索归因留痕id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_type` | bigint | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_type_name` | string | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `final_new_source` | string | 线索留痕source | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_department_code` | bigint | 渠道属性-一级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_department_code` | bigint | 渠道属性-二级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `third_department_code` | bigint | 渠道属性-三级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `put_plan_id` | string | 渠道属性-投放计划id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `plan_create_email_prefix` | string | 渠道属性-计划创建人用户名-邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `plan_create_email_name` | string | 渠道属性-计划创建人-带数字名字 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_manager_username` | string | 渠道属性-source管理人邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_id` | bigint | 渠道属性-流量池id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_provider_id` | bigint | 渠道属性-一级渠道商id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_second_provider_id` | string | 渠道属性-二级渠道商id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `get_customer_way_id` | bigint | 渠道属性-获客方式id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `get_customer_way_parent_id` | bigint | 渠道属性-获客方式父级id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `get_customer_way_parent_name` | string | 渠道属性-获客方式父级name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_original_order_activity_number` | bigint | 联报活动ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_original_order_activity_name` | string | 联报活动名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_purchase_intention_id` | bigint | 购买意向id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_purchase_intention_level1_category_id` | bigint | 购买意向-一级品类id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_purchase_intention_level2_category_id` | bigint | 购买意向-二级品类id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_intention_level` | string | 截面分配-分配意向度 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_first_level_department_code` | bigint | 员工_期截面时间_一级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_second_level_department_code` | bigint | 员工_期截面时间_二级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_third_level_department_code` | bigint | 员工_期截面时间_三级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_third_level_department_name` | string | 员工_期截面时间_三级部门name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_first_department_name` | string | 员工-最新-虚拟架构一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_blacklist_user` | string | 用户是否黑名单 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_number` | string | 期次code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_name` | string | 期name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_mapping_first_level_department_code` | string | 期归属一级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_mapping_second_level_department_code` | string | 期归属二级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_first_level_course_project_code` | bigint | 一级项目code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_first_level_course_project_name` | string | 一级项目name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_second_level_course_project_code` | bigint | 二级项目code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_second_level_course_project_name` | string | 二级项目name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_clazz_begin_time` | string | 开课日期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_main_teacher_numbers` | string | 主讲 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_main_teacher_nicknames` | string | 主讲昵称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_course_category_code` | string | 课程类型，eg：10-公开课｜20-体验课｜30-专题课｜40-系列课 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_first_level_subject_code` | bigint | 课程品类一级code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_first_level_subject_name` | string | 课程品类一级name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_second_level_subject_code` | bigint | 课程品类二级code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_second_level_subject_name` | string | 课程品类二级name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_third_level_subject_code` | bigint | 课程品类三级code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_third_level_subject_name` | string | 课程品类三级name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_conversion_begin_time` | string | 转化开始时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_conversion_end_time` | string | 转化结束时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `group_period_name` | string | 期分组_期名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_cost` | double | 单线索成本（含解密费用，单位：元） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_lead_count` | bigint | 分配线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `no_assign_lead` | bigint | 未分配线索数（废弃） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_call_connected_count` | bigint | 截面分配-分配后电话接通次数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_call_missed_count` | bigint | 截面分配-分配后电话未接通次数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_all_call_duration` | bigint | 截面分配-分配后总通话时长(s) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_call_duration` | bigint | 截面分配-分配后电话通话时长(s) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_is_login_app` | bigint | 期内是否登录APP | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `waiting_time` | bigint | 线索行课等待时长（秒） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_conversion_taketime` | bigint | 线索首次转化时长（秒） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_department_order_count` | bigint | 同学部_转化订单数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_department_subject_count` | bigint | 同学部_转化科目人次 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_department_lb_subject_count` | bigint | 同学部_联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_department_conversion_lead_count` | bigint | 同学部_转化线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_department_income_amount` | double | 同学部_收款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_department_in_pay_period_refund_amount` | double | 同学部_同期退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_department_non_pay_period_refund_amount` | double | 同学部_跨期退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_mini_leader_email_name` | string | 员工-最新-虚拟架构帮带师傅带数字名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `rn` | bigint | 辅助-区分是否分母 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_order_count` | bigint | 线索期_转化订单数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_conversion_lead_count` | bigint | 线索期_转化线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_income_amount` | double | 线索期_收款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_refund_amount` | double | 线索期_退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_same_department_order_count` | bigint | 线索期_同学部转化订单数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_same_department_conversion_lead_count` | bigint | 线索期_同学部转化线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_same_department_income_amount` | double | 线索期_同学部收款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_same_department_refund_amount` | double | 线索期_同学部退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_lead_period_department_order_count` | bigint | 当期_同学部转化订单数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_lead_period_department_conversion_lead_count` | bigint | 当期_同学部转化线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_lead_period_department_income_amount` | double | 当期_同学部收款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_lead_period_department_refund_amount` | double | 当期_同学部退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_lead_period_department_subject_count` | bigint | 同线索期同学部转化科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `same_lead_period_department_lb_subject_count` | bigint | 同线索期同学部转化联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_order_clazz_name` | string | 引流课-班级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_order_clazz_biz_number` | string | 引流课-班级业务编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `data_type` | bigint | 数据类型：1-可用，0-不可用 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_income_order_count` | bigint | 流水期-收款订单数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_income_zhsy_subject_count` | bigint | 流水期-综合素养-收款联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_income_subject_count` | bigint | 流水期-收款科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_income_lb_subject_count` | bigint | 流水期-收款联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_income_lead_count` | bigint | 流水期-收款线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_before_nth_lesson_refund_amount` | double | 流水期-开课nth-退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_department_income_order_count` | bigint | 流水期-同学部-收款订单数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_department_income_zhsy_subject_count` | bigint | 流水期-同学部-综合素养-收款联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_department_income_subject_count` | bigint | 流水期-同学部-收款科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_department_income_lb_subject_count` | bigint | 流水期-同学部-收款联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_department_income_lead_count` | bigint | 流水期-同学部-收款线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_department_before_nth_lesson_refund_amount` | double | 流水期-同学部-开课nth-退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_income_order_count` | bigint | 当期-收款订单数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_income_zhsy_subject_count` | bigint | 当期-综合素养-收款联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_income_subject_count` | bigint | 当期-收款科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_income_lb_subject_count` | bigint | 当期-收款联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_income_lead_count` | bigint | 当期-收款线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_before_nth_lesson_refund_amount` | double | 当期-开课nth-退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_department_income_order_count` | bigint | 当期-同学部-收款订单数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_department_income_zhsy_subject_count` | bigint | 当期-同学部-综合素养-收款联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_department_income_subject_count` | bigint | 当期-同学部-收款科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_department_income_lb_subject_count` | bigint | 当期-同学部-收款联报科目数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_department_income_lead_count` | bigint | 当期-同学部-收款线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_period_department_before_nth_lesson_refund_amount` | double | 当期-同学部-开课nth-退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `province_name` | string | 省份 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `city_name` | string | 城市 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `city_level_name` | string | 城市等级 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sku_id` | string | 落地页上报，用户进入的页面关联的sku_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `promoter_name` | string | 推广员姓名 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `qw_add_time` | string | 添加企微时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `gw_add_time` | string | 添加个微时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `touch_duration_second` | bigint | 触达时长（秒） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `learning_attitude` | string | 学习态度 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `academic_record` | string | 成绩 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `weak_subject` | string | 薄弱学科 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `weak_point_comment` | string | 薄弱点 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `boarder_status` | string | 走读/住校 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `boarder_note` | string | 住校/走读说明 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `tutoring` | string | 补习情况 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `tutoring_note` | string | 补习情况说明 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `learn_situation_comment` | string | 学情/深沟 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `refund_warn_desc` | string | 高危退费说明 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `refund_warn_comment` | string | 高危退费(文本) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `follow_up_content` | string | 跟进内容 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `deep_communicate_method` | string | 深沟方式 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `deep_communicate_duration` | string | 深沟时长 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_pre_signup` | string | 是否预报名 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_sign_up` | string | 预报名学科 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `consumptionpower` | string | 付费能力 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `payment_ability` | string | 支付能力 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `contact_role_note` | string | 联系人角色 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `intention_level` | string | 意向度 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_baseline_exam_user` | string | 是否参加摸底测验 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `user_age` | bigint | 用户年龄 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `user_sex` | string | 用户性别 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `ad_account_id` | string | 平台账户ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `ad_model_id` | bigint | 投放模式ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `ad_model_name` | string | 投放模式NAME | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_room_type` | int | 授课模式 1-大班课 2-小班课 3-一对一 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_count_zhsy` | string | 线索量-zhsy | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_mapping_third_level_department_code` | bigint | 期归属三级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_mapping_third_level_department_name` | string | 期归属三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `xz_internal_contact_email_prefix` | string | 先知投放账户内部管理人邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `xz_internal_contact_email_name` | string | 先知投放账户内部管理人姓名+数字 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_order_number` | string | 主留痕引流课-订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_order_pay_success_timestamp` | string | 主留痕引流课-支付成功时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_order_full_refund_timestamp` | string | 主留痕引流课-完全退款时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_refund_before_clazz_begin` | bigint | 是否课前退费（crm系统字段） 0:否，1:是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_latest_order_full_refund_timestamp` | string | 主留痕引流课-最新子订单完全退款时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `friend_status_name` | string | 好友状态名（流量表字段） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_login_time` | string | 首次登录时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_subject_count` | bigint | 线索期_转化科目人次 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_same_dept_subject_count` | bigint | 线索期_同学部_转化科目人次 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_period_code` | bigint | 主期编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_period_name` | string | 主期名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_period_clazz_begin_date` | string | 主期开课日期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_period_conversion_begin_time` | string | 主期转化开始时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_period_conversion_end_time` | string | 主期转化结束时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_period_first_level_course_project_name` | string | 主期一级项目 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_period_mapping_first_level_department_name` | string | 主期映射一级部门 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_period_mapping_second_level_department_name` | string | 主期映射二级部门 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `target_assign_lead_count_per_lead` | double | 目标分配线索数/实际线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `target_same_department_conversion_lead_count_per_lead` | double | 目标同部门转化线索数/实际线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `target_same_department_net_conversion_per_lead` | double | 目标同部门净收款金额/实际线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `target_lead_cost_per_lead` | double | 目标线索成本/实际线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `target_market_lead_cost_per_lead` | double | 目标市场人员成本/实际线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `target_consultant_lead_cost_per_lead` | double | 目标顾问人员成本/实际线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_orders_refund_amount` | double | 线索引流课退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stats_grade_name` | string | 统计口径线索年级 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `business_id` | string | 直播账号uid | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `business_nickname` | string | 直播账号昵称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_valid_lead_count` | bigint | 有效分配线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `crm_intention_level` | bigint | 意向等级，1-A、2-B、3-C、4-D | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `target_same_department_subject_count_per_lead` | double | 目标-同部门转化科目数/实际线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_streaming_host_id` | string | 三方订单主播 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_put_plan_id` | string | source上的put_plan_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_lead_cost` | double | 直播-单线索成本(不含解密费用，单位：元，目的：集团使用) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `decrypt_fee_lead_cost` | double | 解密费用(单位：元) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_type` | string | 期类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `zhsy_channel_name_1` | string | zhsy-一级渠道 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `zhsy_channel_name_2` | string | zhsy-二级渠道 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `zhsy_channel_name_3` | string | zhsy-三级渠道 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `h_channel_name_1` | string | h-一级渠道 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `yw_channel_name_1` | string | yw_一级渠道 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `yw_channel_name_2` | string | yw_二级渠道 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `yw_channel_name_3` | string | yw_三级渠道 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_first_call_connected_time` | string | 截面分配-分配后首次接通时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_type_id` | string | 流量池类型id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_type_name` | string | 流量池类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `page_id` | string | 落地页id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `page_type` | string | 落地页页面类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `page_type_name` | string | 落地页页面类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_yw_conversion_subject_count` | bigint | 流水期_语文转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_sx_conversion_subject_count` | bigint | 流水期_数学转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_yy_conversion_subject_count` | bigint | 流水期_英语转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_wl_conversion_subject_count` | bigint | 流水期_物理转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_hx_conversion_subject_count` | bigint | 流水期_化学转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_type` | int | 1-xxl、2-sw、3-dzhk、4-sn、5-source | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_email_prefix` | string | 截面管理人邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_first_level_department_code` | bigint | 截面管理人-组织架构一级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_first_level_department_name` | string | 截面管理人-组织架构一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_second_level_department_code` | bigint | 截面管理人-组织架构二级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_second_level_department_name` | string | 截面管理人-组织架构二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_third_level_department_code` | bigint | 截面管理人-组织架构三级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_third_level_department_name` | string | 截面管理人-组织架构三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `third_platform_live_anchor_id` | string | 获客-三方平台直播-主播ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `third_platform_live_anchor_name` | string | 获客-三方平台直播-主播名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `third_platform_live_begin_timestamp` | string | 获客-三方平台直播-直播开始时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `third_platform_live_end_timestamp` | string | 获客-三方平台直播-直播结束时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_model_type` | bigint | 线索模型类型 0:线索 1:潜客 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_model_type_name` | string | 线索模型类型 0:线索 1:潜客 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_lead_effect_timestamp` | string | 获客-三方平台直播-订单支付时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `merge_lead_count` | bigint | 合并线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `merge_assign_lead_count` | bigint | 合并分配线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `merge_valid_lead_count` | bigint | 合并有效线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `merge_assign_valid_lead_count` | bigint | 合并分配有效线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `room_id` | bigint | 直播间id（直播；信息流=NULL） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `cost_belong_department_code` | string | 费用归属部门CODE（信息流空耗专属，从dwd透传） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `cost_belong_department_name` | string | 费用归属部门名称（信息流空耗专属） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `data_source_type` | bigint | 1-业财主数据，2-信息流空耗，3-直播空耗 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `undertake_lead_count` | bigint | 交付线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `undertake_assign_lead_count` | bigint | 交付分配线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `undertake_valid_lead_count` | bigint | 交付有效线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `undertake_assign_valid_lead_count` | bigint | 交付分配有效线索量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_private_sea_clazz_number` | bigint | 截面分配-私海分配留痕对应班级编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_private_sea_clazz_name` | string | 截面分配-私海分配留痕对应班级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_private_sea_clazz_biz_number` | string | 截面分配-私海分配留痕对应班级业务编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_third_provider_id` | string | 渠道属性-三级渠道商id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_third_provider_name` | string | 渠道属性-三级渠道商name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

### 8.1 过程数据 raw / 转化 raw 版本

```sql
where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and f.hour = format_datetime(now() - interval '3' hour, 'HH')
  and f.section_assign_employee_first_level_department_name = 'H业务线'
  and f.section_assign_employee_second_level_department_name = '青橙项目部'
  and f.period_mapping_first_level_department_name = 'H业务线'
  and f.period_mapping_second_level_department_name in ('精品班学部','青橙项目部')
  and f.valid_lead_count = '1'
```

### 8.2 转化宽表-市场渠道版本

```sql
where t1.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and t1.hour = format_datetime(now() - interval '2' hour, 'HH')
  and t1.section_assign_employee_first_level_department_name = 'H业务线'
  and t1.section_assign_employee_second_level_department_name in ('青橙项目部')
  and t1.period_mapping_first_level_department_name = 'H业务线'
```

注意差异：
- hour 偏移不同（`-2h` vs `-3h`）。
- 未加 `period_mapping_second_level_department_name` 过滤。
- 未加 `valid_lead_count = '1'` 过滤（宽表市场渠道看板需要全量线索，不限于有效线索）。

## 9. 常用 join key

- `lead_id`
- `user_id`
- `employee_email_prefix`
- `employee_email_name`

## 10. 常用 SQL 片段

```sql
case when f.valid_lead_count = '1' then 1 else 0 end as v_lead
```

## 11. 注意事项

- 本表在不同看板 SQL 中 hour 偏移不一致：过程数据/转化 raw 使用 `now()-3h`，宽表市场渠道使用 `now()-2h`，原因待确认。
- 宽表市场渠道 SQL 使用 `select distinct t1.*`，若宽表本身有重复行，distinct 可能掩盖数据质量问题。
- 宽表市场渠道 SQL 未加 `valid_lead_count = '1'` 过滤，输出全量线索（含无效线索）。
- 宽表市场渠道 SQL 未加 `period_mapping_second_level_department_name` 过滤，是否会引入非青橙期次数据待确认。
- 本表存在物理字段 `rn`。后续写窗口函数时不要再把别名命名为 `rn`，否则容易触发 `Column 'rn' is ambiguous`。
- 若业务问“某批 lead 最原始从哪里来”，优先查看 `trace_type_name`、`final_new_source`、`channel_name_1/2/3`、`flow_pool_name`、`put_plan_name`、`source_put_plan_name`、`source_manager_name`、`get_customer_way_name`，不要先拿 `rule_name` 当结论。
- 后续生成新 SQL 时不得使用三参数 `date_add` 计算期次，应改为 `interval` 写法。
- 本表字段清单已大幅扩充（从 19 个增至 50+），新增字段均来自 `qingcheng_conversion_wide_table_market_channel_20260611.sql` 实际使用，完整字段含义待表结构确认。
- CRM 线索转移操作必须在当期开课前完成，数据库侧才能记录该转移状态；当期开课后发生退费、转移顾问或状态变化时，本表相关看板可能仍保留原顾问/原期次/原架构口径下的数据。该规则来自用户补充的 CRM 系统限制，青橙具体看板适用性待人工确认。
