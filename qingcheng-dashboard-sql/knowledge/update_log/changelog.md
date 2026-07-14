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

## 2026-06-21 青橙 lead_id 原始来源追溯模式补充

- 新增 `knowledge/sql_patterns/qingcheng_lead_origin_trace.md`，沉淀青橙某批 `lead_id` 的原始来源/原始分配线索追溯方法，区分当前归因字段与更接近原始来源的候选字段。
- 文档中补充 3 段可复用 SQL 模板：20-50 条 `lead_id` 抽样分布、一行一 `lead_id` 全量导出、以及 `rule_name like '%公开课%'` 为 0 的诊断 SQL。
- 更新 `knowledge/quick_reference.md` 和 `knowledge/decision_tree.md`，新增“追溯某批 lead_id 原始来源”路由入口。
- 更新 `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`，增加来源追溯提示，并记录物理字段 `rn` 会与窗口别名冲突。
- 更新 `knowledge/tables/service_dw.dm_crm_lead_stats_detail_hf.md`，明确 `lead_period_name / lead_group_period_name / lead_period_conversion_begin_time / end_time` 更适合期次标签和保护期窗口校验，而非原始来源追溯。
- 本次知识沉淀基于 2026-06-21 已验证样例：`20260619期 + 青橙IP + 公开课` 切片共 2230 条 `lead_id`，`rule_name like '%公开课%'` 为 0，但 `period_name / lead_period_name` 可命中 `公开课`。

## 2026-06-21 青橙个人完成度折算后产出修复

- 将数据中心 `青橙个人转化` 数据集当前生产 SQL 同步到 `resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`，并保存同源快照 `resources/raw_sql/data_center_qingcheng_2769_20260621.sql`。
- 新增 `knowledge/sql_patterns/qingcheng_personal_completion_discounted_output_risks.md`，沉淀 `折算后产出` 与订单流水不一致时的排查路径、诊断 SQL 和已验证样例。
- 更新个人转化 dashboard/metrics 文档，明确 `折算后产出` 前端公式依赖 `H_promit_4`、`n_H_promit_4`、`Y_promit_4` 和 `refund_4` 源指标正确入桶。
- 记录 3 个关键风险点：课程部门空值必须按年级兜底，`gmv_t` 调课调班必须保留订单/课程粒度，任职窗口开始/结束边界必须使用一致的交易时间字段。
- 本次验证样例：`宋青蔓` 差异来自调课调班退款 `1073.61`，`李孟笛06` 和 `许世杰05` 差异来自空课程部门流水未进入 H 班课桶。

## 2026-06-22 青橙团队完成度调课调班链路修复

- 将 runtime 中已验证的团队完成度【月】和团队完成度【期】SQL 同步覆盖到 canonical raw SQL：`qingcheng_team_completion_month_raw_20260522.sql`、`qingcheng_team_completion_period_raw_20260522.sql`。
- 团队完成度同步个人完成度修复口径：课程部门空值按年级兜底，`gmv_t` 调课调班按订单/课程/用户/期次/科目/课程部门粒度汇总，避免 `name + user_id1` 粗粒度去重吃掉退款或吞掉明细。
- 任职窗口同步个人完成度口径，使用 `trade_time >= begin_time` 和 `trade_time <= end_time`，避免团队完成度用 `paid_time >= begin_time` 时纳入支付时间与交易/退款发生时间不一致的记录。
- 补充订单明细侧核对风险：service 表原始 `income_amount/refund_amount` 在部分调课调班链路可能缺失或为 0，核对时需叠加 `transfer_in_amount/transfer_out_amount`，并用 finance 明细补齐 service 缺失事件。
- 看板型 SQL 不引入 `${begin_trade_time}` / `${end_trade_time}` 模板时间参数，继续通过期次、目标表和架构表控制展示范围。

