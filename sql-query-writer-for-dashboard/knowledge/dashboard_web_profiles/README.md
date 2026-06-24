# Web BI 看板结构快照

本目录存放通过 `usql-web-query-operator/scripts/read_dashboard.py` 从自助 BI 页面抽取的看板结构摘要。

- 只保存页面结构、组件单元、筛选器、字段/指标、刷新任务 ID 和行数/序列计数。
- 不保存查询结果明细行，不替代 `knowledge/dashboards/*.md` 中的 SQL 业务口径。
- 当用户问题涉及“页面上有哪些筛选器/组件/字段/下载按钮/刷新任务”时，先读本目录；当问题涉及 SQL 口径、表、join、指标公式时，再读 dashboards/metrics/tables。
- 2026-06-24 已补充看板编辑页指标公式快照：`edit_metrics/README.md`。需要把前端指标含义、计算公式和数据中心 SQL 关联起来时，先读 `knowledge/metrics/market_consultant_dashboard_metric_formula_linkage.md`。

## 已入库快照

| 文件夹 | 看板 | 文件 | dashboard_id | 状态 |
|---|---|---|---|---|
| 市场顾问数据 | 11老板_运营侧数据看板 | `boss11_operation_side_dashboard_web_profile.md` | `dashboard_3833805337379700736` | ✅ 成功 |
| 市场顾问数据 | KOC渠道播报数据 | `dashboard_3952506916510425088_web_profile.md` | `dashboard_3952506916510425088` | ✅ 成功 |
| 市场顾问数据 | 【新人】前期过程转化数据 | `newcomer_early_stage_process_conversion_web_profile.md` | `dashboard_3874439982521286657` | ✅ 成功 |
| 市场顾问数据 | 到课数据-顾问维度 | `consultant_attendance_data_dimension_web_profile.md` | `dashboard_3706108893345009664` | ✅ 成功 |
| 市场顾问数据 | 外呼过程数据看板 | `outbound_call_process_dashboard_web_profile.md` | `dashboard_3730722176629411841` | ✅ 成功 |
| 市场顾问数据 | 多维度时效分析-抖咨 | `multi_dimensional_timeliness_analysis_douzi_web_profile.md` | `dashboard_3861041931986931712` | ✅ 成功 |
| 市场顾问数据 | 市场顾问--评优看板 | `market_consultant_evaluation_web_profile.md` | `dashboard_3822396843512627200` | ✅ 成功 |
| 市场顾问数据 | 市场顾问-用户画像分析 | `market_consultant_user_profile_analysis_web_profile.md` | `dashboard_3804681042591760385` | ✅ 成功 |
| 市场顾问数据 | 市场顾问-进量节奏 | `market_consultant_volume_pace_web_profile.md` | `dashboard_3791961955008733184` | ✅ 成功 |
| 市场顾问数据 | 市场顾问部_行课报表 | `market_consultant_attendance_report_web_profile.md` | `dashboard_3748410696516800512` | ✅ 成功 |
| 市场顾问数据 | 昆仑山战役-暑期激励数据看板 | `kunlun_summer_incentive_web_profile.md` | `dashboard_3881610656431284224` | ✅ 成功 |
| 市场顾问数据 | 测试 | `home_3955604854469165056_web_profile.md` | `home_3955604854469165056` | ✅ 成功 |
| 市场顾问数据 | 评优文字播报 | `evaluation_broadcast_text_web_profile.md` | `dashboard_3839499028752805888` | ✅ 成功 |
| 市场顾问数据 | 转化数据 | `market_consultant_conversion_web_profile.md` | `dashboard_3767151344579387392` | ✅ 成功 |
| 市场顾问数据 | 过程播报文字 | `process_broadcast_text_web_profile.md` | `dashboard_3845252580183867393` | ✅ 成功 |
| 市场顾问数据 | 过程数据--顾问维度 | `consultant_process_data_dimension_web_profile.md` | `dashboard_3699054046816116737` | ✅ 成功 |
| 市场顾问数据 | 运营侧数据看板 | `operation_side_dashboard_web_profile.md` | `dashboard_3759973841100165121` | ✅ 成功 |
