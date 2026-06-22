# finance_dw.dm_finance_order_refund_detail_df

## 1. 中文名称

财务订单退款明细日表

## 2. 表用途

在青橙团队完成度【月/期】和个人转化 SQL 中提供全退订单的退款时间、退款金额和完全退款时已完课课节数，用于计算行课阈值退款 `refund_4`。

## 3. 数据粒度

待人工确认。当前 SQL 按 `order_number` 关联财务业绩订单。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | string | 日期分区 |
## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `course_first_level_department_name` | `'H业务线'` | 课程一级部门 |
| `course_second_level_department_name` | `('精品班学部','菁英班学部','一对一学部')` | 课程二级部门 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `order_number` | bigint | 订单号 | join 财务业绩订单 |
| `user_number` | bigint | 用户编号 | 当前 SQL 取出 |
| `final_paid_timestamp` | timestamp | 最终支付时间 | 当前 SQL 取出 |
| `full_refund_timestamp` | timestamp | 完全退款时间 | 计算退款期次 `qici_re` |
| `total_refund_amount` | bigint | 总退款金额 | 非空且非 0 |
| `talent_type_name` | string | 人才类型 | 当前 SQL 取出 |
| `employee_email_name` | string | 员工姓名/邮箱名 | 当前 SQL 取出 |
| `email_prefix` | string | 员工邮箱前缀 | 当前 SQL 取出 |
| `full_refund_finish_lesson_count` | bigint | 完全退款时已完课课节数 | 直播课，不含类直播赠课 |
| `full_refund_chain_finish_lesson_count` | bigint | 完全退款时调课链路总完课课节数 | 计算 `re_lc` |
| `original_order_pay_success_clazz_remain_lesson_count` | bigint | 原始父订单下单时剩余课节数 | 当前 SQL 取出 |
| `clazz_number` | bigint | 班级编号 | 当前 SQL 取出 |
| `clazz_biz_number` | string | 班级业务编号 | 当前 SQL 取出 |
| `clazz_name` | string | 班级名称 | 当前 SQL 取出 |
| `course_category_code` | bigint | 课程类别编码 | 映射公开课/体验课/专题课/系列课 |
| `course_first_level_department_name` | string | 课程一级部门 | 范围限定 |
| `course_second_level_department_name` | string | 课程二级部门 | 范围限定 |
| `course_third_level_department_name` | string | 课程三级部门 | 当前 SQL 取出 |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `goods_number` | bigint | 商品编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `goods_type` | bigint | 商品类型，2-课程 \| 50-实物 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `performance_employee_id` | bigint | 归属人employee_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `city_code` | bigint | 归属人工作城市 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `talent_type` | bigint | 归属人人才类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_name` | string | 归属人员工姓名 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_number` | bigint | 课程编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_name` | string | 课程名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_biz_number` | string | 课程业务编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_top_level_department_code` | bigint | 课程头部门编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_top_level_department_name` | string | 课程头部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_department_code` | bigint | 课程一级部门编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_department_code` | bigint | 课程二级部门编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_department_code` | bigint | 课程三级部门编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_year` | bigint | 学年 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_term_code` | string | 学期代码，eg：C-春｜X-夏｜Q-秋｜D-冬｜R-循环班｜Y-全年班｜X-Q - 暑秋｜D-C - 寒春班 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_term_name` | string | 学期名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_department_code` | bigint | 学部代码，eg：10-小学｜20-初中｜30-高中｜40-小学专题｜50-成人 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_department_name` | string | 学部名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `grade_code` | bigint | 年级代码（多个年级取最小值） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `grade_name` | string | 年级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_subject_code` | bigint | 科目编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `school_subject_name` | string | 科目名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_subject_code` | bigint | 课程一级品类编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_subject_name` | string | 课程一级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_subject_code` | bigint | 课程二级品类编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_subject_name` | string | 课程二级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_subject_code` | bigint | 课程三级品类编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_subject_name` | string | 课程三级品类名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_type` | bigint | 班级类型，eg：1-长期班｜2-短期班｜3-入口班 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_label` | string | 班级标签 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_teacher_number` | string | 主讲老师编号（第一节正式课节主讲老师） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_teacher_nickname` | string | 主讲老师昵称（第一节正式课节主讲老师） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `main_teacher_email_name` | string | 主讲老师员工名称（第一节正式课节主讲老师） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `full_refund_clazz_finish_lesson_count` | bigint | 完全退款时班级总完课课节数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_lesson_begin_timestamp` | timestamp | 第二讲开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_normal_lesson_begin_timestamp` | timestamp | 第二讲正式课节开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_custom_lesson_begin_timestamp` | timestamp | 第二讲课节修正开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_lesson_begin_timestamp` | timestamp | 第四讲开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_normal_lesson_begin_timestamp` | timestamp | 第四讲正式课节开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_custom_lesson_begin_timestamp` | timestamp | 第四讲课节修正开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_lesson_number` | bigint | 第二讲课节编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_normal_lesson_number` | bigint | 第二讲正式课节编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_custom_lesson_number` | bigint | 第二讲课节修正编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_lesson_number` | bigint | 第四讲课节编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_normal_lesson_number` | bigint | 第四讲正式课节编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_custom_lesson_number` | bigint | 第四讲课节修正编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_lesson_index` | bigint | 第二讲课节序号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_normal_lesson_index` | bigint | 第二讲正式课节序号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `second_custom_lesson_index` | bigint | 第二讲修正课节序号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_lesson_index` | bigint | 第四讲课节序号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_normal_lesson_index` | string | 第四讲正式课节序号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_custom_lesson_index` | string | 第四讲修正课节序号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_number` | bigint | 辅导班老师编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `current_subclazz_number` | bigint | 辅导班编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_email_prefix` | string | 辅导班老师邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_employee_email_name` | string | 辅导老师真实姓名带编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_full_refund_order` | bigint | 是否全部退款 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `full_chain_fourth_lesson_begin_timestamp` | timestamp | 调课链路第4讲开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `full_chain_second_lesson_begin_timestamp` | timestamp | 调课链路第2讲开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_live_normal_lesson_begin_timestamp` | timestamp | 第一讲正式课节直播课开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fourth_live_normal_lesson_begin_timestamp` | timestamp | 第四讲正式课节直播课开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and course_first_level_department_name = 'H业务线'
  and course_second_level_department_name in ('精品班学部','菁英班学部','一对一学部')
  and is_full_refund_order = 1
  and total_refund_amount is not null
  and total_refund_amount <> 0
```

## 9. 常用 join key

- `order_number = rd.order_number`
- 当前完成度 SQL 中，`finance_dw.dim_finance_order_change_df` 会先展开并聚合为订单号映射，再按 `order_number = order_change.order_number` 关联；不要回退为只按 `parent_order_number` 单点关联。

## 10. 常用 SQL 片段

```sql
coalesce(full_refund_chain_finish_lesson_count, 0) as re_lc
```

## 11. 注意事项

- 退款期次 `qici_re` 由 `full_refund_timestamp` 计算，原 SQL 使用三参数 `date_add`；后续生成新 SQL 时需改为 `interval`。
- `full_refund_chain_finish_lesson_count` 是团队完成度和个人转化口径中行课阈值退款的核心字段。