## 2026-06-22 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：青橙项目部目录下的全部 SQL 数据集。
- 保存 1 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_qingcheng_datasets.md`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-06-22 青橙完成度调课调班主交易层修复

- 同步修改个人完成度、团队完成度【期】、团队完成度【月】三份 SQL：`dim_finance_order_change_df` 从只接退款明细层改为同时接入 `rd/t4` 主交易层。
- `order_change` 链路从 `parent_order_number` 单点关联改为展开 `order_number`、`parent_order_number`、`original_order_number`、`latest_child_order_number`，按订单号聚合后复用。
- `biz_type` 覆盖范围从 `biz_type = 2` 改为 `biz_type in (2, 7)`，避免漏掉青橙 `biz_type=7` 的调课调班链路。
- 主交易层命中内部调课调班调入/调出后，不进入 `income`、`refund`、`refund_4` 和科目数，避免把调出退款误算为 4 节内外部退费。
- 期次推导同步改为 `interval` 写法，避免平台将 Presto 三参数 `date_add` 解析为 Hive 两参数函数。
- 网页端验证：`谷锦茜` `20260619期` 修复后 `income=9200`、`refund=4800`、`H_promit_4=4400`、折算后产出 `4400`；团队期次和月度小范围验证 SQL 均执行成功。

## 2026-06-24 18:47:53

- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 扫描 `青橙项目部` 文件夹，并将原始 `profile.json` 写入本地 runtime 目录。
- 刷新 `knowledge/dashboard_web_profiles/README.md`，当前索引 10 个看板快照。
- 本次 profile 结果：成功 10 个，失败 0 个。

## 2026-06-24 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：青橙项目部目录下的全部 SQL 数据集。
- 保存 9 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_qingcheng_datasets.md`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-06-24 青橙看板编辑页指标公式与 SQL 联动补充

- 使用 `usql-web-query-operator/scripts/read_dashboard.py profile-edit-dashboard` 只读抽取青橙项目部 10 个看板的编辑页配置，生成 `knowledge/dashboard_web_profiles/edit_metrics/`。
- 新增 `knowledge/metrics/qingcheng_dashboard_metric_formula_linkage.md`，把看板前端自定义公式、BI 模型指标、数据中心源 SQL 和已知排查顺序串联起来。
- 更新 `knowledge/dashboard_web_profiles/README.md`、`knowledge/quick_reference.md` 和 `knowledge/decision_tree.md`，新增“看板前端公式/字段配置/SQL 联动”的路由入口。
- 清理已被 20260624 最新数据中心快照替代的旧快照：`data_center_qingcheng_2740_20260617.sql`、`data_center_qingcheng_2769_20260621.sql`、`data_center_qingcheng_2769_20260622.sql`。
- 本次维护不修改生产看板、不发布看板、不执行 SQL 结果下载；编辑页 profile 仅调用读取类接口。

## 2026-06-24 raw SQL 重复快照收敛

- 按 SQL 正文哈希比对 `resources/raw_sql`，确认 6 个 20260624 数据中心快照与既有 canonical raw SQL 完全一致，删除重复副本，仅保留 canonical 文件。
- 数据中心清单、编辑页指标快照和指标-SQL 联动文档已改为引用单一 SQL 文件，避免同一 SQL 因文件名不同被误识别为两个数据集。
- 保留映射：`青橙到课` -> `qingcheng_daoke_raw_20260522.sql`；`年季月营收情况` -> `qingcheng_revenue_year_quarter_month_raw_20260522.sql`；`团队完成度【月】` -> `qingcheng_team_completion_month_raw_20260522.sql`；`团队完成度【期】` -> `qingcheng_team_completion_period_raw_20260522.sql`；`青橙个人转化` -> `qingcheng_personal_conversion_raw_20260522.sql`；`转化-宽表-市场渠道` -> `qingcheng_conversion_wide_table_market_channel_20260611.sql`。
- `青橙-过程数据`、`转化数据`、`抖私-转化` 的 20260624 数据中心 SQL 与现有历史 SQL 不完全一致，暂保留 20260624 快照作为当前数据中心版本。

## 2026-06-25 青橙转化数据集课程部门名单扩充

