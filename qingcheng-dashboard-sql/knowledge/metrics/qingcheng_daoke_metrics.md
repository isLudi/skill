# 青橙到课指标

## 1. 来源

`resources/raw_sql/qingcheng_daoke_raw_20260522.sql`

适用看板：`knowledge/dashboards/qingcheng_daoke_raw_20260522.md`

## 2. 指标计算粒度

本 SQL 在最终层按以下粒度输出到课标记：

```text
qici + channel_map_1 + channel_map_2 + grade_1 + xiaozu + department + dept_2
+ lead + employee_email_prefix + employee_email_name + user_id
```

其中 `lead` 来自 `coalesce(data.valid_lead_count,0)`，原 SQL 将其作为维度输出。

## 3. 课次字段解释

`temp_table.dingxi01_qing_daoke.ke_1` 在此 SQL 中表示课次编号，取值包括 `'1'` 至 `'6'`。字段名虽然叫 `ke_1`，但不是只表示第一讲。

## 4. 到课指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `ke_1` | `sum(case when daoke.ke_1 = '1' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0` | 第 1 讲到课标记 | 已从 SQL 入库 |
| `ke_2` | `sum(case when daoke.ke_1 = '2' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0` | 第 2 讲到课标记 | 已从 SQL 入库 |
| `ke_3` | `sum(case when daoke.ke_1 = '3' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0` | 第 3 讲到课标记 | 已从 SQL 入库 |
| `ke_4` | `sum(case when daoke.ke_1 = '4' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0` | 第 4 讲到课标记 | 已从 SQL 入库 |
| `ke_5` | `sum(case when daoke.ke_1 = '5' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0` | 第 5 讲到课标记 | 已从 SQL 入库 |
| `ke_6` | `sum(case when daoke.ke_1 = '6' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0` | 第 6 讲到课标记 | 已从 SQL 入库 |

## 5. 有效到课指标

| 指标 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `v_ke_1` | `sum(case when daoke.ke_1 = '1' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0` | 第 1 讲有效到课标记 | 已从 SQL 入库 |
| `v_ke_2` | `sum(case when daoke.ke_1 = '2' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0` | 第 2 讲有效到课标记 | 已从 SQL 入库 |
| `v_ke_3` | `sum(case when daoke.ke_1 = '3' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0` | 第 3 讲有效到课标记 | 已从 SQL 入库 |
| `v_ke_4` | `sum(case when daoke.ke_1 = '4' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0` | 第 4 讲有效到课标记 | 已从 SQL 入库 |
| `v_ke_5` | `sum(case when daoke.ke_1 = '5' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0` | 第 5 讲有效到课标记 | 已从 SQL 入库 |
| `v_ke_6` | `sum(case when daoke.ke_1 = '6' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0` | 第 6 讲有效到课标记 | 已从 SQL 入库 |

## 6. 有效线索字段

| 字段 | SQL 口径 | 说明 | 状态 |
|---|---|---|---|
| `lead` | `coalesce(data.valid_lead_count,0)` | 有效线索标记，原 SQL 作为最终维度输出 | 待确认类型 |

## 7. 待确认事项

- `valid_lead_count` 类型待确认；当前 SQL 可能存在字符串与数字混用。
- `ke_n` 和 `v_ke_n` 是明细标记，汇总到看板时应明确是否按线索、用户或员工粒度聚合。
- 如果同一用户同一讲存在多条学习明细，当前逻辑用 `sum(...) > 0` 压成 1。

