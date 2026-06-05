# 市场顾问线索转化到课看板

## 1. 看板名称

市场顾问线索转化到课看板

## 2. SQL 来源

- 原始 SQL：`resources/raw_sql/market_consultant_lead_conversion_attendance.sql`
- 来源：用户提供的最新到课 SQL
- 入库日期：2026-05-08
- 最近覆盖：2026-06-05

## 3. 查询目的

基于 H 业务线市场部市场顾问线索和行课数据，按期次、渠道、规则、年级、架构和顾问聚合有效线索、第 1-6 节到课、第 1-6 节有效到课。

当前 raw SQL 已切换为“到课衰减”版本，不再输出转化、GMV、成本目标、渠道分组、深沟、AB 意向等旧版指标。后续撰写到课 SQL 时，应优先参考当前 raw SQL 的 `qici + channel_map_1 + grade_1 + begin_time` 到课映射口径。

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | f / data | 主线索、期次、渠道、年级、顾问、有效线索来源 |
| service_dw.dwd_crm_assign_private_detail_hf | t | 最新私海阶段来源；当前 raw SQL 派生 `is_shengou`、`is_shuanggou`，结果层未输出 |
| service_dw.dm_crm_lead_stats_detail_hf | jt | 首呼接通时间差辅助来源；当前 raw SQL 保留派生字段，结果层未输出 |
| service_dw.dws_service_user_learn_detail_hf | t2 / daoke | 行课记录，提供 `begin_time`、`live_learn_duration`、`is_valid_live_learn` |
| temp_table.dingxi01_daoke_1_6_t | ke | 期次-渠道-年级-开课时间到课课次映射，当前使用 `qudao` 字段关联渠道 |
| temp_table.dingxi01_jiagou_db | jg | 期次-员工邮箱前缀架构映射，输出 `xiaozu`、`department`、`jingli` 并过滤空架构 |

## 5. CTE 逻辑

| CTE | 作用 |
|---|---|
| data | 从主全链路表读取有效线索，派生 `qici`、`channel_map_1`、`grade_1`，并保留顾问和线索字段 |
| daoke | 将线索用户与行课明细关联，再通过 `temp_table.dingxi01_daoke_1_6_t` 标记第 1-6 节课次 |
| prc | 按用户、线索、期次、渠道、年级、架构和顾问去重，计算每个用户是否第 1-6 节到课/有效到课 |
| final select | 按期次、渠道、规则、年级、架构和顾问聚合有效线索及 1-6 节到课指标 |

## 6. join 关系

| 左表/CTE | 左字段 | 右表/CTE | 右字段 | 说明 |
|---|---|---|---|---|
| f | user_id | service_dw.dwd_crm_assign_private_detail_hf | user_number | 获取最新私海阶段 |
| f | user_id | service_dw.dm_crm_lead_stats_detail_hf | user_number | 获取首呼接通时间差 |
| data | lead_id, user_id, employee_email_prefix, qici, channel_map_1, grade_1 | daoke 子查询 t1 | 同名字段 | 形成到课候选线索 |
| data / t1 | user_id, qici | service_dw.dws_service_user_learn_detail_hf | user_number, 派生 qici | 对齐线索期次与课程期次 |
| daoke | qici, channel_map_1, grade_1, begin_time | temp_table.dingxi01_daoke_1_6_t | qici, qudao, grade, begin_time | 识别第 1-6 节课次 |
| data | employee_email_prefix, qici | temp_table.dingxi01_jiagou_db | employee_email_prefix, qici | 补充小组、部门、经理架构 |

## 7. 分区和范围限定

主全链路表：

```sql
f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and f.hour = format_datetime(now() - interval '3' hour, 'HH')
and f.section_assign_employee_first_level_department_name = 'H业务线'
and f.section_assign_employee_second_level_department_name = '市场部'
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
| ke_1 | `sum(ke_1)`，用户第 1 节 `live_learn_duration > 0` |
| ke_2 | `sum(ke_2)`，用户第 2 节 `live_learn_duration > 0` |
| ke_3 | `sum(ke_3)`，用户第 3 节 `live_learn_duration > 0` |
| ke_4 | `sum(ke_4)`，用户第 4 节 `live_learn_duration > 0` |
| ke_5 | `sum(ke_5)`，用户第 5 节 `live_learn_duration > 0` |
| ke_6 | `sum(ke_6)`，用户第 6 节 `live_learn_duration > 0` |
| v_ke_1 | `sum(v_ke_1)`，用户第 1 节 `is_valid_live_learn = '1'` |
| v_ke_2 | `sum(v_ke_2)`，用户第 2 节 `is_valid_live_learn = '1'` |
| v_ke_3 | `sum(v_ke_3)`，用户第 3 节 `is_valid_live_learn = '1'` |
| v_ke_4 | `sum(v_ke_4)`，用户第 4 节 `is_valid_live_learn = '1'` |
| v_ke_5 | `sum(v_ke_5)`，用户第 5 节 `is_valid_live_learn = '1'` |
| v_ke_6 | `sum(v_ke_6)`，用户第 6 节 `is_valid_live_learn = '1'` |

## 10. 待确认事项

- raw SQL 当前保留 `date_add('day', n, expr)` 三参数写法；公司查询平台生成新 SQL 时仍需改为 `expr + interval 'n' day` 或 `expr - interval 'n' day`。
- `valid_lead_count = '1'` 和 `is_valid_live_learn = '1'` 存在数值/字符串比较，字段类型需结合平台结果确认；生成新 SQL 时优先按字段表类型显式处理。
- 当前到课映射使用 `temp_table.dingxi01_daoke_1_6_t.qudao`，不是 `channel`；维护到课临时表或写新 SQL 时不要混用。
- `channel_map_1` CASE 为超长渠道归因规则，`孟亚飞IP99元` 等特例必须放在更泛化的 `孟亚飞9元`、`信息流` 等规则之前；以后排查“某渠道从某期开始消失”时，应优先检查 CASE 顺序和 rule_name 新旧名称。
- `data` 使用 `select distinct f.*`，属于历史 raw SQL 保留写法；生成新 SQL 时建议只选必要字段，降低字段权限和解析风险。
