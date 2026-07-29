# 线索分配计划与实际有效量指标

## 1. 指标集合名称

线索分配计划与实际有效量指标集合

## 2. 来源

- 看板 SQL：`resources/raw_sql/lead_assign_plan_actual_valid_count.sql`
- 看板文档：`knowledge/dashboards/lead_assign_plan_actual_valid_count.md`
- 入库日期：2026-05-09

## 3. 适用范围

适用于 H 业务线市场部分配规则计划和实际进量、有效量对比分析。

默认范围来自 SQL：

- `section_assign_employee_first_level_department_name = 'H业务线'`
- `section_assign_employee_second_level_department_name = '市场部'`
- `period_mapping_first_level_department_name = 'H业务线'`
- `temp_table.dingxi01_plan_id.group_id is not null`

## 4. 维度字段

| 字段 | 口径 | 来源 |
|---|---|---|
| plan_id | 分配计划 ID | `service_dw.dim_crm_assign_rule_lead_detail_hf.plan_id` |
| group_id | 分配规则组 ID | `service_dw.dim_crm_assign_rule_lead_detail_hf.group_id` 经 `temp_table.dingxi01_plan_id` 过滤；维护表中 `group_id` 单字段可跨期重复 |
| group_period_name | `split_part(rule_name, '-', 1)` | 规则名拆分 |
| qudao | `split_part(rule_name, '-', 3)` | 规则名拆分 |
| nianji | `split_part(rule_name, '-', 4)` | 规则名拆分 |
| rule_name | 分配规则名称 | `service_dw.dim_crm_assign_rule_lead_detail_hf.rule_name` |
| purchase_intention_id | 购买意向 ID | `service_dw.dim_crm_assign_rule_lead_detail_hf.purchase_intention_id` |
| employee_email_name | 顾问姓名/带编号名称 | `service_dw.dim_crm_assign_rule_plan_item_info_hf.employee_email_name` |
| xiaozu | 小组 | `temp_table.dingxi01_jiagou_db.xiaozu` |
| jingli | 经理 | `temp_table.dingxi01_jiagou_db.jingli` |

## 5. 状态派生字段

| 字段 | SQL 口径 | 中文含义 |
|---|---|---|
| employee_state_1 | `case when employee_state = '0' then '未知' when employee_state = '1' then '可分配' when employee_state = '2' then '离职' when employee_state = '3' then '分配达到上限' else '兜底顾问' end` | 顾问分配状态 |
| employee_is_enable | `case when employee_is_enable = '0' then '启用' when employee_is_enable = '1' then '禁用' else '未知' end` | 顾问配置启停状态 |

## 6. 指标

| 指标名 | 中文含义 | SQL 口径 | 待确认 |
|---|---|---|---|
| assign_lead_count | 计划分配数量/已分配数量 | `t.assign_lead_count` | 字段中文含义需确认 |
| assign_ceiling_count | 分配上限数量 | `t.assign_ceiling_count` | 否 |
| lead | 实际线索量 | `sum(bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.lead_count)`，按 `rule_name + employee_email_name` 聚合 | 否 |
| valid_lead | 实际有效线索量 | `sum(bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.valid_lead_count)`，按 `rule_name + employee_email_name` 聚合 | 否 |

## 7. 指标计算粒度和最终输出粒度

- 指标计算粒度：`rule_name + employee_email_name` 汇总实际线索量；计划分配量在 `plan_id + group_id + rule_name + employee_email_name + 状态字段` 粒度去重。
- 最终输出粒度：`fp` 的计划配置粒度，并补充 `xiaozu`、`jingli`、`lead`、`valid_lead`。
- 聚合风险：如果前端继续按小组、经理、渠道或年级聚合，需确认 `temp_table.dingxi01_jiagou_db` 关联是否唯一；重复架构行会放大计划量和实际量。

## 8. 待确认事项

- `assign_lead_count` 是“计划应分配数量”还是“当前已分配数量”需结合字段文档确认。
- `employee_state` 与 `employee_is_enable` 在 SQL 中与字符串比较，真实字段类型待确认；若为整数，生产 SQL 应统一为数值比较或显式 cast。
- `rule_name` 拆分出的 `group_period_name` 仅是期次尾号片段，不等同完整 `qici`。
- `temp_table.dingxi01_plan_id.qici` 同样是期次尾号片段，跨年必须结合 `year`。
- 实际量和计划量使用不同小时分区偏移，需要确认数据延迟口径。
