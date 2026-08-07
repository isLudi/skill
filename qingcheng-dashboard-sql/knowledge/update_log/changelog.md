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

- 从 `market-consultant-dashboard-sql` 复用并清洗 5 张公共物理表文档：`finance_dw.dim_finance_employee_df`、`gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`、`service_dw.app_user_attribute_label_gaia_wide_df`、`service_dw.dim_crm_assign_rule_lead_detail_hf`、`service_dw.dim_crm_assign_rule_plan_item_info_hf`。
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

## 2026-07-15 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2460`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-15 青橙转化数据看板暑期期次 20260724 修正

- 更新 `resources/raw_sql/data_center_qingcheng_2460.sql`，新增 `biz_qici_calendar` 覆盖 `20260716期` 至 `20260821期`，将 `2026-07-21` 至 `2026-07-27` 的历史固定周五结果 `20260724期` 归一为业务期次 `20260722期`。
- 同步修正订单侧 `trade_timestamp`、线索侧 `group_period_year + group_period_term`、当期短期次 `qici0`，并修复 `lead_map` / `bb` 中 `select *` 引发的字段二义性风险。
- 线上 SQL 验证 query id：`1474435390`；聚合结果仅出现 `20260716期=224`、`20260722期=42`，未出现 `20260724期`。

## 2026-07-15 青橙过程数据 SEC 未加好友双重限域

- 更新生产数据中心 `青橙-过程数据`（model `2064`）：`规划系统高一/高二/高三` 潜客进入 `tmk_prelead_raw` 前必须来自 `学习顾问部 / SEC创新部`，最终输出仍需同一期次顾问命中 `dept_2='SEC'`。
- `tmk_output_transfer_ids` 同步使用相同来源门禁，避免其他部门潜客错误排除转化后的正常线索；其他青橙 TMK 意向保持原逻辑。
- 候选 SQL 完整预览 query id `1475692517`；历史回归 query id `1475707964`：20260710 期保留 10,142 条，历史 144,330 条来源均为 `学习顾问部 / SEC创新部`；当日来源核验 query id `1475714339`：968 条均为 `私域运营部 / 筛优组`，严格 SEC 来源为 0。
- 生产替换计划哈希 `22e0f49ec9356ebf05bfbd2ca02d37a6dae7568e0b828a4b3a29bce395fbbdff`；保存后 SQL 哈希 `50d965ebc77f53d184f45f806e2e493fb286bba5ea7f96517925ebc764d81efc`；新抽数记录 `159071145` 于 2026-07-15 22:49:30 达到 `SUCCESS`。
- `过程数据报表-青橙` 只读值健康检查：7 个分析组件全部 data-ready，错误数 0；未修改看板配置或发布状态。

## 2026-07-16 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2064`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-16 青橙过程数据 14 天指标上线

- 更新生产数据中心 `青橙-过程数据`（model `2064`），新增 6 个可加总字段：`first_call_cnt_14d`、`first_call_connected_cnt_14d`、`v_lead_14d_denominator`、`is_long_call_14d`、`call_duration_14d`、`zong_call_ci_14d`，由看板组合得到 7 个 14 天指标；SQL 未直接输出任何比率型指标。
- 14 天窗口统一为线索分配后 `0-336` 小时。14 天外呼明细按 `user_number + lead_id + section_assign_employee_email_prefix` 精确关联，避免同一用户、同一顾问下多条线索串数；`call_duration_14d` 已换算为分钟。
- 全量候选 SQL query id `1477043537`；渠道级校验 query id `1477067724`，所有期次/渠道 `invalid_flag=0`，分子未超过分母且新增累计值无负数。
- 生产替换计划哈希 `e286c0cbaa70d4c4cf2a20966e23660e92164f5f14733ab5cac55a97d38704de`；生产 Preview task id `1477125780`，输出 35 列；保存后 SQL 哈希 `4d75c1219cdc550485203a854328f3687e5cac43ce1ba3845cf7c4640eb38f8d`。
- 新抽数记录 `159190210` 于 2026-07-16 15:45:55 达到 `SUCCESS`；随后按本地同步计划哈希 `8330671f2af20d3073fc1e5f5471b9733b32cb2a5fbb1e3cc22602146871bd36` 反向同步 stable canonical raw SQL。
- Data Center 新增字段触发连续两层保存确认；修复 `usql-web-query-operator` 的确认按钮识别和连续弹窗处理，并通过替换/创建回归测试 27/27。
- `过程数据报表-青橙` 刷新后只读值健康检查：7 个分析组件全部 data-ready，错误数 0；本次未修改看板公式、组件或发布状态。

## 2026-07-17 青橙行课报表暑期期次映射上线

- 更新生产数据中心 `青橙到课`（model `2244`），服务看板 `青橙项目部_行课报表`（`dashboard_3765824192103694336`）。
- 新增 `biz_qici_calendar`，按业务确认区间维护 `20260716期`、`20260722期`、`20260728期`、`20260803期`、`20260809期`：`2026-07-14~2026-07-19`、`2026-07-20~2026-07-25`、`2026-07-26~2026-07-31`、`2026-08-01~2026-08-06`、`2026-08-07~2026-08-12`。
- 线索侧以 `group_period_year + group_period_term` 解析日期后范围 join 业务日历；行课侧以 `begin_time` 日期范围 join 同一业务日历；未命中时回退历史周五期次逻辑。
- 生产替换计划哈希 `e44e618081750be9b30f15a8fdf74d6ba8540dd6aaef812e949e8360b9c79191`；Preview task id `1479043748` 输出 23 列；保存后 SQL 哈希 `dcbd66c000d3c6f0f1ccecd81c9c6271a3a5912d1434fa1d828904f5b7538561`。
- 新抽数记录 `159369980` 于 `2026-07-17 14:58:55` 开始、`14:59:04` 结束，状态 `SUCCESS`。

## 2026-07-17 青橙 TMK 转移链路小时产出观测台账

