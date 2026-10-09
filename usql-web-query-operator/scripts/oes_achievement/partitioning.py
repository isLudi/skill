"""Adaptive time partitions, exact source coverage and resumable batch exports."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from _shared.config import OES_RUNTIME_DIR
from _shared.errors import UsageError
from .board import SHANGHAI, TimeWindow, epoch_ms, inspect_range, query_all, write_exports
from .session import open_session
from .event_log import emit_event
from .workbook import atomic_json, file_info, merge_native_workbooks, validate_output_dir
from .workflow import NATIVE_EXPORT_LIMIT, _check_files, exclusive_workflow_lock, run_pipeline


def row_timestamp(row: dict[str, Any]) -> int:
    value = row.get("tradeTime")
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise UsageError("OES query lacks a millisecond tradeTime; exact time partitioning is unavailable.")
    try:
        return int(value)
    except ValueError as exc:
        raise UsageError("OES tradeTime is not a millisecond integer.") from exc


def build_partition_plan(rows: list[dict[str, Any]], window: TimeWindow, *, limit: int = NATIVE_EXPORT_LIMIT) -> list[dict[str, Any]]:
    if limit < 1:
        raise UsageError("Partition row limit must be positive.")
    timestamps = sorted(row_timestamp(row) for row in rows)
    ids = [row.get("id") for row in rows]
    if any(value is None for value in ids) or len(set(ids)) != len(ids):
        raise UsageError("Complete OES snapshot requires distinct row IDs; order numbers are not deduplication keys.")
    if timestamps and (timestamps[0] < window.start_ms or timestamps[-1] > window.end_ms):
        raise UsageError("OES tradeTime lies outside the requested range; filter semantics must be diagnosed before splitting.")
    plan: list[dict[str, Any]] = []
    def partition(current: TimeWindow) -> None:
        count = bisect_right(timestamps, current.end_ms) - bisect_left(timestamps, current.start_ms)
        if count <= limit:
            plan.append({**current.metadata(), "row_count": count})
            return
        if current.start_ms == current.end_ms:
            raise UsageError("More than 10000 rows share one millisecond; time splitting cannot produce a complete native export. No batch was submitted.")
        start, end = current.dates
        if start < end:
            next_date = start + timedelta(days=(end - start).days // 2 + 1)
            midpoint = int(epoch_ms(next_date, end_of_day=False)) - 1
        else:
            midpoint = (current.start_ms + current.end_ms) // 2
        partition(TimeWindow(current.start_ms, midpoint))
        partition(TimeWindow(midpoint + 1, current.end_ms))
    partition(window)
    if not plan or plan[0]["start_ms"] != window.start_ms or plan[-1]["end_ms"] != window.end_ms:
        raise UsageError("Partition plan does not cover the requested outer boundaries.")
    if any(left["end_ms"] + 1 != right["start_ms"] for left, right in zip(plan, plan[1:])):
        raise UsageError("Partition plan has a time gap or overlap.")
    if sum(part["row_count"] for part in plan) != len(rows):
        raise UsageError("Partition plan does not cover every source row.")
    return plan


def rows_in_window(rows: list[dict[str, Any]], window: TimeWindow) -> list[dict[str, Any]]:
    return [row for row in rows if window.start_ms <= row_timestamp(row) <= window.end_ms]


def run_partitioned_pipeline(playwright: Any, args: Any, start: Any, end: Any) -> dict[str, Any]:
    output_dir = validate_output_dir(args.output_dir)
    if not args.run_key.strip():
        raise UsageError("--run-key must be non-empty.")
    key_hash = hashlib.sha256(args.run_key.encode("utf-8")).hexdigest()
    directory = output_dir / f"oes-run-{key_hash[:24]}"
    root_receipt = directory / "batch-receipt.json"
    identity = {"run_key_hash": key_hash, "start_date": start.isoformat(), "end_date": end.isoformat(),
                "mail_sender": args.mail_sender, "mail_subject_contains": args.mail_subject_contains}
    requested_window = getattr(args, "time_window", None)
    if requested_window is not None:
        identity["time_window"] = requested_window.metadata()
    with exclusive_workflow_lock(OES_RUNTIME_DIR / "export-mail.lock"):
        child_base = SimpleNamespace(**{**vars(args), "workflow_lock_held": True})
        # Preserve existing single-batch receipts and their one-submission recovery semantics.
        if not root_receipt.exists() and (directory / "receipt.json").exists():
            return run_pipeline(playwright, child_base, start, end)
        receipt: dict[str, Any]
        if root_receipt.exists():
            receipt = json.loads(root_receipt.read_text(encoding="utf-8"))
            if receipt.get("identity") != identity:
                raise UsageError("Run key is already bound to another batch date range or mailbox selector.")
            _check_files(receipt, directory)
            if receipt.get("status") == "completed":
                return {**receipt, "reused_completed_run": True}
            if receipt.get("status") != "processing_batches":
                raise UsageError("Unknown batch workflow state; no automatic export retry.")
            rows = json.loads(Path(receipt["files"][0]["path"]).read_text(encoding="utf-8"))
            plan = json.loads(Path(receipt["files"][2]["path"]).read_text(encoding="utf-8"))["partitions"]
        else:
            oes = open_session(playwright, args)
            try:
                info = inspect_range(oes.context.request, start, end, args.timeout_ms, window=requested_window)
                if info["row_count"] <= NATIVE_EXPORT_LIMIT:
                    return run_pipeline(playwright, child_base, start, end)
                rows, count, api = query_all(oes.context.request, start, end, page_size=args.page_size, timeout_ms=args.timeout_ms, window=requested_window)
                window = requested_window or TimeWindow.from_dates(start, end)
                plan = build_partition_plan(rows, window)
                # Prove that the API applies each planned timestamp boundary before sending any batch.
                for part in plan:
                    subwindow = TimeWindow(part["start_ms"], part["end_ms"])
                    checked = inspect_range(oes.context.request, *subwindow.dates, args.timeout_ms, window=subwindow)
                    if checked["row_count"] != part["row_count"]:
                        raise UsageError("Planned time partitions do not match live API counts; no batch was exported.")
                if inspect_range(oes.context.request, start, end, args.timeout_ms, window=requested_window)["row_count"] != count:
                    raise UsageError("OES source changed during batch planning; no batch was exported.")
                json_path, csv_path = write_exports(rows, directory, start, end)
                plan_path = directory / "partition-plan.json"
                atomic_json(plan_path, {"schema_version": 1, "window": window.metadata(), "row_count": count,
                                       "coverage": "contiguous_closed_millisecond_ranges", "row_id_count": len(rows), "partitions": plan})
                receipt = {"schema_version": 2, "identity": identity, "receipt_path": str(root_receipt),
                           "status": "processing_batches", "row_count": count, "batch_count": sum(part["row_count"] > 0 for part in plan),
                           "query_api": api, "files": [file_info(json_path), file_info(csv_path), file_info(plan_path)],
                           "batches": [], "sequence": ["query_complete_source", "verify_gapless_partition_plan"]}
                atomic_json(root_receipt, receipt)
                emit_event(args, "oes_partition_plan_ready", row_count=count, batch_count=receipt["batch_count"])
            finally:
                oes.close()
        try:
            children = []
            for part in plan:
                if part["row_count"] == 0:
                    continue
                window = TimeWindow(part["start_ms"], part["end_ms"])
                child = SimpleNamespace(**{**vars(child_base), "run_key": f"{args.run_key}::batch::{window.start_ms}::{window.end_ms}",
                                           "output_dir": directory / "batches", "time_window": window,
                                           "prepared_rows": rows_in_window(rows, window), "prepared_query_api": receipt["query_api"],
                                           "parent_snapshot_sha256": receipt["files"][0]["sha256"]})
                children.append((part, child))
            # Different row counts distinguish outstanding export mails. Let the
            # server prepare these files together while Base deletion also runs.
            counts = [part["row_count"] for part, _ in children]
            dispatch_all = len(counts) > 1 and len(set(counts)) == len(counts)
            receipt["export_dispatch"] = "submit_all_then_receive" if dispatch_all else "serial_for_mail_disambiguation"
            if dispatch_all:
                submissions = []
                for part, child in children:
                    pending = SimpleNamespace(**{**vars(child), "submit_only": True})
                    submitted = run_pipeline(playwright, pending, *child.time_window.dates)
                    submissions.append({"partition": part, "receipt_path": submitted["receipt_path"], "status": submitted["status"]})
                    receipt["batch_submissions"] = submissions
                    atomic_json(root_receipt, receipt)
            batches = []
            for part, child in children:
                result = run_pipeline(playwright, child, *child.time_window.dates)
                batches.append({"partition": part, "receipt_path": result["receipt_path"], "status": result["status"],
                                "mail_download": result["mail_download"]})
                receipt["batches"] = batches
                atomic_json(root_receipt, receipt)
            if sum(batch["mail_download"]["verification"]["row_count"] for batch in batches) != receipt["row_count"]:
                raise UsageError("Downloaded batch totals do not match the complete source query.")
            merged = merge_native_workbooks([Path(batch["mail_download"]["file"]["path"]) for batch in batches], rows, directory)
            receipt.update(status="completed", merged_workbook=merged, completed_at=datetime.now(timezone.utc).isoformat())
            receipt["files"].extend(batch["mail_download"]["file"] for batch in batches)
            receipt["files"].append(merged["file"])
            receipt["sequence"].extend(["receive_and_verify_each_batch", "merge_xlsx", "reconcile_complete_source"])
            receipt.pop("last_error", None)
            atomic_json(root_receipt, receipt)
            emit_event(args, "excel_merge_verified", row_count=receipt["row_count"], batch_count=len(batches))
            return receipt
        except Exception as exc:
            receipt["last_error"] = str(exc) if isinstance(exc, UsageError) else "Browser or workbook operation failed."
            atomic_json(root_receipt, receipt)
            raise UsageError(f"{receipt['last_error']} Resume the same --run-key. Batch receipt: {root_receipt}") from exc
