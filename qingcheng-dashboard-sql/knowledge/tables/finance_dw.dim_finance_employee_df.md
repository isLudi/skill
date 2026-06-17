# finance_dw.dim_finance_employee_df

## 1. 中文名称

员工维表

## 2. 表用途

记录员工基础信息、账号 ID、邮箱前缀、在职状态、入离职时间、城市、人才类型、岗位和组织架构信息，常用于为业务表补充顾问入离职和架构维度。

本 Skill 仅复用该公共物理表的结构说明，不继承其他部门 Skill 中的默认范围值或业务口径。

字段来源：`E:\2000_work\GAOTU\员工维表.docx`。

## 3. 数据粒度

- 员工-日级快照粒度，建议结合 `dt` 取最新或指定日期的员工状态。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |
## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| first_level_department_name | string | '<青橙一级部门名称>' | 是 | 组织架构一级部门范围 |
| second_level_department_name | string | '<青橙二级部门名称>' | 是 | 组织架构二级部门范围 |
| third_level_department_name | string | '<青橙三级部门/项目名称>' | 是 | 组织架构三级部门范围 |
| is_on_job | bigint | 1 | 是 | 需要在职员工时使用 |
| is_main_job | bigint | 1 | 是 | 需要主岗员工时使用 |

## 7. 字段清单

字段来源：`E:\2000_work\GAOTU\员工维表.docx`，非分区字段 42 个。

| 字段名 | 类型 | 说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| display_number | string | 员工工号 | 员工/顾问维度 | 是 |
| account_id | bigint | account id | 指标聚合 | 是 |
| employee_name | string | 员工名称 | 员工/顾问维度 | 是 |
| employee_email_name | string | 带数字的员工名称 | 员工/顾问维度 | 是 |
| email_prefix | string | 邮箱前缀 | 员工/顾问维度 | 是 |
| birthday | string | 员工生日 | 明细属性 | 否 |
| sex | bigint | 性别，eg：0-男｜1-女 | 明细属性 | 否 |
| first_work_date | string | 第一次工作日期 | 时间过滤/时间分析 | 否 |
| is_main_job | bigint | 是否主岗，eg：0-否｜1-是 | 状态/类型过滤 | 是 |
| is_on_job | bigint | 是否在职，eg：0-否｜1-是 | 状态/类型过滤 | 是 |
| job_status | string | 在岗状态，eg：10-正常在职｜20-试用期｜30-实习｜40-劳务｜50-待离职｜60-已离职 | 状态/类型过滤 | 是 |
| city_code | bigint | 工作城市编码 | 员工/顾问维度 | 否 |
| city_name | string | 工作城市名称 | 员工/顾问维度 | 否 |
| talent_type_code | bigint | 人才类型编码 | 状态/类型过滤 | 否 |
| talent_type_name | string | 人才类型名称 | 状态/类型过滤 | 否 |
| employee_type | bigint | 员工类型，eg：10-正式员工｜20-实习生｜30-劳务人员｜40-派遣人员｜50-外包人员｜60-岗前训人员｜70-平台合作 | 状态/类型过滤 | 否 |
| company_age | bigint | 司龄（天） | 明细属性 | 否 |
| first_enroll_date | string | 第一次入职日期 | 时间过滤/时间分析 | 是 |
| last_enroll_date | string | 最近一次入职日期 | 时间过滤/时间分析 | 是 |
| last_resign_date | string | 最近一次离职日期 | 时间过滤/时间分析 | 是 |
| enroll_dates | string | 入职日期列表（逗号分隔） | 时间过滤/时间分析 | 否 |
| resign_dates | string | 离职日期列表（逗号分隔） | 时间过滤/时间分析 | 否 |
| department_path_json | string | 部门信息，json字符串 | 范围限定 | 否 |
| department_path | string | 部门路径（-分割） | 范围限定 | 是 |
| cost_center_number | bigint | 成本中心编号 | 关联键 | 否 |
| cost_center_name | string | 成本中心名称 | 明细属性 | 否 |
| highest_education | bigint | 最高教育程度，eg：10-博士研究生及以上\|20-硕士研究生\|30-大学本科（一本）\|40-大学本科（二本）\|50-大学本科（三本）\|60-大学专科及以下 | 明细属性 | 否 |
| position_number | string | 职务编号 | 员工/顾问维度 | 否 |
| position_name | string | 职务名称 | 员工/顾问维度 | 否 |
| leader_display_number | string | 直属上级员工工号 | 员工/顾问维度 | 否 |
| leader_employee_email_name | string | 直属上级带数字员工名称 | 员工/顾问维度 | 否 |
| is_skilled_employee | bigint | 是否成熟员工，eg：0-否｜1-是 | 状态/类型过滤 | 否 |
| department_code | bigint | 部门编号 | 关联键 | 否 |
| department_code_path | string | 部门路径code（-分割） | 关联键 | 否 |
| first_level_department_name | string | '<青橙一级部门名称>' | 范围限定 | 是 |
| first_level_department_code | bigint | 组织架构一级部门编码 | 关联键 | 否 |
| second_level_department_name | string | '<青橙二级部门名称>' | 范围限定 | 是 |
| second_level_department_code | bigint | 组织架构二级部门编码 | 关联键 | 否 |
| third_level_department_name | string | '<青橙三级部门/项目名称>' | 范围限定 | 是 |
| third_level_department_code | bigint | 组织架构三级部门编码 | 关联键 | 否 |
| top_level_department_name | string | 组织架构顶级部门名称 | 范围限定 | 是 |
| top_level_department_code | bigint | 组织架构顶级部门编码 | 关联键 | 否 |

## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.is_main_job = 1`
- `t.is_on_job = 1`
- `t.first_level_department_name = '<青橙一级部门名称>'`

## 9. 常用 join key

- `account_id` 可与 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf.account_id` 关联。
- `email_prefix` 可与业务表中 `employee_email_prefix`、`performance_employee_email_prefix` 关联。
- `employee_email_name` 可与临时架构表或财务明细表中的员工姓名关联，但姓名不一定唯一，优先用 `account_id/email_prefix`。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from finance_dw.dim_finance_employee_df t
where t.dt = 'YYYYMMDD'
  and t.first_level_department_name = '<青橙一级部门名称>'
  and t.is_main_job = 1
limit 20;
```

### 按 account_id/邮箱前缀取员工信息

```sql
select
    t.account_id,
    t.email_prefix,
    t.employee_email_name,
    t.is_on_job,
    t.first_level_department_name,
    t.second_level_department_name,
    t.third_level_department_name
from finance_dw.dim_finance_employee_df t
where t.dt = 'YYYYMMDD'
  and t.is_main_job = 1
  and t.first_level_department_name = '<青橙一级部门名称>'
limit 100;
```

## 11. 注意事项

- 该表为日分区表，查询必须加 `dt`。
- 字段描述已按 Word 文档补充，指标口径仍需结合看板 SQL 和业务确认。
- 青橙场景下应使用 `<青橙一级部门名称>`、`<青橙二级部门名称>`、`<青橙三级部门/项目名称>` 占位符或已确认取值，不要沿用其他部门的默认组织范围。
