---
name: usql-web-query-operator
description: Automate governed USQL web-query execution through the company SQL取数 page with Playwright, preserving browser login state and enforcing local safety checks such as row/download limits. Use when Codex needs to run, verify, or download results from https://uanalysis.baijia.com/getDataSql because API permissions are insufficient but the authenticated web UI can perform the same user-authorized operation.
---

# usql-web-query-operator

## 用途

当 USQL RestAPI 权限不足、但当前登录账号可以在网页端手工执行 SQL 时，使用本 skill 通过 Playwright 自动操作公司 `SQL取数` 页面。

本 skill 不绕过权限，只自动化当前认证用户在浏览器中本来可以完成的动作。

## 安全边界

- 不要把密码、cookie、token、截图或下载的查询结果写入 skill 目录。
- Playwright 登录态只保存到 git 外的本地 runtime 路径，默认是 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`。
- 账号密码从环境变量、`E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env` 或交互式输入读取，不要硬编码到脚本、文档、shell history 或已提交文件中。
- 除非 SQL 明确限制 `limit <= 1000`，或成功结果页能证明结果不超过 1000 行，否则不要下载结果集。
- 预览和探索 SQL 优先使用 `limit <= 1000`。
- 如果页面返回权限、平台或 SQL 错误，保留错误文本；只有显式设置 `--debug-artifacts` 时才保存调试截图。
- 如果 `run` 返回 `ok=false`，先读 `error_details.detail`，再读 `error_details.raw_snippet`，最后读 `error_details.title`，根据捕获到的原因修 SQL 后再重试。
- 同时读取最终 JSON 里的 `error_category`、`error_category_label`、`repair_guidance`。`即时错误` 和 `日志区错误` 是两条不同修复路径。
- SQL/BI 浏览器登录态归本 skill 管理。不要使用通用 `playwright` skill 读取、写入、复制、刷新或替换 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`。

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

脚本会在写入 SQL 前切换查询引擎。默认引擎是 `doris-presto`。当需要基线对比，或需要排除 Doris-Presto 行为差异时，使用 `--engine presto`。

6. 检查返回的 JSON summary。成功运行会包含查询状态、检测到的 query id，以及页面能暴露时的小范围可见表格预览。
7. 如果 `status=Failed`，修改 SQL 前必须先读 `error_details`：
   - `error_category=immediate_platform_error` / `error_category_label=即时错误`：页面在稳定查询行生成前拒绝 SQL，通常是右上角 notification。停止重复运行，先按弹窗文本修 SQL。
   - `error_category=query_log_error` / `error_category_label=日志区错误`：查询行已创建，错误在执行日志里；优先使用 `VALIDATE_SQL_ERROR`、行列号、表名、字段名等信息修复。
   - `notification` / `message` / `alert`：页面在提交前或提交中拒绝 SQL，可能没有 query id。
   - `log_area`：查询任务已创建，使用执行日志，尤其是 `VALIDATE_SQL_ERROR`、行列号、表名、字段名。
   - `repair_guidance`：先用脚本给出的修复建议，再考虑从原始页面文本推断。
   - 已验证案例和修复规则见 `references/query_error_handling.md`。
8. 如果运行成功且满足下载策略，可重新运行并加 `--download`，或在原始运行中直接包含 `--download`。

## 数据地图字段同步

