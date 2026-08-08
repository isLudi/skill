# 青橙转化数据 raw

## 1. 来源

`resources/raw_sql/data_center_qingcheng_2460.sql`

入库时间：2026-06-26；当前热修版本：2026-08-02

来源说明：

- 本版由 runtime 已验证 SQL `runtime/tmp/qingcheng_conversion_raw_discounted_podan_final_20260625.sql` 回写为 canonical raw SQL。
- 2026-07-09 将 runtime 热修 SQL `runtime/qingcheng_qici_20260716_patch_20260709/data_center_qingcheng_2460_20260709_qici0716_hotfix.sql` 同步为当前 canonical raw SQL。
- 2026-07-15 将暑期期次改为 SQL 内 `biz_qici_calendar` CTE，并修复 `lead_map` / `bb` 中 `select *` 引发的字段二义性风险。
- 2026-07-26 保留已上线的抖音正价退费潜客渠道归因，并新增 20260722 期起的 B 用户私海保护期课程转移补数分支。
- 2026-07-29 校准暑期运营周期并将 `IP退费 / 春春、朱博士、郭艺` 精确渠道规则同步到 `lead_map` 与 `normal_bb`；2026-08-08 更新为 `0808=08-07~08-11`、`0815=08-12~08-18`、`0821=08-19~08-23`。
- 该 canonical SQL 同时作为 `转化数据看板` 的当前知识库源 SQL。

## 2. 查询目标

沉淀青橙项目部 `转化数据看板` / BI model `2460` 的当前口径。该 SQL 将：

1. 用 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 作为订单营收主表。
2. 用 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 补青橙渠道、年级、主管和有效线索。
3. 用 `finance_dw.dim_finance_order_change_df` 和 `finance_dw.dm_finance_order_refund_detail_df` 识别调课调班/课程转移链路与退 4 / 点睛退 2 口径。
4. 对 20260722 期起“订单转到 B 用户且 B 用户在青橙顾问保护期”的课程转移，使用财务正向支付、私海历史和当前 `lead_map` 补回 B 用户成单。
5. 按顾问、期次、二级渠道、年级、主管汇总支付、退款、净营收、当期营收、破蛋、退款人数、成单周期和线索成本。

本版核心变化：

- `qici` 以 SQL 内 `biz_qici_calendar` 业务日历优先、历史周五逻辑兜底：当前覆盖 `2026-07-07` 至 `2026-08-23`，避免 `20260717期`、`20260724期` 等旧周五期次进入筛选器。
- `qici0` 通过 `biz_qici_calendar` 的 `legacy_short_qici -> short_qici` 映射归一，避免暑期业务期次下的当期指标被误判为往期。
- 线索侧 `bb.qici` 对 `group_period_year + group_period_term` 使用同一份业务日历，保证有效线索量和订单结果在业务期次上对齐。
- `mm -> temp_table.dingxi01_qing_team_jg` 改为 `employee_email_name + qici` join，不再用最新架构回填历史结果期次。
- 营收逻辑统一到 service 主表，并在 service 已带 `transfer_in_amount/transfer_out_amount` 的行上直接剔除内部调课调班金额。
- 原 `dd -> service_gmv` 分支保持不变；保护期课程转移单独生成 `course_transfer_gmv` 后再 union，避免改变原服务订单的退款、课消和分配时间联表。
- `lead_map` 和 `normal_bb` 的一级、二级渠道 CASE 同步维护；`IP退费` 三个精确分支位于宽泛 `%青橙IP%` 与 `%招生退费%` 之前。
- `podan` 改为按折算净收口径统计，不再使用简单的 `promit > 0`。

## 3. 最终输出粒度

| 维度 | 字段 |
|---|---|
| 期次 | `qici` |
| 二级渠道 | `channel_map_2` |
| 渠道大类 | `channel_1` |
| 年级 | `grade_1` |
| 顾问 | `employee_email_name` |
| 主管 | `virtual_direct_leader_email_name` |
| 团队架构 | `dept_2`, `xiaozu`, `dazu`, `jingli` |

订单侧和线索侧在 `mm` 层按以下键对齐：

