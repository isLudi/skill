# gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf

## 1. 中文名称

顾问首call数据分析表

## 2. 表用途

记录顾问首 call 任务的任务状态、账号、期次、开始/完成/过期时间等信息，用于替换旧看板中来自 `service_dw.app_h_crm_lead_task_process_info_detail_hf` 的 CRM 首 call 任务口径。

本 Skill 仅复用该公共任务表的结构与任务状态口径，不继承其他部门的员工范围列表。

字段来源：`E:\2000_work\GAOTU\顾问首call数据分析表.docx`。

## 3. 数据粒度

- 用户-顾问账号-首call任务-小时快照粒度，可按 `biz_number + account_id` 聚合任务数和已完成数。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |
| hour | string | 小时分区 | 是 |
## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| task_generate_rule_type | int | 2 | 是 | 任务类型 2 表示顾问首call |
| is_del | int | 0 | 是 | 剔除已删除任务 |
| first_call_status | int | 3 | 是 | 如只统计首call已完成，使用 3 |
| start_time | timestamp | 'YYYY-MM-DD' | 是 | 任务开始时间范围 |

## 7. 字段清单

字段来源：`E:\2000_work\GAOTU\顾问首call数据分析表.docx`，非分区字段 19 个。

| 字段名 | 类型 | 说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| id | bigint | id | 关联键 | 否 |
| task_code | string | 任务编号 | 关联键 | 否 |
| subclazz_number | bigint | 辅导班编号（顾问首call不带该字段) | 课程/班级维度 | 否 |
| user_id | bigint | 学员id | 关联键 | 是 |
| first_call_status | int | 首call状态 1.未开始 2.进行中 3.已完成 4.未完成 | 状态/类型过滤 | 是 |
| account_id | bigint | 账号id | 指标聚合 | 是 |
| expired_time | timestamp | 过期时间点 | 时间过滤/时间分析 | 否 |
| finished_time | timestamp | 完成时间点 | 时间过滤/时间分析 | 是 |
| start_time | timestamp | 开始时间点 | 时间过滤/时间分析 | 是 |
| task_generate_rule_type | int | 任务类型 2 顾问首call | 状态/类型过滤 | 是 |
| task_rule_config | string | 任务规则配置 | 任务维度 | 否 |
| org_number | string | 老师虚拟组织架构路径 | 范围限定 | 否 |
| condition_relation | int | 完成条件间关系：1-AND（所有条件都要满足），2-OR（任意条件满足即可） | 状态/类型过滤 | 否 |
| task_tag | int | 任务当前标签：1-有效，2-无效 | 状态/类型过滤 | 否 |
| extend_count | int | 已延长次数 | 指标聚合 | 否 |
| biz_number | bigint | 首call场景下为：期number | 关联键 | 是 |
| is_del | int | 是否删除 | 状态/类型过滤 | 是 |
| create_time | timestamp | 创建时间 | 时间过滤/时间分析 | 否 |
| update_time | timestamp | 更新时间 | 时间过滤/时间分析 | 否 |

## 8. 常用过滤条件

- `t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')`
- `t.hour = format_datetime(now() - interval '2' hour, 'HH')`
- `t.task_generate_rule_type = 2`
- `t.is_del = 0`
- `t.start_time > timestamp '2026-01-01 00:00:00'`

## 9. 常用 join key

- `account_id` 可与 `finance_dw.dim_finance_employee_df.account_id` 关联补充顾问员工信息。
- `biz_number` 在首call场景下为期 number，与期次名 `qici/period_name` 不是同一字段，需确认映射口径。
- `user_id` 可与线索/用户明细中的 `user_id` 关联，需先检查去重口径。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.task_generate_rule_type = 2
  and t.is_del = 0
limit 20;
```

### 按期次和账号统计已完成首call任务

```sql
select
    t.biz_number,
    t.account_id,
    sum(if(t.first_call_status = 3, 1, 0)) as completed24h,
    count(t.first_call_status) as task24h
from gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf t
where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and t.hour = format_datetime(now() - interval '2' hour, 'HH')
  and t.task_generate_rule_type = 2
  and t.is_del = 0
  and t.start_time > timestamp '2026-01-01 00:00:00'
group by t.biz_number, t.account_id
limit 100;
```

### 看板首 call 任务标记桥接主线索

```sql
with first_call_task as (
    select distinct
        t.user_id,
        t.account_id,
        t.first_call_status
    from gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf t
    where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '2' hour, 'HH')
      and t.task_generate_rule_type = 2
      and t.is_del = 0
      and t.start_time > timestamp '2026-01-01 00:00:00'
),
employee_map as (
    select
        account_id,
        employee_email_name
    from (
        select
            e.account_id,
            e.employee_email_name,
            row_number() over (partition by e.account_id order by e.employee_email_name) as rn
        from finance_dw.dim_finance_employee_df e
        where e.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
          and e.first_level_department_name = '<青橙一级部门名称>'
          and e.second_level_department_name = '<青橙二级部门名称>'
    ) x
    where rn = 1
),
f_call0 as (
    select
        m.employee_email_name as assign_employee_email_name,
        t.user_id,
        case
            when sum(case when t.first_call_status = 3 then 1 else 0 end) > 0 then 1
            else 0
        end as completed_first_call_flag
    from first_call_task t
    left join employee_map m
      on t.account_id = m.account_id
    where m.employee_email_name is not null
    group by
        m.employee_email_name,
        t.user_id
)
select
    d.*,
    case
        when d.valid_lead_count = 1 then coalesce(f.completed_first_call_flag, 0)
        else 0
    end as is_f_call
from data d
left join f_call0 f
  on f.assign_employee_email_name = d.employee_email_name
 and f.user_id = d.user_id
```

## 11. 注意事项

- 该表为小时表，查询必须加 `dt` 和 `hour`。
- 字段描述已按 Word 文档补充，指标口径仍需结合看板 SQL 和业务确认。
- 当仅需首 call 已完成任务时，使用 `first_call_status = 3`；如需任务总数，不要过滤掉其他状态。
- 新 SQL 生成 `is_f_call`、首 call 任务数、首 call 任务率时，默认使用本表作为唯一首 call 任务来源；不要再用 `service_dw.app_h_crm_lead_task_process_info_detail_hf.call_answer_lead_count`。
- 员工维表范围应与主查询范围一致；在青橙场景下使用 `<青橙一级部门名称>` / `<青橙二级部门名称>` 占位符或已确认取值，不要复用其他部门的二级部门列表。
