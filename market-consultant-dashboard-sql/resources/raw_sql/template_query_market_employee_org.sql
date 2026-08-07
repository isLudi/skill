with jiagou_zx_active as (
    select employee_email_name, employee_email_prefix, xiaozu, jingli, department
    from (
        select
            z.employee_email_name,
            z.employee_email_prefix,
            z.xiaozu,
            z.jingli,
            z.department,
            row_number() over (
                partition by z.employee_email_name
                order by
                    case
                        when z.department = '郑州顾问部' then 1
                        when z.department = '西安一部' then 2
                        when z.department = '西安二部' then 3
                        else 9
                    end,
                    z.employee_email_prefix,
                    z.xiaozu,
                    z.jingli
            ) as rn
        from temp_table.dingxi01_jiagou_zx z
        where cast(z.zaizhi as varchar) = '1'
          and z.department in ('郑州顾问部', '西安一部', '西安二部')
    ) x
    where x.rn = 1
),
employee_snapshot as (
    select
        e.employee_email_name, e.email_prefix, e.employee_name, e.display_number,
        e.leader_display_number, e.last_enroll_date, e.last_resign_date,
        e.is_on_job, e.is_main_job, e.job_status, e.city_name, e.talent_type_name,
        e.first_level_department_name, e.second_level_department_name, e.third_level_department_name
    from finance_dw.dim_finance_employee_df e
    where e.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and e.is_main_job = 1
      and e.first_level_department_name = 'H业务线'
      and e.second_level_department_name = '市场部'
      and e.third_level_department_name = '市场顾问部'
),
employee_dim as (
    select
        d.employee_email_name, d.email_prefix, d.employee_name, d.display_number,
        d.leader_display_number, d.first_level_department_name,
        d.second_level_department_name, d.third_level_department_name
    from finance_dw.dim_finance_employee_df d
    where d.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and d.is_main_job = 1
      and d.first_level_department_name = 'H业务线'
      and d.second_level_department_name = '市场部'
      and d.third_level_department_name = '市场顾问部'
)
select
    coalesce(e.employee_email_name, z.employee_email_name) as employee_email_name,
    coalesce(e.email_prefix, z.employee_email_prefix) as email_prefix,
    e.employee_name, e.display_number, e.last_enroll_date, e.last_resign_date,
    e.is_on_job, e.is_main_job, e.job_status, e.city_name, e.talent_type_name,
    e.first_level_department_name, e.second_level_department_name, e.third_level_department_name,
    z.department as jiagou_department,
    z.jingli as jiagou_jingli,
    z.xiaozu as jiagou_xiaozu,
    e.leader_display_number as plus1_display_number,
    l1.employee_email_name as plus1_employee_email_name,
    l1.email_prefix as plus1_email_prefix,
    l1.employee_name as plus1_employee_name,
    l1.leader_display_number as plus2_display_number,
    l2.employee_email_name as plus2_employee_email_name,
    l2.email_prefix as plus2_email_prefix,
    l2.employee_name as plus2_employee_name,
    case
        when e.employee_email_name is null then '架构名单存在，员工维表未匹配到当前市场顾问部主岗快照'
        when cast(e.is_on_job as varchar) <> '1' then '架构名单在职，员工维表非在职'
        else '架构名单与员工维表市场顾问部主岗快照匹配'
    end as match_status
from jiagou_zx_active z
left join employee_snapshot e
  on z.employee_email_name = e.employee_email_name
left join employee_dim l1
  on e.leader_display_number = l1.display_number
left join employee_dim l2
  on l1.leader_display_number = l2.display_number
order by z.department, z.jingli, z.xiaozu, z.employee_email_name
