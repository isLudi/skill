from __future__ import annotations

import argparse
import copy
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from tiangong2_task.cli import build_parser  # noqa: E402
from tiangong2_task.config import TASK_CONTENT_SPECS  # noqa: E402
from tiangong2_task.editing import (  # noqa: E402
    Tiangong2QueryUpdateClient,
    authorize_query_update,
    build_query_update_plan,
    extract_query_regions,
    prepare_query_update,
    project_query_update,
    verify_query_update_readback,
)
from tiangong2_task.execution import (  # noqa: E402
    EXECUTE_ENDPOINT,
    Tiangong2ExecuteOnceClient,
    authorize_execution,
    validate_execution_plan,
)
from tiangong2_task.publishing import finalize_hash, text_sha256  # noqa: E402
from tiangong2_task.scope import ScopedTask  # noqa: E402
from tiangong2_task.submission import (  # noqa: E402
    SUBMIT_ENDPOINT,
    Tiangong2SubmitClient,
    authorize_submit,
    build_submit_plan,
    validate_pre_submit_drift,
    validate_submit_plan,
    verify_submit_readback,
)


SOURCE = '''# -*- coding: utf-8 -*-
field_mapping = {"data_type": "数据类型"}
query_sql = """
SELECT 'old' AS data_type
"""
#.format(dt = dt)
# === end 用户自定义参数，需要修改 ===
# === 默认参数，不需要修改 ===
app_id = 'company-app-id'
app_secret = 'company-secret-value'
# === end 默认参数，不需要修改 ===
print(query_sql)
'''

def make_task() -> ScopedTask:
    return ScopedTask(
        project={"id": 308, "name": "project"},
        menu={"id": 101900, "name": "market_conversion_2_lark", "ifDir": 0, "taskType": 4},
        metadata={
            "taskId": 46817,
            "taskName": "market_conversion_2_lark",
            "taskType": 4,
            "principal": "lvshuai01",
            "creator": "lvshuai01",
            "nezhaId": 65369,
        },
        path=("数据开发", "吕帅", "市场顾问-数据播报", "market_conversion_2_lark"),
        project_id=308,
        folder_name="吕帅",
        menu_id=101900,
        task_id=46817,
        nezha_task_id=65369,
        task_name="market_conversion_2_lark",
        owner_name="lvshuai01",
    )


class FakeReader:
    def __init__(self, source: str = SOURCE):
        self.source = source
        self.metadata = dict(make_task().metadata)
        self.versions = [
            {
                "id": 1,
                "status": "已发布",
                "ver": "V1",
                "publishTime": "2026-08-16 12:00:00",
            }
        ]

    def get_task_content(self, *, menu_id, task_id, task_type):
        return TASK_CONTENT_SPECS[task_type], {"python": self.source, "resourceId": None}

    def get_task(self, menu_id):
        return dict(self.metadata)

    def list_versions(self, task_id):
        return copy.deepcopy(self.versions)

    def get_version_code(self, version_id):
        return {"code": SOURCE.replace("SELECT 'old'", "SELECT 'published'")}


class FakeResponse:
    ok = True
    status = 200

    def json(self):
        return {"status": "success", "errorCode": 0, "data": {"accepted": True}}


class FakeRequest:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse()


