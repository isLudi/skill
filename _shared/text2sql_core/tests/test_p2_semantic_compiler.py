from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import sqlglot
from jsonschema import Draft202012Validator


CORE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CORE_ROOT.parents[1]
sys.path.insert(0, str(CORE_ROOT))
sys.path.insert(0, str(REPO_ROOT / "usql-web-query-operator" / "scripts"))

from _shared.errors import UsageError  # noqa: E402
from text2sql_core.catalog import CatalogBundle  # noqa: E402
from text2sql_core.cli import main_for_domain  # noqa: E402
from text2sql_core.compiler import compile_query_plan  # noqa: E402
from text2sql_core.contracts import CONTRACT_FILES, ContractRegistry  # noqa: E402
from text2sql_core.dataset import build_dataset_spec  # noqa: E402
from text2sql_core.evaluator import evaluate_resolution_cases  # noqa: E402
from text2sql_core.models import QuerySpec  # noqa: E402
from text2sql_core.planner import build_query_plan  # noqa: E402
from text2sql_core.probe import generate_probe  # noqa: E402
from usql_web_query.query_contract import load_query_plan_contract  # noqa: E402


DOMAIN_CASES = {
    "market_consultant": {
        "skill": "sql-query-writer-for-dashboard",
        "metric": "market_consultant:metric:conversion_users",
        "dimension": "market_consultant:dimension:period_name",
        "scope": "market_consultant:scope:conversion_dashboard",
        "department": "市场顾问部",
        "foreign_department": "青橙项目部",
    },
    "qingcheng": {
        "skill": "qingcheng-dashboard-sql",
        "metric": "qingcheng:metric:valid_leads",
        "dimension": "qingcheng:dimension:period_name",
        "scope": "qingcheng:scope:conversion_lead_department",
        "department": "青橙项目部",
        "foreign_department": "市场顾问部",
    },
}
BASE_TABLE = "bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df"
BASE_TABLE_DOC = "knowledge/tables/bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.md"


