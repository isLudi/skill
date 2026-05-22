# finance_dw.app_finance_performance_extend_details_hf

## 1. 中文名称

财务业绩扩展明细小时表

## 2. 表用途

在青橙年季月营收 SQL 中作为财务业绩来源，提供订单、用户、交易、课程、员工、金额和部门归属字段。

## 3. 数据粒度

待人工确认。当前 SQL 以订单/交易明细使用，字段包含 `id`、`order_number`、`biz_number`、`user_id`、`trade_time`。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | 待人工确认 | 日期分区 |
| `hour` | 待人工确认 | 小时分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `employee_first_level_department_name` | `'H业务线'` | 员工一级部门 |
| `employee_second_level_department_name` | `'青橙项目部'` | 员工二级部门 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `id` | 待人工确认 | 明细 ID | 调课调班去重排序 |
| `order_number` | 待人工确认 | 订单号 | 输出明细字段 |
| `biz_number` | 待人工确认 | 业务编号 | 截取 `sub_biz_number` |
| `pre_biz_number` | 待人工确认 | 前置业务编号 | 当前 SQL 取出 |
| `clazz_name` | 待人工确认 | 班级名称 | 当前 SQL 取出 |
| `user_id` | 待人工确认 | 用户 ID | SQL 别名 `user_id1` |
| `pre_employee_id` | 待人工确认 | 前置员工 ID | 当前 SQL 取出 |
| `type` | 待人工确认 | 类型 | 当前 SQL 取出 |
| `trade_status` | 待人工确认 | 交易状态 | 归一为支付/退款/未知 |
| `trade_type` | 待人工确认 | 交易类型 | 正常订单/调课调班 |
| `order_paid_time` | 待人工确认 | 订单支付时间 | SQL 别名 `paid_time` |
| `trade_time` | 待人工确认 | 交易时间 | 计算期次、年季月 |
| `real_price` | 待人工确认 | 实付金额 | `real_price_0` 计算但后续未使用 |
| `transfer_price` | 待人工确认 | 转移金额 | 当前 SQL 取出 |
| `price` | 待人工确认 | 金额 | 营收/退款/净营收核心金额 |
| `email_prefix` | 待人工确认 | 员工邮箱前缀 | 当前 SQL 取出 |
| `employee_email_name` | 待人工确认 | 员工姓名/邮箱名 | SQL 别名 `name`，join 组织表 |
| `talent_type_name` | 待人工确认 | 人才类型 | 当前 SQL 取出 |
| `city_name` | 待人工确认 | 城市 | SQL 别名 `city` |
| `department` | 待人工确认 | 部门 | 当前 SQL 取出 |
| `course_grade` | 待人工确认 | 课程年级 | SQL 别名 `grade_list` |
| `course_subject` | 待人工确认 | 课程科目 | 计算科目数 |
| `course_term_id` | 待人工确认 | 季节 ID | C/X/Q/D 映射春夏秋冬 |
| `leader_employee_email_name` | 待人工确认 | 直属主管 | 当前 SQL 取出 |
| `teacher_name` | 待人工确认 | 主讲老师 | 当前 SQL 取出 |
| `note` | 待人工确认 | 备注 | 当前 SQL 取出 |
| `course_first_level_department_name` | 待人工确认 | 课程一级部门 | 最终维度 |
| `course_second_level_department_name` | 待人工确认 | 课程二级部门 | 最终维度 |
| `course_top_level_department_name` | 待人工确认 | 课程顶级部门 | 当前 SQL 取出 |
| `employee_first_level_department_name` | 待人工确认 | 员工一级部门 | 青橙范围限定 |
| `employee_second_level_department_name` | 待人工确认 | 员工二级部门 | 青橙范围限定 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '2' hour, 'HH')
  and employee_first_level_department_name = 'H业务线'
  and employee_second_level_department_name = '青橙项目部'
```

## 9. 常用 join key

- `employee_email_name = org_t.name`
- `employee_email_name = temp_table.dingxi01_qing_zz.employee_email_name`
- `trade_time between org_t.begin_time and org_t.end_time`

## 10. 常用 SQL 片段

```sql
case
    when trade_status like '%退款%' then '退款'
    when trade_status like '%支付%' then '支付'
    else '未知'
end as trade_status
```

## 11. 注意事项

- 当前 SQL 直接使用 `price` 计算营收，没有除以 100；与其他订单表金额单位不同，需确认。
- `real_price_0` 计算后未参与后续营收指标。
- 期次计算使用三参数 `date_add`，后续生成新 SQL 时需改为 `interval` 写法。

