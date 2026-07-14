from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.commands.apply_data_center_dataset_creation import (  # noqa: E402
    validate_apply_request,
)
from usql_web_query.data_center import (  # noqa: E402
    DataCenterDataset,
    DataCenterFolder,
    iter_dataset_folders,
    select_folder_for_creation,
)
from usql_web_query.data_center_creation import (  # noqa: E402
    build_creation_plan,
    load_creation_plan,
    load_creation_sql,
    write_creation_plan,
)
from usql_web_query.data_center_replacement import sql_sha256  # noqa: E402
from usql_web_query.data_center_ui import matches_sql_response  # noqa: E402


def folder() -> DataCenterFolder:
    return DataCenterFolder(
        id="menu_set_folder",
        key="menu_set_folder",
        name="青橙项目部",
        file_value="",
        subject_id="",
        parent_id="menu_set_parent",
        owner="owner",
        path=("通用", "SQL数据集", "H业务线", "市场部", "市场顾问部", "青橙项目部"),
    )


def dataset(name: str, dataset_id: str = "menu_set_existing") -> DataCenterDataset:
    return DataCenterDataset(
        id=dataset_id,
        key=dataset_id,
        name=name,
        file_value="1",
        subject_id="2",
        parent_id="menu_set_folder",
        owner="owner",
        create_time="2026-07-14",
        path=(*folder().path, name),
    )


class DataCenterCreationPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.sql_file = self.root / "create.sql"
        self.sql_file.write_text("select 1 as probe\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def build(self, datasets: list[DataCenterDataset] | None = None):
        today = date.today()
        return build_creation_plan(
            domain="qingcheng",
            folder=folder(),
            datasets=datasets or [],
            dataset_name="Codex创建验收",
            sql_file=self.sql_file,
            sql_text=load_creation_sql(self.sql_file),
            data_source_name="PRESTO数据源（DORIS加速）",
            data_source_id="menu_source_1",
            schedule_start=today,
            schedule_end=today + timedelta(days=90),
            schedule_hours=tuple(f"{hour}:00" for hour in range(24)),
            created_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )

    def test_ready_plan_round_trip_and_hash_tamper_detection(self) -> None:
        plan = self.build([dataset("Existing")])
        self.assertEqual("ready", plan.status)
        self.assertEqual(24, len(plan.schedule["synchronizationFrequency"]["timeHourMinuteList"]))
        output = self.root / "plan.json"
        write_creation_plan(output, plan)
        loaded = load_creation_plan(output)
        self.assertEqual(plan.plan_sha256, loaded.plan_sha256)

        payload = json.loads(output.read_text(encoding="utf-8"))
        payload["dataset_name"] = "tampered"
        output.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(UsageError, "hash is invalid"):
            load_creation_plan(output)

    def test_duplicate_name_blocks_plan(self) -> None:
        plan = self.build([dataset("Codex创建验收")])
        self.assertEqual("blocked", plan.status)
        self.assertIn(
            "DATASET_NAME_ALREADY_EXISTS",
            {item["code"] for item in plan.diagnostics},
        )

    def test_schedule_range_over_90_days_blocks_plan(self) -> None:
        today = date.today()
        plan = build_creation_plan(
            domain="qingcheng",
            folder=folder(),
            datasets=[],
            dataset_name="Codex创建验收",
            sql_file=self.sql_file,
            sql_text=load_creation_sql(self.sql_file),
            data_source_name="source",
            data_source_id="source_1",
            schedule_start=today,
            schedule_end=today + timedelta(days=91),
            schedule_hours=("0:00",),
        )
        self.assertEqual("blocked", plan.status)
        self.assertIn("INVALID_SCHEDULE_RANGE", {item["code"] for item in plan.diagnostics})

    def test_apply_requires_confirmation_and_exact_hash(self) -> None:
        plan = self.build()
        args = SimpleNamespace(
            confirm_production_write=False,
            expected_plan_sha256=plan.plan_sha256,
        )
        with self.assertRaisesRegex(UsageError, "confirm-production-write"):
            validate_apply_request(args, plan)
        args.confirm_production_write = True
        args.expected_plan_sha256 = "wrong"
        with self.assertRaisesRegex(UsageError, "hash mismatch"):
            validate_apply_request(args, plan)
        args.expected_plan_sha256 = plan.plan_sha256
        validate_apply_request(args, plan)


class DataCenterCreationFolderTests(unittest.TestCase):
    def test_folder_tree_and_domain_resolution(self) -> None:
        payload = {
            "data": {
                "commonList": [
                    {
                        "id": "root",
                        "name": "通用",
                        "fileType": "DATA_SET_MENU_GENERAL",
                        "isFile": 0,
                        "children": [
                            {
                                "id": "market",
                                "name": "市场顾问部",
                                "fileType": "DATA_SET_MENU_GENERAL",
                                "isFile": 0,
                                "children": [
                                    {
                                        "id": "qc",
                                        "name": "青橙项目部",
                                        "fileType": "DATA_SET_MENU_GENERAL",
                                        "isFile": 0,
                                        "children": [
                                            {
                                                "id": "qc_child",
                                                "name": "自动化测试",
                                                "fileType": "DATA_SET_MENU_GENERAL",
                                                "isFile": 0,
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        }
        folders = list(iter_dataset_folders(payload))
        selected = select_folder_for_creation(
            folders,
            domain="qingcheng",
            folder_path="自动化测试",
        )
        self.assertEqual("qc_child", selected.id)


class DataCenterCreationMatcherTests(unittest.TestCase):
    def test_new_save_match_requires_null_id_parent_and_source(self) -> None:
        request = SimpleNamespace(
            post_data=json.dumps(
                {
                    "id": None,
                    "parentId": "folder",
                    "dataSourceId": "source",
                    "executeSql": "select 1\n",
                }
            )
        )
        response = SimpleNamespace(
            url="https://example.test/data/set/saveAndUpdate",
            request=request,
        )
        self.assertTrue(
            matches_sql_response(
                response,
                endpoint="/data/set/saveAndUpdate",
                expected_sql_sha256=sql_sha256("select 1"),
                require_null_dataset_id=True,
                expected_parent_id="folder",
                expected_data_source_id="source",
            )
        )
        request.post_data = json.dumps(
            {
                "id": "menu_set_existing",
                "parentId": "folder",
                "dataSourceId": "source",
                "executeSql": "select 1\n",
            }
        )
        self.assertFalse(
            matches_sql_response(
                response,
                endpoint="/data/set/saveAndUpdate",
                expected_sql_sha256=sql_sha256("select 1"),
                require_null_dataset_id=True,
                expected_parent_id="folder",
                expected_data_source_id="source",
            )
        )


if __name__ == "__main__":
    unittest.main()
