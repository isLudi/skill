# 外呼过程数据看板指标

## 1. 中文名称

外呼过程数据看板指标集合

## 2. 指标定义

指标来自 `resources/raw_sql/outbound_call_process_dashboard.sql` 的 `prc` CTE 和最终聚合层。当前状态为“历史看板 SQL 口径”，未与业务指标文档核对。2026-05-22 起，`is_f_call` 首 call 任务指标强制改用 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` 加员工维表桥接，不能再从旧过程表 `service_dw.app_h_crm_lead_task_process_info_detail_hf.call_answer_lead_count` 取数。

## 3. SQL 表达式

| 指标名 | SQL 表达式 | 说明 |
|---|---|---|
| `lead_count` | `sum(lead_count)` | 线索数 |
| `valid_lead_count` | `sum(valid_lead_count)` | 有效线索数 |
| `first_call_time_diff_hour` | `sum(first_call_time_diff_hour)` | 首呼时差小时数求和 |
| `first_call_in_6h` | `sum(case when first_call_time_diff_hour <= 6 and valid_lead_count > 0 then 1 else 0 end)` | 6 小时内首呼有效线索数 |
| `first_call_in_12h` | `sum(case when first_call_time_diff_hour <= 12 and valid_lead_count > 0 then 1 else 0 end)` | 12 小时内首呼有效线索数 |
| `first_call_in_24h` | `sum(case when first_call_time_diff_hour <= 24 and valid_lead_count > 0 then 1 else 0 end)` | 24 小时内首呼有效线索数 |
| `first_call_in_48h` | `sum(case when first_call_time_diff_hour <= 48 and valid_lead_count > 0 then 1 else 0 end)` | 48 小时内首呼有效线索数 |
| `first_call_cnt` | `sum(case when first_call_time_diff_hour <= 168 and valid_lead_count > 0 then 1 else 0 end)` | 168 小时内首呼有效线索数 |
| `first_call_connected_in_24h` | `sum(case when first_call_connected_time_diff_hour_1 <= 24 and valid_lead_count > 0 then 1 else 0 end)` | 24 小时内首呼接通有效线索数 |
| `first_call_connected_in_48h` | `sum(case when first_call_connected_time_diff_hour_1 <= 48 and valid_lead_count > 0 then 1 else 0 end)` | 48 小时内首呼接通有效线索数 |
| `first_call_connected_cnt` | `sum(case when first_call_connected_time_diff_hour_1 <= 168 and valid_lead_count > 0 then 1 else 0 end)` | 168 小时内首呼接通有效线索数 |
| `call_duration` | `sum(round(coalesce(call_duration_1, 0) / 60.00, 2))` | 通话时长，秒转分钟后聚合 |
| `zong_call_ci` | 底层 `sum(case when call_status in ('1','0') then 1 else 0 end)`，最终 `sum(zong_call_ci)` | 总外呼次数，底层按线索、用户、顾问聚合后再汇总 |
| `call_status` | 底层 `sum(case when call_status = '1' then 1 else 0 end)`，最终 `sum(call_status)` | 外呼接通次数 |
| `is_long_call` | `sum(case when valid_lead_count > 0 then max(case when call_duration > 300 then 1 else 0 end) else 0 end)` | 有效线索中存在 300 秒以上通话的标记求和 |
| `is_friend_lead` | `sum(case when valid_lead_count = '1' then friend_lead_count else 0 end)` | 有效线索加好友数 |
| `is_app_denglu` | `sum(case when is_app_denglu_d = 1 or is_app_denglu_h = 1 then 1 else 0 end)` | APP/PC 登录标记求和 |
| `is_shengou` | `sum(case when jieduan in ('深沟', '已双沟') then 1 else 0 end)` | 深沟或已双沟线索数 |
| `is_shuanggou` | `sum(case when jieduan = '已双沟' then 1 else 0 end)` | 已双沟线索数 |
| `yi_shuanggou` | `sum(case when deep_communicate_method is not null and deep_communicate_method != '' and valid_lead_count = '1' then 1 else 0 end)` | 有效线索中深度沟通方式非空的已双沟方式标记 |
| `is_yichang` | `sum(case when abnormal_traffic is not null and abnormal_traffic != '' and sale_flow_stage_name_1 in ('新线索','已建联','未成交') then 1 else 0 end)` | 指定阶段中存在异常流量标签的线索数 |
| `yi_huishou` | `sum(case when send_double_table = '是' and valid_lead_count = '1' then 1 else 0 end)` | 有效线索中双表发送/回收标记 |
| `is_f_call` | `sum(case when valid_lead_count = 1 then completed_first_call_flag else 0 end)` | CRM 首 call 任务数；`completed_first_call_flag` 来自首 call 任务表按 `user_id + employee_email_name` 聚合后的已完成任务标记 |
| `daoke1` | `count(distinct case when duf.has_daoke = 1 then prc.user_id end)` | 首节到课人数；曹忆IP99元按第 3 节，其余按第 1 节 |
| `v_daoke1` | `count(distinct case when duf.has_v_daoke = 1 then prc.user_id end)` | 首节有效到课人数；曹忆IP99元按第 3 节，其余按第 1 节 |

## 4. 适用表

- `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- `service_dw.app_h_crm_lead_employee_workload_detail_hf`
- `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`
- `finance_dw.dim_finance_employee_df`
- `service_dw.app_h_crm_lead_task_process_info_detail_hf`，仅用于双表发送/回收、任务过程等非首 call 任务指标；禁止用于 `is_f_call`
- `service_dw.dm_crm_lead_stats_detail_hf`
- `service_dw.dwd_crm_assign_private_detail_hf`
- `service_dw.dws_service_user_learn_detail_hf`
- `dw.dim_cstm_active_user_c_appliction_mb_df`
- `dw.dws_user_active_user_c_appliction_hf`
- `service_dw.app_user_attribute_label_gaia_wide_df`
- `temp_table.dingxi01_jiagou_db`
- `temp_table.dingxi01_daoke_1_6_t`

