# 用户需求到知识库路由

> 先用本文件判断要读哪些知识，再进入具体表、指标、看板、join、反向索引或 SQL 模板。不要把本文件当完整口径来源。

| 用户说法 | 先读 | 再读 | 必要规则/踩坑 |
|---|---|---|---|
| 用户给出青橙指标、维度、join 或范围别名 | `semantic/generated/contract_index.json` | 命中的 `semantic/contracts/*.json` 条目及其 `source_path` | contract index 只负责路由；`confirmed` 才能进入可执行计划，`pending_confirmation` 必须保留为未决 |
| 用户只说“顾问” | contract index 中别名 `顾问` 的两个候选 | `qingcheng:dimension:section_consultant` 与 `qingcheng:dimension:performance_consultant` | 询问是线索分配顾问还是业绩归属顾问；不得按当前候选表自动决定 |
| 已解析 confirmed 指标，候选指标共享一个基础表 | 命中的 metric/dimension/scope contracts | 对应表文档、范围文档和 QuerySpec | 先生成 QueryPlan；仅无未决槽位、无 join 的单基础表计划可自动 compile |
| 命中 pending 契约或多表 join | 对应契约的 `source_path` | `knowledge/joins/`、`knowledge/reverse_index/join_risk_index.md`、命中的 Raw SQL | pending 阻断生产；多表 join 只输出计划并人工审阅，不能用另一部门口径补齐 |
| 需要探查分区新鲜度、字段分布、重复键或 join 放大 | `semantic/domain_manifest.json` 与共享中性物理目录 | 命中的表/Join 文档，使用 `probe` 生成有界只读 SQL | 使用具体分区和小范围；probe 生成不代表执行授权，结果解释仍回到青橙业务文档 |
| 未说明业务部门，或同名指标可能属于青橙/市场顾问 | `semantic/domain_manifest.json` | 先形成 `domain: unresolved` 的 QuerySpec | 不得默认青橙或市场顾问；业务域、指标版本、范围或粒度未决时停止生成生产 SQL |
| 已确认青橙需求，准备生成或修复 SQL | `semantic/domain_manifest.json` | `knowledge/quick_reference.md` 与命中的单个 dashboard/metric/table/temp_table/join 文档 | 使用 `scripts/text2sql.py` 校验 QuerySpec；evidence 只能来自青橙 Skill 或中性物理目录 |
| 青橙与市场顾问跨部门对比 | 两个 Skill 各自的 `semantic/domain_manifest.json` | 两边各自命中的 metrics/dashboard/raw SQL | 构建两份独立 QuerySpec；不得共享指标、范围、临时表、渠道/期次或业务 join，只在兼容聚合粒度合并结果 |
| 青橙有哪些表、某表能不能用于青橙 | `knowledge/04_qingcheng_project_profile.md` | `knowledge/01_table_index.md`、对应 `knowledge/tables/*.md` 或 `knowledge/temp_tables/*.md` | 不从市场顾问 skill 自动迁移表语义；公共表也要确认青橙范围字段 |
| 写青橙过程数据 SQL | `knowledge/dashboards/qingcheng_process_data_raw_20260522.md` | `knowledge/metrics/qingcheng_process_data_metrics.md`、`knowledge/joins/table_relationships.md` | 外呼、APP 登录、到课补充会改变粒度，先查 join 风险 |
| 写青橙到课 SQL | `knowledge/dashboards/qingcheng_daoke_raw_20260522.md` | `knowledge/metrics/qingcheng_daoke_metrics.md`、`knowledge/temp_tables/temp_table.dingxi01_qing_daoke.md` | 到课表 `qici + qudao + grade + begin_time` 唯一性待确认 |
| 写青橙转化 SQL、修复转化 SQL、修正暑期期次 | `knowledge/dashboards/qingcheng_conversion_raw_20260626.md` | `knowledge/metrics/qingcheng_conversion_metrics.md`、`knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`、`knowledge/sql_patterns/qingcheng_summer_qici_corrections.md` | 先确认业务日期范围、期次正则、`hour` 偏移和 `bb_dedup ↔ ud` join 粒度 |
| 写青橙渠道订单明细 SQL / 算绩效模板 SQL | `knowledge/dashboards/qingcheng_channel_order_detail_raw_20260627.md` | `knowledge/metrics/qingcheng_channel_order_detail_metrics.md`、`knowledge/joins/table_relationships.md` | 明细 SQL 必须说明 `ld` 范围限定、订单粒度和模板扩列字段 |
| 写青橙退费原因分析、按原因看退费金额或退费人头 | `knowledge/dashboards/qingcheng_refund_reason_analysis_template.md` | `knowledge/metrics/qingcheng_refund_reason_metrics.md`、`knowledge/tables/finance_dw.dwd_finance_order_refund_df.md`、`knowledge/joins/table_relationships.md` | 原因金额是订单退款按原因源金额再分摊；pending_confirmation 阻断自动编译；结果期次架构 join 前后金额必须守恒 |
| 写青橙 TMK 转移线索、承接顾问、成交订单追踪 | `knowledge/dashboards/qingcheng_tmk_transfer_order_trace_template.md` | `knowledge/metrics/qingcheng_tmk_transfer_order_trace_metrics.md`、`knowledge/joins/common_join_keys.md`；延迟排查再读观测台账 | 潜客 ID 与转移后正常 lead_id 不可混用；业财无行是“未回补”而不是“未成交”；首次承接需按私海历史去重 |
| 导出青橙某期次/渠道过程数据、制作部门/年级/主管过程透视 | `knowledge/sql_patterns/qingcheng_period_channel_process_export_template.md` | 当前 `resources/raw_sql/data_center_qingcheng_2064.sql`、`knowledge/metrics/qingcheng_process_data_metrics.md` | 只加受控过滤与展示层；不重复保存全量 SQL；比率必须按聚合后分子÷分母重算 |
| 写青橙营收、团队完成度、个人转化 SQL | 对应 `knowledge/dashboards/qingcheng_*_raw_*.md` | 对应 `knowledge/metrics/*.md`、`knowledge/temp_tables/*.md`、`knowledge/sql_patterns/qingcheng_completion_sql_repair_checklist.md` | 先区分目标表驱动、架构表驱动和事实主表驱动；完成度三份 SQL 必须联动维护 |
| 排查个人/团队完成度与订单流水不一致 | `knowledge/sql_patterns/qingcheng_completion_sql_repair_checklist.md` | `knowledge/sql_patterns/qingcheng_personal_completion_discounted_output_risks.md`、`knowledge/dashboards/qingcheng_personal_conversion_raw_20260522.md`、`knowledge/metrics/qingcheng_personal_conversion_metrics.md`、`knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md` | 先查原始支付时间、`team_hist` 兜底、`gmv_t` 粒度、`is_internal_order_change` 和 service transfer 兜底，最后再看前端公式 |
| 追溯某批青橙 `lead_id` 最原始的来源线索 | `knowledge/sql_patterns/qingcheng_lead_origin_trace.md` | `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`、`knowledge/tables/service_dw.dm_crm_lead_stats_detail_hf.md` | 先抽样 20-50 条，再做全量导出；不要只看 `rule_name`；别把窗口别名写成 `rn` |
| 解释看板某个指标的前端公式、计算字段或与数据中心 SQL 的关系 | `knowledge/dashboard_web_profiles/edit_metrics/README.md` | `knowledge/metrics/qingcheng_dashboard_metric_formula_linkage.md`、对应当前 retained snapshot（如 `resources/raw_sql/data_center_qingcheng_2064.sql`） | 先确认看板组件和 BI 模型，再解析前端自定义公式，最后回到源 SQL 字段；不要把 `${指标}` 当物理字段 |
| 设计、比较或 dry-run 青橙看板组件、布局、公式、筛选器 | `knowledge/sql_patterns/dashboard_design_change_workflow.md` | 最新 `DashboardProfile`、命中的青橙 contracts/source、`DashboardDatasetSpec` | P3A 四类对象均可设计/diff；DesignSpec 每个业务依赖必须引用 `qingcheng:*` confirmed contract ID 与 `source_path` |
| Apply 青橙看板变更 | `DashboardChangePlan` 与 operator 当前 allowlist | `usql-web-query-operator` 的 `apply-dashboard-change` | 当前只允许 stable-ID `update_filter_dynamic_default`；任一 blocked operation 使整次 Apply 零写入；本 Skill 不掌握登录态或写接口 |
| 从 live profile 反查组件字段、公式或筛选器口径 | `knowledge/sql_patterns/dashboard_design_change_workflow.md` | `dashboard_web_profiles -> metric linkage -> contract_index -> qingcheng contract -> source_path/raw SQL` | 必须反查到唯一青橙 contract；unknown/ambiguous 或跨域依赖不得进入可 Apply DesignSpec |
| 用户只给字段名、指标名或别名 | `knowledge/reverse_index/field_to_metrics.md` | `knowledge/reverse_index/metric_to_raw_sql.md`、对应 metrics/dashboard 文档 | 反向索引只定位候选文档，最终口径回到 metrics/dashboard |
| 用户只给表名，问哪些看板用到 | `knowledge/reverse_index/table_to_dashboards.md` | `knowledge/01_table_index.md`、对应 dashboard 文档 | 表被引用不代表所有看板可复用同一范围或 join |
| SQL 结果为空、某期次/顾问/渠道查不到 | `knowledge/reverse_index/join_risk_index.md` | `knowledge/joins/table_relationships.md`、对应表文档 | 先排查主表有无数据、范围过滤、join anti-check，再判断业务无数据 |
| SQL 报错、平台函数问题 | `knowledge/00_global_rules.md` | `knowledge/sql_patterns/presto_date_partition_patterns.md`、`scripts/validate_sql_rules.py` | 禁用三参数 `date_add`；AST 检查器逐个 SELECT/CTE 核对物理表 `dt`、`hour` 和业务范围，不用外层过滤替代内层范围，也不把 `SELECT DISTINCT` 与其他查询块的 GROUP BY 混检 |
| 入库新的青橙看板 SQL | `SKILL.md` 的知识库维护流程 | `scripts/ingest_dashboard_sql.py`、`scripts/build_reverse_indexes.py`、`scripts/check_skill_integrity.py` | 自动解析只是草稿；人工核对后再更新索引和 changelog |