- 新增 `knowledge/sql_patterns/qingcheng_tmk_transfer_latency_observation_log.md`，以 2026-07-17 约 15:32 的 `20260716期` SEC 后转操作为基线，记录 DWD 模型关系、私海首次承接、潜客小时宽表、当前截面和业财归因的分阶段到数情况。
- 截至 `dt=20260717/hour=18`，固定集合为 17 条唯一转移线索、15 个唯一用户；私海首次承接 17/17，其中叶柱 9 条、王晓楠04 8 条；潜客小时宽表仅回补 2/17，当前截面和业财均为 0/17。
- 明确区分“物理分区存在”“目标线索进入”“目标字段可回补”，并把当前约 3 小时、5 小时等时间只登记为单批次观测上界，不作为正式 SLA。
- 固化查询顺序为 `dwd_crm_leads_rt 潜客 -> 同表 previous_model_id 正常线索 -> 私海首次承接 -> 左连接潜客小时宽表 -> 左连接当前截面和业财`；禁止先从潜客小时宽表构造转移集合。
- 记录 query id `1479804384`、`1479815909`、`1479821287` 及对应 runtime 结果路径，并提供今晚和次日持续追加的统一观测模板。

## 2026-07-17 青橙 TMK 转移链路二次复跑

- 追加更新 `knowledge/sql_patterns/qingcheng_tmk_transfer_latency_observation_log.md`，比较 `dt=20260717/hour=18-21` 并用最新 `hour=21` 复跑17条固定转移线索。
- DWD 与私海继续稳定为 17/17；潜客小时宽表分区由 15,610 增至 15,613，但目标仍为 2/17；青橙业财分区由 81,092 行/14,112 个线索增至 81,204 行/14,143 个线索，目标仍为 0/17。
- `hour=21` 潜客规则核验仍只有杨亮，陈瑶11、行嵩丽和任意 `0716期-青橙SEC-SEC后转` 规则均为 0；当前截面目标也仍为 0/17。
- 将成交状态改成三态：业财无目标行时输出 `业财未回补`，不再将空值兜底为“否”；明确业财目标为 0 只有在业务确认已有订单后才能判定为归因延迟。
- 成功 query id：`1480173653`、`1480180574`、`1480189271`；SQL 和结果制品均保存在 runtime，未修改数据中心或看板。

## 2026-07-18 青橙 TMK 转移链路跨日三次复跑

- 追加更新 `knowledge/sql_patterns/qingcheng_tmk_transfer_latency_observation_log.md`，比较 `20260717/hour=21` 与 `20260718/hour=04/06/08` 的固定17条目标覆盖。
- 潜客小时宽表由2/17补齐至17/17：陈瑶11 8条、行嵩丽7条、杨亮2条，17条均回补 `20260716期`、年级、有效线索标记和渠道；首次完整快照不晚于 `20260718/hour=04`。
- 17条目标渠道均仍为 `0716期-青橙公海-SEC未加好友-高二/高三`，任意 `SEC后转` 规则命中仍为0；转移漏斗继续以 DWD `previous_model_id` 和私海分配事实为准。
- 当前截面和青橙业财目标仍为0/17。业财分区相对 `hour=21` 增加56行、13个线索ID，不能把目标空结果直接解释为未成交或整表停更。
- 成功 query id：`1480815292`、`1480820219`、`1480822900`；SQL和结果制品均保存在 runtime，未修改数据中心或看板。

## 2026-07-18 13:21:42 runtime 首批可复用查询模板入库

- 新增 Q1 青橙退费原因分析模板，归档结果期次口径 SQL，补充 `finance_dw.dwd_finance_order_refund_df` 最小表文档、订单—原因分摊链路、字段口径和守恒校验；原因权重、退款类型、渠道 CASE、500 元人头阈值及结果期次架构继续保持待确认门禁。
- 新增 Q2 青橙 TMK 转移、承接与订单追踪模板，复用 `transferred_lead_to_prelead` 和 `transferred_lead_to_private_assignment_history` 两个已确认 Join；明确订单必须关联转移后的正常 lead_id。
- Q2 可复用 SQL 将成交状态改为“是/否/业财未回补”三态，业财未回补时金额保持空值，避免把下游尚未产出误解释为未成交或 0 元。
- 两个模板均只写入青橙 Skill；未借用市场顾问退费/渠道语义，未修改数据中心、看板或任何线上状态。

## 2026-07-18 runtime 第二批可复用查询模板入库

- 新增 Q3 青橙期次×渠道过程数据导出模板，直接引用 current model `2064` canonical SQL 和既有过程指标，不重复归档 runtime 921 行全量 SQL。
- 固化期次、渠道一/二级、规则、分配日和组织范围参数；历史 `20260710期 / SEC招生退费` 仅作为调用示例。
- 明确导出层保留可加总分子、分母和累计值，部门、年级、主管透视均在聚合后重算好友率、APP率、首呼/沟通、8min、外呼时长/频次和 14 天指标。
- 本次只写青橙知识路由与调用模板，未修改数据中心、看板或线上状态。

## 2026-07-18 青橙 TMK 转移链路四次复跑

- 追加更新 `knowledge/sql_patterns/qingcheng_tmk_transfer_latency_observation_log.md`，比较 `dt=20260718/hour=08/10/12` 的固定17条目标覆盖。
- 潜客小时宽表继续稳定为17/17，`hour=12` 明细仍为陈瑶11 8条、行嵩丽7条、杨亮2条；期次、年级、渠道和有效线索均完整。
- 当前截面继续0/17；青橙业财分区增加49行和15个线索ID，但目标仍为0/17，证明业财表在更新但无法确认本批是否已有订单。
- 任意 `SEC后转` 规则仍为0；规则清单与 `hour=08` 一致，转移漏斗继续使用 DWD `previous_model_id` 和私海分配事实。
- 成功 query id：`1481295796`、`1481303285`、`1481308921`；SQL和结果制品保存在runtime，未修改数据中心或看板。

## 2026-07-18 青橙完成度班课退费字段上线

