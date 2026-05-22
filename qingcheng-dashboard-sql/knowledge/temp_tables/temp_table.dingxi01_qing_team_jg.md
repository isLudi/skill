# temp_table.dingxi01_qing_team_jg

## 1. 临时表用途

青橙最新团队架构表。当前在 `qingcheng_conversion_raw_20260522.sql` 最终层按员工姓名补充学部、小组、大组和经理。

## 2. 来源和刷新方式

| 项目 | 内容 |
|---|---|
| 创建来源 | 待人工确认 |
| 刷新方式 | 待人工确认 |
| 刷新频率 | 待人工确认 |
| 有效期 | 使用 `max(qici)` 作为最新期次 |

## 3. 数据粒度

疑似为：

```text
qici + employee_email_name
```

待人工确认同一员工在同一期次是否唯一。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `qici` | 待人工确认 | 期次 | SQL 使用最大期次 |
| `employee_email_name` | 待人工确认 | 员工姓名/邮箱名 | join `mm.employee_email_name` |
| `xuebu` | 待人工确认 | 学部 | 最终别名 `dept_2` |
| `leader_employee_email_name` | 待人工确认 | 直属主管/小组负责人 | 最终别名 `xiaozu` |
| `dazu` | 待人工确认 | 大组 | 最终输出字段 |
| `jingli` | 待人工确认 | 经理 | 最终输出字段 |

## 5. 适用看板

- `qingcheng_conversion_raw_20260522`

## 6. join key

```sql
mm.employee_email_name = jg.employee_email_name
```

临时表子查询使用：

```sql
where qici = (select max(qici) from temp_table.dingxi01_qing_team_jg)
```

## 7. 不可复用边界

- 默认只作为青橙转化看板的最新团队架构表。
- 使用最新期次架构回填历史期次转化数据，可能造成历史架构漂移；如果需要历史归属，应改为按 `mm.qici = jg.qici` join。
- 不得与 `temp_table.dingxi01_jiagou_db` 默认等同；两者字段和 join key 不同。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- `xuebu`、`leader_employee_email_name`、`dazu`、`jingli` 的组织层级含义。
- 是否应使用最新架构还是交易期次/线索期次对应架构。

