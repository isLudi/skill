# 临时表知识维护账号迁移

本流程只维护已登记业务 Skill 的本地知识。明确确认维护账号变更后，将同后缀的 `temp_table.dingxi01_*` 迁移至 `temp_table.lvshuai01_*`。不上传、删除或改名线上表，不改写业务 Skill 的 raw SQL 目录或 Web BI 原始画像，也不提交或推送 Git。

原表没有独立文档时，只能以显式 `merged_markdown` 新建原本不存在的目标文档，同时绑定两个路径的存在性；不把缺少文档当作任意删除或覆盖许可。增量计划保留已有迁移映射，不能用单表补充请求覆盖整份登记，也不能静默替换已有映射。

`plan-temp-table-knowledge-migration` 的 `--input` 为 UTF-8 JSON：`schema_version=1.0.0`、`as_of=YYYY-MM-DD`、`maintenance_change_confirmed=true`、`mappings` 数组。每项含 `target=qingcheng|market`、`old_table`、`new_table`。目标文档已存在时必须提供完整、人工审阅的 `merged_markdown`，不能自动覆盖或机械拼接。

物理更名不保证业务来源等价。若当前生产改用另一张本域已有表，mapping 可额外声明 `current_reference_table` 和 `production_evidence`。每条证据绑定 `dataset_id`、`model_id`、完整保存 SQL 的 `sql_sha256`；Plan 与 Apply 都通过 DataCenterClient 只读重取精确数据集，并以 AST 验证实际引用。Hash 或来源不符则停止，不凭目录存在决定业务替代。物理副本仍有独立文档，可标为不完整且禁止默认复用。

用户明确要求移除不完整副本的知识文档时，可对已有迁移 mapping 声明 `retire_destination=true`。必须已有精确迁移记录、旧文档已移除、新文档仍存在，并有独立当前来源及生产 SQL Hash 证据。只删除本地副本文档和当前索引入口，迁移登记保留历史身份及退役标记，链接指向当前来源；不会删除线上表。

必要的业务纠正用可选 `document_updates`：每项明确 `target`、本域知识 Markdown 的相对 `path`、`before_sha256` 和完整 `content`。新文档的前置 Hash 为 null；现有文档必须精确匹配。该入口不能修改脚本、权限、SQL、历史更新日志或原始画像，重复目标拒绝。所有内容仍由精确 Plan Hash 和维护确认绑定。

迁移后的源文档纠正或规范换行可以只提供 `document_updates` 和空的 `mappings`；仍由注册域解析、精确源 Hash、维护确认、相同独占锁及全栈门禁保护，不构成任意文件编辑入口。

Plan 通过 USQL 精确账号区段和 getAuth 验证 `lvshuai01`，只读临时表列表并要求新表唯一 ID。它绑定两域注册 metadata、所有知识/契约/SQL 源 Hash、目标文件存在性、明确合并内容、线上新表 ID 和迁移代码 Hash；计划仅写 runtime。新表名存在不代表本次数据、字段类型、唯一性或刷新已验证，业务结构沿用仍须用户确认。

`apply-temp-table-knowledge-migration` 消费 Plan `--input`、精确 `--plan-sha256`、`--confirm-skill-maintenance`、新建的 runtime `--artifacts-dir` 及 `--output`。重新读取线上 ID；使用与 Data Center 本地同步相同的仓库级独占锁，拒绝旧锁，不自动清理。复核全部源 Hash并重建同一计划，漂移时零写入停止。基线 ZIP 和回执保存在 Git 外。任何失败均恢复本次受影响文件及生成物；检测到第三状态时不覆盖并发改动并报告恢复阻断。

当前文档和契约使用新表名，重复文档按审阅内容合并，原文档删除。历史 changelog 只修复指向已迁移文档的链接，不改写旧事实；SQL 和原始画像保持原文。每域生成临时表维护迁移说明和语义迁移登记，明确新旧映射及历史证据边界。旧 SQL 是历史/线上快照，不得因本次知识迁移声称线上消费者已更新。

Apply 内强制重建域内反向索引、catalog，再运行完整 Text2SQL 栈；失败不能用成功回执交付。更新其他已有临时表的维护人、改变表后缀或跨域语义迁移不在此适配器范围内。

共享目录可能改变其他域的生成边界清单，其输入与输出一并纳入 Hash、快照和恢复，但不改其他域业务源文件。旧名称只登记为历史别名：新 SQL 的 AST 验证默认阻断；历史快照审计须显式选择历史名称模式，且跨域限制仍生效。
