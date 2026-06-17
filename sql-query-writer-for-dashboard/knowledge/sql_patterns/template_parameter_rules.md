# 平台模板取数参数规则

## 适用场景

当用户要求生成可放入公司 SQL 取数平台“模板取数”的 SQL，且 SQL 中需要维护日期或时间区间参数时，使用本规则。

## 日期/时间区间参数

时间区间必须维护为左闭右开的同名字段参数：

```sql
字段名 >= ${字段名:1}
and 字段名 < ${字段名:2}
```

示例：

```sql
dt >= ${dt:1}
and dt < ${dt:2}

trade_time >= ${trade_time:1}
and trade_time < ${trade_time:2}

day >= ${day:1}
and day < ${day:2}
```

## 禁止写法

模板取数 SQL 中不得使用以下写法：

```sql
cast(day as date) >= cast('${begin_paid_time}' as date)
and cast(day as date) <= cast('${end_paid_time}' as date)

trade_time >= '${trade_time1}'
and trade_time < '${trade_time2}'

cast(substr('${begin_paid_time}', 1, 10) as date)
```

原因：

- 平台模板参数识别依赖 `${字段名}` / `${字段名:序号}` 格式。
- 同一个过滤列存在多个参数时，必须使用 `:1`、`:2` 区分区间上下界。
- 参数名必须与过滤列名一致，例如过滤 `trade_time` 时使用 `${trade_time:1}` 和 `${trade_time:2}`。
- 模板版本不能在参数或过滤列外层加 `cast()`、`date()`、`substr()` 等函数，否则平台可能无法添加或识别日期参数。

## 派生日期字段

如果业务上按某个时间字段的日期部分过滤，可以先在 CTE 中派生同名或明确命名字段，再按该字段维护参数：

```sql
substr(trade_time, 1, 10) as day
...
where day >= ${day:1}
  and day < ${day:2}
```

如果希望模板参数显示为 `trade_time`，则过滤列也应直接写为 `trade_time`：

```sql
where trade_time >= ${trade_time:1}
  and trade_time < ${trade_time:2}
```

不要写成过滤 `day` 但参数名叫 `${trade_time:1}`，也不要写成过滤 `trade_time` 但参数名叫 `${begin_trade_time}`。

## 验证 SQL

为了在网页端验证模板 SQL 是否可运行，可以单独生成验证版 SQL，将模板参数替换为带引号的实际值：

```sql
trade_time >= '2026-06-12 00:00:00'
and trade_time < '2026-06-13 00:00:00'
```

验证通过后，交付给用户或写入模板的版本仍应恢复为：

```sql
trade_time >= ${trade_time:1}
and trade_time < ${trade_time:2}
```

## 输出要求

生成模板取数 SQL 时，需要在说明中明确：

- 时间字段名；
- 参数字段名；
- 是否为左闭右开区间；
- 验证版 SQL 使用的实际日期或时间范围；
- 模板版本不包含 `cast()` 函数。
