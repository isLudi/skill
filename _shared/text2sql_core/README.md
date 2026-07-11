# Text2SQL shared core

This directory is a non-discoverable implementation package shared by the two
business SQL skills. It is not a skill and intentionally has no `SKILL.md`.

The boundary is strict:

- `catalog/physical_catalog.json` contains only physical table identifiers,
  columns, partition candidates, provenance, and explicit conflicts.
- Business metrics, dashboard semantics, range values, temporary tables,
  business joins, channel/period rules, and raw SQL remain in each domain skill.
- `semantic/contracts/*.json` is a domain-local, source-hash-bound overlay. Only
  `confirmed` entries may enter an executable plan; Markdown and raw SQL remain
  authoritative.
- `QuerySpec` must resolve a domain before executable SQL is produced.
- `QueryPlan` records selected contracts, scope filters, grain, evidence,
  lineage, unresolved slots, execution policy, and the exact compiled SQL hash.
- Markdown and raw SQL remain the authoritative evidence. Generated manifests
  are deterministic routing indexes, not replacement knowledge bases.

Build or verify the generated catalog from the skills repository root:

```powershell
D:\anaconda3\python.exe scripts/build_text2sql_catalog.py
D:\anaconda3\python.exe scripts/build_text2sql_catalog.py --check
```

Each business skill exposes the same fixed-domain CLI:

```powershell
D:\anaconda3\python.exe scripts/text2sql.py summary
D:\anaconda3\python.exe scripts/text2sql.py search --query '<business term>'
D:\anaconda3\python.exe scripts/text2sql.py resolve --query '<metric or dimension>'
D:\anaconda3\python.exe scripts/text2sql.py init-spec --intent metric_query
D:\anaconda3\python.exe scripts/text2sql.py validate-spec --spec '<query-spec.json>'
D:\anaconda3\python.exe scripts/text2sql.py plan --spec '<query-spec.json>' --output '<query-plan.json>'
D:\anaconda3\python.exe scripts/text2sql.py compile --spec '<query-spec.json>' --sql-output '<query.sql>' --plan-output '<query-plan.json>'
D:\anaconda3\python.exe scripts/text2sql.py probe --kind freshness --table '<schema.table>' --start-value '<YYYYMMDD>' --end-value '<YYYYMMDD>'
D:\anaconda3\python.exe scripts/text2sql.py dataset-spec --plan '<query-plan.json>' --output '<dataset-spec.json>'
D:\anaconda3\python.exe scripts/text2sql.py evaluate
D:\anaconda3\python.exe scripts/text2sql.py validate-sql --spec '<query-spec.json>' --sql-file '<query.sql>'
```

The P2 pipeline is domain resolution, generated contract-index lookup, targeted
source reading, QuerySpec validation, QueryPlan construction, conservative
single-table compilation, AST/platform validation, then optional execution.
Ambiguous aliases, pending contracts, metrics without explicit
`automatic_compile` approval, unresolved scope values, grain mismatch, or an
unreviewed join produce a blocked or `requires_manual_sql` plan instead of
guessed SQL. Bounded probes are read-only diagnostics. Dashboard dataset
specs are read-only designs and cannot authorize edits or publication.

## P3 dashboard design and controlled change artifacts

P3 adds a pure-local change-control layer in `text2sql_core.dashboard_change`.
It does not add browser access or widen the P2 SQL and dataset boundaries:

1. `normalize_dashboard_profile` creates a read-only `DashboardProfile` from
   stable node, relation, filter, and field identities. Its hash also binds a
   normalized completeness record; incomplete profiles remain useful for
   inspection but cannot enter design or apply.
2. `build_dashboard_design_spec` binds desired state to the exact profile,
   QueryPlan, and DashboardDatasetSpec hashes. The DatasetSpec must be ready,
   self-hashed, QueryPlan-bound, and carry confirmed domain-local source
   evidence for every referenced business contract. Contract evidence is not
   trusted from the DatasetSpec alone: design resolves the domain to its own
   business Skill, reloads the live contract registry, requires an exact
   `status + source_path + source_sha256` match, and rereads the registered
   source file to recompute SHA-256. Missing, stale, forged, or cross-domain
   evidence blocks the DesignSpec.
   The same gate resolves `dashboard_id` through both domain-local
   `dashboard_registry` sections. An unregistered, stale, duplicated, or
   cross-domain dashboard remains profile-only until its governed web profile
   is synchronized into the correct business Skill and the catalog is rebuilt.
3. `diff_dashboard` emits a `DashboardChangePlan` with before/after values,
   risk, support status, and block reasons. The plan is always dry-run-only and
   never grants apply or publish authority.
4. `build_apply_receipt` and `validate_apply_receipt` require post-write
   profile readback to match the complete target state.
5. Publication remains a separate confirmation and receipt. A no-op apply
   receipt cannot be used as a publication credential. When only draft
   readback is available, the receipt records `publish_requested_unverified`
   and `fully_verified=false`; it explicitly does not claim that a formal
   published-version read API exists.

P3A can profile and diff components, layouts, formulas, public filters, and
dataset bindings. Current P3B write support is intentionally narrower: only an
existing public-filter dynamic default addressed by the stable
`relation_id + filter_id + field_id` triple can be marked `supported`.
Component, layout, formula, generic filter, create, delete, container move,
and dataset-rebind operations remain visible in the diff but are
`blocked_unsupported`; one blocked operation blocks the entire apply.

Artifact hashes use canonical UTF-8 JSON. Call `artifact_sha256(value,
"<self_hash_field>")`; it omits only the artifact's own hash field so upstream
profile, design, plan, QueryPlan, and DatasetSpec bindings remain covered.
Schemas are under `schemas/dashboard_*.schema.json`. Existing QuerySpec,
QueryPlan, and DashboardDatasetSpec schema version `2.0.0` remains supported;
new P3 artifacts use `3.0.0`.

For optional web execution, pass the exact compiled SQL and its plan to
`usql-web-query-operator run --query-plan`. The operator validates the plan
status, unresolved slots, SQL SHA-256, and download policy before opening the
browser; its existing 1000-row gate and dashboard dry-run boundaries remain in
force.
