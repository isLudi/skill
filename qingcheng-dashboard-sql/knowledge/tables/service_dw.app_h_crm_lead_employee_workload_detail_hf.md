# service_dw.app_h_crm_lead_employee_workload_detail_hf

## 1. 中文名称

CRM 线索员工工作量明细小时表

## 2. 表用途

在青橙过程数据 SQL 中作为外呼明细来源，计算通时、外呼次数、接通次数和长通话标记。

## 3. 数据粒度

待人工确认。当前 SQL 先 `select distinct` 外呼明细，再按 `user_number + lead_id + section_assign_employee_email_prefix` 聚合。

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
| 无直接青橙字段 | 通过青橙主表 join 限定 | 单独查询本表时必须补充员工/部门范围或从青橙主表驱动 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `user_number` | 待人工确认 | 用户编号 | join `data.user_id` |
| `lead_id` | 待人工确认 | 线索 ID | 外呼聚合粒度 |
| `section_assign_employee_email_prefix` | 待人工确认 | 截面分配员工邮箱前缀 | join `data.employee_email_prefix` |
| `call_duration` | 待人工确认 | 通话时长，疑似秒 | 大于 480 秒为长通话 |
| `call_status` | 待人工确认 | 呼叫状态 | `'1'` 为接通，`'1','0'` 计入外呼次数 |
| `call_time` | 待人工确认 | 呼叫时间 | 当前 SQL 取出用于 distinct |
| `call_type_name` | 待人工确认 | 呼叫类型 | 当前 SQL 取出用于 distinct |
| `data_source` | 待人工确认 | 数据来源 | 当前 SQL 取出用于 distinct |
| `msg_type_name` | 待人工确认 | 消息类型 | 当前 SQL 取出用于 distinct |

## 8. 常用过滤条件

```sql
where wf.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and wf.hour = format_datetime(now() - interval '2' hour, 'HH')
```

## 9. 常用 join key

- `user_number = data.user_id`
- `section_assign_employee_email_prefix = data.employee_email_prefix`

## 10. 常用 SQL 片段

```sql
sum(case when call_status in ('1','0') then 1 else 0 end) as zong_call_ci_1,
sum(case when call_status = '1' then 1 else 0 end) as call_status_1
```

## 11. 注意事项

- 本表当前 SQL 未直接过滤青橙部门，必须通过青橙主表 join 后限定范围。

