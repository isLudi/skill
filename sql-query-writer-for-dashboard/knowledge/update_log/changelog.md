# 更新记录

## 2026-05-01

- 创建 `sql-query-writer-for-dashboard` Skill。
- 复制初始 PDF：`resources/raw_pdfs/数据地图概览.pdf`。
- 渲染 PDF 页面到 `resources/rendered_pages/`。
- 初始化 9 张 PDF 表和 2 张稳定临时表的知识库。
- 标记 PDF 图片型字段页为低置信度，需人工复核。

## 2026-05-01 临时表 Excel 结构补充

- 从 `E:\2000_work\GAOTU\看板维护表格\jiagou_xian_zhengzhou.xlsx` 补充 `temp_table.dingxi01_jiagou_db` 字段结构。
- 从 `E:\2000_work\GAOTU\看板维护表格\daoke_t_one_six.xlsx` 补充 `temp_table.dingxi01_daoke_1_6_t` 字段结构。
- 更新临时表常用过滤条件、join key、SQL 片段和注意事项。
- 更新 `knowledge/joins/common_join_keys.md` 与 `knowledge/joins/table_relationships.md` 中的临时表关系说明。

## 2026-05-01 市场顾问转化看板 SQL 入库

- 新增原始 SQL：`resources/raw_sql/market_consultant_conversion.sql`。
- 新增看板文档：`knowledge/dashboards/market_consultant_conversion.md`。
- 新增指标集合：`knowledge/metrics/market_consultant_conversion_metrics.md`。
- 确认主表完整库名：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`。
- 新增表知识：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`、`temp_table.dingxi01_channel_group`、`temp_table.dingxi01_cost`、`temp_table.dingxi01_jiagou_zx`。
- 更新 join 知识和 department/virtual department 范围限定规则。

## 2026-05-01 15:34:37

- 规范化表结构文件：11 个。
- 更新 `knowledge/01_table_index.md`。

## 2026-05-01 15:35:24

- 规范化表结构文件：11 个。
- 更新 `knowledge/01_table_index.md`。

## 2026-05-01 15:35:47

- 规范化表结构文件：11 个。
- 更新 `knowledge/01_table_index.md`。

## 2026-05-01 15:54:31

- 规范化表结构文件：2 个。
- 更新 `knowledge/01_table_index.md`。

## 2026-05-01 16:10:55

- 规范化表结构文件：4 个。
- 更新 `knowledge/01_table_index.md`。

## 2026-05-01 16:31:45 百家字段目录与权限整合

- 从 `table_fields_full_20260420_092405.json` 补全/新增表文档：14 张。
- 从 `row_permissions.json` 更新真实历史权限切分字段和值。
- 更新 `knowledge/01_table_index.md` 与 `knowledge/03_range_limit_rules.md`。
- 重命名表文档 `service_dw.dim_cstm_active_user_c_appliction_mb_df` -> `dw.dim_cstm_active_user_c_appliction_mb_df`。
- 重命名表文档 `service_dw.dws_user_active_user_c_appliction_hf` -> `dw.dws_user_active_user_c_appliction_hf`。
- 重命名表文档 `unknown.app_user_attribute_label_gaia_wide_df` -> `service_dw.app_user_attribute_label_gaia_wide_df`。
- 移除重复且字段目录未确认的表文档 `service_dw.dm_crm_lead_cost_gmv_communication_learn_full_link_df`，保留 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`。

## 2026-05-01 外呼过程数据看板 SQL 入库

- 新增原始 SQL：`resources/raw_sql/outbound_call_process_dashboard.sql`。
- 新增看板文档：`knowledge/dashboards/outbound_call_process_dashboard.md`。
- 新增指标集合：`knowledge/metrics/outbound_call_process_metrics.md`。
- 更新 dashboards 与 metrics README 索引。
- 更新 `knowledge/joins/table_relationships.md` 中的外呼过程看板关系。
- 标记主表 `dt/hour` 偏移、数值/字符串比较、首呼时差求和、外呼和首 call CTE 部门过滤、临时表 join 唯一性等待确认事项。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/outbound_call_process_dashboard.sql`；历史 SQL 保持原样，校验输出包含部门过滤解析告警、字符串数字混用、别名解析误报和 group by 解析告警。

## 2026-05-02 外呼过程数据看板 SQL 更新

- 按用户提供的新版本覆盖 `resources/raw_sql/outbound_call_process_dashboard.sql`。
- 更新 `knowledge/dashboards/outbound_call_process_dashboard.md`，同步 `sbb` 双表发送关联、`yi_shuanggou`、`yi_huishou`、到课最终层去重计数和新版过滤条件。
- 同步更新 `knowledge/metrics/outbound_call_process_metrics.md` 与 `knowledge/joins/table_relationships.md` 中的相关指标和 join 关系。
- 新版在 `data` CTE 中新增一段读取 `service_dw.app_h_crm_lead_task_process_info_detail_hf` 的 `sbb` 关联；该物理表旧版已用于 `f_call0` 首 call 统计，本次新增用途为双表发送/回收标记。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/outbound_call_process_dashboard.sql`；校验仍提示部门字段解析告警、数值/字符串混用、别名解析误报和 group by 解析告警，已在看板文档待确认事项中保留。

## 2026-05-02 顾问销售评优 SQL 入库

- 从 `D:\Feishu\评优.txt` 规范化入库原始 SQL：`resources/raw_sql/consultant_sales_ranking_evaluation.sql`。
- 新增看板文档：`knowledge/dashboards/consultant_sales_ranking_evaluation.md`。
- 新增指标集合：`knowledge/metrics/consultant_sales_ranking_evaluation_metrics.md`。
- 新增表结构文档：`knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md`、`knowledge/tables/temp_table.dingxi01_pingyou_jg.md`。
- 更新 `knowledge/01_table_index.md`、dashboards/metrics README、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`、`knowledge/03_range_limit_rules.md`。
- 标记该 SQL 与市场顾问转化看板同属顾问销售数据计算，但本 SQL 以财务流水和评优临时表为基础，分别按期次、月度、季度、半年聚合排名。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/consultant_sales_ranking_evaluation.sql`；校验提示课程部门字段被选出但未单独过滤，已写入看板待确认事项。

## 2026-05-02 业绩归属信息扩展表字段补充

- 根据 `E:\2000_work\GAOTU\新建 Microsoft Word 文档.docx` 补充 `knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md`。
- 确认分区字段 2 个：`dt`、`hour`。
- 补全非分区字段 145 个，并记录字段类型、字段描述、常见用途和是否常用。
- 补充该表的强制范围限定字段，包括 `employee_*_department_name`、`course_*_department_name`、`pre_course_*_department_name` 以及组织架构 path 字段。
- 更新 `knowledge/01_table_index.md` 中该表的中文名、粒度说明和字段校验状态。

## 2026-05-02 临时表 Excel 结构复核补充

- 从 `E:\2000_work\GAOTU\看板维护表格\daoke_t_one_six.xlsx` 更新 `knowledge/tables/temp_table.dingxi01_daoke_1_6_t.md`，确认数据行 2862 行、字段 7 个、空行 1 行。
- 从 `E:\2000_work\GAOTU\看板维护表格\jiagou_xian_zhengzhou.xlsx` 更新 `knowledge/tables/temp_table.dingxi01_jiagou_db.md`，确认数据行 5017 行、字段 10 个、空行 7 行。
- 从 `E:\2000_work\GAOTU\看板维护表格\jiagou2026_zx.xlsx` 更新 `knowledge/tables/temp_table.dingxi01_jiagou_zx.md`，确认数据行 885 行、字段 7 个。
- 从 `E:\2000_work\GAOTU\看板维护表格\pingyou_jg.xlsx` 更新 `knowledge/tables/temp_table.dingxi01_pingyou_jg.md`，确认数据行 1220 行、有效字段 14 个，并忽略 1 个空表头列。
- 四张临时表均补充字段样例、Excel 推断类型、强制范围限定字段、常用过滤条件、常用 join key、key 重复检查和去重 join 模板。
- 更新 `knowledge/01_table_index.md` 中四张临时表的数据规模、字段来源和校验状态。

## 2026-05-02 Word 表结构补充：首call、员工维表、归因流水

- 根据 `E:\2000_work\GAOTU\顾问首call数据分析表.docx` 新增 `knowledge/tables/gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf.md`，确认分区字段 2 个、非分区字段 19 个。
- 根据 `E:\2000_work\GAOTU\员工维表.docx` 更新 `knowledge/tables/finance_dw.dim_finance_employee_df.md`，确认分区字段 1 个、非分区字段 42 个。
- 根据 `E:\2000_work\GAOTU\归因流水粒度统计明细表.docx` 更新 `knowledge/tables/service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.md`，确认分区字段 2 个、非分区字段 184 个。
- 更新 `knowledge/01_table_index.md`，登记首 call 新表并刷新员工维表、归因流水表的字段来源和校验状态。
- 更新 `knowledge/joins/common_join_keys.md` 与 `knowledge/joins/table_relationships.md`，补充 `account_id`、`biz_number`、`performance_employee_email_prefix` 与员工维表、首 call 任务、归因流水的关系。
- 明确外呼过程看板的首 call 任务推荐从 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` 读取，并通过 `finance_dw.dim_finance_employee_df.account_id` 桥接员工信息；禁止将 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.ad_account_id` 当成员工 `account_id` 使用。

## 2026-05-03 Skill 封装与调用模板补充

- 将 `metadata.json` 版本更新为 `0.2.0`，补充 `docs/USAGE_PROMPTS.md` 和 `scripts/check_skill_integrity.py` 元信息。
- 在 `SKILL.md` 增加“加载与封装边界”，明确新对话加载入口、知识库读取顺序、禁止编造字段和维护自检规则。
- 新增 `docs/USAGE_PROMPTS.md`，提供标准加载、简短加载、SQL 报错修复、看板 SQL 改写和知识库维护模板。
- 新增 `scripts/check_skill_integrity.py`，用于检查入口文件、metadata、知识库目录、核心脚本、表文档结构和表索引覆盖。
- 更新 `README.md` 和 `scripts/README.md`，补充新对话调用方式和结构自检命令。

## 2026-05-03 外呼过程数据看板期次映射二级部门口径更新

- 根据排查确认，市场顾问外呼看板允许主线索 `period_mapping_second_level_department_name = '精品班学部'`，不能只保留 `市场部`。
- 更新 `resources/raw_sql/outbound_call_process_dashboard.sql`，将主线索范围从 `period_mapping_second_level_department_name = '市场部'` 改为 `period_mapping_second_level_department_name in ('市场部','精品班学部')`。
- 更新 `knowledge/dashboards/outbound_call_process_dashboard.md`、`knowledge/metrics/outbound_call_process_metrics.md` 与 `knowledge/joins/table_relationships.md`，同步记录截面分配在 `市场部/市场顾问部`、期次映射二级部门允许 `市场部` 和 `精品班学部` 的口径。

## 2026-05-07 顾问部门任职期销售 SQL 入库

- 新增原始 SQL：`resources/raw_sql/data_center_market_2727_20260705.sql`，来源为用户提供的“伙伴在部门开始时间”SQL。
- 新增看板文档：`knowledge/dashboards/consultant_sales_department_tenure.md`。
- 新增指标集合：`knowledge/metrics/consultant_sales_department_tenure_metrics.md`。
- 新增最小表结构文档：`knowledge/tables/dw.dim_employee_chain.md`，记录该 SQL 中使用的组织链字段，并标记真实 DDL、字段类型、数据粒度和权限范围待人工确认。
- 更新 `knowledge/01_table_index.md`，登记 `dw.dim_employee_chain`。
- 更新 `knowledge/dashboards/README.md` 与 `knowledge/metrics/README.md`，补充新看板和指标集合索引。
- 更新 `knowledge/joins/common_join_keys.md` 与 `knowledge/joins/table_relationships.md`，补充组织链 `path_name` 范围限定、`email_prefix` 优先关联建议、`name` 关联风险和顾问部门任职期销售统计关系。
- 记录待确认事项：`org_t.name = dd_0.name` 是否可改为邮箱前缀关联、在职员工 `end_time` 为空处理、是否补充 `employee_third_level_department_name = '市场顾问部'`、课程部门是否需要单独范围限定、`promit/pmit` 命名和口径。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/data_center_market_2727_20260705.sql`；校验提示课程部门字段未过滤、部门字段解析误报和 `org_t` group by 解析误报，已写入看板待确认事项。
- 运行 `python scripts/check_skill_integrity.py`；结构自检通过，表索引覆盖正常。

## 2026-05-07 员工信息表 Word 字段补充

