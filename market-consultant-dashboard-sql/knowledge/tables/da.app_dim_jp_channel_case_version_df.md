# da.app_dim_jp_channel_case_version_df

## 1. 中文名称

精品班飞书渠道映射版本表

## 2. 表用途

保存业务提交的渠道 CASE 版本、状态和来源文件。它提供版本治理元数据，但渠道逻辑仍是整段 SQL 文本，不是可直接等值 Join 的规则明细。

## 3. 数据粒度

数据地图登记为日全量快照，目标逻辑粒度为规则版本/期次；单分区唯一键尚未通过 SQL 验证。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 飞书同步日期 yyyyMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| dt | string | 最新已完成分区 | 是 | 全量快照跨分区会重复版本 |

## 7. 字段清单

> 来源：2026-08-13 天工2数据地图 `tableV2` 字段和 DDL；本轮未执行该表的 SQL 数据探针。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| seq_no | bigint | 版本序号，数字越大表示版本越新 | 版本排序 | 是 |
| period_name | string | 期 | 规则适用期次 | 是 |
| channel_case_when | string | 业务维护的完整渠道映射 CASE WHEN SQL 片段 | 规则文本 | 是 |
| rule_version | string | 渠道规则版本，例如 jp_channel_v20260529 | 版本标识 | 是 |
| status | string | 版本状态：生效、待确认、停用 | 生效过滤 | 是 |
| source_file | string | 业务提交的来源文件，例如 0529.txt | 来源追溯 | 否 |
| submitted_by | string | 提交人 | 来源追溯 | 否 |
| remark | string | 版本说明及变更备注 | 变更审计 | 否 |
| dt | string | 飞书同步日期 yyyyMMdd | 分区过滤 | 是 |

## 8. 常用过滤条件

- 必须限定单个 `dt`，并按 `status='生效'`、期次和版本序号选择规则；具体唯一性需权限和数据探针确认。

## 9. 常用 join key

- `period_name + rule_version/seq_no` 可定位一段版本化 CASE 文本，但不能将文本动态应用到事实行。
- 市场顾问全链路宽表当前没有 `rule_version` 或 `seq_no`，也没有与本表共享的逐规则条件 ID，因此不存在直接渠道归因 Join。

## 10. 常用 SQL 片段

```sql
select *
from da.app_dim_jp_channel_case_version_df
where dt = 'YYYYMMDD'
  and status = '生效'
limit 20;
```

## 11. 注意事项

- 该表可用于版本审计或驱动上游编译任务，不能作为运行时维表直接替代有序 CASE。
- `da.app_crm_lead_channel_map_di` 虽输出 `channel_map/rule_version/rule_seq_no`，仍是 `lead_id` 粒度结果表；市场顾问宽表不带规则版本键，不能据此建立非 `lead_id` Join。
