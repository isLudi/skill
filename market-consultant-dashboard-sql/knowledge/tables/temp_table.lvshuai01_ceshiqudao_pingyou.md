# temp_table.lvshuai01_ceshiqudao_pingyou

## 1. 中文名称

评优测试渠道指标临时表。

## 2. 表用途

市场顾问部评优测试渠道指标表。手工临时表登记来源为 `ceshiqudao_pingyou.xlsx`；历史模型 2644 曾按 `name` 聚合后与员工姓名关联。是否仍被某个线上模型使用，应回读该模型的当前 SQL。

## 3. 数据粒度

候选粒度为 `qici + qudao + name`；当前唯一性未验证。

## 4. 查询引擎

Presto。

## 5. 分区字段

未取得完整分区 DDL；登记为稳定手工表，探索时保留目标业务范围。

## 6. 强制范围限定字段

探索时按请求限定期次和员工。历史 2644 采用的业务范围不自动变更。

## 7. 字段清单

| 字段 | 平台解析类型 | 说明 |
|---|---|---|
| qici | string | 期次 |
| qudao | string | 渠道 |
| name | string | 员工姓名 |
| gmv | string | 历史 SQL 用作比值分子 |
| gmv_goal | string | 历史 SQL 用作比值分母 |
| gmv_rate | string | 原始维护比率字段 |

历史 SQL 计算 `gmv` 与 `gmv_goal` 前显式转换类型；历史 2644 CTE 未直接使用 `gmv_rate`。

## 8. 常用过滤条件

按请求指定期次、员工和渠道；探索结果应限制返回行数。

## 9. 常用 join key

历史 2644 先按 `name` 聚合再关联 `employee_email_name`；不得默认明细姓名唯一或将其等同邮箱前缀。

## 10. 常用 SQL 片段

```sql
SELECT qici, qudao, name, gmv, gmv_goal, gmv_rate
FROM temp_table.lvshuai01_ceshiqudao_pingyou
WHERE qici = '<业务期次>'
LIMIT 20
```

## 11. 注意事项

原表没有部门列，业务和期次范围依目标 SQL 明确；不能仅凭结构相同扩大指标或人员范围。具体行数、覆盖期次和数据质量需另行核验。

## 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`qici`、`qudao`、`name`、`gmv`、`gmv_goal`、`gmv_rate`。
