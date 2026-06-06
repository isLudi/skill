# 市场渠道用户画像分析

## 1. 来源

原始 SQL：

- `resources/raw_sql/market_channel_conversion_profile_call_duration_dataset.sql`
- `resources/raw_sql/market_channel_conversion_profile_learn_duration_dataset.sql`
- `resources/raw_sql/market_channel_conversion_profile_deep_stage_dataset.sql`
- `resources/raw_sql/market_channel_conversion_profile_overall_dataset_fixed.sql`

入库时间：2026-06-06

最近更新：2026-06-06

## 2. 查询目标

按期次、渠道、渠道组、年级和过程分桶展示市场渠道用户成单过程画像。当前过程画像拆为三个分桶数据集，并另有一个整体画像数据集：

- 成单用户首 call 通时占比：按总通时分桶。
- 成单用户上课时长占比：按总出勤时长分桶。
- 深沟成单用户占比：按私海销售阶段/好友关系分桶。
- 成单用户画像整体数据：不按过程分桶，按期次、渠道、年级和经理展示整体线索、有效线索、成交用户、科目数、订单数、收入和科目档位。

三个数据集的总计口径应一致：相同期次、渠道、年级筛选下，`bucket_user_cnt`、`conversion_user_cnt`、`order_cnt`、`section_profit_amt` 的总计应一致；差异只应体现在 `bucket_name` 分桶分布上。

## 3. 使用表

| 表名 | 别名/CTE | 用途 | 状态 |
|---|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `lead_raw`, `lead_base` | 三个数据集共同主表，提供线索、有效线索、转化人头、订单数、收入退款、渠道、年级和部门字段 | 历史 SQL 口径；字段业务口径待人工确认 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `call_duration_raw` | 仅在首 call 通时数据集中按 `period_name + lead_id + user_id` 取 `max(section_assign_all_call_duration)`，用于分桶 | 通时字段含义和是否取 max 代表最终总通时待人工确认；当前为排重防放大方案 |
| `service_dw.dws_service_user_learn_detail_hf` | `learn_duration` | 仅在上课时长数据集中按 `period_name + user_id` 汇总 `live_learn_duration`，用于出勤时长分桶 | 行课口径待人工确认 |
| `service_dw.dwd_crm_assign_private_detail_hf` | `private_stage` | 仅在深沟阶段数据集中按 `user_number + lead_id` 取最新 `sale_flow_stage_sequence`，用于深沟/双沟分桶 | 私海阶段口径待人工确认 |
| `temp_table.shenbaoxin_channel_group` | `channel_group` | 按 `channel = channel_map` 补充渠道组 | 字段结构、唯一性和维护来源待人工确认 |

## 4. 范围限定

三份 SQL 的主全链路表共同范围：

```sql
t1.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and t1.hour = format_datetime(now() - interval '3' hour, 'HH')
and t1.section_assign_employee_first_level_department_name = 'H业务线'
and t1.section_assign_employee_second_level_department_name = '市场部'
and t1.section_assign_employee_third_level_department_name = '市场顾问部'
and t1.virtual_third_department_name = '市场顾问部'
and (t1.period_mapping_first_level_department_name = 'H业务线' or t1.period_mapping_first_level_department_name is null)
and (
      t1.period_mapping_second_level_department_name in ('市场部', '精品班学部')
   or t1.period_mapping_second_level_department_name is null
)
```

最终过滤：

```sql
where a.period_name > '20260417期'
```

待人工确认：

- `dt = now - 2h` 与 `hour = now - 3h` 的偏移是否为稳定产出延迟口径。
- `period_mapping_second_level_department_name is null` 放宽条件是否符合当前业务范围。
- `精品班学部` 是否只作为市场顾问相关期次映射保留，不能扩展为青橙、菁英班或中价。

## 5. CTE 结构

### 5.1 首 call 通时数据集

| CTE | 用途 | 关键字段 |
|---|---|---|
| `lead_raw` | 从全链路表抽取共同业务指标，不携带 `section_assign_all_call_duration`，避免通时快照参与 `distinct` 导致指标放大 | `period_name`, `lead_id`, `user_id`, `lead_count`, `valid_lead_count`, `conversion_lead_count`, `order_count`, `income_amount` |
| `call_duration_raw` | 从同一主表单独抽取通时，按 `period_name + lead_id + user_id` 取最大通时 | `section_assign_all_call_duration` |
| `lead_base` | 生成 `channel_map`、`grade_name` 和基础指标 | `channel_map`, `grade_name` |
| `profile_base` | 将通时回连到业务底表，仅用于分桶 | `total_call_duration_seconds` |
| `dim_totals` | 在分桶前计算渠道年级总线索/总有效线索 | `total_leads`, `total_valid_leads` |
| `profile_union` | 生成通时分桶 | `bucket_name`, `bucket_sort` |
| `profile_agg` | 按分桶聚合输出 | `bucket_user_count`, `conversion_user_count`, `positive_course_order_count`, `section_trade_profit` |

