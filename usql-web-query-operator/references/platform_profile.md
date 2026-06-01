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
5. Choose/keep engine `Presto`.
6. Paste SQL into the Monaco editor.
7. Click the run icon near the editor toolbar.
8. Wait for query history status to become `Success` or `Failed`.
9. Successful runs open a lower result tab named like `查询1377529335`.
10. In the result tab, use `结果` -> `表格` to inspect the table.
11. The download button is the small down-arrow icon at the left above the result table.
12. Do not download if the result can exceed 1000 rows.

## Selector Strategy (verified 2026-05-31 smoke test)

### Page architecture

The page at `https://uanalysis.baijia.com/getDataSql` hosts the SQL editor inside an **iframe** (`<iframe src="/sql/?ts=...">`). All editor, run button, and result interactions must target the iframe content via `page.frame_locator('iframe[src^=\"/sql/\"]')`.

### Editor

The platform uses **CodeMirror** (NOT Monaco). The editor is inside the `/sql/` iframe.

- Set SQL: use `document.querySelector('.CodeMirror').CodeMirror.setValue(sql)` via `frame_obj.evaluate()`.
- Fallback: click `.CodeMirror` → Ctrl+A → paste.

### Run button

Inside the iframe editor toolbar:
- Primary: `[aria-label='play-circle']` (anticon `anticon-play-circle` in `.antd-pro-src-components-editor-index-editorBtn`)

### NPS satisfaction survey

An NPS (Net Promoter Score) modal may appear on page load. Dismiss it via:
- Close icon: `.nps-modal-close-icon` or `.nps-modal-close-icon > svg`
- Skip button: `.nps-result-button`
- Must dismiss before interacting with the editor or SQL tab.

### Status detection

After clicking run, poll both the outer page and iframe body text for `Success` / `Failed`. The status appears in the query history table inside the iframe.

### Result extraction

The result panel does NOT open automatically after query success. The query history row shows "Success" but result data is NOT in the DOM until explicitly opened. This needs `--headed` debugging to determine the correct trigger. Candidates:
- Click the history row or the Success tag
- Click action buttons in the "操作" column

Once the result panel opens, expected sub-tabs: "结果" → "表格".

### Download

The download button is inside the iframe result area. Selectors to try:
- `[title*='下载']`, `[aria-label*='下载']`, `.anticon-download`
- Fallback: buttons in the 350-650 x-range near the result area

## Open Questions

- How to reliably open the result panel after query success (needs `--headed` debugging).
- Whether the download button exposes a stable aria-label/title or only an icon.
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