class Tiangong2QueryUpdateTests(unittest.TestCase):
    def test_projection_changes_only_query_and_preserves_company_block(self) -> None:
        projected, old_regions = project_query_update(
            SOURCE,
            "SELECT 'new' AS data_type",
        )
        new_regions = extract_query_regions(projected)
        self.assertEqual(old_regions.default_block, new_regions.default_block)
        self.assertIn("SELECT 'new' AS data_type", projected)
        self.assertNotIn("SELECT 'old' AS data_type", projected)
        self.assertIn("company-secret-value", projected)

    def test_plan_contains_hashes_not_source_and_enforces_drift(self) -> None:
        reader = FakeReader()
        with tempfile.TemporaryDirectory() as directory:
            sql_path = Path(directory) / "replacement.sql"
            sql_path.write_text("SELECT 'new' AS data_type\n", encoding="utf-8")
            plan = build_query_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                replacement_sql_file=sql_path,
            )
            self.assertEqual(plan["status"], "ready")
            self.assertNotIn("company-secret-value", str(plan))
            authorization = authorize_query_update(
                plan,
                expected_plan_sha256=plan["plan_sha256"],
                confirm_save_query=True,
            )
            self.assertEqual(authorization.task_id, 46817)
            projected, _ = prepare_query_update(reader, task=make_task(), plan=plan)
            reader.source = projected
            readback = verify_query_update_readback(reader, task=make_task(), plan=plan)
            self.assertTrue(readback["fully_verified"])
            reader.source += "# drift\n"
            with self.assertRaisesRegex(UsageError, "precondition drifted"):
                prepare_query_update(reader, task=make_task(), plan=plan)

    def test_query_update_writer_is_single_use_and_exact_task(self) -> None:
        reader = FakeReader()
        with tempfile.TemporaryDirectory() as directory:
            sql_path = Path(directory) / "replacement.sql"
            sql_path.write_text("SELECT 'new' AS data_type\n", encoding="utf-8")
            plan = build_query_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                replacement_sql_file=sql_path,
            )
            authorization = authorize_query_update(
                plan,
                expected_plan_sha256=plan["plan_sha256"],
                confirm_save_query=True,
            )
            request = FakeRequest()
            writer = Tiangong2QueryUpdateClient(
                request,
                authorization=authorization,
                dp_api_base="https://example/dp",
            )
            with self.assertRaisesRegex(UsageError, "task id"):
                writer.save_python(task_id=999, source=SOURCE, resource_id=0)
            self.assertEqual(request.calls, [])
            writer = Tiangong2QueryUpdateClient(
                request,
                authorization=authorization,
                dp_api_base="https://example/dp",
            )
            writer.save_python(task_id=46817, source=SOURCE, resource_id=0)
            self.assertEqual(request.calls[0][0], "https://example/dp/dataDevelop/savePython")
            self.assertEqual(request.calls[0][1]["form"]["taskId"], "46817")
            self.assertEqual(request.calls[0][1]["form"]["resourceId"], "0")
            self.assertEqual(text_sha256(request.calls[0][1]["form"]["python"]), text_sha256(SOURCE))
            with self.assertRaisesRegex(UsageError, "single-use"):
                writer.save_python(task_id=46817, source=SOURCE, resource_id=0)


class Tiangong2CapabilityBoundaryTests(unittest.TestCase):
    def test_full_source_replacement_commands_are_not_exposed(self) -> None:
        parser = build_parser()
        subparsers = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        commands = set(subparsers.choices)
        self.assertIn("plan-task-query-update", commands)
        self.assertIn("apply-task-query-update", commands)
        self.assertNotIn("plan-task-source-replacement", commands)
        self.assertNotIn("apply-task-source-replacement", commands)


