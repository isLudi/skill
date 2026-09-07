# Codex Workspace and Skills Repository Instructions

This file is the Git-versioned instruction source for `C:\Users\Ludim\.codex`. Maintain `skills\AGENTS.md`; `WORKSPACE_AGENTS.md` is its generated runtime mirror. Relative links below resolve from the `skills` repository, including when this text is loaded through the mirror.

## Scope and authorization

- The user's explicit instructions and authorization take precedence over Skill workflow suggestions. A Skill cannot expand the requested scope or grant a new permission. Machine-enforced identity, Hash, capability and safety gates remain required; report an unavailable operation rather than bypassing its adapter.
- Inspect, explain, diagnose, review, profile and plan requests are read-only. They do not authorize knowledge maintenance, remote writes, publication, Git commits/pushes or external messages.
- Keep planning, draft Apply, production Apply and Publish as distinct authorization phases. A Plan, profile, receipt or successful earlier phase is evidence, never authorization for the next. Honor an existing explicit authorization for the same target, reviewed change and phase; do not ask again merely because a command needs a confirmation flag. Scope changes, drift or uncertain writes require a new decision.
- Complete authorized local work through implementation, relevant verification and repair of failures caused by the change. Make routine implementation choices autonomously. Ask only when an unresolved choice materially changes the result or a required authorization is absent; prepare the concrete reviewable change first. Explain the exact Skill instruction if it causes a pause.
- Preserve unrelated files, cells and user changes. Do not commit, push, send external messages or perform destructive operations without explicit authorization. Do not stop/restart production services as a side effect of documentation or local validation work.
- Never expose passwords, access/refresh tokens, device codes, browser state or secret-bearing files. User-facing verification links and QR codes from an authorized login flow may be shown to that user; credential/session-bearing URLs must not be shown or logged.

## Runtime and text transport

