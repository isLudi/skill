"""Durable per-slot delivery claims for the local market broadcaster."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
from typing import Any, Mapping


def connect_ledger(state_dir: Path) -> sqlite3.Connection:
    state_dir.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(state_dir / "deliveries.sqlite3", timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.execute("CREATE TABLE IF NOT EXISTS deliveries (key TEXT PRIMARY KEY, slot TEXT, channel TEXT, status TEXT, message_id TEXT, detail TEXT)")
    db.commit()
    return db


def delivery_key(cfg: Mapping[str, Any], slot, channel: str, report_kind: str = "regular") -> str:
    scope = cfg["chat_id"] + "|" + slot.isoformat() + "|" + channel + "|" + report_kind + "|bot"
    if cfg.get("channel_key") and (cfg["channel_key"] != "market_consultant/self_incubated_koc_5"
                                    or cfg.get("target_id") != "gaoyang"):
        scope = cfg["channel_key"] + "|" + cfg["target_id"] + "|" + scope
    return hashlib.sha256(scope.encode()).hexdigest()[:40]


def claim(db: sqlite3.Connection, key: str, slot, channel: str) -> bool:
    cur = db.execute("INSERT OR IGNORE INTO deliveries VALUES (?,?,?,?,?,?)",
                     (key, slot.isoformat(), channel, "sending", "", "{}"))
    db.commit()
    return cur.rowcount == 1
