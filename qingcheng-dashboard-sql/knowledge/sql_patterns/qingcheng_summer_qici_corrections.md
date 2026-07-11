# 青橙暑期期次修正规则

## 背景

2026 年 7 月后，青橙项目部进入暑期业务排期，期次不再稳定等同自然周周五。转化数据看板 `2460` 原 SQL 以 `trade_timestamp` 或 `group_period_year + group_period_term` 推导固定周五期次，导致 `2026-07-14` 至 `2026-07-18` 这 5 天被显示为 `20260717期`。

业务实际要求：`2026-07-14` 至 `2026-07-18` 统一归属 `20260716期`。

## 已落库修正

2026-07-09 已将 `2460 转化数据` 同步为当前 canonical SQL：

```text
resources/raw_sql/data_center_qingcheng_2460.sql
```

本次修正包含三处：

1. 订单侧结果期次 `dd.base.qici`：在 `trade_timestamp` 周五推导前增加 `2026-07-14` 至 `2026-07-18` 返回 `20260716期` 的优先分支。
2. 当期判断短期次 `qici0`：当结果期次为 `20260716期` 且 `rule_name` 提取短期次为 `0717期` 时，归一为 `0716期`，避免 `is_on_period` 被误判为往期。
3. 线索侧期次 `bb.qici`：在 `group_period_year + group_period_term` 周五推导前增加同一日期范围优先分支，保证有效线索量与订单结果在 `20260716期` 对齐。

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

短期可继续使用 `case when 日期范围 then 期次` 的方式热修，但必须先由业务确认日期范围。

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
- 当前仅确认 `2026-07-14` 至 `2026-07-18` 归属 `20260716期`。后续 `0722`、`0728`、`0803/0809` 等暑期期次需要继续按业务日历补充。
