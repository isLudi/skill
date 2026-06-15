# 青橙转化数据 raw

## 1. 来源

`resources/raw_sql/qingcheng_conversion_raw_20260615.sql`

入库时间：2026-06-15

## 2. 查询目标

沉淀青橙项目部转化数据 SQL。该 SQL 将订单业绩明细、线索期次、青橙有效线索量和最新团队架构合并，输出顾问/主管/渠道/年级维度的支付用户、支付科目、营收、退款、净营收、当期收入、破单、退款用户、成单周期、截量标记和线索成本等指标。

20260615 版本核心变更：期次对齐机制从"交易时间周对齐 vs 线索期次"改为"rule_name 前 4 位提取 vs 交易时间周对齐提取"，渠道映射新增"青橙IP"分支，并调整 hour 偏移。

## 3. 最终输出粒度

| 维度 | 字段 |
|---|---|
| 期次 | `qici` |
| 二级渠道 | `channel_map_2` |
| 渠道大类 | `channel_1` |
| 年级 | `grade_1` |
| 员工 | `employee_email_name` |
| 主管 | `virtual_direct_leader_email_name` |
| 团队架构 | `dept_2`, `xiaozu`, `dazu`, `jingli` |

该版本将线索侧与订单侧的对齐键扩展为顾问 + 期次 + 二级渠道 + 年级 + 主管，不再通过缺少年级的去重逻辑吞掉某个年级的例子数。

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `gmv` / `dd` | 订单业绩、营收、退款、课程和业绩归属明细 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `ld`, `prc`, `bb` | 青橙线索补充、渠道年级映射、线索期次和有效线索量 |

## 5. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.dingxi01_qing_team_jg` | 最新青橙团队架构表，按员工补充学部、小组、大组和经理 | 已从 SQL 入库，来源/刷新方式待人工确认 |

## 6. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `dd` | 订单业绩明细，补充青橙渠道和年级，计算收入、退款、净营收、交易期次。0615版新增 `rule_name0`（CASE映射渠道）、`qici0`（rule_name提取期次）、`period`（交易时间提取期次） | `lead_id`, `original_order_user_number`, `performance_employee_email_name`, `income_amount`, `refund_amount`, `promit_amount`, `qici`, `qici0`, `period`, `rule_name0`, `grade_0` |
| `prc` | 取青橙线索期次和分配时间，按 `lead_id` 取最新 `qici_lead`。0615版 `qici_lead` 改为 `regexp_extract(rule_name, '(\d{4}期)', 1)` | `lead_id`, `employee_email_name`, `qici_lead`, `section_assign_time`, `rn` |
| `gmv` | 将业绩明细与线索期次合并，标记是否当期成交。0615版 `is_on_period = dd.qici0 = dd.period` | `is_on_period`, `uid`, `name`, `zhuguan`, `sub`, `income_amount`, `refund_amount`, `promit_amount` |
| `udd` | 先按用户聚合订单 | `pay_sub`, `p_pay_sub`, `income`, `refund`, `promit`, `p_income`, `sc` |
| `ud` | 再按顾问 + 期次 + 二级渠道 + 年级 + 主管聚合订单指标 | `pay_user`, `p_pay_user`, `pay_sub`, `income`, `refund`, `promit`, `podan`, `sc` |
| `bb` | 青橙有效线索量，按期次、渠道、年级、主管、顾问聚合。0615版渠道映射新增"青橙IP"分支 | `v_lead`, `channel_map_1`, `channel_map_2`, `grade_1` |
| `bb_dedup` | 保留年级维度的线索对齐层，并生成 `if_jieliang` | `rn`, `if_jieliang` |
| `mm` | 线索量与业绩指标 full outer join | 合并后的核心转化指标 |
| 最终查询 | 补充硬编码线索成本、渠道大类和最新团队架构 | `cost_lead`, `channel_1`, `dept_2`, `xiaozu`, `dazu`, `jingli` |

## 7. 0615 版期次对齐机制（核心变更）

