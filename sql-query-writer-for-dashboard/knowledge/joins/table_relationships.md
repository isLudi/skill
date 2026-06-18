# 表关系

## CRM 私海与线索统计

- 主表：`service_dw.dwd_crm_assign_private_detail_hf`
- 可关联表：`service_dw.dm_crm_lead_stats_detail_hf`
- 候选 join key：`lead_id`、`user_number`/`user_id`
- 状态：待人工确认。字段类型和主键唯一性需从历史看板 SQL 或业务文档确认。

## 线索统计与全链路数据

- 主表：`service_dw.dm_crm_lead_stats_detail_hf`
- 可关联表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- 候选 join key：`lead_id`
- 状态：库名前缀已由百家字段目录确认。字段类型、分区对齐和主键唯一性仍需人工确认。

## 留痕全链路与分配规则

- 主表：`service_dw.dm_crm_trace_lead_full_link_data_hf`
- 可关联表：`service_dw.dim_crm_assign_rule_lead_detail_hf`
- 候选 join key：`trace_id`、`lead_id`
- 历史频率：data-map 500 条成功 SQL 中分别出现 75 次和 60 次。
- 范围限定：历史 SQL 出现 `first_level_department_name = 'H业务线'`、`second_level_department_name = '精品班学部'`。
- 状态：来自高频查询历史，join key 需结合去重口径确认。

## 线索与归因流水

- 主表：`service_dw.dm_crm_trace_lead_full_link_data_hf` 或 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- 可关联表：`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`
- 候选 join key：`lead_id`
- 常用指标字段：`income_amount`、`refund_amount`、`order_number`、`original_order_number`、`performance_employee_email_prefix`、`trade_period_mapping_*`、`pay_period_mapping_*`
- 员工维表关联：`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.performance_employee_email_prefix = finance_dw.dim_finance_employee_df.email_prefix`
- 范围限定：归因流水表需重点检查 `performance_first_level_department_name`、`performance_second_level_department_name`、`performance_third_level_department_name`。
- 状态：字段结构已根据 `E:\2000_work\GAOTU\归因流水粒度统计明细表.docx` 补全。金额字段通常以分为单位，是否 `/100` 需按指标口径确认。

## 员工维表补充新老顾问

- 主表：`finance_dw.dim_finance_employee_df`
- 可关联表：业务表中的员工邮箱前缀字段，例如 `employee_email_prefix`、`performance_employee_email_prefix`；也可关联首 call 任务表的 `account_id`
- 候选 join key：`finance_dw.dim_finance_employee_df.account_id = gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf.account_id`；或 `finance_dw.dim_finance_employee_df.email_prefix = <业务表>.employee_email_prefix`
- 常用字段：`account_id`、`employee_email_name`、`email_prefix`、`first_enroll_date`、`last_enroll_date`、`is_on_job`、`first_level_department_name`、`second_level_department_name`
- 范围限定：`first_level_department_name = 'H业务线'`，必要时加 `second_level_department_name = '精品班学部'`。
- 状态：字段结构已根据 `E:\2000_work\GAOTU\员工维表.docx` 补全；入离职口径需结合业务规则确认。

## 顾问首 call 任务与员工维表