- 更新生产数据中心 `青橙个人转化`（model `2769`）、`团队完成度【期】`（model `2680`）、`团队完成度【月】`（model `2677`），新增输出字段 `class_refund_4`。
- `class_refund_4` 口径为班课行课阈值退费：`H业务线 + 一对一学部` 计 0，其余课程取 `refund_4`；用于替代前端历史公式 `sum(refund)-sum(Y_refund_4)`。
- 三份数据集生产替换均完成预览、保存、SQL hash 回读和新抽数 SUCCESS：`青橙个人转化` 预览 task `1482775746`、抽数记录 `159598857`；`团队完成度【期】` 预览 task `1482780777`、抽数记录 `159598870`；`团队完成度【月】` 预览 task `1482784354`、抽数记录 `159598874`。
- 需将个人/团队完成度看板透视表中的 `班课退费` 自定义公式改为 `sum(class_refund_4)`；依赖 `班课退费` 的 `班课净收` 等派生字段保持依赖链即可。

## 2026-07-18 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2677, 2680`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-20 青橙 TMK 转移链路五次复跑与新 Case 探查

- 追加更新 `knowledge/sql_patterns/qingcheng_tmk_transfer_latency_observation_log.md`；潜客、私海、截面使用 `20260720/hour=12`，按业务确认将未更新的业财 `hour=12` 降级为 `hour=11`。
- 固定17条继续保持 DWD、潜客宽表和私海 `17/17`，当前截面和业财仍为 `0/17`；潜客宽表最新分配时间达到 `2026-07-20 12:46:34`，业财 `hour=11` 最新交易时间达到 `2026-07-20 11:45:48`，排除两表整表停更。
- 四个新流转 Case 在工作量表完整手机号/后四位及青橙通话明细手机号 MD5 均未命中，无法建立 `手机号 -> 用户ID -> 潜客/转移线索ID` 稳定映射；私海中王晓楠04、叶柱的最新分配时间仍停在 7 月18日，当前截面也无目标记录。
- 记录一个 3698 元金额候选误匹配反例：其 TMK顾问、私海顾问均与业务 Case2 不一致，且业财 `lead_id` 在 DWD 中为潜客、同用户正常线索 `previous_model_id` 全为0；明确禁止用顾问+金额+年级+科目或用户级任意线索强行补链。
- 成功 query id：`1486838605`、`1486844491`、`1486848897`、`1486860065`、`1486866538`、`1486902160`；本次只更新青橙知识与 runtime 探查 SQL，未修改数据中心或看板线上状态。

## 2026-07-20 P4B 九类窄写能力青橙沙箱验证

- 在 `P4C看板构建沙箱` 的 `dashboard_3994584279860838400` 完成字段显示名、局部筛选标签、组件标题、公共筛选标题、Tab 标签、布局、既有公式表达式、公共筛选动态默认项和根背景色九类适配器的逐项写入/回读/恢复验证。
- 完成九操作连续正向 Apply 与逆序补偿恢复；最终完整 Profile Hash 精确回到基线 `64856e0fdd685f9c8ffe1027c5fc8985dd2d87c3e82fa97e063a9d0d046f750e`，verification SHA-256 为 `ccc9bbccc7d6cad3d26ecfae93c1691ddc19256d2a274fcb8db68d26b3762231`。
- 本次只修改并恢复沙箱草稿，未调用发布接口；泛化组件筛选、字段增删/绑定、Tab 成员、数据集重绑、新建和删除仍保持阻断。

## 2026-07-20 Skill 只读与知识维护边界收敛

- 青橙 Web BI 批量画像默认改为 runtime-only；只有 `profile-all --write-knowledge --confirm-skill-maintenance` 才可写固定的青橙知识目标，任一画像失败时整批不写。
- 青橙物理 schema 权威统一为 `usql-web-query-operator sync-datamap-fields --target-skill qingcheng`；PDF、截图、OCR 和旧版文档提取资源不再作为字段目录写入入口。
- 移除完整性检查对旧版 PDF/图片/渲染目录的强制要求，并刷新反向索引、域清单和共享 physical catalog；未修改任何远端数据集或看板。

## 2026-07-21 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2460`；每个 model_id 只保留稳定 canonical 路径。
- 仅校准 `转化数据` 的暑期 `biz_qici_calendar`：`0710=07-07~07-13`、`0716=07-14~07-19`、`0722=07-20~07-25`、`0728=07-26~07-31`、`0803=08-01~08-06`、`0809=08-07~08-12`；未修改快照、内部转单、渠道映射或指标公式。
- 生产保存后 SQL SHA-256 为 `59f336d5f0150cde29f6c5c9e60d6e3bb2f382820e6b9dc75cc1ed09aadcc76f`，立即抽数记录 `160164065` 为 `SUCCESS`。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-26 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2460`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-26 青橙转化课程转移保护期归因上线

- 在已包含抖音正价退费潜客渠道归因修复的 `转化数据` / model `2460` 最新线上哈希 `00102e94bcd28e6163fa96294850afb2739c85f624d55325322cb1a3afdfd8a6` 上追加课程转移补数，未覆盖并发渠道修复。
- 从 `2026-07-20`（`20260722期`）起，仅补回 `order_change_type = 1` 最新子订单、青橙财务正向支付，且 B 用户在交易时点处于同一青橙顾问私海保护期的记录；更早期次不回刷。
- 原 `dd -> service_gmv` 内部转单剔除逻辑保持不变；补数单独生成 `course_transfer_gmv` 后再 union。移除新增段并还原 CTE 名称后的 SQL SHA-256 与上线前基线完全一致。
- 目标验证为 2 个子订单、合计 4000 元；目标用户聚合增加支付用户 1、当期支付用户 1、科目 1、当期科目 1、营收/净营收/当期营收各 4000、破蛋 1、成单周期 2 天。
- 43 个期次渠道桶回归中，除 `20260722期 / 私域 / 私域表单` 外，线索、成单、科次、营收、退款、净营收、当期营收、退款人数和破蛋人数均无差异；记录原 `prc` 并列排序导致 `sc` 重跑非确定性的既有风险。
- 生产替换计划 `b61ce4b4cca61179deac019f795858b05a8a563faaa5d455f28f271981027258`；保存后 SQL SHA-256 `8416e707d618bc5b959936035edac3d10809215e8adc2d7822c7b0f2580288a7`；Preview task `1500672337`；新抽数记录 `161027733` 为 `SUCCESS`。
- 新增 `knowledge/sql_patterns/qingcheng_protected_course_transfer_conversion.md`，沉淀证据链、隔离追加结构、并发哈希门禁和回归验证规则。

## 2026-07-28 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2064`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-28 过程数据 IP 退费渠道上线

