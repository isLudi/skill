# 更新日志

## 2026-05-22

- 初始化 `qingcheng-dashboard-sql` Skill，用于隔离维护青橙项目部看板 SQL、指标、临时表和字段匹配规则。
- 创建空知识库目录和模板文件，等待后续青橙看板 SQL 入库。

## 2026-05-22 16:53:55

- 入库青橙看板 SQL `qingcheng_process_data_raw_20260522.sql`，生成 `qingcheng_process_data_raw_20260522` 初始看板知识文档和指标/临时表待确认项。

## 2026-05-22 16:54:58

- 人工整理青橙过程数据 raw SQL：补充看板结构、指标集合、渠道/年级映射、物理表文档、临时表文档、join 关系和表索引。
- 将自动生成的 `metric_1` 至 `metric_22` 占位文档合并为 `knowledge/metrics/qingcheng_process_data_metrics.md`。

## 2026-05-22 18:19:42

- 入库青橙到课 SQL `qingcheng_daoke_raw_20260522.sql`，新增到课看板文档和第 1 至第 6 讲到课/有效到课指标文档。
- 更新 `temp_table.dingxi01_qing_daoke` 语义：`ke_1` 字段在到课 SQL 中承载课次编号 `'1'` 至 `'6'`，不再只按首节课理解。
- 更新 `temp_table.dingxi01_jiagou_db` 语义：到课 SQL 使用 `employee_email_prefix + qici` join 架构，和过程数据 raw 的 `employee_email_name + qici` join key 差异需确认。

## 2026-05-22 18:20:57

- 修正 `scripts/validate_sql_rules.py` 读取 Markdown 字段清单时未剥离反引号导致的字段误报问题。

## 2026-05-22 18:28:41

