---
name: sync-qingcheng-temp-tables
description: Synchronize the latest Excel files posted by 郅玲玉 in the Feishu group 青橙数据对接 into the Qingcheng and shared architecture maintenance workbooks, then upload the complete verified workbooks to their existing USQL temporary tables. Use for requests such as “上传郅玲玉在青橙数据对接内发布的最新临时表到线上平台”, for dry-run comparisons of those files, or for explaining and auditing this workflow.
---

# Sync Qingcheng Temp Tables

## Purpose

Turn one natural-language request into a governed Feishu-to-local-to-USQL workflow for five incoming workbook families:

- 个人期度目标表
- 团队期度目标表
- 团队月度目标表
- 全员结果数据架构
- `****期带班架构`

The workflow downloads the newest matching attachment from 郅玲玉, compares effective cell values with the local cumulative workbook, performs a slice replacement or append in a staged copy, validates the result, writes the reviewed local copy only after confirmation, and uploads the complete local workbook only after a separate production confirmation.

## Required Skill Order

Before acting, read and follow these skills completely:

1. `lark-shared`, then `lark-im`, including the message-search and resource-download references needed for attachment discovery.
2. `xlsx` for workbook inspection, formula-cache handling, recalculation, and QA.
3. `usql-web-query-operator` for manual-table validation and production upload.

For historical mapping or workflow maintenance, also read [historical_file_mapping.md](references/historical_file_mapping.md) and [workflow_registry.json](references/workflow_registry.json).

Do not use the Qingcheng or market SQL-generation skills to reinterpret these workbook schemas. The destination workbooks span both domains, but this workflow only performs the explicit file mappings in the registry.

## Authorization Boundaries

Treat the stages as separate authorization boundaries:

1. `plan` is read-only with respect to the E-drive workbooks and the platform. It may search Feishu, download attachments to runtime storage, build staged copies, recalculate them, and validate them.
2. `apply-local` may update the named E-drive workbooks only with the exact reviewed plan hash and `--confirm-local-write`. It creates timestamped backups before replacement and rolls back on failure.
3. `upload` may overwrite the five existing platform temporary tables only with the exact successful local receipt hash and `--confirm-production-upload`.

A request only to analyze, explain, audit, or design the workflow stops after `plan`. The explicit request “上传郅玲玉在青橙数据对接内发布的最新临时表到线上平台” authorizes the intended end-to-end operation, but still execute and verify all three stages in order; never bypass the hashes, drift checks, backups, or receipts.

## Source Selection

Resolve the group and sender by their stable IDs from the registry, not by display name alone. Search all file messages in the group, keep only the configured sender, and choose the newest message matching each family’s filename patterns.

Do not treat these historical or intermediate files as current inputs:

- `qi*daibanguocheng.xlsx`
- `qing_team_moth_jg.xlsx`
- `task_*.xlsx`
- `CRM线索数据*.xlsx`

If any required family is absent, ambiguous, malformed, or has duplicate business keys, block the plan. Do not silently reuse an older local slice.

## Merge Rules

Never blindly append rows.

- Normalize only the explicit column aliases and constants in the registry.
- Compare effective cached values, not formula strings. This prevents needless rewrites of workbooks containing external-link formulas.
- For each source `qici` or `month`, remove the corresponding target slice and insert the current source slice.
- Preserve every target slice not present in the source.
- For `jiagou_db.xlsx`, replace rows only where `dept_1 = 青橙项目部` and the `qici` overlaps. Preserve all market-consultant rows, including those in the same period.
- Enforce the configured business key after merging.
- Preserve the configured sort direction and target column order.

An unchanged effective-value comparison is a valid local no-op. Do not rebuild a workbook merely because formulas or workbook metadata differ. A production upload still requires the explicit upload request and the successful local receipt.

## Run the Workflow

Use the mandated Python runtime:

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_temp_table_sync.py plan
```

Review `sync_plan.json`, especially:

- the five selected Feishu message IDs and source hashes;
- source slices, row counts, key uniqueness, and validation results;
- per-table added, replaced, removed, and unchanged counts;
- staged workbook hashes and any blockers;
- whether the result is a five-table no-op.

Apply the reviewed local plan using the exact printed values:

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_temp_table_sync.py apply-local `
  --plan <absolute-sync-plan-path> `
  --expected-plan-sha256 <exact-plan-sha256> `
  --confirm-local-write
```

Review `local_apply_receipt.json`, the backups, final local hashes, and post-write validation. Then upload the complete local workbooks:

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_temp_table_sync.py upload `
  --local-receipt <absolute-local-receipt-path> `
  --expected-receipt-sha256 <exact-receipt-sha256> `
  --confirm-production-upload
```

The upload stage must re-check that each selected Feishu message is still latest, verify that all local hashes still match the receipt, validate each workbook with the operator, and upload in registry order using the existing-table overwrite workflow.

## Failure Handling

- Stop before local writes when the plan has blockers or any staged validation regression.
- Preserve a baseline validation finding in the shared `jiagou_db.xlsx` only when the candidate introduces no new or worsened finding. Do not repair unrelated market-consultant data in this workflow.
- If local replacement fails, roll back every workbook already replaced and report the backup paths.
- If an upload fails, stop immediately. Record the successful uploads, the failed family, and the failed plus later families as pending. Never report a partial upload as success.
- Do not delete downloads, staged files, plans, backups, or receipts during the run.

## Completion Report

Report:

- selected source files with message time and message ID;
- source-to-local-to-platform mapping;
- slice-level diff and whether each family changed;
- local backup and receipt paths when writes occurred;
- platform upload status per family and the final receipt;
- any excluded files, pre-existing baseline warnings, blockers, or partial failures.

State explicitly when all five families were already aligned and no production upload was performed.
