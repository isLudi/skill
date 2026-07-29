-- 探索型查询模板：查询单小时样本
select *
from service_dw.dwd_crm_assign_private_detail_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.assign_employee_first_level_department_name = '<一级部门名称>'
limit 20;
