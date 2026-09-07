# 青橙项目部知识维护

仅在用户明确授权本域知识维护时读取。文中的 `knowledge/`、`resources/`、`semantic/`、`scripts/` 均相对本 Skill 根目录。

## 5. 知识库维护流程

新增或修改 SQL 时按 [SQL 质量验证](sql_quality.md) 区分文本变化与逻辑变化。来源 Hash、领域归属、受影响契约与生成索引仍须一致；验证命令按 [维护验证](../../references/maintenance-verification.md) 去重。

新增青橙看板 SQL：

1. 普通青橙专题 SQL 保存到 `resources/raw_sql/`，可使用 `qingcheng_<看板英文名或拼音>_<YYYYMMDD>.sql`；数据中心 SQL 例外，只允许稳定路径 `data_center_qingcheng_<model_id>.sql`。
2. 运行 `scripts/ingest_dashboard_sql.py --sql-file <path>` 生成 `knowledge/dashboards/`、`knowledge/metrics/` 和 `knowledge/temp_tables/` 的初始文档。
3. 人工核对自动解析结果，把“待人工确认”补齐为青橙真实口径。
4. 更新 `knowledge/01_table_index.md`、`knowledge/joins/common_join_keys.md`、`knowledge/joins/table_relationships.md`。
5. 更新 `knowledge/update_log/changelog.md`，按时间正序追加在文件末尾。
6. 数据中心 current model 与语义槽位登记在 `semantic/current_model_bindings.json`；刷新必须通过 operator 的 `sync-data-center-sql` dry-run 获取精确计划哈希，再用 `--write --expected-plan-sha256 <hash>` 原子替换。禁止日期副本；Apply 后强制执行反向索引、共享 catalog、唯一版本审计、integrity 和完整栈验证，失败自动回滚。
7. 运行 `scripts/build_reverse_indexes.py` 刷新 `knowledge/reverse_index/`。
8. 若业务定义已明确且需要进入 P2 规划，更新对应 `semantic/contracts/*.json`，同步当前 `source_path` SHA-256；证据不足的契约只能标为 `pending_confirmation`。
9. 运行 `../scripts/build_text2sql_catalog.py` 重建结构化清单、`semantic/generated/contract_index.json` 和共享中性物理目录；`semantic/domain_manifest.json` 与 `semantic/generated/` 均为生成物，不手工编辑。
10. 人工核对 domain manifest、contract index、契约状态和来源引用；不得从市场顾问 manifest 或 contracts 复制业务语义。
11. 运行 `semantic/evals/resolution_cases.json` 的离线别名解析评测，确认已知别名、预期歧义和 unknown 用例均符合预期。
12. 使用 `scripts/text2sql.py` 校验 QuerySpec、QueryPlan、编译 SQL 或 probe，再运行 `scripts/check_skill_integrity.py`。

新增青橙临时表：

- 必须在 `knowledge/temp_tables/<库名.表名>.md` 中记录来源、刷新方式、字段含义、数据粒度、适用看板、有效期、和不可复用边界。
- 如果临时表只服务某个看板，不得在其他看板 SQL 中复用，除非用户明确确认。
- 如果临时表名称与其他部门临时表相似，必须写清楚不是同一口径。

新增或刷新物理表结构：

- 唯一权威入口是 `usql-web-query-operator sync-datamap-fields --target-skill qingcheng`：先运行默认 dry-run，用户明确授权知识维护后才加 `--write`。
- PDF、截图、OCR、手工字段 JSON 和旧版文档提取/渲染资源目录均不是现行物理 schema 权威，不得据此新建或刷新 `knowledge/tables/`。
- Data Map 只提供中性物理字段、类型、分区和 DDL；青橙指标、范围、临时表、业务 join 与看板语义仍只写在本 Skill 的域内 contracts/knowledge 中。
- 不从其他 Skill 自动复制表文档；需要复用共享物理事实时，必须经共享中性 physical catalog 或 Data Map 重新核对，不得复制市场顾问业务语义。

新增或刷新青橙 Web BI 结构快照：

- 单看板/文件夹命令只把原始画像写入 runtime。需要批量写入知识库时，必须显式运行 `usql-web-query-operator/scripts/read_dashboard.py profile-all --write-knowledge --confirm-skill-maintenance`；少任一参数都不得修改本 Skill。
- 所有青橙快照、README 索引和相关说明只写入本 Skill 的 `knowledge/dashboard_web_profiles/`。
- 不得把 `青橙项目部` 文件夹下的结构快照写入 `market-consultant-dashboard-sql`。
