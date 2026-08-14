# gaotu_hl.dim_mkt_h_period_df

## 1. 中文名称

H业务线标准期次映射表

## 2. 表用途

来自天工数据地图的表说明：记录 H 业务线班课标准期次、转化窗口、绩效月归属、月内期数、前后期关系和期次质量标记。

## 3. 数据粒度

天工数据地图未提供可直接确认的主键或物理唯一性；具体快照粒度和联合键待 SQL 验证。

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
| stat_period_name | string | 标准期名，如 20260722期（全域唯一口径） | 数据地图补充 | 否 |
| department | string | 学部 | 数据地图补充 | 否 |
| month | bigint | 归属绩效月 yyyyMM（业务指定，非按窗口推导） | 数据地图补充 | 否 |
| period_cnt_month | bigint | 月内期数（飞书维护值，用于月薪摊分） | 数据地图补充 | 否 |
| period_cnt_month_calc | bigint | 月内期数（由日历自身推导，校验用） | 数据地图补充 | 否 |
| is_cnt_mismatch | int | 1=飞书月期数与日历实际不符，需修飞书 | 数据地图补充 | 否 |
| period_begin_day | string | 转化开始日 yyyy-MM-dd | 数据地图补充 | 否 |
| period_end_day | string | 转化结束日 yyyy-MM-dd | 数据地图补充 | 否 |
| period_span_days | int | 窗口天数（正常7天，暑假保护期5~6天） | 数据地图补充 | 否 |
| begin_dow | int | 起始日周几 1=周一..7=周日（锚点法算，非 dayofweek） | 数据地图补充 | 否 |
| end_dow | int | 结束日周几 1=周一..7=周日 | 数据地图补充 | 否 |
| is_special_period | int | 1=特殊期（起始日非周二） | 数据地图补充 | 否 |
| mkt_cb_week | string | 市场成本分摊周 yyyyMMdd=(结束日-2天)所在周周一 | 数据地图补充 | 否 |
| period_seq_in_month | int | 本部门本月第几期 | 数据地图补充 | 否 |
| prev_period_name | string | 本部门上一期期名 | 数据地图补充 | 否 |
| next_period_name | string | 本部门下一期期名 | 数据地图补充 | 否 |
| gap_days_from_prev | int | 与上期间隔 0=正常 >0=空档 <0=重叠(必修) | 数据地图补充 | 否 |

## 8. 常用过滤条件

- 查询必须限定 `dt` 分区。

## 9. 常用 join key

待权限审批完成后进行 Join 关系和基数探查；本次不记录已确认的 Join 关系。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from gaotu_hl.dim_mkt_h_period_df t
where t.dt = 'YYYYMMDD'
limit 20;
```

## 11. 注意事项

- 字段、类型和分区信息来源于天工数据地图；本次仅完成物理字段登记。
- 当前账号尚未具备完整查询权限，标准期次的唯一性、快照粒度和跨表 Join 基数待后续验证。
- `stat_period_name` 与 `department` 的业务关联关系暂不在本次登记中确认。
