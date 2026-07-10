# 青橙过程数据 raw

## 1. 来源

`resources/raw_sql/qingcheng_process_data_raw_20260522.sql`

入库时间：2026-05-22

## 2. 查询目标

沉淀青橙项目部过程数据看板 SQL。该 SQL 将青橙有效线索按期次、分配日期、规则、渠道、年级、架构和员工聚合，输出线索、加微、首次触达、首次沟通、外呼、APP 登录、首节到课和有效到课等过程指标。

## 3. 最终输出粒度

| 维度 | 字段 |
|---|---|
| 期次 | `qici` |
| 规则 | `rule_name` |
| 分配日期 | `assign_day` |
| 一级渠道 | `channel_map_1` |
| 二级渠道 | `channel_map_2` |
| 年级 | `grade_1` |
| 架构 | `department`, `dept_2`, `xiaozu` |
| 员工 | `employee_email_name` |

注意：SQL 注释写有“剔除线索量<2”，但最终查询未看到 `v_lead >= 2` 或类似过滤条件。后续复用时必须确认是否需要补充该剔除逻辑。

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `f` / `data` | 青橙有效线索主表，提供分配、渠道、年级、员工、期次和部分过程字段 |
| `service_dw.dm_crm_lead_stats_detail_hf` | `jt` | 补充首次接通时间差 |
| `service_dw.app_h_crm_lead_employee_workload_detail_hf` | `wf` / `call_c` | 外呼明细，聚合外呼次数、接通次数、通时和长通话 |
| `service_dw.dws_service_user_learn_detail_hf` | `t2` / `daoke` | 用户上课明细，用于首节到课和有效到课 |
| `dw.dim_cstm_active_user_c_appliction_mb_df` | `d_ap` | APP/PC 天级最近登录状态 |
| `dw.dws_user_active_user_c_appliction_hf` | `h_ap` | APP/PC 小时级登录状态 |

## 5. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.dingxi01_qing_daoke` | 青橙首节课映射表，按期次、二级渠道、年级和开课时间标记 `ke_1` | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_jiagou_db` | 青橙架构映射表，按期次和员工姓名补充 `department`、`dept_2`、`xiaozu` | 已从 SQL 入库，来源/刷新方式待人工确认 |

## 6. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `d_ap` | 取用户最近一次天级 APP/PC 登录，并判断近 7 天是否登录 | `user_number`, `last_event_time`, `appliction_name`, `is_app_denglu_d` |
| `h_ap` | 取近 2 小时小时级 APP/PC 登录状态 | `user_number`, `application_name`, `is_app_denglu_h` |
| `denglu_app` | 合并天级和小时级登录状态 | `user_number`, `is_app_denglu` |
| `data` | 青橙有效线索基础层，生成期次、渠道、年级、首次触达/接通时间差、有效线索和加微字段 | `lead_id`, `user_id`, `employee_email_prefix`, `employee_email_name`, `qici`, `channel_map_1`, `channel_map_2`, `grade_1`, `v_lead` |
| `call_c` | 外呼明细按用户、线索、顾问聚合 | `user_number`, `lead_id`, `section_assign_employee_email_prefix`, `call_duration_1`, `zong_call_ci_1`, `call_status_1`, `is_long_call` |
| `daoke` | 将青橙线索与上课明细和首节课临时表匹配 | `qici`, `employee_email_prefix`, `lead_id`, `user_id`, `begin_time`, `live_learn_duration`, `is_valid_live_learn`, `ke_1` |
| `prc` | 线索粒度过程指标层，补充架构、外呼、登录、到课标记 | 最终聚合前的全部过程指标 |

## 7. 青橙范围限定

| 位置 | 范围字段 | 取值 |
|---|---|---|
| `data` 主表 | `f.section_assign_employee_first_level_department_name` | `'H业务线'` |
| `data` 主表 | `f.section_assign_employee_second_level_department_name` | `'青橙项目部'` |
| `data` 主表 | `f.period_mapping_first_level_department_name` | `'H业务线'` |
| `data` 主表 | `f.period_mapping_second_level_department_name` | `('精品班学部','青橙项目部')` |
| `jt` 线索状态表 | `mapping_first_level_department_name` | `'H业务线'` |
| `jt` 线索状态表 | `mapping_second_level_department_name` | `('精品班学部','菁英班学部','市场部','本地化大班学部','青橙项目部')` |
| `daoke` 上课明细 | `course_first_level_department_name` | `'H业务线'` |
| `daoke` 上课明细 | `course_second_level_department_name` | `('精品班学部','市场部','青橙项目部')` |
| `prc` 最终线索层 | `data.virtual_second_department_name` | `'青橙项目部'` |

## 8. 分区和小时条件

| 表/CTE | dt 条件 | hour 条件 | 说明 |
|---|---|---|---|
| `dw.dim_cstm_active_user_c_appliction_mb_df` | `format_datetime(now() - interval '24' hour, 'YYYYMMdd')` | 无 | 天级表 |
| `dw.dws_user_active_user_c_appliction_hf` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | `format_datetime(now() - interval '2' hour, 'HH')` | 小时级 APP 登录 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | `format_datetime(now() - interval '3' hour, 'HH')` | 主表使用 T-2 日分区但 T-3 小时，原因待确认 |
| `service_dw.dm_crm_lead_stats_detail_hf` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | `format_datetime(now() - interval '2' hour, 'HH')` | 首次接通补充表 |
| `service_dw.app_h_crm_lead_employee_workload_detail_hf` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | `format_datetime(now() - interval '2' hour, 'HH')` | 外呼明细 |
| `service_dw.dws_service_user_learn_detail_hf` | `date_format(now() - interval '2' hour, '%Y%m%d')` | `date_format(now() - interval '2' hour, '%H')` | 上课明细 |