## 5. 分母/分子口径

- 首呼及时率可用 `first_call_in_6h`、`first_call_in_12h`、`first_call_in_24h`、`first_call_in_48h` 或 `first_call_cnt` 作为分子，`valid_lead_count` 作为分母。
- 首呼接通及时率可用 `first_call_connected_in_24h`、`first_call_connected_in_48h` 或 `first_call_connected_cnt` 作为分子，`valid_lead_count` 作为分母。
- 首 call 任务率使用 `sum(is_f_call) / sum(valid_lead_count)`；`is_f_call` 必须来自 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` 的 `first_call_status = 3` 完成任务标记，先通过 `account_id` 关联 `finance_dw.dim_finance_employee_df` 得到 `employee_email_name`，再用 `employee_email_name + user_id` 关联主线索数据。
- 外呼接通率可用 `call_status / zong_call_ci`。
- 长通话率可用 `is_long_call / valid_lead_count`。
- 加好友率可用 `is_friend_lead / valid_lead_count`。
- APP 登录率可用 `is_app_denglu / valid_lead_count` 或按业务指定线索分母计算。
- 深沟率、双沟率、已双沟方式率、双表回收率、异常率、首节到课率、有效到课率的分母未在 SQL 中显式输出，复用时需按看板展示口径选择 `lead_count` 或 `valid_lead_count`。

## 6. 时间口径

主要分区：

```sql
f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and f.hour = format_datetime(now() - interval '3' hour, 'HH')
```

小时表分区多使用：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
```

日表分区多使用：

```sql
dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
```

最终期次过滤：

```sql
data.qici > '20260403期'
```

## 7. 范围限定

主线索范围：

```sql
section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name = '市场部'
and virtual_third_department_name = '市场顾问部'
and period_mapping_first_level_department_name = 'H业务线'
and period_mapping_second_level_department_name in ('市场部', '精品班学部')
```

补充口径：市场顾问外呼看板允许主线索 `period_mapping_second_level_department_name = '精品班学部'`；不要仅因期次映射二级部门不是 `市场部` 排除截面分配在市场顾问部的线索。

私海阶段范围：

```sql
assign_employee_first_level_department_name = 'H业务线'
and assign_employee_second_level_department_name = '市场部'
and assign_employee_third_level_department_name = '市场顾问部'
```

线索统计范围：

```sql
mapping_first_level_department_name = 'H业务线'
and mapping_second_level_department_name in ('精品班学部', '菁英班学部', '市场部', '本地化大班学部')
```

双表发送任务范围：

```sql
virtual_department_name_2 = 'H业务线'
and virtual_department_name_3 = '市场部'
```

## 8. 待人工确认

是。需要确认主表 `dt/hour` 偏移是否为平台延迟口径、数值/字符串比较是否符合字段类型、首呼时差求和是否有展示意义、首 call 员工维表范围是否与主查询部门范围一致、`sbb` 最新任务是否会跨期影响 `yi_huishou`、架构临时表 join key 是否唯一，以及渠道映射 CASE 是否仍为最新规则。
