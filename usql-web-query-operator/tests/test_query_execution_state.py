from __future__ import annotations

import base64
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.editor import set_monaco_sql  # noqa: E402
from usql_web_query.engine import (  # noqa: E402
    engine_label_matches,
    normalize_query_engine,
    recognize_engine_value,
)
from usql_web_query.executor import click_run, summarize_submission_response  # noqa: E402
from usql_web_query.result_resolution import resolve_result_state  # noqa: E402
from usql_web_query.status_poller_api import (  # noqa: E402
    _new_query_id,
    _query_status_from_api,
    fetch_query_result_evidence,
    wait_for_query_result_evidence,
)


class FakeEditorFrame:
    url = "https://uanalysis.baijia.com/sql/index"

    def __init__(self, *, accept_write: bool = True) -> None:
        self.value = ""
        self.accept_write = accept_write

    def evaluate(self, script: str, arg=None):
        if "cm.setValue(sql)" in script:
            if self.accept_write:
                self.value = base64.b64decode(arg).decode("utf-8")
            return True
        if "CodeMirror.getValue()" in script:
            return self.value
        raise AssertionError("unexpected editor script")


class FakeEditorPage:
    def __init__(self, frame: FakeEditorFrame) -> None:
        self.frames = [frame]

    def wait_for_timeout(self, _milliseconds: int) -> None:
        return None


class FakeRequest:
    method = "POST"

    def __init__(self, payload) -> None:
        self.post_data_json = payload
        self.post_data = json.dumps(payload)


class FakeResponse:
    def __init__(self, payload, response_payload, *, url: str, status: int = 200) -> None:
        self.request = FakeRequest(payload)
        self._payload = response_payload
        self.url = url
        self.status = status
        self.ok = 200 <= status < 300

    def json(self):
        return self._payload


class FakeResultRequestClient:
    def __init__(self, response: FakeResponse | list[FakeResponse]) -> None:
        self.responses = response if isinstance(response, list) else [response]
        self.calls = []

    def post(self, url: str, **kwargs):
        self.calls.append((url, kwargs))
        index = min(len(self.calls) - 1, len(self.responses) - 1)
        return self.responses[index]


class FakeResultPage:
    def __init__(self, response: FakeResponse | list[FakeResponse]) -> None:
        self.context = type("Context", (), {"request": FakeResultRequestClient(response)})()

    def wait_for_timeout(self, _milliseconds: int) -> None:
        return None


class FakeSubmitPage:
    def __init__(self) -> None:
        self.listeners = {}

    def on(self, event: str, callback) -> None:
        self.listeners[event] = callback

    def remove_listener(self, event: str, callback) -> None:
        if self.listeners.get(event) is callback:
            self.listeners.pop(event)

    def wait_for_timeout(self, _milliseconds: int) -> None:
        return None


