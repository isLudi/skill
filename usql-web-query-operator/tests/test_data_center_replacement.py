from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.commands.apply_data_center_sql_replacement import (  # noqa: E402
    validate_apply_request,
)
from usql_web_query.data_center import (  # noqa: E402
    DataCenterClient,
    DataCenterDataset,
    DataCenterDatasetSql,
    DataCenterScheduleRun,
    select_dataset_for_replacement,
)
from usql_web_query.data_center_replacement import (  # noqa: E402
    DataCenterSqlReplacementPlan,
    build_replacement_plan,
    canonical_sql_text,
    data_center_replacement_lock,
    load_replacement_plan,
    load_replacement_sql,
    write_replacement_plan,
)
from usql_web_query.data_center_write import (  # noqa: E402
    DataCenterReplacementExecutor,
    _matches_schedule_trigger,
    _matches_sql_response,
    _wait_for_editor_sql_hash,
)


def dataset_sql(sql: str = "select 1") -> DataCenterDatasetSql:
    dataset = DataCenterDataset(
        id="menu_set_1001",
        key="menu_set_1001",
        name="Dataset One",
        file_value="1001",
        subject_id="991",
        parent_id="parent",
        owner="owner",
        create_time="2026-01-01",
        path=("Root", "市场顾问部", "市场顾问部", "Dataset One"),
    )
    return DataCenterDatasetSql(
        dataset=dataset,
        execute_sql=sql,
        data_source_id="source_1",
        open_external="0",
        detail_payload={
            "modelId": "1001",
            "schedule": {
                "taskStatus": True,
                "isExpire": False,
                "taskId": "11,12",
            },
        },
    )


class DataCenterReplacementPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.sql_file = self.root / "replacement.sql"
        self.sql_file.write_text("select 2\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def build(self, *, current: str = "select 1", replacement: str = "select 2", allow_noop: bool = False):
        self.sql_file.write_text(replacement, encoding="utf-8")
        return build_replacement_plan(
            domain="market",
            dataset_sql=dataset_sql(current),
            sql_file=self.sql_file,
            replacement_sql=load_replacement_sql(self.sql_file),
            allow_noop=allow_noop,
            created_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )

    def test_canonical_sql_normalizes_line_endings_and_one_final_newline(self) -> None:
        self.assertEqual("select 1\n", canonical_sql_text("select 1\r\n\r\n"))

    def test_replacement_sql_rejects_bom(self) -> None:
        self.sql_file.write_bytes(b"\xef\xbb\xbfselect 1\n")
        with self.assertRaisesRegex(UsageError, "without BOM"):
            load_replacement_sql(self.sql_file)

    def test_plan_is_ready_for_a_content_change(self) -> None:
        plan = self.build()
        self.assertEqual("ready", plan.status)
        self.assertTrue(plan.content_change)
        self.assertEqual(plan.plan_sha256, plan.computed_sha256())

    def test_noop_is_blocked_by_default(self) -> None:
        plan = self.build(current="select 1", replacement="select 1")
        self.assertEqual("blocked", plan.status)
        self.assertIn("NO_CONTENT_CHANGE", {item["code"] for item in plan.diagnostics})

    def test_explicit_noop_refresh_plan_is_ready(self) -> None:
        plan = self.build(current="select 1", replacement="select 1", allow_noop=True)
        self.assertEqual("ready", plan.status)
        self.assertFalse(plan.content_change)

    def test_modified_plan_artifact_is_rejected(self) -> None:
        plan = self.build()
        payload = plan.to_json()
        payload["dataset"]["name"] = "tampered"
        with self.assertRaisesRegex(UsageError, "artifact was modified"):
            DataCenterSqlReplacementPlan.from_json(payload)

    def test_plan_round_trip_validates_hash(self) -> None:
        plan = self.build()
        path = self.root / "plan.json"
        write_replacement_plan(path, plan)
        loaded = load_replacement_plan(path)
        self.assertEqual(plan.plan_sha256, loaded.plan_sha256)

    def test_dataset_replacement_lock_rejects_concurrency(self) -> None:
        with data_center_replacement_lock("menu_set_1001"):
            with self.assertRaisesRegex(UsageError, "another Data Center replacement"):
                with data_center_replacement_lock("menu_set_1001"):
                    pass


class DataCenterReplacementIdentityTests(unittest.TestCase):
    def test_exact_dataset_is_resolved_inside_domain(self) -> None:
        item = dataset_sql().dataset
        selected = select_dataset_for_replacement(
            [item], domain="market", dataset_name="Dataset One"
        )
        self.assertEqual(item.id, selected.id)

    def test_cross_domain_dataset_is_rejected(self) -> None:
        item = dataset_sql().dataset
        with self.assertRaisesRegex(UsageError, "was not found"):
            select_dataset_for_replacement(
                [item], domain="qingcheng", dataset_id=item.id
            )

    def test_schedule_history_parser_normalizes_status(self) -> None:
        client = object.__new__(DataCenterClient)
        client.post_json = lambda endpoint, payload: {
            "data": [
                {
                    "id": 10,
                    "startTime": "2026-07-14 20:00:00",
                    "endTime": "2026-07-14 20:00:10",
                    "elapsed": 10,
                    "status": "success",
                }
            ]
        }
        runs = client.fetch_schedule_runs("1,2")
        self.assertEqual("10", runs[0].id)
        self.assertEqual("SUCCESS", runs[0].status)


class DataCenterReplacementApplyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        sql_file = root / "replacement.sql"
        sql_file.write_text("select 2\n", encoding="utf-8")
        self.plan = build_replacement_plan(
            domain="market",
            dataset_sql=dataset_sql(),
            sql_file=sql_file,
            replacement_sql="select 2",
            allow_noop=False,
            created_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_apply_requires_explicit_confirmation(self) -> None:
        args = SimpleNamespace(
            confirm_production_write=False,
            expected_plan_sha256=self.plan.plan_sha256,
        )
        with self.assertRaisesRegex(UsageError, "confirm-production-write"):
            validate_apply_request(args, self.plan)

    def test_apply_requires_exact_plan_hash(self) -> None:
        args = SimpleNamespace(
            confirm_production_write=True,
            expected_plan_sha256="wrong",
        )
        with self.assertRaisesRegex(UsageError, "plan hash mismatch"):
            validate_apply_request(args, self.plan)

    def test_response_matcher_binds_sql_hash_and_dataset(self) -> None:
        request = SimpleNamespace(
            post_data=json.dumps({"id": "menu_set_1001", "executeSql": "select 2"})
        )
        response = SimpleNamespace(
            url="https://example.test/data/set/saveAndUpdate",
            request=request,
        )
        self.assertTrue(
            _matches_sql_response(
                response,
                endpoint="/data/set/saveAndUpdate",
                expected_sql_sha256=self.plan.replacement_sql_sha256,
                expected_dataset_id="menu_set_1001",
            )
        )

    def test_schedule_trigger_matcher_binds_task_id(self) -> None:
        response = SimpleNamespace(
            url="https://example.test/data/set/schedules/executeOnce",
            request=SimpleNamespace(post_data=json.dumps({"id": "11,12"})),
        )
        self.assertTrue(_matches_schedule_trigger(response, "11,12"))

    def test_editor_waits_for_async_sql_population(self) -> None:
        values = iter(["", "", "select 1"])
        editor = SimpleNamespace(evaluate=lambda expression: next(values))
        page = SimpleNamespace(wait_for_timeout=lambda milliseconds: None)
        result = _wait_for_editor_sql_hash(
            page=page,
            editor=editor,
            expected_sha256=self.plan.current_sql_sha256,
            timeout_ms=1000,
        )
        self.assertEqual("select 1\n", result)

    def test_poll_requires_a_new_success_record(self) -> None:
        running = DataCenterScheduleRun("2", "start", "", None, "RUNNING")
        success = DataCenterScheduleRun("2", "start", "end", 10, "SUCCESS")
        client = SimpleNamespace()
        values = iter([[running], [success]])
        client.fetch_schedule_runs = lambda task_id: next(values)
        page = SimpleNamespace(wait_for_timeout=lambda milliseconds: None)
        executor = DataCenterReplacementExecutor(
            page=page,
            client=client,
            plan=self.plan,
            replacement_sql="select 2",
            preview_timeout_ms=1000,
            refresh_timeout_ms=1000,
            poll_interval_ms=1,
        )
        result = executor._poll_for_new_success("11,12", {"1"})
        self.assertEqual("2", result.id)
        self.assertEqual("SUCCESS", result.status)

    def test_poll_stops_on_a_failed_new_record(self) -> None:
        failed = DataCenterScheduleRun("2", "start", "end", 10, "FAILED")
        client = SimpleNamespace(fetch_schedule_runs=lambda task_id: [failed])
        page = SimpleNamespace(wait_for_timeout=lambda milliseconds: None)
        executor = DataCenterReplacementExecutor(
            page=page,
            client=client,
            plan=self.plan,
            replacement_sql="select 2",
            preview_timeout_ms=1000,
            refresh_timeout_ms=1000,
            poll_interval_ms=1,
        )
        with self.assertRaisesRegex(UsageError, "synchronization failed"):
            executor._poll_for_new_success("11,12", {"1"})


if __name__ == "__main__":
    unittest.main()
