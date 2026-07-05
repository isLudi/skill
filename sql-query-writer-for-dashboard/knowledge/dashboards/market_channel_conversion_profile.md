# 市场渠道用户画像分析

## 1. 来源

原始 SQL：

- `resources/raw_sql/market_channel_conversion_profile_call_duration_dataset.sql`
- `resources/raw_sql/market_channel_conversion_profile_learn_duration_dataset.sql`
- `resources/raw_sql/market_channel_conversion_profile_deep_stage_dataset.sql`
- `resources/raw_sql/market_channel_conversion_profile_overall_dataset_fixed.sql`
- `resources/raw_sql/refund_rate_multidim.sql`
- `resources/raw_sql/data_center_market_2349_refund_amount_share_fixed_20260704.sql`

入库时间：2026-06-06

最近更新：2026-06-07

## 2. 查询目标

按期次、渠道、渠道组、年级和过程分桶展示市场渠道用户成单过程画像。当前过程画像拆为三个分桶数据集，并另有一个整体画像数据集：

- 成单用户首 call 通时占比：按总通时分桶。
- 成单用户上课时长占比：按总出勤时长分桶。
- 深沟成单用户占比：按私海销售阶段/好友关系分桶。
- 成单用户画像整体数据：不按过程分桶，按期次、渠道、年级和经理展示整体线索、有效线索、成交用户、科目数、订单数、收入和科目档位。
- 多维退费率数据：不按过程分桶，按期次、渠道、年级、经理、主管、顾问输出 GMV 退费率、人头退费率和单科/多科退费分子分母字段；看板数据透视表自行计算比率。
- 退费金额结构占比数据：按期次、渠道、年级、经理、主管输出科目、产品、年级维度的退款金额占当期筛选范围总退款金额比例。

三个数据集的总计口径应一致：相同期次、渠道、年级筛选下，`bucket_user_cnt`、`conversion_user_cnt`、`order_cnt`、`section_profit_amt` 的总计应一致；差异只应体现在 `bucket_name` 分桶分布上。

## 3. 使用表

| 表名 | 别名/CTE | 用途 | 状态 |
|---|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `lead_raw`, `lead_base` | 三个数据集共同主表，提供线索、有效线索、转化人头、订单数、收入退款、渠道、年级和部门字段 | 历史 SQL 口径；字段业务口径待人工确认 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `call_duration_raw` | 仅在首 call 通时数据集中按 `period_name + lead_id + user_id` 取 `max(section_assign_all_call_duration)`，用于分桶 | 通时字段含义和是否取 max 代表最终总通时待人工确认；当前为排重防放大方案 |
| `service_dw.dws_service_user_learn_detail_hf` | `learn_duration` | 仅在上课时长数据集中按 `period_name + user_id` 汇总 `live_learn_duration`，用于出勤时长分桶 | 行课口径待人工确认 |
| `service_dw.dwd_crm_assign_private_detail_hf` | `private_stage` | 仅在深沟阶段数据集中按 `user_number + lead_id` 取最新 `sale_flow_stage_sequence`，用于深沟/双沟分桶 | 私海阶段口径待人工确认 |
| `temp_table.shenbaoxin_channel_group` | `channel_group` | 按 `channel = channel_map` 补充渠道组 | 字段结构、唯一性和维护来源待人工确认 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `refund_rate_multidim` 的 `lead_raw`, `lead_base`, `agg` | 多维退费率数据集唯一物理表，提供线索、有效线索、成交科目数、当期/截面收入和退款金额、经理/主管/顾问字段 | 退费率分子分母口径来自用户提供 SQL；金额单位、科目数和人头口径待人工确认 |
| `finance_dw.app_finance_performance_extend_details_hf` | 2349 `dd`, `gmv_z`, `gmv_t`, `refund_base` | 退费金额结构占比财务业绩明细来源，按 `trade_time` 推导 `qici`，按 `real_price_0/name_total_price` 识别退款金额 | 当前用于科目/产品/年级退款金额占比；不再使用旧负数 `refund_total` 作为前端指标 |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | 2349 `n_uid` | 通过 `original_order_user_number + performance_employee_email_name` 补充 `lead_id` | 使用多业务线/二级部门长白名单 |
| `service_dw.dim_crm_assign_rule_lead_detail_hf` | 2349 `rule` | 通过 `lead_id + account_domain` 补充分配规则并派生 `channel_1` | 渠道 CASE 来自历史退费 SQL |
| `temp_table.dingxi01_jiagou_zx` | 2349 `base` | 通过 `employee_email_name = name` 补充 `jingli`, `xiaozu` | 当前架构表，不含期次 |

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

