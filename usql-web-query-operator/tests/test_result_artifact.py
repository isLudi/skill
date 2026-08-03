from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.query_contract import QueryPlanContract  # noqa: E402
from usql_web_query.query_trace_bridge import prepare_query_trace  # noqa: E402
from usql_web_query.result_artifact import (  # noqa: E402
    build_result_artifact,
    validate_result_artifact,
    write_result_artifact,
)


class ResultArtifactTests(unittest.TestCase):
    def test_artifact_redacts_rows_and_hashes_preview(self) -> None:
        preview = {
            "headers": ["period", "metric_value"],
            "rows": [["sensitive-period", "123"]],
            "row_count_visible": 1,
            "no_more": True,
        }
        artifact = build_result_artifact(
            trace_id="trace_" + "a" * 32,
            domain="market_consultant",
            plan_id="plan_0123456789abcdef0123",
            sql_sha256="b" * 64,
            policy_report_sha256="c" * 64,
            ok=True,
            status="Success",
            query_id="query_example",
            requested_engine="presto",
            selected_engine_label="Presto",
            history_engine="Presto",
            query_duration_seconds=1.0,
            elapsed_seconds=2.0,
            result_preview=preview,
            download_path=None,
            expected_columns=("period", "metric_value"),
        )

        rendered = json.dumps(artifact, ensure_ascii=False)
        self.assertNotIn("sensitive-period", rendered)
        self.assertNotIn('"rows"', rendered)
        self.assertEqual(artifact["validation"]["status"], "passed")
        self.assertTrue(artifact["result"]["preview_rows_redacted"])
        validate_result_artifact(artifact)

    def test_expected_column_miss_is_warning_only(self) -> None:
        artifact = build_result_artifact(
            trace_id="trace_" + "d" * 32,
            domain="qingcheng",
            plan_id=None,
            sql_sha256="e" * 64,
            policy_report_sha256="f" * 64,
            ok=True,
            status="Success",
            query_id=None,
            requested_engine="presto",
            selected_engine_label=None,
            history_engine=None,
            query_duration_seconds=None,
            elapsed_seconds=None,
            result_preview={"headers": ["observed"], "rows": [["1"]], "row_count_visible": 1, "no_more": True},
            download_path=None,
            expected_columns=("expected",),
        )
        self.assertEqual(artifact["validation"]["status"], "warning")
        self.assertIn(
            "EXPECTED_RESULT_COLUMNS_MISSING",
            {item["code"] for item in artifact["validation"]["diagnostics"]},
        )

    def test_artifact_and_trace_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = QueryPlanContract(
                source_path=root / "plan.json",
                source_sha256="1" * 64,
                schema_version="2.0.0",
                domain="market_consultant",
                status="executable",
                sql_sha256="2" * 64,
                execution_policy={"allow_download": False},
                plan_id="plan_0123456789abcdef0123",
                expected_columns=("value",),
            )
            trace, trace_path = prepare_query_trace(
                requested_path=None,
                artifacts_dir=root,
                sql_sha256="2" * 64,
                query_plan_contract=contract,
            )
            artifact = build_result_artifact(
                trace_id=trace["trace_id"],
                domain=contract.domain,
                plan_id=contract.plan_id,
                sql_sha256=contract.sql_sha256,
                policy_report_sha256="3" * 64,
                ok=False,
                status="Failed",
                query_id=None,
                requested_engine=None,
                selected_engine_label=None,
                history_engine=None,
                query_duration_seconds=None,
                elapsed_seconds=None,
                result_preview=None,
                download_path=None,
                expected_columns=contract.expected_columns,
            )
            artifact_path = root / "result_artifact.json"
            write_result_artifact(artifact_path, artifact)

            self.assertTrue(trace_path.is_file())
            self.assertTrue(artifact_path.is_file())
            self.assertEqual(json.loads(artifact_path.read_text(encoding="utf-8"))["trace_id"], trace["trace_id"])

    def test_existing_trace_rejects_plan_or_sql_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = QueryPlanContract(
                source_path=root / "plan.json",
                source_sha256="4" * 64,
                schema_version="2.0.0",
                domain="qingcheng",
                status="executable",
                sql_sha256="5" * 64,
                execution_policy={"allow_download": False},
                plan_id="plan_0123456789abcdef0123",
            )
            _, trace_path = prepare_query_trace(
                requested_path=root / "trace.json",
                artifacts_dir=root,
                sql_sha256=first.sql_sha256,
                query_plan_contract=first,
            )
            drifted_plan = QueryPlanContract(
                source_path=root / "plan.json",
                source_sha256="6" * 64,
                schema_version="2.0.0",
                domain="qingcheng",
                status="executable",
                sql_sha256=first.sql_sha256,
                execution_policy={"allow_download": False},
                plan_id=first.plan_id,
            )
            with self.assertRaisesRegex(UsageError, "plan_sha256"):
                prepare_query_trace(
                    requested_path=trace_path,
                    artifacts_dir=root,
                    sql_sha256=first.sql_sha256,
                    query_plan_contract=drifted_plan,
                )
            with self.assertRaisesRegex(UsageError, "sql_sha256"):
                prepare_query_trace(
                    requested_path=trace_path,
                    artifacts_dir=root,
                    sql_sha256="7" * 64,
                    query_plan_contract=first,
                )


if __name__ == "__main__":
    unittest.main()
