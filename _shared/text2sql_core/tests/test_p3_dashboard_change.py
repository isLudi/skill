from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver


CORE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CORE_ROOT.parents[1]
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.dashboard_change import (  # noqa: E402
    SAFE_OPERATION_TYPES,
    artifact_sha256,
    build_apply_receipt,
    build_dashboard_design_spec,
    build_publish_receipt,
    canonical_sha256,
    diff_dashboard,
    normalize_dashboard_profile,
    validate_apply_receipt,
    validate_dashboard_change_plan,
    validate_publish_receipt,
)
from text2sql_core.contracts import ContractRegistry  # noqa: E402


DOMAIN_SKILLS = {
    "market_consultant": "sql-query-writer-for-dashboard",
    "qingcheng": "qingcheng-dashboard-sql",
}
DASHBOARD_IDS = {
    "market_consultant": "dashboard_3699054046816116737",
    "qingcheng": "dashboard_3852445620602875904",
}


def raw_profile(domain: str = "qingcheng") -> dict:
    return {
        "domain": domain,
        "profiled_at": "2026-07-11T10:00:00+08:00",
        "snapshot": {
            "dashboard": {
                "dashboard_id": DASHBOARD_IDS.get(domain, DASHBOARD_IDS["qingcheng"]),
                "dashboard_name": "Process dashboard",
                "version_id": "draft",
                "html_id": "html-1",
                "domain": domain,
            },
            "components": [
                {
                    "node_id": "node-1",
                    "parent_node_id": "root",
                    "node_component": "PivotTable",
                    "node_title": "Detail",
                    "unit_id": "unit-1",
                    "component_type": "pivot",
                    "hidden": False,
                    "locked": False,
                },
                {
                    "node_id": "node-2",
                    "parent_node_id": "root",
                    "node_component": "Text",
                    "node_title": "Note",
                    "unit_id": None,
                    "component_type": "text",
                    "hidden": False,
                    "locked": False,
                },
            ],
            "layout": [
                {"node_id": "node-1", "parent_node_id": "root", "x": 0, "y": 0, "w": 12, "h": 8},
                {"node_id": "node-2", "parent_node_id": "root", "x": 12, "y": 0, "w": 12, "h": 8},
            ],
            "formulas": [
                {
                    "unit_id": "unit-1",
                    "field_id": "metric-1",
                    "business_name": "Rate",
                    "formula": "a / b",
                    "dependencies": ["a", "b"],
                }
            ],
            "public_filters": [
                {
                    "relation_id": "relation-1",
                    "filter_id": "public-filter-1",
                    "field_id": "grade",
                    "filter_name": "Grade",
                    "show_name": "Grade",
                    "condition": "in",
                    "dynamics_filter": True,
                    "dynamics_filter_value": "1",
                    "auto_search_default_value": False,
                },
                {
                    "relation_id": "relation-1",
                    "filter_id": "public-filter-1",
                    "field_id": "consultant",
                    "filter_name": "Consultant",
                    "show_name": "Consultant",
                    "condition": "in",
                    "dynamics_filter": True,
                    "dynamics_filter_value": "1",
                    "auto_search_default_value": False,
                },
            ],
            "component_filters": [
                {"unit_id": "unit-1", "field_id": "period", "write_status": "blocked_unsupported"}
            ],
            "datasets": [],
        },
    }


def dataset_spec(domain: str = "qingcheng") -> dict:
    plan_hash = "1" * 64
    registry = ContractRegistry.load(REPO_ROOT / DOMAIN_SKILLS[domain], domain)
    contract = registry.by_id(f"{domain}:dimension:period_name")
    assert registry.ok and contract is not None
    value = {
        "schema_version": "2.0.0",
        "artifact_type": "dashboard_dataset_spec",
        "mode": "read_only_design",
        "domain": domain,
        "plan_id": "plan-1",
        "status": "ready",
        "grain": ["period_name"],
        "base_table": "db.fact",
        "scope_contracts": [],
        "fields": [
            {
                "name": "period_name",
                "role": "dimension",
                "contract_id": f"{domain}:dimension:period_name",
                "contract_status": contract["status"],
                "source_domain": domain,
                "source_path": contract["source_path"],
                "source_sha256": contract["source_sha256"],
            }
        ],
        "default_filters": [],
        "lineage": [],
        "query_plan_sha256": plan_hash,
        "write_boundary": {
            "may_profile_existing_dashboard": True,
            "may_generate_diff_plan": True,
            "may_modify_dashboard": False,
            "may_publish_dashboard": False,
        },
    }
    value["dataset_spec_sha256"] = artifact_sha256(value, "dataset_spec_sha256")
    return value


