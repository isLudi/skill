# 青橙转化宽表-市场渠道

## 1. 来源

`resources/raw_sql/qingcheng_conversion_wide_table_market_channel_20260611.sql`

入库时间：2026-06-11

## 2. 查询目标

以青橙项目部市场渠道视角，输出期次-渠道-年级-部门维度的转化宽表。核心包括：

1. 通过 100+ 分支的 CASE WHEN 将来源流量池、投放计划、部门、SKU 等字段映射为统一的市场渠道名称（`channel_map`）。
2. 补充首次外呼标记（`is_f_call`），关联 `service_dw.app_h_crm_lead_task_process_info_detail_hf`。
3. 按 `period_name + channel_map + grade + depart_1 + dept_name + depart + rule_name` 粒度汇总线索量、有效线索、支付用户、支付科目、营收、退款、净营收等指标。
4. 通过 `temp_table.shenbaoxin_channel_group` 补充渠道大类（`channel_1`），并计算 S 级线索量（`s_lead`）和破单标记（`podan`）。

## 3. 最终输出粒度

| 维度 | 字段 |
|---|---|
| 期次 | `period_name`（calc_period_name，周对齐计算） |
| 市场渠道 | `channel_map`（CASE WHEN 映射结果） |
| 渠道大类 | `channel_1`（来自 temp_table.shenbaoxin_channel_group.channel_group） |
| 年级 | `lead_purchase_intention_level2_category_name`（优先 rule_name 匹配初二/初三/高一/高二/高三，兜底原字段） |
| 虚拟三级部门 | `depart_1` |
| 二级部门 | `dept_name` |
| 虚拟四级部门 | `depart` |
| 分配规则 | `rule_name` |

最终不是线索明细粒度，而是聚合后的期次-渠道-年级-部门粒度。

## 4. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `t1` / `data_base` | 青橙线索宽表主表，提供所有线索和转化指标原始字段 |
| `service_dw.app_h_crm_lead_task_process_info_detail_hf` | `f_call0` | 首次外呼任务处理明细，标记线索是否有 F 类外呼 |
| `temp_table.shenbaoxin_channel_group` | `channel_grp` | 渠道分组映射表，将 channel_map 归类到 channel_group |

## 5. 使用临时表

| 表名 | 用途 | 口径状态 |
|---|---|---|
| `temp_table.shenbaoxin_channel_group` | 将市场渠道名称（`channel`）映射到渠道大类（`channel_group`） | 待人工确认来源和刷新方式 |

## 6. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `data_base` | 从 bdg_ba 宽表取数，计算 `calc_period_name`（周对齐期次），限定青橙范围 | `lead_id`, `user_id`, `employee_email_name`, `group_period_year`, `group_period_term`, `calc_period_name` |
| `data` | 从 data_base 加工：100+ 分支 CASE WHEN 生成 `channel_map`，取虚拟架构字段，nvl 处理所有指标字段，计算 `first_call_in_24h` 和 `is_friend_lead` | `period_name`, `depart_1`, `dept_name`, `depart`, `jingli`, `zhuguan`, `employee_email_name`, `lead_id`, `user_id`, `channel_map`, `rule_name`, `lead_count`~`same_lead_period_refund_amount`, `first_call_in_24h`, `is_friend_lead` |
| `f_call0` | 从任务处理明细表取首次外呼数据，按 `flow_order_period_name` 计算期次名 | `period_name`, `assign_employee_email_name`, `user_id`, `lead_id`, `is_f_call` |
| `data_with_process` | data 左关联 f_call0，补充 `is_f_call` 标记 | data 全部字段 + `is_f_call` |
| `zhuanhua` | 按 7 个维度聚合所有指标，rule_name 优先提取年级 | `period_name`, `channel_map`, `lead_purchase_intention_level2_category_name`, `depart_1`, `dept_name`, `depart`, `rule_name` + 22 个聚合指标 |
| 最终 SELECT | 关联 channel_group 获取渠道大类，计算 S 级线索和破单 | `channel_1`, `s_lead`, `podan` |

## 7. 青橙范围限定

| 位置 | 范围字段 | 取值 |
|---|---|---|
| data_base | `section_assign_employee_first_level_department_name` | `'H业务线'` |
| data_base | `section_assign_employee_second_level_department_name` | `'青橙项目部'` |
| data_base | `period_mapping_first_level_department_name` | `'H业务线'` |

注意：本 SQL **未**加 `period_mapping_second_level_department_name` 过滤（与过程数据 raw 不同），是否遗漏待人工确认。

