# temp_table.shenbaoxin_channel_group

## 1. 临时表用途

将市场渠道名称（`channel`）映射到渠道大类（`channel_group`），用于青橙转化宽表-市场渠道 SQL 的最终 SELECT。

SQL 中的使用方式：
```sql
left join temp_table.shenbaoxin_channel_group channel_grp
  on channel_grp.channel = zz.channel_map
```
取 `channel_grp.channel_group as channel_1`。

## 2. 来源和刷新方式

| 项目 | 内容 |
|---|---|
| 创建来源 | 待人工确认。表名含 `shenbaoxin`，可能为个人创建的中台渠道分组映射表 |
| 刷新方式 | 待人工确认 |
| 刷新频率 | 待人工确认 |
| 有效期 | 待人工确认。渠道分组变化时需同步更新 |

## 3. 数据粒度

待人工确认。推测为 `channel` 到 `channel_group` 的一对一或一对多映射。若一对多，left join 会导致数据行数放大。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `channel` | 待人工确认 | 市场渠道名称 | join key，对应 SQL 中的 `channel_map` 值 |
| `channel_group` | 待人工确认 | 渠道大类/渠道分组 | 输出为 `channel_1` |

仅从 SQL 使用推断这两个字段，完整字段清单待确认。

## 5. 适用看板

- `qingcheng_conversion_wide_table_market_channel_20260611`

## 6. join key

- `channel`：对应渠道宽表中的 `channel_map` 字段值

## 7. 不可复用边界

- 本表为中台市场渠道分组体系专用，**不得**用于青橙过程数据 raw 或青橙转化 raw 的渠道归类（两者渠道体系完全不同）。
- 若其他青橙看板需要渠道大类映射，需先确认渠道体系与本表是否一致。
- 表名含 `shenbaoxin` 表明可能为个人维度创建，是否稳定维护待确认。

## 8. 待确认事项

- 临时表创建者（推测 `shenbaoxin`）和维护责任人待确认。
- `channel` 字段的全量枚举值及与 `channel_map` CASE WHEN 的覆盖对应关系待确认。
- `channel_group` 的全量枚举值及归类逻辑待确认。
- 刷新频率和有效期：渠道分组变更时是否需要同步更新本表。
- 是否青橙项目部专用，或中台多部门共用。
- left join 时若 `channel` 不唯一（一对多映射），数据会被放大，需确认唯一性。
