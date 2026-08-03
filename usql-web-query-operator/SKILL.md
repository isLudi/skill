---
name: usql-web-query-operator
description: 通过 Playwright 执行受治理的 USQL 网页查询、小结果下载、模板 SQL 读取与大结果临时模板下载、手工临时表上传、数据地图及 Data Center 本地知识同步、显式生产数据集替换/创建，以及 BI 看板只读画像、受控草稿变更和独立发布。使用本 Skill 运行或下载公司 SQL、读取模板、检查或上传已登记临时表、扫描/画像 Taitan 看板、执行经 Hash 审阅的 Data Center 或看板 Plan；不要用它生成业务 SQL、推断指标口径、跨域写知识或调用未经验证的写接口。
---

# USQL Web Query Operator

## 角色

本 Skill 是公司 SQL、Data Center 和 Taitan BI 的平台执行层。它管理浏览器登录态、页面/API 适配、运行状态、结构化错误、Hash、回读、回执和生产写入门禁。

业务 SQL、指标、范围、渠道、期次和 Join 语义必须由领域 Skill 提供：

- `market_consultant`：`market-consultant-dashboard-sql`
- `qingcheng`：`qingcheng-dashboard-sql`

域未解析时只允许读取中立物理事实，不得生成或执行生产 SQL。

## 先读路由

按任务只读取对应 reference，不要全量打开脚本或全部文档：

| 任务 | 必读 reference | 稳定入口 |
|---|---|---|
| SQL 执行、错误、小结果下载 | [sql_query_execution.md](references/sql_query_execution.md)；有 QueryPlan 再读 [query_plan_contract.md](references/query_plan_contract.md)；追踪和结果工件见 [text2sql_runtime_artifacts.md](references/text2sql_runtime_artifacts.md) | `scripts/usql_web_query.py` |
| 模板 SQL、模板市场、大结果下载 | [template_query.md](references/template_query.md) | `scripts/usql_web_query.py` |
| 手工临时表检查或上传 | [manual_temp_table_registry.md](references/manual_temp_table_registry.md) | `scripts/usql_web_query.py` |
| 数据地图/Data Center 本地知识同步 | [data_knowledge_sync.md](references/data_knowledge_sync.md) 和 [domain_adapters.md](references/domain_adapters.md) | `scripts/usql_web_query.py` |
| 远端既有数据集替换 | [data_center_replacement.md](references/data_center_replacement.md) | `scripts/usql_web_query.py` |
| 远端新建数据集与首抽 | [data_center_creation.md](references/data_center_creation.md) | `scripts/usql_web_query.py` |
| 看板扫描、配置画像、编辑页公式 | [platform_profile.md](references/platform_profile.md) | `scripts/read_dashboard.py` |
| 既有看板设计、Diff、草稿 Apply、发布 | [dashboard_change_workflow.md](references/dashboard_change_workflow.md) | `scripts/read_dashboard.py` |
| P4A/P4B 写能力和沙箱取证 | [dashboard_write_capabilities.md](references/dashboard_write_capabilities.md) | `scripts/read_dashboard.py` |
| P4C 从零构建看板 | [dashboard_build_workflow.md](references/dashboard_build_workflow.md) | `scripts/read_dashboard.py` |
| 所有命令的快速索引 | [command_reference.md](references/command_reference.md) | 两个入口的 `--help` |

只有修改命令、排查 selector 漂移或文档不足时，才读取对应 `scripts/**/commands/*.py` 和邻近 helper。

## 不可绕过的安全边界

