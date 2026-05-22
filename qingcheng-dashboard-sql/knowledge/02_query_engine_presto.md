# Presto 查询引擎规则

## 1. 日期和时间

公司查询平台会将 `date_add` 解析为 Hive 两参数函数。生成新 SQL 时禁止使用：

```sql
date_add('day', n, expr)
```

优先使用：

```sql
expr + interval 'n' day
expr - interval 'n' day
```

## 2. 类型比较

数字字段尽量与数字常量比较，避免：

```sql
lead_count >= '2'
```

优先使用：

```sql
lead_count >= 2
```

## 3. group by

`select` 中所有非聚合字段必须出现在 `group by` 中。

## 4. CTE

复杂 SQL 优先使用 CTE。CTE 名称要表达中间结果含义，不要使用无语义的 `a`、`b`、`c` 作为主结构名称。

## 5. limit

探索型查询必须加 `limit`。生产型聚合查询可不加 `limit`，但必须有分区和范围限定。