class Tiangong2ExecuteOnceTests(unittest.TestCase):
    @staticmethod
    def make_plan() -> dict:
        payload = {
            "schema_version": "tiangong2-task-execution-plan-v1",
            "operation": "execute_owned_published_tiangong2_task_once",
            "status": "ready",
            "identity": {"id": 249907, "name": "lvshuai01"},
            "scope": {
                "project_id": 308,
                "folder": "吕帅",
                "menu_id": 101900,
                "task_id": 46817,
                "nezha_task_id": 65369,
                "task_name": "market_conversion_2_lark",
                "owner_name": "lvshuai01",
            },
            "execution": {
                "period_time": "2026-08-17 17:30:00",
                "trigger_successor": False,
                "params": {},
                "disabled_stages": [],
            },
            "baseline": {"baseline_execution_ids": [1, 2]},
        }
        return finalize_hash(payload, "plan_sha256")

    def test_execute_plan_and_writer_are_hash_bound_single_use(self) -> None:
        plan = self.make_plan()
        validate_execution_plan(plan)
        tampered = copy.deepcopy(plan)
        tampered["execution"]["trigger_successor"] = True
        with self.assertRaisesRegex(UsageError, "SHA-256"):
            validate_execution_plan(tampered)
        authorization = authorize_execution(
            plan,
            expected_plan_sha256=plan["plan_sha256"],
            confirm_execute=True,
        )
        request = FakeRequest()
        writer = Tiangong2ExecuteOnceClient(
            request,
            authorization=authorization,
            api_base="https://example/nezha",
        )
        writer.execute_once(task_id=65369, period_time="2026-08-17 17:30:00")
        self.assertEqual(request.calls[0][0], f"https://example/nezha/{EXECUTE_ENDPOINT}")
        self.assertEqual(
            request.calls[0][1]["data"],
            {
                "triggerSuccessor": False,
                "periodTime": "2026-08-17 17:30:00",
                "params": {},
                "taskId": 65369,
                "disabledStages": [],
            },
        )
        with self.assertRaisesRegex(UsageError, "single-use"):
            writer.execute_once(task_id=65369, period_time="2026-08-17 17:30:00")


class Tiangong2SubmitTests(unittest.TestCase):
    def test_submit_plan_is_note_hash_bound_and_rejects_tampering(self) -> None:
        reader = FakeReader()
        plan = build_submit_plan(
            reader,
            task=make_task(),
            identity={"id": 249907, "name": "lvshuai01"},
            note="修复KOC导入SQL_移除高风险多表广播连接",
        )
        self.assertEqual(plan["status"], "ready")
        self.assertNotIn("company-secret-value", str(plan))
        validate_submit_plan(plan)
        tampered = copy.deepcopy(plan)
        tampered["submission"]["note"] = "different"
        with self.assertRaisesRegex(UsageError, "SHA-256"):
            validate_submit_plan(tampered)

    def test_submit_writer_is_exact_and_single_use(self) -> None:
        note = "修复KOC导入SQL_移除高风险多表广播连接"
        reader = FakeReader()
        plan = build_submit_plan(
            reader,
            task=make_task(),
            identity={"id": 249907, "name": "lvshuai01"},
            note=note,
        )
        authorization = authorize_submit(
            plan,
            expected_plan_sha256=plan["plan_sha256"],
            confirm_submit=True,
        )
        request = FakeRequest()
        writer = Tiangong2SubmitClient(
            request,
            authorization=authorization,
            dp_api_base="https://example/dp",
        )
        with self.assertRaisesRegex(UsageError, "task id"):
            writer.submit_task(task_id=999, note=note)
        self.assertEqual(request.calls, [])
        writer = Tiangong2SubmitClient(
            request,
            authorization=authorization,
            dp_api_base="https://example/dp",
        )
        writer.submit_task(task_id=46817, note=note)
        self.assertEqual(request.calls[0][0], f"https://example/dp/{SUBMIT_ENDPOINT}")
        self.assertEqual(
            request.calls[0][1]["form"],
            {"taskId": "46817", "note": note},
        )
        with self.assertRaisesRegex(UsageError, "single-use"):
            writer.submit_task(task_id=46817, note=note)

    def test_submit_drift_and_readback_are_explicit(self) -> None:
        reader = FakeReader()
        plan = build_submit_plan(
            reader,
            task=make_task(),
            identity={"id": 249907, "name": "lvshuai01"},
            note="修复KOC导入SQL_移除高风险多表广播连接",
        )
        validate_pre_submit_drift(reader, task=make_task(), plan=plan)
        reader.metadata["updateTime"] = "2026-08-17 17:30:00"
        with self.assertRaisesRegex(UsageError, "precondition drifted"):
            validate_pre_submit_drift(reader, task=make_task(), plan=plan)
        readback = verify_submit_readback(
            reader,
            task=make_task(),
            plan=plan,
            attempts=1,
            delay_seconds=0,
        )
        self.assertTrue(readback["submit_state_observed"])
        self.assertTrue(readback["fully_verified"])


if __name__ == "__main__":
    unittest.main()
