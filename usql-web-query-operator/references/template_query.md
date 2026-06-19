# Template Query SQL Fetch

Use `scripts/usql_web_query.py fetch-template-sql` when the user wants the latest SQL stored in a template under:

`https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`

The command is read-only. It authenticates with the shared Baijia browser state, opens the My Created templates page if needed, calls the same list API used by the page, and saves the selected template's `sqlDetail` field under the local runtime directory by default.

## Command

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

## API Profile

- Page URL: `https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`
- Shared state: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
- Runtime output: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`
- List API: `POST https://uanalysis.baijia.com/uanalysis-template/template/createList`
- Request body: `{"name":"<optional template name>","status":2,"pager":{"pageSize":100,"pageNo":1}}`
- Response field: each row includes `sqlDetail`, which is the SQL shown by the UI's `View template -> View SQL` flow.

The script does not create a template query, execute SQL, or download query results. It only reads template metadata and the stored SQL source.
