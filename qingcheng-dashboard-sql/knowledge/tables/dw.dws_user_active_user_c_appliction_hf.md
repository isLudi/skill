# dw.dws_user_active_user_c_appliction_hf

## 1. 中文名称

用户应用活跃小时表

## 2. 表用途

在青橙过程数据 SQL 中判断用户近 2 小时是否有 APP/PC 登录。

## 3. 数据粒度

待人工确认。当前 SQL 按 `user_number` 去重。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | string | 日期分区 |
| `hour` | string | 小时分区 |
## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| 无青橙部门字段 | 通过青橙线索主表 join 限定 | 单独查询时不能代表青橙范围 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `user_number` | string | 用户编号 | join `data.user_id` |
| `application_name` | string | 应用名称 | `PC客户端`,`APP`,`PC` 计登录 |
| `product_name` | string | 产品名称 | 过滤 `高途`,`规划精品` |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `dt_first_active_time` | string | 当日首次活跃时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `tid` | string | 当日首次活跃设备编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_reatin_1d` | bigint | 是否次日留存 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `dt_last_active_time` | string | 当日末次活跃时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_learn_plan_show` | bigint | 是否有规划师曝光 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_course_details_page_show` | bigint | 是否有课程详情页曝光 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '2' hour, 'HH')
  and product_name in ('高途','规划精品')
```

## 9. 常用 join key

- `user_number = data.user_id`

## 10. 常用 SQL 片段

```sql
case when application_name in ('PC客户端','APP','PC') then 1 else 0 end as is_app_denglu_h
```

## 11. 注意事项

- 与天级表字段名不同：本表使用 `application_name`。
