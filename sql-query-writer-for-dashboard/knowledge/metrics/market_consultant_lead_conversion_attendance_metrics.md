# 市场顾问线索转化到课指标

## 1. 指标集合名称

市场顾问线索转化到课指标集合

## 2. 来源

- 看板 SQL：`resources/raw_sql/market_consultant_lead_conversion_attendance.sql`
- 看板文档：`knowledge/dashboards/market_consultant_lead_conversion_attendance.md`
- 入库日期：2026-05-08
- 最近覆盖：2026-06-05

## 3. 适用范围

适用于 H 业务线市场部市场顾问到课衰减分析，默认统计有效线索在第 1-6 节课的普通到课和有效到课。

默认范围来自 SQL：

- `section_assign_employee_first_level_department_name = 'H业务线'`
- `section_assign_employee_second_level_department_name = '市场部'`
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

在 `prc` CTE 中，先按用户和线索维度去重，再计算每个用户在对应课次是否到课。

| 指标 | 中文含义 | SQL 口径 |
|---|---|---|
| ke_1 | 第 1 节到课 | `sum(case when ke_1 = '1' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_2 | 第 2 节到课 | `sum(case when ke_1 = '2' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_3 | 第 3 节到课 | `sum(case when ke_1 = '3' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_4 | 第 4 节到课 | `sum(case when ke_1 = '4' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_5 | 第 5 节到课 | `sum(case when ke_1 = '5' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| ke_6 | 第 6 节到课 | `sum(case when ke_1 = '6' and live_learn_duration > 0 then 1 else 0 end) > 0` |
| v_ke_1 | 第 1 节有效到课 | `sum(case when ke_1 = '1' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_2 | 第 2 节有效到课 | `sum(case when ke_1 = '2' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_3 | 第 3 节有效到课 | `sum(case when ke_1 = '3' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_4 | 第 4 节有效到课 | `sum(case when ke_1 = '4' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_5 | 第 5 节有效到课 | `sum(case when ke_1 = '5' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |
| v_ke_6 | 第 6 节有效到课 | `sum(case when ke_1 = '6' and is_valid_live_learn = '1' then 1 else 0 end) > 0` |

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

到课课次来自 `temp_table.dingxi01_daoke_1_6_t`，当前 SQL 关联条件为：

```sql
dk.qici = ke.qici
and dk.channel_map_1 = ke.qudao
and dk.grade_1 = ke.grade
and dk.begin_time = ke.begin_time
```

其中 `qudao` 是当前 raw SQL 确认使用的渠道映射字段；不要默认改成 `channel`。

## 9. 待确认事项

- `lead` 实际来自 `valid_lead_count`，展示文案若叫“线索数”需确认是否应改名为“有效线索数”。
- `ke_1` 字段名同时被用作到课映射表中的课次字段和最终第 1 节到课指标，阅读 SQL 时需要区分 CTE 层级。
- `valid_lead_count = '1'`、`is_valid_live_learn = '1'` 为历史 SQL 字符串比较写法，生成新 SQL 时建议按字段类型统一。
- 渠道 CASE 顺序会直接影响到课临时表的渠道匹配，新增或修复渠道时应先确认特例是否被更靠前的泛化规则截走。
