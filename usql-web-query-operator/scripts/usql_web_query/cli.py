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

from _shared.config import DEFAULT_ARTIFACTS, DEFAULT_BROWSER_CHANNEL, DEFAULT_ENV_FILE, DEFAULT_STATE
from _shared.errors import UsageError

from .commands.doctor import cmd_doctor
from .commands.login import cmd_login
from .commands.run import cmd_run
from .commands.upload_temp_table import cmd_upload_temp_table
from .config import DEFAULT_QUERY_ENGINE


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
    run.add_argument("--headed", action="store_true", help="Show browser window.")
    run.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    run.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    run.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    run.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    run.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    run.add_argument("--engine", choices=["doris-presto", "presto"], default=DEFAULT_QUERY_ENGINE, help="Query engine to select before writing SQL. Default: doris-presto.")
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

    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
