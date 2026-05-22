# service_dw.dws_service_user_learn_detail_hf

## 1. 中文名称

用户学习明细小时表

## 2. 表用途

在青橙过程数据 SQL 中提供上课明细，结合 `temp_table.dingxi01_qing_daoke` 计算首节到课和首节有效到课。

## 3. 数据粒度

待人工确认。当前 SQL 按 `user_number + begin_time` 与青橙线索匹配。

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
| `course_first_level_department_name` | `'H业务线'` | 课程一级部门 |
| `course_second_level_department_name` | `('精品班学部','市场部','青橙项目部')` | 课程二级部门 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `user_number` | 待人工确认 | 用户编号 | join `data.user_id` |
| `begin_time` | 待人工确认 | 开课时间 | join 首节课临时表 |
| `is_need_attend` | 待人工确认 | 是否应到 | SQL 过滤 `= 1` |
| `live_learn_duration` | 待人工确认 | 直播学习时长 | 大于 0 计首节到课 |
| `is_valid_live_learn` | 待人工确认 | 是否有效直播学习 | `'1'` 计有效到课 |
| `course_first_level_department_name` | 待人工确认 | 课程一级部门 | 范围限定 |
| `course_second_level_department_name` | 待人工确认 | 课程二级部门 | 范围限定 |

## 8. 常用过滤条件

```sql
where dt = date_format(now() - interval '2' hour, '%Y%m%d')
  and hour = date_format(now() - interval '2' hour, '%H')
  and course_first_level_department_name = 'H业务线'
  and course_second_level_department_name in ('精品班学部','市场部','青橙项目部')
  and is_need_attend = 1
```

## 9. 常用 join key

- `user_number`
- `begin_time`

## 10. 常用 SQL 片段

```sql
case
    when day_of_week(cast(begin_time as timestamp)) = 1
    then concat(date_format(date_add('day', -3, date_trunc('week', cast(begin_time as timestamp))), '%Y%m%d'), '期')
    else concat(date_format(date_add('day', 4, date_trunc('week', cast(begin_time as timestamp))), '%Y%m%d'), '期')
end as qici
```

## 11. 注意事项

- 上述片段来自历史 SQL，后续生成新 SQL 时应把三参数 `date_add` 改成 `interval` 写法。

