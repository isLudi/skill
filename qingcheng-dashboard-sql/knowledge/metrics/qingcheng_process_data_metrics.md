# 青橙过程数据指标

## 1. 来源

`resources/raw_sql/qingcheng_process_data_raw_20260522.sql`

适用看板：`knowledge/dashboards/qingcheng_process_data_raw_20260522.md`

## 2. 指标计算粒度

本 SQL 先在 `prc` CTE 中构造线索过程指标，近似粒度为：

```text
期次 + 分配日期 + 规则 + 渠道 + 年级 + 架构 + 员工 + user_id
```

最终输出粒度为：

```text
期次 + 分配日期 + 规则 + 渠道 + 年级 + 架构 + 员工
```

## 3. 基础线索指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `v_lead` | `case when f.valid_lead_count = '1' then 1 else 0 end`，最终 `sum(v_lead)` | 有效线索数 | 已从 SQL 入库 |
| `is_friend_lead` | `case when f.valid_lead_count = '1' then f.friend_lead_count else 0 end`，最终 `sum(is_friend_lead)` | 有效线索中的加微数 | 已从 SQL 入库 |

## 4. 首次触达指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `first_call_time_diff_hour` | `date_diff('hour', cast(f.section_assign_time as timestamp), cast(f.first_call_time as timestamp))`，最终被 `sum` | 首次触达时间差小时数；直接求和的业务意义待确认 | 待人工确认 |
| `first_call_in_24h` | `first_call_time_diff_hour between 0 and 24 and valid_lead_count > 0` | 24 小时内触达线索数 | 已从 SQL 入库 |
| `first_call_in_48h` | `first_call_time_diff_hour between 0 and 48 and valid_lead_count > 0` | 48 小时内触达线索数 | 已从 SQL 入库 |
| `first_call_cnt` | `first_call_time_diff_hour between 0 and 168 and valid_lead_count > 0` | 168 小时内触达线索数 | 已从 SQL 入库 |

## 5. 首次沟通指标

`first_call_connected_time_diff_hour_1` 来自 `service_dw.dm_crm_lead_stats_detail_hf`：

```sql
date_diff(
    'hour',
    cast(section_assign_time as timestamp),
    cast(section_assign_first_call_connected_time as timestamp)
)
```

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `first_call_connected_in_24h` | `first_call_connected_time_diff_hour_1 between 0 and 24 and valid_lead_count > 0` | 24 小时内首次接通/沟通线索数 | 已从 SQL 入库 |
| `first_call_connected_in_48h` | `first_call_connected_time_diff_hour_1 between 0 and 48 and valid_lead_count > 0` | 48 小时内首次接通/沟通线索数 | 已从 SQL 入库 |
| `first_call_connected_cnt` | `first_call_connected_time_diff_hour_1 between 0 and 168 and valid_lead_count > 0` | 168 小时内首次接通/沟通线索数 | 已从 SQL 入库 |

## 6. 外呼指标

外呼指标先在 `call_c` 中按 `user_number + lead_id + section_assign_employee_email_prefix` 聚合，再 join 到青橙线索。

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `call_duration` | `sum(call_duration) / 60.00` 后最终 `sum(call_duration)` | 外呼总通时，单位分钟 | 已从 SQL 入库 |
| `is_long_call` | `max(case when call_duration > 480 then 1 else 0 end)` 后最终 `sum(is_long_call)` | 是否存在单次通话超过 480 秒；最终为长通话线索/组合数 | 已从 SQL 入库 |
| `zong_call_ci` | `sum(case when call_status in ('1','0') then 1 else 0 end)` | 外呼总次数 | 已从 SQL 入库 |
| `call_status` | `sum(case when call_status = '1' then 1 else 0 end)` | 外呼接通次数 | 已从 SQL 入库 |

## 7. APP/PC 登录指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `is_app_denglu_d` | 最近登录时间在近 7 天内，且 `appliction_name in ('PC客户端','APP','PC')` | 天级 APP/PC 登录标记 | 已从 SQL 入库 |
| `is_app_denglu_h` | 小时表中 `application_name in ('PC客户端','APP','PC')` | 小时级 APP/PC 登录标记 | 已从 SQL 入库 |
| `is_app_denglu` | 天级或小时级任一为 1 | 最终 APP/PC 登录标记，按线索 join 后汇总 | 已从 SQL 入库 |

注意：原 SQL 使用 `coalesce(is_app_denglu_h,0) = '1'`，存在数字与字符串比较。后续生成新 SQL 时建议改成 `= 1`。

## 8. 首节到课指标

首节课判断依赖 `temp_table.dingxi01_qing_daoke` 的 `ke_1 = '1'`。

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `daoke1` | `ke_1 = '1' and live_learn_duration > 0`，同一分组内大于 0 则记 1 | 首节到课 | 已从 SQL 入库 |
| `valid_daoke_1` | `ke_1 = '1' and is_valid_live_learn = '1'`，同一分组内大于 0 则记 1 | 首节有效到课 | 已从 SQL 入库 |

## 9. 待确认事项

- `first_call_time_diff_hour` 最终求和是否应作为指标输出待确认；更常见可能是平均值、中位数或分桶。
- “剔除线索量<2”是否应加入最终 `having sum(v_lead) >= 2` 待确认。
- `valid_lead_count`、`friend_lead_count` 在主表中是字符串还是数值待表结构确认；当前 SQL 同时存在字符串和数值比较。
- APP 登录按 `user_id = user_number` join 到线索，若一名用户多条线索，汇总 `is_app_denglu` 可能按线索放大；前端聚合需注意。

