# 探索查询模式

## 1. 字段分布

```sql
select
    t.<field>,
    count(*) as cnt
from <库名.表名> t
where t.dt = '<yyyy-mm-dd>'
  and <青橙范围字段> = '<青橙范围取值>'
group by t.<field>
order by cnt desc
limit 100
```

## 2. 明细抽样

```sql
select
    *
from <库名.表名> t
where t.dt = '<yyyy-mm-dd>'
  and <青橙范围字段> = '<青橙范围取值>'
limit 100
```

## 3. 最新小时

```sql
with latest_hour as (
    select max(hour) as hour
    from <库名.小时表> t
    where t.dt = '<yyyy-mm-dd>'
)
select
    t.*
from <库名.小时表> t
join latest_hour h
  on t.hour = h.hour
where t.dt = '<yyyy-mm-dd>'
  and <青橙范围字段> = '<青橙范围取值>'
limit 100
```

