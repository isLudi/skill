# bdg_ba.dwd_crm_crm_order_income_refund_info_hf

## 1. 中文名称

crm订单归因流水表。数据地图表 ID：27345。

## 2. 表用途

青橙月度流水复刻的待核验候选源；物理字段通过 operator 数据地图同步维护。业务取数状态见 [月度流水复刻](../sql_patterns/qingcheng_monthly_cashflow_excel_replication.md)，不能仅因字段存在或权限获批就认定其与原 Excel 同口径。

**已知业务覆盖缺口（用户确认，2026-10-09）：本表缺失 TT 业务线订单。** 青橙月度订单流水每次必须使用 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 检查并补充 TT。来源切换、TT/V/T 登记范围、共有字段对账、跨源重叠和缺失编码处理均遵循上述月度内置流程。此为本域业务适用性结论，不是 Data Map 字段或分区定义，也不意味着本表所有业务线均为空。

## 3. 数据粒度

全量小时快照。具体业务行粒度、同订单同交易时间是否唯一、历史归属时点待本域探针确认。不得仅按订单号去重。

## 4. 查询引擎

Presto_lakehouse。

## 5. 分区字段

必须给定具体 dt 和 hour；字段类型以数据地图同步段为准。

## 6. 强制范围限定字段

课程或业绩部门限定为已核验的青橙业务范围；权限过滤按当前账号平台检查，不从其他表复制白名单。探索还须限定交易月份或具体订单并设置 LIMIT。

## 7. 字段清单

由 `usql-web-query-operator sync-datamap-fields --target-skill qingcheng --table bdg_ba.dwd_crm_crm_order_income_refund_info_hf` 从数据地图生成，不手写字段。