- 在 `青橙-过程数据` / model `2064` 的普通线索渠道 CASE 中新增 `IP退费`：规则名去除普通空格后匹配 `%青橙IP-招生退费-春春%`、`%青橙IP-招生退费-朱博士%`、`%青橙IP-招生退费-郭艺%`，一级输出 `IP退费`，二级分别输出 `春春`、`朱博士`、`郭艺`；期次前缀未写死。
- 精确分支位于宽泛 `%青橙IP%` 与 `%招生退费%` 之前，且限定 `record_source='normal_lead'`；TMK 潜客映射和转化模型 `2460` 均未修改。
- 实际回归中 5 个目标规则、770 条有效线索发生预期改名；其余 24 个青橙 IP 历史规则、5,482 条有效线索保持原一级、二级渠道。
- 生产替换计划 `b1879dc8914389c224e547ab914266f1cfe4bf89861f09dc835ff51d3b2202d9`；保存后 SQL SHA-256 `a5e32e446328ca48201a314a28394dae2dbb5bf0f264071699795fe6072b500d`；Preview task `1505545924`；新抽数记录 `161440948` 为 `SUCCESS`。

## 2026-07-29 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2460, 2740`；每个 model_id 只保留稳定 canonical 路径。
- `2460` 的 `lead_map` 与 `normal_bb` 四处一级/二级渠道 CASE 同步新增 `IP退费 / 春春、朱博士、郭艺` 精确分支，并置于 `%青橙IP%`、`%招生退费%` 之前；785 条有效线索发生预期改名，验证时无目标规则订单金额变化。
- `2740` 改为复用 `2460` 的 `service_gmv + course_transfer_gmv` 标准订单集：内部转移金额先归零，再补交易时处于同一青橙顾问保护期的 B 用户课程转移；团队架构 Join 改为 `employee_email_name + qici`，仅额外计算 7/14/30 天等时间分层。
- 46 个期次渠道组合的净营收、退款与标准订单集逐项一致，最大差额均为 `0.00`；2740 净营收桶和退款桶闭合差均为 `0.00`。
- `2460` 保存后 SHA-256 `9cbdc5535317ec07473ef9469555dbd3ce9f1b6390ea8a3a181646e6ad4bdf5a`，Preview task `1507317427`，新抽数 `161603508` 为 `SUCCESS`。
- `2740` 保存后 SHA-256 `d85b1f745c20935a9a29046655a05b48174b9a351bda93af4b0c5b3995f225c0`，Preview task `1507319914`，新抽数 `161603511` 为 `SUCCESS`。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-08-02 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2244, 2460, 2677, 2680, 2740, 2769, 3180`；每个 model_id 只保留稳定 canonical 路径。
- 按业务最终命名将 `2026-08-07~2026-08-12` 窗口从 `20260809期` 更名为 `20260808期`，带短期次映射的 SQL 同步将 `0809期` 更名为 `0808期`；日期范围、历史期次、渠道 CASE、订单归因和指标公式均未修改。
- 生产数据集 `青橙到课`、`转化数据`、`团队完成度【月】`、`团队完成度【期】`、`抖私-转化`、`青橙个人转化`、`TMK线索转移明细` 均完成 Preview、保存后 Hash 回读和新抽数 `SUCCESS`。
- 各模型的 `Preview task / 新抽数记录` 为：`2244=1518968099/162359115`、`2460=1518972594/162359118`、`2677=1518976965/162359122`、`2680=1518981190/162359124`、`2740=1518985194/162359125`、`2769=1518989022/162359128`、`3180=1519004523/162359137`。
- 保存后 SQL SHA-256 为：`2244=a921174d62701c9df0ff723eecdd8cf65e4fc3233d8029a0109d3b001cca5af2`、`2460=3a451998811769b79dbc110482ab08afd03d01cd0dadcb86de414e5fd9647186`、`2677=10f2e804dbc1bbb7794d20137adcc7b53b75fb1d2f533cd7261ab41d7eb7503a`、`2680=f98d393cefa70a5df04a53386c840b99a23943723c4b2040b222f43bec22fcd3`、`2740=cdf02c3cef6af336b737b0e4e7f8289567abe37a6dcd49949a0f2f3fc0c9a277`、`2769=1f89b179752cf6aafe5c8007f2c1c024956e8f0be76ca0e0d4ddf9796b755fd2`、`3180=7eec4d57ae288468b1040e9a4f16568133c3b532c86315223472cf009f1402eb`。
- 全目录回读确认 7 个受影响模型的旧完整/短期次标签计数均为 0；未含映射的 `2064`、`2576`、`2834`、`3131` Hash 与修改前一致，未执行无内容刷新。
- 本地 canonical 同步计划 SHA-256 为 `496c717954f72fc1a4e9146b64dd9a6fb772526447665f388dc8e36e3ccd0121`；新增 model `3180` 后 Qingcheng raw SQL 基线由 17 份调整为 18 份。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-08-03 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`3180`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-08-03 TMK 线索转移明细新增小组字段

- 在 `TMK线索转移明细` / model `3180` 新增 `xiaozu`，取值为 `finance_dw.dim_finance_employee_df.leader_employee_email_name`，表示 `tmk_consultant_name` 的直属上级带数字员工名。
- 员工维表使用 T-1 `dt`、`first_level_department_name='H业务线'` 和 `is_main_job=1`，按 `email_prefix` 去重后通过 `tmk_consultant_email_prefix` left join；不使用姓名作生产 Join key，不过滤架构未匹配线索。
- 覆盖探查 query `1522332746`：69 名当前 TMK 顾问按邮箱前缀和姓名都 69/69 匹配，直属上级 69/69 非空，邮箱前缀重复数为 0。
- 回归 query `1522351329` / `1522366854`：新旧均为 2,146 行和 2,146 个唯一转移线索，匹配订单 113，营收 210,395.00，退费 27,585.96，净收 182,809.04；1,832 行 TMK 顾问非空且 `xiaozu` 全部非空，剩余 314 行原始 TMK 顾问本身为空。
- 生产替换计划 `891a8438af4ff97b6065a6480fad8988da9b5811defd54732febafdbec403e9b`；保存后 SQL SHA-256 `4aff14a536c209bbfe485c5ac94734704ee15bc3ae0e7efce6627a126e0fb34c`；Preview task `1522382107` 成功，44 列、100 行；新抽数记录 `162538939` 为 `SUCCESS`，receipt `fully_verified=true`。
- 本地 canonical 同步计划 SHA-256 为 `38d32e9f999cd2a2b8f0648ef3d433b1c86d8fdd7cfbd3c928f3e8e8698111e6`。

## 2026-08-03 TMK 线索转移明细渠道、成交线索与输出精简上线

- `TMK线索转移明细` / model `3180` 新增 `channel_map_1`、`channel_map_2`，复用 current model `2064`“青橙-过程数据”的 TMK 特殊渠道识别与一级渠道归并规则；新增 `deal_lead_count`，在一行一个 `transfer_lead_id` 粒度按 `has_deal=1` 计 1。
- 最终输出移除 15 个不用于看板的诊断/快照字段：`transfer_lead_create_time`、`transfer_lead_period_name`、`lead_snapshot_key`、`app_snapshot_key`、`private_snapshot_key`、`finance_snapshot_key`、`qici_source`、`deal_attribution_type`、`deal_time_relation`、`transfer_deal_status`、`current_private_is_active`、`private_history_count`、`first_receiver_time`、`current_private_assign_time`、`current_private_candidate`；必要内部字段仍保留在 CTE 中参与归因和校验。
- 登记后续看板口径：线索析出率=`sum(deal_lead_count)/sum(lead_count)`，全量单效=`sum(net_amount)/sum(lead_count)`，后转单效=`sum(net_amount)/sum(deal_lead_count)`；分母均使用 `nullif(...,0)`，并要求在最终分组粒度按分子分母重算。
- 生产替换计划 SHA-256 为 `d58c9ecc9e3ed7a03394c1ced2001461d2f865823033fa6ef3ad287ab8e26508`；保存后 SQL SHA-256 为 `b1861eb4d1fa6b6e6d71dfeb8bbc8146f17b05aee9c531822a8d0459b8ca5a4c`；Preview task `1522874258` 成功，32 列、100 行；新抽数记录 `162559838` 为 `SUCCESS`，receipt `fully_verified=true`。
- 本地 canonical 同步计划 SHA-256 为 `d62db5a22a7b57af648a1e6954d1e30e6e4eac56d164723f4eba9a028a3ebae7`；另回读同步 current model `2064` 作为渠道口径基线，其线上渠道 CASE 未发生本次远程修改。

## 2026-08-04 青橙抖音正价复用过程导出契约补齐

- 为“青橙-过程数据”历史过程导出补齐加微、首 call 等待时长、24/48 小时及 7 天首 call、累计首 call、24/48 小时及 7 天沟通、外呼时长/长通话/外呼次数/接通次数、APP 登录等过程指标契约；指标保留可加总分子字段，比例由最终透视粒度的分子/分母重算。
- 登记结果期次、过程规则、分配日、年级、学部、二级部门、小组等导出维度，并补充 `20260728期` 暑期结果期次日历映射；本次只维护青橙本地语义与 runtime 查询文件，未修改线上数据集或看板。
- 依据过程看板校验补入 TMK/潜客路径候选源 `bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf`；固定 `20260804` 快照后 canonical 查询回读 `20260626期=3,685`、`20260728期=2,509` 有效线索，避免只查普通线索路径造成漏数。

## 2026-08-04 15:36:53

- 入库青橙看板 SQL `qingcheng_refund_rate_analysis_20260710_20260728.sql`，生成 `qingcheng_refund_rate_analysis_20260710_20260728` 初始看板知识文档和指标/临时表待确认项。

## 2026-08-04 15:36:53

- 入库青橙看板 SQL `qingcheng_refund_structure_share_analysis_20260710_20260728.sql`，生成 `qingcheng_refund_structure_share_analysis_20260710_20260728` 初始看板知识文档和指标/临时表待确认项。

## 2026-08-04 15:36:53

- 入库青橙看板 SQL `qingcheng_refund_reason_analysis_20260710_20260728.sql`，生成 `qingcheng_refund_reason_analysis_20260710_20260728` 初始看板知识文档和指标/临时表待确认项。

## 2026-08-04 青橙退费分析查询与口径沉淀

- 将 20260710 期至 20260728 期的退费率、退费结构和退费原因查询代码登记到 `resources/raw_sql/`，并保留查询 SHA-256，便于按代码版本复核。
- 新增 `knowledge/dashboards/qingcheng_refund_analysis_20260710_20260728.md`、`knowledge/metrics/qingcheng_refund_analysis_metrics.md` 和 `knowledge/sql_patterns/qingcheng_refund_analysis.md`，沉淀 2460 订单归属、期次日历、退费原因分摊、500 元退费人头阈值、分子/分母及金额守恒规则。
- 退费原因 SQL 显式保留订单号，并将 NULL 渠道、二级渠道和年级归一为“未知”，修复 `refund_head_key` 因 NULL 丢失导致的退费人头不一致；本期快照退费人头与转化看板核对为 337。
- 更新 `01_table_index.md`、`quick_reference.md`、`decision_tree.md`、`joins/common_join_keys.md` 和 `joins/table_relationships.md`，将本期查询和方法文档纳入导航；退款类型、原因金额分摊和 500 元人头阈值已由业务确认。
- 20260804 追加诊断：20260710-20260728 产品 CASE 仅按 `clazz_name` 识别小班/大班，精品班学部的“目标一本班”等非标准班型会落入“其他”；修复前需先确认二级部门到产品的业务映射，不能直接把全部“其他”改成“大班”。

## 2026-08-04 青橙产品退费归类迁移

- 将 `qingcheng_refund_structure_share_analysis_20260710_20260728.sql` 的产品归类迁移为 `course_second_level_department_name` 优先匹配：`精品班学部 -> 大班`、`菁英班学部 -> 小班`、`一对一学部 -> 一对一`、`本地化学部 -> 本地化`、`清北班学部 -> 清北`，其余为 `其他`；结构查询 SQL SHA-256 为 `ACFA35AE0138441B7892E641FFA0DE456CDDA906697E8CE20F7AFA30A21062E1`。
- 通过一次性临时模板 `QingProdRefund0804`（template id `9726`）下载产品粒度结果，查询记录 `385023`、任务 `1525289328`，返回 234 条记录；临时模板已完成下线和删除，未保留线上模板。
- 新规则下产品退费金额合计 `1,347,448.07`：大班 `1,089,504.33 / 80.86%`、一对一 `117,336.50 / 8.71%`、小班 `102,626.24 / 7.62%`、清北 `20,531.70 / 1.52%`、其他 `17,449.30 / 1.30%`。原 20260710-20260728 版本的其他为 `81.61%`，其主要差额被重新识别为大班；剩余其他仍表示未命中上述二级部门规则的产品，不能继续整体并入大班。
- 退费结构透视表的产品占比改为由退费金额分子除以产品分类退费金额分母计算，并在 Excel 中保留新归类原始数据、业务口径说明和结果核验。

## 2026-08-04 修复 finance 源表重复行导致业绩多算

- 诊断确认 `finance_dw.app_finance_performance_extend_details_hf` 存在业务键完全相同但 `id` 不同的重复行：全表约 39% 订单受影响，其中 52,949 笔订单每笔 ≥6 行重复，185 名顾问被多算。
- 修复 `data_center_qingcheng_2769.sql`（青橙个人转化）、`data_center_qingcheng_2677.sql`（团队完成度【月】）、`data_center_qingcheng_2680.sql`（团队完成度【期】）三个数据集 SQL：
  1. 将 `dd` CTE 中 `org_t` 的 LEFT JOIN + WHERE 窗口判断改为 `EXISTS` 子查询，避免组织链多行导致的笛卡尔积；
  2. 新增 `dd2` CTE，用 `row_number() over (partition by 16 列业务键 order by id) = 1` 消除源表重复行，避免 `gmv_z`/`gmv_t` 的 `sum(price)` 倍乘。
- 三个数据集均已在 Data Center 完成替换上线并确认抽数 `SUCCESS`：个人转化 run `162756633`、团队完成度【期】run `162763410`、团队完成度【月】run `162763412`。
- 更新 `semantic/current_model_bindings.json` 三个 model 的 SQL SHA-256 与字节数。
- 相关字段/表知识补充：`finance_dw.app_finance_performance_extend_details_hf` 的 `id` 字段不保证业务唯一，按订单/课程/交易维度聚合前必须先按业务键去重。

## 2026-08-05 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2677, 2680, 2769`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-08-05 青橙看板与模板金额五期核对

