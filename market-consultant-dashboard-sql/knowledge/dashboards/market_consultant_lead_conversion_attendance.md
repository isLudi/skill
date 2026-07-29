# 市场顾问线索转化到课看板

## 1. 看板名称

市场顾问线索转化到课看板

## 2. SQL 来源

- 原始 SQL：`resources/raw_sql/market_consultant_lead_conversion_attendance.sql`
- 来源：用户提供并经网页端 Presto 验证的自动课次优化 SQL
- 入库日期：2026-05-08
- 最近覆盖：2026-06-30

## 3. 查询目的

基于 H 业务线市场部市场顾问线索和行课数据，按期次、渠道、规则、年级、架构和顾问聚合有效线索、第 1-6 节自动课次到课、第 1-6 节自动课次有效到课，并保留手工课次映射和自动/手工课次对照计数。

当前 raw SQL 已切换为“到课衰减”版本，不再输出转化、GMV、成本目标、渠道分组、深沟、AB 意向等旧版指标。2026-06-30 覆盖后，到课主口径不再依赖手工课次映射，也不再用行课表自身派生期次作为唯一关联依据；而是先以 `data` 中的 `qici + channel_map_1 + grade_1` 为准圈定用户行课候选，再按同一期次、渠道、年级下实际开课 `begin_time` 的先后顺序自动编号课 1-课 6。最终 SQL 保持原看板输出字段，不在 SQL 中输出到课率或有效到课率，比例由看板用 `sum(ke_n) / sum(lead)`、`sum(v_ke_n) / sum(lead)` 计算。手工课次 `manual_*` 和自动/手工对照字段仍作为诊断字段保留。

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | f / data | 主线索、期次、渠道、年级、顾问、有效线索来源 |
| service_dw.dwd_crm_assign_private_detail_hf | t | 最新私海阶段来源；当前 raw SQL 派生 `is_shengou`、`is_shuanggou`，结果层未输出 |
| service_dw.dm_crm_lead_stats_detail_hf | jt | 首呼接通时间差辅助来源；当前 raw SQL 保留派生字段，结果层未输出 |
| service_dw.dws_service_user_learn_detail_hf | t / learn_raw / learn_candidates | 行课记录，提供 `begin_time`、课程名称、到课时长和有效到课标记；先按用户和期次窗口进入候选，再参与自动课次排序 |
| temp_table.dingxi01_daoke_1_6_t | ke / ke_manual | 期次-渠道-年级-开课时间手工课次映射，当前仅用于 `manual_*` 和自动/手工对照诊断，不能作为主课次来源 |
| temp_table.dingxi01_jiagou_db | jg | 期次-员工邮箱前缀架构映射，输出 `xiaozu`、`department`、`jingli` 并过滤空架构 |

## 5. CTE 逻辑

| CTE | 作用 |
|---|---|
| data | 从主全链路表读取有效线索，派生 `qici`、`channel_map_1`、`grade_1`，并保留顾问和线索字段 |
| ke_manual | 对 `temp_table.dingxi01_daoke_1_6_t` 按 `qici + qudao + grade + begin_time` 去重，得到手工课次 `manual_ke_1` |
| learn_raw | 读取行课明细，不再把 `begin_time` 派生期次作为唯一关联依据；保留原始 `begin_time`、课程名称、到课时长和有效到课标记 |
| lead_user_period | 从 `data` 抽取 `lead_id + user_id + employee_email_prefix + qici + channel_map_1 + grade_1`，并由 `qici` 派生 `qici_date` |
| learn_candidates | 按用户关联 `lead_user_period` 与 `learn_raw`，用 `qici_date - 3 day` 到 `qici_date + 4 day` 的窗口圈定候选行课，覆盖周二/周三提前开课和周一补充开课；同时把 `begin_time` 规范到分钟粒度 `begin_time_slot` |
| period_user_counts | 统计每个 `qici + channel_map_1 + grade_1` 的候选用户数，用于过滤低覆盖噪声行课 |
| lesson_slot_candidates / lesson_slots | 按 `qici + channel_map_1 + grade_1 + begin_time_slot` 聚合真实开课槽位，保留 `lesson_user_cnt` 和课程名样例；小样本允许 1-2 人，大样本要求至少 1% 且不少于 3 人 |
| lesson_ranked / lesson_ranked_1_6 | 对每个 `qici + channel_map_1 + grade_1` 内的开课槽位按 `begin_time` 做 `dense_rank`，生成自动课次 `auto_ke_1`，仅保留 1-6 |
| daoke | 将候选行课按 `qici + channel_map_1 + grade_1 + begin_time_slot` 回连自动课次，再按 `qici + qudao + grade + begin_time` 补充手工课次诊断，输出自动/手工课次对照状态 |
| prc | 按用户、线索、期次、渠道、年级、架构和顾问去重，计算自动课次、手工课次和自动/手工对照计数 |
| final select | 按期次、渠道、规则、年级、架构和顾问聚合有效线索、1-6 节到课指标及课次对照指标 |

## 6. join 关系

