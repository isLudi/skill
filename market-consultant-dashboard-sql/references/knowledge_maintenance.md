# 市场顾问部知识维护

仅在用户明确授权本域知识维护时读取。文中的 `knowledge/`、`resources/`、`semantic/`、`scripts/` 均相对本 Skill 根目录。

## 5. 维护入口

新增或修改 SQL 时按 [SQL 质量验证](sql_quality.md) 区分文本变化与逻辑变化。来源 Hash、领域归属、受影响契约与生成索引仍须一致；验证命令按 [维护验证](../../references/maintenance-verification.md) 去重。

- 新增或刷新物理表字段时，统一调用 `usql-web-query-operator sync-datamap-fields`。先 dry-run 核对目标表、字段缺口、类型和说明，再显式 `--write`；物理字段以天工数据地图及 DDL 返回为准，业务含义、范围、Join 和指标仍由本 Skill 的 confirmed contract 与业务文档治理。不要在本 Skill 中保存或解析表结构 PDF、截图、页面渲染图或手工字段目录 JSON。
- 新增或刷新 Web BI 结构快照时，`profile-dashboard`、`profile-folder` 和默认 `profile-all` 只写 runtime。只有用户明确要求市场顾问知识维护后，才可运行 `profile-all --write-knowledge --confirm-skill-maintenance`；目标固定路由到本 Skill，任一画像失败时整批不写，且不得把青橙快照混入本目录。
- 新增看板 SQL：放入 `resources/raw_sql/`，运行 `scripts/ingest_dashboard_sql.py` 并人工核对业务文档；依次运行 `scripts/build_reverse_indexes.py`、仓库级 `../scripts/build_text2sql_catalog.py`、`scripts/check_skill_integrity.py`，最后用 `scripts/text2sql.py` 校验相关 QuerySpec、QueryPlan 与 SQL。`semantic/domain_manifest.json` 和 `semantic/generated/contract_index.json` 都是生成物，不手工编辑。
- 数据中心 SQL 只允许稳定路径 `resources/raw_sql/data_center_market_<model_id>.sql`；current model 与语义槽位登记在 `semantic/current_model_bindings.json`。刷新必须通过 operator 的 `sync-data-center-sql` dry-run 获取精确计划哈希，再用 `--write --expected-plan-sha256 <hash>` 原子替换；禁止手工新增日期副本。Apply 后强制执行反向索引、共享 catalog、唯一版本审计、integrity 和完整栈验证，失败自动回滚。
- 新增或修改 `semantic/contracts/*.json` 时，必须引用本域现有 `source_path` 和精确 SHA-256；业务证据不足的条目标为 `pending_confirmation`。更新后运行仓库级 catalog builder 生成 contract index，再运行域内完整性与离线 resolution eval；不得只刷新哈希而不核对业务变化。
- 新增指标口径时，必须落入 `knowledge/metrics/`、对应 dashboard/raw SQL 和 semantic contract，并绑定可复核证据；临时截图或页面图片只允许放在 runtime 调试目录，不作为本 Skill 的长期权威来源。
- 模板取数 raw SQL 只维护线上 `published` 版本的一个 stable canonical 文件：`resources/raw_sql/template_query_market_<logical_name>.sql`。日期后缀模板文件属于历史副本，禁止作为路由入口或继续留在活跃知识库；同步必须使用 operator 的 `sync-template-sql`，先回读精确模板 ID/名称和 SQL SHA-256，再以 reviewed plan hash 原位覆盖并清理旧副本。保存后必须更新本清单、反向索引、共享 catalog、唯一版本审计、域内 integrity 和完整 Text2SQL 栈。
- 更新市场顾问最新渠道 CASE 时，如果来源文件名包含日期后缀，例如 `D:\Feishu\MMDD.txt`，归档 SQL 文件名必须同步使用相同后缀：`resources/raw_sql/market_channel_case_when_MMDD.sql`。后续若来源日期变化，应将旧归档重命名或替换为新的 `market_channel_case_when_MMDD.sql`，同步更新所有知识库引用、`knowledge/sql_patterns/channel_mapping_case_when.md` 和更新日志；不得保留过期日期后缀作为最新入口。
- 共享渠道 CASE 的消费者以 `knowledge/sql_patterns/channel_mapping_case_when.md` 与 `knowledge/dashboards/template_query_market_datasets.md` 的当前登记为准，包括模板 `7689`。更新 CASE 时识别全部登记消费者的影响，回读现状并准备差异；本地知识维护授权不自动授权线上更新、发布或执行。只有相应目标和阶段已获明确授权，才通过 operator 模板计划/Apply/Publish 流程实施，保持模板 id、申请关系、参数、期次逻辑、来源表和最终字段不变。已授权发布与真实期次验证完成后，再刷新获授权维护的模板 canonical SQL 和清单；其余消费者明确标记待同步。Data Center 定向覆盖仅在业务明确提升为共享规则或要求模板吸收时进入模板。
- 更新记录写入 `knowledge/update_log/changelog.md`，必须按时间正序追加在文件末尾；不要把新记录插到文件顶部。同一天多次维护按发生顺序继续向后追加，必要时使用 `YYYY-MM-DD HH:mm:ss` 标题区分顺序。
