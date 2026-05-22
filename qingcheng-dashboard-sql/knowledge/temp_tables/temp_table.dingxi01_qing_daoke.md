# temp_table.dingxi01_qing_daoke

## 1. 临时表用途

青橙课次映射表。当前用于将青橙线索对应的上课明细映射到第 1 至第 6 讲课次，支持计算到课和有效到课。

已入库使用场景：

- `qingcheng_process_data_raw_20260522.sql`：只使用 `ke_1 = '1'` 计算首节到课和首节有效到课。
- `qingcheng_daoke_raw_20260522.sql`：使用 `ke_1 in ('1','2','3','4','5','6')` 计算第 1 至第 6 讲到课和有效到课。

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
qici + qudao + grade + begin_time
```

待人工确认是否唯一。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `qici` | 待人工确认 | 期次 | 与 `dk.qici` join |
| `qudao` | 待人工确认 | 二级渠道 | 与 `dk.channel_map_2` join |
| `grade` | 待人工确认 | 年级 | 与 `dk.grade_1` join |
| `begin_time` | 待人工确认 | 开课时间 | 与 `dk.begin_time` join |
| `ke_1` | 待人工确认 | 课次编号 | 当前 SQL 使用 `'1'` 至 `'6'`；字段名不等同于“只表示第一讲” |

## 5. 适用看板

- `qingcheng_process_data_raw_20260522`
- `qingcheng_daoke_raw_20260522`

## 6. join key

```sql
dk.qici = ke.qici
and dk.channel_map_2 = ke.qudao
and dk.grade_1 = ke.grade
and dk.begin_time = ke.begin_time
```

## 7. 不可复用边界

- 默认仅用于青橙过程数据和青橙到课看板。
- 不得默认用于其他部门或其他青橙看板，除非确认该表的刷新范围和课次定义一致。
- 如果 `qudao` 与 `channel_map_2` 的映射规则更新，必须同步核对本表。
- 如果新增第 7 讲及以后课次，必须确认 `ke_1` 值域并更新到课指标文档。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- `ke_1` 的类型和值域。
- 同一 `qici + qudao + grade + begin_time` 是否会多行。

