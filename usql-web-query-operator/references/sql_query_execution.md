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

默认引擎为 `presto`。只有 Presto 成功但结果疑似为空、需要补充验证或排查引擎差异时，才显式使用 `--engine doris-presto`。

## 4. 错误处理

失败时按以下顺序读取：

1. `error_details.detail`
2. `error_details.raw_snippet`
3. `error_details.title`
4. `error_category`、`error_category_label`
5. `repair_guidance`

`immediate_platform_error` 与 `query_log_error` 必须走不同修复路径。先使用结构化错误，不要默认重跑 headed、截图或 OCR。完整分类见 [query_error_handling.md](query_error_handling.md)。

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
