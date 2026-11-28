# temp_table.lvshuai01_plan_id

## 1. 中文名称

当前市场分配计划组ID表。

## 2. 表用途

当前分配SQL使用的计划组ID登记，不因渠道CASE更新改动计划或分配目标。 2026-11-28从实时生产模型2307读取的完整SQL确认当前表名。

## 3. 数据粒度

登记或关联键为`year + qici + group_id`；这不保证当前数据唯一。当前重复、空值、历史覆盖与具体Join粒度须按目标验证。

## 4. 查询引擎

Presto，当前生产查询已实际执行。其他引擎按各目标运行证据确认。

## 5. 分区字段

当前消费者未使用本表的dt/hour分区条件；完整物理分区结构未确认，不能仅据SQL推断无分区。

## 6. 强制范围限定字段

保留各模型已有期次、渠道、年级或员工范围及主查询业务范围。尚未确认通用部门限定或新的联接合同，不自动放宽范围或复用其他部门定义。

## 7. 字段清单

以下为治理登记的上传列，不是重新生成的完整DDL；字段类型见下方平台结构核验。

| 字段名 | 类型 | 字段描述 |
|---|---|---|
| year | string | 沿用本域治理登记及目标SQL的实际用法 |
| qici | string | 沿用本域治理登记及目标SQL的实际用法 |
| group_id | string | 沿用本域治理登记及目标SQL的实际用法 |
| group_name | string | 沿用本域治理登记及目标SQL的实际用法 |

## 8. 常用过滤条件

`qici = '<MMDD期>'`仅为占位示意，须以目标已审定范围替换；不能直接进入生产执行。

## 9. 常用 join key

`year + qici + group_id`仅记录现有用法。对映射表或目标表Join前检查键唯一性，禁止未经验证的明细放大或跨期关联。

## 10. 常用 SQL 片段

```sql
SELECT year, qici, group_id, group_name
FROM temp_table.lvshuai01_plan_id
WHERE year = '<年份>' AND qici = '<MMDD期>'
```

该片段不提供独立执行授权，也不确认任何新业务指标。

## 11. 注意事项

[治理登记](../../../sync-qingcheng-market-temp-tables/references/workflow_registry.json)中的`market_plan_id`确认本域平台表名、上传列与登记键。 本轮只维护当前物理绑定，不上传、重命名或改写临时表数据，不推断当前行数、最新期次或质量状态；这些信息需新回执或受治理查询。confirmed及automatic_compile状态不因本条记录自动提升。

## 补充业务语义与风险

`qici` 历史登记为 `MMDD期`，由 `year` 补足年份；`group_id` 可跨期复用。跨年关联应核验 `year + qici + group_id`，不可仅用 `group_id` 推断唯一；`year` 和 `group_id` 的平台解析类型是 `string`。

## 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`year`、`qici`、`group_id`、`group_name`。
