# SQL 网页执行与小结果下载

## 1. 适用范围

本流程只负责把已经解析完成的具体 SQL 提交到 `SQL取数` 页面、等待状态、提取结构化错误、预览小结果，并在双重下载门禁允许时下载不超过 1000 行的结果。

业务 SQL 和指标口径必须来自对应领域 Skill：

- `market_consultant` → `market-consultant-dashboard-sql`
- `qingcheng` → `qingcheng-dashboard-sql`

域未解析、QueryPlan 不可执行、SQL Hash 不一致或 SQL Policy 不通过时，在浏览器启动前停止。

## 2. 依赖和登录

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py doctor
D:\anaconda3\python.exe scripts\usql_web_query.py login --headed
```

凭据只从环境变量、`--env-file`、`USQL_ENV_FILE` 或交互输入读取。SSO、MFA、二维码或风控阻断自动登录时，使用 `login --manual --headed`，不得尝试绕过。

登录态固定保存在 Git 外的 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`。

## 3. 执行

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py run `
  --sql-file C:\path\to\query.sql `
  --headed `
  --no-download
```

存在精确绑定的 QueryPlan 时：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py run `
  --sql-file C:\path\to\query.sql `
  --trace-file C:\path\to\query_trace.json `
  --query-plan C:\path\to\query_plan.json `
  --headed `
  --no-download
```

QueryPlan 必须满足 `schema_version=2.0.0`、受支持业务域、`status=executable`、`unresolved_slots=[]`、SQL SHA-256 完全一致并包含 `execution_policy`。完整契约见 [query_plan_contract.md](query_plan_contract.md)。

每次 `run` 都会在浏览器启动前生成 SQL Policy Report，并在运行结束后生成 QueryTrace 与 ResultArtifact；默认落在本次 runtime artifact 目录。完整字段与隐私边界见 [text2sql_runtime_artifacts.md](text2sql_runtime_artifacts.md)。

默认引擎为 `presto`。当前显式支持：

- `--engine presto` → `Presto`
- `--engine presto-lakehouse` → `Presto_lakehouse`
- `--engine doris-presto` → `Doris-Presto / doris内测加速版`

普通 `run` 只执行一个引擎 attempt，默认不回退。用户已确认 `Presto` 与 `Presto_lakehouse` 使用等价目录；该确认记录在 [query_engine_fallbacks.json](query_engine_fallbacks.json)。`Doris-Presto` 仍必须显式指定或由领域 override 注册，不能从名字推断目录、权限或数据新鲜度等价。

提交使用确定性状态门禁，而不是模拟人工输入：

1. 引擎标签连续稳定回读；
2. CodeMirror 内容连续稳定回读，SHA-256 必须与输入 SQL 完全一致；
3. 只触发一次运行控件；
4. 在 `--submission-ack-timeout-ms` 内绑定唯一新 Query ID；未确认时停止，不自动再次点击；
5. 若捕获到提交请求，则核对提交 SQL Hash，并在可识别时核对请求引擎。

`--engine-ready-timeout-ms`、`--editor-ready-timeout-ms`、`--submission-ack-timeout-ms`、`--result-api-timeout-ms` 和 `--result-ui-timeout-ms` 只调整有条件的状态等待上限，不增加随机打字、删改、viewport 变化或浏览器指纹伪装。

### 结果状态

查询状态成功后，operator 使用精确 Query ID 轮询结果 API，并只把 UI 结果面板作为第二证据：

| `result_state` | 含义 | 命令结果 |
|---|---|---|
| `success_with_rows` | API 有行且 UI 同时可见 | 成功 |
| `success_ui_missing_recovered` | API 有行、UI 未暴露表格，已从 API 恢复预览 | 成功 |
| `success_with_rows_ui` | API 暂不可用，但精确查询 UI 有可见行 | 成功，保留 API 诊断 |
| `success_empty_verified` | 精确 Query ID 的 API/完成状态证明 0 行 | 成功，明确报告 0 行 |
| `result_unresolved` | 执行成功，但 API 与对应 UI 都无法确认结果 | 失败；不得解释成业务无数据 |