```text
qici + channel_map_2/qudao + grade_1/grade_0 + employee_email_name/name + virtual_direct_leader_email_name/zhuguan
```

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `gmv` / `dd` | 订单营收、退款、交易时间、课程部门、service 侧调课调班金额 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `lead_map` / `prc` / `bb` | 线索渠道、rule_name、年级、主管、有效线索量 |
| `finance_dw.dim_finance_order_change_df` | `order_change_raw` / `order_change` | 识别调课调班 / 课程转移链路，兼容 `biz_type in (2,7)` |
| `finance_dw.app_finance_performance_extend_details_hf` | `course_transfer_finance_detail` | 课程转移最新子订单的 B 用户、青橙顾问、交易时间和正向支付金额 |
| `service_dw.dwd_crm_assign_private_detail_hf` | `course_transfer_protected_finance` | 判断 B 用户在交易时点是否处于同一青橙顾问私海保护期 |
| `finance_dw.dm_finance_order_refund_detail_df` | `ord` / `re_ke` | 全退链路完课节数，用于退 4 / 点睛退 2 判断 |

## 5. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.dingxi01_qing_team_jg` | 按结果期次补充学部、小组、大组和经理 | 已入库；转化看板当前按 `employee_email_name + qici` 使用 |

## 6. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `lead_map` | 对同一 `lead_id + employee_email_name` 只保留最新分配记录，补渠道、年级、主管 | `lead_id`, `employee_email_name`, `rule_name0`, `grade_0`, `virtual_direct_leader_email_name` |
| `dd` | 订单主明细层，按 `trade_timestamp` 生成结果期次，补课程部门兜底、渠道、主管和 service 侧调课调班金额 | `order_number`, `trade_timestamp`, `qici`, `income_amount`, `refund_amount`, `service_transfer_in_amount_yuan`, `service_transfer_out_amount_yuan` |
| `course_transfer_order_rows` / `course_transfer_order` | 只取 `order_change_type = 1` 的最新子订单并按订单去重 | `order_number`, `transfer_in_amount_yuan`, `transfer_out_amount_yuan` |
| `course_transfer_finance_detail` / `course_transfer_finance` | 取 2026-07-20 起青橙财务正向支付并按订单、B 用户、顾问、科目聚合 | `target_user_number`, `trade_time`, `income_amount` |
| `course_transfer_protected_finance` | 用 B 用户、同顾问和交易时点保护期筛选私海记录 | `lead_id`, `section_assign_time`, `protection_rank` |
| `course_transfer_base` / `course_transfer_dd` | 复用 `lead_map` 补渠道、年级和主管，生成补数订单层 | `channel_map_1`, `rule_name0`, `qici0`, `grade_0` |
| `prc` | 补线索最新 `qici_lead` 和 `section_assign_time` | `lead_id`, `employee_email_name`, `qici_lead`, `section_assign_time`, `rn` |
| `dd_order_scope` | 收敛当前转化结果涉及的订单号范围 | `qici`, `order_number` |
| `order_change_raw` / `order_change_order_map` / `order_change` | 展开调课调班链路的多个订单号并按 `order_number` 聚合 | `order_number`, `refund_type`, `transfer_in_amount_yuan`, `transfer_out_amount_yuan` |
| `ord` / `re_ke` | 补全退费链路完课节数 | `order_number`, `full_refund_chain_finish_lesson_count` |
| `service_gmv` | 原 service 订单层，剔除内部调课调班金额并计算 `refund_4` | `income_amount`, `refund_amount`, `promit_amount`, `refund_4`, `is_on_period` |
| `course_transfer_gmv` | 保护期课程转移补数层；收入和净营收取财务正向金额，退款与 `refund_4` 为 0 | `uid`, `income_amount`, `section_assign_time` |
| `gmv` | `service_gmv union all course_transfer_gmv`，再复用原用户/顾问聚合 | 全部订单层字段 |
| `udd` | 用户层汇总，沉淀折算净收中间量 | `income`, `refund`, `promit`, `p_income`, `H_promit_4`, `n_H_promit_4`, `Y_promit_4` |
| `ud` | 顾问层汇总输出主指标 | `pay_user`, `pay_sub`, `income`, `refund`, `promit`, `p_income`, `refund_user`, `podan`, `sc` |
| `bb` | 线索侧有效线索量 | `v_lead`, `channel_map_1`, `channel_map_2`, `grade_1` |
| `bb_dedup` | 保留完全同维度重复中的一条，并生成 `if_jieliang` | `rn`, `if_jieliang` |
| `mm` | 线索量与订单指标 full outer join | `v_lead`, `pay_user`, `income`, `refund`, `promit`, `podan`, `sc` |
| 最终查询 | 补渠道大类、硬编码线索成本和团队架构 | `cost_lead`, `channel_1`, `dept_2`, `xiaozu`, `dazu`, `jingli` |

## 7. 当前期次逻辑

### 7.1 结果期次 `qici`

订单结果期次来自 `trade_timestamp`，但暑期期次优先按 `biz_qici_calendar` 修正：

