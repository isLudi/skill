# service_dw.app_h_crm_lead_task_process_info_detail_hf

## 1. 中文名称

CRM 线索任务处理信息明细小时表

## 2. 表用途

在青橙转化宽表-市场渠道 SQL 中作为首次外呼数据来源，用于标记线索是否有 F 类外呼记录（`is_f_call`）。

## 3. 数据粒度

待人工确认。当前 SQL 按 `flow_order_period_name + assign_employee_email_name + user_id + call_answer_lead_count（作为 lead_id）` 使用 `select distinct`。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | 待人工确认 | 日期分区 |
| `hour` | 待人工确认 | 小时分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `dt` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | 最新日期快照 |
| `hour` | `format_datetime(now() - interval '3' hour, 'HH')` | 小时偏移与主表不同（主表 -2h，本表 -3h），原因待确认 |

## 7. 字段清单

以下字段基于本 SQL 实际使用情况整理，完整字段清单待表结构确认。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `dt` | 待人工确认 | 日期分区 | 必加 |
| `hour` | 待人工确认 | 小时分区 | 建议加 |
| `flow_order_period_name` | 待人工确认 | 订单期次名称 | 格式如 `2026YYMM期`，用于拼接 `period_name` |
| `assign_employee_email_name` | 待人工确认 | 分配员工邮箱名 | join key，对应宽表的 `employee_email_name` |
| `user_id` | 待人工确认 | 用户 ID | join key |
| `call_answer_lead_count` | 待人工确认 | 外呼接通线索数/线索 ID | 本 SQL 中作为 `lead_id` 使用，语义待确认 |
| `period_create_time` | 待人工确认 | 期次创建时间 | 过滤条件 `> '2026-01-01'` |
| `is_refund_before_clazz_begin` | 待人工确认 | 是否课前退款 | 过滤条件 `= 0`，排除课前退款 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '3' hour, 'HH')
  and period_create_time > '2026-01-01'
  and is_refund_before_clazz_begin = 0
  and call_answer_lead_count is not null
```

## 9. 常用 join key

- `assign_employee_email_name`（对应宽表的 `employee_email_name`）
- `user_id`
- `call_answer_lead_count`（本 SQL 中作为 `lead_id` 使用，对应宽表的 `lead_id`）
- `flow_order_period_name`（拼接后对应 `period_name`）

## 10. 常用 SQL 片段

```sql
select distinct
    concat(substr(flow_order_period_name, 1, 4), substr(flow_order_period_name, 7, 4), '期') as period_name,
    assign_employee_email_name,
    user_id,
    call_answer_lead_count as lead_id,
    1 as is_f_call
from service_dw.app_h_crm_lead_task_process_info_detail_hf
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '3' hour, 'HH')
  and period_create_time > '2026-01-01'
  and is_refund_before_clazz_begin = 0
  and call_answer_lead_count is not null
```

## 11. 注意事项

- 本表在青橙知识库中首次入库，字段含义均来源于历史 SQL 推断，需表结构确认。
- `call_answer_lead_count` 字段名暗示为"计数"类型，但本 SQL 将其作为 `lead_id`（标识符）使用，语义存在矛盾，待确认。
- 本表 hour 使用 `now()-3h`，与其他表（主表 `now()-2h`）偏移不同，可能是数据延迟差异。
- `flow_order_period_name` 格式假设为 `YYYYMMdd期` 或类似格式，通过 `substr(1,4) + substr(7,4)` 拼接，若格式变化会导致 `period_name` 解析错误。
- 本表目前仅在转化宽表-市场渠道 SQL 中使用，是否可用于其他青橙看板待确认。
