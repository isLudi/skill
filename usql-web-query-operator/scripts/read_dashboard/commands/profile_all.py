"""Scan configured folders, profile all dashboards, and sync markdown docs."""

from __future__ import annotations

import json
import time
from pathlib import Path

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import parse_dashboard_names, safe_filename, write_json
from ..constants import DASHBOARD_MARKET_URL
from ..markdown import dashboard_filename, update_dashboards_readme, write_profile_markdown, write_readme
from ..menu import collect_dashboard_records, fetch_dashboard_menu
from ..models import DashboardKnowledgeEntry
from ..profile import profile_records


def _append_changelog(changelog_path: Path, results: list[dict[str, object]], entries: list[DashboardKnowledgeEntry]) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "",
        f"## {timestamp}",
        "",
        "- 通过 `usql-web-query-operator/scripts/read_dashboard.py profile-all` 扫描 `市场顾问数据` 和 `青橙项目部` 文件夹，并将原始 `profile.json` 写入本地 runtime 目录。",
        f"- 刷新 `knowledge/dashboard_web_profiles/README.md`，当前索引 {len(entries)} 个看板快照。",
        "- 本次 profile 结果：成功 {ok_count} 个，失败 {failed_count} 个。".format(
            ok_count=sum(1 for item in results if item.get("ok")),
            failed_count=sum(1 for item in results if not item.get("ok")),
        ),
    ]
    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    existing = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
    changelog_path.write_text(existing.rstrip() + "\n" + "\n".join(lines).rstrip() + "\n", encoding="utf-8")


def cmd_profile_all(args) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir, args.knowledge_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_dir = args.output_dir or artifacts_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    requested_folders = parse_dashboard_names(args.folders) or list(args.default_folders)

    results: list[dict[str, object]] = []
    entries: list[DashboardKnowledgeEntry] = []
    folder_summaries: list[dict[str, object]] = []

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            for folder in requested_folders:
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
                folder_summaries.append(
                    {
                        "folder": folder,
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
                    markdown_path = args.knowledge_dir / filename
                    write_profile_markdown(profile, raw_profile_path, markdown_path)
                    entries.append(
                        DashboardKnowledgeEntry(
                            folder=folder,
                            dashboard_name=record.name,
                            dashboard_id=record.dashboard_id or "",
                            filename=filename,
                            ok=bool(profile.get("ok", True)),
                            rendered=bool(profile.get("rendered")),
                            message=str(profile.get("message") or ""),
                        )
                    )
        finally:
            browser.close()

    write_readme(entries, args.readme_path)
    if not args.skip_dashboards_readme:
        update_dashboards_readme(args.dashboards_readme_path)
    if not args.skip_changelog:
        _append_changelog(args.changelog_path, results, entries)

    consolidated = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "folders": requested_folders,
        "output_dir": str(output_dir),
        "knowledge_dir": str(args.knowledge_dir),
        "readme_path": str(args.readme_path),
        "target_count": len(results),
        "ok_count": sum(1 for item in results if item.get("ok")),
        "folder_summaries": folder_summaries,
        "results": results,
        "knowledge_entries": [entry.__dict__ for entry in entries],
    }
    consolidated_path = output_dir / "profile_all_consolidated.json"
    write_json(consolidated, consolidated_path)
    print(json.dumps({k: v for k, v in consolidated.items() if k != "results"}, ensure_ascii=False, indent=2))
    return 0 if all(item.get("ok") for item in results) else 1
