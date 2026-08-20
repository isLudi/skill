from __future__ import annotations

import contextlib
import io
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

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.cli import build_parser  # noqa: E402
from usql_web_query.commands.run import RunCommandOutcome  # noqa: E402
from usql_web_query.commands.run_with_fallback import cmd_run_with_fallback  # noqa: E402
from usql_web_query.engine_fallback import (  # noqa: E402
    decide_fallback,
    load_engine_fallback_registry,
    REGISTRY_SCHEMA_PATH,
    resolve_fallback_engine,
)
from usql_web_query.models import RunSummary  # noqa: E402
from usql_web_query.query_execution_group import (  # noqa: E402
    build_attempt_record,
    build_query_execution_group_artifact,
    validate_query_execution_group_artifact,
)
from usql_web_query.result_artifact import (  # noqa: E402
    build_result_artifact,
    write_result_artifact,
)


SQL_HASH = "a" * 64
POLICY_HASH = "b" * 64


def _outcome(
    root: Path,
    *,
    attempt_no: int,
    engine: str,
    status: str,
    ok: bool,
    result_state: str | None,
    error_details: dict | None = None,
    submission_status: int | None = 200,
) -> RunCommandOutcome:
    attempt_dir = root / f"attempt_{attempt_no}"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    trace_id = "trace_" + f"{attempt_no:x}" * 32
    trace_path = attempt_dir / "query_trace.json"
    trace = {"trace_id": trace_id}
    trace_path.write_text(json.dumps(trace), encoding="utf-8")
    has_rows = result_state in {
        "success_with_rows",
        "success_ui_missing_recovered",
        "success_with_rows_ui",
    }
    is_empty = result_state == "success_empty_verified"
    preview = None
    if has_rows:
        preview = {
            "headers": ["probe_value"],
            "rows": [["sensitive-row"]],
            "row_count_visible": 1,
            "no_more": True,
        }
    elif is_empty:
        preview = {
            "headers": ["probe_value"],
            "rows": [],
            "row_count_visible": 0,
            "no_more": True,
        }
    query_id = f"15250000{attempt_no:02d}"
    summary = RunSummary(
        ok=ok,
        status=status,
        message="test summary",
        artifacts_dir=str(attempt_dir),
        query_id=query_id,
        result_preview=preview,
        error_details=error_details,
        requested_engine=engine,
        selected_engine_label=engine,
        selected_engine_key=engine,
        elapsed_seconds=float(attempt_no),
        error_category="query_log_error" if error_details else None,
        submission_evidence={
            "query_id_source": "submission_response",
            "attempt_count": 1,
            "http_status": submission_status,
            "submitted_sql_sha256": SQL_HASH,
        },
        result_state=result_state,
        result_evidence={"source": "result_api", "completion_source": "result_api"},
        ui_result_state="ui_timeout" if result_state == "result_unresolved" else "ui_with_rows",
    )
    artifact = build_result_artifact(
        trace_id=trace_id,
        domain="unresolved",
        plan_id=None,
        sql_sha256=SQL_HASH,
        policy_report_sha256=POLICY_HASH,
        ok=ok,
        status=status,
        query_id=query_id,
        requested_engine=engine,
        selected_engine_label=engine,
        history_engine=engine,
        selected_engine_key=engine,
        query_duration_seconds=1.0,
        elapsed_seconds=float(attempt_no),
        result_preview=preview,
        download_path=None,
        editor_evidence={"sql_sha256": SQL_HASH, "byte_length": 8, "stable_reads": 2},
        submission_evidence=summary.submission_evidence,
        result_state=result_state,
        result_evidence=summary.result_evidence,
        ui_result_state=summary.ui_result_state,
    )
    artifact_path = attempt_dir / "result_artifact.json"
    write_result_artifact(artifact_path, artifact)
    summary.provenance = {
        "query_trace": {"path": str(trace_path), "trace_id": trace_id},
        "result_artifact": {
            "path": str(artifact_path),
            "artifact_id": artifact["artifact_id"],
            "artifact_sha256": artifact["artifact_sha256"],
        },
    }
    return RunCommandOutcome(
        exit_code=0 if ok else 1,
        summary=summary,
        result_artifact_path=artifact_path,
        result_artifact=artifact,
        query_trace_path=trace_path,
        query_trace=trace,
    )