- 根据 `D:\Feishu\task_1426616138_1782372877570.xlsx` 订单明细补充青橙转化数据集课程部门白名单。
- 在 `data_center_qingcheng_2460_20260624.sql` 和 `qingcheng_conversion_raw_20260615.sql` 的 `gmv` 过滤中新增一级部门 `CA业务线`、`创新中心`。
- 同步新增二级部门 `创新学部`、`升学规划中心`、`线上考研学部`，保持数据中心源 SQL 与青橙历史转化 raw SQL 的课程部门范围一致。
- 网页端验证通过：`Presto` 引擎下用精确部门组合 probe 成功返回并下载 17 行结果，命中 `创新中心-Theta智学项目部`、`H业务线-升学规划中心`、`CA业务线-线上考研学部`、`CA业务线-创新学部`。
- 同一 probe 在 `doris-presto` 下出现 `PRESTO_817034371362430977 - Connection is not available` 连接池超时，属于引擎连接问题，不是权限或 SQL 语义问题。

## 2026-06-25 青橙转化 canonical raw SQL 与知识文档对齐

- 将 `runtime/tmp/qingcheng_conversion_raw_aligned_20260625.sql` 回写覆盖到 canonical raw SQL `resources/raw_sql/qingcheng_conversion_raw_20260615.sql`。
- 同步修正文档引用，清理仍指向 `qingcheng_conversion_raw_20260614.sql` / `qingcheng_conversion_raw_20260614.md` 的旧入口，统一到 0615 版本文档。
- 更新 `knowledge/metrics/qingcheng_conversion_metrics.md` 的当期判断口径为 `dd.qici0 = dd.period`，不再沿用旧版 `dd.qici = prc.qici_lead` 描述。
- 在转化 raw 看板说明、范围规则、表文档和临时表文档中补充 2026-06-25 课程部门白名单扩容说明，保证 raw SQL、数据中心 2460 SQL 与知识文档一致。

