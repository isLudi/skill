---
name: explore-data
description: Profile and explore datasets, database tables, SQL query results, CSV/Excel/Parquet/JSON files, and internal Presto/USQL table samples to understand shape, grain, columns, null rates, distributions, duplicates, date coverage, suspicious values, candidate dimensions/metrics, join keys, and query permission boundaries. Use when Codex is asked to inspect a new table, generate a data profile, check nulls/outliers/duplicates, verify which internal tables can be queried through USQL RestAPI, identify department or row-scope restrictions, understand table quality before writing SQL, or decide which dimensions and metrics are suitable for analysis. For internal dashboard tables, coordinate with sql-query-writer-for-dashboard and its USQL RestAPI rules.
---

# Explore Data

Use this skill to build a compact, evidence-based profile of a dataset before deeper analysis or dashboard SQL work.

## Scope

- Use this skill for data discovery, table profiling, field quality checks, candidate join-key discovery, and exploratory recommendations.
- Use this skill for USQL permission-boundary discovery: which tables can be queried, which fields are blocked, where department or row-scope limits apply, and what evidence is needed to request more access.
- Use `sql-query-writer-for-dashboard` when the main task is governed dashboard SQL generation or SQL repair.
- Use `validate-data` after an analysis exists and the task is to assess whether the methodology, result, chart, or conclusion is safe to share.
- For spreadsheet deliverables, use `xlsx`; for file profiling only, this skill may inspect CSV/XLSX/Parquet/JSON data with Python.

## Data Access

### Internal Presto / USQL Tables

When the user gives an internal table name or asks to explore a company dashboard table:

1. First check whether `../sql-query-writer-for-dashboard/knowledge/tables/` or `../sql-query-writer-for-dashboard/knowledge/01_table_index.md` already documents the table.
2. If the user wants live data profiling, read `../sql-query-writer-for-dashboard/knowledge/sql_patterns/usql_rest_api_python.md` and use the documented USQL RestAPI flow.
3. Use only read-only `SELECT` queries. Never run DDL, DML, deletes, inserts, updates, or writes.
4. Avoid full table scans. Require or infer a tight `dt`, `hour`, date, department, or other range condition before querying large partitioned tables.
5. For exploratory table samples, use `limit`; for large counts and distinct counts, prefer approximate or partition-scoped checks when exact scans are risky.
6. Do not print or persist real tokens, account credentials, cookies, or env values. Only report whether config was loaded.
7. Treat table permission and row-scope permission as separate facts. A table can be callable while still returning only the user's authorized departments, periods, or business lines.
8. Do not brute-force unknown table names or department values. Explore only user-provided tables, tables already present in the knowledge base, or explicitly approved candidate lists.

### USQL Permission Boundary Discovery

When the user's goal is to learn API permission boundaries, run the smallest safe checks in this order:

1. Verify API connectivity with `select 1 as smoke_test`.
2. For each candidate table, test a minimal scoped read such as `select 1 from <table> where <safe_partition_filter> limit 1`.
3. If the table is readable, test scoped row counts and sample rows only within approved filters.
4. Identify required filters from docs and errors: `dt`, `hour`, date, department, qici, project, business line, tenant, or other row-scope fields.
5. Test likely department/range fields one at a time with conservative `limit` or grouped counts. Prefer fields already documented in `sql-query-writer-for-dashboard`.
6. Classify failures as API config, table permission, field permission, row-scope restriction, parser false block, SQL syntax, missing partition/filter, or empty-but-readable result.
7. Record enough evidence to support a permission request: table, field(s), intended business scope, minimum SQL attempted, error signature, and why access is needed. Do not record token values or full sensitive responses.

Use a permission matrix:

| Table | Scope Tested | Result | Required Filter / Scope Field | Evidence | Follow-Up |
| --- | --- | --- | --- | --- | --- |
| schema.table | dt=... / dept=... | readable / denied / empty | field_name | error signature or row_count | apply for table/field/dept access |

### Local Files

When the user provides a file:

1. Read only the needed file. Preserve the original file.
2. Use `D:\anaconda3\python.exe` in this local Codex workspace unless the user explicitly requests another interpreter.
3. Use pandas/openpyxl/python-calamine/pyarrow or standard library tools depending on format availability.
4. For large files, inspect schema and sampled rows first, then decide whether full profiling is safe.

## Workflow

### 1. Clarify the Exploration Target

Identify:

- Dataset source: table, SQL result, CSV, Excel, Parquet, JSON, or pasted rows.
- Business question, if any.
- Required filters: date partition, hour, department, project, qici, tenant, or other scope.
- Whether the user wants a quick profile, data-quality scan, join-key investigation, or metric/dimension recommendation.
- Whether the task is also a permission-boundary investigation for USQL RestAPI.

If a live internal table has no safe range condition, ask for one or generate only metadata/sample-safe queries.

### 2. Understand Structure

Determine:

- Row count within the scoped range.
- Column count and available types.
- Grain: one row per what.
- Candidate primary key or natural key.
- Partition/date coverage.
- Update recency when a timestamp or partition field exists.

Classify each column:

- Identifier: unique keys, foreign keys, entity IDs.
- Dimension: categorical fields for grouping/filtering.
- Metric: numeric values for measurement.
- Temporal: dates, timestamps, partitions, qici, week/month fields.
- Text: names, descriptions, notes, free-form strings.
- Boolean/flag: true/false, 0/1, yes/no flags.
- Structural: JSON, arrays, serialized maps, nested fields.