- 根据 `E:\2000_work\GAOTU\员工信息表.docx` 更新 `knowledge/tables/dw.dim_employee_chain.md`。
- 确认分区字段 1 个：`dt`。
- 补全非分区字段 33 个，包括 `biz_type`、`employee_id`、`email_prefix`、`role_id`、`department`、`phase`、`path_name`、`name`、`job_number`、`leader`、`source_hr_status`、`begin_time`、`end_time` 等。
- 更新 `knowledge/01_table_index.md`，将 `dw.dim_employee_chain` 从 SQL 推断字段升级为 Word 字段说明来源。
- 更新 `knowledge/joins/common_join_keys.md`，补充 `employee_id`、`job_number/display_number`、`leader` 等员工关联键。
- 更新 `knowledge/joins/table_relationships.md`、`knowledge/dashboards/consultant_sales_department_tenure.md` 和 `knowledge/metrics/consultant_sales_department_tenure_metrics.md`，将组织链字段来源改为 Word 文档，保留主键唯一性、行权限、姓名关联和 `end_time` 空值处理待确认事项。

## 2026-05-08 市场顾问线索转化到课 SQL 入库

- 新增原始 SQL：`resources/raw_sql/market_consultant_lead_conversion_attendance.sql`，来源为用户提供的市场顾问线索转化、到课、深沟、AB 意向和成本目标 SQL。
- 新增看板文档：`knowledge/dashboards/market_consultant_lead_conversion_attendance.md`。
- 新增指标集合：`knowledge/metrics/market_consultant_lead_conversion_attendance_metrics.md`。
- 新增表结构文档：`knowledge/tables/temp_table.shenbaoxin_channel_group.md`，记录 SQL 中使用的 `channel` join key，并将完整字段、字段类型、维护来源和唯一性标记为待人工确认。
- 更新 `knowledge/01_table_index.md`，登记 `temp_table.shenbaoxin_channel_group`。
- 更新 `knowledge/dashboards/README.md` 与 `knowledge/metrics/README.md`，补充新看板和指标集合索引。
- 更新 `knowledge/joins/common_join_keys.md` 与 `knowledge/joins/table_relationships.md`，补充 `channel + grade + begin_time` 到课映射、`shenbaoxin_channel_group` 渠道分组关联、成本目标和架构临时表关系。
- 记录待确认事项：`temp_table.shenbaoxin_channel_group` 字段结构、`temp_table.dingxi01_daoke_1_6_t` 使用 `channel` 还是 `qudao`、`AB_zhuanhua` 字符串数字比较、`temp_table.dingxi01_jiagou_db` join 但未输出字段是否为预期。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/market_consultant_lead_conversion_attendance.sql`；校验提示部门字段解析告警、`conversion_lead_count = '1'` 字符串数字混用、`sale_flow_stage_sequence` 字段类型待确认、派生字段误报和 `select distinct` group by 解析误报，已在看板文档待确认事项中保留。
- 运行 `python scripts/check_skill_integrity.py`；结构自检通过，新增表文档存在待人工确认项属预期。

## 2026-05-08 顾问部门任职期销售 20260424 期版本入库

- 新增原始 SQL：`resources/raw_sql/data_center_market_2742_20260705.sql`，来源为用户提供的“伙伴在部门开始时间”SQL。
- 新增看板文档：`knowledge/dashboards/consultant_sales_department_tenure_period_20260424.md`。
- 新增指标集合：`knowledge/metrics/consultant_sales_department_tenure_period_20260424_metrics.md`。
- 更新 `knowledge/dashboards/README.md` 与 `knowledge/metrics/README.md`，补充该期次过滤版本索引。
- 更新 `knowledge/joins/table_relationships.md`，记录该 SQL 继承 `data_center_market_2727_20260705.sql` 的组织链、财务流水和专项架构关系，仅在最终输出层增加 `qici = '20260424期'`。
- 记录待确认事项：`name` 关联唯一性、`end_time` 为空处理、是否补充 `employee_third_level_department_name = '市场顾问部'`、课程部门是否需要单独范围限定、`promit/pmit` 命名和口径。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/data_center_market_2742_20260705.sql`；校验提示课程部门字段未过滤、员工部门字段解析误报和 `org_t` group by 解析误报，已在看板文档待确认事项中保留。
- 运行 `python scripts/check_skill_integrity.py`；结构自检通过，表索引覆盖正常。

## 2026-05-08 顾问部门任职期销售通用 SQL 排名增强

- 按用户提供的新版本覆盖 `resources/raw_sql/data_center_market_2727_20260705.sql`。
- 更新 `knowledge/dashboards/consultant_sales_department_tenure.md`，同步新版 CTE 链路、邮箱前缀关联、三层员工部门限定、日维度排名和期次维度排名逻辑。
- 更新 `knowledge/metrics/consultant_sales_department_tenure_metrics.md`，补充 `day_dept_period_rank_scope`、`day_dept_period_rank_no`、`day_dept_period_need_pmit_to_previous`、`period_dept_rank_scope`、`period_dept_rank_no`、`period_dept_need_pmit_to_previous`、`period_income`、`period_refund`、`period_pmit` 等指标。
- 更新 `knowledge/joins/table_relationships.md`，将任职期过滤 join 从 `org_t.name = dd_0.name` 改为 `org_t.email_prefix = dd_0.email_prefix`，并记录日维度和期次维度排名关系。
- 新版财务流水范围补充 `employee_third_level_department_name = '市场顾问部'`。
- 记录待确认事项：`end_time` 为空处理、`temp_table.dingxi01_jiagou_zx.employee_email_name = rd.name` 姓名关联唯一性、排名是否允许并列、固定期次版本 `data_center_market_2742_20260705.sql` 是否需要同步新版排名增强逻辑。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/data_center_market_2727_20260705.sql`；校验提示 `employee_*_department_name` 已过滤但被脚本解析为未过滤、`org_t` 中 `name` group by 解析误报，已在看板文档待确认事项中保留。
- 运行 `python scripts/check_skill_integrity.py`；结构自检通过，表索引覆盖正常。

## 2026-05-08 date_add 平台兼容规则

- 扫描 `resources/raw_sql/` 中的 `date_add` 用法，确认多份历史 SQL 仍存在 Presto 三参数写法 `date_add('day', n, expr)`，不能将历史 SQL 视为平台兼容模板直接照抄。
- 基于 DLC/Presto 报错 `date_add() requires 2 argument, got 3`，在 `SKILL.md` 增加平台兼容规则：生成新 SQL 时禁止使用三参数 `date_add`，日期偏移优先使用 `interval`。
- 在 `knowledge/sql_patterns/dashboard_query_patterns.md` 增加期次计算的 `interval` 模板。
- 在 `scripts/validate_sql_rules.py` 增加三参数 `date_add` 检查，避免后续生成 SQL 再触发同类平台解析错误。
- 同步更新 `docs/USAGE_PROMPTS.md` 标准加载模板中的 SQL 生成规则。

## 2026-05-08 排名粒度与顾问名单来源规则补充

- 根据暑期激励看板转化指标联调问题，补充排名、比率、目标、差值类指标的“计算粒度 vs 最终输出粒度”规则：若期次粒度指标输出到日维度结果，必须提示前端聚合风险，并提供期次粒度最终查询或 `*_once` 防重复字段方案。
- 明确 `temp_table.dingxi01_pingyou_jg` 只在评优/参评名单/评优架构/人产口径下使用；该表含 `qici`，会限制结果落在已维护期次内。
- 补充 `temp_table.dingxi01_jiagou_zx` 作为在职架构顾问名单替代来源的使用模板，要求限定在职和郑州/西安顾问部范围，并按 `employee_email_name` 去重。
- 同步更新 `SKILL.md`、`docs/USAGE_PROMPTS.md`、`knowledge/sql_patterns/dashboard_query_patterns.md`、`knowledge/tables/temp_table.dingxi01_pingyou_jg.md`、`knowledge/tables/temp_table.dingxi01_jiagou_zx.md`。

## 2026-05-09 线索分配计划与实际有效量 SQL 入库

- 新增原始 SQL：`resources/raw_sql/lead_assign_plan_actual_valid_count.sql`，来源为用户提供的“实际有效数量/计划分配数量”SQL。
- 新增看板文档：`knowledge/dashboards/lead_assign_plan_actual_valid_count.md`。
- 新增指标集合：`knowledge/metrics/lead_assign_plan_actual_valid_count_metrics.md`。
- 新增表结构文档：`knowledge/tables/service_dw.dim_crm_assign_rule_plan_item_info_hf.md`、`knowledge/tables/temp_table.dingxi01_plan_id.md`，记录 SQL 中使用的最小字段和待确认项。
- 更新 `knowledge/01_table_index.md`、`knowledge/dashboards/README.md`、`knowledge/metrics/README.md`。
- 更新 `knowledge/joins/common_join_keys.md` 与 `knowledge/joins/table_relationships.md`，补充分配规则 `rule_id + plan_id`、`group_id`、实际量 `rule_name + employee_email_name`、架构 `employee_email_name + substr(qici, -5)` 等关联关系。
- 更新既有表文档 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`、`service_dw.dim_crm_assign_rule_lead_detail_hf.md`、`temp_table.dingxi01_jiagou_db.md`，补充该 SQL 的使用注意事项。
- 记录待确认事项：计划 item 表真实 DDL、`temp_table.dingxi01_plan_id` 维护来源和唯一性、`assign_lead_count` 含义、实际量与计划侧小时偏移不一致、规则名拆分格式、期次尾号关联跨年份重复风险。
- 将用户 SQL 中的 `group by 1,2` 和 `group by 1..12` 改为显式字段/表达式分组，便于作为后续模板复用。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/lead_assign_plan_actual_valid_count.sql`；当前脚本对多 CTE 的 `group by` 片段存在串段解析限制，仍提示 `employee_email_name` 未分组，实际 `vd` CTE 已显式按 `rule_name, employee_email_name` 分组。
- 运行 `python scripts/check_skill_integrity.py`；结构自检通过，新增表文档包含待人工确认项属预期。

## 2026-05-09 plan_id Excel 来源补充

- 根据用户提供路径 `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\plan_id.xlsx` 更新 `temp_table.dingxi01_plan_id` 表知识。
- 确认 Excel sheet `Sheet1` 字段为 `year`、`qici`、`group_id`、`group_name`，非空数据行 51 行，字段 4 个，当前年份均为 2026。
- 更新 `knowledge/tables/temp_table.dingxi01_plan_id.md`，补充字段样例、常用过滤、SQL 片段和 key 重复检查。
- 更新 `knowledge/01_table_index.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`、`knowledge/dashboards/lead_assign_plan_actual_valid_count.md` 和 `knowledge/metrics/lead_assign_plan_actual_valid_count_metrics.md`。
- 记录唯一性：`qici + group_id`、`year + qici + group_id` 唯一；`group_id` 单字段不全局唯一，`15175` 出现在 `0501期`、`0508期`、`0515期`；`group_name` 单字段也不唯一。

## 2026-05-09 渠道 CASE 口径归档

- 根据用户提供路径 `D:\Feishu\0508.txt` 归档最新渠道 CASE 片段到 `resources/raw_sql/market_channel_case_when_0508.sql`。
- 新增渠道 CASE 知识文档：`knowledge/sql_patterns/channel_mapping_case_when.md`，记录来源、输出字段 `qudao`、依赖字段、关键抖音私信规则、复用模板和定期更新流程。
- 统计当前片段：198 行、197 个 `then` 分支、128 个去重渠道输出值。
- 更新 `knowledge/sql_patterns/dashboard_query_patterns.md`，补充市场顾问渠道 CASE 映射入口。
- 更新市场顾问转化、市场顾问线索转化到课、线索分配计划实际有效量相关 dashboard/metrics 文档，提示后续改写 SQL 优先引用独立渠道 CASE 资源。
- 记录关键排查口径：`抖音私信` 不应只依赖 `rule_name`，还需检查 `source_manager_name = '韩正卿'`，以及 `channel_name_1 = '信息流'` 且 `put_plan_name` 命中 `抖音私信/初三0元/高中0元` 的 `信息流-抖音私信` 规则。

## 2026-05-09 流量画像 SQL 入库

- 新增原始 SQL：`resources/raw_sql/data_center_market_2683_20260705.sql`，来源为用户提供的“流量画像”原始查询代码。
- 新增看板文档：`knowledge/dashboards/traffic_profile.md`，记录 APP 登录、最新设备渠道、外呼、深沟、到课、成交科目档位、成本目标和城市等级等 CTE/指标口径。
- 新增指标集合：`knowledge/metrics/traffic_profile_metrics.md`。
- 更新 `knowledge/dashboards/README.md` 与 `knowledge/metrics/README.md`，补充流量画像入口。
- 更新 `knowledge/joins/common_join_keys.md` 与 `knowledge/joins/table_relationships.md`，补充用户 APP 登录、外呼工作量、行课到课、财务成交科目数、成本目标和架构临时表的关联关系。
- 更新相关表文档：主全链路表、C 端应用登录日表、私海明细、外呼工作量、行课明细、财务业绩明细、到课映射、渠道分组、成本目标和架构临时表，补充流量画像 SQL 使用备注。
- 更新 `knowledge/03_range_limit_rules.md`，补充流量画像看板的历史范围限定；更新 `knowledge/sql_patterns/dashboard_query_patterns.md`，补充流量画像增强模式。
- 记录待确认事项：原始 SQL 存在三参数 `date_add` 历史写法、主表 `dt/hour` 偏移不一致、`call_c` join 未带 `lead_id`、成交科目数 join 未带顾问名、`podan` 注释与代码不一致、临时表唯一性和数值/字符串比较风险。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/data_center_market_2683_20260705.sql`；历史 SQL 保持原样，校验提示三参数 `date_add`、数值/字符串比较、部门过滤解析告警、派生字段误报和 `select distinct` group by 解析告警，已写入看板待确认事项。
- 运行 `python scripts/check_skill_integrity.py`；结构自检通过，既有表文档含待人工确认项属预期。

