from __future__ import annotations

import unittest
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError
from tiangong2_task.client import Tiangong2ReadOnlyClient
from tiangong2_task.config import FORM_READ_ENDPOINTS, JSON_READ_ENDPOINTS


class FakeResponse:
    ok = True
    status = 200

    def __init__(self, data):
        self._data = data

    def json(self):
        return {"status": "success", "error": None, "errorCode": 0, "data": self._data, "pageQuery": None}


class FakeRequestContext:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if url.endswith("listProjects"):
            return FakeResponse([{"id": 308, "name": "project"}])
        return FakeResponse({"name": "reader"})

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        if url.endswith("listMenus"):
            return FakeResponse({"menus": []})
        if url.endswith("getScheduleConfig"):
            return FakeResponse({"taskId": 1})
        if url.endswith("resource/task/list"):
            return FakeResponse([])
        return FakeResponse([])


class Tiangong2ReadOnlyClientTests(unittest.TestCase):
    def test_form_and_json_transports_are_explicit(self) -> None:
        request = FakeRequestContext()
        client = Tiangong2ReadOnlyClient(request, dp_api_base="https://example/dp", base_api_base="https://example/base")
        client.list_menu_children(308, -1)
        client.get_schedule(1)
        menu_call, schedule_call = request.calls
        self.assertIn("form", menu_call[2])
        self.assertNotIn("data", menu_call[2])
        self.assertIn("data", schedule_call[2])
        self.assertNotIn("form", schedule_call[2])

    def test_non_allowlisted_endpoint_is_blocked_before_request(self) -> None:
        request = FakeRequestContext()
        client = Tiangong2ReadOnlyClient(request)
        with self.assertRaisesRegex(UsageError, "Blocked non-allowlisted"):
            client._post_form_body("dataDevelop/savePython", {})
        self.assertEqual(request.calls, [])

    def test_registry_contains_no_write_named_endpoints(self) -> None:
        lowered = " ".join(sorted(FORM_READ_ENDPOINTS | JSON_READ_ENDPOINTS)).lower()
        for term in ("save", "delete", "publish", "starttest", "newtask"):
            self.assertNotIn(term, lowered)


if __name__ == "__main__":
    unittest.main()
