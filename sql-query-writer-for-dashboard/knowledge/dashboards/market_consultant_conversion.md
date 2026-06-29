# 市场顾问转化看板

## 1. 来源

原始 SQL：`resources/raw_sql/data_center_market_2253_20260628.sql`

入库时间：2026-05-01

最近更新：2026-05-24

## 2. 查询目标

按期次、渠道映射、规则、年级、虚拟部门、经理、主管、小组长和员工聚合线索、有效线索、转化、科目人次、联报、收款、退款、净营收、成本和目标成本，用于市场顾问转化类看板。

## 3. 使用表

| 表名 | 别名 | 用途 |
|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | t1 | 主数据表，提供线索、转化、收款、退款、渠道、部门和员工字段 |
| temp_table.dingxi01_channel_group | channel_grp | 渠道映射到渠道组 |
| temp_table.dingxi01_cost | ct | 按渠道、年级、期次补充单例子成本和目标 |
| temp_table.dingxi01_jiagou_db | jg | 按期次、部门、小组、员工补充架构映射 |
| temp_table.dingxi01_jiagou_zx | zx | 按员工姓名补充小组和经理 |

## 4. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| data | 从全链路明细表抽取基础字段，计算 `period_name`、`d_w`、`xiansuo`、`channel_map`、`grade_1`，并将指标空值转为 0 | `period_name`, `d_w`, `xiansuo`, `channel_map`, `grade_1`, `lead_count`, `valid_lead_count`, `merge_assign_lead_count`, `merge_valid_lead_count`, `lead_period_income_amount`, `lead_period_refund_amount`, `income_amount` |
| zhuanhua | 按看板维度聚合转化和收入指标，2026-05-24 起分组增加 `rule_name`，输出粒度细化到规则级别 | `period_name`, `channel_map`, `rule_name`, `grade_1`, `depart_1`, `depart`, `jingli`, `zhuguan`, `employee_email_name` |
| final select | 补充破单、有效线索门槛、架构、渠道组、成本和目标，从 `rule_name` 派生 `sx_qi`，新增 `jingli_1` | `s_lead`, `podan`, `name1`, `sx_qi`, `jingli_1`, `channel_group`, `cb_cb`, `gl_gl` |

## 5. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| zhuanhua zz | temp_table.dingxi01_channel_group channel_grp | `channel_grp.channel = zz.channel_map` | left join | 渠道映射到渠道组 |
| zhuanhua zz | temp_table.dingxi01_cost ct | `ct.channel = zz.channel_map` + `(ct.grade = zz.grade_1 or ct.grade = '0')` + `ct.qici = zz.period_name` | left join | 补充单例子成本 `cost` 和目标 `goal`；2026-05-24 起当 `grade_1` 无匹配时回退到年级 `'0'` 通配 |
| zhuanhua zz | temp_table.dingxi01_jiagou_db jg | `jg.qici = zz.period_name` + `jg.department = zz.depart` + `jg.xiaozu = zz.zhuguan` + `jg.employee_email_name = zz.employee_email_name` | left join | 补充期次内员工架构映射；该 join 的输出字段未在最终 select 使用，但会影响重复行风险 |
| zhuanhua zz | temp_table.dingxi01_jiagou_zx zx | `zx.employee_email_name = zz.employee_email_name` | left join | 补充 `xiaozu` 和 `jingli_1`（2026-05-24 新增经理字段） |

## 6. where 条件

