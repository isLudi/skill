# temp_table.dingxi01_cost

## 1. 中文名称

渠道成本目标表

## 2. 表用途

稳定临时表，用于按渠道、年级和期次补充单例子成本 `cost` 与目标 `goal`。

字段来源：`resources/raw_sql/market_consultant_conversion.sql`。

## 3. 数据粒度

渠道-年级-期次粒度，待确认。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| 无 | - | 稳定临时表无固定分区；查询时必须限定期次、渠道或年级 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| qici | string，待确认 | '<期次>' | 是 | 期次 |
| channel | string，待确认 | '<渠道名称>' | 是 | 渠道名称，与 `channel_map` 关联 |
| grade | string，待确认 | '<年级>' | 是 | 年级，与 `grade_1` 关联 |

说明：
- 对所有 department_name 相关字段，标记为需要范围限定；
- 不知道默认值时，推荐取值写 `'<待填写>'`。


## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| channel | string，待确认 | 渠道名称 | join `channel_map` | 是 |
| grade | string，待确认 | 年级 | join `grade_1` | 是 |
| qici | string，待确认 | 期次 | join `period_name` | 是 |
| cost | double，待确认 | 单例子成本 | 看板指标 `cb_cb` | 是 |
| goal | double，待确认 | 单例子目标 | 看板指标 `gl_gl` | 是 |

## 8. 常用过滤条件

- `t.qici = '<期次>'`
- `t.channel = '<渠道名称>'`
- `t.grade = '<年级>'`

## 9. 常用 join key

- `channel + grade + qici`：与 `channel_map + grade_1 + period_name` 关联。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.dingxi01_cost t
where t.qici = '<期次>'
  and t.channel = '<渠道名称>'
  and t.grade = '<年级>'
limit 20;
```

### 成本目标分布

```sql
select
    t.qici,
    t.channel,
    t.grade,
    max(t.cost) as cost,
    max(t.goal) as goal
from temp_table.dingxi01_cost t
where t.qici = '<期次>'
group by
    t.qici,
    t.channel,
    t.grade
limit 200;
```

## 11. 注意事项

- 字段和口径根据历史 SQL 推断，真实类型、单位和维护来源需人工确认。
- `channel + grade + qici` 应唯一；如果不唯一，关联看板会放大行数。
- **`grade = '0'` 为全年级通配**：当 grade 取值为 `'0'` 时，表示该渠道的 `cost`/`goal` 适用于所有年级。生成 JOIN SQL 时必须加 `or ct.grade = '0'`，否则只匹配到有具体年级值的行（绝大多数渠道 GMV 目标将全为 0）。已验证：同一 `(channel, qici)` 不会同时存在 `grade='0'` 和具体年级值，不会产生行膨胀。

### 流量画像 SQL 使用备注

- `traffic_profile.sql` 使用 `ct.channel = channel_map`、`ct.grade = grade_1`、`ct.qici = period_name` 补充 `cb_cb = cost` 和 `gl_gl = goal`。
- 成本目标在结果层用 `coalesce(..., 0)`，无法区分真实 0 和未维护缺失，复用时可额外输出命中标记。
