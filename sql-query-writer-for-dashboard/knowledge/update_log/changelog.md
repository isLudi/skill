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

- 新增原始 SQL：`resources/raw_sql/consultant_sales_department_tenure.sql`，来源为用户提供的“伙伴在部门开始时间”SQL。
- 新增看板文档：`knowledge/dashboards/consultant_sales_department_tenure.md`。
- 新增指标集合：`knowledge/metrics/consultant_sales_department_tenure_metrics.md`。
- 新增最小表结构文档：`knowledge/tables/dw.dim_employee_chain.md`，记录该 SQL 中使用的组织链字段，并标记真实 DDL、字段类型、数据粒度和权限范围待人工确认。
- 更新 `knowledge/01_table_index.md`，登记 `dw.dim_employee_chain`。
- 更新 `knowledge/dashboards/README.md` 与 `knowledge/metrics/README.md`，补充新看板和指标集合索引。
- 更新 `knowledge/joins/common_join_keys.md` 与 `knowledge/joins/table_relationships.md`，补充组织链 `path_name` 范围限定、`email_prefix` 优先关联建议、`name` 关联风险和顾问部门任职期销售统计关系。
- 记录待确认事项：`org_t.name = dd_0.name` 是否可改为邮箱前缀关联、在职员工 `end_time` 为空处理、是否补充 `employee_third_level_department_name = '市场顾问部'`、课程部门是否需要单独范围限定、`promit/pmit` 命名和口径。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/consultant_sales_department_tenure.sql`；校验提示课程部门字段未过滤、部门字段解析误报和 `org_t` group by 解析误报，已写入看板待确认事项。
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

- 新增原始 SQL：`resources/raw_sql/consultant_sales_department_tenure_period_20260424.sql`，来源为用户提供的“伙伴在部门开始时间”SQL。
- 新增看板文档：`knowledge/dashboards/consultant_sales_department_tenure_period_20260424.md`。
- 新增指标集合：`knowledge/metrics/consultant_sales_department_tenure_period_20260424_metrics.md`。
- 更新 `knowledge/dashboards/README.md` 与 `knowledge/metrics/README.md`，补充该期次过滤版本索引。
- 更新 `knowledge/joins/table_relationships.md`，记录该 SQL 继承 `consultant_sales_department_tenure.sql` 的组织链、财务流水和专项架构关系，仅在最终输出层增加 `qici = '20260424期'`。
- 记录待确认事项：`name` 关联唯一性、`end_time` 为空处理、是否补充 `employee_third_level_department_name = '市场顾问部'`、课程部门是否需要单独范围限定、`promit/pmit` 命名和口径。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/consultant_sales_department_tenure_period_20260424.sql`；校验提示课程部门字段未过滤、员工部门字段解析误报和 `org_t` group by 解析误报，已在看板文档待确认事项中保留。
- 运行 `python scripts/check_skill_integrity.py`；结构自检通过，表索引覆盖正常。

## 2026-05-08 顾问部门任职期销售通用 SQL 排名增强

- 按用户提供的新版本覆盖 `resources/raw_sql/consultant_sales_department_tenure.sql`。
- 更新 `knowledge/dashboards/consultant_sales_department_tenure.md`，同步新版 CTE 链路、邮箱前缀关联、三层员工部门限定、日维度排名和期次维度排名逻辑。
- 更新 `knowledge/metrics/consultant_sales_department_tenure_metrics.md`，补充 `day_dept_period_rank_scope`、`day_dept_period_rank_no`、`day_dept_period_need_pmit_to_previous`、`period_dept_rank_scope`、`period_dept_rank_no`、`period_dept_need_pmit_to_previous`、`period_income`、`period_refund`、`period_pmit` 等指标。
- 更新 `knowledge/joins/table_relationships.md`，将任职期过滤 join 从 `org_t.name = dd_0.name` 改为 `org_t.email_prefix = dd_0.email_prefix`，并记录日维度和期次维度排名关系。
- 新版财务流水范围补充 `employee_third_level_department_name = '市场顾问部'`。
- 记录待确认事项：`end_time` 为空处理、`temp_table.dingxi01_jiagou_zx.employee_email_name = rd.name` 姓名关联唯一性、排名是否允许并列、固定期次版本 `consultant_sales_department_tenure_period_20260424.sql` 是否需要同步新版排名增强逻辑。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/consultant_sales_department_tenure.sql`；校验提示 `employee_*_department_name` 已过滤但被脚本解析为未过滤、`org_t` 中 `name` group by 解析误报，已在看板文档待确认事项中保留。
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

- 新增原始 SQL：`resources/raw_sql/traffic_profile.sql`，来源为用户提供的“流量画像”原始查询代码。
- 新增看板文档：`knowledge/dashboards/traffic_profile.md`，记录 APP 登录、最新设备渠道、外呼、深沟、到课、成交科目档位、成本目标和城市等级等 CTE/指标口径。
- 新增指标集合：`knowledge/metrics/traffic_profile_metrics.md`。
- 更新 `knowledge/dashboards/README.md` 与 `knowledge/metrics/README.md`，补充流量画像入口。
- 更新 `knowledge/joins/common_join_keys.md` 与 `knowledge/joins/table_relationships.md`，补充用户 APP 登录、外呼工作量、行课到课、财务成交科目数、成本目标和架构临时表的关联关系。
- 更新相关表文档：主全链路表、C 端应用登录日表、私海明细、外呼工作量、行课明细、财务业绩明细、到课映射、渠道分组、成本目标和架构临时表，补充流量画像 SQL 使用备注。
- 更新 `knowledge/03_range_limit_rules.md`，补充流量画像看板的历史范围限定；更新 `knowledge/sql_patterns/dashboard_query_patterns.md`，补充流量画像增强模式。
- 记录待确认事项：原始 SQL 存在三参数 `date_add` 历史写法、主表 `dt/hour` 偏移不一致、`call_c` join 未带 `lead_id`、成交科目数 join 未带顾问名、`podan` 注释与代码不一致、临时表唯一性和数值/字符串比较风险。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/traffic_profile.sql`；历史 SQL 保持原样，校验提示三参数 `date_add`、数值/字符串比较、部门过滤解析告警、派生字段误报和 `select distinct` group by 解析告警，已写入看板待确认事项。
- 运行 `python scripts/check_skill_integrity.py`；结构自检通过，既有表文档含待人工确认项属预期。

