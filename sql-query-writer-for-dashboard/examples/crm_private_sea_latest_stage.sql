-- 每个用户取最新 CRM 私海阶段
select *
from (
    select
        t.user_number,
        t.sale_flow_stage_sequence,
        t.private_sea_update_time,
        t.assign_employee_first_level_department_name,
        t.assign_employee_second_level_department_name,
        t.assign_employee_third_level_department_name,
        row_number() over (
            partition by t.user_number
            order by t.private_sea_update_time desc
        ) as rn
    from service_dw.dwd_crm_assign_private_detail_hf t
    where t.dt = 'YYYYMMDD'
      and t.hour = 'HH'
      and t.assign_employee_first_level_department_name = '<一级部门名称>'
      and t.assign_employee_second_level_department_name = '<二级部门名称>'
      and t.assign_employee_third_level_department_name = '<三级部门名称>'
) x
where x.rn = 1
limit 100;
