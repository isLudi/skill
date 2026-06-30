# 市场顾问线索转化到课指标

## 1. 指标集合名称

市场顾问线索转化到课指标集合

## 2. 来源

- 看板 SQL：`resources/raw_sql/market_consultant_lead_conversion_attendance.sql`
- 看板文档：`knowledge/dashboards/market_consultant_lead_conversion_attendance.md`
- 入库日期：2026-05-08
- 最近覆盖：2026-06-30

## 3. 适用范围

适用于 H 业务线市场部市场顾问到课衰减分析，默认统计有效线索在第 1-6 节自动课次的普通到课和有效到课。2026-06-30 起，自动课次按同一 `qici + channel_map_1 + grade_1` 下实际行课 `begin_time` 的先后顺序生成，不再依赖手工课次表或课程名称精确匹配；手工课次映射到课、手工课次有效到课和自动/手工课次对照计数仅作为诊断字段保留。

默认范围来自 SQL：

- `section_assign_employee_first_level_department_name = 'H业务线'`
- `section_assign_employee_second_level_department_name = '市场部'`
- `section_assign_employee_third_level_department_name = '市场顾问部'`
- `period_mapping_first_level_department_name = 'H业务线'`
- `valid_lead_count = '1'`
- `data.qici > '20260410期'`
- `temp_table.dingxi01_jiagou_db.department is not null`

## 4. 基础派生字段

| 字段 | 口径 |
|---|---|
| qici | 由 `group_period_year + group_period_term` 去掉“期”后按周五规则派生 |
| channel_map_1 | 基于 `rule_name`、`flow_pool_name`、`channel_name_1/2`、`put_plan_name`、`third_department_name` 等字段的超长 CASE 渠道归因 |
| grade_1 | `rule_name` 包含高一/高二/高三/初二/初三时取对应年级，否则为 `未知` |
| lead | `coalesce(valid_lead_count, 0)`，字段名为 `lead`，实际口径是有效线索 |
| is_shengou | 最新私海阶段为深沟或已双沟时为 1；当前结果层未输出 |
| is_shuanggou | 最新私海阶段为已双沟时为 1；当前结果层未输出 |
| first_call_connect_diff_hour | 首呼接通时间差；当前结果层未输出 |

## 5. 用户级到课标记

在 `prc` CTE 中，先按用户和线索维度去重，再计算每个用户在对应课次是否到课。`auto_ke_1` 来自 `lesson_ranked_1_6`：先把行课 `begin_time` 规范到分钟级 `begin_time_slot`，再在每个 `qici + channel_map_1 + grade_1` 内按开课时间 `dense_rank` 生成课 1-课 6。

