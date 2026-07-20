# Codex Workspace and Skills Repository Instructions

This file is the single versioned instruction source for `C:\Users\Ludim\.codex`. Codex loads it directly when the working directory is the `skills` Git repository and loads its byte-for-byte runtime mirror when the working directory is `C:\Users\Ludim\.codex`.

The Runtime, UTF-8, Authorization, and Instruction Layout sections apply throughout the `.codex` workspace. The remaining repository sections apply when work selects, reads, or changes assets under `C:\Users\Ludim\.codex\skills`. Detailed procedures remain in each selected Skill's complete `SKILL.md` and its required references.

## Runtime

- Use `D:\anaconda3\python.exe` for Python and `D:\anaconda3\python.exe -m pip ...` for package work.
- Do not use bare `python` or `C:\Python314\python.exe` unless the task explicitly targets Python 3.14.

## UTF-8

- Create and edit text as UTF-8, preferably without BOM when the consumer does not require one.
- Before PowerShell reads, prints, pipes, or transmits non-ASCII text, set `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1`, UTF-8 console input/output encodings, and `$OutputEncoding`.
- Do not generate or rewrite non-ASCII text through PowerShell text pipelines, here-strings, interpolation, `Set-Content`, `Add-Content`, `Out-File`, `>`, or `>>`. Use `apply_patch` or `D:\anaconda3\python.exe` with explicit `encoding="utf-8"`. Byte-for-byte file copying is allowed.
- Read important text with an explicit UTF-8 encoding and check for mojibake before relying on its meaning.

## Authorization and Safety

- A request to inspect, explain, diagnose, review, or plan is read-only. Do not infer permission for local knowledge maintenance, production writes, publication, Git commits, pushes, or external messages.
- Keep plan/dry-run, draft Apply, production Apply, and Publish as separate authorization boundaries. A plan, spec, hash, profile, or receipt does not itself grant the next permission.
- Preserve unrelated user changes. Do not use destructive Git or filesystem commands unless the user explicitly requests the exact operation.
- Never print, hardcode, copy, or expose credentials, tokens, browser storage state, or secret-bearing environment files.
- When a decision is genuinely required and bounded choices exist, offer concise structured options instead of requesting a free-form description.

## Instruction Layout and Git Versioning

- `C:\Users\Ludim\.codex\skills\AGENTS.md` is the only Git-versioned source for these workspace instructions.
- `C:\Users\Ludim\.codex\WORKSPACE_AGENTS.md` is a generated runtime mirror. Do not edit both files independently or commit the runtime mirror.
- `C:\Users\Ludim\.codex\AGENTS.md`, `C:\Users\Ludim\.codex\AGENTS.override.md`, and `C:\Users\Ludim\.codex\skills\AGENTS.global.md` must remain absent. Reintroducing any of them can restore duplicate or competing instruction discovery.
- `C:\Users\Ludim\.codex\config.toml` must keep `project_doc_fallback_filenames = ["WORKSPACE_AGENTS.md"]`. This makes the mirror a project fallback at `.codex`; it is not a global `AGENTS.md` input.
- Run `sync_agents.ps1 -Mode Export -NoCommit` after editing the canonical file, then run `sync_agents.ps1 -Mode Check`. Use `-Mode Import -ConfirmImport -NoCommit` only to deliberately replace the canonical file with a manually edited runtime mirror.
- Omitting `-NoCommit` authorizes the sync script to commit only `AGENTS.md`; adding `-Push` also pushes the current branch. Do not commit or push unless the user explicitly requested that boundary.
- Before a requested commit or push, inspect `git status`, synchronize the mirror, run the layout and repository validators, review the diff, and report the exact commit/push result.

## Skill Routing

- Resolve the business domain before semantic retrieval or SQL generation: `market_consultant`, `qingcheng`, or `unresolved`.
- Use `sql-query-writer-for-dashboard` only for market-consultant semantics and governed SQL planning/generation. It does not execute SQL or supply Qingcheng definitions.
- Use `qingcheng-dashboard-sql` only for Qingcheng semantics and governed SQL planning/generation. It must not borrow market-consultant definitions.
- Use `usql-web-query-operator` for authenticated SQL execution/download, Template Query, Data Center operations, and Taitan dashboard reading or governed mutation. It does not generate business SQL or infer metric semantics.
- Use generic `playwright` only outside the company SQL/BI workflow or for bounded selector diagnosis after the operator reproduces a UI problem.
- Use the most specific `lark-*` Skill for Feishu work and keep installed Feishu Skills under this repository. Use the spreadsheet Skill when the deliverable is a spreadsheet.

## Text2SQL and Domain Isolation

- An unresolved domain may inspect only neutral physical facts. It must not inherit a department metric, scope, range, temporary table, mapping, business join, dashboard definition, or raw SQL.
- Production SQL requires a QuerySpec with domain, intent, metrics, dimensions, filters, business scope, time range, calculation grain, output grain, candidate tables, join path, evidence, and no unresolved required slots.
- Only source-hash-bound `confirmed` contracts may enter an executable QueryPlan; deterministic compilation additionally requires explicit automatic-compile approval. Pending, ambiguous, conflicting, grain-incompatible, or unreviewed multi-table work remains blocked or manual-review-only.
- Cross-department comparison uses two independent QuerySpecs and combines only validated results at an explicitly compatible aggregation grain.
- Market artifacts stay under `sql-query-writer-for-dashboard`; Qingcheng artifacts stay under `qingcheng-dashboard-sql`. The shared physical catalog contains neutral schema facts only.

## Execution and Production Boundaries

- When a QueryPlan is supplied for execution, the operator must reject it before browser launch unless it is executable, has no unresolved slots, and its SQL SHA-256 matches the submitted SQL exactly.
- QueryPlan and dashboard/Data Center specs, plans, hashes, profiles, and receipts are review artifacts; none authorizes execution, download, remote mutation, knowledge writeback, or publication by itself.
- Dashboard operations are read-only by default. Existing-dashboard Apply, from-zero dashboard build, and Publish must follow the exact plan/hash, explicit confirmation, drift checks, capability Registry, readback, and separate publication rules in `usql-web-query-operator`.
- Data Center sync and plan commands are remote read-only. Only the matching Apply command may perform replacement or creation, and only with the exact reviewed plan hash plus explicit production-write confirmation. Creation and replacement never authorize each other.
- Business-Skill knowledge maintenance requires an explicit user request and the Skill-specific confirmation flags. Runtime artifacts do not become durable knowledge automatically.
- Generic Playwright must not own or modify the USQL browser state. Never expose `BAIJIA_USERNAME`, `BAIJIA_PASSWORD`, `USQL_ENV_FILE`, or the browser storage state.

## Maintenance and Verification

- After changing dashboards, metrics, tables, temporary tables, joins, raw SQL, or semantic contracts, run the selected business Skill's `scripts/build_reverse_indexes.py`, repository `scripts/build_text2sql_catalog.py`, the selected Skill's `scripts/check_skill_integrity.py`, and repository `scripts/validate_text2sql_stack.py`.
- Refresh market physical schema only through the operator's governed Data Map sync. Keep domain semantics in their business Skill.
- Keep `agents/openai.yaml` for every installed custom Skill so discovery metadata remains versioned; restart Codex when registration changes require it.
- Close maintenance with applicable tests, UTF-8/mojibake checks, `git diff --check`, and a reviewed `git status`.