### 5.5 多维退费率数据集

来源：`resources/raw_sql/refund_rate_multidim.sql`

该数据集属于市场渠道用户画像分析看板的退费模块，替代原独立退费看板入口中的多科用户退费占比、退费科目产品和退费原因分析的拆散调用。当前 SQL 只使用全链路主表，不再 join 财务业绩明细、退款原因表或架构临时表。

| CTE | 用途 | 关键字段 |
|---|---|---|
| `lead_raw` | 从全链路表抽取市场顾问部主表字段、业务指标和退款金额字段 | `period_name`, `lead_id`, `user_id`, `valid_lead_count`, `subject_count`, `income_amount`, `in_pay_period_refund_amount`, `non_pay_period_refund_amount`, `same_lead_period_income_amount`, `same_lead_period_refund_amount` |
| `lead_base` | 生成 `channel_map`、`grade_name`，透传经理、主管、顾问和退款指标 | `channel_map`, `grade_name`, `jingli`, `zhuguan`, `employee_email_name` |
| `user_base` | 按 `period_name + channel_map + grade_name + jingli + zhuguan + employee_email_name + user_id` 聚合用户层正价课与退费信息 | `regular_course_user_count`, `pay_subject_person_count`, `refund_section_amount` |
| `user_agg` | 按展示粒度输出正价课人头、正价课退费人头和正价课退费人次 | `pay_user_head_count`, `refund_headcount_section`, `refund_subject_person_count_section`, `refund_*_subject_headcount` |
| `agg` | 按 `period_name + channel_map + grade_name + jingli + zhuguan + employee_email_name` 汇总金额类分子/分母 | `refund_current_gmv`, `net_income_current_gmv`, `refund_section_gmv`, `net_income_section_gmv`, `total_headcount` |

输出为分子/分母字段，不直接输出退费率。看板数据透视表必须用 `sum(分子) / sum(分母)` 自行计算，避免行级比率在多维汇总时失真。

### 5.6 退费科目/产品/年级金额占比数据集

来源：`resources/raw_sql/data_center_market_2349_refund_amount_share_fixed_20260704.sql`

该数据集对应数据中心模型 `2349` / `退费_科目_产品`，用于看板中的“不同科目退费占比”“不同产品退费占比”“不同年级退费占比”。当前口径已废弃旧 `refund_total` 负数输出，统一输出退款金额、总退款金额和金额占比。

| CTE | 用途 | 关键字段 |
|---|---|---|
| `dd` / `gmv_z` / `gmv_t` / `rd` | 处理财务业绩明细、正常订单和调课调班订单 | `qici`, `real_price_0`, `name_total_price`, `grade_list`, `subject`, `course_second_level_department_name` |
| `n_uid` / `lead_gmv` / `rule` | 补充 `lead_id` 和渠道规则 | `lead_id`, `rule_name`, `channel_1` |
| `base` | 补充经理、主管并生成周差字段 | `jingli`, `xiaozu`, `week_diff` |
| `refund_base` | 只保留退款流水，生成标准科目、产品和退款金额 | `subject`, `course_name`, `refund_amount` |
| `filter_group_with_grade` | 科目/产品图表筛选范围总退款金额 | `qici`, `channel_1`, `jingli`, `xiaozu`, `grade_list`, `total_refund_amount` |
| `filter_group_without_grade` | 年级图表筛选范围总退款金额 | `qici`, `channel_1`, `jingli`, `xiaozu`, `total_refund_amount` |

