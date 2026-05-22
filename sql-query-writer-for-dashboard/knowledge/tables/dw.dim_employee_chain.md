# dw.dim_employee_chain

## 1. 中文名称

员工信息表

## 2. 表用途

用于查询员工基础信息、CAS 角色、邮箱前缀、部门路径、职位、直属上级、新员工状态、离职信息，以及员工在部门内的开始和结束时间。

该表可用于看板中按组织路径限定员工范围，并判断销售流水是否发生在顾问位于指定部门的任职时间段内。

字段来源：`E:\2000_work\GAOTU\员工信息表.docx`。

## 3. 数据粒度

- 员工-部门路径-任职时间段粒度。
- 具体主键唯一性待人工确认；从字段看，建议优先按 `email_prefix + path_name + begin_time + end_time` 理解。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| path_name | string | '高途-H业务线-市场部-市场顾问部' | 是 | 部门全路径名称，组织架构范围限定 |
| department | string | '<部门名称>' | 是 | 部门字段 |
| source_department | string | '<新部门名称>' | 是 | 新部门字段 |
| phase | string | '<学部名称>' | 是 | 学部字段 |
| structure_fnc | string | '<组织架构>' | 是 | 组织架构字段 |
| email_prefix | string | '<员工邮箱前缀>' | 否 | 按员工范围查询时建议限定 |
| name | string | '<员工姓名>' | 否 | 按员工姓名查询时建议限定，姓名不唯一 |

说明：
- 该表用于员工组织链和部门范围判断，生成 SQL 时必须加 `dt`。
- `path_name`、`department`、`source_department`、`phase`、`structure_fnc` 虽不一定都包含 `department_name`，但业务语义是部门/学部/组织架构，使用时必须有范围限定。

## 7. 字段清单

字段来源：`E:\2000_work\GAOTU\员工信息表.docx`，非分区字段 33 个。

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| biz_type | int | 业务线类型 | 状态/类型过滤 | 否 |
| employee_id | string | 员工id | 员工 join key | 是 |
| email_prefix | string | 邮箱前缀 | 员工 join key | 是 |
| role_id | int | cas账号角色，1主讲老师，2辅导老师，3销售老师，其他详见 wiki 枚举 | 角色过滤 | 是 |
| department | string | 部门 | 组织架构范围限定 | 是 |
| phase | string | 学部 | 组织架构范围限定 | 是 |
| path_name | string | 部门全路径名称 | 组织架构范围限定 | 是 |
| parent_department_number | string | ehr父部门number | 组织架构关联 | 否 |
| cas_uid | string | cas_uid | CAS 账号关联 | 否 |
| name | string | 姓名 | 员工 join key | 是 |
| law_name | string | 法律名 | 员工属性 | 否 |
| job_number | string | 员工编号 | 员工 join key | 是 |
| begin_work_time | string | 入职时间 | 入职时间判断 | 是 |
| talent_type | int | 人才类型 | 员工属性 | 否 |
| talent_type_name | string | 人才类型名称 | 员工属性 | 是 |
| position | string | 职位名称id | 职位关联 | 否 |
| position_name | string | 职位名称 | 员工属性 | 是 |
| structure_fnc | string | 组织架构 | 组织架构范围限定 | 是 |
| leader | string | 直属上级（邮箱前缀） | 上级员工关联 | 是 |
| leader_name | string | 直属上级名称 | 上级维度 | 是 |
| display_number | string | 新员工编号 | 员工编号关联 | 是 |
| source_department | string | 新部门 | 组织架构范围限定 | 是 |
| source_status | int | 新员工状态码，1-已入职，8-待离职，4-已离职 | 员工状态过滤 | 是 |
| source_type | int | 新员工类型，1-正式，2-实习，3-劳务 | 员工类型过滤 | 否 |
| source_city | int | 工作城市编号 | 城市维度 | 否 |
| source_city_name | string | 工作城市名称 | 城市维度 | 是 |
| source_hr_status | int | 新在职状态，0-未知，1-在职，2-离职 | 在职状态过滤 | 是 |
| resign_reason | string | 员工离职原因 | 离职分析 | 否 |
| resign_reason_name | string | 员工离职原因名称 | 离职分析 | 否 |
| leave_time | string | 离职时间 | 离职时间判断 | 是 |
| execute_time | string | 执行变更时间 | 组织链变更时间 | 否 |
| begin_time | string | 员工在部门开始时间 | 部门任职期过滤 | 是 |
| end_time | string | 员工在部门结束时间 | 部门任职期过滤 | 是 |

