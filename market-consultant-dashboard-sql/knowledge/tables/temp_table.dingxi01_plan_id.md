# temp_table.dingxi01_plan_id

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
|---|---|---|---|
| 无 | - | 稳定临时表，SQL 中未体现 dt/hour 分区 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| year | bigint | 2026 | 建议 | 年份字段；当前 Excel 仅有 2026 |
| qici | string | '<MMDD期>' | 建议 | 期次尾号格式，例如 `0306期`、`0508期` |
| group_id | bigint | '<规则组ID>' | 建议 | 分配规则组 ID；单字段可能跨期重复 |

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
|---|---|---|---|---|---|
| year | bigint | 年份 | 和 `qici` 组成完整期次范围 | 2026 | 是 |
| qici | string | 期次尾号，格式为 MMDD期，不含年份 | 期次过滤、与规则名拆出的期次片段关联 | 0306期；0508期；0515期 | 是 |
| group_id | bigint | 分配规则组 ID | 与 `service_dw.dim_crm_assign_rule_lead_detail_hf.group_id` 关联 | 14153；15175；15366 | 是 |
| group_name | string | 分配规则组名称 | 规则组展示、渠道/年级类别识别 | 0306期-市场-高中年级；2026年-短期班-抖音私信 | 是 |

## 8. 常用过滤条件

- `t.year = 2026`
- `t.qici = '<MMDD期>'`
- `t.group_id is not null`
- `t.group_name like '%市场%'`

## 9. 常用 join key

| 左表 | 左字段 | 右表 | 右字段 | 说明 |
|---|---|---|---|---|
| service_dw.dim_crm_assign_rule_lead_detail_hf | group_id | temp_table.dingxi01_plan_id | group_id | 仅保留临时表维护的规则组；若输出 `qici/group_name`，必须处理 `group_id` 跨期重复 |
| 规则名派生 | `split_part(rule_name, '-', 1)` | temp_table.dingxi01_plan_id | qici | 可用规则名期次片段与维护表期次对齐，需确认规则名格式 |

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
from temp_table.dingxi01_plan_id t
limit 20;
```

### 按期次查看规则组

```sql
select
    t.year,
    t.qici,
    t.group_id,
    t.group_name
from temp_table.dingxi01_plan_id t
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
from temp_table.dingxi01_plan_id t
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
from temp_table.dingxi01_plan_id t
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
join temp_table.dingxi01_plan_id pl
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
join temp_table.dingxi01_plan_id pl
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
