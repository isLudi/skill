# bdg_ba.dws_crm_order_income_refund_period_detail_hf

## 1. 中文名称

订单业绩收退款流水期归因明细。

## 2. 表用途

订单业绩收退款流水期归因明细，是已完成交易、课程、商品、业绩归属人与组织部门期归因的正价课收退款事实源。粒度为订单号 + 交易时间 + 收款/退款类型。数据地图表 ID 为 36724，属于 dt/hour 全量小时快照。

## 3. 数据粒度

市场大客户运营部物理探查 Query ID 1599261552 验证 dt=20260923、hour=23 有 614 行、446 个订单、383 条收款、84 条退款；该结果不替代青橙范围独立验证。

## 4. 查询引擎

Presto / Presto_lakehouse。

## 5. 分区字段

dt（日快照）与 hour（小时快照）。

## 6. 强制范围限定字段

必须限定 dt、hour；青橙业绩和商品部门范围、权限集合须本域独立验证后填写。

## 7. 字段清单

| 字段 | 含义/用法 |
|---|---|
| order_number / original_order_number | 订单号 / 原始订单号；不得仅按订单号去重 |
| stats_trade_timestamp | MBR 交易时间基准；模板按源时间减 8 小时展示 |
| pay_success_timestamp / original_order_pay_success_timestamp | 支付时间 / 原始订单支付时间 |
| income_amount / refund_amount | 收款 / 退款金额，单位为分 |
| is_stats_conversion_amount | 正价统计金额标记使用 Y |
| performance_employee_email_name / performance_employee_email_prefix | 归属人带数字姓名 / 邮箱前缀 |
| performance_type | 21 续班、22 扩科、23 召回、24 拉新 |
| stat_judge_type | 1 拉新、2 续扩 |
| course_* / clazz_name | 课程品类、年级、科目、班级信息 |

