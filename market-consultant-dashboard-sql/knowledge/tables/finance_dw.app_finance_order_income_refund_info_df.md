# finance_dw.app_finance_order_income_refund_info_df

## 1. 中文名称

订单收款退款交易信息表。

## 2. 表用途

记录订单收款、退款交易及订单、用户、课程、商品、班级、业绩归属人与组织字段。市场顾问部可用于生成交易流水明细；收入、退款金额单位为分。

## 3. 数据粒度

数据地图登记为全量日快照表。业务行包含订单号、原始订单号、支付编号、交易时间、业绩归属人和课程/商品信息；精确流水唯一键尚待 USQL 基数探针确认，不能仅按订单号去重。

## 4. 查询引擎

Presto / Presto_lakehouse。

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级全量快照分区，yyyyMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 推荐取值/规则 | 是否必填 | 说明 |
|---|---|---|---|
| performance_first_level_department_name | `'H业务线'` | 是 | 业绩归属一级部门 |
| performance_second_level_department_name | `'市场部'` | 是 | 业绩归属二级部门 |
| performance_third_level_department_name | `'大客户运营部'` | 是 | 本次后续取数目标的业绩归属三级部门 |
| goods_first_level_department_name | `'H业务线'` | 是 | 平台行权限必需范围 |
| goods_second_level_department_name | 使用平台返回的授权值集合 | 是 | 平台要求明确等值/IN 范围；不得把单一商品部门探针外推为全量口径 |
| dt | 固定快照日 | 是 | 全量快照表禁止无分区扫描 |

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|