| 左表/CTE | 左字段 | 右表/CTE | 右字段 | 说明 |
|---|---|---|---|---|
| f | user_id | service_dw.dwd_crm_assign_private_detail_hf | user_number | 获取最新私海阶段 |
| f | user_id | service_dw.dm_crm_lead_stats_detail_hf | user_number | 获取首呼接通时间差 |
| data | lead_id, user_id, employee_email_prefix, qici, channel_map_1, grade_1 | lead_user_period | 同名字段 | 形成期次、渠道、年级下的候选线索 |
| lead_user_period | user_id, qici_date 时间窗口 | learn_raw | user_number, begin_date | 以线索期次为准圈定候选行课，不依赖课程名称精确匹配 |
| learn_candidates | qici, channel_map_1, grade_1, begin_time_slot | lesson_ranked_1_6 | qici, channel_map_1, grade_1, begin_time | 回连自动课次 `auto_ke_1` |
| daoke | qici, channel_map_1, grade_1, begin_time | ke_manual | qici, qudao, grade, begin_time | 补充手工课次 `manual_ke_1`，仅用于 manual 指标和自动/手工课次对照 |
| data | employee_email_prefix, qici | temp_table.dingxi01_jiagou_db | employee_email_prefix, qici | 补充小组、部门、经理架构 |

## 7. 分区和范围限定

主全链路表：

```sql
f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and f.hour = format_datetime(now() - interval '3' hour, 'HH')
and f.section_assign_employee_first_level_department_name = 'H业务线'
and f.section_assign_employee_second_level_department_name = '市场部'
and f.section_assign_employee_third_level_department_name = '市场顾问部'
and f.period_mapping_first_level_department_name = 'H业务线'
and f.valid_lead_count = '1'
```

私海阶段表：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and assign_employee_first_level_department_name = 'H业务线'
and assign_employee_second_level_department_name = '市场部'
and assign_employee_third_level_department_name = '市场顾问部'
```

首呼统计明细表：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and mapping_first_level_department_name = 'H业务线'
and mapping_second_level_department_name in ('精品班学部','菁英班学部','市场部','本地化大班学部')
```

行课明细表：

```sql
dt = date_format(now() - interval '2' hour, '%Y%m%d')
and hour = date_format(now() - interval '2' hour, '%H')
and course_first_level_department_name = 'H业务线'
and course_second_level_department_name in ('精品班学部','市场部','青橙项目部')
and is_need_attend = 1
```

最终范围：

```sql
data.qici > '20260410期'
and jg.department is not null
```

## 8. 输出粒度

最终输出按以下字段聚合：

- `qici`
- `channel_map_1`
- `rule_name`
- `grade_1`
- `xiaozu`
- `department`
- `jingli`
- `employee_email_prefix`
- `employee_email_name`

## 9. 聚合指标

| 指标 | SQL 口径 |
|---|---|
| lead | `sum(lead)`；`lead` 在 `data` 中来自 `coalesce(valid_lead_count, 0)` |
| ke_1 ~ ke_6 | 自动课次第 1-6 节普通到课；使用 `auto_ke_1` 且 `live_learn_duration > 0` |
| v_ke_1 ~ v_ke_6 | 自动课次第 1-6 节有效到课；使用 `auto_ke_1` 且 `is_valid_live_learn = '1'` |
| manual_ke_1 ~ manual_ke_6 | 手工映射课次第 1-6 节普通到课；使用 `manual_ke_1` 且 `live_learn_duration > 0` |
| manual_v_ke_1 ~ manual_v_ke_6 | 手工映射课次第 1-6 节有效到课；使用 `manual_ke_1` 且 `is_valid_live_learn = '1'` |
| auto_matched_lesson_row_cnt | 自动课次命中 1-6 节的行课记录数 |
| manual_matched_lesson_row_cnt | 手工课次映射非空的行课记录数 |
| manual_auto_same_lesson_row_cnt | 手工课次与自动课次一致的行课记录数 |
| manual_auto_diff_lesson_row_cnt | 手工课次与自动课次不一致的行课记录数 |
| manual_missing_auto_present_row_cnt | 手工课次缺失但自动课次存在的行课记录数 |
| auto_missing_manual_present_row_cnt | 自动课次缺失或不在 1-6 节、但手工课次存在的行课记录数 |

## 10. 待确认事项

- `valid_lead_count = '1'` 和 `is_valid_live_learn = '1'` 存在数值/字符串比较，字段类型需结合平台结果确认；生成新 SQL 时优先按字段表类型显式处理。
- 当前手工课次映射使用 `temp_table.dingxi01_daoke_1_6_t.qudao`，不是 `channel`；该表只作为诊断对照，主课次不再依赖手工映射维护。
- 当前最终 `ke_*` / `v_ke_*` 主口径使用按 `qici + channel_map_1 + grade_1 + begin_time_slot` 自动排序得到的 `auto_ke_1`；`manual_*` / `manual_v_*` 只反映临时表手工课次映射口径。
- 自动课次按开课时间排序，不按课程名精确匹配；课程名样例只用于诊断。若课程表后续出现周一、周二、周三开课，优先检查 `learn_candidates` 的 `qici_date - 3 day` 到 `qici_date + 4 day` 窗口是否覆盖业务实际开课日期。
- `channel_map_1` CASE 为超长渠道归因规则，`孟亚飞IP99元` 等特例必须放在更泛化的 `孟亚飞9元`、`信息流` 等规则之前；2026-06-18 起 `孟亚飞-1组-视频号` 已合并为 `孟亚飞9元`，以后排查“某渠道从某期开始消失”时，应优先检查 CASE 顺序和 rule_name 新旧名称。
- `data` 使用 `select distinct f.*`，属于历史 raw SQL 保留写法；生成新 SQL 时建议只选必要字段，降低字段权限和解析风险。
