# temp_table.lvshuai01_qing_team_jg

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 临时表用途

青橙全员结果数据架构表。2026-11-22 核对现行 2460 线上 SQL：最终层按期次和顾问账号补充学部、直属主管、大组和经理。维护账号由 dingxi01 改为 lvshuai01，用户确认业务结构基本一致；不因此声称所有历史消费者已在线切换。

## 2. 来源和刷新方式

来源以 sync-qingcheng-market-temp-tables/references/workflow_registry.json 的青橙 result_architecture 为准。从附件维护累计工作簿，经新鲜度、唯一键和变化率门禁上传既有表。刷新依赖登记事件流程，表内覆盖多个 qici，有效期以最新成功回执为准。本次只同步知识，不上传。

## 3. 数据粒度与 Join

登记键是 qici + employee_email_name。2460 使用 mm.qici=jg.qici 且 mm.employee_email_name=jg.employee_email_name；每次刷新均需唯一性验证，不能退回只按顾问关联。

历史转化 2740 使用 b.name=jg.employee_email_name 且 b.qici=jg.qici；个人转化与团队月/期完成度使用 qtg.employee_email_name=wa.name 且 qtg.qici=wa.qici。个人转化以架构为输出骨架，保留没有业绩匹配的人员；迁移不能改变 LEFT JOIN 或过滤掉未匹配人员。

2026-07-29 旧表快照曾验证 155 名员工、1729 行以及 employee_email_name+qici 唯一；这是历史验证，不是新表当前唯一性或行数证据。

## 4. 字段清单

| 字段 | 来源或用途 |
|---|---|
| employee_name | 登记上传列 |
| employee_email_name | 顾问账号，登记键 |
| email_prefix | 登记上传列 |
| leader_employee_email_name | 直属主管；历史输出别名 xiaozu |
| leader_email_prefix | 登记上传列 |
| dazu | 大组 |
| jingli | 经理 |
| xuebu | 学部；历史输出别名 dept_2 |
| qici | 结果/交易期次，关联必带 |

这些是登记上传列和已有业务用途，数据库类型未因迁移自动获得验证。

## 5. 适用看板

当前 2460 的使用关系已经核实。历史知识还覆盖抖私转化、青橙个人转化和团队完成度月/期；其 raw SQL 作为历史/线上快照保留，复用时核实当前消费者，不把旧 SQL 直接当新表已上线证据。

## 6. join key

同期次 qici + employee_email_name；个人/团队完成度须保持架构骨架及 LEFT JOIN。

## 7. 不可复用边界

本表不等同于 temp_table.lvshuai01_jiagou_db：前者是结果架构，后者是期次带班架构，保留各自字段、范围和 Join。所有消费者必须按同期次同账号回连，不能因换维护人回退到最新架构或仅按员工 Join。表刷新后仍需重复键、源新鲜度及最新行数门禁；组织层级解释以本域登记和当前 SQL 为准。

## 8. 待确认事项

每次实际使用均核对当前新鲜度、数据覆盖和唯一性；不把维护人迁移当作本次数据质量验收。