## 8. 分区和小时条件

| 表/CTE | dt 条件 | hour 条件 | 说明 |
|---|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | `format_datetime(now() - interval '2' hour, 'HH')` | 线索宽表主表 |
| `service_dw.app_h_crm_lead_task_process_info_detail_hf` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | `format_datetime(now() - interval '3' hour, 'HH')` | 任务处理明细，hour 偏移与主表不同 |
| `temp_table.shenbaoxin_channel_group` | 无 dt/hour | — | 临时表，刷新方式待确认 |

## 9. 期次计算逻辑（data_base.calc_period_name）

```sql
concat(
    cast(
        date_format(
            date_trunc('week',
                date_parse(replace(concat(t1.group_period_year, t1.group_period_term), '期', ''), '%Y%m%d')
                - interval '1' day
            ) + interval '4' day,
            '%Y%m%d'
        ) as varchar
    ),
    '期'
)
```

计算逻辑：取 `group_period_year + group_period_term` 拼接为期次日期，减 1 天后按周 trunc，再加 4 天到周四，格式化为 `YYYYMMdd期`。

**待人工确认**：此期次计算与过程数据 raw、转化 raw 中的期次计算是否一致；周四对齐的周边界定义是否符合青橙业务口径。

## 10. 市场渠道映射（channel_map CASE WHEN）

`channel_map` 通过 100+ 分支的 CASE WHEN 生成，涉及字段包括：
`flow_pool_name`, `rule_name`, `third_department_name`, `sku_id_name`, `ad_account_name`, `source_manager_name`, `channel_name_1`, `channel_name_2`, `channel_name_3`, `put_plan_name`, `virtual_fourth_department_name`, `virtual_fifth_department_name`, `channel_provider_name`, `first_department_name`, `second_department_name`, `page_id_name`, `source_put_plan_name`, `channel_second_provider_name`, `lead_purchase_intention_level1_category_name`, `lead_purchase_intention_name`, `flow_original_order_activity_price`, `flow_order_price`, `flow_orders_income_amount`, `get_customer_way_name`, `virtual_second_department_name`, `lead_create_time`, `period_name`。

CASE WHEN 优先级至关重要：前面的分支会吞掉后面可能命中的记录。详细映射规则已追加到 `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md` 第 9 节。

未命中任何分支时输出 `'其他未知流量'`。

## 11. 渠道大类映射（channel_1）

`channel_1` 不通过 CASE WHEN 生成，而是通过 `temp_table.shenbaoxin_channel_group` 的 `channel_group` 字段获取：
```sql
left join temp_table.shenbaoxin_channel_group channel_grp
  on channel_grp.channel = zz.channel_map
```

**待人工确认**：`shenbaoxin_channel_group` 的完整映射关系、覆盖范围和刷新频率。

## 12. where 条件

| 位置 | 条件 | 说明 |
|---|---|---|
| data_base | `dt = now()-2h`, `hour = now()-2h` | 最新快照 |
| data_base | 青橙范围三段过滤 | 见第 7 节 |
| f_call0 | `dt = now()-2h`, `hour = now()-3h` | 任务处理明细，hour 偏移不同 |
| f_call0 | `period_create_time > '2026-01-01'` | 限制期次创建时间 |
| f_call0 | `is_refund_before_clazz_begin = 0` | 排除课前退款 |
| f_call0 | `call_answer_lead_count is not null` | 有外呼接通的线索 |
| 最终 | `zz.period_name > '20260424期'` | 期次过滤，起始期次硬编码 |

## 13. group by 维度

- `period_name`
- `channel_map`
- `lead_purchase_intention_level2_category_name`（CASE WHEN 年级映射）
- `depart_1`（virtual_third_department_name）
- `dept_name`（section_assign_employee_second_level_department_name）
- `depart`（virtual_fourth_department_name）
- `rule_name`

## 14. join 关系

| 左侧 | 右侧 | join key | join 类型 | 用途 |
|---|---|---|---|---|
| `data` (d) | `f_call0` (f) | `f.period_name = d.period_name and f.assign_employee_email_name = d.employee_email_name and f.user_id = d.user_id and f.lead_id = d.lead_id` | left join | 补充线索是否有 F 类首次外呼 |
| `zhuanhua` (zz) | `temp_table.shenbaoxin_channel_group` (channel_grp) | `channel_grp.channel = zz.channel_map` | left join | 补充渠道大类 |

## 15. 聚合指标

指标集合沉淀到 `knowledge/metrics/qingcheng_conversion_wide_table_market_channel_metrics.md`。