## 9. join 关系

| 左侧 | 右侧 | join key | 用途 |
|---|---|---|---|
| `d_ap` | `h_ap` | `d_ap.user_number = h_ap.user_number` | 合并天级和小时级登录 |
| `f` | `jt` | `f.lead_id = jt.lead_id` | 补充首次接通时间差 |
| `data` | `temp_table.dingxi01_jiagou_db jg` | `data.employee_email_name = jg.employee_email_name and data.qici = jg.qici` | 补充青橙架构 |
| `data` | `daoke` | `data.employee_email_prefix = daoke.employee_email_prefix and data.qici = daoke.qici and data.lead_id = daoke.lead_id` | 匹配首节到课 |
| `call_c` | `data` | `call_c.user_number = data.user_id and call_c.section_assign_employee_email_prefix = data.employee_email_prefix` | 匹配外呼指标 |
| `denglu_app` | `data` | `denglu_app.user_number = data.user_id` | 匹配 APP 登录 |
| `t1` | `t2` | `t1.qici = t2.qici and t1.user_id = t2.user_number` | 匹配用户上课明细 |
| `dk` | `temp_table.dingxi01_qing_daoke ke` | `dk.qici = ke.qici and dk.channel_map_2 = ke.qudao and dk.grade_1 = ke.grade and dk.begin_time = ke.begin_time` | 标记首节课 |

## 10. 渠道和年级映射

详细 CASE 口径沉淀到 `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`。

核心规则：

- 当前 2064 权威快照中，`%抖音正价退费%` 在 `channel_map_1`、`channel_map_2` 均映射为 `抖音复用`；两级必须成对维护，否则最终非空门禁会丢失该渠道数据。
- `channel_map_1` 其余规则按 `rule_name` 映射为青橙私域、青橙IP、青橙公海、青橙公域、青橙图书、青橙本地化、抖音私信、进校、青橙训练营。
- `channel_map_2` 其余规则进一步细分私域表单、私域图书、私域裂变、私域品效、私域IE、私域本地化、亚飞IP、SEC未加好友、SEC首期掉海、顾问未加好友、郑州图书、武汉图书、西安图书、图书咨询、公域学霸、南京、抖音私信、进校9元、青橙训练营。
- `grade_1` 优先从 `rule_name` 识别高一、高二、高三、初二、初三，否则使用 `lead_purchase_intention_level2_category_name`。

## 11. 聚合指标

指标集合沉淀到 `knowledge/metrics/qingcheng_process_data_metrics.md`。

本看板最终输出以下聚合指标：

| 指标 | 表达式 | 口径简述 |
|---|---|---|
| `v_lead` | `sum(v_lead)` | 有效线索数 |
| `is_friend_lead` | `sum(is_friend_lead)` | 有效线索中的加微数 |
| `first_call_in_24h` | `sum(first_call_in_24h)` | 分配后 24 小时内首次触达数 |
| `first_call_in_48h` | `sum(first_call_in_48h)` | 分配后 48 小时内首次触达数 |
| `first_call_cnt` | `sum(first_call_cnt)` | 分配后 168 小时内首次触达数 |
| `first_call_connected_in_24h` | `sum(first_call_connected_in_24h)` | 分配后 24 小时内首次接通数 |
| `first_call_connected_in_48h` | `sum(first_call_connected_in_48h)` | 分配后 48 小时内首次接通数 |
| `first_call_connected_cnt` | `sum(first_call_connected_cnt)` | 分配后 168 小时内首次接通数 |
| `call_duration` | `sum(call_duration)` | 外呼总通时，分钟 |
| `is_long_call` | `sum(is_long_call)` | 单用户-线索-顾问维度是否存在大于 480 秒通话 |
| `zong_call_ci` | `sum(zong_call_ci)` | 外呼次数 |
| `call_status` | `sum(call_status)` | 外呼接通次数 |
| `is_app_denglu` | `sum(is_app_denglu)` | APP/PC 登录用户数标记汇总 |
| `daoke1` | `sum(daoke1)` | 首节到课数 |
| `valid_daoke_1` | `sum(valid_daoke_1)` | 首节有效到课数 |

## 12. 已知风险和待确认事项

- SQL 中存在 Presto 三参数 `date_add('day', n, expr)`，公司查询平台可能按 Hive 两参数函数解析；后续生成新 SQL 时必须改为 `interval` 写法。
- `denglu_app` 中 `coalesce(is_app_denglu_h,0) = '1'` 和 `coalesce(is_app_denglu_d,0) = '1'` 存在数字与字符串比较，后续改写建议使用 `= 1`。
- 主表 `f` 的 `hour` 使用 `now()-interval '3' hour`，其他小时表多为 `now()-interval '2' hour`，小时错位原因待确认。
- 注释“剔除线索量<2”未在最终 SQL 中体现，是否需要 `having sum(v_lead) >= 2` 待确认。
- `call_c` 外呼表没有直接青橙部门过滤，依赖与青橙 `data` join 后限定范围；若单独复用外呼表必须补充范围或通过青橙主表驱动。
- `temp_table.dingxi01_jiagou_db` 名称不含 qing，但本 SQL 用作青橙架构表；是否为青橙专用或多部门复用待确认。
- `temp_table.dingxi01_qing_daoke` 的刷新来源、有效期和维护负责人待确认。
