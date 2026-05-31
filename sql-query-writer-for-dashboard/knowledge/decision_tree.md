# 用户需求到知识库路由

> 先用本文件判断要读哪些知识，再进入具体表、指标、看板、join 或踩坑文档。不要把本文件当完整口径来源。

| 用户说法 | 先读 | 再读 | 必要规则/踩坑 |
|---|---|---|---|
| 市场顾问转化、线索转化、GMV、净收、破单 | `knowledge/dashboards/market_consultant_conversion.md` | `knowledge/metrics/market_consultant_conversion_metrics.md`、`knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md` | `knowledge/sql_patterns/channel_mapping_case_when.md`、`knowledge/pitfalls/common_join_failures.md` |
| 线索转化到课、首节到课、AB 意向 | `knowledge/dashboards/market_consultant_lead_conversion_attendance.md` | `knowledge/metrics/market_consultant_lead_conversion_attendance_metrics.md`、`knowledge/tables/temp_table.dingxi01_daoke_1_6_t.md` | 到课表 key 和 `曹忆` 课次规则 |
| 流量画像、城市渠道、APP 登录、成交科目档位 | `knowledge/dashboards/traffic_profile.md` | `knowledge/metrics/traffic_profile_metrics.md`、`knowledge/sql_patterns/dashboard_query_patterns.md` | 外呼 join 未带 `lead_id`、财务成交科目 join 粒度 |
| 退费分析、多科退费、退费原因、科目产品退费 | `knowledge/metrics/refund_analysis_metrics.md` | `knowledge/dashboards/refund_multi_subject_user_ratio.md`、`knowledge/dashboards/refund_subject_product.md`、`knowledge/dashboards/refund_reason_analysis.md` | 财务表权限、退款正负号、三参数 `date_add` 改写 |
| 分配计划、计划分配量、实际有效量 | `knowledge/dashboards/lead_assign_plan_actual_valid_count.md` | `knowledge/tables/service_dw.dim_crm_assign_rule_lead_detail_hf.md`、`knowledge/tables/temp_table.dingxi01_plan_id.md` | `group_id` 不全局唯一，规则名拆期次风险 |
| 外呼过程、长通话、深沟、双沟、首 call 任务 | `knowledge/dashboards/outbound_call_process_dashboard.md` | `knowledge/sql_patterns/first_call_task_metric_pattern.md`、`knowledge/tables/service_dw.dwd_crm_assign_private_detail_hf.md` | 首 call 必须用任务表，API 验证需看权限 |
| 顾问销售评优、ROI、退费率、人产、排名 | `knowledge/dashboards/consultant_sales_ranking_evaluation.md` | `knowledge/metrics/consultant_sales_ranking_evaluation_metrics.md`、`knowledge/sql_patterns/dashboard_query_patterns.md` | 评优名单 vs 在职架构名单，不同输出粒度避免前端重复聚合 |
| H 业务线二级部门转化、跨二级部门对比 | `knowledge/dashboards/h_biz_line_department_conversion.md` | `knowledge/metrics/h_biz_line_department_conversion_metrics.md`、`knowledge/sql_patterns/first_call_task_metric_pattern.md` | 市场顾问看板和跨部门看板范围不同 |
| 某期次/经理/顾问查不到 | `knowledge/sql_patterns/dashboard_query_patterns.md` | 事实主表文档、名单/架构表文档、`knowledge/sql_patterns/usql_permission_boundaries.md` | 先判断事实主表驱动还是名单/架构表驱动 |
| JOIN 后指标为 0、行数放大、年级断裂 | `knowledge/pitfalls/common_join_failures.md` | `knowledge/joins/common_join_keys.md`、相关表文档 | `grade='0'` 通配、到课映射缺失、架构截面错位 |
| Python 调 USQL、API 执行、权限失败 | `knowledge/sql_patterns/usql_rest_api_python.md` | `knowledge/sql_patterns/usql_permission_boundaries.md`、`knowledge/01_table_index.md` | 区分接口连通、表权限、字段权限、行级范围和 SQL 语义错误 |

## 路由原则

- 简单表结构或字段问题：读 `quick_reference.md`、`01_table_index.md`、相关 `tables/*.md` 即可。
- 指标或看板口径问题：先读对应 `dashboards/*.md` 和 `metrics/*.md`，再补 join 或 SQL pattern。
- SQL 报错或结果异常：先读全局规则、范围限定、权限边界，再读相关 pitfalls。
- 生成新市场顾问渠道归因 SQL：默认使用 `resources/raw_sql/market_channel_case_when_0524.sql`，除非用户明确要求沿用历史 SQL 旧口径。
