# gaotu_hl.dim_mkt_h_period_map_df

## 1. 中文名称

H业务线标准期名映射表

## 2. 表用途

来自天工数据地图的表说明：将系统期名映射为统一的标准期名，并记录转化窗口、后三天判定区间、重叠天数和折入标记。

## 3. 数据粒度

期次映射快照粒度；在 `dt='20260812'` 快照中，`(department, source_period_name)` 为 845/845 唯一。`source_period_name` 单字段不能作为唯一键，同一系统期可能属于多个部门。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 计算日期 yyyyMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|

### 7.1 数据地图字段补充（2026-08-13）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| department | string | 顾问所属二级部门（精品班中价单列为 精品中价） | 数据地图补充 | 否 |
| source_period_name | string | 底表系统期名 group_period_year+group_period_term，如 20260722期 | 数据地图补充 | 否 |
| stat_period_name | string | 折入后的标准期名，如 20260724期 | 数据地图补充 | 否 |
| win_begin_day | string | 该系统期的转化开始日 yyyy-MM-dd | 数据地图补充 | 否 |
| win_end_day | string | 该系统期的转化结束日 yyyy-MM-dd | 数据地图补充 | 否 |
| tail_begin_day | string | 判定区间起点=后三天起点 GREATEST(win_begin, win_end-2) | 数据地图补充 | 否 |
| period_begin_day | string | 命中标准期的转化开始日 | 数据地图补充 | 否 |
| period_end_day | string | 命中标准期的转化结束日 | 数据地图补充 | 否 |
| overlap_days | int | 后三天区间与标准期的重叠天数（择大者胜的依据） | 数据地图补充 | 否 |
| is_folded | int | 1=发生折入(系统期名≠标准期名)，0=原样 | 数据地图补充 | 否 |

## 8. 常用过滤条件

- 查询必须限定 `dt` 分区。

## 9. 常用 join key

- 与 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 的确认关联键：
  - `concat(group_period_year, group_period_term) = source_period_name`；
  - `period_mapping_second_level_department_name = department`。
- `group_period_name` 是带业务描述的 verbose 字段，不能直接替代 `group_period_year + group_period_term`；历史探针直接用它关联时 425 个宽表键命中 0 个。
- `period_name` 也不是稳定关联键。同一“系统期名+部门”下宽表可能存在多个 verbose `period_name`，应只用紧凑系统期键关联。
- 生产 SQL 建议先按 `dt` 取期次映射快照，并按 `(department, source_period_name)` 预聚合/校验后再 `left join`；当前快照该键无重复，因此不会放大宽表。若同一键出现多个 `stat_period_name`，应先阻断并人工确认，不得用任意 `min` 静默覆盖。

### 9.1 SQL 验证证据（2026-08-13）

- `dt='20260812'`：845 行，`(department, source_period_name)` 去重后仍为 845；`source_period_name` 单字段抽样 189 个，其中 177 个跨多个部门，最多 6 个部门。
- 市场顾问部宽表快照 `dt='20260813', hour='11'`：按上述键关联后宽表 1,587,881 行，Join 后仍为 1,587,881 行；`市场部` 子集 210,630 行、29 个宽表键全部命中。
- 全量宽表快照包含历史期次，宽表 419 个系统期+部门键中 260 个命中；未命中主要是期次映射保留期外或其他学部数据，不能据此否定当前市场部关联。
- 证据 Query ID：`1545552186`、`1545561455`、`1545568337`、`1545590228`、`1545588820`。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from gaotu_hl.dim_mkt_h_period_map_df t
where t.dt = 'YYYYMMDD'
limit 20;
```

## 11. 注意事项

- 字段、类型和分区信息来源于天工数据地图；唯一性和 Join 基数来自 2026-08-13 的线上 SQL 探针。
- 必须同时使用 `source_period_name + department`；只用 `source_period_name` 会产生多部门匹配风险。
- 当前验证确认了市场部快照的覆盖和无 1:N 放大，但历史期次覆盖仍受 `dt` 快照/保留期影响，使用更早宽表数据时应单独检查未命中量。
