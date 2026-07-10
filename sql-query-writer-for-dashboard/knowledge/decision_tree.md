# 用户需求到知识库路由

> 先用本文件判断要读哪些知识，再进入具体表、指标、看板、join 或踩坑文档。不要把本文件当完整口径来源。

| 用户说法 | 先读 | 再读 | 必要规则/踩坑 |
|---|---|---|---|
| 未说明业务部门，或同名指标可能属于市场顾问/青橙 | `semantic/domain_manifest.json` | 先形成 `domain: unresolved` 的 QuerySpec | 不得默认市场顾问；业务域、指标版本、范围或粒度未决时停止生成生产 SQL |
| 已确认市场顾问需求，准备生成或修复 SQL | `semantic/domain_manifest.json` | `knowledge/quick_reference.md` 与命中的单个 dashboard/metric/table/join 文档 | 使用 `scripts/text2sql.py` 校验 QuerySpec；evidence 只能来自市场顾问 Skill 或中性物理目录 |
| 市场顾问与青橙跨部门对比 | 两个 Skill 各自的 `semantic/domain_manifest.json` | 两边各自命中的 metrics/dashboard/raw SQL | 构建两份独立 QuerySpec；不得共享指标、范围、临时表、渠道/期次或业务 join，只在兼容聚合粒度合并结果 |
| 市场顾问转化、线索转化、GMV、净收、破单 | `knowledge/dashboards/market_consultant_conversion.md` | `knowledge/metrics/market_consultant_conversion_metrics.md`、`knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md` | `knowledge/sql_patterns/channel_mapping_case_when.md`、`knowledge/pitfalls/common_join_failures.md` |
| 线索转化到课、首节到课、AB 意向 | `knowledge/dashboards/market_consultant_lead_conversion_attendance.md` | `knowledge/metrics/market_consultant_lead_conversion_attendance_metrics.md`、`knowledge/tables/temp_table.dingxi01_daoke_1_6_t.md` | 主课次按 `qici + channel_map_1 + grade_1` 内实际开课时间自动排序；`manual_ke_1` 仅诊断；注意到课候选窗口、槽位过滤和渠道 CASE 顺序 |
| 流量画像、城市渠道、APP 登录、成交科目档位 | `knowledge/dashboards/traffic_profile.md` | `knowledge/metrics/traffic_profile_metrics.md`、`knowledge/sql_patterns/dashboard_query_patterns.md` | 外呼 join 未带 `lead_id`、财务成交科目 join 粒度 |
| 市场渠道用户画像、成单用户过程分析、多维退费率、人头退费率、GMV 退费率、退费科目产品占比 | `knowledge/dashboards/market_channel_conversion_profile.md` | `knowledge/metrics/market_channel_conversion_profile_metrics.md`、`resources/raw_sql/data_center_market_2890_20260705.sql`、`resources/raw_sql/data_center_market_2349_20260705.sql` | 退费率默认输出分子/分母字段，由透视表重算；科目/产品/年级退款金额占比使用 2349 fixed SQL |
| 模板取数最新代码、AI分析市场顾问部多科/分周期/每天/转化/过程/到课/员工架构/进量模板 | `knowledge/dashboards/template_query_market_datasets.md` | 清单中的对应 raw SQL 文件 | 使用口径必须说明为“模板取数”；不要默认覆盖或替代数据中心/Web BI canonical SQL |
| 市场顾问看板指标含义、前端公式、透视表字段、指标与数据中心 SQL 关系 | `knowledge/metrics/market_consultant_dashboard_metric_formula_linkage.md` | `knowledge/dashboard_web_profiles/edit_metrics/README.md`、对应看板 `*_edit_metrics.md`、`resources/raw_sql/data_center_market_*_20260705.sql` | 每个看板指标先按 `model_id` 回到唯一数据中心 SQL；不要因看板名或数据集别名不同重复维护同一份 SQL |
| 历史退费分析、多科退费历史口径、退费原因、科目产品退费 | `knowledge/metrics/refund_analysis_metrics.md` | `knowledge/dashboards/refund_multi_subject_user_ratio.md`、`knowledge/dashboards/refund_subject_product.md`、`knowledge/dashboards/refund_reason_analysis.md` | 2349 科目/产品/年级金额占比已更新为当前 fixed SQL；退费原因和多科历史口径仍需区分历史财务流水 |
| 分配计划、计划分配量、实际有效量 | `knowledge/dashboards/lead_assign_plan_actual_valid_count.md` | `knowledge/tables/service_dw.dim_crm_assign_rule_lead_detail_hf.md`、`knowledge/tables/temp_table.dingxi01_plan_id.md` | `group_id` 不全局唯一，规则名拆期次风险 |
| 外呼过程、长通话、深沟、双沟、首 call 任务 | `knowledge/dashboards/outbound_call_process_dashboard.md` | `knowledge/sql_patterns/first_call_task_metric_pattern.md`、`knowledge/tables/service_dw.dwd_crm_assign_private_detail_hf.md` | 首 call 必须用任务表，API 验证需看权限 |
| 外呼过程期次导出、外呼过程模板取数、period_name1/period_name2 | `knowledge/sql_patterns/outbound_call_process_export_template.md` | `knowledge/dashboards/outbound_call_process_dashboard.md`、`knowledge/metrics/outbound_call_process_metrics.md` | 使用 `qici >= ${period_name1}` 且 `qici < ${period_name2}`；不要覆盖 raw SQL |
| 外呼过程数据看板页面字段、筛选器、组件结构 | `knowledge/dashboard_web_profiles/outbound_call_process_dashboard_web_profile.md` | `knowledge/dashboards/outbound_call_process_dashboard.md`、`knowledge/metrics/outbound_call_process_metrics.md` | Web BI 结构只说明页面配置；SQL 口径回到 dashboards/metrics |
| 市场顾问部_行课报表页面结构 | `knowledge/dashboard_web_profiles/market_consultant_attendance_report_web_profile.md` | `knowledge/dashboards/market_consultant_lead_conversion_attendance.md`、`knowledge/metrics/market_consultant_lead_conversion_attendance_metrics.md` | 先区分页面字段 ID 和底层 SQL 字段名 |
| 运营侧数据看板页面结构、运营侧个人数据、渠道分段组件、暑期期次修正 | `knowledge/dashboard_web_profiles/operation_side_dashboard_web_profile.md` | `knowledge/dashboards/market_consultant_conversion.md`、`knowledge/dashboards/outbound_call_process_dashboard.md`、`knowledge/sql_patterns/market_summer_qici_corrections.md` | 该页面组合多个模型和组件，不能用单一 SQL 文档替代；7 月后期次不能默认按周五推导 |
| 转化数据页面字段、GMV、净收、退费率、人产组件 | `knowledge/dashboard_web_profiles/market_consultant_conversion_web_profile.md` | `knowledge/dashboards/market_consultant_conversion.md`、`knowledge/metrics/market_consultant_conversion_metrics.md` | Web 字段 ID 多为自定义指标，口径需回到转化 SQL |
| 市场顾问-进量节奏页面结构 | `knowledge/dashboard_web_profiles/market_consultant_volume_pace_web_profile.md` | `knowledge/dashboards/lead_assign_plan_actual_valid_count.md`、`knowledge/metrics/lead_assign_plan_actual_valid_count_metrics.md` | 进量节奏是 Web BI 页面结构；计划/实际口径另读分配计划文档 |
| 顾问销售评优、ROI、退费率、人产、排名 | `knowledge/dashboards/consultant_sales_ranking_evaluation.md` | `knowledge/metrics/consultant_sales_ranking_evaluation_metrics.md`、`knowledge/sql_patterns/dashboard_query_patterns.md` | 评优名单 vs 在职架构名单，不同输出粒度避免前端重复聚合 |
| 市场顾问--评优看板页面结构 | `knowledge/dashboard_web_profiles/market_consultant_evaluation_web_profile.md` | `knowledge/dashboards/consultant_sales_ranking_evaluation.md`、`knowledge/metrics/consultant_sales_ranking_evaluation_metrics.md` | 页面评优结构不等于所有评优 SQL 口径，排名/人产仍需看评优文档 |
| 昆仑山战役、暑期激励数据看板页面结构 | `knowledge/dashboard_web_profiles/kunlun_summer_incentive_web_profile.md` | `knowledge/dashboard_web_profiles/operation_side_dashboard_web_profile.md`、相关 dashboards/metrics | 激励看板以页面结构快照为主，业务奖励规则需人工确认 |
| H 业务线二级部门转化、跨二级部门对比 | `knowledge/dashboards/h_biz_line_department_conversion.md` | `knowledge/metrics/h_biz_line_department_conversion_metrics.md`、`knowledge/sql_patterns/first_call_task_metric_pattern.md` | 市场顾问看板和跨部门看板范围不同 |
| 某期次/经理/顾问查不到 | `knowledge/sql_patterns/dashboard_query_patterns.md` | 事实主表文档、名单/架构表文档、`knowledge/sql_patterns/web_permission_guide.md` | 先判断事实主表驱动还是名单/架构表驱动 |
| JOIN 后指标为 0、行数放大、年级断裂、某渠道某期次消失 | `knowledge/pitfalls/common_join_failures.md` | `knowledge/joins/common_join_keys.md`、`knowledge/sql_patterns/channel_mapping_case_when.md`、相关表文档 | `grade='0'` 通配、到课映射缺失、渠道 CASE 顺序抢先命中、架构截面错位 |
| Web 查询执行、SQL 下载、权限问题 | `knowledge/sql_patterns/web_query_playwright.md` | `knowledge/sql_patterns/web_permission_guide.md`、`usql-web-query-operator` Skill | 区分 Web 登录态过期、SQL 语法、部门范围、表级不可见 |

## 路由原则

- 先做 domain resolution，再读取 `semantic/domain_manifest.json` 并构建 QuerySpec；`domain != market_consultant` 时停止本 Skill 的业务检索。
- QuerySpec 的必填 unresolved slot 未清空前，不得生成或执行生产 SQL；反向索引只定位候选，最终证据回到 domain-local metrics/dashboard/raw SQL。
- 简单表结构或字段问题：读 `quick_reference.md`、`01_table_index.md`、相关 `tables/*.md` 即可。
- 指标或看板口径问题：先读对应 `dashboards/*.md` 和 `metrics/*.md`，再补 join 或 SQL pattern。
- SQL 报错或结果异常：先读全局规则、范围限定、权限边界，再读相关 pitfalls。
- 生成新市场顾问渠道归因 SQL：默认使用 `resources/raw_sql/market_channel_case_when_0612.sql`，除非用户明确要求沿用历史 SQL 旧口径。
