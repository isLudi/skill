---
name: usql-web-query-operator
description: Automate governed USQL web-query execution through the company SQL取数 page with Playwright, preserving browser login state and enforcing local safety checks such as row/download limits. Use when Codex needs to run, verify, or download results from https://uanalysis.baijia.com/getDataSql because API permissions are insufficient but the authenticated web UI can perform the same user-authorized operation.
---

# usql-web-query-operator

## Purpose

Use this skill to operate the company SQL取数 web page through Playwright when USQL RestAPI permissions are insufficient but the logged-in web account can run the query manually.

This skill does not bypass permissions. It only automates actions that the authenticated user can perform in the browser.

## Safety Boundary

- Never write passwords, cookies, tokens, screenshots, or downloaded query results into the skill directory.
- Store Playwright login state only under a local runtime path outside git, defaulting to `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`.
- Read account credentials from environment variables, `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env`, or interactive prompts. Do not hard-code them in scripts, docs, shell history, or committed files.
- Do not download result sets unless the SQL visibly limits output to 1000 rows or fewer, or the successful result page proves there are no more than 1000 rows.
- Prefer preview/exploration SQL with `limit <= 1000`.
- If the page reports permission, platform, or SQL errors, preserve the error text and optionally save debug screenshots only when `--debug-artifacts` is explicitly set.
- If `run` returns `ok=false`, read `error_details.detail`, then `error_details.raw_snippet`, then `error_details.title`; repair the SQL from that captured reason before retrying.
- Also read `error_category`, `error_category_label`, and `repair_guidance` from the final JSON summary. Treat `即时错误` and `日志区错误` as different repair paths.

- Keep SQL/BI browser login state owned by this skill. Do not use the generic `playwright` skill to read, write, copy, refresh, or replace `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`.

## Workflow

1. Generate and validate SQL with `sql-query-writer-for-dashboard`.
2. Ensure the SQL is safe for web execution:
   - Presto syntax.
   - Full table names.
   - Required `dt` and `hour` partitions.
   - Required department or architecture filters.
   - `limit <= 1000` before any download attempt.
3. Run the local dependency check:

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py doctor
```

The script defaults to the installed Microsoft Edge channel (`--browser-channel msedge`), so a separate Playwright Chromium download is optional when Edge is available.

4. Save or refresh browser login state:

```powershell
$env:BAIJIA_USERNAME='<account>'
$env:BAIJIA_PASSWORD='<password>'
D:\anaconda3\python.exe scripts\usql_web_query.py login --headed
```

If automated login is blocked by SSO, MFA, QR code, or risk control, rerun `login --manual --headed`, complete login in the opened browser, then press Enter in the terminal.

5. Execute a safe SQL file:

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py run --sql-file C:\path\to\query.sql --headed --no-download
```

The script now switches the query engine before writing SQL. Default: `doris-presto`.
Use `--engine presto` when you need a baseline comparison or when Doris-Presto behavior must be ruled out.

6. Inspect the returned JSON summary. Successful runs include the query status, query id when detected, and a small visible-table preview when the page exposes one.
7. If `status=Failed`, read `error_details` before changing SQL:
   - `error_category=immediate_platform_error` / `error_category_label=即时错误`: the page rejected the SQL before a stable query row was created, often through a top-right notification. Stop retrying and fix the SQL first.
   - `error_category=query_log_error` / `error_category_label=日志区错误`: a query row was created; use the execution log, especially `VALIDATE_SQL_ERROR`, line/column, table, and column names.
   - `notification` / `message` / `alert`: the page rejected the SQL before or during submission, often without a query id.
   - `log_area`: a query was created; use the execution log, especially `VALIDATE_SQL_ERROR`, line/column, table, and column names.
   - `repair_guidance`: use the script-provided repair suggestion before guessing from raw page text.
   - See `references/query_error_handling.md` for verified cases and repair rules.
8. If the run succeeds and the result is within the download policy, rerun with `--download` or include `--download` on the original run.

## Temporary Table Upload

Use `scripts/usql_web_query.py upload-temp-table` when the user explicitly wants to upload a local CSV/Excel manual table through the SQL取数 temporary-table UI.