### 5.2 上课时长数据集

| CTE | 用途 | 关键字段 |
|---|---|---|
| `lead_raw` / `lead_base` | 与首 call 数据集共享主表业务指标和渠道年级派生逻辑 | `period_name`, `channel_map`, `grade_name` |
| `learn_duration` | 行课表按 `begin_time` 派生期次，按 `period_name + user_id` 汇总总出勤时长 | `total_live_learn_duration_seconds` |
| `profile_base` | 将上课时长回连到业务底表，仅用于分桶 | `total_live_learn_duration_seconds` |
| `dim_totals` / `profile_union` / `profile_agg` | 计算分母和分桶聚合 | 同首 call |

### 5.3 深沟阶段数据集

| CTE | 用途 | 关键字段 |
|---|---|---|
| `lead_raw` / `lead_base` | 与另两个数据集共享主表业务指标和渠道年级派生逻辑；保留 `friend_lead_count` 作为已建联兜底 | `friend_lead_count` |
| `private_stage` | 私海表按 `user_number + lead_id` 取最新阶段 | `sale_flow_stage_sequence` |
| `profile_base` | 按阶段生成 `deep_communication_bucket` | `bucket_name`, `bucket_sort` |
| `dim_totals` / `profile_union` / `profile_agg` | 计算分母和分桶聚合 | 同首 call |

### 5.4 整体画像数据集

来源：`resources/raw_sql/market_channel_conversion_profile_overall_dataset_fixed.sql`

| CTE | 用途 | 关键字段 |
|---|---|---|
| `src` | 从全链路表抽取整体画像基础字段和业务指标；已补充 `lead_id` 保留线索粒度，避免 `select distinct` 在用户维度折叠多线索 | `period_name`, `lead_id`, `user_id`, `lead_count`, `valid_lead_count`, `conversion_lead_count`, `subject_count`, `order_count` |
| `data` | 生成 `channel_map`、`grade_name`、`manager_name`，并透传业务指标 | `channel_map`, `grade_name`, `manager_name` |
| `user_base` | 按 `period_name + channel_map + grade_name + manager_name + user_id` 聚合用户层指标 | `lead_count`, `valid_lead_count`, `regular_course_user_count`, `regular_course_order_count`, `pay_subject_person_count` |
| `agg` | 按 `period_name + channel_map + grade_name + manager_name` 输出整体画像 | `pay_user_head_count`, `subject_*_user_count`, `subject_*_gmv`, `valid_lead_count`, `regular_course_order_count` |

重要修复口径：

- 主表范围增加 `virtual_third_department_name = '市场顾问部'`，与三个分桶数据集保持一致。
- `lead_count` 和 `valid_lead_count` 使用标准宽表字段直接汇总，不再对 `抖音私域`/`抖音私信` 切换到 `merge_assign_lead_count`/`merge_valid_lead_count`。
- `lead_id` 仅作为 `src` 阶段防折叠字段保留，最终不输出。

待人工确认：

- 整体画像 `pay_user_head_count` 当前使用 `regular_course_user_count > 0` 后按用户计 1，是否与所有看板正价课转化人头口径完全一致。
- 科目档位 `subject_1/subject_2_3/subject_3_plus/subject_0` 是否应按用户层 `sum(subject_count)` 分层；多订单、多科目退款后的档位归属需人工确认。

## 6. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| `lead_base b` | `call_duration_raw cd` | `period_name + lead_id + user_id` | left join | 首 call 通时只用于分桶，不参与业务指标去重 |
| `lead_base b` | `learn_duration ld` | `period_name + user_id` | left join | 上课时长按用户期次汇总后分桶；同一用户多线索是否共享时长待人工确认 |
| `lead_base b` | `private_stage ps` | `user_id = user_number` + `lead_id` | left join | 深沟阶段按用户线索最新私海阶段分桶 |
| `profile_agg a` | `temp_table.shenbaoxin_channel_group cg` | `cg.channel = a.channel_map` | left join | 补充渠道组 |
| `profile_agg a` | `dim_totals dt` | `period_name + channel_map + grade_name` | left join | 补充分桶前总线索和总有效线索 |
| 整体画像数据集 | 无外部 join | 无 | 无 | `market_channel_conversion_profile_overall_dataset_fixed.sql` 仅使用全链路主表；如后续补渠道组或架构表，需另行确认 join key 和唯一性 |

## 7. 输出粒度

最终输出粒度：

```text
period_name + channel_map + channel_group + grade_name + analysis_type + bucket_name + bucket_sort
```

其中 `analysis_type` 三个数据集分别固定为：

- `不同通时成单用户占比（总通时）`
- `不同上课时长成单用户占比（总出勤时长）`
- `是否深沟成单用户占比`

整体画像数据集最终输出粒度：

```text
period_name + channel_map + grade_name + manager_name
```

