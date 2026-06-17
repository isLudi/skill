# service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf

## 1. 中文名称

归因流水粒度统计明细表

## 2. 表用途

记录订单支付/退款流水、业绩归属人、课程班级、线索归因、流水期/支付期和统计标签等明细信息，用于计算收入、退款、转化金额和业绩归因指标。

字段来源：`E:\2000_work\GAOTU\归因流水粒度统计明细表.docx`。

## 3. 数据粒度

- 订单-流水-业绩归属-小时快照粒度；同一订单可有多笔支付/退款流水。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |
| hour | string | 小时分区 | 是 |
## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| performance_first_level_department_name | string | '<一级部门名称>' | 是 | 业绩归属一级部门 |
| performance_second_level_department_name | string | '<二级部门名称>' | 是 | 业绩归属二级部门 |
| performance_third_level_department_name | string | '<三级部门名称>' | 是 | 业绩归属三级部门 |
| course_first_level_department_name | string | '<课程一级部门名称>' | 是 | 课程一级部门 |
| course_second_level_department_name | string | '<课程二级部门名称>' | 是 | 课程二级部门 |
| trade_period_mapping_first_level_department_name | string | '<流水期一级部门名称>' | 是 | 流水期映射一级部门 |
| pay_period_mapping_first_level_department_name | string | '<支付期一级部门名称>' | 是 | 支付期映射一级部门 |

## 7. 字段清单

字段来源：`E:\2000_work\GAOTU\归因流水粒度统计明细表.docx`，非分区字段 184 个。

