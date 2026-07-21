---
name: xunji-training-data
description: Read, cache, interpret, summarize, and safely write back Xunji (训记) training records through its Open API, and read official PlatformPlan or UniversalPlan schedules. Use only when the user explicitly asks to read, organize, analyze, edit, or write back 训记/Xunji training data, heart-rate, RPE, difficulty, history-card color, or official plan data. Do not use for general fitness advice or when no training-data operation was requested.
---

# Xunji Training Data

Use the Xunji Open APIs through the bundled guarded client. Keep reads, proposed changes, confirmed writes, and unrelated fitness advice as separate boundaries.

## Hard boundaries

- Call an API only after the user explicitly asks to read, organize, analyze, or write Xunji training data or official plans.
- Treat a read, summary, or edit proposal as read-only. It does not authorize writeback.
- Before every write, show a concise change summary and plan SHA-256, then stop and wait for explicit user confirmation of that exact plan.
- Never include an API key in a command, file, example, log, URL, query, body, or response. Read it only from `XUNJI_API_KEY` at request time.
- Never place API results, write plans, or receipts in this Skill or another Git repository. Keep them under the runtime cache directory.
- Do not infer that a missing raw heart-rate array is an error. Interpret the supported summary fields instead.

Before designing a request or interpreting a response, read [references/api.md](references/api.md) completely. Read the client source only when diagnosing or changing its behavior.

## Runtime setup

Use `D:\anaconda3\python.exe` in this workspace.

The user must configure `XUNJI_API_KEY` outside the conversation and repository. If it is absent, stop and ask the user to configure or regenerate the key in the app; do not ask them to paste it into a command or committed file. Set `XUNJI_AUTH_HEADER=x-api-key` only when the alternative header is required; otherwise use the default Bearer authorization.

The client stores private runtime artifacts under `~/.codex/runtime/xunji-training-data/` by default. Override only with `XUNJI_CACHE_DIR` pointing to another non-repository runtime directory.

```powershell
$xunjiClient = 'C:\Users\Ludim\.codex\skills\xunji-training-data\scripts\xunji_open_api.py'
& 'D:\anaconda3\python.exe' $xunjiClient --help
```

## Choose the operation

- For an ordinary training read, use lightweight mode.
- For unfinished sets, RPE, notes, completion feelings, left/right weights, actual duration, per-set rest, any heart-rate request, or any planned update, use full mode.
- For official plans, list first, then get one exact `plan_ref` and bounded date range.
- For organizing data already present in cache, read the cache; do not call the API again.
- For writeback, follow the guarded workflow below. Never call the endpoint manually.

## Read training records

```powershell
& 'D:\anaconda3\python.exe' $xunjiClient read-training --datestr 2026-07-20
& 'D:\anaconda3\python.exe' $xunjiClient read-training --datestr 2026-07-20 --full
```

The client caches by `datestr` and mode. Reuse the cache for the same date. A full cache may satisfy a lightweight read. Use `--refresh` only when the user explicitly requests a live refresh or there is concrete evidence that the cache is stale.

Read training rows from `res.trains`. Preserve `localid`, `start`, and `end` when preparing an update to an existing training.

For heart rate:

- Read with `--full`.
- Use `trains[].heartRate` for whole-training heart rate stored in the note.
- Use `sets[].metrics.avgHeartRate/maxHeartRate/minHeartRate` for movement-level summaries.
- Interpret `sets[].heartRate.values` as at most 50 bucket-average BPM points, with point `N` occurring at about `N * step` seconds.
- Report “no exportable heart-rate data” only when the training and all sets lack every supported heart-rate field.

## Read official plans

```powershell
& 'D:\anaconda3\python.exe' $xunjiClient list-plans
& 'D:\anaconda3\python.exe' $xunjiClient get-plan --plan-ref platform:155 --start-date 2026-07-20 --end-date 2026-08-12
& 'D:\anaconda3\python.exe' $xunjiClient get-plan --plan-ref universal:155 --without-movements
```

Treat `platform:155` and `universal:155` as different plan instances. Custom ranges may contain at most 92 inclusive calendar days. Read summaries from `res.plans` and detail from `res.plan`, `res.date_range`, and `res.days`.

## Prepare a write safely

1. Read the existing date with `read-training --full` when any item has a `localid`.
2. Build a complete candidate JSON under the runtime directory. Preserve all unrelated training, movement, set, unfinished-set, and note metadata.
3. Use only confirmed Chinese movement names. If uncertain, verify the name in the official [Xunji movement table](https://github.com/Foveluy/Xunji-movements); never invent a name.
4. Run `prepare-upsert`. It validates limits and field values, compares existing records with the full cached baseline, rejects accidental removals, writes a hash-bound plan, and prints a compact summary.
5. Present the printed summary and `plan_sha256` to the user. Do not apply it in the same turn unless the user had already explicitly confirmed that exact hash and summary.

```powershell
& 'D:\anaconda3\python.exe' $xunjiClient prepare-upsert --input 'C:\Users\Ludim\.codex\runtime\xunji-training-data\candidate.json' --include-full-data
```

Use `--allow-removal` only when the user explicitly requested deleting a movement, set, or note field and the summary makes that removal visible. A plan is descriptive and does not authorize writeback.

## Apply a confirmed write

After the user confirms the exact plan hash, run:

```powershell
& 'D:\anaconda3\python.exe' $xunjiClient apply-upsert --plan 'C:\Users\Ludim\.codex\runtime\xunji-training-data\plans\PLAN.json' --expected-sha256 '<CONFIRMED_SHA256>' --confirm-write
```

The client rejects a missing confirmation flag, a mismatched or modified plan, and an already-applied plan. After success it writes a receipt and replaces the affected date cache with the server-normalized response. Report the server result and receipt path without exposing credentials.

## Preserve field semantics

- Write RPE only to a concrete set as a permitted string from `"6"` through `"10"` in half steps; clear it with `""`, never `0`.
- Write super-set or drop-set RPE to `sets[].items[].set.rpe`.
- Write movement difficulty only as `easy`, `normal`, or `hard`.
- Write history color only to `note.trainColor` as `#RRGGBB` or `""`; preserve every other note field.
- Send movement `name`, never an internal `key`.
- Keep unfinished sets with `done: false`; do not silently drop them.
- Do not interpret an omitted old training as a deletion request.

## Handle failures

- On `too frequent`, report the server retry interval, wait that long, and retry only the same authorized operation.
- On `apikey missing` or `apikey invalid`, ask the user to regenerate the key in the app and configure `XUNJI_API_KEY` privately.
- On `仅VIP可用`, explain that the current account needs membership access.
- Treat a response as successful when its required core data is present in `res`; do not require `success === true`.
- If an action name is uncertain, stop for confirmation rather than writing.
