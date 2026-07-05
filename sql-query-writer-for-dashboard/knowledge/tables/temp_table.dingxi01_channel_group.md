# temp_table.dingxi01_channel_group

## 1. 中文名称

渠道分组映射表

## 2. 表用途

稳定临时表，用于将看板派生出的 `channel_map` 映射到渠道组 `channel_group`。

字段来源：`resources/raw_sql/data_center_market_2253_20260705.sql`。

## 3. 数据粒度

渠道映射粒度，待确认。理论上一行对应一个 `channel`。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| 无 | - | 稳定临时表无固定分区；查询时必须限定渠道或通过主查询范围控制 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| channel | string，待确认 | '<渠道名称>' | 是 | 渠道名称，与 `channel_map` 关联 |

说明：
- 对所有 department_name 相关字段，标记为需要范围限定；
- 不知道默认值时，推荐取值写 `'<待填写>'`。


## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| channel | string，待确认 | 渠道名称 | join `channel_map` | 是 |
| channel_group | string，待确认 | 渠道组 | 看板展示维度 | 是 |

## 8. 常用过滤条件

- `t.channel = '<渠道名称>'`

## 9. 常用 join key

- `channel`：与 `channel_map` 关联。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.dingxi01_channel_group t
where t.channel = '<渠道名称>'
limit 20;
```

### 渠道组分布

```sql
select
    t.channel_group,
    count(*) as cnt
from temp_table.dingxi01_channel_group t
group by t.channel_group
order by cnt desc
limit 100;
```

## 11. 注意事项

- 表结构根据历史 SQL 推断，仅确认字段被使用，真实类型和唯一性需人工确认。
- 如果 `channel` 不唯一，关联看板会放大行数。

### 流量画像 SQL 使用备注

- `data_center_market_2683_20260705.sql` 最终层通过 `channel_grp.channel = zz.channel_map` 关联该表，但当前结果没有输出 `channel_grp` 字段。
- 如后续需要展示 `channel_group`，必须先检查 `channel` 唯一性，避免按渠道放大结果。
