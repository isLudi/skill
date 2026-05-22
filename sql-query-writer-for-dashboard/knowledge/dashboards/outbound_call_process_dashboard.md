# 外呼过程数据看板

## 1. 来源

原始 SQL：`resources/raw_sql/outbound_call_process_dashboard.sql`

入库时间：2026-05-01

最近更新：2026-05-22

## 2. 查询目标

按期次、规则、渠道、年级、架构、经理、小组、顾问和数据小时聚合外呼过程指标，用于观察市场顾问外呼跟进链路中的线索量、有效线索、首呼及时性、首呼接通及时性、外呼次数、接通次数、通话时长、长通话、加好友、APP 登录、深沟、双沟、已双沟方式、双表回收、异常流量、首 call 任务和首节到课表现。

## 3. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `dw.dim_cstm_active_user_c_appliction_mb_df` | `ul` | APP 日级活跃，取用户最近一次活跃应用并判断近 7 天登录 |
| `dw.dws_user_active_user_c_appliction_hf` | `h_ap` | APP 小时级活跃，补充最近 2 小时登录 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `f` | 主线索全链路明细，提供线索、有效线索、渠道、年级、分配、顾问、部门、深沟方式等字段 |
| `service_dw.dwd_crm_assign_private_detail_hf` | `t` | 私海阶段，补充当前销售阶段、深沟和双沟标记 |
| `service_dw.dm_crm_lead_stats_detail_hf` | `jt` | 线索统计，补充首呼接通时间差 |
| `service_dw.app_user_attribute_label_gaia_wide_df` | `yc` | 用户属性标签，补充异常流量标记 |
| `service_dw.app_h_crm_lead_task_process_info_detail_hf` | `sbb` | 取用户-顾问最新任务过程记录，补充双表发送/回收标记 |
| `service_dw.app_h_crm_lead_employee_workload_detail_hf` | `wf` | 顾问工作量明细，聚合外呼次数、接通次数、通话时长和长通话 |
| `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` | `first_call_task` | 顾问首 call 任务表，统计已完成首 call 任务标记 |
| `finance_dw.dim_finance_employee_df` | `employee_map` | 通过 `account_id` 将首 call 任务账号转换为顾问 `employee_email_name` |
| `service_dw.dws_service_user_learn_detail_hf` | `t2` | 行课学习明细，判断到课和有效到课 |
| `temp_table.dingxi01_jiagou_db` | `jg` | 稳定临时架构表，按期次和员工邮箱前缀补充部门、经理、小组 |
| `temp_table.dingxi01_daoke_1_6_t` | `ke` | 稳定临时课次映射表，按期次、渠道、年级、上课时间映射第几节课 |

## 4. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `d_ap` | 从日级 APP 活跃表取每个用户最新活跃记录，判断近 7 天是否 PC/APP 登录 | `user_number`, `is_app_denglu_d`, `event_timestamp` |
| `h_ap` | 从小时级 APP 活跃表判断最近 2 小时是否 PC/APP 登录 | `user_number`, `is_app_denglu_h` |
| `denglu_app` | 合并日级和小时级登录标记，生成最终 APP 登录标记 | `user_number`, `is_app_denglu` |
| `data` | 主线索明细，生成期次、渠道映射、年级、首呼时差、首呼接通时差、好友、深沟、双沟、已双沟方式、异常和双表回收标记 | `qici`, `channel_map_1`, `grade_1`, `first_call_time_diff_hour`, `first_call_connected_time_diff_hour_1`, `yi_shuanggou`, `yi_huishou` |
| `call_c` | 按用户、线索、顾问邮箱前缀聚合外呼工作量 | `call_duration_1`, `zong_call_ci_1`, `call_status_1`, `is_long_call` |
| `first_call_task` | 从首 call 任务表筛选顾问首 call 有效任务 | `user_id`, `account_id`, `first_call_status` |
| `employee_map` | 从员工维表按 `account_id` 取顾问姓名，并按目标部门范围限定 | `account_id`, `employee_email_name` |
| `f_call0` | 按顾问和用户聚合 CRM 首 call 已完成任务标记 | `assign_employee_email_name`, `user_id`, `completed_first_call_flag` |
| `daoke` | 将线索用户与行课明细、课次映射表关联后，按期次、用户、渠道预聚合到课和有效到课标记 | `qici`, `user_id`, `channel_map_1`, `has_daoke`, `has_v_daoke` |
| `prc` | 线索维度宽表，汇总首呼及时性分子、外呼过程指标、APP 登录、深沟、双沟、已双沟方式、异常、双表回收和首 call 标记 | `first_call_in_6h`, `first_call_connected_in_24h`, `zong_call_ci`, `call_status`, `yi_shuanggou`, `yi_huishou` |
| final select | 按看板维度聚合输出过程指标，并在最终层关联 `daoke` 计算到课人数 | `qici`, `rule_name`, `channel_map_1`, `grade_1`, `department`, `jingli`, `xiaozu`, `employee_email_name`, `datt`, `daoke1`, `v_daoke1` |