Example:

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py upload-temp-table `
  --file E:\path\to\manual_table.xlsx `
  --target-table dingxi01_qing_team_jg `
  --target-mode reuse `
  --import-mode overwrite
```

The command opens the SQL取数 page, switches to `临时表`, runs `建表向导`, uploads the local file via the hidden file input, maps all detected fields, starts the import, and waits until `导入历史` reports `成功`. Successful summaries include the import-history row, including `临时表名` and `数据量`.

Keep uploads user-authorized and file-specific. Do not upload arbitrary local files without an explicit user request. Debug artifacts stay under the runtime artifacts directory.

## Dashboard Folder Scan

Do not use `usql_web_query.py` for dashboard folders or dashboard data. That script is only for SQL取数 execution and result downloads.

When asked to discover dashboard names and IDs under a web folder, use `scripts/read_dashboard.py`:

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py scan-folder --folder 市场顾问数据 --headed
```

Use `--wait-ms <milliseconds>` when the BI page or dashboard list refreshes slowly. The command writes JSON under the local runtime artifacts directory by default.

When asked to open dashboards and capture their page structures, use:

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py profile-dashboard --dashboard-id dashboard_3730722176629411841 --wait-ms 45000
D:\anaconda3\python.exe scripts\read_dashboard.py profile-folder --folder 市场顾问数据 --names '外呼过程数据看板|转化数据' --dashboard-wait-ms 45000
```

Profile output records dashboard render status, component units, global filters, field IDs, metric names, task IDs, row counts, and chart series counts. It intentionally avoids storing returned result rows.

For a full sync of the current market-consultant and Qingcheng dashboard folders into their isolated SQL skill knowledge bases, run:

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py profile-all --dashboard-wait-ms 15000
```

## Script Capabilities

Use `scripts/usql_web_query.py` only for SQL取数:

- `doctor`: check Python Playwright availability and show install commands if missing.
- `login`: open the CAS login flow, authenticate, and save browser storage state outside the repo.
- `run`: open SQL取数, create or reuse a query tab, switch the engine before writing SQL, insert SQL into the CodeMirror editor, submit with `Ctrl+E` first and run-button fallbacks second, wait for query-history/result-tab status, capture `error_details` on platform failures, extract a small visible result-table preview when available, and optionally download xlsx when the local row-limit policy allows it.
- `upload-temp-table`: upload a local `.csv`, `.xls`, or `.xlsx` into the `临时表` area. It supports `--target-mode new|reuse`, `--import-mode overwrite|append`, `--header-row|--no-header-row`, and emits a JSON summary from `导入历史`.

Relevant `run` options:
- Failure summaries now explicitly classify `即时错误` versus `日志区错误` and emit `repair_guidance` for the next SQL edit.
- `--engine doris-presto`: select `Doris-Presto -> doris内测加速版` before query execution. This is the default.
- `--engine presto`: force the original Presto engine for baseline checks and engine-difference troubleshooting.

Use `scripts/read_dashboard.py` only for 自助BI/dashboard operations:

- `scan-folder`: open 自助BI, read the dashboard menu, find a named folder such as `市场顾问数据`, and extract dashboard Chinese names plus IDs for later quick calls.
- `profile-dashboard`: open one dashboard by ID, wait for refresh, and store its component/filter/value structure outside the repo.
- `profile-folder`: find selected dashboard names under a folder and profile them one by one.
- `profile-all`: scan `市场顾问数据` and `青橙项目部` by default, profile every discovered dashboard, write raw `profile.json` artifacts under the runtime directory, route market markdown web profiles to `sql-query-writer-for-dashboard/knowledge/dashboard_web_profiles/`, route Qingcheng markdown web profiles to `qingcheng-dashboard-sql/knowledge/dashboard_web_profiles/`, and rebuild each target README/changelog without mixing the two knowledge bases.

If selectors drift, inspect `references/platform_profile.md`, update the selector list or fallback strategy in the script, and rerun with `--headed --debug-artifacts`. Debug artifacts may include SQL text or visible results, so delete them after troubleshooting.

## Selector Drift and Generic Playwright Fallback

