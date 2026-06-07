# 市场渠道用户画像分析指标

## 1. 中文名称

市场渠道用户画像分析指标集合

## 2. 适用 SQL

- `resources/raw_sql/market_channel_conversion_profile_call_duration_dataset.sql`
- `resources/raw_sql/market_channel_conversion_profile_learn_duration_dataset.sql`
- `resources/raw_sql/market_channel_conversion_profile_deep_stage_dataset.sql`
- `resources/raw_sql/market_channel_conversion_profile_overall_dataset_fixed.sql`
- `resources/raw_sql/refund_rate_multidim.sql`

## 3. 指标粒度

SQL 输出粒度：

```text
period_name + channel_map + channel_group + grade_name + analysis_type + bucket_name + bucket_sort
```

三份数据集仅分桶字段不同，基础业务指标总计应保持一致。该一致性为 2026-06-06 Web 查询验证结果，后续若修改过滤条件、渠道 CASE 或 join 方式，需要重新验证。

整体画像数据集输出粒度：

```text
period_name + channel_map + grade_name + manager_name
```

整体画像数据集不按过程分桶，不输出 `bucket_*` 字段；用于展示整体有效线索、成交用户、成交科目、收入和科目档位。

多维退费率数据集输出粒度：

```text
period_name + channel_map + grade_name + jingli + zhuguan + employee_email_name
```

多维退费率数据集不按过程分桶，输出 GMV 退费率、人头退费率和单科/多科退费率所需的分子、分母字段；看板数据透视表必须自行计算比率。

## 4. SQL 输出指标

| 字段 | SQL 口径 | 说明 | 聚合规则 |
|---|---|---|---|
| `bucket_user_cnt` | `sum(case when lead_count > 0 then lead_count else 0 end)` | 当前分桶对应区间人数/线索量。字段名称叫人数，但实质沿用 `lead_count`，业务是否等同人数待人工确认。 | 可 sum |
| `bucket_valid_lead_cnt` | `sum(case when valid_lead_count > 0 then valid_lead_count else 0 end)` | 当前分桶有效线索量 | 可 sum |
| `total_lead_cnt` | 分桶前 `period_name + channel_map + grade_name` 总线索量 | 每个桶重复带出 | 不可跨桶 sum |
| `total_valid_lead_cnt` | 分桶前 `period_name + channel_map + grade_name` 总有效线索量 | 每个桶重复带出 | 不可跨桶 sum |
| `total_lead_cnt_once` | `bucket_sort = 1` 时输出 `total_lead_cnt`，其他桶为 0 | 避免跨桶重复的总线索字段 | 可谨慎 sum |
| `total_valid_lead_cnt_once` | `bucket_sort = 1` 时输出 `total_valid_lead_cnt`，其他桶为 0 | 避免跨桶重复的总有效线索字段 | 可谨慎 sum |
| `conversion_user_cnt` | `sum(case when conversion_lead_count > 0 then conversion_lead_count else 0 end)` | 当前分桶正价课转化人头 | 可 sum |
| `order_cnt` | `sum(case when lead_count > 0 then order_count else 0 end)` | 当前分桶正价课订单数 | 可 sum |
| `trade_income_amt` | `sum(case when lead_count > 0 then income_amount else 0 end) / 100` | 当前分桶收款金额，金额单位推断为分转元 | 可 sum；单位待人工确认 |
| `section_profit_amt` | `sum(case when lead_count > 0 then income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount else 0 end) / 100` | 当前分桶截面净营收 | 可 sum；单位待人工确认 |
| `head_conversion_rate` | `conversion_user_cnt / bucket_user_cnt` | SQL 行级人头转化率 | 不可 sum/avg；透视表需重算 |
| `order_conversion_rate` | `order_cnt / bucket_user_cnt` | SQL 行级订单转化率 | 不可 sum/avg；透视表需重算 |
| `section_unit_efficiency` | `section_profit_amt / bucket_user_cnt` | SQL 行级截面单效 | 不可 sum/avg；透视表需重算 |

