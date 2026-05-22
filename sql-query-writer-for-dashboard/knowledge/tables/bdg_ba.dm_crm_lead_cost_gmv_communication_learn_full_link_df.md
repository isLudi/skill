# bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df

## 1. 中文名称

线索成本转化沟通行课全链路数据

## 2. 表用途

用于线索、有效线索、转化、科目人次、联报、收款、退款、净营收、渠道映射、部门架构和员工维度分析。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

data-map 高频统计：500 条成功 SQL 中出现 10 次，占比 2.0%。

## 3. 数据粒度

线索-渠道-转化全链路明细，小时快照粒度待确认。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |
| hour | string | 小时级分区 HH | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 | 来源 |
|---|---|---|---|---|---|
| first_department_name | string | 'H业务线' | 是 | 渠道属性-一级部门name | 按 row_permissions 同层级历史取值补充 |
| second_department_name | string | '精品班学部' | 是 | 渠道属性-二级部门name | 按 row_permissions 同层级历史取值补充 |
| third_department_name | string | '学习顾问部' | 是 | 渠道属性-三级部门name | 按 row_permissions 同层级历史取值补充 |
| section_assign_employee_first_level_department_name | string | 'H业务线' | 是 | 员工_期截面时间_一级部门name | 按 row_permissions 同层级历史取值补充 |
| section_assign_employee_second_level_department_name | string | '精品班学部' | 是 | 员工_期截面时间_二级部门name | 按 row_permissions 同层级历史取值补充 |
| section_assign_employee_third_level_department_name | string | '学习顾问部' | 是 | 员工_期截面时间_三级部门name | 按 row_permissions 同层级历史取值补充 |
| virtual_first_department_name | string | 'H业务线' | 是 | 员工-最新-虚拟架构一级部门名称 | 按 row_permissions 同层级历史取值补充 |
| virtual_second_department_name | string | '精品班学部' | 是 | 员工-最新-虚拟架构二级部门名称 | 按 row_permissions 同层级历史取值补充 |
| virtual_third_department_name | string | '学习顾问部' | 是 | 员工-最新-虚拟架构三级部门名称 | 按 row_permissions 同层级历史取值补充 |
| virtual_fourth_department_name | string | '<待填写>' | 是 | 员工-最新-虚拟架构四级部门名称 | 待人工确认 |
| virtual_fifth_department_name | string | '<待填写>' | 是 | 员工-最新-虚拟架构五级部门名称 | 待人工确认 |
| period_mapping_first_level_department_name | string | 'H业务线' | 是 | 期归属一级部门name | 按 row_permissions 同层级历史取值补充 |
| period_mapping_second_level_department_name | string | '精品班学部' | 是 | 期归属二级部门name | 按 row_permissions 同层级历史取值补充 |
| period_mapping_third_level_department_name | string | '学习顾问部' | 是 | 期归属三级部门名称 | 按 row_permissions 同层级历史取值补充 |
| main_period_mapping_first_level_department_name | string | 'H业务线' | 是 | 主期映射一级部门 | 按 row_permissions 同层级历史取值补充 |
| main_period_mapping_second_level_department_name | string | '精品班学部' | 是 | 主期映射二级部门 | 按 row_permissions 同层级历史取值补充 |
| manager_first_level_department_name | string | 'H业务线' | 是 | 截面管理人-组织架构一级部门名称 | 按 row_permissions 同层级历史取值补充 |
| manager_second_level_department_name | string | '精品班学部' | 是 | 截面管理人-组织架构二级部门名称 | 按 row_permissions 同层级历史取值补充 |
| manager_third_level_department_name | string | '学习顾问部' | 是 | 截面管理人-组织架构三级部门名称 | 按 row_permissions 同层级历史取值补充 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| hour | string | 小时级分区 HH | 分区过滤 | 是 |
| lead_id | bigint | 线索id | 主键/关联键 | 是 |
| gy_trace_id | bigint | 线索归因留痕id | 待按需求确认 | 否 |
| trace_type | bigint | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 待按需求确认 | 否 |
| trace_type_name | string | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 待按需求确认 | 否 |
| final_new_source | string | 线索留痕source | 待按需求确认 | 否 |
| first_department_code | bigint | 渠道属性-一级部门code | 常用维度 | 是 |
| first_department_name | string | 渠道属性-一级部门name | 权限/业务范围限定 | 是 |
| second_department_code | bigint | 渠道属性-二级部门code | 常用维度 | 是 |
| second_department_name | string | 渠道属性-二级部门name | 权限/业务范围限定 | 是 |
| third_department_code | bigint | 渠道属性-三级部门code | 常用维度 | 是 |
| third_department_name | string | 渠道属性-三级部门name | 权限/业务范围限定 | 是 |
| put_plan_id | string | 渠道属性-投放计划id | 待按需求确认 | 否 |
| put_plan_name | string | 渠道属性-投放计划名称 | 待按需求确认 | 否 |
| plan_create_email_prefix | string | 渠道属性-计划创建人用户名-邮箱前缀 | 待按需求确认 | 否 |
| plan_create_email_name | string | 渠道属性-计划创建人-带数字名字 | 待按需求确认 | 否 |
| source_manager_username | string | 渠道属性-source管理人邮箱前缀 | 待按需求确认 | 否 |
| source_manager_name | string | 渠道属性-source管理人-带数字名字 | 待按需求确认 | 否 |
| channel_name_1 | string | 渠道属性-渠道树一级名称 | 常用维度 | 是 |
| channel_name_2 | string | 渠道属性-渠道树二级名称 | 常用维度 | 是 |
| channel_name_3 | string | 渠道属性-渠道树三级名称 | 常用维度 | 是 |
| flow_pool_id | bigint | 渠道属性-流量池id | 待按需求确认 | 否 |
| flow_pool_name | string | 渠道属性-流量池name | 待按需求确认 | 否 |
| channel_provider_id | bigint | 渠道属性-一级渠道商id | 常用维度 | 是 |
| channel_provider_name | string | 渠道属性-一级渠道商name | 常用维度 | 是 |
| channel_second_provider_id | string | 渠道属性-二级渠道商id | 常用维度 | 是 |
| channel_second_provider_name | string | 渠道属性-二级渠道商name | 常用维度 | 是 |
| get_customer_way_id | bigint | 渠道属性-获客方式id | 待按需求确认 | 否 |
| get_customer_way_name | string | 渠道属性-获客方式name | 待按需求确认 | 否 |
| get_customer_way_parent_id | bigint | 渠道属性-获客方式父级id | 待按需求确认 | 否 |
| get_customer_way_parent_name | string | 渠道属性-获客方式父级name | 待按需求确认 | 否 |
| flow_original_order_activity_number | bigint | 联报活动ID | 待按需求确认 | 否 |
| flow_original_order_activity_name | string | 联报活动名称 | 待按需求确认 | 否 |
| flow_original_order_activity_price | double | 联报活动售价 | 指标聚合 | 是 |
| lead_purchase_intention_id | bigint | 购买意向id | 待按需求确认 | 否 |
| lead_purchase_intention_name | string | 购买意向name | 待按需求确认 | 否 |
| lead_purchase_intention_level1_category_id | bigint | 购买意向-一级品类id | 待按需求确认 | 否 |
| lead_purchase_intention_level1_category_name | string | 购买意向-一级品类name | 待按需求确认 | 否 |
| lead_purchase_intention_level2_category_id | bigint | 购买意向-二级品类id | 待按需求确认 | 否 |
| lead_purchase_intention_level2_category_name | string | 购买意向-二级品类name | 待按需求确认 | 否 |
| section_assign_intention_level | string | 截面分配-分配意向度 | 待按需求确认 | 否 |
| employee_email_prefix | string | 员工_邮箱前缀 | 常用维度 | 是 |
| employee_email_name | string | 员工_姓名数字 | 常用维度 | 是 |
| section_assign_employee_first_level_department_code | bigint | 员工_期截面时间_一级部门code | 常用维度 | 是 |
| section_assign_employee_first_level_department_name | string | 员工_期截面时间_一级部门name | 权限/业务范围限定 | 是 |
| section_assign_employee_second_level_department_code | bigint | 员工_期截面时间_二级部门code | 常用维度 | 是 |
| section_assign_employee_second_level_department_name | string | 员工_期截面时间_二级部门name | 权限/业务范围限定 | 是 |
| section_assign_employee_third_level_department_code | bigint | 员工_期截面时间_三级部门code | 常用维度 | 是 |
| section_assign_employee_third_level_department_name | string | 员工_期截面时间_三级部门name | 权限/业务范围限定 | 是 |
| virtual_first_department_name | string | 员工-最新-虚拟架构一级部门名称 | 权限/业务范围限定 | 是 |
| virtual_second_department_name | string | 员工-最新-虚拟架构二级部门名称 | 权限/业务范围限定 | 是 |
| virtual_third_department_name | string | 员工-最新-虚拟架构三级部门名称 | 权限/业务范围限定 | 是 |
| virtual_fourth_department_name | string | 员工-最新-虚拟架构四级部门名称 | 权限/业务范围限定 | 是 |
| virtual_fifth_department_name | string | 员工-最新-虚拟架构五级部门名称 | 权限/业务范围限定 | 是 |
| virtual_leader_email_name | string | 员工-最新-虚拟架构大组长 | 待按需求确认 | 否 |
| virtual_direct_leader_email_name | string | 员工-最新-虚拟架构小组长 | 待按需求确认 | 否 |
| user_id | bigint | userid | 主键/关联键 | 是 |
| is_blacklist_user | string | 用户是否黑名单 | 待按需求确认 | 否 |
| period_number | string | 期次code | 常用维度 | 是 |
| period_name | string | 期name | 常用维度 | 是 |
| period_mapping_first_level_department_code | bigint | 期归属一级部门code | 常用维度 | 是 |
| period_mapping_first_level_department_name | string | 期归属一级部门name | 权限/业务范围限定 | 是 |
| period_mapping_second_level_department_code | bigint | 期归属二级部门code | 常用维度 | 是 |
| period_mapping_second_level_department_name | string | 期归属二级部门name | 权限/业务范围限定 | 是 |
| period_first_level_course_project_code | bigint | 一级项目code | 常用维度 | 是 |
| period_first_level_course_project_name | string | 一级项目name | 常用维度 | 是 |
| period_second_level_course_project_code | bigint | 二级项目code | 常用维度 | 是 |
| period_second_level_course_project_name | string | 二级项目name | 常用维度 | 是 |
| period_clazz_begin_time | string | 开课日期 | 常用维度 | 是 |
| period_main_teacher_numbers | string | 主讲 | 常用维度 | 是 |
| period_main_teacher_nicknames | string | 主讲昵称 | 常用维度 | 是 |
| period_course_category_code | string | 课程类型，eg：10-公开课｜20-体验课｜30-专题课｜40-系列课 | 常用维度 | 是 |
| lead_period_first_level_subject_code | bigint | 课程品类一级code | 常用维度 | 是 |
| lead_period_first_level_subject_name | string | 课程品类一级name | 常用维度 | 是 |
| lead_period_second_level_subject_code | bigint | 课程品类二级code | 常用维度 | 是 |
| lead_period_second_level_subject_name | string | 课程品类二级name | 常用维度 | 是 |
| lead_period_third_level_subject_code | bigint | 课程品类三级code | 常用维度 | 是 |
| lead_period_third_level_subject_name | string | 课程品类三级name | 常用维度 | 是 |
| period_conversion_begin_time | string | 转化开始时间 | 常用维度 | 是 |
| period_conversion_end_time | string | 转化结束时间 | 常用维度 | 是 |
| group_period_year | string | 期分组_期年 | 常用维度 | 是 |
| group_period_term | string | 期分组_期次 | 常用维度 | 是 |
| group_period_name | string | 期分组_期名称 | 常用维度 | 是 |
| lead_count | bigint | 线索数 | 指标聚合 | 是 |
| friend_lead_count | bigint | 加微数 | 指标聚合 | 是 |
| lead_cost | double | 单线索成本（含解密费用，单位：元） | 待按需求确认 | 否 |
| assign_lead_count | bigint | 分配线索数 | 指标聚合 | 是 |
| no_assign_lead | bigint | 未分配线索数（废弃） | 待按需求确认 | 否 |
| valid_lead_count | bigint | 有效线索数 | 指标聚合 | 是 |
| section_assign_call_connected_count | bigint | 截面分配-分配后电话接通次数 | 指标聚合 | 是 |
| section_assign_call_missed_count | bigint | 截面分配-分配后电话未接通次数 | 指标聚合 | 是 |
| section_assign_all_call_duration | bigint | 截面分配-分配后总通话时长(s) | 指标聚合 | 是 |
| section_assign_call_duration | bigint | 截面分配-分配后电话通话时长(s) | 指标聚合 | 是 |
| period_is_login_app | bigint | 期内是否登录APP | 常用维度 | 是 |
| waiting_time | bigint | 线索行课等待时长（秒） | 时间分析 | 否 |
| first_conversion_taketime | bigint | 线索首次转化时长（秒） | 时间分析 | 否 |
| order_count | bigint | 转化订单数 | 指标聚合 | 是 |
| subject_count | bigint | 转化科目人次 | 指标聚合 | 是 |
| lb_subject_count | bigint | 联报科目数 | 指标聚合 | 是 |
| conversion_lead_count | bigint | 转化线索数 | 指标聚合 | 是 |
| income_amount | double | 收款金额 | 指标聚合 | 是 |
| in_pay_period_refund_amount | double | 同期退款金额 | 指标聚合 | 是 |
| non_pay_period_refund_amount | double | 跨期退款金额 | 指标聚合 | 是 |
| jp_cross_department_refund_amount | double | 精品班_跨学部退款金额 | 指标聚合 | 是 |
| same_lead_period_order_count | bigint | 当期_转化订单数 | 指标聚合 | 是 |
| same_lead_period_subject_count | bigint | 当期_转化科目人次 | 指标聚合 | 是 |
| same_lead_period_lb_subject_count | bigint | 当期_联报科目数 | 指标聚合 | 是 |
| same_lead_period_conversion_lead_count | bigint | 当期_转化线索数 | 指标聚合 | 是 |
| same_lead_period_income_amount | double | 当期_收款金额 | 指标聚合 | 是 |
| same_lead_period_refund_amount | double | 当期_退款金额 | 指标聚合 | 是 |
| same_department_order_count | bigint | 同学部_转化订单数 | 指标聚合 | 是 |
| same_department_subject_count | bigint | 同学部_转化科目人次 | 指标聚合 | 是 |
| same_department_lb_subject_count | bigint | 同学部_联报科目数 | 指标聚合 | 是 |
| same_department_conversion_lead_count | bigint | 同学部_转化线索数 | 指标聚合 | 是 |
| same_department_income_amount | double | 同学部_收款金额 | 指标聚合 | 是 |
| same_department_in_pay_period_refund_amount | double | 同学部_同期退款金额 | 指标聚合 | 是 |
| same_department_non_pay_period_refund_amount | double | 同学部_跨期退款金额 | 指标聚合 | 是 |
| virtual_mini_leader_email_name | string | 员工-最新-虚拟架构帮带师傅带数字名称 | 待按需求确认 | 否 |
| rn | bigint | 辅助-区分是否分母 | 待按需求确认 | 否 |
| lead_period_order_count | bigint | 线索期_转化订单数 | 指标聚合 | 是 |
| lead_period_conversion_lead_count | bigint | 线索期_转化线索数 | 指标聚合 | 是 |
| lead_period_income_amount | double | 线索期_收款金额 | 指标聚合 | 是 |
| lead_period_refund_amount | double | 线索期_退款金额 | 指标聚合 | 是 |
| lead_period_same_department_order_count | bigint | 线索期_同学部转化订单数 | 指标聚合 | 是 |
| lead_period_same_department_conversion_lead_count | bigint | 线索期_同学部转化线索数 | 指标聚合 | 是 |
| lead_period_same_department_income_amount | double | 线索期_同学部收款金额 | 指标聚合 | 是 |
| lead_period_same_department_refund_amount | double | 线索期_同学部退款金额 | 指标聚合 | 是 |
| same_lead_period_department_order_count | bigint | 当期_同学部转化订单数 | 指标聚合 | 是 |
| same_lead_period_department_conversion_lead_count | bigint | 当期_同学部转化线索数 | 指标聚合 | 是 |
| same_lead_period_department_income_amount | double | 当期_同学部收款金额 | 指标聚合 | 是 |
| same_lead_period_department_refund_amount | double | 当期_同学部退款金额 | 指标聚合 | 是 |
| same_lead_period_department_subject_count | bigint | 同线索期同学部转化科目数 | 指标聚合 | 是 |
| same_lead_period_department_lb_subject_count | bigint | 同线索期同学部转化联报科目数 | 指标聚合 | 是 |
| flow_order_clazz_name | string | 引流课-班级名称 | 待按需求确认 | 否 |
| flow_order_clazz_biz_number | string | 引流课-班级业务编号 | 待按需求确认 | 否 |
| data_type | bigint | 数据类型：1-可用，0-不可用 | 待按需求确认 | 否 |
| lead_create_time | string | 线索创建时间 | 时间分析 | 否 |
| trade_period_income_order_count | bigint | 流水期-收款订单数 | 指标聚合 | 是 |
| trade_period_income_zhsy_subject_count | bigint | 流水期-综合素养-收款联报科目数 | 指标聚合 | 是 |
| trade_period_income_subject_count | bigint | 流水期-收款科目数 | 指标聚合 | 是 |
| trade_period_income_lb_subject_count | bigint | 流水期-收款联报科目数 | 指标聚合 | 是 |
| trade_period_income_lead_count | bigint | 流水期-收款线索数 | 指标聚合 | 是 |
| trade_period_before_nth_lesson_refund_amount | double | 流水期-开课nth-退款金额 | 指标聚合 | 是 |
| trade_period_department_income_order_count | bigint | 流水期-同学部-收款订单数 | 指标聚合 | 是 |
| trade_period_department_income_zhsy_subject_count | bigint | 流水期-同学部-综合素养-收款联报科目数 | 指标聚合 | 是 |
| trade_period_department_income_subject_count | bigint | 流水期-同学部-收款科目数 | 指标聚合 | 是 |
| trade_period_department_income_lb_subject_count | bigint | 流水期-同学部-收款联报科目数 | 指标聚合 | 是 |
| trade_period_department_income_lead_count | bigint | 流水期-同学部-收款线索数 | 指标聚合 | 是 |
| trade_period_department_before_nth_lesson_refund_amount | double | 流水期-同学部-开课nth-退款金额 | 指标聚合 | 是 |
| current_period_income_order_count | bigint | 当期-收款订单数 | 指标聚合 | 是 |
| current_period_income_zhsy_subject_count | bigint | 当期-综合素养-收款联报科目数 | 指标聚合 | 是 |
| current_period_income_subject_count | bigint | 当期-收款科目数 | 指标聚合 | 是 |
| current_period_income_lb_subject_count | bigint | 当期-收款联报科目数 | 指标聚合 | 是 |
| current_period_income_lead_count | bigint | 当期-收款线索数 | 指标聚合 | 是 |
| current_period_before_nth_lesson_refund_amount | double | 当期-开课nth-退款金额 | 指标聚合 | 是 |
| current_period_department_income_order_count | bigint | 当期-同学部-收款订单数 | 指标聚合 | 是 |
| current_period_department_income_zhsy_subject_count | bigint | 当期-同学部-综合素养-收款联报科目数 | 指标聚合 | 是 |
| current_period_department_income_subject_count | bigint | 当期-同学部-收款科目数 | 指标聚合 | 是 |
| current_period_department_income_lb_subject_count | bigint | 当期-同学部-收款联报科目数 | 指标聚合 | 是 |
| current_period_department_income_lead_count | bigint | 当期-同学部-收款线索数 | 指标聚合 | 是 |
| current_period_department_before_nth_lesson_refund_amount | double | 当期-同学部-开课nth-退款金额 | 指标聚合 | 是 |
| province_name | string | 省份 | 待按需求确认 | 否 |
| city_name | string | 城市 | 待按需求确认 | 否 |
| city_level_name | string | 城市等级 | 待按需求确认 | 否 |
| sku_id | string | 落地页上报，用户进入的页面关联的sku_id | 待按需求确认 | 否 |
| sku_id_name | string | 落地页上报，用户进入的页面关联的sku_id_name | 待按需求确认 | 否 |
| promoter_name | string | 推广员姓名 | 待按需求确认 | 否 |
| rule_name | string | 分配规则 | 待按需求确认 | 否 |
| qw_add_time | string | 添加企微时间 | 时间分析 | 否 |
| gw_add_time | string | 添加个微时间 | 时间分析 | 否 |
| first_call_time | string | 分配后首call时间 | 时间分析 | 否 |
| touch_duration_second | bigint | 触达时长（秒） | 指标聚合 | 是 |
| learning_attitude | string | 学习态度 | 待按需求确认 | 否 |
| academic_record | string | 成绩 | 待按需求确认 | 否 |
| weak_subject | string | 薄弱学科 | 常用维度 | 是 |
| weak_point_comment | string | 薄弱点 | 待按需求确认 | 否 |
| boarder_status | string | 走读/住校 | 待按需求确认 | 否 |
| boarder_note | string | 住校/走读说明 | 待按需求确认 | 否 |
| tutoring | string | 补习情况 | 待按需求确认 | 否 |
| tutoring_note | string | 补习情况说明 | 待按需求确认 | 否 |
| learn_situation_comment | string | 学情/深沟 | 待按需求确认 | 否 |
| refund_warn_desc | string | 高危退费说明 | 待按需求确认 | 否 |
| refund_warn_comment | string | 高危退费(文本) | 待按需求确认 | 否 |
| follow_up_content | string | 跟进内容 | 待按需求确认 | 否 |
| deep_communicate_method | string | 深沟方式 | 待按需求确认 | 否 |
| deep_communicate_duration | string | 深沟时长 | 指标聚合 | 是 |
| is_pre_signup | string | 是否预报名 | 待按需求确认 | 否 |
| pre_sign_up | string | 预报名学科 | 待按需求确认 | 否 |
| consumptionpower | string | 付费能力 | 待按需求确认 | 否 |
| payment_ability | string | 支付能力 | 待按需求确认 | 否 |
| contact_role_note | string | 联系人角色 | 待按需求确认 | 否 |
| intention_level | string | 意向度 | 待按需求确认 | 否 |
| is_baseline_exam_user | string | 是否参加摸底测验 | 待按需求确认 | 否 |
| user_age | bigint | 用户年龄 | 待按需求确认 | 否 |
| user_sex | bigint | 用户性别 | 待按需求确认 | 否 |
| ad_account_id | string | 平台账户ID | 指标聚合 | 是 |
| ad_account_name | string | 平台账户名称 | 指标聚合 | 是 |
| ad_model_id | bigint | 投放模式ID | 待按需求确认 | 否 |
| ad_model_name | string | 投放模式NAME | 待按需求确认 | 否 |
| clazz_room_type | int | 授课模式 1-大班课 2-小班课 3-一对一 | 待按需求确认 | 否 |
| lead_count_zhsy | string | 线索量-zhsy | 指标聚合 | 是 |
| period_mapping_third_level_department_code | bigint | 期归属三级部门code | 常用维度 | 是 |
| period_mapping_third_level_department_name | string | 期归属三级部门名称 | 权限/业务范围限定 | 是 |
| xz_internal_contact_email_prefix | string | 先知投放账户内部管理人邮箱前缀 | 待按需求确认 | 否 |
| xz_internal_contact_email_name | string | 先知投放账户内部管理人姓名+数字 | 待按需求确认 | 否 |
| section_assign_time | string | 截面分配-分配时间 | 时间分析 | 否 |
| flow_order_number | string | 主留痕引流课-订单编号 | 待按需求确认 | 否 |
| flow_order_pay_success_timestamp | string | 主留痕引流课-支付成功时间戳 | 时间分析 | 否 |
| flow_order_full_refund_timestamp | string | 主留痕引流课-完全退款时间戳 | 时间分析 | 否 |
| flow_order_price | string | 主留痕引流课-订单价格 | 指标聚合 | 是 |
| is_refund_before_clazz_begin | bigint | 是否课前退费（crm系统字段） 0:否，1:是 | 待按需求确认 | 否 |
| flow_latest_order_full_refund_timestamp | string | 主留痕引流课-最新子订单完全退款时间戳 | 时间分析 | 否 |
| friend_status_name | string | 好友状态名（流量表字段） | 待按需求确认 | 否 |
| first_login_time | string | 首次登录时间 | 时间分析 | 否 |
| lead_period_subject_count | bigint | 线索期_转化科目人次 | 指标聚合 | 是 |
| lead_period_same_dept_subject_count | bigint | 线索期_同学部_转化科目人次 | 指标聚合 | 是 |
| main_period_code | bigint | 主期编号 | 常用维度 | 是 |
| main_period_name | string | 主期名称 | 常用维度 | 是 |
| main_period_clazz_begin_date | string | 主期开课日期 | 常用维度 | 是 |
| main_period_conversion_begin_time | string | 主期转化开始时间 | 常用维度 | 是 |
| main_period_conversion_end_time | string | 主期转化结束时间 | 常用维度 | 是 |
| main_period_first_level_course_project_name | string | 主期一级项目 | 常用维度 | 是 |
| main_period_mapping_first_level_department_name | string | 主期映射一级部门 | 权限/业务范围限定 | 是 |
| main_period_mapping_second_level_department_name | string | 主期映射二级部门 | 权限/业务范围限定 | 是 |
| target_assign_lead_count_per_lead | double | 目标分配线索数/实际线索量 | 指标聚合 | 是 |
| target_same_department_conversion_lead_count_per_lead | double | 目标同部门转化线索数/实际线索量 | 指标聚合 | 是 |
| target_same_department_net_conversion_per_lead | double | 目标同部门净收款金额/实际线索量 | 常用维度 | 是 |
| target_lead_cost_per_lead | double | 目标线索成本/实际线索量 | 待按需求确认 | 否 |
| target_market_lead_cost_per_lead | double | 目标市场人员成本/实际线索量 | 待按需求确认 | 否 |
| target_consultant_lead_cost_per_lead | double | 目标顾问人员成本/实际线索量 | 待按需求确认 | 否 |
| flow_orders_income_amount | double | 线索引流课收款金额 | 指标聚合 | 是 |
| flow_orders_refund_amount | double | 线索引流课退款金额 | 指标聚合 | 是 |
| stats_grade_name | string | 统计口径线索年级 | 常用维度 | 是 |
| business_id | string | 直播账号uid | 待按需求确认 | 否 |
| business_nickname | string | 直播账号昵称 | 待按需求确认 | 否 |
| assign_valid_lead_count | bigint | 有效分配线索量 | 指标聚合 | 是 |
| crm_intention_level | bigint | 意向等级，1-A、2-B、3-C、4-D | 待按需求确认 | 否 |
| target_same_department_subject_count_per_lead | double | 目标-同部门转化科目数/实际线索量 | 指标聚合 | 是 |
| live_streaming_host_id | string | 三方订单主播 | 待按需求确认 | 否 |
| source_put_plan_id | bigint | source上的put_plan_id | 待按需求确认 | 否 |
| source_put_plan_name | string | source上的put_plan_name | 待按需求确认 | 否 |
| live_lead_cost | double | 直播-单线索成本(不含解密费用，单位：元，目的：集团使用) | 待按需求确认 | 否 |
| decrypt_fee_lead_cost | double | 解密费用(单位：元) | 待按需求确认 | 否 |
| period_type | string | 期类型 | 常用维度 | 是 |
| zhsy_channel_name_1 | string | zhsy-一级渠道 | 常用维度 | 是 |
| zhsy_channel_name_2 | string | zhsy-二级渠道 | 常用维度 | 是 |
| zhsy_channel_name_3 | string | zhsy-三级渠道 | 常用维度 | 是 |
| h_channel_name_1 | string | h-一级渠道 | 常用维度 | 是 |
| yw_channel_name_1 | string | yw_一级渠道 | 常用维度 | 是 |
| yw_channel_name_2 | string | yw_二级渠道 | 常用维度 | 是 |
| yw_channel_name_3 | string | yw_三级渠道 | 常用维度 | 是 |
| section_assign_first_call_connected_time | string | 截面分配-分配后首次接通时间 | 时间分析 | 否 |
| flow_pool_type_id | string | 流量池类型id | 待按需求确认 | 否 |
| flow_pool_type_name | string | 流量池类型名称 | 待按需求确认 | 否 |
| page_id | string | 落地页id | 待按需求确认 | 否 |
| page_id_name | string | 落地页名称 | 待按需求确认 | 否 |
| page_type | string | 落地页页面类型 | 待按需求确认 | 否 |
| page_type_name | string | 落地页页面类型名称 | 待按需求确认 | 否 |
| trade_period_yw_conversion_subject_count | bigint | 流水期_语文转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 指标聚合 | 是 |
| trade_period_sx_conversion_subject_count | bigint | 流水期_数学转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 指标聚合 | 是 |
| trade_period_yy_conversion_subject_count | bigint | 流水期_英语转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 指标聚合 | 是 |
| trade_period_wl_conversion_subject_count | bigint | 流水期_物理转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 指标聚合 | 是 |
| trade_period_hx_conversion_subject_count | bigint | 流水期_化学转化科目数。需求文档：https://gaotuedu.feishu.cn/wiki/XV41wWmcbiQpUukbSi7cyavPnBg | 指标聚合 | 是 |
| manager_type | int | 1-xxl、2-sw、3-dzhk、4-sn、5-source | 待按需求确认 | 否 |
| manager_email_prefix | string | 截面管理人邮箱前缀 | 待按需求确认 | 否 |
| manager_first_level_department_code | bigint | 截面管理人-组织架构一级部门编码 | 常用维度 | 是 |
| manager_first_level_department_name | string | 截面管理人-组织架构一级部门名称 | 权限/业务范围限定 | 是 |
| manager_second_level_department_code | bigint | 截面管理人-组织架构二级部门编码 | 常用维度 | 是 |
| manager_second_level_department_name | string | 截面管理人-组织架构二级部门名称 | 权限/业务范围限定 | 是 |
| manager_third_level_department_code | bigint | 截面管理人-组织架构三级部门编码 | 常用维度 | 是 |
| manager_third_level_department_name | string | 截面管理人-组织架构三级部门名称 | 权限/业务范围限定 | 是 |
| third_platform_live_anchor_id | string | 获客-三方平台直播-主播ID | 待按需求确认 | 否 |
| third_platform_live_anchor_name | string | 获客-三方平台直播-主播名称 | 待按需求确认 | 否 |
| third_platform_live_begin_timestamp | string | 获客-三方平台直播-直播开始时间 | 时间分析 | 否 |
| third_platform_live_end_timestamp | string | 获客-三方平台直播-直播结束时间 | 时间分析 | 否 |
| lead_model_type | bigint | 线索模型类型 0:线索 1:潜客 | 待按需求确认 | 否 |
| lead_model_type_name | string | 线索模型类型 0:线索 1:潜客 | 待按需求确认 | 否 |
| live_lead_effect_timestamp | timestamp | 获客-三方平台直播-订单支付时间 | 时间分析 | 否 |
| merge_lead_count | bigint | 合并线索量 | 指标聚合 | 是 |
| merge_assign_lead_count | bigint | 合并分配线索量 | 指标聚合 | 是 |
| merge_valid_lead_count | bigint | 合并有效线索量 | 指标聚合 | 是 |
| merge_assign_valid_lead_count | bigint | 合并分配有效线索量 | 指标聚合 | 是 |

## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`
- `t.first_department_name = 'H业务线'`
- `t.second_department_name = '精品班学部'`
- `t.third_department_name = '学习顾问部'`
- `t.section_assign_employee_first_level_department_name = 'H业务线'`
- `t.section_assign_employee_second_level_department_name = '精品班学部'`
- `t.section_assign_employee_third_level_department_name = '学习顾问部'`
- `t.virtual_first_department_name = 'H业务线'`
- `t.virtual_second_department_name = '精品班学部'`
- `t.virtual_third_department_name = '学习顾问部'`
- `t.virtual_fourth_department_name = '<待填写>'`
- `t.virtual_fifth_department_name = '<待填写>'`
- `t.period_mapping_first_level_department_name = 'H业务线'`
- `t.period_mapping_second_level_department_name = '精品班学部'`
- `t.period_mapping_third_level_department_name = '学习顾问部'`
- `t.main_period_mapping_first_level_department_name = 'H业务线'`
- `t.main_period_mapping_second_level_department_name = '精品班学部'`
- `t.manager_first_level_department_name = 'H业务线'`
- `t.manager_second_level_department_name = '精品班学部'`
- `t.manager_third_level_department_name = '学习顾问部'`

## 9. 常用 join key

- `lead_id`：线索关联/去重
- `user_id`：用户关联
- `employee_email_prefix`：员工邮箱前缀关联
- `employee_email_name`：员工姓名关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.lead_id,
    t.user_id,
    t.employee_email_prefix,
    t.employee_email_name,
    t.channel_name_1,
    t.channel_name_2,
    t.period_name,
    t.income_amount,
    t.lead_count,
    t.virtual_fourth_department_name,
    t.virtual_third_department_name,
    t.third_department_name,
    t.section_assign_employee_third_level_department_name,
    t.second_department_name
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.first_department_name = 'H业务线'
  and t.second_department_name = '精品班学部'
  and t.third_department_name = '学习顾问部'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 283。