### 7.1 数据地图字段补充（2026-10-09）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `dt` | string | 天级别分区 yyyyMMdd | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `hour` | string | 小时级分区 HH | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `user_number` | bigint | 用户编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_number` | bigint | 订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_timestamp` | string | 交易时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_month` | string | 交易月份 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_refund_type` | string | 收退类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `income_amount` | bigint | 收款金额(分) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `refund_amount` | bigint | 退款金额(分) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_number` | bigint | 原始父订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_price` | bigint | 原始父订单价格 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_pay_number` | bigint | 原始父订单支付编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_activity_number` | bigint | 原始父订单联报编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_activity_price` | bigint | 原始父订单联报价格 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_order_pay_success_timestamp` | string | 原始父订单支付成功时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_valid_payed` | bigint | 是否有效支付 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_order_number` | bigint | 最新子订单编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_order_is_full_refund_order` | bigint | 最新子订单是否全部退款订单，eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `latest_order_full_refund_timestamp` | string | 最新子订单完全退款时间戳 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_number` | bigint | 课程编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_name` | string | 课程名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_category_code` | bigint | 课程类型编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_department_code` | bigint | 课程一级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_department_name` | string | 课程一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_department_code` | bigint | 课程二级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_department_name` | string | 课程二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_subject_code` | bigint | 课程一级品类代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_subject_name` | string | 课程一级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_subject_code` | bigint | 课程二级品类代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_subject_name` | string | 课程二级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_subject_code` | bigint | 课程三级品类代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_subject_name` | string | 课程三级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_number` | bigint | 班级编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_name` | string | 班级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_biz_number` | string | 班级业务编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_type` | bigint | 班级类型，eg：1-长期班｜2-短期班｜3-入口班 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_clazz_type` | bigint | 前置班型：1，长期班。2，入口班。3，短期班。 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_room_type` | bigint | 授课模式，eg：1-大班课｜2-小班课｜3-一对一 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_attribution_type` | bigint | 业绩归属类型：0, 无归属。1, 长期班保护期续班。2, 长期班扩科。3, 长期班召回。4, 长期班窗口期扩科。5, 长期班保护期外出单。6, 短期班保护期续班。7, 短期班扩科。8, 短期班召回。9, 短期班保护期外出单。10, 其他扩科。11,12, 好课扩科。13，入口班保护期续班，14，入口班保护期扩科，15，入口班召回。16，转介绍。21，续班。22，扩科。23，召回。24，拉新。 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `attribution_is_del` | bigint | 0:有效 1：无效 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `attribution_divide_reason` | bigint | 线索归因原因说明:0:线索归因，1:自然流量2:个人私域-业绩归属人和用户无历史线索管理3:个人私域-历史留痕超30天4:调课订单-无历史归因 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `attribution_divide_reason_name` | string | 线索归因原因说明 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_employee_email_name` | string | 业绩归属人员工带数字名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_employee_email_prefix` | string | 业绩归属人邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_first_level_department_code` | bigint | 业绩归属一级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_first_level_department_name` | string | 业绩归属一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_second_level_department_code` | bigint | 业绩归属二级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_second_level_department_name` | string | 业绩归属二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_third_level_department_code` | bigint | 业绩归属三级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_third_level_department_name` | string | 业绩归属三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_talent_type_code` | bigint | 业绩归属人人才类型编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_talent_type_name` | string | 业绩归属人人才类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_type` | bigint | 业绩类型，eg：21-续班｜22-扩科｜23-召回｜24-拉新 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_id` | bigint | 线索id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_order_period_number` | bigint | 线索期编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `final_new_source` | string | 线索source | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_name_1` | string | 渠道属性-渠道树一级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_name_2` | string | 渠道属性-渠道树二级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_name_3` | string | 渠道属性-渠道树三级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_id` | bigint | 渠道属性-流量池id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_name` | string | 渠道属性-流量池 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_type_id` | bigint | 渠道属性-流量池类型id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_pool_type_name` | string | 渠道属性-流量池类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_provider_id` | bigint | 渠道属性-业务渠道商id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_provider_name` | string | 渠道属性-业务渠道商 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_second_provider_id` | bigint | 渠道属性-二级渠道商id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `channel_second_provider_name` | string | 渠道属性-二级渠道商 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_lead_conversion_tag` | bigint | 是否线索转化 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `o_order_is_payed_tag` | bigint | 原始父订单是否支付 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `o_order99_is_payed_tag` | bigint | 原始父订单是否有效支付 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `o_order_refund_is_same_pay_period` | bigint | 原始父订单是否有效支付且与在支付期内退款 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `o_order_is_fullrefund_tag` | bigint | 原始父订单是否完全退款 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_full_refund_trade_tag` | bigint | 原始付订单是否在该流水完全退款 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `refund_is_same_pay_period` | bigint | 退款流水是否在支付期内退款 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_code` | bigint | 流水期code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_name` | string | 流水期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_begin_time` | string | 流水期开始转化时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_period_end_time` | string | 流水期结束转化时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_code` | bigint | 支付期code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_name` | string | 支付期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_begin_time` | string | 支付期开始转化时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pay_period_end_time` | string | 支付期结束转化时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_in_blacklist` | bigint | 用户是否在黑名单内 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `rn_number` | bigint | 辅助编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_employee_id` | string | 归属人employee_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_last_performance_employee_id` | bigint | 业绩最新归属人employee_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_last_performance_employee_email_name` | string | 业绩最新归属人姓名+数字 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_last_performance_employee_email_prefix` | string | 业绩最新归属人邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stat_judge_type` | bigint | 正价课 1:拉新 2:续扩 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_subject_code` | int | 科目code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_subject_name` | string | 科目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `mapping_school_subject_code` | bigint | 映射科目代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `mapping_school_subject_name` | string | 映射科目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `price_ratio` | double | 价格占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_type` | int | 商品类型，eg：2-班级｜50-实物｜51-组合｜6003-小班课｜7001-课时包｜70002-倾听师 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_same_period_type` | bigint | 是否当期转化 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_calculate_order_cnt` | string | 是否计算续班人次 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_calculate_order_amount` | string | 是否计算续班金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_year` | int | 学年 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_term_code` | bigint | 学季代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_term_name` | string | 学季 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `grade_code` | string | 年级代码，多个年级取最小值 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `grade_name` | string | 年级 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_department_code` | bigint | 课程二级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_department_name` | string | 课程二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

目标业务月份与物理快照分区分别限定；零金额、归属有效性、统计标签规则待核验。

## 9. 常用 join key

订单号和交易信息为候选关联键；任何补字段 Join 必须先检查一对多及金额放大，当前未登记 confirmed Join。

## 10. 常用 SQL 片段

尚无经全月回归的生产 SQL，使用有界探针。

## 11. 注意事项

- 2026-10-08 曾被平台拒绝整表查询；2026-10-09 用户确认审批通过，实际验证回执保存在任务工作目录。
- 权限快照不是业务口径。不能以此表的可读性绕过其他源表的访问控制。
