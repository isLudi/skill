# 市场顾问部模板取数源 SQL 清单

维护日期：2026-08-08

本文件记录从 `模板取数 -> 模板查询 -> 我的模板 -> 我创建的` 中抓取的市场顾问部模板 SQL。所有条目的使用口径均为 **模板取数**，与数据中心数据集源 SQL、Web BI 看板 canonical SQL 分开维护。模板 raw SQL 只保留线上 `published` 版本的 stable canonical 文件，不保留日期副本；后续排查模板取数代码时优先读取本清单和下表中的具体 raw SQL 文件。

## 维护结论

- 来源页面：`https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`。
- 来源接口：模板 ID 已知时优先使用 `POST https://uanalysis.baijia.com/uanalysis-template/template/detail` 精确回读；创建列表只用于发现，不再决定当前 SQL 路由。
- 同步策略：raw SQL 只保存平台当前有效且已发布模板的线上版本。治理变更必须原位更新远端、发布并回读一致后，再用 `sync-template-sql` 按模板 ID、名称和线上 SQL SHA-256 原位覆盖 stable canonical 文件并清理日期副本；远端已删除模板直接移除 stable SQL 和当前路由，不恢复、不再同步。
- 口径说明：本清单 SQL 的使用口径统一标记为 `模板取数`。若与数据中心或看板 SQL 同名/同类，默认先按来源区分，不自动互相替代。
- 2026-08-08 当前版本：有效渠道归因模板为 `7689, 7808, 8735, 8882, 8948, 9002`。六个模板均保持原模板 ID 原位更新、独立发布、线上 SQL 哈希回读和发布后真实查询；既有申请关系与权限主体不变。
- 0808 渠道 CASE 采用原始顺序逐分支融合结果：175 个 `WHEN` 分支、118 个去重渠道值；模板只按源字段别名做等价适配，不机械切片删除、相邻同值合并或改变优先级。
- `7689` 与 `9002` 同步新增 `20260815期=2026-08-13..2026-08-18`，并从 `2026-08-19` 恢复正常周五期次，首个正常期次为 `20260821期`。发布后查询分别为 `386621`（11057 行）和 `386622`（540 行），均为 `SUCCESS`。
- `8882`、`9002` 继续使用五组连续 CASE + `UNION ALL` + `min_by(rule_group)` 和无碰撞长度前缀键；0808 的 175 条规则均衡为五组、每组 35 条。两个馒头模板复用同一 5×35 first-match 结构，并保留各自原有规则分类作为 fallback。
- 2026-07-23 将 5 个仍有效且已发布的市场顾问渠道归因模板原位更新为 `rule_name like '%北京直播江苏%' then '北京直播江苏'`；模板 id 保持不变，发布后逐个新建查询验证。
- 历史查询验证记录（非当前路由）：`8882 -> 379800 (2523 行)`、`8866 -> 379801 (5237 行)`、`8796 -> 379810 (1566 行)`、`8797 -> 379812 (582 行)`、`8801 -> 379804 (1053 行)` 均为 `SUCCESS`。其中 `8796/8797/8801` 已不在当前线上“我创建的”模板列表，未保留其旧 SQL 或路由入口；`8796/8797` 的单期次验证范围为 `20260710期 <= qici < 20260711期`。
- 2026-07-26 仅原位更新 `AI分析市场顾问部_宽表`（模板 id `9002`）：基于宽表现有字段别名和辅助字段整合 0726 渠道归因，未直接粘贴标准 CASE；保留 `${qici:1}`、`${qici:2}` 两个参数和原 122 个输出字段，并将相同期次半开区间下推至 `lead_raw` 主链。该历史代码已清理，当前线上 SQL 只从上方 stable canonical 入口读取。
- 2026-08-03 原位更新 `业财用户出单明细`（模板 id `7689`）：仅用历史 `market_channel_case_when_0726_legacy.sql` 的 156 条共享渠道分支替换旧的 196 条 `channel_map` 分支，保留模板身份、申请关系、`${dt}`、暑期期次表达式、来源表和 26 个最终字段。线上 SQL 文本 SHA-256 为 `8704c71c2962a75173e66873e3b9d5388d63e7eb0623bfa7b5ae35ad37a38cfa`；发布后查询 `384631` 为 `SUCCESS`。本条为历史记录，当前线上口径以上方 0808 清单为准。

## 当前有效渠道模板清单（0808 规则 / 0815 期次）