- 密码、Cookie、Token、登录态、截图、SQL 结果和下载文件不得进入 Skill 目录。
- 登录态固定保存在 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`；通用 Playwright 不得读取、替换或管理它。
- QueryPlan 仅约束 `run`：必须为受支持域、`status=executable`、`unresolved_slots=[]` 且 SQL SHA-256 完全一致。
- `run` 在浏览器启动前强制执行只读 SQL Policy；DDL/DML、命令语句、多语句、解析失败和未解析模板参数不得通过 audit 模式绕过。
- QueryTrace、SQL Policy Report 和 ResultArtifact 只记录 Hash、状态、列级元数据与脱敏结果证据，不保存问题原文、SQL 文本或结果行，也不构成任何后续授权。
- QueryPlan 不授予下载、模板、临时表、数据集、看板或权限写入能力。
- 直接下载同时要求结果不超过 1000 行；携带 QueryPlan 时还要求 `execution_policy.allow_download=true`。
- `profile-*`、数据地图和 Data Center 本地同步默认只写 runtime/dry-run；领域知识落点只由 [domain_adapters.json](references/domain_adapters.json) 决定。
- 领域适配器解析成功不构成知识写入、Apply 或 Publish 授权；metadata、路径或域不匹配时必须失败，不得猜测回退目录。
- DashboardProfile、DesignSpec、ChangePlan、BuildPlan、Data Center Plan 和 Receipt 都是证据工件，不是下一阶段授权。
- 看板 Apply 只写 draft，Publish 必须独立命令和独立确认。
- P4B 只允许 capability registry 中九类 `verified/allowlisted` 既有对象窄修改；其他修改阻断。
- P4C 使用独立创建 Saga；失败不自动删除资源，Receipt 必须列出孤立资源和人工清理要求。
- Data Center 替换和创建分别要求独立只读 Plan、精确 Hash、`--confirm-production-write`、保存后回读、立即执行和新的 `SUCCESS`。
- `sync-data-center-sql --write` 只写本地业务 Skill，绝不等于远端生产写入。
- 模板大结果下载必须强制执行临时模板 `offline -> delete`；清理失败则整个命令失败。
- 只在显式 `--debug-artifacts` 时保存截图；CAPTCHA、MFA 和风控只识别并报告。

## 领域注册适配器

执行器代码不得直接硬编码业务 Skill 根目录。统一通过 `_shared/domain_adapters.py` 加载 `references/domain_adapters.json`：

- 验证 target、domain、Skill 名称和 metadata；
- 验证相对知识路径不能包含绝对路径或 `..`；
- 验证看板知识文件夹归属唯一；
- 为看板画像写回、数据地图同步、Data Center canonical SQL 同步和 P4C 上游绑定提供同一领域根目录。

注册表只保存路由和平台范围，不保存业务指标或 SQL 语义。新增领域必须先有独立业务 Skill、稳定 `domain_id`、领域测试和经审阅的知识写回范围。

## 标准协作顺序

1. 用领域 Skill 解析需求并生成经验证的 SQL/QueryPlan/DesignSpec。
2. 用本 Skill 运行只读 Plan、画像、探查或 SQL。
3. 审阅精确身份、Hash、差异和 capability。
4. 仅在用户明确授权对应写入阶段后执行 Apply。
5. 回读目标并生成 Receipt。
6. Publish 或生产刷新作为独立阶段再次确认。

SQL 执行失败必须把结构化错误交回原领域 Skill 修复，不能通过切换领域绕过。登录过期时请求手工登录，不暴露凭据。

## 维护与验证

修改 operator 时至少运行：

```powershell
D:\anaconda3\python.exe -m pytest tests -q
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\Ludim\.codex\skills\usql-web-query-operator
```

修改 CLI 命令或能力边界时，先更新 `references/command_capabilities.json`，再运行 `scripts/build_command_reference.py`；`--check` 必须确认注册表、两个 parser 和生成的 `references/command_reference.md` 完全一致。

若改动领域注册、知识同步、QueryPlan、看板工件或 Data Center 流程，还必须运行两个领域 Skill 的完整性检查和仓库 `../scripts/validate_text2sql_stack.py`。

命令参数始终以当前 `--help` 为准；reference 不得扩大 CLI、Hash、确认或 capability registry 的权限。
