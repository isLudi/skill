# gaotu_hl.ods_mkt_h_channel_group_df

## 1. 中文名称

H业务线渠道分类表

## 2. 表用途

来自天工数据地图的表说明：维护 CRM 渠道名到渠道大类的分类关系，并记录适用学部。

## 3. 数据粒度

待 SQL 验证；当前最新快照验证为 `department_name + channel` 唯一，`department_name='all'` 下每个 `channel` 一行。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 同步日期 yyyyMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| department_name | string | all | 是 | 当前线上快照仅验证到 `all`；使用前应按快照确认 |

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|

### 7.1 数据地图字段补充（2026-08-13）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| channel | string | 渠道（对齐 channel_map，来源飞书列 channel_map） | 数据地图补充 | 否 |
| channel_group | string | 渠道大类，如 KOC/ip/信息流/本地化图书 | 数据地图补充 | 否 |
| department_name | string | 适用学部，当前统一 all | 范围限定 | 是 |

## 8. 常用过滤条件

- 查询必须限定 `dt` 分区。
- 当前已验证渠道分类关联使用 `department_name = 'all'`。

## 9. 常用 join key

- 与全链路宽表的逻辑关联键：`derived_channel_map = channel`，其中 `derived_channel_map` 必须先由市场顾问 0808 渠道 CASE 从宽表原始渠道字段派生。
- 不得直接用宽表 `channel_name_1`、`channel_name_2`、`channel_name_3` 代替 `derived_channel_map`。

## 10. 常用 SQL 片段

```sql
with channel_group as (
    select channel, min(channel_group) as channel_group
    from gaotu_hl.ods_mkt_h_channel_group_df
    where dt = 'YYYYMMDD'
      and department_name = 'all'
    group by channel
)
select ...
from channel_derived src
left join channel_group cg
  on cg.channel = src.channel_map;
```

## 11. 注意事项

- 字段、类型和分区信息来源于天工数据地图；渠道组唯一性来自已执行的 SQL 探针。
- `channel_map` 不是全链路宽表的物理字段，而是由 `resources/raw_sql/market_channel_case_when_0808.sql` 派生的逻辑字段。
- 该表必须先按 `dt` 和 `department_name='all'` 限定，并按 `channel` 预聚合/去重后再关联，避免配置表异常重复时放大宽表。
- 完整 0808 CASE 的单体展开曾触发平台 `Compiler failed`；随后用保持 175 条分支顺序的五段式 CASE 完成 bounded 验证：50,000 个宽表物理字段去重组合中，59 个派生渠道值有 56 个命中渠道组表，49,765 个组合行命中，渠道组侧最大匹配行数为 1。该结果是覆盖探针，不替代生产 SQL 的完整分支语义校验。
- 覆盖探针 Query ID：`1545605539`；单体 CASE 编译失败 Query ID：`1545581106`。后者是平台编译器错误，不是业务数据结论。
