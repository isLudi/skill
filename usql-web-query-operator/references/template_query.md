# 模板取数自动化

模板取数自动化目前分为四类场景，分别对应“读取我创建的模板 SQL”“读取模板市场中的模板 SQL”“永久参数化模板创建/发布/回读”和“用临时模板完成大结果下载”。永久模板与临时下载模板是两条独立生命周期，不能互相降级。

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

## 永久参数化模板创建、发布和回读

当用户明确要求把一份已核对的参数化 SQL 上线为长期使用的模板时，必须使用三个独立命令：

1. `plan-template-creation`：远端只读。读取精确重名状态、当前登录创建人和平台 `sqlParser` 元数据，绑定 SQL、字段/参数元数据和 Plan Hash。
2. `apply-template-creation`：生产写入。只创建状态为 `unpublished` 的模板，并立即回读模板 ID、名称、状态、SQL Hash、`instanceKey`、输出字段和参数元数据 Hash。
3. `publish-template`：独立发布。绑定成功创建回执的精确 Hash，发布前重读未发布状态，发布后再回读 `published` 状态和全部 Hash。

参数配置文件是 UTF-8 JSON，对 SQL 中每一个 `${name}` 参数提供一条明确配置。当前受支持的已验证模式为：

- `date`：平台日期控件，固定 `paramType=3`，格式 `yyyy-MM-dd`。
- `condition`：普通条件控件，固定 `paramType=1`，需要字段类型。
- 两种模式当前都要求 `mandatory=2`；SQL parser 解析出的比较符（例如 `>=`、`<`）会进入 Plan 和回读 Hash。

日期区间示例：

```json
{
  "day:1": {
    "showName": "维护日期开始",
    "mode": "date",
    "mandatory": 2,
    "format": "yyyy-MM-dd"
  },
  "day:2": {
    "showName": "维护日期结束",
    "mode": "date",
    "mandatory": 2,
    "format": "yyyy-MM-dd"
  }
}
```

创建计划：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py plan-template-creation `
  --template-name "<永久模板名>" `
  --template-description "<模板说明>" `
  --sql-file C:\path\to\parameterized.sql `
  --parameter-config C:\path\to\parameters.json `
  --variable-display-name "parser_name=业务展示名" `
  --output-file C:\path\to\template_plan.json
```

创建未发布模板：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py apply-template-creation `
  --plan-file C:\path\to\template_plan.json `
  --expected-plan-sha256 <reviewed_plan_hash> `
  --confirm-production-write `
  --output-file C:\path\to\create_receipt.json
```

独立发布：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py publish-template `
  --receipt-file C:\path\to\create_receipt.json `
  --expected-receipt-sha256 <reviewed_create_receipt_hash> `
  --confirm-publish `
  --output-file C:\path\to\publish_receipt.json
```

治理边界：

- 模板名必须为 1–20 个字符且精确唯一；Plan 发现重名即阻断。
- SQL 必须是 UTF-8 无 BOM、单条只读查询，且至少含一个合法 `${name}` 参数。安全检查只为解析而把参数替换为 `NULL`，不会改变保存的原 SQL 或其 Hash。
- 参数配置必须与 parser 参数全集一一对应；未知配置、遗漏配置、字段别名漂移、数据源或登录创建人漂移均阻断。同一参数可在 SQL 的多个谓词中复用，但只配置一次。
- 默认数据源实例为已验证的 `dlc_presto`；该值和 parser 表/字段/参数全部进入 Hash。
- `apply-template-creation` 只创建未发布模板，绝不自动发布；`publish-template` 只能消费成功且完整回读的创建回执。
- 创建或发布失败时不自动下线、删除或回滚永久模板。远端写入可能已发生时，失败回执会设置 `manual_attention_required=true`。
- Plan、创建回执和 QueryPlan 都不构成下一阶段授权；每个生产阶段仍需本命令要求的精确 Hash 和显式确认。

2026-08-03 已验证的永久模板接口：

- `POST .../template/sqlParser`，请求同时携带参数化 SQL 和 `instanceKey`。
- `POST .../template/saveAndUpdate`，保存 `templateVariable`、`templateParam`、创建人、所有者和 `instanceKey`。
- `POST .../template/detail`，回读 SQL、状态、参数、字段、表和数据源实例。
- `POST .../template/publish`，只由独立发布命令调用。
- 日期参数回读为 `paramType=3`、`format=yyyy-MM-dd`；普通条件参数为 `paramType=1`。

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
- `--debug-artifacts`：把截图和 HTML 保存到带时间戳的 runtime 目录。

当前范围与安全边界：

- 输入 SQL 必须已经是可直接执行的具体 SQL。当前实现会拒绝仍包含模板参数或未解析查询条件的 SQL。
- 清理是不可跳过的强制路径。无论成功或失败，只要临时模板已经创建，命令都会尝试执行 `offline -> delete`；清理失败时整条命令失败，不提供保留模板参数。
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
