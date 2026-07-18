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
| 携带上游 QueryPlan 执行 SQL | `references/query_plan_contract.md` | `scripts\usql_web_query.py run --sql-file <sql> --query-plan <json>` | 只有契约字段或 Hash 校验失败时检查上游计划；平台执行失败仍转到 `references/query_error_handling.md` |
| SQL 执行失败、需要分类错误 | `references/query_error_handling.md` | `scripts\usql_web_query.py run` | 只有错误信息不足或页面结构变了，才看 `references/platform_profile.md` 或相关命令实现 |
| 模板取数中读取我创建的模板 SQL | `references/template_query.md` | `scripts\usql_web_query.py fetch-template-sql` | 只有模板匹配或页面状态异常时，才看 `references/platform_profile.md` 或相关实现 |
| 模板市场中按模板名读取 SQL | `references/template_query.md` | `scripts\usql_web_query.py fetch-market-template-sql` | 只有市场搜索、模板匹配或页面状态异常时，才看 `references/platform_profile.md` 或相关实现 |
| 结果超过 1000 行，需要绕开 `SQL取数` 直接下载审批 | `references/template_query.md` | `scripts\usql_web_query.py template-download` | 只有 SQL 仍带模板参数、下载链路异常、或清理逻辑异常时，才看相关命令实现 |
| 看板配置画像 / 实时取值健康检查 | `SKILL.md` 中“看板文件夹扫描”“脚本能力” + `references/platform_profile.md` | 默认 config-only：`profile-dashboard` / `profile-folder` / `profile-all`；独立健康检查：`check-dashboard-values` | 只有菜单、组件、筛选器或页面结构异常时，才继续看 `read_dashboard/commands/*.py`；不要让 value/unit 超时阻塞知识同步 |
| Taitan 编辑页透视表字段、指标含义、自定义公式读取 | `SKILL.md` 中“看板文件夹扫描” + `references/platform_profile.md` 的“Taitan 编辑页指标公式 API” | 单张：`profile-edit-dashboard`；批量：`profile-edit-folder` / `profile-edit-all` | 只有字段详情接口变化、公式缺失、Hash 不稳定或 selector 回退验证失败时，才看 `read_dashboard/edit_profile.py`、`edit_batch.py` 和对应命令实现 |
| Text2SQL 看板组件/布局/公式/筛选器设计与变更 | `references/dashboard_change_workflow.md` | `profile-edit-dashboard` → `design-dashboard` → `plan-dashboard-change` → `apply-dashboard-change` → `publish-dashboard-change` | P3A 可画像和 Diff 全部类型；P4B 只 Apply Registry 中五类窄修改，Apply 与 Publish 必须独立 |
| P4A/P4B 看板写能力与受控 Apply | `references/dashboard_write_capabilities.md` + `references/dashboard_change_workflow.md` | 离线 `inspect-write-capabilities`；人工抓证据用 `capture-write-evidence`；可逆沙箱事务验证用 `verify-sandbox-write-adapters`；生产草稿变更用 `apply-dashboard-change` | 只有 Registry `verified/allowlisted` 的五类窄操作可 Apply；`sandbox_verified` 仍不能自动晋级，发布必须独立确认 |
| P4C 从零创建新看板 | `references/dashboard_build_workflow.md` + `references/dashboard_write_capabilities.md` | `plan-dashboard-build` → 必要的数据中心独立 Plan/Apply/SUCCESS → 重新 Plan → `apply-dashboard-build` → `publish-dashboard-build` | 八项创建 capability 已 `verified/allowlisted`，生产适配器为 `taitan_dashboard_build_v1`；仍须 exact Hash、显式 Apply/Publish 分权、完整回读和 `creation_saga_no_auto_delete` |
| 透视表组件复制重建 / unit 重新绑定 | `references/dashboard_change_workflow.md` 的“复制重建透视表组件” | 沙箱：`rebind-pivot-fields-sandbox --confirm-sandbox-write`；生产 draft：`rebind-pivot-fields-production --manifest-sha256 <hash> --confirm-production-write` | 生产仅限 registry allowlisted 的 `rebuild_pivot_unit_by_copy`；必须先备份配置、绑定 manifest hash，并用带 `publicFilterList` 的 `filtered_value_checks` 验证指定期次/周期；无 filter 的 value/unit 原始结果不是生产门禁；发布仍需独立确认 |
| Legacy 公共筛选器计划检查 | `references/platform_profile.md` 的“Legacy 公共筛选器只读检查” | `scripts\read_dashboard.py edit-public-filters` | 仅保留 dry-run；所有 legacy 写入/发布参数都会在浏览器前拒绝 |
| 手工临时表上传 | `SKILL.md` 中“临时表上传” + `references/manual_temp_table_registry.md` | `scripts\usql_web_query.py check-manual-table` / `upload-temp-table` | 只有需要确认具体登记项或表名映射时，才打开 `manual_temp_table_registry.json` |
| 数据地图字段同步 | `SKILL.md` 中“数据地图字段同步” | `scripts\usql_web_query.py sync-datamap-fields` | 两业务 Skill 的物理字段权威入口；PDF/截图/手工 JSON 不再进入业务 Skill。只有同步结果异常或需要改写逻辑时，才看相关实现 |
| 数据中心源 SQL 同步 | `SKILL.md` 中“数据中心源 SQL 同步” | `sync-data-center-sql` dry-run → `--write --expected-plan-sha256 <hash>` | 稳定 model_id 路径；current-model registry、跨进程独占锁、原子回滚和全栈验证均为强制门禁 |
| 数据中心 SQL 生产替换与刷新 | `references/data_center_replacement.md` | `plan-data-center-sql-replacement` → 审阅 Hash → `apply-data-center-sql-replacement --confirm-production-write` | Plan 远端只读；Apply 才能替换、预览、保存、立即执行并等待新记录 `SUCCESS`；与本地知识同步分权 |
| 数据中心新建数据集并抽数 | `references/data_center_creation.md` | `plan-data-center-dataset-creation` → 审阅 Hash → `apply-data-center-dataset-creation --confirm-production-write` | 自然语言先落到明确域、文件夹、名称和具体 SQL；Plan 只读，Apply 才创建、配置同步、保存、立即执行并等待新 `SUCCESS` |
| 截图内容检查 | `SKILL.md` 中“直接检查截图” | Codex 原生多模态查看 | 只在结构化证据不足且本 skill 已捕获截图后使用 |