## 2026-06-25 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：青橙项目部目录下的全部 SQL 数据集。
- 保存 1 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_qingcheng_datasets.md`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-06-25 青橙-过程数据 2064 快照与文档对齐

- 数据中心 `青橙-过程数据` 最新快照已同步为 `resources/raw_sql/data_center_qingcheng_2064_20260625.sql`，替换 20260624 版作为当前数据中心 retained snapshot。
- `channel_map_1` 新增 `%抖音正价退费% -> 抖音复用`。
- `channel_map_2` 针对青橙 IP 新增高优先级细分：`%赠失-星义% -> IP星义`、`%赠失-朱博士% -> IP朱博士`、`%赠失-春春% -> IP春春`、`%赠失-郭艺% -> IP郭艺`、`%赠失-亚飞% -> IP亚飞`。
- 同步更新 `knowledge/metrics/qingcheng_dashboard_metric_formula_linkage.md`、两个 2064 看板 edit-metrics profile，以及 `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`，避免知识库继续引用 20260624 旧快照或遗漏新的二级渠道分支。

## 2026-06-26 青橙转化 canonical raw SQL 收敛与营收逻辑统一

- 将 runtime 最新已验证版本 `runtime/tmp/qingcheng_conversion_raw_discounted_podan_final_20260625.sql` 回写为唯一 canonical 转化 SQL：`resources/raw_sql/data_center_qingcheng_2460_20260626.sql`。
- 删除旧版本转化 SQL / 文档：`resources/raw_sql/qingcheng_conversion_raw_20260615.sql`、`resources/raw_sql/data_center_qingcheng_2460_20260624.sql`、`knowledge/dashboards/qingcheng_conversion_raw_20260615.md`。
- 转化结果期次统一为 `trade_timestamp` 周五期次映射：周二到周日归当周周五，周一回拨到上一周周五。
- 转化营收逻辑统一为 service 主明细 + `transfer_in_amount / transfer_out_amount` 内部调课调班剔除；`order_change` / `re_ke` 仅用于调课调班识别和 `refund_4` / 点睛退 2 节口径。
- `podan` 统一为折算净收口径：`((H_promit_4 - Y_promit_4) + n_H_promit_4 * 0.5) > 0`，不再使用简单 `promit > 0`。
- 团队架构补充统一为 `employee_email_name + qici`，不再用最新 `qici` 回填历史转化结果期次。
- 同步更新转化指标文档、表索引、范围规则、团队架构临时表文档、表关系文档、数据中心数据集映射和 dashboard metric linkage。
- 课程一级部门白名单以 0626 canonical SQL 为准，当前包含 `H业务线`、`LL业务线`、`TUTU`、`TT`、`A业务线`、`EM业务线`、`KA业务线`、`TT业务线`、`创新中心`；历史文档中 `CA业务线` 记载不再作为当前 canonical 口径。

## 2026-06-27 青橙完成度任职窗口归属修正

- 将三份 canonical raw SQL 同步修正为按 `coalesce(paid_time, trade_time)` 过滤青橙任职窗口：
  - `resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`
  - `resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql`
  - `resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql`
- 修复原因：旧口径只按 `trade_time` 过滤 `org_t`，会把历史订单在顾问转入青橙后发生的退款误计入青橙个人/团队完成度。
- 已验证样例：顾问 `陈贺新` 于 `2025-05-26` 进入青橙，`user_id=1606647` 的原单支付在 `2023-10`、退款发生在 `2026-06-25`。旧口径命中，修正后排除。
- 同步更新个人/团队完成度 dashboard 文档、join key 文档和风险排查文档，后续排查完成度异常时必须先比对 `paid_time`、`trade_time` 和 `org_t.begin_time/end_time`，不能只看退款发生时间。

## 2026-06-27 青橙渠道订单明细模板升级

- 将模板取数 SQL `template_market_sql_2689_20260627-154011.sql` 升级为新的青橙渠道订单明细 canonical raw SQL：`resources/raw_sql/qingcheng_channel_order_detail_raw_20260627.sql`。
- 旧版 `qingcheng_channel_order_detail_raw_20260613.sql` 已不再作为当前 canonical 版本保留；相关 dashboard 文档入口统一切换到 `knowledge/dashboards/qingcheng_channel_order_detail_raw_20260627.md`。
- 与 2026-06-13 版相比，本次模板版新增 `province_name`、`city_name`、`city_level_name` 三个线索侧地域字段；`gmv ↔ ld` join 逻辑、时间占位符和青橙范围限定保持不变。
- 同步更新订单明细 dashboard 文档、字段说明、快速入口、决策树、无临时表清单和 join 文档，避免继续按旧版字段集合理解该模板 SQL。
## 2026-06-27 青橙原始线索表入库补充

- 使用 `usql-web-query-operator` 的数据地图同步脚本查询 `data_lake_fuwu.dwd_crm_leads_rt`，确认中文名为“线索统计表”，数据地图登记字段 51 个，`partitionColumns` 为空。
- 新增表文档 `knowledge/tables/data_lake_fuwu.dwd_crm_leads_rt.md`，沉淀表用途、字段清单、常用 join key 和风险说明。
- 更新 `knowledge/01_table_index.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`，补充 `crm_leads_id = lead_id` 的原始线索回查关系。
- 记录结论边界：
  - `crm_leads_id` 可按字段语义理解为线索 ID；
  - `previous_model_id` 先按“上一阶段模型 ID / 潜客 ID 候选字段”记录；
  - 2026-06-27 网页 SQL live 补验遇到 `ERR_PROXY_CONNECTION_FAILED` 和执行超时，join 结果样本待网络恢复后补验。

## 2026-06-27 青橙原始线索表 join 小样本补验

- 使用 `usql-web-query-operator` 追加小样本验证 SQL：
  - `verify_lead_to_crm_leads_id_fixed_20260627_16.sql`，query id `1433250612`，验证 `cast(f.lead_id as bigint) = lrt.crm_leads_id`，青橙主宽表 `dt='20260627' and hour='16'` 样本 30 行命中 30 行。
  - `verify_previous_model_id_positive_self_join_20260627.sql`，query id `1433259664`，验证 `lrt.previous_model_id = prev.crm_leads_id`，在 `previous_model_id > 0` 条件下样本 30 行命中 30 行。
- 同步更新 `knowledge/tables/data_lake_fuwu.dwd_crm_leads_rt.md`、`knowledge/joins/common_join_keys.md` 和 `knowledge/joins/table_relationships.md`，将 `crm_leads_id` 关联状态从“待补验”改为“已小样本验证”。
- 风险说明：`previous_model_id is not null` 会抽到大量 `0`，不能直接代表有效上一阶段；追溯上阶段模型时必须加 `previous_model_id > 0`。

## 2026-06-27 青橙完成度调课调班识别修复

- 同步修复个人完成度、团队完成度期次、团队完成度月度三份 canonical raw SQL：
  - `resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`
  - `resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql`
  - `resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql`
- 修复原因：旧逻辑只有在主交易层订单命中 `finance_dw.dim_finance_order_change_df` 且存在调入/调出金额时，才从 `income`、`refund`、`refund_4`、科目统计中排除调课调班。实际排查发现部分主交易层已标记 `trade_type='调课调班'` 的正负流水没有命中该维表，导致正数误入班课营收、负数误入班课退费。
- 修复方式：在 `t4` 增加 `is_internal_order_change`，只要 `rd.trade_type='调课调班'` 即识别为内部调课调班；保留原有 `dim_finance_order_change_df` 命中逻辑作为补充。后续 `income`、`refund`、`refund_4`、`sub/p_sub/r_sub` 统一优先使用 `is_internal_order_change = 1` 排除。
- 已验证样例：
  - 张宁晴 `20260626期`：订单 `417613649250092004` 为 `调出退款/调课调班`，对应调入订单 `421483326725423588`；修复后个人完成度 `refund=0`，不再展示 `1190` 班课退费。
  - 许多03 `20260626期`：订单 `419661531526992745` 为 `调出退款/调课调班`，对应调入订单 `421495436394627433`；修复后个人完成度只保留真实退款约 `3400`，不再把该调课调班负流水计入班课退费。
- 验证 SQL 输出到 runtime：
  - `runtime/tmp/validate_qingcheng_personal_completion_order_change_20260627.sql`，query id `1434324030`。
  - `runtime/tmp/validate_qingcheng_team_month_order_change_20260627.sql`，query id `1434328550`。
  - `runtime/tmp/validate_qingcheng_team_period_order_change_20260627.sql`，query id `1434332703`。
## 2026-06-28 青橙完成度三份 SQL 与经验沉淀同步

- 用 runtime 最终验证版覆盖三份 canonical raw SQL：
  - `resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`
  - `resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql`
  - `resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql`
- 同步落地 2026-06-28 最终修复点：
  - 新增 `order_attr`，优先使用 `original_order_pay_success_timestamp / pay_success_timestamp / trade_timestamp` 生成 `original_paid_time`，完成度按原始成交窗口归属组织。
  - 新增 `team_hist` 期次兜底，解决组织链 `begin_time` 滞后导致当前有效订单被误删。
  - `gmv_z` 从 `trade_type = '正常订单'` 调整为 `coalesce(trade_type, '') <> '调课调班'`，避免误排除应保留的正常绩效订单。
  - `is_internal_order_change` 从“命中变更链路就剔除”修正为“只剔除调课调班流水本身”；命中变更链路但本身是正常成交的订单不再排除。
  - 团队架构回连统一改为 `qtg.qici = wa.qici`，不再固定取 `max(qici)`。
  - 业务确认：`H业务线` 按 100% 计入，所有 `非H业务线` 统一按 50% 折算；SQL 输出保留非 H 原始净收，前端公式再乘 0.5。
- 新增经验清单文档：`knowledge/sql_patterns/qingcheng_completion_sql_repair_checklist.md`。
- 更新完成度相关 dashboard、metrics、risk、quick_reference、decision_tree 文档，沉淀以下高频误区：
  - 不要只看 `trade_time` 或只看 `paid_time` 判定组织归属；
  - 不要把 service 订单明细当完成度金额唯一事实源；
  - 不要把命中 `dim_finance_order_change_df` 的所有订单都当内部流水；
  - 不要在团队完成度中继续固定取 `temp_table.dingxi01_qing_team_jg.max(qici)`；
  - 不要再写“仅小初 50% 折算”或“非 H 是否全部 50% 待确认”。

## 2026-07-03 青橙完成度 service transfer 补充识别修复

- 同步修复个人完成度、团队完成度期次、团队完成度月度三份 canonical raw SQL：
  - `resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`
  - `resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql`
  - `resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql`
- 修复原因：20260703 期顾问 `李兵建` 看板展示班课营收 / 折算后产出约 `2012.34`，但订单明细全为 `trade_type='调课调班'` 的调入流水。两笔订单在 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 已有 `transfer_in_amount`，但未命中 `finance_dw.dim_finance_order_change_df`，旧 SQL 只依赖财务订单变更维表和 `trade_type` 聚合路径，导致该类 service transfer 漏链路被当作正向出单。
- 修复方式：在三份 SQL 的 `order_attr` 汇总 `service_transfer_in_amount_yuan / service_transfer_out_amount_yuan`，一路传递到 `rd`、`t4`，并在 `is_internal_order_change` 中补充 `rd.trade_type='调课调班' and (service_transfer_in_amount_yuan > 0 or service_transfer_out_amount_yuan > 0)` 的兜底识别。保留原有 `dim_finance_order_change_df` 识别逻辑；正常订单命中变更链路但自身不是调课调班流水时仍不剔除。
- 验证结果：
  - 个人完成度验证 `query id 1445444633`：李兵建 20260703 期 `class_income=0`、`discounted_output=0`、`income=0`。
  - 团队完成度期次验证 `query id 1445448835`：李兵建小组 20260703 期 `class_income=16200`、`discounted_output=12569`，已剔除误入的 2012.34，其他顾问正常保留。
  - 团队完成度月度验证 `query id 1445453872`：李兵建小组 202607 月结果可执行并输出月度聚合。
  - 正常订单保护验证 `query id 1445458630 / 1445463148 / 1445467414`：三份 SQL 均未把正常订单误判为内部调课调班，错误标记金额均为 `0`。
- 同步更新 dashboard、metrics、表说明、join 文档、quick reference、decision tree、完成度修复 checklist 和个人完成度风险文档。后续排查个人/团队完成度异常时，必须同时检查 `dim_finance_order_change_df` 和 service 明细的 `transfer_in_amount / transfer_out_amount`。

## 2026-07-09 青橙转化数据看板暑期期次热修

- 将 runtime 热修版 SQL `runtime/qingcheng_qici_20260716_patch_20260709/data_center_qingcheng_2460_20260709_qici0716_hotfix.sql` 同步为当前 canonical raw SQL：`resources/raw_sql/data_center_qingcheng_2460_20260709.sql`。
- 修正原因：2026 年 7 月后青橙暑期业务排期不再稳定等同自然周周五；`2026-07-14` 至 `2026-07-18` 这 5 天实际业务期次应为 `20260716期`，旧固定周五逻辑会显示为 `20260717期`。
- 修正范围：订单侧结果期次 `dd.base.qici` 增加日期范围优先分支；线索侧 `bb.qici` 增加同一范围分支；当结果期次为 `20260716期` 且 `rule_name` 提取短期次为 `0717期` 时，将 `qici0` 归一为 `0716期`，避免 `is_on_period` 和当期指标误归为往期。
- 同步更新 `data_center_qingcheng_datasets.md`、转化 raw 文档、转化指标文档、前端指标联动、业务档案、表说明、quick reference、decision tree，并新增 `knowledge/sql_patterns/qingcheng_summer_qici_corrections.md`，作为后续其他暑期期次继续校正的入口。

## 2026-07-09 青橙 TMK 潜客转正常线索链路探查

- 新增表文档 `knowledge/tables/bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf.md`，记录“潜客转线索指标统计表”的用途、分区、核心字段、TMK/规划系统意向过滤和与 `data_lake_fuwu.dwd_crm_leads_rt` 的关联边界。
- 更新 `knowledge/01_table_index.md`、`knowledge/tables/data_lake_fuwu.dwd_crm_leads_rt.md`、`knowledge/tables/service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`，沉淀以下链路：
  - 潜客阶段：`bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf.lead_id = data_lake_fuwu.dwd_crm_leads_rt.crm_leads_id`，且 app 表 `lead_model_type=1`；
  - 转移阶段：正常线索 `data_lake_fuwu.dwd_crm_leads_rt.previous_model_id = 潜客 crm_leads_id`，且正常线索 `model_type=0`；
  - 成交阶段：用转移后的正常线索 ID 关联 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.lead_id`，金额字段按分转元。
