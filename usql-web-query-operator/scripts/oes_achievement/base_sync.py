"""Parallel OES/mail collection and full Base replacement with durable recovery."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace

from _shared.config import OES_RUNTIME_DIR
from _shared.errors import UsageError
from .base_client import BaseClient
from .base_records import HEADERS, field_definitions, timestamp_ms, validate_schema, verify_records, workbook_records
from .board import SHANGHAI, TimeWindow
from .event_log import EventLog
from .partitioning import run_partitioned_pipeline
from .retention import CacheRetention, validate_days
from .workbook import atomic_json, file_info, validate_output_dir
from .workflow import exclusive_workflow_lock, resolve_job_options

CREATE_LIMIT = 500
DELETE_LIMIT = 500
CONFIG_FIELDS = [
    {"name": "配置名称", "type": "text"},
    {"name": "开始时间", "type": "datetime", "style": {"format": "yyyy-MM-dd HH:mm"}},
    {"name": "启用", "type": "checkbox"},
    {"name": "数据表ID", "type": "text"},
    {"name": "最近运行标识", "type": "text"},
    {"name": "最近运行状态", "type": "text"},
    {"name": "最近截止时间", "type": "datetime", "style": {"format": "yyyy-MM-dd HH:mm"}},
    {"name": "最近完成时间", "type": "datetime", "style": {"format": "yyyy-MM-dd HH:mm"}},
    {"name": "最近明细行数", "type": "number", "style": {"type": "plain", "precision": 0}},
]


def prepare_runtime_services(args) -> CacheRetention:
    args.output_dir = validate_output_dir(args.output_dir)
    days = validate_days(getattr(args, "cache_retention_days", 7), "cache_retention_days")
    log_days = validate_days(getattr(args, "log_retention_days", 30), "log_retention_days")
    target_hash = hashlib.sha256(f"{args.base_token}:{args.table_id}".encode()).hexdigest()[:24]
    run_hash = hashlib.sha256(getattr(args, "run_key", "local-cache-cleanup").encode()).hexdigest()
    root = OES_RUNTIME_DIR.parent
    args.event_log = EventLog(root / "logs" / target_hash, run_hash, args.table_id)
    args.event_log.prune(log_days)
    args.cache_retention = CacheRetention(args.output_dir, root / "completed-runs" / target_hash,
                                          args.base_token, args.table_id, days, args.event_log)
    return args.cache_retention


def clean_cache(args) -> dict:
    retention = prepare_runtime_services(args)
    target_hash = hashlib.sha256(f"{args.base_token}:{args.table_id}".encode()).hexdigest()[:24]
    with exclusive_workflow_lock(OES_RUNTIME_DIR / f"base-{target_hash}.lock"):
        result = retention.cleanup()
    return {"status": "completed" if not result["failed_runs"] else "completed_with_cleanup_errors",
            "cache_cleanup": result, "log_file": str(args.event_log.path), "log_write_errors": args.event_log.write_errors}


def _register_completion(retention: CacheRetention, receipt: dict) -> None:
    try:
        retention.register(receipt)
    except (OSError, UsageError) as exc:
        # Data has already passed full readback. Keep its receipt and retry indexing at the next cleanup.
        receipt["completion_index_write_failed"] = True
        retention.logger.emit("completion_index_failed", error_type=type(exc).__name__)


def setup_base(args) -> dict:
    client = BaseClient(args.base_token, args.output_dir / "base-setup", args.lark_cli)
    fields = client.fields(args.table_id)
    if len(fields) == 1 and fields[0]["name"] == "文本" and fields[0]["type"] == "text":
        rows = client.records(args.table_id, ["文本"], "initial-backup")
        if any(row.get("文本") for row in rows):
            raise UsageError("Existing primary field contains data; schema initialization cannot rename unrelated content.")
        field = dict(fields[0])
        field.pop("id", None)
        field["name"] = "订单号"
        client.call("+field-update", "--table-id", args.table_id, "--field-id", fields[0]["id"],
                    "--format", "json", payload=field, confirm=True)
        fields = [{**fields[0], "name": "订单号"}]
    names = {field["name"] for field in fields}
    if names - set(HEADERS):
        raise UsageError("Target has unrelated fields; no schema fields were removed.")
    missing = [field for field in field_definitions() if field["name"] not in names]
    if missing:
        client.call("+field-create", "--table-id", args.table_id, "--format", "json", payload=missing)
    validate_schema(client.fields(args.table_id))
    tables = client.call("+table-list", "--format", "json")["tables"]
    configs = [table for table in tables if table["name"] == "导出配置"]
    if len(configs) > 1:
        raise UsageError("Multiple export configuration tables exist; resolve the exact target.")
    if configs:
        config_id = configs[0]["id"]
    else:
        created = client.call("+table-create", "--name", "导出配置", "--format", "json",
                              payload=CONFIG_FIELDS, payload_flag="--fields")
        config_id = created.get("table", {}).get("id") or created.get("table_id")
        if not config_id:
            raise UsageError("Configuration table create response changed; inspect tables before retrying.")
    schema = client.fields(config_id)
    if {item["name"]: item["type"] for item in schema} != {item["name"]: item["type"] for item in CONFIG_FIELDS}:
        raise UsageError("Existing configuration schema differs from the export contract.")
    config_rows = client.records(config_id, [field["name"] for field in CONFIG_FIELDS], "configuration")
    selected = [row for row in config_rows if row.get("数据表ID") == args.table_id]
    if not selected:
        record_id = client.create(config_id, [{"配置名称": "OES订单全量同步", "开始时间": timestamp_ms(args.start_time),
                                              "启用": True, "数据表ID": args.table_id, "最近运行状态": "ready"}])[0]
    elif len(selected) == 1:
        record_id = selected[0]["record_id"]  # Setup never rewrites a maintained start time.
    else:
        raise UsageError("Multiple configurations address the same target table.")
    result = {"status": "completed", "base_token": args.base_token, "table_id": args.table_id,
              "config_table_id": config_id, "config_record_id": record_id, "fields": list(HEADERS)}
    atomic_json(client.directory / "setup-receipt.json", result)
    return result


def clear_table(client: BaseClient, table_id: str, directory: Path, event_log=None) -> dict:
    started = time.time()
    if event_log:
        event_log.emit("base_clear_started")
    journal_path = directory / "clear-receipt.json"
    backup_path = directory / "previous-records.json"
    if journal_path.exists():
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        if journal["backup"] != file_info(backup_path):
            raise UsageError("Previous Base backup changed; replacement recovery was stopped.")
        backup = json.loads(backup_path.read_text(encoding="utf-8"))
        if journal["status"] == "cleared":
            if client.records(table_id, ["订单号"], "resume-empty"):
                raise UsageError("Cleared target acquired records; no new rows were written.")
            return journal
    else:
        backup = client.records(table_id, list(HEADERS), "backup")
        atomic_json(backup_path, backup)
        journal = {"status": "deleting", "backup": file_info(backup_path), "previous_row_count": len(backup),
                   "started_at_epoch": started, "deleted_batches": 0}
        atomic_json(journal_path, journal)
        if event_log:
            event_log.emit("base_backup_completed", previous_rows=len(backup))
    live = client.records(table_id, ["订单号"], "delete-preflight")
    old_ids = {row["record_id"] for row in backup}
    if any(row["record_id"] not in old_ids for row in live):
        raise UsageError("Target acquired unrelated record IDs during replacement; deletion stopped.")
    for offset in range(0, len(live), DELETE_LIMIT):
        client.delete(table_id, [row["record_id"] for row in live[offset:offset + DELETE_LIMIT]])
        journal["deleted_batches"] += 1
        atomic_json(journal_path, journal)
        if event_log:
            event_log.emit("base_delete_batch_completed", batch_index=journal["deleted_batches"],
                           batch_rows=min(DELETE_LIMIT, len(live) - offset))
    if client.records(table_id, ["订单号"], "confirm-empty"):
        raise UsageError("Base deletion did not produce a verified empty table; no Excel records were written.")
    journal.update(status="cleared", finished_at_epoch=time.time(), seconds=round(time.time() - started, 3))
    atomic_json(journal_path, journal)
    if event_log:
        event_log.emit("base_empty_verified", previous_rows=len(backup), seconds=journal["seconds"])
    return journal


def restore_previous(client: BaseClient, table_id: str, directory: Path, created_ids: list[str]) -> dict:
    backup_path = directory / "previous-records.json"
    journal_path = directory / "clear-receipt.json"
    if not backup_path.exists() or not journal_path.exists():
        return {"status": "no_deletion_started"}
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if journal["backup"] != file_info(backup_path):
        raise UsageError("Base restore backup failed its saved hash.")
    backup = json.loads(backup_path.read_text(encoding="utf-8"))
    actual = client.records(table_id, list(HEADERS), "restore-preflight")
    allowed = {row["record_id"] for row in backup} | set(created_ids)
    if any(row["record_id"] not in allowed for row in actual):
        raise UsageError("Unknown Base records exist after failure; preserve the backup and diagnose uncertain writes before restoring.")
    present = {row["record_id"] for row in actual}
    for offset in range(0, len(created_ids), DELETE_LIMIT):
        client.delete(table_id, [identity for identity in created_ids[offset:offset + DELETE_LIMIT] if identity in present])
    missing = []
    for row in backup:
        if row["record_id"] in present:
            continue
        values = {name: row[name] for name in HEADERS if row.get(name) is not None}
        if "时间" in values:
            # base/v3 reads ISO dates; native bitable/v1 writes epoch milliseconds.
            values["时间"] = timestamp_ms(values["时间"])
        missing.append(values)
    for offset in range(0, len(missing), CREATE_LIMIT):
        client.create(table_id, missing[offset:offset + CREATE_LIMIT])
    checked = verify_records(backup, client.records(table_id, list(HEADERS), "restored-readback"))
    return {"status": "restored_previous_values", "verification": checked}


def run_base_sync(playwright, args) -> dict:
    retention = getattr(args, "cache_retention", None) or prepare_runtime_services(args)
    logger = args.event_log
    logger.emit("run_started")
    try:
        result = _run_base_sync(playwright, args, retention)
        logger.emit("run_completed", status=result["status"], row_count=result.get("row_count"),
                    seconds=result.get("total_seconds"), reused=result.get("reused_completed_run", False))
        return {**result, "log_file": str(logger.path), "log_write_errors": logger.write_errors}
    except Exception as exc:
        logger.emit("run_failed", error_type=type(exc).__name__)
        raise


def _run_base_sync(playwright, args, retention: CacheRetention) -> dict:
    run_hash = hashlib.sha256(args.run_key.encode()).hexdigest()
    directory = args.output_dir / f"base-sync-{run_hash[:24]}"
    receipt_path = directory / "base-receipt.json"
    lock_hash = hashlib.sha256(f"{args.base_token}:{args.table_id}".encode()).hexdigest()[:24]
    with exclusive_workflow_lock(OES_RUNTIME_DIR / f"base-{lock_hash}.lock"):
        cleanup = retention.cleanup()
        completed = retention.expired_completion(run_hash)
        if completed is not None:
            identity = completed["identity"]
            if identity["config_table_id"] != args.config_table_id or (args.config_record_id and identity["config_record_id"] != args.config_record_id):
                raise UsageError("Expired run belongs to another configuration; choose a new run key.")
            args.event_log.emit("completed_run_cache_expired", row_count=completed["row_count"], reused=True)
            return {"status": "completed_cache_expired", "reused_completed_run": True,
                    "remote_readback_performed": False, "completed_at": completed["completed_at"],
                    "row_count": completed["row_count"], "end_ms": completed["end_ms"], "cache_cleanup": cleanup}
        directory.mkdir(parents=True, exist_ok=True)
        client = BaseClient(args.base_token, directory, args.lark_cli)
        validate_schema(client.fields(args.table_id))
        configs = client.records(args.config_table_id, [item["name"] for item in CONFIG_FIELDS], "config-read")
        selected = [row for row in configs if row.get("启用") is True and row.get("数据表ID") == args.table_id
                    and (not args.config_record_id or row["record_id"] == args.config_record_id)]
        if len(selected) != 1 or not selected[0].get("开始时间"):
            raise UsageError("Exactly one enabled configuration with a maintained start time is required.")
        config = selected[0]
        identity = {"base_token": args.base_token, "table_id": args.table_id, "config_table_id": args.config_table_id,
                    "config_record_id": config["record_id"], "start_ms": timestamp_ms(config["开始时间"]), "run_key_hash": run_hash}
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt["identity"] != identity:
                raise UsageError("Run key configuration changed; choose a new occurrence key instead of rebinding this run.")
            records_path = directory / "excel-records.json"
            if receipt["status"] == "completed":
                if receipt["excel_records"] != file_info(records_path):
                    raise UsageError("Completed Excel record snapshot changed.")
                verification = verify_records(json.loads(records_path.read_text(encoding="utf-8")), client.records(args.table_id, list(HEADERS), "reused-readback"))
                _register_completion(retention, receipt)
                args.event_log.emit("base_readback_verified", row_count=receipt["row_count"], reused=True)
                return {**receipt, "verification": verification, "reused_completed_run": True, "cache_cleanup": cleanup}
            if receipt["status"] == "failed_restored":
                # Restoration was verified. Preserve the old backup before a fresh deletion attempt.
                suffix = str(int(time.time() * 1000))
                for name in ("clear-receipt.json", "previous-records.json"):
                    previous = directory / name
                    if previous.exists():
                        previous.rename(directory / f"recovered-{suffix}-{name}")
                receipt["status"] = "source_ready" if receipt.get("source_receipt_path") else "collecting"
                receipt["created_record_ids"] = []
                receipt.pop("last_error", None)
                atomic_json(receipt_path, receipt)
            if receipt["status"] not in ("collecting", "source_ready"):
                raise UsageError(f"Base replacement state is {receipt['status']}; inspect the saved backup and receipt before starting another run.")
        else:
            now_ms = int(datetime.now(SHANGHAI).timestamp() * 1000)
            if identity["start_ms"] > now_ms:
                raise UsageError("Configured OES start time is later than the fixed run cutoff.")
            receipt = {"schema_version": 1, "identity": identity, "status": "collecting", "end_ms": now_ms,
                       "receipt_path": str(receipt_path), "started_at_epoch": time.time(), "created_record_ids": []}
            atomic_json(receipt_path, receipt)
        receipt["cache_cleanup"] = cleanup
        window = TimeWindow(identity["start_ms"], receipt["end_ms"])
        receipt["query_window"] = window.metadata()
        created_ids = list(receipt["created_record_ids"])
        with ThreadPoolExecutor(max_workers=1) as executor:
            clear_future = executor.submit(clear_table, client, args.table_id, directory, args.event_log)
            try:
                source_started = time.time()
                args.event_log.emit("source_collection_started", start_time=window.metadata()["start_time"],
                                    cutoff_time=window.metadata()["end_time"])
                if receipt["status"] == "source_ready":
                    source = json.loads(Path(receipt["source_receipt_path"]).read_text(encoding="utf-8"))
                    if receipt["excel_records"] != file_info(directory / "excel-records.json"):
                        raise UsageError("Saved Excel snapshot changed during recovery.")
                    records = json.loads((directory / "excel-records.json").read_text(encoding="utf-8"))
                else:
                    source_args = SimpleNamespace(**{**vars(args), "time_window": window, "run_key": args.run_key + "::oes",
                        "output_dir": directory / "source", "date": None, "start_date": window.dates[0].isoformat(),
                        "end_date": window.dates[1].isoformat(), "config_file": None})
                    resolve_job_options(source_args)
                    source = run_partitioned_pipeline(playwright, source_args, *window.dates)
                    paths = [Path(batch["mail_download"]["file"]["path"]) for batch in source.get("batches", [])]
                    if not paths and source.get("mail_download"):
                        paths = [Path(source["mail_download"]["file"]["path"])]
                    records = workbook_records(paths, source["row_count"]) if source["row_count"] else []
                    atomic_json(directory / "excel-records.json", records)
                    receipt.update(status="source_ready", source_receipt_path=source["receipt_path"],
                                   excel_records=file_info(directory / "excel-records.json"), row_count=len(records))
                    atomic_json(receipt_path, receipt)
                source_finished = time.time()
                args.event_log.emit("source_collection_completed", row_count=len(records), seconds=round(source_finished - source_started, 3))
                cleared = clear_future.result()
                receipt.update(clear=cleared, status="writing", source_seconds=round(source_finished - source_started, 3),
                    overlap_seconds=round(max(0, min(source_finished, cleared["finished_at_epoch"]) - max(source_started, cleared["started_at_epoch"])), 3))
                atomic_json(receipt_path, receipt)
                write_started = time.time()
                args.event_log.emit("base_write_started", row_count=len(records))
                for offset in range(0, len(records), CREATE_LIMIT):
                    receipt.update(write_batch_pending={"offset": offset, "count": min(CREATE_LIMIT, len(records)-offset)})
                    atomic_json(receipt_path, receipt)
                    # Never repeat an uncertain batch; the durable pending marker survives process death.
                    created_ids.extend(client.create(args.table_id, records[offset:offset + CREATE_LIMIT]))
                    receipt["created_record_ids"] = created_ids
                    receipt.pop("write_batch_pending", None)
                    atomic_json(receipt_path, receipt)
                    args.event_log.emit("base_write_batch_completed", batch_index=offset // CREATE_LIMIT + 1,
                                        batch_rows=min(CREATE_LIMIT, len(records) - offset))
                receipt["write_seconds"] = round(time.time() - write_started, 3)
                args.event_log.emit("base_write_completed", row_count=len(records), seconds=receipt["write_seconds"])
                read_started = time.time()
                args.event_log.emit("base_readback_started", row_count=len(records))
                actual = client.records(args.table_id, list(HEADERS), "full-readback")
                verification = verify_records(records, actual)
                receipt.update(status="completed", verification=verification, readback_seconds=round(time.time() - read_started, 3),
                               total_seconds=round(time.time() - receipt["started_at_epoch"], 3), completed_at=datetime.now(SHANGHAI).isoformat())
                atomic_json(receipt_path, receipt)
                args.event_log.emit("base_readback_verified", row_count=len(records), seconds=receipt["readback_seconds"])
                _register_completion(retention, receipt)
                client.call("+record-batch-update", "--table-id", args.config_table_id, "--format", "json",
                    payload={"update_records": {config["record_id"]: {"最近运行标识": args.run_key, "最近运行状态": "completed",
                        "最近截止时间": receipt["end_ms"], "最近完成时间": int(time.time()*1000), "最近明细行数": len(records)}}})
                return receipt
            except Exception as exc:
                if receipt.get("status") == "completed":
                    # Configuration status reporting is separate from the already verified data replacement.
                    receipt["config_status_update_failed"] = True
                    atomic_json(receipt_path, receipt)
                    args.event_log.emit("base_config_status_update_failed", error_type=type(exc).__name__)
                    return receipt
                try:
                    clear_future.result()
                except Exception:
                    pass
                receipt["last_error"] = str(exc) if isinstance(exc, UsageError) else "OES/mail/Base operation failed."
                if receipt.get("write_batch_pending"):
                    receipt["status"] = "base_write_uncertain"
                else:
                    try:
                        receipt["recovery"] = restore_previous(client, args.table_id, directory, created_ids)
                        receipt["status"] = "failed_restored"
                    except Exception:
                        receipt["status"] = "failed_requires_recovery"
                atomic_json(receipt_path, receipt)
                args.event_log.emit("base_recovery_completed", status=receipt["status"], error_type=type(exc).__name__)
                raise UsageError(f"{receipt['last_error']} State={receipt['status']}; keep the backup. Receipt: {receipt_path}") from exc