主表分区条件：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '3' hour, 'HH')
```

主表范围限定：

```sql
section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name = '市场部'
and section_assign_employee_third_level_department_name = '市场顾问部'
and period_mapping_first_level_department_name = 'H业务线'
```

最终结果过滤：

```sql
zz.period_name > '20260424期'
```

## 7. group by 维度

- `period_name`
- `channel_map`
- `rule_name`
- `grade_1`
- `depart_1`
- `depart`
- `jingli`
- `zhuguan`
- `employee_email_name`

## 8. 聚合指标

| 指标名 | SQL 表达式 | 口径说明 | 状态 |
|---|---|---|---|
| lead_count | `sum(case when channel_map = '抖音私域' then merge_assign_lead_count else lead_count end)` | 抖音私域使用合并分配线索数，其他渠道使用原始线索数 | 来自看板 SQL，待业务确认 |
| can_renew_ds_count_a | `sum(case when channel_map = '抖音私域' then merge_valid_lead_count else valid_lead_count end)` | 抖音私域使用合并有效线索数，其他渠道使用原始有效线索数 | 来自看板 SQL，待业务确认 |
| sx_qi | `case when rule_name like '2026年-%' then split_part(rule_name, '-', 2) else split_part(rule_name, '-', 1) end` | 从 `rule_name` 中按 `-` 拆分提取筛选期次标签 | 2026-05-24 新增 |
| xiansuo | `sum(xiansuo)` | 按 `D:\Feishu\0522.txt` 的 `xiansuo` 0/1 规则聚合后的线索标记数 | 2026-05-22 新增 |
| pay_users | `sum(conversion_lead_count)` | 转化人数 | 来自看板 SQL |
| pay_users_on_period | `sum(same_lead_period_conversion_lead_count)` | 当期线索当期转化人数 | 来自看板 SQL |
| pay_users_not_on_period | `sum(conversion_lead_count - same_lead_period_conversion_lead_count)` | 跨期转化人数 | 来自看板 SQL |
| pay_user_subs | `sum(subject_count)` | 转化科目人次 | 来自看板 SQL |
| pay_user_subs_on_period | `sum(same_lead_period_subject_count)` | 当期转化科目人次 | 来自看板 SQL |
| pay_user_subs_not_on_period | `sum(subject_count - same_lead_period_subject_count)` | 跨期转化科目人次 | 来自看板 SQL |
| pay_user_subs_joint | `sum(lb_subject_count)` | 联报人次 | 来自看板 SQL |
| pay_user_subs_joint_onp | `sum(same_lead_period_lb_subject_count)` | 当期联报人次 | 来自看板 SQL |
| pay_user_subs_joint_nonp | `sum(lb_subject_count - same_lead_period_lb_subject_count)` | 跨期联报人次 | 来自看板 SQL |
| trade_income | `sum(income_amount / 100)` | 收款金额，分转元 | 来自看板 SQL |
| trade_refund | `sum(in_pay_period_refund_amount / 100 + non_pay_period_refund_amount / 100)` | 当期支付当期退款 + 往期支付当期退款，分转元 | 来自看板 SQL |
| trade_profit | `sum(income_amount / 100 - in_pay_period_refund_amount / 100 - non_pay_period_refund_amount / 100)` | 净营收，分转元 | 来自看板 SQL |
| xb_trade_income | `sum(same_lead_period_income_amount / 100)` | 当期线索当期收款，分转元 | 来自看板 SQL |
| xb_trade_profit | `sum(same_lead_period_income_amount / 100 - same_lead_period_refund_amount / 100)` | 当期线索当期净营收，分转元 | 来自看板 SQL |
| kk_trade_income | `sum(income_amount / 100 - same_lead_period_income_amount / 100)` | 跨期收款，分转元 | 来自看板 SQL |
| pre_refund | `sum(non_pay_period_refund_amount / 100)` | 往期支付当期退款，分转元 | 来自看板 SQL |
| pp_pmit | `sum(case when d_w = '当期' then lead_period_income_amount / 100 - lead_period_refund_amount / 100 else 0 end)` | `D:\Feishu\0522.txt` 中 `qici` 规则在本看板落为 `d_w` 后的当期 GMV | 2026-05-22 更新 |
| ww_pmit | `sum(case when d_w = '非当期' then income_amount / 100 - in_pay_period_refund_amount / 100 - non_pay_period_refund_amount / 100 else 0 end)` | `D:\Feishu\0522.txt` 中 `qici` 规则在本看板落为 `d_w` 后的非当期 GMV | 2026-05-22 更新 |
| s_lead | `case when can_renew_ds_count_a >= 5 then can_renew_ds_count_a else 0 end` | 有效线索数达到 5 才计入 | 来自看板 SQL，阈值待业务确认 |
| podan | `case when can_renew_ds_count_a >= 5 and trade_profit > 0 then 1 else 0 end` | 有效线索达 5 且净营收为正则破单 | 来自看板 SQL，阈值待业务确认 |
| cb_cb | `coalesce(ct.cost, 0)` | 单例子成本，来自成本临时表 | 待确认成本表维护口径 |
| gl_gl | `coalesce(ct.goal, 0)` | 单例子目标，来自成本临时表 | 待确认成本表维护口径 |

## 9. 前端展示派生公式

以下公式为 2026-05-28 根据看板截图和 `D:\Feishu\task_1370386373_1779954054145.xlsx` 数据集校验后维护的展示口径。生成 SQL 或配置看板指标时应使用聚合后的 `sum(...)` / `count(distinct ...)` 口径。

| 展示指标 | 公式 | 说明 |
|---|---|---|
| 人头转化率（当期） | `ifnull(sum(${pay_users_on_period}) / sum(${can_renew_ds_count_a}), 0)` | 当期支付人数 / 退后线索 |
| 人头转化率（截面） | `ifnull(sum(${pay_users}) / sum(${can_renew_ds_count_a}), 0)` | 截面支付人数 / 退后线索 |
| 订单转化率（当期） | `ifnull(sum(${pay_user_subs_on_period}) / sum(${can_renew_ds_count_a}), 0)` | 当期科目人次 / 退后线索 |
| 订单转化率（截面） | `ifnull(sum(${pay_user_subs}) / sum(${can_renew_ds_count_a}), 0)` | 截面科目人次 / 退后线索 |
| 单效（当期） | `ifnull(sum(${xb_trade_profit}) / sum(${can_renew_ds_count_a}), 0)` | 当期净收款 / 退后线索 |
| 单效（截面） | `ifnull(sum(${trade_profit}) / sum(${can_renew_ds_count_a}), 0)` | 截面净收款 / 退后线索 |
| 破蛋率 | `ifnull(sum(${podan}) / count(distinct ${employee_email_name}), 0)` | 破蛋顾问数 / 接量人力 |
| 拓科率（截面） | `ifnull(sum(${pay_user_subs}) / sum(${pay_users}), 0)` | 科目人次 / 支付用户数 |
| 退费率 | `ifnull(sum(${trade_refund}) / sum(${trade_income}), 0)` | 退款 / 总收款 |
| roi1（mroi） | `ifnull(sum(${trade_profit}) / sum(${lead_count} * ${cb_cb}), 0)` | 净收款 / 市场成本 |
| roi2（smroi） | `ifnull(sum(${trade_profit}) / (sum(${lead_count} * ${cb_cb}) + ${人力成本}), 0)` | 净收款 /（市场成本 + 人力成本）；当前数据集未维护人力成本字段 |
| gmv完成度 | `ifnull(sum(${trade_profit}) / sum(${lead_count} * ${gl_gl}), 0)` | 净收款 / GMV目标 |
| 人产 | `ifnull(sum(${trade_profit}) / count(distinct ${employee_email_name}), 0)` | 净收款 / 接量人力 |

## 10. 可复用 SQL 模式

- `data` CTE：全链路明细表中做 `d_w`、`xiansuo`、渠道 CASE 映射、年级识别和基础指标空值处理。`D:\Feishu\0524.txt` 中输出别名为 `qici` 的当期/非当期 CASE，在本看板中沿用历史字段名 `d_w`。
- 渠道 CASE 有独立最新来源：`resources/raw_sql/market_channel_case_when_0612.sql`（0612 版本新增/细分孟亚飞 1 组/2 组、B站信息流细分、进校直推等输出，并移除或合并一批旧渠道输出值），说明见 `knowledge/sql_patterns/channel_mapping_case_when.md`。
- `zhuanhua` CTE：按期次、渠道、规则、年级、部门和员工聚合转化/收入指标。2026-05-24 起分组增加 `rule_name`，输出粒度细化到规则级别。
- final select：补充成本、目标和架构信息，并派生 `s_lead`、`podan`、`sx_qi`、`jingli_1`。

## 11. 待确认事项

- `data` CTE 内部同时生成 `period_name`，又在部分 CASE 条件中引用 `period_name`；需确认 Presto 环境是否允许同层 select 引用别名，或主表是否本身已有 `period_name` 字段。
- `dt` 使用最近 2 小时，`hour` 使用最近 3 小时，存在时间偏移不一致；需确认是否为平台产出延迟口径。
- SQL 在 `channel_map` CASE 中使用 `third_department_name`、`first_department_name`、`second_department_name`、`virtual_third_department_name`、`virtual_fourth_department_name`、`virtual_fifth_department_name` 等部门字段，但 where 中只显式限定了截面分配部门和期次映射一级部门；复用时需确认这是否满足公司范围限定规范。
- `temp_table.dingxi01_channel_group`、`temp_table.dingxi01_cost`、`temp_table.dingxi01_jiagou_zx` 的真实字段类型和维护来源待补充。
- `temp_table.dingxi01_jiagou_db` join 后未在最终 select 直接使用字段，但可能造成重复行；需确认该表在 join key 下是否唯一。
- `channel_map` 是超长 CASE 规则，历史完整规则以原始 SQL 为准；最新渠道 CASE 已归档为 `resources/raw_sql/market_channel_case_when_0612.sql`。后续改写 SQL 时应优先使用该独立渠道映射知识，除非用户明确要求沿用本看板历史口径。
- `xiansuo` 当前按底层 0/1 标记求和输出；如前端需要作为维度筛选，应另行确认是否改为明细维度，不能直接把当前聚合字段放入 group by。
- 所有指标口径来自历史看板 SQL，尚未经过业务口径文档确认。