### 7.1 数据地图字段补充（2026-09-24）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| business_dt | string | 收入/退款时间（yyyyMMdd日期） | 数据地图补充 | 否 |
| biz_type | bigint | 业务类型，eg：1-好课｜2-高途 | 数据地图补充 | 否 |
| biz_line_type | bigint | 业务线类型，eg：1- K12｜2-成人 | 数据地图补充 | 否 |
| order_number | bigint | 订单编号 | 数据地图补充 | 否 |
| trade_timestamp | timestamp | 收入/退款时间戳 | 数据地图补充 | 否 |
| final_paid_timestamp | timestamp | 订单支付时间 | 数据地图补充 | 否 |
| order_status | bigint | 订单状态 1:未付款;2:已付款;4:手动取消;5:自动取消;6:全额退款;7:部分退款 | 数据地图补充 | 否 |
| original_order_number | bigint | 原始父订单 | 数据地图补充 | 否 |
| fund_supervision_number | string | 收款账户编号 | 数据地图补充 | 否 |
| fund_supervision_name | string | 收款账户名称 | 数据地图补充 | 否 |
| performance_employee_id | bigint | 业绩归属人id | 数据地图补充 | 否 |
| performance_type | bigint | 业绩归属类型：0, 无归属。1, 正价班保护期续班。2, 正价班扩科。3, 正价班转介绍。 | 数据地图补充 | 否 |
| order_price_category | bigint | 订单价格类型,0 9.9 99 0，免费课；1，促销课；2，体验课；3，正价课 | 数据地图补充 | 否 |
| user_number | bigint | 用户id | 数据地图补充 | 否 |
| user_province | string | 用户省份 | 数据地图补充 | 否 |
| user_city_level | string | 用户城市等级 | 数据地图补充 | 否 |
| course_number | bigint | 课程编号 课程 | 数据地图补充 | 否 |
| course_biz_number | string | 课程ID | 数据地图补充 | 否 |
| course_name | string | 课程名称 | 数据地图补充 | 否 |
| course_top_level_department_code | bigint | 课程所属零级部门代码 | 数据地图补充 | 否 |
| course_top_level_department_name | string | 课程所属零级部门名称 | 数据地图补充 | 否 |
| course_first_level_department_code | bigint | 课程所属一级部门代码 | 数据地图补充 | 否 |
| course_first_level_department_name | string | 课程所属一级部门名称 | 数据地图补充 | 否 |
| course_second_level_department_code | bigint | 课程所属二级部门代码 | 数据地图补充 | 否 |
| course_second_level_department_name | string | 课程所属二级部门代名称 | 数据地图补充 | 否 |
| course_third_level_department_code | bigint | 课程所属三级部门代码 | 数据地图补充 | 否 |
| course_third_level_department_name | string | 课程所属三级部门名称 | 数据地图补充 | 否 |
| course_first_level_subject_code | bigint | 课程一级品类 | 数据地图补充 | 否 |
| course_second_level_subject_code | bigint | 课程二级品类 | 数据地图补充 | 否 |
| course_third_level_subject_code | bigint | 课程三级品类 | 数据地图补充 | 否 |
| course_category_code | bigint | 课程类型代码，eg：10-公开课｜20-体验课｜30-专题课｜40-系列课 | 数据地图补充 | 否 |
| school_year_id | bigint | 课程学年 | 数据地图补充 | 否 |
| school_term_id | string | 课程学季 | 数据地图补充 | 否 |
| talent_type | bigint | 业绩归属人人才类型 X 结果表 | 数据地图补充 | 否 |
| city_name | string | 业绩归属人工作城市 X 结果表 | 数据地图补充 | 否 |
| performance_top_level_department_code | bigint | 业绩所属头部门代码 | 数据地图补充 | 否 |
| performance_first_level_department_code | bigint | 业绩所属一级部门代码 | 数据地图补充 | 否 |
| performance_second_level_department_code | bigint | 业绩所属二级部门代码 | 数据地图补充 | 否 |
| performance_third_level_department_code | bigint | 业绩所属三级部门代码 | 数据地图补充 | 否 |
| performance_third_level_department_name | string | 业绩所属三级部门名称 | 数据地图补充 | 否 |
| clazz_number | bigint | 班级编号 | 数据地图补充 | 否 |
| clazz_biz_number | string | 班级ID | 数据地图补充 | 否 |
| clazz_name | string | 班级名称 | 数据地图补充 | 否 |
| calzz_beign_timestamp | timestamp | 班级开课时间 | 数据地图补充 | 否 |
| clazz_end_timestamp | timestamp | 班级结课时间 | 数据地图补充 | 否 |
| type | string | 班级直播类型， 直播、视频、伪直播、混合 | 数据地图补充 | 否 |
| teacher_nickname_first | string | 班级首节主讲：班级维度，第一个课节所对应的主讲老师，不包含补充课节 | 数据地图补充 | 否 |
| teacher_name | string | 班级主讲 正式课节主讲，多主讲逗号分割，按姓名顺序聚合 | 数据地图补充 | 否 |
| clazz_type | bigint | 班级标签 | 数据地图补充 | 否 |
| channel_top_level_department_code | bigint | 渠道头部门代码 | 数据地图补充 | 否 |
| channel_top_level_department_name | string | 渠道头部门名称 | 数据地图补充 | 否 |
| channel_first_level_department_code | bigint | 渠道一级部门代码 | 数据地图补充 | 否 |
| channel_first_level_department_name | string | 渠道一级部门名称 | 数据地图补充 | 否 |
| channel_second_level_department_code | bigint | 渠道二级部门代码 | 数据地图补充 | 否 |
| channel_second_level_department_name | string | 渠道二级部门名称 | 数据地图补充 | 否 |
| channel_third_level_department_code | bigint | 渠道三级部门代码 | 数据地图补充 | 否 |
| channel_third_level_department_name | string | 渠道三级部门名称 | 数据地图补充 | 否 |
| income_amount | decimal(20 | 收入金额(分) | 数据地图补充 | 否 |
| refund_amount | decimal(20 | 退费金额(分) | 数据地图补充 | 否 |
| course_first_level_subject_name | string | 一级品类名称 | 数据地图补充 | 否 |
| course_second_level_subject_name | string | 二级品类名称 | 数据地图补充 | 否 |
| course_third_level_subject_name | string | 三级品类名称 | 数据地图补充 | 否 |
| order_type | bigint | 订单类型：0，正常订单；1，联报主课订单；2，联报从课订单; 4,公开课 | 数据地图补充 | 否 |
| city_code | string | 业绩归属人-工作城市 | 数据地图补充 | 否 |
| talent_type_name | string | 业绩归属人-人才类型名称 | 数据地图补充 | 否 |
| employee_name | string | 业绩归属人-员工名称 | 数据地图补充 | 否 |
| employee_email_name | string | 业绩归属人-带数字的员工名称 | 数据地图补充 | 否 |
| email_prefix | string | 业绩归属人-邮箱前缀 | 数据地图补充 | 否 |
| pay_number | bigint | 支付编号 | 数据地图补充 | 否 |
| goods_type | bigint | 商品类型，2-课程 \| 50-实物 | 数据地图补充 | 否 |
| goods_number | bigint | 商品编号 | 数据地图补充 | 否 |
| goods_top_level_department_code | bigint | 商品所属零级部门代码 | 数据地图补充 | 否 |
| goods_top_level_department_name | string | 商品所属零级部门名称 | 数据地图补充 | 否 |
| goods_first_level_department_code | bigint | 商品所属一级部门代码 | 数据地图补充 | 否 |
| goods_second_level_department_code | bigint | 商品所属二级部门代码 | 数据地图补充 | 否 |
| goods_third_level_department_code | bigint | 商品所属三级部门代码 | 数据地图补充 | 否 |
| goods_third_level_department_name | string | 商品所属三级部门名称 | 数据地图补充 | 否 |
| current_subclazz_number | bigint | 当前在读辅导班编号 | 数据地图补充 | 否 |
| assistant_email_prefix | string | 辅导老师邮箱前缀 | 数据地图补充 | 否 |
| current_subclazz_biz_number | string | 当前在读辅导班业务编号 | 数据地图补充 | 否 |
| channel_source | string | 引流课渠道来源 | 数据地图补充 | 否 |

## 8. 常用过滤条件

- 必须固定 `dt` 快照日。
- 市场大客户运营部范围使用 `performance_first_level_department_name = 'H业务线'`、`performance_second_level_department_name = '市场部'`、`performance_third_level_department_name = '大客户运营部'`。
- 平台行权限还要求 `goods_first_level_department_name = 'H业务线'`，并为 `goods_second_level_department_name` 提供明确等值或授权集合。
- 交易周期使用 `trade_timestamp` 或 `business_dt`，不能用快照分区 `dt` 代替业务时间。

## 9. 常用 join key

用户明确本任务中的“业财表”指 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`。目标交易表没有 `lead_id`，GMV Communication 也没有可作为正价交易订单号的稳定订单字段，因此不能按 `lead_id` 或 `flow_order_number` 直接关联正价订单。

可执行的候选桥接键为 `user_number = user_id` 且 `email_prefix = employee_email_prefix`。2026-09-24 使用双方 `dt='20260923'`、GMV `hour='23'` 及大客户运营部范围实测：交易侧 85 个用户-归属人键中命中 83 个（97.6471%），覆盖 604/614 条流水；但 58 个键对应多条 GMV 记录、58 个键跨多期次，直接 Join 会生成 1,839 行，是已命中流水的 3.0447 倍。必须先按所需期次/线索规则选定唯一主归因行，或使用 `exists`/按键预聚合；禁止用 GMV 明细直接承接、汇总交易金额。证据：USQL Query ID `1599192970`。

GMV Communication 实际不存在 `section_assign_employee_email_prefix`；使用该字段的探针由平台报 `cannot resolve column`（Query ID `1599194950`），不得将外呼表上的同名字段规则迁移到本表关系。

## 10. 常用 SQL 片段

```sql
select
    order_number, original_order_number, user_number,
    trade_timestamp, final_paid_timestamp,
    income_amount, refund_amount, performance_employee_id, email_prefix
from finance_dw.app_finance_order_income_refund_info_df
where dt = '<快照日YYYYMMDD>'
  and performance_first_level_department_name = 'H业务线'
  and performance_second_level_department_name = '市场部'
  and performance_third_level_department_name = '大客户运营部'
  and goods_first_level_department_name = 'H业务线'
  and goods_second_level_department_name in (<平台授权值集合>)
  and trade_timestamp >= timestamp '<开始时间>'
  and trade_timestamp < timestamp '<结束时间>'
limit 100;
```

## 11. 注意事项

- `income_amount`、`refund_amount` 单位为分；净收需派生为 `(income_amount - refund_amount) / 100.0`。
- 交易流水日/月由 `trade_timestamp` 派生；支付日由 `final_paid_timestamp` 派生。
- 正价支付/退费人次需结合 `order_price_category = 3`、收退款方向与明确去重粒度定义，不能直接把物理行数当人次。
- 年级、科目和“课程部门(修正)”不在该表的数据地图字段中，需从课程品类/班级字段派生或使用已确认维表；不得从 GMV Communication 的购买意向字段冒充成交课程属性。
- `flow_order_number` 是 GMV Communication 的主留痕引流课订单号，不是本表正价交易 `order_number`；两者禁止直接等值关联。
- 本表本地知识只记录物理字段和本域使用边界，不代表已经授权最终大结果下载。
