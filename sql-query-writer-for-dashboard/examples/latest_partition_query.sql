-- 查询分区数据量
select
    t.dt,
    t.hour,
    count(*) as cnt
from service_dw.dwd_crm_assign_private_detail_hf t
where t.dt in ('YYYYMMDD')
  and t.assign_employee_first_level_department_name = '<一级部门名称>'
group by t.dt, t.hour
order by t.dt desc, t.hour desc
limit 50;
