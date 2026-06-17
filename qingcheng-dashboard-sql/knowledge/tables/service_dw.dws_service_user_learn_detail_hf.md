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
| `dt` | string | 日期分区 |
| `hour` | string | 小时分区 |
## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `course_first_level_department_name` | `'H业务线'` | 课程一级部门 |
| `course_second_level_department_name` | `('精品班学部','市场部','青橙项目部')` | 课程二级部门 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `user_number` | bigint | 用户编号 | join `data.user_id` |
| `begin_time` | string | 开课时间 | join 首节课临时表 |
| `is_need_attend` | int | 是否应到 | SQL 过滤 `= 1` |
| `live_learn_duration` | bigint | 直播学习时长 | 大于 0 计首节到课 |
| `is_valid_live_learn` | bigint | 是否有效直播学习 | `'1'` 计有效到课 |
| `course_first_level_department_name` | string | 课程一级部门 | 范围限定 |
| `course_second_level_department_name` | string | 课程二级部门 | 范围限定 |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `clazz_lesson_number` | bigint | 班级课节编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_number` | bigint | 班级编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_black` | int | 是否黑名单 1-是｜0-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `end_time` | string | 课节结束时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lesson_index` | int | 课节序号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `original_subclazz_number` | bigint | 原辅导班编号，直播结束时用户所在辅导班 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lesson_live_length` | bigint | 课节直播时长（s），分课段课程取核心课段直播时长 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lesson_video_length` | bigint | 课节视频时长（s），取课节最新关联视频的视频长度 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lesson_standard_length` | bigint | 课节标准时长（s），课节结束时间戳与课节开始时间戳差值 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lesson_length` | bigint | 课节时长（s），对于非伴学课，取课节视频时长和课节标准时长最小值，对于伴学课，取课节直播时长和课节标准时长最小值 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `learn_effective_ratio` | bigint | 有效听课系数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `video_learn_duration` | bigint | 用户回放听课时长（单位：s） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `learn_duration` | bigint | 用户听课时长（直播+回放去重） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_valid_learn` | bigint | 是否有效听课，eg：0-否｜1-是 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lesson_index_add` | int | 课节序号（包含补充课节） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lesson_name` | string | 课节名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `video_learn_times` | bigint | 回放/视频听课次数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `learn_interval` | string | 用户听课区间（直播+回放去重） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `live_learn_interval` | string | 用户直播听课区间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_combine_valid_learn` | bigint | 仅限于班级课节，直播有效听课 或 用户合并听课时长与课节时长的比值大于等于听课有效系数（learn_combine_duration / lesson_length >= learn_effective_ratio） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_first_level_department_code` | bigint | 课程一级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `course_second_level_department_code` | string | 课程二级部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_combine_need_attend` | int | 是否伴学课合并后应出勤 1-是｜0-否 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `learn_combine_duration` | bigint | 用户伴学课合并听课时长（直播+回放去重） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

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
