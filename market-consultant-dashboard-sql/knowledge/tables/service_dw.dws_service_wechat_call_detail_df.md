# service_dw.dws_service_wechat_call_detail_df

## 1. 中文名称

沟通电话微信明细表

## 2. 表用途

沟通电话微信明细表。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

data-map 高频统计：500 条成功 SQL 中出现 4 次，占比 0.8%。

## 3. 数据粒度

待确认；字段目录未提供数据粒度

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |
## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 | 来源 |
|---|---|---|---|---|---|
| employee_first_level_department_name | string | 'H业务线' | 是 | 业绩归属人一级部门名称 | row_permissions 表级历史取值，出现 4 次 |
| employee_second_level_department_name | string | '精品班学部' | 是 | 业绩归属人二级部门名称 | row_permissions 表级历史取值，出现 2 次 |
| employee_third_level_department_name | string | '学习顾问部' | 是 | 业绩归属人三级部门名称 | 按 row_permissions 同层级历史取值补充 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| communication_timestamp | timestamp | 沟通时间 | 时间分析 | 否 |
| from_username | string | 消息发送者微信id | 待按需求确认 | 否 |
| from_role_code | bigint | 发送者角色 eg:1-老师、2-学生、-1-未知 | 待按需求确认 | 否 |
| from_teacher_email_prefix | string | 发送者为老师时邮箱前缀 | 待按需求确认 | 否 |
| from_user_number | bigint | 发送者为用户时user_number | 待按需求确认 | 否 |
| to_username | string | 接收方微信id | 待按需求确认 | 否 |
| to_role_code | bigint | 接收者角色 eg:1-老师、2-学生、-1-未知 | 待按需求确认 | 否 |
| to_teacher_email_prefix | string | 接收老师邮箱前缀 | 待按需求确认 | 否 |
| to_user_number | bigint | 接收user_number | 待按需求确认 | 否 |
| wechat_msg_type | bigint | 微信消息类型 49001文件 | 待按需求确认 | 否 |
| wechat_msg_name | string | 微信消息类型 | 待按需求确认 | 否 |
| content | string | 沟通内容 | 待按需求确认 | 否 |
| wechat_source | bigint | 微信号来源 | 待按需求确认 | 否 |
| wechat_source_name | string | 微信号来源名称 | 待按需求确认 | 否 |
| is_from_robot | bigint | from是否是机器人 | 待按需求确认 | 否 |
| call_duration | bigint | 通话时长 | 指标聚合 | 是 |
| call_status | bigint | 通话状态 1 是 0 否 | 待按需求确认 | 否 |
| call_type | bigint | 通话类型 1 呼入 2 呼出 | 待按需求确认 | 否 |
| call_type_name | string | 0未知 1 呼入 2 呼出 | 待按需求确认 | 否 |
| call_phone_number | string | 脱敏手机号 | 待按需求确认 | 否 |
| md5_call_phone_number | string | MD5加密手机号 | 待按需求确认 | 否 |
| extend_msg | string | 扩展信息 | 待按需求确认 | 否 |
| data_source | bigint | 数据来源 1:工作机微信 2:其他微信 3:工作机电话 4:先驱电话 | 待按需求确认 | 否 |
| data_source_name | string | 数据来源 | 待按需求确认 | 否 |
| teacher_msg_way | string | 群发/单发 | 待按需求确认 | 否 |
| is_valid_communicate | bigint | 是否有效沟通 1 是 2 否 | 待按需求确认 | 否 |
| is_answered | bigint | 是否被应答 1是 0否 | 待按需求确认 | 否 |
| direct_group_name | string | 小组名称 | 待按需求确认 | 否 |
| direct_leader_email_name | string | 小组长名称带数字名称 | 待按需求确认 | 否 |
| direct_leader_email_prefix | string | 小组长邮箱前缀 | 待按需求确认 | 否 |
| direct_group_parent_department_code | bigint | 小组父节点code | 常用维度 | 是 |
| mini_group_name | string | 帮带组名称 | 待按需求确认 | 否 |
| mini_leader_email_name | string | 帮带师傅名称带数字名称 | 待按需求确认 | 否 |
| mini_leader_email_prefix | string | 帮带师傅邮箱前缀 | 待按需求确认 | 否 |
| mini_group_parent_department_code | bigint | 帮带组父节点code | 常用维度 | 是 |
| group_name | string | 大组名称 | 待按需求确认 | 否 |
| leader_email_name | string | 大组长名称带数字名称 | 待按需求确认 | 否 |
| leader_email_prefix | string | 大组长邮箱前缀 | 待按需求确认 | 否 |
| group_parent_department_code | bigint | 大组父节点code | 常用维度 | 是 |
| operations_unit_name | string | 运营单元名称 | 指标聚合 | 是 |
| operations_unit_leader_email_name | string | 运营单元负责人名称带数字名称 | 指标聚合 | 是 |
| operations_unit_leader_email_prefix | string | 运营单元负责人邮箱前缀 | 指标聚合 | 是 |
| operations_unit_parent_department_code | bigint | 运营单元父节点code | 指标聚合 | 是 |
| sub_operations_unit_name | string | 运营子单元名称 | 指标聚合 | 是 |
| sub_operations_unit_leader_email_name | string | 运营子单元负责人名称带数字名称 | 指标聚合 | 是 |
| sub_operations_unit_leader_email_prefix | string | 运营子单元负责人邮箱前缀 | 指标聚合 | 是 |
| sub_operations_unit_parent_department_code | bigint | 运营子单元父节点code | 指标聚合 | 是 |
| grade_group_name | string | 年级组名称 | 常用维度 | 是 |
| grade_group_leader_email_name | string | 年级组负责人名称带数字名称 | 常用维度 | 是 |
| grade_group_leader_email_prefix | string | 年级组负责人邮箱前缀 | 常用维度 | 是 |
| grade_group_parent_department_code | bigint | 年级组父节点code | 常用维度 | 是 |
| subject_group_name | string | 学科组名称 | 常用维度 | 是 |
| subject_group_leader_email_name | string | 学科组负责人名称带数字名称 | 常用维度 | 是 |
| subject_group_leader_email_prefix | string | 学科组负责人邮箱前缀 | 常用维度 | 是 |
| subject_group_parent_department_code | bigint | 学科组父节点code | 常用维度 | 是 |
| virtual_department_code | bigint | 虚拟组织架构部门编码 | 常用维度 | 是 |
| employee_parent_department_code | bigint | 父节点code | 常用维度 | 是 |
| employee_virtual_department_level_code | bigint | 员工末级节点code组织编码 | 常用维度 | 是 |
| employee_virtual_department_level_name | string | 员工末级节点code组织级别名称 | 常用维度 | 是 |
| employee_first_level_department_code | bigint | 业绩归属人一级部门编码 | 常用维度 | 是 |
| employee_first_level_department_name | string | 业绩归属人一级部门名称 | 权限/业务范围限定 | 是 |
| employee_second_level_department_code | bigint | 业绩归属人二级部门编码 | 常用维度 | 是 |
| employee_second_level_department_name | string | 业绩归属人二级部门名称 | 权限/业务范围限定 | 是 |
| employee_third_level_department_code | bigint | 业绩归属人三级部门编码 | 常用维度 | 是 |
| employee_third_level_department_name | string | 业绩归属人三级部门名称 | 权限/业务范围限定 | 是 |
| robot_task_id | bigint | 机器人任务id | 待按需求确认 | 否 |
| robot_task_package_id | bigint | 机器人任packageid | 待按需求确认 | 否 |
| robot_task_source_desc | string | 机器人任务来源 | 待按需求确认 | 否 |
| robot_task_status | bigint | 机器人任务状态 | 待按需求确认 | 否 |
| employee_email_name | string | 带数字的员工名称 | 常用维度 | 是 |
## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.employee_first_level_department_name = 'H业务线'`
- `t.employee_second_level_department_name = '精品班学部'`
- `t.employee_third_level_department_name = '学习顾问部'`

## 9. 常用 join key

- `employee_email_name`：员工姓名关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.employee_email_name,
    t.employee_first_level_department_name,
    t.employee_second_level_department_name,
    t.employee_third_level_department_name,
    t.communication_timestamp,
    t.from_username,
    t.from_role_code,
    t.from_teacher_email_prefix,
    t.from_user_number,
    t.to_username,
    t.to_role_code,
    t.to_teacher_email_prefix,
    t.to_user_number,
    t.wechat_msg_type,
    t.wechat_msg_name
from service_dw.dws_service_wechat_call_detail_df t
where t.dt = 'YYYYMMDD'
  and t.employee_first_level_department_name = 'H业务线'
  and t.employee_second_level_department_name = '精品班学部'
  and t.employee_third_level_department_name = '学习顾问部'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 71。
- 所属项目：服务域；owner：杨宇星。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
