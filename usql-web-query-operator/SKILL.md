---
name: usql-web-query-operator
description: 通过 Playwright 自动化执行受控的 USQL 网页取数、模板下载、临时表上传、数据中心 SQL 读取/本地同步、显式生产替换刷新与新建数据集抽数，以及 BI 看板读取流程；可校验上游 QueryPlan，按独立 profile→design→diff/dry-run→apply draft→publish confirmation 链路治理 Taitan 看板变更，并在明确沙箱中探测、审计写接口能力。使用本 skill 运行或下载公司 SQL、读取模板 SQL、计划或执行经 Hash 审阅的数据中心数据集替换/创建与刷新、扫描/画像看板、设计看板变更或检查 P4A/P4B capability registry；不要用它生成业务 SQL、推断指标口径或调用未经验证的写接口。
---

# usql-web-query-operator 技能说明

## 0. 加载与读取顺序

加载本 skill 后，先确认 skill 根目录，再按渐进式披露原则读取最小必要内容，不要一上来全量展开所有参考文档和脚本实现。

推荐顺序：

1. 先读本文件的“安全边界”，确认登录态、下载限制、runtime 目录和跨 skill 边界。
2. 再读 [references/quick_reference.md](C:/Users/Ludim/.codex/skills/usql-web-query-operator/references/quick_reference.md)，按任务类型路由到最小必要文档。
3. 只有在任务属于对应分支时，才继续下钻：
   - SQL 页面执行 / 小结果下载：读“标准流程”；携带 `--query-plan` 时再读 `references/query_plan_contract.md`；失败时再读 `references/query_error_handling.md`。
   - 模板取数已保存 SQL / 模板市场 SQL / 大结果下载：读 `references/template_query.md`。
   - 看板文件夹扫描 / 看板画像 / 编辑页指标公式读取：读“看板文件夹扫描”和 `references/platform_profile.md`。
   - Text2SQL 看板设计、Diff、草稿 Apply 或发布：读 `references/dashboard_change_workflow.md`；P4A 写接口探测再读 `references/dashboard_write_capabilities.md`，不要从 legacy `edit-public-filters` 推导新流程权限。
   - 手工临时表上传：读“临时表上传”和 `references/manual_temp_table_registry.md`；只有需要精确映射时才打开 `manual_temp_table_registry.json`。
   - 数据地图字段同步 / 数据中心源 SQL 同步：只读对应同步章节，不要顺带展开无关参考文档。
   - 数据中心远端 SQL 替换与刷新：读 [references/data_center_replacement.md](C:/Users/Ludim/.codex/skills/usql-web-query-operator/references/data_center_replacement.md)；先走独立只读 Plan，再走显式生产 Apply。
   - 数据中心新建数据集并抽数：读 [references/data_center_creation.md](C:/Users/Ludim/.codex/skills/usql-web-query-operator/references/data_center_creation.md)；把自然语言解析成域、文件夹、名称和具体 SQL 后，先走只读 Plan，再走显式生产 Apply。
4. 只有在需要修改某个命令、排查 selector 漂移、或文档已不足以支持判断时，才打开对应的 `scripts/usql_web_query/commands/*.py`、`scripts/read_dashboard/commands/*.py` 和邻近 helper。
5. 不要默认全量阅读 `references/*.md`、`scripts/usql_web_query/**/*.py` 或 `scripts/read_dashboard/**/*.py`。

## 用途

当 USQL RestAPI 权限不足、但当前登录账号可以在网页端手工执行 SQL 时，使用本 skill 通过 Playwright 自动操作公司 `SQL取数` 页面。

本 skill 不绕过权限，只自动化当前认证用户在浏览器中本来可以完成的动作。

## 安全边界

