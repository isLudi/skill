with employee_base as (
    select
        employee_email_name,
        email_prefix,
        employee_name,
        display_number,
        leader_display_number,
        last_enroll_date,
        last_resign_date,
        is_on_job,
        job_status,
        city_name,
        talent_type_name,
        first_level_department_name,
        second_level_department_name,
        third_level_department_name
    from finance_dw.dim_finance_employee_df
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and first_level_department_name = 'H业务线'
      and second_level_department_name = '市场部'
      and third_level_department_name = '市场顾问部'
      and (
            last_resign_date is null
         or last_resign_date = ''
         or cast(last_resign_date as date) >= date '2026-05-01'
      )
),
employee_dim as (
    select distinct
        employee_email_name,
        email_prefix,
        employee_name,
        display_number,
        leader_display_number,
        first_level_department_name,
        second_level_department_name,
        third_level_department_name
    from finance_dw.dim_finance_employee_df
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and first_level_department_name = 'H业务线'
      and second_level_department_name = '市场部'
      and third_level_department_name = '市场顾问部'
)
select distinct
    e.employee_email_name,
    e.email_prefix,
    e.employee_name,
    e.display_number,
    e.last_enroll_date,
    e.last_resign_date,
    e.is_on_job,
    e.job_status,
    e.city_name,
    e.talent_type_name,
    e.first_level_department_name,
    e.second_level_department_name,
    e.third_level_department_name,

    e.leader_display_number as plus1_display_number,
    l1.employee_email_name as plus1_employee_email_name,
    l1.email_prefix as plus1_email_prefix,
    l1.employee_name as plus1_employee_name,
    l1.first_level_department_name as plus1_first_level_department_name,
    l1.second_level_department_name as plus1_second_level_department_name,
    l1.third_level_department_name as plus1_third_level_department_name,

    l1.leader_display_number as plus2_display_number,
    l2.employee_email_name as plus2_employee_email_name,
    l2.email_prefix as plus2_email_prefix,
    l2.employee_name as plus2_employee_name,
    l2.first_level_department_name as plus2_first_level_department_name,
    l2.second_level_department_name as plus2_second_level_department_name,
    l2.third_level_department_name as plus2_third_level_department_name
from employee_base e
left join employee_dim l1
  on e.leader_display_number = l1.display_number
left join employee_dim l2
  on l1.leader_display_number = l2.display_number
order by
    e.employee_email_name
