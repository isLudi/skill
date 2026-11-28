# 临时表维护迁移

核实日期：2026-11-28。用户确认本次为维护账号变更，业务结构基本一致。

当前生成、修订 SQL 使用下列 lvshuai01 表名；旧维护人名称只作为历史来源，不再作为当前知识入口。
resources/raw_sql 中的线上/历史 SQL 快照保持原文；不把本次知识迁移描述成生产 SQL 已更新。
历史样本行数、Excel 扫描、旧 Query 及旧 SQL 的使用关系不能直接证明新表最新内容、唯一性或刷新状态。
两域共享物理表不代表共享业务口径；各自保留部门范围、Join 键及上传切片门禁。

| 原表名（历史） | 当前表名 | 线上表 ID | 当前文档 |
|---|---|---|---|
| `temp_table.dingxi01_ceshiqudao_pingyou` | temp_table.lvshuai01_ceshiqudao_pingyou | `16498` | [temp_table.lvshuai01_ceshiqudao_pingyou](tables/temp_table.lvshuai01_ceshiqudao_pingyou.md) |
| `temp_table.dingxi01_channel_group` | temp_table.lvshuai01_channel_group | `16486` | [temp_table.lvshuai01_channel_group](tables/temp_table.lvshuai01_channel_group.md) |
| `temp_table.dingxi01_cost` | temp_table.lvshuai01_cost | `16488` | [temp_table.lvshuai01_cost](tables/temp_table.lvshuai01_cost.md) |
| `temp_table.dingxi01_daoke_1_6_t` | temp_table.lvshuai01_daoke_1_6_t | `16489` | [temp_table.lvshuai01_daoke_1_6_t](tables/temp_table.lvshuai01_daoke_1_6_t.md) |
| `temp_table.dingxi01_jiagou_db` | temp_table.lvshuai01_jiagou_db | `14050` | [temp_table.lvshuai01_jiagou_db](tables/temp_table.lvshuai01_jiagou_db.md) |
| `temp_table.dingxi01_jiagou_zx` | temp_table.lvshuai01_jiagou_zx | `14049` | [temp_table.lvshuai01_jiagou_zx](tables/temp_table.lvshuai01_jiagou_zx.md) |
| `temp_table.dingxi01_jinliang_goal` | temp_table.lvshuai01_jinliang_goal | `16490` | [temp_table.lvshuai01_jinliang_goal](tables/temp_table.lvshuai01_jinliang_goal.md) |
| `temp_table.dingxi01_pingyou_jg` | 已删除副本文档；当前使用 temp_table.zhangjunyan01_pingyou_jg | `14059` | [temp_table.zhangjunyan01_pingyou_jg](tables/temp_table.zhangjunyan01_pingyou_jg.md) |
| `temp_table.dingxi01_plan_id` | temp_table.lvshuai01_plan_id | `16491` | [temp_table.lvshuai01_plan_id](tables/temp_table.lvshuai01_plan_id.md) |

业务来源例外：`temp_table.lvshuai01_pingyou_jg` 不作为完整业务来源，当前引用改用 `temp_table.zhangjunyan01_pingyou_jg`；按精确线上 SQL Hash 重新验证，不据前缀推断等价。
