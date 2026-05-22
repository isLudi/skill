# 首 call 任务指标 SQL 模式

## 适用场景

生成 `is_f_call`、首 call 任务数、首 call 任务率等 CRM 首 call 任务指标时使用。

2026-05-22 起，新 SQL 必须使用 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` 作为首 call 任务来源，并通过 `finance_dw.dim_finance_employee_df.account_id` 转换顾问姓名后关联主线索数据。禁止再使用 `service_dw.app_h_crm_lead_task_process_info_detail_hf.call_answer_lead_count` 拉取首 call 任务指标。

## 口径

- 任务来源：`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`
- 已完成首 call：`first_call_status = 3`
- 顾问首 call 任务：`task_generate_rule_type = 2`
- 有效任务：`is_del = 0`
- 员工桥接：`first_call_task.account_id = finance_dw.dim_finance_employee_df.account_id`
- 主数据关联：`employee_email_name + user_id`
- 根字段：`is_f_call`
- 前端首 call 任务率：`sum(is_f_call) / sum(valid_lead_count)`

## 标准 CTE

```sql
first_call_task as (
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
          and e.first_level_department_name = 'H业务线'
          and e.second_level_department_name in ('市场部','精品班学部','青橙项目部','菁英班学部')
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
```

主数据关联写法：

```sql
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

## 生成规则

- 员工维表范围必须跟主查询范围一致。主查询覆盖多个二级部门时，`employee_map` 使用相同二级部门列表；只有用户明确要求市场顾问部时，才补充 `third_level_department_name = '市场顾问部'`。
- 不要使用 `period_name` 关联首 call 任务表，除非业务提供 `biz_number` 到期次名的映射；`biz_number` 不是 `period_name/qici`。
- 不要使用 `lead_id` 关联首 call 任务表；任务表粒度没有可靠的线索 id。
- 保留 `valid_lead_count = 1` 的门槛，避免无效线索进入 `is_f_call` 分子。
- 若需要严格复刻某个历史运营 SQL 且该 SQL 未过滤 `task_generate_rule_type = 2`，必须在 SQL 说明中标明这是为复刻历史口径而放宽任务类型过滤；默认生成新 SQL 时仍要加 `task_generate_rule_type = 2`。
- 旧过程表 `service_dw.app_h_crm_lead_task_process_info_detail_hf` 仍可用于 `send_double_table`、任务过程、电话接通字段，但不能作为首 call 任务数来源。

## 输出粒度提示

`is_f_call` 是根字段，输出到期次、渠道、年级、部门、顾问等任意聚合粒度时都应先 `sum(is_f_call)`。首 call 任务率在前端或最终 SQL 中用 `sum(is_f_call) / nullif(sum(valid_lead_count), 0)` 计算，不能直接 sum 已计算好的比例。
