# temp_table.lvshuai01_daoke_1_6_t

## 1. 中文名称

市场顾问到课课次映射表（当前物理绑定）。

## 2. 表用途

市场顾问部当前到课课次临时表。2026-11-28 从生产数据集 2054 完整保存 SQL 回读确认，当前表名为 `temp_table.lvshuai01_daoke_1_6_t`。

## 3. 数据粒度

治理登记按期次、渠道、年级、开课时间与课次管理；具体 Join 键和当前唯一性按目标 SQL 与本次数据核验。

## 4. 查询引擎

Presto。

## 5. 分区字段

无 `dt/hour` 分区，读取限定实际业务期次。

## 6. 强制范围限定字段

`qici` 限定目标完整业务期次；`qudao/channel`、`grade`、`begin_time`、`dow/ke_1` 沿用目标已审定的渠道与课次条件。

## 7. 字段清单

以下为治理登记的七个上传列；平台 SQL 解析结果均为 string。

| 字段名 | 类型 | 字段描述 |
|---|---|---|
| qudao | string | 登记渠道 |
| begin_time | string | 开课时间 |
| qici | string | 完整业务期次 |
| dow | string | 课次相关登记维度，沿用目标用法 |
| grade | string | 年级 |
| ke_1 | string | 课次编号；历史口径使用 1 至 6 |
| channel | string | 映射渠道 |

## 8. 常用过滤条件

`qici = '<YYYYMMDD期>'`，再结合目标现有的渠道、年级及课次范围。

## 9. 常用 join key

以各生产 SQL 已审定的期次、渠道、年级和课次组合为准。上传登记包含 `qici/qudao/grade/begin_time/dow/ke_1` 组合，不据此保证 Join 不放大。

## 10. 常用 SQL 片段

```sql
SELECT qici, qudao, channel, grade, begin_time
FROM temp_table.lvshuai01_daoke_1_6_t
WHERE qici = '<YYYYMMDD期>'
```

此片段仅展示字段与期次范围，须先补齐目标已审定条件才能执行。

## 11. 注意事项

[临时表治理登记](../../../sync-qingcheng-market-temp-tables/references/workflow_registry.json)中的 `market_attendance_schedule` 记录当前平台表名、输入列、期次与渠道约束。这里只同步已登记的市场物理绑定，不把生产 SQL 里的字段用法提升为新的已确认指标契约。

查询保留其实际期次、渠道、年级与时间联接条件；不得仅因渠道共享 CASE 升级而修改课次记录、联接粒度或到课计算。当前上传质量、行数和可用期次需以新回执或实际查询验证。

## 补充业务语义与风险

历史课次映射使用 `qici + qudao + grade + begin_time` 匹配，`ke_1` 表示第 1 至第 6 课而非只能表示首课；历史源曾出现重复键，当前必须重新核验。特殊渠道的首课规则应以目标 SQL 为准。

## 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`qudao`、`begin_time`、`qici`、`dow`、`grade`、`ke_1`、`channel`。
