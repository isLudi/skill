# gaotu_hl.ods_mkt_h_channel_rule_df

## 1. 中文名称

H业务线渠道映射原文表

## 2. 表用途

按适用二级学部和期次保存完整渠道归因 `CASE WHEN ... END` 规则文本。该表是规则原文载体，不是逐条规则条件明细表，也不直接输出 `channel_map`。

## 3. 数据粒度

数据地图登记为日增量快照；业务目标粒度看似为 `department_name + period_name + channel_case_when`。当前 SQL 查询权限未开通，最新分区、联合键唯一性和重复规则文本尚未实测，不能把目标粒度当作已确认主键。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 同步日期 yyyyMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| dt | string | 最新已完成分区 | 是 | 跨分区会重复保存不同日期的规则原文；当前最新分区尚未通过 SQL 验证 |

## 7. 字段清单

> 来源：2026-08-13 天工2数据地图 `tableV2` 字段和 DDL；业务查询权限未开通。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| department_name | string | 适用二级学部 | 选择适用规则文本 | 是 |
| period_name | string | 规则适用期次，如 20260724期 | 选择适用规则文本 | 是 |
| channel_case_when | string | 完整渠道归因 CASE WHEN ... END 规则文本 | 规则审计、版本同步 | 是 |
| dt | string | 同步日期 yyyyMMdd | 分区过滤 | 是 |

## 8. 常用过滤条件

- 必须限定单个 `dt`；在查询权限开通前，不得猜测最新分区。
- 若用于规则选择，还需同时限定 `department_name` 和 `period_name`，并先验证单分区内该联合键是否唯一。

## 9. 常用 join key

- `department_name + period_name` 只能选出一段规则文本，不能通过等值 Join 直接得到 `channel_map`。
- 表中没有 `rule_code`、条件字段、操作符、条件值、优先级和逐规则 `channel_map`。`channel_case_when` 是 SQL 文本，Presto 不会把 Join 后的字符串动态执行为当前行的表达式。
- 因此本表不能直接替代宽表中的有序 CASE，也不能与 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 构成非 `lead_id` 的渠道归因 Join。

## 10. 常用 SQL 片段

### 权限开通后的唯一性探针

```sql
select
    department_name,
    period_name,
    count(*) as row_cnt,
    count(distinct channel_case_when) as case_text_cnt
from gaotu_hl.ods_mkt_h_channel_rule_df
where dt = 'YYYYMMDD'
group by department_name, period_name
having count(*) > 1
limit 100;
```

## 11. 注意事项

- 2026-08-13 通过数据地图确认表结构；同日 Presto 探针在提交前被权限门禁阻断，错误为“下列表无查询权限：`gaotu_hl.ods_mkt_h_channel_rule_df`”，没有业务查询 ID。
- 相关 `da.app_dim_jp_channel_case_version_df` 同样保存整段 `channel_case_when` 及版本元数据，并非关系化规则明细。
- 若要通过 Join 替换超长 CASE，需要上游另建逐规则配置或直接在事实宽表输出 `channel_map/rule_code`；不得解析后无审计地重排 first-match 规则。
