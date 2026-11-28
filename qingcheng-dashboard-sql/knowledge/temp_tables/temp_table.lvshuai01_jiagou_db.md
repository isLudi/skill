# temp_table.lvshuai01_jiagou_db

## 1. 临时表用途

2026-11-22核对现行2460线上SQL：2460的SEC抖音退费潜客入选门槛：从本表取得dept_2=SEC的期次、账号集合，关联潜客。

## 2. 来源和刷新方式

来源身份以`sync-qingcheng-market-temp-tables/references/workflow_registry.json`内青橙`period_architecture`登记为准；业务名为青橙期次带班架构。登记上传流程从附件维护累计工作簿，再经新鲜度、唯一键及变化率门禁上传既有平台表。本次只同步知识，不执行上传。刷新依赖登记事件流程；表内覆盖多个qici，有效期依最新成功回执。

## 3. 数据粒度

登记键为`qici + employee_email_name`；按来源期次片段合并。每次上传仍须校验唯一性，不用历史样本替代最新门禁。

## 4. 字段清单

| 字段 | 来源证据 |
|---|---|
| `xiaozu_z` | 登记上传列 |
| `employee_email_prefix` | 登记上传列 |
| `xiaozu` | 登记上传列 |
| `employee_email_name` | 登记上传列 |
| `department` | 登记上传列 |
| `zaizhi` | 登记上传列 |
| `qici` | 登记上传列 |
| `dept_1` | 登记上传列 |
| `dept_2` | 登记上传列 |
| `jingli` | 登记上传列 |

以上为登记上传列，不额外推断数据库物理类型。

## 5. 适用看板

现行2460“转化数据”及已登记转化看板。只证明本次线上SQL的使用关系，不自动扩展其他看板。

## 6. join key

`p.qici = jg.qici and p.employee_email_name = jg.employee_email_name`。其他过滤和匹配保护以当前`resources/raw_sql/data_center_qingcheng_2460.sql`为准。

## 7. 不可复用边界

本表已承接同后缀旧表的维护，仍需按当前数据验证质量，不从市场顾问部引入语义。物理工作簿共享，上传流程只维护dept_1=青橙项目部切片；当前2460读取dept_2=SEC子集。

## 8. 待确认事项

数据库物理类型、每次源新鲜度及最新行数需按需要读取，不能由本登记推断。业务用途和本次SQL使用关系已核验。

## 9. 业务关联补充

按员工与期次关联时保留完整 `qici`，并校验人员键唯一性；只按姓名或期次尾号关联可能跨期放大。不要与全员结果架构表混用。

## 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`xiaozu_z`、`employee_email_prefix`、`xiaozu`、`employee_email_name`、`department`、`zaizhi`、`qici`、`dept_1`、`dept_2`、`jingli`。