## 5. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| `d_ap` | `h_ap` | `d_ap.user_number = h_ap.user_number` | left join | 合并日级和小时级 APP 登录状态 |
| `bdg_ba... f` | `service_dw.dwd_crm_assign_private_detail_hf t` | `f.user_id = t.user_number` | left join | 补充最新私海销售阶段和深沟/双沟标记 |
| `bdg_ba... f` | `service_dw.dm_crm_lead_stats_detail_hf jt` | `f.lead_id = jt.lead_id` | left join | 补充首呼接通时间差 |
| `service_dw.app_user_attribute_label_gaia_wide_df yc` | `bdg_ba... f` | `yc.user_number = f.user_id` | left join | 补充异常流量标签 |
| `bdg_ba... f` | `service_dw.app_h_crm_lead_task_process_info_detail_hf sbb` | `sbb.assign_employee_email_name = f.employee_email_name` + `sbb.user_id = f.user_id` | left join | 补充双表发送标记，生成 `yi_huishou` |
| `data` | `temp_table.dingxi01_jiagou_db jg` | `data.employee_email_prefix = jg.employee_email_prefix` + `data.qici = jg.qici` | left join | 补充期次内顾问架构 |
| `data` | `call_c` | `call_c.user_number = data.user_id` + `call_c.section_assign_employee_email_prefix = data.employee_email_prefix` | left join | 补充外呼次数、接通次数、时长和长通话 |
| `data` | `denglu_app` | `denglu_app.user_number = data.user_id` | left join | 补充 APP 登录 |
| `first_call_task` | `employee_map` | `first_call_task.account_id = employee_map.account_id` | left join | 首 call 任务账号转顾问姓名 |
| `data` | `f_call0` | `f_call0.assign_employee_email_name = data.employee_email_name` + `f_call0.user_id = data.user_id` | left join | 补充首 call 任务数 |
| `data` | `service_dw.dws_service_user_learn_detail_hf t2` | `t1.qici = t2.qici` + `t1.user_id = t2.user_number` | inner join | 在 `daoke` CTE 中筛选线索用户对应的行课记录 |
| `daoke 内层` | `temp_table.dingxi01_daoke_1_6_t ke` | `t2.qici = ke.qici` + `t1.channel_map_1 = ke.qudao` + `t1.grade_1 = ke.grade` + `t2.begin_time = ke.begin_time` | left join | 将上课记录映射为第几节课，并只保留第 1/3 节 |
| `prc` | `daoke duf` | `prc.qici = duf.qici` + `prc.user_id = duf.user_id` + `prc.channel_map_1 = duf.channel_map_1` | left join | 最终聚合层计算到课和有效到课人数 |

## 6. where 条件

主线索表分区：

