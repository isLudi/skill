# 市场渠道财务正价课科目结构模板

## 1. 定位

- 业务域：`market_consultant`
- 模板编号：M6
- 用途：查询指定渠道集合在各期次、年级、经理下的财务正价课科目用户、人次、金额和订单结构。
- 历史 SQL：`resources/raw_sql/market_finance_positive_subject_structure_example_20260718.sql`
- 历史结果：`runtime/sql-query-writer-for-dashboard/koc_finance_positive_subjects_20260605_20260703.xlsx`
- 指标文档：`knowledge/metrics/market_finance_positive_subject_structure_metrics.md`

## 2. 为什么使用财务识别

历史 KOC 样例在目标范围内按 2809 转化口径读取 `regular_course_user_count / positive_user_cnt` 均为 0；若继续要求 `conversion_lead_count > 0` 会得到空结果。因此 M6 以财务业绩明细中 `real_price <> 0` 且 `trade_type in ('正常订单','调课调班')` 的同 `qici + user_id` 订单识别正价课用户。

这是一种待确认的财务正价课识别，不应替换已有 2809 转化口径。调用前必须明确用户需要“业财订单识别”还是“运营转化识别”。

## 3. QuerySpec 骨架

| 槽位 | 取值/要求 |
|---|---|
| `domain` | `market_consultant` |
| `intent` | 指定渠道的财务正价课科目结构 |
| `dimensions` | 期次、渠道、年级、经理、科目 |
| `time_range` | 线索期次范围；财务分区与交易时间策略同时明确 |
| `business_scope` | H 业务线和明确的承接组织范围 |
| `calculation_grain` | `period + channel + grade + manager + user + subject` |
| `output_grain` | `period + channel + grade + manager + subject` |
| `candidate_tables` | 市场全链路宽表、财务业绩扩展明细 |
| `join_path` | `period_name + user_id`；财务侧先压缩到用户—科目 |

## 4. 参数化要求

- 渠道必须先通过当前 `channel_map` 入口生成，再使用 `channel_list` 过滤；不要把历史四个 KOC 渠道写成模板常量。
- `period_start`、`period_end`、`grade_list`、经理维度是否保留均为参数。
- 财务课程组织、交易类型、`real_price` 条件必须随具体产品范围复核。
- 需要补齐零售科目时，使用受控 `subject_dim`；新增科目不能默默归入“其他”。

## 5. 比率与分母

SQL 只输出可加总的分子/分母：

```text
用户覆盖占比 = sum(subject_user_count_num) / sum(total_positive_user_den)
科目人次占比 = sum(subject_person_count_num) / sum(total_subject_person_den)
科目金额占比 = sum(subject_amount_num) / sum(total_subject_amount_den)
```

分母已在每个科目行重复展示，跨科目求总计时不能直接 `sum(total_*_den)`；应在不含科目的目标粒度取一次分母或重新从用户—科目基础层计算。

## 6. 校验

- 先核对 `period + user_id` 财务匹配率与未匹配用户数。
- 检查每组 `subject_user_count_num <= total_positive_user_den`。
- 科目人次、金额允许一个用户多科，但各科金额合计应与同组财务净额守恒。
- 历史样例 810 行，覆盖 5 个期次、4 个渠道、10 个科目；只作为 worked evidence。
