# 最新记录模板

## row_number 取最新记录

```sql
select *
from (
    select
        t.*,
        row_number() over (
            partition by t.user_number
            order by t.private_sea_update_time desc
        ) as rn
    from 完整库名.表名 t
    where t.dt = 'YYYYMMDD'
      and t.hour = 'HH'
      and t.section_assign_employee_second_level_department_name = '<青橙二级部门名称>'
) x
where x.rn = 1
limit 100;
```

## 注意

- `partition by` 必须是业务主键，例如 `user_number`、`lead_id`。
- `order by` 必须是可信更新时间字段。
- 范围过滤字段应替换成当前查询已确认的青橙范围字段。
- 如果存在同一主键多条同一更新时间记录，需增加二级排序字段并标记待确认。
