# 市场顾问部模板取数源 SQL 清单

维护日期：2026-07-23

本文件记录从 `模板取数 -> 模板查询 -> 我的模板 -> 我创建的` 中抓取的市场顾问部模板 SQL。所有条目的使用口径均为 **模板取数**，与数据中心数据集源 SQL、Web BI 看板 canonical SQL 分开维护。后续排查模板取数代码时优先读取本清单和下表中的具体 raw SQL 文件。

## 维护结论

- 来源页面：`https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`。
- 来源接口：`POST https://uanalysis.baijia.com/uanalysis-template/template/createList`，读取返回行中的 `sqlDetail`。
- 同步策略：raw SQL 保存平台模板取数当前发布版本；治理变更必须原位更新远端、发布并回读一致后再登记，不用模板 SQL 覆盖数据中心或看板 canonical SQL。
- 口径说明：本清单 SQL 的使用口径统一标记为 `模板取数`。若与数据中心或看板 SQL 同名/同类，默认先按来源区分，不自动互相替代。
- 2026-07-23 将 5 个仍有效且已发布的市场顾问渠道归因模板原位更新为 `rule_name like '%北京直播江苏%' then '北京直播江苏'`；模板 id 保持不变，发布后逐个新建查询验证。
- 最新 SQL 查询验证均为 `SUCCESS`：`8882 -> 379800 (2523 行)`、`8866 -> 379801 (5237 行)`、`8796 -> 379810 (1566 行)`、`8797 -> 379812 (582 行)`、`8801 -> 379804 (1053 行)`。其中 `8796/8797` 使用单期次范围 `20260710期 <= qici < 20260711期`；整月首轮仅因平台 5 分钟上限失败，不作为最新版 SQL 不可执行的证据。

## 模板清单