- 对 `<个人转化数据-青橙>`、`<团队转化完成度-青橙>` 在 `20260710期`、`20260716期`、`20260722期`、`20260728期`、`20260803期` 做同员工范围、同团队范围的个人/团队双粒度核对：个人 575 个键、团队 110 个键，双方键集合均完全一致。
- 五期合计模板收入 `11,841,407.12`、看板收入 `11,841,082.72`，差异 `-324.40`；模板退款 `1,452,160.60`、看板退款 `1,452,071.80`，差异 `-88.80`。`20260803期` 两个粒度的收入和退款均逐分一致。
- 差异集中在 10 个员工/团队键，诊断显示全部由模板保留、看板 `service_base0` 排除的 `clazz_name` 含“试听”流水解释；非 H 流失为 0，渠道 `ld` 重复放大指标为 0。
- 确认 `finance_dw.app_finance_performance_extend_details_hf` 虽存在独立的业务键重复风险，但当前 `income_all/refund_all` 是 service 主事实金额，不由 finance 直接求和，因此不是本次看板与模板差异原因。finance 继续仅用于 service 缺失的课程转移补充、内部调课识别和退 4/点睛退 2 规则，并在补充前去重。
- 更新个人/团队 raw、metrics、公式链路、看板编辑器快照、表说明、join key、决策树、快速参考和修复清单；新增 `knowledge/sql_patterns/qingcheng_template_dashboard_amount_reconciliation_20260805.md` 作为证据与对齐建议。
- 刷新青橙项目部 16 个线上看板的只读 profile 文档，全部 `ok_count=16`；本次未执行线上模板、看板保存或发布。

