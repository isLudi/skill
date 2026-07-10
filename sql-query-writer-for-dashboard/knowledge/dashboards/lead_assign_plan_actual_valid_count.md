# 线索分配计划与实际有效量看板

## 1. 看板名称

线索分配计划与实际有效量看板

## 2. SQL 来源

- 原始 SQL：`resources/raw_sql/lead_assign_plan_actual_valid_count.sql`
- 来源：用户提供 SQL
- 入库日期：2026-05-09

## 3. 查询目的

对比分配规则计划中的顾问计划分配数量、分配上限和启停状态，与全链路宽表中按规则和顾问统计的实际线索量、实际有效线索量，并补充架构小组和经理字段。

该 SQL 适用于排查某一批分配规则下：

- 规则对应顾问是否可分配；
- 顾问计划分配数量和分配上限；
- 实际进入顾问名下的线索量和有效线索量；
- 顾问所在小组和经理。

如果需要将规则侧或实际量侧按最新渠道口径归因，可引用 `resources/raw_sql/market_channel_case_when_0612.sql` 中的渠道 CASE。该 CASE 输出别名为 `qudao`，说明见 `knowledge/sql_patterns/channel_mapping_case_when.md`。

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | vd | 按 `rule_name + employee_email_name` 汇总实际线索量和有效线索量 |
| service_dw.dim_crm_assign_rule_lead_detail_hf | f / fp | 分配规则明细，提供 `plan_id`、`group_id`、`rule_name`、`purchase_intention_id` |
| service_dw.dim_crm_assign_rule_plan_item_info_hf | t | 计划 item 顾问配置，提供顾问状态、计划分配量、分配上限和启停状态 |
| temp_table.dingxi01_plan_id | pl | 规则组白名单/计划组映射，来自 `plan_id.xlsx`，仅保留被维护的 `group_id` |
| temp_table.dingxi01_jiagou_db | db | 根据顾问和期次尾号补充 `xiaozu`、`jingli` |

## 5. CTE 逻辑

| CTE | 作用 |
|---|---|
| vd | 在主全链路表中按分配规则和顾问汇总 `lead_count` 与 `valid_lead_count` |
| fp | 读取规则明细、计划 item 和计划组临时表，得到计划分配配置与顾问可分配状态 |
| final select | 用 `rule_name + employee_email_name` 合并实际量，用 `employee_email_name + group_period_name` 合并架构 |

## 6. join 关系

| 左表/CTE | 左字段 | 右表/CTE | 右字段 | 说明 |
|---|---|---|---|---|
| service_dw.dim_crm_assign_rule_lead_detail_hf | rule_id, plan_id | service_dw.dim_crm_assign_rule_plan_item_info_hf | rule_id, plan_id | 关联规则下顾问计划 item |
| service_dw.dim_crm_assign_rule_lead_detail_hf | group_id | temp_table.dingxi01_plan_id | group_id | 保留已维护计划组；`where pl.group_id is not null` 使左连接等价于半连接过滤。该表 `group_id` 单字段不全局唯一，如输出 `pl.qici/group_name` 需补期次条件 |
| fp | rule_name, employee_email_name | vd | rule_name, employee_email_name | 合并实际线索量和有效线索量 |
| fp | employee_email_name, group_period_name | temp_table.dingxi01_jiagou_db | employee_email_name, substr(qici, -5) | 补充小组和经理；期次使用 `qici` 尾 5 位与规则名拆出的期次片段匹配 |

## 7. 分区和范围限定

实际有效数量主表：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '3' hour, 'HH')
and section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name = '市场部'
and period_mapping_first_level_department_name = 'H业务线'
```

分配规则明细表：

```sql
f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and f.hour = format_datetime(now() - interval '2' hour, 'HH')
and pl.group_id is not null
```

计划 item 表：

```sql
t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and t.hour = format_datetime(now() - interval '2' hour, 'HH')
and t.is_del = '0'
```

临时架构表：

```sql
substr(qici, -5) = fp.group_period_name
and employee_email_name = fp.employee_email_name
```

## 8. group by 维度

`vd` 聚合维度：

- `rule_name`
- `employee_email_name`

`fp` 聚合/去重维度：

- `plan_id`
- `group_id`
- `group_period_name`
- `qudao`
- `nianji`
- `rule_name`
- `purchase_intention_id`
- `employee_email_name`
- `employee_state_1`
- `assign_lead_count`
- `assign_ceiling_count`
- `employee_is_enable`

## 9. 派生字段和指标

| 字段/指标 | SQL 口径 | 说明 |
|---|---|---|
| group_period_name | `split_part(f.rule_name, '-', 1)` | 从规则名拆出的期次片段 |
| qudao | `split_part(f.rule_name, '-', 3)` | 从规则名拆出的渠道片段 |
| nianji | `split_part(f.rule_name, '-', 4)` | 从规则名拆出的年级片段 |
| employee_state_1 | `employee_state` 枚举映射 | 0 未知、1 可分配、2 离职、3 分配达到上限，其余兜底顾问 |
| employee_is_enable | `employee_is_enable` 枚举映射 | 0 启用、1 禁用，其余未知 |
| assign_lead_count | `t.assign_lead_count` | 计划已分配或计划分配量字段，含义待确认 |
| assign_ceiling_count | `t.assign_ceiling_count` | 分配上限 |
| lead | `sum(lead_count)` | 实际线索量 |
| valid_lead | `sum(valid_lead_count)` | 实际有效线索量 |
| xiaozu | `temp_table.dingxi01_jiagou_db.xiaozu` | 小组 |
| jingli | `temp_table.dingxi01_jiagou_db.jingli` | 经理 |

## 10. 待确认事项

- `service_dw.dim_crm_assign_rule_plan_item_info_hf` 字段结构来自用户 SQL 推断，真实字段类型、中文名、数据粒度和主键唯一性待确认。
- `temp_table.dingxi01_plan_id` 已确认来源为 `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\plan_id.xlsx`，字段为 `year/qici/group_id/group_name`；`qici + group_id` 唯一，`group_id` 单字段不全局唯一。
- `vd` 使用 `dt = now() - 2 hour` 但 `hour = now() - 3 hour`，和 `fp/t` 的 `hour = now() - 2 hour` 不一致；是否为业务延迟口径需确认。
- `vd` 只限定了截面分配一级/二级部门和期次映射一级部门，未限定 `section_assign_employee_third_level_department_name`、`period_mapping_second_level_department_name`；生成新 SQL 时应按需求补充或保留占位。
- `rule_name` 通过 `split_part(..., '-', n)` 拆期次、渠道和年级，依赖规则名格式稳定；规则名中若渠道含 `-` 会导致拆分错位。
- 分配规则表本身没有完整渠道 CASE 依赖字段；若要按最新渠道口径识别“抖音私信”等渠道，应优先在全链路宽表中按 `market_channel_case_when_0612.sql` 派生 `qudao/channel_map`，或确认规则表是否具备 CASE 所需字段。
- `fp` CTE 中 `group by` 后又 `order by`，在 CTE 内排序对最终结果通常无稳定语义；改写生产 SQL 时建议将排序放到最终输出层。
- `temp_table.dingxi01_jiagou_db` 通过 `substr(qici, -5)` 关联期次尾号，可能跨年份重复；若数据跨多年，建议改为完整期次匹配。
