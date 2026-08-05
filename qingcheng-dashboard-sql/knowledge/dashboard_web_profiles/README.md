# Web BI 看板结构快照

本目录存放通过 `usql-web-query-operator/scripts/read_dashboard.py` 从自助 BI 页面抽取的看板结构摘要。

- 只保存页面结构、组件单元、筛选器、字段/指标、刷新任务 ID 和行数/序列计数。
- 不保存查询结果明细行，不替代 `knowledge/dashboards/*.md` 中的 SQL 业务口径。
- 当用户问题涉及“页面上有哪些筛选器/组件/字段/下载按钮/刷新任务”时，先读本目录；当问题涉及 SQL 口径、表、join、指标公式时，再读 dashboards/metrics/tables。

## 已入库快照

| 文件夹 | 看板 | 文件 | dashboard_id | 状态 |
|---|---|---|---|---|
| 青橙项目部 | P4C高级功能取证-20260718-1605-沙箱 | `dashboard_3994491256855117825_web_profile.md` | `dashboard_3994491256855117825` | ✅ 成功 |
| 青橙项目部 | P4C高级生产验收-20260718-1739-沙箱 | `dashboard_3994584279860838400_web_profile.md` | `dashboard_3994584279860838400` | ✅ 成功 |
| 青橙项目部 | TMK渠道线索析出及转化结果看板 | `dashboard_4018019033706541056_web_profile.md` | `dashboard_4018019033706541056` | ✅ 成功 |
| 青橙项目部 | TMK顾问线索析出及转化结果看板 | `dashboard_4007415299481022465_web_profile.md` | `dashboard_4007415299481022465` | ✅ 成功 |
| 青橙项目部 | 个人转化数据-青橙 | `qingcheng_personal_conversion_web_profile.md` | `dashboard_3873038327756636161` | ✅ 成功 |
| 青橙项目部 | 团队转化完成度-青橙 | `qingcheng_team_conversion_completion_web_profile.md` | `dashboard_3872626876332130305` | ✅ 成功 |
| 青橙项目部 | 完成度文字播报_青 | `qingcheng_completion_broadcast_text_web_profile.md` | `dashboard_3893277592797257728` | ✅ 成功 |
| 青橙项目部 | 转化数据看板 | `qingcheng_conversion_dashboard_web_profile.md` | `dashboard_3885764906392891392` | ✅ 成功 |
| 青橙项目部 | 过程数据报表-青橙 | `qingcheng_process_data_report_web_profile.md` | `dashboard_3733927793301065728` | ✅ 成功 |
| 青橙项目部 | 青橙-全域产品数据看板 | `qingcheng_all_product_dashboard_web_profile.md` | `dashboard_3852445620602875904` | ✅ 成功 |
| 青橙项目部 | 青橙-全年级营收看板 | `qingcheng_full_grade_revenue_dashboard_web_profile.md` | `dashboard_3865509979877412864` | ✅ 成功 |
| 青橙项目部 | 青橙-渠道过程数据-天 | `qingcheng_channel_process_daily_web_profile.md` | `dashboard_3910621974690701312` | ✅ 成功 |
| 青橙项目部 | 青橙渠道分周期转化 | `qingcheng_dousi_conversion_web_profile.md` | `dashboard_3884629814875697153` | ✅ 成功 |
| 青橙项目部 | 青橙用户退费画像 | `dashboard_4020796953570476033_web_profile.md` | `dashboard_4020796953570476033` | ✅ 成功 |
| 青橙项目部 | 青橙运营侧看板 | `dashboard_4019042032853901313_web_profile.md` | `dashboard_4019042032853901313` | ✅ 成功 |
| 青橙项目部 | 青橙项目部_行课报表 | `qingcheng_attendance_report_web_profile.md` | `dashboard_3765824192103694336` | ✅ 成功 |