最终输出为长表：

```text
qici + channel_1 + jingli + xiaozu + grade_list + analysis_type + dim_value
```

其中 `analysis_type` 取值：

- `subject`：科目退款金额占比。
- `product`：产品退款金额占比。
- `grade`：年级退款金额占比。

核心指标：

- `refund_amount`：当前维度退款金额，正数。
- `total_refund_amount`：当前筛选范围总退款金额。
- `refund_amount_ratio`：`refund_amount / total_refund_amount`。

## 6. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| `lead_base b` | `call_duration_raw cd` | `period_name + lead_id + user_id` | left join | 首 call 通时只用于分桶，不参与业务指标去重 |
| `lead_base b` | `learn_duration ld` | `period_name + user_id` | left join | 上课时长按用户期次汇总后分桶；同一用户多线索是否共享时长待人工确认 |
| `lead_base b` | `private_stage ps` | `user_id = user_number` + `lead_id` | left join | 深沟阶段按用户线索最新私海阶段分桶 |
| `profile_agg a` | `temp_table.shenbaoxin_channel_group cg` | `cg.channel = a.channel_map` | left join | 补充渠道组 |
| `profile_agg a` | `dim_totals dt` | `period_name + channel_map + grade_name` | left join | 补充分桶前总线索和总有效线索 |
| 整体画像数据集 | 无外部 join | 无 | 无 | `market_channel_conversion_profile_overall_dataset_fixed.sql` 仅使用全链路主表；如后续补渠道组或架构表，需另行确认 join key 和唯一性 |
| 多维退费率数据集 | 无外部 join | 无 | 无 | `refund_rate_multidim.sql` 仅使用全链路主表；经理/主管/顾问均来自主表虚拟架构字段，字段最终展示口径待人工确认 |
| 退费金额结构占比数据集 | `n_uid` / `rr` / `zx` | `user_id1 + name`、`lead_id + account_domain`、`employee_email_name = name` | left join 后部分 CTE 用 `where n_uid.rn = 1` 收窄 | 用于 2349 科目/产品/年级金额占比；历史架构和渠道规则仍沿用退费财务流水链路 |

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

多维退费率数据集最终输出粒度：

```text
period_name + channel_map + grade_name + jingli + zhuguan + employee_email_name
```

多维退费率数据集不输出 `analysis_type`、`bucket_name`、`bucket_sort`、`channel_group`。科目/产品/年级退款金额占比使用 2349 fixed SQL；退费原因仍需另行确认是否改造成同样的金额占比长表口径。

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

## 9. 透视表推荐公式

在自助 BI 数据透视表中，比例和单效必须用可加和字段重算，不能使用 SQL 已输出的行级比率字段。

| 展示指标 | 推荐公式 |
|---|---|
| 对应区间人数 | `sum(${bucket_user_cnt})` |
| 转化人头数 | `sum(${conversion_user_cnt})` |
| 人头转化率 | `ifnull(sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}), 0)` |
| 订单转化率 | `ifnull(sum(${order_cnt}) / sum(${bucket_user_cnt}), 0)` |
| 单效（截面） | `ifnull(sum(${section_profit_amt}) / sum(${bucket_user_cnt}), 0)` |
| 当前桶占比 | 优先使用 `sum(${bucket_user_cnt}) / sum(${total_lead_cnt})` 或看板“占总计”能力；总计行展示方式待人工确认 |

### 9.1 多维退费率透视表公式

适用 SQL：`resources/raw_sql/refund_rate_multidim.sql`

