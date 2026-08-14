from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.config import DEFAULT_STATE, DEFAULT_TIANGONG2_TASK_STATE, TIANGONG2_TASK_RUNTIME_DIR  # noqa: E402
from _shared.errors import UsageError  # noqa: E402
from tiangong2_task.artifacts import write_artifact_bundle  # noqa: E402
from tiangong2_task.cli import build_parser, cmd_explore  # noqa: E402
from tiangong2_task.config import TASK_CONTENT_SPECS  # noqa: E402
from tiangong2_task.explorer import Tiangong2TaskExplorer, _normalized_editor_source  # noqa: E402


class FakeExplorerClient:
    def __init__(self) -> None:
        self.used_endpoints = {"GET base/menu/listProjects"}
        self.tree = {
            -1: [{"id": 1, "name": "数据开发", "ifDir": 1}],
            1: [
                {"id": 2, "name": "关赛楠", "ifDir": 1},
                {"id": 3, "name": "申宝鑫", "ifDir": 1},
            ],
            2: [{"id": 10, "name": "refund_job", "ifDir": 0, "taskId": 100, "taskType": 4}],
            3: [{"id": 4, "name": "nested", "ifDir": 1}],
            4: [{"id": 11, "name": "shell_job", "ifDir": 0, "taskId": 101, "taskType": 5}],
        }
        self.sources = {
            100: 'PASSWORD="literal-secret-value"\nCREATE TABLE mart.refund AS SELECT * FROM dw.refund_detail',
            101: "#!/bin/bash\nhive -e 'select * from dw.source_table'",
        }

    def list_projects(self):
        return [{"id": 308, "name": "H业务线-精品班学部"}]

    def list_menu_children(self, project_id, parent_id):
        self.used_endpoints.add("POST form/menu/listMenus")
        return self.tree.get(parent_id, [])

    def task_type_mapping(self):
        return [{"code": 4, "enumName": "PYTHON"}, {"code": 5, "enumName": "SHELL"}]

    def list_quality_inventory(self, project_id):
        return [{"tableName": "mart.refund", "description": "refund output"}]

    def get_task(self, menu_id):
        task_id = 100 if menu_id == 10 else 101
        task_type = 4 if menu_id == 10 else 5
        return {"taskId": task_id, "taskName": self.tree[2][0]["name"] if menu_id == 10 else "shell_job", "taskType": task_type}

    def get_task_content(self, *, menu_id, task_id, task_type):
        spec = TASK_CONTENT_SPECS[task_type]
        key = spec.source_keys[0]
        return spec, {key: self.sources[task_id], "resourceId": None}

    def get_schedule(self, task_id):
        return {"taskId": task_id, "scheduleType": 1, "runInterval": 1, "timeUnit": 2}

    def list_resources(self, menu_id):
        return []

    def list_versions(self, task_id):
        return [{"id": task_id + 1000, "ver": "V1", "status": "已发布"}]

    def get_version_code(self, version_id):
        return {"code": self.sources[version_id - 1000], "info": "V1"}


def make_snapshot():
    client = FakeExplorerClient()
    return client, Tiangong2TaskExplorer(client).explore(
        identity={"id": 1, "name": "reader", "displayName": "Reader"},
        login_performed=True,
        project_id=308,
        folder_names=["关赛楠", "申宝鑫"],
        include_version_code=True,
    )


class Tiangong2ExplorerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client, self.snapshot = make_snapshot()

    def test_recursive_exact_folder_exploration_covers_every_task(self) -> None:
        self.assertEqual(len(self.snapshot.tasks), 2)
        self.assertEqual(self.snapshot.tasks[1].path, ["数据开发", "申宝鑫", "nested", "shell_job"])
        self.assertTrue(all(task.current_matches_latest_published for task in self.snapshot.tasks))

    def test_secret_is_redacted_and_quality_link_is_preserved(self) -> None:
        task = self.snapshot.tasks[0]
        self.assertNotIn("literal-secret-value", task.current_source.redacted_text)
        self.assertTrue(task.current_source.redactions)
        self.assertEqual(task.analysis["matching_quality_tables"][0]["tableName"], "mart.refund")

    def test_duplicate_folder_request_is_rejected(self) -> None:
        with self.assertRaisesRegex(UsageError, "Duplicate"):
            Tiangong2TaskExplorer(self.client).explore(
                identity={},
                login_performed=False,
                project_id=308,
                folder_names=["关赛楠", "关赛楠"],
                include_version_code=False,
            )

    def test_kyuubi_version_ui_wrapper_is_ignored_for_comparison(self) -> None:
        current = "insert overwrite table db.t\nselect 1"
        version = "sql:insert overwrite table db.t\nselect 1\n SQL参数:参数名:${dt}\n 运行参数:"
        self.assertEqual(
            _normalized_editor_source("kyuubi_sql", current),
            _normalized_editor_source("kyuubi_sql", version),
        )


class Tiangong2ArtifactTests(unittest.TestCase):
    def test_bundle_stays_in_runtime_and_contains_only_redacted_source(self) -> None:
        TIANGONG2_TASK_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        _, snapshot = make_snapshot()
        with tempfile.TemporaryDirectory(dir=TIANGONG2_TASK_RUNTIME_DIR) as tmp:
            run_dir = write_artifact_bundle(snapshot, Path(tmp))
            inventory = json.loads((run_dir / "inventory.json").read_text(encoding="utf-8"))
            source_path = run_dir / inventory["tasks"][0]["current_source"]["runtime_file"]
            source_text = source_path.read_text(encoding="utf-8")
            self.assertNotIn("literal-secret-value", source_text)
            self.assertIn("<redacted>", source_text)
            self.assertTrue((run_dir / "summary.md").is_file())
            self.assertTrue((run_dir / "manifest.json").is_file())

    def test_artifact_path_outside_runtime_is_rejected(self) -> None:
        _, snapshot = make_snapshot()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(UsageError, "isolated runtime"):
                write_artifact_bundle(snapshot, Path(tmp))


class Tiangong2CliTests(unittest.TestCase):
    def test_explore_parser_uses_isolated_state_and_runtime(self) -> None:
        args = build_parser().parse_args(
            ["explore", "--project-id", "308", "--folder", "关赛楠"]
        )
        self.assertEqual(args.state_path, DEFAULT_TIANGONG2_TASK_STATE)
        self.assertNotEqual(args.state_path, DEFAULT_STATE)
        self.assertTrue(str(args.artifacts_dir).startswith(str(TIANGONG2_TASK_RUNTIME_DIR)))
        self.assertFalse(args.include_version_code)

    def test_outside_artifact_path_is_rejected_before_browser_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(artifacts_dir=Path(tmp))
            with patch("tiangong2_task.cli.import_playwright") as browser_import:
                with self.assertRaisesRegex(UsageError, "isolated runtime"):
                    cmd_explore(args)
        browser_import.assert_not_called()
if __name__ == "__main__":
    unittest.main()