API 未给出总行数的空页只有在同一 Query ID 的日志或历史行确认完成后，才能升级为 `success_empty_verified`。如果结果 API 明确为 0 行、但激活后的同一查询结果页出现数据，则记录 `api_zero_ui_rows` 冲突并返回 `result_unresolved`，不让任一侧静默覆盖另一侧。

### 显式 fallback_once

只有以下外层命令开启一次性回退：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py run-with-fallback `
  --sql-file C:\path\to\query.sql `
  --engine presto `
  --no-download
```

不传 `--fallback-engine` 时，注册表把 `presto-lakehouse` 解析为 `presto` 的默认等价目录备用。显式 Doris 示例：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py run-with-fallback `
  --sql-file C:\path\to\query.sql `
  --engine presto `
  --fallback-engine doris-presto `
  --no-download
```

执行组规则：

1. primary 与 fallback 必须使用完全相同的 SQL SHA-256；不做方言改写。
2. 每个 attempt 仍只点击一次，并分别生成 QueryTrace 与 ResultArtifact；平台受理提交后，各自绑定自己的新 Query ID。若请求在平台受理前即以 502/503/504 终止，Query ID 只能如实记录为 `null`，不得伪造或重复提交来补 ID。
3. 只有 primary 为 `result_unresolved`，或终态错误命中明确暂态白名单（HTTP 502/503/504、服务临时不可用、连接失败、引擎/集群临时不可用）时才运行 fallback。
4. 语法、字段、表、类型、Join、权限、403/429、CAPTCHA/MFA、分区规则、stage 上限及普通客户端 Timeout 不触发 fallback。Timeout 时原任务可能仍在运行，禁止创建第二个并发任务。
5. fallback 最多一次；fallback 失败后不得再试第三个引擎。
6. fallback 成功时，只有普通回退路径可以采用结果并在原下载门禁允许时下载。

`success_empty_verified` 默认停止。只有显式交叉验证才执行备用引擎：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py run-with-fallback `
  --sql-file C:\path\to\query.sql `
  --empty-result-policy crosscheck-only `
  --no-download
```

交叉验证始终强制备用 attempt `download=false`：两侧都为 0 行时记录 `consistent_empty`；备用有行时记录 `cross_engine_data_divergence` 并退出失败；备用结果不会成为 selected result，也不会自动下载，命令摘要同时隐藏备用结果预览和下载路径。

每次显式外层执行都会生成一个 `QueryExecutionGroupArtifact`，记录 attempt 的引擎、Query ID、子工件 Hash、触发类型、资格判定原因、最终选择和跨引擎一致性，不复制 SQL 或结果行。

## 4. 错误处理

失败时按以下顺序读取：

1. `error_details.detail`
2. `error_details.raw_snippet`
3. `error_details.title`
4. `error_category`、`error_category_label`
5. `repair_guidance`

`immediate_platform_error` 与 `query_log_error` 必须走不同修复路径。先使用结构化错误，不要默认重跑 headed、截图或 OCR。完整分类见 [query_error_handling.md](query_error_handling.md)。

`result_unresolved` 不是 SQL 失败，也不是空结果。普通 `run` 仍先检查 ResultArtifact；显式 `run-with-fallback` 可在同一 SQL Hash 下执行一次注册备用。若两次都未决，再决定是否需要 headed selector 诊断。

只有显式使用 `--debug-artifacts` 才保存截图/HTML。结构化证据不足且 operator 已复现后，才按 [platform_profile.md](platform_profile.md) 使用通用 Playwright 做一次性 selector 诊断。

## 5. 下载边界

直接下载必须同时满足：

- SQL 明确 `limit <= 1000`，或结果页能可靠证明不超过 1000 行；
- 携带 QueryPlan 时，`execution_policy.allow_download=true`。

无效 CSV/XML、空表头或列不完整 Excel 必须报告失败。超过 1000 行的明确结果切换到 [template_query.md](template_query.md) 的 `template-download`，不得静默创建模板。

## 6. 登录态和调试制品

- 通用 Playwright 不得管理或替换 operator 登录态。
- SQL、结果预览、截图、HTML、下载文件和 API 缓存只写 runtime。
- CAPTCHA、MFA 和风控挑战只识别并报告。
- QueryTrace、Policy Report 和 ResultArtifact 只保存 Hash、状态与列级元数据；ResultArtifact 不复制预览结果行。