- 主表：`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`
- 可关联表：`finance_dw.dim_finance_employee_df`
- 候选 join key：`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf.account_id = finance_dw.dim_finance_employee_df.account_id`
- 常用过滤：首 call 表必须加 `dt`、`hour`；顾问首 call 使用 `task_generate_rule_type = 2`、`is_del = 0`；只统计已完成任务时使用 `first_call_status = 3`。
- 期次字段：`biz_number` 是任务期 number，不等同于 `qici`/`period_name`，如需与看板期次合并必须确认映射。
- 外呼过程看板桥接：先用首 call 表 `account_id` 关联员工维表，再用员工维表 `employee_email_name` 或 `email_prefix` 关联主数据中的 `employee_email_name`/`employee_email_prefix`。不要把 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.ad_account_id` 当成员工 `account_id` 使用。
- 首 call 任务指标默认 join：`first_call_task.account_id = employee_map.account_id` 后，使用 `employee_map.employee_email_name = data.employee_email_name` 且 `first_call_task.user_id = data.user_id` 关联主数据；一般不使用 `lead_id` 或 `period_name` join，除非业务提供任务期 number 到期次名的映射。
- 禁用来源：生成新的 `is_f_call`、首 call 任务数、首 call 任务率 SQL 时，不得使用 `service_dw.app_h_crm_lead_task_process_info_detail_hf.call_answer_lead_count`。该旧过程表字段只可作为电话接通/任务过程字段参考，不能代表 CRM 首 call 任务完成数。
- 员工维表范围：员工维表必须加 `dt`，并使用与主查询一致的一级/二级/三级部门范围；若主查询覆盖多个二级部门，不要将员工维表硬编码为 `市场部/市场顾问部`。
- 状态：字段结构已根据 `E:\2000_work\GAOTU\顾问首call数据分析表.docx` 补全；2026-05-22 起作为新的首 call 任务强制口径。

## 市场顾问转化看板全链路数据

- 主表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- 来源：`resources/raw_sql/market_consultant_conversion.sql`
- 分区：`dt`、`hour`
- 强制范围：`section_assign_employee_first_level_department_name`、`section_assign_employee_second_level_department_name`、`section_assign_employee_third_level_department_name`、`period_mapping_first_level_department_name`
- 维度：`period_name`、`channel_map`、`rule_name`、`grade_1`、`depart_1`、`depart`、`jingli`、`zhuguan`、`employee_email_name`
- 状态：历史 SQL 口径已入库，字段类型和部分业务口径待人工确认。

## 市场渠道用户画像分析关系

- 来源：`resources/raw_sql/market_channel_conversion_profile_call_duration_dataset.sql`、`resources/raw_sql/market_channel_conversion_profile_learn_duration_dataset.sql`、`resources/raw_sql/market_channel_conversion_profile_deep_stage_dataset.sql`、`resources/raw_sql/market_channel_conversion_profile_overall_dataset_fixed.sql`、`resources/raw_sql/refund_rate_multidim.sql`。
- 主表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`。
- 主表范围：`section_assign_employee_first_level_department_name = 'H业务线'`、`section_assign_employee_second_level_department_name = '市场部'`、`section_assign_employee_third_level_department_name = '市场顾问部'`、`virtual_third_department_name = '市场顾问部'`；期次映射一级为 `H业务线` 或空，二级为 `市场部/精品班学部` 或空。
- 三数据集共同粒度：`period_name + channel_map + channel_group + grade_name + analysis_type + bucket_name + bucket_sort`。
- 首 call 通时：同一主表单独抽取 `section_assign_all_call_duration`，按 `period_name + lead_id + user_id` 取 `max` 后回连 `lead_base` 分桶。该字段只用于分桶，不参与业务指标 `select distinct`，避免同一线索因通时快照差异放大指标。
- 上课时长：`service_dw.dws_service_user_learn_detail_hf` 按 `begin_time` 派生 `period_name`，按 `period_name + user_id` 汇总 `live_learn_duration` 后回连主表分桶。行课表范围限定 `course_first_level_department_name = 'H业务线'`、`course_second_level_department_name in ('精品班学部','市场部')`、`is_need_attend = 1`。
- 深沟阶段：`service_dw.dwd_crm_assign_private_detail_hf` 按 `user_number + lead_id` 取最新 `private_sea_update_time`，`sale_flow_stage_sequence = 450/470` 分别映射深沟/双沟；非深沟双沟时用主表 `friend_lead_count > 0` 兜底为已建联。
- 渠道组：`temp_table.shenbaoxin_channel_group` 通过 `channel = channel_map` 关联，字段结构、维护来源和唯一性待人工确认。
- 指标使用：`bucket_user_cnt`、`conversion_user_cnt`、`order_cnt`、`section_profit_amt` 可加和；`head_conversion_rate`、`order_conversion_rate`、`section_unit_efficiency` 是行级比率，透视表总计必须用可加和字段重算，不得直接 `sum` 或 `avg`。
- 整体画像数据集：`market_channel_conversion_profile_overall_dataset_fixed.sql` 不做外部 join，仅使用全链路主表，按 `period_name + channel_map + grade_name + manager_name` 输出整体线索、有效线索、成交用户、科目档位、收入和订单指标。
- 多维退费率数据集：`refund_rate_multidim.sql` 不做外部 join，仅使用全链路主表，按 `period_name + channel_map + grade_name + jingli + zhuguan + employee_email_name` 输出当期/截面 GMV 退费率、人头退费率、1科/2-3科/3科以上退费率所需的分子和分母字段。该数据集不输出行级退费率，透视表必须用分子分母字段重算。
- 整体画像修复点：新增 `virtual_third_department_name = '市场顾问部'` 与三个分桶数据集保持范围一致；`valid_lead_count` 使用标准宽表字段汇总，不再对 `抖音私域`/`抖音私信` 切换 `merge_valid_lead_count`；`lead_id` 仅用于 `src` 阶段防止 `select distinct` 折叠多线索，最终不输出。
- 状态：2026-06-06 Web 查询已验证三份分桶 SQL 可执行，且 20260522期、20260529期、20260605期在总计层面核心可加和指标一致；整体画像 SQL 已在 Web 端跑出结果预览，但三期期次汇总下载受页面权限/下载控件限制未完成，字段业务含义、金额单位、通时 max 口径、整体画像有效线索 merge 禁用口径和 null 映射部门放宽条件仍需人工确认。

