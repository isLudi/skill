from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.config import DEFAULT_TIANGONG2_TASK_STATE, TIANGONG2_TASK_RUNTIME_DIR  # noqa: E402
from _shared.errors import UsageError  # noqa: E402
from tiangong2_task.cli import build_parser  # noqa: E402
from tiangong2_task.config import TASK_CONTENT_SPECS  # noqa: E402
from tiangong2_task.publishing import (  # noqa: E402
    Tiangong2PublishClient,
    authorize_publish,
    build_publish_plan,
    task_publish_lock,
    validate_pre_publish_drift,
    validate_publish_plan,
    verify_publish_readback,
)
from tiangong2_task.scope import ScopedTask, resolve_owned_task  # noqa: E402


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
            "updateTime": "2026-08-16 14:30:00",
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


class FakeTaskClient:
    def __init__(self):
        self.current_source = 'print("new")\n'
        self.versions = [
            {"id": 1, "ver": "V1", "status": "已发布", "publishTime": "2026-08-15"},
            {"id": 2, "ver": "-", "status": "未发布", "publishTime": "2026-08-16"},
        ]
        self.version_codes = {1: 'print("old")\n', 2: self.current_source}

    def get_task_content(self, *, menu_id, task_id, task_type):
        return TASK_CONTENT_SPECS[task_type], {"python": self.current_source}

    def list_versions(self, task_id):
        return copy.deepcopy(self.versions)

    def get_version_code(self, version_id):
        return {"code": self.version_codes[version_id]}


class FakeResponse:
    ok = True
    status = 200

    def json(self):
        return {"status": "success", "error": None, "errorCode": 0, "data": {"id": 101900}}


class FakePublishRequest:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse()


class AmbiguousPublishRequest:
    def post(self, url, **kwargs):
        raise TimeoutError("ambiguous timeout")


class Tiangong2PublishPlanTests(unittest.TestCase):
    def test_plan_is_hash_bound_and_blocks_identical_published_source(self) -> None:
        client = FakeTaskClient()
        plan = build_publish_plan(
            client,
            task=make_task(),
            identity={"id": 1, "name": "lvshuai01", "displayName": "吕帅"},
        )
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["publish_target"]["version_id"], 2)
        validate_publish_plan(plan)
        tampered = copy.deepcopy(plan)
        tampered["scope"]["menu_id"] = 999
        with self.assertRaisesRegex(UsageError, "SHA-256"):
            validate_publish_plan(tampered)

        client.version_codes[1] = client.current_source
        blocked = build_publish_plan(
            client,
            task=make_task(),
            identity={"id": 1, "name": "lvshuai01", "displayName": "吕帅"},
        )
        self.assertEqual(blocked["status"], "blocked_already_published")

    def test_authorization_requires_confirmation_exact_hash_and_ready_plan(self) -> None:
        plan = build_publish_plan(
            FakeTaskClient(),
            task=make_task(),
            identity={"id": 1, "name": "lvshuai01"},
        )
        with self.assertRaisesRegex(UsageError, "confirm-publish"):
            authorize_publish(plan, expected_plan_sha256=plan["plan_sha256"], confirm_publish=False)
        with self.assertRaisesRegex(UsageError, "hash mismatch"):
            authorize_publish(plan, expected_plan_sha256="0" * 64, confirm_publish=True)

    def test_pre_publish_drift_and_version_readback_are_enforced(self) -> None:
        client = FakeTaskClient()
        task = make_task()
        plan = build_publish_plan(client, task=task, identity={"id": 1, "name": "lvshuai01"})
        validate_pre_publish_drift(client, task=task, plan=plan)
        client.current_source = 'print("changed-after-plan")\n'
        with self.assertRaisesRegex(UsageError, "drifted"):
            validate_pre_publish_drift(client, task=task, plan=plan)

        client.current_source = 'print("new")\n'
        client.versions = [
            {"id": 2, "ver": "V2", "status": "已发布", "publishTime": "2026-08-16"},
            {"id": 1, "ver": "V1", "status": "历史版本", "publishTime": "2026-08-15"},
        ]
        client.version_codes[2] = client.current_source
        readback = verify_publish_readback(
            client,
            task=task,
            plan=plan,
            attempts=1,
            delay_seconds=0,
        )
        self.assertTrue(readback["fully_verified"])