## 2026-08-07 青橙完成度调课调班行级识别修复与三模型上线

- 根因确认：旧版三份完成度 SQL 在 `order_attr` 中按 `order_number + performance_employee_email_name` 取 `max(transfer_in_amount/transfer_out_amount)`，再将订单级 transfer 标记传给同订单全部 service 行。张地43 的 20260803期订单同时包含正常支付行和调课调班行，约 `12,000` 元正常支付因此被误标为内部流水，造成 `income_all=19,800` 但旧 legacy `income/折算后产出=7,800`。
- 按五条排查建议统一修复：`order_attr` 只保留 `original_paid_time`；`service_base0` 在当前 service 明细行识别 transfer 并传递到 `t4`；finance 只在 service 缺失且当前行实际退款、变更金额非 0 时补充；`ord/re_ke` 退 4/点睛退 2 规则保持；finance 补充继续先按业务键去重，所有补充表先聚合到唯一业务粒度再 join。
- 个人行级回归 query `1534542940`：张地43 修复后 `income_all=19,800`、`refund_all=0`、`income=19,800`、`H_promit_4=19,800`、折算后产出 `19,800`。
- 团队期聚合回归 query `1534547907`：`output_rows=330`、`income_all=26,961,943.26`、`refund_all=3,507,394.74`、内部规则后 `promit=23,811,176.26`、折算后产出 `23,009,158.79`；canonical 全量 query `1534553633` 成功。
- 团队月聚合回归 query `1534550261`：`output_rows=88`、`income_all=26,962,143.26`、`refund_all=3,507,394.74`、内部规则后 `promit=23,811,376.26`、折算后产出 `23,009,358.79`；canonical 全量 query `1534556864` 成功。个人 canonical 全量 query 为 `1534559704`。
- 三个数据中心生产替换均完成 Preview、保存后 SQL Hash 回读、刷新和新抽数：
  - `青橙个人转化` / model `2769`：SQL SHA-256 `491b3c9dfb4062cff47ca9b3faaf39b663a25aa044d03117ad11399db2ebc3f1`，Preview `1534567480`，run `163237842`，`SUCCESS`。
  - `团队完成度【期】` / model `2680`：SQL SHA-256 `3d80ad72267fc071998a94e18878991757617d052d3c0b8933979c6d1adbec07`，Preview `1534569423`，run `163237888`，`SUCCESS`。
  - `团队完成度【月】` / model `2677`：SQL SHA-256 `f8bfc3cf89cdb3e8cea4b9193da9294294c67f11dcccc3aff2b87aee4dbe2827`，Preview `1534571611`，run `163237923`，`SUCCESS`。
