# QueryPlan 执行契约

`run --query-plan` 为 SQL 页面执行增加一个可选的只读前置契约。它用于确认上游业务 SQL skill 产出的 QueryPlan 与本次提交的 SQL 完全对应，并且已经达到可执行状态。

该能力只验证计划，不生成或修改 SQL，不修复 QueryPlan，也不打开任何新的看板、模板、临时表、数据集或权限写入能力。不传 `--query-plan` 时，`run` 保持原有行为。

## 命令

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py run `
  --sql-file C:\path\to\query.sql `
  --query-plan C:\path\to\query_plan.json `
  --no-download
```

`--sql-file` 仍是实际提交到 SQL 页面中的内容；QueryPlan 不能内嵌或替代 SQL 文件。

## 必需契约

QueryPlan 根对象必须满足：

| 字段 | 必需值或规则 |
|---|---|
| `schema_version` | 必须等于 `2.0.0` |
| `domain` | 只允许 `market_consultant` 或 `qingcheng` |
| `status` | 必须等于 `executable` |
| `unresolved_slots` | 必须存在且为空数组 |
| `diagnostics` | 必须存在且为数组，不得包含 `severity=error` |
| `sql_sha256` | 必须与本次提交的完整 SQL 文本 SHA-256 完全一致 |
| `execution_policy` | 必须存在且为 JSON 对象 |
| `execution_policy.allow_download` | 必须为布尔值；请求 `--download` 时必须严格等于 `true` |
| `execution_policy.max_direct_download_rows` | 必须为 1 到 1000 的整数 |
| `execution_policy.requires_preview` | 必须严格等于 `true` |
| `execution_policy.execution_mode` | 只允许 `production` 或 `exploratory` |

SQL Hash 不做去空格、去注释、大小写转换或结尾分号归一化。SQL 中的空白、注释和末尾换行发生变化后，应由上游重新生成 QueryPlan，不能手工沿用旧 Hash。

## 执行顺序

1. 读取 `--sql-file`。
2. 读取并校验 QueryPlan 的版本、业务域、状态和未解析槽位。
3. 校验 `sql_sha256` 是否匹配本次完整 SQL 文本。
4. 请求下载时，先检查 `execution_policy.allow_download`。
5. 继续执行原有本地下载预检查。
6. 只有以上校验通过后才导入 Playwright、打开浏览器并提交 SQL。
7. 查询成功后，下载仍要通过结果页行数策略。

契约无效时，命令返回使用错误并在浏览器启动前停止。不要把这类错误当成平台 SQL 报错重复提交。

## 下载双重门禁

携带 QueryPlan 的 `--download` 必须同时满足：

1. `execution_policy.allow_download=true`；
2. SQL 明显包含 `LIMIT 1000` 或更低限制，或者成功结果页能证明结果不超过 1000 行。

QueryPlan 只会收紧下载权限，不会放宽原有 1000 行限制。未携带 QueryPlan 时，现有下载策略保持不变。超过 1000 行且已获明确授权的具体 SQL，应继续走 `template-download` 及其独立清理流程。

## 运行摘要

契约通过后，`RunSummary` JSON 会增加紧凑的 `query_plan_contract`：

- QueryPlan 文件路径；
- `schema_version`；
- `domain`；
- `status`；
- `sql_sha256`；
- `allow_download`。

摘要不会复制完整 QueryPlan，也不会写入 SQL、凭证、cookie 或浏览器状态。不使用 `--query-plan` 时，不输出该字段，从而保持原有 summary 结构。

## 看板边界

QueryPlan 契约只适用于 `usql_web_query.py run`。它不会授权 `read_dashboard.py` 修改任何内容：

- `profile-edit-dashboard` 仍为只读；
- `edit-public-filters` 仍默认 dry-run；
- 写草稿仍必须显式 `--apply`；
- 发布仍必须显式 `--apply --publish --confirm-publish`。
