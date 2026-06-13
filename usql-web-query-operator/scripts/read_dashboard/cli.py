"""CLI entrypoint for dashboard scanning and profiling."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from _shared.config import DEFAULT_ARTIFACTS, DEFAULT_BROWSER_CHANNEL, DEFAULT_ENV_FILE, DEFAULT_STATE
from _shared.errors import UsageError

from .commands.capture_dashboard import cmd_capture_dashboard
from .commands.profile_all import cmd_profile_all
from .commands.profile_dashboard import cmd_profile_dashboard
from .commands.profile_folder import cmd_profile_folder
from .commands.scan_folder import cmd_scan_folder
from .constants import DEFAULT_PROFILE_ALL_FOLDERS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan-folder", help="Scan dashboard names and IDs under a dashboard folder.")
    scan.add_argument("--folder", default="市场顾问数据")
    scan.add_argument("--output", type=Path, default=None)
    scan.add_argument("--headed", action="store_true", help="Show browser window.")
    scan.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    scan.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    scan.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    scan.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    scan.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    scan.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    scan.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    scan.add_argument("--wait-ms", type=int, default=3_000, help="Extra wait for lazy BI page refresh.")
    scan.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under the runtime artifacts directory.")
    scan.set_defaults(func=cmd_scan_folder)

    capture = subparsers.add_parser("capture-dashboard", help="Apply a period filter to one dashboard and save a focused screenshot.")
    capture.add_argument("--dashboard-id", required=True)
    capture.add_argument("--dashboard-name", default=None)
    capture.add_argument("--folder", default=None)
    capture.add_argument("--period", required=True, help="Target period, for example 20260612 or 20260612期.")
    capture.add_argument("--output-dir", type=Path, default=None)
    capture.add_argument("--headed", action="store_true", help="Show browser window.")
    capture.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    capture.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    capture.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    capture.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    capture.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    capture.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    capture.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    capture.add_argument("--wait-ms", type=int, default=12_000, help="Wait after opening the dashboard before interacting with filters.")
    capture.add_argument("--apply-wait-ms", type=int, default=12_000, help="Wait after changing the period filter before capturing.")
    capture.add_argument("--viewport-width", type=int, default=1_600, help="Browser viewport width used for the dashboard capture.")
    capture.add_argument("--viewport-height", type=int, default=1_000, help="Browser viewport height used for the dashboard capture.")
    capture.add_argument("--device-scale-factor", type=float, default=2.0, help="Device scale factor used for sharper screenshots.")
    capture.add_argument("--debug-artifacts", action="store_true", help="Save before/after full-page screenshots and HTML under the runtime artifacts directory.")
    capture.set_defaults(func=cmd_capture_dashboard)

    profile = subparsers.add_parser("profile-dashboard", help="Open one dashboard and store its component/filter/value structure.")
    profile.add_argument("--dashboard-id", required=True)
    profile.add_argument("--dashboard-name", default=None)
    profile.add_argument("--folder", default=None)
    profile.add_argument("--output", type=Path, default=None)
    profile.add_argument("--headed", action="store_true", help="Show browser window.")
    profile.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    profile.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    profile.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    profile.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    profile.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    profile.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    profile.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    profile.add_argument("--wait-ms", type=int, default=45_000, help="Wait after opening the dashboard so its data can refresh.")
    profile.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under the runtime artifacts directory.")
    profile.set_defaults(func=cmd_profile_dashboard)

    profile_folder = subparsers.add_parser("profile-folder", help="Profile selected dashboards under a folder.")
    profile_folder.add_argument("--folder", default="市场顾问数据")
    profile_folder.add_argument("--names", action="append", help="Dashboard names to profile. Repeat or separate with | or comma. Omit to profile all.")
    profile_folder.add_argument("--output-dir", type=Path, default=None)
    profile_folder.add_argument("--headed", action="store_true", help="Show browser window.")
    profile_folder.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    profile_folder.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    profile_folder.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    profile_folder.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    profile_folder.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    profile_folder.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    profile_folder.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    profile_folder.add_argument("--wait-ms", type=int, default=5_000, help="Wait after opening the BI page before scanning the folder.")
    profile_folder.add_argument("--dashboard-wait-ms", type=int, default=45_000, help="Wait after opening each dashboard so its data can refresh.")
    profile_folder.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under each dashboard profile directory.")
    profile_folder.set_defaults(func=cmd_profile_folder)

    profile_all = subparsers.add_parser("profile-all", help="Scan configured folders, profile all dashboards, and sync markdown web profiles.")
    profile_all.add_argument("--folders", action="append", help="Folder names to scan. Repeat or separate with | or comma. Defaults to 市场顾问数据 and 青橙项目部.")
    profile_all.add_argument("--output-dir", type=Path, default=None)
    profile_all.add_argument("--knowledge-dir", type=Path, default=None, help="Override the target dashboard_web_profiles directory when profiling exactly one folder.")
    profile_all.add_argument("--readme-path", type=Path, default=None, help="Override the target dashboard_web_profiles README when profiling exactly one folder.")
    profile_all.add_argument("--dashboards-readme-path", type=Path, default=None, help="Override the target dashboards README when profiling exactly one folder.")
    profile_all.add_argument("--changelog-path", type=Path, default=None, help="Override the target changelog when profiling exactly one folder.")
    profile_all.add_argument("--headed", action="store_true", help="Show browser window.")
    profile_all.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    profile_all.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    profile_all.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    profile_all.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    profile_all.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    profile_all.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    profile_all.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    profile_all.add_argument("--wait-ms", type=int, default=5_000, help="Wait after opening the BI page before scanning a folder.")
    profile_all.add_argument("--dashboard-wait-ms", type=int, default=45_000, help="Wait after opening each dashboard so its data can refresh.")
    profile_all.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under each dashboard profile directory.")
    profile_all.add_argument("--skip-dashboards-readme", action="store_true", help="Do not update knowledge/dashboards/README.md.")
    profile_all.add_argument("--skip-changelog", action="store_true", help="Do not append a knowledge changelog entry.")
    profile_all.set_defaults(func=cmd_profile_all, default_folders=list(DEFAULT_PROFILE_ALL_FOLDERS))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
