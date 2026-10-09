"""CLI for persistent OES achievement-board query/export operations."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _shared.browser import import_playwright
from _shared.config import DEFAULT_BROWSER_CHANNEL, DEFAULT_ENV_FILE, DEFAULT_OES_STATE
from _shared.errors import UsageError

from .board import inspect_range, query_all, request_native_export, resolve_date_range, write_exports
from .session import open_session, state_expiry_summary
from .mailbox import (DEFAULT_MAIL_STATE, DEFAULT_SENDER, DEFAULT_SUBJECT,
                      open_outlook_session, parse_timestamp)
from .workflow import NATIVE_EXPORT_LIMIT, resolve_job_options, validate_mail_options, wait_for_attachment
from .partitioning import run_partitioned_pipeline
from .event_log import emit_event
from .workbook import atomic_json, file_info, validate_output_dir
from .base_sync import clean_cache, prepare_runtime_services, setup_base, run_base_sync


def _browser_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--headed", action="store_true")
    command.add_argument("--state-path", type=Path, default=DEFAULT_OES_STATE)
    command.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    command.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL)
    command.add_argument("--executable-path", default=None)
    command.add_argument("--login-timeout-ms", type=int, default=180_000)


def _mail_args(command: argparse.ArgumentParser, *, configurable: bool = False) -> None:
    command.add_argument("--mail-state-path", type=Path, default=DEFAULT_MAIL_STATE)
    command.add_argument("--mail-sender", default=None if configurable else DEFAULT_SENDER)
    command.add_argument("--mail-subject-contains", default=None if configurable else DEFAULT_SUBJECT)
    command.add_argument("--wait-seconds", type=int, default=None if configurable else 0)
    command.add_argument("--poll-seconds", type=int, default=None if configurable else 15)
    command.add_argument("--scan-pages", type=int, default=None if configurable else 5)


def _date_args(command: argparse.ArgumentParser, *, required: bool) -> None:
    dates = command.add_mutually_exclusive_group(required=required)
    dates.add_argument("--date", help="One business date, YYYY-MM-DD.")
    dates.add_argument("--start-date", help="Inclusive start date, YYYY-MM-DD.")
    command.add_argument("--end-date", help="Inclusive end date; required with --start-date.")
    command.add_argument("--output-dir", type=Path, required=True)
    command.add_argument("--page-size", type=int, default=500)
    command.add_argument("--timeout-ms", type=int, default=120_000)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persistent OES achievement-board query/export operator.")
    commands = parser.add_subparsers(dest="command", required=True)
    login = commands.add_parser("login", help="Create or refresh the isolated OES login state.")
    _browser_args(login)
    status = commands.add_parser("session-status", help="Verify the saved OES state against the live board.")
    _browser_args(status)
    export = commands.add_parser("export", help="Query a date range, export all rows locally, then request native export.")
    _browser_args(export)
    _date_args(export, required=True)
    probe = commands.add_parser("inspect-range", help="Read a tiny page to check date span, row count and complete native-export eligibility.")
    _browser_args(probe)
    dates = probe.add_mutually_exclusive_group(required=True)
    dates.add_argument("--date")
    dates.add_argument("--start-date")
    probe.add_argument("--end-date")
    probe.add_argument("--timeout-ms", type=int, default=120_000)
    for name, help_text in (("mail-login", "Create or refresh the isolated Outlook state using OES credentials."),
                            ("mail-session-status", "Verify the live Outlook state and refresh login once if expired.")):
        command = commands.add_parser(name, help=help_text)
        _browser_args(command)
        command.add_argument("--mail-state-path", type=Path, default=DEFAULT_MAIL_STATE)
    download = commands.add_parser("download-mail", help="Download one unambiguous OES Excel attachment without resubmitting export.")
    _browser_args(download)
    _mail_args(download)
    download.add_argument("--mail-subject", help="Optional exact subject in addition to the subject keyword.")
    download.add_argument("--received-after", required=True, help="ISO-8601 timestamp with timezone offset.")
    download.add_argument("--received-before", help="Optional inclusive ISO-8601 upper bound with timezone offset.")
    download.add_argument("--expected-count", type=int, required=True)
    download.add_argument("--query-json", type=Path, help="Optional saved OES query JSON for order reconciliation.")
    download.add_argument("--latest", action="store_true", help="Select the newest match only when its minute timestamp is unique.")
    download.add_argument("--output-dir", type=Path, required=True)
    pipeline = commands.add_parser("export-and-download", help="Query, split ranges over 10k rows, export each batch once, receive mail and merge verified XLSX; resume by run key.")
    _browser_args(pipeline)
    _date_args(pipeline, required=False)
    _mail_args(pipeline, configurable=True)
    pipeline.add_argument("--config-file", type=Path, help="Version 1 standalone date-filter and mail job JSON.")
    pipeline.add_argument("--run-key", required=True, help="Stable scheduler occurrence key; reusing it resumes instead of resubmitting.")
    setup = commands.add_parser("base-setup", help="Initialize the target's 13 Excel fields and the maintained Base start-time configuration.")
    setup.add_argument("--base-token", required=True)
    setup.add_argument("--table-id", required=True)
    setup.add_argument("--start-time", required=True)
    setup.add_argument("--output-dir", type=Path, required=True)
    setup.add_argument("--lark-cli", help="Native official Feishu CLI executable; discovered automatically when omitted.")
    sync = commands.add_parser("sync-base", help="Read the maintained Base start time, fix cutoff to run start, collect mail and clear old records in parallel, replace and verify all Excel fields.")
    _browser_args(sync)
    _mail_args(sync, configurable=True)
    sync.add_argument("--base-token", required=True)
    sync.add_argument("--table-id", required=True)
    sync.add_argument("--config-table-id", required=True)
    sync.add_argument("--config-record-id")
    sync.add_argument("--lark-cli")
    sync.add_argument("--output-dir", type=Path, required=True)
    sync.add_argument("--run-key", required=True)
    sync.add_argument("--page-size", type=int, default=1000)
    sync.add_argument("--timeout-ms", type=int, default=120_000)
    cleanup = commands.add_parser("clean-cache", help="Locally remove verified completed Base caches older than retention, preserve recovery files and compact replay guards, rotate daily logs.")
    cleanup.add_argument("--base-token", required=True)
    cleanup.add_argument("--table-id", required=True)
    cleanup.add_argument("--output-dir", type=Path, required=True)
    for command in (sync, cleanup):
        command.add_argument("--cache-retention-days", type=int, default=7)
        command.add_argument("--log-retention-days", type=int, default=30)
    return parser


def _run(args: Any) -> dict[str, Any]:
    if args.command == "clean-cache":
        return clean_cache(args)
    if args.command == "base-setup":
        validate_output_dir(args.output_dir)
        return setup_base(args)
    if getattr(args, "page_size", 1) <= 0 or getattr(args, "page_size", 1) > 1000:
        raise UsageError("--page-size must be between 1 and 1000.")
    if args.command == "export-and-download":
        start, end = resolve_job_options(args)
        validate_output_dir(args.output_dir)
    elif args.command in ("export", "inspect-range"):
        start, end = resolve_date_range(args.date, args.start_date, args.end_date)
        if args.command == "export":
            validate_output_dir(args.output_dir)
    elif args.command == "download-mail":
        validate_mail_options(args)
        validate_output_dir(args.output_dir)
        if not 0 <= args.expected_count <= NATIVE_EXPORT_LIMIT:
            raise UsageError("--expected-count must be between 0 and 10000.")
        received_after = parse_timestamp(args.received_after)
        received_before = parse_timestamp(args.received_before) if args.received_before else None
        if received_before and received_before < received_after:
            raise UsageError("--received-before must not be earlier than --received-after.")
    if args.command == "sync-base":
        prepare_runtime_services(args)
        emit_event(args, "browser_starting")
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        if args.command == "sync-base":
            result = run_base_sync(playwright, args)
            return {key: value for key, value in result.items() if key != "created_record_ids"}
        if args.command == "export-and-download":
            return run_partitioned_pipeline(playwright, args, start, end)
        if args.command.startswith("mail-") or args.command == "download-mail":
            mail_session = open_outlook_session(playwright, args)
            try:
                if args.command != "download-mail":
                    return {"status": "ok", "authenticated": True, "login_performed": mail_session.login_performed,
                            "state_path": str(args.mail_state_path), "checked_at": datetime.now(timezone.utc).isoformat()}
                rows = None
                if args.query_json:
                    try:
                        rows = json.loads(args.query_json.read_text(encoding="utf-8"))
                    except (OSError, ValueError) as exc:
                        raise UsageError("--query-json must contain a readable saved OES result array.") from exc
                    if not isinstance(rows, list):
                        raise UsageError("--query-json must contain a JSON array.")
                download = wait_for_attachment(mail_session, args, received_after=received_after,
                                               received_before=received_before, expected_count=args.expected_count,
                                               query_rows=rows, output_dir=args.output_dir)
                result = {"status": "completed", "row_count": args.expected_count, "mail_download": download,
                          "generated_at": datetime.now(timezone.utc).isoformat()}
                receipt_path = Path(download["file"]["path"]).with_suffix(".receipt.json")
                result["receipt_path"] = str(receipt_path)
                atomic_json(receipt_path, result)
                return result
            finally:
                mail_session.close()
        session = open_session(playwright, args, allow_interactive_login=args.command == "login")
        try:
            if args.command == "login":
                return {"status": "ok", "login_performed": session.login_performed, "state_path": str(args.state_path)}
            if args.command == "session-status":
                return {
                    "status": "ok",
                    "authenticated": True,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "declared_cookie_expiry": state_expiry_summary(args.state_path),
                }
            range_info = inspect_range(session.context.request, start, end, args.timeout_ms)
            if args.command == "inspect-range":
                return {"status": "ok", "checked_at": datetime.now(timezone.utc).isoformat(), **range_info}
            if range_info["row_count"] > NATIVE_EXPORT_LIMIT:
                raise UsageError("Native OES export is limited to 10000 rows; narrow the date range to avoid a truncated attachment.")
            rows, count, query_api = query_all(session.context.request, start, end, page_size=args.page_size, timeout_ms=args.timeout_ms)
            if count > NATIVE_EXPORT_LIMIT:
                raise UsageError("Native OES export is limited to 10000 rows; narrow the date range to avoid a truncated attachment.")
            json_path, csv_path = write_exports(rows, args.output_dir.resolve(), start, end)
            requested_at = datetime.now(timezone.utc).isoformat()
            native_export = request_native_export(session.context.request, start, end, args.timeout_ms)
            receipt = {
                "status": "ok",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "filter": {"start_date": start.isoformat(), "end_date": end.isoformat()},
                "sequence": ["query_all_pages", "write_local_json_csv", "request_native_export"],
                "row_count": count,
                "query_api": query_api,
                "native_export": native_export,
                "export_requested_at": requested_at,
                "files": [file_info(json_path), file_info(csv_path)],
            }
            receipt_path = json_path.with_suffix(".receipt.json")
            atomic_json(receipt_path, receipt)
            receipt["receipt_path"] = str(receipt_path)
            return receipt
        finally:
            session.close()


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        result = _run(args)
    except UsageError as exc:
        emit_event(args, "command_failed", error_type=type(exc).__name__, exit_code=2)
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except Exception as exc:
        emit_event(args, "command_failed", error_type=type(exc).__name__, exit_code=2)
        # Playwright exceptions can contain credential/session URLs; never print their raw call logs.
        print(json.dumps({"status": "error", "error_type": type(exc).__name__,
                          "error": "Browser or file operation failed; native export is never automatically retried."}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
