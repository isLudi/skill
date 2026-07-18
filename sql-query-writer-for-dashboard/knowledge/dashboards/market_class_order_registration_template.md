# 市场顾问指定班级订单与暑秋联报报名类型模板

## 1. 定位

- 业务域：`market_consultant`
- 模板编号：M1
- 用途：查询指定班级的订单—班级明细，并补充“暑秋联报 / 单秋”报名类型。
- 证据 SQL：
  - `resources/raw_sql/market_class_order_detail_20260718.sql`
  - `resources/raw_sql/market_class_order_registration_type_20260718.sql`
- 历史验证工作簿：`runtime/market_class_orders_20260503/市场顾问部_指定班级订单明细_区分暑秋联报.xlsx`

这是两段查询组合而成的人工 SQL 模板，不是单表自动编译模板。先分别得到财务订单—班级明细和 service 报名类型，再按 `order_number + class_id` 合并。

## 2. QuerySpec 骨架

| 槽位 | 取值/要求 |
|---|---|
| `domain` | `market_consultant` |
| `intent` | 指定班级订单明细，并识别暑秋联报/秋季单报 |
| `business_scope` | `H业务线 / 市场部 / 市场顾问部` |
| `time_range` | 原始支付时间或订单支付时间；必须明确起止边界 |
| `calculation_grain` | `order_number + clazz_biz_number` |
| `output_grain` | 一行一个订单—班级 |
| `candidate_tables` | 财务业绩扩展明细、订单归因收入退款明细 |
| `join_path` | 两段结果按 `order_number + class_id` 一对一预期合并 |

## 3. 两段 SQL 的职责

### 3.1 财务订单—班级明细

`market_class_order_detail_20260718.sql` 输出：

- 订单、用户、班级、子班、课程科目、年级、学年、学季、主讲；
- 支付时间、订单状态、订单价格；
- 收款、退款、净业绩金额；
- 顾问、主管、最新交易时间；
- `performance_detail_id_count`、`raw_event_row_count`、源分区。

金额从交易事件汇总到 `order_number + clazz_biz_number`。同一订单包含多个班级时，不能在未确认金额分摊方式的情况下直接跨班级求和。

### 3.2 报名类型

`market_class_order_registration_type_20260718.sql` 以 2026 秋季班 `school_term_code='Q'` 为样例：

| 条件 | 报名类型 |
|---|---|
| `bind_type=2` | 暑秋联报，从课 |
| `bind_type=1` | 暑秋联报，主课 |
| `bind_type=0` | 单秋/秋季普通订单 |

同一订单—班级出现多种 `bind_type` 时，历史模板按“联报优先”归类；该优先级只服务报名类型展示，不等于财务订单去重规则。

## 4. 调用时必须替换的参数

1. `clazz_biz_number` 班级列表。
2. 支付时间范围，建议左闭右开；历史样例使用 `order_paid_time > '2026-05-03 19:30:00'`，复用时不得沿用该时间。
3. 学年和学季：`school_year`、`school_term_code`。
4. 市场顾问范围：财务侧与 service 侧都要保持 `H业务线 / 市场部 / 市场顾问部`。
5. 快照小时：两段 SQL 的 `dt/hour` 必须来自同一可用快照策略。

## 5. 合并与校验

- 合并键：`order_number + class_id`，不要只按用户或订单号合并。
- 合并前分别检查两侧键重复数；报名类型侧若不唯一，先按模板优先级压成一行。
- 合并后检查财务明细行数是否守恒、未匹配键数、报名类型分布以及订单金额去重总额。
- 历史工作簿验证：2258 个订单—班级键全部匹配；其中暑秋联报 2254、单秋 4。

## 6. 不可直接复用边界

- `bind_type` 的报名类型解释只在当前 2026 秋季样例中验证；其他学年、学季先做分布探查。
- 一张订单多班级时，订单金额可能重复带出；汇总订单金额必须使用订单级去重字段或另建订单层。
- 本模板不授权直接执行；生成 QueryPlan 时必须保留多表人工审阅。