## 2026-05-09 changelog 正序规则补充

- 调整 `knowledge/update_log/changelog.md` 展示顺序，改为按日期从旧到新正序排列。
- 明确后续更新 changelog 必须按日期向后追加在文件末尾；同一天多次更新按发生顺序继续追加，必要时使用 `YYYY-MM-DD HH:mm:ss` 标题区分顺序。
- 更新 `SKILL.md`、`docs/USAGE_PROMPTS.md`、`knowledge/sql_patterns/channel_mapping_case_when.md` 和 `scripts/check_skill_integrity.py`，固化 changelog 正序追加和校验规则。
- 排查其他 Markdown 日期标题顺序，未发现除 `knowledge/update_log/changelog.md` 外的同类时间排序问题。

## 2026-05-09 退费分析 SQL 入库

- 新增原始 SQL：`resources/raw_sql/data_center_market_2350_20260705.sql`，来源 `E:\2000_work\GAOTU\多科用户退费占比.txt`。
- 新增原始 SQL：`resources/raw_sql/data_center_market_2349_20260705.sql`，来源 `E:\2000_work\GAOTU\退费_科目_产品.txt`。
- 新增原始 SQL：`resources/raw_sql/data_center_market_2353_20260705.sql`，来源 `E:\2000_work\GAOTU\退费原因分析.txt`。
- 新增看板文档：`knowledge/dashboards/refund_multi_subject_user_ratio.md`、`knowledge/dashboards/refund_subject_product.md`、`knowledge/dashboards/refund_reason_analysis.md`。
- 新增指标集合：`knowledge/metrics/refund_analysis_metrics.md`，记录 `zong_price`、`name_total_price`、`refund_amount`、`refund_total`、多科分层、标准科目、产品分类和退费原因等口径。
- 新增表文档：`knowledge/tables/finance_dw.dwd_finance_order_refund_df.md`，根据退费原因分析 SQL 补充 `dt`、`order_number`、`refund_reason`、`refund_type` 最小字段，真实 DDL 和 `refund_type = '1'` 含义待人工确认。
- 更新 `knowledge/dashboards/README.md`、`knowledge/metrics/README.md`、`knowledge/01_table_index.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`、`knowledge/03_range_limit_rules.md` 和相关表文档。
- 记录关键关联：财务业绩明细通过 `user_id1 + name` 关联归因流水 `original_order_user_number + performance_employee_email_name` 获取最新 `lead_id`，再通过 `lead_id + account_domain` 关联分配规则；退费原因通过 `order_number` 关联退款明细表。
- 运行三份 SQL 的 `scripts/validate_sql_rules.py`；历史 SQL 原样归档，校验提示三参数 `date_add` 和窗口函数/`select distinct` 导致的 group by 解析告警，已在看板文档待确认事项中保留。

## 2026-05-14 结果缺失与未来期次排查规则补充

- 根据外呼过程看板排查沉淀“某期次/经理/顾问查不到”的诊断流程：先判断 SQL 是事实主表驱动还是名单/架构表驱动。
- 在 `knowledge/sql_patterns/dashboard_query_patterns.md` 新增“结果缺失与未来期次排查”，强调临时架构表有目标期次不代表事实主表已经产出目标期次数据。
- 增加指定期次事实存在性验证模板，要求显式过滤事实主表派生 `qici`，避免只用目标期次架构名单查询出历史所有期次。
- 记录 `order by qici asc limit N` 会截断最新期次的误判风险；查最新期次应使用倒序或显式目标期次过滤。
- 更新 `knowledge/dashboards/outbound_call_process_dashboard.md`，说明外呼过程看板当前为事实主表驱动，未来期次仅在架构表维护但主表无数据时不会展示。
- 更新 `knowledge/tables/temp_table.dingxi01_jiagou_db.md`，补充该表可能提前维护未来期次，排查时需单独验证事实主表派生期次和指标。
- 更新 `SKILL.md`，在加载边界中加入结果缺失排查入口提示。

## 2026-05-15 流量画像 city_channel SQL 更新

- 使用用户提供的 `D:\Feishu\city_channel.txt` 覆盖归档 `resources/raw_sql/data_center_market_2683_20260705.sql`，确认文件哈希与来源一致。
- 更新 `knowledge/dashboards/traffic_profile.md` 和 `knowledge/metrics/traffic_profile_metrics.md`，补充 `province_name`、`city_name`、`city_level_name` 城市渠道维度，移除旧版 `city_level_row` 结果指标说明。
- 更新期次范围口径：当前版本在 `base` CTE 使用 `period_name >= ${period_name1}` 且 `period_name < ${period_name2}`，执行前必须替换参数。
- 更新主表分区说明：当前版本主全链路表使用 `dt = now() - 2 hour` 且 `hour = now() - 2 hour`；旧版 `hour = now() - 3 hour` 仅作为历史变体风险保留。
- 更新 `knowledge/01_table_index.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`、`knowledge/03_range_limit_rules.md`、`knowledge/sql_patterns/dashboard_query_patterns.md`、`knowledge/dashboards/README.md`、`knowledge/metrics/README.md` 和相关表文档。
- 待人工确认：省市归属和城市等级字段口径、三参数 `date_add` 平台兼容性、`call_c` 未带 `lead_id` join 的重复风险、`dd` 未带 `employee_email_name` join 的重复风险、临时表唯一性、`podan` 注释与代码不一致。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/data_center_market_2683_20260705.sql`；历史 SQL 原样归档，校验提示三参数 `date_add`、数值/字符串比较、部门过滤解析告警、派生别名 `channel_map/grade_1` 误报和 `select distinct` group by 解析告警，已在看板待确认事项中保留。
- 运行 `python scripts/check_skill_integrity.py`；结构自检通过，既有表文档含待人工确认项属预期。

## 2026-05-21 渠道 CASE 0515 来源更新

- 使用用户提供的 `D:\Feishu\0515.txt` 覆盖归档 `resources/raw_sql/market_channel_case_when_0515.sql`，确认文件 SHA256 与来源一致。
- 将最新渠道 CASE 归档文件从旧后缀 `market_channel_case_when_0508.sql` 修正为 `market_channel_case_when_0515.sql`，并同步更新知识库中的活跃引用。
- 更新 `knowledge/sql_patterns/channel_mapping_case_when.md`，将最新来源文件改为 `D:\Feishu\0515.txt`，记录来源文件最后修改时间 `2026-05-21 18:10:45`。
- 统计当前片段：198 行、197 个 `then` 分支、129 个去重渠道输出值；输出字段仍为 `qudao`。
- 在 `SKILL.md` 和渠道 CASE 知识文档中补充维护规则：后续更新最新渠道 CASE 时，归档 SQL 文件名后缀必须与来源文件日期后缀一致，例如 `D:\Feishu\MMDD.txt` 对应 `market_channel_case_when_MMDD.sql`。

## 2026-05-22 首 call 任务指标口径更新

- 将 `is_f_call`、首 call 任务数、首 call 任务率的默认口径更新为 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` 加 `finance_dw.dim_finance_employee_df.account_id` 桥接员工信息。
- 明确新 SQL 禁止使用 `service_dw.app_h_crm_lead_task_process_info_detail_hf.call_answer_lead_count` 作为首 call 任务来源；该旧过程表仅保留双表发送/回收、任务过程和电话接通等非首 call 任务用途。
- 新增 `knowledge/sql_patterns/first_call_task_metric_pattern.md`，沉淀首 call 任务标准 CTE、join key、部门范围、前端聚合方式和待确认口径。
- 更新 `knowledge/01_table_index.md`、`knowledge/metrics/outbound_call_process_metrics.md`、`knowledge/dashboards/outbound_call_process_dashboard.md`、`knowledge/joins/table_relationships.md` 以及两张相关表文档，确保后续生成新 SQL 默认走首 call 任务表 + 员工维表口径。

## 2026-05-22 渠道 CASE 0522 版本更新

- 使用用户提供的 `D:\Feishu\0522.txt` 新增归档 `resources/raw_sql/market_channel_case_when_0522.sql`。
- 相比 `market_channel_case_when_0515.sql` 的变更：
  - **新增**：`when flow_pool_name like '%星义大大%' then '赵星义'` 渠道规则（1 条）。
  - **修改**：「进校私域合作」（`third_department_name = '私域运营部'` 分支）的 `source_manager_name` 名单追加 `'王绍阳'`。
  - **移位**：「信息流-抖音私信」（`channel_name_1='信息流' and put_plan_name like ...`）从原第 72 位移至倒数第 3 位（`途途私域` 之前），CASE WHEN 优先级大幅降低。此规则在 0515 版本位于 `APP` 规则之前，0522 版本移至近末尾，可能影响同时命中 `APP` 和其他条件的记录的渠道归类。
- 当前片段：199 行、198 个 `then` 分支、130 个去重渠道输出值；输出字段仍为 `qudao`。
- 注意：`0522.txt` 首部新增的 `qici`（当期/非当期）和 `xiansuo`（0/1）CASE WHEN 块已在后续“市场顾问转化看板 0522 口径更新”中落入转化看板。

## 2026-05-22 市场顾问转化看板 0522 口径更新

- 根据用户指定的 `D:\Feishu\0522.txt` 更新 `resources/raw_sql/market_consultant_conversion.sql`；当前 raw_sql 目录中该文件缺失，本次按既有看板结构重新落回完整 SQL。
- 将 `0522.txt` 中输出别名为 `qici` 的当期/非当期 CASE 落到转化看板历史字段 `d_w`，并按表字段类型将 `assign_lead_count`、`valid_lead_count`、`merge_valid_lead_count` 的 `'1'` 比较改为数字 `1`。
- 新增 `xiansuo` 底层 0/1 标记，并在 `zhuanhua` CTE 中以 `sum(xiansuo) as xiansuo` 聚合后通过最终 `zz.*` 输出；未把 `xiansuo` 放入 group by，避免拆分既有维度。
- 渠道映射使用 `resources/raw_sql/market_channel_case_when_0522.sql`，仅将片段输出别名从 `qudao` 改为转化看板使用的 `channel_map`。
- 将期次计算中的三参数 `date_add` 改为 `interval` 写法，将最终 `sx_qi` 中的 `substring_index` 改为 Presto `split_part`，并将 `nvl` 改为 `coalesce`。
- 更新 `knowledge/dashboards/market_consultant_conversion.md`、`knowledge/metrics/market_consultant_conversion_metrics.md` 和 `knowledge/sql_patterns/channel_mapping_case_when.md`，同步 `xiansuo`、`pp_pmit`、`ww_pmit`、0522 渠道 CASE 和最终期次过滤口径。

## 2026-05-24 市场顾问转化看板 0524 口径更新

- 使用用户提供的最新 SQL 覆盖 `resources/raw_sql/market_consultant_conversion.sql`，来源为 `D:\Feishu\0524.txt`。
- 渠道 CASE 同步更新到 `resources/raw_sql/market_channel_case_when_0524.sql`，201 行、200 个 `then` 分支、132 个去重渠道输出值。
- 相比 0522 的渠道 CASE 变更：
  - **新增** `周帅-百度数字人`：`when third_department_name = '直播部' and sku_id_name like '%周帅%' and channel_name_2 in ('百度','B站') then '周帅-百度数字人'`。
  - **新增** `途途私域`：`when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') then '途途私域'`。
  - **修改** `B站信息流-亚飞`：条件追加 `or rule_name like '%亚飞%' or page_id_name like '%初中-0元%'`。
