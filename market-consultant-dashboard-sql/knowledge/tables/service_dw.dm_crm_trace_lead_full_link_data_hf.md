# service_dw.dm_crm_trace_lead_full_link_data_hf

## 1. 中文名称

线索留痕宽表

## 2. 表用途

线索留痕宽表。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

data-map 高频统计：500 条成功 SQL 中出现 75 次，占比 15.0%。

## 3. 数据粒度

待确认；字段目录未提供数据粒度

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
| last_assign_employee_top_level_department_name | string | '<待填写>' | 是 | 最新分配-分配顾问头部门名称 | 待人工确认 |
| last_assign_employee_first_level_department_name | string | 'H业务线' | 是 | 最新分配-分配顾问一级部门名称 | 按 row_permissions 同层级历史取值补充 |
| last_assign_employee_second_level_department_name | string | '精品班学部' | 是 | 最新分配-分配顾问二级部门名称 | 按 row_permissions 同层级历史取值补充 |
| last_assign_employee_third_level_department_name | string | '学习顾问部' | 是 | 最新分配-分配顾问三级部门名称 | 按 row_permissions 同层级历史取值补充 |
| flow_order_course_top_level_department_name | string | '<待填写>' | 是 | 引流课-课程头部门名称 | 待人工确认 |
| flow_order_course_first_level_department_name | string | 'H业务线' | 是 | 引流课-课程一级部门名称 | 按 row_permissions 同层级历史取值补充 |
| flow_order_course_second_level_department_name | string | '精品班学部' | 是 | 引流课-课程二级部门名称 | 按 row_permissions 同层级历史取值补充 |
| flow_order_course_third_level_department_name | string | '学习顾问部' | 是 | 引流课-课程三级部门名称 | 按 row_permissions 同层级历史取值补充 |
| flow_order_school_department_name | string | '<待填写>' | 是 | 引流课-学部名称 | 待人工确认 |
| top_department_name | string | '<待填写>' | 是 | 渠道属性-集团名称 | 待人工确认 |
| first_department_name | string | 'H业务线' | 是 | 渠道属性-一级部门名称 | 按 row_permissions 同层级历史取值补充 |
| second_department_name | string | '精品班学部' | 是 | 渠道属性-二级部门名称 | 按 row_permissions 同层级历史取值补充 |
| third_department_name | string | '学习顾问部' | 是 | 渠道属性-三级部门名称 | 按 row_permissions 同层级历史取值补充 |
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
| trace_id | bigint | 留痕id | 主键/关联键 | 是 |
| trace_scenario_type | int | 留痕录入场景，线上(1)/线下(2) | 待按需求确认 | 否 |
| trace_scenario_type_name | string | 留痕录入场景，线上(1)/线下(2) | 待按需求确认 | 否 |
| user_id | bigint | 用户id | 主键/关联键 | 是 |
| city_id | bigint | 城市ID | 待按需求确认 | 否 |
| trace_create_time | string | 留痕创建时间 | 时间分析 | 否 |
| trace_update_time | string | 留痕更新时间 | 时间分析 | 否 |
| trace_state | int | 留痕分配状态，0:初始状态，1:待分配，2:已分配，3:分配失败 | 待按需求确认 | 否 |
| trace_order_number | bigint | 留痕订单号 | 待按需求确认 | 否 |
| union_id | string | trace微信unionId | 待按需求确认 | 否 |
| trace_type | int | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 待按需求确认 | 否 |
| trace_type_name | string | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 待按需求确认 | 否 |
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
| is_gy_trace | string | 线索归因留痕。Y-是 \| N-不是 | 待按需求确认 | 否 |
| lead_derivative_dependence_leads_id | bigint | 衍生依赖的线索ID | 待按需求确认 | 否 |
| self_source | string | 留痕自身的source | 待按需求确认 | 否 |
| is_refund_before_clazz_begin | int | 是否课前退费（crm系统字段） 0:否，1:是 | 待按需求确认 | 否 |
| lead_org_id | bigint | 线索部门 | 待按需求确认 | 否 |
| lead_core_id | bigint | 线索唯一标致ID | 待按需求确认 | 否 |
| lead_model_type | int | 线索模型类型 0:线索 1:潜客 | 待按需求确认 | 否 |
| lead_model_type_name | string | 线索模型类型 0:线索 1:潜客 | 待按需求确认 | 否 |
| lead_previous_model_id | bigint | 线索上阶段模型ID(线索表的id) | 待按需求确认 | 否 |
| final_new_source | string | 线索留痕source | 待按需求确认 | 否 |
| flow_order_period_number | bigint | 引流课期编号 | 常用维度 | 是 |
| flow_order_period_name | string | 引流课期名称 | 常用维度 | 是 |
| flow_order_period_course_category_id | int | 引流课期直播课程类型 10 公开课 20 体验课 30 专题课 40 系列课 | 常用维度 | 是 |
| flow_order_period_course_tag | int | 引流课期课程标签 7：克瑞斯 9：文曲星 | 常用维度 | 是 |
| flow_order_period_school_year | int | 引流课期学年 | 常用维度 | 是 |
| flow_order_period_department | int | 引流课期学部信息：10、小学；20、初中；30、高中；40、小学专题 | 常用维度 | 是 |
| flow_order_period_start_time | string | 引流课期期开始时间 | 常用维度 | 是 |
| flow_order_period_end_time | string | 引流课期期结束时间 | 常用维度 | 是 |
| flow_order_period_create_time | string | 引流课期创建时间 | 常用维度 | 是 |
| flow_order_period_update_time | string | 引流课期更新时间 | 常用维度 | 是 |
| flow_order_period_biz_type | int | 引流课期业务类型：1-中小学，2-成人 | 常用维度 | 是 |
| flow_order_period_is_test | int | 引流课期是否测试：0-正式，1-测试 | 常用维度 | 是 |
| flow_order_period_project_id_path | string | 引流课期展示的项目id路径：一级id/二级id/三级 | 常用维度 | 是 |
| flow_order_period_show_category_id_path | string | 引流课期展示的品类id路径：一级id/二级id/三级id | 常用维度 | 是 |
| flow_order_period_show_teacher_list | string | 引流课期期展示主讲：英文逗号分隔 | 常用维度 | 是 |
| flow_order_period_clazz_begin_time | string | 引流课期展示的开课时间 | 常用维度 | 是 |
| flow_order_period_service_begin_time | string | 引流课期服务开始日期 | 常用维度 | 是 |
| flow_order_period_conversion_begin_time | string | 引流课期转化开始日期 | 常用维度 | 是 |
| flow_order_period_conversion_end_time | string | 引流课期转化结束日期 | 常用维度 | 是 |
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
| private_sea_id | bigint | 最新分配-私海id | 待按需求确认 | 否 |
| last_assign_employee_id | int | 最新分配-顾问employee_id | 常用维度 | 是 |
| last_assign_stage | int | 最新分配-线索状态 我的线索(4) 我的客户(5) 我的成单(6) | 待按需求确认 | 否 |
| last_assign_last_follow_time | string | 最新分配-跟进时间 | 时间分析 | 否 |
| last_assign_last_follow_content | string | 最新分配-最后一次跟进内容 | 待按需求确认 | 否 |
| last_assign_time | string | 最新分配-分配时间 | 时间分析 | 否 |
| last_assign_update_time | string | 最新分配-私海更新时间 | 时间分析 | 否 |
| last_assign_account_id | int | 最新分配-分配顾问account_id | 指标聚合 | 是 |
| last_assign_employee_email_name | string | 最新分配-分配顾问员工带数字名称 | 常用维度 | 是 |
| last_assign_employee_email_prefix | string | 最新分配-分配顾问邮箱前缀 | 常用维度 | 是 |
| last_assign_employee_city_code | bigint | 最新分配-分配顾问人城市编码 | 常用维度 | 是 |
| last_assign_employee_city_name | string | 最新分配-分配顾问人城市名称 | 常用维度 | 是 |
| last_assign_employee_talent_type_code | bigint | 最新分配-分配顾问人人才类型编码 | 常用维度 | 是 |
| last_assign_employee_talent_type_name | string | 最新分配-分配顾问人人才类型名称 | 常用维度 | 是 |
| last_assign_employee_top_level_department_code | bigint | 最新分配-分配顾问头部门编码 | 常用维度 | 是 |
| last_assign_employee_top_level_department_name | string | 最新分配-分配顾问头部门名称 | 权限/业务范围限定 | 是 |
| last_assign_employee_first_level_department_code | bigint | 最新分配-分配顾问一级部门编码 | 常用维度 | 是 |
| last_assign_employee_first_level_department_name | string | 最新分配-分配顾问一级部门名称 | 权限/业务范围限定 | 是 |
| last_assign_employee_second_level_department_code | bigint | 最新分配-分配顾问二级部门编码 | 常用维度 | 是 |
| last_assign_employee_second_level_department_name | string | 最新分配-分配顾问二级部门名称 | 权限/业务范围限定 | 是 |
| last_assign_employee_third_level_department_code | bigint | 最新分配-分配顾问三级部门编码 | 常用维度 | 是 |
| last_assign_employee_third_level_department_name | string | 最新分配-分配顾问三级部门名称 | 权限/业务范围限定 | 是 |
| last_assign_employee_last_level_department_code | bigint | 最新分配-分配顾问末级部门编码 | 常用维度 | 是 |
| last_assign_employee_department_path_json | string | 最新分配-分配顾问部门路径 | 常用维度 | 是 |
| last_assign_fall_time | string | 最新分配-掉海时间 | 时间分析 | 否 |
| last_assign_fall_reason | int | 最新分配-掉海原因 | 待按需求确认 | 否 |
| last_assign_is_wx_friend | string | 最新分配-分配后微信好友状态：好友 \| 非好友 | 待按需求确认 | 否 |
| last_assign_call_connected_count | bigint | 最新分配-分配后电话接通次数 | 指标聚合 | 是 |
| last_assign_call_missed_count | bigint | 最新分配-分配后电话未接通次数 | 指标聚合 | 是 |
| last_assign_all_call_duration | bigint | 最新分配-分配后总通话时长(s) | 指标聚合 | 是 |
| last_assign_first_call_time | string | 最新分配-分配后首次拨打时间 | 时间分析 | 否 |
| last_assign_last_call_time | string | 最新分配-分配后最后一次拨打时间 | 时间分析 | 否 |
| last_assign_first_call_connected_time | string | 最新分配-分配后首次接通时间 | 时间分析 | 否 |
| last_assign_last_call_connected_time | string | 最新分配-分配后最后一次接通时间 | 时间分析 | 否 |
| flow_order_number | bigint | 引流课-订单编号 | 待按需求确认 | 否 |
| flow_order_pay_number | bigint | 引流课-支付单编号 | 待按需求确认 | 否 |
| flow_order_course_number | bigint | 引流课-course_number | 待按需求确认 | 否 |
| flow_order_clazz_number | bigint | 引流课-clazz_number | 待按需求确认 | 否 |
| flow_order_biz_line_type | bigint | 引流课-业务线类型，eg：1-k12｜2-成人｜0-不限业务线 | 待按需求确认 | 否 |
| flow_order_mark | bigint | 引流课- 1:赠课) | 待按需求确认 | 否 |
| flow_order_price | bigint | 引流课-订单金额(分) | 指标聚合 | 是 |
| flow_order_bind_type | bigint | 引流课-订单类型，eg：0-正常订单｜1-联报主课订单｜2-联报从课订单 | 待按需求确认 | 否 |
| flow_order_bind_main_order_number | bigint | 引流课-联报主课订单编号 | 待按需求确认 | 否 |
| flow_order_status | bigint | 引流课-订单状态 | 待按需求确认 | 否 |
| flow_order_pay_success_timestamp | timestamp | 引流课-支付成功时间戳 | 时间分析 | 否 |
| flow_order_full_refund_timestamp | timestamp | 引流课-完全退款时间戳 | 时间分析 | 否 |
| flow_order_is_pay_success_order | int | 引流课-是否支付成功订单（支付成功过就算，非最新状态），eg：0-否｜1-是 | 待按需求确认 | 否 |
| flow_order_is_part_refund_order | int | 引流课-是否部分退款订单，eg：0-否｜1-是 | 待按需求确认 | 否 |
| flow_order_is_full_refund_order | int | 引流课-是否全部退款订单，eg：0-否｜1-是 | 待按需求确认 | 否 |
| flow_original_order_number | bigint | 引流课-原始父订单订单编号 | 待按需求确认 | 否 |
| flow_original_order_price | bigint | 引流课-原始父订单金额(分) | 指标聚合 | 是 |
| flow_original_order_pay_number | bigint | 引流课-原始父订单支付单编号 | 待按需求确认 | 否 |
| flow_original_order_activity_number | bigint | 引流课-原始父订单联报活动编号 | 待按需求确认 | 否 |
| flow_original_order_activity_price | bigint | 引流课-原始父订单联报活动价格 | 指标聚合 | 是 |
| flow_original_order_pay_success_timestamp | timestamp | 引流课-原始父订单支付成功时间戳 | 时间分析 | 否 |
| flow_latest_order_number | bigint | 引流课-最新子订单编号 | 待按需求确认 | 否 |
| flow_latest_order_full_refund_timestamp | timestamp | 引流课-最新子订单完全退款时间戳 | 时间分析 | 否 |
| flow_latest_order_is_pay_success_order | int | 引流课-最新子订单是否支付成功订单（支付成功过就算，非最新状态），eg：0-否｜1-是 | 待按需求确认 | 否 |
| flow_latest_order_is_part_refund_order | int | 引流课-最新子订单是否部分退款订单，eg：0-否｜1-是 | 待按需求确认 | 否 |
| flow_latest_order_is_full_refund_order | int | 引流课-最新子订单是否全部退款订单，eg：0-否｜1-是 | 待按需求确认 | 否 |
| flow_order_clazz_name | string | 引流课-班级名称 | 待按需求确认 | 否 |
| flow_order_clazz_biz_number | string | 引流课-班级业务编号 | 待按需求确认 | 否 |
| flow_order_clazz_type | bigint | 引流课-班级类型，eg：1-长期班｜2-短期班｜3-入口班 | 待按需求确认 | 否 |
| flow_order_clazz_begin_timestamp | timestamp | 引流课-班级开课时间戳（第一节正式课节开课时间戳） | 时间分析 | 否 |
| flow_order_clazz_end_timestamp | timestamp | 引流课-班级结课时间戳（最后一节正式课节结课时间戳） | 时间分析 | 否 |
| flow_order_main_teacher_number | bigint | 引流课-主讲老师编号（第一节正式课节主讲老师） | 待按需求确认 | 否 |
| flow_order_main_teacher_nickname | string | 引流课-主讲老师昵称（第一节正式课节主讲老师） | 待按需求确认 | 否 |
| flow_order_main_teacher_email_name | string | 引流课-主讲老师员工名称（第一节正式课节主讲老师） | 待按需求确认 | 否 |
| flow_order_main_teacher_email_prefix | string | 引流课-主讲老师邮箱前缀 | 待按需求确认 | 否 |
| flow_order_course_top_level_department_code | bigint | 引流课-课程头部门代码 | 常用维度 | 是 |
| flow_order_course_top_level_department_name | string | 引流课-课程头部门名称 | 权限/业务范围限定 | 是 |
| flow_order_course_first_level_department_code | bigint | 引流课-课程一级部门代码 | 常用维度 | 是 |
| flow_order_course_first_level_department_name | string | 引流课-课程一级部门名称 | 权限/业务范围限定 | 是 |
| flow_order_course_second_level_department_code | bigint | 引流课-课程二级部门代码 | 常用维度 | 是 |
| flow_order_course_second_level_department_name | string | 引流课-课程二级部门名称 | 权限/业务范围限定 | 是 |
| flow_order_course_third_level_department_code | bigint | 引流课-课程三级部门代码 | 常用维度 | 是 |
| flow_order_course_third_level_department_name | string | 引流课-课程三级部门名称 | 权限/业务范围限定 | 是 |
| flow_order_course_first_level_subject_code | bigint | 引流课-课程一级品类代码 | 常用维度 | 是 |
| flow_order_course_first_level_subject_name | string | 引流课-课程一级品类名称 | 常用维度 | 是 |
| flow_order_course_second_level_subject_code | bigint | 引流课-课程二级品类代码 | 常用维度 | 是 |
| flow_order_course_second_level_subject_name | string | 引流课-课程二级品类名称 | 常用维度 | 是 |
| flow_order_course_third_level_subject_code | bigint | 引流课-课程三级品类代码 | 常用维度 | 是 |
| flow_order_course_third_level_subject_name | string | 引流课-课程三级品类名称 | 常用维度 | 是 |
| flow_order_course_name | string | 引流课-课程名称 | 待按需求确认 | 否 |
| flow_order_course_category_code | bigint | 引流课-课程类型编号 | 待按需求确认 | 否 |
| flow_order_course_biz_number | string | 引流课-课程业务编号 | 待按需求确认 | 否 |
| flow_order_school_department_code | bigint | 引流课-学部代码 | 常用维度 | 是 |
| flow_order_school_department_name | string | 引流课-学部名称 | 权限/业务范围限定 | 是 |
| flow_order_grade_code | bigint | 引流课-年级代码（多个年级取最小值） | 常用维度 | 是 |
| flow_order_grade_name | string | 引流课-年级名称 | 常用维度 | 是 |
| flow_order_school_subject_code | bigint | 引流课-科目代码 | 常用维度 | 是 |
| flow_order_school_subject_name | string | 引流课-科目名称 | 常用维度 | 是 |
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
| rq_time | string | 入群时间 | 时间分析 | 否 |
| last_assign_assign_intention_level | int | 意向度 | 待按需求确认 | 否 |
| flow_original_order_activity_name | string | 联报活动名称 | 待按需求确认 | 否 |
| flow_original_order_activity_total_price | bigint | 联报活动价格 | 指标聚合 | 是 |
| live_order_id | string | 电商订单ID | 待按需求确认 | 否 |
| live_account_id | string | 直播账号id | 指标聚合 | 是 |
| live_lead_effect_timestamp | timestamp | 直播线索生效时间 | 时间分析 | 否 |
| leads_id | bigint | 流量id | 待按需求确认 | 否 |
| leads_id_create_timestamp | timestamp | 流量产生时间 | 时间分析 | 否 |
| relation_trace_id | bigint | 关联留痕id | 待按需求确认 | 否 |
| business_id | string | 其他业务系统对该流量池定义的id | 待按需求确认 | 否 |
| internal_contact_email_name | string | 管理人带数字名称 | 待按需求确认 | 否 |
| internal_contact_email_prefix | string | 管理人邮箱前缀 | 待按需求确认 | 否 |
| ad_account_id | string | 账户id | 指标聚合 | 是 |
| ad_account_name | string | 投放账户名称 | 指标聚合 | 是 |
| ad_model_id | int | 投放模式 | 待按需求确认 | 否 |
| ad_model_name | string | 投放模式名称 | 待按需求确认 | 否 |
| project_id | bigint | 项目id | 待按需求确认 | 否 |
| project_name | string | 项目名称 | 待按需求确认 | 否 |
| sku_id | string | sku_id | 待按需求确认 | 否 |
| sku_id_name | string | sku_id_name | 待按需求确认 | 否 |
| promoter_name | string | 推广员姓名 | 待按需求确认 | 否 |
| friend_status_name | string | 好友状态名（流量表字段） | 待按需求确认 | 否 |
| first_full_refund_timestamp | timestamp | 首次全部退款时间 | 时间分析 | 否 |
| period_section_time | timestamp | 期截面时间 | 常用维度 | 是 |
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
## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`
- `t.last_assign_employee_top_level_department_name = '<待填写>'`
- `t.last_assign_employee_first_level_department_name = 'H业务线'`
- `t.last_assign_employee_second_level_department_name = '精品班学部'`
- `t.last_assign_employee_third_level_department_name = '学习顾问部'`
- `t.flow_order_course_top_level_department_name = '<待填写>'`
- `t.flow_order_course_first_level_department_name = 'H业务线'`
- `t.flow_order_course_second_level_department_name = '精品班学部'`
- `t.flow_order_course_third_level_department_name = '学习顾问部'`
- `t.flow_order_school_department_name = '<待填写>'`
- `t.top_department_name = '<待填写>'`
- `t.first_department_name = 'H业务线'`
- `t.second_department_name = '精品班学部'`
- `t.third_department_name = '学习顾问部'`
- `t.manager_top_level_department_name = '<待填写>'`
- `t.manager_first_level_department_name = 'H业务线'`
- `t.manager_second_level_department_name = '精品班学部'`
- `t.manager_third_level_department_name = '学习顾问部'`

## 9. 常用 join key

- `lead_id`：线索关联/去重
- `user_id`：用户关联
- `trace_id`：留痕/线索链路关联
- `private_sea_id`：私海记录关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.lead_id,
    t.trace_id,
    t.user_id,
    t.channel_name_1,
    t.channel_name_2,
    t.second_department_name,
    t.last_assign_employee_second_level_department_name,
    t.last_assign_employee_first_level_department_name,
    t.manager_first_level_department_name,
    t.last_assign_employee_top_level_department_name,
    t.flow_order_course_third_level_department_name,
    t.last_assign_employee_third_level_department_name,
    t.flow_order_course_second_level_department_name,
    t.manager_top_level_department_name
from service_dw.dm_crm_trace_lead_full_link_data_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.last_assign_employee_top_level_department_name = '<待填写>'
  and t.last_assign_employee_first_level_department_name = 'H业务线'
  and t.last_assign_employee_second_level_department_name = '精品班学部'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 249。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 249。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。