整体画像数据集不输出 `analysis_type`、`bucket_name`、`bucket_sort`、`channel_group`。如果看板需要渠道组，需要额外 join `temp_table.shenbaoxin_channel_group`，字段和唯一性待人工确认。

## 8. 输出字段和看板使用

| 字段 | 说明 | 是否可直接 sum | 备注 |
|---|---|---|---|
| `bucket_user_cnt` | 当前桶对应区间人数，SQL 中为 `sum(case when lead_count > 0 then lead_count else 0 end)` | 是 | 对应区间人数用 `sum(${bucket_user_cnt})` |
| `bucket_valid_lead_cnt` | 当前桶有效线索数 | 是 | 备用字段 |
| `total_lead_cnt` | 当前 `period + channel + grade` 分桶前总线索数，每个桶重复带出 | 否 | 仅用于展示或单桶占比，不要跨桶 sum |
| `total_valid_lead_cnt` | 当前 `period + channel + grade` 分桶前总有效线索数，每个桶重复带出 | 否 | 仅用于展示或单桶占比，不要跨桶 sum |
| `total_lead_cnt_once` | 在 `bucket_sort = 1` 的桶输出总线索，其余桶为 0 | 可谨慎 sum | 用于避免总线索跨桶重复；分桶缺失时需确认 |
| `total_valid_lead_cnt_once` | 在 `bucket_sort = 1` 的桶输出总有效线索，其余桶为 0 | 可谨慎 sum | 用于避免总有效线索跨桶重复；分桶缺失时需确认 |
| `conversion_user_cnt` | 当前桶正价课转化人头数 | 是 | 转化人头用 `sum(${conversion_user_cnt})` |
| `order_cnt` | 当前桶正价课订单数 | 是 | 订单数用 `sum(${order_cnt})` |
| `trade_income_amt` | 当前桶收入金额，分转元 | 是 | 金额单位待人工确认 |
| `section_profit_amt` | 当前桶截面净营收，分转元 | 是 | 单效分子 |
| `head_conversion_rate` | SQL 行级人头转化率 | 否 | 不能在透视表 sum/avg；仅作单行参考，建议隐藏 |
| `order_conversion_rate` | SQL 行级订单转化率 | 否 | 不能在透视表 sum/avg；仅作单行参考，建议隐藏 |
| `section_unit_efficiency` | SQL 行级截面单效 | 否 | 不能在透视表 sum/avg；仅作单行参考，建议隐藏 |
| `bucket_user_share` | 当前桶人数占同组分桶总人数比例 | 否 | 饼图可在单一分组下使用；跨渠道/年级汇总需重算 |

## 9. 透视表推荐公式

在自助 BI 数据透视表中，比例和单效必须用可加和字段重算，不能使用 SQL 已输出的行级比率字段。

| 展示指标 | 推荐公式 |
|---|---|
| 对应区间人数 | `sum(${bucket_user_cnt})` |
| 转化人头数 | `sum(${conversion_user_cnt})` |
| 人头转化率 | `ifnull(sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}), 0)` |
| 订单转化率 | `ifnull(sum(${order_cnt}) / sum(${bucket_user_cnt}), 0)` |
| 单效（截面） | `ifnull(sum(${section_profit_amt}) / sum(${bucket_user_cnt}), 0)` |
| 当前桶占比 | `ifnull(sum(${bucket_user_cnt}) / sum(${bucket_user_cnt}) over 当前透视分组, 0)`；具体窗口/总计写法取决于看板能力，待人工确认 |

## 10. 已验证现象

2026-06-06 通过 Web 查询验证：

- 三份正式 SQL 均可在网页端执行。
- 在相同期次总计口径下，`bucket_user_cnt`、`conversion_user_cnt`、`order_cnt`、`section_profit_amt` 三份数据集一致。
- 行级字段 `head_conversion_rate`、`order_conversion_rate`、`section_unit_efficiency` 在不同分桶数据集中直接 `sum` 或 `avg` 会得到不同结果，这是透视表二次聚合问题，不是底表总量不一致。

## 11. 待人工确认

- `section_assign_all_call_duration` 是否应取 `max` 作为最终总通时。
- 上课时长按 `period_name + user_id` 汇总后回连，若同一用户同一期有多条线索，是否应共享同一上课时长。
- 私海阶段 `sale_flow_stage_sequence = 450/470` 对应深沟/双沟的业务口径是否稳定。
- `bucket_user_cnt` 当前沿用 `lead_count > 0` 的线索量口径，并非 `count(distinct user_id)`；业务是否称为“人数”需人工确认。
- 整体画像数据集中 `pay_user_head_count`、`pay_subject_person_count`、`subject_*` 档位是否完全等同 CRM 画像口径需人工确认。
- 金额字段统一 `/100`，推断原始单位为分，需人工确认。
- `temp_table.shenbaoxin_channel_group` 的字段结构、唯一性和维护来源待人工确认。
