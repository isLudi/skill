# service_dw.dm_crm_lead_stats_detail_hf

## 1. 中文名称

线索统计公共明细层

## 2. 表用途

线索统计公共明细，包含线索状态、来源渠道、部门映射、截面分配和成本等信息。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

data-map 高频统计：500 条成功 SQL 中出现 1 次，占比 0.2%。

## 3. 数据粒度

线索-小时粒度，待确认

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级分区 yyyyMMdd | 是 |
| hour | string | 小时分区 HH | 是 |
## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 | 来源 |
|---|---|---|---|---|---|
| top_department_name | string | '<待填写>' | 是 | 渠道属性-集团名称 | 待人工确认 |
| first_department_name | string | 'H业务线' | 是 | 渠道属性-一级部门名称 | 按 row_permissions 同层级历史取值补充 |
| second_department_name | string | '精品班学部' | 是 | 渠道属性-二级部门名称 | 按 row_permissions 同层级历史取值补充 |
| third_department_name | string | '学习顾问部' | 是 | 渠道属性-三级部门名称 | 按 row_permissions 同层级历史取值补充 |
| mapping_top_level_department_name | string | '<待填写>' | 是 | 线索归属期映射 top部门name | 待人工确认 |
| mapping_first_level_department_name | string | 'H业务线' (1次) | 是 | 线索归属期映射 一级部门name | row_permissions 全局历史取值 |
| mapping_second_level_department_name | string | '精品班学部' (1次) | 是 | 线索归属期映射 二级部门name | row_permissions 全局历史取值 |
| section_assign_employee_top_level_department_name | string | '<待填写>' | 是 | 截面分配-分配顾问头部门名称 | 待人工确认 |
| section_assign_employee_first_level_department_name | string | 'H业务线' | 是 | 截面分配-分配顾问一级部门名称 | 按 row_permissions 同层级历史取值补充 |
| section_assign_employee_second_level_department_name | string | '精品班学部' | 是 | 截面分配-分配顾问二级部门名称 | 按 row_permissions 同层级历史取值补充 |
| section_assign_employee_third_level_department_name | string | '学习顾问部' | 是 | 截面分配-分配顾问三级部门名称 | 按 row_permissions 同层级历史取值补充 |
| manager_top_level_department_name | string | '<待填写>' | 是 | 管理人-组织架构顶级部门名称 | 待人工确认 |
| manager_first_level_department_name | string | 'H业务线' | 是 | 管理人-组织架构一级部门名称 | 按 row_permissions 同层级历史取值补充 |
| manager_second_level_department_name | string | '精品班学部' | 是 | 管理人-组织架构二级部门名称 | 按 row_permissions 同层级历史取值补充 |
| manager_third_level_department_name | string | '学习顾问部' | 是 | 管理人-组织架构三级部门名称 | 按 row_permissions 同层级历史取值补充 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| hour | string | 小时级分区 HH | 分区过滤 | 是 |
| lead_id | bigint | 线索id | 主键/关联键 | 是 |
| lead_purchase_intention_id | bigint | 线索购买意向 | 待按需求确认 | 否 |
| lead_purchase_intention_name | string | 线索意向name | 待按需求确认 | 否 |
| lead_purchase_intention_level1_category_id | bigint | 线索意向一级品类id | 待按需求确认 | 否 |
| lead_purchase_intention_level1_category_name | string | 线索意向一级品类name | 待按需求确认 | 否 |
| lead_create_time | string | 线索创建时间 | 时间分析 | 否 |
| lead_update_time | string | 线索更新时间 | 时间分析 | 否 |
| lead_state | int | 线索状态 1待分配 2已分配 3分配失败 4close线索生命周期结束 | 待按需求确认 | 否 |
| lead_state_name | string | 线索状态 1待分配 2已分配 3分配失败 4close线索生命周期结束 | 待按需求确认 | 否 |
| lead_state_change_reason | int | 线索状态变更原因 1.待分配：初始状态 2.分配失败：未配置规则（未在执行期）3.分配失败：未分配规则执行失败 4.正常分配 5.close:掉海 6.close:修改购买意向 7.close:顾问无服务能力 8.close:微信线索合并 9.异常中断导致分配失败 | 待按需求确认 | 否 |
| lead_state_change_reason_name | string | 线索状态变更原因 1.待分配：初始状态 2.分配失败：未配置规则（未在执行期）3.分配失败：未分配规则执行失败 4.正常分配 5.close:掉海 6.close:修改购买意向 7.close:顾问无服务能力 8.close:微信线索合并 9.异常中断导致分配失败 | 待按需求确认 | 否 |
| lead_assign_plan_id | bigint | 线索分配应用的规则下的计划id 只记录第一次分配计划id因为后面会走唯一性 | 待按需求确认 | 否 |
| gy_trace_id | bigint | 线索归因留痕id | 待按需求确认 | 否 |
| trace_scenario_type | int | 留痕录入场景，线上(1)/线下(2) | 待按需求确认 | 否 |
| trace_scenario_type_name | string | 留痕录入场景，线上(1)/线下(2) | 待按需求确认 | 否 |
| user_id | bigint | 用户id | 主键/关联键 | 是 |
| city_id | bigint | 城市ID | 待按需求确认 | 否 |
| trace_create_time | string | 留痕创建时间 | 时间分析 | 否 |
| trace_update_time | string | 留痕更新时间 | 时间分析 | 否 |
| trace_state | int | 留痕分配状态，0:初始状态，1:待分配，2:已分配，3:分配失败 | 待按需求确认 | 否 |
| trace_order_number | bigint | 留痕订单号 | 待按需求确认 | 否 |
| trace_type | int | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 待按需求确认 | 否 |
| trace_type_name | string | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 待按需求确认 | 否 |
| lead_derivative_dependence_leads_id | bigint | 衍生依赖的线索ID | 待按需求确认 | 否 |
| self_source | string | 留痕自身的source | 待按需求确认 | 否 |
| is_refund_before_clazz_begin | int | 是否课前退费（crm系统字段） 0:否，1:是 | 待按需求确认 | 否 |
| lead_org_id | bigint | 线索部门 | 待按需求确认 | 否 |
| lead_core_id | bigint | 线索唯一标致ID | 待按需求确认 | 否 |
| lead_model_type | int | 线索模型类型 0:线索 1:潜客 | 待按需求确认 | 否 |
| lead_model_type_name | string | 线索模型类型 0:线索 1:潜客 | 待按需求确认 | 否 |
| lead_previous_model_id | bigint | 线索上阶段模型ID(线索表的id) | 待按需求确认 | 否 |
| final_new_source | string | 线索留痕source | 待按需求确认 | 否 |
| wechat_id | string | 留痕用户wxid，入群或加好友后匹配 | 待按需求确认 | 否 |
| is_rq_trace | string | 留痕是否入群留痕，eg: Y-入群 \| N-未入群 | 待按需求确认 | 否 |
| chatroom | string | 留痕所属群 | 待按需求确认 | 否 |
| passage_id | bigint | 留痕入群通道id | 待按需求确认 | 否 |
| lead_provider_type | int | 线索分配类型 | 待按需求确认 | 否 |
| lead_provider_type_name | string | 线索分配类型 | 待按需求确认 | 否 |
| trace_rule_id | bigint | 留痕分配规则id | 待按需求确认 | 否 |
| trace_rule_name | string | 留痕分配规则name | 待按需求确认 | 否 |
| trace_assign_way | int | 留痕分配方式 1 权重平均 2 完全平均 3 顺序分配 | 待按需求确认 | 否 |
| trace_assign_way_name | string | 留痕分配方式 1 权重平均 2 完全平均 3 顺序分配 | 待按需求确认 | 否 |
| system_id | bigint | 渠道属性-应用系统id(source_access表的id) | 待按需求确认 | 否 |
| system_name | string | 渠道属性-投放系统名称 | 待按需求确认 | 否 |
| get_customer_way_id | bigint | 渠道属性-获客方式id | 待按需求确认 | 否 |
| get_customer_way_name | string | 渠道属性-获客方式 | 待按需求确认 | 否 |
| get_customer_way_parent_id | bigint | 渠道属性-获客方式父级ID | 待按需求确认 | 否 |
| get_customer_way_parent_name | string | 渠道属性-获客方式父级名称 | 待按需求确认 | 否 |
| flow_pool_id | bigint | 渠道属性-流量池id | 待按需求确认 | 否 |
| flow_pool_name | string | 渠道属性-流量池名称 | 待按需求确认 | 否 |
| flow_pool_type_id | bigint | 渠道属性-流量池类型id | 待按需求确认 | 否 |
| flow_pool_type_name | string | 渠道属性-流量池类型名称 | 待按需求确认 | 否 |
| resource_position_id | bigint | 渠道属性-资源位id | 待按需求确认 | 否 |
| resource_position_name | string | 渠道属性-资源位名称 | 待按需求确认 | 否 |
| resource_type_id | bigint | 渠道属性-资源位类型id | 待按需求确认 | 否 |
| resource_type_name | string | 渠道属性-资源位类型名称 | 待按需求确认 | 否 |
| put_plan_id | string | 渠道属性-投放计划id | 待按需求确认 | 否 |
| put_plan_name | string | 渠道属性-投放计划名称 | 待按需求确认 | 否 |
| plan_create_username | string | 渠道属性-计划创建人用户名-邮箱前缀 | 待按需求确认 | 否 |
| plan_create_name | string | 渠道属性-计划创建人-带数字名字 | 待按需求确认 | 否 |
| source_manager_username | string | 渠道属性-source管理人邮箱前缀 | 待按需求确认 | 否 |
| source_manager_name | string | 渠道属性-source管理人-带数字名字 | 待按需求确认 | 否 |
| tree_code | string | 渠道属性-组织结构 | 待按需求确认 | 否 |
| tree_name | string | 渠道属性-组织结构名称 | 待按需求确认 | 否 |
| top_department_code | bigint | 渠道属性-集团id | 常用维度 | 是 |
| top_department_name | string | 渠道属性-集团名称 | 权限/业务范围限定 | 是 |
| first_department_code | bigint | 渠道属性-一级部门id | 常用维度 | 是 |
| first_department_name | string | 渠道属性-一级部门名称 | 权限/业务范围限定 | 是 |
| second_department_code | bigint | 渠道属性-二级部门id | 常用维度 | 是 |
| second_department_name | string | 渠道属性-二级部门名称 | 权限/业务范围限定 | 是 |
| third_department_code | bigint | 渠道属性-三级部门id | 常用维度 | 是 |
| third_department_name | string | 渠道属性-三级部门名称 | 权限/业务范围限定 | 是 |
| channel_provider_id | bigint | 渠道属性-业务渠道商id | 常用维度 | 是 |
| channel_provider_name | string | 渠道属性-渠道商名称 | 常用维度 | 是 |
| channel_second_provider_id | bigint | 渠道属性-二级渠道商id | 常用维度 | 是 |
| channel_second_provider_name | string | 渠道属性-二级渠道商名称 | 常用维度 | 是 |
| channel_name_1 | string | 渠道属性-渠道树一级名称 | 常用维度 | 是 |
| channel_name_2 | string | 渠道属性-渠道树二级名称 | 常用维度 | 是 |
| channel_name_3 | string | 渠道属性-渠道树三级名称 | 常用维度 | 是 |
| channel_name_4 | string | 渠道属性-渠道树四级名称 | 常用维度 | 是 |
| channel_name_5 | string | 渠道属性-渠道树五级名称 | 常用维度 | 是 |
| flow_latest_order_number | bigint | 引流课-最新子订单编号 | 待按需求确认 | 否 |
| latest_trace_id | bigint | 主留痕最新子订单留痕 | 待按需求确认 | 否 |
| lead_period_number | bigint | 线索归属期number | 常用维度 | 是 |
| lead_period_name | string | 线索归属期name | 常用维度 | 是 |
| lead_period_course_category_id | int | 线索归属期 | 常用维度 | 是 |
| lead_period_course_tag | int | 线索归属期 | 常用维度 | 是 |
| lead_period_school_year | int | 线索归属期 | 常用维度 | 是 |
| lead_period_department | int | 线索归属期 | 常用维度 | 是 |
| lead_period_start_time | string | 线索归属期 | 常用维度 | 是 |
| lead_period_end_time | string | 线索归属期 | 常用维度 | 是 |
| lead_period_create_time | string | 线索归属期 | 常用维度 | 是 |
| lead_period_update_time | string | 线索归属期 | 常用维度 | 是 |
| lead_period_biz_type | int | 线索归属期 | 常用维度 | 是 |
| lead_period_is_test | int | 线索归属期 | 常用维度 | 是 |
| lead_period_project_id_path | string | 线索归属期 | 常用维度 | 是 |
| lead_period_show_category_id_path | string | 线索归属期 | 常用维度 | 是 |
| lead_period_show_teacher_list | string | 线索归属期 | 常用维度 | 是 |
| lead_period_clazz_begin_time | string | 线索归属期 | 常用维度 | 是 |
| lead_period_service_begin_time | string | 线索归属期 | 常用维度 | 是 |
| lead_period_conversion_begin_time | string | 线索归属期 | 常用维度 | 是 |
| lead_period_conversion_end_time | string | 线索归属期 | 常用维度 | 是 |
| mapping_top_level_department_code | string | 线索归属期映射 top部门code | 常用维度 | 是 |
| mapping_top_level_department_name | string | 线索归属期映射 top部门name | 权限/业务范围限定 | 是 |
| mapping_first_level_department_code | string | 线索归属期映射 一级部门code | 常用维度 | 是 |
| mapping_first_level_department_name | string | 线索归属期映射 一级部门name | 权限/业务范围限定 | 是 |
| mapping_second_level_department_code | string | 线索归属期映射 二级部门code | 常用维度 | 是 |
| mapping_second_level_department_name | string | 线索归属期映射 二级部门name | 权限/业务范围限定 | 是 |
| period_section_time | timestamp | 线索归属期映射 期截面时间 | 常用维度 | 是 |
| lead_period_first_level_course_project_code | string | 课程一级项目编码 | 常用维度 | 是 |
| lead_period_first_level_course_project_name | string | 课程一级项目名称 | 常用维度 | 是 |
| lead_period_second_level_course_project_code | string | 课程二级项目编码 | 常用维度 | 是 |
| lead_period_second_level_course_project_name | string | 课程二级项目名称 | 常用维度 | 是 |
| lead_period_third_level_course_project_code | string | 课程三级项目编码 | 常用维度 | 是 |
| lead_period_third_level_course_project_name | string | 课程三级项目名称 | 常用维度 | 是 |
| lead_period_first_level_subject_code | string | 课程一级品类编码 | 常用维度 | 是 |
| lead_period_first_level_subject_name | string | 课程一级品类名称 | 常用维度 | 是 |
| lead_period_second_level_subject_code | string | 课程二级品类编码 | 常用维度 | 是 |
| lead_period_second_level_subject_name | string | 课程二级品类名称 | 常用维度 | 是 |
| lead_period_third_level_subject_code | string | 课程三级品类编码 | 常用维度 | 是 |
| lead_period_third_level_subject_name | string | 课程三级品类名称 | 常用维度 | 是 |
| lead_period_main_teacher_numbers | string | 主讲老师编号列表，逗号分隔 | 常用维度 | 是 |
| lead_period_main_teacher_nicknames | string | 主讲老师名称列表，逗号分隔 | 常用维度 | 是 |
| lead_period_course_category_code | string | 课程类型，eg：10-公开课｜20-体验课｜30-专题课｜40-系列课 | 常用维度 | 是 |
| section_private_sea_id | bigint | 截面分配-私海id | 待按需求确认 | 否 |
| section_assign_employee_id | bigint | 截面分配-顾问employee_id | 常用维度 | 是 |
| section_assign_stage | int | 截面分配-线索状态 我的线索(4) 我的客户(5) 我的成单(6) | 待按需求确认 | 否 |
| section_assign_last_follow_time | string | 截面分配-跟进时间 | 时间分析 | 否 |
| section_assign_last_follow_content | string | 截面分配-最后一次跟进内容 | 待按需求确认 | 否 |
| section_assign_time | string | 截面分配-分配时间 | 时间分析 | 否 |
| section_assign_update_time | string | 截面分配-私海更新时间 | 时间分析 | 否 |
| section_assign_account_id | int | 截面分配-分配顾问account_id | 指标聚合 | 是 |
| section_assign_employee_email_name | string | 截面分配-分配顾问员工带数字名称 | 常用维度 | 是 |
| section_assign_employee_email_prefix | string | 截面分配-分配顾问邮箱前缀 | 常用维度 | 是 |
| section_assign_employee_city_code | bigint | 截面分配-分配顾问人城市编码 | 常用维度 | 是 |
| section_assign_employee_city_name | string | 截面分配-分配顾问人城市名称 | 常用维度 | 是 |
| section_assign_employee_talent_type_code | bigint | 截面分配-分配顾问人人才类型编码 | 常用维度 | 是 |
| section_assign_employee_talent_type_name | string | 截面分配-分配顾问人人才类型名称 | 常用维度 | 是 |
| section_assign_employee_top_level_department_code | bigint | 截面分配-分配顾问头部门编码 | 常用维度 | 是 |
| section_assign_employee_top_level_department_name | string | 截面分配-分配顾问头部门名称 | 权限/业务范围限定 | 是 |
| section_assign_employee_first_level_department_code | bigint | 截面分配-分配顾问一级部门编码 | 常用维度 | 是 |
| section_assign_employee_first_level_department_name | string | 截面分配-分配顾问一级部门名称 | 权限/业务范围限定 | 是 |
| section_assign_employee_second_level_department_code | bigint | 截面分配-分配顾问二级部门编码 | 常用维度 | 是 |
| section_assign_employee_second_level_department_name | string | 截面分配-分配顾问二级部门名称 | 权限/业务范围限定 | 是 |
| section_assign_employee_third_level_department_code | bigint | 截面分配-分配顾问三级部门编码 | 常用维度 | 是 |
| section_assign_employee_third_level_department_name | string | 截面分配-分配顾问三级部门名称 | 权限/业务范围限定 | 是 |
| section_assign_employee_last_level_department_code | bigint | 截面分配-分配顾问末级部门编码 | 常用维度 | 是 |
| section_assign_employee_department_path_json | string | 截面分配-分配顾问部门路径 | 常用维度 | 是 |
| section_assign_fall_time | string | 截面分配-掉海时间 | 时间分析 | 否 |
| section_assign_fall_reason | int | 截面分配-掉海原因 | 待按需求确认 | 否 |
| section_assign_is_wx_friend | string | 截面分配-分配后微信好友状态：好友 \| 非好友 | 待按需求确认 | 否 |
| section_assign_call_connected_count | bigint | 截面分配-分配后电话接通次数 | 指标聚合 | 是 |
| section_assign_call_missed_count | bigint | 截面分配-分配后电话未接通次数 | 指标聚合 | 是 |
| section_assign_all_call_duration | bigint | 截面分配-分配后总通话时长(s) | 指标聚合 | 是 |
| section_assign_first_call_time | string | 截面分配-分配后首次拨打时间 | 时间分析 | 否 |
| section_assign_last_call_time | string | 截面分配-分配后最后一次拨打时间 | 时间分析 | 否 |
| section_assign_first_call_connected_time | string | 截面分配-分配后首次接通时间 | 时间分析 | 否 |
| section_assign_last_call_connected_time | string | 截面分配-分配后最后一次接通时间 | 时间分析 | 否 |
| is_blacklist_user | string | 是否黑名单用户，eg: Y-是 \| N-不是 | 待按需求确认 | 否 |
| is_fully_refunded | string | 线索是否完全退款。主留痕类型【订单】：找出与主留痕【同线索 and 同原始父pay_number】的所有留痕，这些留痕全部退款则标记为线索退款，否则线索有效。 eg： Y-完全退款 \| N-未完全退款 | 待按需求确认 | 否 |
| is_lead | string | 是否计算线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功。eg: Y-算 \| N-不算 | 待按需求确认 | 否 |
| is_assign_lead | string | 是否计算分配线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功；3.截面分配顾问不为空。eg: Y-算 \| N-不算 | 待按需求确认 | 否 |
| is_no_assign_lead | string | 是否计算未分配线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功；3.截面分配顾问为空。eg: Y-算 \| N-不算 | 待按需求确认 | 否 |
| is_valid_lead | string | 是否计算有效线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功；3.截面分配顾问不为空；4.线索是否有效为是。 eg: Y-算 \| N-不算 | 待按需求确认 | 否 |
| rq_time | string | 入群时间 | 时间分析 | 否 |
| lead_group_period_year | string | 分组期年，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 常用维度 | 是 |
| lead_group_period_term | string | 分组期次，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 常用维度 | 是 |
| lead_group_period_name | string | 分组期名，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 常用维度 | 是 |
| section_assign_intention_level | int | 截面分配-分配意向度 | 待按需求确认 | 否 |
| flow_original_order_activity_number | bigint | 联报活动编号 | 待按需求确认 | 否 |
| flow_original_order_activity_name | string | 联报活动名称 | 待按需求确认 | 否 |
| flow_original_order_activity_total_price | bigint | 联报活动价格 | 指标聚合 | 是 |
| valid_private_sea_id | bigint | 有效私海id | 待按需求确认 | 否 |
| real_section_private_sea_id | bigint | 截面分配-实际私海id | 待按需求确认 | 否 |
| last_assign_private_sea_id | bigint | 最新分配私海id | 待按需求确认 | 否 |
| conversion_last_assign_private_sea_id | bigint | 转化期内最新分配私海id | 待按需求确认 | 否 |
| live_order_id | string | 电商订单ID | 待按需求确认 | 否 |
| live_account_id | string | 直播账号id | 指标聚合 | 是 |
| live_lead_effect_timestamp | timestamp | 直播线索生效时间 | 时间分析 | 否 |
| stats_flow_order_grade_name | string | 统计口径线索引流课年级：定义：取主留痕引流课订单的年级（特殊处理：flow_order_course_first_level_department_name = "H业务线" and flow_order_course_second_level_subject_name = "初级" and flow_order_grade_name = "高一" then "初三"）。 | 常用维度 | 是 |
| stats_lead_purchase_intention_level2_category_name | string | 统计口径线索购买意向二级品类。定义：购买意向第一个设置的二级品类 | 待按需求确认 | 否 |
| stats_grade_name | string | 统计口径线索年级。定义：nvl(stats_flow_order_grade_name，stats_lead_purchase_intention_level2_category_name) | 常用维度 | 是 |
| lead_cost | double | 线索成本 | 待按需求确认 | 否 |
| cost_config_project_name | string | 成本配置 项目名称 | 待按需求确认 | 否 |
| type_name | string | 类型名称-真/为/数字 | 待按需求确认 | 否 |
| live_streaming_host_id | string | 主播 | 待按需求确认 | 否 |
| live_begin_timestamp | timestamp | 直播开始时间戳 | 时间分析 | 否 |
| business_id | string | 其他业务系统对该流量池定义的id | 待按需求确认 | 否 |
| internal_contact_email_name | string | 管理人带数字名称 | 待按需求确认 | 否 |
| internal_contact_email_prefix | string | 管理人邮箱前缀 | 待按需求确认 | 否 |
| ad_account_id | string | 账户id | 指标聚合 | 是 |
| ad_account_name | string | 平台账户名称 | 指标聚合 | 是 |
| ad_model_id | int | 投放模式 | 待按需求确认 | 否 |
| ad_model_name | string | 投放模式名称 | 待按需求确认 | 否 |
| sku_id | string | sku_id | 待按需求确认 | 否 |
| sku_id_name | string | sku_id_name | 待按需求确认 | 否 |
| promoter_name | string | 推广员姓名 | 待按需求确认 | 否 |
| friend_status_name | string | 好友状态名（流量表字段） | 待按需求确认 | 否 |
| relation_trace_id | bigint | 关联留痕id | 待按需求确认 | 否 |
| project_id | bigint | 项目ID | 待按需求确认 | 否 |
| project_name | string | 项目名称 | 待按需求确认 | 否 |
| lead_income_amount | -- | 线索引流课收款金额 | 指标聚合 | 是 |
| lead_refund_amount | -- | 线索引流课退款金额 | 指标聚合 | 是 |
| third_order_id | string | 电商订单号（不带skuid） | 待按需求确认 | 否 |
| product_name | string | 产品线 | 待按需求确认 | 否 |
| trace_is_mkt_put | int | 留痕是否归属市场投放 | 待按需求确认 | 否 |
| channel_tree_id_level_1 | bigint | 一级渠道id-sourceV4 | 常用维度 | 是 |
| channel_tree_name_level_1 | string | 一级渠道名称-sourceV4 | 常用维度 | 是 |
| channel_tree_id_level_2 | bigint | 二级渠道id-sourceV4 | 常用维度 | 是 |
| channel_tree_name_level_2 | string | 二级渠道名称-sourceV4 | 常用维度 | 是 |
| channel_tree_id_level_3 | bigint | 三级渠道id-sourceV4 | 常用维度 | 是 |
| channel_tree_name_level_3 | string | 三级渠道名称-sourceV4 | 常用维度 | 是 |
| manager_type | int | 1-xxl、2-sw、3-dzhk、4-sn、5-source | 待按需求确认 | 否 |
| manager_email_prefix | string | 管理人邮箱前缀 | 待按需求确认 | 否 |
| manager_department_path_json | string | 管理人部门路径 | 常用维度 | 是 |
| manager_top_level_department_name | string | 管理人-组织架构顶级部门名称 | 权限/业务范围限定 | 是 |
| manager_top_level_department_code | bigint | 管理人-组织架构顶级部门编码 | 常用维度 | 是 |
| manager_first_level_department_name | string | 管理人-组织架构一级部门名称 | 权限/业务范围限定 | 是 |
| manager_first_level_department_code | bigint | 管理人-组织架构一级部门编码 | 常用维度 | 是 |
| manager_second_level_department_name | string | 管理人-组织架构二级部门名称 | 权限/业务范围限定 | 是 |
| manager_second_level_department_code | bigint | 管理人-组织架构二级部门编码 | 常用维度 | 是 |
| manager_third_level_department_name | string | 管理人-组织架构三级部门名称 | 权限/业务范围限定 | 是 |
| manager_third_level_department_code | bigint | 管理人-组织架构三级部门编码 | 常用维度 | 是 |
| platform_nickname | string | 平台账号昵称 | 待按需求确认 | 否 |
| page_id | string | 落地页id | 待按需求确认 | 否 |
| page_id_name | string | 落地页名称 | 待按需求确认 | 否 |
| page_type | string | 页面类型 | 待按需求确认 | 否 |
| page_type_name | string | 页面类型名称 | 待按需求确认 | 否 |
| source_put_plan_id | string | source上的put_plan_id | 待按需求确认 | 否 |
| source_put_plan_name | string | source上的put_plan_name | 待按需求确认 | 否 |
| live_end_timestamp | timestamp | 直播结束时间戳 | 时间分析 | 否 |
| live_employee_name | string | 主播名称 | 常用维度 | 是 |
## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`
- `t.top_department_name = '<待填写>'`
- `t.first_department_name = 'H业务线'`
- `t.second_department_name = '精品班学部'`
- `t.third_department_name = '学习顾问部'`
- `t.mapping_top_level_department_name = '<待填写>'`
- `t.mapping_first_level_department_name = 'H业务线'`
- `t.mapping_second_level_department_name = '精品班学部'`
- `t.section_assign_employee_top_level_department_name = '<待填写>'`
- `t.section_assign_employee_first_level_department_name = 'H业务线'`
- `t.section_assign_employee_second_level_department_name = '精品班学部'`
- `t.section_assign_employee_third_level_department_name = '学习顾问部'`
- `t.manager_top_level_department_name = '<待填写>'`
- `t.manager_first_level_department_name = 'H业务线'`
- `t.manager_second_level_department_name = '精品班学部'`
- `t.manager_third_level_department_name = '学习顾问部'`

## 9. 常用 join key

- `lead_id`：线索关联/去重
- `user_id`：用户关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.lead_id,
    t.user_id,
    t.channel_name_1,
    t.channel_name_2,
    t.second_department_name,
    t.mapping_first_level_department_name,
    t.section_assign_employee_second_level_department_name,
    t.manager_first_level_department_name,
    t.mapping_top_level_department_name,
    t.section_assign_employee_top_level_department_name,
    t.mapping_second_level_department_name,
    t.section_assign_employee_third_level_department_name,
    t.manager_top_level_department_name,
    t.manager_third_level_department_name
from service_dw.dm_crm_lead_stats_detail_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.top_department_name = '<待填写>'
  and t.first_department_name = 'H业务线'
  and t.second_department_name = '精品班学部'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 234。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 234。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 分区限制：查询分区表必须带分区条件。
- department_name 范围限定：涉及部门字段必须过滤；未给取值时使用占位符。
- 物理字段来源：当前字段、类型和说明以天工数据地图同步结果为准；业务含义仍需结合市场顾问使用场景确认。
- 常见报错：字段不存在、库名前缀不正确、小时表遗漏 hour、group by 不完整。
