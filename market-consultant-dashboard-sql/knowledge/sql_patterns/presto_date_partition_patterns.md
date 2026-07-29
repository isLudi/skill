# Presto 日期分区模板

## 固定日期

```sql
t.dt = 'YYYYMMDD'
```

## 固定小时

```sql
t.dt = 'YYYYMMDD'
and t.hour = 'HH'
```

## 最近 2 小时

```sql
t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and t.hour = format_datetime(now() - interval '2' hour, 'HH')
```

## 最近 24 小时对应日期

```sql
t.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
```

注意：不要默认使用动态时间函数，除非用户明确需要“当前”“最近”“实时”口径。
