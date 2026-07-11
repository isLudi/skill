"""Profile Taitan edit pages in bounded isolated subprocesses with resume support."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import parse_dashboard_names, write_json
from ..constants import DASHBOARD_MARKET_URL, DEFAULT_PROFILE_EDIT_ALL_FOLDERS
from ..edit_batch import (
    commit_staged_normalized,
    commit_staged_profile,
    resolve_folder_domain,
    reusable_cached_profile,
)
from ..menu import collect_dashboard_records, fetch_dashboard_menu


def _scan_targets(args, folders: list[str]) -> list[dict[str, str]]:
    sync_playwright = import_playwright()
    targets: list[dict[str, str]] = []
    wanted_names = set(parse_dashboard_names(getattr(args, "names", None)))
    with sync_playwright() as playwright:
        browser, context = launch_context(
            playwright,
            args.state_path,
            args.headed,
            args.browser_channel,
            args.executable_path,
        )
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            for folder in folders:
                domain = resolve_folder_domain(folder, args.domain)
                page.goto(DASHBOARD_MARKET_URL, wait_until="domcontentloaded", timeout=45_000)
                page.wait_for_timeout(args.scan_wait_ms)
                records = collect_dashboard_records(fetch_dashboard_menu(page), folder)
                selected = [record for record in records if not wanted_names or record.name in wanted_names]
                for record in selected:
                    if not record.dashboard_id or record.dashboard_id.startswith("home_"):
                        continue
                    targets.append(
                        {
                            "folder": folder,
                            "domain": domain,
                            "dashboard_name": record.name,
                            "dashboard_id": record.dashboard_id,
                        }
                    )
                if wanted_names:
                    found = {record.name for record in selected}
                    missing = sorted(wanted_names - found)
                    if missing:
                        raise UsageError(f"Dashboard names not found in `{folder}`: {', '.join(missing)}")
        finally:
            browser.close()
    deduped = {item["dashboard_id"]: item for item in targets}
    return [deduped[key] for key in sorted(deduped)]


def _worker_command(args, task: dict[str, str], staged_rich: Path, staged_normalized: Path) -> list[str]:
    entrypoint = Path(__file__).resolve().parents[2] / "read_dashboard.py"
    command = [
        sys.executable,
        str(entrypoint),
        "profile-edit-dashboard",
        "--dashboard-id",
        task["dashboard_id"],
        "--domain",
        task["domain"],
        "--version-id",
        args.version_id,
        "--wait-ms",
        str(args.wait_ms),
        "--output",
        str(staged_rich),
        "--normalized-output",
        str(staged_normalized),
        "--state-path",
        str(args.state_path),
        "--artifacts-dir",
        str(args.artifacts_dir / "edit-batch" / task["dashboard_id"]),
        "--browser-channel",
        args.browser_channel,
    ]
    if args.env_file:
        command.extend(["--env-file", str(args.env_file)])
    if args.executable_path:
        command.extend(["--executable-path", str(args.executable_path)])
    if args.headed:
        command.append("--headed")
    if args.skip_dataset_fields:
        command.append("--skip-dataset-fields")
    if args.debug_artifacts:
        command.append("--debug-artifacts")
    return command


def _run_task(args, task: dict[str, str], output_dir: Path) -> dict[str, Any]:
    dashboard_id = task["dashboard_id"]
    target_rich = output_dir / f"{dashboard_id}_edit_profile.json"
    target_normalized = output_dir / f"{dashboard_id}_normalized.json"
    if args.resume:
        cached = reusable_cached_profile(
            target_rich,
            dashboard_id=dashboard_id,
            domain=task["domain"],
            max_age_seconds=args.resume_max_age_seconds,
        )
        if cached is not None:
            return {
                **task,
                "ok": True,
                "status": "cached",
                "complete": True,
                "profile_sha256": cached.get("profile_sha256"),
                "output_path": str(target_rich),
                "elapsed_seconds": 0.0,
            }

    staging = output_dir / ".staging"
    staging.mkdir(parents=True, exist_ok=True)
    staged_rich = staging / f"{dashboard_id}_edit_profile.json"
    staged_normalized = staging / f"{dashboard_id}_normalized.json"
    staged_rich.unlink(missing_ok=True)
    staged_normalized.unlink(missing_ok=True)
    started = time.monotonic()
    completed = subprocess.run(
        _worker_command(args, task, staged_rich, staged_normalized),
        cwd=str(Path(__file__).resolve().parents[3]),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=args.worker_timeout_seconds,
    )
    elapsed = round(time.monotonic() - started, 3)
    if not staged_rich.is_file():
        tail = ((completed.stdout or "") + "\n" + (completed.stderr or ""))[-1000:]
        return {
            **task,
            "ok": False,
            "status": "failed",
            "complete": False,
            "message": tail.strip() or f"Worker exited with {completed.returncode}.",
            "elapsed_seconds": elapsed,
        }
    status, profile = commit_staged_profile(staged_rich, target_rich)
    commit_staged_normalized(staged_normalized, target_normalized, status)
    return {
        **task,
        "ok": bool(profile.get("complete")),
        "status": status,
        "complete": bool(profile.get("complete")),
        "profile_sha256": profile.get("profile_sha256"),
        "output_path": str(target_rich),
        "normalized_output_path": str(target_normalized) if target_normalized.is_file() else None,
        "return_code": completed.returncode,
        "elapsed_seconds": elapsed,
        "message": profile.get("message"),
    }


def _cmd_profile_edit_batch(args, folders: list[str]) -> int:
    load_env_file(args.env_file)
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    output_dir = args.output_dir or safe_artifact_dir(args.artifacts_dir) / "edit-batch"
    output_dir.mkdir(parents=True, exist_ok=True)
    targets = _scan_targets(args, folders)
    if not targets:
        raise UsageError("No editable dashboard targets were found.")
    max_workers = max(1, min(int(args.max_workers), 4, len(targets)))
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_task, args, task, output_dir): task for task in targets}
        for future in as_completed(futures):
            task = futures[future]
            try:
                results.append(future.result())
            except subprocess.TimeoutExpired:
                results.append(
                    {
                        **task,
                        "ok": False,
                        "status": "worker_timeout",
                        "complete": False,
                        "message": f"Edit-profile worker exceeded {args.worker_timeout_seconds} seconds.",
                    }
                )
            except Exception as exc:  # noqa: BLE001
                results.append({**task, "ok": False, "status": "failed", "complete": False, "message": str(exc)})
    results.sort(key=lambda item: (item["folder"], item["dashboard_name"]))
    summary = {
        "schema_version": "1.0.0",
        "artifact_type": "DashboardEditProfileBatch",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "folders": folders,
        "output_dir": str(output_dir),
        "max_workers": max_workers,
        "resume": bool(args.resume),
        "resume_max_age_seconds": args.resume_max_age_seconds,
        "target_count": len(targets),
        "ok_count": sum(1 for item in results if item.get("ok")),
        "status_counts": {
            status: sum(1 for item in results if item.get("status") == status)
            for status in sorted({str(item.get("status")) for item in results})
        },
        "results": results,
    }
    manifest_path = output_dir / "edit_profile_batch_manifest.json"
    write_json(summary, manifest_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all(item.get("ok") for item in results) else 1


def cmd_profile_edit_folder(args) -> int:
    return _cmd_profile_edit_batch(args, [args.folder])


def cmd_profile_edit_all(args) -> int:
    folders = parse_dashboard_names(args.folders) or list(DEFAULT_PROFILE_EDIT_ALL_FOLDERS)
    return _cmd_profile_edit_batch(args, folders)
