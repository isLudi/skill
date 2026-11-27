# temp_table.lvshuai01_qing_team_jg

## 1. 临时表用途

2026-11-22核对现行2460线上SQL：2460最终层补充学部、主管、大组及经理；按期次、账号唯一键回填，并由SQL重复键门禁保护。

## 2. 来源和刷新方式

来源身份以`sync-qingcheng-market-temp-tables/references/workflow_registry.json`内青橙`result_architecture`登记为准；业务名为全员结果数据架构。登记上传流程从附件维护累计工作簿，再经新鲜度、唯一键及变化率门禁上传既有平台表。本次只同步知识，不执行上传。刷新依赖登记事件流程；表内覆盖多个qici，有效期依最新成功回执。

## 3. 数据粒度

登记键为`qici + employee_email_name`；按来源期次片段合并。每次上传仍须校验唯一性，不用历史样本替代最新门禁。

## 4. 字段清单

| 字段 | 来源证据 |
|---|---|
| `employee_name` | 登记上传列 |
| `employee_email_name` | 登记上传列 |
| `email_prefix` | 登记上传列 |
| `leader_employee_email_name` | 登记上传列 |
| `leader_email_prefix` | 登记上传列 |
| `dazu` | 登记上传列 |
| `jingli` | 登记上传列 |
| `xuebu` | 登记上传列 |
| `qici` | 登记上传列 |

以上为登记上传列，不额外推断数据库物理类型。

## 5. 适用看板

现行2460“转化数据”及已登记转化看板。只证明本次线上SQL的使用关系，不自动扩展其他看板。

## 6. join key

`mm.qici = jg.qici and mm.employee_email_name = jg.employee_email_name`。其他过滤和匹配保护以当前`resources/raw_sql/data_center_qingcheng_2460.sql`为准。

## 7. 不可复用边界

本表身份不与历史dingxi01同后缀表默认等同，不从市场顾问部引入语义。只能在同期次、同账号回连，SQL中不唯一键阻断，不得退回仅按顾问关联。

## 8. 待确认事项

数据库物理类型、每次源新鲜度及最新行数需按需要读取，不能由本登记推断。业务用途和本次SQL使用关系已核验。