## 线索分配计划与实际有效量看板关系

- 来源：`resources/raw_sql/lead_assign_plan_actual_valid_count.sql`
- 实际量主表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- 计划侧主表：`service_dw.dim_crm_assign_rule_lead_detail_hf`
- 计划 item 表：`service_dw.dim_crm_assign_rule_plan_item_info_hf`
- 计划组维护表：`temp_table.dingxi01_plan_id`，来源 Excel `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\plan_id.xlsx`
- 架构临时表：`temp_table.dingxi01_jiagou_db`
- 实际量范围：`section_assign_employee_first_level_department_name = 'H业务线'`、`section_assign_employee_second_level_department_name = '市场部'`、`period_mapping_first_level_department_name = 'H业务线'`；未限定三级部门和期次映射二级部门，复用时需按业务补充或保留占位。
- 实际量聚合：按 `rule_name + employee_email_name` 汇总 `sum(lead_count)` 为 `lead`、`sum(valid_lead_count)` 为 `valid_lead`。
- 计划 item 关联：`service_dw.dim_crm_assign_rule_lead_detail_hf.rule_id = service_dw.dim_crm_assign_rule_plan_item_info_hf.rule_id` 且 `plan_id` 相等，同时限定计划 item `dt/hour` 和 `is_del = '0'`。
- 计划组过滤：`temp_table.dingxi01_plan_id.group_id = service_dw.dim_crm_assign_rule_lead_detail_hf.group_id`，再用 `pl.group_id is not null` 仅保留已维护规则组。`temp_table.dingxi01_plan_id` 的推荐唯一键是 `qici + group_id`；若输出 `pl.qici` 或 `pl.group_name`，应补充 `pl.qici = split_part(f.rule_name, '-', 1)` 或其他期次条件。
- 实际与计划合并：`fp.rule_name = vd.rule_name` 且 `fp.employee_email_name = vd.employee_email_name`。
- 架构补充：`temp_table.dingxi01_jiagou_db.employee_email_name = fp.employee_email_name` 且 `substr(qici, -5) = fp.group_period_name`；该关联只用期次尾号，跨年份可能重复。
- 状态：新增 SQL 口径已入库；`temp_table.dingxi01_plan_id` 已按 Excel 补全字段和 key 检查；计划 item 表字段结构、`assign_lead_count` 含义、不同小时偏移、规则名拆分格式和架构 join 唯一性仍需人工确认。

## 线索与行课数据

