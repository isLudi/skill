# 青橙暑期期次修正规则

## 背景

2026 年 7 月后，青橙项目部进入暑期业务排期，期次不再稳定等同自然周周五。相关 SQL 若继续以 `trade_timestamp`、`full_refund_timestamp` 或 `group_period_year + group_period_term` 推导固定周五期次，会把暑期运营周期误切为自然周周五期次，例如 `20260717期`、`20260724期`。

2026-07-16 业务重新确认，当前已确认的暑期运营期次以以下日期范围为准：

| 日期范围 | 业务期次 | 旧周五期次 |
|---|---|---|
| `2026-07-14` 至 `2026-07-19` | `20260716期` | `20260717期` |
| `2026-07-20` 至 `2026-07-25` | `20260722期` | `20260724期` |
| `2026-07-26` 至 `2026-07-31` | `20260728期` | `20260731期` |
| `2026-08-01` 至 `2026-08-06` | `20260803期` | `20260807期` |
| `2026-08-07` 至 `2026-08-12` | `20260809期` | `20260814期` |

## 已落库修正

2026-07-15 已将 `2460 转化数据` 同步为 canonical SQL：

```text
resources/raw_sql/data_center_qingcheng_2460.sql
```

该转化数据修正包含三处：

1. 订单侧结果期次 `dd.base.qici`：先按 `trade_timestamp` 命中 `biz_qici_calendar`，未命中才回退固定周五逻辑。
2. 当期判断短期次 `qici0`：当最终业务 `qici` 对应的旧周五短期次与 `rule_name` 提取短期次一致时，归一到业务短期次，避免 `is_on_period` 被误判为往期。
3. 线索侧期次 `bb.qici`：先按 `group_period_year + group_period_term` 命中同一份 `biz_qici_calendar`，保证有效线索量与订单结果在业务期次上对齐。

2026-07-16 已按业务重新确认的实际运行区间，将以下完成度/个人产出数据集替换并抽数成功：

- `resources/raw_sql/data_center_qingcheng_2769.sql`：青橙个人转化。
- `resources/raw_sql/data_center_qingcheng_2680.sql`：团队完成度【期】。
- `resources/raw_sql/data_center_qingcheng_2677.sql`：团队完成度【月】。

这三份 SQL 均在 `biz_qici_calendar` 中维护 `0716/0722/0728/0803/0809` 五个已确认区间，并在订单结果期次、团队历史架构回填期次、退费期次三类日期来源上使用日期范围 join。

2026-07-17 已按相同实际区间更新行课报表数据集：

- `resources/raw_sql/data_center_qingcheng_2244.sql`：青橙到课，服务 `青橙项目部_行课报表`。线索侧按 `group_period_year + group_period_term` 解析日期后范围 join `biz_qici_calendar`，行课侧按 `begin_time` 日期范围 join 同一日历；未命中日历时才回退历史周五逻辑。

## 影响指标

期次修正会影响看板全局筛选器 `qici`，以及所有按 `qici` 分组、筛选或 join 的组件。

当期判断也会影响以下 SQL 输出字段：

- `p_pay_user`
- `p_pay_sub`
- `p_income`

前端自定义指标中，基于这些字段计算的当期人头转化率、当期订单转化率、当期单效也会随之变化。

## 后续修正原则

后续校正其他暑期期次时，不能只改筛选期展示值。必须同时检查：

- 订单侧结果期次 `qici`
- 线索侧有效线索期次 `bb.qici`
- 当期判断短期次 `qici0`
- `mm` 层线索和订单 full outer join 的 `qici` 对齐
- `temp_table.dingxi01_qing_team_jg` 的 `employee_email_name + qici` 架构回填

短期可继续维护 SQL 内的 `biz_qici_calendar` CTE，但必须先由业务确认日期范围、业务期次、旧周五期次和短期次映射。

中长期应改为业务日历表日期范围 join，例如：

```sql
left join temp_table.dingxi01_biz_qici_calendar cal
  on cast(t.<business_date_field> as date) >= cal.start_date
 and cast(t.<business_date_field> as date) <= cal.end_date
 and cal.biz_line = 'qingcheng'
```

生产 SQL 中优先使用 `cal.qici`，只有日历缺失时才回退历史周五逻辑。

## 风险提醒

- `rule_name` 中的短期次不一定跟最终展示 `qici` 同步变化，必须显式处理短期次归一。
- 青橙转化数据看板是 lead-attribution 口径，不等同个人/团队完成度 finance-performance 口径；不要把本修正规则直接套到完成度 SQL，除非逐个核对其期次字段和目标表 join。
- 当前业务已确认并维护至 `20260809期`。后续新增期次时，应优先补充 `biz_qici_calendar`，并同步验证看板公共筛选器 `qici` 不再暴露旧周五期次。