- 转化看板 SQL 结构变更：
  - `zhuanhua` CTE 的 `group by` 新增 `rule_name`，输出粒度从渠道级别细化到规则级别。
  - `data` CTE 新增字段 `merge_assign_lead_count`、`merge_valid_lead_count`、`lead_period_income_amount`、`lead_period_refund_amount`。
  - `lead_count` 和 `can_renew_ds_count_a` 对抖音私域使用合并字段口径。
  - 新增 `sx_qi` 字段，从 `rule_name` 中用 `split_part` 提取筛选期次标签。
  - 新增 `jingli_1` 字段，从 `temp_table.dingxi01_jiagou_zx.jingli` 补充经理维度。
  - `cost` join 条件从 `ct.grade = zz.grade_1` 放宽为 `(ct.grade = zz.grade_1 or ct.grade = '0')`，年级无匹配时回退到通配 `'0'`。
  - 最终期次过滤更新为 `zz.period_name > '20260424期'`。
- 更新 `knowledge/dashboards/market_consultant_conversion.md`、`knowledge/sql_patterns/channel_mapping_case_when.md`，同步 0524 版本号、CASE 变更、新增字段和粒度变化。
- 待确认：`rule_name` 加入 `group by` 后导致输出行数增加，前端看板是否需要同步调整聚合逻辑；`jingli_1` 与既有 `jingli` 字段是否含义一致；成本表 `grade = '0'` 通配逻辑是否覆盖所有未匹配年级。

## 2026-05-24 H业务线二级部门转化看板 SQL 入库

- 新增原始 SQL：`resources/raw_sql/h_biz_line_department_conversion.sql`，来源为平台数据集最新查询，用于查询整个 H业务线二级部门的转化数据。
- 新增看板文档：`knowledge/dashboards/h_biz_line_department_conversion.md`。
- 新增指标集合：`knowledge/metrics/h_biz_line_department_conversion_metrics.md`。
- 看板特点：
  - 覆盖四个二级部门：`section_assign_employee_second_level_department_name in ('市场部','精品班学部','青橙项目部','菁英班学部')`，虚拟三级部门限制 `学习顾问部/市场顾问部/中价产品项目部`。
  - 聚合粒度为**部门级别**（`depart_1 + dept_name + depart`），无顾问个体维度（不含 `employee_email_name` / `jingli` / `zhuguan`）。
  - 主表 `dt/hour` 均使用 `now - 3h`（一致偏移），与市场顾问转化看板的 `2h/3h` 偏移不同。
  - 期次映射一级部门允许 `null`（`period_mapping_first_level_department_name = 'H业务线' or is null`）。
  - 首 call 任务使用 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` → `finance_dw.dim_finance_employee_df` 桥接模式，与 2026-05-22 强制口径一致；但首 call 表未限定 `task_generate_rule_type = 2`。
  - 渠道分组使用 `temp_table.shenbaoxin_channel_group`（而非市场顾问转化看板的 `dingxi01_channel_group`）。
  - 不含 `d_w`（当期/非当期）、`xiansuo`、`pp_pmit`/`ww_pmit`、`merge_*`、`sx_qi`、`jingli_1` 等市场顾问转化看板独有字段。
  - 使用 `nvl` 做空值处理（Hive 兼容，Presto 标准版为 `coalesce`）。
- CTE 结构：`data_base`（`select t1.*`）→ `data` → `first_call_task` + `employee_map` + `f_call0` → `data_with_process` → `zhuanhua` → final select。
- 更新 `knowledge/dashboards/README.md`、`knowledge/metrics/README.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`、`knowledge/03_range_limit_rules.md`。
- 更新 `temp_table.shenbaoxin_channel_group` 表文档，补充该看板的使用场景。
- 待确认：`data_base` 使用 `select t1.*`、双层 `select distinct`、首 call 未限定 `task_generate_rule_type = 2`、`valid_lead_count`/`can_renew_ds_count_a` 重复输出为同一聚合、员工维表 `account_id` 去重逻辑（取字典序第一个 `employee_email_name`）、`channel_group` 字段是否真实存在、`period_mapping_first_level_department_name is null` 放宽条件、渠道 CASE 同层引用 `period_name` 是否可解析。

## 2026-05-24 顾问销售评优-自然月份排名 SQL 覆盖更新

- 使用平台数据集最新查询覆盖 `resources/raw_sql/consultant_sales_ranking_evaluation_month_clean.sql`，SQL 标题含 `-- 更新时间：2026-05-24`。
- 该变体与主 `consultant_sales_ranking_evaluation.sql` 的核心差异：
  - **聚合周期**：按自然月份聚合（多期次合并为一个自然月），而非按期次/月/季/半年分层。
  - **顾问名单来源**：使用 `temp_table.dingxi01_jiagou_zx`（`zaizhi='1'`，郑州/西安部门优先级去重），而非 `temp_table.dingxi01_pingyou_jg`。
  - **组织链过滤**：新增 `dw.dim_employee_chain` 取 `高途-H业务线-市场部-市场顾问部` 路径，按 `email_prefix` 内连接任职期间流水（`org_t.begin_time <= trade_time <= org_t.end_time`）。
  - **自然月派生**：统一 `day_of_week` 公式推导 `trade_qici`（无硬编码特殊日期）；`20260731期` 特殊映射为自然月 `202608`。
  - **转化侧完整链路**：包含 `conversion_base` → `conversion_data` → `conversion_by_channel` → `conversion_with_target` → `conversion_agg` → `conversion_metric_base` 全链路，补充线索、转化、成本目标、目标完成率和拓科率指标。
  - **渠道 CASE**：完整 200 分支 CASE，但版本为 pre-0524（不含 王绍阳/途途私域/周帅-百度数字人，信息流-抖音私信 位于旧位置 APP 之前）。
  - **成本维度**：`temp_table.dingxi01_cost` 按 `trim(channel)` 取 `try_cast(cost as double) > 0` 的 `max(cost)`，计算 `receive_target = leads_count * cost`。
  - **双排名体系**：pmit 排名 + 目标完成率排名，各带 lag 差值。
  - **新增指标**：`natural_month`、`qici_list`、`target_completion_rate`、`target_completion_period_dept_rank_no`、`target_completion_need_rate_to_previous`、`receive_target`、`tuoke_rate`。
- 更新 `knowledge/dashboards/consultant_sales_ranking_evaluation.md`，新增 §12 变体 SQL 章节，记录 CTE 结构、差异指标和待确认事项。
- 待确认：channel_map 版本未同步 0524、`period_mapping_* is null` 放宽条件、`conversion_base` 使用 `select fl.*`、`temp_table.dingxi01_cost` 中 `cost` 字段为字符串需 `try_cast`、`jiagou_zx_active` 部门优先级去重逻辑、`20260731期 → 202608` 硬编码、`day_of_week` 期次公式与业务周五对齐口径。

## 2026-05-28 转化与过程看板前端展示公式补充

- 根据用户确认截图和本地数据集校验结果，更新 `knowledge/metrics/market_consultant_conversion_metrics.md` 与 `knowledge/dashboards/market_consultant_conversion.md`，补充前端展示派生公式：人头转化率、订单转化率、单效、破蛋率、拓科率、退费率、mroi、smroi、gmv完成度、人产。
- 明确 `cb_cb` 为单例子成本、`gl_gl` 为单例子目标，mroi 使用 `trade_profit / (lead_count * cb_cb)`，gmv完成度使用 `trade_profit / (lead_count * gl_gl)`。
- 明确 smroi 公式为 `trade_profit / (lead_count * cb_cb + 人力成本)`，但当前数据集未维护人力成本字段。
- 更新 `knowledge/metrics/outbound_call_process_metrics.md` 与 `knowledge/dashboards/outbound_call_process_dashboard.md`，补充过程看板派生公式：6h/12h/24h外呼率、外呼频次、首call率、5min比例、深沟率、双沟率、好友率、40min占比、40min转化率。
- 明确 5min比例使用 `is_long_call / valid_lead_count`，不要误用 `first_call_in_5min`；40min占比/转化率依赖转化数据侧补充 `is_40m_call`、`call_40m_z` 字段，当前外呼过程 SQL 和过程数据集未直接输出。

## 2026-05-28 查询平台权限解析误拦截规则补充

- 更新 `knowledge/sql_patterns/dashboard_query_patterns.md`，新增“调试字符串与权限解析误拦截”规则。
- 明确排查 SQL 中不要使用 `concat('jingli=', coalesce(jingli, '<null>'))`、`concat('zhuguan=', ...)` 等 `字段名=字段值` 字符串拼接，避免查询平台权限解析器误判为无权限 SQL。
- 建议排查字段拆成独立列输出，例如 `coalesce(cast(jingli as varchar), '空值') as sample_jingli`，并使用中文空值占位替代 `'<null>'`。

## 2026-05-28 多检查项排查 SQL stage 超限规则补充

- 根据查询平台报错 `Number of stages in the query exceeds the allowed maximum`，更新 `knowledge/sql_patterns/dashboard_query_patterns.md`，新增“多检查项排查 SQL 的执行计划控制”规则。
- 明确不要在多个 `union all` 分支中反复引用重 CTE；应先计算 `flag_*` 字段，再用 `cross join unnest` 将检查项转成长表。
- 补充减少多个 `distinct` 聚合的建议，优先用 `min(path) <> max(path)` 判断多架构。

## 2026-05-29 顾问销售评优季度/半年度离职顾问过滤

- 更新 `resources/raw_sql/consultant_sales_ranking_evaluation_quarter_clean.sql` 与 `resources/raw_sql/consultant_sales_ranking_evaluation_year_clean.sql`。
- 在季度和半年度 clean 脚本中新增 `jiagou_zx_active` CTE，从 `temp_table.dingxi01_jiagou_zx` 取 `cast(zaizhi as varchar) = '1'` 且部门为 `郑州顾问部`、`西安一部`、`西安二部` 的当前在职顾问，并按 `employee_email_name` 去重。
- 在 `process` CTE 中增加 `inner join jiagou_zx_active`，保留原 `temp_table.dingxi01_pingyou_jg` 参评口径的同时，额外剔除当前已离职顾问，避免跨季度/半年度聚合把历史期次曾在职顾问带入看板。
- 将两处三参 `date_add('day', ...)` 改为等价 `interval` 日期偏移写法，规避查询平台按 Hive 两参函数解析导致的校验风险。
- 更新 `knowledge/dashboards/consultant_sales_ranking_evaluation.md`，补充季度/半年度 clean 脚本的当前在职过滤口径。

## 2026-05-31 全链路主表最新分区产出排查模板

- 更新 `knowledge/sql_patterns/dashboard_query_patterns.md`，在“结果缺失与未来期次排查”中新增 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 最新分区产出排查模板。
- 明确当涉及 join 该主表的看板整体查不到数据、结果集为空或核心指标突然大面积为 0 时，应优先按 `dt/hour` 汇总最近分区行数和 `lead_count`，判断最近 2-3 小时是否无数据产出。
- 模板中的 `dt >= '<排查起始日期YYYYMMDD>'` 必须按用户提问当天或排查当天动态替换，通常取当天或往前 1 天，跨零点或怀疑延迟时扩大到最近 2 天；不得固定沿用历史日期。
- 更新 `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`，在主表历史备注中增加该排查模板入口。

## 2026-05-31 删除 USQL RestAPI 调用路径

- **删除** `knowledge/sql_patterns/usql_rest_api_python.md`：USQL RestAPI Python 调用规则文档。
- **删除** `knowledge/sql_patterns/usql_permission_boundaries.md`：USQL RestAPI 权限边界探查记录。
- **原因**：查询执行路径已完全迁移至 Playwright Web 自动化（`usql-web-query-operator` Skill），Web 路径覆盖所有表的完整用户权限，不再需要 RestAPI 路径。RestAPI 权限覆盖率仅 27 张表中 13 张可读，关键表无法使用，不具备作为备选路径的价值。
- **关联变更**：
  - `SKILL.md`：§0、§3.B 不再引用 RestAPI 文档。
  - `knowledge/sql_patterns/web_query_playwright.md`：移除 RestAPI 对比章节。
  - `knowledge/sql_patterns/web_permission_guide.md`：简化为纯 Web 权限指南。
  - `knowledge/quick_reference.md`、`knowledge/decision_tree.md`：移除 RestAPI 入口。
  - `knowledge/01_table_index.md`：移除 `USQL状态` 列。
  - 所有表文档：移除 USQL RestAPI 备注。
  - `scripts/check_skill_integrity.py`：移除 USQL 列强制检查。

## 2026-06-01 自助 BI 看板结构快照入库

- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-folder` 逐个打开 `市场顾问数据` 文件夹下 7 个重点看板，并等待页面刷新后抽取 Web BI 结构。
- 新增 `knowledge/dashboard_web_profiles/`，保存自助 BI 页面结构摘要：dashboard_id、打开入口、全局筛选器、组件单元、字段 ID、指标/序列名、刷新 task_id、行数/序列计数。
- 已入库看板：外呼过程数据看板、市场顾问部_行课报表、运营侧数据看板、转化数据、市场顾问-进量节奏、市场顾问--评优看板、昆仑山战役-暑期激励数据看板。
- 更新 `knowledge/dashboards/README.md`、`knowledge/quick_reference.md`、`knowledge/decision_tree.md`，将“页面筛选器/字段 ID/组件结构”路由到 `knowledge/dashboard_web_profiles/README.md` 和对应快照。
- 结构快照只保存字段和刷新元数据，不保存返回结果明细行；业务口径仍以 `knowledge/dashboards/*.md` 与 `knowledge/metrics/*.md` 为准。

