# Codex Workspace and Skills Repository Instructions

This is the single Git-versioned instruction source for `C:\Users\Ludim\.codex`. Codex loads it directly from the `skills` repository and loads its byte-identical runtime mirror when the working directory is `C:\Users\Ludim\.codex`.

Runtime, encoding, authorization, instruction-layout, and orchestration rules apply throughout the `.codex` workspace. Repository rules apply when work reads or changes `C:\Users\Ludim\.codex\skills`. For a selected Skill, read its complete `SKILL.md` and required references before acting. Skill-local rules remain authoritative when they are more specific or restrictive; this top-level summary never expands a Skill's write, download, Apply, or Publish authority.

## Runtime

- Use `D:\anaconda3\python.exe` for Python and `D:\anaconda3\python.exe -m pip ...` for package work.
- Do not use bare `python` or `C:\Python314\python.exe` unless the task explicitly targets Python 3.14.

## Global UTF-8 Policy

- Create and edit text as UTF-8, preferably without BOM unless the consumer explicitly requires another encoding.
- Before PowerShell reads, prints, pipes, or transmits non-ASCII text, run:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
```

- PowerShell must not carry or generate non-ASCII file payloads through pipelines, here-strings, `echo`, `Write-Output`, interpolation, `Set-Content`, `Add-Content`, `Out-File`, `>`, or `>>`. Use `apply_patch` or `D:\anaconda3\python.exe` with explicit `encoding="utf-8"`; byte-for-byte copying is allowed.
- Read important text with explicit UTF-8, for example `Get-Content -LiteralPath $path -Raw -Encoding UTF8`. Reopen important writes and check for the Unicode replacement character `U+FFFD`, known Chinese/Western mojibake sequences, or suspicious repeated question marks before trusting the content.
- Python snippets that emit non-ASCII output must reconfigure stdout and stderr to UTF-8. Build JSON/API payloads in Python and encode bytes explicitly; prefer `ensure_ascii=True` for unproven gateways and use `ensure_ascii=False` only on a verified UTF-8 path.
- Treat mojibake, empty non-ASCII replies, and corrupted JSON as transport or encoding failures before inferring business meaning.

## Authorization and Safety

- Inspect, explain, diagnose, review, profile, or plan requests are read-only. They do not authorize knowledge maintenance, browser writes, production changes, publication, Git commits/pushes, or external messages.
- Keep read-only planning/dry-run, draft Apply, production Apply, and Publish as separate authorization boundaries. A spec, QueryPlan, profile, plan hash, receipt, or successful prior step does not grant the next permission.
- Preserve unrelated user changes. Never use destructive Git or filesystem commands unless the user explicitly requests the exact operation and the targets are verified.
- Never print, hardcode, copy, or expose credentials, tokens, browser storage state, authorization URLs, or secret-bearing environment files.
- When a material decision needs user input and bounded choices exist, provide concise structured options rather than requesting a free-form description.

## Instruction Layout and Git Versioning

- `C:\Users\Ludim\.codex\skills\AGENTS.md` is the only Git-versioned source. `C:\Users\Ludim\.codex\WORKSPACE_AGENTS.md` is its generated runtime mirror; do not edit both independently or commit the mirror.
- `C:\Users\Ludim\.codex\AGENTS.md`, `C:\Users\Ludim\.codex\AGENTS.override.md`, `C:\Users\Ludim\.codex\.git`, and `C:\Users\Ludim\.codex\skills\AGENTS.global.md` must remain absent because they can restore duplicate or competing discovery.
- `C:\Users\Ludim\.codex\config.toml` must keep `project_doc_fallback_filenames = ["WORKSPACE_AGENTS.md"]` and a project-document limit of at least this file's size but no more than `32768` bytes.
- After editing the canonical file, run `sync_agents.ps1 -Mode Export -NoCommit`, then `sync_agents.ps1 -Mode Check`. Use `-Mode Import -ConfirmImport -NoCommit` only to deliberately replace the canonical file with a reviewed runtime mirror.
- Omitting `-NoCommit` lets the sync script commit only `AGENTS.md`; adding `-Push` pushes the current branch. During multi-file maintenance use `-NoCommit`, validate all files, then commit the reviewed scope together. Never infer commit or push permission from an ordinary edit request.

## Skill Auto-Orchestration

Auto-detect the smallest sufficient Skill set from the request and current artifact identities. Announce each transition when chaining Skills. Do not ask the user to name a Skill that can be resolved from these rules.

### Business SQL Skills

- Select `sql-query-writer-for-dashboard` for explicit 市场顾问部 / market-consultant metrics, dashboards, tables, joins, ranges, channels, evaluation, attendance, outbound calls, refunds, traffic, registered artifacts, or market knowledge maintenance. It owns market semantic contracts, QuerySpec/QueryPlan, governed SQL generation/repair, bounded probes, and dashboard design artifacts. It does not execute SQL, manipulate Excel, or supply Qingcheng semantics.
- Select `qingcheng-dashboard-sql` for explicit 青橙项目部 / Qingcheng metrics, dashboards, temporary tables, joins, ranges, Web BI profiles, governed SQL generation/repair, or Qingcheng knowledge maintenance. All Qingcheng contracts, profiles, indexes, and documentation stay inside that Skill; it must not borrow market semantics.
- Select `usql-web-query-operator` when the user asks to run/execute SQL, preview or download results, fetch stored Template Query SQL, perform a large-result template download, scan/profile dashboards, read edit-page metrics/formulas, plan/apply/publish governed Taitan changes, or read/sync/replace/create Data Center datasets. It executes approved workflows but does not generate business SQL or infer metric definitions.
- Select generic `playwright` only for non-USQL sites or bounded DOM/selector diagnosis after the operator has reproduced an SQL/BI UI problem. Generic Playwright must not own USQL login state or replace operator workflows.

### Files, Documents, and Feishu

- Select the spreadsheet Skill for `.xlsx`, `.xlsm`, `.csv`, or `.tsv` work, spreadsheet exports, formatting, formulas, recalculation, and tabular deliverables. It does not generate or execute SQL.
- Use native visual inspection for images/screenshots and the matching PDF/Office Skill for document files.
- For Feishu/Lark, use the most specific `lark-*` Skill. Use `lark-shared` first for CLI setup, login/status, user-vs-bot identity, missing scopes, or permission recovery; then hand off to the domain Skill.
- Route docs/wiki to `lark-doc`/`lark-wiki`, Drive files to `lark-drive`, sheets to `lark-sheets`, Base to `lark-base`, Miaoda/Spark apps to `lark-apps`, chat to `lark-im`, native Markdown to `lark-markdown`, real-time events to `lark-event`, reusable wrappers to `lark-skill-maker`, and uncovered native APIs to `lark-openapi-explorer`. Calendar, contacts, mail, slides, tasks, approvals, OKRs, minutes, VC, whiteboard, attendance, and workflow synthesis use their matching `lark-*` Skill.
- A recognizable Feishu/Lark URL or token routes to its domain Skill rather than generic web fetch. On permission or identity failure, return to `lark-shared`, repair the minimum required authorization, then retry the same domain Skill.

## Text2SQL Domain Resolution

Resolve the business domain before semantic retrieval or production SQL generation:

1. Explicit market-consultant language or a registered `market_consultant` artifact selects `sql-query-writer-for-dashboard`.
2. Explicit Qingcheng language or a registered `qingcheng` artifact selects `qingcheng-dashboard-sql`.
3. Ambiguous metrics, joins, ranges, dashboards, or business definitions remain `domain: unresolved`; never default them to market-consultant.
4. An unresolved request may inspect only neutral physical facts such as table names, fields, types, partitions, and candidate keys. It must not inherit a department metric, scope, range, temporary table, mapping, business join, dashboard definition, or raw SQL.
5. Cross-department comparison requires two independent QuerySpecs with separate evidence and validation. Combine results only after both sides are aggregated at an explicitly compatible grain.

A production QuerySpec must identify domain, intent, metrics, dimensions, filters, business scope, time range, calculation grain, output grain, candidate tables, join path, evidence, and unresolved slots. Required unresolved slots block execution. Only source-hash-bound `confirmed` contracts may enter an executable QueryPlan; `pending_confirmation`, ambiguity, conflicting scope, incompatible dimensions, grain mismatch, complex recipes, or unreviewed multi-table joins stay blocked or manual-review-only. Deterministic compilation additionally requires `automatic_compile=true`.

## Composite Workflows

In this section, **selected business SQL Skill** means the domain-resolved market or Qingcheng Skill. Artifacts and knowledge remain inside that domain.

### A. Data Query and Fetch

Selected business SQL Skill builds and validates QuerySpec/QueryPlan and SQL → `usql-web-query-operator` verifies executable status, unresolved slots, and exact SQL SHA-256 before browser launch, then executes and previews. Download only within the direct-download boundary; use Workflow L for explicitly required large results.

### B. Query and Excel Report

Selected business SQL Skill → operator execution/download → spreadsheet Skill for formatting, formulas, QA, and the finished workbook. If direct download would exceed its boundary, use Workflow L before spreadsheet work.

### C. SQL Fix and Re-run

The originally selected business Skill repairs SQL within the same QuerySpec and domain → operator re-executes it. Never repair a failure by switching departments.

### D. SQL Generation Only

Use only the selected business SQL Skill. Generate governed SQL and validation evidence without execution, download, browser launch, or Excel work.

### E. Dashboard Discovery and Read-only Profiling

Use only the operator for folder scans, dashboard ID lists, normalized profiles, and value checks. Read/profile requests never authorize save, create, update, delete, Apply, or Publish.

### E2. Edit-page Metric and Formula Profiling

Use only the operator to read pivot fields, metric meanings, custom formulas, and component identities from the dashboard edit page. This remains strictly read-only and must not save or publish transient edit-page state.

### E3. Legacy Public-filter Inspection

`edit-public-filters` is backward-compatible dry-run inspection only; legacy `--apply` or `--publish` flags must fail before browser launch. New or resumed mutation uses E4 with stable identities, exact ChangePlan hash, readback, and separate publication.

### E4. Governed Existing-dashboard Change

Operator profiles the complete draft and canonical hash → a ready domain-bound DatasetSpec/DesignSpec produces a ChangePlan → mandatory diff/dry-run rejects cross-domain inputs, stale hashes, ambiguous identities, cycles, collisions, rebinding, unsupported create/delete, and unverified adapters → explicitly authorized draft Apply consumes the reviewed hash, re-reads for drift, writes only allowlisted operations, reads back targets, and emits an ApplyReceipt → Publish is a separate command and confirmation. The dashboard must be registered by one current domain profile and absent from the other domain; otherwise it stays read-only. Draft readback is not proof of the online version.

### E5. Governed From-zero Dashboard Build

Operator validates DashboardBuildSpec and read-only BuildPlan with exact upstream, folder, dataset, schema, contract, and field-binding hashes. Required new datasets use Workflow O under their own plan and confirmation. Evidence capture is limited to an explicit sandbox/test target with visible confirmation. Production Apply requires an exact ready BuildPlan, explicit production-write confirmation, and verified/allowlisted creation adapters; it creates only a new unpublished dashboard. Failure never auto-deletes Saga resources and must report orphaned resources plus manual cleanup. Publish separately consumes a successful BuildReceipt and explicit version description.

### F. Spreadsheet-only Work

Use only the spreadsheet Skill for cleaning, analysis, formulas, formatting, recalculation, and spreadsheet delivery when no SQL or browser step is required.

### G. Query and Analyze Results

Selected business SQL Skill → operator execution/download (or Workflow L) → spreadsheet Skill for analysis, formulas, visualization, and validated delivery.

### H. Document and Image Reading

Inspect images/screenshots natively. Use the matching PDF or Office Skill for documents, then answer from inspected content without inferring unrelated write authorization.

### I. SQL/BI Debug Screenshot

Operator captures debug artifacts → inspect the visible screenshot/state → operator or the same selected business SQL Skill diagnoses and repairs within the resolved domain.

### J. USQL Selector Drift

Operator reproduces with headed/debug artifacts → inspect screenshots → generic Playwright performs only bounded DOM exploration if still needed → update the operator selector/fallback and rerun the operator verification.

### K. Stored Template SQL Fetch

Use only the operator's `fetch-template-sql` flow against Template Query → My templates → My created. Fetching stored SQL is not permission to execute or modify it.

### L. Large-result Template Download

Selected business SQL Skill finalizes a concrete, fully resolved SQL file → operator `template-download` creates/publishes/queries/downloads a temporary template and enforces cleanup `offline -> delete` → spreadsheet Skill if formatting is requested. A QueryPlan does not itself authorize template writes or downloads.

### M. Feishu Setup and Domain Handoff

`lark-shared` initializes or repairs config/auth/identity/scope → matching domain Skill performs the requested action → permission or identity failure returns to `lark-shared` for minimum-scope repair before retry.

### N. Data Center SQL Replacement and Refresh

Resolve domain and reviewed concrete SQL → operator `plan-data-center-sql-replacement` reads exact dataset identity, current/replacement SQL hashes, source, and schedule without remote writes → only explicit production authorization may call `apply-data-center-sql-replacement` with the exact reviewed plan hash and `--confirm-production-write` → full replace, preview success, save/readback SQL hash, `executeOnce`, and a new `SUCCESS` synchronization record are all required.

### O. Data Center Dataset Creation and First Extraction

Resolve domain and reviewed concrete SQL → operator `plan-data-center-dataset-creation` resolves one exact folder, unique name, SQL hash, data source, and schedule without writes → only explicit production authorization may call the matching Apply with exact plan hash and `--confirm-production-write` → create draft, set name/source/full SQL, preview, configure schedule, save/read back unique `menu_set_*` identity/SQL/schedule, run `executeOnce`, and wait for a new `SUCCESS`. Save alone is incomplete.

## Cross-Skill Execution and Production Boundaries

### Core Contracts and Knowledge Isolation

- When a QueryPlan is supplied to the operator, reject it before browser launch unless `status=executable`, `unresolved_slots=[]`, and the submitted SQL SHA-256 matches exactly. QueryPlan execution policy must separately allow any requested download.
- QueryPlan, DashboardDatasetSpec, DashboardDesignSpec, DashboardChangePlan, DashboardBuildSpec/Plan, Data Center plans, profiles, and receipts are descriptive/review artifacts. None authorizes execution, download, knowledge writeback, remote mutation, or publication by itself.
- Market metrics, dashboards, temporary tables, mappings, joins, raw SQL, profiles, contracts, and indexes stay under `sql-query-writer-for-dashboard`; Qingcheng equivalents stay under `qingcheng-dashboard-sql`. Never copy semantics across domains.
- The shared physical catalog contains neutral physical schema facts only, never department metrics, ranges, mappings, business joins, dashboard semantics, or raw SQL definitions.
- Business-Skill knowledge is read-only unless the user explicitly requests that domain's knowledge maintenance. Runtime artifacts do not become durable knowledge automatically.

### SQL Knowledge Maintenance

- After changing dashboards, metrics, tables, temporary tables, joins, raw SQL, or semantic contracts, run the selected Skill's `scripts/build_reverse_indexes.py`, repository `scripts/build_text2sql_catalog.py`, the selected Skill's `scripts/check_skill_integrity.py`, then repository `scripts/validate_text2sql_stack.py`.
- Refresh market physical schema only through operator `sync-datamap-fields`; Data Map owns neutral fields/types/partitions/DDL, while market semantics stay in domain contracts. Do not recreate raw PDF/image extraction or hand-maintained physical catalogs.
- Canonical Data Center SQL uses only `resources/raw_sql/data_center_market_<model_id>.sql` or `resources/raw_sql/data_center_qingcheng_<model_id>.sql`. Local sync must use operator `sync-data-center-sql`, review dry-run hash, bind each domain's `semantic/current_model_bindings.json`, hold the exclusive lock, run all catalog/integrity gates, and restore the pre-write snapshot if a local knowledge gate fails. Local `--write` never means remote production write.

### SQL Download and Template Safety

- Direct `SQL取数` download requires `limit <= 1000` or reliable result-page proof that rows do not exceed 1000, plus any QueryPlan download policy. For an explicitly required larger concrete result, use Workflow L and mandatory temporary-template cleanup; never silently switch paths.
- Failed or malformed downloads must be reported as failures. Never expose credentials or create Template Query assets without the workflow's explicit user authorization.

### Existing-dashboard Governance (P3/P4A/P4B)

- All changes follow `profile -> design -> diff/dry-run -> explicitly authorized draft Apply -> separately confirmed Publish`, with exact hashes, full-profile drift checks, per-target readback, and final-state verification.
- Production P4B is limited to Registry `verified/allowlisted` operations: one existing stable field display-name slot; one existing component-local filter label bound by stable unit/field identity; one existing component title; one public-filter title bound by stable relation/filter/field identity; one existing Tab label; existing-node `x/y/w/h` within the same container after bounds/collision checks; one dependency-stable non-shared component formula expression; one stable public-filter dynamic default; and dashboard-root `#RRGGBB` background color. Dataset rebinding, create/delete, unsupported style expansion, permissions, folder moves, and unverified operations remain blocked.
- On Apply failure, stop and reverse completed operations where the verified adapter supports it; require the full baseline Profile hash to return. Unprovable recovery remains failed and needs manual inspection. Publication is blocked after failed recovery.
- Inspect `references/dashboard_write_capabilities.json` before mutation. Evidence capture and sandbox verification require an exact sandbox, visible confirmation, redacted immutable evidence, and full reversibility tests; sandbox evidence never auto-promotes a production allowlist.
- Without a formal published-version read API, publication receipts must say `publish_requested_unverified` and `fully_verified=false`; matching draft state is not online proof.

