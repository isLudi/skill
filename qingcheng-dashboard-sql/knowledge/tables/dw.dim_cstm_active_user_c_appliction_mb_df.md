# dw.dim_cstm_active_user_c_appliction_mb_df

## 1. 中文名称

用户应用活跃天级维表

## 2. 表用途

在青橙过程数据 SQL 中获取用户最近一次 APP/PC 登录，并判断近 7 天是否有 APP/PC 登录。

## 3. 数据粒度

待人工确认。当前 SQL 按 `user_number` 取最近 `last_event_time` 一条。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | 待人工确认 | 日期分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| 无青橙部门字段 | 通过青橙线索主表 join 限定 | 单独查询时不能代表青橙范围 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `user_number` | 待人工确认 | 用户编号 | join `data.user_id` |
| `last_event_time` | 待人工确认 | 最近事件时间 | 使用 `%Y-%m-%d %H:%i:%s:%f` 解析 |
| `product_name` | 待人工确认 | 产品名称 | 过滤 `高途`,`规划精品` |
| `appliction_name` | 待人工确认 | 应用名称 | 历史字段拼写为 `appliction_name` |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and product_name in ('高途','规划精品')
```

## 9. 常用 join key

- `user_number = data.user_id`

## 10. 常用 SQL 片段

```sql
row_number() over (
    partition by user_number
    order by try(date_parse(last_event_time, '%Y-%m-%d %H:%i:%s:%f')) desc
) as rn
```

## 11. 注意事项

- 字段名为 `appliction_name`，不是 `application_name`；小时表字段为 `application_name`。