本版引入双期次字段替代旧版单期次对齐：

| 字段 | 提取方式 | 含义 | 示例 |
|---|---|---|---|
| `qici0` | `regexp_extract(rule_name, '(\d{4}期)', 1)` | 从原始 rule_name 前 4 位提取期次 | 从 `2026年-0612期-短期班-抖音私信-抖音私信-高中` 提取 `0612期` |
| `period` | `regexp_extract(qici, '\d{4}(\d{4}期)', 1)` | 从交易时间的周对齐 qici 中提取日期部分 | 从 `20260612期` 提取 `0612期` |
| `is_on_period` | `case when dd.qici0 = dd.period then 1 else 0 end` | 判断 rule_name 期次是否等于交易时间期次 | — |
| `prc.qici_lead` | `regexp_extract(rule_name, '(\d{4}期)', 1)` | 线索期次同样从 rule_name 提取 | — |

旧版（0614）的 `is_on_period = dd.qici = prc.qici_lead` 已废弃。

## 8. 青橙范围限定

| 位置 | 范围字段 | 取值 |
|---|---|---|
| 订单表 `gmv` | `performance_second_level_department_name` | `'青橙项目部'` |
| 订单表 `gmv` | `course_first_level_department_name` | 多业务线白名单，包含 `H业务线` 等 |
| 订单表 `gmv` | `course_second_level_department_name` | 长白名单，包含 `青橙项目部` |
| 线索补充 `ld` | `section_assign_employee_first_level_department_name` | `'H业务线'` |
| 线索补充 `ld` | `section_assign_employee_second_level_department_name` | `'青橙项目部'` |
| 线索补充 `ld` | `period_mapping_first_level_department_name` | `'H业务线'` |
| 线索期次 `prc` | `section_assign_employee_first_level_department_name` | `'H业务线'` |
| 线索期次 `prc` | `section_assign_employee_second_level_department_name` | `'青橙项目部'` |
| 线索量 `bb` | `section_assign_employee_first_level_department_name` | `'H业务线'` |
| 线索量 `bb` | `section_assign_employee_second_level_department_name` | `'青橙项目部'` |
| 线索量 `bb` | `period_mapping_first_level_department_name` | `'H业务线'` |

## 9. 分区和小时条件

| 表/CTE | dt 条件 | hour 条件 | 说明 |
|---|---|---|---|
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` (dd) | `now() - 2h` | `now() - 2h` | 订单业绩明细（0615 从 -3h 改为 -2h） |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` (ld) | `now() - 2h` | `now() - 2h` | 线索补充（0615 从 -3h 改为 -2h） |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` (prc) | `now() - 2h` | `now() - 3h` | 线索期次（保持 -3h） |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` (bb) | `now() - 2h` | `now() - 2h` | 线索量（0615 从 -3h 改为 -2h） |
| `temp_table.dingxi01_qing_team_jg` | 无 `dt/hour` | `qici = (select max(qici) ...)` | 最新青橙团队架构 |

## 10. join 关系

| 左侧 | 右侧 | join key | 用途 |
|---|---|---|---|
| `gmv` | `ld` | `gmv.lead_id = ld.lead_id and ld.employee_email_name = gmv.performance_employee_email_name` | 给订单明细补充青橙规则渠道、年级和主管 |
| `dd` | `prc` | `prc.lead_id = dd.lead_id and prc.employee_email_name = dd.performance_employee_email_name and prc.rn = 1` | 判断订单期次是否等于最新线索期次 |
| `bb_dedup` | `ud` | `employee_email_name + qici + channel_map_2 + grade_1 + virtual_direct_leader_email_name` 对 `name + qici + qudao + grade_0 + zhuguan` | 合并线索量和顾问业绩指标，并保留年级维度 |
| `mm` | `temp_table.dingxi01_qing_team_jg jg` | `mm.employee_email_name = jg.employee_email_name` | 补充最新团队架构 |

## 11. 渠道、年级、截量和成本映射

