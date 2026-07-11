# temp_table.shenbaoxin_channel_group

## 1. 中文名称

渠道分组映射表（申保鑫）

## 2. 表用途

用于 H业务线二级部门转化看板，将看板 SQL 派生出的 `channel_map` 与渠道分组口径关联。

当前从以下 SQL 中确认该表被使用：
- `resources/raw_sql/h_biz_line_department_conversion.sql`（二级部门转化看板，输出 `channel_group as channel_1`）

2026-06-05 最新 `resources/raw_sql/market_consultant_lead_conversion_attendance.sql` 已替换为到课衰减版本，不再 join 本表。

真实维护来源、完整字段清单和唯一性待人工确认。

## 3. 数据粒度

- 渠道映射粒度，待确认

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| 无 | - | 稳定临时表，SQL 中未体现 dt/hour 分区 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| channel | string（待确认） | '<渠道名称>' | 建议 | 渠道映射 key；临时表无分区时建议限制渠道范围或与主查询聚合结果关联后使用 |

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| channel | string（待确认） | 渠道名称，和主查询派生字段 `channel_map` 关联 | 渠道分组映射 join key | 是 |
| channel_group | string（待确认） | 渠道分组，字段名根据历史同类表推测，当前 SQL 未输出 | 渠道大类展示/聚合 | 待确认 |

## 8. 常用过滤条件

```sql
where channel = '<渠道名称>'
```

## 9. 常用 join key

| 左表 | 左字段 | 右表 | 右字段 | 说明 |
|---|---|---|---|---|
| H业务线二级部门转化聚合 CTE | channel_map | temp_table.shenbaoxin_channel_group | channel | 将派生渠道映射到渠道分组 |

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.shenbaoxin_channel_group t
limit 20;
```

### 按渠道抽样

```sql
select *
from temp_table.shenbaoxin_channel_group t
where t.channel = '<渠道名称>'
limit 20;
```

### 渠道重复检查

```sql
select
    t.channel,
    count(*) as cnt
from temp_table.shenbaoxin_channel_group t
group by t.channel
having count(*) > 1
limit 50;
```

### 与看板渠道映射关联

```sql
select
    b.channel_map,
    g.channel_group
from base_channel b
left join temp_table.shenbaoxin_channel_group g
  on g.channel = b.channel_map
limit 100;
```

## 11. 注意事项

- 该表来自 SQL 使用字段推断，尚未通过源表或平台结构接口确认。
- 仅确认 `channel` 在 SQL 中作为 join key 出现。
- `channel_group` 为同类表口径推断字段，使用前必须通过平台 `desc temp_table.shenbaoxin_channel_group` 或表格源文件确认。
- 临时表无分区，直接探索必须加 `limit`。
- 与看板聚合结果关联前，应确认 `channel` 是否唯一；不唯一会放大看板行数。