## 2026-06-05 渠道 CASE 顺序抢先命中规则补充

- 更新 `knowledge/sql_patterns/channel_mapping_case_when.md`，新增“超长 CASE 顺序风险”，明确维护 `channel_map` / `channel_map_1` / `qudao` 时，特异规则必须先于宽泛规则。
- 更新 `knowledge/pitfalls/common_join_failures.md`，新增“daoke 表有渠道，但看板渠道消失”排查项：当临时到课表已维护渠道但看板缺失时，优先模拟现有 CASE 输出，检查是否被前序分支归到相邻渠道。
- 更新 `knowledge/decision_tree.md`，将“某渠道某期次消失”和到课指标异常路由到渠道 CASE 顺序排查。
- 已验证案例：`0529期/0605期-孟亚飞ip99元-孟亚飞ip99元-*` 被前序 `孟亚飞9元` 宽泛规则抢先命中；修复应将 `when lower(f.rule_name) like '%孟亚飞ip99%' then '孟亚飞IP99元'` 放在 `孟亚飞9元` 宽泛规则之前。

## 2026-06-05 市场顾问线索转化到课 raw SQL 覆盖

- 使用用户提供的最新到课 SQL 覆盖 `resources/raw_sql/market_consultant_lead_conversion_attendance.sql`。
- 同步更新 `knowledge/dashboards/market_consultant_lead_conversion_attendance.md` 和 `knowledge/metrics/market_consultant_lead_conversion_attendance_metrics.md`，将旧版“转化 + GMV + 成本目标 + 首节到课”口径改为“有效线索 + 第 1-6 节到课 + 第 1-6 节有效到课”口径。
- 更新 `knowledge/joins/table_relationships.md`，明确当前到课映射使用 `qici + channel_map_1 + grade_1 + begin_time` 关联 `temp_table.dingxi01_daoke_1_6_t`，且渠道字段使用 `qudao` 而不是 `channel`。
- 更新 `knowledge/01_table_index.md` 和 `knowledge/tables/temp_table.shenbaoxin_channel_group.md`，说明最新到课 raw SQL 已不再 join `temp_table.shenbaoxin_channel_group`。
- 记录渠道 CASE 顺序风险：`孟亚飞IP99元` 等特例必须放在泛化的 `孟亚飞9元`、`信息流` 等规则之前；后续排查“某渠道从某期开始消失”应优先检查 rule_name 变化和 CASE 顺序。

## 2026-06-05 外呼过程期次导出模板补充

- 新增 `knowledge/sql_patterns/outbound_call_process_export_template.md`，保存用户提供的外呼过程查询为模板取数格式，不覆盖 `resources/raw_sql/outbound_call_process_dashboard.sql`。
- 增加 `${period_name1}`、`${period_name2}` 参数，分别在 `jg_market` 架构 CTE 和 `prc` 线索宽表 CTE 中限制 `qici` 半开区间：`qici >= ${period_name1}` 且 `qici < ${period_name2}`。
- 更新 `knowledge/quick_reference.md`、`knowledge/decision_tree.md`、`knowledge/sql_patterns/dashboard_query_patterns.md`，将外呼过程期次导出和模板取数需求路由到该模板文档。

## 2026-06-06 市场渠道用户画像分析三数据集入库

- 新增三份原始 SQL：
  - `resources/raw_sql/data_center_market_2836_20260705.sql`
  - `resources/raw_sql/data_center_market_2885_20260705.sql`
  - `resources/raw_sql/data_center_market_2883_20260705.sql`
- 新增看板文档：`knowledge/dashboards/market_channel_conversion_profile.md`。
- 新增指标集合：`knowledge/metrics/market_channel_conversion_profile_metrics.md`。
- 更新 `knowledge/dashboards/README.md` 与 `knowledge/metrics/README.md`，补充市场渠道用户画像分析入口。
- 更新 `knowledge/joins/common_join_keys.md`，新增：
  - `period_name + lead_id + user_id`：首 call 通时字段独立聚合后回连分桶。
  - `period_name + user_id`：上课时长按用户期次汇总后回连分桶。
  - `user_number + lead_id`：私海阶段按用户线索取最新阶段。
- 更新 `knowledge/joins/table_relationships.md`，记录三数据集共同主表、范围限定、分桶逻辑、渠道组 join 和透视表指标使用风险。
- 更新 `knowledge/01_table_index.md` 与 `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`，补充该主表在市场渠道用户画像分析中的使用方式。
- 关键口径：
  - 三份数据集基础指标均来自 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`，分桶差异分别来自首 call 通时、上课时长和私海阶段。
  - 首 call 通时字段 `section_assign_all_call_duration` 单独在 `call_duration_raw` 中按 `period_name + lead_id + user_id` 取 `max` 后回连，不参与业务指标底表 `select distinct`。
  - 透视表总计必须使用 `sum(conversion_user_cnt) / sum(bucket_user_cnt)`、`sum(order_cnt) / sum(bucket_user_cnt)`、`sum(section_profit_amt) / sum(bucket_user_cnt)` 重算人头转化率、订单转化率和截面单效；不得直接聚合 SQL 行级 `head_conversion_rate`、`order_conversion_rate`、`section_unit_efficiency`。
- 待人工确认：`section_assign_all_call_duration` 取 `max` 是否代表最终总通时；`bucket_user_cnt` 用 `lead_count` 是否可称为人数；金额字段 `/100` 单位；`conversion_lead_count`/`order_count` 是否均为正价课口径；`period_mapping_second_level_department_name is null` 放宽条件；`temp_table.shenbaoxin_channel_group` 字段结构和唯一性。

## 2026-06-06 16:37 市场渠道用户画像整体数据集入库

- 新增原始 SQL：`resources/raw_sql/data_center_market_2809_20260705.sql`。
- 该 SQL 属于 `market_channel_conversion_profile` 市场渠道用户画像分析看板的整体画像数据集，不是独立看板；与首 call 通时、上课时长、深沟阶段三份分桶数据集共同服务同一看板。
- 更新 `knowledge/dashboards/market_channel_conversion_profile.md`，补充整体画像数据集的 CTE 结构、输出粒度、修复点和待人工确认事项。
- 更新 `knowledge/metrics/market_channel_conversion_profile_metrics.md`，补充整体画像字段口径和透视表建议公式。
- 更新 `knowledge/joins/common_join_keys.md`，记录整体画像 `src` 阶段使用 `period_name + lead_id + user_id` 防止多线索被 `select distinct` 折叠，并记录 `period_name + channel_map + grade_name + manager_name` 为整体画像最终聚合键；该聚合键不是跨表 join key。
- 更新 `knowledge/joins/table_relationships.md`，补充整体画像数据集仅使用全链路主表、不做外部 join，并记录有效线索数修复口径。
- 更新 `knowledge/01_table_index.md` 与 `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`，补充该主表在整体画像数据集中的使用方式。
- 关键修复：
  - 主表范围新增 `virtual_third_department_name = '市场顾问部'`，与三份分桶画像数据集保持一致。
  - 整体画像有效线索数使用标准 `valid_lead_count`，不再对 `抖音私域`/`抖音私信` 切换 `merge_valid_lead_count`。
  - `src` 阶段新增 `lead_id` 防止同一用户多线索被 `select distinct` 折叠；最终结果不输出 `lead_id`。
- 待人工确认：整体画像中 `pay_user_head_count` 与 `regular_course_user_count` 的业务区别；科目档位 `subject_*` 是否按用户层 `sum(subject_count)` 分层；整体画像有效线索是否所有组件都应禁用 merge 口径；金额 `/100` 单位；`manager_name` 来自 `virtual_leader_email_name` 是否为经理展示最终口径。

## 2026-06-07 市场渠道用户画像多维退费率数据集入库

- 新增原始 SQL：`resources/raw_sql/data_center_market_2890_20260705.sql`，来源 `c:\Users\Ludim\.codex\runtime\data_center_market_2890_20260705.sql`。
- 该 SQL 属于 `market_channel_conversion_profile` 市场渠道用户画像分析看板的多维退费率数据集，不是独立看板；用于输出当期/截面 GMV 退费率、人头退费率、1科/2-3科/3科以上退费率所需分子和分母字段。
- 更新 `knowledge/dashboards/market_channel_conversion_profile.md`，补充多维退费率数据集的来源、CTE、输出粒度、透视表公式和待人工确认事项。
- 将 `refund_multi_subject_user_ratio.md`、`refund_reason_analysis.md`、`refund_subject_product.md` 调整为历史合并入口，默认路由到市场渠道用户画像分析看板；旧 raw SQL 仅保留追溯。
- 更新 `knowledge/metrics/market_channel_conversion_profile_metrics.md` 与 `knowledge/metrics/refund_analysis_metrics.md`，将退费率口径维护到画像指标集合，旧退费指标集合标记为历史。
- 更新 `knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`、`knowledge/01_table_index.md` 和相关表文档，记录该数据集仅使用 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`，不再使用历史财务流水/退费原因/架构表 join。
- 新增通用规则：当 SQL 用于看板数据透视表且涉及比值指标时，优先输出英文分子和分母字段，透视表用 `sum(分子) / sum(分母)` 重算，不默认只输出行级比值。
- 待人工确认：金额字段 `/100` 单位、`subject_count` 是否代表最终购买科目数、单科/多科人头退费率分母是否应使用对应科目分层用户数、经理/主管/顾问字段最终展示口径。

## 2026-06-12 16:59:59

- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 扫描 `市场顾问数据` 文件夹，并将原始 `profile.json` 写入本地 runtime 目录。
- 刷新 `knowledge/dashboard_web_profiles/README.md`，当前索引 15 个看板快照。
- 本次 profile 结果：成功 15 个，失败 0 个。

## 2026-06-12 18:16:48 CRM 开课后转移状态记录边界补充

- 更新 `knowledge/pitfalls/common_join_failures.md`，新增“CRM 开课后转移/退费状态无法回写导致顾问仍有退前/退后线索”排查规则。
- 更新 `knowledge/sql_patterns/dashboard_query_patterns.md`，补充运营侧个人数据、退前/退后线索、顾问流量归属排查时的 CRM 状态记录边界。
- 更新 `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`，记录线索转移必须在当期开课前完成才会被数据库记录；开课后退费或转移顾问可能导致 CRM 当前状态与看板/数据集结果不一致。
- 待人工确认：是否存在可记录开课后转移顾问或退费后状态变化的独立明细表；未确认前不得直接用 SQL join 改写该业务事实。

## 2026-06-12 22:14:50 市场顾问渠道 CASE 0612 版本归档

- 使用用户提供的 `D:\Feishu\0612.txt` 新增归档 `resources/raw_sql/market_channel_case_when_0612.sql`，并在文件头记录来源和统计信息。
- 更新 `knowledge/sql_patterns/channel_mapping_case_when.md`，将最新渠道 CASE 来源从 0524 切换为 0612；排除注释后当前版本为 172 个 `then` 分支、107 个去重渠道输出值。
- 0612 相比 0524 新增/细分 `孟亚飞-1组-抖音`、`孟亚飞-1组-视频号`、`孟亚飞-1组-B站`、`孟亚飞-1组-百度`、`孟亚飞-2组-百度`、`孟亚飞-2组-抖音`、`B站信息流-曹忆`、`B站信息流-汤学健`、`B站信息流-亚飞(1元)`、`进校直推`、`信息流-陈瑞春` 等输出值。
- 同步更新 `knowledge/quick_reference.md`、`knowledge/decision_tree.md`、`knowledge/joins/table_relationships.md`、相关 dashboards/metrics/table/pattern 文档中的最新渠道 CASE 活跃引用；历史 changelog 和旧 raw SQL 保留追溯。

## 2026-06-15 知识反向索引最小改造

- 新增 `scripts/build_reverse_indexes.py`，自动生成 `knowledge/reverse_index/field_to_metrics.md`、`metric_to_raw_sql.md`、`table_to_dashboards.md` 和 `join_risk_index.md`。
- 更新 `SKILL.md`、`metadata.json` 和 `scripts/check_skill_integrity.py`，将反向索引纳入加载顺序、维护流程和结构自检。
- 本次只增加字段/表/指标/debug 的反向定位层，不改写既有市场顾问指标口径、表语义或 raw SQL。

