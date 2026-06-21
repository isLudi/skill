# 快速参考卡

> 80% 高频青橙取数入口。只用于快速定位，生成 SQL 前仍需读取对应表、指标、看板、join、范围或反向索引文档。

## 高频看板入口

| 用户需求 | 先读 | 再读 | 关键风险 |
|---|---|---|---|
| 青橙过程数据、有效线索、外呼、APP 登录 | `knowledge/dashboards/qingcheng_process_data_raw_20260522.md` | `knowledge/metrics/qingcheng_process_data_metrics.md`、`knowledge/joins/table_relationships.md` | 外呼和 APP 登录补充可能按用户粒度放大线索 |
| 青橙到课、第 1-6 讲到课、有效到课 | `knowledge/dashboards/qingcheng_daoke_raw_20260522.md` | `knowledge/metrics/qingcheng_daoke_metrics.md`、`knowledge/temp_tables/temp_table.dingxi01_qing_daoke.md` | 课次映射表唯一性和渠道/年级/开课时间匹配待确认 |
| 青橙转化、青橙订单、净营收、破单 | `knowledge/dashboards/qingcheng_conversion_raw_20260615.md` | `knowledge/metrics/qingcheng_conversion_metrics.md`、`knowledge/sql_patterns/qingcheng_channel_grade_mapping.md` | `rule_name` 正则期次、跨 CTE hour 偏移、最新团队架构补历史数据 |
| 青橙渠道订单明细 | `knowledge/dashboards/qingcheng_channel_order_detail_raw_20260613.md` | `knowledge/metrics/qingcheng_channel_order_detail_metrics.md`、`knowledge/joins/table_relationships.md` | `ld` 子查询范围限定和 `lead_id + employee` 唯一性待确认 |
| 青橙年季月营收 | `knowledge/dashboards/qingcheng_revenue_year_quarter_month_raw_20260522.md` | `knowledge/metrics/qingcheng_revenue_year_quarter_month_metrics.md`、`knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md` | 组织链姓名匹配、调课调班去重和平台函数风险 |
| 青橙团队完成度月/期 | `knowledge/dashboards/qingcheng_team_completion_month_raw_20260522.md` 或 `knowledge/dashboards/qingcheng_team_completion_period_raw_20260522.md` | 对应 metrics、`knowledge/temp_tables/temp_table.dingxi01_qing_team_goal.md`、`knowledge/temp_tables/temp_table.dingxi01_qing_team_g_qi.md` | 目标表层级、期次月份映射和 H/非 H 折算待确认 |
| 青橙个人转化 | `knowledge/dashboards/qingcheng_personal_conversion_raw_20260522.md` | `knowledge/metrics/qingcheng_personal_conversion_metrics.md`、`knowledge/temp_tables/temp_table.dingxi01_qing_team_jg.md` | 架构表一人一期唯一性和个人业绩重复计算风险 |
| 青橙转化宽表-市场渠道 | `knowledge/dashboards/qingcheng_conversion_wide_table_market_channel_20260611.md` | `knowledge/metrics/qingcheng_conversion_wide_table_market_channel_metrics.md`、`knowledge/temp_tables/temp_table.shenbaoxin_channel_group.md` | 大 CASE 顺序、F 类外呼 join 语义和渠道分组唯一性待确认 |

## 高频排查入口

| 用户需求 | 先读 | 再读 | 关键风险 |
|---|---|---|---|
| 追溯某批 `lead_id` 的原始来源 / 原始分配线索 | `knowledge/sql_patterns/qingcheng_lead_origin_trace.md` | `knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md`、`knowledge/tables/service_dw.dm_crm_lead_stats_detail_hf.md` | 不要把 `rule_name` 当原始来源；`rule_name like '%公开课%'` 可能为 0；窗口别名不要写成 `rn` |

## 高频表与临时表

| 表 | 常见场景 | 优先动作 |
|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | 青橙线索、渠道、转化主表 | 先确认 `dt/hour`、青橙范围字段和最新分区；若是追溯原始来源，先读 `knowledge/sql_patterns/qingcheng_lead_origin_trace.md` |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | 青橙订单、收入、退款、净营收 | 用订单侧业绩部门过滤时，说明是否依赖订单侧范围兜底 |
| `finance_dw.app_finance_performance_extend_details_hf` | 年季月营收、团队完成度、个人转化 | 先确认金额单位、交易类型和任职期间 join |
| `temp_table.dingxi01_qing_team_jg` | 青橙团队架构 | 区分最新架构和期次架构，不默认补历史数据 |
| `temp_table.dingxi01_jiagou_db` | 过程/到课架构补充 | 姓名 key 和邮箱前缀 key 不一致时先查 join 风险 |
| `temp_table.dingxi01_qing_daoke` | 到课课次映射 | 检查 `qici + qudao + grade + begin_time` 唯一性 |
| `temp_table.shenbaoxin_channel_group` | 青橙转化宽表渠道大类 | 来源、字段结构和 `channel` 唯一性均待确认 |

## 反向定位入口

| 已知线索 | 读取 |
|---|---|
| 已知字段或指标别名，想找影响哪些指标 | `knowledge/reverse_index/field_to_metrics.md` |
| 已知表，想找哪些看板或 raw SQL 使用 | `knowledge/reverse_index/table_to_dashboards.md` |
| 已知指标文档，想找来源 raw SQL | `knowledge/reverse_index/metric_to_raw_sql.md` |
| SQL 结果异常、join 后变 0、行数放大 | `knowledge/reverse_index/join_risk_index.md`，再读 `knowledge/joins/table_relationships.md` |

## 强制前置规则

- 先读 `knowledge/04_qingcheng_project_profile.md`，确认青橙隔离边界。
- 先读 `knowledge/00_global_rules.md` 和 `knowledge/03_range_limit_rules.md`，再写生产 SQL。
- 涉及字段、指标、看板反向追溯时，先读 `knowledge/reverse_index/`，再进入具体文档。
- 遇到 `待人工确认` 不得用市场顾问侧口径补齐，除非用户明确确认青橙复用。
