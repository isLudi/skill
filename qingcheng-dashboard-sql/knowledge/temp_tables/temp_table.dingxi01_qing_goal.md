# temp_table.dingxi01_qing_goal

## 1. 临时表用途

青橙个人目标表。当前在 `qingcheng_personal_conversion_raw_20260522.sql` 中同时提供：

- 个人期次目标 `qici_goal`
- 个人月目标 `moth_goal`

用于个人完成度看板的目标值和完成度计算。

## 2. 来源和刷新方式

| 项目 | 内容 |
|---|---|
| 创建来源 | 待人工确认 |
| 刷新方式 | 待人工确认 |
| 刷新频率 | 待人工确认 |
| 有效期 | 表内覆盖多个 `qici` 和 `month`；当前 canonical personal completion 同时按期次和月份读取 |

## 3. 数据粒度

疑似同时包含两类粒度：

```text
name + qici
name + month
```

当前 SQL 用法：

- `goal_qici`：`group by name, qici`
- `goal_moth`：`group by month, name`

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `name` | 待人工确认 | 顾问姓名/邮箱名 | join `employee_email_name` |
| `qici` | 待人工确认 | 期次 | 生成 `qici_goal` |
| `month` | 待人工确认 | 月份 | 生成 `moth_goal` |
| `goal` | 待人工确认 | 目标值 | 当前 SQL 转成 `decimal(18,2)` |

## 5. 适用看板

- `qingcheng_personal_conversion_raw_20260522`

## 6. join key

期次目标：

```sql
gq.qici = r.qici
and gq.employee_email_name = r.employee_email_name
```

月目标：

```sql
gm.moth = r.moth
and gm.employee_email_name = r.employee_email_name
```

## 7. 不可复用边界

- 当前只作为青橙个人完成度 / 个人转化目标表使用。
- 不能默认替代 `temp_table.dingxi01_qing_team_goal` 或 `temp_table.dingxi01_qing_team_g_qi`。
- 如果未来团队完成度也要用到个人目标，需要重新确认字段语义和粒度。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- `name` 是否稳定等于 `employee_email_name`。
- `goal` 单位是否与 `promit` / `累计净营收` 完全一致。
- 同一顾问同一期次、同一顾问同一月份是否唯一；若不唯一，需要在 SQL 中继续聚合去重。