- 入库青橙转化 SQL `qingcheng_conversion_raw_20260522.sql`，新增转化看板文档和转化指标文档。
- 新增订单业绩表文档 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.md`，记录青橙转化的收入、退款、净营收和业绩归属范围。
- 新增临时表文档 `temp_table.dingxi01_qing_team_jg.md`，记录青橙最新团队架构 join 逻辑。
- 更新青橙渠道/年级映射、成本硬编码、转化 join 关系、范围限定规则、表索引和业务域档案。

## 2026-05-22 20:50:31

- 入库青橙年季月营收 SQL `qingcheng_revenue_year_quarter_month_raw_20260522.sql`，新增营收看板文档和年/季/月营收指标文档。
- 新增财务业绩表 `finance_dw.app_finance_performance_extend_details_hf.md`、员工组织链表 `dw.dim_employee_chain.md` 和青橙组织临时表 `temp_table.dingxi01_qing_zz.md`。
- 更新营收范围口径、join 关系、表索引和业务域档案，明确该 SQL 使用交易发生时员工属于青橙的组织时间窗口过滤。

## 2026-05-22 22:26:16

- 入库青橙团队完成度【月】SQL `qingcheng_team_completion_month_raw_20260522.sql`，新增月度完成度看板文档和指标文档。
- 新增退款明细表 `finance_dw.dm_finance_order_refund_detail_df.md`、订单调课调班维表 `finance_dw.dim_finance_order_change_df.md`、期次月份映射表 `temp_table.dingxi01_qing_qi_moth.md` 和团队月目标表 `temp_table.dingxi01_qing_team_goal.md`。
- 更新团队架构表 `temp_table.dingxi01_qing_team_jg.md` 的适用场景，并补充团队完成度【月】的 join、范围、索引和业务域档案。

## 2026-05-22 22:31:54

- 入库青橙团队完成度【期】SQL `qingcheng_team_completion_period_raw_20260522.sql`，新增期次完成度看板文档和指标文档。
- 新增期次团队目标表 `temp_table.dingxi01_qing_team_g_qi.md`，并更新 `temp_table.dingxi01_qing_qi_moth.md`、`temp_table.dingxi01_qing_team_jg.md`、`temp_table.dingxi01_qing_team_goal.md` 的适用边界。
- 更新团队完成度【期】的 join、范围、索引和业务域档案。

## 2026-05-22 22:39:00

- 入库青橙个人转化 SQL `qingcheng_personal_conversion_raw_20260522.sql`，新增个人转化看板文档和指标文档。
- 更新 `temp_table.dingxi01_qing_team_jg.md` 和 `temp_table.dingxi01_qing_qi_moth.md`，记录个人转化以团队架构表为人员期次骨架并按期次补充月份。
- 更新个人转化的 join、范围、索引和业务域档案，明确该 SQL 不接团队目标表。

## 2026-06-11

- 入库青橙转化宽表-市场渠道 SQL `qingcheng_conversion_wide_table_market_channel_20260611.sql`，新增转化宽表-市场渠道看板文档和指标文档。
- 该 SQL 通过 100+ 分支 CASE WHEN 将中台市场渠道字段映射为统一 `channel_map`，覆盖信息流/B 站信息流/市场私域/名师 IP/KOC/进校/创新商务/图书/途途/文旅等渠道大类。
- 新增物理表文档 `service_dw.app_h_crm_lead_task_process_info_detail_hf.md`，记录 CRM 线索任务处理信息明细小时表的字段和用法（用于标记 F 类首次外呼）。
- 新增临时表文档 `temp_table.shenbaoxin_channel_group.md`，记录市场渠道分组映射表的字段和 join 方式（channel → channel_group）。
- 大幅扩充 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md` 字段清单，从 19 个字段扩充至 50+ 字段，按用途分组（标识/时间/渠道/部门/线索量/转化量/收入退款/意向），新增字段均来源于本 SQL 实际使用。
- 更新 `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`，新增第 9 节"转化宽表-市场渠道版本"，完整记录 100+ 分支的渠道映射逻辑、渠道大类分组和已知风险（AND/OR 优先级、硬编码人名/日期/价格）。
- 更新 `knowledge/joins/common_join_keys.md`，新增 data↔f_call0 和 zhuanhua↔shenbaoxin_channel_group 两组 join key。
- 更新 `knowledge/joins/table_relationships.md`，新增两个关联关系和对应的待确认问题。
- 更新 `knowledge/01_table_index.md`，新增物理表、临时表、看板入口。
- 已知风险和待确认事项：
  - CASE WHEN 中多处 AND/OR 优先级歧义需人工核对。
  - `call_answer_lead_count` 字段语义矛盾（字段名暗示计数，但用作 `lead_id`）。
  - `period_mapping_second_level_department_name` 过滤缺失。
  - `calc_period_name` 周对齐边界（周四）是否与青橙其他看板一致。
  - `shenbaoxin_channel_group` 临时表的来源/刷新/唯一性待确认。
  - bdg_ba 表 hour 偏移不一致（本 SQL 用 -2h，其他看板用 -3h）。
  - 多个指标（order_count, same_lead_period_order_count, jp_cross_department_refund_amount）nvl 后未参与最终聚合，是否为遗漏待确认。

## 2026-06-12 16:59:59

- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 扫描 `青橙项目部` 文件夹，并将原始 `profile.json` 写入本地 runtime 目录。
- 刷新 `knowledge/dashboard_web_profiles/README.md`，当前索引 10 个看板快照。
- 本次 profile 结果：成功 10 个，失败 0 个。

## 2026-06-12 17:25:24

- 从 `sql-query-writer-for-dashboard` 复用并清洗 5 张公共物理表文档：`finance_dw.dim_finance_employee_df`、`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`、`service_dw.app_user_attribute_label_gaia_wide_df`、`service_dw.dim_crm_assign_rule_lead_detail_hf`、`service_dw.dim_crm_assign_rule_plan_item_info_hf`。
- 清除市场侧默认范围值、市场临时表引用和市场专属历史口径，只保留公共表结构说明，并将组织范围占位符改为青橙占位符或待确认说明。
- 新增 3 个中性 SQL 模板：`knowledge/sql_patterns/aggregation_patterns.md`、`knowledge/sql_patterns/cte_patterns.md`、`knowledge/sql_patterns/latest_record_patterns.md`。
- 更新 `knowledge/01_table_index.md`，将新增公共表纳入青橙索引；本轮未同步市场侧 metrics、dashboard 文档、渠道 CASE 或临时表口径。

## 2026-06-12 18:16:48 CRM 开课后转移状态记录边界补充

