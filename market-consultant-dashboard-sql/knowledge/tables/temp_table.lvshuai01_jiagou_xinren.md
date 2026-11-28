# temp_table.lvshuai01_jiagou_xinren

## 1. 中文名称

新人入组期次架构表。

## 2. 表用途

2026-11-28 回读线上生产数据集“新人过程转化数据”2688（menu_set_3874438523397902337）完整保存 SQL，SHA-256 为 6c4449c949438f10219e396b33e2a1283607c405ab3424c6dbc154ac481fba0a。
jiagou_xinren CTE 从本表按 employee_email_prefix + employee_email_name 分组，取 max(new_qici)，最终字段为 new_qici。评优架构及 x_qi_count 来自 zhangjunyan01_pingyou_jg，不来自本表或不完整的 lvshuai01_pingyou_jg。

## 3. 数据粒度

线上 SQL 在 CTE 中压缩为 employee_email_prefix + employee_email_name 一行，max(new_qici) 的取法是当前生产事实，不代表源表原始键已唯一。不能把 new_qici 与 x_qi_count 混同。

## 4. 查询引擎

Presto。业务字段来源为线上 SQL 实际引用，本次未查询数据行或完整 DDL。

## 5. 分区字段

当前 SQL 未使用 dt/hour；不能由此推断全部物理分区定义。

## 6. 强制范围限定字段

如需数据质量探查，应按具体顾问账号或期次有界核对，不使用无界大表关联。

## 7. 字段清单

| 字段 | 已验证使用 |
|---|---|
| employee_email_prefix | CTE 分组及最终关联 prefix |
| employee_email_name | CTE 分组及最终关联账号 |
| new_qici | CTE 取 max，最终独立输出 |

本次只证明 SQL 读取和计算关系，不编造物理字段类型。

## 8. 常用过滤条件

按当前任务的明确顾问和期次约束；未登记可跨部门默认复用的范围。

## 9. 常用 join key

线上 2688 使用 jx.employee_email_prefix=zk.employee_email_prefix 且 jx.employee_email_name=zz.employee_email_name。zk 为原 SQL 的关联键 CTE。不要把它替换为评优架构的 employee_email_name+qici。

## 10. 常用 SQL 片段

生产 CTE 的关键投影为 employee_email_prefix、employee_email_name、max(new_qici)，按前两列分组；这里只保存可复核关系，不提供脱离本域 QuerySpec 的执行计划。

## 11. 注意事项

上传来源依 sync-qingcheng-market-temp-tables/references/workflow_registry.json 的市场顾问维护清单。当前状态、覆盖及字段类型需在实际任务中核对，不自动更新其他账号的评优表，不把成功读回 SQL 当作数据完整性证明。
