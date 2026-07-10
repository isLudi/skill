# 模板取数自动化

模板取数自动化目前分为三类场景，分别对应“读取我创建的模板 SQL”“读取模板市场中的模板 SQL”和“用临时模板完成大结果下载”。

## 读取模板中已保存的 SQL

当用户要查看 `模板取数 -> 模板查询 -> 我的模板 -> 我创建的` 中某个模板当前保存的最新 SQL 时，使用 `scripts/usql_web_query.py fetch-template-sql`：

`https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py fetch-template-sql `
  --template-name "<模板名称>"
```

常用参数：

- `--match exact|contains`：默认 `exact`。`contains` 会扫描模板列表，并选择最近更新的匹配项。
- `--status unpublished|published|offline`：可选状态过滤。
- `--output-file <path>`：把 SQL 保存到指定文件。不传时，输出会写到 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`。
- `--include-sql`：除了写出 SQL 文件，也把完整 SQL 放进 JSON 摘要。
- `--headed`：需要检查登录态或页面行为时显示浏览器。

已验证的接口画像：

- 页面 URL：`https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`
- 共享登录态：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
- 运行时输出目录：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`
- 列表接口：`POST https://uanalysis.baijia.com/uanalysis-template/template/createList`
- 请求体结构：`{"name":"<可选模板名>","status":2,"pager":{"pageSize":100,"pageNo":1}}`
- 返回行包含 `sqlDetail` 字段，它与页面上“查看模板 -> 查看SQL”展示的是同一份 SQL。

该命令是只读的：不会创建模板、不会执行 SQL、也不会下载结果。

## 读取模板市场中的模板 SQL

当用户要查看 `模板取数 -> 模板市场` 中某个模板当前保存的 SQL 时，使用 `scripts/usql_web_query.py fetch-market-template-sql`：
`https://uanalysis.baijia.com/templateGetData/templateMarket`

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py fetch-market-template-sql `
  --template-name "<模板名称>"
```

常用参数：
- `--match exact|contains`：默认 `exact`。`contains` 会在模板市场搜索结果中选择最近发布/更新的匹配项。
- `--creator <creator>`：可选创建人精确过滤，用于模板名不唯一时收窄结果。
- `--output-file <path>`：把 SQL 保存到指定文件。不传时，输出写到 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`。
- `--include-sql`：除了写出 SQL 文件，也把完整 SQL 放进 JSON 摘要。
- `--headed`：需要检查登录态或页面行为时显示浏览器。

已验证的接口画像：
- 页面 URL：`https://uanalysis.baijia.com/templateGetData/templateMarket`
- 共享登录态：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
- 运行时输出目录：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`
- 模板市场搜索接口：`POST https://uanalysis.baijia.com/uanalysis-template/market/search`
- 请求体结构：`{"name":"<可选模板名>","pager":{"pageSize":100,"pageNo":1}}`
- 返回行包含 `sqlDetail` 字段，它与页面上“查看模板 -> 模板SQL -> 查看SQL”展示的是同一份 SQL。

该命令是只读的：不会创建模板、不会执行 SQL、不会下载结果，也不会修改模板市场中的任何内容。

## 临时模板大结果下载

当用户已经有一份可直接执行的 SQL，并且结果量超过 1000 行、想绕开 `SQL取数` 页面下载审批链路时，使用 `scripts/usql_web_query.py template-download`。

该命令会创建临时模板、发布模板、立即创建查询、等待结果完成、下载结果，然后默认执行下线和删除清理。

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py template-download `
  --sql-file C:\path\to\query.sql `
  --download-format csv
```

常用参数：

- `--template-name <name>`：可选的临时模板名，长度不超过 20 个字符。
- `--query-name <name>`：覆盖自动生成的“我的查询”名称。
- `--download-format csv|xls`：默认 `csv`；`xls` 对应页面暴露的 Excel 格式下载分支。
- `--output-file <path>`：把下载文件写到固定路径。
- `--include-preview`：在 JSON 摘要中附带小规模结果预览。
- `--keep-template`：调试时跳过下线和删除清理。
- `--debug-artifacts`：把截图和 HTML 保存到带时间戳的 runtime 目录。

当前范围与安全边界：

- 输入 SQL 必须已经是可直接执行的具体 SQL。当前实现会拒绝仍包含模板参数或未解析查询条件的 SQL。
- 清理是生产默认路径。无论成功或失败，只要未传 `--keep-template`，命令都会尝试执行 `offline -> delete` 清理临时模板。
- `我的查询` 下的查询历史记录不在该命令清理范围内；当前已验证的清理范围仅覆盖临时模板本身。
- 下载不是只看 HTTP 状态：XML `ListBucketResult`/错误负载、查询非空但 Excel 只有表头、Excel 表头列数少于 `query/result.meta` 都会被拒绝。
- 当请求 `xls` 且 Excel 制品校验失败时，命令自动改取模板 CSV；如 `--output-file` 以 `.xlsx` 结尾，实际文件写为同名 `.csv`。JSON summary 的 `downloadFormatRequested`、`downloadFormatActual` 和 `downloadFallbackReason` 用于审计该回退。

2026-06-21 已验证的接口顺序：

1. `POST https://uanalysis.baijia.com/uanalysis-template/template/sqlParser`
2. `POST https://uanalysis.baijia.com/uanalysis-template/template/saveAndUpdate`
3. `POST https://uanalysis.baijia.com/uanalysis-template/template/publish`
4. `POST https://uanalysis.baijia.com/uanalysis-template/query/detail`
5. `POST https://uanalysis.baijia.com/uanalysis-template/query/create`
6. `POST https://uanalysis.baijia.com/uanalysis-template/query/list`
7. `GET https://uanalysis.baijia.com/uanalysis-template/query/log?queryId=<id>`
8. `POST https://uanalysis.baijia.com/uanalysis-template/query/result`
9. `GET https://uanalysis.baijia.com/uanalysis-template/query/download?queryId=<id>&type=1|2`
10. `POST https://uanalysis.baijia.com/uanalysis-template/template/offline`
11. `POST https://uanalysis.baijia.com/uanalysis-template/template/delete`

下载类型映射：

- `type=1`：`csv`
- `type=2`：Excel 制品，实测文件名为 `*.xlsx`