## 2026-06-17 模板取数时间区间参数规则补充

- 新增 `knowledge/sql_patterns/template_parameter_rules.md`，记录平台模板取数日期/时间区间参数标准写法：`字段名 >= ${字段名:1} and 字段名 < ${字段名:2}`。
- 更新 `knowledge/00_global_rules.md`，将模板取数时间参数规则纳入全局时间口径规则。
- 更新 `knowledge/03_range_limit_rules.md` 顶部必读核心规则，强调参数名必须与过滤列名一致，不得使用 `begin_xxx` / `end_xxx`，不得在模板参数或过滤列外层添加 `cast()`、`date()`、`substr()` 等函数。
- 更新 `knowledge/quick_reference.md` 强制前置规则，增加模板取数参数规则入口。
- 验证要求：如需网页端验证，可单独生成实际日期字面量版本执行；交付或写入模板的 SQL 仍必须恢复为无 `cast` 的 `${字段名:1}` / `${字段名:2}` 参数格式。

## 2026-06-17 数据地图字段说明补全

- 登录 `https://tiangong2.baijia.com/dataMap/dataMapNew`，使用数据地图 `tableV2/searchTableList`、`normalColumns`、`partitionColumns` 和 `getDdl` 接口刷新市场顾问 Skill 物理表字段信息。
- 覆盖 `knowledge/tables` 中 19 张物理表文档；其中 3 张表新增 `数据地图字段补充（2026-06-17）` 小节，追加 40 个数据地图字段。
- 以数据地图和 DDL 为准回填字段类型和说明占位；复扫结果为字段缺口 0、类型占位 0、说明占位 0。
- 未覆盖 `temp_table.*` 临时表文档；临时表字段仍以本地 Excel、SQL 使用场景和人工维护规则为准。

## 2026-06-17 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：市场顾问部目录下从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- 保存 37 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_market_datasets.md`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-06-17 数据中心源 SQL 对比与 canonical raw_sql 更新

- 将市场顾问部数据中心中已确认同源的 20 份源 SQL 映射并覆盖到现有 canonical raw_sql，包括外呼过程、到课衰减、转化、进量节奏、评优、退费和画像类数据集。
- 当时保留未能确认同源的数据中心 SQL 为 20260617 快照，不强行覆盖既有知识库口径；2026-06-24 刷新后旧快照已按最新数据中心 SQL 去重替换。
- 更新 `knowledge/dashboards/data_center_market_datasets.md`，记录每份数据中心 SQL 的用途、主要依赖和冲突处理原则。

## 2026-06-17 运营侧个人数据 2293 架构展示修正

- 使用 runtime 修正版覆盖当日的 2293 运营侧个人数据快照；该架构修正后续已由 `resources/raw_sql/data_center_market_2293_20260624.sql` 继承，旧快照去重删除。
- 修正原因：原最终层 `select zz.*` 会把事实宽表 `zz.jingli` / `zz.zhuguan` 原样输出；BI 透视表绑定 `jingli` 时会使用事实宽表 `virtual_leader_email_name`，导致顾问展示在旧经理或旧主管下。
- 修正逻辑：新增 `zx_active` 对 `temp_table.dingxi01_jiagou_zx` 做在职和部门过滤并按 `employee_email_name` 去重；最终层显式输出 `jingli`、`zhuguan`、`xiaozu`、`jingli_11`，优先级为 `temp_table.dingxi01_jiagou_db` 期次架构 > `temp_table.dingxi01_jiagou_zx` 当前在职架构 > 事实宽表 `virtual_*` 字段。
- 更新 `knowledge/dashboards/data_center_market_datasets.md`、`knowledge/tables/temp_table.dingxi01_jiagou_db.md`、`knowledge/tables/temp_table.dingxi01_jiagou_zx.md`、`knowledge/pitfalls/common_join_failures.md`、`knowledge/sql_patterns/dashboard_query_patterns.md`，记录 2293 同类架构错位的排查路径和修复模板。

## 2026-06-18 市场顾问渠道 CASE 孟亚飞视频号合并

- 按业务反馈修正 `resources/raw_sql/market_channel_case_when_0612.sql`：孟亚飞 1 组且 `channel_name_2 = '视频号'` 的分支不再输出 `孟亚飞-1组-视频号`，统一输出 `孟亚飞9元`。
- 更新 `knowledge/sql_patterns/channel_mapping_case_when.md`，记录 `孟亚飞-1组-视频号` 与 `孟亚飞9元` 为同一渠道，后续看板不应再把 `孟亚飞-1组-视频号` 作为独立展示渠道。
- 注意：已复制 0612 CASE 的数据集 SQL 需要单独同步该分支输出，否则不会自动继承独立 CASE 片段的修正。

## 2026-06-18 到课数据查询最新 SQL 覆盖

- 使用用户提供的粘贴 SQL 覆盖 `resources/raw_sql/market_consultant_lead_conversion_attendance.sql`，作为到课数据查询最新 canonical 代码。
- 与 2026-06-17 数据中心版本相比，SQL 内容差异为孟亚飞 1 组视频号分支从 `孟亚飞-1组-视频号` 合并为 `孟亚飞9元`；到课 CTE、自动/手工课次指标和输出粒度保持一致。
- 同步更新 `knowledge/dashboards/market_consultant_lead_conversion_attendance.md`、`knowledge/metrics/market_consultant_lead_conversion_attendance_metrics.md`、`knowledge/joins/table_relationships.md`、`knowledge/joins/common_join_keys.md`、`knowledge/tables/temp_table.dingxi01_daoke_1_6_t.md` 和 `knowledge/dashboards/data_center_market_datasets.md`，明确最终输出包含自动课次 `ke_*` / `v_ke_*`、手工课次 `manual_*` / `manual_v_*` 以及自动/手工课次对照计数。

## 2026-06-19 市场顾问部模板取数源 SQL 同步

- 使用 `usql-web-query-operator` 的 `fetch-template-sql` 命令从模板取数页面抓取 8 个已发布模板的最新 `sqlDetail`：多科用户成单、分周期转化、每天转化、转化、过程、到课、员工架构和进量数据。
- 新增 8 份 `template_query_market_` 前缀的模板取数 raw SQL，完整保存平台模板 SQL 原文，不改写 SQL 语义，不覆盖现有 canonical 看板或数据中心 SQL。
- 新增 `knowledge/dashboards/template_query_market_datasets.md`，记录模板 id、更新时间、raw SQL 路径、主要依赖表、模板参数和用途，并统一标记使用口径为“模板取数”。
- 更新 `knowledge/quick_reference.md` 与 `knowledge/decision_tree.md`，后续用户明确提到模板取数最新代码或 AI 分析市场顾问部模板时优先路由到模板取数清单，回答时必须说明口径来源。

## 2026-06-24 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：市场顾问部目录下从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- 保存 38 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_market_datasets.md`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-06-24 19:26:35

- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 扫描 `市场顾问数据` 文件夹，并将原始 `profile.json` 写入本地 runtime 目录。
- 刷新 `knowledge/dashboard_web_profiles/README.md`，当前索引 17 个看板快照。
- 本次 profile 结果：成功 17 个，失败 0 个。

## 2026-06-24 市场顾问看板指标公式与数据集 SQL 联动

- 使用 `read_dashboard.py profile-edit-dashboard` 读取 `市场顾问数据` 文件夹下 16 个 dashboard 看板的编辑页配置，补充 `knowledge/dashboard_web_profiles/edit_metrics/`。
- 新增 `knowledge/metrics/market_consultant_dashboard_metric_formula_linkage.md`，按看板、透视表、`model_id`、前端指标公式和唯一数据中心 raw SQL 建立联动关系。
- 与 2026-06-24 数据中心同步结果对齐，联动文档默认指向 `resources/raw_sql/data_center_market_*_20260624.sql`；文本播报看板保留为 text-only，不强行绑定 SQL。
- 更新 `knowledge/quick_reference.md`、`knowledge/decision_tree.md`、`knowledge/metrics/README.md` 和 `knowledge/dashboard_web_profiles/README.md`，后续排查看板指标含义或公式时优先从联动索引进入。
- 完成 raw SQL 去重：删除 17 个 20260617 数据中心旧快照；对 14 个与 canonical SQL 完全一致的 20260624 数据中心副本，改由清单和联动文档指向 canonical 文件后删除副本；另将 2 个与数据中心/canonical 完全一致的模板取数 raw SQL 改为清单指向唯一 SQL 文件后删除副本。

## 2026-06-28 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：市场顾问部目录下从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- 保存 1 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_market_datasets.md`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-06-29 raw SQL 最新口径清理

- 删除已被最新版本替代的旧 raw SQL：`data_center_market_2132_20260624.sql`、`data_center_market_2253_20260624.sql`、`data_center_market_2293_20260624.sql`、`market_channel_case_when_0515.sql`、`market_channel_case_when_0522.sql`、`market_channel_case_when_0524.sql`、`market_consultant_conversion.sql`。
- 保留对应最新口径入口：`data_center_market_2132_20260705.sql`、`data_center_market_2253_20260628.sql`、`data_center_market_2293_20260628.sql`、`market_channel_case_when_0612.sql`。
- 将活跃知识库引用从旧文件迁移到最新 raw SQL，并重新生成反向索引。

## 2026-06-30 市场顾问到课 SQL 自动课次优化

- 使用网页端 Presto 已验证版本覆盖 `resources/raw_sql/market_consultant_lead_conversion_attendance.sql`，作为市场顾问到课 canonical raw SQL。
- 新口径不再把手工课次表或课程名称作为主课次来源；先以 `data` 中的 `qici + channel_map_1 + grade_1` 为准圈定用户行课候选，再按实际 `begin_time` 在同一期次、渠道、年级内自动排序生成课 1-课 6。
- 保留原看板最终输出字段，不在 SQL 中输出到课率或有效到课率；比例继续由看板用 `sum(ke_n) / sum(lead)`、`sum(v_ke_n) / sum(lead)` 计算。
- 清理知识库中旧的 `lesson_index` / `lesson_index_add` / 班级内顺序驱动主课次描述，更新到课看板、指标、join、临时课次表和常见 join 失败排查说明。
- `template_query_market_attendance_20260619.sql` 仍作为模板取数原文保留，不作为最新 canonical；模板清单已标注 2026-06-30 后 canonical 以 `market_consultant_lead_conversion_attendance.sql` 为准。

## 2026-07-02 市场顾问年级 `rule_name` 主留痕边界补充

- 更新 `knowledge/pitfalls/grade_extraction_gotchas.md`，明确业财宽表 `rule_name` 只记录主留痕分配规则，不等同于 CRM 当前页面可见的所有分配规则。
- 更新 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 表文档中 `rule_name` 字段说明：线索进量后经调课调班或后续流转才产生的分配规则可能不回写该字段。
- 更新市场顾问转化和 H业务线二级部门转化看板文档，记录当宽表 `rule_name` 缺失时，年级会回退到 `lead_purchase_intention_level2_category_name`；如需按 CRM 当前规则修正，应额外对比规则明细表和线索统计留痕表。

## 2026-07-02 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：市场顾问部目录下从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- 保存 1 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_market_datasets.md`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-07-02 评优临时表 `is_emp` 字段含义确认

- 明确 `temp_table.dingxi01_pingyou_jg.is_emp` 的业务含义为“是否参与评优”：`是` 表示参与，`否` 表示不参与。
- 更新评优临时表、顾问销售评优看板、评优指标和临时表 join 关系文档，避免将 `is_emp` 误解为是否在职；在职状态仍由 `zaizhi` 表示。

## 2026-07-03 评优临时表上传人变更

- 评优架构人产临时表后续由 `zhangjunyan01` 维护上传，评优看板相关 SQL 表名从 `temp_table.dingxi01_pingyou_jg` 调整为 `temp_table.zhangjunyan01_pingyou_jg`。
- 更新评优看板期次、月度、季度、半年度相关 raw SQL，以及表文档、看板文档、指标文档、join 文档和 SQL 生成入口说明。

## 2026-07-03 运营侧个人数据 2293 JOIN 放大修复

- 新增 `resources/raw_sql/data_center_market_2293_20260703.sql`，使用本次排查后的修正版作为 2293 运营侧个人数据最新 raw SQL。
- 修复点：`call_c` 回连主数据时补充 `lead_id`；`f_call0` 先按 `user_id + employee_email_name` 聚合；`dingxi01_cost` 拆为具体年级与 `grade='0'` 通配两路去重；`dingxi01_jiagou_db` 先按 `qici + department + employee_email_name` 去重后再 join。
- 更新 2293 相关看板指标联动、编辑页模型引用、临时架构表说明和 JOIN 踩坑文档，明确运营侧个人数据中 `lead_count`、`can_renew_ds_count_a`、收款和退款字段会被最终层 1:N join 同步放大。