| 模板名称 | 模板 id | 状态 | 发布后 SQL SHA-256 | raw SQL | SQL 行数/字节 | 模板参数 | 发布后验证 |
|---|---:|---|---|---|---:|---|---|
| 业财用户出单明细 | 7689 | published | `81c24d5a21dd747807e3641f2edd882693cd6cec50a60fb6a60f91a0f4e4394d` | [`template_query_market_finance_order_detail.sql`](../../resources/raw_sql/template_query_market_finance_order_detail.sql) | 389 / 50702 | `${dt}` | query `386621`，11057 行，29 秒，`SUCCESS` |
| 市场运营专用_多维全链路分析 | 7808 | published | `4f10fa2f7d76db7e3dd49aee115f78b539f19e69e82d04431c4bdbb769c5bf01` | [`template_query_market_wide_analysis.sql`](../../resources/raw_sql/template_query_market_wide_analysis.sql) | 702 / 67324 | `${period_name1}`, `${period_name2}` | query `386596`，9623 行，101 秒，`SUCCESS` |
| 馒头_订单明细_支付时间 | 8735 | published | `8c98bc59e61535395be51a77dd78b6a5637ec29ce56fba7a7e32a7104c13fc48` | [`template_query_market_mantou_order_detail_pay_time.sql`](../../resources/raw_sql/template_query_market_mantou_order_detail_pay_time.sql) | 671 / 63340 | `${day:1}`, `${day:2}` | query `386603`，141 行，93 秒，`SUCCESS` |
| AI分析市场顾问部多科用户成单数据 | 8882 | published | `0a410a877c5895dae41f3bd46241a6fe003f2a20d7c2bf77f0e72fa87aa811ff` | [`template_query_market_multi_subject_order_user.sql`](../../resources/raw_sql/template_query_market_multi_subject_order_user.sql) | 364 / 51027 | `${qici:1}`, `${qici:2}` | query `386604`，102 行，19 秒，`SUCCESS` |
| 馒头_订单明细_流水时间 | 8948 | published | `79e98bd31a718e383adb97b238abd1b9527a1f5a4282b26aa8d136172694c84a` | [`template_query_market_mantou_order_detail_trade_time.sql`](../../resources/raw_sql/template_query_market_mantou_order_detail_trade_time.sql) | 594 / 61243 | `${day:1}`, `${day:2}` | query `386605`，243 行，66 秒，`SUCCESS` |
| AI分析市场顾问部_宽表 | 9002 | published | `71274379824c29b4216041b0841a3696a41525589d80075fd3ca536941356138` | [`template_query_market_wide.sql`](../../resources/raw_sql/template_query_market_wide.sql) | 191 / 81749 | `${qici:1}`, `${qici:2}` | query `386622`，540 行，130 秒，`SUCCESS` |

下方表格仅保留历史验证记录；历史 SQL 文本和日期文件均已清理，当前线上口径只从本节 stable 清单路由。

## 历史模板归档