def _args(root: Path, **overrides):
    sql_path = root / "query.sql"
    sql_path.write_text("select 1", encoding="utf-8")
    values = {
        "sql_file": sql_path,
        "query_plan": None,
        "engine": "presto-lakehouse",
        "fallback_engine": None,
        "empty_result_policy": "stop",
        "group_artifact": None,
        "artifacts_dir": root / "runtime",
        "download": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class EngineFallbackTests(unittest.TestCase):
    def test_registry_confirms_lakehouse_default_and_reciprocal_presto_backup(self) -> None:
        registry, registry_sha256 = load_engine_fallback_registry()
        self.assertEqual(registry["default_primary"], "presto-lakehouse")
        self.assertEqual(registry["default_fallback_by_primary"]["presto-lakehouse"], "presto")
        self.assertEqual(registry["default_fallback_by_primary"]["presto"], "presto-lakehouse")
        self.assertEqual(len(registry_sha256), 64)
        resolution = resolve_fallback_engine(
            "presto-lakehouse",
            requested_fallback=None,
            domain=None,
        )
        self.assertEqual(resolution.fallback_engine, "presto")
        self.assertEqual(resolution.resolution_source, "default_equivalent")
        self.assertEqual(resolution.equivalence_group, "presto_equivalent_directory")
        reverse = resolve_fallback_engine("presto", requested_fallback=None, domain=None)
        self.assertEqual(reverse.fallback_engine, "presto-lakehouse")

    def test_registry_rejects_default_engine_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry, _ = load_engine_fallback_registry()
            registry["default_primary"] = "presto"
            registry_path = Path(temp_dir) / "query_engine_fallbacks.json"
            registry_path.write_text(
                json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(UsageError, "default differs from the CLI"):
                load_engine_fallback_registry(
                    registry_path,
                    REGISTRY_SCHEMA_PATH,
                )

    def test_doris_requires_explicit_or_domain_resolution(self) -> None:
        resolution = resolve_fallback_engine(
            "presto",
            requested_fallback="doris-presto",
            domain=None,
        )
        self.assertEqual(resolution.fallback_engine, "doris-presto")
        self.assertEqual(resolution.resolution_source, "explicit")
        self.assertIsNone(resolution.equivalence_group)
        with self.assertRaises(UsageError):
            resolve_fallback_engine("presto", requested_fallback="presto", domain=None)

    def test_domain_registry_can_select_doris_without_making_it_global_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry, _ = load_engine_fallback_registry()
            registry["domain_overrides"]["qingcheng"] = {"presto": "doris-presto"}
            registry_path = Path(temp_dir) / "query_engine_fallbacks.json"
            registry_path.write_text(
                json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            resolution = resolve_fallback_engine(
                "presto",
                requested_fallback=None,
                domain="qingcheng",
                registry_path=registry_path,
                registry_schema_path=REGISTRY_SCHEMA_PATH,
            )
        self.assertEqual(resolution.fallback_engine, "doris-presto")
        self.assertEqual(resolution.resolution_source, "domain_registered")
        self.assertIsNone(resolution.equivalence_group)

    def test_run_parser_keeps_fallback_disabled_by_default(self) -> None:
        parser = build_parser()
        ordinary = parser.parse_args(["run", "--sql-file", "query.sql"])
        explicit = parser.parse_args(["run-with-fallback", "--sql-file", "query.sql"])
        self.assertFalse(hasattr(ordinary, "fallback_engine"))
        self.assertEqual(ordinary.engine, "presto-lakehouse")
        self.assertEqual(explicit.engine, "presto-lakehouse")
        self.assertIsNone(explicit.fallback_engine)
        self.assertEqual(explicit.empty_result_policy, "stop")

    def test_only_unresolved_or_explicit_transient_errors_are_eligible(self) -> None:
        unresolved = RunSummary(False, "Success", "", "runtime", result_state="result_unresolved")
        transient = RunSummary(
            False,
            "Failed",
            "service unavailable",
            "runtime",
            error_details={"source": "log_area", "detail": "503 service unavailable"},
        )
        syntax = RunSummary(
            False,
            "Failed",
            "service unavailable after syntax failure",
            "runtime",
            error_details={"source": "log_area", "detail": "syntax error; service unavailable"},
        )
        timeout = RunSummary(False, "Timeout", "timed out", "runtime")
        empty = RunSummary(True, "Success", "", "runtime", result_state="success_empty_verified")
        submission_503 = RunSummary(
            False,
            "Failed",
            "submission failed",
            "runtime",
            submission_evidence={"http_status": 503},
        )
        self.assertEqual(decide_fallback(unresolved).trigger, "result_unresolved")
        self.assertEqual(decide_fallback(transient).trigger, "engine_transient_error")
        self.assertEqual(decide_fallback(submission_503).transient_error_code, "submission_http_503")
        self.assertFalse(decide_fallback(syntax).eligible)
        self.assertFalse(decide_fallback(timeout).eligible)
        self.assertFalse(decide_fallback(empty).eligible)

    def test_group_artifact_is_redacted_and_hash_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = _outcome(
                root,
                attempt_no=1,
                engine="presto",
                status="Success",
                ok=False,
                result_state="result_unresolved",
            )
            fallback = _outcome(
                root,
                attempt_no=2,
                engine="presto-lakehouse",
                status="Success",
                ok=True,
                result_state="success_with_rows",
            )
            resolution = resolve_fallback_engine("presto", requested_fallback=None, domain=None)
            artifact = build_query_execution_group_artifact(
                resolution=resolution,
                empty_result_policy="stop",
                attempts=[
                    build_attempt_record(primary, attempt_no=1, role="primary"),
                    build_attempt_record(fallback, attempt_no=2, role="fallback"),
                ],
                final_status="fallback_success",
                final_ok=True,
                selected_attempt=2,
                fallback_trigger="result_unresolved",
                eligibility_reason="exact_result_unresolved",
                alternate_result_adopted=True,
                cross_engine_consistency="not_checked",
            )
            validate_query_execution_group_artifact(artifact)
            rendered = json.dumps(artifact, ensure_ascii=False)
            self.assertEqual(artifact["fallback_policy"]["mode"], "fallback_once")
            self.assertNotIn("sensitive-row", rendered)
            self.assertNotIn('"rows"', rendered)

    def test_group_rejects_child_sql_hash_reference_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = _outcome(
                root,
                attempt_no=1,
                engine="presto",
                status="Failed",
                ok=False,
                result_state=None,
            )
            record = build_attempt_record(primary, attempt_no=1, role="primary")
            record["sql_sha256"] = "c" * 64
            resolution = resolve_fallback_engine("presto", requested_fallback=None, domain=None)
            with self.assertRaisesRegex(ValueError, "SQL hash reference drifted"):
                build_query_execution_group_artifact(
                    resolution=resolution,
                    empty_result_policy="stop",
                    attempts=[record],
                    final_status="primary_failed_not_eligible",
                    final_ok=False,
                    selected_attempt=None,
                    fallback_trigger=None,
                    eligibility_reason="no_explicit_transient_engine_evidence",
                    alternate_result_adopted=False,
                    cross_engine_consistency="not_checked",
                )

    def test_unresolved_runs_one_default_fallback_and_adopts_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = _outcome(root, attempt_no=1, engine="presto-lakehouse", status="Success", ok=False, result_state="result_unresolved")
            fallback = _outcome(root, attempt_no=2, engine="presto", status="Success", ok=True, result_state="success_with_rows")
            with patch(
                "usql_web_query.commands.run_with_fallback.execute_run",
                side_effect=[primary, fallback],
            ) as execute:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = cmd_run_with_fallback(_args(root))
            self.assertEqual(exit_code, 0)
            self.assertEqual(execute.call_count, 2)
            self.assertEqual(execute.call_args_list[0].args[0].engine, "presto-lakehouse")
            self.assertEqual(execute.call_args_list[1].args[0].engine, "presto")
            group_path = next((root / "runtime" / "fallback-groups").rglob("query_execution_group.json"))
            group = json.loads(group_path.read_text(encoding="utf-8"))
            self.assertEqual(group["final"]["status"], "fallback_success")
            self.assertEqual(group["final"]["selected_attempt"], 2)

    def test_verified_empty_stops_without_crosscheck(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = _outcome(root, attempt_no=1, engine="presto-lakehouse", status="Success", ok=True, result_state="success_empty_verified")
            with patch(
                "usql_web_query.commands.run_with_fallback.execute_run",
                return_value=primary,
            ) as execute:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = cmd_run_with_fallback(_args(root))
            self.assertEqual(exit_code, 0)
            execute.assert_called_once()

    def test_explicit_transient_error_runs_exactly_one_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = _outcome(
                root,
                attempt_no=1,
                engine="presto-lakehouse",
                status="Failed",
                ok=False,
                result_state=None,
                error_details={"source": "log_area", "detail": "coordinator temporarily unavailable"},
            )
            fallback = _outcome(
                root,
                attempt_no=2,
                engine="presto",
                status="Success",
                ok=True,
                result_state="success_with_rows",
            )
            with patch(
                "usql_web_query.commands.run_with_fallback.execute_run",
                side_effect=[primary, fallback],
            ) as execute:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = cmd_run_with_fallback(_args(root))
            self.assertEqual(exit_code, 0)
            self.assertEqual(execute.call_count, 2)
            group_path = next((root / "runtime" / "fallback-groups").rglob("query_execution_group.json"))
            group = json.loads(group_path.read_text(encoding="utf-8"))
            self.assertEqual(group["final"]["fallback_trigger"], "engine_transient_error")
            self.assertEqual(group["final"]["eligibility_reason"], "engine_temporarily_unavailable")

    def test_crosscheck_only_never_adopts_alternate_rows_or_downloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = _outcome(root, attempt_no=1, engine="presto-lakehouse", status="Success", ok=True, result_state="success_empty_verified")
            fallback = _outcome(root, attempt_no=2, engine="presto", status="Success", ok=True, result_state="success_with_rows")
            with patch(
                "usql_web_query.commands.run_with_fallback.execute_run",
                side_effect=[primary, fallback],
            ) as execute:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exit_code = cmd_run_with_fallback(
                        _args(root, empty_result_policy="crosscheck-only", download=True)
                    )
            self.assertEqual(exit_code, 1)
            self.assertFalse(execute.call_args_list[1].args[0].download)
            group_path = next((root / "runtime" / "fallback-groups").rglob("query_execution_group.json"))
            group = json.loads(group_path.read_text(encoding="utf-8"))
            self.assertEqual(group["final"]["status"], "cross_engine_data_divergence")
            self.assertFalse(group["final"]["alternate_result_adopted"])
            self.assertNotIn("sensitive-row", output.getvalue())
            emitted = json.loads(output.getvalue())
            self.assertIsNone(emitted["diagnostic_result"]["result_preview"])

    def test_crosscheck_only_two_verified_empty_results_selects_primary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = _outcome(root, attempt_no=1, engine="presto-lakehouse", status="Success", ok=True, result_state="success_empty_verified")
            fallback = _outcome(root, attempt_no=2, engine="presto", status="Success", ok=True, result_state="success_empty_verified")
            with patch(
                "usql_web_query.commands.run_with_fallback.execute_run",
                side_effect=[primary, fallback],
            ) as execute:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = cmd_run_with_fallback(
                        _args(root, empty_result_policy="crosscheck-only", download=True)
                    )
            self.assertEqual(exit_code, 0)
            self.assertEqual(execute.call_count, 2)
            self.assertFalse(execute.call_args_list[1].args[0].download)
            group_path = next((root / "runtime" / "fallback-groups").rglob("query_execution_group.json"))
            group = json.loads(group_path.read_text(encoding="utf-8"))
            self.assertEqual(group["final"]["status"], "crosscheck_empty_consistent")
            self.assertEqual(group["final"]["selected_attempt"], 1)
            self.assertFalse(group["final"]["alternate_result_adopted"])

    def test_failed_fallback_never_starts_a_third_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = _outcome(root, attempt_no=1, engine="presto-lakehouse", status="Success", ok=False, result_state="result_unresolved")
            fallback = _outcome(
                root,
                attempt_no=2,
                engine="presto",
                status="Failed",
                ok=False,
                result_state=None,
                error_details={"source": "log_area", "detail": "503 service unavailable"},
            )
            with patch(
                "usql_web_query.commands.run_with_fallback.execute_run",
                side_effect=[primary, fallback],
            ) as execute:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = cmd_run_with_fallback(_args(root))
            self.assertEqual(exit_code, 1)
            self.assertEqual(execute.call_count, 2)
            group_path = next((root / "runtime" / "fallback-groups").rglob("query_execution_group.json"))
            group = json.loads(group_path.read_text(encoding="utf-8"))
            self.assertEqual(group["final"]["status"], "fallback_failed")
            self.assertEqual(len(group["attempts"]), 2)

    def test_non_transient_sql_error_does_not_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = _outcome(
                root,
                attempt_no=1,
                engine="presto-lakehouse",
                status="Failed",
                ok=False,
                result_state=None,
                error_details={"source": "log_area", "detail": "syntax error at line 1"},
            )
            with patch(
                "usql_web_query.commands.run_with_fallback.execute_run",
                return_value=primary,
            ) as execute:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = cmd_run_with_fallback(_args(root))
            self.assertEqual(exit_code, 1)
            execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