| 字段名 | 类型 | 说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| order_number | bigint | 订单编号 | 订单/支付维度 | 是 |
| performance_employee_id | bigint | 业绩归属人员工id | 员工/顾问维度 | 否 |
| performance_employee_name | string | 业绩归属人员工名称 | 员工/顾问维度 | 否 |
| performance_employee_email_name | string | 业绩归属人员工带数字名称 | 员工/顾问维度 | 是 |
| performance_employee_email_prefix | string | 业绩归属人邮箱前缀 | 员工/顾问维度 | 是 |
| performance_city_code | bigint | 业绩归属人城市编码 | 员工/顾问维度 | 否 |
| performance_city_name | string | 业绩归属人城市名称 | 员工/顾问维度 | 否 |
| performance_talent_type_code | bigint | 业绩归属人人才类型编码 | 状态/类型过滤 | 否 |
| performance_talent_type_name | string | 业绩归属人人才类型名称 | 状态/类型过滤 | 否 |
| performance_top_level_department_code | bigint | 业绩归属头部门编码 | 关联键 | 否 |
| performance_top_level_department_name | string | 业绩归属头部门名称 | 范围限定 | 是 |
| performance_first_level_department_code | bigint | 业绩归属一级部门编码 | 关联键 | 否 |
| performance_first_level_department_name | string | 业绩归属一级部门名称 | 范围限定 | 是 |
| performance_second_level_department_code | bigint | 业绩归属二级部门编码 | 关联键 | 否 |
| performance_second_level_department_name | string | 业绩归属二级部门名称 | 范围限定 | 是 |
| performance_third_level_department_code | bigint | 业绩归属三级部门编码 | 关联键 | 否 |
| performance_third_level_department_name | string | 业绩归属三级部门名称 | 范围限定 | 是 |
| performance_last_level_department_code | bigint | 业绩归属末级部门编码 | 关联键 | 否 |
| performance_department_path_json | string | 业绩归属部门路径 | 范围限定 | 否 |
| performance_type | int | 业绩类型，eg：21-续班｜22-扩科｜23-召回｜24-拉新 | 状态/类型过滤 | 否 |
| user_ratio | decimal(20 | 业绩归属用户占比 | 指标聚合 | 否 |
| price_ratio | decimal(20 | 业绩归属金额占比 | 指标聚合 | 否 |
| order_ratio | decimal(20 | 业绩归属订单占比 | 指标聚合 | 否 |
| pay_number | bigint | 支付编号 | 订单/支付维度 | 否 |
| spu_number | bigint | 商品spu编号 | 订单/支付维度 | 否 |
| sku_number | bigint | 商品sku编号 | 订单/支付维度 | 否 |
| course_number | bigint | 课程编号 | 课程/班级维度 | 否 |
| clazz_number | bigint | 班级编号 | 课程/班级维度 | 否 |
| biz_line_type | bigint | 业务线类型，eg：1-k12｜2-成人｜0-不限业务线 | 状态/类型过滤 | 否 |
| mark | bigint | 1:赠课) | 状态/类型过滤 | 否 |
| order_price | bigint | 订单金额(分) | 指标聚合 | 否 |
| sku_count | bigint | 购买sku数量 | 指标聚合 | 否 |
| clazz_hour_count | decimal(20 | 购买课时数 | 指标聚合 | 否 |
| activity_number | bigint | 联报活动编号 | 关联键 | 否 |
| activity_price | bigint | 活动优惠价格（分） | 指标聚合 | 否 |
| fund_supervision_number | string | 资金所在账户编号 | 订单/支付维度 | 否 |
| fund_supervision_name | string | 资金所在账户名称 | 订单/支付维度 | 否 |
| invoice_number | string | 发票主体编号 | 订单/支付维度 | 否 |
| bind_type | bigint | 订单类型，eg：0-正常订单｜1-联报主课订单｜2-联报从课订单 | 状态/类型过滤 | 否 |
| bind_main_order_number | bigint | 联报主课订单编号 | 订单/支付维度 | 否 |
| order_status | bigint | 订单状态 | 状态/类型过滤 | 否 |
| pay_success_timestamp | timestamp | 支付成功时间戳 | 时间过滤/时间分析 | 否 |
| full_refund_timestamp | timestamp | 完全退款时间戳 | 指标聚合 | 否 |
| is_pay_success_order | int | 是否支付成功订单（支付成功过就算，非最新状态），eg：0-否｜1-是 | 状态/类型过滤 | 否 |
| is_part_refund_order | int | 是否部分退款订单，eg：0-否｜1-是 | 指标聚合 | 否 |
| is_full_refund_order | int | 是否全部退款订单，eg：0-否｜1-是 | 指标聚合 | 否 |
| lead_id | bigint | 归因线索id | 关联键 | 是 |
| original_order_number | bigint | 原始父订单订单编号 | 订单/支付维度 | 否 |
| original_order_price | bigint | 原始父订单订单价格 | 指标聚合 | 否 |
| original_order_pay_number | bigint | 原始父订单订单支付编号 | 订单/支付维度 | 否 |
| original_order_activity_number | bigint | 原始父订单订单活动编号 | 订单/支付维度 | 否 |
| original_order_activity_price | bigint | 原始父订单订单活动价格 | 指标聚合 | 否 |
| original_order_pay_success_timestamp | timestamp | 原始父订单支付成功时间 | 时间过滤/时间分析 | 否 |
| original_order_user_number | string | 原始父订单用户编号 | 订单/支付维度 | 否 |
| latest_order_number | bigint | 最新子订单编号 | 订单/支付维度 | 否 |
| latest_order_full_refund_timestamp | timestamp | 最新子订单完全退款时间戳 | 指标聚合 | 否 |
| latest_order_is_pay_success_order | int | 最新子订单是否支付成功订单（支付成功过就算，非最新状态），eg：0-否｜1-是 | 状态/类型过滤 | 否 |
| latest_order_is_part_refund_order | int | 最新子订单是否部分退款订单，eg：0-否｜1-是 | 指标聚合 | 否 |
| latest_order_is_full_refund_order | int | 最新子订单是否全部退款订单，eg：0-否｜1-是 | 指标聚合 | 否 |
| clazz_name | string | 班级名称 | 课程/班级维度 | 否 |
| clazz_biz_number | string | 班级业务编号 | 课程/班级维度 | 否 |
| clazz_type | bigint | 班级类型，eg：1-长期班｜2-短期班｜3-入口班 | 状态/类型过滤 | 否 |
| clazz_begin_timestamp | timestamp | 班级开课时间戳（第一节正式课节开课时间戳） | 时间过滤/时间分析 | 否 |
| clazz_end_timestamp | timestamp | 班级结课时间戳（最后一节正式课节结课时间戳） | 时间过滤/时间分析 | 否 |
| main_teacher_number | bigint | 主讲老师编号（第一节正式课节主讲老师） | 课程/班级维度 | 否 |
| main_teacher_nickname | string | 主讲老师昵称（第一节正式课节主讲老师） | 课程/班级维度 | 否 |
| main_teacher_email_name | string | 主讲老师员工名称（第一节正式课节主讲老师） | 课程/班级维度 | 否 |
| main_teacher_email_prefix | string | 主讲老师邮箱前缀 | 员工/顾问维度 | 否 |
| course_top_level_department_code | bigint | 课程头部门代码 | 课程/班级维度 | 否 |
| course_top_level_department_name | string | 课程头部门名称 | 范围限定 | 是 |
| course_first_level_department_code | bigint | 课程一级部门代码 | 课程/班级维度 | 否 |
| course_first_level_department_name | string | 课程一级部门名称 | 范围限定 | 是 |
| course_second_level_department_code | bigint | 课程二级部门代码 | 课程/班级维度 | 否 |
| course_second_level_department_name | string | 课程二级部门名称 | 范围限定 | 是 |
| course_third_level_department_code | bigint | 课程三级部门代码 | 课程/班级维度 | 否 |
| course_third_level_department_name | string | 课程三级部门名称 | 范围限定 | 是 |
| course_first_level_subject_code | bigint | 课程一级品类代码 | 课程/班级维度 | 否 |
| course_first_level_subject_name | string | 课程一级品类名称 | 课程/班级维度 | 否 |
| course_second_level_subject_code | bigint | 课程二级品类代码 | 课程/班级维度 | 否 |
| course_second_level_subject_name | string | 课程二级品类名称 | 课程/班级维度 | 否 |
| course_third_level_subject_code | bigint | 课程三级品类代码 | 课程/班级维度 | 否 |
| course_third_level_subject_name | string | 课程三级品类名称 | 课程/班级维度 | 否 |
| course_name | string | 课程名称 | 课程/班级维度 | 否 |
| course_category_code | bigint | 课程类型编号 | 课程/班级维度 | 否 |
| course_biz_number | string | 课程业务编号 | 课程/班级维度 | 否 |
| school_department_code | bigint | 学部代码 | 课程/班级维度 | 否 |
| school_department_name | string | 学部名称 | 范围限定 | 是 |
| grade_code | bigint | 年级代码（多个年级取最小值） | 课程/班级维度 | 否 |
| grade_name | string | 年级名称 | 课程/班级维度 | 否 |
| clazz_room_type | bigint | 授课模式，eg：1-大班课｜2-小班课｜3-一对一 | 状态/类型过滤 | 否 |
| school_year | bigint | 学年 | 课程/班级维度 | 否 |
| school_term_code | string | 学期代码 | 课程/班级维度 | 否 |
| school_term_name | string | 学期名称 | 课程/班级维度 | 否 |
| pre_clazz_type | bigint | pre_clazz_type | 状态/类型过滤 | 否 |
| is_renew_class_amount | string | 【课程标签】是否计算续班金额 | 指标聚合 | 否 |
| is_renew_class_user | string | 【课程标签】是否计算续班人次 | 状态/类型过滤 | 否 |
| school_subject_code | bigint | 科目编码 | 课程/班级维度 | 否 |
| school_subject_name | string | 科目名称 | 课程/班级维度 | 否 |
| mapping_school_subject_code | bigint | 映射科目编码 | 课程/班级维度 | 否 |
| mapping_school_subject_name | string | 映射科目名称 | 课程/班级维度 | 否 |
| is_blacklist_user | string | 是否黑名单用户，eg: Y-黑名单 \| N-非黑名单 | 状态/类型过滤 | 否 |
| trade_timestamp | timestamp | 订单交易流水时间，每一笔收款退款的时间 | 时间过滤/时间分析 | 是 |
| pay_refund_type | string | 流水支付退款类型，eg: 支付 \| 退款 | 指标聚合 | 是 |
| income_amount | decimal(20 | 收款金额。单位（分） | 指标聚合 | 是 |
| refund_amount | decimal(20 | 退款金额。单位（分） | 指标聚合 | 是 |
| refund_type | bigint | 退款类型，eg：1-全部退款｜2-部分退款｜3-调出 | 指标聚合 | 否 |
| stats_trade_timestamp | timestamp | 统计口径订单流水时间。如果该笔流水记录为原始父订单首次支付流水时间，则把流水时间改成原始父订单尾款支付时间。其他流水时间保持不变 | 时间过滤/时间分析 | 是 |
| is_original_order_pay_success | string | 【统计标签】是否为原始父订单支付成功流水，eg: Y-是 \| N-否 | 状态/类型过滤 | 否 |
| is_latest_order_first_full_refund | string | 【统计标签】是否最新子订单首次完全退款时间，eg: Y-是 \| N-否 | 指标聚合 | 否 |
| lead_period_number | bigint | 线索归属期number | 关联键 | 否 |
| lead_period_name | string | 线索归属期name | 明细属性 | 否 |
| trade_period_number | string | 流水期number,使用stats_trade_timestamp时间归属的期 | 关联键 | 否 |
| trade_period_name | string | 流水期name,使用stats_trade_timestamp时间归属的期 | 明细属性 | 是 |
| trade_period_conversion_begin_time | string | 流水期转化开始时间 | 时间过滤/时间分析 | 否 |
| trade_period_conversion_end_time | string | 流水期转化结束时间 | 时间过滤/时间分析 | 否 |
| trade_period_mapping_top_level_department_code | string | 流水期top部门code | 关联键 | 否 |
| trade_period_mapping_top_level_department_name | string | 流水期top部门name | 范围限定 | 是 |
| trade_period_mapping_first_level_department_code | string | 流水期top部门code | 关联键 | 否 |
| trade_period_mapping_first_level_department_name | string | 流水期一级部门name | 范围限定 | 是 |
| trade_period_mapping_second_level_department_code | string | 流水期top部门code | 关联键 | 否 |
| trade_period_mapping_second_level_department_name | string | 流水期二级部门name | 范围限定 | 是 |
| trade_period_clazz_begin_time | string | 线索归属期 | 时间过滤/时间分析 | 否 |
| trade_period_is_test | int | 线索归属期 | 状态/类型过滤 | 否 |
| trade_period_first_level_course_project_code | string | 课程一级项目编码 | 课程/班级维度 | 否 |
| trade_period_first_level_course_project_name | string | 课程一级项目名称 | 课程/班级维度 | 否 |
| trade_period_second_level_course_project_code | string | 课程二级项目编码 | 课程/班级维度 | 否 |
| trade_period_second_level_course_project_name | string | 课程二级项目名称 | 课程/班级维度 | 否 |
| trade_period_third_level_course_project_code | string | 课程三级项目编码 | 课程/班级维度 | 否 |
| trade_period_third_level_course_project_name | string | 课程三级项目名称 | 课程/班级维度 | 否 |
| trade_period_first_level_subject_code | string | 课程一级品类编码 | 课程/班级维度 | 否 |
| trade_period_first_level_subject_name | string | 课程一级品类名称 | 课程/班级维度 | 否 |
| trade_period_second_level_subject_code | string | 课程二级品类编码 | 课程/班级维度 | 否 |
| trade_period_second_level_subject_name | string | 课程二级品类名称 | 课程/班级维度 | 否 |
| trade_period_third_level_subject_code | string | 课程三级品类编码 | 课程/班级维度 | 否 |
| trade_period_third_level_subject_name | string | 课程三级品类名称 | 课程/班级维度 | 否 |
| trade_period_main_teacher_numbers | string | 主讲老师编号列表，逗号分隔 | 课程/班级维度 | 否 |
| trade_period_main_teacher_nicknames | string | 主讲老师名称列表，逗号分隔 | 课程/班级维度 | 否 |
| trade_period_course_category_code | string | 课程类型，eg：10-公开课｜20-体验课｜30-专题课｜40-系列课 | 课程/班级维度 | 否 |
| pay_period_number | string | 支付期number,使用stats_trade_timestamp时间归属的期 | 关联键 | 否 |
| pay_period_name | string | 支付期name,使用stats_trade_timestamp时间归属的期 | 明细属性 | 是 |
| pay_period_conversion_begin_time | string | 支付期转化开始时间 | 时间过滤/时间分析 | 否 |
| pay_period_conversion_end_time | string | 支付期转化结束时间 | 时间过滤/时间分析 | 否 |
| pay_period_mapping_top_level_department_code | string | 支付期top部门code | 关联键 | 否 |
| pay_period_mapping_top_level_department_name | string | 支付期top部门name | 范围限定 | 是 |
| pay_period_mapping_first_level_department_code | string | 支付期top部门code | 关联键 | 否 |
| pay_period_mapping_first_level_department_name | string | 支付期一级部门name | 范围限定 | 是 |
| pay_period_mapping_second_level_department_code | string | 支付期top部门code | 关联键 | 否 |
| pay_period_mapping_second_level_department_name | string | 支付期二级部门name | 范围限定 | 是 |
| pay_period_clazz_begin_time | string | 线索归属期 | 时间过滤/时间分析 | 否 |
| pay_period_is_test | int | 线索归属期 | 状态/类型过滤 | 否 |
| pay_period_first_level_course_project_code | string | 课程一级项目编码 | 课程/班级维度 | 否 |
| pay_period_first_level_course_project_name | string | 课程一级项目名称 | 课程/班级维度 | 否 |
| pay_period_second_level_course_project_code | string | 课程二级项目编码 | 课程/班级维度 | 否 |
| pay_period_second_level_course_project_name | string | 课程二级项目名称 | 课程/班级维度 | 否 |
| pay_period_third_level_course_project_code | string | 课程三级项目编码 | 课程/班级维度 | 否 |
| pay_period_third_level_course_project_name | string | 课程三级项目名称 | 课程/班级维度 | 否 |
| pay_period_first_level_subject_code | string | 课程一级品类编码 | 课程/班级维度 | 否 |
| pay_period_first_level_subject_name | string | 课程一级品类名称 | 课程/班级维度 | 否 |
| pay_period_second_level_subject_code | string | 课程二级品类编码 | 课程/班级维度 | 否 |
| pay_period_second_level_subject_name | string | 课程二级品类名称 | 课程/班级维度 | 否 |
| pay_period_third_level_subject_code | string | 课程三级品类编码 | 课程/班级维度 | 否 |
| pay_period_third_level_subject_name | string | 课程三级品类名称 | 课程/班级维度 | 否 |
| pay_period_main_teacher_numbers | string | 主讲老师编号列表，逗号分隔 | 课程/班级维度 | 否 |
| pay_period_main_teacher_nicknames | string | 主讲老师名称列表，逗号分隔 | 课程/班级维度 | 否 |
| pay_period_course_category_code | string | 课程类型，eg：10-公开课｜20-体验课｜30-专题课｜40-系列课 | 课程/班级维度 | 否 |
| is_same_trade_lead_period | string | 【统计标签】流水期与线索期是否相同code，eg: Y-相同 \| N-不同或为空 | 状态/类型过滤 | 否 |
| is_same_second_department | string | 【统计标签】流水期与正价课课程是否同部门，eg: Y-相同 \| N-不同或为空 | 状态/类型过滤 | 否 |
| is_exist_lead | string | 统计标签】是否归因到线索，eg: Y-是 \| N-否 | 状态/类型过滤 | 否 |
| is_full_refund_in_pay_period | string | 【统计标签】最新子订单是否支付期内完全退款，eg: Y-是 \| N-否 | 指标聚合 | 否 |
| is_same_trade_pay_period | string | 【统计标签】流水期是否与支付期相同 | 状态/类型过滤 | 否 |
| refund_pay_diff_seconds | bigint | 【统计标签】统计流水时间与完全支付时间间隔秒。口径：stats_trade_timestamp-original_order_pay_success_timestamp | 指标聚合 | 否 |
| is_stats_conversion_num | string | 【统计标签】是否统计转化数，eg: Y-是 \| N-否 | 状态/类型过滤 | 是 |
| is_stats_conversion_amount | string | 【统计标签】是否统计转化金额，eg: Y-是 \| N-否 | 指标聚合 | 是 |
| trade_group_period_year | string | 流水期分组期年，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 明细属性 | 否 |
| trade_group_period_term | string | 流水期分组期次，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 课程/班级维度 | 否 |
| pay_group_period_year | string | 支付期分组期年，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 明细属性 | 否 |
| pay_group_period_term | string | 支付期分组期次，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 课程/班级维度 | 否 |
| pay_group_period_name | string | 支付期分组期名，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 明细属性 | 是 |
| trade_group_period_name | string | 流水期分组期名，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 明细属性 | 是 |
| stat_judge_type | bigint | 1:拉新 2:续扩 | 状态/类型过滤 | 否 |
| transfer_in_amount | bigint | 调入金额（分） | 指标聚合 | 否 |
| transfer_out_amount | bigint | 调出金额（分） | 指标聚合 | 否 |
| is_same_lead_second_department | string | 是否同线索期二级部门 | 状态/类型过滤 | 否 |
| pre_course_type | int | 前置课程类型 | 状态/类型过滤 | 否 |

## 8. 常用过滤条件

- `t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')`
- `t.hour = format_datetime(now() - interval '2' hour, 'HH')`
- `t.performance_first_level_department_name = '<一级部门名称>'`
- `t.pay_refund_type in ('支付', '退款')`

## 9. 常用 join key

- `lead_id` 可与线索全链路/统计明细表关联。
- `order_number`、`original_order_number`、`latest_order_number` 用于订单维度关联和去重。
- `performance_employee_email_prefix` 可与 `finance_dw.dim_finance_employee_df.email_prefix` 关联补充员工信息。
- 金额字段 `income_amount`、`refund_amount`、`order_price` 文档标注单位为分，看板展示元时通常需 `/100`。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.performance_first_level_department_name = '<一级部门名称>'
limit 20;
```

### 按业绩归属顾问聚合收入和退款

```sql
select
    t.performance_employee_email_prefix,
    sum(t.income_amount) / 100.00 as income_amount_yuan,
    sum(t.refund_amount) / 100.00 as refund_amount_yuan
from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.performance_first_level_department_name = '<一级部门名称>'
group by t.performance_employee_email_prefix
limit 100;
```

## 11. 注意事项

- 该表为小时表，查询必须加 `dt` 和 `hour`。
- 字段描述已按 Word 文档补充，指标口径仍需结合看板 SQL 和业务确认。
- 金额字段多为分单位，展示元时需按口径 `/100`，不要直接混用分/元。

### 退费分析 SQL 使用备注

- 三份退费分析 SQL 使用该表从财务业绩明细补充 `lead_id`，join key 为 `original_order_user_number + performance_employee_email_name` 对应财务表 `user_id1 + name`。
- `n_uid` CTE 按 `original_order_user_number` 排序取最新 `qici` 的 `rn = 1`；如果同一用户在多个顾问或多个期次下有订单，可能只保留最新 lead_id。
- 多科用户退费占比和退费原因分析限定 `course_first_level_department_name = 'H业务线'` 与课程二级部门短名单；退费科目产品 SQL 使用很长的课程一级/二级部门白名单，范围含义待确认。
