# CTE 模板

```sql
with base_data as (
    select
        t.user_number,
        t.lead_id,
        t.dt,
        t.hour
    from 完整库名.表名 t
    where t.dt = 'YYYYMMDD'
      and t.hour = 'HH'
      and t.section_assign_employee_second_level_department_name = '<青橙二级部门名称>'
),
final_data as (
    select
        b.user_number,
        count(*) as cnt
    from base_data b
    group by b.user_number
)
select *
from final_data
limit 100;
```

## 规则

- CTE 名称使用业务含义，例如 `base_data`、`call_data`、`stage_data`。
- 每个 CTE 只做一层清晰逻辑。
- 基础 CTE 优先完成分区过滤和青橙范围过滤，再做后续 join 和聚合。
- 复杂看板 SQL 应将基础过滤、join、指标聚合拆开。
