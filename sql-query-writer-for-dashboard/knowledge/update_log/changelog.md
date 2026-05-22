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
