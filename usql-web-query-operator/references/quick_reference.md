# usql-web-query-operator 快速路由

这是本 skill 的轻量入口，用于渐进式披露。先读这里，再按任务类型下钻到最小必要文档和命令，不要默认全量阅读所有 `references/*.md` 或 `scripts/**/*.py`。

## 通用原则

- 先判断任务属于哪一类，再只读对应说明。
- 先读文档边界和命令入口，再决定是否需要看实现代码。
- 只有在修改某个命令、排查 selector 漂移、或文档信息不足时，才打开对应的 `scripts/.../commands/*.py` 和邻近 helper。
- 运行时产物始终放在 `C:\Users\Ludim\.codex\runtime\`，不要写入 skill 目录。

## 任务到文档/命令的最小路由

| 任务类型 | 先读哪些内容 | 主要命令 | 何时继续下钻 |
|---|---|---|---|
| SQL 页面执行、小结果预览、<=1000 行下载 | `SKILL.md` 中“安全边界”“标准流程” | `scripts\usql_web_query.py run` | 失败时再读 `references/query_error_handling.md`；若怀疑 UI 变化再读 `references/platform_profile.md` |
| SQL 执行失败、需要分类错误 | `references/query_error_handling.md` | `scripts\usql_web_query.py run` | 只有错误信息不足或页面结构变了，才看 `references/platform_profile.md` 或相关命令实现 |
| 模板取数中读取我创建的模板 SQL | `references/template_query.md` | `scripts\usql_web_query.py fetch-template-sql` | 只有模板匹配或页面状态异常时，才看 `references/platform_profile.md` 或相关实现 |
| 模板市场中按模板名读取 SQL | `references/template_query.md` | `scripts\usql_web_query.py fetch-market-template-sql` | 只有市场搜索、模板匹配或页面状态异常时，才看 `references/platform_profile.md` 或相关实现 |
| 结果超过 1000 行，需要绕开 `SQL取数` 直接下载审批 | `references/template_query.md` | `scripts\usql_web_query.py template-download` | 只有 SQL 仍带模板参数、下载链路异常、或清理逻辑异常时，才看相关命令实现 |
| 看板文件夹扫描 / 看板画像 | `SKILL.md` 中“看板文件夹扫描”“脚本能力” + `references/platform_profile.md` | `scripts\read_dashboard.py scan-folder` / `profile-dashboard` / `profile-folder` / `profile-all` | 只有菜单、组件、筛选器或页面结构异常时，才继续看 `read_dashboard/commands/*.py` |
| Taitan 编辑页透视表字段、指标含义、自定义公式读取 | `SKILL.md` 中“看板文件夹扫描” + `references/platform_profile.md` 的“Taitan 编辑页指标公式 API” | `scripts\read_dashboard.py profile-edit-dashboard` | 只有字段详情接口变化、公式缺失或 selector 回退验证失败时，才看 `read_dashboard/edit_profile.py` 和对应命令实现 |
| 手工临时表上传 | `SKILL.md` 中“临时表上传” + `references/manual_temp_table_registry.md` | `scripts\usql_web_query.py check-manual-table` / `upload-temp-table` | 只有需要确认具体登记项或表名映射时，才打开 `manual_temp_table_registry.json` |
| 数据地图字段同步 | `SKILL.md` 中“数据地图字段同步” | `scripts\usql_web_query.py sync-datamap-fields` | 只有同步结果异常或需要改写逻辑时，才看相关实现 |
| 数据中心源 SQL 同步 | `SKILL.md` 中“数据中心源 SQL 同步” | `scripts\usql_web_query.py sync-data-center-sql` | 只有目录范围、写入规则或接口行为异常时，才看相关实现 |
| 截图读字 / OCR 协作 | `SKILL.md` 中“通过 mineru-converter 读取图片” | `mineru-open-api flash-extract` / `extract` | 只在本 skill 已经捕获到截图后使用，不要反过来先做 OCR |

## 跨 skill 路由

- 需要生成、修复、解释市场顾问 SQL：先用 `sql-query-writer-for-dashboard`，再由本 skill 执行。
- 需要生成、修复、解释青橙 SQL：先用 `qingcheng-dashboard-sql`，再由本 skill 执行。
- 需要大结果下载时，先确保上游 SQL skill 已经产出“可直接执行的具体 SQL”，再调用 `template-download`；不要把模板参数解析留到下载阶段。

## 不要默认做的事

- 不要一上来就读完整个 `references/` 目录。
- 不要一上来就读全部命令实现。
- 不要把 `read_dashboard.py` 的问题塞回 `usql_web_query.py`，也不要把 SQL 页面执行逻辑塞进 `read_dashboard.py`。
- 不要用 `profile-edit-dashboard` 修改、删除、发布或新建看板指标；它只负责读取字段说明和公式。
- 不要在未经确认的情况下，对超过 1000 行的结果走 `SQL取数` 直接下载。
