# dw.dws_user_active_user_c_appliction_hf

## 1. 中文名称

c端用户活跃表应用粒度_当日小时全量

## 2. 表用途

C 端用户在应用粒度的当日小时活跃数据。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

## 3. 数据粒度

用户-应用-小时粒度，待确认

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |
| hour | string | 小时级分区 HH | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 | 来源 |
|---|---|---|---|---|---|
| 无 | - | - | 否 | 未识别 department_name 字段；若查询涉及业务范围仍需人工限定 | 字段目录 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| hour | string | 小时级分区 HH | 分区过滤 | 是 |
| user_number | string | 用户编号 | 主键/关联键 | 是 |
| product_name | string | 产品线 | 待按需求确认 | 否 |
| application_name | string | 应用 | 待按需求确认 | 否 |
| dt_first_active_time | string | 当日首次活跃时间 | 时间分析 | 否 |
| tid | string | 当日首次活跃设备编号 | 待按需求确认 | 否 |
| is_reatin_1d | bigint | 是否次日留存 | 待按需求确认 | 否 |
| dt_last_active_time | string | 当日末次活跃时间 | 时间分析 | 否 |
| is_learn_plan_show | bigint | 是否有规划师曝光 | 待按需求确认 | 否 |
| is_course_details_page_show | bigint | 是否有课程详情页曝光 | 待按需求确认 | 否 |

## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`

## 9. 常用 join key

- `user_number`：用户关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.user_number,
    t.product_name,
    t.application_name,
    t.dt_first_active_time,
    t.tid,
    t.is_reatin_1d,
    t.dt_last_active_time,
    t.is_learn_plan_show,
    t.is_course_details_page_show
from dw.dws_user_active_user_c_appliction_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 11。
- 所属项目：dw；owner：刘江04。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 11。
- 所属项目：dw；owner：刘江04。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 11。
- 所属项目：dw；owner：刘江04。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 分区限制：查询分区表必须带分区条件。
- department_name 范围限定：涉及部门字段必须过滤；未给取值时使用占位符。
- 字段类型注意事项：PDF 图片 OCR 低置信度字段必须先人工确认。
- 常见报错：字段不存在、库名前缀不正确、小时表遗漏 hour、group by 不完整。
- 待人工确认问题：
- PDF 第 21 页字段表为图片型，需人工校验。
