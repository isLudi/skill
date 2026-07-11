from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.commands.sync_data_center_sql import (  # noqa: E402
    validate_sync_scope_args,
    validate_sync_write_mode,
)
from usql_web_query.data_center import DataCenterDataset, DataCenterDatasetSql  # noqa: E402
from usql_web_query.data_center_knowledge import (  # noqa: E402
    DataCenterSkillTarget,
    apply_data_center_plans,
    combined_plan_sha256,
    data_center_apply_lock,
    plan_data_center_sync,
)


def dataset_sql(sql: str = "select 1", *, model_id: str = "1001", name: str = "Dataset One") -> DataCenterDatasetSql:
    dataset = DataCenterDataset(
        id=f"menu_{model_id}",
        key=f"menu_{model_id}",
        name=name,
        file_value=model_id,
        subject_id="991",
        parent_id="parent",
        owner="owner",
        create_time="2026-01-01",
        path=("Root", name),
    )
    return DataCenterDatasetSql(
        dataset=dataset,
        execute_sql=sql,
        data_source_id="source_1",
        open_external="0",
        detail_payload={},
    )


class DataCenterCanonicalSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.skills_root = Path(self.temp_dir.name)
        self.skill_root = self.skills_root / "sql-query-writer-for-dashboard"
        for relative in (
            "resources/raw_sql",
            "knowledge/dashboards",
            "knowledge/update_log",
            "knowledge/reverse_index",
            "semantic/generated",
        ):
            (self.skill_root / relative).mkdir(parents=True, exist_ok=True)
        (self.skill_root / "knowledge/update_log/changelog.md").write_text("# Log\n", encoding="utf-8")
        self.target = DataCenterSkillTarget(
            name="market",
            root=self.skill_root,
            dataset_prefix="market",
            doc_filename="data_center_market_datasets.md",
            title="Market datasets",
            scope_note="test scope",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def plan(self, sql: str = "select 1"):
        return plan_data_center_sync(
            self.target,
            [dataset_sql(sql)],
            run_date=date(2026, 7, 11),
            scope_complete=True,
            update_changelog=True,
        )

    def test_plan_uses_stable_path_and_is_read_only(self) -> None:
        legacy = self.skill_root / "resources/raw_sql/data_center_market_1001_20260710.sql"
        legacy.write_text("select 0\n", encoding="utf-8")
        plan = self.plan()
        self.assertEqual("ready", plan.status)
        self.assertEqual("resources/raw_sql/data_center_market_1001.sql", plan.datasets[0].raw_sql_file)
        self.assertIn("resources/raw_sql/data_center_market_1001_20260710.sql", plan.datasets[0].legacy_files_removed)
        self.assertFalse((self.skill_root / "resources/raw_sql/data_center_market_1001.sql").exists())
        self.assertEqual(combined_plan_sha256([plan]), combined_plan_sha256([self.plan()]))

    def test_apply_requires_exact_hash_and_removes_legacy_file(self) -> None:
        legacy = self.skill_root / "resources/raw_sql/data_center_market_1001_20260710.sql"
        legacy.write_text("select 0\n", encoding="utf-8")
        plan = self.plan()
        with self.assertRaisesRegex(UsageError, "plan hash mismatch"):
            apply_data_center_plans([plan], expected_plan_sha256="wrong")
        self.assertTrue(legacy.exists())
        with patch("usql_web_query.data_center_knowledge.run_mandatory_maintenance", return_value=[]):
            apply_data_center_plans([plan], expected_plan_sha256=combined_plan_sha256([plan]))
        stable = self.skill_root / "resources/raw_sql/data_center_market_1001.sql"
        self.assertEqual("select 1\n", stable.read_text(encoding="utf-8"))
        self.assertFalse(legacy.exists())
        registry = json.loads((self.skill_root / "semantic/current_model_bindings.json").read_text(encoding="utf-8"))
        self.assertEqual("1001", registry["models"][0]["model_id"])

    def test_failed_maintenance_rolls_back_every_mutation(self) -> None:
        stable = self.skill_root / "resources/raw_sql/data_center_market_1001.sql"
        stable.write_text("select 0\n", encoding="utf-8")
        plan = self.plan("select 2")
        with patch(
            "usql_web_query.data_center_knowledge.run_mandatory_maintenance",
            side_effect=UsageError("forced failure"),
        ):
            with self.assertRaisesRegex(UsageError, "rolled back"):
                apply_data_center_plans([plan], expected_plan_sha256=combined_plan_sha256([plan]))
        self.assertEqual("select 0\n", stable.read_text(encoding="utf-8"))
        self.assertFalse((self.skill_root / "semantic/current_model_bindings.json").exists())

    def test_concurrent_apply_is_rejected_before_any_write(self) -> None:
        plan = self.plan()
        with data_center_apply_lock([plan]):
            with self.assertRaisesRegex(UsageError, "another Data Center Apply"):
                apply_data_center_plans(
                    [plan],
                    expected_plan_sha256=combined_plan_sha256([plan]),
                )
        self.assertFalse((self.skill_root / "resources/raw_sql/data_center_market_1001.sql").exists())

    def test_registry_slot_cannot_point_to_non_current_model(self) -> None:
        registry = {
            "schema_version": "1.0.0",
            "domain": "market_consultant",
            "models": [],
            "semantic_slots": [{"slot_id": "slot:one", "current_model_id": "9999"}],
        }
        (self.skill_root / "semantic/current_model_bindings.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        plan = self.plan()
        self.assertEqual("blocked", plan.status)
        self.assertIn("SLOT_MODEL_NOT_CURRENT", {item["code"] for item in plan.diagnostics})

    def test_semantic_replacement_rebinds_slot_and_retires_old_model_together(self) -> None:
        initial = self.plan()
        with patch("usql_web_query.data_center_knowledge.run_mandatory_maintenance", return_value=[]):
            apply_data_center_plans([initial], expected_plan_sha256=combined_plan_sha256([initial]))
        registry_path = self.skill_root / "semantic/current_model_bindings.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["semantic_slots"] = [{"slot_id": "market_consultant:slot:one", "current_model_id": "1001"}]
        registry_path.write_text(json.dumps(registry), encoding="utf-8")

        replacement = plan_data_center_sync(
            self.target,
            [dataset_sql("select 2", model_id="1002", name="Dataset Two")],
            run_date=date(2026, 7, 12),
            scope_complete=False,
            update_changelog=False,
            retire_model_ids={"1001"},
            slot_bindings={"market_consultant:slot:one": "1002"},
        )
        self.assertEqual("ready", replacement.status)
        with patch("usql_web_query.data_center_knowledge.run_mandatory_maintenance", return_value=[]):
            apply_data_center_plans(
                [replacement], expected_plan_sha256=combined_plan_sha256([replacement])
            )
        updated = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(["1002"], [item["model_id"] for item in updated["models"]])
        self.assertEqual("1002", updated["semantic_slots"][0]["current_model_id"])
        self.assertFalse((self.skill_root / "resources/raw_sql/data_center_market_1001.sql").exists())


class DataCenterSyncCliSafetyTests(unittest.TestCase):
    def test_write_requires_reviewed_plan_hash(self) -> None:
        args = SimpleNamespace(
            write=True,
            expected_plan_sha256=None,
            rebuild_indexes=True,
            check_integrity=True,
            validate_stack=True,
        )
        with self.assertRaisesRegex(UsageError, "requires --expected-plan-sha256"):
            validate_sync_write_mode(args)

    def test_write_cannot_disable_validation(self) -> None:
        args = SimpleNamespace(
            write=True,
            expected_plan_sha256="abc",
            rebuild_indexes=True,
            check_integrity=True,
            validate_stack=False,
        )
        with self.assertRaisesRegex(UsageError, "unsafe Data Center write options"):
            validate_sync_write_mode(args)

    def test_cross_domain_retirement_is_rejected(self) -> None:
        args = SimpleNamespace(
            target_skill="market",
            retire_model_id=["qingcheng:2460"],
            slot_binding=[],
        )
        with self.assertRaisesRegex(UsageError, "outside selected domain"):
            validate_sync_scope_args(args)

    def test_all_target_retirement_requires_domain_prefix(self) -> None:
        args = SimpleNamespace(target_skill="all", retire_model_id=["2460"], slot_binding=[])
        with self.assertRaisesRegex(UsageError, "requires market:<id>"):
            validate_sync_scope_args(args)


if __name__ == "__main__":
    unittest.main()
