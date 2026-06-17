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
| `dt` | string | 日期分区 |
## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| 无青橙部门字段 | 通过青橙线索主表 join 限定 | 单独查询时不能代表青橙范围 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `user_number` | string | 用户编号 | join `data.user_id` |
| `last_event_time` | string | 最近事件时间 | 使用 `%Y-%m-%d %H:%i:%s:%f` 解析 |
| `product_name` | string | 产品名称 | 过滤 `高途`,`规划精品` |
| `appliction_name` | string | 应用名称 | 历史字段拼写为 `appliction_name` |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `event_time` | string | 用户在各应用第一次出现的时间 yyyy-MM-dd hh:mm:ss | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_app_channel` | string | 设备首次出现渠道 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_app_channel` | string | 最后一次渠道 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_date` | string | 用户在各应用第一次出现日期 yyyy-MM-dd | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `ydt_if_active` | int | 当前分区是否活跃 1 :活跃 0:不活跃 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_app_version` | string | 首次出现版本（20220520以后新设备有效） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_app_version` | string | 最后出现版本（20220520以后新设备有效） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `biz_type` | int | 业务线：7-高途系，29-途途系 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_user_type` | int | 是否纯新用户 (1 是，0 否) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_tid` | string | 用户首次出现时的设备tid | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `dt_first_active_time` | string | 当日首次活跃时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

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