## 2026-07-04 评优看板起始期次修正

- 核查 `temp_table.dingxi01_pingyou_jg` 已维护的 2026 年最早期次为 `20260101期`，不是 `20260102期`。
- 将评优看板期次、月度、季度、半年度相关 raw SQL 和口径文档中的起始过滤从 `20260320期` 统一调整为 `20260101期`，避免遗漏 2026 年 1-3 月已维护评优期次。

## 2026-07-04 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：市场顾问部目录下从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- 保存 2 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_market_datasets.md`。
- 当前最新入口为 `data_center_market_2253_20260705.sql` 和 `data_center_market_2293_20260705.sql`；活跃知识库引用已统一迁移到 20260704 版本。
- 删除旧 raw SQL 快照：`data_center_market_2253_20260628.sql`、`data_center_market_2293_20260628.sql`、`data_center_market_2293_20260703.sql`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-07-04 退费_科目_产品 2349 退款金额占比口径更新

- 将 `resources/raw_sql/data_center_market_2349_20260705.sql` 设为数据中心 2349「退费_科目_产品」当前知识库入口。
- 当时 2349 输出 `analysis_type`、`dim_value`、`refund_amount`、`total_refund_amount` 和 SQL 行级占比字段；该行级占比字段已在后续 2026-07-05 口径中废弃。
- 废弃旧 `refund_total` 负数输出和前端隐式占比口径；旧 `data_center_market_2349_20260705.sql` 仅保留为历史归档。
- 更新市场渠道用户画像、退费科目产品、退费指标、表关系、范围规则和相关表文档，后续排查不同科目/产品/年级退费占比优先读取 2349 数据中心 SQL。

## 2026-07-04 评优看板半年度归属逻辑修正

- 将半年度评优 SQL 中 `half_year` 归属从评优周期口径（4-9 月为上半年、10-次年 3 月为下半年）改为自然半年口径（1-6 月为上半年、7-12 月为下半年）。
- 同步更新用户粘贴 SQL、顾问销售评优看板文档和评优指标文档，保证出勤率分母按自然半年统计。

## 2026-07-05 市场顾问-用户画像分析看板画像刷新

- 使用 `usql-web-query-operator/scripts/read_dashboard.py profile-dashboard` 重新采集 `dashboard_3804681042591760385` 运行态 Web BI 结构，刷新 `knowledge/dashboard_web_profiles/market_consultant_user_profile_analysis_web_profile.md`。
- 使用 `profile-edit-dashboard` 重新采集 Taitan 编辑态指标配置，当前加载草稿 `html_3975684262305193985`，刷新 `knowledge/dashboard_web_profiles/edit_metrics/dashboard_3804681042591760385_edit_metrics.md`。
- 删除旧 2026-06-24 快照口径在该看板画像中的主入口，当前记录为 28 个运行态组件、8 个编辑态透视单元、99 个配置字段、52 个自定义公式。
- 更新 `knowledge/metrics/market_consultant_dashboard_metric_formula_linkage.md`：该看板当前映射 11 个模型，其中透视单元为 `2683/2809/2812/2836/2885/2883/2344/2890`，运行态图表/指标卡另含 `2349/2886/2353`。

## 2026-07-05 2344 分析--分周期转化截面净收款口径修正

- 将已验证的 2344 修正版 SQL 入库为 `resources/raw_sql/data_center_market_2344_20260705.sql`，删除旧入口 `resources/raw_sql/data_center_market_2344_20260624.sql`。
- 修正 `gmv_total` 最终输出口径：不再使用财务流水 `bucket_agg.sum(name_total_price)`，改为 `metric_agg.metric_gmv_total = sum(trade_profit)`，与转化看板 2253 和运营侧 2293 的截面净收款口径对齐。
- 退款分周期字段继续使用财务流水金额口径，`refund_total/refund_7/refund_14/refund_30/refund_n30/refund_7_p` 由 `name_total_price < 0` 的金额按 `week_diff` 分桶生成。
- 更新 2344 相关编辑页指标映射和 `market_consultant_dashboard_metric_formula_linkage.md`，旧 20260624 SQL 不再作为当前知识库入口。

## 2026-07-05 2344 分析--分周期转化退款分桶归期修正

- 排查发现此前 2344 修正版把 `bucket_agg` 输出期次从原始 `qici` 改成 `coalesce(friday_period, qici)`，并过滤 `friday_period is not null`，导致退款按规则期次重归属且总退款分母变窄，20260703 当期退款占比从原始约 37% 抬升到约 79%。
- 修正 `resources/raw_sql/data_center_market_2344_20260705.sql`：退款分桶恢复按财务交易期次 `b.qici` 聚合；`refund_total/refund_7/refund_14/refund_30/refund_n30/refund_7_p` 恢复保留负数金额；未匹配或不可解析的 `friday_period` 不再剔除，统一落入 `week_diff = 3` / 非30天桶。
- 验证 SQL：`runtime/tmp/validate_2344_refund_bucket_20260705_limit.sql`，USQL query_id=`1449456595`。验证结果：20260703 当期退款占比 37.54%、五个分桶合计占比 100.00%；20260626 当期退款占比 36.12%、五个分桶合计占比 100.00%；20260619 当期退款占比 36.65%、五个分桶合计占比 100.00%。

## 2026-07-05 2886 退费整体数据人头退费率分母修正

- 修正 `resources/raw_sql/data_center_market_2886_20260705.sql`：新增与 2809 成单用户画像整体数据一致的用户层聚合，输出 `正价课人头`、`正价课人次`、`退费人次`、`GMV退费率`、`人头退费率`。
- `退费人头` 修正为正价课出单用户中的退费去重人数：同一 `period_name + channel_map + grade_name + jingli + user_id` 下 `regular_course_user_count > 0` 且截面退款金额大于 0 计 1；`人头退费率` 分母从旧的有效线索量调整为 `正价课人头`。
- `退费人次` 修正为发生退费的正价课出单用户对应的正价课科目人次：当前 2886 源表没有实际退款科目数字段，因此不能解释为精确退款科目数。
- 验证 SQL：`runtime/tmp/validate_2886_refund_head_rate_20260705.sql`，USQL query_id=`1449552739`。20260703 退费人头 41、退费人次 107、正价课人头 365、人头退费率 11.2%；20260626 退费人头 45、退费人次 102、正价课人头 396、人头退费率 11.4%。2809 对照 query_id=`1449489543`，20260703 `pay_user_head_count = 365`、`pay_subject_person_count = 810`，与 2886 正价课分母一致。

## 2026-07-05 2890 多科用户退费人头退费率分母修正

- 修正 `resources/raw_sql/data_center_market_2890_20260705.sql`：新增用户层 `user_base/user_agg`，按 `period_name + channel_map + grade_name + jingli + zhuguan + employee_email_name + user_id` 先聚合，再判断正价课出单与退费用户。
- 新增 `pay_user_head_count`，作为人头退费率推荐分母；`total_headcount` 保留为有效线索用户历史字段，不再作为人头退费率推荐分母。
- `refund_headcount_section` 修正为正价课出单用户中的截面退费去重人数；新增 `refund_subject_person_count_section` 表示这些退费正价课用户对应的正价课科目人次。
- 单科/多科退费人头分子改为用户层 `pay_subject_person_count` 分层后的正价课退费去重人数；GMV 金额类字段保持原金额汇总口径。
- 验证 SQL：`runtime/tmp/validate_2890_refund_head_person_times_20260705.sql`，USQL query_id=`1449584224`。20260703 正价课人头 365、退费人头 41、退费人次 107、人头退费率 11.2%；20260626 正价课人头 396、退费人头 45、退费人次 102、人头退费率 11.4%；20260619 正价课人头 290、退费人头 43、退费人次 87、人头退费率 14.8%。

## 2026-07-05 数据中心数据集源 SQL 同步

- 从数据中心 `https://uanalysis.baijia.com/data-center/data-set` 同步数据集源 SQL，范围：市场顾问部目录下从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- 保存 39 个数据集源 SQL 到 `resources/raw_sql`，更新清单 `knowledge/dashboards/data_center_market_datasets.md`。
- 未改写 SQL 语义；后续字段、指标或临时表口径仍需基于源 SQL 和业务规则单独维护。

## 2026-07-05 市场顾问-用户画像分析知识库全量刷新与 raw SQL 去重

- 使用 `usql-web-query-operator` 重新探查 `dashboard_3804681042591760385` 运行态和 Taitan 编辑态：运行态 28 个组件、23 个取值单元、18 个分析单元全部 ready；编辑态 8 个透视单元、99 个配置字段、52 个自定义公式。
- 将该看板 11 个模型统一映射到 20260705 数据中心 SQL：`2683/2809/2812/2836/2885/2883/2349/2886/2344/2890/2353`。
- 2349「退费_科目_产品」当前 SQL 只保留 `refund_amount` 和 `total_refund_amount` 分子/分母字段；删除旧 SQL 行级退款金额占比口径，要求看板自定义指标使用 `sum(refund_amount) / sum(total_refund_amount)`。
- 清理 37 个被 20260705 版本覆盖的旧 raw SQL 或语义重复 SQL 文件；保留 `data_center_market_*_20260705.sql` 作为当前 canonical 入口。
- 更新看板文档、指标文档、编辑页画像、Web BI 结构快照、表关系、范围规则、quick reference、decision tree，并重建反向索引后执行完整性校验。

## 2026-07-09 运营侧数据看板暑期期次热修

- 通过 `sync-data-center-sql` dry run 从数据中心确认 8 个运营侧相关数据集仍为当前网页端目标：`2054/2132/2293/2310/2344/2345/2423/2424`。
- 将 runtime 中已校验的热修 SQL 同步为知识库 canonical raw SQL：`resources/raw_sql/data_center_market_{2054,2132,2293,2310,2344,2345,2423,2424}_20260709.sql`，并更新 `knowledge/dashboards/data_center_market_datasets.md` 的文件映射。
- 修正原因：暑期运营排期后，期次不再稳定等同自然周周五；`2026-07-14` 至 `2026-07-18` 的业务期次应为 `20260716期`，旧周五推导会误显示为 `20260717期`。
- `2054 (内部渠道)外呼过程数据` 在本次入库版本中删除末尾 `where valid_lead_count > 0`，保留有效线索为 0 的外呼过程行；字段内部用于指标判定的 `valid_lead_count > 0` 条件不变。
- 新增 `knowledge/sql_patterns/market_summer_qici_corrections.md`，记录暑期期次改造原因、已修正数据集、短期 `case when 日期范围 then qici` 方案，以及后续用业务日历日期范围 join 统一取 `qici` 的生产改造方向。

## 2026-07-10 Text2SQL P0 注册、配置与验证门禁修复

- 移除 `SKILL.md` 文件头 BOM，修正 `agents/openai.yaml` 的 `$sql-query-writer-for-dashboard` 调用入口，并将 metadata 版本更新为 `0.2.4`。
- 将 SQL 网页执行说明统一改为通过命令行 `--env-file` 或环境变量 `USQL_ENV_FILE` 指定凭证文件，不再在运行入口硬编码易漂移路径。
- 在 skills 仓库新增统一 Text2SQL 栈验证入口，串行运行三个 Skill 的 `quick_validate`、两个业务 SQL Skill 的 integrity、当前文档引用检查和 USQL P0 安全测试。
- 本次只修复 Skill 发现、运行配置和安全验证，不修改指标口径、表结构、看板 SQL、Raw SQL 或反向索引。

## 2026-07-11 Text2SQL P3A/P3B 市场顾问看板设计路由

- 新增 `knowledge/sql_patterns/dashboard_design_change_workflow.md`，明确市场顾问正向 `QuerySpec -> QueryPlan -> DashboardDatasetSpec -> DashboardDesignSpec -> DashboardChangePlan` 链路，以及从 live profile 反查 component/model/field/formula、市场顾问 contract、`source_path` 和 retained SQL 的反向链路。
- P3A 对 component、layout、formula、filter 开放画像、设计、结构化 diff 和 dry-run；所有业务字段和公式依赖必须引用 `market_consultant:*` 的 `confirmed` contract ID 与本域 `source_path`，不借用青橙同名口径。
- P3B 当前只允许 stable-ID `update_filter_dynamic_default`：必须同时定位 `relation_id + filter_id + field_id`。组件字段、布局、公式、数据集重绑、新建和删除均标为 `blocked_unsupported`；计划含任一 blocked operation 时整次 Apply 零写入。
- `apply-dashboard-change` 仅写 draft，`publish-dashboard-change --confirm-publish` 独立执行并校验成功 ApplyReceipt 与最新 profile hash。本 Skill 不保存登录态、不掌握写接口，也不把任何设计工件当授权。
- 同步 `agents/openai.yaml` 的描述和默认提示，使 Skill 入口能发现市场顾问域内 DashboardDesignSpec/ChangePlan 能力，同时保留 operator 写入门禁。
- 仅更新 Skill 路由、速查、决策树与工作流说明；未删除、覆盖或修改既有市场顾问指标、维度、范围、Join 契约及业务知识文档。

