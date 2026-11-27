"""Load one governed Tiangong release for a local push producer."""

from datetime import datetime
import json
from pathlib import Path
import re


CONFIG_ROOT = Path(__file__).resolve().parents[3] / "config"
PRODUCER_FILES = {
    "market_consultant.leads": "market2lark.json",
    "market_consultant.volume": "market2lark_jinliang.json",
    "qingcheng.process": "qing2lark_guocheng.json",
    "qingcheng.transformation": "qing2lark_zhuanhua.json",
}


def binding_path(task_key, *, expected_domain, config_root=None):
    """Resolve only a registered local producer in the caller's own department."""
    if (not isinstance(task_key, str) or task_key not in PRODUCER_FILES
            or task_key.partition(".")[0] != expected_domain):
        raise ValueError(f"Unknown upstream producer for {expected_domain}: {task_key!r}")
    root = Path(config_root or CONFIG_ROOT).resolve()
    path = (root / "release" / PRODUCER_FILES[task_key]).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Upstream producer file escaped configuration root: {task_key}")
    return path


def _positive_integer(value):
    return type(value) is int and value > 0


def read_binding_document(task_key, *, expected_domain, config_root=None):
    path = binding_path(task_key, expected_domain=expected_domain, config_root=config_root)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read upstream binding {task_key}: {error}") from error
    if not isinstance(record, dict) or (
            record.get("schema_version"), record.get("domain"), record.get("execution_surface"),
            record.get("task_key")) != (1, expected_domain, "local", task_key):
        raise ValueError(f"Upstream binding identity differs: {task_key}")
    upstream = record.get("upstream")
    if not isinstance(upstream, dict) or "approved_release_binding" in upstream:
        raise ValueError(f"Missing upstream identity: {task_key}")
    market = expected_domain == "market_consultant"
    version_field = "verified_version_id" if market else "version_id"
    source_field = "verified_source_sha256" if market else "source_sha256"
    ids = ["project_id", "menu_id", "task_id", "nezha_task_id", "exec_file_id", version_field]
    if market:
        ids.append("schedule_id")
    text_fields = ("folder", "task_name", "owner", "log_protocol") if market else (
        "folder", "task_name", "owner", "published_version", "table_id",
        "audit_schema" if task_key == "qingcheng.process" else "audit_mode",
    )
    if (any(not _positive_integer(upstream.get(key)) for key in ids)
            or any(not isinstance(upstream.get(key), str) or not upstream[key].strip() for key in text_fields)
            or not re.fullmatch(r"[0-9a-f]{64}", str(upstream.get(source_field, "")))
            or not _positive_integer(record.get("bound_execution_id"))):
        raise ValueError(f"Incomplete or invalid upstream binding: {task_key}")
    interval = record.get("schedule_interval_hours")
    start_minute = record.get("schedule_start_minute")
    anchor_hour = record.get("schedule_anchor_hour")
    target_table = record.get("target_table_id")
    if (not _positive_integer(interval) or 24 % interval
            or type(start_minute) is not int or not 0 <= start_minute < 60
            or type(anchor_hour) is not int or not 0 <= anchor_hour < 24
            or not isinstance(target_table, str) or not target_table.startswith("tbl")
            or record.get("source_hash_algorithm") != "sha256-utf8-ver-getCode"):
        raise ValueError(f"Invalid upstream contract: {task_key}")
    if not market and upstream["table_id"] != target_table:
        raise ValueError(f"Upstream target table differs: {task_key}")
    if not market and "audit_field_count" in upstream:
        supported = (33, 50, 51) if task_key == "qingcheng.process" else (31, 48, 49)
        if type(upstream["audit_field_count"]) is not int or upstream["audit_field_count"] not in supported:
            raise ValueError(f"Invalid upstream audit field count: {task_key}")
    try:
        started = datetime.fromisoformat(record["bound_execution_start"])
        if started.utcoffset() is None:
            raise ValueError("execution timestamp has no timezone")
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid binding execution timestamp: {task_key}") from error
    if task_key == "market_consultant.leads" and not re.fullmatch(
            r"\d{4}", str(record.get("channel_mapping_version", ""))):
        raise ValueError(f"Invalid channel mapping version: {task_key}")
    if task_key == "market_consultant.volume" and record.get("volume_table_id") != target_table:
        raise ValueError(f"Upstream volume table differs: {task_key}")
    return record


def load_binding(task_key, *, expected_domain, config_root=None):
    """Read the current release without a process cache or per-consumer override."""
    record = read_binding_document(task_key, expected_domain=expected_domain, config_root=config_root)
    binding = dict(record["upstream"])
    for field in ("channel_mapping_version", "volume_table_id"):
        if field in record:
            binding[field] = record[field]
    return binding