def isolated_contract_root(root: Path, domain: str = "qingcheng") -> tuple[Path, dict]:
    skill_root = root / DOMAIN_SKILLS[domain]
    source_path = "knowledge/tables/fact.md"
    source = skill_root / source_path
    source.parent.mkdir(parents=True)
    source.write_text("authoritative contract evidence\n", encoding="utf-8")
    contract = {
        "id": f"{domain}:dimension:period_name",
        "name": "Period",
        "aliases": ["period_name"],
        "status": "confirmed",
        "source_path": source_path,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "field": "period_name",
        "table": "db.fact",
    }
    contract_root = skill_root / "semantic" / "contracts"
    contract_root.mkdir(parents=True)
    for kind in ("metric", "dimension", "join", "scope"):
        envelope = {
            "schema_version": "2.0.0",
            "domain": domain,
            "contracts": [contract] if kind == "dimension" else [],
        }
        (contract_root / f"{kind}_contracts.json").write_text(
            json.dumps(envelope), encoding="utf-8"
        )
    return skill_root, contract


class P3DashboardChangeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {
            path.name: json.loads(path.read_text(encoding="utf-8"))
            for path in (CORE_ROOT / "schemas").glob("dashboard_*.schema.json")
        }
        cls.store = {schema["$id"]: schema for schema in cls.schemas.values()}

    def assert_schema(self, filename: str, value: dict) -> None:
        schema = self.schemas[filename]
        resolver = RefResolver.from_schema(schema, store=self.store)
        errors = sorted(
            Draft202012Validator(schema, resolver=resolver).iter_errors(value),
            key=lambda item: list(item.path),
        )
        self.assertEqual([], [error.message for error in errors])

    def design(self, profile: dict | None = None, **kwargs) -> dict:
        return build_dashboard_design_spec(
            dataset_spec(),
            profile or raw_profile(),
            **kwargs,
        )

    def dynamic_design(self) -> tuple[dict, dict, list[dict]]:
        profile = normalize_dashboard_profile(raw_profile())
        desired = copy.deepcopy(profile["public_filters"])
        desired[0]["dynamics_filter"] = True
        desired[0]["dynamics_filter_value"] = "2"
        desired[0]["auto_search_default_value"] = False
        design = self.design(profile, desired_public_filters=desired)
        return profile, design, desired

    def test_real_snapshot_shape_normalizes_idempotently_and_uses_composite_filter_identity(self) -> None:
        profile = normalize_dashboard_profile(raw_profile())
        self.assertEqual("node-1", profile["components"][0]["component_id"])
        self.assertEqual("root", profile["layout"][0]["container_id"])
        self.assertEqual(2, len(profile["public_filters"]))
        self.assertEqual("unit-1::period", profile["component_filters"][0]["component_filter_key"])
        self.assertEqual(
            "relation-1::public-filter-1::consultant",
            profile["public_filters"][0]["filter_key"],
        )
        self.assertEqual(profile, normalize_dashboard_profile(profile))
        self.assert_schema("dashboard_profile.schema.json", profile)

    def test_profile_hash_is_stable_but_state_sensitive(self) -> None:
        first = raw_profile()
        second = raw_profile()
        second["profiled_at"] = "2026-07-11T11:00:00+08:00"
        self.assertEqual(
            normalize_dashboard_profile(first)["profile_sha256"],
            normalize_dashboard_profile(second)["profile_sha256"],
        )
        second["snapshot"]["dashboard"]["html_id"] = "html_ephemeral_2"
        self.assertEqual(
            normalize_dashboard_profile(first)["profile_sha256"],
            normalize_dashboard_profile(second)["profile_sha256"],
        )
        second["snapshot"]["layout"][0]["w"] = 11
        self.assertNotEqual(
            normalize_dashboard_profile(first)["profile_sha256"],
            normalize_dashboard_profile(second)["profile_sha256"],
        )
        enriched = raw_profile()
        enriched["completeness"] = {
            "status": "complete",
            "required": [
                "components", "layout", "formulas", "public_filters",
                "component_filters", "datasets",
            ],
            "details": {"profile_api": "verified"},
        }
        self.assertNotEqual(
            normalize_dashboard_profile(first)["profile_sha256"],
            normalize_dashboard_profile(enriched)["profile_sha256"],
        )

    def test_unresolved_profile_is_readable_but_design_is_blocked(self) -> None:
        profile = normalize_dashboard_profile(raw_profile("unresolved"))
        self.assertEqual("unresolved", profile["domain"])
        self.assert_schema("dashboard_profile.schema.json", profile)
        design = build_dashboard_design_spec(dataset_spec(), profile)
        self.assertEqual("blocked", design["status"])
        self.assertIn(
            "DASHBOARD_DOMAIN_UNRESOLVED",
            {item["code"] for item in design["diagnostics"]},
        )

    def test_incomplete_profile_is_hashable_but_design_is_blocked(self) -> None:
        raw = raw_profile()
        raw["snapshot"].pop("datasets")
        profile = normalize_dashboard_profile(raw)
        self.assertEqual("incomplete", profile["completeness"]["status"])
        self.assertIn("datasets", profile["completeness"]["missing"])
        self.assert_schema("dashboard_profile.schema.json", profile)
        design = build_dashboard_design_spec(dataset_spec(), profile)
        self.assertEqual("blocked", design["status"])
        self.assertIn(
            "DASHBOARD_PROFILE_INCOMPLETE",
            {item["code"] for item in design["diagnostics"]},
        )

    def test_dataset_must_be_ready_and_contract_evidence_must_be_confirmed_local(self) -> None:
        draft = dataset_spec()
        draft["status"] = "draft"
        draft["dataset_spec_sha256"] = artifact_sha256(draft, "dataset_spec_sha256")
        self.assertIn(
            "DASHBOARD_DATASET_NOT_READY",
            {
                item["code"]
                for item in build_dashboard_design_spec(draft, raw_profile())["diagnostics"]
            },
        )

        mutations = (
            ("contract_status", "pending_confirmation", "DASHBOARD_CONTRACT_NOT_CONFIRMED"),
            ("source_domain", "market_consultant", "DASHBOARD_CONTRACT_SOURCE_DOMAIN_INVALID"),
            ("source_path", "", "DASHBOARD_CONTRACT_SOURCE_PATH_REQUIRED"),
            ("source_sha256", None, "DASHBOARD_CONTRACT_SOURCE_HASH_INVALID"),
            (
                "source_path",
                "sql-query-writer-for-dashboard/knowledge/metrics/foreign.md",
                "DASHBOARD_CONTRACT_SOURCE_CROSS_DOMAIN",
            ),
            ("source_path", "C:/absolute/evidence.md", "DASHBOARD_CONTRACT_SOURCE_PATH_INVALID"),
        )
        for field, value, expected_code in mutations:
            with self.subTest(field=field, expected_code=expected_code):
                dataset = dataset_spec()
                dataset["fields"][0][field] = value
                dataset["dataset_spec_sha256"] = artifact_sha256(
                    dataset, "dataset_spec_sha256"
                )
                design = build_dashboard_design_spec(dataset, raw_profile())
                self.assertEqual("blocked", design["status"])
                self.assertIn(
                    expected_code,
                    {item["code"] for item in design["diagnostics"]},
                )

        scope_dataset = dataset_spec()
        scope_dataset["scope_contracts"] = [
            {
                "id": "qingcheng:scope:process",
                "contract_status": "pending_confirmation",
                "source_domain": "qingcheng",
                "source_path": "knowledge/ranges/process.md",
                "source_sha256": "5" * 64,
            }
        ]
        scope_dataset["dataset_spec_sha256"] = artifact_sha256(
            scope_dataset, "dataset_spec_sha256"
        )
        self.assertIn(
            "DASHBOARD_CONTRACT_NOT_CONFIRMED",
            {
                item["code"]
                for item in build_dashboard_design_spec(
                    scope_dataset, raw_profile()
                )["diagnostics"]
            },
        )

        filter_dataset = dataset_spec()
        filter_dataset["default_filters"] = [
            {
                "field": "department",
                "operator": "=",
                "value": "Qingcheng",
                "role": "scope_contract",
                "contract_id": "qingcheng:scope:process",
            }
        ]
        filter_dataset["dataset_spec_sha256"] = artifact_sha256(
            filter_dataset, "dataset_spec_sha256"
        )
        filter_codes = {
            item["code"]
            for item in build_dashboard_design_spec(
                filter_dataset, raw_profile()
            )["diagnostics"]
        }
        self.assertIn("DASHBOARD_CONTRACT_SOURCE_DOMAIN_INVALID", filter_codes)
        self.assertIn("DASHBOARD_CONTRACT_SOURCE_HASH_INVALID", filter_codes)

    def test_design_rechecks_domain_registry_and_real_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root, contract = isolated_contract_root(Path(temp_dir))
            roots = {"qingcheng": skill_root}
            dataset = dataset_spec()
            dataset["fields"][0].update(
                {
                    "contract_id": contract["id"],
                    "contract_status": contract["status"],
                    "source_domain": "qingcheng",
                    "source_path": contract["source_path"],
                    "source_sha256": contract["source_sha256"],
                }
            )
            dataset["dataset_spec_sha256"] = artifact_sha256(
                dataset, "dataset_spec_sha256"
            )
            ready = build_dashboard_design_spec(
                dataset, raw_profile(), business_skill_roots=roots
            )
            self.assertEqual("ready", ready["status"], ready["diagnostics"])

            cases = (
                (
                    "contract_id",
                    "qingcheng:dimension:not_registered",
                    "DASHBOARD_CONTRACT_NOT_REGISTERED",
                ),
                (
                    "source_path",
                    "knowledge/tables/does_not_exist.md",
                    "DASHBOARD_CONTRACT_SOURCE_PATH_MISMATCH",
                ),
                (
                    "source_sha256",
                    "0" * 64,
                    "DASHBOARD_CONTRACT_SOURCE_HASH_MISMATCH",
                ),
                (
                    "contract_id",
                    "market_consultant:dimension:period_name",
                    "DASHBOARD_CONTRACT_NOT_REGISTERED",
                ),
            )
            for field, value, expected_code in cases:
                with self.subTest(field=field, expected_code=expected_code):
                    forged = copy.deepcopy(dataset)
                    forged["fields"][0][field] = value
                    forged["dataset_spec_sha256"] = artifact_sha256(
                        forged, "dataset_spec_sha256"
                    )
                    blocked = build_dashboard_design_spec(
                        forged, raw_profile(), business_skill_roots=roots
                    )
                    self.assertEqual("blocked", blocked["status"])
                    self.assertIn(
                        expected_code,
                        {item["code"] for item in blocked["diagnostics"]},
                    )

            source = skill_root / contract["source_path"]
            source.write_text("drifted evidence\n", encoding="utf-8")
            drifted = build_dashboard_design_spec(
                dataset, raw_profile(), business_skill_roots=roots
            )
            drift_codes = {item["code"] for item in drifted["diagnostics"]}
            self.assertEqual("blocked", drifted["status"])
            self.assertIn("DASHBOARD_CONTRACT_SOURCE_FILE_HASH_MISMATCH", drift_codes)

    def test_dataset_cannot_promote_pending_registry_contract_to_confirmed(self) -> None:
        registry = ContractRegistry.load(
            REPO_ROOT / DOMAIN_SKILLS["qingcheng"], "qingcheng"
        )
        pending = registry.by_id("qingcheng:metric:team_completion_rate")
        assert pending is not None and pending["status"] == "pending_confirmation"
        dataset = dataset_spec()
        dataset["fields"][0].update(
            {
                "contract_id": pending["id"],
                "contract_status": "confirmed",
                "source_domain": "qingcheng",
                "source_path": pending["source_path"],
                "source_sha256": pending["source_sha256"],
            }
        )
        dataset["dataset_spec_sha256"] = artifact_sha256(
            dataset, "dataset_spec_sha256"
        )
        blocked = build_dashboard_design_spec(dataset, raw_profile())
        codes = {item["code"] for item in blocked["diagnostics"]}
        self.assertEqual("blocked", blocked["status"])
        self.assertIn("DASHBOARD_CONTRACT_REGISTRY_NOT_CONFIRMED", codes)
        self.assertIn("DASHBOARD_CONTRACT_STATUS_MISMATCH", codes)

    def test_design_binds_dashboard_id_to_domain_registry(self) -> None:
        wrong_domain = raw_profile("market_consultant")
        wrong_domain["snapshot"]["dashboard"]["dashboard_id"] = DASHBOARD_IDS[
            "qingcheng"
        ]
        blocked = build_dashboard_design_spec(
            dataset_spec("market_consultant"),
            wrong_domain,
        )
        self.assertEqual("blocked", blocked["status"])
        self.assertIn(
            "DASHBOARD_DOMAIN_REGISTRATION_MISMATCH",
            {item["code"] for item in blocked["diagnostics"]},
        )

        unregistered = raw_profile()
        unregistered["snapshot"]["dashboard"]["dashboard_id"] = (
            "dashboard_9999999999999999999"
        )
        blocked = build_dashboard_design_spec(dataset_spec(), unregistered)
        self.assertEqual("blocked", blocked["status"])
        self.assertIn(
            "DASHBOARD_DOMAIN_UNREGISTERED",
            {item["code"] for item in blocked["diagnostics"]},
        )

    def test_dataset_without_business_contract_fields_is_allowed(self) -> None:
        dataset = dataset_spec()
        dataset["fields"] = [
            {"name": "physical_partition", "role": "physical", "data_type": "string"}
        ]
        dataset["dataset_spec_sha256"] = artifact_sha256(
            dataset, "dataset_spec_sha256"
        )
        design = build_dashboard_design_spec(dataset, raw_profile())
        self.assertEqual("ready", design["status"], design["diagnostics"])

    def test_design_binds_profile_query_plan_and_dataset_hashes(self) -> None:
        design = self.design()
        self.assertEqual("ready", design["status"])
        self.assertEqual("1" * 64, design["query_plan_sha256"])
        self.assertEqual(
            normalize_dashboard_profile(raw_profile())["profile_sha256"],
            design["source_profile_sha256"],
        )
        self.assert_schema("dashboard_design_spec.schema.json", design)
        self.assertEqual(design["design_sha256"], artifact_sha256(design, "design_sha256"))

    def test_design_resolves_each_domain_to_its_own_live_contract_registry(self) -> None:
        for domain in DOMAIN_SKILLS:
            with self.subTest(domain=domain):
                design = build_dashboard_design_spec(
                    dataset_spec(domain), raw_profile(domain)
                )
                self.assertEqual("ready", design["status"], design["diagnostics"])

    def test_dataset_self_hash_tampering_and_query_plan_conflict_block_design(self) -> None:
        dataset = dataset_spec()
        dataset["fields"][0]["name"] = "tampered"
        design = build_dashboard_design_spec(
            dataset,
            raw_profile(),
            query_plan_sha256="2" * 64,
        )
        self.assertEqual("blocked", design["status"])
        codes = {item["code"] for item in design["diagnostics"]}
        self.assertIn("DASHBOARD_DATASET_SPEC_HASH_MISMATCH", codes)
        self.assertIn("DASHBOARD_QUERY_PLAN_HASH_CONFLICT", codes)

    def test_legacy_dataset_spec_remains_readable_but_cannot_enter_p3_design(self) -> None:
        legacy = dataset_spec()
        legacy.pop("query_plan_sha256")
        legacy.pop("dataset_spec_sha256")
        blocked = build_dashboard_design_spec(legacy, raw_profile())
        self.assertEqual("blocked", blocked["status"])
        still_blocked = build_dashboard_design_spec(
            legacy,
            raw_profile(),
            query_plan_sha256="3" * 64,
        )
        self.assertEqual("blocked", still_blocked["status"])

    def test_noop_diff_is_dry_run_only_and_cannot_authorize_apply(self) -> None:
        profile = normalize_dashboard_profile(raw_profile())
        plan = diff_dashboard(profile, self.design(profile))
        self.assertEqual("no_changes", plan["status"])
        self.assertEqual([], plan["operations"])
        self.assertFalse(plan["authorization"]["apply_authorized"])
        self.assertFalse(plan["authorization"]["publish_authorized"])
        self.assertEqual([], validate_dashboard_change_plan(plan, profile))
        self.assert_schema("dashboard_change_plan.schema.json", plan)

    def test_inconsistent_empty_plan_returns_diagnostic_instead_of_crashing(self) -> None:
        profile = normalize_dashboard_profile(raw_profile())
        plan = diff_dashboard(profile, self.design(profile))
        plan["status"] = "ready_for_dry_run"
        plan["change_plan_sha256"] = artifact_sha256(plan, "change_plan_sha256")
        diagnostics = validate_dashboard_change_plan(plan, profile)
        self.assertIn(
            "DASHBOARD_CHANGE_PLAN_STATUS_INCONSISTENT",
            {item["code"] for item in diagnostics},
        )

    def test_only_stable_dynamic_default_is_p3b_supported(self) -> None:
        profile, design, _ = self.dynamic_design()
        plan = diff_dashboard(profile, design)
        self.assertEqual("ready_for_dry_run", plan["status"])
        self.assertEqual(1, len(plan["operations"]))
        operation = plan["operations"][0]
        self.assertEqual("update_filter_dynamic_default", operation["type"])
        self.assertEqual("supported", operation["write_status"])
        self.assertEqual("planned", operation["status"])
        self.assertEqual(
            {"relation_id", "filter_id", "field_id"},
            {key for key, value in operation["target"].items() if value},
        )
        self.assertEqual({"update_filter_dynamic_default"}, SAFE_OPERATION_TYPES)
        self.assertEqual([], validate_dashboard_change_plan(plan, profile))

    def test_dynamic_default_without_stable_triple_is_blocked(self) -> None:
        raw = raw_profile()
        raw["snapshot"]["public_filters"][0]["relation_id"] = ""
        profile = normalize_dashboard_profile(raw)
        desired = copy.deepcopy(profile["public_filters"])
        desired[0]["dynamics_filter_value"] = "2"
        plan = diff_dashboard(
            profile,
            build_dashboard_design_spec(
                dataset_spec(), profile, desired_public_filters=desired
            ),
        )
        self.assertEqual("blocked", plan["status"])
        self.assertEqual("blocked_unsupported", plan["operations"][0]["write_status"])

    def test_component_layout_formula_and_generic_filter_diffs_are_visible_but_blocked(self) -> None:
        profile = normalize_dashboard_profile(raw_profile())
        cases: list[tuple[str, dict]] = []

        components = copy.deepcopy(profile["components"])
        components[0]["title"] = "Changed"
        cases.append(("update_existing_component", self.design(profile, desired_components=components)))

        layout = copy.deepcopy(profile["layout"])
        layout[0]["x"] = 1
        cases.append(("update_layout", self.design(profile, desired_layout=layout)))

        formulas = copy.deepcopy(profile["formulas"])
        formulas[0]["expression"] = "a / nullif(b, 0)"
        cases.append(("update_formula", self.design(profile, desired_formulas=formulas)))

        filters = copy.deepcopy(profile["public_filters"])
        filters[0]["title"] = "Changed"
        cases.append(("update_filter", self.design(profile, desired_public_filters=filters)))

        component_filters = copy.deepcopy(profile["component_filters"])
        component_filters[0]["condition"] = "not_empty"
        cases.append(
            (
                "update_component_filter",
                build_dashboard_design_spec(
                    dataset_spec(),
                    profile,
                    desired_component_filters=component_filters,
                ),
            )
        )

        for expected_type, design in cases:
            with self.subTest(expected_type=expected_type):
                plan = diff_dashboard(profile, design)
                self.assertEqual("blocked", plan["status"])
                self.assertIn(expected_type, {item["type"] for item in plan["operations"]})
                self.assertTrue(
                    all(item["write_status"] == "blocked_unsupported" for item in plan["operations"])
                )

    def test_layout_collision_and_formula_cycle_have_explicit_diagnostics(self) -> None:
        profile = normalize_dashboard_profile(raw_profile())
        layout = copy.deepcopy(profile["layout"])
        layout[1].update({"x": 1, "y": 1})
        collision = diff_dashboard(profile, self.design(profile, desired_layout=layout))
        self.assertIn(
            "DASHBOARD_LAYOUT_COLLISION",
            {item["code"] for item in collision["diagnostics"]},
        )

        formulas = [
            {
                "formula_id": "f1", "name": "f1", "expression": "f2",
                "dependencies": ["f2"], "scope": "component", "shared": False,
                "component_ids": ["unit-1"],
            },
            {
                "formula_id": "f2", "name": "f2", "expression": "f1",
                "dependencies": ["f1"], "scope": "component", "shared": False,
                "component_ids": ["unit-1"],
            },
        ]
        cycle = diff_dashboard(profile, self.design(profile, desired_formulas=formulas))
        self.assertIn(
            "DASHBOARD_FORMULA_CYCLE",
            {item["code"] for item in cycle["diagnostics"]},
        )

    def test_create_delete_dataset_rebind_and_cross_domain_contract_are_blocked(self) -> None:
        profile = normalize_dashboard_profile(raw_profile())
        components = copy.deepcopy(profile["components"])
        components[0]["dataset_id"] = "new-dataset"
        components.append({"component_id": "node-3", "component_type": "pivot"})
        plan = diff_dashboard(profile, self.design(profile, desired_components=components))
        types = {item["type"] for item in plan["operations"]}
        self.assertIn("rebind_dataset", types)
        self.assertIn("create_component", types)
        self.assertEqual("blocked", plan["status"])

        foreign_dataset = dataset_spec()
        foreign_dataset["fields"][0]["contract_id"] = "market_consultant:dimension:period_name"
        foreign_dataset["dataset_spec_sha256"] = artifact_sha256(
            foreign_dataset, "dataset_spec_sha256"
        )
        design = build_dashboard_design_spec(foreign_dataset, profile)
        self.assertEqual("blocked", design["status"])
        self.assertIn(
            "DASHBOARD_CROSS_DOMAIN_CONTRACT",
            {item["code"] for item in design["diagnostics"]},
        )

    def test_stale_profile_hash_blocks_change_plan(self) -> None:
        profile = normalize_dashboard_profile(raw_profile())
        design = self.design(profile)
        drifted = copy.deepcopy(raw_profile())
        drifted["snapshot"]["components"][0]["node_title"] = "Drifted"
        plan = diff_dashboard(drifted, design)
        self.assertEqual("blocked", plan["status"])
        self.assertIn(
            "DASHBOARD_PROFILE_STALE",
            {item["code"] for item in plan["diagnostics"]},
        )

    def test_validator_rejects_rehashed_forged_status_hash_and_boundaries(self) -> None:
        profile, design, _ = self.dynamic_design()
        original = diff_dashboard(profile, design)
        mutations = []

        bad_status = copy.deepcopy(original)
        bad_status["status"] = "no_changes"
        mutations.append((bad_status, "DASHBOARD_CHANGE_PLAN_STATUS_INCONSISTENT"))

        bad_hash_binding = copy.deepcopy(original)
        bad_hash_binding["query_plan_sha256"] = "not-a-hash"
        mutations.append((bad_hash_binding, "DASHBOARD_HASH_BINDING_INVALID"))

        bad_boundary = copy.deepcopy(original)
        bad_boundary["write_boundary"]["may_apply_from_this_artifact_alone"] = True
        mutations.append((bad_boundary, "DASHBOARD_PLAN_WRITE_BOUNDARY_INVALID"))

        forged_operation = copy.deepcopy(original)
        forged_operation["operations"][0]["target"]["field_id"] = "another-field"
        mutations.append((forged_operation, "DASHBOARD_OPERATIONS_STATE_MISMATCH"))

        for plan, expected_code in mutations:
            with self.subTest(expected_code=expected_code):
                plan["change_plan_sha256"] = artifact_sha256(
                    plan, "change_plan_sha256"
                )
                codes = {
                    item["code"] for item in validate_dashboard_change_plan(plan, profile)
                }
                self.assertIn(expected_code, codes)

    def test_apply_receipt_requires_full_readback_match(self) -> None:
        profile, design, desired = self.dynamic_design()
        plan = diff_dashboard(profile, design)
        post = copy.deepcopy(profile)
        post["public_filters"] = desired
        post = normalize_dashboard_profile(post)
        receipt = build_apply_receipt(plan, post)
        self.assertTrue(receipt["ok"])
        self.assertEqual("applied", receipt["status"])
        self.assertEqual([], validate_apply_receipt(receipt, plan, post))
        self.assert_schema("dashboard_apply_receipt.schema.json", receipt)

        tampered = copy.deepcopy(receipt)
        tampered["post_profile_sha256"] = "0" * 64
        tampered["apply_receipt_sha256"] = artifact_sha256(
            tampered, "apply_receipt_sha256"
        )
        self.assertIn(
            "DASHBOARD_RECEIPT_POST_HASH_MISMATCH",
            {item["code"] for item in validate_apply_receipt(tampered, plan, post)},
        )

    def test_apply_receipt_fails_for_blocked_mixed_plan(self) -> None:
        profile, design, desired = self.dynamic_design()
        components = copy.deepcopy(design["desired_components"])
        components[0]["title"] = "Also changed"
        mixed_design = self.design(
            profile,
            desired_components=components,
            desired_public_filters=desired,
        )
        plan = diff_dashboard(profile, mixed_design)
        self.assertEqual("blocked", plan["status"])
        post = copy.deepcopy(profile)
        post["public_filters"] = desired
        receipt = build_apply_receipt(plan, normalize_dashboard_profile(post))
        self.assertFalse(receipt["ok"])
        self.assertEqual("failed", receipt["status"])

    def test_publish_requires_separate_confirmation_and_non_noop_apply(self) -> None:
        profile, design, desired = self.dynamic_design()
        plan = diff_dashboard(profile, design)
        post = copy.deepcopy(profile)
        post["public_filters"] = desired
        post = normalize_dashboard_profile(post)
        apply_receipt = build_apply_receipt(plan, post)
        missing_readback = build_publish_receipt(
            apply_receipt,
            pre_publish_profile_sha256=post["profile_sha256"],
            confirmed=True,
            version_description="unverified",
            publish_status="publish_requested_unverified",
            published_at="2026-07-11T12:00:00+08:00",
        )
        self.assertFalse(missing_readback["ok"])
        self.assertIn(
            "DASHBOARD_PUBLISH_POST_READBACK_REQUIRED",
            {
                item["code"]
                for item in validate_publish_receipt(missing_readback, apply_receipt)
            },
        )
        publish = build_publish_receipt(
            apply_receipt,
            pre_publish_profile_sha256=post["profile_sha256"],
            confirmed=True,
            version_description="reviewed",
            publish_status="publish_requested_unverified",
            post_publish_draft_profile_sha256=post["profile_sha256"],
            readback_performed=True,
            published_at="2026-07-11T12:00:00+08:00",
        )
        self.assertTrue(publish["ok"])
        self.assertFalse(publish["fully_verified"])
        diagnostics = validate_publish_receipt(publish, apply_receipt)
        self.assertFalse(any(item["severity"] == "error" for item in diagnostics))
        self.assertIn(
            "DASHBOARD_PUBLISHED_VERSION_UNVERIFIED",
            {item["code"] for item in diagnostics},
        )
        self.assert_schema("dashboard_publish_receipt.schema.json", publish)

        verified_publish = build_publish_receipt(
            apply_receipt,
            pre_publish_profile_sha256=post["profile_sha256"],
            confirmed=True,
            version_description="formally verified",
            publish_status="published_verified",
            post_publish_draft_profile_sha256=post["profile_sha256"],
            readback_performed=True,
            published_version_profile_sha256=post["profile_sha256"],
            published_version_readback_performed=True,
            published_at="2026-07-11T12:00:00+08:00",
        )
        self.assertTrue(verified_publish["ok"])
        self.assertTrue(verified_publish["fully_verified"])
        self.assertEqual(
            [],
            validate_publish_receipt(verified_publish, apply_receipt),
        )
        self.assert_schema("dashboard_publish_receipt.schema.json", verified_publish)

        noop_plan = diff_dashboard(profile, self.design(profile))
        noop_receipt = build_apply_receipt(noop_plan, profile)
        noop_publish = build_publish_receipt(
            noop_receipt,
            pre_publish_profile_sha256=profile["profile_sha256"],
            confirmed=True,
            version_description="no-op",
            publish_status="publish_requested_unverified",
            post_publish_draft_profile_sha256=profile["profile_sha256"],
            readback_performed=True,
            published_at="2026-07-11T12:00:00+08:00",
        )
        self.assertFalse(noop_publish["ok"])
        self.assertIn(
            "DASHBOARD_PUBLISH_APPLIED_CHANGE_REQUIRED",
            {item["code"] for item in validate_publish_receipt(noop_publish, noop_receipt)},
        )

    def test_canonical_hash_binds_upstream_hashes_and_omits_only_self(self) -> None:
        first = {"source_profile_sha256": "1" * 64, "design_sha256": "x"}
        second = {"source_profile_sha256": "2" * 64, "design_sha256": "x"}
        self.assertNotEqual(
            artifact_sha256(first, "design_sha256"),
            artifact_sha256(second, "design_sha256"),
        )
        self.assertEqual(canonical_sha256({"b": 2, "a": 1}), canonical_sha256({"a": 1, "b": 2}))


if __name__ == "__main__":
    unittest.main()