## 8. 常用过滤条件

- `t.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')`
- `array_join(slice(split(t.path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'`
- `t.role_id = 3`
- `t.source_hr_status = 1`
- `t.source_status = 1`

## 9. 常用 join key

- `email_prefix` 可关联财务流水表 `finance_dw.app_finance_performance_extend_details_hf.email_prefix`。
- `name` 可关联财务流水中的 `employee_email_name as name`，但姓名可能不唯一，生产 SQL 应优先确认是否可用 `email_prefix` 替代。
- `employee_id` 可关联其他员工 ID 字段，具体字段需结合目标表确认。
- `job_number`、`display_number` 可用于员工编号关联，需确认口径是否一致。
- `leader` 可关联上级员工的 `email_prefix`。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from dw.dim_employee_chain t
where t.dt = 'YYYYMMDD'
  and array_join(slice(split(t.path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'
limit 20
```

### 销售角色员工抽样

```sql
select
    t.email_prefix,
    t.name,
    t.role_id,
    t.source_hr_status,
    t.path_name,
    t.begin_time,
    t.end_time
from dw.dim_employee_chain t
where t.dt = 'YYYYMMDD'
  and t.role_id = 3
  and array_join(slice(split(t.path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'
limit 50
```

### 按组织路径统计人数

```sql
select
    array_join(slice(split(t.path_name, '-'), 1, 4), '-') as dep_path_4,
    count(distinct t.email_prefix) as employee_cnt
from dw.dim_employee_chain t
where t.dt = 'YYYYMMDD'
  and array_join(slice(split(t.path_name, '-'), 1, 3), '-') = '高途-H业务线-市场部'
group by array_join(slice(split(t.path_name, '-'), 1, 4), '-')
order by employee_cnt desc
limit 50
```

### 提取部门任职起止时间

```sql
select
    array_join(slice(split(t.path_name, '-'), 1, 3), '-') as dep_path,
    t.email_prefix,
    t.name,
    min(t.begin_time) as begin_time,
    max(t.end_time) as end_time
from dw.dim_employee_chain t
where t.dt = 'YYYYMMDD'
  and array_join(slice(split(t.path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'
group by
    array_join(slice(split(t.path_name, '-'), 1, 3), '-'),
    t.email_prefix,
    t.name
limit 100
```

### 用邮箱前缀关联财务流水的推荐模板

```sql
with org_t as (
    select
        t.email_prefix,
        min(t.begin_time) as begin_time,
        max(t.end_time) as end_time
    from dw.dim_employee_chain t
    where t.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and array_join(slice(split(t.path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'
    group by t.email_prefix
)
select
    f.employee_email_name,
    sum(f.price) as amount
from finance_dw.app_finance_performance_extend_details_hf f
join org_t o
  on f.email_prefix = o.email_prefix
where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and f.hour = format_datetime(now() - interval '2' hour, 'HH')
  and f.employee_first_level_department_name = 'H业务线'
  and f.employee_second_level_department_name = '市场部'
  and f.trade_time >= o.begin_time
  and f.trade_time <= o.end_time
group by f.employee_email_name
limit 100
```

## 11. 注意事项

- 字段已根据 `E:\2000_work\GAOTU\员工信息表.docx` 补全，但主键唯一性和具体行权限仍需人工确认。
- `path_name`、`department`、`source_department`、`phase`、`structure_fnc` 属于组织/部门范围字段，查询必须加范围限定。
- `name` 不是稳定唯一键，生成生产 SQL 前应优先确认能否用 `email_prefix` 关联。
- `begin_time`、`end_time` 类型为 string；与 `trade_time` 比较时需确认平台是否按 timestamp 或字符串比较，必要时使用 `cast(... as timestamp)`。
- 若在职员工 `end_time` 为空，`trade_time <= end_time` 会过滤掉记录；是否使用 `coalesce(end_time, '9999-12-31')` 需业务确认。
- `role_id = 3` 表示销售老师，可作为顾问口径过滤条件，但是否必须使用需按看板口径确认。
