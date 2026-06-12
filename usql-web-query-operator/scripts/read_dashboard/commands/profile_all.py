"""Scan configured folders, profile all dashboards, and sync markdown docs."""

from __future__ import annotations

from dataclasses import replace
import json
import time
from pathlib import Path

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import parse_dashboard_names, safe_filename, write_json
from ..constants import DASHBOARD_MARKET_URL, DashboardKnowledgeTarget, FOLDER_KNOWLEDGE_TARGETS
from ..markdown import dashboard_filename, update_dashboards_readme, write_profile_markdown, write_readme
from ..menu import collect_dashboard_records, fetch_dashboard_menu
from ..models import DashboardKnowledgeEntry
from ..profile import profile_records


def _format_folder_scope(folder_names: list[str]) -> str:
    quoted = [f"`{name}`" for name in folder_names if name]
    if not quoted:
        return "目标文件夹"
    if len(quoted) == 1:
        return f"{quoted[0]} 文件夹"
    return f"{'、'.join(quoted[:-1])} 和 {quoted[-1]} 文件夹"


def _append_changelog(
    changelog_path: Path,
    results: list[dict[str, object]],
    entries: list[DashboardKnowledgeEntry],
    folder_names: list[str],
) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "",
        f"## {timestamp}",
        "",
        f"- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 扫描 {_format_folder_scope(folder_names)}，并将原始 `profile.json` 写入本地 runtime 目录。",
        f"- 刷新 `knowledge/dashboard_web_profiles/README.md`，当前索引 {len(entries)} 个看板快照。",
        "- 本次 profile 结果：成功 {ok_count} 个，失败 {failed_count} 个。".format(
            ok_count=sum(1 for item in results if item.get("ok")),
            failed_count=sum(1 for item in results if not item.get("ok")),
        ),
    ]
    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    existing = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
    changelog_path.write_text(existing.rstrip() + "\n" + "\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _single_target_override_requested(args) -> bool:
    return any(
        getattr(args, name) is not None
        for name in ("knowledge_dir", "readme_path", "dashboards_readme_path", "changelog_path")
    )


def _apply_single_folder_overrides(base_target: DashboardKnowledgeTarget | None, folder: str, args) -> DashboardKnowledgeTarget:
    knowledge_dir = args.knowledge_dir or (base_target.knowledge_dir if base_target else None)
    if knowledge_dir is None:
        raise UsageError(
            f"Folder `{folder}` has no default knowledge target. Provide `--knowledge-dir` and `--readme-path` when profiling a single folder."
        )
    readme_path = args.readme_path
    if readme_path is None:
        readme_path = knowledge_dir / "README.md" if args.knowledge_dir else (base_target.readme_path if base_target else knowledge_dir / "README.md")
    dashboards_readme_path = args.dashboards_readme_path if args.dashboards_readme_path is not None else (base_target.dashboards_readme_path if base_target else None)
    changelog_path = args.changelog_path if args.changelog_path is not None else (base_target.changelog_path if base_target else None)
    if base_target is None:
        return DashboardKnowledgeTarget(
            skill_name=f"custom:{folder}",
            knowledge_dir=knowledge_dir,
            readme_path=readme_path,
            dashboards_readme_path=dashboards_readme_path,
            changelog_path=changelog_path,
        )
    return replace(
        base_target,
        knowledge_dir=knowledge_dir,
        readme_path=readme_path,
        dashboards_readme_path=dashboards_readme_path,
        changelog_path=changelog_path,
    )


def _resolve_targets(args, requested_folders: list[str]) -> dict[str, DashboardKnowledgeTarget]:
    override_requested = _single_target_override_requested(args)
    if override_requested and len(requested_folders) != 1:
        raise UsageError(
            "Single-target overrides for `profile-all` can only be used with exactly one folder. "
            "Use the built-in folder routing for multi-folder syncs so Qingcheng and market knowledge stay isolated."
        )

    targets: dict[str, DashboardKnowledgeTarget] = {}
    for folder in requested_folders:
        base_target = FOLDER_KNOWLEDGE_TARGETS.get(folder)
        if override_requested:
            targets[folder] = _apply_single_folder_overrides(base_target, folder, args)
            continue
        if base_target is None:
            raise UsageError(
                f"No default knowledge target is configured for folder `{folder}`. "
                "Profile it alone with explicit `--knowledge-dir` / `--readme-path` overrides."
            )
        targets[folder] = base_target
    return targets


def cmd_profile_all(args) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    requested_folders = parse_dashboard_names(args.folders) or list(args.default_folders)
    targets = _resolve_targets(args, requested_folders)
    ensure_runtime([args.state_path.parent, args.artifacts_dir, *(target.knowledge_dir for target in targets.values())])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_dir = args.output_dir or artifacts_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, object]] = []
    entries: list[DashboardKnowledgeEntry] = []
    folder_summaries: list[dict[str, object]] = []
    target_buckets: dict[str, dict[str, object]] = {}

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            for folder in requested_folders:
                target = targets[folder]
                bucket = target_buckets.setdefault(
                    target.skill_name,
                    {
                        "target": target,
                        "entries": [],
                        "results": [],
                        "folders": [],
                    },
                )
                bucket_folders = bucket["folders"]
                if folder not in bucket_folders:
                    bucket_folders.append(folder)
                page.goto(DASHBOARD_MARKET_URL, wait_until="domcontentloaded", timeout=45_000)
                page.wait_for_timeout(args.wait_ms)
                records = collect_dashboard_records(fetch_dashboard_menu(page), folder)
                folder_dir = output_dir / safe_filename(folder)
                folder_dir.mkdir(parents=True, exist_ok=True)
                folder_results, folder_profiles = profile_records(
                    page=page,
                    folder_name=folder,
                    records=records,
                    output_dir=folder_dir,
                    dashboard_wait_ms=args.dashboard_wait_ms,
                    debug_artifacts=args.debug_artifacts,
                )
                results.extend(folder_results)
                bucket["results"].extend(folder_results)
                folder_summaries.append(
                    {
                        "folder": folder,
                        "skill_name": target.skill_name,
                        "dashboard_count": len(records),
                        "ok_count": sum(1 for item in folder_results if item.get("ok")),
                        "result_count": len(folder_results),
                    }
                )
                for item in folder_profiles:
                    record = item["record"]
                    profile = item["profile"]
                    raw_profile_path = item["profile_path"]
                    filename = dashboard_filename(record)
                    markdown_path = target.knowledge_dir / filename
                    write_profile_markdown(profile, raw_profile_path, markdown_path)
                    entry = DashboardKnowledgeEntry(
                        folder=folder,
                        dashboard_name=record.name,
                        dashboard_id=record.dashboard_id or "",
                        filename=filename,
                        ok=bool(profile.get("ok", True)),
                        rendered=bool(profile.get("rendered")),
                        message=str(profile.get("message") or ""),
                    )
                    entries.append(entry)
                    bucket["entries"].append(entry)
        finally:
            browser.close()

    target_summaries: list[dict[str, object]] = []
    for bucket in target_buckets.values():
        target = bucket["target"]
        target_entries = list(bucket["entries"])
        target_results = list(bucket["results"])
        target_folders = list(bucket["folders"])
        write_readme(target_entries, target.readme_path)
        if not args.skip_dashboards_readme and target.dashboards_readme_path is not None:
            update_dashboards_readme(target.dashboards_readme_path, target_folders)
        if not args.skip_changelog and target.changelog_path is not None:
            _append_changelog(target.changelog_path, target_results, target_entries, target_folders)
        target_summaries.append(
            {
                "skill_name": target.skill_name,
                "folders": target_folders,
                "knowledge_dir": str(target.knowledge_dir),
                "readme_path": str(target.readme_path),
                "dashboards_readme_path": str(target.dashboards_readme_path) if target.dashboards_readme_path else None,
                "changelog_path": str(target.changelog_path) if target.changelog_path else None,
                "entry_count": len(target_entries),
                "ok_count": sum(1 for item in target_results if item.get("ok")),
                "result_count": len(target_results),
            }
        )

    consolidated = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "folders": requested_folders,
        "output_dir": str(output_dir),
        "target_count": len(results),
        "ok_count": sum(1 for item in results if item.get("ok")),
        "folder_summaries": folder_summaries,
        "knowledge_targets": target_summaries,
        "results": results,
        "knowledge_entries": [entry.__dict__ for entry in entries],
    }
    consolidated_path = output_dir / "profile_all_consolidated.json"
    write_json(consolidated, consolidated_path)
    print(json.dumps({k: v for k, v in consolidated.items() if k != "results"}, ensure_ascii=False, indent=2))
    return 0 if all(item.get("ok") for item in results) else 1