## 2026-05-09 changelog 正序规则补充

- 调整 `knowledge/update_log/changelog.md` 展示顺序，改为按日期从旧到新正序排列。
- 明确后续更新 changelog 必须按日期向后追加在文件末尾；同一天多次更新按发生顺序继续追加，必要时使用 `YYYY-MM-DD HH:mm:ss` 标题区分顺序。
- 更新 `SKILL.md`、`docs/USAGE_PROMPTS.md`、`knowledge/sql_patterns/channel_mapping_case_when.md` 和 `scripts/check_skill_integrity.py`，固化 changelog 正序追加和校验规则。
- 排查其他 Markdown 日期标题顺序，未发现除 `knowledge/update_log/changelog.md` 外的同类时间排序问题。

## 2026-05-09 退费分析 SQL 入库

- 新增原始 SQL：`resources/raw_sql/refund_multi_subject_user_ratio.sql`，来源 `E:\2000_work\GAOTU\多科用户退费占比.txt`。
- 新增原始 SQL：`resources/raw_sql/refund_subject_product.sql`，来源 `E:\2000_work\GAOTU\退费_科目_产品.txt`。
- 新增原始 SQL：`resources/raw_sql/refund_reason_analysis.sql`，来源 `E:\2000_work\GAOTU\退费原因分析.txt`。
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

- 使用用户提供的 `D:\Feishu\city_channel.txt` 覆盖归档 `resources/raw_sql/traffic_profile.sql`，确认文件哈希与来源一致。
- 更新 `knowledge/dashboards/traffic_profile.md` 和 `knowledge/metrics/traffic_profile_metrics.md`，补充 `province_name`、`city_name`、`city_level_name` 城市渠道维度，移除旧版 `city_level_row` 结果指标说明。
- 更新期次范围口径：当前版本在 `base` CTE 使用 `period_name >= ${period_name1}` 且 `period_name < ${period_name2}`，执行前必须替换参数。
- 更新主表分区说明：当前版本主全链路表使用 `dt = now() - 2 hour` 且 `hour = now() - 2 hour`；旧版 `hour = now() - 3 hour` 仅作为历史变体风险保留。
- 更新 `knowledge/01_table_index.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`、`knowledge/03_range_limit_rules.md`、`knowledge/sql_patterns/dashboard_query_patterns.md`、`knowledge/dashboards/README.md`、`knowledge/metrics/README.md` 和相关表文档。
- 待人工确认：省市归属和城市等级字段口径、三参数 `date_add` 平台兼容性、`call_c` 未带 `lead_id` join 的重复风险、`dd` 未带 `employee_email_name` join 的重复风险、临时表唯一性、`podan` 注释与代码不一致。
- 运行 `python scripts/validate_sql_rules.py --sql-file resources/raw_sql/traffic_profile.sql`；历史 SQL 原样归档，校验提示三参数 `date_add`、数值/字符串比较、部门过滤解析告警、派生别名 `channel_map/grade_1` 误报和 `select distinct` group by 解析告警，已在看板待确认事项中保留。
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
  - `resources/raw_sql/market_channel_conversion_profile_call_duration_dataset.sql`
  - `resources/raw_sql/market_channel_conversion_profile_learn_duration_dataset.sql`
  - `resources/raw_sql/market_channel_conversion_profile_deep_stage_dataset.sql`
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

- 新增原始 SQL：`resources/raw_sql/market_channel_conversion_profile_overall_dataset_fixed.sql`。
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
