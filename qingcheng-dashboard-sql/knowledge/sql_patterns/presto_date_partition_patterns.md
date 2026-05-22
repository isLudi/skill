# Presto 日期和分区模式

## 1. 禁止三参数 date_add

禁止：

```sql
date_add('day', -7, current_date)
```

使用：

```sql
current_date - interval '7' day
```

## 2. dt 字符串比较

如果 `dt` 是字符串分区，优先使用字符串日期：

```sql
where t.dt between '2026-05-01' and '2026-05-21'
```

## 3. 单日小时表

```sql
where t.dt = '<yyyy-mm-dd>'
  and t.hour = '<hh>'
```

如果 `hour` 类型待确认，先保持与历史 SQL 一致，并标记待确认。