### From-zero Dashboard Governance (P4C)

- Keep creation separate from DashboardChangePlan. Use `DashboardBuildSpec -> DashboardBuildPlan -> DashboardBuildReceipt -> DashboardBuildPublishReceipt` with exact upstream and schema hashes, unique pre-existing folder/name resolution, and `creation_saga_no_auto_delete` semantics.
- The thirteen creation categories are dashboard shell, subject formula, card, pivot, bar, pie, public filter, dashboardHtml assembly, all-new-metric display names, evidence-backed component style, two-slot Tab creation, Tab slot assembly, and restricted rich text. Apply requires every needed category to be Registry `verified/allowlisted`, with production adapter, full readback, failure/idempotency tests, exact BuildPlan hash, and explicit confirmation.
- Multiple local/global filters are allowed only inside their verified creation operations; aliases are all-or-none; nested slot pivots cannot add local filters; arbitrary HTML/CSS, raw style, arbitrary tab nesting, cloning fallback, automatic folder creation/move, and pre-created-empty-dashboard fallback remain blocked.
- Never auto-delete or claim rollback of Saga resources. Failure receipts list created/reused/orphaned resources and `manual_cleanup_required`; resume only exact logical matches. Apply never publishes; Publish separately consumes a successful receipt and explicit non-empty version description.

