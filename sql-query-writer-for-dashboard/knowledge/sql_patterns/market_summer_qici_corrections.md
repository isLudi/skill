# 市场顾问部暑期期次修正规则

## 背景

2026 年 7 月后，运营节奏进入暑期排期，业务期次不再稳定等同于“自然周周五”。旧 SQL 中常见的期次生成方式是从业务日期或 `group_period` 推导到当周周五，例如把 `2026-07-14` 至 `2026-07-18` 这一段识别为 `20260717期`。但运营侧实际排期要求这 5 天归属 `20260716期`。

因此，不能继续把“周五日期”当作所有暑期期次的唯一锚点。后续每个暑期期次应优先按业务日历维护的日期范围认定，再回填到数据集 SQL。

## 本次已落库修正

2026-07-09 已将运营侧数据看板相关 8 个数据集同步为 `*_20260709.sql` 热修版本：

| 数据集 | fileValue | 修正点 |
|---|---:|---|
| `(内部渠道)外呼过程数据` | `2054` | `group_period`、`assign_time`、`begin_time` 派生期次；并删除末尾 `where valid_lead_count > 0` |
| `(内部)到课衰减情况` | `2132` | `group_period` 派生期次 |
| `运营侧个人数据` | `2293` | `group_period` 派生 `period_name`；`begin_time` 派生 `qici` |
| `分二级部门转化` | `2310` | `group_period` 派生期次 |
| `分析--分周期转化` | `2344` | `trade_time`、`trade_group_period/group_period` 派生期次 |
| `进量测试(市场渠道)` | `2345` | `group_period` 派生 `period_name`；`begin_time` 派生 `qici` |
| `每日转化情况` | `2423` | `trade_time`、`trade_group_period` 派生期次 |
| `每日转化数据表` | `2424` | `trade_time`、`trade_group_period/group_period` 派生期次 |

本次热修规则：

```sql
case
    when cast(<business_date_field> as date) between date '2026-07-14' and date '2026-07-18'
    then '20260716期'
    ...
end
```

`20260716期` 的统计周期必须覆盖 `2026-07-14` 至 `2026-07-18`，不是只改展示文本。如果 SQL 中同一数据集存在多个期次字段，例如筛选期、成交期、线索/分配期，所有参与看板筛选或分组的派生字段都要一致修正。

## 后续改造方向

短期继续修正其他暑期期次时，可以沿用上面的 `case when 日期范围 then 期次` 方式，但每次必须先确认实际业务日期范围，不能按自然周推算。

中长期应把期次认定迁移到业务日历表，通过日期范围 join 统一取期次：

```sql
left join temp_table.dingxi01_biz_qici_calendar cal
  on cast(t.<business_date_field> as date) >= cal.start_date
 and cast(t.<business_date_field> as date) <= cal.end_date
 and cal.biz_line = 'market_consultant'
```

生产 SQL 中优先使用 `cal.qici`，只有业务日历缺失时才回退历史周五推导逻辑：

```sql
coalesce(
    cal.qici,
    concat(date_format(date_add('day', 5 - day_of_week(cast(t.<business_date_field> as date)), cast(t.<business_date_field> as date)), '%Y%m%d'), '期')
) as qici
```

日历表建议维护为单 sheet 上传版本，至少包含：

| 字段 | 含义 |
|---|---|
| `biz_line` | 业务线，例如 `market_consultant` |
| `qici` | 业务期次，例如 `20260716期` |
| `start_date` | 期次开始日期 |
| `end_date` | 期次结束日期 |
| `status` | `active` / `inactive` |
| `remark` | 业务说明或变更原因 |

## 排查提醒

- 只改筛选器展示期次不够，必须同步检查看板表格维度、明细 `qici` 字段和当期/往期判断字段。
- 截面类字段要单独判断是否仍按期次截面表取数；暑期期次改动后，若截面表仍用周五期次，可能造成顾问架构、经理、小组错配。
- 当期/往期判断应依赖业务日历的 `qici` 或日期范围，不应依赖 `date_add(... day_of_week ...)` 推导出的周五期次。
- 2054 外呼过程数据本次删除末尾 `where valid_lead_count > 0`，目的是保留重分期后有效线索数为 0 的过程行，避免看板筛选期下分母或过程明细被提前过滤。