class Tiangong2PublishClientTests(unittest.TestCase):
    def test_write_client_is_single_use_and_exact_menu_only(self) -> None:
        plan = build_publish_plan(
            FakeTaskClient(),
            task=make_task(),
            identity={"id": 1, "name": "lvshuai01"},
        )
        authorization = authorize_publish(
            plan,
            expected_plan_sha256=plan["plan_sha256"],
            confirm_publish=True,
        )
        request = FakePublishRequest()
        client = Tiangong2PublishClient(
            request,
            authorization=authorization,
            dp_api_base="https://example/dp",
        )
        with self.assertRaisesRegex(UsageError, "menu id"):
            client.publish_task(999)
        self.assertEqual(request.calls, [])

        client = Tiangong2PublishClient(
            request,
            authorization=authorization,
            dp_api_base="https://example/dp",
        )
        client.publish_task(101900)
        self.assertEqual(request.calls[0][0], "https://example/dp/dataDevelop/publishTask")
        self.assertEqual(request.calls[0][1]["form"], {"id": "101900"})
        with self.assertRaisesRegex(UsageError, "single-use"):
            client.publish_task(101900)
        self.assertEqual(len(request.calls), 1)

        ambiguous = Tiangong2PublishClient(
            AmbiguousPublishRequest(),
            authorization=authorization,
            dp_api_base="https://example/dp",
        )
        with self.assertRaises(TimeoutError):
            ambiguous.publish_task(101900)
        self.assertEqual(ambiguous.write_count, 1)

    def test_same_menu_publish_lock_rejects_concurrent_local_writer(self) -> None:
        with task_publish_lock(987654321):
            with self.assertRaisesRegex(UsageError, "another Tiangong2 publish"):
                with task_publish_lock(987654321):
                    pass


class FakeScopeClient:
    def __init__(self, owner="lvshuai01", creator=None):
        self.owner = owner
        self.creator = owner if creator is None else creator
        self.tree = {
            -1: [{"id": 1, "name": "数据开发", "ifDir": 1}],
            1: [{"id": 2, "name": "吕帅", "ifDir": 1}, {"id": 3, "name": "其他人", "ifDir": 1}],
            2: [{"id": 4, "name": "市场顾问-数据播报", "ifDir": 1}],
            4: [{"id": 101900, "name": "market_conversion_2_lark", "ifDir": 0, "taskId": 46817}],
        }

    def list_projects(self):
        return [{"id": 308, "name": "project"}]

    def list_menu_children(self, project_id, parent_id):
        return self.tree.get(parent_id, [])

    def get_task(self, menu_id):
        return {
            "taskId": 46817,
            "taskName": "market_conversion_2_lark",
            "taskType": 4,
            "principal": self.owner,
            "creator": self.creator,
            "nezhaId": 65369,
        }


class Tiangong2ScopeAndParserTests(unittest.TestCase):
    def test_scope_accepts_numeric_principal_matching_authenticated_identity_id(self) -> None:
        scoped = resolve_owned_task(
            FakeScopeClient(owner="249907", creator="lvshuai01"),
            identity={"id": 249907, "name": "lvshuai01"},
            project_id=308,
            folder_name="吕帅",
            menu_id=101900,
            task_name="market_conversion_2_lark",
        )
        self.assertEqual(scoped.owner_name, "lvshuai01")

    def test_scope_rejects_different_numeric_principal_even_when_creator_matches(self) -> None:
        with self.assertRaisesRegex(UsageError, "not owned"):
            resolve_owned_task(
                FakeScopeClient(owner="999999", creator="lvshuai01"),
                identity={"id": 249907, "name": "lvshuai01"},
                project_id=308,
                folder_name="吕帅",
                menu_id=101900,
                task_name="market_conversion_2_lark",
            )

    def test_scope_rejects_cross_owner_and_cross_folder(self) -> None:
        with self.assertRaisesRegex(UsageError, "not owned"):
            resolve_owned_task(
                FakeScopeClient(owner="other", creator="lvshuai01"),
                identity={"name": "lvshuai01"},
                project_id=308,
                folder_name="吕帅",
                menu_id=101900,
                task_name="market_conversion_2_lark",
            )
        with self.assertRaisesRegex(UsageError, "not uniquely found"):
            resolve_owned_task(
                FakeScopeClient(),
                identity={"name": "lvshuai01"},
                project_id=308,
                folder_name="其他人",
                menu_id=101900,
                task_name="market_conversion_2_lark",
            )

    def test_new_commands_keep_isolated_state_and_runtime_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "fetch-execution-log",
                "--project-id",
                "308",
                "--folder",
                "吕帅",
                "--menu-id",
                "101900",
                "--task-name",
                "market_conversion_2_lark",
                "--exec-id",
                "164912112",
            ]
        )
        self.assertEqual(args.state_path, DEFAULT_TIANGONG2_TASK_STATE)
        self.assertTrue(str(args.artifacts_dir).startswith(str(TIANGONG2_TASK_RUNTIME_DIR)))


if __name__ == "__main__":
    unittest.main()
