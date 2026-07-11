"""Reusable cache and staging helpers for edit-profile batch commands."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


FOLDER_DOMAINS = {
    "市场顾问数据": "market_consultant",
    "青橙项目部": "qingcheng",
    "青橙播报": "qingcheng",
}


def resolve_folder_domain(folder: str, requested_domain: str) -> str:
    inferred = FOLDER_DOMAINS.get(folder)
    if requested_domain == "auto":
        if inferred is None:
            raise ValueError(f"Folder `{folder}` has no governed domain mapping; pass --domain explicitly.")
        return inferred
    if inferred is not None and inferred != requested_domain:
        raise ValueError(
            f"Folder `{folder}` belongs to {inferred}, not {requested_domain}; cross-domain edit profiling is blocked."
        )
    return requested_domain


def read_profile(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def reusable_cached_profile(
    path: Path,
    *,
    dashboard_id: str,
    domain: str,
    max_age_seconds: int,
    now: float | None = None,
) -> dict[str, Any] | None:
    profile = read_profile(path)
    if not profile or not profile.get("complete"):
        return None
    if str(profile.get("dashboard_id") or "") != dashboard_id:
        return None
    if str(profile.get("domain") or "") != domain:
        return None
    if max_age_seconds <= 0:
        return None
    age = (now if now is not None else time.time()) - path.stat().st_mtime
    return profile if age <= max_age_seconds else None


def commit_staged_profile(staged: Path, target: Path) -> tuple[str, dict[str, Any]]:
    profile = read_profile(staged)
    if profile is None:
        raise ValueError(f"Staged edit profile is missing or invalid: {staged}")
    existing = read_profile(target)
    staged_hash = str(profile.get("profile_sha256") or "")
    existing_hash = str((existing or {}).get("profile_sha256") or "")
    if staged_hash and existing_hash == staged_hash and bool(profile.get("complete")) == bool((existing or {}).get("complete")):
        staged.unlink(missing_ok=True)
        return "unchanged", existing or profile
    target.parent.mkdir(parents=True, exist_ok=True)
    staged.replace(target)
    return ("updated" if profile.get("complete") else "incomplete"), profile


def commit_staged_normalized(staged: Path, target: Path, profile_status: str) -> None:
    if not staged.is_file():
        return
    if profile_status == "unchanged" and target.is_file():
        staged.unlink(missing_ok=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    staged.replace(target)
