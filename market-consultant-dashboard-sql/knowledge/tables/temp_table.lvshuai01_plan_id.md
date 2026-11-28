# temp_table.lvshuai01_plan_id

字段类型合并说明（2026-11-28）：类型栏采用本地已记录的平台 SQL 解析输出；历史 Excel 推断不作为当前类型结论。查询输出结构不等同完整 DDL，也不证明当前数据覆盖、唯一性或生产消费者已切换。

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 中文名称

市场顾问分配计划组 ID 维护表

## 2. 表用途

稳定临时表，用于维护需要纳入“线索分配计划与实际有效量看板”的分配规则组 ID、期次和规则组名称。

当前表结构来自原始 Excel：

- 文件：`E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\plan_id.xlsx`
- Sheet：`Sheet1`
- 文件最后修改时间：2026-05-07 14:29:59
- 本次读取：非空数据行 51 行，字段 4 个；工作表最大行号 61，存在空行

历史 SQL `resources/raw_sql/lead_assign_plan_actual_valid_count.sql` 通过 `pl.group_id = f.group_id` 且 `pl.group_id is not null` 过滤分配规则明细。

## 3. 数据粒度

- 期次-规则组粒度：`qici + group_id` 唯一。
- `group_id` 单字段不全局唯一，当前 Excel 中 `15175` 跨多个期次重复。
- `group_name` 单字段不唯一，但 `qici + group_name` 唯一。
- 稳定临时表无 `dt`/`hour` 分区，生成 SQL 时建议用 `year`、`qici` 或与规则明细表关联后的业务范围收窄。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
| --- | --- | --- | --- |
| 无 | - | 稳定临时表，SQL 中未体现 dt/hour 分区 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
| --- | --- | --- | --- | --- |
| year | string | 2026 | 建议 | 年份字段；当前 Excel 仅有 2026 |
| qici | string | '<MMDD期>' | 建议 | 期次尾号格式，例如 `0306期`、`0508期` |
| group_id | string | '<规则组ID>' | 建议 | 分配规则组 ID；单字段可能跨期重复 |

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
| --- | --- | --- | --- | --- | --- |
| year | string | 年份 | 和 `qici` 组成完整期次范围 | 2026 | 是 |
| qici | string | 期次尾号，格式为 MMDD期，不含年份 | 期次过滤、与规则名拆出的期次片段关联 | 0306期；0508期；0515期 | 是 |
| group_id | string | 分配规则组 ID | 与 `service_dw.dim_crm_assign_rule_lead_detail_hf.group_id` 关联 | 14153；15175；15366 | 是 |
| group_name | string | 分配规则组名称 | 规则组展示、渠道/年级类别识别 | 0306期-市场-高中年级；2026年-短期班-抖音私信 | 是 |

## 8. 常用过滤条件

- `t.year = 2026`
- `t.qici = '<MMDD期>'`
- `t.group_id is not null`
- `t.group_name like '%市场%'`

## 9. 常用 join key

| 左表 | 左字段 | 右表 | 右字段 | 说明 |
|---|---|---|---|---|
| service_dw.dim_crm_assign_rule_lead_detail_hf | group_id | temp_table.lvshuai01_plan_id | group_id | 仅保留临时表维护的规则组；若输出 `qici/group_name`，必须处理 `group_id` 跨期重复 |
| 规则名派生 | `split_part(rule_name, '-', 1)` | temp_table.lvshuai01_plan_id | qici | 可用规则名期次片段与维护表期次对齐，需确认规则名格式 |

本次 Excel key 重复检查：

| join key | 非空行数 | 唯一组合数 | 重复组合数 | 涉及重复行数 | 最大重复次数 | 说明 |
|---|---:|---:|---:|---:|---:|---|
| group_id | 51 | 49 | 1 | 3 | 3 | `15175` 出现在 `0501期`、`0508期`、`0515期` |
| qici + group_id | 51 | 51 | 0 | 0 | 1 | 推荐用于需要输出期次的关联 |
| year + qici + group_id | 51 | 51 | 0 | 0 | 1 | 推荐用于跨年场景 |
| group_name | 51 | 47 | 4 | 8 | 2 | 存在跨期同名或名称复用 |
| qici + group_name | 51 | 51 | 0 | 0 | 1 | 可用于展示校验，不建议作为主 join key |

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.year,
    t.qici,
    t.group_id,
    t.group_name
from temp_table.lvshuai01_plan_id t
limit 20;
```

### 按期次查看规则组

```sql
select
    t.year,
    t.qici,
    t.group_id,
    t.group_name
from temp_table.lvshuai01_plan_id t
where t.year = 2026
  and t.qici = '<MMDD期>'
order by t.group_id;
```

### group_id 重复检查

```sql
select
    t.group_id,
    count(*) as cnt,
    array_join(array_agg(t.qici), ',') as qici_list
