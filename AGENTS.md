# Local Codex Runtime

- For Python tasks in this Codex workspace, use `D:\anaconda3\python.exe` as the default interpreter.
- For package inspection or installation, use `D:\anaconda3\python.exe -m pip ...`.
- Do not call bare `python` or `C:\Python314\python.exe` unless the task explicitly requires checking or using the Python 3.14 installation.

## Global UTF-8 Encoding Policy

The rules in this section are global. They apply across all workflows, all skills, all repositories under this workspace, and all PowerShell commands that may touch non-ASCII text such as Chinese, Japanese, emoji, Markdown, YAML, JSON, JSONL, SQL, prompts, logs, and API payloads.

- Default all newly created or edited text artifacts to `UTF-8` by default. When exact encoding matters on Windows, prefer `UTF-8 without BOM` unless the target tool explicitly requires BOM or another encoding.
- Before running PowerShell commands that read, write, print, pipe, or transmit non-ASCII text, first force the shell and Python subprocesses into UTF-8 mode:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
```

- If a local `windows-utf8-shell` skill or equivalent prelude script exists, it may be sourced before such commands, but the behavior above is the required baseline even when the skill is not installed.
- PowerShell is forbidden from directly generating non-ASCII file content. Do not use PowerShell pipelines, here-strings, `echo`, `Write-Output`, string interpolation, `Set-Content`, `Add-Content`, `Out-File`, `>`, `>>`, or any other shell-text path to create or rewrite files that contain Chinese, Japanese, emoji, Markdown, YAML, JSON, JSONL, SQL, prompts, logs, or any other non-ASCII content.
- The only approved ways to create or rewrite non-ASCII text files in this workspace are:
  1. `apply_patch` for direct repository edits.
  2. `D:\anaconda3\python.exe` with explicit `encoding="utf-8"` or explicit UTF-8 byte writes.
- If PowerShell needs to participate in a workflow that produces non-ASCII content, PowerShell may only orchestrate file paths and invoke Python or another already-validated UTF-8-safe writer. PowerShell must not carry the non-ASCII payload itself.
- Prefer `apply_patch` for stable text-file edits. For generated reports or exact file writes, prefer Python file I/O with explicit encoding, for example `Path(path).read_text(encoding="utf-8")` and `Path(path).write_text(text, encoding="utf-8")`.
- For PowerShell file reads, use `-LiteralPath`, `-Raw`, and explicit UTF-8 encoding:

```powershell
Get-Content -LiteralPath $path -Raw -Encoding UTF8
```

- Treat any PowerShell-based write path for non-ASCII content as unsafe by default, even if `-Encoding UTF8` is specified. Prefer Python when exact `UTF-8 without BOM` behavior matters because Windows PowerShell 5.1 and PowerShell 7 differ on UTF-8 write behavior.
- For Python snippets that may emit non-ASCII stdout or stderr, explicitly reconfigure the streams:

```python
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
```

- For JSON or API payloads, build the payload in Python and encode bytes explicitly as UTF-8. Use `ensure_ascii=True` for unproven gateways or fragile transport paths; use `ensure_ascii=False` only after that specific path is proven safe.
- After reading or writing important non-ASCII files, verify the content by reopening the file with explicit UTF-8 and checking for mojibake markers such as `�`, `锟斤拷`, `鈥`, `Ã`, `Â`, or `??`.
- If output contains mojibake, unreadable Chinese, empty replies, or corrupted JSON, suspect shell transport or encoding first. Do not infer business logic, field meanings, SQL semantics, or API behavior from garbled text.

## Skill Auto-Orchestration

When a user request matches any scenario below, automatically load and orchestrate the corresponding skills. **Do not require the user to explicitly name which skill to use.**

### Skill Inventory & Trigger Conditions

#### sql-query-writer-for-dashboard
**Load when ANY of the following is true:**
- User wants to query, fetch, or export data from the company's internal database
- User asks to write, modify, explain, or fix SQL (especially Presto SQL)
- User mentions dashboards (看板), metrics (指标), table schemas (表结构), field meanings (字段含义), or data definitions (口径)
- User provides a SQL error message and asks for a fix
- User mentions company-specific business concepts: consultant (顾问), lead (线索), conversion (转化), outbound call (外呼), department/org structure (部门/架构), channel (渠道), refund (退款), traffic (流量), etc.
- User says "query/ fetch/ pull/ run XX data" (查/取/跑/拉 XX 数据)
- User asks to maintain or update the skill knowledge base (tables, metrics, dashboard docs, etc.), unless the request is explicitly for 青橙项目部 / Qingcheng project department

**Scope:** SQL generation, validation, and repair; knowledge base lookups; reverse lookup across fields, tables, metrics, raw SQL, and debug clues; metric definition explanations. Does NOT execute SQL or manipulate Excel files.

#### qingcheng-dashboard-sql
**Load when ANY of the following is true:**
- User explicitly mentions 青橙项目部 / Qingcheng project department
- User asks to write, modify, explain, or fix SQL for 青橙 dashboards, metrics, temp tables, joins, or range rules
- User asks to ingest, maintain, or correct 青橙 dashboard docs, metric docs, table docs, temp-table docs, join docs, changelog entries, or Web BI structure snapshots
- User asks to profile or document 青橙 dashboard front-end structure for later SQL/BI maintenance

**Scope:** Qingcheng-only SQL generation and isolated knowledge-base maintenance. All 青橙 artifacts, including Web BI profile markdown, README indexes, quick references, decision trees, and reverse indexes, must stay inside `skills/qingcheng-dashboard-sql`.

#### usql-web-query-operator
**Load when ANY of the following is true:**
- User asks to execute/run SQL (including SQL just generated by sql-query-writer)
- User wants to download query results from the company SQL platform (SQL取数)
- User wants to fetch the latest stored SQL from a Template Query template (模板取数 / 我的模板 / 我创建的)
- User wants to use Template Query to download a concrete SQL result that would exceed the direct `SQL取数` download approval path, including temporary template create-query-download-cleanup
- User asks to scan dashboard folders or retrieve dashboard ID lists
- User says "run this SQL" (跑一下这个 SQL), "execute this query" (执行这个查询), "download results" (下载结果)
- User wants to profile BI dashboard structures
- User wants to read Taitan dashboard edit-page pivot-table fields, metric meanings, or custom metric formulas without modifying the dashboard

**Scope:** Playwright web automation for SQL execution, direct xlsx result downloads, Template Query stored-SQL fetch and large-result download, BI dashboard scanning/profiling, and read-only Taitan edit-page metric/formula profiling. Does NOT generate SQL or modify dashboards.

#### playwright
**Load only when ANY of the following is true:**
- User asks for generic browser automation outside company SQL/BI workflows
- User asks to inspect, click, type, screenshot, snapshot, or debug a non-USQL web page
- A `usql-web-query-operator` script has a selector drift or UI-flow problem and needs one-off DOM/screenshot exploration after the USQL script has already captured or reproduced the issue
- A local web app or ordinary website needs browser interaction that is not covered by a more specific skill

**Scope:** Generic browser CLI automation and UI debugging. It is a supporting tool, not the entrypoint for SQL取数, BI dashboard scanning, dashboard profiling, login-state refresh, or result downloads.

#### xlsx
**Load when ANY of the following is true:**
- User references a `.xlsx` / `.xlsm` / `.csv` / `.tsv` file by path or name
- User asks to create, edit, fix, or format a spreadsheet
- User wants data exported as an Excel file
- User says "make a table" (做成表格), "generate Excel" (生成 Excel), "export to spreadsheet" (导出到表格), "process this file" (处理这个文件)
- User needs to analyze or clean tabular data where the deliverable is a spreadsheet file

**Scope:** Excel creation, editing, formatting, and formula calculation. Does NOT generate SQL or execute queries.

#### mineru-converter
**Load when ANY of the following is true:**
- User wants to read, parse, extract, or summarize content from a PDF, image, or Office document
- User shares a document file path and asks about its content
- User needs OCR on scanned documents or screenshots
- User wants to extract tables, formulas, or structured data from a document
- User says "read this PDF/image" (读一下这个 PDF/图片), "what does this screenshot say" (这个截图里有什么), "extract tables from this document" (提取文档中的表格)
- User wants to convert a document between formats (PDF -> Markdown, PDF -> Word, etc.)
- **OR**: another skill (especially usql-web-query-operator) needs to interpret image/screenshot content during debugging, error analysis, or code inspection

**Scope:** Document-to-Markdown extraction via MinerU Open API. Two modes: `flash-extract` (free, <=10MB/20pp) and `extract` (auth required, <=200MB/600pp, full fidelity). Output can be consumed inline (stdout) or saved to file.

#### lark-* (Feishu CLI Skills)
**Load when ANY of the following is true:**
- User wants to configure `lark-cli`, authenticate, switch `user`/`bot` identity, fix Feishu scope errors, or handle permission-denied responses -> `lark-shared`
- User wants to read or edit Feishu docs or wiki content, or gives a recognizable `/docx/` or `/wiki/` URL/token -> `lark-doc` or `lark-wiki`
- User wants to upload, download, search, move, copy, import, export, inspect, or organize Feishu Drive files/folders -> `lark-drive`
- User wants to read or edit Feishu online sheets, formulas, pivot tables, charts, or workbook structure -> `lark-sheets`
- User wants to work with Feishu Base/bitable tables, records, views, dashboards, forms, or workflows -> `lark-base`
- User wants to send/search chat messages, manage chats, download chat files, or reply in Feishu IM -> `lark-im`
- User wants calendar, contacts, mail, slides, tasks, approvals, OKRs, minutes, notes, VC, whiteboard, or other Feishu domain operations -> use the matching `lark-*` skill by domain
- User gives a Feishu/Lark/OpenLark URL or token and the resource type is recognizable from the path -> route to the matching `lark-*` skill instead of generic web fetch

**Scope:** `lark-*` skills are the preferred path for Feishu data and operations. Keep setup/auth, identity repair, and scope recovery in `lark-shared`, then hand off to the most specific domain skill.

### Composite Workflows (Auto-Orchestrated)

When a task spans multiple skills, chain them in the order specified below.

If the business domain is explicitly 青橙项目部, replace step 1's SQL-writing skill with `qingcheng-dashboard-sql` and keep every generated knowledge artifact under that skill only.

#### Workflow A: Data Query & Fetch (highest frequency)
> "Query last week's outbound call conversion data" (查一下上周外呼转化数据)

1. **sql-query-writer-for-dashboard** - Search knowledge base, generate Presto SQL
2. **usql-web-query-operator** - Execute SQL via Playwright on the SQL platform, preview results
3. If download is needed and the result can stay within the normal `SQL取数` safety boundary -> `usql-web-query-operator` downloads xlsx
4. If the user explicitly needs a large-result export that would trigger the `SQL取数` approval path -> switch to **Workflow L**

#### Workflow B: Query + Export to Excel Report
> "Export this month's consultant sales ranking to Excel" (导出本月顾问销售排名到 Excel)

1. **sql-query-writer-for-dashboard** - Generate SQL
2. **usql-web-query-operator** - Execute SQL and download xlsx; if the export would exceed the direct `SQL取数` download boundary, switch to **Workflow L**
3. **xlsx** - Open the downloaded file, format it, add formulas, and produce the polished report

#### Workflow C: SQL Fix & Re-run
> "This SQL errored out - fix it" (这个 SQL 报错了，修一下)

1. **sql-query-writer-for-dashboard** - Analyze error details and repair the SQL
2. **usql-web-query-operator** - Re-execute the fixed SQL

#### Workflow D: SQL Generation Only
> "Write a SQL query for XX" (写一个查询 XX 的 SQL)

- **sql-query-writer-for-dashboard** only (no execution)

#### Workflow E: Dashboard Discovery & Profiling
> "What dashboards are under the 市场顾问数据 folder?" (看一下市场顾问数据文件夹下有哪些看板)

- **usql-web-query-operator** only (`read_dashboard.py scan-folder` / `profile-dashboard`)

#### Workflow E2: Dashboard Edit-Page Metric Formula Profiling
> "Read each pivot table's metric meaning and custom formula from this dashboard edit page" (读取这个看板编辑页每个透视表的指标含义和自定义公式)

- **usql-web-query-operator** only (`read_dashboard.py profile-edit-dashboard`)
- Boundary: read-only. Do not save, publish, delete, create, update, or otherwise modify dashboard metrics.

#### Workflow F: Excel-Only Operations
> "Clean up this CSV and turn it into a formatted Excel file" (把这个 CSV 整理成格式化的 Excel)

- **xlsx** only

#### Workflow G: Query + Analyze Results
> "Query XX data, then analyze the trends" (查询 XX 数据，然后分析趋势)

1. **sql-query-writer-for-dashboard** - Generate SQL
2. **usql-web-query-operator** - Execute SQL and download xlsx; if the export would exceed the direct `SQL取数` download boundary, switch to **Workflow L**
3. **xlsx** - Load the data with pandas and perform analysis or visualization

#### Workflow H: Document Reading & Extraction
> "Read this PDF and summarize" (读一下这个 PDF 并总结) / "What does this screenshot contain?" (这个截图里有什么)

1. **mineru-converter** - Extract document/image content to Markdown
2. Parse the extracted Markdown and respond to the user's specific request

#### Workflow I: Debug Screenshot Analysis
> Agent encounters an error screenshot during USQL script execution and needs to understand its content

1. **usql-web-query-operator** - Capture the debug screenshot from the Playwright session
2. **mineru-converter** - Read the screenshot via `flash-extract` and return the text or error content
3. **usql-web-query-operator** or **sql-query-writer-for-dashboard** - Use the extracted text to diagnose and repair

#### Workflow J: USQL Selector Drift & Browser Fallback
> A SQL/BI automation script fails because the page structure, selector, popup, or interaction flow appears to have changed

1. **usql-web-query-operator** - Reproduce with the relevant script and `--headed --debug-artifacts`; keep artifacts under the runtime directory, not in skill directories
2. **mineru-converter** - If screenshots contain needed text, extract the visible message or page labels
3. **playwright** - Only if DOM-level or one-off browser exploration is still needed, inspect the page with snapshot, screenshot, click, or type commands
4. **usql-web-query-operator** - Update the selector list, fallback strategy, or documentation, then rerun the USQL script to verify

#### Workflow K: Template Query Stored SQL Fetch
> "Fetch the latest SQL saved in template XX" (把模板 XX 里最新保存的 SQL 取出来)

- **usql-web-query-operator** only (`fetch-template-sql` against `Template Query -> My templates -> My created`)

#### Workflow L: Large-Result Download Via Template Query
> "Download this concrete SQL result even if it exceeds 1000 rows" (这个具体 SQL 的结果超过 1000 行也要下载)

1. **sql-query-writer-for-dashboard** - Generate or finalize a concrete SQL file with no unresolved template parameters
2. **usql-web-query-operator** - Use `template-download` to create a temporary Template Query template, publish it, create the query, download the result, then run `offline -> delete`
3. If a formatted deliverable is needed -> **xlsx**

#### Workflow M: Feishu CLI Setup, Auth, and Domain Handoff
> "Set up Feishu CLI / log in / fix Feishu permissions / operate a Feishu resource"

1. **lark-shared** - Initialize config, start the auth flow, or repair identity or scope issues
2. **Matching `lark-*` domain skill** - Execute the requested Feishu task once config or auth is ready
3. If the task fails because of missing scope or wrong identity, return to **lark-shared**, repair auth or identity, then retry the domain skill

### Execution Rules

1. **Auto-detect**: On receiving a user request, determine which skill(s) are needed based on the trigger conditions above, then execute in workflow order. Never wait for the user to say "please load skill X."
2. **Progress transparency**: When orchestrating multiple skills, briefly inform the user at each stage transition, for example "Generating SQL -> Executing via web -> Exporting to Excel".
3. **Failure recovery**: If a stage fails, auto-repair in the next stage when possible. Example: SQL error -> fall back to `sql-query-writer-for-dashboard` for a fix and retry; expired web login -> prompt the user for manual login.
4. **Global UTF-8 enforcement**: The UTF-8 policy above is not optional. Whenever commands or files involve non-ASCII content, follow the UTF-8 rules before using PowerShell, Python, Node, Playwright wrappers, document tools, or API/debug scripts.
5. **Boundary enforcement**:
   - `sql-query-writer-for-dashboard` is read-only with respect to skill content unless the user explicitly requests knowledge-base maintenance
   - Qingcheng isolation: any 青橙 dashboard docs, metrics, temp tables, joins, changelog entries, or `dashboard_web_profiles` content must be written only to `skills/qingcheng-dashboard-sql`; never mix them into `sql-query-writer-for-dashboard`
   - SQL skill index maintenance: after modifying dashboards, metrics, tables, temp tables, joins, or raw SQL for either `sql-query-writer-for-dashboard` or `qingcheng-dashboard-sql`, run that skill's `scripts/build_reverse_indexes.py` before `scripts/check_skill_integrity.py`
   - Feishu skill location: install and maintain Feishu CLI skills under `C:\Users\Ludim\.codex\skills\lark-*`; do not treat `C:\Users\Ludim\.codex\.agents\skills` as the long-term home for these skills
   - Feishu skill discovery: every installed `lark-*` skill must keep `agents/openai.yaml`; if a new skill does not appear in the callable skill list, inspect its registration metadata and restart Codex after install or update
   - `usql-web-query-operator` safety policy: no direct `SQL取数` downloads exceeding 1000 rows without confirmation; when the user explicitly needs a large-result export and the SQL is already concrete, prefer the Template Query temporary-download path with enforced cleanup (`offline -> delete`); never expose credentials
   - Playwright boundary: do not use generic Playwright directly for `SQL取数` execution, BI dashboard scanning or profiling, Taitan edit-page metric or formula profiling, authenticated SQL-platform downloads, or login-state management; route those through `usql-web-query-operator`
   - `xlsx` formula rule: use Excel formulas, not hardcoded Python-computed values
6. **Credentials**:
   - Generic Playwright must not read, write, copy, or replace the USQL browser storage state. Keep SQL/BI login state owned by `usql-web-query-operator` at `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
   - `usql-web-query-operator` reads login credentials from `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env` (`BAIJIA_USERNAME` / `BAIJIA_PASSWORD`). Never hardcode them. Browser login state is stored at `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
   - `mineru-converter` reads `MINERU_TOKEN` from the same env file `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env`. Token expires 2026-09-09. Load it with:

```powershell
$env:MINERU_TOKEN = (Get-Content -LiteralPath "E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env" -Encoding UTF8 | Select-String '^MINERU_TOKEN=(.+)$').Matches.Groups[1].Value
```