转化 SQL 的渠道/年级映射已追加到 `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`。

### 11.1 渠道映射（20260615 更新）

`rule_name0`（dd CTE ld 子查询）和 `channel_map_2`（bb CTE）新增"青橙IP"作为第一优先级分支：

```
%青橙IP% → '青橙IP'
%私域会话% → '私域会话'
%私域表单% → '私域表单'
...（其余同 0614 版）
```

### 11.2 硬编码字段

| 字段 | 规则 |
|---|---|
| `if_jieliang` | `case when v_lead > 5 then employee_email_name else '0' end` |
| `cost_lead` | `亚飞IP = 120`、`武汉图书 = 20`、`抖音私信 = 130`、`进校 = 70`、其他 `0` |
| `channel_1` | `%私域%` 或 `%公域%` -> `私域`；`%IP%` -> `IP`；`%图书%` -> `图书`；`%SEC未加好友%/%SEC首期掉海%/%公海%/%顾问未加好友%` -> `公海`；`%抖音私信%` -> `抖音私信`；`%训练营%` -> `青橙训练营`；`%进校%` -> `进校` |

## 12. 转化指标

指标集合沉淀到 `knowledge/metrics/qingcheng_conversion_metrics.md`。

| 指标 | 口径简述 |
|---|---|
| `v_lead` | 青橙有效线索量 |
| `pay_user` | 支付收入大于 0 的用户数 |
| `p_pay_user` | 当期收入大于 0 的用户数 |
| `pay_sub` | 非定制方案支付科目数 |
| `p_pay_sub` | 当期且非定制方案支付科目数 |
| `income` | 总营收，分为元 |
| `refund` | 退款金额，分为元 |
| `promit` | 净营收，`income - refund` |
| `p_income` | 当期收入（`is_on_period = 1` 的收入） |
| `refund_user` | 退款金额大于 500 的用户数 |
| `podan` | 净营收大于 0 的用户数 |
| `sc` | 成单周期天数汇总 |
| `cost_lead` | 二级渠道硬编码线索成本 |

## 13. 已知风险和待确认事项

- SQL 中存在 Presto 三参数 `date_add('day', n, expr)`，公司查询平台可能按 Hive 两参数函数解析；后续生成新 SQL 时建议逐步改为 `interval` 写法。
- `bb_dedup` 已补上年级和主管维度，解决同顾问同渠道跨年级吞数问题；但如果同顾问同一期次同渠道同年级同主管仍有多行，仍由 `row_number()` 保留一条，具体业务语义待人工确认。
- `full outer join ud` 会保留无 `bb` 的业绩记录；如果只分析例子数，需明确是否过滤掉纯订单侧行。
- `sc` 是用户层成单周期 `date(max(section_assign_time))` 到首个收入订单日期的差值，再在顾问层 `sum(sc)`；是否应取平均或中位数待确认。
- `promit` 疑似为 `profit`/净营收拼写，保留历史 SQL 字段名。
- `if_jieliang` 的业务语义仅能从历史 SQL 推断为截量标记，最终含义待人工确认。
- **0615 新增风险**：`qici0` 和 `qici_lead` 通过 `regexp_extract(rule_name, '(\d{4}期)', 1)` 提取，依赖 rule_name 前 4 位必须是期次号。如果 rule_name 格式变化（如"2026年-0612期"变为其他格式），提取将失败。
- **0615 新增风险**：`period` 通过 `regexp_extract(qici, '\d{4}(\d{4}期)', 1)` 从周对齐 qici 提取，正则假设 qici 格式为 `YYYYMMDD期`。
- **0615 新增风险**：`is_on_period` 比较 `qici0 = period`，两个字段都只取后 4 位数字+期（如"0612期"），如果年月跨年（如"0101期"），可能误匹配。
- **0615 新增风险**：dd/ld/bb 的 hour 偏移改为 `-2h`，但 prc 保持 `-3h`。跨 CTE 的 hour 不一致可能导致数据快照时间点不同。