- live 验证记录：
  - `desc bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf`，query id `1456918587`；
  - `desc service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`，query id `1456920675`；
  - service 业财字段样本验证，query id `1456926952`；
  - `dwd_crm_leads_rt` 自关联 TMK/规划系统潜客转正常线索验证，query id `1456961079`；
  - 最终明细导出 SQL，query id `1457006107`。
- 关键限制：当前最新小时快照里，严格按青橙截面范围只能补到极少数历史转移后的承接顾问；`service_dw.dm_crm_lead_stats_detail_hf` 同样只能补到 1 条。后续如业务必须全量补齐“线索承接顾问”，需要继续寻找 CRM 当前 owner / 转移记录明细表，不能从本轮已验证的三张表中强推。

## 2026-07-10 青橙 2064 抖音复用两级渠道契约对齐

- 修正 `resources/raw_sql/data_center_qingcheng_2064_20260625.sql`：`channel_map_2` 新增高优先级 `%抖音正价退费% -> 抖音复用`，与既有 `channel_map_1` 对齐，避免最终 `channel_map_2 is not null` 门禁过滤该渠道。
- `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md` 升级为 2064 权威渠道契约，明确两级渠道成对维护、优先级、适用域和 Text2SQL 契约 ID。
- 新增青橙过程一级、二级渠道派生维度契约；两者均从 `rule_name` 确定性编译，且仅允许在青橙基础表和已确认指标兼容范围内使用。
- 新增契约/权威 SQL 对齐回归测试，防止后续只修改一级或二级渠道。