from temp_table.lvshuai01_plan_id t
group by t.group_id
having count(*) > 1
limit 50;
```

### 期次内 group_id 唯一性检查

```sql
select
    t.year,
    t.qici,
    t.group_id,
    count(*) as cnt
from temp_table.lvshuai01_plan_id t
group by t.year, t.qici, t.group_id
having count(*) > 1
limit 50;
```

### 与分配规则明细关联

```sql
select
    f.group_id,
    pl.year,
    pl.qici,
    pl.group_name,
    f.plan_id,
    f.rule_id,
    f.rule_name
from service_dw.dim_crm_assign_rule_lead_detail_hf f
join temp_table.lvshuai01_plan_id pl
  on pl.group_id = f.group_id
where f.dt = 'YYYYMMDD'
  and f.hour = 'HH'
  and pl.year = 2026
  and pl.qici = '<MMDD期>'
limit 100;
```

### 与规则名期次片段共同关联

```sql
select
    f.group_id,
    pl.year,
    pl.qici,
    pl.group_name,
    f.plan_id,
    f.rule_id,
    f.rule_name
from service_dw.dim_crm_assign_rule_lead_detail_hf f
join temp_table.lvshuai01_plan_id pl
  on pl.group_id = f.group_id
 and pl.qici = split_part(f.rule_name, '-', 1)
where f.dt = 'YYYYMMDD'
  and f.hour = 'HH'
limit 100;
```

## 11. 注意事项

- 表来源已确认来自 `plan_id.xlsx`，但查询平台中的物理表刷新频率、导入方式和是否完全等同 Excel 仍需人工确认。
- 临时表无分区，探索查询必须加 `limit`。
- `qici` 是 `MMDD期` 形式，不含年份；跨年分析必须同时使用 `year`。
- `group_id` 单字段不唯一，若后续 SQL 输出 `pl.qici` 或 `pl.group_name`，不能只按 `group_id` 关联，否则 `15175` 等跨期复用 ID 会导致重复行。
- 当前 `lead_assign_plan_actual_valid_count.sql` 只输出 `pl.group_id`，且 `fp` 层按全部输出字段 `group by` 去重；如改为输出 `pl.qici/group_name`，需同步调整 join key 和聚合粒度。
- `group_name` 含业务分类信息，如“高中年级”“初三年级”“IP渠道”“抖音私信”，但不是稳定结构化字段；需要渠道/年级时优先使用规则名拆分或明确业务映射。

## 本地登记与平台核验补充（2026-11-28）

历史类型记录（仅说明原文推断来源）：`year` 原记为 bigint；`group_id` 原记为 bigint。当前查询输出类型采用上文平台解析记录。

### 1. 中文名称

当前市场分配计划组ID表。

### 2. 表用途

当前分配SQL使用的计划组ID登记，不因渠道CASE更新改动计划或分配目标。 2026-11-28从实时生产模型2307读取的完整SQL确认当前表名。

### 3. 数据粒度

登记或关联键为`year + qici + group_id`；这不保证当前数据唯一。当前重复、空值、历史覆盖与具体Join粒度须按目标验证。

### 4. 查询引擎

Presto，当前生产查询已实际执行。其他引擎按各目标运行证据确认。

### 5. 分区字段

当前消费者未使用本表的dt/hour分区条件；完整物理分区结构未确认，不能仅据SQL推断无分区。

### 6. 强制范围限定字段

保留各模型已有期次、渠道、年级或员工范围及主查询业务范围。尚未确认通用部门限定或新的联接合同，不自动放宽范围或复用其他部门定义。

### 7. 字段清单

以下为治理登记的上传列，不是重新生成的完整DDL；字段类型见下方平台结构核验。

### 8. 常用过滤条件

`qici = '<MMDD期>'`仅为占位示意，须以目标已审定范围替换；不能直接进入生产执行。

### 9. 常用 join key

`year + qici + group_id`仅记录现有用法。对映射表或目标表Join前检查键唯一性，禁止未经验证的明细放大或跨期关联。

### 10. 常用 SQL 片段

```sql
SELECT year, qici, group_id, group_name
FROM temp_table.lvshuai01_plan_id
WHERE year = '<年份>' AND qici = '<MMDD期>'
```

该片段不提供独立执行授权，也不确认任何新业务指标。

### 11. 注意事项

[治理登记](../../../sync-qingcheng-market-temp-tables/references/workflow_registry.json)中的`market_plan_id`确认本域平台表名、上传列与登记键。 本轮只维护当前物理绑定，不上传、重命名或改写临时表数据，不推断当前行数、最新期次或质量状态；这些信息需新回执或受治理查询。confirmed及automatic_compile状态不因本条记录自动提升。

### 补充业务语义与风险

`qici` 历史登记为 `MMDD期`，由 `year` 补足年份；`group_id` 可跨期复用。跨年关联应核验 `year + qici + group_id`，不可仅用 `group_id` 推断唯一；`year` 和 `group_id` 的平台解析类型是 `string`。

### 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`year`、`qici`、`group_id`、`group_name`。