- 三份替换 receipt 均 `fully_verified=true`；本地 Data Center 知识同步计划 SHA-256 为 `f8d780014c6c5cde290ba5dc19c7f6d219d4d82d6a4287461cc7e41caa96eba5`，已同步 current model bindings、数据集说明、反向索引和 Text2SQL 目录。
- 维护收尾：`build_reverse_indexes.py`、`build_text2sql_catalog.py`、`check_skill_integrity.py`、`validate_text2sql_stack.py` 均通过；SQL 静态规则检查仅保留三份历史复杂 SQL 的既有非聚合表达式警告，Presto/Preview/生产抽数均成功。

## 2026-08-07 青橙个人转化 finance 调课调班独立明细归因修复

- 纠正前次对 finance 明细的泛化判断：`order_number + clazz_name + user_id + trade_status + trade_type + trade_time + employee_email_name + course_grade` 不是当前调课调班明细的可靠唯一粒度。付金艳订单的 36 条明细均有独立 `id/pre_biz_number`，价格合计 `1,500` 元；谈梦玲两笔订单分别为 38 条明细，价格合计 `826.10` 和 `2,687.98` 元，均与 service `transfer_in` 金额一致。
- 修改 `resources/raw_sql/data_center_qingcheng_2769.sql`：删除 finance raw 层基于上述复合键的 `row_number()=1`；保留独立 finance 明细，并按订单、用户、顾问、交易时间、班级、科目、课程部门等真实输出粒度聚合。新增 `service_order_employee`，按 `order_number + employee_email_name` 识别 service 已覆盖的调课链路，避免 finance 用户 ID 与 service 原始用户 ID 不一致时重复补金额。
- 20260803期基线与候选逐员工回归：113 个员工期次键均保留；仅付金艳 `income/H_promit_4` 减少 `30` 元、谈梦玲减少 `70.2816` 元，合计移除旧逻辑误选的 `100.2816` 元；`income_all=1,071,942`、`refund_all=144,332.22`、非 H 金额和退款规则字段不变。付金艳最终班课净收和折算后产出均为 `9,700`。
- 关键验证：finance 明细查询 `1534686938`、付金艳 service 链路查询 `1534690105`、候选个人冒烟 `1534719894`、基线汇总 `1534737041`、候选汇总 `1534741393`、逐员工下载回归 `1534750249/1534760279`、旧 finance 补充明细 `1534794175`。
- Data Center `青橙个人转化` / model `2769` 已完成生产替换：计划 SHA-256 `087613b394475ea8c2280617b229a20f3b5f52264632c22a258065a960107f35`，新 SQL SHA-256 `b92ad3f4bfa4eb1e98c0406138f4ec69232880fc39fd37898e5671de28091ad8`，Preview `1534800547`，新抽数 run `163245267`，状态 `SUCCESS`，receipt `fully_verified=true`。
- 本地 Data Center 同步计划 SHA-256 `1b2b691eae2e45a83cd6cb735fef34c2f6203656fd72dabe0fae0a8766dec146` 已应用；反向索引、catalog、青橙 integrity、351/351 语义评测和完整 Text2SQL 栈均通过。团队完成度【期/月】本次未修改。

## 2026-08-07 青橙团队完成度 finance 独立明细归因修复与双模型上线

- 纠正团队期/月 SQL 中 finance 调课调班补充的现行口径：`order_number + clazz_name + user_id + trade_status + trade_type + trade_time + employee_email_name + course_grade` 不是可靠唯一粒度；该组合键相同的 finance 行可能是不同 `id/pre_biz_number` 的独立明细，不能用 `row_number()=1` 任意吞行。
- 修改 `resources/raw_sql/data_center_qingcheng_2680.sql`、`data_center_qingcheng_2677.sql`：finance raw 层保留独立明细并按订单、目标用户、顾问、交易时间、班级、科目、课程部门、学期、教师等真实输出粒度聚合；新增 `service_order_employee`，按 `order_number + employee_email_name` 判断 service 已覆盖链路，避免 finance/service 用户 ID 不一致时重复补金额。
- 团队期基线/候选均为 330 行、键集合完全一致，7 个团队键发生变化；团队月基线/候选均为 88 行、键集合完全一致，6 个团队键发生变化。两模型合计移除旧 finance 误补 `4,573.3206` 元；`income_all`、`refund_all`、退款及人数指标不变，变化只落在错误追加的 finance legacy 收入及其净收/折算规则金额。20260803期/202608月对应误补金额均为 `100.2816` 元。
- 回归下载查询：团队期基线/候选 `1534860885` / `1534852526`；团队月基线/候选 `1534863973` / `1534857808`。两组结果均未达到 1000 行下载上限，键集合和金额差异已逐行核对。
- Data Center 生产替换与新抽数均成功：
  - `团队完成度【期】` / model `2680`：SQL SHA-256 `3fb78491f8ae5ac8540d673f3e499e7e786404588f60fb1cd15b94b89d1bf4d7`，Preview `1534870341`，run `163252065`，`SUCCESS`。
  - `团队完成度【月】` / model `2677`：SQL SHA-256 `5152db09f17995d8d82851826ac2875764ecc144e63fe03d7e1a515d163679a4`，Preview `1534872315`，run `163252066`，`SUCCESS`。
