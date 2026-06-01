# Web BI 看板结构快照

本目录存放通过 `usql-web-query-operator/scripts/read_dashboard.py` 从自助 BI 页面抽取的看板结构摘要。

- 只保存页面结构、组件单元、筛选器、字段/指标、刷新任务 ID 和行数/序列计数。
- 不保存查询结果明细行，不替代 `knowledge/dashboards/*.md` 中的 SQL 业务口径。
- 当用户问题涉及“页面上有哪些筛选器/组件/字段/下载按钮/刷新任务”时，先读本目录；当问题涉及 SQL 口径、表、join、指标公式时，再读 dashboards/metrics/tables。

## 已入库快照

| 看板 | 文件 | dashboard_id |
|---|---|---|
| 外呼过程数据看板 | `outbound_call_process_dashboard_web_profile.md` | `dashboard_3730722176629411841` |
| 市场顾问--评优看板 | `market_consultant_evaluation_web_profile.md` | `dashboard_3822396843512627200` |
| 市场顾问-进量节奏 | `market_consultant_volume_pace_web_profile.md` | `dashboard_3791961955008733184` |
| 市场顾问部_行课报表 | `market_consultant_attendance_report_web_profile.md` | `dashboard_3748410696516800512` |
| 昆仑山战役-暑期激励数据看板 | `kunlun_summer_incentive_web_profile.md` | `dashboard_3881610656431284224` |
| 转化数据 | `market_consultant_conversion_web_profile.md` | `dashboard_3767151344579387392` |
| 运营侧数据看板 | `operation_side_dashboard_web_profile.md` | `dashboard_3759973841100165121` |