- 不要把密码、cookie、token、截图或下载的查询结果写入 skill 目录。
- Playwright 登录态只保存到 git 外的本地 runtime 路径，默认是 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`。
- 账号密码从环境变量、命令行 `--env-file`、环境变量 `USQL_ENV_FILE` 指向的文件或交互式输入读取；未指定时脚本才使用本机兼容回退路径。不要把凭证硬编码到脚本、文档、shell history 或已提交文件中。
- 除非 SQL 明确限制 `limit <= 1000`，或成功结果页能证明结果不超过 1000 行，否则不要下载结果集。
- `run --query-plan <path>` 是可选的只读执行契约校验。使用时，QueryPlan 必须满足 `schema_version=2.0.0`、业务域受支持、`status=executable`、`unresolved_slots` 为空、`sql_sha256` 与本次提交的完整 SQL 文本完全一致，并包含 `execution_policy`；否则在打开浏览器前停止。
- QueryPlan 不是下载豁免。携带 QueryPlan 时，`--download` 还要求 `execution_policy.allow_download=true`；通过后仍必须满足原有 `LIMIT <= 1000` 或结果页证明不超过 1000 行的本地门禁。
- QueryPlan 只约束 `usql_web_query.py run` 的 SQL 执行，不授予看板、模板、临时表、数据集或权限配置的任何写入能力。
- DashboardProfile、DesignSpec、ChangePlan 和 ApplyReceipt 都不授予写入或发布权限。P3 Apply 与 Publish 必须是两个独立命令，并分别校验精确 Hash 与当前 draft 画像。
- P4B draft Apply 仅允许 Registry 中五类 `verified/allowlisted` 操作：既有稳定字段显示名、同容器/Tab 既有节点 `x/y/w/h`、依赖不变的单组件非共享既有公式表达式、稳定三元组公共筛选器动态默认项、根背景色。其余组件、布局、公式、筛选器、主题以及所有新建/删除/重绑仍为 `blocked_unsupported`。
- P4A capability registry 默认阻断所有未经验证的写操作。沙箱 `DashboardWriteProbe` 只收集脱敏请求结构和前后 Profile，不自动晋级 registry、Apply allowlist 或发布权限。
- `sandbox_verified/sandbox_only` 仍不等于生产权限；只有同时经过共享 ChangePlan 策略、生产补偿事务、完整测试、不可变证据 Hash，并在 Registry 明确标记 `verified/allowlisted` 的操作才能进入 Apply。`verify-sandbox-write-adapters` 会额外执行五操作连续写入、逆序恢复和完整 Profile Hash 复原。
- 预览和探索 SQL 优先使用 `limit <= 1000`。
- 如果页面返回权限、平台或 SQL 错误，保留错误文本；只有显式设置 `--debug-artifacts` 时才保存调试截图。
- 如果 `run` 返回 `ok=false`，先读 `error_details.detail`，再读 `error_details.raw_snippet`，最后读 `error_details.title`，根据捕获到的原因修 SQL 后再重试。
- 同时读取最终 JSON 里的 `error_category`、`error_category_label`、`repair_guidance`。`即时错误` 和 `日志区错误` 是两条不同修复路径。
- SQL/BI 浏览器登录态归本 skill 管理。不要使用通用 `playwright` skill 读取、写入、复制、刷新或替换 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`。
- 数据中心读取与远端写入必须分权：`sync-data-center-sql`、`plan-data-center-sql-replacement` 和 `plan-data-center-dataset-creation` 不执行远端修改；只有各自独立的 `apply-data-center-sql-replacement` / `apply-data-center-dataset-creation` 在精确计划 Hash 与 `--confirm-production-write` 同时满足时可执行生产写入。创建计划不授权替换，替换计划也不授权创建。

## 标准流程

1. 先用 `sql-query-writer-for-dashboard` 生成并校验 SQL。
2. 确认 SQL 适合网页执行：
   - 使用 Presto 语法。
   - 使用完整表名。
   - 补齐必要的 `dt` 和 `hour` 分区。
   - 补齐必要的部门、架构或权限范围过滤。
   - 下载前必须有 `limit <= 1000`，或页面能证明结果不超过 1000 行。
3. 运行本地依赖检查：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py doctor
```

脚本默认使用已安装的 Microsoft Edge channel（`--browser-channel msedge`）。如果 Edge 可用，通常不需要额外下载 Playwright Chromium。

4. 保存或刷新浏览器登录态：

```powershell
$env:BAIJIA_USERNAME='<account>'
$env:BAIJIA_PASSWORD='<password>'
D:\anaconda3\python.exe scripts\usql_web_query.py login --headed
```

如果自动登录被 SSO、MFA、二维码或风控拦截，改用 `login --manual --headed`，在打开的浏览器中完成登录，然后回到终端按 Enter。

5. 执行一个安全 SQL 文件：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py run --sql-file C:\path\to\query.sql --headed --no-download
```

如果上游业务 SQL skill 同时产出了与该 SQL 精确绑定的 QueryPlan，可增加可选执行契约：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py run `
  --sql-file C:\path\to\query.sql `
  --query-plan C:\path\to\query_plan.json `
  --headed `
  --no-download
