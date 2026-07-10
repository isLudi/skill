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

For optional web execution, pass the exact compiled SQL and its plan to
`usql-web-query-operator run --query-plan`. The operator validates the plan
status, unresolved slots, SQL SHA-256, and download policy before opening the
browser; its existing 1000-row gate and dashboard dry-run boundaries remain in
force.
