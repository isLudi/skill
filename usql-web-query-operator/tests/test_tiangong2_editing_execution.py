from __future__ import annotations

import argparse
import copy
import json
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
from tiangong2_task.maintenance import (  # noqa: E402
    PATCH_FILE_SCHEMA_VERSION,
    Tiangong2PythonPatchClient,
    activate_maintenance_session,
    authorize_phase_with_maintenance_session,
    authorize_python_patch,
    build_maintenance_session_plan,
    build_python_patch_plan,
    prepare_python_patch,
    project_python_patch,
    validate_maintenance_session_activation,
    verify_python_patch_readback,
)
from tiangong2_task.publishing import finalize_hash, text_sha256  # noqa: E402
from tiangong2_task.query_quality import SQL_REVIEW_SCHEMA_VERSION  # noqa: E402
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
        menu={"id": 101900, "name": "market2lark_koc", "ifDir": 0, "taskType": 4},
        metadata={
            "taskId": 46817,
            "taskName": "market2lark_koc",
            "taskType": 4,
            "principal": "lvshuai01",
            "creator": "lvshuai01",
            "nezhaId": 65369,
        },
        path=("数据开发", "吕帅", "市场顾问-数据播报", "market2lark_koc"),
        project_id=308,
        folder_name="吕帅",
        menu_id=101900,
        task_id=46817,
        nezha_task_id=65369,
        task_name="market2lark_koc",
        owner_name="lvshuai01",
    )


def write_sql_review(
    path: Path,
    sql: str,
    *,
    output_columns: list[str] | None = None,
    justifications: list[dict[str, str]] | None = None,
) -> Path:
    payload = {
        "schema_version": SQL_REVIEW_SCHEMA_VERSION,
        "sql_sha256": text_sha256(sql.strip("\r\n")),
        "review_method": "code-simplifier",
        "accuracy": {
            "status": "passed",
            "output_grain": "one test row",
            "required_output_columns": output_columns or ["data_type"],
            "invariants": ["the reviewed output contract is stable"],
            "evidence": [{"type": "unit_test", "reference": "test fixture"}],
        },
        "simplification": {
            "status": "passed",
            "changes": ["kept one explicit projection"],
            "preserved_semantics": ["data_type remains the only output"],
            "repeated_processing_removed": ["no repeated branch is present"],
        },
        "performance": {
            "status": "static_passed",
            "runtime_evidence": [],
            "justifications": justifications or [],
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


class FakeReader:
    def __init__(self, source: str = SOURCE):
        self.source = source
        self.metadata = dict(make_task().metadata)
        self.schedule = {
            "taskId": make_task().task_id,
            "scheduleType": 0,
            "executorGroup": "new_bigdata",
        }
        self.versions = [
            {
                "id": 1,
                "status": "已发布",
                "ver": "V1",
                "publishTime": "2026-08-16 12:00:00",
            }
        ]
        self.version_codes = {
            1: SOURCE.replace("SELECT 'old'", "SELECT 'published'"),
        }

    def get_task_content(self, *, menu_id, task_id, task_type):
        return TASK_CONTENT_SPECS[task_type], {"python": self.source, "resourceId": None}

    def get_task(self, menu_id):
        return dict(self.metadata)

    def get_schedule(self, task_id):
        return copy.deepcopy(self.schedule)

    def list_versions(self, task_id):
        return copy.deepcopy(self.versions)

    def get_version_code(self, version_id):
        return {"code": self.version_codes[version_id]}


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
            replacement_sql = "SELECT 'new' AS data_type\n"
            sql_path.write_text(replacement_sql, encoding="utf-8")
            review_path = write_sql_review(Path(directory) / "review.json", replacement_sql)
            plan = build_query_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                replacement_sql_file=sql_path,
                sql_review_file=review_path,
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
            replacement_sql = "SELECT 'new' AS data_type\n"
            sql_path.write_text(replacement_sql, encoding="utf-8")
            review_path = write_sql_review(Path(directory) / "review.json", replacement_sql)
            plan = build_query_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                replacement_sql_file=sql_path,
                sql_review_file=review_path,
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

    def test_sql_quality_gate_blocks_physical_star_and_repeated_union_source(self) -> None:
        reader = FakeReader()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            star_sql = "SELECT * FROM db.fact_table\n"
            star_path = root / "star.sql"
            star_path.write_text(star_sql, encoding="utf-8")
            star_review = write_sql_review(root / "star-review.json", star_sql)
            star_plan = build_query_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                replacement_sql_file=star_path,
                sql_review_file=star_review,
            )
            self.assertEqual("blocked_sql_quality", star_plan["status"])
            self.assertIn(
                "physical_select_star",
                star_plan["sql_quality_gate"]["static_analysis"]["hard_error_codes"],
            )

            union_sql = """WITH base AS (SELECT 'new' AS data_type)
SELECT data_type FROM base
UNION ALL SELECT data_type FROM base
UNION ALL SELECT data_type FROM base
"""
            union_path = root / "union.sql"
            union_path.write_text(union_sql, encoding="utf-8")
            union_review = write_sql_review(root / "union-review.json", union_sql)
            union_plan = build_query_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                replacement_sql_file=union_path,
                sql_review_file=union_review,
            )
            self.assertEqual("blocked_sql_quality", union_plan["status"])
            unresolved = union_plan["sql_quality_gate"]["static_analysis"][
                "unresolved_review_codes"
            ]
            self.assertIn("repeated_union_source", unresolved)

    def test_sql_quality_review_drift_blocks_apply(self) -> None:
        reader = FakeReader()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replacement_sql = "SELECT 'new' AS data_type\n"
            sql_path = root / "replacement.sql"
            sql_path.write_text(replacement_sql, encoding="utf-8")
            review_path = write_sql_review(root / "review.json", replacement_sql)
            plan = build_query_update_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                replacement_sql_file=sql_path,
                sql_review_file=review_path,
            )
            review = json.loads(review_path.read_text(encoding="utf-8"))
            review["accuracy"]["invariants"].append("review changed after planning")
            review_path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(UsageError, "drifted after planning"):
                prepare_query_update(reader, task=make_task(), plan=plan)