## 5. 看板透视表公式

配置数据透视表或总计行时，必须使用以下公式：

| 展示指标 | 公式 |
|---|---|
| 对应区间人数 | `sum(${bucket_user_cnt})` |
| 转化人头数 | `sum(${conversion_user_cnt})` |
| 人头转化率 | `ifnull(sum(${conversion_user_cnt}) / sum(${bucket_user_cnt}), 0)` |
| 订单转化率 | `ifnull(sum(${order_cnt}) / sum(${bucket_user_cnt}), 0)` |
| 单效（截面） | `ifnull(sum(${section_profit_amt}) / sum(${bucket_user_cnt}), 0)` |

人数占比、退费率等占比类指标应使用分子/分母字段重算。若使用 SQL 行级比率字段，在渠道、年级、期次或顾问维度折叠时会出现二次聚合失真。

不要将以下 SQL 行级字段直接放入透视表总计指标：

- `head_conversion_rate`
- `order_conversion_rate`
- `section_unit_efficiency`

原因：三个数据集的分桶维度不同，行级比率在不同分桶下 `sum` 或 `avg` 会天然不同，无法用于跨桶总计。

## 5.1 整体画像数据集指标

适用 SQL：`resources/raw_sql/market_channel_conversion_profile_overall_dataset_fixed.sql`

| 字段 | SQL 口径 | 说明 | 聚合规则 |
|---|---|---|---|
| `lead_count` | `sum(lead_count)` | 整体线索数，使用全链路主表标准字段，不再按抖音私信切换 merge 口径 | 可 sum；是否等同“进量人数”待人工确认 |
| `valid_lead_count` | `sum(valid_lead_count)` | 整体有效线索数，已与分桶画像数据集主表范围对齐 | 可 sum |
| `pay_user_head_count` | `sum(case when regular_course_user_count > 0 then 1 else 0 end)` | 成交用户人头，先在用户层聚合后判断是否成单 | 可 sum；与 CRM 成单用户口径待人工确认 |
| `pay_subject_person_count` | `sum(pay_subject_person_count)` | 成交科次/科目人次，来自用户层 `sum(subject_count)` | 可 sum；字段中文含义待人工确认 |
| `net_income` | `sum(net_income)` | 净营收，等于收入减支付期内/非支付期退款后 `/100` | 可 sum；金额单位待人工确认 |
| `trade_income` | `sum(trade_income)` | 收款金额，`income_amount / 100` | 可 sum；金额单位待人工确认 |
| `net_trade_income` | `sum(net_income)` | 与 `net_income` 同口径重复输出 | 可 sum；是否需要同时保留待人工确认 |
| `regular_course_user_count` | `sum(conversion_lead_count)` | 正价课转化人头宽表指标汇总 | 可 sum；与 `pay_user_head_count` 的差异需人工确认 |
| `regular_course_order_count` | `sum(order_count)` | 正价课订单数 | 可 sum |
| `avg_income_per_regular_course_user` | `trade_income / regular_course_user_count` | SQL 行级客单/人均收入 | 不可直接 sum/avg；透视表需用 `sum(trade_income) / sum(regular_course_user_count)` 重算 |
| `subject_1_user_count` / `subject_2_3_user_count` / `subject_3_plus_user_count` / `subject_0_user_count` | 按用户层 `pay_subject_person_count` 分档统计成交用户 | 成交用户科目档位人数 | 可 sum；分档口径待人工确认 |
| `subject_1_gmv` / `subject_2_3_gmv` / `subject_3_plus_gmv` / `subject_0_gmv` | 对应科目档位下的 `net_income` | 科目档位净营收 | 可 sum；金额单位待人工确认 |

整体画像透视表推荐公式：