| 指标 | 口径简述 |
|---|---|
| `lead_count` | 线索总量 |
| `can_renew_ds_count_a` | 可续报 DS 数（= `valid_lead_count`） |
| `first_call_in_24h` | 24 小时内首次外呼线索数 |
| `valid_lead_count` | 有效线索量 |
| `is_f_call` | F 类外呼线索数（来自任务处理表） |
| `is_friend_lead` | 加微线索数（valid_lead_count=1 时取 friend_lead_count） |
| `pay_users` | 支付用户数（conversion_lead_count） |
| `pay_users_on_period` | 当期支付用户数（same_lead_period_conversion_lead_count） |
| `pay_users_not_on_period` | 非当期支付用户数 |
| `pay_user_subs` | 支付科目数（subject_count） |
| `pay_user_subs_on_period` | 当期支付科目数 |
| `pay_user_subs_not_on_period` | 非当期支付科目数 |
| `pay_user_subs_joint` | 联报科目数（lb_subject_count） |
| `pay_user_subs_joint_onp` | 当期联报科目数 |
| `pay_user_subs_joint_nonp` | 非当期联报科目数 |
| `trade_income` | 交易收入（income_amount / 100，单位元） |
| `trade_refund` | 交易退款（(in_pay_period_refund + non_pay_period_refund) / 100，单位元） |
| `trade_profit` | 交易净营收（trade_income - trade_refund，单位元） |
| `xb_trade_income` | 当期收入（same_lead_period_income_amount / 100） |
| `xb_trade_profit` | 当期净营收（xb_trade_income - same_lead_period_refund_amount / 100） |
| `kk_trade_income` | 跨期收入（income_amount / 100 - same_lead_period_income_amount / 100） |
| `pre_refund` | 课前退款（non_pay_period_refund_amount / 100） |
| `s_lead` | S 级线索（can_renew_ds_count_a >= 5 时取值，否则 0） |
| `podan` | 破单标记（can_renew_ds_count_a >= 5 且 trade_profit > 0 时为 1，否则 0） |

## 16. 已知风险和待确认事项

- **channel_map CASE WHEN 优先级**：100+ 分支的 CASE WHEN 顺序至关重要，部分分支存在重叠条件（例如多个 `third_department_name='直播部'` 分支位于不同位置），需确认当前顺序是否符合业务预期。
- **AND/OR 优先级问题**：原始 SQL 中存在 `when A or B and C then ...` 写法（如 `put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部'`），SQL 中 AND 优先级高于 OR，可能导致条件组合与预期不符。需人工确认此处是否应加括号。
- **AND 优先级歧义**：`曹忆` 分支存在 `flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统'` 与其他 `flow_pool_name like '%xxx%'` 处于同一 OR 链中，可能因 AND 优先级导致 `库洛米` 分支匹配范围异常。
- **period_mapping_second_level_department_name 缺失**：与过程数据 raw 不同，本 SQL 未限定 `period_mapping_second_level_department_name in ('精品班学部','青橙项目部')`，是否会引入非青橙期次数据待确认。
- **期次计算**：`calc_period_name` 的周对齐逻辑（周四为界）与青橙其他看板的期次口径是否一致待确认。
- **f_call0 的 hour 偏移**：主表 hour 取 `now()-2h`，f_call0 hour 取 `now()-3h`，偏移不一致的原因待确认。
- **shenbaoxin_channel_group 临时表**：来源、刷新频率、字段完整映射关系均待人工确认。
- **s_lead 阈值**：S 级线索阈值为 `can_renew_ds_count_a >= 5`，此阈值是否适用所有期次待确认。
- **jp_cross_department_refund_amount**：跨部门退款字段在 data CTE 中有 nvl 处理但未在 zhuanhua 聚合中使用，是否为遗漏待确认。
- **金额单位**：所有收入/退款指标在聚合时除以 100（分转元），原始字段单位为分。
- **rule_name 年级映射**：`zhuanhua` 中重新对 `rule_name` 做年级映射后输出 `lead_purchase_intention_level2_category_name`，data 层也有 `lead_purchase_intention_level2_category_name` 原值；注意 group by 使用的是 CASE WHEN 映射后的值。
- **distinct 使用**：`data_base` 和 `data` 均使用了 `select distinct`，若宽表本身有重复，distinct 会去重；去重粒度是否合适待确认。
- 本 SQL 渠道映射逻辑为中台/市场渠道口径，**不是**青橙过程数据 raw 或青橙转化 raw 中的 `rule_name` 简单映射。两者渠道体系完全不同，不得混用。
