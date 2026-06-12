# Web BI 看板结构快照

本目录存放通过 `usql-web-query-operator/scripts/read_dashboard.py` 从自助 BI 页面抽取的看板结构摘要。

- 只保存页面结构、组件单元、筛选器、字段/指标、刷新任务 ID 和行数/序列计数。
- 不保存查询结果明细行，不替代 `knowledge/dashboards/*.md` 中的 SQL 业务口径。
- 当用户问题涉及“页面上有哪些筛选器/组件/字段/下载按钮/刷新任务”时，先读本目录；当问题涉及 SQL 口径、表、join、指标公式时，再读 dashboards/metrics/tables。

## 已入库快照

| 文件夹 | 看板 | 文件 | dashboard_id | 状态 |
|---|---|---|---|---|
| 青橙播报 | 推送--转化-抖音私信 | `dashboard_3916483456733192193_web_profile.md` | `dashboard_3916483456733192193` | ✅ 成功 |
| 青橙播报 | 推送--转化-抖音私信_团 | `dashboard_3916517219847778305_web_profile.md` | `dashboard_3916517219847778305` | ✅ 成功 |
| 青橙播报 | 推送--转化-私域_ | `dashboard_3916532959832903681_web_profile.md` | `dashboard_3916532959832903681` | ✅ 成功 |
| 青橙播报 | 推送--转化-私域_团 | `dashboard_3916532003721617409_web_profile.md` | `dashboard_3916532003721617409` | ✅ 成功 |
| 青橙播报 | 推送--转化-进校 | `dashboard_3916546265268498433_web_profile.md` | `dashboard_3916546265268498433` | ✅ 成功 |
| 青橙播报 | 推送--转化-进校_团 | `dashboard_3916545163522686976_web_profile.md` | `dashboard_3916545163522686976` | ✅ 成功 |
| 青橙项目部 | 个人转化数据-青橙 | `qingcheng_personal_conversion_web_profile.md` | `dashboard_3873038327756636161` | ❌ 失败： |
| 青橙项目部 | 团队转化完成度-青橙 | `qingcheng_team_conversion_completion_web_profile.md` | `dashboard_3872626876332130305` | ❌ 失败： |
| 青橙项目部 | 完成度文字播报_青 | `qingcheng_completion_broadcast_text_web_profile.md` | `dashboard_3893277592797257728` | ❌ 失败： |
| 青橙项目部 | 转化数据看板 | `qingcheng_conversion_dashboard_web_profile.md` | `dashboard_3885764906392891392` | ❌ 失败： |
| 青橙项目部 | 过程数据报表-青橙 | `qingcheng_process_data_report_web_profile.md` | `dashboard_3733927793301065728` | ❌ 失败： |
| 青橙项目部 | 青-抖私-转化 | `qingcheng_dousi_conversion_web_profile.md` | `dashboard_3884629814875697153` | ❌ 失败： |
| 青橙项目部 | 青橙-全域产品数据看板 | `qingcheng_all_product_dashboard_web_profile.md` | `dashboard_3852445620602875904` | ❌ 失败： |
| 青橙项目部 | 青橙-全年级营收看板 | `qingcheng_full_grade_revenue_dashboard_web_profile.md` | `dashboard_3865509979877412864` | ❌ 失败： |
| 青橙项目部 | 青橙-渠道过程数据-天 | `qingcheng_channel_process_daily_web_profile.md` | `dashboard_3910621974690701312` | ❌ 失败： |
| 青橙项目部 | 青橙项目部_行课报表 | `qingcheng_attendance_report_web_profile.md` | `dashboard_3765824192103694336` | ❌ 失败： |
