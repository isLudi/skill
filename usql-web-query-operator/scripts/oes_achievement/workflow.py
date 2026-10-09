"""Resumable, single-submission OES -> OWA -> verified XLSX workflow."""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Iterator

from _shared.config import OES_RUNTIME_DIR
from _shared.errors import UsageError
from .board import SHANGHAI, inspect_range, query_all, request_native_export, resolve_date_range, write_exports
from .mailbox import (DEFAULT_SENDER, DEFAULT_SUBJECT, list_export_mails, matching_mails,
                      read_export_mail, download_attachment, open_outlook_session)
from .session import open_session
from .event_log import emit_event
from .workbook import atomic_json, file_info, save_attachment, validate_output_dir, verify_xlsx

NATIVE_EXPORT_LIMIT = 10_000


@contextmanager
def exclusive_workflow_lock(path: Path) -> Iterator[None]:
    """OS-owned lock: process death releases it, without an orphaned lock-file gate."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            raise UsageError("Another OES/mail workflow is active; no native export was submitted.") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def resolve_job_options(args: Any, *, today: date | None = None) -> tuple[date, date]:
    config: dict[str, Any] = {}
    if getattr(args, "config_file", None):
        try:
            config = json.loads(args.config_file.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise UsageError("Job configuration must be a readable UTF-8 JSON file.") from exc
        if not isinstance(config, dict) or config.get("schema_version") != 1 or set(config) - {"schema_version", "job_name", "date_filter", "mail"}:
            raise UsageError("Unsupported OES/mail configuration schema or unknown top-level fields.")
        if any((args.date, args.start_date, args.end_date)):
            raise UsageError("Use either --config-file date_filter or explicit date flags, not both.")
        dates = config.get("date_filter", {})
        if not isinstance(dates, dict) or set(dates) - {"mode", "start_date", "end_date", "lookback_days"}:
            raise UsageError("Invalid date_filter configuration.")
        mode = dates.get("mode")
        if mode == "absolute":
            args.start_date, args.end_date = dates.get("start_date"), dates.get("end_date")
        elif mode in ("previous_day", "rolling_days"):
            anchor = today or datetime.now(SHANGHAI).date()
            days = 1 if mode == "previous_day" else dates.get("lookback_days")
            if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days < anchor.toordinal():
                raise UsageError("rolling_days requires a positive lookback_days within the representable calendar.")
            args.start_date, args.end_date = (anchor - timedelta(days=days)).isoformat(), (anchor - timedelta(days=1)).isoformat()
        else:
            raise UsageError("date_filter.mode must be absolute, previous_day or rolling_days.")
    mail = config.get("mail", {})
    if not isinstance(mail, dict) or set(mail) - {"sender", "subject_contains", "wait_seconds", "poll_seconds", "scan_pages"}:
        raise UsageError("Invalid mail configuration or unsupported fields.")
    defaults = {"mail_sender": DEFAULT_SENDER, "mail_subject_contains": DEFAULT_SUBJECT,
                "wait_seconds": 600, "poll_seconds": 15, "scan_pages": 5}
    for flag, default in defaults.items():
        config_key = {"mail_sender": "sender", "mail_subject_contains": "subject_contains"}.get(flag, flag)
        if getattr(args, flag, None) is None:
            setattr(args, flag, mail.get(config_key, default))
    validate_mail_options(args)
    return resolve_date_range(args.date, args.start_date, args.end_date)


def validate_mail_options(args: Any) -> None:
    for name, lower, upper in (("wait_seconds", 0, 7200), ("poll_seconds", 1, 60), ("scan_pages", 1, 50)):
        value = getattr(args, name)
        if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
            raise UsageError(f"{name} must be an integer between {lower} and {upper}.")
    if not args.mail_sender or not args.mail_subject_contains:
        raise UsageError("Mail sender and subject keyword must be non-empty.")


def wait_for_attachment(session: Any, args: Any, *, received_after: datetime,
                        expected_count: int, query_rows: list[dict[str, Any]] | None,
                        output_dir: Path, excluded_hashes: set[str] | None = None,
                        received_before: datetime | None = None) -> dict[str, Any]:
    deadline = time.monotonic() + args.wait_seconds
    emit_event(args, "mail_waiting", row_count=expected_count)
    while True:
        mails = list_export_mails(session, sender=args.mail_sender, subject_contains=args.mail_subject_contains, scan_pages=args.scan_pages)
        candidates = matching_mails(mails, received_after=received_after, received_before=received_before,
                                    excluded_hashes=excluded_hashes, exact_subject=getattr(args, "mail_subject", None))
        compatible = []
        for mail in candidates:
            count, attachments = read_export_mail(session, mail)
            if count == expected_count:
                compatible.append((mail, attachments[0]))
        if len(compatible) > 1 and not getattr(args, "latest", False):
            raise UsageError("Multiple new OES mails match the time, sender, subject and count; refusing an ambiguous attachment.")
        if compatible:
            mail, attachment = max(compatible, key=lambda pair: (pair[0].received_at, pair[0].identity_hash))
            if len(compatible) > 1:
                newest = mail.received_at
                if sum(candidate.received_at == newest for candidate, _ in compatible) != 1:
                    raise UsageError("The newest matching mails share a minute timestamp; --latest cannot disambiguate them.")
            data = download_attachment(session, attachment)
            verification = verify_xlsx(data, expected_count, query_rows)
            path = save_attachment(data, output_dir, mail.identity_hash)
            emit_event(args, "mail_excel_verified", row_count=expected_count, message_hash=mail.identity_hash)
            return {"message_hash": mail.identity_hash, "subject": mail.subject,
                    "received_at": mail.received_at.isoformat(), "sender": mail.sender,
                    "attachment_name": attachment.filename, "verification": verification, "file": file_info(path)}
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise UsageError("OES export mail did not arrive with the expected data count before the deadline; resume the same run key.")
        # Playwright's event loop remains live during a bounded wait.
        session.page.wait_for_timeout(int(min(args.poll_seconds, remaining) * 1000))


def _check_files(receipt: dict[str, Any], directory: Path) -> None:
    files = list(receipt.get("files", []))
    if receipt.get("mail_download"):
        files.append(receipt["mail_download"]["file"])
    for expected in files:
        path = Path(expected["path"]).resolve()
        if directory.resolve() not in path.parents or not path.is_file() or file_info(path) != expected:
            raise UsageError("Saved workflow files moved or changed; no export was resubmitted.")


def run_pipeline(playwright: Any, args: Any, start: date, end: date) -> dict[str, Any]:
    output_dir = validate_output_dir(args.output_dir)
    if not args.run_key.strip():
        raise UsageError("--run-key must be non-empty and stable across retries.")
    key_hash = hashlib.sha256(args.run_key.encode("utf-8")).hexdigest()
    directory = output_dir / f"oes-run-{key_hash[:24]}"
    receipt_path = directory / "receipt.json"
    identity = {"run_key_hash": key_hash, "start_date": start.isoformat(), "end_date": end.isoformat(),
                "mail_sender": args.mail_sender, "mail_subject_contains": args.mail_subject_contains}
    window = getattr(args, "time_window", None)
    if window:
        identity["time_window"] = window.metadata()
    lock = nullcontext() if getattr(args, "workflow_lock_held", False) else exclusive_workflow_lock(OES_RUNTIME_DIR / "export-mail.lock")
    with lock:
        receipt: dict[str, Any] = {"schema_version": 1, "identity": identity, "receipt_path": str(receipt_path),
                                   "status": "new", "sequence": [], "files": []}
        if receipt_path.exists():
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise UsageError("Existing run receipt is unreadable; refusing to resubmit native export.") from exc
            if receipt.get("identity") != identity:
                raise UsageError("Run key is already bound to another date range or mailbox selector.")
            _check_files(receipt, directory)
            if receipt.get("status") in ("completed", "completed_no_data"):
                if "last_error" in receipt or "last_error_type" in receipt:
                    receipt.pop("last_error", None)
                    receipt.pop("last_error_type", None)
                    atomic_json(receipt_path, receipt)
                return {**receipt, "reused_completed_run": True}
            if receipt.get("status") in ("export_requesting", "export_uncertain", "export_rejected"):
                raise UsageError(f"Native export status is {receipt['status']}; inspect receipt before choosing a new run key. No automatic resubmission.")
            if receipt.get("status") != "waiting_for_mail":
                raise UsageError("Unknown existing workflow state; refusing an automatic export retry.")
            if getattr(args, "submit_only", False):
                return receipt
        mail_session = None
        try:
            if receipt["status"] == "new":
                oes_session = open_session(playwright, args)
                try:
                    range_info = inspect_range(oes_session.context.request, start, end, args.timeout_ms, window=window)
                    if range_info["row_count"] > NATIVE_EXPORT_LIMIT:
                        raise UsageError("OES native export is limited to 10000 rows; narrow the date range before requesting mail export.")
                    prepared = getattr(args, "prepared_rows", None)
                    if prepared is None:
                        rows, count, api = query_all(oes_session.context.request, start, end, page_size=args.page_size, timeout_ms=args.timeout_ms, window=window)
                    else:
                        rows, count, api = prepared, len(prepared), getattr(args, "prepared_query_api", [])
                        if range_info["row_count"] != count:
                            raise UsageError("OES batch count changed since the complete query snapshot; no export was submitted.")
                    if count > NATIVE_EXPORT_LIMIT:
                        raise UsageError("OES native export is limited to 10000 rows; narrow the date range before requesting mail export.")
                    json_path, csv_path = write_exports(rows, directory, start, end)
                    receipt.update(row_count=count, query_api=api, files=[file_info(json_path), file_info(csv_path)])
                    emit_event(args, "oes_snapshot_ready", row_count=count)
                    if prepared is not None:
                        receipt.update(query_scope="complete_parent_snapshot", source_snapshot_sha256=getattr(args, "parent_snapshot_sha256", None))
                    receipt["sequence"].extend(["partition_complete_source_snapshot" if prepared is not None else "query_all_pages", "write_local_json_csv"])
                    if count == 0:
                        receipt.update(status="completed_no_data", completed_at=datetime.now(timezone.utc).isoformat())
                        atomic_json(receipt_path, receipt)
                        return receipt
                    # Mailbox login must work before the one authorized export request is made.
                    mail_session = open_outlook_session(playwright, args)
                    baseline = list_export_mails(mail_session, sender=args.mail_sender,
                                                 subject_contains=args.mail_subject_contains, scan_pages=args.scan_pages)
                    receipt["baseline_message_hashes"] = [m.identity_hash for m in baseline]
                    receipt["sequence"].append("snapshot_existing_export_mails")
                    receipt.update(status="export_requesting", export_requested_at=datetime.now(timezone.utc).isoformat())
                    atomic_json(receipt_path, receipt)
                    emit_event(args, "native_export_requested", row_count=count, receipt_path=str(receipt_path))
                    try:
                        native = request_native_export(oes_session.context.request, start, end, args.timeout_ms, window=window)
                    except Exception as exc:
                        receipt.update(status="export_uncertain", last_error_type=type(exc).__name__)
                        atomic_json(receipt_path, receipt)
                        emit_event(args, "native_export_uncertain", error_type=type(exc).__name__, receipt_path=str(receipt_path))
                        raise UsageError(f"Native export outcome is uncertain; no automatic retry. Receipt: {receipt_path}") from exc
                    receipt.update(status="waiting_for_mail", native_export=native)
                    receipt["sequence"].append("request_native_export_once")
                    atomic_json(receipt_path, receipt)
                    emit_event(args, "native_export_accepted", row_count=count, receipt_path=str(receipt_path))
                finally:
                    oes_session.close()
            else:
                rows = json.loads(Path(receipt["files"][0]["path"]).read_text(encoding="utf-8"))
            if getattr(args, "submit_only", False):
                return receipt
            if mail_session is None:
                mail_session = open_outlook_session(playwright, args)
            download = wait_for_attachment(mail_session, args, received_after=datetime.fromisoformat(receipt["export_requested_at"]),
                                           expected_count=receipt["row_count"], query_rows=rows, output_dir=directory,
                                           excluded_hashes=set(receipt["baseline_message_hashes"]))
            receipt.update(status="completed", mail_download=download, completed_at=datetime.now(timezone.utc).isoformat())
            receipt["sequence"].extend(["receive_new_export_mail", "verify_query_mail_workbook", "download_and_readback_xlsx"])
            receipt.pop("last_error_type", None)
            receipt.pop("last_error", None)
            atomic_json(receipt_path, receipt)
            return receipt
        except Exception as exc:
            if receipt["status"] == "waiting_for_mail":
                receipt["last_error_type"] = type(exc).__name__
                receipt["last_error"] = str(exc) if isinstance(exc, UsageError) else "Browser or file operation failed."
                atomic_json(receipt_path, receipt)
                raise UsageError(f"{receipt['last_error']} Resume the same --run-key. Receipt: {receipt_path}") from exc
            raise
        finally:
            if mail_session is not None:
                mail_session.close()
