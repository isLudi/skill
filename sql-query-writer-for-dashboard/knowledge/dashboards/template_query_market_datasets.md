# 市场顾问部模板取数源 SQL 清单

维护日期：2026-06-19

本文件记录从 `模板取数 -> 模板查询 -> 我的模板 -> 我创建的` 中抓取的市场顾问部模板 SQL。所有条目的使用口径均为 **模板取数**，与数据中心数据集源 SQL、Web BI 看板 canonical SQL 分开维护。后续排查模板取数代码时优先读取本清单和下表中的具体 raw SQL 文件。

## 维护结论

- 来源页面：`https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`。
- 来源接口：`POST https://uanalysis.baijia.com/uanalysis-template/template/createList`，读取返回行中的 `sqlDetail`。
- 写入策略：完整保存平台模板取数中的 SQL 原文，不改写 SQL 语义；不覆盖现有 canonical raw SQL。
- 口径说明：本批 8 份 SQL 的使用口径统一标记为 `模板取数`。若与数据中心或看板 SQL 同名/同类，默认先按来源区分，不自动互相替代。

## 模板清单

| 模板名称 | 模板 id | 状态 | 更新时间 | 使用口径 | raw SQL | SQL 行数 | SQL 字节 | 主要依赖表 | 模板参数 | 用途与说明 | 注意事项 |
|---|---:|---|---|---|---|---:|---:|---|---|---|---|
| AI分析市场顾问部多科用户成单数据 | 8882 | published | 2026-06-18 21:59:45 | 模板取数 | [`template_query_market_multi_subject_order_user_20260619.sql`](../../resources/raw_sql/template_query_market_multi_subject_order_user_20260619.sql) | 370 | 44117 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | - | 多科用户成单分析，按用户/期次/渠道/年级等维度沉淀成单与多科相关字段。 | 本文件按模板取数来源单独归档，不默认覆盖同类 canonical 看板 SQL。 |
| AI分析市场顾问部分周期转化数据 | 8866 | published | 2026-06-18 21:51:14 | 模板取数 | [`template_query_market_period_conversion_20260619.sql`](../../resources/raw_sql/template_query_market_period_conversion_20260619.sql) | 256 | 17560 | `finance_dw.app_finance_performance_extend_details_hf`<br>`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`<br>`service_dw.dim_crm_assign_rule_lead_detail_hf`<br>`temp_table.dingxi01_jiagou_zx` | - | 分周期转化分析，按期次、渠道、年级、人员等维度输出 GMV、退款等周期转化字段。 | 本文件按模板取数来源单独归档，不默认覆盖同类 canonical 看板 SQL。 |
| AI分析市场顾问部每天转化数据 | 8869 | published | 2026-06-18 21:50:37 | 模板取数 | [`data_center_market_2424_20260624.sql`](../../resources/raw_sql/data_center_market_2424_20260624.sql) | 493 | 27417 | `finance_dw.app_finance_performance_extend_details_hf`<br>`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`<br>`service_dw.dim_crm_assign_rule_lead_detail_hf`<br>`temp_table.dingxi01_jiagou_zx`<br>`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | - | 每天转化数据，按日期或期次与渠道/人员维度输出日粒度转化字段。 | 模板 SQL 与数据中心每日转化数据表 SQL 完全一致；raw SQL 去重后指向唯一保留的 `data_center_market_2424_20260624.sql`，使用时仍说明来源为模板取数。 |
| AI分析市场顾问部转化数据 | 8796 | published | 2026-06-18 21:49:44 | 模板取数 | [`template_query_market_conversion_20260619.sql`](../../resources/raw_sql/template_query_market_conversion_20260619.sql) | 623 | 55233 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dwd_crm_assign_private_detail_hf`<br>`service_dw.app_h_crm_lead_employee_workload_detail_hf`<br>`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`<br>`finance_dw.dim_finance_employee_df`<br>`service_dw.dws_service_user_learn_detail_hf`<br>`temp_table.dingxi01_daoke_1_6_t`<br>`temp_table.dingxi01_cost`<br>`temp_table.dingxi01_jiagou_db`<br>`temp_table.dingxi01_jiagou_zx` | `${period_name1}`<br>`${period_name2}` | 市场顾问部转化数据模板，沉淀线索、成单、GMV、退款、渠道和人员维度的转化宽表。 | 可与 canonical `data_center_market_2253_20260628.sql` 对照，但本文件的使用口径为模板取数。 |
| AI分析市场顾问部过程数据 | 8797 | published | 2026-06-18 21:44:09 | 模板取数 | [`template_query_market_process_20260619.sql`](../../resources/raw_sql/template_query_market_process_20260619.sql) | 709 | 58902 | `dw.dim_cstm_active_user_c_appliction_mb_df`<br>`dw.dws_user_active_user_c_appliction_hf`<br>`temp_table.dingxi01_jiagou_db`<br>`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dwd_crm_assign_private_detail_hf`<br>`service_dw.dm_crm_lead_stats_detail_hf`<br>`service_dw.app_user_attribute_label_gaia_wide_df`<br>`service_dw.app_h_crm_lead_task_process_info_detail_hf`<br>`service_dw.app_h_crm_lead_employee_workload_detail_hf`<br>`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`<br>... +3 | `${period_name1}`<br>`${period_name2}` | 市场顾问部过程数据模板，沉淀线索、外呼、首呼、深沟、到课等过程链路字段。 | 可与 canonical `outbound_call_process_dashboard.sql` 对照，但本文件的使用口径为模板取数。 |
| AI分析市场顾问部到课数据 | 8801 | published | 2026-06-18 16:20:46 | 模板取数 | [`template_query_market_attendance_20260619.sql`](../../resources/raw_sql/template_query_market_attendance_20260619.sql) | 508 | 53494 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dwd_crm_assign_private_detail_hf`<br>`service_dw.dm_crm_lead_stats_detail_hf`<br>`temp_table.dingxi01_daoke_1_6_t`<br>`service_dw.dws_service_user_learn_detail_hf`<br>`temp_table.dingxi01_jiagou_db` | `${period_name1}`<br>`${period_name2}` | 市场顾问部到课数据模板，沉淀自动/手工课次、到课和有效到课相关字段。 | 可与 canonical `market_consultant_lead_conversion_attendance.sql` 对照，但本文件的使用口径为模板取数。 |
| AI分析市场顾问部员工架构数据 | 8878 | published | 2026-06-11 15:23:28 | 模板取数 | [`template_query_market_employee_org_20260619.sql`](../../resources/raw_sql/template_query_market_employee_org_20260619.sql) | 80 | 2790 | `finance_dw.dim_finance_employee_df` | - | 市场顾问部员工架构模板，输出市场顾问部员工、部门、经理、小组等架构字段。 | 本文件按模板取数来源单独归档，不默认覆盖同类 canonical 看板 SQL。 |
| AI分析市场顾问部进量数据 | 8867 | published | 2026-06-05 16:35:43 | 模板取数 | [`lead_assign_plan_actual_valid_count.sql`](../../resources/raw_sql/lead_assign_plan_actual_valid_count.sql) | 96 | 3092 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dim_crm_assign_rule_lead_detail_hf`<br>`service_dw.dim_crm_assign_rule_plan_item_info_hf`<br>`temp_table.dingxi01_plan_id`<br>`temp_table.dingxi01_jinliang_goal`<br>`temp_table.dingxi01_jiagou_db` | - | 市场顾问部进量模板，输出计划进量和实际有效线索相关字段。 | 模板 SQL 与 canonical `lead_assign_plan_actual_valid_count.sql` 完全一致；raw SQL 去重后指向该唯一文件，使用时仍说明来源为模板取数。 |

## 口径使用规则

- 用户明确说“模板取数代码”“模板中的最新代码”“平台模板取数里存储的代码”时，优先读取本文件与下表中的对应 raw SQL 文件。
- 用户要排查 Web BI 看板或数据中心数据集时，不要直接用本批模板 SQL 替代 canonical 看板 SQL；先确认来源口径是否就是模板取数。
- 本批 SQL 来源为模板平台 `sqlDetail`，可能包含模板参数 `${...}`；生成验证版 SQL 时可临时替换为实际日期/期次，写回模板或知识库时仍保留模板参数形态。
- 若同一业务主题同时存在 canonical raw SQL 和模板取数 raw SQL，回答时必须说明当前采用的是“模板取数口径”还是“看板/数据中心口径”。

## 同步来源

- 抓取命令：`D:\anaconda3\python.exe scripts\usql_web_query.py fetch-template-sql --template-name <模板名称>`
- raw SQL 文件已按模板取数来源单独归档，后续排查以本清单中的 raw SQL 为准。
