# 领域注册适配器

## 1. 目的

`usql-web-query-operator` 只负责平台执行、读取、受治理写入和结构化回执。市场顾问与青橙的 Skill 名称、知识目录、看板文件夹和 Data Center 本地同步目标由 [domain_adapters.json](domain_adapters.json) 登记，不再散落在各命令的常量中。

注册表不包含指标、范围、渠道、期次、Join 或 SQL 业务语义。业务口径仍分别归属 `market-consultant-dashboard-sql` 和 `qingcheng-dashboard-sql`。

## 2. 注册字段

| 字段 | 含义 |
|---|---|
| `target` | operator CLI 使用的稳定短名，目前为 `market` 或 `qingcheng` |
| `domain_id` | QuerySpec、QueryPlan 和领域 metadata 使用的稳定域 ID |
| `skill_name` | 当前可发现的业务 Skill 目录名和 frontmatter 名称 |
| `row_style` | 数据地图 Markdown 行格式适配器 |
| `dashboard.*_folders` | 只读画像、编辑页画像和知识写回允许的文件夹 |
| `dashboard.*` 路径 | 相对业务 Skill 根目录的受控知识落点 |
| `data_center.selector` | operator 内部 allowlist 中的数据集范围选择器 |
| `data_center.*` | canonical SQL 前缀、清单文件和说明模板 |

所有路径必须是相对路径，禁止绝对路径和 `..`。加载器会确认目标 Skill 存在、`metadata.json` 的 `name/domain_id` 与注册表一致，并拒绝重复 target、domain、Skill 或文件夹。

## 3. 写入边界

- `profile-*` 默认只写 runtime。只有 `--write-knowledge --confirm-skill-maintenance` 同时存在时，才使用适配器写入已登记的领域知识目录。
- `sync-datamap-fields` 和 `sync-data-center-sql` 默认只生成 dry-run。写入仍需各命令原有确认、Hash、锁、回滚和完整验证门禁。
- 注册表只决定“写到哪个已验证领域”，不授予写入权限，也不能把一个领域的内容路由到另一个领域。
- `DashboardProfile`、QueryPlan、Data Center Plan 或适配器解析成功都不构成 Apply、Publish 或生产写入授权。

## 4. 维护流程

1. 先修改目标业务 Skill 的目录名、frontmatter、metadata 和调用方。
2. 再更新 `domain_adapters.json`，运行 `tests/test_domain_adapters.py`。
3. 运行 operator 全部测试、两个领域 Skill 的完整性检查和仓库 `validate_text2sql_stack.py`。
4. 若任一 metadata、路径、文件夹或域校验失败，保持 operator 只读失败，不回退到猜测路径。

新增业务域时，必须同时提供独立业务 Skill、稳定 `domain_id`、领域测试和受审阅的知识写回范围；不得只在注册表中新增一行就启用生产写入。