```sql
coalesce(trade_cal.qici, <历史周五期次逻辑>)
```

解释：

- Presto `day_of_week(...)=1` 表示周一。
- 周一归上一周周五期次。
- 周二到周日归当前周周五期次。
- `biz_qici_calendar` 是暑期业务日历修正窗口，当前覆盖 `20260710期`、`20260716期`、`20260722期`、`20260728期`、`20260803期`、`20260808期`、`20260815期`、`20260821期`。

### 7.1.1 线索侧期次 `bb.qici`

线索量 CTE `bb` 原本按 `group_period_year + group_period_term` 再推导周五期次。2026-07-15 起，先判断该组合日期是否落入 `biz_qici_calendar`，若命中则同样归业务期次；否则再回退历史周五推导逻辑。

### 7.2 当期判断 `is_on_period`

当期成交仍然沿用 `rule_name` 期次和结果期次的比较：

| 字段 | 生成方式 |
|---|---|
| `qici0` | 默认 `regexp_extract(rule_name, '(\d{4}期)', 1)`；当最终 `qici` 命中 `biz_qici_calendar` 且 `rule_name` 提取值等于 `legacy_short_qici` 时归一为 `short_qici` |
| `period` | `regexp_extract(qici, '\d{4}(\d{4}期)', 1)` |
| `is_on_period` | `case when qici0 = period then 1 else 0 end` |

这一步会影响 `p_pay_user`、`p_pay_sub`、`p_income` 以及前端基于这些字段计算的当期转化率、当期订单转化率和当期单效。

## 8. 营收和破蛋逻辑

### 8.1 订单金额主口径

- 原始收入：`coalesce(gmv.income_amount / 100, 0)`
- 原始退款：`coalesce(gmv.refund_amount / 100, 0)`
- 原始净营收：`income_amount - refund_amount`

### 8.2 service 侧内部调课调班金额剔除

如果 service 主表该行已有内部调课调班金额：

```sql
dd.service_transfer_in_amount_yuan > 0 or dd.service_transfer_out_amount_yuan > 0
```

则该行直接不进入：

- `income_amount`
- `refund_amount`
- `promit_amount`
- `refund_4`

这一步是转化结果数据当前营收逻辑的关键统一口径。

### 8.3 保护期课程转移补数

从 `2026-07-20` 起，只有同时满足以下条件的课程转移最新子订单才补回：

- `order_change_type = 1`、有效最新子订单状态、`biz_type in (2,7)`。
- 财务行属于 `H业务线 / 青橙项目部`，`trade_type = '调课调班'`、支付状态、`price > 0`。
- B 用户在交易时点已分配给同一青橙顾问，尚未关闭、删除或掉海。
- 私海 `lead_id + employee_email_name` 能命中当前 `lead_map`，复用当前渠道 CASE。

该分支不解除原 service 行的内部转单剔除，而是在 `service_gmv` 之外追加 B 用户有效业绩。完整规则见 `knowledge/sql_patterns/qingcheng_protected_course_transfer_conversion.md`。

### 8.4 退 4 / 点睛退 2

`refund_4` 规则：

- `H业务线 + 一对一学部`：直接按退款额计入。
- `clazz_name like '%点睛%'`：仅 `re_lc < 2` 时计入。
- 非点睛班课：仅 `re_lc < 4` 时计入。

### 8.5 破蛋 `podan`

用户层先计算：

```sql
H_promit_4
n_H_promit_4
Y_promit_4
```

顾问层破蛋人数口径：

```sql
count(distinct case
    when ((H_promit_4 - Y_promit_4) + n_H_promit_4 * 0.5) > 0
    then uid end) as podan
```

也就是说，`podan` 已按折算净收统计，不再是简单的 `promit > 0`。

## 9. 青橙范围限定

| 场景 | 字段 | 取值 |
|---|---|---|
| 订单业绩归属 | `performance_second_level_department_name` | `'青橙项目部'` |
| 订单课程一级部门 | `course_first_level_department_name` | 长白名单，当前含 `H业务线`、`LL业务线`、`TUTU`、`TT`、`A业务线`、`EM业务线`、`KA业务线`、`TT业务线`、`创新中心` |
| 订单课程二级部门 | `course_second_level_department_name` | 长白名单，当前覆盖 `青橙项目部`、`创新学部`、`升学规划中心`、`线上考研学部` 等 |
| 线索补充/期次/例子量 | `section_assign_employee_first_level_department_name` | `'H业务线'` |
| 线索补充/期次/例子量 | `section_assign_employee_second_level_department_name` | `'青橙项目部'` |
| 线索补充/期次/例子量 | `period_mapping_first_level_department_name` | `'H业务线'` |

