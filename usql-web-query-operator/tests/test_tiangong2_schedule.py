from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from tiangong2_task.schedule import (  # noqa: E402
    PATCH_SCHEMA_VERSION,
    Tiangong2ScheduleUpdateClient,
    authorize_schedule_update,
    build_schedule_update_plan,
    prepare_schedule_update,
    verify_effective_scheduler_readback,
    verify_schedule_update_readback,
)
from tiangong2_task.scope import ScopedTask  # noqa: E402


def make_task() -> ScopedTask:
    return ScopedTask(
        project={"id": 308, "name": "project"},
        menu={"id": 103625, "name": "qing2lark_guocheng", "ifDir": 0, "taskType": 4},
        metadata={
            "taskId": 47728,
            "taskName": "qing2lark_guocheng",
            "taskType": 4,
            "principal": "lvshuai01",
            "creator": "lvshuai01",
            "nezhaId": 67318,
        },
        path=("数据开发", "吕帅", "青橙-数据播报", "qing2lark_guocheng"),
        project_id=308,
        folder_name="吕帅",
        menu_id=103625,
        task_id=47728,
        nezha_task_id=67318,
        task_name="qing2lark_guocheng",
        owner_name="lvshuai01",
    )


SCHEDULE = {
    "taskId": 47728,
    "selfReliance": 0,
    "concurrentCount": 5,
    "concurrentStrategy": 0,
    "priority": 2,
    "downStreamPriority": 1,
    "executorGroup": "new_bigdata",
    "failOption": 0,
    "maxRetryNum": 3,
    "retryInterval": 5,
    "firstRetryAlarm": True,
    "scheduleType": 1,
    "firstRunTime": "2026-09-26 22:00:00",
    "endRunTime": "2027-12-31 23:59:59",
    "runInterval": 2,
    "timeUnit": 1,
    "nextRunTime": "2026-09-30 22:00:00",
    "dependencyTaskList": [],
}


class FakeReader:
    def __init__(self) -> None:
        self.schedule = copy.deepcopy(SCHEDULE)

    def get_schedule(self, task_id: int) -> dict:
        self.assert_task(task_id)
        return copy.deepcopy(self.schedule)

    @staticmethod
    def assert_task(task_id: int) -> None:
        if task_id != 47728:
            raise AssertionError(task_id)


class FakeOperationsReader:
    def __init__(self, schedule: dict) -> None:
        self.schedule = copy.deepcopy(schedule)

    def get_task_and_schedule(self, task_id: int) -> dict:
        if task_id != 67318:
            raise AssertionError(task_id)
        return copy.deepcopy(self.schedule)


class FakeResponse:
    ok = True
    status = 200

    def json(self) -> dict:
        return {"status": "success", "errorCode": 0, "data": {"accepted": True}}


class FakeRequest:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def post(self, url: str, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse()


class Tiangong2ScheduleUpdateTests(unittest.TestCase):
    def write_patch(self, directory: str, changes: dict) -> Path:
        path = Path(directory) / "schedule-patch.json"
        path.write_text(
            json.dumps(
                {"schema_version": PATCH_SCHEMA_VERSION, "changes": changes},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path

    def test_plan_preserves_non_schedule_settings_and_projects_next_run_recalculation(self) -> None:
        reader = FakeReader()
        with tempfile.TemporaryDirectory() as directory:
            patch_path = self.write_patch(
                directory,
                {"firstRunTime": "2026-09-30 21:40:00", "runInterval": 2, "timeUnit": 1},
            )
            plan = build_schedule_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01", "displayName": "吕帅01"},
                schedule_patch_file=patch_path,
            )
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["desired"]["schedule"]["firstRunTime"], "2026-09-30 21:40:00")
        self.assertEqual(plan["desired"]["schedule"]["nextRunTime"], "2026-09-30 22:00:00")
        self.assertEqual(plan["desired"]["schedule"]["executorGroup"], "new_bigdata")
        self.assertEqual(plan["desired"]["schedule"]["retryInterval"], 5)

    def test_writer_uses_json_transport_and_is_single_use(self) -> None:
        reader = FakeReader()
        with tempfile.TemporaryDirectory() as directory:
            patch_path = self.write_patch(directory, {"firstRunTime": "2026-09-30 21:40:00"})
            plan = build_schedule_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                schedule_patch_file=patch_path,
            )
            authorization = authorize_schedule_update(
                plan,
                expected_plan_sha256=plan["plan_sha256"],
                confirm_save_schedule=True,
            )
            payload, _ = prepare_schedule_update(reader, task=make_task(), plan=plan)
            request = FakeRequest()
            writer = Tiangong2ScheduleUpdateClient(request, authorization=authorization)
            response = writer.save_schedule(payload=payload)
            self.assertEqual(response["data"]["accepted"], True)
            self.assertEqual(request.calls[0][0], "https://tiangong2.baijia.com/api/dp/task/saveScheduleConfig")
            self.assertIn("data", request.calls[0][1])
            self.assertNotIn("form", request.calls[0][1])
            with self.assertRaisesRegex(Exception, "single-use"):
                writer.save_schedule(payload=payload)

    def test_readback_matches_projected_schedule(self) -> None:
        reader = FakeReader()
        with tempfile.TemporaryDirectory() as directory:
            patch_path = self.write_patch(directory, {"firstRunTime": "2026-09-30 21:40:00"})
            plan = build_schedule_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                schedule_patch_file=patch_path,
            )
            reader.schedule["firstRunTime"] = "2026-09-30 21:40:00"
            reader.schedule["nextRunTime"] = "2026-09-30 21:40:00"
            readback = verify_schedule_update_readback(reader, task=make_task(), plan=plan)
        self.assertTrue(readback["configuration_fully_verified"])
        self.assertEqual(readback["schedule"]["firstRunTime"], "2026-09-30 21:40:00")

    def test_effective_scheduler_readback_detects_stale_nezha_schedule(self) -> None:
        reader = FakeReader()
        with tempfile.TemporaryDirectory() as directory:
            patch_path = self.write_patch(directory, {"firstRunTime": "2026-09-30 21:40:00"})
            plan = build_schedule_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                schedule_patch_file=patch_path,
            )
        operations = FakeOperationsReader(
            {
                "taskId": 67318,
                "taskName": "qing2lark_guocheng",
                "firstRunTime": "2026-09-26 22:00:00",
                "nextRunTime": "2026-09-30 22:00:00",
                "scheduleFrequency": "2h",
            }
        )
        readback = verify_effective_scheduler_readback(
            operations,
            task=make_task(),
            plan=plan,
        )
        self.assertFalse(readback["fully_verified"])
        self.assertFalse(readback["first_run_time_matches"])


if __name__ == "__main__":
    unittest.main()
