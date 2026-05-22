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
| `dt` | 待人工确认 | 日期分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `course_first_level_department_name` | `'H业务线'` | 课程一级部门 |
| `course_second_level_department_name` | `('精品班学部','菁英班学部','一对一学部')` | 课程二级部门 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `order_number` | 待人工确认 | 订单号 | join 财务业绩订单 |
| `user_number` | 待人工确认 | 用户编号 | 当前 SQL 取出 |
| `final_paid_timestamp` | 待人工确认 | 最终支付时间 | 当前 SQL 取出 |
| `full_refund_timestamp` | 待人工确认 | 完全退款时间 | 计算退款期次 `qici_re` |
| `total_refund_amount` | 待人工确认 | 总退款金额 | 非空且非 0 |
| `talent_type_name` | 待人工确认 | 人才类型 | 当前 SQL 取出 |
| `employee_email_name` | 待人工确认 | 员工姓名/邮箱名 | 当前 SQL 取出 |
| `email_prefix` | 待人工确认 | 员工邮箱前缀 | 当前 SQL 取出 |
| `full_refund_finish_lesson_count` | 待人工确认 | 完全退款时已完课课节数 | 直播课，不含类直播赠课 |
| `full_refund_chain_finish_lesson_count` | 待人工确认 | 完全退款时调课链路总完课课节数 | 计算 `re_lc` |
| `original_order_pay_success_clazz_remain_lesson_count` | 待人工确认 | 原始父订单下单时剩余课节数 | 当前 SQL 取出 |
| `clazz_number` | 待人工确认 | 班级编号 | 当前 SQL 取出 |
| `clazz_biz_number` | 待人工确认 | 班级业务编号 | 当前 SQL 取出 |
| `clazz_name` | 待人工确认 | 班级名称 | 当前 SQL 取出 |
| `course_category_code` | 待人工确认 | 课程类别编码 | 映射公开课/体验课/专题课/系列课 |
| `course_first_level_department_name` | 待人工确认 | 课程一级部门 | 范围限定 |
| `course_second_level_department_name` | 待人工确认 | 课程二级部门 | 范围限定 |
| `course_third_level_department_name` | 待人工确认 | 课程三级部门 | 当前 SQL 取出 |

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
- `order_number = finance_dw.dim_finance_order_change_df.parent_order_number`

## 10. 常用 SQL 片段

```sql
coalesce(full_refund_chain_finish_lesson_count, 0) as re_lc
```

## 11. 注意事项

- 退款期次 `qici_re` 由 `full_refund_timestamp` 计算，原 SQL 使用三参数 `date_add`；后续生成新 SQL 时需改为 `interval`。
- `full_refund_chain_finish_lesson_count` 是团队完成度和个人转化口径中行课阈值退款的核心字段。
