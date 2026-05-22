# 青橙到课 raw

## 1. 来源

`resources/raw_sql/qingcheng_daoke_raw_20260522.sql`

入库时间：2026-05-22

## 2. 查询目标

沉淀青橙项目部到课 SQL。该 SQL 以青橙有效线索为基础，匹配用户上课明细和 `temp_table.dingxi01_qing_daoke` 课次映射表，输出第 1 至第 6 讲的到课标记和有效到课标记。

## 3. 最终输出粒度

| 维度 | 字段 |
|---|---|
| 期次 | `qici` |
| 一级渠道 | `channel_map_1` |
| 二级渠道 | `channel_map_2` |
| 年级 | `grade_1` |
| 架构 | `xiaozu`, `department`, `dept_2` |
| 员工 | `employee_email_prefix`, `employee_email_name` |
| 用户 | `user_id` |
| 有效线索标记 | `lead` |

该 SQL 是用户/线索/顾问维度的到课标记明细，不是最终汇总查询。后续要看汇总人数或比率时，应在外层按目标维度 `sum(ke_n)`、`sum(v_ke_n)`，并确认是否需要按 `user_id` 去重。

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `f` / `data` | 青橙有效线索基础表，生成期次、渠道和年级 |
| `service_dw.dws_service_user_learn_detail_hf` | `t2` / `daoke` | 用户上课明细，提供开课时间、学习时长和有效学习标记 |

## 5. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.dingxi01_qing_daoke` | 按期次、二级渠道、年级、开课时间标记课次，`ke_1` 字段取值支持 `'1'` 至 `'6'` | 已从 SQL 入库，来源/刷新方式待人工确认 |
| `temp_table.dingxi01_jiagou_db` | 按期次和员工邮箱前缀补充青橙架构 | 已从 SQL 入库，来源/刷新方式待人工确认 |

## 6. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `data` | 青橙有效线索基础层，生成 `qici`、`channel_map_1`、`channel_map_2`、`grade_1` | `lead_id`, `user_id`, `employee_email_prefix`, `employee_email_name`, `valid_lead_count`, `qici`, `channel_map_1`, `channel_map_2`, `grade_1` |
| `daoke` | 将青橙线索与上课明细和课次映射表匹配 | `qici`, `employee_email_prefix`, `lead_id`, `user_id`, `begin_time`, `live_learn_duration`, `is_valid_live_learn`, `ke_1` |

## 7. 青橙范围限定

| 位置 | 范围字段 | 取值 |
|---|---|---|
| `data` 主表 | `f.section_assign_employee_first_level_department_name` | `'H业务线'` |
| `data` 主表 | `f.section_assign_employee_second_level_department_name` | `'青橙项目部'` |
| `data` 主表 | `f.period_mapping_first_level_department_name` | `('H业务线')` |
| `data` 主表 | `f.period_mapping_second_level_department_name` | `('精品班学部','青橙项目部')` |
| 上课明细 | `course_first_level_department_name` | `'H业务线'` |
| 上课明细 | `course_second_level_department_name` | `('精品班学部','市场部','青橙项目部')` |
| 最终层 | `jg.department is not null` | 只保留匹配到青橙架构的记录 |

## 8. 分区和小时条件

| 表/CTE | dt 条件 | hour 条件 | 说明 |
|---|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | `format_datetime(now() - interval '2' hour, 'HH')` | 青橙有效线索基础表 |
| `service_dw.dws_service_user_learn_detail_hf` | `date_format(now() - interval '2' hour, '%Y%m%d')` | `date_format(now() - interval '2' hour, '%H')` | 用户上课明细 |

## 9. join 关系

| 左侧 | 右侧 | join key | 用途 |
|---|---|---|---|
| `t1` | `t2` | `t1.qici = t2.qici and t1.user_id = t2.user_number` | 将青橙线索用户匹配到上课明细 |
| `dk` | `temp_table.dingxi01_qing_daoke ke` | `dk.qici = ke.qici and dk.channel_map_2 = ke.qudao and dk.grade_1 = ke.grade and dk.begin_time = ke.begin_time` | 匹配课次编号 |
| `data` | `daoke` | `data.employee_email_prefix = daoke.employee_email_prefix and data.qici = daoke.qici and data.lead_id = daoke.lead_id` | 将到课标记回连到线索 |
| `data` | `temp_table.dingxi01_jiagou_db jg` | `data.employee_email_prefix = jg.employee_email_prefix and data.qici = jg.qici` | 补充青橙架构 |

## 10. 渠道和年级映射

本 SQL 使用独立的到课 SQL 渠道/年级映射，已补充到 `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`。

与过程数据 SQL 的差异：

- `channel_map_1` 未包含 `青橙本地化`、`抖音私信`、`青橙训练营`。
- `channel_map_2` 未包含 `私域IE`、`私域本地化`、`郑州图书`、`图书咨询`、`南京`、`抖音私信`、`青橙训练营`。
- `grade_1` 未命中时输出 `'未知'`，不再回退到 `lead_purchase_intention_level2_category_name`。

## 11. 到课指标

指标集合沉淀到 `knowledge/metrics/qingcheng_daoke_metrics.md`。

| 指标 | 表达式 | 口径简述 |
|---|---|---|
| `ke_1` 至 `ke_6` | `ke_1 = 'n' and live_learn_duration > 0` | 第 n 讲到课标记 |
| `v_ke_1` 至 `v_ke_6` | `ke_1 = 'n' and is_valid_live_learn = '1'` | 第 n 讲有效到课标记 |

## 12. 已知风险和待确认事项

- SQL 中存在 Presto 三参数 `date_add('day', n, expr)`，公司查询平台可能按 Hive 两参数函数解析；后续生成新 SQL 时必须改为 `interval` 写法。
- `coalesce(data.valid_lead_count,0) lead` 可能存在字符串和数字类型混用；如果 `valid_lead_count` 是字符串，建议改为 `coalesce(cast(data.valid_lead_count as integer), 0)` 或保持字符串后另行转数值。
- `temp_table.dingxi01_qing_daoke.ke_1` 字段名容易误解为“首节课”，但本 SQL 使用它承载 1-6 讲课次编号。
- `temp_table.dingxi01_jiagou_db` 在此 SQL 使用 `employee_email_prefix + qici` join；过程数据 raw 中曾使用 `employee_email_name + qici` join，两个 join key 差异需确认。
- 最终输出含 `lead` 维度并 group by `lead`，后续汇总时要确认是否直接 `sum(lead)`。

