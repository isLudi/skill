# temp_table.dingxi01_qing_team_jg

## 1. 临时表用途

青橙团队架构表。当前在 `data_center_qingcheng_2460.sql` 最终层按员工姓名补充学部、小组、大组和经理；在 `qingcheng_team_completion_month_raw_20260522.sql` 和 `qingcheng_team_completion_period_raw_20260522.sql` 中补充直属主管，用于和团队目标表合并；在 `qingcheng_personal_conversion_raw_20260522.sql` 中作为个人期次输出骨架。

## 2. 来源和刷新方式

| 项目 | 内容 |
|---|---|
| 创建来源 | 待人工确认 |
| 刷新方式 | 待人工确认 |
| 刷新频率 | 待人工确认 |
| 有效期 | 表内覆盖多个 `qici`；当前 canonical 转化 raw、个人转化和团队完成度月/期都按结果期次/交易期次 join |

## 3. 数据粒度

疑似为：

```text
qici + employee_email_name
```

待人工确认同一员工在同一期次是否唯一。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `qici` | 待人工确认 | 期次 | 当前 canonical 转化 raw、个人转化和团队完成度月/期都按 `qici` 回连 |
| `employee_email_name` | 待人工确认 | 员工姓名/邮箱名 | join `mm.employee_email_name` |
| `xuebu` | 待人工确认 | 学部 | 最终别名 `dept_2` |
| `leader_employee_email_name` | 待人工确认 | 直属主管/小组负责人 | 最终别名 `xiaozu` |
| `dazu` | 待人工确认 | 大组 | 最终输出字段 |
| `jingli` | 待人工确认 | 经理 | 最终输出字段 |

## 5. 适用看板

- `qingcheng_conversion_raw_20260626`
- `qingcheng_team_completion_month_raw_20260522`
- `qingcheng_team_completion_period_raw_20260522`
- `qingcheng_personal_conversion_raw_20260522`

## 6. join key

```sql
mm.employee_email_name = jg.employee_email_name
and mm.qici = jg.qici
```

个人转化使用：

```sql
qtg.employee_email_name = wa.name
and qtg.qici = wa.qici
```

该 SQL 以 `temp_table.dingxi01_qing_team_jg` 为主表，保留没有业绩匹配的架构人员。

团队完成度【月/期】使用：

```sql
qtg.employee_email_name = wa.name
and qtg.qici = wa.qici
```

## 7. 不可复用边界

- 默认只作为青橙转化、青橙团队完成度【月/期】和青橙个人转化看板的团队架构表。
- 当前 canonical 转化 raw 已按 `mm.qici = jg.qici` 使用期次架构；如果后续改回最新架构，会重新引入历史期次漂移风险。
- 个人转化和团队完成度月/期当前都按 `qtg.qici = wa.qici` 使用期次架构；如果后续改回最新架构，会重新引入跨期漂移风险。
- 不得与 `temp_table.dingxi01_jiagou_db` 默认等同；两者字段和 join key 不同。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- `xuebu`、`leader_employee_email_name`、`dazu`、`jingli` 的组织层级含义。
- 团队完成度月/期与个人转化当前都已切到交易期次/结果期次架构；若未来调整，需要同步回归三份完成度 SQL。
- 个人转化场景下是否一人一期唯一；若不唯一会放大个人业绩。
