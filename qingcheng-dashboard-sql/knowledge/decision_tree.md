# 用户需求到知识库路由

> 先用本文件判断要读哪些知识，再进入具体表、指标、看板、join、反向索引或 SQL 模板。不要把本文件当完整口径来源。

| 用户说法 | 先读 | 再读 | 必要规则/踩坑 |
|---|---|---|---|
| 青橙有哪些表、某表能不能用于青橙 | `knowledge/04_qingcheng_project_profile.md` | `knowledge/01_table_index.md`、对应 `knowledge/tables/*.md` 或 `knowledge/temp_tables/*.md` | 不从市场顾问 skill 自动迁移表语义；公共表也要确认青橙范围字段 |
| 写青橙过程数据 SQL | `knowledge/dashboards/qingcheng_process_data_raw_20260522.md` | `knowledge/metrics/qingcheng_process_data_metrics.md`、`knowledge/joins/table_relationships.md` | 外呼、APP 登录、到课补充会改变粒度，先查 join 风险 |
| 写青橙到课 SQL | `knowledge/dashboards/qingcheng_daoke_raw_20260522.md` | `knowledge/metrics/qingcheng_daoke_metrics.md`、`knowledge/temp_tables/temp_table.dingxi01_qing_daoke.md` | 到课表 `qici + qudao + grade + begin_time` 唯一性待确认 |
| 写青橙转化 SQL、修复转化 SQL、修正暑期期次 | `knowledge/dashboards/qingcheng_conversion_raw_20260626.md` | `knowledge/metrics/qingcheng_conversion_metrics.md`、`knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`、`knowledge/sql_patterns/qingcheng_summer_qici_corrections.md` | 先确认业务日期范围、期次正则、`hour` 偏移和 `bb_dedup ↔ ud` join 粒度 |
| 写青橙渠道订单明细 SQL / 算绩效模板 SQL | `knowledge/dashboards/qingcheng_channel_order_detail_raw_20260627.md` | `knowledge/metrics/qingcheng_channel_order_detail_metrics.md`、`knowledge/joins/table_relationships.md` | 明细 SQL 必须说明 `ld` 范围限定、订单粒度和模板扩列字段 |
| 写青橙营收、团队完成度、个人转化 SQL | 对应 `knowledge/dashboards/qingcheng_*_raw_*.md` | 对应 `knowledge/metrics/*.md`、`knowledge/temp_tables/*.md`、`knowledge/sql_patterns/qingcheng_completion_sql_repair_checklist.md` | 先区分目标表驱动、架构表驱动和事实主表驱动；完成度三份 SQL 必须联动维护 |
| 排查个人/团队完成度与订单流水不一致 | `knowledge/sql_patterns/qingcheng_completion_sql_repair_checklist.md` | `knowledge/sql_patterns/qingcheng_personal_completion_discounted_output_risks.md`、`knowledge/dashboards/qingcheng_personal_conversion_raw_20260522.md`、`knowledge/metrics/qingcheng_personal_conversion_metrics.md`、`knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md` | 先查原始支付时间、`team_hist` 兜底、`gmv_t` 粒度、`is_internal_order_change` 和 service transfer 兜底，最后再看前端公式 |
| 追溯某批青橙 `lead_id` 最原始的来源线索 | `knowledge/sql_patterns/qingcheng_lead_origin_trace.md` | `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`、`knowledge/tables/service_dw.dm_crm_lead_stats_detail_hf.md` | 先抽样 20-50 条，再做全量导出；不要只看 `rule_name`；别把窗口别名写成 `rn` |
| 解释看板某个指标的前端公式、计算字段或与数据中心 SQL 的关系 | `knowledge/dashboard_web_profiles/edit_metrics/README.md` | `knowledge/metrics/qingcheng_dashboard_metric_formula_linkage.md`、对应当前 retained snapshot（如 `resources/raw_sql/data_center_qingcheng_2064_20260625.sql`） | 先确认看板组件和 BI 模型，再解析前端自定义公式，最后回到源 SQL 字段；不要把 `${指标}` 当物理字段 |
| 用户只给字段名、指标名或别名 | `knowledge/reverse_index/field_to_metrics.md` | `knowledge/reverse_index/metric_to_raw_sql.md`、对应 metrics/dashboard 文档 | 反向索引只定位候选文档，最终口径回到 metrics/dashboard |
| 用户只给表名，问哪些看板用到 | `knowledge/reverse_index/table_to_dashboards.md` | `knowledge/01_table_index.md`、对应 dashboard 文档 | 表被引用不代表所有看板可复用同一范围或 join |
| SQL 结果为空、某期次/顾问/渠道查不到 | `knowledge/reverse_index/join_risk_index.md` | `knowledge/joins/table_relationships.md`、对应表文档 | 先排查主表有无数据、范围过滤、join anti-check，再判断业务无数据 |
| SQL 报错、平台函数问题 | `knowledge/00_global_rules.md` | `knowledge/sql_patterns/presto_date_partition_patterns.md`、`scripts/validate_sql_rules.py` | 禁用三参数 `date_add`，分区表必须加 `dt`，小时表说明 `hour` 逻辑 |
| 入库新的青橙看板 SQL | `SKILL.md` 的知识库维护流程 | `scripts/ingest_dashboard_sql.py`、`scripts/build_reverse_indexes.py`、`scripts/check_skill_integrity.py` | 自动解析只是草稿；人工核对后再更新索引和 changelog |

## 路由原则

- 简单字段或表结构问题：读 `quick_reference.md`、`01_table_index.md`、相关 `tables/*.md` 或 `temp_tables/*.md`。
- 指标或看板口径问题：先读对应 `dashboards/*.md` 和 `metrics/*.md`；如果问题涉及看板自定义公式、字段展示名或透视表聚合，再读 `knowledge/dashboard_web_profiles/edit_metrics/` 和 `knowledge/metrics/qingcheng_dashboard_metric_formula_linkage.md`。
- 反向排查问题：先读 `knowledge/reverse_index/`，再进入具体文档，不要全量读取知识库。
- 结果异常或 debug：优先构造分层诊断 SQL，顺序为分区新鲜度、范围过滤、主表驱动、join anti-check、聚合粒度、前端聚合。
- 任何跨域来源都必须标注 `待人工确认`，除非用户明确确认青橙复用。
