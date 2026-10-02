from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from tiangong2_task.nezha_schedule import (  # noqa: E402
    Tiangong2NezhaScheduleUpdateClient,
    authorize_nezha_schedule_update,
    build_nezha_schedule_update_plan,
    prepare_nezha_schedule_update,
    verify_nezha_schedule_readback,
)
from tiangong2_task.schedule import PATCH_SCHEMA_VERSION  # noqa: E402
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


class FakeOperationsReader:
    def __init__(self) -> None:
        self.config = {
            "id": 54676,
            "taskId": 67318,
            "firstRunTime": "2026-09-26 22:00:00",
            "nextRunTime": "2026-09-30 22:00:00",
            "endRunTime": "2027-12-31 23:59:59",
            "runInterval": 2,
            "formatRunInterval": "2h",
            "timeUnit": 1,
            "status": 0,
            "periodic": True,
        }
        self.effective = {
            "taskId": 67318,
            "taskName": "qing2lark_guocheng",
            "scheduleId": 54676,
            "scheduleType": "周期",
            "scheduleStatus": 0,
            "firstRunTime": "2026-09-26 22:00:00",
            "endRunTime": "2027-12-31 23:59:59",
            "scheduleFrequency": "2h",
            "supervisor": "lvshuai01",
        }
        self.list_row = {
            "taskId": 67318,
            "taskName": "qing2lark_guocheng",
            "scheduleId": 54676,
            "scheduleType": "周期",
            "scheduleStatus": 0,
            "firstRunTime": "2026-09-26 22:00:00",
            "endRunTime": "2027-12-31 23:59:59",
            "scheduleFrequency": "2h",
            "supervisor": "lvshuai01",
        }

    def get_schedule_config(self, task_id: int) -> dict:
        if task_id != 67318:
            raise AssertionError(task_id)
        return copy.deepcopy(self.config)

    def get_task_and_schedule(self, task_id: int) -> dict:
        if task_id != 67318:
            raise AssertionError(task_id)
        return copy.deepcopy(self.effective)

    def list_task_and_schedule_page(self, project_id: int, *, page_no: int, page_size: int):
        if project_id != 308 or page_no != 1 or page_size != 100:
            raise AssertionError((project_id, page_no, page_size))
        return [copy.deepcopy(self.list_row)], {"pageTotal": 1}


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


class Tiangong2NezhaScheduleTests(unittest.TestCase):
    def write_patch(self, directory: str) -> Path:
        path = Path(directory) / "schedule-patch.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": PATCH_SCHEMA_VERSION,
                    "changes": {
                        "firstRunTime": "2026-09-30 21:40:00",
                        "runInterval": 2,
                        "timeUnit": 1,
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path

    def test_plan_projects_periodic_nezha_payload(self) -> None:
        operations = FakeOperationsReader()
        with tempfile.TemporaryDirectory() as directory:
            plan = build_nezha_schedule_update_plan(
                operations,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01", "displayName": "吕帅01"},
                schedule_patch_file=self.write_patch(directory),
            )
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["desired"]["request_payload"]["taskId"], 67318)
        self.assertEqual(plan["desired"]["request_payload"]["firstRunTime"], "2026-09-30 21:40:00")
        self.assertTrue(plan["desired"]["request_payload"]["periodic"])
        self.assertNotIn("nextRunTime", plan["desired"]["request_payload"])
        self.assertNotIn("id", plan["desired"]["request_payload"])

    def test_writer_uses_periodic_schedule_endpoint_and_is_single_use(self) -> None:
        operations = FakeOperationsReader()
        with tempfile.TemporaryDirectory() as directory:
            plan = build_nezha_schedule_update_plan(
                operations,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                schedule_patch_file=self.write_patch(directory),
            )
            authorization = authorize_nezha_schedule_update(
                plan,
                expected_plan_sha256=plan["plan_sha256"],
                confirm_save_schedule=True,
            )
            payload, _ = prepare_nezha_schedule_update(
                operations,
                task=make_task(),
                plan=plan,
            )
            request = FakeRequest()
            writer = Tiangong2NezhaScheduleUpdateClient(request, authorization=authorization)
            response = writer.save_schedule(payload=payload)
        self.assertTrue(response["data"]["accepted"])
        self.assertEqual(
            request.calls[0][0],
            "https://tiangong2.baijia.com/api/nezha/task/schedule",
        )
        self.assertIn("data", request.calls[0][1])
        self.assertNotIn("form", request.calls[0][1])
        with self.assertRaisesRegex(Exception, "single-use"):
            writer.save_schedule(payload=payload)

    def test_readback_requires_config_effective_and_list_to_match(self) -> None:
        operations = FakeOperationsReader()
        with tempfile.TemporaryDirectory() as directory:
            plan = build_nezha_schedule_update_plan(
                operations,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                schedule_patch_file=self.write_patch(directory),
            )
        operations.config.update(
            {"firstRunTime": "2026-09-30 21:40:00", "nextRunTime": "2026-09-30 21:40:00"}
        )
        for row in (operations.effective, operations.list_row):
            row["firstRunTime"] = "2026-09-30 21:40:00"
        readback = verify_nezha_schedule_readback(operations, task=make_task(), plan=plan)
        self.assertTrue(readback["fully_verified"])
        self.assertTrue(readback["schedule_config_matches"])
        self.assertTrue(readback["effective_scheduler_matches"])
        self.assertTrue(readback["schedule_list_matches"])


if __name__ == "__main__":
    unittest.main()
