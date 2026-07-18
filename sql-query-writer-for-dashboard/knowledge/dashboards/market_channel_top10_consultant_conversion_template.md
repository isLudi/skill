# 市场渠道内 TOP10 顾问转化模板

## 1. 定位

- 业务域：`market_consultant`
- 模板编号：M7
- 用途：在每个“顾问学部 + 渠道”组合内，按当期净 GMV 选择前 N 名顾问，并输出承接线索、正价课人头/科目人次和单效分子分母。
- 历史结果：`runtime/sql-query-writer-for-dashboard/top10_consultant_conversion_20260710_jpb_koc_zhou_jyb_xian_link.xlsx`
- 指标文档：`knowledge/metrics/market_channel_top10_consultant_conversion_metrics.md`
- 基础口径：`knowledge/dashboards/market_consultant_conversion.md`

本模板不归档历史 SQL 中的超长渠道 CASE。生成查询时必须从 `knowledge/sql_patterns/channel_mapping_case_when.md` 定位当前 canonical 渠道映射，再叠加排名层。

## 2. QuerySpec 骨架

| 槽位 | 取值/要求 |
|---|---|
| `domain` | `market_consultant` |
| `intent` | 渠道内顾问净 GMV TOP N |
| `dimensions` | 期次、顾问学部、渠道、顾问；明细可带年级、规则、经理、主管 |
| `filters` | 目标 `department_channel_pairs` 与 `top_n` |
| `time_range` | 单期或明确期次范围 |
| `calculation_grain` | 先按 `period + advisor_department + channel + consultant` 汇总排名指标 |
| `output_grain` | 汇总版一行一个顾问；明细版可回连规则/年级行 |
| `candidate_tables` | 市场全链路宽表；首 call 任务和员工维只在需要过程指标时加入 |
| `join_path` | 基础转化层 → 顾问聚合 → 窗口排名 → 可选回连明细 |

## 3. 排名规则

```text
partition by consultant_department + channel_map
order by current_net_gmv_num desc,
         take_leads_den desc,
         employee_email_name asc
```

默认 `top_n=10`。必须使用确定性并列顺序，不能只按净 GMV 排名后任意截断。

## 4. 参数化与渠道治理

- `department_channel_pairs` 是显式配对，不是两个独立 `IN` 集合，防止组合交叉扩张。
- `top_n`、期次和是否保留零 GMV 顾问均为参数。
- 渠道显示值必须来自当前 canonical 映射；若用户改查其他渠道，只替换配对过滤，不复制历史 CASE。
- 顾问学部使用明确字段，不能在 `section_assign`、`virtual`、`period_mapping` 三套部门之间静默替换。

## 5. 校验

- 排名前先确认顾问聚合键唯一，排名后每个组合人数不超过 `top_n`。
- 回连规则明细后排名值会在多行重复；最终汇总必须只取顾问层字段一次，或重新按顾问聚合。
- 历史工作簿包含 2 个学部—渠道组合、20 名顾问和 52 条规则明细；排名规则为净 GMV 降序、承接线索降序、顾问名升序。

## 6. 门禁

该模板依赖当前仍为 `pending_confirmation` 的有效线索特殊渠道分支和长渠道映射，因此属于人工 SQL 模板；不得由 P2 单表编译器自动生成。
