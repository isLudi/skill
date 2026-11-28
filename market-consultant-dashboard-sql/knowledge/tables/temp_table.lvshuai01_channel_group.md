# temp_table.lvshuai01_channel_group

字段类型合并说明（2026-11-28）：类型栏采用本地已记录的平台 SQL 解析输出；历史 Excel 推断不作为当前类型结论。查询输出结构不等同完整 DDL，也不证明当前数据覆盖、唯一性或生产消费者已切换。

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 中文名称

渠道分组映射表

## 2. 表用途

稳定临时表，用于将看板派生出的 `channel_map` 映射到渠道组 `channel_group`。

字段来源：`resources/raw_sql/data_center_market_2253.sql`。

## 3. 数据粒度

渠道映射粒度，待确认。理论上一行对应一个 `channel`。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
| --- | --- | --- | --- |
| 无 | - | 稳定临时表无固定分区；查询时必须限定渠道或通过主查询范围控制 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
| --- | --- | --- | --- | --- |
| channel | string | '<渠道名称>' | 是 | 渠道名称，与 `channel_map` 关联 |

说明：
- 对所有 department_name 相关字段，标记为需要范围限定；
- 不知道默认值时，推荐取值写 `'<待填写>'`。


## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
| --- | --- | --- | --- | --- |
| channel | string | 渠道名称 | join `channel_map` | 是 |
| channel_group | string | 渠道组 | 看板展示维度 | 是 |

## 8. 常用过滤条件

- `t.channel = '<渠道名称>'`

## 9. 常用 join key

- `channel`：与 `channel_map` 关联。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.lvshuai01_channel_group t
where t.channel = '<渠道名称>'
limit 20;
```

### 渠道组分布

```sql
select
    t.channel_group,
    count(*) as cnt
from temp_table.lvshuai01_channel_group t
group by t.channel_group
order by cnt desc
limit 100;
```

## 11. 注意事项

- 表结构根据历史 SQL 推断，仅确认字段被使用，真实类型和唯一性需人工确认。
- 如果 `channel` 不唯一，关联看板会放大行数。

### 流量画像 SQL 使用备注

- `data_center_market_2683.sql` 最终层通过 `channel_grp.channel = zz.channel_map` 关联该表，但当前结果没有输出 `channel_grp` 字段。
- 如后续需要展示 `channel_group`，必须先检查 `channel` 唯一性，避免按渠道放大结果。

## 本地登记与平台核验补充（2026-11-28）

历史类型记录（仅说明原文推断来源）：`channel` 原记为 string，待确认；`channel_group` 原记为 string，待确认。当前查询输出类型采用上文平台解析记录。

### 1. 中文名称

当前渠道分组关联表。

### 2. 表用途

当前生产SQL按渠道键补充渠道组，未重新定义各组名单。 2026-11-28从实时生产模型2253、2345、2461、2623、2683读取的完整SQL确认当前表名。

### 3. 数据粒度

登记或关联键为`channel`；这不保证当前数据唯一。当前重复、空值、历史覆盖与具体Join粒度须按目标验证。

### 4. 查询引擎

Presto，当前生产查询已实际执行。其他引擎按各目标运行证据确认。

### 5. 分区字段

当前消费者未使用本表的dt/hour分区条件；完整物理分区结构未确认，不能仅据SQL推断无分区。

### 6. 强制范围限定字段

保留各模型已有期次、渠道、年级或员工范围及主查询业务范围。尚未确认通用部门限定或新的联接合同，不自动放宽范围或复用其他部门定义。

### 7. 字段清单

以下为当前SQL实际引用的列名子集，不是重新生成的完整DDL；字段类型见下方平台结构核验。

### 8. 常用过滤条件

`channel = '<已审定值>'`仅为占位示意，须以目标已审定范围替换；不能直接进入生产执行。

### 9. 常用 join key

`channel`仅记录现有用法。对映射表或目标表Join前检查键唯一性，禁止未经验证的明细放大或跨期关联。

### 10. 常用 SQL 片段

```sql
SELECT channel, channel_group
FROM temp_table.lvshuai01_channel_group
WHERE channel = '<已审定值>'
```

该片段不提供独立执行授权，也不确认任何新业务指标。

### 11. 注意事项

当前仅根据本域生产SQL的实际引用登记物理绑定；上游工作簿、完整DDL、业务键唯一性与完整适用范围仍待确认。 本轮只维护当前物理绑定，不上传、重命名或改写临时表数据，不推断当前行数、最新期次或质量状态；这些信息需新回执或受治理查询。confirmed及automatic_compile状态不因本条记录自动提升。

### 补充业务语义与风险

`channel` 对应看板派生 `channel_map`，`channel_group` 为分组展示；同一渠道若多行会放大结果，须先验证唯一性。

### 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`channel`、`channel_group`。
