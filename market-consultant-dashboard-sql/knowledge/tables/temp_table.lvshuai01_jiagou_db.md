# temp_table.lvshuai01_jiagou_db

## 1. 中文名称

市场顾问期次带班架构映射表（当前物理绑定）。

## 2. 表用途

市场顾问部当前使用的期次带班架构临时表。2026-11-28 从生产数据集 2054 完整保存 SQL 回读确认，当前表名为 `temp_table.lvshuai01_jiagou_db`。本条记录当前物理绑定，不从其他部门推断市场业务口径。

该物理表由两部门共用，市场切片须限定 `dept_1 = '市场顾问部'`；青橙切片由青橙知识库独立定义。相同表名不代表可混用两个部门的数据范围、指标或架构含义。

## 3. 数据粒度

市场登记的业务键为 `qici + employee_email_prefix`。当前快照的键唯一性、重复行和空值需实测，不继承旧表扫描数值。

## 4. 查询引擎

Presto。天宫任务使用的 Spark 查询另按其实际 SQL 审阅。

## 5. 分区字段

无 `dt/hour` 分区，按期次和本部门切片限定读取。

## 6. 强制范围限定字段

- 市场切片：`dept_1 = '市场顾问部'`。
- 期次：`qici` 使用当前目标所需的完整期次。
- `department`、`dept_2`、`zaizhi` 沿用目标已审定范围，不为渠道 CASE 升级修改它们。

## 7. 字段清单

以下为治理登记的上传列；平台 SQL 解析结果均为 string。

| 字段名 | 类型 | 字段描述 |
|---|---|---|
| xiaozu_z | string | 小组长邮箱前缀 |
| employee_email_prefix | string | 顾问邮箱前缀 |
| xiaozu | string | 小组长姓名 |
| employee_email_name | string | 顾问姓名 |
| department | string | 展示部门 |
| zaizhi | string | 在职标记，按目标既有条件解释 |
| qici | string | 完整业务期次 |
| dept_1 | string | 部门切片，本域限定市场顾问部 |
| dept_2 | string | 本域城市或团队架构 |
| jingli | string | 经理姓名 |

## 8. 常用过滤条件

`dept_1 = '市场顾问部' AND qici = '<YYYYMMDD期>'`。模板占位值需在执行前解析。

## 9. 常用 join key

`qici + employee_email_prefix` 为市场登记键；Join 前按当前 SQL 的去重合同核验，不能据登记键推断当前数据唯一。

## 10. 常用 SQL 片段

```sql
SELECT qici, employee_email_prefix, xiaozu, jingli
FROM temp_table.lvshuai01_jiagou_db
WHERE dept_1 = '市场顾问部'
  AND qici = '<YYYYMMDD期>'
```

此片段仅说明本域范围，不能直接进入生产执行。

## 11. 注意事项

[临时表治理登记](../../../sync-qingcheng-market-temp-tables/references/workflow_registry.json)中的 `market_period_architecture` 登记当前平台表名、目标列、`qici + employee_email_prefix` 键与 `dept_1` 市场范围。生产 SQL 的实际字段、去重与联接逻辑须从实时 SQL 核验，本记录不授权更换生产联接或缩小部门范围。

新任务不得从历史知识快照推断此表的行数、最新期次、上传成功状态或当前数据质量；这些信息需读取当前上传回执或执行受治理查询。

## 补充业务语义与风险

历史关联包含完整期次与员工邮箱前缀；其他 SQL 曾使用员工姓名、部门、小组或期次尾号。使用期次尾号跨年可能错配，应核验目标粒度并检查重复。

## 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`xiaozu_z`、`employee_email_prefix`、`xiaozu`、`employee_email_name`、`department`、`zaizhi`、`qici`、`dept_1`、`dept_2`、`jingli`。
