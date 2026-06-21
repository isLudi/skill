# Template Query automation

Use Template Query automation in two distinct cases.

## Fetch stored SQL

Use `scripts/usql_web_query.py fetch-template-sql` when the user wants the latest SQL stored in a template under:

`https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py fetch-template-sql `
  --template-name "<template name>"
```

Useful options:

- `--match exact|contains`: exact is the default. `contains` scans templates and picks the most recently updated match.
- `--status unpublished|published|offline`: optional status filter.
- `--output-file <path>`: save SQL to a specific file. Without this, output is written to `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`.
- `--include-sql`: include the full SQL in the JSON summary in addition to writing the SQL file.
- `--headed`: show the browser if login state needs inspection.

Verified API profile:

- Page URL: `https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`
- Shared state: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
- Runtime output: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`
- List API: `POST https://uanalysis.baijia.com/uanalysis-template/template/createList`
- Request body: `{"name":"<optional template name>","status":2,"pager":{"pageSize":100,"pageNo":1}}`
- Response rows include `sqlDetail`, which is the SQL shown by the UI flow `View template -> View SQL`.

The command is read-only. It does not create a template query, execute SQL, or download results.

## Temporary large-result download

Use `scripts/usql_web_query.py template-download` when the user has a concrete SQL file and needs to bypass the `SQL取数` download approval path for results larger than 1000 rows.

The command creates a temporary template, publishes it, creates an immediate query, waits for completion, downloads the result, then offlines and deletes the template by default.

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py template-download `
  --sql-file C:\path\to\query.sql `
  --download-format csv
```

Useful options:

- `--template-name <name>`: optional temporary template name, 20 characters or fewer.
- `--query-name <name>`: override the generated query name in `My Query`.
- `--download-format csv|xls`: `csv` is the default; `xls` returns the Excel-format artifact exposed by the page.
- `--output-file <path>`: save the downloaded file to a fixed path.
- `--include-preview`: include a small result preview in the JSON summary.
- `--keep-template`: skip offline/delete cleanup for debugging.
- `--debug-artifacts`: save screenshots and HTML in a timestamped runtime directory.

Current scope and safety boundary:

- Input SQL must already be concrete. This command currently rejects template parameters or unresolved query conditions.
- Cleanup is part of the production path. After a successful or failed run, the command attempts `offline -> delete` for the temporary template unless `--keep-template` is set.
- Query history entries under `My Query` are not cleaned by this command. The validated cleanup scope is the temporary template itself.

Verified API sequence on 2026-06-21:

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

Download type mapping:

- `type=1`: `csv`
- `type=2`: Excel artifact, observed filename `*.xlsx`
