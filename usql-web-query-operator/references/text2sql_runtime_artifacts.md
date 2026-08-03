# Text2SQL 运行工件

`run` 在不改变 QuerySpec/QueryPlan 2.0 契约的前提下，使用三种相互绑定的 JSON 工件记录可观测性与结果质量。它们是审计证据，不是执行、下载、Apply 或 Publish 授权。

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

ResultArtifact 记录列头、可见行数、预览 Hash、QueryPlan 预期输出列校验、引擎、耗时、下载文件路径/大小/Hash 和诊断。预览结果行不会复制到该工件，只保留整体 Hash 并固定标记 `preview_rows_redacted=true`。

P0 的结果契约校验是观察性门禁：缺少预期列、缺少可见 preview 等以 warning 记录；重复列、行宽不一致或摘要指向不存在的下载文件标记 failed，但不替代现有下载文件硬校验。

## 默认落点与连续性校验

未指定路径时，三个工件均落在 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\<run-id>\`。已有 QueryTrace 的 domain、plan ID/hash 或 SQL hash 与本次输入不一致时，命令在浏览器启动前停止，不能把旧 trace 绑定到新 SQL。