class P2SemanticCompilerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {
            name: json.loads((CORE_ROOT / "schemas" / name).read_text(encoding="utf-8"))
            for name in (
                "query_spec.schema.json",
                "query_plan.schema.json",
                "dashboard_dataset_spec.schema.json",
                "semantic_contracts.schema.json",
            )
        }

    def _registry(self, domain: str) -> ContractRegistry:
        config = DOMAIN_CASES[domain]
        return ContractRegistry.load(REPO_ROOT / config["skill"], domain)

    def _spec(
        self,
        domain: str,
        *,
        scopes: list[str] | None = None,
        business_scope: list[dict[str, object]] | None = None,
        output_grain: list[str] | None = None,
    ) -> QuerySpec:
        config = DOMAIN_CASES[domain]
        registry = self._registry(domain)
        metric = registry.by_id(config["metric"])
        dimension = registry.by_id(config["dimension"])
        assert metric and dimension
        return QuerySpec(
            domain=domain,
            intent="metric_query",
            metrics=[
                {
                    "id": metric["id"],
                    "name": metric["name"],
                    "source_path": metric["source_path"],
                }
            ],
            dimensions=[dimension["id"]],
            filters=[],
            business_scope=(
                [{"field": "hour", "operator": "=", "value": "12"}]
                if business_scope is None
                else business_scope
            ),
            scopes=[config["scope"]] if scopes is None else scopes,
            time_range={"field": "dt", "start": "20260701", "end": "20260702"},
            calculation_grain=[dimension["field"]],
            output_grain=[dimension["field"]] if output_grain is None else output_grain,
            candidate_tables=[{"name": BASE_TABLE, "source_path": BASE_TABLE_DOC}],
            join_path=[],
            evidence=[
                {
                    "source_path": metric["source_path"],
                    "kind": "metric",
                    "supports": [metric["id"]],
                }
            ],
            unresolved_slots=[],
            execution_mode="production",
        )

    def test_contracts_are_hash_bound_and_resolution_evals_pass(self) -> None:
        for domain, config in DOMAIN_CASES.items():
            with self.subTest(domain=domain):
                skill_root = REPO_ROOT / config["skill"]
                registry = self._registry(domain)
                self.assertTrue(registry.ok, [item.to_dict() for item in registry.diagnostics])
                report = evaluate_resolution_cases(skill_root, domain)
                self.assertTrue(report["ok"], report)
                self.assertEqual(9, report["passed"])
                for filename in CONTRACT_FILES.values():
                    envelope = json.loads(
                        (skill_root / "semantic" / "contracts" / filename).read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        [],
                        list(
                            Draft202012Validator(self.schemas["semantic_contracts.schema.json"]).iter_errors(
                                envelope
                            )
                        ),
                    )

    def test_domain_aliases_are_isolated_and_intentional_ambiguity_is_visible(self) -> None:
        market = self._registry("market_consultant")
        qing = self._registry("qingcheng")
        self.assertEqual("unknown", market.resolve("青橙目标完成率").status)
        self.assertEqual("unknown", qing.resolve("市场顾问支付人数").status)

        market_ambiguous = market.resolve("当期转化")
        self.assertEqual("ambiguous", market_ambiguous.status)
        self.assertEqual(
            {
                "market_consultant:metric:same_period_conversion_users",
                "market_consultant:metric:same_period_conversion_subject_count",
            },
            {item["id"] for item in market_ambiguous.candidates},
        )
        qing_ambiguous = qing.resolve("顾问")
        self.assertEqual("ambiguous", qing_ambiguous.status)
        self.assertEqual(2, len(qing_ambiguous.candidates))

    def test_confirmed_single_table_path_compiles_for_both_domains(self) -> None:
        for domain, config in DOMAIN_CASES.items():
            with self.subTest(domain=domain):
                spec = self._spec(domain)
                self.assertEqual(
                    [],
                    list(
                        Draft202012Validator(self.schemas["query_spec.schema.json"]).iter_errors(spec.to_dict())
                    ),
                )
                skill_root = REPO_ROOT / config["skill"]
                plan = build_query_plan(spec, skill_root=skill_root, core_root=CORE_ROOT)
                self.assertTrue(plan.executable, plan.to_dict())
                self.assertEqual("executable", plan.status)
                self.assertEqual(config["scope"], plan.scopes[0]["id"])
                self.assertEqual(
                    [],
                    list(
                        Draft202012Validator(self.schemas["query_plan.schema.json"]).iter_errors(plan.to_dict())
                    ),
                )

                compiled = compile_query_plan(plan, self._registry(domain))
                self.assertEqual(hashlib.sha256(compiled.sql.encode("utf-8")).hexdigest(), plan.sql_sha256)
                self.assertEqual(1, len(sqlglot.parse(compiled.sql, read="presto")))
                self.assertIn(config["department"], compiled.sql)
                self.assertNotIn(config["foreign_department"], compiled.sql)
                self.assertNotIn("sql", plan.to_dict())

                dataset = build_dataset_spec(plan)
                self.assertEqual(
                    [],
                    list(
                        Draft202012Validator(
                            self.schemas["dashboard_dataset_spec.schema.json"]
                        ).iter_errors(dataset)
                    ),
                )
                self.assertFalse(dataset["write_boundary"]["may_modify_dashboard"])
                self.assertFalse(dataset["write_boundary"]["may_publish_dashboard"])
                self.assertEqual(config["scope"], dataset["scope_contracts"][0]["id"])

    def test_qingcheng_derived_channel_dimensions_compile_from_contract_expressions(self) -> None:
        skill_root = REPO_ROOT / DOMAIN_CASES["qingcheng"]["skill"]
        registry = self._registry("qingcheng")
        for dimension_id, output_alias in (
            ("qingcheng:dimension:process_channel_level_1", "channel_map_1"),
            ("qingcheng:dimension:process_channel_level_2", "channel_map_2"),
        ):
            with self.subTest(dimension_id=dimension_id):
                dimension = registry.by_id(dimension_id)
                assert dimension
                spec = self._spec("qingcheng")
                spec.dimensions = [dimension_id]
                spec.calculation_grain = [output_alias]
                spec.output_grain = [output_alias]

                plan = build_query_plan(spec, skill_root=skill_root, core_root=CORE_ROOT)

                self.assertTrue(plan.executable, plan.to_dict())
                compiled = compile_query_plan(plan, registry)
                compiled_sql = compiled.sql.lower()
                if output_alias == "channel_map_1":
                    self.assertIn(
                        "case when t.rule_name like '%抖音正价退费%' then '抖音复用'",
                        compiled_sql,
                    )
                    self.assertIn(
                        "concat('ip', chr(36192), chr(35838), chr(22833), chr(36133))",
                        compiled_sql,
                    )
                else:
                    self.assertIn(
                        "case when t.rule_name like '%抖音正价退费%' then '抖音正价退费'",
                        compiled_sql,
                    )
                    self.assertIn("then '星义ip'", compiled_sql)
                self.assertIn(f"as {output_alias}", compiled.sql)
                self.assertIn("group by", compiled.sql.lower())

    def test_unique_scope_is_auto_selected_but_missing_or_conflicting_values_block(self) -> None:
        automatic = self._spec("market_consultant", scopes=[])
        plan = build_query_plan(
            automatic,
            skill_root=REPO_ROOT / DOMAIN_CASES["market_consultant"]["skill"],
            core_root=CORE_ROOT,
        )
        self.assertTrue(plan.executable, plan.to_dict())
        self.assertEqual("market_consultant:scope:conversion_dashboard", plan.scopes[0]["id"])

        missing = self._spec("market_consultant", scopes=[], business_scope=[])
        missing_plan = build_query_plan(
            missing,
            skill_root=REPO_ROOT / DOMAIN_CASES["market_consultant"]["skill"],
            core_root=CORE_ROOT,
        )
        self.assertEqual("blocked", missing_plan.status)
        self.assertIn("PLAN_SCOPE_VALUE_REQUIRED", {item.code for item in missing_plan.diagnostics})

        conflicting = self._spec(
            "market_consultant",
            scopes=[],
            business_scope=[
                {"field": "hour", "operator": "=", "value": "12"},
                {
                    "field": "section_assign_employee_third_level_department_name",
                    "operator": "=",
                    "value": "青橙项目部",
                },
            ],
        )
        conflict_plan = build_query_plan(
            conflicting,
            skill_root=REPO_ROOT / DOMAIN_CASES["market_consultant"]["skill"],
            core_root=CORE_ROOT,
        )
        self.assertEqual("blocked", conflict_plan.status)
        self.assertIn("PLAN_SCOPE_FILTER_CONFLICT", {item.code for item in conflict_plan.diagnostics})

    def test_pending_metric_disallowed_dimension_and_grain_mismatch_are_gated(self) -> None:
        registry = self._registry("market_consultant")
        pending_contract = registry.by_id("market_consultant:metric:valid_lead_count")
        assert pending_contract
        pending = self._spec("market_consultant")
        pending.metrics = [
            {
                "id": pending_contract["id"],
                "name": pending_contract["name"],
                "source_path": pending_contract["source_path"],
            }
        ]
        pending_plan = build_query_plan(
            pending,
            skill_root=REPO_ROOT / DOMAIN_CASES["market_consultant"]["skill"],
            core_root=CORE_ROOT,
        )
        self.assertEqual("blocked", pending_plan.status)
        self.assertIn("PLAN_METRIC_PENDING", {item.code for item in pending_plan.diagnostics})

        qing = self._spec("qingcheng")
        qing.dimensions = ["qingcheng:dimension:grade_name"]
        qing.calculation_grain = ["grade_name"]
        qing.output_grain = ["grade_name"]
        disallowed_plan = build_query_plan(
            qing,
            skill_root=REPO_ROOT / DOMAIN_CASES["qingcheng"]["skill"],
            core_root=CORE_ROOT,
        )
        self.assertEqual("blocked", disallowed_plan.status)
        self.assertIn("PLAN_DIMENSION_NOT_ALLOWED", {item.code for item in disallowed_plan.diagnostics})

        mismatch = self._spec("market_consultant", output_grain=["employee_email_name"])
        mismatch_plan = build_query_plan(
            mismatch,
            skill_root=REPO_ROOT / DOMAIN_CASES["market_consultant"]["skill"],
            core_root=CORE_ROOT,
        )
        self.assertEqual("requires_manual_sql", mismatch_plan.status)
        self.assertIn("PLAN_GRAIN_MISMATCH_REQUIRES_REVIEW", {item.code for item in mismatch_plan.diagnostics})

        pending_join = registry.by_id("market_consultant:join:lead_to_outbound_workload")
        assert pending_join
        with_join = self._spec("market_consultant")
        with_join.join_path = [
            {
                "contract_id": pending_join["id"],
                "left": pending_join["left_table"],
                "right": pending_join["right_table"],
                "keys": ["user_id=user_number", "employee_email_prefix=section_assign_employee_email_prefix"],
                "source_path": pending_join["source_path"],
            }
        ]
        join_plan = build_query_plan(
            with_join,
            skill_root=REPO_ROOT / DOMAIN_CASES["market_consultant"]["skill"],
            core_root=CORE_ROOT,
        )
        self.assertEqual("blocked", join_plan.status)
        self.assertIn("PLAN_JOIN_PENDING", {item.code for item in join_plan.diagnostics})

        qing_registry = self._registry("qingcheng")
        manual_metric = qing_registry.by_id("qingcheng:metric:refund_amount_yuan")
        manual_dimension = qing_registry.by_id("qingcheng:dimension:grade_name")
        assert manual_metric and manual_dimension
        manual_spec = self._spec("qingcheng", scopes=[])
        manual_spec.metrics = [
            {
                "id": manual_metric["id"],
                "name": manual_metric["name"],
                "source_path": manual_metric["source_path"],
            }
        ]
        manual_spec.evidence = [
            {
                "source_path": manual_metric["source_path"],
                "kind": "metric",
                "supports": [manual_metric["id"]],
            }
        ]
        manual_spec.dimensions = [manual_dimension["id"]]
        manual_spec.calculation_grain = [manual_dimension["field"]]
        manual_spec.output_grain = [manual_dimension["field"]]
        manual_spec.candidate_tables = [
            {
                "name": manual_metric["candidate_tables"][0],
                "source_path": "knowledge/tables/service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.md",
            }
        ]
        manual_plan = build_query_plan(
            manual_spec,
            skill_root=REPO_ROOT / DOMAIN_CASES["qingcheng"]["skill"],
            core_root=CORE_ROOT,
        )
        self.assertNotEqual("executable", manual_plan.status)
        self.assertIn("PLAN_METRIC_MANUAL_RECIPE_REQUIRED", {item.code for item in manual_plan.diagnostics})

    def test_probes_are_bounded_read_only_and_catalog_checked(self) -> None:
        bundle = CatalogBundle.load(REPO_ROOT / "sql-query-writer-for-dashboard", CORE_ROOT)
        for kind, kwargs in (
            ("freshness", {}),
            ("distribution", {"field": "period_name"}),
            ("duplicates", {"keys": ["lead_id"]}),
            (
                "join-cardinality",
                {"keys": ["lead_id"], "right_table": BASE_TABLE, "right_keys": ["lead_id"]},
            ),
        ):
            with self.subTest(kind=kind):
                probe = generate_probe(
                    bundle,
                    kind=kind,
                    table=BASE_TABLE,
                    start_value="20260701",
                    end_value="20260702",
                    limit=5000,
                    **kwargs,
                )
                self.assertEqual(1, len(sqlglot.parse(probe.sql, read="presto")))
                if kind != "join-cardinality":
                    self.assertIn("limit 1000", probe.sql.lower())
                self.assertNotIn("insert ", probe.sql.lower())
                self.assertNotIn("update ", probe.sql.lower())
                self.assertNotIn("delete ", probe.sql.lower())
        with self.assertRaises(ValueError):
            generate_probe(
                bundle,
                kind="freshness",
                table="other.unknown_table",
                start_value="20260701",
                end_value="20260702",
            )
        with self.assertRaises(ValueError):
            generate_probe(
                bundle,
                kind="distribution",
                table=BASE_TABLE,
                field="definitely_unknown_field",
                start_value="20260701",
                end_value="20260702",
            )

    def test_cli_plan_compile_and_dataset_handoff(self) -> None:
        domain = "market_consultant"
        skill_root = REPO_ROOT / DOMAIN_CASES[domain]["skill"]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            spec_path = temp_root / "query_spec.json"
            sql_path = temp_root / "query.sql"
            plan_path = temp_root / "query_plan.json"
            dataset_path = temp_root / "dataset_spec.json"
            spec_path.write_text(
                json.dumps(self._spec(domain).to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(output):
                result = main_for_domain(
                    domain=domain,
                    skill_root=skill_root,
                    core_root=CORE_ROOT,
                    argv=[
                        "compile",
                        "--spec",
                        str(spec_path),
                        "--sql-output",
                        str(sql_path),
                        "--plan-output",
                        str(plan_path),
                    ],
                )
            self.assertEqual(0, result, output.getvalue())
            self.assertTrue(sql_path.is_file())
            self.assertTrue(plan_path.is_file())
            plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(
                hashlib.sha256(sql_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest(),
                plan_payload["sql_sha256"],
            )
            sql_text = sql_path.read_text(encoding="utf-8")
            operator_contract = load_query_plan_contract(plan_path, sql_text)
            self.assertEqual(domain, operator_contract.domain)
            with self.assertRaises(UsageError):
                load_query_plan_contract(plan_path, sql_text + "-- tampered\n")

            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(output):
                result = main_for_domain(
                    domain=domain,
                    skill_root=skill_root,
                    core_root=CORE_ROOT,
                    argv=["dataset-spec", "--plan", str(plan_path), "--output", str(dataset_path)],
                )
            self.assertEqual(0, result, output.getvalue())
            self.assertFalse(
                json.loads(dataset_path.read_text(encoding="utf-8"))["write_boundary"]["may_modify_dashboard"]
            )


if __name__ == "__main__":
    unittest.main()
