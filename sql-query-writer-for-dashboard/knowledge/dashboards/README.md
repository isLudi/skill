# dashboards 知识库

存放历史看板 SQL 解析结果。每个看板一个 Markdown 文件，记录：

- 看板名称
- SQL 来源文件
- 使用表
- CTE 列表
- join key
- where 条件
- group by 维度
- 聚合指标
- 待确认口径

新增 SQL 放入 `resources/raw_sql/` 后运行：

```bash
python scripts/ingest_dashboard_sql.py
```

## 已入库看板

- `market_consultant_conversion.md`：市场顾问转化看板，来源 `resources/raw_sql/market_consultant_conversion.sql`。
- `market_consultant_lead_conversion_attendance.md`：市场顾问线索转化到课看板，来源 `resources/raw_sql/market_consultant_lead_conversion_attendance.sql`。
- `traffic_profile.md`：流量画像看板，来源 `resources/raw_sql/traffic_profile.sql`；2026-05-15 已按 `city_channel.txt` 更新为省份/城市维度版本。
- `refund_multi_subject_user_ratio.md`：多科用户退费占比看板，来源 `resources/raw_sql/refund_multi_subject_user_ratio.sql`。
- `refund_subject_product.md`：退费科目产品看板，来源 `resources/raw_sql/refund_subject_product.sql`。
- `refund_reason_analysis.md`：退费原因分析看板，来源 `resources/raw_sql/refund_reason_analysis.sql`。
- `outbound_call_process_dashboard.md`：外呼过程数据看板，来源 `resources/raw_sql/outbound_call_process_dashboard.sql`。
- `lead_assign_plan_actual_valid_count.md`：线索分配计划与实际有效量看板，来源 `resources/raw_sql/lead_assign_plan_actual_valid_count.sql`。
- `consultant_sales_ranking_evaluation.md`：顾问销售评优看板，来源 `resources/raw_sql/consultant_sales_ranking_evaluation.sql`。
- `consultant_sales_department_tenure.md`：顾问部门任职期销售统计，来源 `resources/raw_sql/consultant_sales_department_tenure.sql`。
- `consultant_sales_department_tenure_period_20260424.md`：顾问部门任职期销售统计 20260424 期过滤版本，来源 `resources/raw_sql/consultant_sales_department_tenure_period_20260424.sql`。
- `h_biz_line_department_conversion.md`：H业务线二级部门转化看板，来源 `resources/raw_sql/h_biz_line_department_conversion.sql`；2026-05-24 入库，覆盖市场部、精品班学部、青橙项目部、菁英班学部四个二级部门的渠道-规则-年级-部门级转化汇总。
- `market_channel_conversion_profile.md`：市场渠道用户画像分析，来源三份 raw SQL：`market_channel_conversion_profile_call_duration_dataset.sql`、`market_channel_conversion_profile_learn_duration_dataset.sql`、`market_channel_conversion_profile_deep_stage_dataset.sql`；2026-06-06 入库，分别用于首 call 通时、上课时长、深沟阶段三个过程分桶数据集。

## Web BI 结构快照

当问题涉及自助 BI 页面上的筛选器、组件、字段 ID、下载按钮、刷新任务 ID 或行数/序列计数时，读取 `knowledge/dashboard_web_profiles/README.md` 及对应看板快照。该目录只记录 Web 前端结构，不替代本目录中的 SQL 业务口径。

已通过 `usql-web-query-operator/scripts/read_dashboard.py profile-folder` 刷新并入库的市场顾问数据看板：

- `knowledge/dashboard_web_profiles/outbound_call_process_dashboard_web_profile.md`：外呼过程数据看板。
- `knowledge/dashboard_web_profiles/market_consultant_attendance_report_web_profile.md`：市场顾问部_行课报表。
- `knowledge/dashboard_web_profiles/operation_side_dashboard_web_profile.md`：运营侧数据看板。
- `knowledge/dashboard_web_profiles/market_consultant_conversion_web_profile.md`：转化数据。
- `knowledge/dashboard_web_profiles/market_consultant_volume_pace_web_profile.md`：市场顾问-进量节奏。
- `knowledge/dashboard_web_profiles/market_consultant_evaluation_web_profile.md`：市场顾问--评优看板。
- `knowledge/dashboard_web_profiles/kunlun_summer_incentive_web_profile.md`：昆仑山战役-暑期激励数据看板。
