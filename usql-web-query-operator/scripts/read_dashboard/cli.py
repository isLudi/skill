"""CLI entrypoint for dashboard scanning and profiling."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from _shared.config import DEFAULT_ARTIFACTS, DEFAULT_BROWSER_CHANNEL, DEFAULT_ENV_FILE, DEFAULT_STATE
from _shared.errors import UsageError

from .commands.capture_dashboard import cmd_capture_dashboard
from .commands.check_dashboard_values import cmd_check_dashboard_values
from .commands.capture_write_evidence import cmd_capture_write_evidence
from .commands.apply_dashboard_change import cmd_apply_dashboard_change
from .commands.design_dashboard import cmd_design_dashboard
from .commands.edit_public_filters import cmd_edit_public_filters
from .commands.plan_dashboard_change import cmd_plan_dashboard_change
from .commands.profile_all import cmd_profile_all
from .commands.profile_dashboard import cmd_profile_dashboard
from .commands.profile_edit_dashboard import cmd_profile_edit_dashboard
from .commands.profile_edit_batch import cmd_profile_edit_all, cmd_profile_edit_folder
from .commands.profile_folder import cmd_profile_folder
from .commands.publish_dashboard_change import cmd_publish_dashboard_change
from .commands.scan_folder import cmd_scan_folder
from .commands.inspect_write_capabilities import cmd_inspect_write_capabilities
from .commands.verify_sandbox_write_adapters import cmd_verify_sandbox_write_adapters
from .constants import DEFAULT_PROFILE_ALL_FOLDERS
from .write_capabilities import DEFAULT_REGISTRY, MANUAL_PROBE_OPERATIONS


def _add_value_probe_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--value-request-timeout-ms", type=int, default=15_000)
    parser.add_argument("--value-max-attempts", type=int, default=2)
    parser.add_argument("--value-retry-backoff-ms", type=int, default=500)
    parser.add_argument("--value-dashboard-timeout-ms", type=int, default=90_000)
    parser.add_argument(
        "--value-failure-cache",
        type=Path,
        default=DEFAULT_ARTIFACTS / "dashboard_value_failures.json",
    )
    parser.add_argument("--value-failure-cache-ttl-seconds", type=int, default=900)
    parser.add_argument("--no-value-failure-cache", action="store_true")


def _add_edit_batch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--domain", choices=["auto", "market_consultant", "qingcheng"], default="auto")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--version-id", default="draft")
    parser.add_argument("--max-workers", type=int, default=2, help="Bounded worker count; clamped to 1..4.")
    parser.add_argument("--worker-timeout-seconds", type=int, default=300)
    parser.add_argument("--resume-max-age-seconds", type=int, default=86_400)
    resume = parser.add_mutually_exclusive_group()
    resume.add_argument("--resume", dest="resume", action="store_true")
    resume.add_argument("--no-resume", dest="resume", action="store_false")
    parser.set_defaults(resume=True)
    parser.add_argument("--skip-dataset-fields", action="store_true")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    parser.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL)
    parser.add_argument("--executable-path", default=None)
    parser.add_argument("--scan-wait-ms", type=int, default=3_000)
    parser.add_argument("--wait-ms", type=int, default=2_000)
    parser.add_argument("--debug-artifacts", action="store_true")


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
    profile.add_argument("--wait-ms", type=int, default=5_000, help="Wait after opening the dashboard before reading config.")
    profile.add_argument("--profile-mode", choices=["config", "full"], default="config")
    _add_value_probe_args(profile)
    profile.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under the runtime artifacts directory.")
    profile.set_defaults(func=cmd_profile_dashboard)

    value_health = subparsers.add_parser(
        "check-dashboard-values",
        help="Run bounded value/unit health checks from a cached dashboard config profile.",
    )
    value_health.add_argument("--profile", type=Path, required=True)
    value_health.add_argument("--output", type=Path, default=None)
    value_health.add_argument("--headed", action="store_true")
    value_health.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    value_health.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    value_health.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    value_health.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    value_health.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    value_health.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL)
    value_health.add_argument("--executable-path", default=None)
    value_health.add_argument("--wait-ms", type=int, default=3_000)
    _add_value_probe_args(value_health)
    value_health.set_defaults(func=cmd_check_dashboard_values)

    profile_edit = subparsers.add_parser(
        "profile-edit-dashboard",
        help="Read metric meanings and formulas from a Taitan dashboard edit page without modifying the dashboard.",
    )
    profile_edit.add_argument("--edit-url", default=None, help="Taitan edit URL containing dashboardId and optional htmlId.")
    profile_edit.add_argument("--dashboard-id", default=None, help="Dashboard ID. Required when --edit-url is omitted.")
    profile_edit.add_argument("--html-id", default=None, help="Optional htmlId used to build the edit URL.")
    profile_edit.add_argument("--version-id", default="draft", help="Dashboard version id to read; defaults to draft.")
    profile_edit.add_argument(
        "--domain",
        choices=["market_consultant", "qingcheng", "unresolved"],
        default="unresolved",
        help="Bind the profile to a business domain; unresolved profiles cannot enter apply or publish.",
    )
    profile_edit.add_argument("--output", type=Path, default=None)
    profile_edit.add_argument(
        "--normalized-output",
        type=Path,
        default=None,
        help="Optionally write the pure DashboardProfile artifact beside the backward-compatible rich profile.",
    )
    profile_edit.add_argument("--headed", action="store_true", help="Show browser window.")
    profile_edit.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    profile_edit.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    profile_edit.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    profile_edit.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    profile_edit.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    profile_edit.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    profile_edit.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    profile_edit.add_argument("--wait-ms", type=int, default=3_000, help="Wait after opening the edit page before reading APIs.")
    profile_edit.add_argument("--skip-dataset-fields", action="store_true", help="Skip the optional model field tree snapshot.")
    profile_edit.add_argument("--debug-artifacts", action="store_true", help="Save screenshot and HTML under the runtime artifacts directory.")
    profile_edit.set_defaults(func=cmd_profile_edit_dashboard)

    profile_edit_folder = subparsers.add_parser(
        "profile-edit-folder",
        help="Profile edit pages under one folder with bounded subprocess concurrency and resume cache.",
    )
    profile_edit_folder.add_argument("--folder", required=True)
    profile_edit_folder.add_argument("--names", action="append")
    _add_edit_batch_args(profile_edit_folder)
    profile_edit_folder.set_defaults(func=cmd_profile_edit_folder)

    profile_edit_all = subparsers.add_parser(
        "profile-edit-all",
        help="Profile governed market and Qingcheng edit pages with bounded concurrency and resume cache.",
    )
    profile_edit_all.add_argument("--folders", action="append")
    _add_edit_batch_args(profile_edit_all)
    profile_edit_all.set_defaults(func=cmd_profile_edit_all)

    design = subparsers.add_parser(
        "design-dashboard",
        help="Build a domain-bound DashboardDesignSpec locally; never writes to Taitan.",
    )
    design.add_argument("--profile", type=Path, required=True, help="DashboardProfile JSON from profile-edit-dashboard.")
    design.add_argument("--dataset-spec", type=Path, required=True, help="Domain-bound DashboardDatasetSpec JSON.")
    design.add_argument("--desired-state", type=Path, default=None, help="Optional JSON containing desired components/layout/formulas/public_filters.")
    design.add_argument("--domain", choices=["market_consultant", "qingcheng"], required=True)
    design.add_argument("--query-plan-sha256", default=None, help="Optional exact upstream QueryPlan SHA-256 binding.")
    design.add_argument("--design-intent", default="preserve_current", help="Auditable design intent label.")
    design.add_argument("--output", type=Path, required=True)
    design.set_defaults(func=cmd_design_dashboard)

    plan_change = subparsers.add_parser(
        "plan-dashboard-change",
        help="Diff a DashboardProfile and DashboardDesignSpec into a zero-write dry-run plan.",
    )
    plan_change.add_argument("--profile", type=Path, required=True)
    plan_change.add_argument("--design-spec", type=Path, required=True)
    plan_change.add_argument("--domain", choices=["market_consultant", "qingcheng"], required=True)
    plan_change.add_argument("--output", type=Path, required=True)
    plan_change.set_defaults(func=cmd_plan_dashboard_change)

    apply_change = subparsers.add_parser(
        "apply-dashboard-change",
        help="Apply one exact P4B allowlisted ChangePlan to draft with reverse recovery; never publishes.",
    )
    apply_change.add_argument("--change-plan", type=Path, required=True)
    apply_change.add_argument("--change-plan-sha256", required=True, help="Exact SHA-256 printed by plan-dashboard-change.")
    apply_change.add_argument("--domain", choices=["market_consultant", "qingcheng"], required=True)
    apply_change.add_argument("--output", type=Path, default=None)
    apply_change.add_argument("--headed", action="store_true", help="Show browser window.")
    apply_change.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    apply_change.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    apply_change.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    apply_change.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    apply_change.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    apply_change.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL)
    apply_change.add_argument("--executable-path", default=None)
    apply_change.add_argument("--wait-ms", type=int, default=3_000)
    apply_change.add_argument("--debug-artifacts", action="store_true")
    apply_change.set_defaults(func=cmd_apply_dashboard_change)

    publish_change = subparsers.add_parser(
        "publish-dashboard-change",
        help="Publish a verified ApplyReceipt in a separate explicitly confirmed command.",
    )
    publish_change.add_argument("--change-plan", type=Path, required=True)
    publish_change.add_argument("--change-plan-sha256", required=True)
    publish_change.add_argument("--apply-receipt", type=Path, required=True)
    publish_change.add_argument("--apply-receipt-sha256", required=True)
    publish_change.add_argument("--domain", choices=["market_consultant", "qingcheng"], required=True)
    publish_change.add_argument("--confirm-publish", action="store_true", required=True)
    publish_change.add_argument("--version-description", required=True)
    publish_change.add_argument("--output", type=Path, default=None)
    publish_change.add_argument("--headed", action="store_true", help="Show browser window.")
    publish_change.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    publish_change.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    publish_change.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    publish_change.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    publish_change.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    publish_change.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL)
    publish_change.add_argument("--executable-path", default=None)
    publish_change.add_argument("--wait-ms", type=int, default=3_000)
    publish_change.add_argument("--debug-artifacts", action="store_true")
    publish_change.set_defaults(func=cmd_publish_dashboard_change)

    inspect_write = subparsers.add_parser(
        "inspect-write-capabilities",
        help="Validate and summarize the P4A/P4B dashboard write capability registry without browser access.",
    )
    inspect_write.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    inspect_write.add_argument("--output", type=Path, default=None)
    inspect_write.set_defaults(func=cmd_inspect_write_capabilities)

    capture_write = subparsers.add_parser(
        "capture-write-evidence",
        help="Capture redacted request-shape evidence for exactly one manual action in an explicit sandbox dashboard.",
    )
    capture_write.add_argument("--operation", choices=sorted(MANUAL_PROBE_OPERATIONS), required=True)
    capture_write.add_argument("--sandbox-dashboard-id", required=True)
    capture_write.add_argument("--expected-dashboard-name", required=True, help="Exact live name; must contain P4A/sandbox/test/沙箱/测试.")
    capture_write.add_argument("--domain", choices=["market_consultant", "qingcheng"], required=True)
    capture_write.add_argument("--confirm-sandbox-write", action="store_true", required=True)
    capture_write.add_argument("--capture-seconds", type=int, default=45, help="Visible manual capture window, 10..300 seconds.")
    capture_write.add_argument("--html-id", default=None)
    capture_write.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    capture_write.add_argument("--output", type=Path, default=None)
    capture_write.add_argument("--headed", action="store_true", required=True)
    capture_write.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    capture_write.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    capture_write.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    capture_write.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    capture_write.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    capture_write.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL)
    capture_write.add_argument("--executable-path", default=None)
    capture_write.add_argument("--wait-ms", type=int, default=3_000)
    capture_write.add_argument("--debug-artifacts", action="store_true")
    capture_write.set_defaults(func=cmd_capture_write_evidence)

    verify_adapters = subparsers.add_parser(
        "verify-sandbox-write-adapters",
        help="Run reversible P4B adapters and a forward/reverse transaction in an exact sandbox, requiring a full-profile recovery match.",
    )
    verify_adapters.add_argument("--target-manifest", type=Path, required=True)
    verify_adapters.add_argument("--sandbox-dashboard-id", required=True)
    verify_adapters.add_argument("--expected-dashboard-name", required=True)
    verify_adapters.add_argument("--domain", choices=["market_consultant", "qingcheng"], required=True)
    verify_adapters.add_argument("--confirm-sandbox-write", action="store_true", required=True)
    verify_adapters.add_argument("--output", type=Path, default=None)
    verify_adapters.add_argument("--headed", action="store_true")
    verify_adapters.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    verify_adapters.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    verify_adapters.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    verify_adapters.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    verify_adapters.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    verify_adapters.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL)
    verify_adapters.add_argument("--executable-path", default=None)
    verify_adapters.add_argument("--wait-ms", type=int, default=3_000)
    verify_adapters.add_argument("--debug-artifacts", action="store_true")
    verify_adapters.set_defaults(func=cmd_verify_sandbox_write_adapters)

    edit_filters = subparsers.add_parser(
        "edit-public-filters",
        help="Legacy ordinal dry-run inspection only; all write/publish flags are rejected.",
    )
    edit_filters.add_argument("--folder", default="青橙播报")
    edit_filters.add_argument(
        "--target-set",
        choices=["qingcheng-required"],
        default=None,
        help="Built-in dashboard target set. qingcheng-required covers the six requested Qingcheng broadcast dashboards.",
    )
    edit_filters.add_argument("--name", action="append", help="Dashboard name. Repeat or separate with | or comma.")
    edit_filters.add_argument("--dashboard-id", action="append", help="Dashboard ID. Repeat or separate with | or comma.")
    edit_filters.add_argument("--html-id", default=None, help="Optional htmlId used to build edit URLs.")
    edit_filters.add_argument("--first-value", default="1", help="Dynamic filter value for the first public filter.")
    edit_filters.add_argument("--second-value", default="2", help="Dynamic filter value for the second public filter.")
    edit_filters.add_argument("--version-description", default="legacy dry-run only", help="Deprecated compatibility option; legacy publication is disabled.")
    edit_filters.add_argument("--output", type=Path, default=None)
    edit_filters.add_argument("--headed", action="store_true", help="Show browser window.")
    edit_filters.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    edit_filters.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    edit_filters.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    edit_filters.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    edit_filters.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    edit_filters.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    edit_filters.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    edit_filters.add_argument("--scan-wait-ms", type=int, default=3_000, help="Wait after opening the BI dashboard list.")
    edit_filters.add_argument("--wait-ms", type=int, default=3_000, help="Wait after opening each edit page before calling edit APIs.")
    edit_mode = edit_filters.add_mutually_exclusive_group()
    edit_mode.add_argument(
        "--apply",
        dest="dry_run",
        action="store_false",
        help="Deprecated and rejected. Use apply-dashboard-change with a reviewed stable-ID plan.",
    )
    edit_mode.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Read and plan changes without calling update or publish APIs. This is the default.",
    )
    edit_filters.add_argument("--publish", action="store_true", default=False, help="Deprecated and rejected. Use publish-dashboard-change.")
    edit_filters.add_argument(
        "--confirm-publish",
        action="store_true",
        help="Deprecated and rejected for the legacy command.",
    )
    edit_filters.add_argument("--strict-filter-count", action="store_true", help="Fail when a requested filter index is missing.")
    edit_filters.set_defaults(func=cmd_edit_public_filters, dry_run=True)

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
    profile_folder.add_argument("--dashboard-wait-ms", type=int, default=5_000, help="Wait after opening each dashboard before reading config.")
    profile_folder.add_argument("--profile-mode", choices=["config", "full"], default="config")
    _add_value_probe_args(profile_folder)
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
    profile_all.add_argument("--dashboard-wait-ms", type=int, default=5_000, help="Wait after opening each dashboard before reading config.")
    profile_all.add_argument("--profile-mode", choices=["config", "full"], default="config")
    _add_value_probe_args(profile_all)
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