- 更新 `knowledge/04_qingcheng_project_profile.md`，新增 CRM 线索转移状态记录边界：线索转移必须在当期开课前完成，数据库侧才能记录该转移状态。
- 更新 `knowledge/sql_patterns/dashboard_query_patterns.md`，要求排查线索归属、顾问转移、退前/退后线索或 CRM 当前状态不一致时，先核对操作时间是否晚于当期开课时间。
- 更新 `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`，记录开课后退费或转移顾问可能导致数据库仍保留原顾问/原期次/原架构口径数据。
- 该规则来自用户补充的 CRM 系统限制；青橙具体看板适用性和是否存在开课后转移状态独立明细表均待人工确认。

## 2026-06-12 22:30
- 使用 `usql-web-query-operator/scripts/read_dashboard.py profile-folder` 扫描 `青橙播报` 文件夹中 6 个以 `推送` 开头的转化看板，原始 `profile.json` 保存在 runtime artifacts `20260612-221819`。
- 新增/刷新 `knowledge/dashboard_web_profiles/` 中从 `推送--转化-抖音私信` 到 `推送--转化-进校` 的 6 个看板结构快照。
- 刷新 `knowledge/dashboard_web_profiles/README.md` 索引，当前记录 16 个看板结构快照。

## 2026-06-13 22:44:34