## 路由原则

- 先做 domain resolution，再按 `domain_manifest -> contract_index -> 命中契约 -> source_path` 渐进披露；`domain != qingcheng` 时停止本 Skill 的业务检索。
- 契约解析后依次形成 QuerySpec 与 QueryPlan；只有全部命中项为 `confirmed`、必填 unresolved slot 已清空且单基础表无 join 时，才可自动 compile。
- `pending_confirmation`、别名歧义和多表 join 必须停在计划或 probe 阶段；反向索引只定位候选，最终证据回到 domain-local metrics/dashboard/raw SQL。
- 简单字段或表结构问题：读 `quick_reference.md`、`01_table_index.md`、相关 `tables/*.md` 或 `temp_tables/*.md`。
- 指标或看板口径问题：先读对应 `dashboards/*.md` 和 `metrics/*.md`；如果问题涉及看板自定义公式、字段展示名或透视表聚合，再读 `knowledge/dashboard_web_profiles/edit_metrics/` 和 `knowledge/metrics/qingcheng_dashboard_metric_formula_linkage.md`。
- 看板设计或编辑问题：只在域内语义已确认后读取 `knowledge/sql_patterns/dashboard_design_change_workflow.md`；依次执行 profile、DesignSpec、ChangePlan/diff、dry-run。Apply 与 publish 必须由 operator 独立命令完成，不能由业务 Skill 授权。
- 反向排查问题：先读 `knowledge/reverse_index/`，再进入具体文档，不要全量读取知识库。
- 结果异常或 debug：优先构造分层诊断 SQL，顺序为分区新鲜度、范围过滤、主表驱动、join anti-check、聚合粒度、前端聚合。
- 任何跨域来源都必须标注 `待人工确认`，除非用户明确确认青橙复用。
