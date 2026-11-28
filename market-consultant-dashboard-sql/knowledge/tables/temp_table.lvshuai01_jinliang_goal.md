# temp_table.lvshuai01_jinliang_goal

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 中文名称

市场顾问部进量目标表。

## 2. 表用途

同后缀旧名在历史 lead_assign_plan_actual_valid_count.sql 和模板知识中作为进量目标来源。2026-11-28 用户确认更换维护账号，线上目录和现行上传登记均为本表。本次只更新知识，不修改模板或数据中心 SQL。

## 3. 数据粒度

工作流 market_lead_goal 登记键为 qici + channel_2 + grade。上传前校验唯一性；键登记不等于本次最新数据已验证。

## 4. 查询引擎

Presto。

## 5. 分区字段

登记为手工临时表，未声明 dt/hour 分区；本次未读取完整 DDL。

## 6. 强制范围限定字段

使用明确期次；按需要增加渠道 channel_2 和年级 grade，不无界关联大表。

## 7. 字段清单

| 字段 | 登记含义 |
|---|---|
| channel_2 | 渠道 |
| grade | 年级 |
| goal | 进量目标，上传校验非负数值 |
| qici | 工作流按四位数字加“期”校验的源期次 |

字段清单来自现行上传登记，不额外推断数据库物理类型。

## 8. 常用过滤条件

按当前查询的真实期次对齐，不把源期次直接当作八位日期期次；映射和范围由领域 QuerySpec 明确。

## 9. 常用 join key

qici + channel_2 + grade；实际匹配到看板渠道字段前要验证转换关系、唯一性和未匹配情况。

## 10. 常用 SQL 片段

不在本次迁移中生成新的生产 SQL。保留已有业务流程并使用当前登记表名，历史线上 SQL 快照不改写。

## 11. 注意事项

来源以 sync-qingcheng-market-temp-tables/references/workflow_registry.json 的 market_lead_goal 为准。来源文件登记为 leads_goal.xlsx 或带期次的人产表，累计输出为 jinliang_goal.xlsx。每次沿用源新鲜度、行数、变化率、必填列和非负目标门禁；本次不上传、不启停事件服务。
