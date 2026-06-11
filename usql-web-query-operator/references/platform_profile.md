# SQL取数 Web Page Profile

## Known URLs

- Query page: `https://uanalysis.baijia.com/getDataSql`
- Dashboard page: `https://uanalysis.baijia.com/dashboard-market`
- Dashboard menu API: `https://uanalysis.baijia.com/uanalysis-intelligence/data/menu/manage`
- CAS login is reached through redirect when the saved login state is missing or expired.

## Script Boundary

- `scripts/usql_web_query.py`: SQL取数 execution, result preview, and result download only.
- `scripts/read_dashboard.py`: 自助BI dashboard folder/menu discovery and dashboard page reads only.
- Do not add dashboard scanning/reading commands back into `usql_web_query.py`.

## Credential Source

The local env file `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env` may contain `BAIJIA_USERNAME` and `BAIJIA_PASSWORD`. The script reads this file without printing values.

## Known Manual Flow

1. Open query page.
2. If redirected to CAS login, enter username and password and click `登录`.
3. On the query page, click top navigation `SQL取数`.
4. Click `+` to create a new query tab when needed.
5. Choose the engine before writing SQL.
   - Default automation path: `Doris-Presto` -> `doris内测加速版`
   - Baseline path: `Presto`
6. Paste SQL into the Monaco editor.
7. Click the run icon near the editor toolbar.
8. Wait for query history status to become `Success` or `Failed`.
9. Successful runs open a lower result tab named like `查询1377529335`.
10. In the result tab, use `结果` -> `表格` to inspect the table.
11. The download button is the small down-arrow icon at the left above the result table.
12. Do not download if the result can exceed 1000 rows.

## Selector Strategy (verified 2026-06-06)

### Page architecture

The page at `https://uanalysis.baijia.com/getDataSql` hosts the SQL editor inside an **iframe** (`<iframe src="/sql/?ts=...">`). All editor, run button, and result interactions must target the iframe content via `page.frame_locator('iframe[src^=\"/sql/\"]')`.

### Editor

The platform uses **CodeMirror** (NOT Monaco). The editor is inside the `/sql/` iframe.

- Set SQL: use `document.querySelector('.CodeMirror').CodeMirror.setValue(sql)` via `frame_obj.evaluate()`.
- Fallback: click `.CodeMirror` → Ctrl+A → paste.

### Engine selector

The engine selector is also inside the `/sql/` iframe, in `.antd-pro-src-components-editor-index-changeModeBox`.

Verified on 2026-06-11:

1. Click `.antd-pro-src-components-editor-index-changeModeBox .ant-select-selector`
2. Click `Doris-Presto`
3. Click `doris内测加速版`

After the Doris switch, the selector text changes from `Presto` to an internal engine label such as `PRESTO_817034371362430977`. Do not verify Doris selection by waiting for the literal child label to remain visible in the selector; it does not.

### Run

Preferred submission path:
- Focus CodeMirror.
- Select the current SQL.
- Press `Ctrl+E`.

Run-button fallback inside the iframe editor toolbar:
- `[aria-label='play-circle']`
- `.anticon-play-circle`
- visible toolbar button near the editor run area

### NPS satisfaction survey

An NPS (Net Promoter Score) modal may appear on page load. Dismiss it via:
- Close icon: `.nps-modal-close-icon` or `.nps-modal-close-icon > svg`
- Skip button: `.nps-result-button`
- Must dismiss before interacting with the editor or SQL tab.

### Status detection

Before clicking run, record existing query ids from both the query-history table and open result tabs. After submission, only treat a status/result as current when it belongs to a new query id or the history row SQL text matches the submitted SQL fingerprint.

Do not rely on whole-page `Success` text alone. Old successful result tabs can remain open and must not be treated as the current run.

Failure details are captured from:
- Ant notification/message/alert text.
- Failed query log (`log_area`) after opening the row's `日志`.
- Whole-page keyword fallback only when no structured source exists.

### Result extraction

Successful runs can open a lower result tab named like `查询1388196115`. A result area is current only when a new `查询<id>` tab exists after the run and the page shows `结果` / `表格` plus a result table, result field text, or download icon.

`已无更多` is useful for proving a small result page, but it is not required for detecting that the result area exists.

### Download

The download button is the down-arrow icon inside the iframe result area. Verified flow:

1. Click the result-area `.anticon-download` / download-labelled icon.
2. If the click opens a dropdown, select `excel` / `Excel` / `xlsx`.
3. If the icon immediately starts a browser download, save that file directly.

The verified xlsx filename pattern is like `task_<query_id>_<timestamp>.xlsx`.

## Open Questions

- Whether the page exposes a reliable total row count before download.
- Whether the platform blocks automated login for some sessions and requires manual SSO/MFA (current automated CAS login works headless).
- Exact dashboard page query/result APIs after opening a specific dashboard still need profiling. Folder names and dashboard IDs can be read from `read_dashboard.py scan-folder`, which posts `{"menuType":"HOME_AND_DASHBOARD"}` to the dashboard menu API.

## Dashboard Profiling APIs

Verified on 2026-06-01:

- Direct dashboard URL: `https://uanalysis.baijia.com/dashboard-market?id=<dashboard_id>&sourceType=1`
- Dashboard config: POST `https://uanalysis.baijia.com/uanalysis-intelligence/config/dashBoard` with `{"dashboardId":"<dashboard_id>","isConfig":false}`
- Unit detail: POST `https://uanalysis.baijia.com/uanalysis-intelligence/value/unit/consumer/detail` with `{"id":"<unit_id>","isConfig":false}`
- Public filter detail: POST `https://uanalysis.baijia.com/uanalysis-intelligence/value/public/unit/relation/detail` with `{"id":"<public_filter_relation_id>","isConfig":false}`
- Unit values / refresh validation: POST `https://uanalysis.baijia.com/uanalysis-intelligence/value/unit` with the target `unit_id`, empty filter lists, and a page object. Table/pivot units return `title`, `data`, `totalData`, `page`, and `taskIds`; chart units can return `xAxis`, `series`, and `taskIds` instead of table `data`.

Use `read_dashboard.py profile-dashboard` or `profile-folder` for this flow. Do not add these dashboard APIs to `usql_web_query.py`.

## Smoke Test SQL

Use this query to verify web execution. It aggregates to one output row and does not need download:

```sql
select
    count(*) as row_cnt,
    count(distinct lead_id) as lead_cnt,
    count(distinct user_id) as user_cnt,
    sum(lead_count) as total_lead,
    sum(valid_lead_count) as total_valid
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
where dt = '20260531'
  and hour = '11'
  and section_assign_employee_first_level_department_name = 'H业务线'
  and section_assign_employee_second_level_department_name = '市场部'
  and section_assign_employee_third_level_department_name = '市场顾问部'
```

Observed manual output on 2026-05-31:

| row_cnt | lead_cnt | user_cnt | total_lead | total_valid |
|---:|---:|---:|---:|---:|
| 1430177 | 1349091 | 1232028 | 1310953 | 1242942 |
