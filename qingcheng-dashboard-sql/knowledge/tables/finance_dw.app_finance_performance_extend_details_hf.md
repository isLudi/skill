# finance_dw.app_finance_performance_extend_details_hf

## 1. 中文名称

财务业绩扩展明细小时表

## 2. 表用途

在青橙年季月营收、团队完成度【月/期】和个人转化 SQL 中作为财务业绩来源，提供订单、用户、交易、课程、员工、金额和部门归属字段。

## 3. 数据粒度

待人工确认。当前 SQL 以订单/交易明细使用，字段包含 `id`、`order_number`、`biz_number`、`user_id`、`trade_time`。

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
| `employee_first_level_department_name` | `'H业务线'` | 员工一级部门 |
| `employee_second_level_department_name` | `'青橙项目部'` | 员工二级部门 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `id` | bigint | 明细 ID | 调课调班去重排序 |
| `order_number` | bigint | 订单号 | 输出明细字段 |
| `biz_number` | string | 业务编号 | 截取 `sub_biz_number` |
| `pre_biz_number` | string | 前置业务编号 | 当前 SQL 取出 |
| `clazz_name` | string | 班级名称 | 当前 SQL 取出 |
| `user_id` | bigint | 用户 ID | SQL 别名 `user_id1` |
| `pre_employee_id` | int | 前置员工 ID | 当前 SQL 取出 |
| `type` | string | 类型 | 当前 SQL 取出 |
| `trade_status` | string | 交易状态 | 归一为支付/退款/未知 |
| `trade_type` | string | 交易类型 | 正常订单/调课调班 |
| `order_paid_time` | string | 订单支付时间 | SQL 别名 `paid_time` |
| `trade_time` | string | 交易时间 | 计算期次、年季月 |
| `real_price` | double | 实付金额 | `real_price_0` 计算但后续未使用 |
| `transfer_price` | double | 转移金额 | 当前 SQL 取出 |
| `price` | double | 金额 | 营收/退款/净营收核心金额 |
| `email_prefix` | string | 员工邮箱前缀 | 当前 SQL 取出 |
| `employee_email_name` | string | 员工姓名/邮箱名 | SQL 别名 `name`，join 组织表 |
| `talent_type_name` | string | 人才类型 | 当前 SQL 取出 |
| `city_name` | string | 城市 | SQL 别名 `city` |
| `department` | string | 部门 | 当前 SQL 取出 |
| `course_grade` | string | 课程年级 | SQL 别名 `grade_list` |
| `course_subject` | string | 课程科目 | 计算科目数 |
| `course_term_id` | string | 季节 ID | C/X/Q/D 映射春夏秋冬 |
| `leader_employee_email_name` | string | 直属主管 | 当前 SQL 取出 |
| `teacher_name` | string | 主讲老师 | 当前 SQL 取出 |
| `note` | string | 备注 | 当前 SQL 取出 |
| `course_first_level_department_name` | string | 课程一级部门 | 最终维度 |
| `course_second_level_department_name` | string | 课程二级部门 | 最终维度 |
| `course_top_level_department_name` | string | 课程顶级部门 | 当前 SQL 取出 |
| `employee_first_level_department_name` | string | 员工一级部门 | 青橙范围限定 |
| `employee_second_level_department_name` | string | 员工二级部门 | 青橙范围限定 |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `pre_order_number` | bigint | 前置订单号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_subclazz_number` | bigint | 前置辅导班 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `judge_type` | string | "判断类型：1，独立。2，继承。3，重判。" | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `user_ratio` | double | 人数占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `price_ratio` | double | 金额占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_ratio` | double | 订单占比 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_paid_time` | string | 前置订单的支付时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `renewal_type` | string | 续班类型：前置学季 - 后置学季 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `top_order_number` | bigint | 后置订单的原始父订单 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_top_order_number` | bigint | 前置订单的原始父订单 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `display_number` | bigint | 员工工号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_name` | string | 员工姓名 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_on_job` | bigint | 是否在职 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `city_code` | bigint | 城市编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `talent_type_code` | bigint | 人才类型编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_enroll_date` | string | 首次入职时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_enroll_date` | string | 最后一次入职时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_resign_date` | string | 最后一次离职时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `department_path` | string | 组织架构 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `department_code_path` | string | 组织架构编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `position_number` | bigint | 职位编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `position_name` | string | 职位名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `leader_display_number` | bigint | 上级员工工号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_subclazz_name` | string | 前置辅导班名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_subclazz_status` | int | 前置辅导班状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_clazz_number` | bigint | 前置班级number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_clazz_biz_number` | string | 前置班级业务id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_clazz_name` | string | 前置班级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_clazz_type_name` | string | 前置班级标签 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_clazz_classify_type` | int | 前置班级类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_number` | bigint | 前置课程编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_biz_number` | string | 前置课程业务编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_name` | string | 前置课程名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_subject` | string | 前置科目 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_term_id` | string | 前置学季 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_year` | string | 前置学年 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_type` | int | 前置课程类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_grade` | string | 前置年级 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_assistant_number` | bigint | 前置辅导老师number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_assistant_email_prefix` | string | 前置辅导老师邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_assistant_name` | string | 前置辅导老师姓名 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_assistant_talent_type` | int | 前置辅导老师人才类型编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_assistant_talent_type_name` | string | 前置辅导老师人才类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_assistant_city_code` | int | 前置辅导老师城市code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_assistant_city` | string | 前置辅导老师城市名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_teacher_email_prefix` | string | 前置主讲老师邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_teacher_name` | string | 前置主讲老师名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_teacher_number` | bigint | 前置主讲老师number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_teacher_talent_type` | int | 前置主讲老师人才类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_teacher_talent_type_name` | string | 前置主讲老师人才类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_department` | string | 前置课程学部 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_teacher_nickname` | string | 前置主讲老师昵称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `subclazz_number` | bigint | 后置辅导班number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `subclazz_name` | string | 后置辅导班名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `subclazz_status` | int | 后置辅导班状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_number` | bigint | 后置班级number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_biz_number` | string | 后置班级业务id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_type_name` | string | 后置班级标签 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_classify_type` | int | 后置班级类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_number` | bigint | 后置课程number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_biz_number` | string | 后置课程业务id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_name` | string | 后置课程名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_year` | string | 后置学年 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_type` | int | 后置课程类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_number` | bigint | 后置辅导老师number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_email_prefix` | string | 后置辅导老师邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_name` | string | 后置辅导老师姓名 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_talent_type` | int | 后置辅导老师人才类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_talent_type_name` | string | 后置辅导老师人才类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_city_code` | int | 后置辅导老师城市 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_city` | string | 后置辅导老师城市名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `teacher_email_prefix` | string | 后置主讲老师邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `teacher_number` | bigint | 后置主讲老师number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `teacher_talent_type` | int | 后置主讲老师人才类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `teacher_talent_type_name` | string | 主讲老师人才类型名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_department` | string | 后置课程学部 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `teacher_nickname` | string | 后置主讲老师昵称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_price` | double | 订单金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_refund_price` | double | 退款金额 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_status` | string | 订单状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_clazz_begin_time` | string | 前置班级开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_begin_time` | string | 后置班级开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `type_code` | int | 业绩归属类型编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `judge_type_code` | int | 判单类型编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_status_code` | int | 交易状态编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trade_type_code` | int | 交易类型编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_status_code` | int | 订单状态编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `department_code` | int | 学部编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `note_code` | int | 全部退款不扣绩效备注 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `gray_type` | int | 灰名单类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_black` | int | 黑名单标识，1:是，0：否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `top_paid_time` | string | 原始父订单支付时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_assistant_department_path` | string | 前置辅导老师组织架构 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assistant_department_path` | string | 后置辅导老师组织架构 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `refund_order_number` | string | 退款记录编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_clazz_end_time` | string | 前置开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_end_time` | string | 后置开课时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_first_level_department_code` | bigint | 业绩归属人一级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_second_level_department_code` | bigint | 业绩归属人二级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_third_level_department_name` | string | 业绩归属人三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_third_level_department_code` | bigint | 业绩归属人三级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_top_level_department_code` | bigint | 后置课程头部部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_department_code` | bigint | 后置课程一级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_department_code` | bigint | 后置课程二级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_department_code` | bigint | 后置课程三级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_third_level_department_name` | string | 后置课程三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_top_level_department_code` | bigint | 前置课程头部部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_top_level_department_name` | string | 前置课程头部部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_first_level_department_code` | bigint | 前置课程一级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_first_level_department_name` | string | 前置课程一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_second_level_department_code` | bigint | 前置课程二级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_second_level_department_name` | string | 前置课程二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_third_level_department_code` | bigint | 前置课程三级部门代码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_course_third_level_department_name` | string | 前置课程三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

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
- `employee_email_name + qici = temp_table.dingxi01_qing_team_jg.employee_email_name + qici`
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
- 个人完成度/个人转化中，`course_first_level_department_name` 和 `course_second_level_department_name` 可能为空；生成折算后产出相关 SQL 时必须按 `grade_list` 兜底课程部门，否则空部门流水不会进入 H/非 H/一对一桶。