```sql
f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and f.hour = format_datetime(now() - interval '3' hour, 'HH')
```

主线索表范围限定：

```sql
f.section_assign_employee_first_level_department_name = 'H业务线'
and f.section_assign_employee_second_level_department_name = '市场部'
and f.section_assign_employee_third_level_department_name = '市场顾问部'
and f.period_mapping_first_level_department_name = 'H业务线'
and f.period_mapping_second_level_department_name in ('市场部', '精品班学部')
```

补充口径：市场顾问外呼看板允许主线索的期次映射二级部门为 `精品班学部`。如果截面分配顾问属于 `市场部/市场顾问部`，但 `period_mapping_second_level_department_name = '精品班学部'`，不应因此过滤掉该线索。

私海阶段范围限定：

```sql
assign_employee_first_level_department_name = 'H业务线'
and assign_employee_second_level_department_name = '市场部'
and assign_employee_third_level_department_name = '市场顾问部'
```

线索统计范围限定：

```sql
mapping_first_level_department_name = 'H业务线'
and mapping_second_level_department_name in ('精品班学部', '菁英班学部', '市场部', '本地化大班学部')
```

双表发送任务范围限定：

```sql
virtual_department_name_2 = 'H业务线'
and virtual_department_name_3 = '市场部'
```

首 call 任务范围限定：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and task_generate_rule_type = 2
and is_del = 0
and start_time > timestamp '2026-01-01 00:00:00'
```

首 call 员工维表范围限定：

```sql
dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
and first_level_department_name = 'H业务线'
and second_level_department_name in ('市场部','精品班学部','青橙项目部','菁英班学部')
```

如主查询只看市场顾问部，可继续补充 `third_level_department_name = '市场顾问部'`；如主查询需要所有二级部门，不要把员工维表硬编码为市场部。

行课范围限定：

```sql
course_first_level_department_name = 'H业务线'
and course_second_level_department_name in ('精品班学部', '市场部', '青橙项目部')
and is_need_attend = 1
```

最终结果过滤：

```sql
data.qici > '20260403期'
and data.virtual_third_department_name = '市场顾问部'
and jg.department is not null
and data.channel_map_1 not in ('未知', '线索复用', '训练营', '进校0元')
```

## 7. group by 维度

- `qici`
- `rule_name`
- `channel_map_1`
- `grade_1`
- `department`
- `jingli`
- `xiaozu`
- `employee_email_name`
- `datt`

## 8. 聚合指标

| 指标名 | SQL 表达式 | 口径说明 | 状态 |
|---|---|---|---|
| `lead_count` | `sum(lead_count)` | 线索数 | 来自看板 SQL |
| `valid_lead_count` | `sum(valid_lead_count)` | 有效线索数 | 来自看板 SQL |
| `first_call_time_diff_hour` | `sum(first_call_time_diff_hour)` | 首呼时差小时数求和 | 来自看板 SQL，聚合意义待确认 |
| `first_call_in_6h` | `sum(first_call_in_6h)` | 有效线索中 6 小时内首呼数 | 来自看板 SQL |
| `first_call_in_12h` | `sum(first_call_in_12h)` | 有效线索中 12 小时内首呼数 | 来自看板 SQL |
| `first_call_in_24h` | `sum(first_call_in_24h)` | 有效线索中 24 小时内首呼数 | 来自看板 SQL |
| `first_call_in_48h` | `sum(first_call_in_48h)` | 有效线索中 48 小时内首呼数 | 来自看板 SQL |
| `first_call_cnt` | `sum(first_call_cnt)` | 有效线索中 168 小时内首呼数 | 来自看板 SQL |
| `first_call_connected_in_24h` | `sum(first_call_connected_in_24h)` | 有效线索中 24 小时内首呼接通数 | 来自看板 SQL |
| `first_call_connected_in_48h` | `sum(first_call_connected_in_48h)` | 有效线索中 48 小时内首呼接通数 | 来自看板 SQL |
| `first_call_connected_cnt` | `sum(first_call_connected_cnt)` | 有效线索中 168 小时内首呼接通数 | 来自看板 SQL |
| `call_duration` | `sum(call_duration)` | 通话时长，`call_duration_1 / 60.00` 后求和，单位分钟 | 来自看板 SQL |
| `zong_call_ci` | `sum(zong_call_ci)` | 总外呼次数，`call_status in ('1','0')` | 来自看板 SQL |
| `call_status` | `sum(call_status)` | 接通次数，`call_status = '1'` | 来自看板 SQL |
| `is_long_call` | `sum(is_long_call)` | 有效线索中是否存在 300 秒以上通话的标记求和 | 来自看板 SQL |
| `is_friend_lead` | `sum(is_friend_lead)` | 有效线索加好友数 | 来自看板 SQL |
| `is_app_denglu` | `sum(is_app_denglu)` | APP/PC 登录人数标记求和 | 来自看板 SQL |
| `is_shengou` | `sum(is_shengou)` | 阶段为深沟或已双沟的线索数 | 来自看板 SQL |
| `is_shuanggou` | `sum(is_shuanggou)` | 阶段为已双沟的线索数 | 来自看板 SQL |
| `yi_shuanggou` | `sum(yi_shuanggou)` | 主表 `deep_communicate_method` 非空且有效线索的已双沟方式标记 | 新版新增，待业务确认命名 |
| `yi_huishou` | `sum(yi_huishou)` | `sbb.send_double_table = '是'` 且有效线索的双表发送/回收标记 | 新版新增，待业务确认命名 |
| `is_yichang` | `sum(is_yichang)` | 新线索、已建联、未成交阶段且存在异常流量标签的线索数 | 来自看板 SQL |
| `is_f_call` | `sum(is_f_call)` | CRM 首 call 任务数；首 call 任务表按 `first_call_status = 3` 聚合，`account_id` 转顾问姓名后用 `employee_email_name + user_id` 关联主数据 | 2026-05-22 更新口径 |
| `daoke1` | `count(distinct case when duf.has_daoke = 1 then prc.user_id end)` | 首节到课人数；曹忆IP99元按第 3 节，其余按第 1 节 | 新版改为最终层 distinct 用户数 |
| `v_daoke1` | `count(distinct case when duf.has_v_daoke = 1 then prc.user_id end)` | 首节有效到课人数；曹忆IP99元按第 3 节，其余按第 1 节 | 新版改为最终层 distinct 用户数 |

## 9. 与上一版差异

- 新增 `sbb` 关联：在 `data` CTE 中再次读取 `service_dw.app_h_crm_lead_task_process_info_detail_hf`，按 `user_id + assign_employee_email_name` 取 `trace_update_time` 最新的一条任务过程记录，用 `send_double_table = '是'` 生成 `yi_huishou`。该物理表仅保留双表发送/回收等任务过程用途，不能再用于 `is_f_call` 首 call 任务指标。
- 首 call 任务口径更新：`is_f_call` 改为读取 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`，以 `task_generate_rule_type = 2`、`is_del = 0` 和 `first_call_status = 3` 标记已完成任务；通过 `account_id` 关联 `finance_dw.dim_finance_employee_df` 得到 `employee_email_name`，再用 `employee_email_name + user_id` 关联主线索数据。
- 新增 `yi_shuanggou`：由主表 `deep_communicate_method` 非空且 `valid_lead_count = '1'` 得到，用于表达已双沟方式或深度沟通方式已填写的有效线索。
- 到课逻辑调整：旧版在 `prc` 内关联 `daoke` 并通过 `sum(case...)` 生成 `daoke1/v_daoke1`；新版先在 `daoke` CTE 按 `qici + user_id + channel_map_1` 预聚合 `has_daoke/has_v_daoke`，最终层用 `count(distinct prc.user_id)` 计算人数，降低重复行放大风险。
- 最终过滤调整：旧版文档记录过 `lead_count >= '2'` 过滤，新版原始 SQL 末尾未保留该过滤条件。
- 主线索范围调整：`period_mapping_second_level_department_name` 从仅限 `市场部` 调整为允许 `市场部` 和 `精品班学部`，用于覆盖截面分配在市场顾问部但期次映射归精品班学部的线索。