## 2026-07-11 Text2SQL P3A/P3B 青橙看板设计路由

- 新增 `knowledge/sql_patterns/dashboard_design_change_workflow.md`，明确青橙正向 `QuerySpec -> QueryPlan -> DashboardDatasetSpec -> DashboardDesignSpec -> DashboardChangePlan` 链路，以及从 live profile 反查 component/model/field/formula、青橙 contract、`source_path` 和 retained SQL 的反向链路。
- P3A 对 component、layout、formula、filter 开放画像、设计、结构化 diff 和 dry-run；所有业务字段和公式依赖必须引用 `qingcheng:*` 的 `confirmed` contract ID 与本域 `source_path`，不借用市场顾问同名口径。
- P3B 当前只允许 stable-ID `update_filter_dynamic_default`：必须同时定位 `relation_id + filter_id + field_id`。组件字段、布局、公式、数据集重绑、新建和删除均标为 `blocked_unsupported`；计划含任一 blocked operation 时整次 Apply 零写入。
- `apply-dashboard-change` 仅写 draft，`publish-dashboard-change --confirm-publish` 独立执行并校验成功 ApplyReceipt 与最新 profile hash。本 Skill 不保存登录态、不掌握写接口，也不把任何设计工件当授权。
- 同步 `agents/openai.yaml` 的描述和默认提示，使 Skill 入口能发现青橙域内 DashboardDesignSpec/ChangePlan 能力，同时保留 operator 写入门禁。
- 仅更新 Skill 路由、速查、决策树与工作流说明；未删除、覆盖或修改既有青橙指标、维度、范围、Join 契约及业务知识文档。