## 跨 skill 路由

- 需要生成、修复、解释市场顾问 SQL：先用 `sql-query-writer-for-dashboard`，再由本 skill 执行。
- 需要生成、修复、解释青橙 SQL：先用 `qingcheng-dashboard-sql`，再由本 skill 执行。
- 上游同时产出 QueryPlan 时，将与计划 Hash 精确对应的 SQL 文件和计划一起传给 `run --query-plan`；operator 只验证，不修改计划或推断缺失槽位。
- 需要大结果下载时，先确保上游 SQL skill 已经产出“可直接执行的具体 SQL”，再调用 `template-download`；不要把模板参数解析留到下载阶段。

## 不要默认做的事

- 不要一上来就读完整个 `references/` 目录。
- 不要一上来就读全部命令实现。
- 不要把 `read_dashboard.py` 的问题塞回 `usql_web_query.py`，也不要把 SQL 页面执行逻辑塞进 `read_dashboard.py`。
- 不要用 `profile-edit-dashboard` 修改、删除、发布或新建看板指标；它只负责读取字段说明和公式。
- 不要把 DesignSpec、ChangePlan 或 ApplyReceipt 当成写入/发布授权；新链路必须逐命令显式执行并校验 Hash。
- 不要对组件、布局、公式调用未经生产验证的写接口；这些类型在 P3A 可完整 Diff，在 operator P3B 必须阻断。
- 修改 Taitan 公共筛选器必须使用 `profile-edit-dashboard → design-dashboard → plan-dashboard-change → apply-dashboard-change → publish-dashboard-change`；`edit-public-filters` 只允许 legacy dry-run 检查。
- 从零创建看板必须使用独立 P4C Artifact/Saga；不得把创建 operation 塞入 `DashboardChangePlan`，也不得用模板克隆或预建空板降级。
- 不要把 QueryPlan 视为下载、看板写入、模板写入或权限变更授权；它只约束 `run`，且下载仍受 QueryPlan 与 1000 行策略双重门禁。
- 不要把 `sync-data-center-sql --write`、Data Center Replacement Plan 或 Creation Plan 视为远端数据集写入授权；远端替换与创建必须分别走各自独立的生产 Apply 命令。
- 不要在未经确认的情况下，对超过 1000 行的结果走 `SQL取数` 直接下载。
