# SQL取数 Error Handling

Verified on 2026-06-06 with `scripts/usql_web_query.py run`.

## Required Response Flow

When a run returns `ok=false`, always read `error_details` before deciding the next SQL edit.

Use this order:

1. `error_details.detail`
2. `error_details.raw_snippet`
3. `error_details.title`

Do not retry the same SQL blindly. Repair the SQL according to the captured error, then rerun.

Also read these summary fields first when present:

1. `error_category`
2. `error_category_label`
3. `repair_guidance`

These fields are the script's final classification layer and should be preferred over ad hoc guessing from the page state.

## Final Output Categories

| `error_category` | `error_category_label` | Meaning | Required response |
|---|---|---|---|
| `immediate_platform_error` | `即时错误` | The page rejected the SQL before a query history row was reliably created. This is usually a top-right notification/message/alert. | Stop retrying immediately. Fix the SQL from the popup text first, then rerun. |
| `query_log_error` | `日志区错误` | A query task was created and the failure is in the query history/log area. | Read the query log and repair from `VALIDATE_SQL_ERROR`, line/column, table, column, or runtime error text before rerunning. |
| `other_platform_error` | `其他平台错误` | The page exposed an error, but it does not match the two main verified routes above. | Preserve the raw text and inspect page state or debug artifacts before changing business logic. |

## Error Sources

| source | Meaning | Typical next step |
|---|---|---|
| `notification` / `message` / `alert` | The platform rejected the SQL before or during submission. A query id may not be created. | Read the notification detail and fix local SQL rules first. |
| `log_area` | A query history row was created and the execution log contains the failure. | Use the log detail, especially `VALIDATE_SQL_ERROR`, line/column, table, and column names. |
| `none` | No reliable platform error text was found. | Treat as automation/page-state issue; rerun with `--debug-artifacts` before changing SQL logic. |

## Verified Cases

| Case | Observed status | Source | Repair rule |
|---|---|---|---|
| Missing department/range boundary | `Failed` | `notification` -> `immediate_platform_error` | Add required department or architecture filters from the SQL skill rules; if user did not give a value, use a placeholder instead of inventing one. Do not click run again on the unchanged SQL. |
| Invalid column | `Failed` | `log_area` -> `query_log_error` | Read the `VALIDATE_SQL_ERROR(code=1017)` detail, then check the table doc/schema and replace or remove the bad field. |
| Presto syntax error | `Failed` | `notification` -> `immediate_platform_error` | Fix the reported line/column and Presto syntax before retrying. |
| No query permission / unknown table | `Failed` | `notification` -> `immediate_platform_error` | Do not interpret this as empty data. Switch to a readable table, reduce scope to a known permitted table, or ask the user to confirm permission/table availability. |
| Runtime type/cast/join mismatch after task creation | `Failed` | `log_area` -> `query_log_error` | Read the log detail for cast/type/join mismatch text, then fix the field type conversion, aggregation grain, or join keys before rerunning. |

## Repair Guidance Rules

Use `repair_guidance` from the JSON summary directly when it is present.

- For `即时错误`:
  - First suspect missing department/architecture range filters, permission scope, or a submission-time syntax problem.
  - The SQL was rejected before a stable query row was created, so repeated retries waste time and resources.
  - Repair the SQL first, then rerun once.
- For `日志区错误`:
  - The platform already accepted the submission and created a query task.
  - The next action is to read the log, not to guess from the SQL text alone.
  - Prioritize `VALIDATE_SQL_ERROR`, line/column, missing column/table, type conversion, and runtime join/aggregation issues.

Encoding note: some Chinese platform notifications currently arrive as mojibake in Playwright text extraction. Keep the raw snippet because it still preserves table names, field names, and SQL text, and the notification title/source is enough to classify the run as `Failed`.

## Non-Error Finding

The web platform did not consistently reject a missing `dt`/`hour` filter during tests. This does not relax SQL generation rules: keep validating partitions and required range filters before running SQL.

## Download Rule

Only use `--download` after `status=Success`. The script enforces local download safety: SQL must visibly contain `LIMIT 1000` or lower, or the result page must prove the output is no larger than 1000 rows.