当用户希望用 `https://tiangong2.baijia.com/dataMap/dataMapNew` 补齐或刷新业务 SQL skill 中的物理表字段说明时，使用：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-datamap-fields --target-skill all
```

默认是 dry-run：脚本登录数据地图，查找目标 skill 知识库中已有的物理表文档，对比数据地图字段和 `knowledge/tables/*.md`，只打印 JSON summary，不写文件。

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
- 使用 `--write` 且确实产生字段变更时，会追加 changelog，并默认运行目标 skill 的 `scripts/build_reverse_indexes.py` 和 `scripts/check_skill_integrity.py`。
- 使用 `--no-refresh-datamap` 可只从本地 runtime 缓存同步；使用 `--only-missing-cache` 可只刷新新增表。

## 数据中心源 SQL 同步

当用户要求把 `https://uanalysis.baijia.com/data-center/data-set` 中的数据集源 SQL 写入业务 SQL skill 知识库时，使用：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-data-center-sql --target-skill all
```

默认是 dry-run：脚本使用本 skill 的共享登录态打开数据中心，通过目录和数据集详情接口读取目标范围，打印 JSON summary，不写业务 skill 文件。
确认范围后再加 `--write`：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-data-center-sql `
  --target-skill all `
  --write
```

内置目标和范围：

- `qingcheng`：写入 `qingcheng-dashboard-sql`，同步父目录为 `市场顾问部/青橙项目部` 的全部 SQL 数据集。
- `market`：写入 `sql-query-writer-for-dashboard`，同步父目录为 `市场顾问部/市场顾问部` 且从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- `all`：按上述规则同步两个业务 skill；两个知识库保持隔离。

写入规则：

- 完整源 SQL 保存到目标 skill 的 `resources/raw_sql/data_center_<target>_<fileValue>_<YYYYMMDD>.sql`。
- 数据集清单保存到目标 skill 的 `knowledge/dashboards/data_center_<target>_datasets.md`，记录数据集名称、菜单 ID、`fileValue`、`subjectId`、数据源 ID、平台路径和 raw SQL 文件。
- 脚本只保存数据中心接口返回的 `executeSql`，不改写 SQL 语义，不推断字段或指标口径。
- 加 `--write` 且发生文件变更时，会追加 changelog，并默认运行目标 skill 的 `scripts/build_reverse_indexes.py` 和 `scripts/check_skill_integrity.py`。
- 运行摘要保存到 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\data-center\`，不会把 cookie 或账号密码写入 skill 目录。

常用增量参数：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-data-center-sql `
  --target-skill market `
  --dataset-name 市场渠道用户成单分析3 `
  --write
```

`--market-start-name` 可覆盖市场顾问目录的起始数据集名；`--dataset-name` 可重复传入，用于只刷新指定数据集。

## 临时表上传

当用户明确要求把本地 CSV/Excel 手工表上传到 `SQL取数` 的临时表 UI 时，使用：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py upload-temp-table `
  --file E:\path\to\manual_table.xlsx `
  --target-mode reuse `
  --import-mode overwrite
```

对于以下目录下已登记的手工表：

- `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格`
- `E:\2000_work\GAOTU\20003_青橙项目部看板维护表格`

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
D:\anaconda3\python.exe scripts\read_dashboard.py profile-dashboard --dashboard-id dashboard_3730722176629411841 --wait-ms 45000
D:\anaconda3\python.exe scripts\read_dashboard.py profile-folder --folder 市场顾问数据 --names '外呼过程数据看板|转化数据' --dashboard-wait-ms 45000
```

profile 输出记录看板渲染状态、组件单元、全局筛选器、字段 ID、指标名、task ID、行数和图表 series 数量。它有意不保存返回的结果行。

如果要把当前市场顾问和青橙看板文件夹完整同步到各自隔离的 SQL skill 知识库，运行：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py profile-all --dashboard-wait-ms 15000
```

## 脚本能力

`scripts/usql_web_query.py` 只用于 `SQL取数`：

- `doctor`：检查 Python Playwright 可用性，缺失时给出安装命令。
- `login`：打开 CAS 登录流程，认证后把浏览器 storage state 保存到 repo 外。
- `run`：打开 `SQL取数`，创建或复用查询 tab，写入 SQL 前切换引擎，将 SQL 写入 CodeMirror，优先用 `Ctrl+E` 提交、再用运行按钮 fallback，等待查询历史/结果 tab 状态，平台失败时捕获 `error_details`，可用时提取小范围可见结果预览，并在本地行数限制允许时下载 xlsx。
- `sync-datamap-fields`：使用数据地图页面和接口刷新 `sql-query-writer-for-dashboard` 和/或 `qingcheng-dashboard-sql` 中的物理表字段说明。默认 dry-run，只有 `--write` 才写文档。
- `sync-data-center-sql`：使用数据中心页面和接口刷新 `sql-query-writer-for-dashboard` 和/或 `qingcheng-dashboard-sql` 中的数据集源 SQL。默认 dry-run，只有 `--write` 才写 raw SQL、清单文档和 changelog。
- `upload-temp-table`：把本地 `.csv`、`.xls` 或 `.xlsx` 上传到 `临时表` 区域。支持 `--target-mode new|reuse`、`--import-mode overwrite|append`、`--header-row|--no-header-row`，并从 `导入历史` 输出 JSON summary。
- `check-manual-table`：读取手工表 registry，将本地 Excel 文件解析到平台标准临时表名，并在不触碰浏览器的情况下执行 workbook 校验。

常用 `run` 选项：

- 失败 summary 会明确区分 `即时错误` 和 `日志区错误`，并输出 `repair_guidance` 供下一轮 SQL 修改使用。
- `--engine doris-presto`：执行前选择 `Doris-Presto -> doris内测加速版`，这是默认值。
- `--engine presto`：强制使用原始 Presto，用于基线检查和引擎差异排查。

`scripts/read_dashboard.py` 只用于自助BI / dashboard：

- `scan-folder`：打开自助BI，读取看板菜单，查找 `市场顾问数据` 等文件夹，并提取中文看板名和 ID。
- `profile-dashboard`：按 ID 打开单个看板，等待刷新，把组件/筛选器/值结构保存到 repo 外。
- `profile-folder`：在某个文件夹下查找指定看板名并逐个 profile。
- `profile-all`：默认扫描 `市场顾问数据` 和 `青橙项目部`，profile 每个发现的看板，将原始 `profile.json` artifact 写到 runtime 目录，把市场顾问 markdown web profile 路由到 `sql-query-writer-for-dashboard/knowledge/dashboard_web_profiles/`，把青橙 markdown web profile 路由到 `qingcheng-dashboard-sql/knowledge/dashboard_web_profiles/`，并重建各自 README/changelog，避免混用两个知识库。

如果 selector 漂移，先看 `references/platform_profile.md`，更新脚本里的 selector 列表或 fallback 策略，再用 `--headed --debug-artifacts` 重跑。调试 artifact 可能包含 SQL 文本或可见结果，排查后应删除。

## Selector 漂移与通用 Playwright fallback

`SQL取数` 和 BI 看板流程默认使用本 skill 的脚本。只有当 `usql-web-query-operator` 命令已经复现问题，且捕获到的 JSON、截图或 HTML artifact 仍不足以判断 UI 变化时，才使用通用 `playwright` skill。

排查顺序：

1. 用相同的 `--browser-channel` / `--state-path`，加 `--headed --debug-artifacts` 重跑失败命令。
2. 先读 JSON summary。SQL 运行失败时，先用 `error_details`、`error_category` 和 `repair_guidance`，不要直接假设 selector 漂移。
3. 检查配置的 runtime artifact 目录。不要把截图、HTML、SQL 文本、结果预览、cookie 或下载文件复制到 `.codex/skills/`。
4. 如果需要读取截图文字，用 `mineru-converter` 提取到 `C:\Users\Ludim\.codex\runtime\tmp\` 或 stdout。
5. 如果仍需要 DOM 级探索，再用通用 `playwright` skill 做一次性 snapshot/screenshot/click/type 检查。
6. 持久修复必须回到本 skill：更新 selector、fallback 逻辑、`references/platform_profile.md` 或修复建议，然后重跑 USQL 脚本验证。

不要用通用 Playwright 替代以下能力：

- SQL 执行或结果下载。
- BI 文件夹扫描或看板 profile。
- 登录态刷新或凭据处理。
- 行数限制 enforcement。
- SQL/BI 任务的调试 artifact 持久化。

当通用 Playwright 找到有用 selector 或交互模式时，只把它当作诊断证据。生产路径仍然是 `scripts/usql_web_query.py` 或 `scripts/read_dashboard.py`。

## 与 SQL skill 的配合

使用 `sql-query-writer-for-dashboard` 负责 SQL 生成、表字段校验、权限判断和结果解释。本 skill 只负责网页 UI 执行路径。

当用户要求“通过页面跑这个 SQL”时，先判断是否应使用本 skill；不要尝试 USQL RestAPI，除非用户明确要求 API 执行。

## 通过 mineru-converter 读取图片

当本 skill 在调试、错误分析、脚本验证或代码检查中捕获截图，且确实需要读取截图内容时，交给 `mineru-converter`，不要凭肉眼猜像素内容。

### 何时调用 mineru-converter

| 场景 | 示例 |
|---|---|
| 错误诊断 | Playwright 捕获到平台错误弹窗 / notification，需要提取准确错误文本 |
| 脚本验证 | 需要确认脚本修改后页面是否正确渲染，读取截图中的可见数据 |
| 登录/状态问题 | 登录页出现 CAPTCHA、风控、MFA 等异常挑战，需要提取页面消息 |
| 看板 profile | `read_dashboard.py` 捕获图表/指标截图，需要提取可见指标名和值 |
| selector 调试 | 页面结构变化，需要从截图判断新布局 |

### 调用方式

```powershell
# 第 1 步：从 env 文件加载 token
$env:MINERU_TOKEN = (Get-Content "E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env" | Select-String '^MINERU_TOKEN=(.+)$').Matches.Groups[1].Value

# 第 2 步：提取图片内容。快速读取用 flash-extract，复杂内容用 extract。
mineru-open-api flash-extract <screenshot_path>.png -o C:\Users\Ludim\.codex\runtime\tmp\<descriptive_name>.md
# 或详细分析（需要鉴权）：
mineru-open-api extract <screenshot_path>.png -o C:\Users\Ludim\.codex\runtime\tmp\<descriptive_name>.md
```

### 输出策略

- **绝不要**把 mineru-converter 输出写入 `.codex/skills/` 或任何 skill 目录。
- 临时 Markdown 输出放到 `C:\Users\Ludim\.codex\runtime\tmp\`。
- 信息消费完成、任务结束后删除临时文件。
- 只需要 stdout 时，省略 `-o`，直接消费 Markdown。
- 截图快速读字优先用 `flash-extract`；只有截图包含复杂表格或公式且需要高保真时才用 `extract`。

## Template Query stored SQL

When the user needs to inspect the latest SQL stored in a Template Query template under `Template Query -> My templates -> My created`, use:

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py fetch-template-sql `
  --template-name "<template name>"
```

The command opens the My Created templates page with the shared Baijia login state, calls the page-backed `template/createList` API, and saves the selected row's `sqlDetail` to `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\` unless `--output-file` is provided. It is read-only: it does not create a query, execute SQL, or download results. Use `--include-sql` only when the full SQL should also be printed in the JSON summary.

## Template Query large-result download

When the user needs to download a concrete SQL result that would otherwise hit the `SQL取数` approval flow for results larger than 1000 rows, use:

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py template-download `
  --sql-file C:\path\to\query.sql `
  --download-format csv
```

The command uses the shared Baijia login state and runs an API-backed lifecycle:

1. Parse SQL and create a temporary template.
2. Publish the template.
3. Create an immediate query from the template.
4. Poll `My Query` until the query leaves the running state.
5. Download the result through Template Query's own download API.
6. Offline the temporary template.
7. Delete the temporary template.

Production notes:

- This path is for concrete SQL, not parameterized template SQL. If the parser finds unresolved template conditions, the command stops before query creation.
- Cleanup is the default behavior. Use `--keep-template` only for debugging.
- `--download-format csv|xls` maps to the two download types exposed by the page. The observed `xls` branch returns an Excel-format artifact with an `.xlsx` filename.
- Query-history rows under `Template Query -> My Query` are not cleaned by this command. The validated cleanup scope is the temporary template itself.

### 跨 skill 顺序

同时需要本 skill 和 `mineru-converter` 时，按以下顺序：

1. **usql-web-query-operator**：执行脚本，遇到错误或需要验证时捕获截图。
2. **mineru-converter**：读取截图，返回提取到的文本/数据。
3. **usql-web-query-operator** 或 **sql-query-writer-for-dashboard**：用提取结果诊断、修复或验证。