| 展示指标 | 推荐公式 |
|---|---|
| 当期 GMV 退费率 | `ifnull(sum(${refund_current_gmv}) / sum(${net_income_current_gmv}), 0)` |
| 截面 GMV 退费率 | `ifnull(sum(${refund_section_gmv}) / sum(${net_income_section_gmv}), 0)` |
| 截面人头退费率 | `ifnull(sum(${refund_headcount_section}) / sum(${pay_user_head_count}), 0)` |
| 1科 GMV 退费率 | `ifnull(sum(${refund_1_subject_gmv}) / sum(${net_income_1_subject_gmv}), 0)` |
| 1科人头退费率 | `ifnull(sum(${refund_1_subject_headcount}) / sum(${pay_user_head_count}), 0)`；1科分母是否应使用 1科用户数待人工确认 |
| 2-3科 GMV 退费率 | `ifnull(sum(${refund_2_3_subject_gmv}) / sum(${net_income_2_3_subject_gmv}), 0)` |
| 2-3科人头退费率 | `ifnull(sum(${refund_2_3_subject_headcount}) / sum(${pay_user_head_count}), 0)`；2-3科分母是否应使用 2-3科用户数待人工确认 |
| 3科以上 GMV 退费率 | `ifnull(sum(${refund_3plus_subject_gmv}) / sum(${net_income_3plus_subject_gmv}), 0)` |
| 3科以上人头退费率 | `ifnull(sum(${refund_3plus_subject_headcount}) / sum(${pay_user_head_count}), 0)`；3科以上分母是否应使用 3科以上用户数待人工确认 |

注意：该 SQL 输出的 `net_income_*` 字段是用户提供 SQL 中的分母字段名称，真实业务含义是否应称为“净营收”或“GMV分母”待人工确认。

### 9.2 退费整体数据指标卡公式

适用 SQL：`resources/raw_sql/data_center_market_2886_20260624.sql`

| 展示指标 | 推荐公式 |
|---|---|
| 退费人头 | `sum(${退费人头})` |
| 退费人次 | `sum(${退费人次})` |
| GMV退费率 | `ifnull(sum(${GMV退费}) / sum(${收款}), 0)` |
| 人头退费率 | `ifnull(sum(${退费人头}) / sum(${正价课人头}), 0)` |

注意：`退费人头` 是正价课出单用户中的退费去重人数；`退费人次` 是这些退费用户对应的正价课科目人次。当前 2886 源表没有实际退款科目数字段，因此 `退费人次` 不能解释为精确退款科目数。`正价课人头` 对齐 2809 成单用户画像整体数据。

### 9.3 退费金额结构占比图表公式

适用 SQL：`resources/raw_sql/data_center_market_2349_refund_amount_share_fixed_20260704.sql`

| 图表 | 数据筛选 | 维度 | 指标 |
|---|---|---|---|
| 不同科目退费占比 | `analysis_type = 'subject'` | `dim_value` 或 `subject` | 优先使用 `refund_amount_ratio`；跨行聚合时用 `sum(refund_amount) / sum(total_refund_amount)` |
| 不同产品退费占比 | `analysis_type = 'product'` | `dim_value` 或 `course_name` | 优先使用 `refund_amount_ratio`；跨行聚合时用 `sum(refund_amount) / sum(total_refund_amount)` |
| 不同年级退费占比 | `analysis_type = 'grade'` | `dim_value` 或 `grade_list` | 优先使用 `refund_amount_ratio`；跨行聚合时用 `sum(refund_amount) / sum(total_refund_amount)` |

注意：旧 `refund_total` 负数口径已废弃，不再作为上述三个图的分子。

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
- 多维退费率数据集中 `subject_count` 直接来自全链路主表，是否能代表用户最终购买科目数分层待人工确认。
- 多维退费率数据集的人头退费率推荐分母已改为 `pay_user_head_count`；`total_headcount = count(distinct valid_lead_count > 0 的 user_id)` 仅保留为历史有效线索用户字段。单科/多科人头退费率是否应改用对应科目分层正价课用户数做分母待人工确认。
- 金额字段统一 `/100`，推断原始单位为分，需人工确认。
- `temp_table.shenbaoxin_channel_group` 的字段结构、唯一性和维护来源待人工确认。