## 2026-07-11 10:01:17

- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 扫描 `青橙项目部` 文件夹，并将原始 `profile.json` 写入本地 runtime 目录。
- 刷新 `knowledge/dashboard_web_profiles/README.md`，当前索引 10 个看板快照。
- 本次 profile 结果：成功 10 个，失败 0 个。

## 2026-07-11 P3 看板探测器全量回归与编辑器知识刷新

- 只读刷新青橙项目部与青橙播报共 26 个当前 Web BI 结构快照。
- 刷新 26 个编辑页组件/字段快照：active=21，paused=5，incomplete=0。
- 两个已从当前青橙播报菜单移除的旧看板快照继续保留为 historical，但通过 registry_status 标记排除出 P3 当前设计/变更路由。
- 本次仅更新 dashboard_web_profiles、索引与生成清单；未修改青橙指标、渠道/期次范围、Join、语义契约或 2064 权威 SQL。

## 2026-07-11 青橙 TMK 潜客过程数据链路验证

- 只读验证 `dwd_crm_leads_rt` 潜客转正常线索、潜客宽表过程字段、青橙承接顾问、临时架构和外呼明细的覆盖率；核心 query id：`1459464455`、`1459472798`、`1459484750`。
- 132 条转移线索中，潜客宽表命中 102 个潜客 ID、100 条过程字段完整；转移后正常线索在青橙承接顾问范围仅命中 1 条，因此承接顾问不能作为 TMK 过程数据的主人员维度。
- 临时架构按 `qici + employee_email_name` 仅命中 8 条；补充登记潜客宽表虚拟三级/四级部门、大组长和直属小组长字段，允许过程数据在保留原始组织名称的前提下作架构兜底。
- 外呼明细按 `user_id + prelead_id + employee_email_prefix` 精确关联，当前样本的外呼次数、接通次数和总通时与潜客宽表汇总一致；8min 人数继续使用单次 `call_duration > 480`，不使用累计通时近似。
- 完整候选 SQL 仅输出到 runtime，未写入数据中心、未保存或发布任何看板。

