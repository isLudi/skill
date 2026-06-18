"""Sync Data Center dataset source SQL into business skill knowledge bases."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError

from usql_web_query.data_center import (
    DEFAULT_MARKET_START_DATASET,
    DataCenterClient,
    DataCenterDataset,
    DataCenterDatasetSql,
    filter_datasets_by_name,
    select_market_datasets,
    select_qingcheng_datasets,
)
from usql_web_query.data_center_knowledge import (
    DataCenterSkillTarget,
    sync_data_center_sql,
)


def cmd_sync_data_center_sql(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    run_date = date.fromisoformat(args.run_date) if args.run_date else date.today()
    targets = _resolve_targets(args)

    discovered, target_datasets, sql_by_id = _fetch_data_center_sql(args, targets)
    results = []
    for target in targets:
        dataset_sqls = [sql_by_id[dataset.id] for dataset in target_datasets[target.name]]
        result = sync_data_center_sql(
            target,
            dataset_sqls,
            write=args.write,
            run_date=run_date,
            update_changelog=args.update_changelog,
            rebuild_indexes=args.rebuild_indexes,
            check_integrity=args.check_integrity,
        )
        results.append(result)

    output = {
        "ok": True,
        "mode": "write" if args.write else "dry_run",
        "run_date": run_date.isoformat(),
        "state_path": str(args.state_path),
        "artifacts_dir": str(args.artifacts_dir),
        "datasets_discovered": len(discovered),
        "targets": {
            target.name: [dataset.to_json() for dataset in target_datasets[target.name]]
            for target in targets
        },
        "skills": [result.to_json() for result in results],
    }
    cache_path = _summary_path(args.artifacts_dir, run_date=run_date) if args.write else None
    output["summary_cache"] = str(cache_path) if cache_path else None
    if cache_path:
        _write_summary(cache_path, output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def _fetch_data_center_sql(
    args: argparse.Namespace,
    targets: list[DataCenterSkillTarget],
) -> tuple[list[DataCenterDataset], dict[str, list[DataCenterDataset]], dict[str, DataCenterDatasetSql]]:
    sync_playwright = import_playwright()
    args.state_path.parent.mkdir(parents=True, exist_ok=True)
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
            client = DataCenterClient(page, args.state_path)
            client.ensure_authenticated(args.username, args.password)
            discovered = client.discover_datasets()
            target_datasets = _select_target_datasets(args, targets, discovered)

            sql_by_id: dict[str, DataCenterDatasetSql] = {}
            for dataset in _unique_datasets(target_datasets):
                sql_by_id[dataset.id] = client.fetch_dataset_sql(dataset)
        finally:
            context.close()
            browser.close()
    return discovered, target_datasets, sql_by_id


def _select_target_datasets(
    args: argparse.Namespace,
    targets: list[DataCenterSkillTarget],
    discovered: list[DataCenterDataset],
) -> dict[str, list[DataCenterDataset]]:
    selected: dict[str, list[DataCenterDataset]] = {}
    for target in targets:
        if target.name == "qingcheng":
            datasets = select_qingcheng_datasets(discovered)
        elif target.name == "market":
            datasets = select_market_datasets(discovered, start_name=args.market_start_name)
        else:
            raise UsageError(f"Unsupported built-in Data Center target: {target.name}")
        selected[target.name] = filter_datasets_by_name(datasets, args.dataset_name)
    return selected


def _unique_datasets(target_datasets: dict[str, list[DataCenterDataset]]) -> list[DataCenterDataset]:
    seen: set[str] = set()
    unique: list[DataCenterDataset] = []
    for datasets in target_datasets.values():
        for dataset in datasets:
            if dataset.id in seen:
                continue
            seen.add(dataset.id)
            unique.append(dataset)
    return unique


def _resolve_targets(args: argparse.Namespace) -> list[DataCenterSkillTarget]:
    skill_root = Path(__file__).resolve().parents[3]
    skills_root = skill_root.parent
    configured = {
        "qingcheng": DataCenterSkillTarget(
            name="qingcheng",
            root=skills_root / "qingcheng-dashboard-sql",
            dataset_prefix="qingcheng",
            doc_filename="data_center_qingcheng_datasets.md",
            title="数据中心数据集源 SQL（青橙项目部）",
            scope_note="青橙项目部目录下的全部 SQL 数据集。",
        ),
        "market": DataCenterSkillTarget(
            name="market",
            root=skills_root / "sql-query-writer-for-dashboard",
            dataset_prefix="market",
            doc_filename="data_center_market_datasets.md",
            title="数据中心数据集源 SQL（市场顾问部）",
            scope_note=f"市场顾问部目录下从 `{args.market_start_name}` 开始到末尾的 SQL 数据集。",
        ),
    }
    if args.target_skill == "all":
        return [configured["qingcheng"], configured["market"]]
    return [configured[args.target_skill]]


def _summary_path(artifacts_dir: Path, *, run_date: date) -> Path:
    return artifacts_dir / f"data_center_sql_sync_{run_date:%Y%m%d}.json"


def _write_summary(path: Path, output: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