- 三模型（2677、2680、2769）本地 Data Center Skill 同步计划 SHA-256 `ef8add37de56320050ffd1af9ba17454a81dbd8912511b495515f7c193f081c5` 已应用；反向索引、catalog、唯一版本审计、青橙 integrity、351/351 语义评测和完整 Text2SQL 栈均通过。前次单模型同步因另一模型旧哈希漂移而回滚，未影响远端；随后已按三模型事务成功同步。

## 2026-08-07 青橙 service 真实退款与 order_change 退款侧修复上线

- 根因确认：service 真实退款行虽然已进入 `refund_all`，但旧版退款逻辑复用订单级 `order_change + transfer` 排除条件，把同一调课调班链路中的真实退款一起置零，造成 `refund`/`refund_4` 少算，折算后产出偏高。安全探针 `1535062058` 证明全表存在少量同一明细同时带 `refund_amount` 和 transfer 金额，不能使用“有 transfer 就整行退款置零”的规则。
- 三份 canonical SQL 同步修复：`order_change_order_map` 仅用 `select distinct` 消除完全相同的订单映射；`order_change` 增加 `has_transfer_event`；`income/p_sub` 使用收入侧 `is_internal_order_change`，`refund/r_sub/refund_4` 使用退款侧 `is_internal_refund_order_change`。service 当前行 `refund_amount > 0` 时退款优先保留，finance 只补 service 缺失链路，不直接替代 service 金额。
- `ord/re_ke` 退 4、点睛退 2、H 一对一全额退款、H/非 H 折算规则均未改变。个人/团队金额展示仍为 `income_all`、`refund_all`、`income_all-refund_all`，折算后产出仍基于 `promit_4 = income-refund_4`。
- 候选 Presto 回归均成功：个人 query `1535081501`，团队期 query `1535084952`，团队月 query `1535084948`。个人五名异常顾问的 `refund` 已恢复为 service 真实退款：刘孟佳 `4,550`、王东亚01 `13,505.26`、樊盼盼 `3,637.74`、白君辉 `2,481.81`、宋佳鑫04 `6,686.06`；`class_refund_4` 仍分别按 4 节/点睛 2 节规则折减。
- 三个数据中心均完成替换、Preview、SQL Hash 回读和新抽数：
  - `青橙个人转化` / model `2769`：SQL SHA-256 `a9345d28e6de5c235e62355646ca83c21c773571b8a23e7436d468a9a9006e5e`，Preview `1535088666`，run `163259511`，`SUCCESS`。
  - `团队完成度【期】` / model `2680`：SQL SHA-256 `9b10aa28042de69dda9b18ed6bf6c42c35ae9d4ea924d250afc7c3c6f09b0e5f`，Preview `1535090729`，run `163259517`，`SUCCESS`。
  - `团队完成度【月】` / model `2677`：SQL SHA-256 `5faa86ec217f865bdbe8057c11fc860b169ec3526516a5ad44c34bd0fe609021`，Preview `1535092614`，run `163259522`，`SUCCESS`。
- 本地 Data Center 同步计划 SHA-256 `94f4b2bdca15706037debb10dbb8624e9e506e7d59f3d5913d1e0b1195128343` 已应用；数据集说明和 current model bindings 已更新。后续已重建 Qingcheng 反向索引、Text2SQL catalog，并通过 Qingcheng integrity、唯一版本审计、语义评测和完整 Text2SQL 栈验证。

## 2026-08-07 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2677, 2680, 2769`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-08-07 青橙退款事件金额级分配修复与三模型重新上线

- 根因：前一版虽然已改为 service 明细行识别 transfer，但退款侧仍可能把同一调课调班订单的真实退款按订单级二元规则整体排除；同时 finance 复合展示键不能代表独立课程退款事件。
- 三份 canonical SQL（`2769`、`2680`、`2677`）新增 `finance_refund_event_allocated`：保留 finance 独立退款明细并按真实事件粒度聚合；以 `order_change` transfer pool 做精确匹配或按事件金额比例分配；`t4` 从 service 退款中扣除内部分配余额，`refund_all` 仍完全使用 service 主事实。
- `ord/re_ke` 班课 4 节、点睛 2 节、H 一对一全额退款和 H/非 H 折算规则未改变；所有补充表先聚合到唯一业务粒度再 join，未使用 `order_number + clazz_name + user_id + trade_status + trade_type + trade_time + employee_email_name + course_grade` 判重。
- 个人、团队期、团队月定向回归 query 分别为 `1535361544`、`1535375732`、`1535381004`；20260803期王东亚01 `H_income_4=64,000`、`refund_all=13,505.26`、`H_refund_4=6,772.61`、`H_promit_4=57,227.39`，张昊62 `15,000 / 2,210 / 12,790`，付金艳 `9,700 / 0 / 9,700`，张地43 `19,800 / 0 / 19,800`。
- 三个数据中心均完成预览、保存后 SQL 哈希回读、刷新和新抽数 `SUCCESS`：
  - 个人转化 `2769`：SQL SHA-256 `f4c545c9345efce20f4268b9f9b307be705e0716afbb5f07d0a243a2012c6630`，Preview `1535390346`，run `163273845`。
  - 团队完成度【期】`2680`：SQL SHA-256 `37e0294f01e7aa40a1c93a7f2efe7b82652a430cef866ae2aab2704bfa7e7109`，Preview `1535392792`，run `163273846`。
  - 团队完成度【月】`2677`：SQL SHA-256 `f84f2244b9474679d1ee5e2701ae5a9968097b1c8a4088a6648754e5d25318fd`，Preview `1535395486`，run `163273848`。
- 本地 Skill 同步计划 SHA-256 `a3ff0a32f9d85594cc8522373b4d9f7b397b03f0ec4c2ffce3a99110ce0676e5` 已应用；反向索引、Text2SQL catalog、唯一版本审计、青橙 integrity、351/351 语义评测及完整 Text2SQL 栈均通过。完整栈中的既有 pending manual-confirmation 与历史引用告警未新增为错误。
