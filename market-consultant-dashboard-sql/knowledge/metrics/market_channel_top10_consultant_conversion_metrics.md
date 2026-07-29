# 市场渠道内 TOP10 顾问转化指标

## 1. 计算粒度

```text
ranking_grain = period_name + consultant_department + channel_map + employee_email_name
detail_grain  = ranking_grain + grade + rule_name
```

排名只能在 `ranking_grain` 计算。将排名窗口直接放在规则明细层会让同一顾问被重复参与排名。

## 2. 指标

| 字段 | 来源/表达式 | 用途 |
|---|---|---|
| `take_leads_den` | `sum(valid_lead_count)` 或已确认的渠道特殊有效线索口径 | 承接线索、单效分母、排名并列顺序 |
| `positive_head_users_num` | `sum(same_lead_period_conversion_lead_count)` | 当期正价课人头 |
| `positive_subject_orders_num` | `sum(same_lead_period_subject_count)` | 当期正价课科目人次 |
| `current_income_amt` | `sum(same_lead_period_income_amount) / 100` | 当期收款，元 |
| `current_net_gmv_num` | `sum(same_lead_period_income_amount - same_lead_period_refund_amount) / 100` | 当期净 GMV，排名主指标 |
| `top_rank` | 确定性 `row_number()` | 渠道内顾问名次 |

展示单效：

```text
sum(current_net_gmv_num) / sum(take_leads_den)
```

SQL 或 BI 不得平均顾问行级单效。

## 3. 待确认项

- `take_leads_den` 对抖音私域等特殊渠道是否使用合并有效线索口径。
- 排名是否保留净 GMV 为 0 或负数的顾问。
- 多期查询是“每期各排 TOP N”还是“整个周期累计排 TOP N”；必须在 QuerySpec 明确。
- 顾问学部字段版本和当前渠道映射版本必须与目标看板一致。