## 2026-07-11 10:01:17

- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 扫描 `市场顾问数据` 文件夹，并将原始 `profile.json` 写入本地 runtime 目录。
- 刷新 `knowledge/dashboard_web_profiles/README.md`，当前索引 18 个看板快照。
- 本次 profile 结果：成功 18 个，失败 0 个。

## 2026-07-11 P3 看板探测器全量回归与编辑器知识刷新

- 只读刷新市场顾问数据文件夹 18 个 Web BI 结构快照；其中 home 测试入口仅保留视图快照，不进入编辑器设计目标。
- 刷新 17 个编辑页组件/字段快照：active=16，incomplete=1。
- 暑期激励看板存在两个组件对同一数据集缺失字段的悬空引用，P3 binding gate 标记 incomplete，未提升为可设计/可变更目标。
- 本次仅更新 dashboard_web_profiles、索引与生成清单；未修改市场顾问指标、范围、Join、语义契约或 retained SQL。

## 2026-07-11 canonical 知识唯一版本清理

- 删除数据中心 `2054`、`2132`、`2293`、`2310`、`2344`、`2345`、`2423`、`2424` 的 `20260705` 旧 SQL，仅保留已包含 `20260716期` 暑期业务日历修正的 `20260709` canonical 版本。
- 将看板、指标、Join 风险、查询模式和临时表文档中的活跃引用全部迁移到 `20260709`，历史更新日志仅承担审计说明，不作为 Text2SQL 当前入口。
- 保留“当期转化人数”和“当期转化科目人次”两个不同粒度契约；裸称“当期转化”继续阻断并要求消歧，不把业务差异误判为历史版本。
- 删除已被 2890 替代的 2350 多科退费 SQL、未同步当前逻辑的 2742 固定期次 SQL，以及六份仅作历史/重复说明的看板与指标文档；固定期次需求改由当前 2727 通用 SQL 加显式期次过滤生成。
- 以最新看板探测结果为准，2353 仍绑定“退费原因占比”组件，因此保留为当前模型；退费知识统一由 `market_channel_conversion_profile.md` 与同名 metrics 文档维护，不再保留多份解释入口。
- 新增仓库级唯一版本审计，阻断重复 canonical 文件、相同内容副本、重复契约 ID 和同类同表同字段的重复所有权。

## 2026-07-11 数据中心 stable canonical 原子同步

- 将 37 个市场顾问数据中心 SQL 一次性迁移为 `data_center_market_<model_id>.sql` 稳定路径；版本日期不再进入文件名，历史内容由 Git 与 changelog 追溯。
- 新增 `semantic/current_model_bindings.json`，登记 37 个 current model 的稳定路径、SQL SHA-256 和数据集元数据，并绑定 2349 退款金额结构、2890 多科退费、2353 退费原因三个当前语义槽位及看板证据。
- 数据中心更新改为 `dry-run plan -> exact plan hash -> atomic apply -> mandatory validation`；跨 model 替代必须同计划更新语义槽位并显式退役旧模型，任一维护门禁失败自动恢复写前快照。

## 2026-07-11 物理表字段来源收敛

- 退役初始数据地图 PDF、29 张页面渲染图、空图片目录、PDF 解析报告，以及 PDF/OCR/手工字段目录 JSON 解析脚本；历史 changelog 继续保留原始导入事实，但不再作为当前 Text2SQL 入口。
- 保留 `knowledge/tables` 已沉淀的全部表字段、业务备注和 confirmed contract，只删除当前文档中的低置信度 PDF/OCR 依赖说明；2026-06-17 数据地图回填记录已确认市场域 19 张物理表字段缺口、类型占位和说明占位均为 0。
- 物理表字段统一改由 `usql-web-query-operator sync-datamap-fields` 探查和维护；数据地图只提供表名、字段、类型、分区和 DDL 等物理事实，不替代市场顾问指标、范围、Join 或业务口径。
- 数据地图写入后的反向索引、共享 catalog、域内 integrity 和完整 Text2SQL stack 改为不可关闭的强制门禁，避免表字段更新后知识索引或 contract source hash 漂移。

## 2026-07-11 评优看板春节特殊期次运营区间校准

- 根据 `D:\Feishu\日期-期次对照.xlsx` 校准评优看板财务流水 `qici` 推导，保证与 `temp_table.zhangjunyan01_pingyou_jg` 的维护期次一致。
- 同步更新期次评优、月度评优、季度评优、半年度评优四个数据集 SQL，修正 `20260206期`、`20260213期`、`20260220期` 等不存在于 `pingyou_jg` 的派生期次。
- 校准后的特殊区间为：`20260123期` 覆盖 `2026-01-20` 至 `2026-01-26`，`20260130期` 覆盖 `2026-01-27` 至 `2026-02-02`，`20260205期` 覆盖 `2026-02-03` 至 `2026-02-08`，`20260211期` 覆盖 `2026-02-09` 至 `2026-02-15`，`20260227期` 覆盖 `2026-02-16` 至 `2026-03-02`。

## 2026-07-12 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2293`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-14 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2253, 2293`；每个 model_id 只保留稳定 canonical 路径。
- 在 `转化数据_市场顾问`（2253）和 `运营侧个人数据`（2293）的渠道映射 CASE 中，将“王容07 + 锋途项目组 + koc常规5元 + 帅师/周帅”规则置于通用 KOC-周帅分支之前，统一映射为 `KOC-周帅数学`；仅重分类渠道，不新增或复制订单行。
- 两个数据集均已在数据中心保存并触发刷新，新增刷新记录状态为 `SUCCESS`；刷新后两套数据按目标筛选结果一致，原 `未知` 的 14600 元迁移至 `KOC-周帅数学`，目标范围 GMV 总额保持不变。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-15 暑期运营期次补全 2026-07-19

- `转化数据_市场顾问`（2253）将 `lead_period` 的 `20260716期` 结束日期由 `2026-07-18` 延长至 `2026-07-19`。
- `运营侧个人数据`（2293）将 `lead_period`、`class_period` 的 `20260716期` 结束日期由 `2026-07-18` 延长至 `2026-07-19`。
- 修正 `group_period=20260719` 因日历缺口回退为自然周周五 `20260717期` 的问题；本次仅调整期次归属，不改变收款、退款事实行及总额。

## 2026-07-15 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2344, 2683, 2809, 2812, 2836, 2883, 2885, 2886, 2890`；每个 model_id 只保留稳定 canonical 路径。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-15 市场顾问-用户画像分析暑期期次修正

- 只读刷新 `dashboard_3804681042591760385`，确认 11 个生产模型和 5 组期次筛选；其中 4 组筛选包含并动态选中 `20260717期`，`2836/2883/2885` 对应筛选已正常显示 `20260716期`。
- 修正 `2344/2349/2353/2683/2809/2812/2886/2890` 的生产候选 SQL，将 `2026-07-14` 至 `2026-07-19` 统一归属 `20260716期`；退款模型同时修正财务 `trade_time`、归因流水 `trade_group_period` 和规则期次，避免只改线索期次后退款组件仍残留异常期次。
- 本次只重新分配期次标签，不新增、删除或复制订单、收款、退款和线索事实行；`20260722期` 继续从 `2026-07-20` 开始。
- 8 个生产数据集均完成完整 SQL 替换、预览、保存回读和立即抽数，新增成功任务分别为：`2344 -> 159010259`、`2349 -> 159010263`、`2353 -> 159010265`、`2683 -> 159010268`、`2809 -> 159010271`、`2812 -> 159010274`、`2886 -> 159010279`、`2890 -> 159010281`。
- 抽数后重新读取看板：5 组期次筛选均默认 `20260716期`，候选值均不再包含 `20260717期`；18 个看板数据单元全部 `data_ready`，以 `20260716期` 正向打开成功，以 `20260717期` 反向验证时提示筛选项不存在。
- 生产 SQL 回读已同步到稳定 canonical raw SQL，并更新当前模型绑定；反向索引、Text2SQL 目录、唯一版本审计、市场域 integrity 和完整 Text2SQL 栈验证全部通过。

## 2026-07-15 koc数据播报暑期期次补齐

- 更新数据中心模型 `2978`（`koc数据播报`）canonical SQL：新增 `biz_qici_calendar`，覆盖 `20260716期`、`20260722期`、`20260728期`、`20260803期`、`20260809期` 的暑期运营期次。
- `lead_base.period_name` 改为优先按业务日历日期范围取期次，未命中时才回退历史自然周周五推导逻辑；本次只修改期次派生，不改变 KOC 渠道映射、外呼 5min 率和经理聚合口径。
- 生产数据中心替换已完成：预览 task id `1474756048`，保存后 SQL hash 回读为 `b0e70665b7abcb76091cdc42fdde936e15e239a54c8bc867d653d05ba63a0c43`，立即执行新增同步记录 `159037651`，状态 `SUCCESS`。

## 2026-07-16 数据中心 stable canonical SQL 同步

- 按已审阅同步计划原子更新 model_id：`2310`；每个 model_id 只保留稳定 canonical 路径。
- `分二级部门转化`仅对映射为“抖音私信”的记录使用承接二级部门作为 `dept_name`，其他渠道继续使用期次映射二级部门；同时补充“青橙项目部 + rule_name 包含抖音私信”的渠道判定，避免依赖单一来源负责人。
- 生产数据中心已完成完整 SQL 替换、预览和保存回读，SQL SHA-256 为 `df6ebc410af838facac0d05ca75ca9c7c2141b5f808a6bdb44fdcd881c3681b3`；立即执行新增同步记录 `159190179`，状态 `SUCCESS`。
- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。

## 2026-07-16 馒头订单明细支付时间模板同步

- 从模板取数平台重新读取 `馒头_订单明细_支付时间`（模板 ID `8735`）当前发布 SQL；发布时间为 `2026-07-16 20:01:40`，平台状态为 `published`。
- 新增 `resources/raw_sql/template_query_market_mantou_order_detail_pay_time_20260716.sql`，完整保存线上 `sqlDetail`，SHA-256 为 `3781532fd35d262d615e1cabf9076567b5cbf92764ff7665af3139eed98c6aa0`。
- 新增执行计划优化文档，记录旧版因重 CTE 多次内联产生 `197 > 130` stages 的原因，以及当前发布版使用窗口统计降低 `cs` 引用次数的修复。
- 当前发布 SQL 已使用 Presto 验证成功，query ID 为 `1477690051`；模板参数继续保留 `${day:1}`、`${day:2}` 半开区间形式。

## 2026-07-18 13:21:42 runtime 首批可复用查询模板入库

- 新增 M1 指定班级订单与暑秋联报报名类型模板，归档财务订单—班级明细和 service `bind_type` 报名类型两份验证 SQL；固定合并键为 `order_number + class_id`，并记录联报优先和跨班级金额重复风险。
- 新增 M2 财务归属正价课订单明细模板，分别保留精品班学部版与市场部版；明确支付期次、业务范围、订单/父订单去重字段和运营口径订单数的差异。
- 新增 M3 精品班初三整周期售卖科目占比模板；固定 `channel_group + top_order_number + course_subject` 净额大于 0 的整数计数口径，默认不增加日期粒度，占比由下游按可加和分子/分母重算。
- 三个模板均来自已产出并核对的 runtime SQL/Excel；作为复杂人工 SQL 证据入库，不提升为单表自动编译模板，也未修改任何线上数据集或看板。

## 2026-07-18 runtime 第二批可复用查询模板入库

- 新增 M4 指定渠道外部课表到课模板，复用现有普通/有效到课指标；历史陈瑞春只作为 worked example，渠道名称、识别谓词、课表、组织范围和时间窗口均定义为可替换参数。
- 新增 M5 初中期次×年级转化概览，保留人头转化、订单转化和单效的可加总分子/分母；历史跨二级部门范围不解释为单一市场顾问部口径。
- 新增 M6 财务正价课科目结构及 pending 指标组，明确与 2809 运营转化识别的差异、用户—科目粒度和重复分母风险。
- 新增 M7 渠道内 TOP N 顾问转化模板，固定“顾问层先聚合再排名”和确定性并列顺序；不归档历史 SQL 中的超长渠道 CASE，统一引用当前 canonical 渠道映射。
- 新增 M8 渠道专项科目/课程/班课 worked example，复用 M6 指标；“西安直播江苏”和“江苏专版”均为可替换的渠道/产品分类参数。
- M4、M5、M6、M8 归档历史验证 SQL；M7 仅沉淀排名层和调用约束，避免复制 dated 渠道 CASE。全部保持人工 SQL 门禁，未修改线上数据集或看板。