- 入库青橙渠道订单明细 SQL `qingcheng_channel_order_detail_raw_20260613.sql`，新增渠道订单明细看板文档和明细派生字段文档。
- 在 `knowledge/temp_tables/_no_temp_table_usage_cases.md` 记录该 SQL 未使用 `temp_table.*`，避免伪造临时表语义。
- 更新 `knowledge/joins/common_join_keys.md` 和 `knowledge/joins/table_relationships.md`，补充 `gmv ↔ ld` join 在渠道订单明细场景下的复用说明和唯一性/范围风险。
- 更新 `knowledge/01_table_index.md`，新增青橙渠道订单明细 raw 看板入口。
- 已知待确认事项：
  - `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 子查询没有显式青橙范围限定。
  - `lead_id + performance_employee_email_name = employee_email_name` 无法保证 `ld` 唯一，可能放大订单明细。
  - `${begin_trade_time}`、`${end_trade_time}` 为运行时占位符，需在实际查询前替换。
  - 多个状态标记字段和 `is_same_trade_lead_period` 语义仍待人工确认。

## 2026-06-14 14:42:49

- 删除旧版青橙转化 raw 文件 `resources/raw_sql/qingcheng_conversion_raw_20260522.sql` 和旧版看板文档 `knowledge/dashboards/qingcheng_conversion_raw_20260522.md`，切换到用户提供的最新版 `qingcheng_conversion_raw_20260614.sql`。
- 新版转化 raw 同步了渠道和年级映射更新：新增 `私域会话`、补充 `初一` 映射、保留 `if_jieliang` 字段，并更新二级渠道成本硬编码为 `武汉图书=20`、`抖音私信=130`、`进校=70`。
- 修正 `bb_dedup` 与 `ud` 的对齐逻辑：join key 从 `顾问 + 期次 + 二级渠道` 扩展为 `顾问 + 期次 + 二级渠道 + 年级 + 主管`，用于按年级展示真实例子数，不再吞掉同顾问同渠道跨年级的线索量。
- 更新 `knowledge/metrics/qingcheng_conversion_metrics.md`、`knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`、`knowledge/01_table_index.md`、`knowledge/03_range_limit_rules.md`、`knowledge/04_qingcheng_project_profile.md` 和 `knowledge/temp_tables/temp_table.dingxi01_qing_team_jg.md` 以匹配最新版转化口径。
- 待人工确认事项：
  - `if_jieliang` 的业务含义。
  - `bb_dedup` 在完全同维度重复时保留 `rn = 1` 是否仍符合业务预期。
  - `channel_1` 将 `%公域%` 并入 `私域` 是否为最新正式口径。

## 2026-06-14 14:58:17

- 将 `resources/raw_sql/qingcheng_conversion_raw_20260614.sql` 中 9 处裸分隔线改为正式 SQL 注释，修复网页端执行时报错 `Statement.executeQuery() cannot issue statements that do not produce result sets.`。
- 使用网页端再次验证最新版转化 raw SQL，可成功提交并执行，查询 ID 为 `1400562499`。

## 2026-06-15

- 入库青橙转化 SQL 20260615 版 `qingcheng_conversion_raw_20260615.sql`，替换 `qingcheng_conversion_raw_20260614.sql`。
- **期次对齐机制重构**（核心变更）：
  - 新增 `qici0 = regexp_extract(rule_name, '(\d{4}期)', 1)`，从原始 rule_name 提取期次（如 `0612期`）。
  - 新增 `period = regexp_extract(qici, '\d{4}(\d{4}期)', 1)`，从交易时间周对齐 qici 提取期次。
  - `is_on_period` 改为 `dd.qici0 = dd.period`（旧版为 `dd.qici = prc.qici_lead`）。
  - `prc.qici_lead` 改为 `regexp_extract(rule_name, '(\d{4}期)', 1)`（旧版为 `group_period_year+group_period_term` 复杂周对齐计算）。
  - `dd` CTE 输出列新增 `rule_name0`（CASE 映射渠道名，区分于原始 `rule_name`）。
- **渠道映射更新**：`rule_name0` 和 `channel_map_2` CASE WHEN 新增 `%青橙IP% → '青橙IP'` 作为第一优先级分支。
- **hour 偏移调整**：dd(gmv)/ld/bb 从 `-3h` 改为 `-2h`，prc 保持 `-3h`。
- 新增看板知识文档 `knowledge/dashboards/qingcheng_conversion_raw_20260615.md`，删除旧版 0614 文档。
- 新增待确认风险：`regexp_extract` 对 rule_name 格式的依赖、`period` 正则假设、跨年误匹配风险、跨 CTE hour 不一致。

## 2026-06-15 知识路由和反向索引最小改造

- 新增 `knowledge/quick_reference.md` 和 `knowledge/decision_tree.md`，补齐青橙高频看板、表、临时表、debug 场景和反向定位入口。
- 新增 `scripts/build_reverse_indexes.py`，自动生成 `knowledge/reverse_index/field_to_metrics.md`、`metric_to_raw_sql.md`、`table_to_dashboards.md` 和 `join_risk_index.md`。
- 更新 `SKILL.md`、`metadata.json` 和 `scripts/check_skill_integrity.py`，将反向索引纳入加载顺序、维护流程和结构自检。
- 本次只增加检索和路由层，不改写既有指标口径、表语义或 raw SQL。

## 2026-06-17 数据地图字段说明补全

- 登录 `https://tiangong2.baijia.com/dataMap/dataMapNew`，使用数据地图 `tableV2/searchTableList`、`normalColumns`、`partitionColumns` 和 `getDdl` 接口刷新青橙 Skill 物理表字段信息。
- 覆盖 `knowledge/tables` 中 17 张物理表文档；其中 13 张表新增 `数据地图字段补充（2026-06-17）` 小节，追加 1034 个数据地图字段。
- 以数据地图和 DDL 为准回填字段类型和说明占位；复扫结果为字段缺口 0、类型占位 0、说明占位 0。
- 本次维护严格限定在 `qingcheng-dashboard-sql` 内，未同步到市场顾问 Skill；未覆盖 `temp_table.*` 临时表文档，临时表字段仍以本地 Excel、SQL 使用场景和人工维护规则为准。

## 2026-06-17 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：青橙项目部目录下的全部 SQL 数据集。
- 保存 9 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_qingcheng_datasets.md`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-06-17 数据中心源 SQL 对比与 canonical raw_sql 更新

- 将青橙数据中心已确认同源的 8 份源 SQL 映射到现有 canonical raw_sql，其中过程数据、到课、转化、团队完成度、个人转化等以数据中心版本作为最新版本。
- 保留 `data_center_qingcheng_2740_20260617.sql` 作为抖私-转化新增数据中心源 SQL，待后续确认是否进入正式专题口径。
- 更新 `knowledge/dashboards/data_center_qingcheng_datasets.md`，记录每份数据中心 SQL 的用途、主要依赖和冲突处理原则。
