# metrics 知识库

每个指标一个 Markdown 文件。指标口径必须来自以下来源之一：

- 历史看板 SQL
- 指标定义文档
- 用户明确说明

如果口径来自图片或不完整 SQL，必须标记“待人工确认”。

## 已入库指标集合

- `market_consultant_conversion_metrics.md`：市场顾问转化看板指标集合。
- `market_consultant_lead_conversion_attendance_metrics.md`：市场顾问线索转化到课指标集合。
- `traffic_profile_metrics.md`：流量画像指标集合；2026-05-15 已补充省份/城市维度口径。
- `refund_analysis_metrics.md`：历史退费分析指标集合，当前退费率优先在 `market_channel_conversion_profile_metrics.md` 的多维退费率章节维护。
- `outbound_call_process_metrics.md`：外呼过程数据看板指标集合。
- `lead_assign_plan_actual_valid_count_metrics.md`：线索分配计划与实际有效量指标集合。
- `consultant_sales_ranking_evaluation_metrics.md`：顾问销售评优指标集合。
- `consultant_sales_department_tenure_metrics.md`：顾问部门任职期销售指标集合。
- `consultant_sales_department_tenure_period_20260424_metrics.md`：顾问部门任职期销售 20260424 期指标集合。
- `h_biz_line_department_conversion_metrics.md`：H业务线二级部门转化指标集合。
- `market_channel_conversion_profile_metrics.md`：市场渠道用户画像分析指标集合，覆盖首 call 通时、上课时长、深沟阶段、整体画像和多维退费率数据集；比例/单效/退费率类总计必须在透视表用可加和分子分母字段重算。