| 展示指标 | 公式 |
|---|---|
| 有效线索数 | `sum(${valid_lead_count})` |
| 成交用户数 | `sum(${pay_user_head_count})` |
| 正价课转化人头 | `sum(${regular_course_user_count})` |
| 正价课订单数 | `sum(${regular_course_order_count})` |
| 成交用户率 | `ifnull(sum(${pay_user_head_count}) / sum(${valid_lead_count}), 0)`；是否使用有效线索作分母待人工确认 |
| 正价课人头转化率 | `ifnull(sum(${regular_course_user_count}) / sum(${valid_lead_count}), 0)`；分母口径待人工确认 |
| 正价课订单转化率 | `ifnull(sum(${regular_course_order_count}) / sum(${valid_lead_count}), 0)`；分母口径待人工确认 |
| 人均收款 | `ifnull(sum(${trade_income}) / sum(${regular_course_user_count}), 0)` |

## 5.2 多维退费率数据集指标

适用 SQL：`resources/raw_sql/refund_rate_multidim.sql`

| 字段 | SQL 口径 | 说明 | 聚合规则 |
|---|---|---|---|
| `valid_lead_cnt` | `count(distinct case when valid_lead_count > 0 then lead_id end)` | 有效线索数 | 可 sum；跨维度重复用户/线索风险待人工确认 |
| `total_headcount` | `count(distinct case when valid_lead_count > 0 then user_id end)` | 有效线索对应用户数/人头退费率分母 | 可 sum；字段是否应称为人数待人工确认 |
| `refund_current_gmv` | `sum(same_lead_period_refund_amount) / 100` | 当期 GMV 退费率分子 | 可 sum；金额单位待人工确认 |
| `net_income_current_gmv` | `sum(same_lead_period_income_amount - same_lead_period_refund_amount) / 100` | 当期 GMV 退费率分母 | 可 sum；字段名称和业务含义待人工确认 |
| `refund_section_gmv` | `sum(in_pay_period_refund_amount + non_pay_period_refund_amount) / 100` | 截面 GMV 退费率分子 | 可 sum；金额单位待人工确认 |
| `net_income_section_gmv` | `sum(income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount) / 100` | 截面 GMV 退费率分母 | 可 sum；字段名称和业务含义待人工确认 |
| `refund_headcount_section` | `count(distinct case when in_pay_period_refund_amount + non_pay_period_refund_amount > 0 then user_id end)` | 截面人头退费率分子 | 可 sum；跨顾问/渠道重复用户风险待人工确认 |
| `refund_1_subject_gmv` | `subject_count = 1` 时截面退款金额 `/100` | 1科 GMV 退费率分子 | 可 sum |
| `net_income_1_subject_gmv` | `subject_count = 1` 时截面净收入 `/100` | 1科 GMV 退费率分母 | 可 sum；分母含义待人工确认 |
| `refund_1_subject_headcount` | `subject_count = 1` 且截面退款金额 > 0 的去重用户数 | 1科人头退费分子 | 可 sum；分母是否应另设 1科用户数待人工确认 |
| `refund_2_3_subject_gmv` | `subject_count between 2 and 3` 时截面退款金额 `/100` | 2-3科 GMV 退费率分子 | 可 sum |
| `net_income_2_3_subject_gmv` | `subject_count between 2 and 3` 时截面净收入 `/100` | 2-3科 GMV 退费率分母 | 可 sum；分母含义待人工确认 |
| `refund_2_3_subject_headcount` | `subject_count between 2 and 3` 且截面退款金额 > 0 的去重用户数 | 2-3科人头退费分子 | 可 sum；分母是否应另设 2-3科用户数待人工确认 |
| `refund_3plus_subject_gmv` | `subject_count > 3` 时截面退款金额 `/100` | 3科以上 GMV 退费率分子；实际为 4科及以上还是 3科以上取决于 `subject_count` 口径，待人工确认 | 可 sum |
| `net_income_3plus_subject_gmv` | `subject_count > 3` 时截面净收入 `/100` | 3科以上 GMV 退费率分母 | 可 sum；分母含义待人工确认 |
| `refund_3plus_subject_headcount` | `subject_count > 3` 且截面退款金额 > 0 的去重用户数 | 3科以上人头退费分子 | 可 sum；分母是否应另设 3科以上用户数待人工确认 |

