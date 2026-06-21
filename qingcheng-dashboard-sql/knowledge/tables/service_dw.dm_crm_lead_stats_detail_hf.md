# service_dw.dm_crm_lead_stats_detail_hf

## 1. 中文名称

线索统计明细小时表

## 2. 表用途

在青橙过程数据 SQL 中补充首次外呼接通时间，并计算从分配到首次接通的小时差。

## 3. 数据粒度

待人工确认。当前 SQL 按 `lead_id` join 到线索主表。

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
| `mapping_first_level_department_name` | `'H业务线'` | 映射一级部门 |
| `mapping_second_level_department_name` | `('精品班学部','菁英班学部','市场部','本地化大班学部','青橙项目部')` | 映射二级部门 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_id` | bigint | 线索 ID | join 主表 |
| `section_assign_time` | string | 截面分配时间 | 计算首次接通时间差 |
| `section_assign_first_call_time` | string | 截面首次外呼时间 | 当前 SQL 取出但未直接使用 |
| `section_assign_first_call_connected_time` | string | 截面首次外呼接通时间 | 计算首次接通时间差 |
| `mapping_first_level_department_name` | string | 映射一级部门 | 范围限定 |
| `mapping_second_level_department_name` | string | 映射二级部门 | 范围限定 |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_purchase_intention_id` | bigint | 线索购买意向 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_purchase_intention_name` | string | 线索意向name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_purchase_intention_level1_category_id` | bigint | 线索意向一级品类id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_purchase_intention_level1_category_name` | string | 线索意向一级品类name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_create_time` | string | 线索创建时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_update_time` | string | 线索更新时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_state` | int | 线索状态 1待分配 2已分配 3分配失败 4close线索生命周期结束 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_state_name` | string | 线索状态 1待分配 2已分配 3分配失败 4close线索生命周期结束 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_state_change_reason` | int | 线索状态变更原因 1.待分配：初始状态 2.分配失败：未配置规则（未在执行期）3.分配失败：未分配规则执行失败 4.正常分配 5.close:掉海 6.close:修改购买意向 7.close:顾问无服务能力 8.close:微信线索合并 9.异常中断导致分配失败 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_state_change_reason_name` | string | 线索状态变更原因 1.待分配：初始状态 2.分配失败：未配置规则（未在执行期）3.分配失败：未分配规则执行失败 4.正常分配 5.close:掉海 6.close:修改购买意向 7.close:顾问无服务能力 8.close:微信线索合并 9.异常中断导致分配失败 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_assign_plan_id` | bigint | 线索分配应用的规则下的计划id 只记录第一次分配计划id因为后面会走唯一性 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `gy_trace_id` | bigint | 线索归因留痕id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_scenario_type` | int | 留痕录入场景，线上(1)/线下(2) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_scenario_type_name` | string | 留痕录入场景，线上(1)/线下(2) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `user_id` | bigint | 用户id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `city_id` | bigint | 城市ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_create_time` | string | 留痕创建时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_update_time` | string | 留痕更新时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_state` | int | 留痕分配状态，0:初始状态，1:待分配，2:已分配，3:分配失败 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_order_number` | bigint | 留痕订单号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_type` | int | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_type_name` | string | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_derivative_dependence_leads_id` | bigint | 衍生依赖的线索ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `self_source` | string | 留痕自身的source | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_refund_before_clazz_begin` | int | 是否课前退费（crm系统字段） 0:否，1:是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_org_id` | bigint | 线索部门 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_core_id` | bigint | 线索唯一标致ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_model_type` | int | 线索模型类型 0:线索 1:潜客 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_model_type_name` | string | 线索模型类型 0:线索 1:潜客 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_previous_model_id` | bigint | 线索上阶段模型ID(线索表的id) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `final_new_source` | string | 线索留痕source | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `wechat_id` | string | 留痕用户wxid，入群或加好友后匹配 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_rq_trace` | string | 留痕是否入群留痕，eg: Y-入群 \| N-未入群 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `chatroom` | string | 留痕所属群 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `passage_id` | bigint | 留痕入群通道id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_provider_type` | int | 线索分配类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_provider_type_name` | string | 线索分配类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_rule_id` | bigint | 留痕分配规则id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_rule_name` | string | 留痕分配规则name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_assign_way` | int | 留痕分配方式 1 权重平均 2 完全平均 3 顺序分配 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_assign_way_name` | string | 留痕分配方式 1 权重平均 2 完全平均 3 顺序分配 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `system_id` | bigint | 渠道属性-应用系统id(source_access表的id) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `system_name` | string | 渠道属性-投放系统名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `get_customer_way_id` | bigint | 渠道属性-获客方式id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `get_customer_way_name` | string | 渠道属性-获客方式 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `get_customer_way_parent_id` | bigint | 渠道属性-获客方式父级ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `get_customer_way_parent_name` | string | 渠道属性-获客方式父级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_id` | bigint | 渠道属性-流量池id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_name` | string | 渠道属性-流量池名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_type_id` | bigint | 渠道属性-流量池类型id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_type_name` | string | 渠道属性-流量池类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `resource_position_id` | bigint | 渠道属性-资源位id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `resource_position_name` | string | 渠道属性-资源位名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `resource_type_id` | bigint | 渠道属性-资源位类型id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `resource_type_name` | string | 渠道属性-资源位类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `put_plan_id` | string | 渠道属性-投放计划id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `put_plan_name` | string | 渠道属性-投放计划名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `plan_create_username` | string | 渠道属性-计划创建人用户名-邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `plan_create_name` | string | 渠道属性-计划创建人-带数字名字 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_manager_username` | string | 渠道属性-source管理人邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_manager_name` | string | 渠道属性-source管理人-带数字名字 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `tree_code` | string | 渠道属性-组织结构 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `tree_name` | string | 渠道属性-组织结构名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `top_department_code` | bigint | 渠道属性-集团id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `top_department_name` | string | 渠道属性-集团名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_department_code` | bigint | 渠道属性-一级部门id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_department_name` | string | 渠道属性-一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_department_code` | bigint | 渠道属性-二级部门id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_department_name` | string | 渠道属性-二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `third_department_code` | bigint | 渠道属性-三级部门id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `third_department_name` | string | 渠道属性-三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_provider_id` | bigint | 渠道属性-业务渠道商id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_provider_name` | string | 渠道属性-渠道商名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_second_provider_id` | bigint | 渠道属性-二级渠道商id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_second_provider_name` | string | 渠道属性-二级渠道商名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_name_1` | string | 渠道属性-渠道树一级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_name_2` | string | 渠道属性-渠道树二级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_name_3` | string | 渠道属性-渠道树三级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_name_4` | string | 渠道属性-渠道树四级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_name_5` | string | 渠道属性-渠道树五级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_latest_order_number` | bigint | 引流课-最新子订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_trace_id` | bigint | 主留痕最新子订单留痕 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_number` | bigint | 线索归属期number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_name` | string | 线索归属期name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_course_category_id` | int | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_course_tag` | int | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_school_year` | int | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_department` | int | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_start_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_end_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_create_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_update_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_biz_type` | int | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_is_test` | int | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_project_id_path` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_show_category_id_path` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_show_teacher_list` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_clazz_begin_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_service_begin_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_conversion_begin_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_conversion_end_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `mapping_top_level_department_code` | string | 线索归属期映射 top部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `mapping_top_level_department_name` | string | 线索归属期映射 top部门name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `mapping_first_level_department_code` | string | 线索归属期映射 一级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `mapping_second_level_department_code` | string | 线索归属期映射 二级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_section_time` | timestamp | 线索归属期映射 期截面时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_first_level_course_project_code` | string | 课程一级项目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_first_level_course_project_name` | string | 课程一级项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_second_level_course_project_code` | string | 课程二级项目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_second_level_course_project_name` | string | 课程二级项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_third_level_course_project_code` | string | 课程三级项目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_third_level_course_project_name` | string | 课程三级项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_first_level_subject_code` | string | 课程一级品类编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_first_level_subject_name` | string | 课程一级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_second_level_subject_code` | string | 课程二级品类编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_second_level_subject_name` | string | 课程二级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_third_level_subject_code` | string | 课程三级品类编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_third_level_subject_name` | string | 课程三级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_main_teacher_numbers` | string | 主讲老师编号列表，逗号分隔 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_main_teacher_nicknames` | string | 主讲老师名称列表，逗号分隔 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_course_category_code` | string | 课程类型，eg：10-公开课｜20-体验课｜30-专题课｜40-系列课 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_private_sea_id` | bigint | 截面分配-私海id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_id` | bigint | 截面分配-顾问employee_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_stage` | int | 截面分配-线索状态 我的线索(4) 我的客户(5) 我的成单(6) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_last_follow_time` | string | 截面分配-跟进时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_last_follow_content` | string | 截面分配-最后一次跟进内容 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_update_time` | string | 截面分配-私海更新时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_account_id` | int | 截面分配-分配顾问account_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_email_name` | string | 截面分配-分配顾问员工带数字名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_email_prefix` | string | 截面分配-分配顾问邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_city_code` | bigint | 截面分配-分配顾问人城市编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_city_name` | string | 截面分配-分配顾问人城市名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_talent_type_code` | bigint | 截面分配-分配顾问人人才类型编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_talent_type_name` | string | 截面分配-分配顾问人人才类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_top_level_department_code` | bigint | 截面分配-分配顾问头部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_top_level_department_name` | string | 截面分配-分配顾问头部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_first_level_department_code` | bigint | 截面分配-分配顾问一级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_first_level_department_name` | string | 截面分配-分配顾问一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_second_level_department_code` | bigint | 截面分配-分配顾问二级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_second_level_department_name` | string | 截面分配-分配顾问二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_third_level_department_code` | bigint | 截面分配-分配顾问三级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_third_level_department_name` | string | 截面分配-分配顾问三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_last_level_department_code` | bigint | 截面分配-分配顾问末级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_department_path_json` | string | 截面分配-分配顾问部门路径 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_fall_time` | string | 截面分配-掉海时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_fall_reason` | int | 截面分配-掉海原因 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_is_wx_friend` | string | 截面分配-分配后微信好友状态：好友 \| 非好友 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_call_connected_count` | bigint | 截面分配-分配后电话接通次数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_call_missed_count` | bigint | 截面分配-分配后电话未接通次数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_all_call_duration` | bigint | 截面分配-分配后总通话时长(s) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_last_call_time` | string | 截面分配-分配后最后一次拨打时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_last_call_connected_time` | string | 截面分配-分配后最后一次接通时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_blacklist_user` | string | 是否黑名单用户，eg: Y-是 \| N-不是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_fully_refunded` | string | 线索是否完全退款。主留痕类型【订单】：找出与主留痕【同线索 and 同原始父pay_number】的所有留痕，这些留痕全部退款则标记为线索退款，否则线索有效。 eg： Y-完全退款 \| N-未完全退款 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_lead` | string | 是否计算线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功。eg: Y-算 \| N-不算 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_assign_lead` | string | 是否计算分配线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功；3.截面分配顾问不为空。eg: Y-算 \| N-不算 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_no_assign_lead` | string | 是否计算未分配线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功；3.截面分配顾问为空。eg: Y-算 \| N-不算 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_valid_lead` | string | 是否计算有效线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功；3.截面分配顾问不为空；4.线索是否有效为是。 eg: Y-算 \| N-不算 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `rq_time` | string | 入群时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_group_period_year` | string | 分组期年，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_group_period_term` | string | 分组期次，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_group_period_name` | string | 分组期名，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_intention_level` | int | 截面分配-分配意向度 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_original_order_activity_number` | bigint | 联报活动编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_original_order_activity_name` | string | 联报活动名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_original_order_activity_total_price` | bigint | 联报活动价格 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `valid_private_sea_id` | bigint | 有效私海id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `real_section_private_sea_id` | bigint | 截面分配-实际私海id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_assign_private_sea_id` | bigint | 最新分配私海id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `conversion_last_assign_private_sea_id` | bigint | 转化期内最新分配私海id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_order_id` | string | 电商订单ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_account_id` | string | 直播账号id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_lead_effect_timestamp` | timestamp | 直播线索生效时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stats_flow_order_grade_name` | string | 统计口径线索引流课年级：定义：取主留痕引流课订单的年级（特殊处理：flow_order_course_first_level_department_name = "H业务线" and flow_order_course_second_level_subject_name = "初级" and flow_order_grade_name = "高一" then "初三"）。 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stats_lead_purchase_intention_level2_category_name` | string | 统计口径线索购买意向二级品类。定义：购买意向第一个设置的二级品类 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stats_grade_name` | string | 统计口径线索年级。定义：nvl(stats_flow_order_grade_name，stats_lead_purchase_intention_level2_category_name) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_cost` | double | 线索成本 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `cost_config_project_name` | string | 成本配置 项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `type_name` | string | 类型名称-真/为/数字 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_streaming_host_id` | string | 主播 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_begin_timestamp` | timestamp | 直播开始时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `business_id` | string | 其他业务系统对该流量池定义的id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `internal_contact_email_name` | string | 管理人带数字名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `internal_contact_email_prefix` | string | 管理人邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `ad_account_id` | string | 账户id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `ad_account_name` | string | 平台账户名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `ad_model_id` | int | 投放模式 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `ad_model_name` | string | 投放模式名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sku_id` | string | sku_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sku_id_name` | string | sku_id_name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `promoter_name` | string | 推广员姓名 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `friend_status_name` | string | 好友状态名（流量表字段） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `relation_trace_id` | bigint | 关联留痕id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `project_id` | bigint | 项目ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `project_name` | string | 项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_income_amount` | decimal(20 | 线索引流课收款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_refund_amount` | decimal(20 | 线索引流课退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `third_order_id` | string | 电商订单号（不带skuid） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `product_name` | string | 产品线 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_is_mkt_put` | int | 留痕是否归属市场投放 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_tree_id_level_1` | bigint | 一级渠道id-sourceV4 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_tree_name_level_1` | string | 一级渠道名称-sourceV4 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_tree_id_level_2` | bigint | 二级渠道id-sourceV4 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_tree_name_level_2` | string | 二级渠道名称-sourceV4 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_tree_id_level_3` | bigint | 三级渠道id-sourceV4 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_tree_name_level_3` | string | 三级渠道名称-sourceV4 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_type` | int | 1-xxl、2-sw、3-dzhk、4-sn、5-source | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_email_prefix` | string | 管理人邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_department_path_json` | string | 管理人部门路径 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_top_level_department_name` | string | 管理人-组织架构顶级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_top_level_department_code` | bigint | 管理人-组织架构顶级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_first_level_department_name` | string | 管理人-组织架构一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_first_level_department_code` | bigint | 管理人-组织架构一级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_second_level_department_name` | string | 管理人-组织架构二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_second_level_department_code` | bigint | 管理人-组织架构二级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_third_level_department_name` | string | 管理人-组织架构三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `manager_third_level_department_code` | bigint | 管理人-组织架构三级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `platform_nickname` | string | 平台账号昵称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `page_id` | string | 落地页id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `page_id_name` | string | 落地页名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `page_type` | string | 页面类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `page_type_name` | string | 页面类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_put_plan_id` | string | source上的put_plan_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_put_plan_name` | string | source上的put_plan_name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_end_timestamp` | timestamp | 直播结束时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_employee_name` | string | 主播名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '2' hour, 'HH')
  and mapping_first_level_department_name = 'H业务线'
  and mapping_second_level_department_name in ('精品班学部','菁英班学部','市场部','本地化大班学部','青橙项目部')
```

## 9. 常用 join key

- `lead_id`

## 10. 常用 SQL 片段

```sql
date_diff(
    'hour',
    cast(section_assign_time as timestamp),
    cast(section_assign_first_call_connected_time as timestamp)
) as first_call_connected_time_diff_hour
```

## 11. 注意事项

- 映射二级部门包含多个学部和市场部，是否必须包含这些部门才能支撑青橙线索待确认。
- `lead_period_name`、`lead_group_period_name`、`lead_period_conversion_begin_time`、`lead_period_conversion_end_time` 更适合回答“系统给 lead 打的期次标签是什么”“保护期窗口落在哪个桶里”，不适合作为原始来源追溯主字段。
- 需要追溯某批青橙 `lead_id` 的原始来源时，优先回到 `knowledge/sql_patterns/qingcheng_lead_origin_trace.md` 和 `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`；本表主要承担期次标签和保护期窗口校验。