class Tiangong2CapabilityBoundaryTests(unittest.TestCase):
    def test_exact_patch_and_maintenance_session_replace_full_source_replacement(self) -> None:
        parser = build_parser()
        subparsers = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        commands = set(subparsers.choices)
        self.assertIn("plan-task-query-update", commands)
        self.assertIn("apply-task-query-update", commands)
        self.assertIn("plan-task-maintenance-session", commands)
        self.assertIn("authorize-task-maintenance-session", commands)
        self.assertIn("plan-task-python-patch", commands)
        self.assertIn("apply-task-python-patch", commands)
        self.assertNotIn("plan-task-source-replacement", commands)
        self.assertNotIn("apply-task-source-replacement", commands)
        plan_parser = subparsers.choices["plan-task-query-update"]
        review_action = next(
            action for action in plan_parser._actions if "--sql-review-file" in action.option_strings
        )
        self.assertTrue(review_action.required)


class Tiangong2MaintenanceSessionTests(unittest.TestCase):
    @staticmethod
    def write_patch(path: Path, *, old: str, new: str) -> Path:
        path.write_text(
            json.dumps(
                {
                    "schema_version": PATCH_FILE_SCHEMA_VERSION,
                    "replacements": [
                        {"old": old, "new": new, "expected_count": 1},
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path

    def make_session(self, reader: FakeReader, *, max_executions: int = 3) -> dict:
        plan = build_maintenance_session_plan(
            reader,
            task=make_task(),
            identity={"id": 249907, "name": "lvshuai01"},
            reason="修复IP渠道校验并完成写入验收",
            duration_minutes=120,
            max_executions=max_executions,
            baseline_execution_ids=[1, 2],
        )
        validate_maintenance_session_activation(
            reader,
            task=make_task(),
            plan=plan,
            current_execution_ids=[1, 2],
        )
        return activate_maintenance_session(
            plan,
            expected_plan_sha256=plan["plan_sha256"],
            confirm_maintenance=True,
        )

    def test_exact_patch_preserves_query_default_block_and_secrets(self) -> None:
        reader = FakeReader()
        with tempfile.TemporaryDirectory() as directory:
            patch_path = self.write_patch(
                Path(directory) / "patch.json",
                old="print(query_sql)",
                new="print('validated', query_sql)",
            )
            plan = build_python_patch_plan(
                reader,
                task=make_task(),
                identity={"id": 249907, "name": "lvshuai01"},
                patch_file=patch_path,
            )
            self.assertEqual(plan["status"], "ready")
            self.assertNotIn("company-secret-value", str(plan))
            self.assertNotIn("print(query_sql)", str(plan))
            projected, _ = prepare_python_patch(reader, task=make_task(), plan=plan)
            self.assertIn("company-secret-value", projected)
            self.assertIn("SELECT 'old' AS data_type", projected)
            self.assertIn("print('validated', query_sql)", projected)
            session = self.make_session(reader)
            context = authorize_phase_with_maintenance_session(
                session,
                phase_plan=plan,
                operation="python_patch_save",
            )
            authorization = authorize_python_patch(
                plan,
                expected_plan_sha256=plan["plan_sha256"],
                confirmed=bool(context),
            )
            request = FakeRequest()
            writer = Tiangong2PythonPatchClient(
                request,
                authorization=authorization,
                dp_api_base="https://example/dp",
            )
            writer.save_python(task_id=46817, source=projected, resource_id=0)
            self.assertEqual(len(request.calls), 1)
            reader.source = projected
            self.assertTrue(
                verify_python_patch_readback(reader, task=make_task(), plan=plan)[
                    "fully_verified"
                ]
            )

    def test_patch_rejects_query_default_block_and_secret_named_regions(self) -> None:
        query_patch = {
            "schema_version": PATCH_FILE_SCHEMA_VERSION,
            "replacements": [
                {
                    "old": "SELECT 'old' AS data_type",
                    "new": "SELECT 'new' AS data_type",
                    "expected_count": 1,
                }
            ],
        }
        with self.assertRaisesRegex(UsageError, "cannot change query_sql"):
            project_python_patch(SOURCE, query_patch)
        with tempfile.TemporaryDirectory() as directory:
            secret_patch = self.write_patch(
                Path(directory) / "secret.json",
                old="app_secret = 'company-secret-value'",
                new="app_secret = 'another-secret-value'",
            )
            with self.assertRaisesRegex(UsageError, "secret-named"):
                build_python_patch_plan(
                    FakeReader(),
                    task=make_task(),
                    identity={"id": 249907, "name": "lvshuai01"},
                    patch_file=secret_patch,
                )

    def test_session_is_exact_scope_and_execution_budget_is_bounded(self) -> None:
        reader = FakeReader()
        session = self.make_session(reader, max_executions=1)
        phase_plan = Tiangong2ExecuteOnceTests.make_plan()
        phase_plan["baseline"]["baseline_execution_ids"] = [1, 2, 3]
        phase_plan = finalize_hash(phase_plan, "plan_sha256")
        with self.assertRaisesRegex(UsageError, "budget is exhausted"):
            authorize_phase_with_maintenance_session(
                session,
                phase_plan=phase_plan,
                operation="execute",
            )
        different_scope = copy.deepcopy(phase_plan)
        different_scope["scope"]["owner_name"] = "other-user"
        different_scope = finalize_hash(different_scope, "plan_sha256")
        with self.assertRaisesRegex(UsageError, "scope mismatch"):
            authorize_phase_with_maintenance_session(
                session,
                phase_plan=different_scope,
                operation="publish",
            )


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
                "task_name": "market2lark_koc",
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
    def test_submit_plan_blocks_matching_unpublished_version(self) -> None:
        reader = FakeReader()
        reader.versions.append(
            {"id": 2, "status": "未发布", "ver": "-", "publishTime": "2026-08-20"}
        )
        reader.version_codes[2] = SOURCE
        plan = build_submit_plan(
            reader,
            task=make_task(),
            identity={"id": 249907, "name": "lvshuai01"},
            note="IP双渠道最简查询_20260820",
        )
        self.assertEqual(plan["status"], "blocked_already_submitted")
        self.assertEqual(plan["baseline"]["matching_unpublished_version_ids"], [2])

    def test_submit_plan_blocks_unconfigured_schedule_before_write(self) -> None:
        reader = FakeReader()
        reader.schedule["taskId"] = None
        plan = build_submit_plan(
            reader,
            task=make_task(),
            identity={"id": 249907, "name": "lvshuai01"},
            note="IP双渠道最简查询_20260820",
        )
        self.assertEqual(plan["status"], "blocked_unconfigured_schedule")
        self.assertFalse(plan["schedule_precondition"]["configured"])
        with self.assertRaisesRegex(UsageError, "blocked"):
            authorize_submit(
                plan,
                expected_plan_sha256=plan["plan_sha256"],
                confirm_submit=True,
            )

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
        reader.schedule["retryInterval"] = 10
        with self.assertRaisesRegex(UsageError, "schedule_state_sha256"):
            validate_pre_submit_drift(reader, task=make_task(), plan=plan)
        reader.schedule.pop("retryInterval")
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