Use `D:\anaconda3\python.exe` and its `-m pip` for Python; do not substitute bare Python or Python 3.14 unless requested. Text is UTF-8, preferably without BOM. Initialize each new PowerShell process before non-ASCII input/output:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
```

Create non-ASCII payloads with `apply_patch` or Python using explicit UTF-8, not PowerShell pipelines, here-strings, interpolation or redirection. Read text with explicit UTF-8. Python that prints non-ASCII must configure stdout/stderr for UTF-8. Encode JSON/API bytes explicitly; prefer `ensure_ascii=True` for unproven gateways. Reopen important writes and check for corruption. Treat mojibake, empty non-ASCII replies and malformed JSON as transport failures before drawing business conclusions.

## Instruction layout

- `skills\AGENTS.md` is the only editable AGENTS source. Keep `.codex\AGENTS.md`, `.codex\AGENTS.override.md`, `.codex\.git` and `skills\AGENTS.global.md` absent.
- `config.toml` uses `project_doc_fallback_filenames = ["WORKSPACE_AGENTS.md"]` and a size limit sufficient for this file but no greater than `32768` bytes.
- After editing the source, run [sync_agents.ps1](sync_agents.ps1) with `-Mode Export -NoCommit`. Export verifies the mirror and layout. Use `-Mode Check` for a separate read-only check when needed; an unchanged successful Export needs no second check. Import additionally requires `-ConfirmImport` and a reviewed mirror. Git commit/push are opt-in (`-Commit`, then optional `-Push`), never part of ordinary synchronization.
- Keep the canonical Lark Skills and their `agents/openai.yaml` under this repository. Use per-path Codex discovery settings to disable duplicate installations without deleting other tools' copies. Preserve registration metadata during upstream sync; restart Codex after discovery changes. Review local instruction adaptations when updating upstream files.

## Skill routing and reading

Select the smallest sufficient Skill set. Read the selected `SKILL.md` completely, then only the reference for the current operation. Reuse already-read unchanged guidance within the task. Search further when evidence is missing, stale or conflicting; stop expanding context once the task is supported. Announce meaningful Skill transitions. Workflow handoffs do not require subagents or new Codex tasks.

| Request / artifact | Entry point |
|---|---|
| 市场顾问部 semantics, SQL, contracts, dashboard design; registered 馒头_订单明细_支付时间 / 馒头_订单明细_流水时间 | [market-consultant-dashboard-sql](market-consultant-dashboard-sql/SKILL.md) |
| 青橙项目部 semantics, SQL, contracts and dashboard design | [qingcheng-dashboard-sql](qingcheng-dashboard-sql/SKILL.md) |
| USQL execution/download/templates, Data Center, BI profiles/changes, Tiangong2 tasks/logs | [usql-web-query-operator](usql-web-query-operator/SKILL.md) |
| Registered workbooks from 青橙数据对接 / 市场顾问部临时表上传 | [sync-qingcheng-market-temp-tables](sync-qingcheng-market-temp-tables/SKILL.md); this owns source identity, transformations and upload routing |
| Local `.xlsx`, `.xlsm`, `.csv`, `.tsv` input/output | [xlsx](xlsx/SKILL.md); preserve registered upload-file contracts |
| Explicit query-result delivery as 飞书电子表格 / `lark_sheet` | [query-result-to-lark-sheet](query-result-to-lark-sheet/SKILL.md), then its Lark Skills |
| Feishu setup, login, identity, scopes or permission repair | [lark-shared](lark-shared/SKILL.md), then the relevant domain Skill |
| Feishu docs/wiki, Drive, Sheets, Base, Miaoda apps, chat | [lark-doc](lark-doc/SKILL.md) / [lark-wiki](lark-wiki/SKILL.md), [lark-drive](lark-drive/SKILL.md), [lark-sheets](lark-sheets/SKILL.md), [lark-base](lark-base/SKILL.md), [lark-apps](lark-apps/SKILL.md), [lark-im](lark-im/SKILL.md) |
| Feishu Markdown, events, contacts, reusable wrappers, uncovered native APIs | [lark-markdown](lark-markdown/SKILL.md), [lark-event](lark-event/SKILL.md), [lark-contact](lark-contact/SKILL.md), [lark-skill-maker](lark-skill-maker/SKILL.md), [lark-openapi-explorer](lark-openapi-explorer/SKILL.md) |
| Feishu calendar/mail/slides/tasks/approval/OKR/whiteboard/attendance | Matching `lark-*` Skill; meetings/minutes/VC use [lark-meeting](lark-meeting/SKILL.md), summaries use [lark-workflow-meeting-summary](lark-workflow-meeting-summary/SKILL.md), agenda/task summaries use [lark-workflow-standup-report](lark-workflow-standup-report/SKILL.md) |
| Images, PDF, Word, PowerPoint | Inspect images natively; use [pdf](pdf/SKILL.md), [docx](docx/SKILL.md), [pptx](pptx/SKILL.md) for the matching file |
| Non-USQL browser work or bounded selector diagnosis after operator reproduction | [playwright](playwright/SKILL.md), subject to the available browser tool's controls |

Recognizable Feishu URLs/tokens route to their resource Skill. Permission failures return to `lark-shared` for the minimum needed repair. Generic browser automation must not own USQL credentials/state or replace its governed execution, download, Data Center or BI workflows.

## Business contracts

Resolve domain before semantic retrieval: explicit department or registered artifact chooses its Skill; otherwise retain `domain: unresolved` and inspect neutral physical facts only. Never fill one domain's semantic gaps with the other's definitions. Cross-department comparison uses two independent QuerySpecs and compares only compatible aggregated grains.

Production QuerySpec records domain, intent, metrics, dimensions, filters, business scope, time, calculation/output grain, tables, joins, evidence and unresolved slots. Only source-Hash-bound `confirmed` contracts may enter an executable plan. Required unresolved slots, ambiguous scope, incompatible grains or unreviewed joins block execution. Deterministic compilation also requires `automatic_compile=true` and compiler-supported structure. The operator checks `status=executable`, `unresolved_slots=[]` and the exact SQL SHA-256 before browser launch.

Keep market and Qingcheng semantics, raw SQL, profiles and indexes in their respective Skills. Shared physical catalogs hold neutral schema facts only. Runtime results are not durable knowledge. Knowledge writes require an explicit maintenance request and the governed adapter; domain routing comes only from [domain_adapters.json](usql-web-query-operator/references/domain_adapters.json).

## Workflow map

“Domain Skill” below means the resolved business Skill. Read the linked operation reference only for that workflow. Technical stages remain separate even when an existing authorization covers them.

| ID | Trigger and sequence | Operation reference / completion boundary |
|---|---|---|
| A | Query/fetch: Domain Skill → operator | [SQL execution](usql-web-query-operator/references/sql_query_execution.md); verified Query ID/result; download separately permitted |
| B | Query/report: A → `xlsx` or explicit `lark_sheet` delivery | [Sheet delivery](query-result-to-lark-sheet/SKILL.md); verified deliverable in requested format |
| C | SQL failure: original Domain Skill repair → operator | [SQL execution](usql-web-query-operator/references/sql_query_execution.md); preserve domain and QuerySpec |
| D | SQL generation only: Domain Skill | [QueryPlan contract](usql-web-query-operator/references/query_plan_contract.md); SQL/evidence, no execution or download |
| E | Dashboard discovery/profile: operator | [Profiles](usql-web-query-operator/references/platform_profile.md); read-only |
| E2 | Edit-page fields/formulas: operator | [Profiles](usql-web-query-operator/references/platform_profile.md); never save transient edit state |
| E3 | Legacy `edit-public-filters`: inspection only | [Dashboard change](usql-web-query-operator/references/dashboard_change_workflow.md); mutation uses E4 |
| E4 | Existing dashboard: profile → design → diff → draft Apply → Publish | [Dashboard change](usql-web-query-operator/references/dashboard_change_workflow.md); exact Hash/identity, allowlist and readback; separate publish authorization |
| E5 | New dashboard: BuildSpec → Plan → unpublished Apply → Publish | [Dashboard build](usql-web-query-operator/references/dashboard_build_workflow.md); required datasets use O; report orphan resources, no automatic deletion |
| F | Spreadsheet-only work: `xlsx` | [xlsx](xlsx/SKILL.md); no SQL/browser step inferred |
| G | Query/analysis: A or L → requested delivery mode | [Sheet delivery](query-result-to-lark-sheet/SKILL.md); local Excel and Feishu are distinct outputs |
| H | Document/image reading: matching file Skill or native image inspection | [pdf](pdf/SKILL.md), [docx](docx/SKILL.md), [pptx](pptx/SKILL.md); answer from inspected content |
| I | SQL/BI screenshot: operator capture → inspect → scoped diagnosis | [Profiles](usql-web-query-operator/references/platform_profile.md); repair requires the relevant authorization |
| J | Selector drift: operator reproduction → bounded DOM diagnosis → operator fix | [playwright](playwright/SKILL.md); generic tooling never takes ownership of USQL state |
| K | Fetch stored template SQL: operator | [Templates](usql-web-query-operator/references/template_query.md); fetching does not authorize execution/modification |
| L | Explicit large result: finalized SQL → temporary template query/download → cleanup | [Templates](usql-web-query-operator/references/template_query.md); required `offline -> delete`, cleanup failure is failure |
| M | Feishu setup/repair → domain Skill | [lark-shared](lark-shared/SKILL.md); minimum required identity/scope |
| N | Existing Data Center SQL replacement: Plan → authorized Apply/refresh | [Replacement](usql-web-query-operator/references/data_center_replacement.md); preview, save/readback and a new SUCCESS |
| O | New Data Center dataset: Plan → authorized creation/first extraction | [Creation](usql-web-query-operator/references/data_center_creation.md); unique identity, SQL/schedule readback and a new SUCCESS |
| P | Registered temp tables: plan → apply-local → upload | [Temp-table sync](sync-qingcheng-market-temp-tables/SKILL.md); separate local/upload authorization, quality gates, backup and per-target receipts |
| Q | Permanent template: Plan → unpublished create/update → Publish | [Templates](usql-web-query-operator/references/template_query.md); exact SQL/parser/metadata Hash, separate publish authorization and readback |
| R | Tiangong2 exploration: isolated identity → exact project/folder read | [Exploration](usql-web-query-operator/references/tiangong2_task_exploration.md); read-only allowlist and redacted runtime artifacts |
| S | Tiangong2 owned-task maintenance: read → scoped repair → submit → publish → execute | [Task operations](usql-web-query-operator/references/tiangong2_task_operations.md), [acceptance](usql-web-query-operator/references/tiangong2_python_task_diagnostics_acceptance.md); P/M authorization, one call per phase, no exec reruns/downstream triggers |

## Production and delivery invariants

- Direct SQL download requires `limit <= 1000` or reliable proof of at most 1000 rows, plus QueryPlan download permission. Larger concrete results use explicitly authorized L with cleanup.
- Dashboard mutation requires one registered domain, stable identities, current baseline Hash, verified/allowlisted adapters and per-target readback. Read [dashboard_write_capabilities.json](usql-web-query-operator/references/dashboard_write_capabilities.json) for actual supported operations. No automatic promotion of sandbox evidence. Draft readback is not online proof; without a published-version read API report `publish_requested_unverified`, `fully_verified=false`.
- Existing-dashboard recovery must use verified restoration and prove the baseline; failed recovery blocks publication. New-resource Sagas do not auto-delete; failures identify created/orphaned resources and manual cleanup. Data Center save without successful readback/refresh is incomplete and must not silently roll back or delete.
- Tiangong2 binds exact task, owner, folder, execution and stage using isolated credentials/state. P authorizes one reviewed phase; M authorizes one task for a fixed time/budget and suppresses repeated questions only. Each phase still needs a fresh Plan Hash, drift check, one write and readback. Expired/exhausted sessions and uncertain writes stop. Cross-owner work, credential/default/resource/schedule changes, downstream triggers, exec reruns and arbitrary full-source replacement remain forbidden.
- Temp-table source identity, freshness, row-count/change/null/duplicate/schema checks and per-domain shared-workbook slices remain mandatory under [workflow_registry.json](sync-qingcheng-market-temp-tables/references/workflow_registry.json). An old Plan cannot bypass source expiry. Candidate/local success is not platform delivery.
- SQL-to-Feishu delivery defaults to one new root-level Sheet in approved `openclaw`, with `市场顾问部_` or `青橙项目部_` title prefixes and underscore-separated segments. Preserve native pivots when requested and verify complete written ranges. Other targets need the requested scope.
- Dynamic spreadsheet deliverables use formulas for derived values, platform recalculation and error verification over the affected dependency scope. Static exports, CSV, analysis intermediates and registered upload files follow their output contracts; do not force formulas into them. Preserve unrelated cells and report pre-existing errors rather than silently expanding the task.

## Maintenance and verification

Use [maintenance verification](references/maintenance-verification.md) to choose checks by changed behavior. Documentation-only work needs relevant links/routing/encoding checks; code changes need affected tests; shared contracts, authorization or cross-domain workflows need the complete stack. A successful superset covers its subsets for the same unchanged revision. Rerun or broaden only after new changes, failures or unresolved concerns.

Knowledge maintenance uses each domain's own maintenance reference and operator synchronization paths. Regenerate changed indexes/catalogs before checking them; never treat validation as permission to refresh remote data. Preserve source Hash gates, exclusive locks and rollback of failed local knowledge updates. Finish with an honest summary of the requested result, verification and remaining limitations, plus scoped `git diff --check` and status. Do not perform production runs to validate an instruction edit.