| 指标 | 中文含义 | SQL 口径 |
|---|---|---|
| ke_1 | 自动课次第 1 节到课 | `sum(case when auto_ke_1 = '1' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_2 | 自动课次第 2 节到课 | `sum(case when auto_ke_1 = '2' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_3 | 自动课次第 3 节到课 | `sum(case when auto_ke_1 = '3' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_4 | 自动课次第 4 节到课 | `sum(case when auto_ke_1 = '4' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_5 | 自动课次第 5 节到课 | `sum(case when auto_ke_1 = '5' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_6 | 自动课次第 6 节到课 | `sum(case when auto_ke_1 = '6' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| v_ke_1 | 自动课次第 1 节有效到课 | `sum(case when auto_ke_1 = '1' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_2 | 自动课次第 2 节有效到课 | `sum(case when auto_ke_1 = '2' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_3 | 自动课次第 3 节有效到课 | `sum(case when auto_ke_1 = '3' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_4 | 自动课次第 4 节有效到课 | `sum(case when auto_ke_1 = '4' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_5 | 自动课次第 5 节有效到课 | `sum(case when auto_ke_1 = '5' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_6 | 自动课次第 6 节有效到课 | `sum(case when auto_ke_1 = '6' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| manual_ke_1 | 手工课次第 1 节到课 | `sum(case when manual_ke_1 = '1' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| manual_ke_2 | 手工课次第 2 节到课 | `sum(case when manual_ke_1 = '2' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| manual_ke_3 | 手工课次第 3 节到课 | `sum(case when manual_ke_1 = '3' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| manual_ke_4 | 手工课次第 4 节到课 | `sum(case when manual_ke_1 = '4' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| manual_ke_5 | 手工课次第 5 节到课 | `sum(case when manual_ke_1 = '5' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| manual_ke_6 | 手工课次第 6 节到课 | `sum(case when manual_ke_1 = '6' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| manual_v_ke_1 | 手工课次第 1 节有效到课 | `sum(case when manual_ke_1 = '1' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| manual_v_ke_2 | 手工课次第 2 节有效到课 | `sum(case when manual_ke_1 = '2' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| manual_v_ke_3 | 手工课次第 3 节有效到课 | `sum(case when manual_ke_1 = '3' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| manual_v_ke_4 | 手工课次第 4 节有效到课 | `sum(case when manual_ke_1 = '4' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| manual_v_ke_5 | 手工课次第 5 节有效到课 | `sum(case when manual_ke_1 = '5' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| manual_v_ke_6 | 手工课次第 6 节有效到课 | `sum(case when manual_ke_1 = '6' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |

## 6. 结果层聚合指标

| 指标名 | 中文含义 | SQL 口径 |
|---|---|---|
| lead | 有效线索数 | `sum(lead)` |
| ke_1 | 第 1 节到课人数 | `sum(ke_1)` |
| ke_2 | 第 2 节到课人数 | `sum(ke_2)` |
| ke_3 | 第 3 节到课人数 | `sum(ke_3)` |
| ke_4 | 第 4 节到课人数 | `sum(ke_4)` |
| ke_5 | 第 5 节到课人数 | `sum(ke_5)` |
| ke_6 | 第 6 节到课人数 | `sum(ke_6)` |
| v_ke_1 | 第 1 节有效到课人数 | `sum(v_ke_1)` |
| v_ke_2 | 第 2 节有效到课人数 | `sum(v_ke_2)` |
| v_ke_3 | 第 3 节有效到课人数 | `sum(v_ke_3)` |
| v_ke_4 | 第 4 节有效到课人数 | `sum(v_ke_4)` |
| v_ke_5 | 第 5 节有效到课人数 | `sum(v_ke_5)` |
| v_ke_6 | 第 6 节有效到课人数 | `sum(v_ke_6)` |
| manual_ke_1 | 手工课次第 1 节到课人数 | `sum(manual_ke_1)` |
| manual_ke_2 | 手工课次第 2 节到课人数 | `sum(manual_ke_2)` |
| manual_ke_3 | 手工课次第 3 节到课人数 | `sum(manual_ke_3)` |
| manual_ke_4 | 手工课次第 4 节到课人数 | `sum(manual_ke_4)` |
| manual_ke_5 | 手工课次第 5 节到课人数 | `sum(manual_ke_5)` |
| manual_ke_6 | 手工课次第 6 节到课人数 | `sum(manual_ke_6)` |
| manual_v_ke_1 | 手工课次第 1 节有效到课人数 | `sum(manual_v_ke_1)` |
| manual_v_ke_2 | 手工课次第 2 节有效到课人数 | `sum(manual_v_ke_2)` |
| manual_v_ke_3 | 手工课次第 3 节有效到课人数 | `sum(manual_v_ke_3)` |
| manual_v_ke_4 | 手工课次第 4 节有效到课人数 | `sum(manual_v_ke_4)` |
| manual_v_ke_5 | 手工课次第 5 节有效到课人数 | `sum(manual_v_ke_5)` |
| manual_v_ke_6 | 手工课次第 6 节有效到课人数 | `sum(manual_v_ke_6)` |
| auto_matched_lesson_row_cnt | 自动课次命中 1-6 节的行课记录数 | `sum(auto_matched_lesson_row_cnt)` |
| manual_matched_lesson_row_cnt | 手工课次映射非空的行课记录数 | `sum(manual_matched_lesson_row_cnt)` |
| manual_auto_same_lesson_row_cnt | 手工课次与自动课次一致的行课记录数 | `sum(manual_auto_same_lesson_row_cnt)` |
| manual_auto_diff_lesson_row_cnt | 手工课次与自动课次不一致的行课记录数 | `sum(manual_auto_diff_lesson_row_cnt)` |
| manual_missing_auto_present_row_cnt | 手工课次缺失但自动课次存在的行课记录数 | `sum(manual_missing_auto_present_row_cnt)` |
| auto_missing_manual_present_row_cnt | 自动课次缺失或不在 1-6 节、但手工课次存在的行课记录数 | `sum(auto_missing_manual_present_row_cnt)` |

## 7. 输出粒度

最终输出粒度为：

- `qici`
- `channel_map_1`
- `rule_name`
- `grade_1`
- `xiaozu`
- `department`
- `jingli`
- `employee_email_prefix`
- `employee_email_name`

如果前端继续计算到课率或有效到课率，应使用“到课人数 / 有效线索数”重新计算比率，不能对行级比率直接 `sum`。

## 8. 到课映射口径

当前主到课课次来自行课明细自动派生：

- `lead_user_period` 从 `data` 中抽取 `lead_id + user_id + employee_email_prefix + qici + channel_map_1 + grade_1`，并由 `qici` 派生 `qici_date`。
- `learn_candidates` 只按用户关联行课表，并用 `qici_date - 3 day` 到 `qici_date + 4 day` 的窗口圈定候选行课；这样以线索期次为准，覆盖周二/周三提前开课和周一补充开课，不把行课表按周五规则派生的期次作为唯一依据。
- `lesson_slots` 按 `qici + channel_map_1 + grade_1 + begin_time_slot` 聚合真实开课槽位，使用 `lesson_user_cnt` 过滤低覆盖噪声行课。
- `lesson_ranked_1_6` 对每个 `qici + channel_map_1 + grade_1` 内的开课槽位按 `begin_time` 做 `dense_rank`，生成 `auto_ke_1`，仅保留 1-6。
- `lesson_index` / `lesson_index_add`、`lesson_name` 当前只保留为诊断字段，不驱动主课次。

手工课次来自 `temp_table.dingxi01_daoke_1_6_t`，当前 SQL 关联条件为：

```sql
dk.qici = ke.qici
and dk.channel_map_1 = ke.qudao
and dk.grade_1 = ke.grade
and dk.begin_time = ke.begin_time
```

其中 `qudao` 是当前 raw SQL 确认使用的手工渠道映射字段；不要默认改成 `channel`。最终 `ke_*` / `v_ke_*` 使用自动排序得到的 `auto_ke_1`，`manual_*` / `manual_v_*` 使用 `manual_ke_1`。

## 9. 待确认事项

- `lead` 实际来自 `valid_lead_count`，展示文案若叫“线索数”需确认是否应改名为“有效线索数”。
- `ke_1` 字段名同时被用作到课映射表中的手工课次字段和最终第 1 节到课指标，阅读 SQL 时需要区分 CTE 层级。
- `valid_lead_count = '1'`、`is_valid_live_learn = '1'` 为历史 SQL 字符串比较写法，生成新 SQL 时建议按字段类型统一。
- 到课率和有效到课率不在 SQL 中输出；看板应基于最终聚合后的 `sum(ke_n) / sum(lead)`、`sum(v_ke_n) / sum(lead)` 计算，避免对行级比率二次聚合。
- 渠道 CASE 顺序会直接影响到课临时表的渠道匹配，新增或修复渠道时应先确认特例是否被更靠前的泛化规则截走；2026-06-18 起 `孟亚飞-1组-视频号` 已合并为 `孟亚飞9元`。