## 10. 可复用 SQL 模式

- APP 登录口径：日级最近一次活跃 + 小时级最近活跃合并，应用名限定 `PC客户端`、`APP`、`PC`。
- 期次口径：由 `group_period_year + group_period_term` 推出周五期次。
- 渠道口径：`channel_map_1` 使用超长 `rule_name` CASE，并结合 `flow_pool_name`、`get_customer_way_name`、`lead_purchase_intention_name` 兜底。
- 首呼及时性：对有效线索按 `section_assign_time` 到 `first_call_time` 的小时差生成 6/12/24/48/168 小时分子。
- 首呼接通及时性：对有效线索按 `section_assign_time` 到 `section_assign_first_call_connected_time` 的小时差生成 24/48/168 小时分子。
- 首 call 任务：必须使用 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` + `finance_dw.dim_finance_employee_df.account_id` 桥接，不得使用 `service_dw.app_h_crm_lead_task_process_info_detail_hf.call_answer_lead_count`。
- 长通话：单线索单顾问内只要存在 `call_duration > 300` 即计 1。
- 首节到课：一般渠道看 `ke_1 = '1'`，`曹忆IP99元` 看 `ke_1 = '3'`；新版最终层按用户去重计数。
- 双表回收：使用 `service_dw.app_h_crm_lead_task_process_info_detail_hf.send_double_table = '是'`，并限制有效线索。
- 结果缺失排查：当前外呼过程看板是事实主表 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 驱动，`temp_table.dingxi01_jiagou_db` 只用于补充架构。若某未来期次在架构表已维护但主表派生期次无数据，最终看板不会展示该期次。

## 11. 待确认事项

- 主表 `dt` 使用最近 2 小时，但 `hour` 使用最近 3 小时；需确认是否为平台产出延迟口径。
- `coalesce(is_app_denglu_h, 0) = '1'`、`valid_lead_count = '1'`、`is_valid_live_learn = '1'` 存在数值/字符串混用，需按字段类型确认。
- `first_call_time_diff_hour` 在最终层直接求和，通常不适合作为平均首呼时长展示；若要展示时长水平，建议另建 `avg` 或分子/分母口径。
- `data` CTE 使用 `select distinct f.*`，宽表扫描成本较高；生产查询建议只选看板所需字段。
- `call_c` 未单独限定部门范围，依赖与 `data` 的用户/顾问关联收敛结果；复用时需确认是否可能带入跨部门外呼。
- `f_call0` 首 call 任务需在员工维表 `employee_map` 中使用与主查询一致的一级/二级/三级部门范围；查询所有二级部门时不要硬编码为仅市场部。
- `sbb` 子查询按 `user_id + assign_employee_email_name` 取最新任务过程，但未使用 `qici` join 主表；需确认跨期最新任务是否会影响 `yi_huishou`。
- `temp_table.dingxi01_jiagou_db` 按 `qici + employee_email_prefix` join，需确认该键在临时表中唯一，避免行放大。
- 若业务要求提前展示已维护但事实主表未产出的未来期次架构人员，需要改为架构表驱动 left join 指标，并调整最终 `valid_lead_count > 0` 过滤；该变更属于展示口径调整，需人工确认。
- 渠道 CASE 为历史看板内嵌规则，完整规则以原始 SQL 为准；后续可拆成独立渠道映射知识或维护表。
- 所有指标口径来自历史看板 SQL，尚未经过业务口径文档确认。
