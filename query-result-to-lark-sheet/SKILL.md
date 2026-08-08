---
name: query-result-to-lark-sheet
description: Deliver a verified business-query result as a new Feishu/Lark Sheet node in the openclaw knowledge-space root, preserving multiple child sheets such as raw data, native pivots, definitions, and run metadata. Use only when the user explicitly requests output as a lark sheet or Feishu electronic spreadsheet; keep local Excel delivery on the spreadsheet path.
---

# Query result to Lark Sheet

Use this Skill only for the final delivery mode `lark_sheet`. It is a cross-Skill delivery layer: the selected business Skill owns semantics and SQL, `usql-web-query-operator` owns execution and downloads, and `lark-sheets`/`lark-wiki` own Feishu resources. Do not generate business SQL here and do not modify official Lark Skills.

## Output-mode routing

- Explicit `lark sheet` / `Lark Sheet` / `飞书电子表格` → use this Skill.
- Explicit `Excel` / `xlsx` / `本地表格` → use the spreadsheet Skill and do not create a Feishu node.
- No explicit output mode → preserve the existing authorization boundary and ask for the output mode before writing either external or local deliverables.

## Required input contract

The delivery input must include the operator's real result file plus its evidence:

- `domain`, `report_key`, and the resolved time/filter scope;
- `query_id`, `sql_sha256`, `result_artifact_hash`, and the downloaded file path/hash;
- one or more named input tables, normally CSV/XLSX, for example `原始数据` or `口径说明`;
- an optional native-pivot specification; a grouped summary must be created through the official Lark pivot API and verified by `+pivot-list`, never supplied as a locally aggregated fake pivot;
- the parent Wiki URL `https://gaotuedu.feishu.cn/wiki/FcLew9hPXi5ViSkxsf9cvrtCnZb` or an explicitly approved equivalent. The default placement is `space-root`, which creates a new Sheet beside the existing root-level Sheets in the `openclaw` knowledge space. Use placement `parent` only when the caller explicitly requires a child of the `openclaw` document node.

`result_artifact.json` alone is insufficient because operator runtime artifacts do not contain result rows.

## Sheet naming convention

Validate the title during `plan`; do not create a node with a non-conforming title:

- `metadata.domain=market_consultant` → title starts with `市场顾问部_`.
- `metadata.domain=qingcheng` → title starts with `青橙项目部_`.
- Separate period, date, and data-description segments with single underscores, for example `市场顾问部_20260808_渠道数据` or `青橙项目部_20260626期_抖音正价复用_过程数据`.
- Do not use hyphens, spaces, slashes, empty segments, or a different department prefix. The plan is rejected before any remote write when the rule fails.

## Governed workflow

1. Run `scripts/deliver_query_result.py plan` to validate the parent node and title naming rule, read input files, validate any native-pivot specification, compute source/schema hashes, and write a runtime-only plan.
2. Review the plan. It must show the exact parent node, new Sheet title, child-sheet names, row counts, and source hashes.
3. Run `scripts/deliver_query_result.py apply --confirm-write --plan <plan>` only when the user requested the Feishu output. The command creates one new root-level `obj_type=sheet` Wiki node in the `openclaw` knowledge space by default; it never overwrites an existing node and never deletes a partially created node.
4. Before any sheet-level write, use `lark-sheets +workbook-info` to resolve the actual sheet IDs. Do not guess `Sheet1`.
5. Write typed values through `lark-sheets +table-put`; preserve numbers and dates as values, identifiers as text, and use native Lark pivots/formulas when a real pivot or formula is requested. Native pivot creation is followed by `+pivot-list` and `info.error_state` validation. Do not use local pandas aggregation to manufacture a fake pivot table.
6. Always add `运行元数据` unless the caller supplied an equivalent sheet. It records domain, report key, query ID, SQL/result hashes, input hashes, row counts, schema hash, plan hash, and creation time.
7. Read the complete used ranges back with `+table-get`, compare columns, row counts, and normalized content hashes, then read the final revision. Only a fully verified receipt may return the new Wiki Sheet URL.

## Failure and idempotence rules

- Recheck every source file hash before Apply. Any drift invalidates the plan.
- A failed Apply never auto-deletes a created Sheet node. The receipt must list the orphaned node URL and require manual inspection.
- Do not retry creation with the same plan unless an explicit resume path is implemented; otherwise a retry can create a second independent node.
- Empty results may be delivered only when the operator has verified `success_empty_verified`; write headers and metadata, and report zero rows explicitly.
- Large operator results must first use the operator's governed large-result/template-download workflow. This Skill only consumes the resulting local file and must not create an operator template itself.
- Keep runtime plans, payloads, and receipts outside the Skill directory. Never store credentials, cookies, or raw authorization responses in the repository.

## Script entry points

```powershell
# Read-only plan
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\query-result-to-lark-sheet\scripts\deliver_query_result.py plan `
  --parent-url "https://gaotuedu.feishu.cn/wiki/FcLew9hPXi5ViSkxsf9cvrtCnZb" `
  --placement space-root `
  --title "报表名称_20260808" `
  --input "原始数据=C:\path\result.xlsx" `
  --output "C:\Users\Ludim\.codex\runtime\query-result-to-lark-sheet\plan.json"

# Explicitly authorized remote creation/write, followed by readback
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\query-result-to-lark-sheet\scripts\deliver_query_result.py apply `
  --plan "C:\Users\Ludim\.codex\runtime\query-result-to-lark-sheet\plan.json" `
  --confirm-write `
  --receipt-out "C:\Users\Ludim\.codex\runtime\query-result-to-lark-sheet\receipt.json"
```

For detailed payload schema and target topology, read [delivery_contract.md](references/delivery_contract.md). For Feishu command semantics, read the current official `lark-shared`, `lark-wiki`, and `lark-sheets` Skills at execution time.