Default to this skill's scripts for SQL取数 and BI dashboard flows. Use the generic `playwright` skill only after a `usql-web-query-operator` command has reproduced the issue and the captured JSON, screenshot, or HTML artifact is not enough to identify the changed UI.

Selector drift triage order:

1. Rerun the failing command with `--headed --debug-artifacts` and the same `--browser-channel` / `--state-path` used by the USQL script.
2. Read the JSON summary first. For SQL runs, use `error_details`, `error_category`, and `repair_guidance` before assuming selector drift.
3. Inspect runtime artifacts under the configured artifacts directory. Do not copy screenshots, HTML, SQL text, result previews, cookies, or downloads into `.codex/skills/`.
4. If screenshot text is needed, use `mineru-converter` to extract it into `C:\Users\Ludim\.codex\runtime\tmp\` or stdout.
5. If DOM-level exploration is still needed, use the generic `playwright` skill for one-off snapshot/screenshot/click/type inspection only.
6. Move the durable fix back into this skill: update selectors, fallback logic, `references/platform_profile.md`, or repair guidance, then rerun the USQL script to verify.

Do not use generic Playwright as a replacement for:

- SQL execution or result downloads.
- BI folder scanning or dashboard profiling.
- Login-state refresh or credential handling.
- Row-limit enforcement.
- Persisting debug artifacts for SQL/BI tasks.

When generic Playwright reveals a useful selector or interaction pattern, treat it as diagnostic evidence. The production path remains `scripts/usql_web_query.py` or `scripts/read_dashboard.py`.

## Integration With SQL Skill

Use `sql-query-writer-for-dashboard` for SQL generation, table/field validation, permission reasoning, and result interpretation. Use this skill only for the web UI execution path.

When a user asks to "run this SQL through the page", first check whether this skill should be used; do not attempt USQL RestAPI unless the user explicitly requests API execution.

## Image Reading via mineru-converter

When this skill captures screenshots during debugging, error analysis, script execution verification, or code inspection — and the content of those images is needed — delegate to `mineru-converter` instead of trying to visually interpret pixels.

### When to invoke mineru-converter

| Scenario | Example |
|---|---|
| **Error diagnosis** | Playwright captured a platform error popup / notification — extract the exact error text |
| **Script verification** | Need to confirm the page rendered correctly after a script change — read the rendered data in the screenshot |
| **Login/state issues** | Login page shows an unexpected challenge (CAPTCHA, risk control, MFA prompt) — extract the message |
| **Dashboard profiling** | read_dashboard.py captured a chart/metric screenshot — extract visible metric names and values |
| **Selector debugging** | The page structure changed — read the screenshot to understand the new layout |

### How to invoke

```powershell
# Step 1: Load token from env file
$env:MINERU_TOKEN = (Get-Content "E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env" | Select-String '^MINERU_TOKEN=(.+)$').Matches.Groups[1].Value

# Step 2: Extract image content (flash-extract for quick reads, extract for detailed analysis)
mineru-open-api flash-extract <screenshot_path>.png -o C:\Users\Ludim\.codex\runtime\tmp\<descriptive_name>.md
# OR for detailed analysis (auth required):
mineru-open-api extract <screenshot_path>.png -o C:\Users\Ludim\.codex\runtime\tmp\<descriptive_name>.md
```

### Output policy

- **NEVER** write mineru-converter output to `.codex/skills/` or any skill directory.
- Use `C:\Users\Ludim\.codex\runtime\tmp\` for temporary extracted Markdown files.
- Delete temp files after the information has been consumed and the task is complete.
- For stdout-only reads (no persistent output needed): omit `-o` and consume the Markdown directly.
- `flash-extract` is preferred for quick text reads of screenshots; use `extract` only when the screenshot contains complex tables or formulas that need precise preservation.

### Cross-skill coordination

When both this skill and `mineru-converter` are needed, follow this sequence:

1. **usql-web-query-operator** — Execute the script, capture screenshot on error or for verification
2. **mineru-converter** — Read the screenshot, return extracted text/data
3. **usql-web-query-operator** or **sql-query-writer-for-dashboard** — Use the extracted content for diagnosis, repair, or verification
