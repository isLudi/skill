# SQL取数 Error Handling

Verified on 2026-06-06 with `scripts/usql_web_query.py run`.

## Required Response Flow

When a run returns `ok=false`, always read `error_details` before deciding the next SQL edit.

Use this order:

1. `error_details.detail`
2. `error_details.raw_snippet`
3. `error_details.title`

Do not retry the same SQL blindly. Repair the SQL according to the captured error, then rerun.

## Error Sources

| source | Meaning | Typical next step |
|---|---|---|
| `notification` / `message` / `alert` | The platform rejected the SQL before or during submission. A query id may not be created. | Read the notification detail and fix local SQL rules first. |
| `log_area` | A query history row was created and the execution log contains the failure. | Use the log detail, especially `VALIDATE_SQL_ERROR`, line/column, table, and column names. |
| `none` | No reliable platform error text was found. | Treat as automation/page-state issue; rerun with `--debug-artifacts` before changing SQL logic. |

## Verified Cases

| Case | Observed status | Source | Repair rule |
|---|---|---|---|
| Missing department/range boundary | `Failed` | `notification` | Add required department or architecture filters from the SQL skill rules; if user did not give a value, use a placeholder instead of inventing one. |
| Invalid column | `Failed` | `log_area` | Read the `VALIDATE_SQL_ERROR(code=1017)` detail, then check the table doc/schema and replace or remove the bad field. |
| Presto syntax error | `Failed` | `notification` | Fix the reported line/column and Presto syntax before retrying. |
| No query permission / unknown table | `Failed` | `notification` | Do not interpret this as empty data. Switch to a readable table, reduce scope to a known permitted table, or ask the user to confirm permission/table availability. |

Encoding note: some Chinese platform notifications currently arrive as mojibake in Playwright text extraction. Keep the raw snippet because it still preserves table names, field names, and SQL text, and the notification title/source is enough to classify the run as `Failed`.

## Non-Error Finding

The web platform did not consistently reject a missing `dt`/`hour` filter during tests. This does not relax SQL generation rules: keep validating partitions and required range filters before running SQL.

## Download Rule

Only use `--download` after `status=Success`. The script enforces local download safety: SQL must visibly contain `LIMIT 1000` or lower, or the result page must prove the output is no larger than 1000 rows.
