"""Operate the Baijia SQL取数 web UI through Playwright.

The script intentionally keeps credentials and browser storage outside the
skill directory. It is a POC automation surface: selectors are conservative and
artifacts are stored under the local Codex runtime folder by default.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from _shared.config import (
    DATA_CENTER_RUNTIME_DIR,
    DEFAULT_ARTIFACTS,
    DEFAULT_BROWSER_CHANNEL,
    DEFAULT_DATAMAP_CACHE,
    DEFAULT_DATAMAP_STATE,
    DEFAULT_ENV_FILE,
    DEFAULT_STATE,
    TEMPLATE_QUERY_RUNTIME_DIR,
)
from _shared.errors import UsageError

from .commands.check_manual_table import cmd_check_manual_table
from .commands.doctor import cmd_doctor
from .commands.fetch_market_template_sql import cmd_fetch_market_template_sql
from .commands.fetch_template_sql import cmd_fetch_template_sql
from .commands.login import cmd_login
from .commands.apply_data_center_sql_replacement import cmd_apply_data_center_sql_replacement
from .commands.plan_data_center_sql_replacement import cmd_plan_data_center_sql_replacement
from .commands.run import cmd_run
from .commands.sync_data_center_sql import cmd_sync_data_center_sql
from .commands.sync_datamap_fields import cmd_sync_datamap_fields
from .commands.template_download import cmd_template_download
from .commands.upload_temp_table import cmd_upload_temp_table
from .config import DEFAULT_QUERY_ENGINE
from .data_center import DEFAULT_MARKET_START_DATASET


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check local Playwright availability.")
    doctor.set_defaults(func=cmd_doctor)

    login = subparsers.add_parser("login", help="Authenticate and save browser storage state.")
    login.add_argument("--headed", action="store_true", help="Show browser window.")
    login.add_argument("--manual", action="store_true", help="Let the user complete login manually.")
    login.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    login.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    login.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    login.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    login.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    login.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    login.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    login.set_defaults(func=cmd_login)

    run = subparsers.add_parser("run", help="Run SQL in the web UI.")
    run.add_argument("--sql-file", type=Path, required=True)
    run.add_argument("--query-plan", type=Path, default=None, help="Optional QueryPlan JSON execution contract for this exact SQL file.")
    run.add_argument("--headed", action="store_true", help="Show browser window.")
    run.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    run.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    run.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    run.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    run.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    run.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    run.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    run.add_argument("--engine", choices=["doris-presto", "presto"], default=DEFAULT_QUERY_ENGINE, help="Query engine to select before writing SQL. Default: presto.")
    run.add_argument("--timeout-ms", type=int, default=10 * 60 * 1000)
    run.add_argument("--new-tab", action=argparse.BooleanOptionalAction, default=True)
    run.add_argument("--download", action="store_true", help="Download the result when local row-limit policy allows it.")
    run.add_argument("--no-download", action="store_false", dest="download")
    run.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under the runtime artifacts directory.")
    run.set_defaults(func=cmd_run)

    upload = subparsers.add_parser("upload-temp-table", help="Upload a local CSV/Excel file as a SQL temporary table.")
    upload.add_argument("--file", type=Path, required=True, help="Local .csv/.xls/.xlsx file to upload.")
    upload.add_argument("--file-type", choices=["csv", "excel"], default=None, help="Override file type inference from extension.")
    upload.add_argument("--target-table", default=None, help="Temporary table name. Defaults to the sanitized file stem.")
    upload.add_argument("--target-mode", choices=["new", "reuse"], default="reuse", help="Create a new table or reuse an existing table.")
    upload.add_argument("--import-mode", choices=["overwrite", "append"], default="overwrite", help="Import mode when reusing an existing table.")
    upload.add_argument("--header-row", action=argparse.BooleanOptionalAction, default=True, help="Treat the first row as field names.")
    upload.add_argument("--registry-path", type=Path, default=None, help="Manual temp-table registry JSON path.")
    upload.add_argument("--validate-manual-table", action=argparse.BooleanOptionalAction, default=True, help="Validate registered manual-table rules before upload.")
    upload.add_argument("--strict-validation", action="store_true", help="Stop before upload when manual-table validation reports errors.")
    upload.add_argument("--timeout-ms", type=int, default=10 * 60 * 1000, help="Maximum wait for import success.")
    upload.add_argument("--keep-history-open", action="store_true", help="Leave the import-history modal open after completion.")
    upload.add_argument("--headed", action="store_true", help="Show browser window.")
    upload.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    upload.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    upload.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    upload.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    upload.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    upload.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    upload.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    upload.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under the runtime artifacts directory.")
    upload.set_defaults(func=cmd_upload_temp_table)

    check_manual = subparsers.add_parser(
        "check-manual-table",
        help="Check local manual Excel files against the temp-table registry without opening the browser.",
    )
    check_manual.add_argument("--file", type=Path, action="append", help="Specific local manual table file to check. Repeatable.")
    check_manual.add_argument("--registry-path", type=Path, default=None, help="Manual temp-table registry JSON path.")
    check_manual.add_argument("--strict", action="store_true", help="Return non-zero when validation errors or review-required mappings exist.")
    check_manual.set_defaults(func=cmd_check_manual_table)

    sync_datamap = subparsers.add_parser(
        "sync-datamap-fields",
        help="Refresh business skill table fields from Data Map.",
    )
    sync_datamap.add_argument("--target-skill", choices=["all", "market", "qingcheng"], default="all", help="Built-in business skill target.")
    sync_datamap.add_argument("--skill-root", type=Path, action="append", help="Custom skill root to update. Repeatable.")
    sync_datamap.add_argument("--row-style", choices=["market", "qingcheng"], default=None, help="Markdown field-table style for custom --skill-root targets.")
    sync_datamap.add_argument("--table", action="append", help="Specific full table name to sync. Repeatable; defaults to all physical table docs.")
    sync_datamap.add_argument("--write", action="store_true", help="Write markdown changes. Default is dry-run.")
    sync_datamap.add_argument("--run-date", default=None, help="Override changelog/supplement date, format YYYY-MM-DD.")
    sync_datamap.add_argument("--refresh-datamap", action=argparse.BooleanOptionalAction, default=True, help="Fetch current schema from Data Map before syncing.")
    sync_datamap.add_argument("--only-missing-cache", action="store_true", help="When refreshing, skip tables already present in the cache.")
    sync_datamap.add_argument("--cache-file", type=Path, default=DEFAULT_DATAMAP_CACHE, help="Runtime Data Map table schema cache.")
    sync_datamap.add_argument("--datamap-state-path", type=Path, default=DEFAULT_DATAMAP_STATE, help="Data Map browser storage state path.")
    sync_datamap.add_argument("--headed", action="store_true", help="Show browser window while authenticating/fetching Data Map.")
    sync_datamap.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    sync_datamap.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    sync_datamap.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    sync_datamap.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    sync_datamap.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    sync_datamap.add_argument("--update-changelog", action=argparse.BooleanOptionalAction, default=True, help="Append changelog entry when writing field changes.")
    sync_datamap.add_argument("--rebuild-indexes", action=argparse.BooleanOptionalAction, default=True, help="Run target skill build_reverse_indexes.py after writes.")
    sync_datamap.add_argument("--build-catalog", action=argparse.BooleanOptionalAction, default=True, help="Rebuild shared Text2SQL manifests and physical catalog after writes.")
    sync_datamap.add_argument("--check-integrity", action=argparse.BooleanOptionalAction, default=True, help="Run target skill check_skill_integrity.py after writes.")
    sync_datamap.add_argument("--validate-stack", action=argparse.BooleanOptionalAction, default=True, help="Run the complete Text2SQL stack validation after writes.")
    sync_datamap.set_defaults(func=cmd_sync_datamap_fields)

    sync_data_center = subparsers.add_parser(
        "sync-data-center-sql",
        help="Refresh business skill raw SQL from Data Center datasets.",
    )
    sync_data_center.add_argument("--target-skill", choices=["all", "market", "qingcheng"], default="all", help="Built-in business skill target.")
    sync_data_center.add_argument("--dataset-name", action="append", help="Specific Data Center dataset name to sync. Repeatable; defaults to the configured scope.")
    sync_data_center.add_argument("--retire-model-id", action="append", help="Explicit current model retirement. With target=all use market:<id> or qingcheng:<id>.")
    sync_data_center.add_argument("--slot-binding", action="append", help="Reviewed semantic slot replacement in the form <slot_id>=<model_id>.")
    sync_data_center.add_argument("--market-start-name", default=DEFAULT_MARKET_START_DATASET, help="First market-consultant dataset to include.")
    sync_data_center.add_argument("--write", action="store_true", help="Write raw SQL and markdown changes. Default is dry-run.")
    sync_data_center.add_argument("--expected-plan-sha256", default=None, help="Exact hash emitted by a reviewed dry-run; required with --write.")
    sync_data_center.add_argument("--run-date", default=None, help="Override changelog/snapshot date, format YYYY-MM-DD.")
    sync_data_center.add_argument("--state-path", type=Path, default=DEFAULT_STATE, help="Shared Baijia browser storage state path.")
    sync_data_center.add_argument("--artifacts-dir", type=Path, default=DATA_CENTER_RUNTIME_DIR, help="Runtime summary output directory.")
    sync_data_center.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    sync_data_center.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    sync_data_center.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    sync_data_center.add_argument("--headed", action="store_true", help="Show browser window while authenticating/fetching Data Center.")
    sync_data_center.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    sync_data_center.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    sync_data_center.add_argument("--update-changelog", action=argparse.BooleanOptionalAction, default=True, help="Append changelog entry when writing SQL snapshots.")
    sync_data_center.add_argument("--rebuild-indexes", action=argparse.BooleanOptionalAction, default=True, help="Run target skill build_reverse_indexes.py after writes.")
    sync_data_center.add_argument("--check-integrity", action=argparse.BooleanOptionalAction, default=True, help="Run target skill check_skill_integrity.py after writes.")
    sync_data_center.add_argument("--validate-stack", action=argparse.BooleanOptionalAction, default=True, help="Run the complete Text2SQL stack after writes; disabling is rejected for Apply.")
    sync_data_center.set_defaults(func=cmd_sync_data_center_sql)

    plan_data_center_replacement = subparsers.add_parser(
        "plan-data-center-sql-replacement",
        help="Read one Data Center dataset and create a hash-bound remote replacement plan.",
    )
    plan_data_center_replacement.add_argument(
        "--domain",
        choices=["market", "qingcheng"],
        required=True,
        help="Department boundary used to resolve the dataset identity.",
    )
    replacement_identity = plan_data_center_replacement.add_mutually_exclusive_group(required=True)
    replacement_identity.add_argument("--dataset-name", help="Exact Data Center dataset name.")
    replacement_identity.add_argument("--dataset-id", help="Exact menu_set_* dataset identity.")
    plan_data_center_replacement.add_argument("--sql-file", type=Path, required=True, help="UTF-8 without BOM replacement SQL file.")
    plan_data_center_replacement.add_argument("--allow-noop", action="store_true", help="Allow an unchanged SQL hash only for an explicit refresh rehearsal.")
    plan_data_center_replacement.add_argument("--output-file", type=Path, default=None, help="Exact plan artifact path. Defaults to the Data Center runtime directory.")
    plan_data_center_replacement.add_argument("--state-path", type=Path, default=DEFAULT_STATE, help="Shared Baijia browser storage state path.")
    plan_data_center_replacement.add_argument("--artifacts-dir", type=Path, default=DATA_CENTER_RUNTIME_DIR / "replacement", help="Runtime directory for plan artifacts.")
    plan_data_center_replacement.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    plan_data_center_replacement.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    plan_data_center_replacement.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    plan_data_center_replacement.add_argument("--headed", action="store_true", help="Show browser while reading the current dataset state.")
    plan_data_center_replacement.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    plan_data_center_replacement.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    plan_data_center_replacement.set_defaults(func=cmd_plan_data_center_sql_replacement)

    apply_data_center_replacement = subparsers.add_parser(
        "apply-data-center-sql-replacement",
        help="Apply one reviewed SQL replacement, save it, trigger refresh, and verify SUCCESS.",
    )
    apply_data_center_replacement.add_argument("--plan-file", type=Path, required=True, help="Reviewed Data Center replacement plan artifact.")
    apply_data_center_replacement.add_argument("--expected-plan-sha256", required=True, help="Exact plan hash shown by the read-only planning command.")
    apply_data_center_replacement.add_argument("--confirm-production-write", action="store_true", help="Explicitly authorize the remote production write and refresh chain.")
    apply_data_center_replacement.add_argument("--preview-timeout-ms", type=int, default=10 * 60 * 1000, help="Maximum wait for replacement SQL preview execution.")
    apply_data_center_replacement.add_argument("--refresh-timeout-ms", type=int, default=20 * 60 * 1000, help="Maximum wait for a new synchronization record to reach SUCCESS.")
    apply_data_center_replacement.add_argument("--poll-interval-ms", type=int, default=3000, help="Synchronization-history polling interval.")
    apply_data_center_replacement.add_argument("--output-file", type=Path, default=None, help="Exact receipt path. Defaults to the Data Center runtime directory.")
    apply_data_center_replacement.add_argument("--state-path", type=Path, default=DEFAULT_STATE, help="Shared Baijia browser storage state path.")
    apply_data_center_replacement.add_argument("--artifacts-dir", type=Path, default=DATA_CENTER_RUNTIME_DIR / "replacement", help="Runtime directory for apply receipts.")
    apply_data_center_replacement.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    apply_data_center_replacement.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    apply_data_center_replacement.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    apply_data_center_replacement.add_argument("--headed", action="store_true", help="Show the browser during the production write chain.")
    apply_data_center_replacement.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    apply_data_center_replacement.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    apply_data_center_replacement.add_argument("--debug-artifacts", action="store_true", help="Capture a failure screenshot under the receipt path.")
    apply_data_center_replacement.set_defaults(func=cmd_apply_data_center_sql_replacement)

    fetch_template = subparsers.add_parser(
        "fetch-template-sql",
        help="Fetch stored SQL for a template in Template Query > My created templates.",
    )
    fetch_template.add_argument("--template-name", required=True, help="Template name to search in my created templates.")
    fetch_template.add_argument("--match", choices=["exact", "contains"], default="exact", help="Name match mode. Default: exact.")
    fetch_template.add_argument("--status", choices=["unpublished", "published", "offline", "1", "2", "3"], default=None, help="Optional template status filter.")
    fetch_template.add_argument("--output-file", type=Path, default=None, help="Where to save the fetched SQL. Defaults to the runtime template-query directory.")
    fetch_template.add_argument("--include-sql", action="store_true", help="Also include the full SQL text in the JSON summary.")
    fetch_template.add_argument("--page-size", type=int, default=100, help="API page size for template discovery.")
    fetch_template.add_argument("--max-pages", type=int, default=20, help="Maximum pages to scan when needed.")
    fetch_template.add_argument("--state-path", type=Path, default=DEFAULT_STATE, help="Shared Baijia browser storage state path.")
    fetch_template.add_argument("--artifacts-dir", type=Path, default=TEMPLATE_QUERY_RUNTIME_DIR, help="Runtime output directory for fetched template SQL.")
    fetch_template.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    fetch_template.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    fetch_template.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    fetch_template.add_argument("--headed", action="store_true", help="Show browser window while authenticating/fetching templates.")
    fetch_template.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    fetch_template.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    fetch_template.set_defaults(func=cmd_fetch_template_sql)

    fetch_market_template = subparsers.add_parser(
        "fetch-market-template-sql",
        help="Fetch stored SQL for a template in Template Query > Template Market.",
    )
    fetch_market_template.add_argument("--template-name", required=True, help="Template name to search in Template Market.")
    fetch_market_template.add_argument("--match", choices=["exact", "contains"], default="exact", help="Name match mode. Default: exact.")
    fetch_market_template.add_argument("--creator", default=None, help="Optional exact creator filter after market search.")
    fetch_market_template.add_argument("--output-file", type=Path, default=None, help="Where to save the fetched SQL. Defaults to the runtime template-query directory.")
    fetch_market_template.add_argument("--include-sql", action="store_true", help="Also include the full SQL text in the JSON summary.")
    fetch_market_template.add_argument("--page-size", type=int, default=100, help="API page size for template discovery.")
    fetch_market_template.add_argument("--max-pages", type=int, default=20, help="Maximum pages to scan when needed.")
    fetch_market_template.add_argument("--state-path", type=Path, default=DEFAULT_STATE, help="Shared Baijia browser storage state path.")
    fetch_market_template.add_argument("--artifacts-dir", type=Path, default=TEMPLATE_QUERY_RUNTIME_DIR, help="Runtime output directory for fetched template SQL.")
    fetch_market_template.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    fetch_market_template.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    fetch_market_template.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    fetch_market_template.add_argument("--headed", action="store_true", help="Show browser window while authenticating/fetching templates.")
    fetch_market_template.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    fetch_market_template.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    fetch_market_template.set_defaults(func=cmd_fetch_market_template_sql)

    template_download = subparsers.add_parser(
        "template-download",
        help="Create a temporary Template Query, run it, download the result, and clean up the template.",
    )
    template_download.add_argument("--sql-file", type=Path, required=True, help="Concrete SQL file to run through Template Query.")
    template_download.add_argument("--template-name", default=None, help="Temporary template name. Must be 20 characters or fewer.")
    template_download.add_argument("--template-description", default=None, help="Temporary template description.")
    template_download.add_argument("--query-name", default=None, help="Override the generated Template Query query name.")
    template_download.add_argument("--download-format", choices=["csv", "xls"], default="csv", help="Download format exposed by Template Query. Default: csv.")
    template_download.add_argument("--output-file", type=Path, default=None, help="Where to save the downloaded result. Defaults to the runtime template-query directory.")
    template_download.add_argument("--timeout-ms", type=int, default=20 * 60 * 1000, help="Maximum wait for query completion.")
    template_download.add_argument("--poll-interval-ms", type=int, default=2000, help="Polling interval for Template Query status checks.")
    template_download.add_argument("--include-preview", action="store_true", help="Include a small query-result preview in the JSON summary.")
    template_download.add_argument("--keep-template", action="store_true", help="Skip offline/delete cleanup for debugging.")
    template_download.add_argument("--headed", action="store_true", help="Show browser window while authenticating.")
    template_download.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under a timestamped runtime directory.")
    template_download.add_argument("--state-path", type=Path, default=DEFAULT_STATE, help="Shared Baijia browser storage state path.")
    template_download.add_argument("--artifacts-dir", type=Path, default=TEMPLATE_QUERY_RUNTIME_DIR / "downloads", help="Runtime output directory for downloads and optional debug artifacts.")
    template_download.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    template_download.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    template_download.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    template_download.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    template_download.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    template_download.set_defaults(func=cmd_template_download)

    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
