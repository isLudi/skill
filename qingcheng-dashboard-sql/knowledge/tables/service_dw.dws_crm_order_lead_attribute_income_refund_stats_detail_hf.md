# service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf

## 1. 中文名称

CRM 订单线索归因收入退款明细小时表

## 2. 表用途

在青橙转化 SQL 中作为订单业绩明细主表，提供订单、用户、支付、退款、营收、课程、业绩归属部门和交易时间等字段。

## 3. 数据粒度

待人工确认。当前 SQL 以订单/线索归因明细使用，字段包含 `order_number`、`lead_id`、`original_order_user_number`。

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
| `performance_second_level_department_name` | `'青橙项目部'` | 业绩归属二级部门，青橙转化核心过滤 |
| `course_first_level_department_name` | 多业务线白名单 | 课程一级部门，历史 SQL 使用长白名单 |
| `course_second_level_department_name` | 长白名单，包含 `'青橙项目部'` | 课程二级部门，历史 SQL 使用长白名单 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_id` | bigint | 线索 ID | join 线索表 |
| `original_order_user_number` | string | 原始订单用户编号 | 转化 SQL 中记为 `uid` |
| `order_number` | bigint | 订单号 | 订单明细字段 |
| `order_status` | bigint | 订单状态 | 订单明细字段 |
| `trade_timestamp` | timestamp | 交易时间 | 计算 `qici` 和成单周期 |
| `pay_success_timestamp` | timestamp | 支付成功时间 | 订单明细字段 |
| `income_amount` | decimal(20 | 收入金额，分 | SQL 除以 100 转元 |
| `refund_amount` | decimal(20 | 退款金额，分 | SQL 除以 100 转元 |
| `performance_employee_email_name` | string | 业绩归属员工 | join 线索员工和最终顾问维度 |
| `performance_second_level_department_name` | string | 业绩归属二级部门 | 青橙过滤 |
| `mapping_school_subject_name` | string | 映射学科 | 非定制方案科目统计 |
| `course_first_level_department_name` | string | 课程一级部门 | 长白名单过滤 |
| `course_second_level_department_name` | string | 课程二级部门 | 长白名单过滤 |
| `pay_group_period_name` | string | 支付期次 | 当前 SQL 取出但未作为核心逻辑 |
| `trade_group_period_name` | string | 交易期次 | 当前 SQL 取出但未作为核心逻辑 |
| `lead_period_name` | string | 线索期次 | 当前 SQL 取出 |
| `trade_period_name` | string | 交易期次 | 当前 SQL 取出 |
| `pay_period_name` | string | 支付期次 | 当前 SQL 取出 |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `performance_employee_id` | bigint | 业绩归属人员工id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_employee_name` | string | 业绩归属人员工名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_employee_email_prefix` | string | 业绩归属人邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_city_code` | bigint | 业绩归属人城市编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_city_name` | string | 业绩归属人城市名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_talent_type_code` | bigint | 业绩归属人人才类型编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_talent_type_name` | string | 业绩归属人人才类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_top_level_department_code` | bigint | 业绩归属头部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_top_level_department_name` | string | 业绩归属头部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_first_level_department_code` | bigint | 业绩归属一级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_first_level_department_name` | string | 业绩归属一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_second_level_department_code` | bigint | 业绩归属二级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_third_level_department_code` | bigint | 业绩归属三级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_third_level_department_name` | string | 业绩归属三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_last_level_department_code` | bigint | 业绩归属末级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_department_path_json` | string | 业绩归属部门路径 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_type` | int | 业绩类型，eg：21-续班｜22-扩科｜23-召回｜24-拉新 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `user_ratio` | decimal(20 | 业绩归属用户占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `price_ratio` | decimal(20 | 业绩归属金额占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_ratio` | decimal(20 | 业绩归属订单占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_number` | bigint | 支付编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `spu_number` | bigint | 商品spu编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sku_number` | bigint | 商品sku编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_number` | bigint | 课程编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_number` | bigint | 班级编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `biz_line_type` | bigint | 业务线类型，eg：1-k12｜2-成人｜0-不限业务线 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `mark` | bigint | 1:赠课) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_price` | bigint | 订单金额(分) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sku_count` | bigint | 购买sku数量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_hour_count` | decimal(20 | 购买课时数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `activity_number` | bigint | 联报活动编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `activity_price` | bigint | 活动优惠价格（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fund_supervision_number` | string | 资金所在账户编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fund_supervision_name` | string | 资金所在账户名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `invoice_number` | string | 发票主体编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `bind_type` | bigint | 订单类型，eg：0-正常订单｜1-联报主课订单｜2-联报从课订单 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `bind_main_order_number` | bigint | 联报主课订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `full_refund_timestamp` | timestamp | 完全退款时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_pay_success_order` | int | 是否支付成功订单（支付成功过就算，非最新状态），eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_part_refund_order` | int | 是否部分退款订单，eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_full_refund_order` | int | 是否全部退款订单，eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_number` | bigint | 原始父订单订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_price` | bigint | 原始父订单订单价格 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_pay_number` | bigint | 原始父订单订单支付编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_activity_number` | bigint | 原始父订单订单活动编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_activity_price` | bigint | 原始父订单订单活动价格 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_pay_success_timestamp` | timestamp | 原始父订单支付成功时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_order_number` | bigint | 最新子订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_order_full_refund_timestamp` | timestamp | 最新子订单完全退款时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_order_is_pay_success_order` | int | 最新子订单是否支付成功订单（支付成功过就算，非最新状态），eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_order_is_part_refund_order` | int | 最新子订单是否部分退款订单，eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_order_is_full_refund_order` | int | 最新子订单是否全部退款订单，eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_name` | string | 班级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_biz_number` | string | 班级业务编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_type` | bigint | 班级类型，eg：1-长期班｜2-短期班｜3-入口班 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_begin_timestamp` | timestamp | 班级开课时间戳（第一节正式课节开课时间戳） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_end_timestamp` | timestamp | 班级结课时间戳（最后一节正式课节结课时间戳） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_teacher_number` | bigint | 主讲老师编号（第一节正式课节主讲老师） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_teacher_nickname` | string | 主讲老师昵称（第一节正式课节主讲老师） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_teacher_email_name` | string | 主讲老师员工名称（第一节正式课节主讲老师） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_teacher_email_prefix` | string | 主讲老师邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_top_level_department_code` | bigint | 课程头部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_top_level_department_name` | string | 课程头部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_department_code` | bigint | 课程一级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_department_code` | bigint | 课程二级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_department_code` | bigint | 课程三级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_department_name` | string | 课程三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_subject_code` | bigint | 课程一级品类代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_subject_name` | string | 课程一级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_subject_code` | bigint | 课程二级品类代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_subject_name` | string | 课程二级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_subject_code` | bigint | 课程三级品类代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_subject_name` | string | 课程三级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_name` | string | 课程名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_category_code` | bigint | 课程类型编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_biz_number` | string | 课程业务编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_department_code` | bigint | 学部代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_department_name` | string | 学部名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `grade_code` | bigint | 年级代码（多个年级取最小值） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `grade_name` | string | 年级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_room_type` | bigint | 授课模式，eg：1-大班课｜2-小班课｜3-一对一 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_year` | bigint | 学年 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_term_code` | string | 学期代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_term_name` | string | 学期名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_clazz_type` | bigint | pre_clazz_type | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_renew_class_amount` | string | 【课程标签】是否计算续班金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_renew_class_user` | string | 【课程标签】是否计算续班人次 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_subject_code` | bigint | 科目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_subject_name` | string | 科目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `mapping_school_subject_code` | bigint | 映射科目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_blacklist_user` | string | 是否黑名单用户，eg: Y-黑名单 \| N-非黑名单 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_refund_type` | string | 流水支付退款类型，eg: 支付 \| 退款 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `refund_type` | bigint | 退款类型，eg：1-全部退款｜2-部分退款｜3-调出 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stats_trade_timestamp` | timestamp | 统计口径订单流水时间。如果该笔流水记录为原始父订单首次支付流水时间，则把流水时间改成原始父订单尾款支付时间。其他流水时间保持不变 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_original_order_pay_success` | string | 【统计标签】是否为原始父订单支付成功流水，eg: Y-是 \| N-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_latest_order_first_full_refund` | string | 【统计标签】是否最新子订单首次完全退款时间，eg: Y-是 \| N-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_number` | bigint | 线索归属期number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_number` | string | 流水期number,使用stats_trade_timestamp时间归属的期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_conversion_begin_time` | string | 流水期转化开始时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_conversion_end_time` | string | 流水期转化结束时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_mapping_top_level_department_code` | string | 流水期top部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_mapping_top_level_department_name` | string | 流水期top部门name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_mapping_first_level_department_code` | string | 流水期top部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_mapping_first_level_department_name` | string | 流水期一级部门name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_mapping_second_level_department_code` | string | 流水期top部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_mapping_second_level_department_name` | string | 流水期二级部门name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_clazz_begin_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_is_test` | int | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_first_level_course_project_code` | string | 课程一级项目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_first_level_course_project_name` | string | 课程一级项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_second_level_course_project_code` | string | 课程二级项目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_second_level_course_project_name` | string | 课程二级项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_third_level_course_project_code` | string | 课程三级项目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_third_level_course_project_name` | string | 课程三级项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_first_level_subject_code` | string | 课程一级品类编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_first_level_subject_name` | string | 课程一级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_second_level_subject_code` | string | 课程二级品类编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_second_level_subject_name` | string | 课程二级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_third_level_subject_code` | string | 课程三级品类编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_third_level_subject_name` | string | 课程三级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_main_teacher_numbers` | string | 主讲老师编号列表，逗号分隔 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_main_teacher_nicknames` | string | 主讲老师名称列表，逗号分隔 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_course_category_code` | string | 课程类型，eg：10-公开课｜20-体验课｜30-专题课｜40-系列课 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_number` | string | 支付期number,使用stats_trade_timestamp时间归属的期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_conversion_begin_time` | string | 支付期转化开始时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_conversion_end_time` | string | 支付期转化结束时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_mapping_top_level_department_code` | string | 支付期top部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_mapping_top_level_department_name` | string | 支付期top部门name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_mapping_first_level_department_code` | string | 支付期top部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_mapping_first_level_department_name` | string | 支付期一级部门name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_mapping_second_level_department_code` | string | 支付期top部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_mapping_second_level_department_name` | string | 支付期二级部门name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_clazz_begin_time` | string | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_is_test` | int | 线索归属期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_first_level_course_project_code` | string | 课程一级项目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_first_level_course_project_name` | string | 课程一级项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_second_level_course_project_code` | string | 课程二级项目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_second_level_course_project_name` | string | 课程二级项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_third_level_course_project_code` | string | 课程三级项目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_third_level_course_project_name` | string | 课程三级项目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_first_level_subject_code` | string | 课程一级品类编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_first_level_subject_name` | string | 课程一级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_second_level_subject_code` | string | 课程二级品类编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_second_level_subject_name` | string | 课程二级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_third_level_subject_code` | string | 课程三级品类编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_third_level_subject_name` | string | 课程三级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_main_teacher_numbers` | string | 主讲老师编号列表，逗号分隔 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_main_teacher_nicknames` | string | 主讲老师名称列表，逗号分隔 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_course_category_code` | string | 课程类型，eg：10-公开课｜20-体验课｜30-专题课｜40-系列课 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_same_trade_lead_period` | string | 【统计标签】流水期与线索期是否相同code，eg: Y-相同 \| N-不同或为空 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_same_second_department` | string | 【统计标签】流水期与正价课课程是否同部门，eg: Y-相同 \| N-不同或为空 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_exist_lead` | string | 统计标签】是否归因到线索，eg: Y-是 \| N-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_full_refund_in_pay_period` | string | 【统计标签】最新子订单是否支付期内完全退款，eg: Y-是 \| N-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_same_trade_pay_period` | string | 【统计标签】流水期是否与支付期相同 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `refund_pay_diff_seconds` | bigint | 【统计标签】统计流水时间与完全支付时间间隔秒。口径：stats_trade_timestamp-original_order_pay_success_timestamp | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_stats_conversion_num` | string | 【统计标签】是否统计转化数，eg: Y-是 \| N-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_stats_conversion_amount` | string | 【统计标签】是否统计转化金额，eg: Y-是 \| N-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_group_period_year` | string | 流水期分组期年，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_group_period_term` | string | 流水期分组期次，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_group_period_year` | string | 支付期分组期年，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_group_period_term` | string | 支付期分组期次，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stat_judge_type` | bigint | 1:拉新 2:续扩 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `transfer_in_amount` | bigint | 调入金额（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `transfer_out_amount` | bigint | 调出金额（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_same_lead_second_department` | string | 是否同线索期二级部门 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_type` | int | 前置课程类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '2' hour, 'HH')
  and performance_second_level_department_name = '青橙项目部'
  and (income_amount <> 0 or refund_amount <> 0)
```

