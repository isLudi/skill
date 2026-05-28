# H业务线二级部门转化看板

## 1. 来源

原始 SQL：`resources/raw_sql/h_biz_line_department_conversion.sql`

入库时间：2026-05-24

## 2. 查询目标

按 H业务线下市场部、精品班学部、青橙项目部、菁英班学部四个二级部门，按期次、渠道映射、规则、年级和虚拟部门聚合线索、有效线索、首 call 任务、24h 首呼、加微、转化、科目人次、联报、收款、退款和净营收。输出粒度为部门级别（非顾问个体），覆盖渠道分组和破单派生指标。

## 3. 使用表

| 表名 | 别名 | 用途 |
|---|---|---|
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | t1 / data_base | 主数据表，提供线索、转化、收款、退款、渠道、部门和员工字段 |
| gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf | first_call_task | 首 call 任务表（2026-05-22 起强制口径），提供 `is_f_call` 标记 |
| finance_dw.dim_finance_employee_df | employee_map | 员工维表，通过 `account_id` 桥接首 call 任务到员工姓名 |
| temp_table.shenbaoxin_channel_group | channel_grp | 渠道分组映射表（申保鑫），通过 `channel = channel_map` 补充 `channel_group` |

## 4. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| data_base | 从全链路明细表抽取全字段并计算 `calc_period_name`；注意使用 `select t1.*`，违反知识库规则但来自用户原始 SQL | `calc_period_name` 及全表字段 |
| data | 从 data_base 选取业务字段，计算 `channel_map`、`first_call_in_24h`、`is_friend_lead`，并将指标空值转为 0 | `period_name`, `channel_map`, `rule_name`, `lead_count`, `valid_lead_count`, `income_amount` |
| first_call_task | 从首 call 任务表取 `user_id + first_call_status + account_id` | `user_id`, `account_id`, `first_call_status` |
| employee_map | 从员工维表按 `account_id` 取第一条 `employee_email_name`，用 `row_number()` 去重 | `account_id`, `employee_email_name` |
| f_call0 | 首 call + 员工维表桥接聚合：若 `first_call_status = 3`（已完成）则标记 1 | `user_id`, `assign_employee_email_name`, `call_answer_lead_count` |
| data_with_process | 将 `is_f_call` 标志左连接回 `data` | data 全字段 + `is_f_call` |
| zhuanhua | 按看板维度聚合转化和收入指标；年级从 `rule_name` 派生 | `period_name`, `channel_map`, `rule_name`, `lead_purchase_intention_level2_category_name`, `depart_1`, `dept_name`, `depart` |
| final select | 补充渠道分组、破单和有效线索门槛指标 | `channel_1`, `s_lead`, `podan` |

## 5. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| first_call_task (首 call) | employee_map (员工维表) | `account_id` | left join | 桥接首 call 账号到员工姓名 |
| data (主数据) | f_call0 (首 call 标记) | `f.assign_employee_email_name = d.employee_email_name` + `f.user_id = d.user_id` | left join | 将首 call 完成标记关联到主线索；未匹配时 `is_f_call = 0` |
| zhuanhua | temp_table.shenbaoxin_channel_group | `channel_grp.channel = zz.channel_map` | left join | 补充渠道分组 `channel_1` |

## 6. where 条件

主表分区条件（dt/hour 一致，均为 now-3h）：

```sql
dt = format_datetime(now() - interval '3' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '3' hour, 'HH')
```

