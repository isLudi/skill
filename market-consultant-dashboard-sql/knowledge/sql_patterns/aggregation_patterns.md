# 聚合模板

## group by 聚合

非聚合字段必须全部进入 `group by`。

```sql
select
    t.dt,
    t.hour,
    t.assign_employee_first_level_department_name,
    count(distinct t.user_number) as user_cnt
from 完整库名.表名 t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.assign_employee_first_level_department_name = '<一级部门名称>'
group by
    t.dt,
    t.hour,
    t.assign_employee_first_level_department_name
order by user_cnt desc
limit 100;
```

## 条件聚合

```sql
sum(case when t.is_valid_lead = 'Y' then 1 else 0 end) as valid_lead_cnt
```

如果 `is_valid_lead` 取值未确认，必须标记待人工确认。
