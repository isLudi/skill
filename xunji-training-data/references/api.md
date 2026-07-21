# Xunji Open API reference

## Contents

1. [Authentication and response contract](#authentication-and-response-contract)
2. [Training reads](#training-reads)
3. [Heart-rate and recorded movement data](#heart-rate-and-recorded-movement-data)
4. [Official plans](#official-plans)
5. [Training writeback](#training-writeback)
6. [RPE, difficulty, and history color](#rpe-difficulty-and-history-color)
7. [Validation and preservation rules](#validation-and-preservation-rules)
8. [Rate limits and errors](#rate-limits-and-errors)
9. [Bundled client contract](#bundled-client-contract)

## Authentication and response contract

- Training base URL: `https://trains.xunjiapp.cn`
- Official-plan base URL: `https://api.xunjiapp.cn`
- Preferred header: `Authorization: Bearer <XUNJI_API_KEY>`
- Compatible alternative header: `x-api-key: <XUNJI_API_KEY>`
- Never send the key in the body or query string.
- Never persist the key in the Skill, cache, plan, receipt, command history, or logs.
- Parse the core successful response from `res`. Do not require a `success` field to exist or equal `true`.

The bundled client reads the key from `XUNJI_API_KEY`. Set `XUNJI_AUTH_HEADER=x-api-key` to select the alternative header.

## Training reads

Endpoint:

```http
POST https://trains.xunjiapp.cn/api_trains_for_llm_v2
Content-Type: application/json
```

Lightweight request:

```json
{
  "schema_version": "train_open_api_v2",
  "datestr": "2026-04-02",
  "include_full_data": false
}
```

Use `include_full_data: false` for normal reading. Use `true` when the task requires any of the following:

- unfinished sets;
- RPE;
- notes or completion feelings;
- left/right weights;
- actual trained seconds;
- per-set rest seconds;
- any heart-rate data;
- preparation of an update to an existing training.

Training rows are under `res.trains`. Existing rows must retain `localid`, `start`, and `end` unless the user explicitly requests a time change.

Cache training reads by `datestr`. Reuse an existing cache instead of requesting the same date again. A full cache may satisfy a light read. A light cache cannot satisfy a request for full-only fields. Replace affected cache entries with the normalized server response after writeback.

## Heart-rate and recorded movement data

Always request full data for heart rate.

- Whole-training heart rate stored in the training note appears as `trains[].heartRate`.
- Movement-level heart-rate summaries for cardio, timed, Tabata, or Apple Health records appear in `sets[].metrics.avgHeartRate`, `maxHeartRate`, and `minHeartRate`.
- Other recorded metrics may include `distance`, `kcal`, `calories`, `workoutTime`, and related summaries under `sets[].metrics`.
- A compressed movement-level trend may appear in `sets[].heartRate`.

`sets[].heartRate` can contain:

```text
avg, max, min, duration, count, step, values, peak
```

`values` contains at most 50 bucket-average BPM points. Point `N` is approximately `N * step` seconds from the start. The API never returns a raw heart-rate sample array.

If `trains[].heartRate`, set metrics, and `sets[].heartRate` are all absent, report that no heart-rate data is exportable. Do not call the read a failure merely because a raw `heartRates` array is absent.

For Apple Health training, `name` is the workout type, such as `Running`; older data may be inferred from the training title.

Super-sets and drop-sets use `sets[].items[]`. Each child item stores its values under `items[].set`, including `weight`, `unit`, `reps`, `time`, `metrics`, and optional RPE.

## Official plans

Endpoint:

```http
POST https://api.xunjiapp.cn/open/plan/query_gzip
Accept-Encoding: gzip
Content-Type: application/json
```

The API may return gzip-compressed JSON. Decompress before parsing when the HTTP client does not do so automatically.

List plans first:

```json
{
  "schema_version": "plan_open_api_v1",
  "action": "list"
}
```

Plan summaries are under `res.plans`.

Then query one returned `plan_ref`:

```json
{
  "schema_version": "plan_open_api_v1",
  "action": "get",
  "plan_ref": "platform:155",
  "start_date": "2026-07-12",
  "end_date": "2026-08-12",
  "include_movements": true
}
```

- `platform:155` and `universal:155` identify different plan instances.
- Omitting dates reads the default window of today minus 7 days through today plus 30 days.
- A custom inclusive date range may contain at most 92 days.
- Use `include_movements: false` when only the calendar is needed.
- Detail is returned under `res.plan`, `res.date_range`, and `res.days`.
- Movement data contains Chinese names and target sets, not internal keys, rules, or synchronization metadata.
- Official plans are read-only.

## Training writeback

Endpoint:

```http
POST https://trains.xunjiapp.cn/api_upsert_trains_for_llm_v2
Content-Type: application/json
```

Request shape:

```json
{
  "schema_version": "train_open_api_v2",
  "client_request_id": "unique-id-from-agent",
  "dry_run": false,
  "include_full_data": false,
  "res": [
    {
      "datestr": "2026-04-02",
      "localid": 123456,
      "title": "胸部训练",
      "start": 1744010000000,
      "end": 1744013600000,
      "movements": [
        {
          "name": "杠铃卧推",
          "sets": [
            {"done": true, "weight": "60", "unit": "kg", "reps": "10"}
          ]
        }
      ]
    }
  ]
}
```

`res` may be a training array or `{ "trains": [...] }`. The bundled client normalizes it to an array.

- A row with `localid` updates the original training.
- A row without `localid` creates a new training.
- Absence from the request is not permission to delete an old training.
- Preserve `localid`, `start`, and `end` on updates unless the user explicitly asked to change time.
- Write only the Chinese movement `name`; never send an internal `key`.
- Resolve uncertain names from the official Chinese-name table: `https://github.com/Foveluy/Xunji-movements`.
- On success, use the server-normalized `res` to replace the affected cache.

## RPE, difficulty, and history color

Read the original with full data before changing any of these fields, and preserve all unrelated movements, sets, and note metadata.

RPE belongs on the concrete set as `movements[].sets[].rpe`. Permitted string values are:

```text
"6", "6.5", "7", "7.5", "8", "8.5", "9", "9.5", "10", ""
```

Use `""` to clear RPE. Never use numeric `0`. For a super-set or drop-set child, write RPE to `sets[].items[].set.rpe`.

Movement completion difficulty belongs on the movement object as `movements[].difficulty` and accepts only:

```text
easy, normal, hard
```

Do not write the Chinese display words into this field.

History-card color belongs in `note.trainColor`, never in a top-level `color` field. Use a CSS hexadecimal string such as `#FF7A00`; clear it with `""`.

If `note` is a JSON string, parse it to an object, merge only `trainColor`, and write a supported note shape. Preserve fields such as `text`, `heartRate`, `customTitle`, and `personalworkout_*`.

## Validation and preservation rules

- One write may contain at most 4 training rows.
- All rows in one write must belong to the same `datestr`.
- Each training may contain at most 15 movements.
- Each movement may contain at most 20 sets.
- A set must contain at least one of `weight`, `weight_kg`, `reps`, `time`, `duration_s`, or `selfWeight`, unless it is a container with `items`.
- Represent unfinished sets with `done: false`; never silently remove them after a full read.
- Preserve unrelated note fields and untouched training content.
- Use full response mode when writing RPE or difficulty so the normalized response retains complete data.

The bundled `prepare-upsert` command requires a full cached or explicitly supplied baseline for every row with `localid`. It blocks removal of movements, sets, nested items, and note fields unless `--allow-removal` is explicitly supplied. That flag is appropriate only after the user explicitly requested those removals.

## Rate limits and errors

Per user and training date:

- lightweight read: once every 15 seconds;
- full read: once every 30 seconds;
- writeback: once every 45 seconds.

Official-plan `list` and `get` requests are limited to once every 15 seconds for the same key, action, and plan instance.

On `too frequent`, read `retry_after_ms`, report the wait, wait the requested interval, and retry only the same authorized request.

- `apikey missing` or `apikey invalid`: ask the user to regenerate the key in the app and configure the new value privately.
- `仅VIP可用`: the account needs membership access.
- Missing `res`: treat the response as an API failure even if another status field appears successful.
- Present `res` as the core result even when no `success` field exists.

## Bundled client contract

`scripts/xunji_open_api.py` provides:

- `read-training`: cached light or full training reads;
- `list-plans`: cached official-plan list reads;
- `get-plan`: cached official-plan detail reads with range validation;
- `prepare-upsert`: offline input validation, full-baseline comparison, removal guard, change summary, and hash-bound plan creation;
- `apply-upsert`: exact-hash verification, explicit write flag, one-time receipt guard, remote write, and cache replacement.

The client never accepts an API key argument. It emits JSON as UTF-8 and redacts the in-memory key from HTTP error text before reporting it.
