# temp_table.dingxi01_qing_qi_moth

## 1. 临时表用途

青橙期次到月份映射表。当前在 `qingcheng_team_completion_month_raw_20260522.sql` 中按 `qici` 补充 `moth`，用于把期次业绩归到月度目标；在 `qingcheng_personal_conversion_raw_20260522.sql` 中按人员架构期次补充月份。

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
qici
```

待人工确认 `qici` 是否唯一。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `qici` | 待人工确认 | 期次 | join `rd_0.qici` |
| `moth` | 待人工确认 | 月份 | 疑似 `month` 拼写，保留历史字段名 |

## 5. 适用看板

- `qingcheng_team_completion_month_raw_20260522`
- `qingcheng_team_completion_period_raw_20260522`（保留在 `wa` 层，但最终目标 join 不依赖月份）
- `qingcheng_personal_conversion_raw_20260522`

## 6. join key

```sql
qm.qici = rd_0.qici
```

个人转化使用：

```sql
qm.qici = qtg.qici
```

## 7. 不可复用边界

- 默认只用于青橙团队完成度【月/期】和青橙个人转化看板。
- 如果后续需要自然月、财务月或期次月不同口径，必须确认 `moth` 的定义。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- `moth` 格式，例如 `2026-05`、`5月` 或其他。
