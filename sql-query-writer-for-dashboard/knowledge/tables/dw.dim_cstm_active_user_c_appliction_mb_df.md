# dw.dim_cstm_active_user_c_appliction_mb_df

## 1. 中文名称

c端用户全量表应用粒度

## 2. 表用途

C 端用户全量应用粒度维表。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

## 3. 数据粒度

用户-应用粒度，待确认

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 日期 YYYYDDMM | 是 |
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
| dt | string | 日期 YYYYDDMM | 分区过滤 | 是 |
| user_number | string | 用户number | 主键/关联键 | 是 |
| product_name | string | 产品线：高途、规划精品（高中）、公考、途途 | 待按需求确认 | 否 |
| appliction_name | string | 应用 | 待按需求确认 | 否 |
| event_time | string | 用户在各应用第一次出现的时间 yyyy-MM-dd hh:mm:ss | 时间分析 | 否 |
| last_event_time | string | 用户在各应用最后一次出现的时间 yyyy-MM-dd hh:mm:ss | 时间分析 | 否 |
| first_app_channel | string | 设备首次出现渠道 | 常用维度 | 是 |
| last_app_channel | string | 最后一次渠道 | 常用维度 | 是 |
| first_date | string | 用户在各应用第一次出现日期 yyyy-MM-dd | 时间分析 | 否 |
| ydt_if_active | int | 当前分区是否活跃 1 :活跃 0:不活跃 | 待按需求确认 | 否 |
| first_app_version | string | 首次出现版本（20220520以后新设备有效） | 待按需求确认 | 否 |
| last_app_version | string | 最后出现版本（20220520以后新设备有效） | 待按需求确认 | 否 |
| biz_type | int | 业务线：7-高途系，29-途途系 | 待按需求确认 | 否 |
| pre_user_type | int | 是否纯新用户 (1 是，0 否) | 待按需求确认 | 否 |
| first_tid | string | 用户首次出现时的设备tid | 待按需求确认 | 否 |
| dt_first_active_time | string | 当日首次活跃时间 | 时间分析 | 否 |
## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`

## 9. 常用 join key

- `user_number`：用户关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.user_number,
    t.product_name,
    t.appliction_name,
    t.event_time,
    t.last_event_time,
    t.first_app_channel,
    t.last_app_channel,
    t.first_date,
    t.ydt_if_active,
    t.first_app_version,
    t.last_app_version,
    t.biz_type,
    t.pre_user_type,
    t.first_tid,
    t.dt_first_active_time
from dw.dim_cstm_active_user_c_appliction_mb_df t
where t.dt = 'YYYYMMDD'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 16。
- 所属项目：dw；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 16。
- 所属项目：dw；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 16。
- 所属项目：dw；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 分区限制：查询分区表必须带分区条件。
- department_name 范围限定：涉及部门字段必须过滤；未给取值时使用占位符。
- 字段类型注意事项：PDF 图片 OCR 低置信度字段必须先人工确认。
- 常见报错：字段不存在、库名前缀不正确、小时表遗漏 hour、group by 不完整。
- 待人工确认问题：
- PDF 第 22 页字段表为图片型，需人工校验。

### 流量画像 SQL 使用备注

- `data_center_market_2683.sql` 使用该表两次：`denglu_app` 取用户最新应用登录记录并判断最近 7 日 `is_app_denglu`，`app_ph` 限定 `appliction_name = 'APP'` 取最新 `last_app_channel`。
- 登录时间使用 `try(date_parse(last_event_time, '%Y-%m-%d %H:%i:%s:%f'))` 解析，并按 `user_number` 做 `row_number()` 取最新记录。
- `denglu_app` 分区为 `dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')`，并限定 `product_name in ('高途','规划精品')`；`app_ph` 只限定 `appliction_name = 'APP'`，未限定产品线。
- `is_app_denglu` 判断应用名包含 `PC客户端`、`APP`、`PC`，名称枚举需结合线上数据确认。
