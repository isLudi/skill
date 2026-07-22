from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


CORE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CORE_ROOT.parents[1]
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.ast_validator import validate_sql_ast  # noqa: E402
from text2sql_core.builder import (  # noqa: E402
    DOMAIN_CONFIG,
    _build_dashboard_registry,
    build_outputs,
    check_outputs,
)
from text2sql_core.catalog import CatalogBundle  # noqa: E402
from text2sql_core.corpus import audit_raw_sql  # noqa: E402


class CatalogAndAstTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_schema = json.loads(
            (CORE_ROOT / "schemas" / "domain_manifest.schema.json").read_text(encoding="utf-8")
        )

    def test_generated_outputs_are_current_and_idempotent(self) -> None:
        outputs = build_outputs(REPO_ROOT)
        self.assertEqual([], check_outputs(outputs))
        self.assertEqual(outputs, build_outputs(REPO_ROOT))

    def test_inactive_dashboard_profile_is_not_registered(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active = root / "knowledge/dashboard_web_profiles/active.md"
            inactive = root / "knowledge/dashboard_web_profiles/inactive.md"
            active.parent.mkdir(parents=True)
            active.write_text("dashboard_100\n", encoding="utf-8")
            inactive.write_text(
                "dashboard_200\n- registry_status: `removed_from_current_folder`\n",
                encoding="utf-8",
            )
            registry = _build_dashboard_registry(
                root,
                [
                    {"source_path": "knowledge/dashboard_web_profiles/active.md", "sha256": "a"},
                    {"source_path": "knowledge/dashboard_web_profiles/inactive.md", "sha256": "b"},
                ],
            )
        self.assertEqual(["dashboard_100"], [item["dashboard_id"] for item in registry["registered"]])

    def test_domain_manifests_cover_every_knowledge_and_raw_sql_file(self) -> None:
        expected_baseline = {
            "market_consultant": (137, 63),
            "qingcheng": (166, 17),
        }
        for domain, config in DOMAIN_CONFIG.items():
            skill_root = REPO_ROOT / config["skill"]
            manifest_path = skill_root / "semantic" / "domain_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual([], list(Draft202012Validator(self.manifest_schema).iter_errors(manifest)))
            inventory = {item["source_path"]: item for item in manifest["source_inventory"]}
            actual = sorted(
                [path for path in (skill_root / "knowledge").rglob("*.md")]
                + [path for path in (skill_root / "resources" / "raw_sql").rglob("*") if path.is_file()]
            )
            self.assertEqual(
                {path.relative_to(skill_root).as_posix() for path in actual},
                set(inventory),
            )
            for path in actual:
                relative = path.relative_to(skill_root).as_posix()
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), inventory[relative]["sha256"])
            self.assertEqual(expected_baseline[domain][0], manifest["counts"]["knowledge_files"])
            self.assertEqual(expected_baseline[domain][1], manifest["counts"]["raw_sql_files"])
            current_registry = manifest["current_model_registry"]
            current_registry_path = skill_root / current_registry["source_path"]
            current_registry_payload = json.loads(current_registry_path.read_text(encoding="utf-8"))
            self.assertEqual(
                hashlib.sha256(current_registry_path.read_bytes()).hexdigest(),
                current_registry["source_sha256"],
            )
            self.assertEqual(domain, current_registry_payload["domain"])
            self.assertEqual(len(current_registry_payload["models"]), current_registry["model_count"])
            self.assertEqual(
                len(current_registry_payload["semantic_slots"]),
                current_registry["semantic_slot_count"],
            )
            self.assertEqual(
                current_registry_payload["canonical_filename_policy"],
                current_registry["canonical_filename_policy"],
            )
            self.assertIn(
                "semantic/current_model_bindings.json",
                manifest["progressive_disclosure"]["forward"],
            )
            for category, entities in manifest["entities"].items():
                for entity in entities:
                    self.assertTrue(entity["id"].startswith(f"{domain}:{category}:"))
            registry = manifest["dashboard_registry"]
            self.assertEqual(registry["count"], len(registry["registered"]))
            self.assertGreater(registry["count"], 0)
            self.assertEqual([], registry["cross_domain_conflicts"])
            profile_sources = {
                item["source_path"]: item["sha256"]
                for item in manifest["entities"]["dashboard_web_profiles"]
            }
            for dashboard in registry["registered"]:
                for evidence in dashboard["evidence"]:
                    self.assertEqual(
                        profile_sources[evidence["source_path"]],
                        evidence["source_sha256"],
                    )

    def test_physical_catalog_contains_no_temporary_or_business_entities(self) -> None:
        catalog = json.loads((CORE_ROOT / "catalog" / "physical_catalog.json").read_text(encoding="utf-8"))
        self.assertEqual("neutral_physical_tables_only", catalog["scope"])
        self.assertTrue(catalog["tables"])
        self.assertFalse(any(item["name"].startswith("temp_table.") for item in catalog["tables"]))
        self.assertTrue(all(item["business_semantics_excluded"] for item in catalog["tables"]))
        shared = [item for item in catalog["tables"] if len(item["domains"]) == 2]
        self.assertGreaterEqual(len(shared), 15)

    def test_same_name_temporary_tables_remain_domain_local(self) -> None:
        boundaries = []
        for domain, config in DOMAIN_CONFIG.items():
            manifest = json.loads(
                (REPO_ROOT / config["skill"] / "semantic" / "domain_manifest.json").read_text(encoding="utf-8")
            )
            boundary = manifest["boundary"]
            boundaries.append(set(boundary["same_name_temp_tables_require_domain_evidence"]))
            for key in ("domain_local_temp_tables", "exclusive_temp_tables", "forbidden_temp_tables"):
                self.assertTrue(all(name.startswith("temp_table.") for name in boundary[key]), (domain, key))
        self.assertEqual(boundaries[0], boundaries[1])
        self.assertTrue(boundaries[0])

    def test_forward_and_reverse_lookup_reach_domain_evidence(self) -> None:
        for domain, config in DOMAIN_CONFIG.items():
            bundle = CatalogBundle.load(REPO_ROOT / config["skill"], CORE_ROOT)
            results = bundle.search("转化", limit=50)
            self.assertTrue(results, domain)
            self.assertTrue(any(row["category"] in {"metrics", "dashboards", "sql_patterns"} for row in results))
            reverse = bundle.domain_manifest["reverse_lookup"]["table_to_sources"]
            self.assertTrue(reverse)
            self.assertTrue(all(source.startswith(("knowledge/", "resources/raw_sql/")) for values in reverse.values() for source in values))

    def test_ast_parses_representative_sql_for_each_domain(self) -> None:
        fixtures = {
            "market_consultant": "resources/raw_sql/data_center_market_2253.sql",
            "qingcheng": "resources/raw_sql/data_center_qingcheng_2460.sql",
        }
        for domain, relative in fixtures.items():
            skill_root = REPO_ROOT / DOMAIN_CONFIG[domain]["skill"]
            sql = (skill_root / relative).read_text(encoding="utf-8-sig")
            result = validate_sql_ast(
                sql,
                skill_root=skill_root,
                core_root=CORE_ROOT,
                expected_domain=domain,
                allow_unknown_tables=False,
            )
            errors = [item.to_dict() for item in result.diagnostics if item.severity == "error"]
            self.assertEqual([], errors, (domain, errors[:5]))

    def test_cross_domain_temporary_table_is_rejected(self) -> None:
        skill_root = REPO_ROOT / DOMAIN_CONFIG["market_consultant"]["skill"]
        result = validate_sql_ast(
            "select * from temp_table.dingxi01_qing_team_jg",
            skill_root=skill_root,
            core_root=CORE_ROOT,
            expected_domain="market_consultant",
        )
        self.assertIn("CROSS_DOMAIN_TEMP_TABLE", {item.code for item in result.diagnostics})

    def test_domain_catalog_rejects_foreign_metric_source(self) -> None:
        from text2sql_core.models import QuerySpec

        bundle = CatalogBundle.load(
            REPO_ROOT / DOMAIN_CONFIG["market_consultant"]["skill"],
            CORE_ROOT,
        )
        spec = QuerySpec.from_dict(
            {
                "domain": "market_consultant",
                "intent": "metric_query",
                "metrics": [
                    {
                        "id": "market_consultant:conversion",
                        "name": "conversion",
                        "source_path": "knowledge/metrics/qingcheng_conversion_metrics.md",
                    }
                ],
                "dimensions": ["period"],
                "filters": [],
                "time_range": {"start": "2026-07-01", "end": "2026-07-01"},
                "calculation_grain": ["period"],
                "output_grain": ["period"],
                "candidate_tables": [],
                "join_path": [],
                "evidence": [],
                "unresolved_slots": [],
            }
        )
        self.assertIn(
            "SPEC_EVIDENCE_NOT_IN_DOMAIN_CATALOG",
            {item.code for item in bundle.validate_query_spec(spec)},
        )

    def test_retained_sql_corpus_is_parsed_or_explicitly_classified(self) -> None:
        result = audit_raw_sql(REPO_ROOT, CORE_ROOT / "config" / "corpus_exceptions.json")
        self.assertTrue(result["ok"], result)
        self.assertEqual(63, result["domains"]["market_consultant"]["total"])
        self.assertEqual(4, result["domains"]["market_consultant"]["templates"])
        self.assertEqual(1, result["domains"]["market_consultant"]["allowed_legacy_failures"])
        self.assertEqual(17, result["domains"]["qingcheng"]["total"])
        self.assertEqual(1, result["domains"]["qingcheng"]["templates"])


if __name__ == "__main__":
    unittest.main()