## 2026-07-11 canonical 知识唯一版本清理

- 删除 `data_center_qingcheng_2064_20260624.sql`，仅保留已补齐“抖音正价退费→抖音复用”一级、二级渠道映射的 `2064_20260625` canonical 版本。
- 删除 `data_center_qingcheng_2460_20260626.sql`，仅保留已包含 `20260716期` 暑期业务日历修正的 `2460_20260709` canonical 版本。
- 保留线索分配顾问与业绩归属顾问两个不同角色契约；裸称“顾问”继续阻断并要求消歧，不把角色差异误判为历史字段。
- 新增仓库级唯一版本审计，阻断重复 canonical 文件、相同内容副本、重复契约 ID 和同类同表同字段的重复所有权。

## 2026-07-11 数据中心 stable canonical 原子同步

- 将 2064、2460、2740 三个青橙数据中心 SQL 一次性迁移为 `data_center_qingcheng_<model_id>.sql` 稳定路径；版本日期不再进入文件名。
- 新增 `semantic/current_model_bindings.json`，分别绑定青橙过程、转化、抖私转化三个 current model 和域内看板证据；市场顾问模型不得进入该 registry。
- 数据中心更新改为 `dry-run plan -> exact plan hash -> atomic apply -> mandatory validation`；跨 model 替代必须同计划更新语义槽位并显式退役旧模型，任一维护门禁失败自动恢复写前快照。
## 2026-07-13 青橙 TMK 私海分配历史表探查与契约登记

- 新增 `service_dw.dwd_crm_assign_private_detail_hf` 青橙表文档，明确当前小时快照内 `private_sea_id` 为物理记录键、`lead_id` 为一对多历史关联键。
- 全量有界探查 H 业务线允许学部 2026-07-01 以来 509829 行：`private_sea_id` 无重复，29208 个线索存在多个私海记录，28798 个线索对应多个顾问。
- 固化首次承接、当前私海候选和完整转手链路的确定性排序；当前顾问继续以 `dm_crm_lead_stats_detail_hf.section_assign_employee_email_name` 为准。
- 当前 144 条 TMK/规划系统转移线索中，私海历史命中 123 条、截面顾问命中 115 条，双方同命中的 115 条全部一致；3 条发生顾问转手，21 条只能解释为 H 范围内未命中。
- live query id：`1466169274`、`1466174917`、`1466178403`、`1466187134`。

## 2026-07-13 数据地图字段补充

- 使用数据地图 `tableV2/searchTableList`、`normalColumns`、`partitionColumns` 和 `getDdl` 接口刷新物理表字段信息。
- 覆盖 `knowledge/tables` 中 1 张物理表文档；追加 42 个数据地图字段，回填类型 0 处、字段说明 0 处。
- 复扫结果为字段缺口 0、类型占位 0、说明占位 0。
- 本次维护严格限定在 `qingcheng-dashboard-sql` 内，未同步到市场顾问 Skill；未覆盖 `temp_table.*` 临时表文档；临时表字段仍以本地 Excel、SQL 使用场景和人工维护规则为准。
