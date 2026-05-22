# service_dw.dm_crm_lead_stats_detail_hf

## 1. 中文名称

线索统计明细小时表

## 2. 表用途

在青橙过程数据 SQL 中补充首次外呼接通时间，并计算从分配到首次接通的小时差。

## 3. 数据粒度

待人工确认。当前 SQL 按 `lead_id` join 到线索主表。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | 待人工确认 | 日期分区 |
| `hour` | 待人工确认 | 小时分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `mapping_first_level_department_name` | `'H业务线'` | 映射一级部门 |
| `mapping_second_level_department_name` | `('精品班学部','菁英班学部','市场部','本地化大班学部','青橙项目部')` | 映射二级部门 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_id` | 待人工确认 | 线索 ID | join 主表 |
| `section_assign_time` | 待人工确认 | 截面分配时间 | 计算首次接通时间差 |
| `section_assign_first_call_time` | 待人工确认 | 截面首次外呼时间 | 当前 SQL 取出但未直接使用 |
| `section_assign_first_call_connected_time` | 待人工确认 | 截面首次外呼接通时间 | 计算首次接通时间差 |
| `mapping_first_level_department_name` | 待人工确认 | 映射一级部门 | 范围限定 |
| `mapping_second_level_department_name` | 待人工确认 | 映射二级部门 | 范围限定 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '2' hour, 'HH')
  and mapping_first_level_department_name = 'H业务线'
  and mapping_second_level_department_name in ('精品班学部','菁英班学部','市场部','本地化大班学部','青橙项目部')
```

## 9. 常用 join key

- `lead_id`

## 10. 常用 SQL 片段

```sql
date_diff(
    'hour',
    cast(section_assign_time as timestamp),
    cast(section_assign_first_call_connected_time as timestamp)
) as first_call_connected_time_diff_hour
```

## 11. 注意事项

- 映射二级部门包含多个学部和市场部，是否必须包含这些部门才能支撑青橙线索待确认。