课程部门白名单来自 `data_center_qingcheng_2460_20260626.sql`，非常长；复用时优先从原始 SQL 拷贝，不要手工删减。2026-06-26 canonical 版本的一级部门白名单包含 `H业务线`、`LL业务线`、`TUTU`、`TT`、`A业务线`、`EM业务线`、`KA业务线`、`TT业务线`、`创新中心`，二级部门白名单包含 `创新学部`、`升学规划中心`、`线上考研学部`。

## 9. 常用 join key

- `lead_id`
- `performance_employee_email_name`
- `original_order_user_number`

## 10. 常用 SQL 片段

```sql
coalesce(income_amount / 100, 0) as income_amount,
coalesce(refund_amount / 100, 0) as refund_amount,
coalesce(income_amount / 100, 0) - coalesce(refund_amount / 100, 0) as promit_amount
```

## 11. 注意事项

- 金额字段在原表疑似以分为单位，SQL 除以 100 转为元。
- `promit_amount` 为历史 SQL 字段名，含义为净营收。
- 交易期次 `qici` 由 `trade_timestamp` 按周五期次规则计算，原 SQL 使用三参数 `date_add`，后续生成新 SQL 时需改为 `interval`。
- 转化 raw 当前把本表作为主营收来源，并使用本表自带 `transfer_in_amount` / `transfer_out_amount` 排除已在 service 明细中体现的内部调课调班金额。
- 订单明细侧核对个人/团队完成度时，不要只用原始 `income_amount` / `refund_amount`；部分调课调班链路金额可能体现在 `transfer_in_amount` / `transfer_out_amount`，甚至 service 明细缺失，需要用 `finance_dw.app_finance_performance_extend_details_hf` 补齐缺失事件。