## 10. 分区和小时条件

| 表/CTE | dt 条件 | hour 条件 | 说明 |
|---|---|---|---|
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `now() - 2h` | `now() - 2h` | 订单营收主表 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` (`lead_map`) | `now() - 2h` | `now() - 2h` | 渠道/主管/年级补充 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` (`prc`) | `now() - 2h` | `now() - 3h` | 分配时间 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` (`bb`) | `now() - 2h` | `now() - 2h` | 例子量 |
| `finance_dw.dim_finance_order_change_df` | `now() - 24h` | 无 | 调课调班 / 课程转移链路 |
| `finance_dw.app_finance_performance_extend_details_hf` | `now() - 2h` | `now() - 2h` | 保护期课程转移的财务正向支付 |
| `service_dw.dwd_crm_assign_private_detail_hf` | `now() - 2h` | `now() - 2h` | B 用户交易时点私海保护期 |
| `finance_dw.dm_finance_order_refund_detail_df` | `now() - 24h` | 无 | 全退链路完课节数 |
| `temp_table.dingxi01_qing_team_jg` | 无 `dt/hour` | 无 | 当前按结果期次 `qici` join |

## 11. 关键 join

| 左侧 | 右侧 | join key | 用途 |
|---|---|---|---|
| `gmv` | `lead_map` | `lead_id + performance_employee_email_name = lead_id + employee_email_name` | 补渠道、年级、主管 |
| `dd` | `prc` | `lead_id + performance_employee_email_name`，且 `prc.rn = 1` | 补 `section_assign_time` |
| `gmv` | `re_ke` | `order_number` | 补退费链路完课节数 |
| `gmv` | `order_change` | `order_number` | 识别调课调班 / 课程转移链路 |
| `course_transfer_finance` | `dwd_crm_assign_private_detail_hf` | `target_user_number = user_number + employee_email_name`，并校验交易时点保护窗口 | 找到 B 用户在同顾问名下的有效正常线索 |
| `course_transfer_protected_finance` | `lead_map` | `lead_id + employee_email_name` | 复用当前渠道、年级和主管归因 |
| `bb_dedup` | `ud` | `employee_email_name + qici + channel_map_2 + grade_1 + virtual_direct_leader_email_name` | 合并例子量和订单结果 |
| `mm` | `temp_table.dingxi01_qing_team_jg` | `employee_email_name + qici` | 按结果期次补团队架构 |

## 12. 输出指标

指标集合沉淀到 `knowledge/metrics/qingcheng_conversion_metrics.md`。

| 指标 | 口径简述 |
|---|---|
| `v_lead` | 青橙有效线索量 |
| `pay_user` | 支付用户数 |
| `p_pay_user` | 当期支付用户数 |
| `pay_sub` | 支付科目数（不含定制方案） |
| `p_pay_sub` | 当期支付科目数（不含定制方案） |
| `income` | 综合营收 |
| `refund` | 综合退款 |
| `promit` | 综合净营收 |
| `p_income` | 当期营收 |
| `refund_user` | 综合退款人数（退款金额 > 500） |
| `podan` | 折算净收为正的破蛋用户数 |
| `sc` | 成单周期天数汇总 |
| `cost_lead` | 二级渠道硬编码线索成本 |

## 13. 已知风险

- `qici0` 依赖 `rule_name` 中仍能稳定提取 `\d{4}期`；暑期期次热修当前依赖 `biz_qici_calendar` 中的 `legacy_short_qici -> short_qici` 映射，后续新增期次必须继续补充日历行。
- `bb` 线索侧期次仍来自 `group_period_year + group_period_term`，和订单侧 `trade_timestamp` 不是同一来源；当前仅在 `biz_qici_calendar` 八个暑期运营窗口内做一致性修正。
- `prc` 保持 `hour = now() - 3h`，与 `lead_map` / `bb` 的 `-2h` 存在快照时间差。
- `prc` 的窗口排序只包含 `qici_lead desc`；并列期次可能导致全量重复执行时 `sc` 自身漂移，不能把两次查询的 `sc` 差异直接归因于课程转移补数。
- 保护期课程转移补数从 `2026-07-20` 起生效；若业务要求回刷更早期次，必须单独评估历史增量后再调整日期门禁。
- `bb_dedup` 仅在完全同维度重复时保留一条；如果同顾问同一期次同渠道同年级同主管仍有多条，业务语义需继续确认。
- `cost_lead` 仍是硬编码，成本变更不会自动从配置表生效。