多维退费率透视表推荐公式：

| 展示指标 | 公式 |
|---|---|
| 当期 GMV 退费率 | `ifnull(sum(${refund_current_gmv}) / sum(${net_income_current_gmv}), 0)` |
| 截面 GMV 退费率 | `ifnull(sum(${refund_section_gmv}) / sum(${net_income_section_gmv}), 0)` |
| 截面人头退费率 | `ifnull(sum(${refund_headcount_section}) / sum(${total_headcount}), 0)` |
| 1科 GMV 退费率 | `ifnull(sum(${refund_1_subject_gmv}) / sum(${net_income_1_subject_gmv}), 0)` |
| 2-3科 GMV 退费率 | `ifnull(sum(${refund_2_3_subject_gmv}) / sum(${net_income_2_3_subject_gmv}), 0)` |
| 3科以上 GMV 退费率 | `ifnull(sum(${refund_3plus_subject_gmv}) / sum(${net_income_3plus_subject_gmv}), 0)` |

## 6. 分桶口径

### 6.1 首 call 总通时

字段来源：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.section_assign_all_call_duration`

处理方式：单独在 `call_duration_raw` 中按 `period_name + lead_id + user_id` 取 `max`，再回连主业务底表分桶。该设计用于避免通时字段参与 `select distinct` 放大业务指标。

分桶：

- `5min以内`
- `5min-10min`
- `10min-15min`
- `15min-20min`
- `20min以上`

待人工确认：`max(section_assign_all_call_duration)` 是否代表业务最终总通时。

### 6.2 总出勤时长

字段来源：`service_dw.dws_service_user_learn_detail_hf.live_learn_duration`

处理方式：按 `begin_time` 派生期次后，按 `period_name + user_id` 汇总总出勤时长，再回连主业务底表分桶。

分桶：

- `没上课`
- `30min以内`
- `30-60min`
- `60-120min`
- `120-180min`
- `180min以上`

待人工确认：同一用户同一期多条线索是否应共享同一上课时长。

### 6.3 深沟阶段

字段来源：

- `service_dw.dwd_crm_assign_private_detail_hf.sale_flow_stage_sequence`
- `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.friend_lead_count`

处理方式：私海表按 `user_number + lead_id` 取最新阶段。阶段 `470` 为双沟，`450` 为深沟；若非深沟/双沟但 `friend_lead_count > 0`，归为已建联。

分桶：

- `新线索（未加好友）`
- `已建联（加好友未深沟）`
- `深沟`
- `双沟`

待人工确认：`sale_flow_stage_sequence` 阶段码和好友兜底规则是否为最新 CRM 口径。

## 7. 已验证口径

2026-06-06 Web 查询验证，在 20260522期、20260529期、20260605期总计层面：

- 三份数据集 `bucket_user_cnt` 总计一致。
- 三份数据集 `conversion_user_cnt` 总计一致。
- 三份数据集 `order_cnt` 总计一致。
- 三份数据集 `section_profit_amt` 总计一致。
- 使用行级 `head_conversion_rate`、`order_conversion_rate`、`section_unit_efficiency` 直接聚合会不一致，属于看板二次聚合错误。

## 8. 待人工确认

- 字段名中的“人数”是否实际应解释为 `lead_count` 线索量。
- 金额字段单位是否稳定为分。
- 转化人头 `conversion_lead_count`、订单数 `order_count` 是否均为正价课口径。
- 整体画像数据集中 `pay_user_head_count` 与 `regular_course_user_count` 的业务区别和展示优先级。
- 整体画像中的有效线索数是否必须始终使用标准 `valid_lead_count`，不得对抖音私信切换 `merge_valid_lead_count`。
- `period_mapping_second_level_department_name is null` 的放宽是否应保留。
- 渠道 CASE 是否需要与最新 `market_channel_case_when_0524.sql` 完全同步。
