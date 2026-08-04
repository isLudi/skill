# Text2SQL 运行工件

`run` 在不改变 QuerySpec/QueryPlan 2.0 契约的前提下，使用三种相互绑定的 JSON 工件记录可观测性与结果质量。显式 `run-with-fallback` 再增加一个只引用子工件的执行组工件。它们是审计证据，不是执行、下载、Apply 或 Publish 授权。

## QueryTrace

QueryTrace Schema 位于共享 Core 的 `schemas/query_trace.schema.json`。领域 `plan` / `compile` 可通过 `--trace-output` 创建 sidecar，operator 通过 `--trace-file` 继续同一条 trace；未指定时，`run` 在本次 runtime artifact 目录自动创建。

Trace 只记录：

- domain、spec/plan/SQL 的 ID 或 SHA-256；
- domain manifest、contract index、physical catalog 的快照 Hash；
- plan、compile、policy、execute 阶段状态、耗时和诊断代码；
- query ID、引擎与 ResultArtifact Hash。

Trace 不保存自然语言问题原文、SQL 文本、结果行、凭证、Cookie 或登录态。需要关联原始问题时只传 `--question-sha256`。

## SQL Policy Report

`run` 总是在导入 Playwright 前生成 `sql_policy_report.json`。DDL、DML、命令语句、多语句、解析失败和未解析模板参数属于硬阻断；Join、CTE、子查询、集合操作和窗口函数采用结构复杂度预算。

- `--policy-mode enforce`：超预算阻断；默认模式。
- `--policy-mode audit`：超预算只告警；只读语句、多语句和模板硬门禁仍不可绕过。
- `--required-partition-field`：显式声明必须出现在 `WHERE` 中的中性物理字段，可重复；operator 不自行推断业务分区。
- `--require-limit`：显式要求 LIMIT；QueryPlan 为 `execution_mode=exploratory` 时自动启用。

Schema 位于 [sql_policy_report.schema.json](sql_policy_report.schema.json)。

## ResultArtifact

`run` 在浏览器关闭后写出 `result_artifact.json`，或写入 `--result-artifact` 指定路径。Schema 位于共享 Core 的 `schemas/result_artifact.schema.json`。

ResultArtifact `1.1.0` 记录列头、可见行数、预览 Hash、QueryPlan 预期输出列校验、引擎、耗时、下载文件路径/大小/Hash 和诊断。预览结果行不会复制到该工件，只保留整体 Hash 并固定标记 `preview_rows_redacted=true`。

SQL取数还记录以下脱敏证据：

- 编辑器 SQL SHA-256、字节数和稳定回读次数；
- 选择引擎 key/标签、历史引擎和可识别的提交请求引擎；
- 单次提交方式、Query ID 来源、请求路径、HTTP 状态和提交 SQL SHA-256；
- `result_state`、结果来源、API 字段数/当前页行数/总行数、精确 Query ID 的完成来源、API/UI 冲突码和 UI 状态。

这些字段不保存 SQL 文本、请求负载、API 结果行、Cookie、Token 或浏览器指纹。QueryTrace 的 execute stage 只追加结果状态、Query ID 来源及 SQL Hash 对照。

结果契约校验中，缺少预期列等仍以 warning 记录；重复列、行宽不一致、摘要指向不存在的下载文件或 `result_unresolved` 标记 failed。UI 缺失但 API 已恢复结果时不再误报空结果。

## QueryExecutionGroupArtifact

`run-with-fallback` 为 primary 与最多一个 fallback/crosscheck attempt 生成 `QueryExecutionGroupArtifact 1.0.0`。Schema 位于共享 Core 的 `schemas/query_execution_group.schema.json`。

执行组工件记录：

- `fallback_once` 策略、主/备用引擎、注册表 Hash、解析来源与目录等价组；
- 每个 attempt 的引擎、Query ID、状态、`result_state`、暂态错误代码、耗时；
- 每个独立 QueryTrace/ResultArtifact 的路径、ID 与 Hash；
- 最终采用的 attempt、回退触发类型、资格判定原因、是否采用备用结果和跨引擎一致性。

执行组工件不保存 SQL 文本、问题原文、错误原文、结果行、Cookie、Token 或浏览器状态。`crosscheck-only` 的备用结果即使有行也固定 `alternate_result_adopted=false`；外层命令摘要同样不会输出备用预览或下载路径。

## 默认落点与连续性校验

未指定路径时，单 attempt 的三个工件均落在 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\<run-id>\`。执行组位于 `artifacts\fallback-groups\<group-id>\`，子 attempt 位于其 `attempts` 目录。已有 QueryTrace 的 domain、plan ID/hash 或 SQL hash 与本次输入不一致时，命令在浏览器启动前停止，不能把旧 trace 绑定到新 SQL。
