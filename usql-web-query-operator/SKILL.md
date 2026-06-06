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

6. Inspect the returned JSON summary. Successful runs include the query status, query id when detected, and a small visible-table preview when the page exposes one.
7. If `status=Failed`, read `error_details` before changing SQL:
   - `notification` / `message` / `alert`: the page rejected the SQL before or during submission, often without a query id.
   - `log_area`: a query was created; use the execution log, especially `VALIDATE_SQL_ERROR`, line/column, table, and column names.
   - See `references/query_error_handling.md` for verified cases and repair rules.
8. If the run succeeds and the result is within the download policy, rerun with `--download` or include `--download` on the original run.

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

## Script Capabilities

Use `scripts/usql_web_query.py` only for SQL取数:

- `doctor`: check Python Playwright availability and show install commands if missing.
- `login`: open the CAS login flow, authenticate, and save browser storage state outside the repo.
- `run`: open SQL取数, create or reuse a query tab, insert SQL into the CodeMirror editor, submit with `Ctrl+E` first and run-button fallbacks second, wait for query-history/result-tab status, capture `error_details` on platform failures, extract a small visible result-table preview when available, and optionally download xlsx when the local row-limit policy allows it.

Use `scripts/read_dashboard.py` only for 自助BI/dashboard operations:

- `scan-folder`: open 自助BI, read the dashboard menu, find a named folder such as `市场顾问数据`, and extract dashboard Chinese names plus IDs for later quick calls.
- `profile-dashboard`: open one dashboard by ID, wait for refresh, and store its component/filter/value structure outside the repo.
- `profile-folder`: find selected dashboard names under a folder and profile them one by one.

If selectors drift, inspect `references/platform_profile.md`, update the selector list or fallback strategy in the script, and rerun with `--headed --debug-artifacts`. Debug artifacts may include SQL text or visible results, so delete them after troubleshooting.

## Integration With SQL Skill

Use `sql-query-writer-for-dashboard` for SQL generation, table/field validation, permission reasoning, and result interpretation. Use this skill only for the web UI execution path.

When a user asks to "run this SQL through the page", first check whether this skill should be used; do not attempt USQL RestAPI unless the user explicitly requests API execution.