### 7.1 数据地图字段补充（2026-10-08）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `dt` | string | 日期分区，yyyyMMdd | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `hour` | string | 小时分区，HH | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_number` | bigint | 订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_employee_id` | bigint | 业绩归属人员工id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_employee_name` | string | 业绩归属人员工名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_employee_email_name` | string | 业绩归属人员工带数字名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
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
| `performance_second_level_department_name` | string | 业绩归属二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_third_level_department_code` | bigint | 业绩归属三级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_third_level_department_name` | string | 业绩归属三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_last_level_department_code` | bigint | 业绩归属末级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_department_path_json` | string | 业绩归属部门路径 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_type` | int | 业绩类型，eg：21-续班｜22-扩科｜23-召回｜24-拉新 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `user_ratio` | decimal | 业绩归属用户占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `price_ratio` | decimal | 业绩归属金额占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_ratio` | decimal | 业绩归属订单占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_number` | bigint | 支付编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `spu_number` | bigint | 商品spu编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sku_number` | bigint | 商品sku编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_number` | bigint | 课程编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_number` | bigint | 班级编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `biz_line_type` | bigint | 业务线类型，eg：1-k12｜2-成人｜0-不限业务线 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `mark` | bigint | 1:赠课) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_price` | bigint | 订单金额(分) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sku_count` | bigint | 购买sku数量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_hour_count` | decimal | 购买课时数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `activity_number` | bigint | 联报活动编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `activity_price` | bigint | 活动优惠价格（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fund_supervision_number` | string | 资金所在账户编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fund_supervision_name` | string | 资金所在账户名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `invoice_number` | string | 发票主体编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `bind_type` | bigint | 订单类型，eg：0-正常订单｜1-联报主课订单｜2-联报从课订单 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `bind_main_order_number` | bigint | 联报主课订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_status` | bigint | 订单状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_success_timestamp` | timestamp | 支付成功时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `full_refund_timestamp` | timestamp | 完全退款时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_pay_success_order` | int | 是否支付成功订单（支付成功过就算，非最新状态），eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_part_refund_order` | int | 是否部分退款订单，eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_full_refund_order` | int | 是否全部退款订单，eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_id` | bigint | 归因线索id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_number` | bigint | 原始父订单订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_price` | bigint | 原始父订单订单价格 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_pay_number` | bigint | 原始父订单订单支付编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_activity_number` | bigint | 原始父订单订单活动编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_activity_price` | bigint | 原始父订单订单活动价格 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_pay_success_timestamp` | timestamp | 原始父订单支付成功时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_user_number` | string | 原始父订单用户编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
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
| `course_first_level_department_name` | string | 课程一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_department_code` | bigint | 课程二级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_department_name` | string | 课程二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
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
| `mapping_school_subject_name` | string | 映射科目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_blacklist_user` | string | 是否黑名单用户，eg: Y-黑名单 \| N-非黑名单 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_timestamp` | timestamp | 订单交易流水时间，每一笔收款退款的时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_refund_type` | string | 流水支付退款类型，eg: 支付 \| 退款 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `income_amount` | decimal | 收款金额。单位（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `refund_amount` | decimal | 退款金额。单位（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `refund_type` | bigint | 退款类型，eg：1-全部退款｜2-部分退款｜3-调出 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stats_trade_timestamp` | timestamp | 统计口径订单流水时间。如果该笔流水记录为原始父订单首次支付流水时间，则把流水时间改成原始父订单尾款支付时间。其他流水时间保持不变 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_original_order_pay_success` | string | 【统计标签】是否为原始父订单支付成功流水，eg: Y-是 \| N-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_latest_order_first_full_refund` | string | 【统计标签】是否最新子订单首次完全退款时间，eg: Y-是 \| N-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_number` | bigint | 线索归属期number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_period_name` | string | 线索归属期name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_number` | string | 流水期number,使用stats_trade_timestamp时间归属的期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_name` | string | 流水期name,使用stats_trade_timestamp时间归属的期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
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
| `pay_period_name` | string | 支付期name,使用stats_trade_timestamp时间归属的期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
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
| `pay_group_period_name` | string | 支付期分组期名，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_group_period_name` | string | 流水期分组期名，具体定义见文档：https://wiki.baijia.com/pages/viewpage.action?pageId=280567818 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stat_judge_type` | bigint | 1:拉新 2:续扩 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `transfer_in_amount` | bigint | 调入金额（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `transfer_out_amount` | bigint | 调出金额（分） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_same_lead_second_department` | string | 是否同线索期二级部门 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_type` | int | 前置课程类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `user_id` | bigint | 用户id，线索优先取线索主归因留痕用户，缺失时回退原始父订单用户 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `user_id_source` | string | 用户id来源：lead_trace-线索主归因留痕｜original_order-原始父订单｜missing-缺失 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_attribution_route` | string | 流水期归期路由：course_feature-课程特征｜employee_department-员工部门 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_match_rule_code` | string | 流水期最终命中规则编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_candidate_count` | bigint | 流水期候选期数量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_trade_period_matched` | string | 流水期是否命中：Y-是｜N-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_normal_lesson_begin_timestamp` | timestamp | 最新子订单班级第4节正式课开始时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_candidate_count` | bigint | 最新子订单业绩归属人候选数量 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_selection_rule_code` | string | 业绩归属人选择规则：MIN_EMPLOYEE_ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_source_record_count` | bigint | 同一流水业务键聚合前源记录数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_top_level_department_code` | bigint | 商品头部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_top_level_department_name` | string | 商品头部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_first_level_department_code` | bigint | 商品一级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_first_level_department_name` | string | 商品一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_second_level_department_code` | bigint | 商品二级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_second_level_department_name` | string | 商品二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_third_level_department_code` | bigint | 商品三级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_third_level_department_name` | string | 商品三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_last_level_department_code` | bigint | 商品末级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_department_path_json` | string | 商品部门路径 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

- finance_dw.app_finance_order_income_refund_info_df 是原始交易日快照，本 DWS 是已做业绩期归因的正价课流水事实。Query ID 1599294111 的宽松键仍有 8 个 app-only 和 8 个 DWS-only，不能硬 Join 或互相替代。
- 与 GMV Communication 的用户+归属人候选键存在多对多放大。正价课和促销课应分别生成金额与事件行后 UNION ALL，禁止直接明细 Join 汇总金额。
- GMV 促销分支归属人使用 source_manager_username / source_manager_name；该映射在市场模板成立，青橙使用前仍须本域复验。
- 必须固定 dt/hour 快照并以 stats_trade_timestamp 限制业务时间。青橙部门范围和权限集合必须独立验证。

## 9. 常用 join key

本表与 GMV 不使用金额明细 Join。App↔DWS 仅可用订单、交易时间、金额与归属字段作诊断候选键，不能假定一一关系。

## 10. 常用 SQL 片段

固定 dt/hour 和本域确认的部门范围后，以 stats_trade_timestamp 限制交易周期，并以 is_stats_conversion_amount=Y 取正价统计流水。

## 11. 注意事项

- App↔DWS Query ID 1599294111：606 个匹配键、8 个 app-only、8 个 DWS-only。
- 市场模板 Query ID 1599327539：DWS 正价课 + GMV 促销课双分支 70 行 × 36 列，五项汇总一致。
- 完整周期任务 ID 1599331293：市场大客户运营部共 2,708 行；只作为物理和方法证据。
