# 探索型查询模板

## A. desc 表结构

```sql
desc 完整库名.表名;
```

## B. 简单抽样

```sql
select *
from 完整库名.表名 t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
limit 20;
```

## C. 带 department_name 范围限定的抽样

```sql
select *
from 完整库名.表名 t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.assign_employee_first_level_department_name = '<一级部门名称>'
limit 20;
```

## D. 分区数据量探索

```sql
select
    t.dt,
    t.hour,
    count(*) as cnt
from 完整库名.表名 t
where t.dt in ('YYYYMMDD')
  and t.hour in ('HH')
group by t.dt, t.hour
order by t.dt desc, t.hour desc
limit 50;
```
