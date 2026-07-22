from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import logging
import logging.handlers
import os
import queue
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import qingcheng_temp_table_sync as workflow


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    workflow.DEFAULT_RUNTIME_ROOT / "event-service" / "config.json"
)
EXAMPLE_CONFIG = SKILL_ROOT / "references" / "event_service_config.example.json"
READY_MARKER = "[event] ready event_key=im.message.receive_v1"
JOB_FIELDS = {
    "action",
    "status",
    "stage",
    "plan_path",
    "plan_sha256",
    "local_receipt_path",
    "local_receipt_sha256",
    "upload_receipt_path",
    "upload_receipt_sha256",
    "error",
    "authorized_by",
}
REPLY_CATEGORIES = {"command", "unknown_command", "source_attachment"}
REPLY_PHASES = {"direct", "progress", "final"}


class ServiceError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ServiceError(f"Cannot read JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ServiceError(f"JSON root must be an object: {path}")
    return value


def resolve_path(value: str | Path, base: Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def load_config(path: Path) -> dict[str, Any]:
    config_path = path.resolve()
    config = read_json(config_path)
    defaults = {
        "schema_version": "1.0.0",
        "mode": "shadow",
        "mention_required": True,
        "bot_names": ["管家"],
        "bot_open_id": None,
        "auto_plan_source_attachments": True,
        "attachment_quiet_seconds": 20,
        "send_replies": False,
        "reply_on_commands": True,
        "reply_on_unknown_commands": False,
        "reply_on_source_attachments": False,
        "reply_progress_updates": False,
        "allow_local_apply": False,
        "allow_production_upload": False,
        "reply_identity": "bot",
        "command_timeout_seconds": 1800,
        "event_ready_timeout_seconds": 30,
        "event_key": "im.message.receive_v1",
        "python_executable": r"D:\anaconda3\python.exe",
        "sync_script": str(SKILL_ROOT / "scripts" / "qingcheng_temp_table_sync.py"),
        "workflow_registry": str(workflow.DEFAULT_REGISTRY),
        "runtime_root": str(workflow.DEFAULT_RUNTIME_ROOT / "event-service"),
        "sync_runtime_root": str(workflow.DEFAULT_RUNTIME_ROOT),
    }
    merged = {**defaults, **config}
    base = config_path.parent
    for key in ("python_executable", "sync_script", "workflow_registry", "runtime_root", "sync_runtime_root"):
        merged[key] = str(resolve_path(merged[key], base))
    required_lists = ("source_sender_ids", "approver_ids", "bot_names")
    for key in required_lists:
        values = merged.get(key)
        if not isinstance(values, list) or not values or not all(isinstance(item, str) and item for item in values):
            raise ServiceError(f"Config field {key} must be a non-empty string list.")
    for key in ("source_sender_ids", "approver_ids"):
        invalid_ids = [value for value in merged[key] if not re.fullmatch(r"ou_[A-Za-z0-9]+", value)]
        if invalid_ids:
            raise ServiceError(f"Config field {key} contains invalid open_id values: {invalid_ids}")
    if merged.get("bot_open_id") is not None and not re.fullmatch(
        r"ou_[A-Za-z0-9]+", str(merged["bot_open_id"])
    ):
        raise ServiceError("Config field bot_open_id must be null or an ou_ id.")
    for key in (
        "mention_required",
        "auto_plan_source_attachments",
        "send_replies",
        "reply_on_commands",
        "reply_on_unknown_commands",
        "reply_on_source_attachments",
        "reply_progress_updates",
        "allow_local_apply",
        "allow_production_upload",
    ):
        if not isinstance(merged[key], bool):
            raise ServiceError(f"Config field {key} must be a JSON boolean.")
    if not re.fullmatch(r"oc_[A-Za-z0-9]+", str(merged.get("chat_id") or "")):
        raise ServiceError("Config field chat_id must be an oc_ id.")
    if merged["mode"] not in {"shadow", "production"}:
        raise ServiceError("Config mode must be shadow or production.")
    if merged["reply_identity"] != "bot":
        raise ServiceError("The persistent service only supports reply_identity=bot.")
    if merged["event_key"] != "im.message.receive_v1":
        raise ServiceError("The persistent service only supports event_key=im.message.receive_v1.")
    for key in ("attachment_quiet_seconds", "command_timeout_seconds", "event_ready_timeout_seconds"):
        if not isinstance(merged[key], int) or merged[key] <= 0:
            raise ServiceError(f"Config field {key} must be a positive integer.")
    if merged["mode"] == "shadow" and (merged["allow_local_apply"] or merged["allow_production_upload"]):
        raise ServiceError("Shadow mode cannot enable local apply or production upload.")
    if merged["allow_production_upload"] and not merged["allow_local_apply"]:
        raise ServiceError("Production upload requires allow_local_apply=true.")
    for key in ("python_executable", "sync_script", "workflow_registry"):
        if not Path(merged[key]).exists():
            raise ServiceError(f"Configured path does not exist: {key}={merged[key]}")
    merged["config_path"] = str(config_path)
    return merged


def configure_logging(runtime_root: Path) -> logging.Logger:
    runtime_root.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("qingcheng_event_service")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.handlers.RotatingFileHandler(
        runtime_root / "service.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


class ServiceLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.stream: Any = None

    def __enter__(self) -> "ServiceLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("a+b")
        self.stream.seek(0, os.SEEK_END)
        if self.stream.tell() == 0:
            self.stream.write(b"0")
            self.stream.flush()
        self.stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.stream.close()
            self.stream = None
            raise ServiceError("Another Qingcheng event service instance is already running.") from exc
        return self

    def __exit__(self, *_: Any) -> None:
        if self.stream is None:
            return
        self.stream.seek(0)
        with contextlib.suppress(OSError):
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        self.stream.close()


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS events (
                    message_id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    message_type TEXT,
                    content TEXT,
                    received_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    request_message_id TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    family_ids TEXT NOT NULL,
                    message_bindings TEXT NOT NULL,
                    plan_path TEXT,
                    plan_sha256 TEXT,
                    local_receipt_path TEXT,
                    local_receipt_sha256 TEXT,
                    upload_receipt_path TEXT,
                    upload_receipt_sha256 TEXT,
                    error TEXT,
                    authorized_by TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS pending_attachments (
                    message_id TEXT PRIMARY KEY,
                    family_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    create_time TEXT,
                    queued_epoch REAL NOT NULL,
                    status TEXT NOT NULL,
                    batch_job_id TEXT
                );
                CREATE TABLE IF NOT EXISTS outbound_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reply_to_message_id TEXT NOT NULL,
                    job_id TEXT,
                    content TEXT NOT NULL,
                    delivery_status TEXT NOT NULL,
                    lark_message_id TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    def claim_event(self, event: dict[str, Any]) -> bool:
        try:
            with self.connect() as connection:
                connection.execute(
                    "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        event["message_id"],
                        event.get("chat_id") or "",
                        event.get("sender_id") or "",
                        event.get("message_type"),
                        str(event.get("content") or ""),
                        now_iso(),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def create_job(
        self,
        *,
        request_message_id: str,
        requester_id: str,
        source: str,
        action: str,
        family_ids: list[str],
        message_bindings: dict[str, str] | None = None,
        authorized_by: str | None = None,
    ) -> str:
        job_id = "qc_" + datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]
        timestamp = now_iso()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id, request_message_id, requester_id, source, action, status, stage,
                    family_ids, message_bindings, authorized_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'queued', 'queued', ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    request_message_id,
                    requester_id,
                    source,
                    action,
                    json.dumps(family_ids, ensure_ascii=False),
                    json.dumps(message_bindings or {}, ensure_ascii=False),
                    authorized_by,
                    timestamp,
                    timestamp,
                ),
            )
        return job_id

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        value = dict(row)
        value["family_ids"] = json.loads(value["family_ids"])
        value["message_bindings"] = json.loads(value["message_bindings"])
        return value

    def update_job(self, job_id: str, **values: Any) -> None:
        unknown = set(values) - JOB_FIELDS
        if unknown:
            raise ServiceError(f"Unsupported job update fields: {sorted(unknown)}")
        values["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in values)
        parameters = [values[key] for key in values]
        with self.connect() as connection:
            cursor = connection.execute(
                f"UPDATE jobs SET {assignments} WHERE job_id = ?",
                [*parameters, job_id],
            )
            if cursor.rowcount != 1:
                raise ServiceError(f"Unknown job id: {job_id}")

    def recent_jobs(self, limit: int = 10) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        values = []
        for row in rows:
            value = dict(row)
            value["family_ids"] = json.loads(value["family_ids"])
            value["message_bindings"] = json.loads(value["message_bindings"])
            values.append(value)
        return values

    def add_pending_attachment(self, event: dict[str, Any], family_id: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO pending_attachments
                (message_id, family_id, sender_id, create_time, queued_epoch, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
                """,
                (
                    event["message_id"],
                    family_id,
                    event.get("sender_id") or "",
                    event.get("create_time"),
                    time.time(),
                ),
            )

    def due_pending_attachments(self, quiet_seconds: int) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM pending_attachments WHERE status = 'pending' ORDER BY queued_epoch, message_id"
            ).fetchall()
        if not rows or time.time() - max(float(row["queued_epoch"]) for row in rows) < quiet_seconds:
            return []
        return [dict(row) for row in rows]

    def mark_pending_batched(self, message_ids: list[str], job_id: str) -> None:
        if not message_ids:
            return
        placeholders = ",".join("?" for _ in message_ids)
        with self.connect() as connection:
            connection.execute(
                f"UPDATE pending_attachments SET status='batched', batch_job_id=? WHERE message_id IN ({placeholders})",
                [job_id, *message_ids],
            )

    def record_outbound(
        self,
        *,
        reply_to: str,
        job_id: str | None,
        content: str,
        status: str,
        lark_message_id: str | None = None,
        error: str | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO outbound_messages
                (reply_to_message_id, job_id, content, delivery_status, lark_message_id, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (reply_to, job_id, content, status, lark_message_id, error, now_iso()),
            )

    def summary(self) -> dict[str, Any]:
        with self.connect() as connection:
            job_counts = {
                row["status"]: row["count"]
                for row in connection.execute(
                    "SELECT status, COUNT(*) AS count FROM jobs GROUP BY status"
                ).fetchall()
            }
            pending = connection.execute(
                "SELECT COUNT(*) AS count FROM pending_attachments WHERE status='pending'"
            ).fetchone()["count"]
            outbound_counts = {
                row["delivery_status"]: row["count"]
                for row in connection.execute(
                    "SELECT delivery_status, COUNT(*) AS count "
                    "FROM outbound_messages GROUP BY delivery_status"
                ).fetchall()
            }
        return {
            "job_counts": job_counts,
            "pending_attachment_count": pending,
            "outbound_counts": outbound_counts,
        }

    def recover_startup(self) -> list[str]:
        timestamp = now_iso()
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE jobs
                SET status='failed', stage='interrupted',
                    error='Service stopped while this job was running; inspect artifacts before retrying.',
                    updated_at=?
                WHERE status IN ('planning', 'applying_local', 'uploading')
                """,
                (timestamp,),
            )
            rows = connection.execute(
                "SELECT job_id FROM jobs WHERE status='queued' ORDER BY created_at"
            ).fetchall()
        return [row["job_id"] for row in rows]


@dataclass(frozen=True)
class Intent:
    action: str
    family_ids: list[str] | None = None
    job_id: str | None = None
    use_replied_file: bool = False


def extract_xlsx_filename(content: str) -> str | None:
    patterns = (
        r'<file\s+key="[^"]+"\s+name="([^"]+\.xlsx)"\s*/>',
        r'([^\\/:*?"<>|\r\n]+\.xlsx)\b',
    )
    for pattern in patterns:
        match = re.search(pattern, content, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def classify_filename(registry: dict[str, Any], filename: str) -> str | None:
    matches = [
        family["id"]
        for family in registry["families"]
        if any(re.fullmatch(pattern, filename) for pattern in family["source_filename_patterns"])
    ]
    if len(matches) > 1:
        raise ServiceError(f"Filename matches multiple workbook families: {filename} -> {matches}")
    return matches[0] if matches else None


def event_mentions_bot(event: dict[str, Any], config: dict[str, Any]) -> bool:
    bot_open_id = config.get("bot_open_id")
    mentions = event.get("mentions") or []
    if bot_open_id:
        for mention in mentions:
            if isinstance(mention, dict) and bot_open_id in {
                str(mention.get("id") or ""),
                str(mention.get("open_id") or ""),
                str(mention.get("user_id") or ""),
            }:
                return True
    content = str(event.get("content") or "")
    return any(re.search(rf"@?{re.escape(name)}(?:\s|[,:：，]|$)", content) for name in config["bot_names"])


def strip_bot_mentions(content: str, bot_names: list[str]) -> str:
    value = content.strip()
    for name in bot_names:
        value = re.sub(
            rf"^\s*@?{re.escape(name)}\s*[,:：，]?\s*",
            "",
            value,
            count=1,
        )
    return value.strip()


def parse_family_phrase(phrase: str, registry: dict[str, Any]) -> list[str] | None:
    normalized = re.sub(r"[\s,，、]+", "", phrase)
    goal_families = ["personal_period_goal", "team_period_goal", "team_month_goal"]
    if not normalized or normalized in {"最新", "最新临时表", "临时表", "全部", "全部临时表"}:
        return list(registry["upload_order"])
    if normalized in {"最新目标表", "目标表", "三个目标表", "三张目标表"}:
        return goal_families
    aliases = {
        "personal_period_goal": ("个人期度", "个人期次", "个人期度目标表", "个人期次目标表"),
        "team_period_goal": ("团队期度", "团队期次", "团队期度目标表", "团队期次目标表"),
        "team_month_goal": ("团队月度", "团队月度目标表", "月度目标表"),
        "result_architecture": ("全员结果数据架构", "结果数据架构", "全员架构"),
        "period_architecture": ("期次带班架构", "期度带班架构", "带班架构"),
    }
    found = []
    for family_id in registry["upload_order"]:
        if any(alias in normalized for alias in aliases[family_id]):
            found.append(family_id)
    if not found and normalized in {"架构", "两个架构", "两张架构"}:
        found = ["result_architecture", "period_architecture"]
    return found or None


def parse_command(content: str, config: dict[str, Any], registry: dict[str, Any]) -> Intent:
    command = strip_bot_mentions(content, config["bot_names"])
    if command in {"帮助", "help", "?", "？"}:
        return Intent("help")
    match = re.fullmatch(r"状态(?:\s+(qc_[A-Za-z0-9_]+))?", command)
    if match:
        return Intent("status", job_id=match.group(1))
    match = re.fullmatch(r"取消\s+(qc_[A-Za-z0-9_]+)", command)
    if match:
        return Intent("cancel", job_id=match.group(1))
    match = re.fullmatch(r"确认上传\s+(qc_[A-Za-z0-9_]+)", command)
    if match:
        return Intent("approve", job_id=match.group(1))
    if command in {"预检此文件", "检查此文件"}:
        return Intent("plan", use_replied_file=True)
    if command == "上传此文件":
        return Intent("upload", use_replied_file=True)
    match = re.fullmatch(r"(?:预检|检查|生成计划)(.*)", command)
    if match:
        families = parse_family_phrase(match.group(1), registry)
        return Intent("plan", family_ids=families) if families else Intent("unknown")
    match = re.fullmatch(r"上传(.*)", command)
    if match:
        families = parse_family_phrase(match.group(1), registry)
        return Intent("upload", family_ids=families) if families else Intent("unknown")
    return Intent("unknown")


def public_error_code(job_id: str, error: BaseException | str) -> str:
    if isinstance(error, BaseException):
        detail = f"{type(error).__name__}:{error}"
    else:
        detail = str(error)
    digest = hashlib.sha256(f"{job_id}:{detail}".encode("utf-8")).hexdigest()[:10]
    return "QC-" + digest.upper()


def stored_public_error_code(job: dict[str, Any]) -> str:
    raw_error = str(job.get("error") or "")
    with contextlib.suppress(json.JSONDecodeError, TypeError):
        value = json.loads(raw_error)
        if isinstance(value, dict) and isinstance(value.get("public_code"), str):
            return value["public_code"]
    return public_error_code(str(job["job_id"]), raw_error)


def job_reply_category(job: dict[str, Any]) -> str:
    return "source_attachment" if job.get("source") == "source_attachment_batch" else "command"


def help_text(config: dict[str, Any]) -> str:
    mode = config["mode"]
    return (
        f"青橙临时表管家（当前模式：{mode}）\n"
        "可用指令：\n"
        "- @管家 预检最新临时表\n"
        "- @管家 预检最新目标表\n"
        "- @管家 预检 个人期度 团队期度 团队月度\n"
        "- 回复一个源附件并 @管家 预检此文件\n"
        "- @管家 状态 [job_id]\n"
        "- @管家 取消 <job_id>\n"
        "- 审批人：@管家 确认上传 <job_id>\n"
        "- 审批人：@管家 上传最新临时表\n"
        "shadow 模式只生成计划，不修改本地表、不上传平台。"
    )


class LarkGateway:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.cli = workflow.resolve_lark_cli()

    def get_message(self, message_id: str) -> dict[str, Any]:
        payload = workflow.run_json_command(
            self.cli,
            [
                "im",
                "+messages-mget",
                "--message-ids",
                message_id,
                "--no-reactions",
                "--as",
                "bot",
                "--format",
                "json",
            ],
            timeout=60,
        )
        messages = payload.get("data", {}).get("messages", [])
        if len(messages) != 1:
            raise ServiceError(f"Expected one replied-to message, found {len(messages)}.")
        return messages[0]

    def reply(self, message_id: str, content: str, idempotency_key: str) -> dict[str, Any]:
        reply_content = json.dumps(
            {"text": content},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return workflow.run_json_command(
            self.cli,
            [
                "im",
                "+messages-reply",
                "--message-id",
                message_id,
                "--as",
                "bot",
                "--idempotency-key",
                idempotency_key[:50],
                "--format",
                "json",
                "--msg-type",
                "text",
                "--content",
                reply_content,
            ],
            timeout=60,
        )


class ReplyDispatcher:
    def __init__(
        self,
        config: dict[str, Any],
        ledger: Ledger,
        gateway: LarkGateway | None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.config = config
        self.ledger = ledger
        self.gateway = gateway
        self.logger = logger or logging.getLogger("qingcheng_event_service")

    def _suppression_reason(self, category: str, phase: str) -> str | None:
        if category not in REPLY_CATEGORIES:
            raise ServiceError(f"Unsupported reply category: {category}")
        if phase not in REPLY_PHASES:
            raise ServiceError(f"Unsupported reply phase: {phase}")
        if not self.config["send_replies"]:
            return "send_replies_disabled"
        if category == "command" and not self.config["reply_on_commands"]:
            return "command_replies_disabled"
        if category == "unknown_command" and (
            not self.config["reply_on_commands"]
            or not self.config["reply_on_unknown_commands"]
        ):
            return "unknown_command_replies_disabled"
        if category == "source_attachment" and not self.config["reply_on_source_attachments"]:
            return "source_attachment_replies_disabled"
        if phase == "progress" and not self.config["reply_progress_updates"]:
            return "progress_replies_disabled"
        if self.gateway is None:
            return "reply_gateway_unavailable"
        return None

    def send(
        self,
        reply_to: str,
        content: str,
        *,
        job_id: str | None = None,
        suffix: str = "reply",
        category: str = "command",
        phase: str = "direct",
    ) -> str:
        suppression_reason = self._suppression_reason(category, phase)
        if suppression_reason is not None:
            self.ledger.record_outbound(
                reply_to=reply_to,
                job_id=job_id,
                content=content,
                status="suppressed",
                error=suppression_reason,
            )
            return "suppressed"
        key_source = f"{reply_to}:{job_id or ''}:{suffix}"
        key = "qc-" + hashlib.sha256(key_source.encode("utf-8")).hexdigest()[:32]
        try:
            assert self.gateway is not None
            payload = self.gateway.reply(reply_to, content, key)
            data = payload.get("data") or {}
            self.ledger.record_outbound(
                reply_to=reply_to,
                job_id=job_id,
                content=content,
                status="sent",
                lark_message_id=data.get("message_id"),
            )
            return "sent"
        except Exception as exc:  # noqa: BLE001
            self.ledger.record_outbound(
                reply_to=reply_to,
                job_id=job_id,
                content=content,
                status="failed",
                error=str(exc),
            )
            self.logger.warning(
                "Bot reply delivery failed reply_to=%s job_id=%s category=%s phase=%s: %s",
                reply_to,
                job_id,
                category,
                phase,
                exc,
            )
            return "failed"


class LarkEventConsumer:
    def __init__(self, config: dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self.process: subprocess.Popen[str] | None = None
        self.stdout_queue: queue.Queue[str | None] = queue.Queue()
        self.stderr_queue: queue.Queue[str | None] = queue.Queue()

    @staticmethod
    def _pump(stream: Any, destination: queue.Queue[str | None]) -> None:
        try:
            for line in iter(stream.readline, ""):
                destination.put(line.rstrip("\r\n"))
        finally:
            destination.put(None)

    def start(self) -> None:
        cli = workflow.resolve_lark_cli()
        argv = workflow._command_argv(
            cli,
            ["event", "consume", self.config["event_key"], "--as", "bot"],
        )
        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
                "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1",
                "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1",
            }
        )
        self.process = subprocess.Popen(
            argv,
            cwd=str(SKILL_ROOT),
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert self.process.stdout is not None and self.process.stderr is not None
        threading.Thread(target=self._pump, args=(self.process.stdout, self.stdout_queue), daemon=True).start()
        threading.Thread(target=self._pump, args=(self.process.stderr, self.stderr_queue), daemon=True).start()
        deadline = time.monotonic() + self.config["event_ready_timeout_seconds"]
        diagnostics = []
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                break
            try:
                line = self.stderr_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if line is None:
                break
            diagnostics.append(line)
            self.logger.info("lark-event: %s", line)
            if READY_MARKER in line:
                return
        self.close()
        raise ServiceError("lark-event did not become ready: " + " | ".join(diagnostics[-10:]))

    def get(self, timeout: float = 1.0) -> dict[str, Any] | None:
        if self.process is None:
            raise ServiceError("Event consumer has not been started.")
        while True:
            with contextlib.suppress(queue.Empty):
                diagnostic = self.stderr_queue.get_nowait()
                if diagnostic:
                    self.logger.info("lark-event: %s", diagnostic)
            try:
                line = self.stdout_queue.get(timeout=timeout)
            except queue.Empty:
                if self.process.poll() is not None:
                    raise ServiceError(f"lark-event exited unexpectedly with code {self.process.returncode}.")
                return None
            if line is None:
                if self.process.poll() is not None:
                    raise ServiceError(f"lark-event stdout closed with code {self.process.returncode}.")
                return None
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                self.logger.warning("Ignoring non-JSON event output: %s", line[:500])
                continue
            if not isinstance(value, dict):
                self.logger.warning("Ignoring event whose JSON root is not an object.")
                continue
            return value

    def close(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None and self.process.stdin is not None:
            with contextlib.suppress(OSError):
                self.process.stdin.close()
        try:
            self.process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.logger.warning("lark-event ignored stdin EOF; sending terminate.")
            self.process.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                self.process.wait(timeout=10)
        self.process = None


class SyncExecutor:
    def __init__(
        self,
        config: dict[str, Any],
        ledger: Ledger,
        replies: ReplyDispatcher,
        logger: logging.Logger,
    ) -> None:
        self.config = config
        self.ledger = ledger
        self.replies = replies
        self.logger = logger

    def _run(self, arguments: list[str]) -> dict[str, Any]:
        return workflow.run_json_command(
            self.config["python_executable"],
            [self.config["sync_script"], *arguments],
            cwd=SKILL_ROOT,
            timeout=self.config["command_timeout_seconds"],
        )

    def _plan(self, job: dict[str, Any]) -> dict[str, Any]:
        command = [
            "plan",
            "--registry",
            self.config["workflow_registry"],
            "--runtime-root",
            self.config["sync_runtime_root"],
        ]
        for family_id in job["family_ids"]:
            command.extend(["--family", family_id])
        for family_id, message_id in job["message_bindings"].items():
            command.extend(["--message-id", f"{family_id}={message_id}"])
        summary = self._run(command)
        self.ledger.update_job(
            job["job_id"],
            plan_path=summary["plan_path"],
            plan_sha256=summary["plan_sha256"],
        )
        return summary

    def _apply_local(self, job: dict[str, Any]) -> dict[str, Any]:
        summary = self._run(
            [
                "apply-local",
                "--plan",
                job["plan_path"],
                "--expected-plan-sha256",
                job["plan_sha256"],
                "--confirm-local-write",
            ]
        )
        self.ledger.update_job(
            job["job_id"],
            local_receipt_path=summary["receipt_path"],
            local_receipt_sha256=summary["receipt_sha256"],
        )
        return summary

    def _upload(self, job: dict[str, Any]) -> dict[str, Any]:
        summary = self._run(
            [
                "upload",
                "--local-receipt",
                job["local_receipt_path"],
                "--expected-receipt-sha256",
                job["local_receipt_sha256"],
                "--confirm-production-upload",
                "--timeout-seconds",
                str(self.config["command_timeout_seconds"]),
            ]
        )
        self.ledger.update_job(
            job["job_id"],
            upload_receipt_path=summary["receipt_path"],
            upload_receipt_sha256=summary["receipt_sha256"],
        )
        return summary

    def execute(self, job_id: str) -> None:
        job = self.ledger.get_job(job_id)
        if job is None or job["status"] == "cancelled":
            return
        try:
            if not job.get("plan_path"):
                self.ledger.update_job(job_id, status="planning", stage="plan")
                plan_summary = self._plan(job)
                self.logger.info("Job %s plan ready: %s", job_id, plan_summary["plan_path"])
                job = self.ledger.get_job(job_id)
                assert job is not None
            if job["action"] == "plan":
                self.ledger.update_job(job_id, status="planned", stage="awaiting_approval")
                self.replies.send(
                    job["request_message_id"],
                    (
                        f"预检完成：{job_id}\n"
                        f"范围：{', '.join(job['family_ids'])}\n"
                        "状态：planned\n"
                        "如需上传，由审批人发送：@管家 确认上传 " + job_id
                    ),
                    job_id=job_id,
                    suffix="planned",
                    category=job_reply_category(job),
                    phase="final",
                )
                return
            if job["action"] != "upload":
                raise ServiceError(f"Unsupported queued job action: {job['action']}")
            if (
                self.config["mode"] != "production"
                or not self.config["allow_local_apply"]
                or not self.config["allow_production_upload"]
            ):
                raise ServiceError("Production gates are not enabled in the event-service config.")
            if job.get("authorized_by") not in self.config["approver_ids"]:
                raise ServiceError("The production job is not bound to a configured approver.")
            self.ledger.update_job(job_id, status="applying_local", stage="apply_local")
            job = self.ledger.get_job(job_id)
            assert job is not None
            local_summary = self._apply_local(job)
            self.logger.info("Job %s local apply completed: %s", job_id, local_summary["status"])
            self.ledger.update_job(job_id, status="uploading", stage="upload")
            job = self.ledger.get_job(job_id)
            assert job is not None
            upload_summary = self._upload(job)
            self.ledger.update_job(job_id, status="success", stage="complete")
            self.replies.send(
                job["request_message_id"],
                (
                    f"上传完成：{job_id}\n"
                    "状态：success\n"
                    f"已上传：{len(upload_summary.get('uploads', []))} 张临时表。"
                ),
                job_id=job_id,
                suffix="success",
                category=job_reply_category(job),
                phase="final",
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Job %s failed", job_id)
            error_code = public_error_code(job_id, exc)
            self.ledger.update_job(
                job_id,
                status="failed",
                stage="failed",
                error=json.dumps(
                    {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "public_code": error_code,
                    },
                    ensure_ascii=False,
                ),
            )
            job = self.ledger.get_job(job_id)
            if job:
                with contextlib.suppress(Exception):
                    self.replies.send(
                        job["request_message_id"],
                        (
                            f"任务失败：{job_id}\n"
                            f"错误编号：{error_code}\n"
                            "详细原因已记录在本机任务账本和日志中。"
                        ),
                        job_id=job_id,
                        suffix="failed",
                        category=job_reply_category(job),
                        phase="final",
                    )


class JobWorker:
    def __init__(self, executor: SyncExecutor, logger: logging.Logger) -> None:
        self.executor = executor
        self.logger = logger
        self.queue: queue.Queue[str | None] = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, name="qingcheng-job-worker", daemon=False)

    def start(self) -> None:
        self.thread.start()

    def submit(self, job_id: str) -> None:
        self.queue.put(job_id)

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                job_id = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                if job_id is None:
                    return
                self.executor.execute(job_id)
            finally:
                self.queue.task_done()

    def close(self) -> None:
        self.stop_event.set()
        self.queue.put(None)
        self.thread.join()


class EventProcessor:
    def __init__(
        self,
        config: dict[str, Any],
        registry: dict[str, Any],
        ledger: Ledger,
        replies: ReplyDispatcher,
        worker: JobWorker | None,
        gateway: LarkGateway | None,
        logger: logging.Logger,
    ) -> None:
        self.config = config
        self.registry = registry
        self.ledger = ledger
        self.replies = replies
        self.worker = worker
        self.gateway = gateway
        self.logger = logger

    def _submit(self, job_id: str) -> None:
        if self.worker is not None:
            self.worker.submit(job_id)

    def _reply_job_status(self, event: dict[str, Any], job_id: str | None) -> None:
        if job_id:
            job = self.ledger.get_job(job_id)
            if job is None:
                text = f"未找到任务：{job_id}"
            else:
                text = (
                    f"任务：{job_id}\n状态：{job['status']}\n阶段：{job['stage']}\n"
                    f"范围：{', '.join(job['family_ids'])}"
                )
                if job.get("error"):
                    text += "\n错误编号：" + stored_public_error_code(job)
        else:
            jobs = self.ledger.recent_jobs(5)
            text = "最近任务：\n" + "\n".join(
                f"- {job['job_id']} | {job['status']} | {','.join(job['family_ids'])}"
                for job in jobs
            ) if jobs else "当前没有任务记录。"
        self.replies.send(
            event["message_id"],
            text,
            suffix="status",
            category="command",
            phase="direct",
        )

    def _resolve_replied_file(self, event: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
        replied_id = event.get("reply_to")
        if not replied_id:
            raise ServiceError("“此文件”指令必须回复一条 Excel 附件消息。")
        if self.gateway is None:
            raise ServiceError("Offline processor cannot resolve the replied-to message.")
        message = self.gateway.get_message(str(replied_id))
        sender = message.get("sender") or {}
        sender_id = sender.get("id") or sender.get("open_id")
        if sender_id not in self.config["source_sender_ids"]:
            raise ServiceError("Replied-to attachment was not posted by an allowed source sender.")
        if message.get("chat_id") and message.get("chat_id") != self.config["chat_id"]:
            raise ServiceError("Replied-to attachment is outside the configured chat.")
        filename = extract_xlsx_filename(str(message.get("content") or ""))
        family_id = classify_filename(self.registry, filename or "") if filename else None
        if family_id is None:
            raise ServiceError("Replied-to message is not a recognized Qingcheng Excel source file.")
        return [family_id], {family_id: str(replied_id)}

    def _deny(self, event: dict[str, Any], text: str) -> None:
        self.replies.send(
            event["message_id"],
            text,
            suffix="denied",
            category="command",
            phase="direct",
        )

    def process(self, event: dict[str, Any]) -> str:
        if event.get("chat_id") != self.config["chat_id"]:
            return "ignored_chat"
        message_id = str(event.get("message_id") or "")
        sender_id = str(event.get("sender_id") or "")
        if not re.fullmatch(r"om_[A-Za-z0-9]+", message_id) or not sender_id:
            return "ignored_invalid"
        if event.get("sender_type") in {"app", "bot"}:
            return "ignored_bot"
        if not self.ledger.claim_event(event):
            return "duplicate"
        content = str(event.get("content") or "")
        if (
            self.config["auto_plan_source_attachments"]
            and sender_id in self.config["source_sender_ids"]
            and event.get("message_type") == "file"
        ):
            filename = extract_xlsx_filename(content)
            family_id = classify_filename(self.registry, filename or "") if filename else None
            if family_id:
                self.ledger.add_pending_attachment(event, family_id)
                self.logger.info("Queued source attachment %s as %s", message_id, family_id)
                return "attachment_queued"
        if event.get("message_type") not in {"text", "post"}:
            return "ignored_type"
        if self.config["mention_required"] and not event_mentions_bot(event, self.config):
            return "ignored_no_mention"
        intent = parse_command(content, self.config, self.registry)
        if intent.action == "help":
            self.replies.send(
                message_id,
                help_text(self.config),
                suffix="help",
                category="command",
                phase="direct",
            )
            return "help"
        if intent.action == "unknown":
            self.replies.send(
                message_id,
                "无法识别该指令。发送“@管家 帮助”查看固定指令。",
                suffix="unknown",
                category="unknown_command",
                phase="direct",
            )
            return "unknown"
        if intent.action == "status":
            self._reply_job_status(event, intent.job_id)
            return "status"
        if intent.action == "cancel":
            job = self.ledger.get_job(intent.job_id or "")
            if job is None:
                self._deny(event, f"未找到任务：{intent.job_id}")
                return "cancel_missing"
            if sender_id != job["requester_id"] and sender_id not in self.config["approver_ids"]:
                self._deny(event, "只有任务发起人或审批人可以取消任务。")
                return "cancel_denied"
            if job["status"] not in {"queued", "planned"}:
                self._deny(event, f"任务处于 {job['status']}，不能取消。")
                return "cancel_conflict"
            self.ledger.update_job(intent.job_id or "", status="cancelled", stage="cancelled")
            self.replies.send(
                message_id,
                f"已取消：{intent.job_id}",
                job_id=intent.job_id,
                suffix="cancel",
                category="command",
                phase="final",
            )
            return "cancelled"
        if intent.action == "approve":
            if sender_id not in self.config["approver_ids"]:
                self._deny(event, "只有配置中的审批人可以确认生产上传。")
                return "approve_denied"
            if (
                self.config["mode"] != "production"
                or not self.config["allow_local_apply"]
                or not self.config["allow_production_upload"]
            ):
                self._deny(event, "当前服务未启用生产写入门禁；该指令不会修改本地表或平台。")
                return "approve_gated"
            job = self.ledger.get_job(intent.job_id or "")
            if job is None or job["status"] != "planned":
                self._deny(event, f"任务不存在或不处于 planned：{intent.job_id}")
                return "approve_conflict"
            self.ledger.update_job(
                intent.job_id or "",
                action="upload",
                status="queued",
                stage="queued_apply",
                authorized_by=sender_id,
            )
            self._submit(intent.job_id or "")
            self.replies.send(
                message_id,
                f"已确认生产上传：{intent.job_id}",
                job_id=intent.job_id,
                suffix="approved",
                category="command",
                phase="progress",
            )
            return "approved"
        if intent.action not in {"plan", "upload"}:
            self._deny(event, "无法识别该指令。")
            return "unknown"
        try:
            if intent.use_replied_file:
                family_ids, bindings = self._resolve_replied_file(event)
            else:
                family_ids = intent.family_ids or list(self.registry["upload_order"])
                bindings = {}
        except Exception as exc:  # noqa: BLE001
            error_code = public_error_code(message_id, exc)
            self.logger.exception(
                "Reply-bound source resolution failed message_id=%s public_code=%s",
                message_id,
                error_code,
            )
            self._deny(
                event,
                "无法安全读取或校验被回复的附件。\n"
                f"错误编号：{error_code}\n"
                "详细原因已记录在本机日志中。",
            )
            return "reply_file_error"
        action = intent.action
        authorized_by = None
        shadow_note = ""
        if action == "upload":
            if sender_id not in self.config["approver_ids"]:
                self._deny(event, "只有配置中的审批人可以发起生产上传；你可以使用“预检”生成计划。")
                return "upload_denied"
            if (
                self.config["mode"] != "production"
                or not self.config["allow_local_apply"]
                or not self.config["allow_production_upload"]
            ):
                action = "plan"
                shadow_note = "当前为 shadow/未启用生产门禁，本次仅生成计划。\n"
            else:
                authorized_by = sender_id
        job_id = self.ledger.create_job(
            request_message_id=message_id,
            requester_id=sender_id,
            source="chat_command",
            action=action,
            family_ids=family_ids,
            message_bindings=bindings,
            authorized_by=authorized_by,
        )
        self._submit(job_id)
        self.replies.send(
            message_id,
            shadow_note + f"已受理：{job_id}\n范围：{', '.join(family_ids)}",
            job_id=job_id,
            suffix="accepted",
            category="command",
            phase="progress",
        )
        return "job_queued"

    def flush_pending(self) -> str | None:
        pending = self.ledger.due_pending_attachments(self.config["attachment_quiet_seconds"])
        if not pending:
            return None
        latest_by_family: dict[str, dict[str, Any]] = {}
        for item in pending:
            existing = latest_by_family.get(item["family_id"])
            if existing is None or (str(item.get("create_time") or ""), item["message_id"]) > (
                str(existing.get("create_time") or ""),
                existing["message_id"],
            ):
                latest_by_family[item["family_id"]] = item
        family_ids = [
            family_id for family_id in self.registry["upload_order"] if family_id in latest_by_family
        ]
        bindings = {family_id: latest_by_family[family_id]["message_id"] for family_id in family_ids}
        reply_item = max(pending, key=lambda item: (item["queued_epoch"], item["message_id"]))
        job_id = self.ledger.create_job(
            request_message_id=reply_item["message_id"],
            requester_id=reply_item["sender_id"],
            source="source_attachment_batch",
            action="plan",
            family_ids=family_ids,
            message_bindings=bindings,
        )
        self.ledger.mark_pending_batched([item["message_id"] for item in pending], job_id)
        self._submit(job_id)
        self.replies.send(
            reply_item["message_id"],
            f"已识别并开始预检：{job_id}\n范围：{', '.join(family_ids)}",
            job_id=job_id,
            suffix="attachment_batch",
            category="source_attachment",
            phase="progress",
        )
        return job_id


class QingchengEventService:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.runtime_root = Path(config["runtime_root"])
        self.logger = configure_logging(self.runtime_root)
        self.ledger = Ledger(self.runtime_root / "jobs.sqlite3")
        self.status_path = self.runtime_root / "status.json"
        self.stop_path = self.runtime_root / "stop.request"
        self.lock_path = self.runtime_root / "service.lock"
        self.stop_event = threading.Event()
        self.consumer: LarkEventConsumer | None = None
        self.worker: JobWorker | None = None

    def write_status(self, status: str, **extra: Any) -> None:
        value = {
            "schema_version": "1.0.0",
            "status": status,
            "pid": os.getpid(),
            "mode": self.config["mode"],
            "send_replies": self.config["send_replies"],
            "reply_on_commands": self.config["reply_on_commands"],
            "reply_on_unknown_commands": self.config["reply_on_unknown_commands"],
            "reply_on_source_attachments": self.config["reply_on_source_attachments"],
            "reply_progress_updates": self.config["reply_progress_updates"],
            "allow_local_apply": self.config["allow_local_apply"],
            "allow_production_upload": self.config["allow_production_upload"],
            "config_path": self.config["config_path"],
            "updated_at": now_iso(),
            "ledger": self.ledger.summary(),
            **extra,
        }
        atomic_write_json(self.status_path, value)

    def request_stop(self, *_: Any) -> None:
        self.stop_event.set()

    def run(self) -> int:
        with ServiceLock(self.lock_path):
            self.stop_path.unlink(missing_ok=True)
            self.write_status("starting")
            gateway = LarkGateway(self.config)
            replies = ReplyDispatcher(self.config, self.ledger, gateway, self.logger)
            executor = SyncExecutor(self.config, self.ledger, replies, self.logger)
            self.worker = JobWorker(executor, self.logger)
            registry = workflow.load_registry(Path(self.config["workflow_registry"]))
            processor = EventProcessor(
                self.config,
                registry,
                self.ledger,
                replies,
                self.worker,
                gateway,
                self.logger,
            )
            self.consumer = LarkEventConsumer(self.config, self.logger)
            signal.signal(signal.SIGINT, self.request_stop)
            signal.signal(signal.SIGTERM, self.request_stop)
            try:
                self.consumer.start()
                self.worker.start()
                for job_id in self.ledger.recover_startup():
                    self.worker.submit(job_id)
                self.write_status("running", event_ready=True)
                self.logger.info(
                    "Qingcheng event service is running in %s mode for chat %s",
                    self.config["mode"],
                    self.config["chat_id"],
                )
                last_status = 0.0
                while not self.stop_event.is_set():
                    if self.stop_path.exists():
                        self.stop_event.set()
                        break
                    event = self.consumer.get(timeout=1.0)
                    if event is not None:
                        result = processor.process(event)
                        self.logger.info(
                            "Processed event message_id=%s result=%s",
                            event.get("message_id"),
                            result,
                        )
                    processor.flush_pending()
                    if time.monotonic() - last_status >= 5:
                        self.write_status("running", event_ready=True)
                        last_status = time.monotonic()
                self.write_status("stopping", event_ready=True)
                return 0
            except Exception as exc:
                self.logger.exception("Event service failed")
                self.write_status(
                    "failed",
                    event_ready=False,
                    error={"type": type(exc).__name__, "message": str(exc)},
                )
                raise
            finally:
                if self.consumer is not None:
                    self.consumer.close()
                if self.worker is not None:
                    self.worker.close()
                self.stop_path.unlink(missing_ok=True)
                current = read_json(self.status_path) if self.status_path.exists() else {}
                if current.get("status") != "failed":
                    self.write_status("stopped", event_ready=False)
                self.logger.info("Qingcheng event service stopped.")


def initialize_config(output: Path, force: bool) -> dict[str, Any]:
    target = output.resolve()
    if target.exists() and not force:
        raise ServiceError(f"Config already exists: {target}; use --force to replace it.")
    config = read_json(EXAMPLE_CONFIG)
    atomic_write_json(target, config)
    return {"ok": True, "config_path": str(target), "mode": config.get("mode")}


def status_summary(config: dict[str, Any]) -> dict[str, Any]:
    runtime_root = Path(config["runtime_root"])
    ledger = Ledger(runtime_root / "jobs.sqlite3")
    status_path = runtime_root / "status.json"
    return {
        "ok": True,
        "config_path": config["config_path"],
        "mode": config["mode"],
        "status": read_json(status_path) if status_path.exists() else {"status": "not_started"},
        "ledger": ledger.summary(),
        "recent_jobs": ledger.recent_jobs(10),
        "paths": {
            "runtime_root": str(runtime_root),
            "status": str(status_path),
            "ledger": str(ledger.path),
            "log": str(runtime_root / "service.log"),
        },
    }


def process_event_offline(config: dict[str, Any], event_file: Path) -> dict[str, Any]:
    offline_root = (
        Path(config["runtime_root"])
        / "offline-events"
        / (datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{os.getpid()}")
    )
    safe_config = {
        **config,
        "mode": "shadow",
        "send_replies": False,
        "allow_local_apply": False,
        "allow_production_upload": False,
        "runtime_root": str(offline_root),
    }
    runtime_root = Path(safe_config["runtime_root"])
    logger = configure_logging(runtime_root)
    ledger = Ledger(runtime_root / "jobs.sqlite3")
    replies = ReplyDispatcher(safe_config, ledger, None, logger)
    registry = workflow.load_registry(Path(safe_config["workflow_registry"]))
    processor = EventProcessor(safe_config, registry, ledger, replies, None, None, logger)
    event = read_json(event_file.resolve())
    result = processor.process(event)
    return {
        "ok": True,
        "result": result,
        "ledger": ledger.summary(),
        "recent_jobs": ledger.recent_jobs(5),
        "external_messages_sent": False,
        "local_apply_performed": False,
        "production_upload_performed": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Persistent Feishu event service for the governed Qingcheng temp-table workflow."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run the persistent lark-event consumer in the foreground.")
    run.add_argument("--config", type=Path, default=DEFAULT_CONFIG)

    validate = subparsers.add_parser("validate-config", help="Validate configuration without starting lark-event.")
    validate.add_argument("--config", type=Path, default=DEFAULT_CONFIG)

    status = subparsers.add_parser("status", help="Read service status and the recent job ledger.")
    status.add_argument("--config", type=Path, default=DEFAULT_CONFIG)

    initialize = subparsers.add_parser("init-config", help="Create a runtime config from the safe example.")
    initialize.add_argument("--output", type=Path, default=DEFAULT_CONFIG)
    initialize.add_argument("--force", action="store_true")

    offline = subparsers.add_parser(
        "process-event",
        help="Process one saved event in forced shadow mode without Lark replies or job execution.",
    )
    offline.add_argument("--config", type=Path, required=True)
    offline.add_argument("--event-file", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init-config":
            result = initialize_config(args.output, args.force)
        else:
            config = load_config(args.config)
            if args.command == "validate-config":
                result = {
                    "ok": True,
                    "config_path": config["config_path"],
                    "mode": config["mode"],
                    "chat_id": config["chat_id"],
                    "send_replies": config["send_replies"],
                    "reply_on_commands": config["reply_on_commands"],
                    "reply_on_unknown_commands": config["reply_on_unknown_commands"],
                    "reply_on_source_attachments": config["reply_on_source_attachments"],
                    "reply_progress_updates": config["reply_progress_updates"],
                    "allow_local_apply": config["allow_local_apply"],
                    "allow_production_upload": config["allow_production_upload"],
                }
            elif args.command == "status":
                result = status_summary(config)
            elif args.command == "process-event":
                result = process_event_offline(config, args.event_file)
            elif args.command == "run":
                return QingchengEventService(config).run()
            else:
                raise ServiceError(f"Unsupported command: {args.command}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ServiceError, workflow.WorkflowError) as exc:
        print(
            json.dumps(
                {"ok": False, "error": {"type": type(exc).__name__, "message": str(exc)}},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