```

`--query-plan` 不会替代 SQL 文件，也不会替 operator 补齐未解析参数或修正 Hash。契约字段、下载双重门禁和失败行为见 `references/query_plan_contract.md`。

脚本会在写入 SQL 前切换查询引擎。默认引擎是 `presto`，优先使用平台稳定性更高但耗时更长的原始 Presto。只有当 Presto 成功执行但结果疑似为空、或需要排查引擎差异时，才显式使用 `--engine doris-presto` 做补充验证。

6. 检查返回的 JSON summary。成功运行会包含查询状态、检测到的 query id，以及页面能暴露时的小范围可见表格预览。
7. 如果 `status=Failed`，修改 SQL 前必须先读 `error_details`：
   - `error_category=immediate_platform_error` / `error_category_label=即时错误`：页面在稳定查询行生成前拒绝 SQL，通常是右上角 notification。停止重复运行，先按弹窗文本修 SQL。
   - `error_category=query_log_error` / `error_category_label=日志区错误`：查询行已创建，错误在执行日志里；优先使用 `VALIDATE_SQL_ERROR`、行列号、表名、字段名等信息修复。
   - `notification` / `message` / `alert`：页面在提交前或提交中拒绝 SQL，可能没有 query id。
   - `log_area`：查询任务已创建，使用执行日志，尤其是 `VALIDATE_SQL_ERROR`、行列号、表名、字段名。
   - `repair_guidance`：先用脚本给出的修复建议，再考虑从原始页面文本推断。
   - 已验证案例和修复规则见 `references/query_error_handling.md`。
8. 如果运行成功且满足下载策略，可重新运行并加 `--download`，或在原始运行中直接包含 `--download`。携带 QueryPlan 时，还必须由 `execution_policy.allow_download=true` 明确允许；该权限不能绕过原有 1000 行门禁。
9. 如果用户明确需要下载的结果超过 1000 行，或会触发 `SQL取数` 页面审批链路，不要继续走这里的直接下载；切换到“模板取数大结果下载”，并先读取 `references/template_query.md`。

## 数据地图字段同步

当用户希望用 `https://tiangong2.baijia.com/dataMap/dataMapNew` 补齐或刷新业务 SQL skill 中的物理表字段说明时，使用：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-datamap-fields --target-skill all
```

默认是 dry-run：脚本登录数据地图，查找目标 skill 知识库中已有的物理表文档，对比数据地图字段和 `knowledge/tables/*.md`，只打印 JSON summary，不写文件。

该命令是两个业务 SQL Skill 的物理表字段权威维护入口。业务 Skill 不再保存表结构 PDF、字段截图、页面渲染图或手工字段目录 JSON；数据地图登录态、接口缓存和调试制品只保存在 runtime。数据地图负责物理事实，不得据此推断部门指标、范围、Join 或业务口径。

确认需要更新知识库后再加 `--write`：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-datamap-fields `
  --target-skill all `
  --write
```

新增单表后的增量补充示例：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-datamap-fields `
  --target-skill qingcheng `
  --table service_dw.example_table_df `
  --write
```

该命令只写业务 skill 文档，不写 SQL 查询输出：

- 内置目标：`market` 对应 `sql-query-writer-for-dashboard`，`qingcheng` 对应 `qingcheng-dashboard-sql`，`all` 同步两者。
- 跳过 `temp_table.*` 文档。手工临时表来自本地 Excel/SQL 规则，不从数据地图维护。
- 只替换占位的类型/说明单元格，或在带日期的 `数据地图字段补充（YYYY-MM-DD）` 段落下追加缺失字段，不覆盖已有业务语义。
- 数据地图浏览器登录态和字段缓存保存在 `C:\Users\Ludim\.codex\runtime\data-map\`，不会写入 skill 目录。
- 使用 `--write` 且确实产生字段变更时，会追加 changelog，并强制运行目标 skill 的反向索引、仓库级 catalog builder、目标 skill integrity 和完整 `validate_text2sql_stack.py`；这些门禁不能通过 `--no-*` 关闭。
- 使用 `--no-refresh-datamap` 可只从本地 runtime 缓存同步；使用 `--only-missing-cache` 可只刷新新增表。

## 数据中心源 SQL 同步

当用户要求把 `https://uanalysis.baijia.com/data-center/data-set` 中的数据集源 SQL 写入业务 SQL skill 知识库时，使用：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-data-center-sql --target-skill all
```

默认是 dry-run：脚本使用本 skill 的共享登录态打开数据中心，通过目录和数据集详情接口读取目标范围，生成 `DataCenterSyncPlan`、精确 `plan_sha256` 和 runtime plan artifact，不写业务 skill 文件。
审阅计划后，使用完全相同的范围重新抓取，并携带精确计划哈希 Apply：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-data-center-sql `
  --target-skill all `
  --write `
  --expected-plan-sha256 <dry-run 输出的 plan_sha256>
```

内置目标和范围：

- `qingcheng`：写入 `qingcheng-dashboard-sql`，同步父目录为 `市场顾问部/青橙项目部` 的全部 SQL 数据集。
- `market`：写入 `sql-query-writer-for-dashboard`，同步父目录为 `市场顾问部/市场顾问部` 且从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- `all`：按上述规则同步两个业务 skill；两个知识库保持隔离。

写入规则：

- 每个 model_id 只写稳定路径 `resources/raw_sql/data_center_<target>_<model_id>.sql`；更新时原位替换，禁止创建日期后缀副本。
- 每个业务域在对应业务 skill 的 semantic 目录中用 `current_model_bindings.json` 记录 current model、SQL SHA-256、稳定路径和语义槽位；该文件不属于 operator，两个域的 registry 也不得互相引用。
- 数据集清单保存到目标 skill 的 `knowledge/dashboards/data_center_<target>_datasets.md`，记录数据集名称、菜单 ID、`fileValue`、`subjectId`、数据源 ID、平台路径和 raw SQL 文件。
- 脚本只保存数据中心接口返回的 `executeSql`，不改写 SQL 语义，不推断字段或指标口径。
- Apply 使用跨进程独占锁，并在锁内重新核对 exact plan hash 和所有文件前置 SHA；同一命令覆盖两个域时作为一个事务执行。并发或残留锁一律先阻断，不允许两个更新进程交错写入。
- Apply 后强制运行反向索引、共享 catalog、唯一版本审计、域内 integrity 和完整 `validate_text2sql_stack.py`；禁止用 `--no-*` 关闭这些门禁。任一步失败会恢复本次业务文件及生成物。
- 模型被新 model_id 替代时，使用 `--slot-binding <slot_id>=<new_model_id>` 更新语义槽位，并用 `--retire-model-id <old_model_id>` 显式退役；未审阅的模型消失会阻断全量同步。
- 运行摘要保存到 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\data-center\`，不会把 cookie 或账号密码写入 skill 目录。

常用增量参数：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-data-center-sql `
  --target-skill market `
  --dataset-name 市场渠道用户成单分析3
```

先读取该增量 dry-run 的 `plan_sha256`，再追加 `--write --expected-plan-sha256 <hash>`。`--market-start-name` 可覆盖市场顾问目录的起始数据集名；`--dataset-name` 可重复传入。

## 数据中心 SQL 生产替换与刷新

当用户明确要求把新 SQL 写回既有数据中心数据集并刷新生产同步时，使用两个独立命令：

1. `plan-data-center-sql-replacement`：只读线上数据集并生成 Hash 绑定计划，不执行远端写入。
2. `apply-data-center-sql-replacement`：消费精确计划 Hash 和显式生产确认，按“整体替换 → 运行预览成功 → 保存并回读 SQL Hash → 立即执行 → 新同步记录 SUCCESS”执行。

完整权限边界、命令参数、失败行为和 receipt 说明见 `references/data_center_replacement.md`。不要把 `sync-data-center-sql --write` 当成远端写命令；它只更新本地业务 Skill 知识库。Plan 也不授予 Apply 权限。

## 数据中心新建数据集与抽数

当用户明确要求在指定文件夹创建命名数据集并成功抽数时，使用两个独立命令：

1. `plan-data-center-dataset-creation`：只读解析域内文件夹、校验名称唯一性，绑定具体 SQL、数据源和同步配置，输出 Hash 绑定计划。
2. `apply-data-center-dataset-creation`：消费精确计划 Hash 和显式生产确认，按“打开新建草稿 → 重命名/选择数据源/写入 SQL → 预览成功 → 配置同步 → 保存 → 回读身份/SQL/同步任务 → 立即执行 → 新同步记录 SUCCESS”执行。

默认同步设置为当天起 90 天、小时级、选择 24 个整点。名称冲突、域/文件夹不匹配、SQL 文件变化、数据源身份变化或保存后回读不一致都会阻断。保存成功后的失败不会自动删除数据集，而是写失败 receipt 并要求人工处理。完整说明见 `references/data_center_creation.md`。

## 临时表上传

当用户明确要求把本地 CSV/Excel 手工表上传到 `SQL取数` 的临时表 UI 时，使用：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py upload-temp-table `
  --file E:\path\to\manual_table.xlsx `
  --target-mode reuse `
  --import-mode overwrite
```

对于以下目录下已登记的手工表：

- `E:\1900_work\GAOTU\19002_市场顾问部看板维护表格`
- `E:\1900_work\GAOTU\19003_青橙项目部看板维护表格`

命令会读取 `references/manual_temp_table_registry.json`，推断平台标准临时表名，并在打开浏览器前执行本地 workbook 校验。成功 summary 会包含匹配到的 registry entry、校验结果和导入历史行，包括 `临时表名` 和 `数据量`。

上传前或修改 workbook 后，可先做无浏览器预检查：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py check-manual-table
D:\anaconda3\python.exe scripts\usql_web_query.py check-manual-table --file E:\path\to\manual_table.xlsx
```

如果登记项标记为 `review_required_*`，`upload-temp-table` 不会自动选择目标表。先确认候选表，再显式传入 `--target-table`。需要遇到本地校验错误就停止上传时，使用 `--strict-validation`；不加该参数时，校验问题会在 JSON summary 中作为 warnings/errors 返回，但上传流程可以继续。

上传必须是用户授权且文件明确的操作。不要上传任意本地文件。调试 artifact 仍保存在 runtime artifact 目录。

## 看板文件夹扫描

不要用 `usql_web_query.py` 处理看板文件夹或看板数据；它只负责 `SQL取数` 执行和结果下载。

当用户要求发现某个网页文件夹下的看板名称和 ID 时，使用 `scripts/read_dashboard.py`：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py scan-folder --folder 市场顾问数据 --headed
```

BI 页面或看板列表刷新较慢时使用 `--wait-ms <milliseconds>`。命令默认把 JSON 写到本地 runtime artifact 目录。

打开看板并采集页面结构时，使用：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py profile-dashboard --dashboard-id dashboard_3730722176629411841
D:\anaconda3\python.exe scripts\read_dashboard.py profile-folder --folder 市场顾问数据 --names '外呼过程数据看板|转化数据'
```

`profile-dashboard`、`profile-folder` 和 `profile-all` 默认使用 `--profile-mode config`，只读页面配置、组件、筛选器和字段，不调用慢速 `value/unit`。需要实时取值健康检查时，先保存 config profile，再独立运行：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py check-dashboard-values --profile <profile.json>
```

健康检查默认使用单请求 15 秒、最多 2 次、单看板 90 秒总预算和 15 分钟失败缓存；可通过 `--value-*` 参数收紧。只有明确需要兼容旧的一体化结果时才使用 `--profile-mode full`。所有画像有意不保存返回的结果行。

当用户需要理解 Taitan 编辑页中每个透视表的字段、指标含义和自定义指标公式时，使用只读命令：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py profile-edit-dashboard `
  --edit-url "https://udata.baijia.com/taitan/?dashboardId=<dashboard_id>&htmlId=<html_id>"
```

`profile-edit-dashboard` 会读取 `draft` 版本的看板配置、透视表单元详情、模型字段详情、自定义指标公式和可识别的数据集字段树，并把 JSON 写入 runtime artifact 目录。该命令只调用读取类接口，不调用保存、发布、删除、新建或更新接口；它的边界是“了解指标含义和公式”，不是修改看板。规范画像会把已选字段、公式 ID、组件筛选器和模型/数据集 identity 绑定到组件，并验证每个已配置 pivot 的 unit/component/dataset 闭环、字段和公式/筛选器引用、dataset 反向引用；抓取完整字段树时还会核对已选字段与公式依赖确实存在于对应 subject。空白容器和文本等非数据组件不参与该门禁。任一抓取或绑定失败时仍保存含 `binding_validation` 的诊断 artifact，但标记 `completeness.status=incomplete`、返回非零，并禁止进入 Design/Apply/Publish。若只想读取当前透视表实际使用字段而不抓取完整字段树，可加 `--skip-dataset-fields`；该选项不跳过 unit/model identity 和引用闭环检查。

文件夹或全域批量读取编辑页时，使用 `profile-edit-folder` / `profile-edit-all`。它们先扫描菜单，再用最多 4 个隔离子进程并发画像；默认 `--max-workers 2 --resume`，24 小时内完整缓存直接复用。强制刷新用 `--no-resume`；live Hash 未变化时返回 `unchanged` 并保留原文件修改时间。批处理只写 runtime JSON/manifest，不写或发布看板。

当任务需要从 Text2SQL 数据集设计继续到看板设计或修改时，按 `references/dashboard_change_workflow.md` 使用独立 P3 链路。`profile-edit-dashboard --domain ...` 会在向后兼容的 rich profile 中增加规范快照和 Hash；可用 `--normalized-output` 另存纯 DashboardProfile Artifact。`design-dashboard` 与 `plan-dashboard-change` 永远是零写入；`apply-dashboard-change` 只写 draft；`publish-dashboard-change` 必须另起命令确认。

如果要把当前市场顾问和青橙看板文件夹完整同步到各自隔离的 SQL skill 知识库，运行：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py profile-all --dashboard-wait-ms 15000
```

## 脚本能力

`scripts/usql_web_query.py` 用于 `SQL取数`、模板取数、临时表和数据平台只读/受控操作：

- `doctor`：检查 Python Playwright 可用性，缺失时给出安装命令。
- `login`：打开 CAS 登录流程，认证后把浏览器 storage state 保存到 repo 外。
- `run`：可选先用 `--query-plan` 校验上游只读执行契约；通过后打开 `SQL取数`，创建或复用查询 tab，写入 SQL 前切换引擎，将 SQL 写入 CodeMirror，优先用 `Ctrl+E` 提交，再用运行按钮回退，等待查询历史/结果 tab 状态，平台失败时捕获 `error_details`，可用时提取小范围可见结果预览，并在 QueryPlan 与本地行数门禁均允许时下载并校验结果制品。直接下载若识别为 XML 伪 CSV、表头空/列不完整 Excel，会自动改走临时 Template Query CSV，并在下线、删除临时模板后才报告成功。
- `sync-datamap-fields`：使用数据地图页面和接口刷新 `sql-query-writer-for-dashboard` 和/或 `qingcheng-dashboard-sql` 中的物理表字段说明。默认 dry-run，只有 `--write` 才写文档。
- `sync-data-center-sql`：使用数据中心页面和接口生成稳定 canonical SQL 同步计划；Apply 必须绑定 dry-run 的精确 Hash，并以可回滚事务写入 raw SQL、current-model registry、清单文档和 changelog。
- `plan-data-center-sql-replacement`：只读解析一个域内数据集，绑定稳定数据集身份、当前 SQL Hash、替换文件 Hash、数据源和同步任务，输出 runtime 计划；默认阻断同 Hash no-op。
- `apply-data-center-sql-replacement`：独立生产写命令；要求精确计划 Hash 和显式确认，经页面运行/保存后回读 SQL，再触发立即同步并轮询到新的 `SUCCESS` 记录，成功或失败均写 receipt。
- `plan-data-center-dataset-creation`：只读解析域内目标文件夹，校验同目录名称唯一性，绑定 SQL Hash、数据源身份和 90 天小时级同步配置，输出 runtime 计划。
- `apply-data-center-dataset-creation`：独立生产写命令；要求精确计划 Hash 和显式确认，创建草稿、预览、配置同步、保存并回读新 `menu_set_*` 身份，触发立即执行并等待新的 `SUCCESS` 记录。
- `upload-temp-table`：把本地 `.csv`、`.xls` 或 `.xlsx` 上传到 `临时表` 区域。支持 `--target-mode new|reuse`、`--import-mode overwrite|append`、`--header-row|--no-header-row`，并从 `导入历史` 输出 JSON summary。
- `check-manual-table`：读取手工表 registry，将本地 Excel 文件解析到平台标准临时表名，并在不触碰浏览器的情况下执行 workbook 校验。
- `fetch-template-sql`：从“我创建的模板”只读抓取已保存 SQL。
- `fetch-market-template-sql`：从“模板市场”按模板名只读抓取已发布模板 SQL。
- `template-download`：通过临时模板创建、查询、下载和默认清理流程处理明确授权的大结果下载；请求 `xls` 但制品为表头空/列不完整 Excel 时自动回退为同名 `.csv`。

常用 `run` 选项：

- 失败 summary 会明确区分 `即时错误` 和 `日志区错误`，并输出 `repair_guidance` 供下一轮 SQL 修改使用。
- `--query-plan <path>`：可选读取 QueryPlan JSON，在浏览器启动前校验可执行状态、未解析槽位、SQL Hash 和执行策略；通过时 summary 增加紧凑的 `query_plan_contract`，不复制完整计划内容。
- `--engine presto`：执行前选择原始 Presto，这是默认值；平台当前更稳定，但通常耗时更长。
- `--engine doris-presto`：执行前选择 `Doris-Presto -> doris内测加速版`，仅在 Presto 结果疑似为空、需要更快的补充验证或排查引擎差异时使用。

`scripts/read_dashboard.py` 只用于自助BI / dashboard：

- `scan-folder`：打开自助BI，读取看板菜单，查找 `市场顾问数据` 等文件夹，并提取中文看板名和 ID。
- `profile-dashboard`：按 ID 打开单个看板，等待刷新，把组件/筛选器/值结构保存到 repo 外。
- `check-dashboard-values`：从已保存的 config profile 独立检查 `value/unit`，按请求超时、重试、单看板总预算和 runtime 失败缓存限时返回。
- `profile-edit-dashboard`：打开 Taitan 编辑页，只读采集透视表字段、指标含义、自定义指标公式和文本口径说明，不保存、不发布、不修改看板。
- `profile-edit-folder` / `profile-edit-all`：以隔离子进程有限并发批量读取编辑页，支持 resume、staging、稳定 Hash 和 unchanged/updated/incomplete 状态。
- `design-dashboard` / `plan-dashboard-change`：纯本地生成域绑定 DesignSpec 和结构化 dry-run Diff。
- `apply-dashboard-change`：消费精确 ChangePlan Hash，只执行五类窄范围 `verified/allowlisted` 草稿操作；逐目标双读、写后回读、最终完整画像。任一步失败会逆序恢复已完成操作，并在 ApplyReceipt 中记录恢复状态；不提供发布参数。
- `publish-dashboard-change`：独立消费 ChangePlan 和成功 ApplyReceipt，发布前再次核对完整 draft 与 publish payload，API 返回后再回读 draft Hash；在正式发布版本读取 API 缺失时，receipt 必须标记 `publish_requested_unverified` 与 `fully_verified=false`，不得把草稿回读冒充线上版本证明。
- `inspect-write-capabilities`：离线验证并汇总 P4A 写能力注册表、代码证据 Hash 和 allowlist；不启动浏览器。
- `capture-write-evidence`：只在明确测试看板中、显式确认且 headed 时，抓取一次人工草稿动作的脱敏请求结构和前后 Profile；主动阻断发布、删除、权限和认证写请求，不自动生成写适配器。
- `verify-sandbox-write-adapters`：读取显式 sandbox manifest，以正式适配器先逐项验证，再执行多操作连续 Apply、逆序恢复和完整 Profile Hash 复原；只用于沙箱，不能单独扩大生产白名单。
- `edit-public-filters`：legacy 只读兼容命令，仅保留序号式 dry-run 计划。任何 `--apply`、`--publish` 或 `--confirm-publish` 都会在浏览器启动前拒绝；所有写入必须走 stable-ID P3 链路。
- `profile-folder`：在某个文件夹下查找指定看板名并逐个生成 config-only 画像；仅在显式 `--profile-mode full` 时同步检查取值。
- `profile-all`：默认以 config-only 扫描 `市场顾问数据` 和 `青橙项目部`，为每个发现的看板生成画像，将原始 `profile.json` artifact 写到 runtime 目录，把市场顾问 markdown web 画像路由到 `sql-query-writer-for-dashboard/knowledge/dashboard_web_profiles/`，把青橙 markdown web 画像路由到 `qingcheng-dashboard-sql/knowledge/dashboard_web_profiles/`，并重建各自 README/changelog，避免混用两个知识库。

如果选择器发生漂移，先看 `references/platform_profile.md`，更新脚本里的 selector 列表或回退策略，再用 `--headed --debug-artifacts` 重跑。调试 artifact 可能包含 SQL 文本或可见结果，排查后应删除。

## 选择器漂移与通用 Playwright 回退

`SQL取数` 和 BI 看板流程默认使用本 skill 的脚本。只有当 `usql-web-query-operator` 命令已经复现问题，且捕获到的 JSON、截图或 HTML artifact 仍不足以判断 UI 变化时，才使用通用 `playwright` skill。

排查顺序：

1. 用相同的 `--browser-channel` / `--state-path`，加 `--headed --debug-artifacts` 重跑失败命令。
2. 先读 JSON summary。SQL 运行失败时，先用 `error_details`、`error_category` 和 `repair_guidance`，不要直接假设 selector 漂移。
3. 检查配置的 runtime artifact 目录。不要把截图、HTML、SQL 文本、结果预览、cookie 或下载文件复制到 `.codex/skills/`。
4. 如果需要理解截图内容，直接使用 Codex 原生多模态能力检查截图中的可见文本、布局和状态。
5. 如果仍需要 DOM 级探索，再用通用 `playwright` skill 做一次性 snapshot/screenshot/click/type 检查。
6. 持久修复必须回到本 skill：更新 selector、回退逻辑、`references/platform_profile.md` 或修复建议，然后重跑 USQL 脚本验证。

不要用通用 Playwright 替代以下能力：

- SQL 执行或结果下载。
- BI 文件夹扫描或看板画像。
- 登录态刷新或凭据处理。
- 行数限制 enforcement。
- SQL/BI 任务的调试 artifact 持久化。

当通用 Playwright 找到有用 selector 或交互模式时，只把它当作诊断证据。生产路径仍然是 `scripts/usql_web_query.py` 或 `scripts/read_dashboard.py`。

## 与 SQL skill 的配合

市场顾问和通用看板场景中，使用 `sql-query-writer-for-dashboard` 负责 SQL 生成、表字段校验、权限判断和结果解释。本 skill 只负责网页 UI 执行路径。

青橙项目部场景中，使用 `qingcheng-dashboard-sql` 负责青橙 SQL 生成、修复和口径解释；本 skill 仍只负责网页执行、模板取数和下载，不承接青橙口径推断。

如果上游业务 SQL skill 产出了 QueryPlan，必须把与之计算 Hash 时相同的 SQL 文件一并传给 `run --query-plan`。本 skill 只验证契约，不修改 QueryPlan、不补齐 `unresolved_slots`、不把不可执行计划升级为可执行计划。该联动不改变 `read_dashboard.py` 的只读默认和公共筛选器显式授权边界。

当用户要求“通过页面跑这个 SQL”时，先判断是否应使用本 skill；不要尝试 USQL RestAPI，除非用户明确要求 API 执行。

## 直接检查截图

当本 skill 在调试、错误分析、脚本验证或代码检查中捕获截图且需要理解其内容时，直接使用 Codex 原生多模态能力检查。

- 优先使用页面 JSON summary、`error_details`、HTML/DOM 和网络响应作为结构化证据。
- 只有结构化证据不足时才查看截图，以确认可见错误、页面状态、布局或字段。
- CAPTCHA、MFA 和风控挑战只做识别与报告，不尝试绕过。
- 截图和其他调试 artifact 仍放在 runtime 目录，不写入 skill 目录。
- 如果截图无法支持精确判断，回到 DOM 或接口证据，不根据模糊像素推断。

## 模板取数已保存 SQL

当用户要查看 `模板取数 -> 模板查询 -> 我的模板 -> 我创建的` 下某个模板当前保存的最新 SQL 时，使用：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py fetch-template-sql `
  --template-name "<模板名称>"
```

该命令会使用共享的百家登录态打开“我创建的模板”页面，调用页面背后的 `template/createList` 接口，并把选中行的 `sqlDetail` 保存到 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`；如果传入 `--output-file`，则写到指定位置。该命令是只读的：不会创建查询、不会执行 SQL、也不会下载结果。只有在需要把完整 SQL 一并打印到 JSON 摘要时，才使用 `--include-sql`。

当用户要从 `模板取数 -> 模板市场` 按模板名搜索模板、查看模板并读取“模板SQL”里的 SQL 时，使用：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py fetch-market-template-sql `
  --template-name "<模板名称>"
```

该命令会使用共享的百家登录态打开模板市场页面，调用 `market/search` 接口，并把返回行中的 `sqlDetail` 保存到 runtime 的 `template-query` 目录。它同样是只读命令：不会创建模板、不会创建查询、不会执行 SQL、不会下载结果，也不会修改模板市场内容。

## 模板取数大结果下载

当用户已经有一份可直接执行的具体 SQL，并且结果量超过 1000 行、若走 `SQL取数` 页面会进入下载审批链路时，使用：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py template-download `
  --sql-file C:\path\to\query.sql `
  --download-format csv
```

该命令会复用共享的百家登录态，并执行一条由接口驱动的完整链路：

1. 解析 SQL 并创建临时模板。
2. 发布模板。
3. 基于模板立即创建查询。
4. 轮询 `我的查询`，直到查询离开运行中状态。
5. 通过模板取数自己的下载接口下载结果。
6. 下线临时模板。
7. 删除临时模板。

生产说明：

- 该路径只适用于具体 SQL，不适用于仍带参数的模板 SQL。如果解析器发现还有未解析的模板条件，命令会在创建查询之前停止。
- 清理是默认行为。`--keep-template` 仅用于调试。
- `--download-format csv|xls` 对应页面暴露的两种下载类型。实测 `xls` 分支返回的是 `.xlsx` 文件名的 Excel 制品。
- 下载成功必须同时通过内容校验：拒绝对象存储 `ListBucketResult`/错误 XML 伪装成 CSV，拒绝查询有数据但工作簿只有表头或表头列数少于查询元数据的 Excel。`xls` 校验失败会自动请求模板 CSV；固定输出路径会把扩展名改为 `.csv`，summary 同时记录 requested/actual format 和 fallback reason。
- `模板取数 -> 我的查询` 下的查询历史记录不在该命令清理范围内；当前已验证的清理范围仅覆盖临时模板本身。

### 文档维护约定

- 后续维护本 skill 的说明类 Markdown 文档时，默认使用中文撰写。
- 命令名、参数名、字段名、接口名、路径、状态值以及必要的英文技术术语保留原文，避免影响识别和执行。

### 截图诊断顺序

1. **usql-web-query-operator**：执行脚本，遇到错误或需要验证时捕获截图。
2. 使用 Codex 原生多模态能力直接检查截图中的可见内容。
3. **usql-web-query-operator** 或 **sql-query-writer-for-dashboard**：用截图证据诊断、修复或验证。