### 3. Generate a Safe Profile

For table-level checks:

- Row count in the scoped range.
- Sample rows.
- Distinct count for likely keys and key dimensions.
- Date or partition min/max.
- Basic row duplication check for candidate keys.

For each important column:

- Null count and null rate.
- Distinct count and cardinality ratio.
- Top values with counts.
- Suspicious placeholder values such as empty string, `N/A`, `TBD`, `test`, `unknown`, `999999`, `-1`, or `0` when unexpected.

For numeric columns:

- min, max, avg.
- approximate percentiles if supported.
- zero count and negative count when meaningful.
- outlier or skew indicators.

For temporal columns:

- min/max date.
- future dates.
- missing partitions or obvious gaps.
- distribution by day/week/month when relevant.

### 4. Use Presto-Friendly Query Patterns

Adapt these patterns to the target table and required filters. Always use full table names.

```sql
-- scoped row count
select count(*) as row_count
from schema.table_name
where dt = '<YYYYMMDD>';

-- safe sample
select *
from schema.table_name
where dt = '<YYYYMMDD>'
limit 20;

-- null and distinct profile for selected columns
select
    count(*) as row_count,
    count_if(col_a is null) as col_a_null_count,
    approx_distinct(col_a) as col_a_approx_distinct,
    count_if(col_b is null) as col_b_null_count,
    approx_distinct(col_b) as col_b_approx_distinct
from schema.table_name
where dt = '<YYYYMMDD>';

-- top values for a dimension
select
    dim_col,
    count(*) as row_count
from schema.table_name
where dt = '<YYYYMMDD>'
group by dim_col
order by row_count desc
limit 20;

-- numeric profile
select
    min(metric_col) as min_value,
    max(metric_col) as max_value,
    avg(metric_col) as avg_value,
    approx_percentile(metric_col, 0.5) as p50,
    approx_percentile(metric_col, 0.95) as p95,
    count_if(metric_col = 0) as zero_count,
    count_if(metric_col < 0) as negative_count
from schema.table_name
where dt = '<YYYYMMDD>';

-- candidate key duplicate check
select
    key_col,
    count(*) as row_count
from schema.table_name
where dt = '<YYYYMMDD>'
group by key_col
having count(*) > 1
order by row_count desc
limit 20;
```

If the query platform rejects any function, simplify the query and explain the limitation.

### 5. Identify Data Quality Issues

Flag issues with severity:

- High null rate: warn above 5%, alert above 20%, unless the field is expected to be sparse.
- Candidate ID with unexpectedly low cardinality.
- Categorical dimension with unexpectedly high cardinality.
- Numeric fields with impossible negatives, extreme values, or suspicious zero concentration.
- Date fields with future dates, stale latest dates, or missing partitions.
- Duplicate natural keys.
- Mixed formats, trailing spaces, inconsistent casing, or placeholder values.
- Potential join explosion risk from many-to-many keys.

### 6. Discover Useful Analysis Paths

Recommend:

- Best dimensions for slicing: categorical fields with useful business meaning and manageable cardinality.
- Key metrics: numeric fields with meaningful non-null distributions.
- Time fields suitable for trend analysis.
- Candidate join keys and relationship direction when evidence supports it.
- Follow-up SQL checks needed before production use.

### 7. Update Knowledge When Permission Boundaries Are Learned

When permission checks reveal reusable facts, update the relevant knowledge base only if the user asks to preserve the finding or the task is clearly about maintaining the skill:

- Add table-specific notes to `../sql-query-writer-for-dashboard/knowledge/tables/<table>.md` when a known table has USQL access constraints.
- Add general API permission behavior to `../sql-query-writer-for-dashboard/knowledge/sql_patterns/usql_rest_api_python.md`.
- Append a dated entry to `../sql-query-writer-for-dashboard/knowledge/update_log/changelog.md`.
- Never write token values, account identifiers, cookies, raw credentials, or sensitive response payloads.

## Output Format

Use the user's language. Prefer concise tables and explicit caveats.

```markdown
## Data Profile: <dataset>

### Overview
- Source: <table/file/query result>
- Scope: <filters/date range/sample rule>
- Rows: <count or sampled count>
- Columns: <count and type summary>
- Likely grain: <one row per ...>
- Candidate key: <key or unknown>

### Column Profile
| Column | Type/Class | Null Rate | Cardinality | Example/Top Values | Notes |
| --- | --- | ---: | ---: | --- | --- |

### Data Quality Issues
1. [High/Medium/Low] <issue and impact>

### Candidate Dimensions, Metrics, and Join Keys
- Dimensions: ...
- Metrics: ...
- Time fields: ...
- Join keys: ...

### Recommended Follow-Up
1. <next query or analysis>

### Caveats
- <scope, sampling, missing metadata, or assumptions>

### Permission Boundary
| Table | Scope Tested | Result | Required Filter / Scope Field | Evidence | Access Request Suggestion |
| --- | --- | --- | --- | --- | --- |
```

## Practical Guidance

- If only metadata is available, clearly label the result as metadata-only and do not invent distributions.
- If profiling uses samples, state the sample size and avoid definitive claims about rare values.
- If a user asks for a "full table profile" on a large table, first propose a scoped or sampled profile.
- If a profile reveals analysis risk, suggest using `validate-data` after the target SQL or result is produced.