### Data Center Remote Governance

- Replacement and creation plans are remote read-only and do not authorize each other. Apply requires exact domain/folder/dataset identity, reviewed plan hash, explicit `--confirm-production-write`, immediate drift re-read, and the matching per-resource lock.
- Replacement must full-replace editor content, preview, save, read back SQL hash, trigger execution, and observe a new `SUCCESS`. Creation must require `id=null` on the save request, planned parent/source/SQL, unique readback identity, schedule no more than 90 days, execution, and a new `SUCCESS`.
- If save succeeds but readback/refresh fails, emit a failed receipt, require manual attention, do not silently roll back/delete, and never claim completion.

### Tool, Feishu, Spreadsheet, and Credential Boundaries

- Generic Playwright must not execute SQL取数, read/write Data Center, scan/profile authenticated BI, manage USQL login state, or download authenticated SQL results; route those operations through the operator.
- Keep Feishu Skills under `C:\Users\Ludim\.codex\skills\lark-*` with `agents/openai.yaml`. Preserve registration metadata during upstream sync and restart Codex when discovery metadata changes.
- Spreadsheet calculations must use spreadsheet formulas rather than Python-hardcoded calculated values, followed by platform recalculation and formula-error verification.
- USQL browser state belongs only to the operator at `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`. Configure credentials through `USQL_ENV_FILE` or `--env-file`; never print or hardcode `BAIJIA_USERNAME` or `BAIJIA_PASSWORD`.

## Execution and Verification Rules

1. Auto-detect and load Skills in workflow order; do not require the user to name them.
2. Briefly report stage transitions for multi-Skill work.
3. On SQL failure, return to the same domain Skill and original QuerySpec. On expired login, request manual login without exposing credentials.
4. Apply the global UTF-8 policy to every command, generated artifact, API/debug payload, and validation step involving non-ASCII text.
5. Close maintenance with applicable Skill tests, routing/contract checks, UTF-8 and mojibake checks, `git diff --check`, reviewed `git status`, and the repository validator.