| 模板名称 | 模板 id | 状态 | 更新时间 | 使用口径 | raw SQL | SQL 行数 | SQL 字节 | 主要依赖表 | 模板参数 | 用途与说明 | 注意事项 |
|---|---:|---|---|---|---|---:|---:|---|---|---|---|
| AI分析市场顾问部_宽表 | 9002 | published | 2026-07-26 19:42:19 | 模板取数 | 已清理历史代码；当前入口为 [`template_query_market_wide.sql`](../../resources/raw_sql/template_query_market_wide.sql) | - | - | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`finance_dw.app_finance_performance_extend_details_hf`<br>`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`<br>`service_dw.dwd_crm_assign_private_detail_hf`<br>`service_dw.dm_crm_lead_stats_detail_hf`<br>`service_dw.app_h_crm_lead_task_process_info_detail_hf`<br>`service_dw.app_h_crm_lead_employee_workload_detail_hf`<br>`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`<br>... +5 | `${qici:1}`<br>`${qici:2}` | 综合沉淀市场顾问考勤、转化、过程、线索、多科与期次数据；0726 渠道归因通过宽表源别名和辅助字段整合。 | 历史查询 `381050` 为 `SUCCESS`，当前 SQL 只从 stable 入口读取。 |
| 业财用户出单明细 | 7689 | published | 2026-08-03 20:06:04 | 模板取数 | 历史代码已清理；当前入口为 [`template_query_market_finance_order_detail.sql`](../../resources/raw_sql/template_query_market_finance_order_detail.sql) | - | - | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `${dt}` | 按运营期次输出市场顾问线索、转化、订单、收退款和渠道明细；`channel_map` 以 0808 线上发布版本为准。 | 历史查询 `384631` 为 `SUCCESS`；当前验收见上方清单。 |
| AI分析市场顾问部多科用户成单数据 | 8882 | published | 2026-07-23 17:48:29 | 模板取数 | 历史代码已清理；当前入口为 [`template_query_market_multi_subject_order_user.sql`](../../resources/raw_sql/template_query_market_multi_subject_order_user.sql) | - | - | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | - | 多科用户成单分析，按用户/期次/渠道/年级等维度沉淀成单与多科相关字段。 | 历史渠道归因代码不再路由；当前线上版本见上方清单。 |
| AI分析市场顾问部分周期转化数据 | 8866 | published | 2026-07-23 17:48:39 | 模板取数 | [`template_query_market_period_conversion.sql`](../../resources/raw_sql/template_query_market_period_conversion.sql) | 257 | 17632 | `finance_dw.app_finance_performance_extend_details_hf`<br>`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`<br>`service_dw.dim_crm_assign_rule_lead_detail_hf`<br>`temp_table.dingxi01_jiagou_zx` | - | 分周期转化分析，按期次、渠道、年级、人员等维度输出 GMV、退款等周期转化字段。 | 线上当前 published 版本已回读并写入 stable 文件。 |
| AI分析市场顾问部员工架构数据 | 8878 | published | 2026-06-11 15:23:28 | 模板取数 | [`template_query_market_employee_org.sql`](../../resources/raw_sql/template_query_market_employee_org.sql) | 83 | 3824 | `finance_dw.dim_finance_employee_df` | - | 市场顾问部员工架构模板，输出市场顾问部员工、部门、经理、小组等架构字段。 | 线上当前 published 版本已回读并覆盖本地旧代码。 |
| AI分析市场顾问部进量数据 | 8867 | published | 2026-06-05 16:35:43 | 模板取数 | [`lead_assign_plan_actual_valid_count.sql`](../../resources/raw_sql/lead_assign_plan_actual_valid_count.sql) | 96 | 3092 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`<br>`service_dw.dim_crm_assign_rule_lead_detail_hf`<br>`service_dw.dim_crm_assign_rule_plan_item_info_hf`<br>`temp_table.dingxi01_plan_id`<br>`temp_table.dingxi01_jinliang_goal`<br>`temp_table.dingxi01_jiagou_db` | - | 市场顾问部进量模板，输出计划进量和实际有效线索相关字段。 | 模板 SQL 与 canonical `lead_assign_plan_actual_valid_count.sql` 完全一致；raw SQL 去重后指向该唯一文件，使用时仍说明来源为模板取数。 |

## 口径使用规则

- 用户明确说“模板取数代码”“模板中的最新代码”“平台模板取数里存储的代码”时，优先读取本文件与下表中的对应 raw SQL 文件。
- 用户要排查 Web BI 看板或数据中心数据集时，不要直接用本批模板 SQL 替代 canonical 看板 SQL；先确认来源口径是否就是模板取数。
- 本批 SQL 来源为模板平台 `sqlDetail`，可能包含模板参数 `${...}`；生成验证版 SQL 时可临时替换为实际日期/期次，写回模板或知识库时仍保留模板参数形态。
- 若同一业务主题同时存在 canonical raw SQL 和模板取数 raw SQL，回答时必须说明当前采用的是“模板取数口径”还是“看板/数据中心口径”。
- 两个馒头模板永久归入 `market_consultant` 域，必须与其他市场顾问渠道消费者一同盘点和更新。支付时间/流水时间当前 SHA-256 分别为 `8c98bc59e61535395be51a77dd78b6a5637ec29ce56fba7a7e32a7104c13fc48`、`79e98bd31a718e383adb97b238abd1b9527a1f5a4282b26aa8d136172694c84a`；后续不得恢复会放大 stages 的重 CTE 多路扫描。
- `业财用户出单明细` 是共享渠道 CASE 的强制同步消费者。每次更新 `market_channel_case_when_MMDD.sql`，必须把模板 id `7689` 纳入规则级差异检查、同 id 保存/发布、SQL 哈希回读、真实模板查询和本清单 raw SQL 刷新；不得只更新数据中心或其他 AI 模板。

## 同步来源

- 同步命令：`D:\anaconda3\python.exe scripts\usql_web_query.py sync-template-sql --target-skill market --template-id <模板ID> --template-name <模板名称> --canonical-file <stable路径>`；Apply 必须追加 dry-run 产生的精确计划哈希和 `--write`。
- raw SQL 文件已按模板取数来源单独归档，后续排查以本清单中的 raw SQL 为准。
