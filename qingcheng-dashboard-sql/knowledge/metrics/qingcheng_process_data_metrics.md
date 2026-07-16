# 青橙过程数据指标

## 1. 来源

当前生产权威 SQL：`resources/raw_sql/data_center_qingcheng_2064.sql`

适用看板：`过程数据报表-青橙`、`青橙-渠道过程数据-天`

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

历史累计外呼指标先在 `call_c` 中按 `user_number + lead_id + section_assign_employee_email_prefix` 聚合，再 join 到青橙线索。正常线索历史字段仍保留原有宽关联兼容逻辑；新增 14 天指标不得复用该宽关联。

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `call_duration` | `sum(call_duration) / 60.00` 后最终 `sum(call_duration)` | 外呼总通时，单位分钟 | 已从 SQL 入库 |
| `is_long_call` | `max(case when call_duration > 480 then 1 else 0 end)` 后最终 `sum(is_long_call)` | 是否存在单次通话超过 480 秒；最终为长通话线索/组合数 | 已从 SQL 入库 |
| `zong_call_ci` | `sum(case when call_status in ('1','0') then 1 else 0 end)` | 外呼总次数 | 已从 SQL 入库 |
| `call_status` | `sum(case when call_status = '1' then 1 else 0 end)` | 外呼接通次数 | 已从 SQL 入库 |

## 7. 14 天过程指标

14 天统一定义为从线索分配时间 `section_assign_timestamp` 起，事件时间差满足 `date_diff('hour', section_assign_timestamp, event_time) between 0 and 336`。SQL 只输出可加总的分子、分母或累计值，不直接输出比率型指标。

外呼事件来自 `service_dw.app_h_crm_lead_employee_workload_detail_hf`，必须使用精确键：

```text
call_detail.user_number = data.user_id
+ call_detail.lead_id = data.process_lead_id
+ call_detail.section_assign_employee_email_prefix = data.employee_email_prefix
```

这条精确 `lead_id` 门禁用于避免同一用户、同一顾问下存在多条线索时发生外呼串数。

| 最终 select 字段 | SQL 口径 | 看板用途 |
|---|---|---|
| `first_call_cnt_14d` | 首次外呼距分配时间 `0-336` 小时且为有效线索时记 1 | 14 天首 call 率分子 |
| `first_call_connected_cnt_14d` | 首次接通距分配时间 `0-336` 小时且为有效线索时记 1 | 14 天沟通率分子 |
| `v_lead_14d_denominator` | 复用有效线索标记 `v_lead` | 14 天首 call 率、沟通率、8min、外呼时长、外呼频次的共同分母 |
| `is_long_call_14d` | 分配后 `0-336` 小时内存在单次 `call_duration > 480` 秒时，在线索键粒度取 `max(flag)` | 14 天 8min 人数；同时作为 14 天 8min 率分子 |
| `call_duration_14d` | 分配后 `0-336` 小时内 `call_status in ('1','0')` 的通话秒数求和后除以 60 | 14 天总通时；同时作为 14 天人均外呼时长分子，单位分钟 |
| `zong_call_ci_14d` | 分配后 `0-336` 小时内 `call_status in ('1','0')` 的外呼事件数 | 14 天人均外呼频次分子 |

看板公式必须使用“聚合后相除”，禁止逐行比率再求平均：

```text
14天首call率 = sum(first_call_cnt_14d) / sum(v_lead_14d_denominator)
14天沟通率 = sum(first_call_connected_cnt_14d) / sum(v_lead_14d_denominator)
14天8min人数 = sum(is_long_call_14d)
14天8min = sum(is_long_call_14d) / sum(v_lead_14d_denominator)
14天外呼时长 = sum(call_duration_14d) / sum(v_lead_14d_denominator)
14天外呼频次 = sum(zong_call_ci_14d) / sum(v_lead_14d_denominator)
14天总通时 = sum(call_duration_14d)
```

2026-07-16 渠道级全量校验 query id `1477067724`：所有期次/渠道的分子均未超过分母，新增字段无负值，`invalid_flag=0`。生产 Preview task id `1477125780`，最终输出 35 列；新抽数记录 `159190210` 为 `SUCCESS`。

## 8. APP/PC 登录指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `is_app_denglu_d` | 最近登录时间在近 7 天内，且 `appliction_name in ('PC客户端','APP','PC')` | 天级 APP/PC 登录标记 | 已从 SQL 入库 |
| `is_app_denglu_h` | 小时表中 `application_name in ('PC客户端','APP','PC')` | 小时级 APP/PC 登录标记 | 已从 SQL 入库 |
| `is_app_denglu` | 天级或小时级任一为 1 | 最终 APP/PC 登录标记，按线索 join 后汇总 | 已从 SQL 入库 |

注意：原 SQL 使用 `coalesce(is_app_denglu_h,0) = '1'`，存在数字与字符串比较。后续生成新 SQL 时建议改成 `= 1`。

## 9. 首节到课指标

首节课判断依赖 `temp_table.dingxi01_qing_daoke` 的 `ke_1 = '1'`。

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `daoke1` | `ke_1 = '1' and live_learn_duration > 0`，同一分组内大于 0 则记 1 | 首节到课 | 已从 SQL 入库 |
| `valid_daoke_1` | `ke_1 = '1' and is_valid_live_learn = '1'`，同一分组内大于 0 则记 1 | 首节有效到课 | 已从 SQL 入库 |

## 10. 待确认事项

- `first_call_time_diff_hour` 最终求和是否应作为指标输出待确认；更常见可能是平均值、中位数或分桶。
- “剔除线索量<2”是否应加入最终 `having sum(v_lead) >= 2` 待确认。
- `valid_lead_count`、`friend_lead_count` 在主表中是字符串还是数值待表结构确认；当前 SQL 同时存在字符串和数值比较。
- APP 登录按 `user_id = user_number` join 到线索，若一名用户多条线索，汇总 `is_app_denglu` 可能按线索放大；前端聚合需注意。
