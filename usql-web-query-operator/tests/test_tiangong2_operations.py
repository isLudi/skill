from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.config import TIANGONG2_TASK_RUNTIME_DIR  # noqa: E402
from _shared.errors import UsageError  # noqa: E402
from tiangong2_task.operations import (  # noqa: E402
    Tiangong2OperationsReadOnlyClient,
    fetch_execution_log_bundle,
    write_execution_log_bundle,
)
from tiangong2_task.scope import ScopedTask  # noqa: E402


class FakeResponse:
    ok = True
    status = 200

    def __init__(self, data, page_query=None):
        self._data = data
        self._page_query = page_query

    def json(self):
        return {
            "status": "success",
            "error": None,
            "errorCode": 0,
            "data": self._data,
            "pageQuery": self._page_query,
        }


class FakeRequest:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if url.endswith("getTaskAndSchedule"):
            return FakeResponse({"taskId": 65369, "taskName": "market_conversion_2_lark"})
        if url.endswith("getTaskExecutionDetail"):
            return FakeResponse(
                {
                    "taskExecutionId": 164912112,
                    "taskName": "market_conversion_2_lark",
                    "status": 7,
                    "statusDesc": "failed",
                    "stageExecutions": [
                        {
                            "id": 166979167,
                            "taskId": 65369,
                            "stageName": "market_conversion_2_lark",
                            "statusDesc": "failed",
                        }
                    ],
                }
            )
        raise AssertionError(url)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        payload = kwargs.get("data") or kwargs.get("form") or {}
        if url.endswith("listTaskExecutionPeriods"):
            return FakeResponse(
                [
                    {
                        "id": 160175153,
                        "taskId": 65369,
                        "taskName": "market_conversion_2_lark",
                        "taskExecutionId": 164912112,
                        "periodTime": "2026-08-16 14:36:00",
                        "statusDesc": "stage执行失败",
                    }
                ],
                {"pageTotal": 1},
            )
        if url.endswith("listTaskExecutions"):
            return FakeResponse(
                [
                    {
                        "id": 164912112,
                        "taskId": 65369,
                        "taskName": "market_conversion_2_lark",
                        "statusDesc": "stage执行失败",
                        "periodTime": payload["periodTime"],
                    }
                ]
            )
        if url.endswith("getStageLog"):
            begin = int(payload["beginPos"])
            if begin == 0:
                return FakeResponse(
                    {
                        "stageExecutionId": 166979167,
                        "hasMore": True,
                        "nextBeginPos": 10,
                        "data": 'PASSWORD="literal-stage-secret"\n执行sql失败\n',
                    }
                )
            return FakeResponse(
                {
                    "stageExecutionId": 166979167,
                    "hasMore": False,
                    "nextBeginPos": None,
                    "data": "Caused by: org.apache.spark.util.SparkFatalException\n"
                    "at BroadcastExchangeExec.scala:183\n",
                }
            )
        raise AssertionError(url)


def make_task() -> ScopedTask:
    return ScopedTask(
        project={"id": 308, "name": "project"},
        menu={"id": 101900, "name": "market_conversion_2_lark", "ifDir": 0},
        metadata={
            "taskId": 46817,
            "taskName": "market_conversion_2_lark",
            "taskType": 4,
            "principal": "lvshuai01",
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


class Tiangong2OperationsClientTests(unittest.TestCase):
    def test_exact_read_chain_and_stage_log_pagination(self) -> None:
        request = FakeRequest()
        client = Tiangong2OperationsReadOnlyClient(request, api_base="https://example/nezha")
        bundle = fetch_execution_log_bundle(client, task=make_task(), execution_id=164912112)
        self.assertIn("SparkFatalException", bundle["stages"][0]["log"])
        stage_calls = [call for call in request.calls if call[1].endswith("getStageLog")]
        self.assertEqual([call[2]["form"]["beginPos"] for call in stage_calls], ["0", "10"])
        period_call = next(call for call in request.calls if call[1].endswith("listTaskExecutionPeriods"))
        execution_call = next(call for call in request.calls if call[1].endswith("listTaskExecutions"))
        self.assertIn("data", period_call[2])
        self.assertIn("form", execution_call[2])

    def test_non_allowlisted_operations_endpoint_is_blocked_before_network(self) -> None:
        request = FakeRequest()
        client = Tiangong2OperationsReadOnlyClient(request)
        with self.assertRaisesRegex(UsageError, "Blocked non-allowlisted"):
            client._post_json_body("task/execute", {"taskId": 65369})
        self.assertEqual(request.calls, [])


class Tiangong2ExecutionArtifactTests(unittest.TestCase):
    def test_log_bundle_is_redacted_and_runtime_only(self) -> None:
        TIANGONG2_TASK_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        request = FakeRequest()
        client = Tiangong2OperationsReadOnlyClient(request, api_base="https://example/nezha")
        bundle = fetch_execution_log_bundle(client, task=make_task(), execution_id=164912112)
        with tempfile.TemporaryDirectory(dir=TIANGONG2_TASK_RUNTIME_DIR) as tmp:
            run_dir = write_execution_log_bundle(
                task=make_task(),
                identity={"id": 1, "name": "lvshuai01", "displayName": "吕帅"},
                execution_id=164912112,
                bundle=bundle,
                used_endpoints=client.used_endpoints,
                artifact_root=Path(tmp),
            )
            payload = json.loads((run_dir / "execution.json").read_text(encoding="utf-8"))
            log_file = run_dir / payload["stages"][0]["log_file"]
            log_text = log_file.read_text(encoding="utf-8")
            self.assertNotIn("literal-stage-secret", log_text)
            self.assertIn("<redacted>", log_text)
            self.assertEqual(payload["diagnostic"]["classification"], "spark_broadcast_exchange_fatal")
            self.assertFalse(payload["diagnostic"]["deeper_nested_cause_exposed"])
            self.assertTrue((run_dir / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
