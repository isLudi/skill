# 渠道专项正价课科目与班课 worked example

## 1. 定位

- 业务域：`market_consultant`
- 模板编号：M8
- 用途：在 M6 财务正价课科目结构上，继续拆分订单类型、课程部门、版本关键词、课程、班级和子班。
- 历史 SQL：`resources/raw_sql/market_channel_positive_subject_course_example_20260718.sql`
- 历史结果：`runtime/sql-query-writer-for-dashboard/xian_live_jiangsu_positive_subjects_20260626_20260703.xlsx`
- 母模板：`knowledge/dashboards/market_finance_positive_subject_structure_template.md`

历史样例使用“西安直播江苏”规则和“江苏专版”关键词。二者都只是 worked example，不是固定渠道或固定产品；未来更换渠道时保留同一指标和 Join 结构，替换渠道/产品分类参数。

## 2. M6 基础层之上的新增维度

| 维度 | 历史样例 | 参数化要求 |
|---|---|---|
| `channel_scope_predicate` | 两个西安直播江苏 `rule_name` | 替换为目标渠道当前规则；先有界探查命中 |
| `channel_label` | 历史 SQL 直接展示 `rule_name` | 可换成当前 `channel_map` 输出 |
| `order_course_type` | 精品班大班课 / 本地化学部 | 按目标课程二级部门重新分类 |
| `edition_flag` | 课程/班级/子班任一包含“江苏专版” | 关键词和命中字段均为参数 |
| `course_fields` | 课程、班级、子班 | 按需要选择，不需要时在更粗粒度聚合 |
| `period_match_flag` | 规则期次与线索期次是否一致 | 其他规则命名不能直接复用截字符串逻辑 |

## 3. 指标不变

继续使用 M6 的：

- 科目用户数 / 同组正价课用户数；
- 科目人次 / 同组总科目人次；
- 科目金额 / 同组总科目金额；
- 科目订单数。

“同组”在 M8 必须包含所有保留的课程分类维度。删除或增加维度时，分子与分母 CTE 必须一起改，不能只改最终 `SELECT`。

## 4. QuerySpec 必填参数

- 期次/交易时间范围；
- `channel_scope_predicate` 与 `channel_label`；
- 规则期次解析方式；
- 财务课程组织范围和正价课识别；
- 订单类型 CASE；
- 版本关键词与命中字段；
- 最终需要的课程/班级/子班粒度。

## 5. 校验

- 检查渠道规则命中用户数和财务 `period + user_id` 匹配率。
- 检查“未匹配到财务订单/科目”人数。
- 版本标记分组应互斥且覆盖全部已匹配订单。
- 历史工作簿有 610 个业务行、107 名用户，并将精品班、本地化学部和江苏专版拆开；这些数字不是新渠道的预期值。
- 新渠道或新版本关键词上线前，必须抽样核对课程、班级、子班名称，避免关键词误命中。
