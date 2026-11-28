# 临时表维护迁移

核实日期：2026-11-28。用户确认本次为维护账号变更，业务结构基本一致。

当前生成、修订 SQL 使用下列 lvshuai01 表名；旧维护人名称只作为历史来源，不再作为当前知识入口。
resources/raw_sql 中的线上/历史 SQL 快照保持原文；不把本次知识迁移描述成生产 SQL 已更新。
历史样本行数、Excel 扫描、旧 Query 及旧 SQL 的使用关系不能直接证明新表最新内容、唯一性或刷新状态。
两域共享物理表不代表共享业务口径；各自保留部门范围、Join 键及上传切片门禁。

| 原表名（历史） | 当前表名 | 线上表 ID | 当前文档 |
|---|---|---|---|
| `temp_table.dingxi01_jiagou_db` | temp_table.lvshuai01_jiagou_db | `14050` | [temp_table.lvshuai01_jiagou_db](temp_tables/temp_table.lvshuai01_jiagou_db.md) |
| `temp_table.dingxi01_qing_daoke` | temp_table.lvshuai01_qing_daoke | `16496` | [temp_table.lvshuai01_qing_daoke](temp_tables/temp_table.lvshuai01_qing_daoke.md) |
| `temp_table.dingxi01_qing_goal` | temp_table.lvshuai01_qing_goal | `16492` | [temp_table.lvshuai01_qing_goal](temp_tables/temp_table.lvshuai01_qing_goal.md) |
| `temp_table.dingxi01_qing_qi_moth` | temp_table.lvshuai01_qing_qi_moth | `16499` | [temp_table.lvshuai01_qing_qi_moth](temp_tables/temp_table.lvshuai01_qing_qi_moth.md) |
| `temp_table.dingxi01_qing_team_g_qi` | temp_table.lvshuai01_qing_team_g_qi | `16493` | [temp_table.lvshuai01_qing_team_g_qi](temp_tables/temp_table.lvshuai01_qing_team_g_qi.md) |
| `temp_table.dingxi01_qing_team_goal` | temp_table.lvshuai01_qing_team_goal | `16494` | [temp_table.lvshuai01_qing_team_goal](temp_tables/temp_table.lvshuai01_qing_team_goal.md) |
| `temp_table.dingxi01_qing_team_jg` | temp_table.lvshuai01_qing_team_jg | `16495` | [temp_table.lvshuai01_qing_team_jg](temp_tables/temp_table.lvshuai01_qing_team_jg.md) |
| `temp_table.dingxi01_qing_zz` | temp_table.lvshuai01_qing_zz | `16487` | [temp_table.lvshuai01_qing_zz](temp_tables/temp_table.lvshuai01_qing_zz.md) |