class QueryExecutionStateTests(unittest.TestCase):
    def test_editor_requires_exact_stable_hash_readback(self) -> None:
        sql = "select '中文' as value limit 1"
        evidence = set_monaco_sql(FakeEditorPage(FakeEditorFrame()), sql)
        self.assertEqual(evidence.sql_sha256, hashlib.sha256(sql.encode("utf-8")).hexdigest())
        self.assertEqual(evidence.byte_length, len(sql.encode("utf-8")))
        self.assertEqual(evidence.stable_reads, 2)

    def test_editor_hash_mismatch_fails_without_exposing_sql(self) -> None:
        sql = "select sensitive_value from governed_source"
        with self.assertRaises(UsageError) as raised:
            set_monaco_sql(
                FakeEditorPage(FakeEditorFrame(accept_write=False)),
                sql,
                timeout_ms=0,
            )
        self.assertNotIn(sql, str(raised.exception))
        self.assertIn("expected=", str(raised.exception))

    def test_engine_labels_and_backend_values_are_normalized(self) -> None:
        self.assertEqual(normalize_query_engine(None), "presto-lakehouse")
        self.assertEqual(normalize_query_engine("Presto_lakehouse"), "presto-lakehouse")
        self.assertTrue(engine_label_matches("presto", "Presto"))
        self.assertFalse(engine_label_matches("presto", "Presto_lakehouse"))
        self.assertTrue(engine_label_matches("presto-lakehouse", "Presto_lakehouse"))
        self.assertTrue(engine_label_matches("doris-presto", "Doris-Presto / doris内测加速版"))
        self.assertEqual(recognize_engine_value("dlc_presto_lakehouse"), "presto-lakehouse")

    def test_submission_response_keeps_hashes_and_query_id_not_sql(self) -> None:
        sql = "select 1 as probe_value limit 1"
        response = FakeResponse(
            {"executeSql": sql, "engine": "Presto_lakehouse"},
            {"data": {"queryId": 1525000001}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/query/execute",
        )
        summary = summarize_submission_response(response)
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary["query_id"], "1525000001")
        self.assertEqual(summary["submitted_engine"], "Presto_lakehouse")
        self.assertEqual(summary["submitted_sql_sha256"], hashlib.sha256(sql.encode()).hexdigest())
        self.assertNotIn(sql, json.dumps(summary))

    def test_result_list_response_is_not_mistaken_for_query_submission(self) -> None:
        response = FakeResponse(
            {"id": "1525000013", "pageSize": 5},
            {"data": {"meta": [{"name": "id"}], "data": [{"id": "1525999999"}]}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/result/list",
        )
        self.assertIsNone(summarize_submission_response(response))

    def test_generic_query_list_response_is_not_submission_acknowledgement(self) -> None:
        response = FakeResponse(
            {"pageSize": 20},
            {"data": {"list": [{"id": "1525999999"}]}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/query/list",
        )
        self.assertIsNone(summarize_submission_response(response))

    def test_exact_query_id_binding_does_not_discover_a_different_task(self) -> None:
        page = type("Page", (), {"frames": []})()
        query_id, row = _new_query_id(
            page,
            {"1525000010"},
            "select 1",
            exact_query_id="1525000011",
        )
        self.assertEqual(query_id, "1525000011")
        self.assertEqual(row["query_id"], "1525000011")

    def test_status_api_records_which_exact_query_source_completed(self) -> None:
        with (
            patch(
                "usql_web_query.status_poller_api._query_status_from_result_api",
                return_value=None,
            ),
            patch(
                "usql_web_query.status_poller_api._query_status_from_log_api",
                return_value=("Success", "query_id=1525000011", None),
            ),
        ):
            status = _query_status_from_api(object(), "1525000011")
        self.assertEqual(status, ("Success", "query_id=1525000011", None, "log_api"))

    def test_click_run_uses_one_control_action_and_one_query_id(self) -> None:
        page = FakeSubmitPage()
        with (
            patch("usql_web_query.executor.dismiss_nps_if_present"),
            patch("usql_web_query.executor._click_one_run_control", return_value="button") as click_control,
            patch(
                "usql_web_query.executor._matching_new_history_row",
                return_value={"query_id": "1525000012", "text": "select 1"},
            ),
            patch("usql_web_query.executor.extract_open_query_tab_ids", return_value=set()),
        ):
            evidence = click_run(page, {"1525000010"}, "select 1")
        click_control.assert_called_once_with(page)
        self.assertEqual(evidence.query_id, "1525000012")
        self.assertEqual(evidence.attempt_count, 1)
        self.assertEqual(evidence.query_id_source, "matching_history_row")

    def test_result_api_classifies_rows_and_builds_bounded_preview(self) -> None:
        response = FakeResponse(
            {},
            {
                "errorCode": 0,
                "data": {
                    "meta": [{"name": "probe_value"}],
                    "data": [[1], [2]],
                    "total": 2,
                },
            },
            url="https://uanalysis.baijia.com/uanalysis-sql/api/result/list",
        )
        evidence = fetch_query_result_evidence(FakeResultPage(response), "1525000002", max_rows=1)
        self.assertEqual(evidence["state"], "success_with_rows")
        self.assertEqual(evidence["meta_count"], 1)
        self.assertEqual(evidence["row_count_page"], 2)
        self.assertEqual(evidence["total_rows"], 2)
        self.assertEqual(evidence["preview"]["rows"], [[1]])

    def test_result_api_explicit_zero_total_is_verified_empty(self) -> None:
        response = FakeResponse(
            {},
            {"errorCode": 0, "data": {"meta": [{"name": "probe_value"}], "data": [], "total": 0}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/result/list",
        )
        evidence = fetch_query_result_evidence(FakeResultPage(response), "1525000003")
        self.assertEqual(evidence["state"], "success_empty_verified")
        self.assertEqual(evidence["row_count_page"], 0)
        self.assertEqual(evidence["total_rows"], 0)

    def test_result_api_empty_without_total_remains_candidate(self) -> None:
        response = FakeResponse(
            {},
            {"errorCode": 0, "data": {"meta": [{"name": "probe_value"}], "data": []}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/result/list",
        )
        evidence = fetch_query_result_evidence(FakeResultPage(response), "1525000006")
        self.assertEqual(evidence["state"], "success_empty_candidate")
        self.assertIsNone(evidence["total_rows"])

    def test_empty_candidate_requires_exact_completion_evidence(self) -> None:
        evidence = {
            "state": "success_empty_candidate",
            "source": "result_api",
            "preview": {"headers": ["probe_value"], "rows": [], "row_count_visible": 0},
        }
        unresolved, preview, unresolved_evidence = resolve_result_state(
            evidence,
            None,
            completion_source="ui_result",
        )
        verified, verified_preview, verified_evidence = resolve_result_state(
            evidence,
            None,
            completion_source="log_api",
        )
        self.assertEqual(unresolved, "result_unresolved")
        self.assertIsNone(preview)
        self.assertEqual(unresolved_evidence["completion_source"], "ui_result")
        self.assertEqual(verified, "success_empty_verified")
        self.assertEqual(verified_preview["row_count_visible"], 0)
        self.assertEqual(verified_evidence["completion_source"], "log_api")

    def test_explicit_api_zero_and_ui_rows_is_unresolved_conflict(self) -> None:
        state, preview, evidence = resolve_result_state(
            {
                "state": "success_empty_verified",
                "source": "result_api",
                "preview": {"headers": ["probe_value"], "rows": [], "row_count_visible": 0},
            },
            {"headers": ["probe_value"], "rows": [[1]], "row_count_visible": 1},
            completion_source="result_api",
        )
        self.assertEqual(state, "result_unresolved")
        self.assertIsNone(preview)
        self.assertEqual(evidence["evidence_conflict"], "api_zero_ui_rows")
        self.assertEqual(evidence["source"], "result_api_and_ui")

    def test_api_rows_survive_missing_ui(self) -> None:
        state, preview, evidence = resolve_result_state(
            {
                "state": "success_with_rows",
                "source": "result_api",
                "preview": {"headers": ["probe_value"], "rows": [[1]], "row_count_visible": 1},
            },
            None,
            completion_source="result_api",
        )
        self.assertEqual(state, "success_ui_missing_recovered")
        self.assertEqual(preview["rows"], [[1]])
        self.assertEqual(evidence["source"], "result_api")

    def test_result_api_wait_retries_pending_payload(self) -> None:
        pending = FakeResponse(
            {},
            {"errorCode": 0, "data": {}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/result/list",
        )
        ready = FakeResponse(
            {},
            {"errorCode": 0, "data": {"meta": [{"name": "probe_value"}], "data": [[1]], "total": 1}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/result/list",
        )
        page = FakeResultPage([pending, ready])
        evidence = wait_for_query_result_evidence(page, "1525000007", timeout_ms=100)
        self.assertEqual(evidence["state"], "success_with_rows")
        self.assertGreaterEqual(len(page.context.request.calls), 2)

    def test_result_api_wait_does_not_freeze_transient_empty_candidate(self) -> None:
        candidate = FakeResponse(
            {},
            {"errorCode": 0, "data": {"meta": [{"name": "probe_value"}], "data": []}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/result/list",
        )
        ready = FakeResponse(
            {},
            {"errorCode": 0, "data": {"meta": [{"name": "probe_value"}], "data": [[1]]}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/result/list",
        )
        page = FakeResultPage([candidate, ready])
        evidence = wait_for_query_result_evidence(page, "1525000009", timeout_ms=100)
        self.assertEqual(evidence["state"], "success_with_rows")
        self.assertGreaterEqual(len(page.context.request.calls), 2)

    def test_result_api_preserves_failure_text_for_structured_error_handling(self) -> None:
        response = FakeResponse(
            {},
            {"errorCode": 0, "data": {"message": "PRESTO_EXECUTE_DQL_ERROR: stage limit"}},
            url="https://uanalysis.baijia.com/uanalysis-sql/api/result/list",
        )
        evidence = fetch_query_result_evidence(FakeResultPage(response), "1525000008")
        self.assertEqual(evidence["state"], "result_api_failed")
        self.assertIn("stage limit", evidence["failure_message"])


if __name__ == "__main__":
    unittest.main()
