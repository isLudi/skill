# 聚合模板

## group by 聚合

非聚合字段必须全部进入 `group by`。

```sql
select
    t.dt,
    t.hour,
    t.section_assign_employee_second_level_department_name,
    count(distinct t.user_number) as user_cnt
from 完整库名.表名 t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.section_assign_employee_second_level_department_name = '<青橙二级部门名称>'
group by
    t.dt,
    t.hour,
    t.section_assign_employee_second_level_department_name
order by user_cnt desc
limit 100;
```

如果实际范围字段不是 `section_assign_employee_second_level_department_name`，替换成当前查询已确认的青橙范围字段。

## 条件聚合

```sql
sum(case when t.is_valid_lead = 'Y' then 1 else 0 end) as valid_lead_cnt
```

如果 `is_valid_lead` 取值未确认，必须标记待人工确认。