- 主表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- 可关联表：`service_dw.dws_service_user_learn_detail_hf`
- 候选 join key：`user_number`、`lead_id`、课程/期次字段
- 状态：待人工确认。

## 外呼过程数据看板关系

- 来源：`resources/raw_sql/outbound_call_process_dashboard.sql`
- 主表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- 主表范围：截面分配顾问限定 `H业务线/市场部/市场顾问部`；期次映射一级部门限定 `H业务线`，期次映射二级部门允许 `市场部` 和 `精品班学部`。
- 私海阶段：通过 `f.user_id = service_dw.dwd_crm_assign_private_detail_hf.user_number` 关联，取最新私海阶段、深沟、双沟。
- 线索统计：通过 `f.lead_id = service_dw.dm_crm_lead_stats_detail_hf.lead_id` 关联，补充首呼接通时间差。
- 异常标签：通过 `service_dw.app_user_attribute_label_gaia_wide_df.user_number = f.user_id` 关联，补充异常流量。
- 双表发送：新版在 `data` CTE 中新增 `service_dw.app_h_crm_lead_task_process_info_detail_hf` 的 `sbb` 关联，通过 `sbb.assign_employee_email_name = f.employee_email_name` 与 `sbb.user_id = f.user_id` 补充 `send_double_table`，生成 `yi_huishou`。
- 外呼工作量：通过 `service_dw.app_h_crm_lead_employee_workload_detail_hf.user_number = data.user_id` 与 `section_assign_employee_email_prefix = data.employee_email_prefix` 关联，补充外呼次数、接通次数、通话时长和长通话。
- 首 call 任务：必须使用 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`，按 `first_call_status = 3` 统计已完成首 call；该表通过 `account_id` 先关联 `finance_dw.dim_finance_employee_df.account_id`，再用员工维表中的 `employee_email_name` 或 `email_prefix` 与主数据员工字段桥接。旧版 `service_dw.app_h_crm_lead_task_process_info_detail_hf.call_answer_lead_count` 已废弃为首 call 任务来源。
- APP 登录：`dw.dim_cstm_active_user_c_appliction_mb_df` 与 `dw.dws_user_active_user_c_appliction_hf` 通过 `user_number` 合并日级和小时级登录标记，再用 `user_number = data.user_id` 关联主线索。
- 架构临时表：`temp_table.dingxi01_jiagou_db` 通过 `qici + employee_email_prefix` 关联。
- 课次映射：`temp_table.dingxi01_daoke_1_6_t` 通过 `qici + qudao + grade + begin_time` 关联行课记录；新版先在 `daoke` CTE 预聚合 `has_daoke/has_v_daoke`，最终层再通过 `qici + user_id + channel_map_1` 关联并按用户去重计数。
- 状态：历史 SQL 口径已入库；外呼工作量、首 call 员工维表范围、`sbb` 最新任务跨期影响和临时表 join 唯一性需人工确认。

## 顾问销售评优看板关系

- 来源：`resources/raw_sql/consultant_sales_ranking_evaluation.sql`
- 主表：`finance_dw.app_finance_performance_extend_details_hf`
- 评优临时表：`temp_table.dingxi01_pingyou_jg`
- 财务流水期次：由 `finance_dw.app_finance_performance_extend_details_hf.trade_time` 按周五规则和部分 2026 年硬编码日期推导 `qici`。
- 订单处理：`trade_type = '正常订单'` 按订单和顾问明细汇总 `price`；`trade_type = '调课调班'` 按 `name + user_id1` 汇总并取第一条非 0 金额记录。
- 架构人产关联：通过 `pg.employee_email_name = rd.name` 与 `pg.qici = rd.qici` 关联，将顾问期次架构、人产、渠道、年级与财务流水合并。
- 周期聚合：同一底层口径分别按 `qici`、`moth`、`quarter`、`half_year` 聚合。`moth` 是原 SQL 字段名，含义为月份。
- 状态：历史 SQL 口径已入库；`temp_table.dingxi01_pingyou_jg` 唯一键、`renchan` 含义和跨周期求和口径需人工确认。

## 顾问部门任职期销售统计关系

- 来源：`resources/raw_sql/consultant_sales_department_tenure.sql`
- 主表：`finance_dw.app_finance_performance_extend_details_hf`
- 组织链表：`dw.dim_employee_chain`
- 架构临时表：`temp_table.dingxi01_jiagou_zx`
- 组织链范围：`array_join(slice(split(path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'`。
- 组织链聚合：按 `dep_path + email_prefix + name` 聚合 `min(begin_time)` 和 `max(end_time)`，得到顾问在该部门路径下的任职时间范围。
- 财务流水范围：`employee_first_level_department_name = 'H业务线'`、`employee_second_level_department_name = '市场部'`、`employee_third_level_department_name = '市场顾问部'`，并按 `trade_time` 推导 `qici >= '20260403期'`。
- 任职期过滤：新版使用 `org_t.email_prefix = dd_0.email_prefix` 做内连接，再用 `dd_0.trade_time >= org_t.begin_time and dd_0.trade_time <= org_t.end_time`，只保留顾问在该部门期间产生的流水。
- 架构补充：`temp_table.dingxi01_jiagou_zx.employee_email_name = rd.name`，补充 `xiaozu`、`jingli` 和 `department`，再派生 `dept = 西安/郑州/未知`。该处仍为姓名关联，唯一性需确认。
- 金额口径：正常订单按明细维度 `sum(price)`；调课调班按 `name + user_id1` 汇总 `price` 并去重；`promit = sum(name_total_price)`，`base_result.pmit = sum(promit)`。
- 日维度排名：在 `trade_date + dept + qici` 内按 `pmit desc, name` 使用 `row_number()` 排名，并用 `lag(pmit) - pmit` 计算 `day_dept_period_need_pmit_to_previous`。
- 期次维度排名：先在 `qici + dept + name + xiaozu + jingli` 粒度汇总 `period_pmit`，再在 `qici + dept` 内按 `period_pmit desc, name` 使用 `row_number()` 排名，并用 `lag(period_pmit) - period_pmit` 计算 `period_dept_need_pmit_to_previous`。
- 期次过滤版本：`resources/raw_sql/consultant_sales_department_tenure_period_20260424.sql` 是旧版固定期次版本，当前未同步本次排名增强逻辑；使用前需确认是否需要按新版通用 SQL 刷新。
- 状态：`dw.dim_employee_chain` 已根据 `E:\2000_work\GAOTU\员工信息表.docx` 补全字段；`end_time` 为空处理、`temp_table.dingxi01_jiagou_zx` 姓名关联唯一性、排名是否允许并列均需人工确认。

## 沟通电话微信明细

- 主表：`service_dw.dws_service_wechat_call_detail_df`
- 可关联表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`、`service_dw.dm_crm_lead_stats_detail_hf`
- 候选 join key：`from_user_number`/`to_user_number` 与用户编号、`from_teacher_email_prefix`/`to_teacher_email_prefix` 与员工邮箱前缀。
- 范围限定：历史 SQL 出现 `employee_first_level_department_name = 'H业务线'`、`employee_second_level_department_name = '精品班学部'`。
- 状态：该表含沟通内容、通话字段，查询时避免 `select *` 和大范围无分区扫描。

## 稳定临时表

- `temp_table.dingxi01_jiagou_db`：架构映射表，来源 Excel `jiagou_xian_zhengzhou.xlsx`。常用字段包括 `employee_email_prefix`、`qici`、`dept_1`、`dept_2`、`department`、`xiaozu`、`jingli`。常用于按员工邮箱前缀补充期次、部门、小组和经理口径。
- `temp_table.dingxi01_daoke_1_6_t`：到课课次映射表，来源 Excel `daoke_t_one_six.xlsx`。常用字段包括 `qici`、`qudao`、`grade`、`begin_time`、`ke_1`、`channel`。常用于首节到课或第 1-6 课课次口径。
- `temp_table.dingxi01_pingyou_jg`：评优架构人产临时表，来源待确认。常用字段包括 `qici`、`employee_email_name`、`dept`、`jingli`、`xiaozu`、`channel`、`renchan`、`grade`、`zaizhi`、`is_emp`。常用于顾问销售评优、人产 ROI 和排名口径。

### 临时表关联注意事项

- 两张临时表均无 `dt`、`hour` 分区，查询时必须使用 `qici`、部门、渠道、年级或员工等范围条件。
- `temp_table.dingxi01_jiagou_db.employee_email_prefix` 可与员工邮箱前缀字段关联；目标表字段名需从看板 SQL 或表结构中确认。
- `temp_table.dingxi01_daoke_1_6_t` 的 `qudao` 与 `channel` 不是同一字段；`qudao` 更像原始渠道，`channel` 更像展示/归因名称。

## 市场顾问转化看板新增临时表

- `temp_table.dingxi01_channel_group`：通过 `channel = channel_map` 补充 `channel_group`。
- `temp_table.shenbaoxin_channel_group`：通过 `channel = channel_map` 关联渠道分组；当前 SQL 仅 join，未输出字段，完整字段结构待确认。
- `temp_table.dingxi01_cost`：通过 `channel = channel_map`、`grade = grade_1`、`qici = period_name` 补充 `cost` 和 `goal`。
- `temp_table.dingxi01_jiagou_zx`：通过 `employee_email_name` 补充 `xiaozu` 和 `jingli`。
- 这些临时表结构来自 SQL 使用字段推断，真实字段类型、维护来源和唯一性需人工确认。

## 市场顾问线索转化到课看板关系

- 来源：`resources/raw_sql/market_consultant_lead_conversion_attendance.sql`
- 主表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- 主表范围：`section_assign_employee_first_level_department_name = 'H业务线'`、`section_assign_employee_second_level_department_name = '市场部'`、`period_mapping_first_level_department_name = 'H业务线'`、`valid_lead_count = '1'`。
- 私海阶段：通过 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.user_id = service_dw.dwd_crm_assign_private_detail_hf.user_number` 关联，并按 `private_sea_update_time desc` 取最新阶段；`sale_flow_stage_sequence in ('450','470')` 分别映射为深沟、已双沟。
- 首呼统计：通过 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.user_id = service_dw.dm_crm_lead_stats_detail_hf.user_number` 关联，当前 raw SQL 仅保留 `first_call_connect_diff_hour` 派生字段，结果层未输出。
- 到课数据：通过 `data.user_id = service_dw.dws_service_user_learn_detail_hf.user_number` 和 `data.qici = 行课派生 qici` 关联；当前主口径用 `lesson_index` / `lesson_index_add` / 班级内开课顺序派生 `auto_ke_1`。
- 到课课次：当前 raw SQL 输出自动课次第 1-6 节到课和第 1-6 节有效到课；普通到课使用 `live_learn_duration > 0`，有效到课使用 `is_valid_live_learn = '1'`。
- 手工课次映射：`temp_table.dingxi01_daoke_1_6_t` 使用 `qici + qudao + grade + begin_time` 与 `qici + channel_map_1 + grade_1 + begin_time` 关联，补充 `manual_ke_1`，不使用 `channel`。
- 对照计数：最终层保留 `auto_matched_lesson_row_cnt`、`manual_matched_lesson_row_cnt`、`manual_auto_same_lesson_row_cnt`、`manual_auto_diff_lesson_row_cnt`、`manual_missing_auto_present_row_cnt`、`auto_missing_manual_present_row_cnt`。
- 架构补充：`temp_table.dingxi01_jiagou_db` 通过 `employee_email_prefix + qici` 关联，输出 `xiaozu`、`department`、`jingli`，并用 `jg.department is not null` 过滤。
- 状态：2026-06-18 已用用户提供的最新到课 SQL 覆盖 raw SQL；该版本不再 join 成本目标表或 `temp_table.shenbaoxin_channel_group`。渠道 CASE 顺序是核心风险，`孟亚飞IP99元` 等特例必须放在泛化规则之前；`孟亚飞-1组-视频号` 已合并为 `孟亚飞9元`。

## 流量画像看板关系

- 来源：`resources/raw_sql/traffic_profile.sql`；2026-05-15 已按用户提供的 `D:\Feishu\city_channel.txt` 覆盖为省份/城市维度版本。
- 主表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- 主表范围：截面分配顾问限定 `H业务线/市场部/市场顾问部`；期次映射一级部门限定 `H业务线`，期次映射二级部门允许 `精品班学部`、`青橙项目部`、`一对一学部`、`本地化大班学部`、`市场部`、`菁英班学部`。
- APP 登录：`dw.dim_cstm_active_user_c_appliction_mb_df` 按 `user_number` 取最新 `last_event_time`，生成近 7 日 `is_app_denglu`；同表再限定 `appliction_name = 'APP'` 取最新 `last_app_channel`。
- 私海阶段：通过主表 `user_id = service_dw.dwd_crm_assign_private_detail_hf.user_number` 关联，按 `private_sea_update_time desc` 取最新阶段，`450/470` 映射为深沟/已双沟。
- 外呼工作量：`service_dw.app_h_crm_lead_employee_workload_detail_hf` 先按 `user_number + lead_id + section_assign_employee_email_prefix` 聚合，再用 `user_number + section_assign_employee_email_prefix` 关联主线索；未带 `lead_id` join，需确认多线索用户是否会重复。
- 到课数据：通过 `data.user_id = service_dw.dws_service_user_learn_detail_hf.user_number` 和 `data.period_name = 行课派生 qici` 关联，再通过 `period_name + channel_map + grade_1 + begin_time` 关联 `temp_table.dingxi01_daoke_1_6_t`。
- 到课课次：`channel_map = '曹忆'` 使用 `ke_1 = '3'`；其他渠道使用 `ke_1 = '1'`。普通到课用 `live_learn_duration > 0`，有效到课用 `is_valid_live_learn = '1'`。
- 成交科目数：`finance_dw.app_finance_performance_extend_details_hf` 按交易时间派生 `qici`，归一化 `course_subject` 后按 `qici + user_id + employee_email_name` 统计 `count(distinct subject)`；最终只用 `qici + user_id` join 主线索，顾问维度未参与 join，需确认重复风险。
- 成本目标：`temp_table.dingxi01_cost` 通过 `channel = channel_map`、`grade = grade_1`、`qici = period_name` 补充 `cost` 和 `goal`。
- 渠道分组：`temp_table.dingxi01_channel_group` 通过 `channel = channel_map` 关联，但当前 SQL 未输出字段。
- 架构补充：`temp_table.dingxi01_jiagou_db` 通过 `qici + department + xiaozu + employee_email_name` 关联但未输出字段；`temp_table.dingxi01_jiagou_zx` 通过 `employee_email_name` 补充 `xiaozu`。
- 省市维度：`province_name`、`city_name`、`city_level_name` 均来自主全链路表，字段存在但归属口径待人工确认。
- 期次范围：当前版本在 `base` CTE 使用 `period_name >= ${period_name1}` 且 `period_name < ${period_name2}`，执行前必须替换参数。
- 结果粒度：`period_name + channel_map + grade_1 + depart_1 + depart + jingli + zhuguan + employee_email_name + province_name + city_name + city_level_name + last_app_channel + sub`。
- 状态：历史 SQL 口径已入库；`date_add` 三参数写法、`podan` 注释与代码不一致、外呼/财务 join 粒度、临时表唯一性、省市城市等级口径需人工确认。

## H业务线二级部门转化看板关系

- 来源：`resources/raw_sql/h_biz_line_department_conversion.sql`；入库时间 2026-05-24。
- 主表：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`
- 主表范围：`section_assign_employee_first_level_department_name = 'H业务线'`；`section_assign_employee_second_level_department_name in ('市场部','精品班学部','青橙项目部','菁英班学部')`；`virtual_third_department_name in ('学习顾问部','市场顾问部','中价产品项目部')`；`period_mapping_first_level_department_name = 'H业务线' or null`。
- 首 call 任务桥接：`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` 通过 `account_id` 关联 `finance_dw.dim_finance_employee_df`，再用员工维表的 `employee_email_name + user_id` 关联主数据的 `employee_email_name + user_id`。
- 渠道分组：`temp_table.shenbaoxin_channel_group` 通过 `channel = channel_map` 补充 `channel_group`（输出别名 `channel_1`）。
- 粒度：部门级别聚合，无顾问个体维度。`zhuanhua` 按 `period_name + channel_map + rule_name + lead_purchase_intention_level2_category_name + depart_1 + dept_name + depart` 分组。
- 渠道 CASE 使用 `resources/raw_sql/market_channel_case_when_0612.sql`。
- 主表 `dt/hour` 均使用 `now - 3h`（一致偏移）；首 call 表使用 `now - 2h`。
- 状态：SQL 口径已入库；`data_base` 使用 `select t1.*`、双层 `select distinct`、首 call 未限定 `task_generate_rule_type = 2`、`valid_lead_count`/`can_renew_ds_count_a` 重复输出、员工维表 `account_id` 去重逻辑、`shenbaoxin_channel_group` 字段存在性、`period_mapping_first_level_department_name is null` 放宽条件需人工确认。

## 退费分析看板关系（历史入口，已合并）

- 新入口：`knowledge/dashboards/market_channel_conversion_profile.md` 的“多维退费率数据集”，来源 `resources/raw_sql/refund_rate_multidim.sql`。
- 历史来源：`resources/raw_sql/refund_multi_subject_user_ratio.sql`、`resources/raw_sql/refund_subject_product.sql`、`resources/raw_sql/refund_reason_analysis.sql`。
- 当前状态：三份独立退费看板文档已改为合并入口说明；旧 SQL 仅作追溯资料。新多维退费率 SQL 改用 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 单表输出分子/分母，不再使用下列财务流水 join。
- 财务主表：`finance_dw.app_finance_performance_extend_details_hf`，按 `trade_time` 推导 `qici`，并限定业绩归属员工 `H业务线/市场部/市场顾问部`。
- 订单流水处理：多科用户退费占比和退费原因分析用 `zong_price`；正常订单按 `employee_email_name + user_id + clazz_name + trade_status` 汇总，调课调班按 `employee_email_name + user_id` 汇总。退费科目产品 SQL 拆为 `gmv_z/gmv_t` 后 `union all`，其中调课调班按 `name` 汇总，粒度需确认。
- lead_id 补充：`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 通过 `original_order_user_number + performance_employee_email_name` 关联财务业绩明细的 `user_id1 + name`，并按 `original_order_user_number order by qici desc` 取最新 `lead_id`。
- 分配规则：`service_dw.dim_crm_assign_rule_lead_detail_hf` 通过 `lead_id + account_domain` 关联，`account_domain` 对应财务表 `email_prefix`，再按 `rule_name` 派生 `channel_1` 和规则期次 `friday_period`。
- 架构补充：`temp_table.dingxi01_jiagou_zx.employee_email_name = name`，补充 `xiaozu`、`jingli`。该表无 `qici`，跨期历史架构需确认。
- 多科分层：先在 `qici + name + channel_1 + jingli + xiaozu + grade_list + user_id1` 粒度计算 `count(distinct subject)`，再聚合出 `refund_1/refund_2/refund_3`。
- 科目产品：按 `subject` CASE 标准化科目，并按 `course_second_level_department_name` 映射 `course_name`。
- 退费原因：`finance_dw.dwd_finance_order_refund_df` 通过 `order_number` 关联财务业绩明细，限定 `dt = now() - 24 hour` 与 `refund_type = '1'` 后输出 `refund_reason`。
- 状态：三份历史 SQL 口径已入库；三参数 `date_add`、订单/用户/顾问去重粒度、退款正负号、`refund_type = '1'` 含义、退款原因表唯一性和课程部门范围均需人工确认。
