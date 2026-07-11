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
    apply_data_center_plans,
    combined_plan_sha256,
    dry_run_results,
    plan_data_center_sync,
)


def cmd_sync_data_center_sql(args: argparse.Namespace) -> int:
    validate_sync_write_mode(args)
    validate_sync_scope_args(args)
    load_env_file(args.env_file)
    run_date = date.fromisoformat(args.run_date) if args.run_date else date.today()
    targets = _resolve_targets(args)

    discovered, target_datasets, sql_by_id = _fetch_data_center_sql(args, targets)
    plans = []
    for target in targets:
        dataset_sqls = [sql_by_id[dataset.id] for dataset in target_datasets[target.name]]
        plan = plan_data_center_sync(
            target,
            dataset_sqls,
            run_date=run_date,
            scope_complete=not bool(args.dataset_name),
            update_changelog=args.update_changelog,
            retire_model_ids=_retire_ids_for_target(args, target),
            slot_bindings=_slot_bindings_for_target(args, target),
        )
        plans.append(plan)

    plan_sha256 = combined_plan_sha256(plans)
    plan_path = _plan_path(args.artifacts_dir, run_date=run_date, plan_sha256=plan_sha256)
    plan_payload = {
        "schema_version": "1.0.0",
        "plan_sha256": plan_sha256,
        "status": "blocked" if any(plan.status == "blocked" for plan in plans) else "ready",
        "plans": [plan.to_json() for plan in plans],
    }
    _write_summary(plan_path, plan_payload)

    if args.write:
        results = apply_data_center_plans(
            plans,
            expected_plan_sha256=args.expected_plan_sha256,
        )
    else:
        results = dry_run_results(plans)

    output = {
        "ok": True,
        "mode": "write" if args.write else "dry_run",
        "run_date": run_date.isoformat(),
        "plan_sha256": plan_sha256,
        "plan_path": str(plan_path),
        "plan_status": plan_payload["status"],
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
    return 0 if plan_payload["status"] == "ready" else 1


def validate_sync_write_mode(args: argparse.Namespace) -> None:
    if not args.write:
        return
    if not args.expected_plan_sha256:
        raise UsageError(
            "sync-data-center-sql --write requires --expected-plan-sha256 from a reviewed dry-run"
        )
    disabled = []
    if not args.rebuild_indexes:
        disabled.append("--no-rebuild-indexes")
    if not args.check_integrity:
        disabled.append("--no-check-integrity")
    if not args.validate_stack:
        disabled.append("--no-validate-stack")
    if disabled:
        raise UsageError("unsafe Data Center write options are forbidden: " + ", ".join(disabled))


def validate_sync_scope_args(args: argparse.Namespace) -> None:
    selected_targets = {"market", "qingcheng"} if args.target_skill == "all" else {args.target_skill}
    for raw in args.retire_model_id or []:
        if ":" in raw:
            target_name, model_id = raw.split(":", 1)
            if target_name not in {"market", "qingcheng"} or target_name not in selected_targets or not model_id:
                raise UsageError(f"retirement target is outside selected domain(s): {raw}")
        elif args.target_skill == "all":
            raise UsageError("--retire-model-id requires market:<id> or qingcheng:<id> with --target-skill all")
    domain_to_target = {"market_consultant": "market", "qingcheng": "qingcheng"}
    for raw in args.slot_binding or []:
        if "=" not in raw:
            raise UsageError("--slot-binding must use <slot_id>=<model_id>")
        slot_id, model_id = raw.rsplit("=", 1)
        domain = slot_id.split(":", 1)[0]
        if domain not in domain_to_target or domain_to_target[domain] not in selected_targets or not model_id:
            raise UsageError(f"semantic slot is outside selected domain(s): {slot_id}")


def _retire_ids_for_target(args: argparse.Namespace, target: DataCenterSkillTarget) -> set[str]:
    values: set[str] = set()
    for raw in args.retire_model_id or []:
        if ":" in raw:
            target_name, model_id = raw.split(":", 1)
            if target_name == target.name:
                values.add(model_id)
        elif args.target_skill == target.name:
            values.add(raw)
        else:
            raise UsageError("--retire-model-id requires market:<id> or qingcheng:<id> with --target-skill all")
    return values


def _slot_bindings_for_target(args: argparse.Namespace, target: DataCenterSkillTarget) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for raw in args.slot_binding or []:
        if "=" not in raw:
            raise UsageError("--slot-binding must use <slot_id>=<model_id>")
        slot_id, model_id = raw.rsplit("=", 1)
        if slot_id.startswith(target.domain + ":"):
            bindings[slot_id] = model_id
    return bindings


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


def _plan_path(artifacts_dir: Path, *, run_date: date, plan_sha256: str) -> Path:
    return artifacts_dir / f"data_center_sql_plan_{run_date:%Y%m%d}_{plan_sha256[:12]}.json"


def _write_summary(path: Path, output: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
