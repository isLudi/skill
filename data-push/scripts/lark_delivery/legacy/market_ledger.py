"""Legacy JSONL receipt compatibility; scheduled delivery uses SQLite."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping


def _ledger_records(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    result: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, Mapping) and item.get("idempotency_key"):
            result[str(item["idempotency_key"])] = dict(item)
    return result


def _append_ledger(path: Path, item: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(dict(item), ensure_ascii=False, sort_keys=True) + "\n")