| 模板名称 | 模板 id | 状态 | 更新时间 | 使用口径 | raw SQL | SQL 行数 | SQL 字节 | 主要依赖表 | 模板参数 | 用途与说明 | 注意事项 |
|---|---:|---|---|---|---|---:|---:|---|---|---|---|
| AI分析市场顾问部多科用户成单数据 | 8882 | published | 2026-07-23 17:48:29 | 模板取数 | [`template_query_market_multi_subject_order_user_20260619.sql`](../../resources/raw_sql/template_query_market_multi_subject_order_user_20260619.sql) | 371 | 44193 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | - | 多科用户成单分析，按用户/期次/渠道/年级等维度沉淀成单与多科相关字段。 | 2026-07-23 已原位更新并保持模板 id；渠道归因包含北京直播江苏。 |
| AI分析市场顾问部分周期转化数据 | 8866 | published | 2026-07-23 17:48:39 | 模板取数 | [`template_query_market_period_conversion_20260619.sql`](../../resources/raw_sql/template_query_market_period_conversion_20260619.sql) | 257 | 17631 | `finance_dw.app_finance_performance_extend_details_hf`<br>`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`<br>`service_dw.dim_crm_assign_rule_lead_detail_hf`<br>`temp_table.dingxi01_jiagou_zx` | - | 分周期转化分析，按期次、渠道、年级、人员等维度输出 GMV、退款等周期转化字段。 | 2026-07-23 已原位更新并保持模板 id；渠道归因包含北京直播江苏。 |
| AI分析市场顾问部转化数据 | 8796 | published | 2026-07-23 17:54:58 | 模板取数 | [`template_query_market_conversion_20260619.sql`](../../resources/raw_sql/template_query_market_conversion_20260619.sql) | 624 | 55309 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dwd_crm_assign_private_detail_hf`<br>`service_dw.app_h_crm_lead_employee_workload_detail_hf`<br>`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`<br>`finance_dw.dim_finance_employee_df`<br>`service_dw.dws_service_user_learn_detail_hf`<br>`temp_table.dingxi01_daoke_1_6_t`<br>`temp_table.dingxi01_cost`<br>`temp_table.dingxi01_jiagou_db`<br>`temp_table.dingxi01_jiagou_zx` | `${period_name1}`<br>`${period_name2}` | 市场顾问部转化数据模板，沉淀线索、成单、GMV、退款、渠道和人员维度的转化宽表。 | 2026-07-23 已原位更新、重新发布并保持模板 id；参数名和比较符不变。 |
| AI分析市场顾问部过程数据 | 8797 | published | 2026-07-23 17:55:12 | 模板取数 | [`template_query_market_process_20260619.sql`](../../resources/raw_sql/template_query_market_process_20260619.sql) | 710 | 58970 | `dw.dim_cstm_active_user_c_appliction_mb_df`<br>`dw.dws_user_active_user_c_appliction_hf`<br>`temp_table.dingxi01_jiagou_db`<br>`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dwd_crm_assign_private_detail_hf`<br>`service_dw.dm_crm_lead_stats_detail_hf`<br>`service_dw.app_user_attribute_label_gaia_wide_df`<br>`service_dw.app_h_crm_lead_task_process_info_detail_hf`<br>`service_dw.app_h_crm_lead_employee_workload_detail_hf`<br>`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`<br>... +3 | `${period_name1}`<br>`${period_name2}` | 市场顾问部过程数据模板，沉淀线索、外呼、首呼、深沟、到课等过程链路字段。 | 2026-07-23 已原位更新、重新发布并保持模板 id；参数名和比较符不变。 |
| AI分析市场顾问部到课数据 | 8801 | published | 2026-07-23 17:55:22 | 模板取数 | [`template_query_market_attendance_20260619.sql`](../../resources/raw_sql/template_query_market_attendance_20260619.sql) | 509 | 53562 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dwd_crm_assign_private_detail_hf`<br>`service_dw.dm_crm_lead_stats_detail_hf`<br>`temp_table.dingxi01_daoke_1_6_t`<br>`service_dw.dws_service_user_learn_detail_hf`<br>`temp_table.dingxi01_jiagou_db` | `${period_name1}`<br>`${period_name2}` | 市场顾问部到课数据模板，沉淀自动/手工课次、到课和有效到课相关字段。 | 2026-07-23 已原位更新、重新发布并保持模板 id；参数名和比较符不变。 |
| AI分析市场顾问部员工架构数据 | 8878 | published | 2026-06-11 15:23:28 | 模板取数 | [`template_query_market_employee_org_20260619.sql`](../../resources/raw_sql/template_query_market_employee_org_20260619.sql) | 80 | 2790 | `finance_dw.dim_finance_employee_df` | - | 市场顾问部员工架构模板，输出市场顾问部员工、部门、经理、小组等架构字段。 | 本文件按模板取数来源单独归档，不默认覆盖同类 canonical 看板 SQL。 |
| AI分析市场顾问部进量数据 | 8867 | published | 2026-06-05 16:35:43 | 模板取数 | [`lead_assign_plan_actual_valid_count.sql`](../../resources/raw_sql/lead_assign_plan_actual_valid_count.sql) | 96 | 3092 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dim_crm_assign_rule_lead_detail_hf`<br>`service_dw.dim_crm_assign_rule_plan_item_info_hf`<br>`temp_table.dingxi01_plan_id`<br>`temp_table.dingxi01_jinliang_goal`<br>`temp_table.dingxi01_jiagou_db` | - | 市场顾问部进量模板，输出计划进量和实际有效线索相关字段。 | 模板 SQL 与 canonical `lead_assign_plan_actual_valid_count.sql` 完全一致；raw SQL 去重后指向该唯一文件，使用时仍说明来源为模板取数。 |
| 馒头_订单明细_支付时间 | 8735 | published | 2026-07-16 20:01:40 | 模板取数 | [`template_query_market_mantou_order_detail_pay_time_20260716.sql`](../../resources/raw_sql/template_query_market_mantou_order_detail_pay_time_20260716.sql) | 412 | 24681 | `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`<br>`finance_dw.app_finance_performance_extend_details_hf`<br>`finance_dw.dws_finance_introduce_detail_hf`<br>`finance_dw.dm_finance_order_refund_detail_df`<br>`finance_dw.dim_finance_order_change_df`<br>`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`temp_table.zhangshiyin01_hesuanqudao` | `${day:1}`<br>`${day:2}` | 按父订单支付时间筛选市场顾问订单明细，输出订单、顾问、渠道、退款课节、人头和科目订单计算字段。 | 当前线上已发布版本；用窗口统计替代重复的 `user_stats`/`subject_stats` 重 CTE，避免执行计划超过 130 stages。诊断与维护规则见 [`mantou_order_detail_pay_time_stage_optimization.md`](../sql_patterns/mantou_order_detail_pay_time_stage_optimization.md)。 |

## 口径使用规则

- 用户明确说“模板取数代码”“模板中的最新代码”“平台模板取数里存储的代码”时，优先读取本文件与下表中的对应 raw SQL 文件。
- 用户要排查 Web BI 看板或数据中心数据集时，不要直接用本批模板 SQL 替代 canonical 看板 SQL；先确认来源口径是否就是模板取数。
- 本批 SQL 来源为模板平台 `sqlDetail`，可能包含模板参数 `${...}`；生成验证版 SQL 时可临时替换为实际日期/期次，写回模板或知识库时仍保留模板参数形态。
- 若同一业务主题同时存在 canonical raw SQL 和模板取数 raw SQL，回答时必须说明当前采用的是“模板取数口径”还是“看板/数据中心口径”。
- `馒头_订单明细_支付时间` 当前发布版本 SHA-256 为 `3781532fd35d262d615e1cabf9076567b5cbf92764ff7665af3139eed98c6aa0`。旧版曾因重 CTE 被多次内联生成 197 stages；后续维护不得恢复为分别扫描 `cs` 的 `user_stats`、`subject_stats`、`lianbao_stats` 三路结构。

## 同步来源

- 抓取命令：`D:\anaconda3\python.exe scripts\usql_web_query.py fetch-template-sql --template-name <模板名称>`
- raw SQL 文件已按模板取数来源单独归档，后续排查以本清单中的 raw SQL 为准。
