# service_dw.dws_service_user_learn_detail_hf

## 1. 中文名称

小时级行课数据全量

## 2. 表用途

小时级用户行课数据全量，用于到课、首节到课、行课时长等指标。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

## 3. 数据粒度

用户-课程-小时粒度，待确认

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级分区 yyyyMMdd | 是 |
| hour | string | 小时级分区 | 是 |
## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 | 来源 |
|---|---|---|---|---|---|
| course_first_level_department_name | string | 'H业务线' (8次) | 是 | 课程一级部门名称 | row_permissions 全局历史取值 |
| course_second_level_department_name | string | '精品班学部' (1次) | 是 | 课程二级部门名称 | row_permissions 全局历史取值 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| hour | string | 小时级分区 | 分区过滤 | 是 |
| user_number | bigint | 用户编号 | 主键/关联键 | 是 |
| clazz_lesson_number | bigint | 班级课节编号 | 待按需求确认 | 否 |
| clazz_number | bigint | 班级编号 | 待按需求确认 | 否 |
| is_need_attend | int | 是否应出勤 1-是｜0-否 | 待按需求确认 | 否 |
| is_black | int | 是否黑名单 1-是｜0-否 | 待按需求确认 | 否 |
| begin_time | string | 课节开始时间 | 时间分析 | 否 |
| end_time | string | 课节结束时间 | 时间分析 | 否 |
| lesson_index | int | 课节序号 | 待按需求确认 | 否 |
| original_subclazz_number | bigint | 原辅导班编号，直播结束时用户所在辅导班 | 待按需求确认 | 否 |
| lesson_live_length | bigint | 课节直播时长（s），分课段课程取核心课段直播时长 | 待按需求确认 | 否 |
| lesson_video_length | bigint | 课节视频时长（s），取课节最新关联视频的视频长度 | 待按需求确认 | 否 |
| lesson_standard_length | bigint | 课节标准时长（s），课节结束时间戳与课节开始时间戳差值 | 待按需求确认 | 否 |
| lesson_length | bigint | 课节时长（s），对于非伴学课，取课节视频时长和课节标准时长最小值，对于伴学课，取课节直播时长和课节标准时长最小值 | 待按需求确认 | 否 |
| learn_effective_ratio | bigint | 有效听课系数 | 指标聚合 | 是 |
| live_learn_duration | bigint | 用户直播听课时长（单位：s） | 指标聚合 | 是 |
| is_valid_live_learn | bigint | 是否有效直播听课，eg：0-否｜1-是 | 待按需求确认 | 否 |
| video_learn_duration | bigint | 用户回放听课时长（单位：s） | 指标聚合 | 是 |
| learn_duration | bigint | 用户听课时长（直播+回放去重） | 指标聚合 | 是 |
| is_valid_learn | bigint | 是否有效听课，eg：0-否｜1-是 | 待按需求确认 | 否 |
| lesson_index_add | int | 课节序号（包含补充课节） | 待按需求确认 | 否 |
| lesson_name | string | 课节名称 | 待按需求确认 | 否 |
| video_learn_times | bigint | 回放/视频听课次数 | 时间分析 | 否 |
| learn_interval | string | 用户听课区间（直播+回放去重） | 待按需求确认 | 否 |
| live_learn_interval | string | 用户直播听课区间 | 待按需求确认 | 否 |
| is_combine_valid_learn | bigint | 仅限于班级课节，直播有效听课 或 用户合并听课时长与课节时长的比值大于等于听课有效系数（learn_combine_duration / lesson_length >= learn_effective_ratio） | 待按需求确认 | 否 |
| course_first_level_department_code | bigint | 课程一级部门编码 | 常用维度 | 是 |
| course_first_level_department_name | string | 课程一级部门名称 | 权限/业务范围限定 | 是 |
| course_second_level_department_code | string | 课程二级部门编码 | 常用维度 | 是 |
| course_second_level_department_name | string | 课程二级部门名称 | 权限/业务范围限定 | 是 |
| is_combine_need_attend | int | 是否伴学课合并后应出勤 1-是｜0-否 | 待按需求确认 | 否 |
| learn_combine_duration | bigint | 用户伴学课合并听课时长（直播+回放去重） | 指标聚合 | 是 |
## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`
- `t.course_first_level_department_name = 'H业务线'`
- `t.course_second_level_department_name = '精品班学部'`

## 9. 常用 join key

- `user_number`：用户关联
- `clazz_number`：班级关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.user_number,
    t.course_second_level_department_name,
    t.course_first_level_department_name,
    t.clazz_lesson_number,
    t.clazz_number,
    t.is_need_attend,
    t.is_black,
    t.begin_time,
    t.end_time,
    t.lesson_index,
    t.original_subclazz_number,
    t.lesson_live_length,
    t.lesson_video_length,
    t.lesson_standard_length
from service_dw.dws_service_user_learn_detail_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.course_first_level_department_name = 'H业务线'
  and t.course_second_level_department_name = '精品班学部'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 33。
- 所属项目：服务域；owner：翟傲森。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 33。
- 所属项目：服务域；owner：翟傲森。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 分区限制：查询分区表必须带分区条件。
- department_name 范围限定：涉及部门字段必须过滤；未给取值时使用占位符。
- 物理字段来源：当前字段、类型和说明以天工数据地图同步结果为准；业务含义仍需结合市场顾问使用场景确认。
- 常见报错：字段不存在、库名前缀不正确、小时表遗漏 hour、group by 不完整。

### 流量画像 SQL 使用备注

- `data_center_market_2683.sql` 使用该表补充用户行课记录，通过 `user_number` 和派生 `qici` 与主线索 `user_id + period_name` 对齐。
- 行课范围限定为 `course_first_level_department_name = 'H业务线'`，`course_second_level_department_name in ('精品班学部','市场部','青橙项目部')`，且 `is_need_attend = 1`。
- `qici` 对 2026-02-03 至 2026-03-02 的若干春节特殊周硬编码，其余日期按周逻辑推导；生成新 SQL 时应优先复用完整期次 CASE。
- 到课字段：普通到课使用 `live_learn_duration > 0`，有效到课使用 `is_valid_live_learn = '1'`，字段类型待确认。
