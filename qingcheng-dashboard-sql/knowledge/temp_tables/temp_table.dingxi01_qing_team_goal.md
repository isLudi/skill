# temp_table.dingxi01_qing_team_goal

## 1. 临时表用途

青橙团队月目标表。当前在 `qingcheng_team_completion_month_raw_20260522.sql` 最终层作为主表，提供月份、学部、小组、大组、目标和层级控制字段，并左连实际业绩。

## 2. 来源和刷新方式

| 项目 | 内容 |
|---|---|
| 创建来源 | 待人工确认 |
| 刷新方式 | 待人工确认 |
| 刷新频率 | 待人工确认 |
| 有效期 | 待人工确认 |

## 3. 数据粒度

疑似为：

```text
month + xuebu + xiaozu + dazu
```

待人工确认 `emye_c` 是否改变展示粒度。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `month` | 待人工确认 | 月份 | join `renchan.moth` |
| `xuebu` | 待人工确认 | 学部 | 最终输出维度 |
| `xiaozu` | 待人工确认 | 小组/主管邮箱 | join `renchan.leader_employee_email_name` |
| `dazu` | 待人工确认 | 大组 | 最终输出维度 |
| `emye_c` | 待人工确认 | 层级/展示控制字段 | `emye_c != '1'` 时展示小组，否则为 `'-'` |
| `goal` | 待人工确认 | 月目标 | 与 `promit`/`promit_4` 对比 |

## 5. 适用看板

- `qingcheng_team_completion_month_raw_20260522`

## 6. join key

```sql
qg.xiaozu = rc.leader_employee_email_name
and qg.month = rc.moth
```

## 7. 不可复用边界

- 默认只用于青橙团队完成度【月】。
- 不得与 `temp_table.dingxi01_qing_team_g_qi` 期目标表混用。
- 目标单位必须与实际业绩金额单位一致，未确认前不得直接计算完成率。
- 如果 `emye_c = '1'` 代表学部/大组层级目标，则小组展示为 `'-'`；具体业务含义待确认。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- `goal` 单位。
- `emye_c` 的枚举和值含义。
- `xiaozu` 字段是否存主管邮箱，还是小组名称。