- 所属项目：大数据-数据分析；owner：崔帅杰。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 283。
- 所属项目：大数据-数据分析；owner：崔帅杰。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 283。
- 所属项目：大数据-数据分析；owner：崔帅杰。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 该表在历史看板 SQL 中库名前缀为 `bdg_ba`，优先使用 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`。
- 金额字段在看板 SQL 中统一 `/ 100`，推断原始单位为分，需业务确认。
- 部分历史 SQL 使用 `dt = now() - 2 hour` 且 `hour = now() - 3 hour`，时间偏移不一致，复用时必须确认原因。
- `lead_assign_plan_actual_valid_count.sql` 也使用 `dt = now() - 2 hour` 且 `hour = now() - 3 hour` 汇总实际 `lead_count`、`valid_lead_count`；同一查询的计划侧小时为 `now() - 2 hour`，复用时需确认分区延迟口径。
- `period_name` 是否为原始字段或仅为 select 别名存在歧义，生成 SQL 时如需同层引用应改成 CTE 后再引用。
- `channel_map` 规则非常长，完整逻辑见 `resources/raw_sql/market_consultant_conversion.sql`。
- 待人工确认：字段类型、主键唯一性、金额单位、转化指标和合并线索指标口径。

### 流量画像 SQL 使用备注

- `traffic_profile.sql` 继续以该表为主表；2026-05-15 `city_channel.txt` 版本输出粒度包含 `province_name`、`city_name`、`city_level_name`、`last_app_channel` 和成交科目档位 `sub`。
- 该 SQL 的主表范围为 `section_assign_employee_* = H业务线/市场部/市场顾问部`，期次映射二级部门允许 `精品班学部`、`青橙项目部`、`一对一学部`、`本地化大班学部`、`市场部`、`菁英班学部`。
- 当前 `city_channel.txt` 版本主表分区使用 `dt = now() - 2 hour` 且 `hour = now() - 2 hour`；旧版曾出现 `hour = now() - 3 hour`，复用时需确认分区延迟口径。
- `province_name`、`city_name`、`city_level_name` 字段已在字段目录中存在，但省市归属和城市等级口径未由独立指标文档确认，需标记待人工确认。
- `first_call_time_diff_hour` 来自 `date_diff('hour', section_assign_time, first_call_time)`，再派生 24/48 小时首呼指标；使用前需确认两个时间字段格式可直接 cast 为 timestamp。
- `channel_map` 在该 SQL 中仍为超长 CASE，且部分分支同层引用派生 `period_name`，生成新 SQL 时建议先拆出 `period_name` CTE 后再引用。
