"""Audit the retained SQL corpus without rewriting historical evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sqlglot

from .builder import DOMAIN_CONFIG


def audit_raw_sql(repo_root: Path, exceptions_path: Path) -> dict[str, Any]:
    exceptions = {
        item["source_path"]: item
        for item in json.loads(exceptions_path.read_text(encoding="utf-8")).get("exceptions", [])
    }
    observed_exceptions: set[str] = set()
    unexpected: list[dict[str, str]] = []
    stale_exceptions: list[str] = []
    domains: dict[str, dict[str, int]] = {}
    for domain, config in DOMAIN_CONFIG.items():
        skill_root = repo_root / str(config["skill"])
        counts = {"total": 0, "parsed": 0, "templates": 0, "allowed_legacy_failures": 0}
        for path in sorted((skill_root / "resources" / "raw_sql").rglob("*")):
            if not path.is_file():
                continue
            counts["total"] += 1
            sql = path.read_text(encoding="utf-8-sig")
            source_path = f"{skill_root.name}/{path.relative_to(skill_root).as_posix()}"
            if "${" in sql:
                counts["templates"] += 1
                continue
            try:
                sqlglot.parse(sql, read="presto")
                counts["parsed"] += 1
            except sqlglot.errors.ParseError as exc:
                exception = exceptions.get(source_path)
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if exception and exception.get("sha256") == digest:
                    observed_exceptions.add(source_path)
                    counts["allowed_legacy_failures"] += 1
                else:
                    unexpected.append(
                        {
                            "source_path": source_path,
                            "sha256": digest,
                            "error": str(exc).splitlines()[0],
                        }
                    )
        domains[domain] = counts
    for source_path in sorted(set(exceptions) - observed_exceptions):
        stale_exceptions.append(source_path)
    return {
        "ok": not unexpected and not stale_exceptions,
        "domains": domains,
        "unexpected_failures": unexpected,
        "stale_exceptions": stale_exceptions,
    }