首 call 任务表分区条件：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
and start_time > '2026-01-01'
and is_del = 0
```

员工维表分区 + 范围：

```sql
dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
and first_level_department_name = 'H业务线'
and second_level_department_name in ('市场部','精品班学部','青橙项目部','菁英班学部')
```

主表范围限定（**比市场顾问转化看板宽**）：

```sql
section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name in ('市场部','精品班学部','青橙项目部','菁英班学部')
and virtual_third_department_name in ('学习顾问部','市场顾问部','中价产品项目部')
and (period_mapping_first_level_department_name = 'H业务线' or period_mapping_first_level_department_name is null)
```

最终结果过滤：

```sql
zz.period_name > '20260417期'
```

## 7. group by 维度

- `period_name`
- `channel_map`
- `rule_name`
- `lead_purchase_intention_level2_category_name`（由 `rule_name` + 原始字段派生）
- `depart_1`（虚拟三级部门）
- `dept_name`（截面分配二级部门）
- `depart`（虚拟四级部门）

**注意**：无 `employee_email_name` / `jingli` / `zhuguan`，与市场顾问转化看板不同。

## 8. 聚合指标

| 指标名 | SQL 表达式 | 口径说明 | 状态 |
|---|---|---|---|
| lead_count | `sum(lead_count)` | 线索数 | 来自 SQL |
| can_renew_ds_count_a | `sum(valid_lead_count)` | 有效线索数 | 来自 SQL |
| first_call_in_24h | `sum(first_call_in_24h)` | 24 小时内首呼线索数 | 来自 SQL |
| valid_lead_count | `sum(valid_lead_count)` | 有效线索数（与 can_renew_ds_count_a 同口径） | 来自 SQL，命名待确认 |
| is_f_call | `sum(is_f_call)` | 已完成首 call 任务的有效线索数，使用 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` + `finance_dw.dim_finance_employee_df` 桥接 | 来自 SQL，2026-05-22 强制口径 |
| is_friend_lead | `sum(is_friend_lead)` | 有效线索中已加微数 | 来自 SQL |
| pay_users | `sum(conversion_lead_count)` | 转化人数 | 来自 SQL |
| pay_users_on_period | `sum(same_lead_period_conversion_lead_count)` | 当期线索当期转化人数 | 来自 SQL |
| pay_users_not_on_period | `sum(conversion_lead_count - same_lead_period_conversion_lead_count)` | 跨期转化人数 | 来自 SQL |
| pay_user_subs | `sum(subject_count)` | 转化科目人次 | 来自 SQL |
| pay_user_subs_on_period | `sum(same_lead_period_subject_count)` | 当期转化科目人次 | 来自 SQL |
| pay_user_subs_not_on_period | `sum(subject_count - same_lead_period_subject_count)` | 跨期转化科目人次 | 来自 SQL |
| pay_user_subs_joint | `sum(lb_subject_count)` | 联报人次 | 来自 SQL |
| pay_user_subs_joint_onp | `sum(same_lead_period_lb_subject_count)` | 当期联报人次 | 来自 SQL |
| pay_user_subs_joint_nonp | `sum(lb_subject_count - same_lead_period_lb_subject_count)` | 跨期联报人次 | 来自 SQL |
| trade_income | `sum(income_amount / 100)` | 收款金额，分转元 | 来自 SQL |
| trade_refund | `sum(in_pay_period_refund_amount / 100 + non_pay_period_refund_amount / 100)` | 退款金额，分转元 | 来自 SQL |
| trade_profit | `sum(income_amount / 100 - in_pay_period_refund_amount / 100 - non_pay_period_refund_amount / 100)` | 净营收，分转元 | 来自 SQL |
| xb_trade_income | `sum(same_lead_period_income_amount / 100)` | 当期线索当期收款，分转元 | 来自 SQL |
| xb_trade_profit | `sum(same_lead_period_income_amount / 100 - same_lead_period_refund_amount / 100)` | 当期线索当期净营收，分转元 | 来自 SQL |
| kk_trade_income | `sum(income_amount / 100 - same_lead_period_income_amount / 100)` | 跨期收款，分转元 | 来自 SQL |
| pre_refund | `sum(non_pay_period_refund_amount / 100)` | 往期支付当期退款，分转元 | 来自 SQL |
| channel_1 | `channel_grp.channel_group` | 渠道分组，来自 `temp_table.shenbaoxin_channel_group` | 待确认字段存在性和唯一性 |
| s_lead | `case when can_renew_ds_count_a >= 5 then can_renew_ds_count_a else 0 end` | 有效线索数达到 5 才计入 | 阈值待业务确认 |
| podan | `case when can_renew_ds_count_a >= 5 and trade_profit > 0 then 1 else 0 end` | 有效线索达 5 且净营收为正则破单 | 阈值待业务确认 |

## 9. 可复用 SQL 模式

- `data_base` → `data` 两层 CTE：先在全链路表计算 `calc_period_name`，再在第二层做渠道 CASE、指标空值处理和派生字段；两层的 `select distinct` 确保了去重。
- 首 call 桥接：`first_call_task` + `employee_map` + `f_call0` 三 CTE 的标准首 call 标记模式，详见 `knowledge/tables/gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf.md`。
- 渠道 CASE 使用 `resources/raw_sql/market_channel_case_when_0524.sql`（0524 版本），仅将输出别名从 `qudao` 改为 `channel_map`。
- 年级在 `zhuanhua` CTE 中派生，相比在 `data` CTE 中派生可避免同层别名引用问题。
- `nvl` 函数用于空值处理（Hive 兼容），Presto 标准写法应使用 `coalesce`。

## 10. 待确认事项

- `data_base` CTE 使用 `select t1.*`，违反知识库"大宽表禁止 select *"规则；已知为原始 SQL 写法，复用时建议改为显式列名。
- `data_base` 和 `data` 双层 `select distinct` 可能带来不必要的 shuffle；需确认是否有意为之。
- `valid_lead_count` 和 `can_renew_ds_count_a` 在 `zhuanhua` 中为同一聚合 `sum(valid_lead_count)`，输出两个同名指标；需确认前端是否需要两个字段。
- `lead_purchase_intention_level2_category_name` 既用作年级维度又保留了原始字段名；如年级是从 `rule_name` 提取的，应考虑更换字段别名。
- 首 call 任务表分区使用 `now - 2h` 而主表使用 `now - 3h`，存在 1 小时偏移不一致；需确认是否为平台产出延迟口径。
- 员工维表按 `account_id` 去重时 `order by employee_email_name`，多姓名时取字典序第一个；如一个 account_id 对应多员工（多部门兼职），需确认该逻辑是否正确。
- 首 call 任务表未限定 `task_generate_rule_type = 2`（顾问首 call），只用了 `is_del = 0` 和 `start_time > '2026-01-01'`；需确认是否需要补充 `task_generate_rule_type = 2`。
- `temp_table.shenbaoxin_channel_group` 的 `channel_group` 字段是否真实存在需通过 `desc` 确认；当前 SQL 未实际输出该字段的旧版中已存在此风险。
- `period_mapping_first_level_department_name is null` 的放宽条件可能导致非目标部门数据混入，需确认业务合理性。
- 渠道 CASE 中引用 `period_name`（派生别名），需确认 Presto 环境是否允许同层 select 引用别名。
- 所有指标口径来自 SQL 推断，尚未经过业务口径文档确认。
