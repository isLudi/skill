"""Isolated local migration tests; never opens a browser or touches production data."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _shared.errors import UsageError
from usql_web_query.data_center_knowledge import data_center_apply_lock
from usql_web_query.temp_table_knowledge import apply_plan, build_plan, digest, safe_path


REAL = Path(__file__).resolve().parents[2]
OLD = "temp_table.dingxi01_qing_goal"
NEW = "temp_table.lvshuai01_qing_goal"


class TempTableKnowledgeMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "skills"
        self.root.mkdir()
        registry = "usql-web-query-operator/references/domain_adapters.json"
        self.put(registry, (REAL / registry).read_text(encoding="utf-8"))
        for name in ("qingcheng-dashboard-sql", "market-consultant-dashboard-sql"):
            self.put(name + "/metadata.json", (REAL / name / "metadata.json").read_text(encoding="utf-8"))
        self.domain = self.root / "qingcheng-dashboard-sql"
        self.old = self.domain / ("knowledge/temp_tables/" + OLD + ".md")
        self.new = self.domain / ("knowledge/temp_tables/" + NEW + ".md")
        self.put(str(self.old.relative_to(self.root)), "# " + OLD + "\n\nKnown join grain.\n")
        self.put("qingcheng-dashboard-sql/knowledge/metrics/goal.md", "# Goal\n" + OLD + "\n")
        self.put("qingcheng-dashboard-sql/knowledge/update_log/changelog.md", "# History\nOld table " + OLD + "\n")
        self.put("qingcheng-dashboard-sql/resources/raw_sql/source.sql", "select x from " + OLD)
        self.put("qingcheng-dashboard-sql/semantic/contracts/metric_contracts.json", json.dumps({"contracts": [{
            "source_path": "knowledge/metrics/goal.md", "source_sha256": "before", "table": OLD}]}))
        self.request = {"schema_version": "1.0.0", "as_of": "2026-11-28", "maintenance_change_confirmed": True,
                        "mappings": [{"target": "qingcheng", "old_table": OLD, "new_table": NEW}]}
        self.catalog = {NEW: {"id": "123", "name": NEW}}

    def put(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def plan(self):
        return build_plan(self.root, self.request, self.catalog)

    @staticmethod
    def good(*args):
        return [{"name": "test", "returncode": 0}]

    def apply(self, plan, maintain=None, catalog=None):
        return apply_plan(self.root, plan, plan["plan_sha256"], catalog or self.catalog,
                          self.base / "artifacts", maintain=maintain or self.good)

    def test_success_rewrites_current_contract_and_removes_legacy_doc_but_keeps_raw_sql(self):
        plan = self.plan()
        receipt = self.apply(plan)
        self.assertTrue(receipt["ok"])
        self.assertFalse(self.old.exists())
        self.assertTrue(self.new.read_text(encoding="utf-8").startswith("# " + NEW))
        metric = self.domain / "knowledge/metrics/goal.md"
        contract = json.loads((self.domain / "semantic/contracts/metric_contracts.json").read_text(encoding="utf-8"))["contracts"][0]
        self.assertEqual(NEW, contract["table"])
        self.assertEqual(digest(metric.read_bytes()), contract["source_sha256"])
        self.assertIn(OLD, (self.domain / "resources/raw_sql/source.sql").read_text(encoding="utf-8"))
        self.assertIn("Old table " + OLD, (self.domain / "knowledge/update_log/changelog.md").read_text(encoding="utf-8"))

    def test_existing_destination_requires_reviewed_merge_and_preserves_both_unique_facts(self):
        self.new.write_text("# " + NEW + "\nNew fact", encoding="utf-8")
        with self.assertRaisesRegex(UsageError, "reviewed"):
            self.plan()
        self.request["mappings"][0]["merged_markdown"] = "# " + NEW + "\nKnown join grain. New fact.\n"
        self.apply(self.plan())
        self.assertIn("Known join grain. New fact.", self.new.read_text(encoding="utf-8"))

    def test_source_drift_is_zero_write_and_preserves_the_new_user_edit(self):
        plan = self.plan()
        self.old.write_text("User changed source", encoding="utf-8")
        with self.assertRaisesRegex(UsageError, "source Hash drift"):
            self.apply(plan)
        self.assertEqual("User changed source", self.old.read_text(encoding="utf-8"))
        self.assertFalse(self.new.exists())
        self.assertFalse((self.base / "artifacts").exists())

    def test_hash_tamper_and_live_identity_drift_are_zero_write(self):
        plan = self.plan()
        wrong = copy.deepcopy(plan)
        wrong["mutations"][0]["content"] = "Injected"
        with self.assertRaisesRegex(UsageError, "Plan Hash"):
            self.apply(wrong)
        with self.assertRaisesRegex(UsageError, "live table identity"):
            self.apply(plan, catalog={NEW: {"id": "999", "name": NEW}})
        self.assertTrue(self.old.exists())

    def test_exclusive_lock_blocks_before_backups_and_writes(self):
        plan = self.plan()
        with data_center_apply_lock([SimpleNamespace(target=SimpleNamespace(root=self.domain))]):
            with self.assertRaisesRegex(UsageError, "lock"):
                self.apply(plan)
        self.assertTrue(self.old.exists())
        self.assertFalse((self.base / "artifacts").exists())

    def test_validation_failure_restores_exact_sources_and_generated_outputs(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

        def fail(root, adapters, logs, journal, snapshots):
            generated = self.domain / "semantic/domain_manifest.json"
            generated.parent.mkdir(parents=True, exist_ok=True)
            generated.write_bytes(b"generated")
            journal[generated] = digest(b"generated")
            raise UsageError("injected validation failure")

        with self.assertRaisesRegex(UsageError, "recovery=restored"):
            self.apply(self.plan(), fail)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        receipt = json.loads((self.base / "artifacts/receipt.json").read_text(encoding="utf-8"))
        self.assertEqual("restored", receipt["recovery"])
        self.assertTrue((self.base / "artifacts/baseline.zip").is_file())

    def test_third_state_is_not_overwritten_on_rollback(self):
        def concurrent(*args):
            self.new.write_text("Concurrent user edit", encoding="utf-8")
            raise UsageError("failed")
        with self.assertRaisesRegex(UsageError, "blocked_concurrent_change"):
            self.apply(self.plan(), concurrent)
        self.assertEqual("Concurrent user edit", self.new.read_text(encoding="utf-8"))
        self.assertTrue(self.old.exists())

    def test_unplanned_journal_path_is_preserved_and_recovery_is_blocked(self):
        extra = self.domain / "knowledge/unplanned.md"

        def fail(root, adapters, logs, journal, snapshots):
            extra.write_bytes(b"unplanned output")
            journal[extra] = digest(b"unplanned output")
            raise UsageError("injected validation failure")

        with self.assertRaisesRegex(UsageError, "blocked_concurrent_change"):
            self.apply(self.plan(), fail)
        self.assertEqual(b"unplanned output", extra.read_bytes())
        self.assertTrue(self.old.exists())
        self.assertFalse(self.new.exists())
        receipt = json.loads((self.base / "artifacts/receipt.json").read_text(encoding="utf-8"))
        self.assertIn(str(extra), receipt["conflicts"])

    def test_mappings_cannot_expand_to_other_owner_schema_suffix_or_domain(self):
        for key, value in (("target", "other"), ("new_table", "temp_table.lvshuai01_other"),
                           ("old_table", "service_dw.real")):
            bad = copy.deepcopy(self.request)
            bad["mappings"][0][key] = value
            with self.subTest(key=key), self.assertRaises(UsageError):
                build_plan(self.root, bad, self.catalog)
        for name in ("../other", "C:/outside", "/outside", "dir\\outside"):
            with self.subTest(name=name), self.assertRaises(UsageError):
                safe_path(self.root, name)

    def test_semantic_successor_needs_live_production_sql_not_just_owner_rename(self):
        reference = "temp_table.zhangjunyan01_pingyou_jg"
        self.put("qingcheng-dashboard-sql/knowledge/temp_tables/" + reference + ".md", "# " + reference)
        row = self.request["mappings"][0]
        row["current_reference_table"] = reference
        evidence = {"dataset_id": "menu_set_1", "model_id": "2688", "sql_sha256": "a" * 64}
        row["production_evidence"] = [evidence]
        with self.assertRaisesRegex(UsageError, "live production SQL"):
            self.plan()
        self.catalog["production_sql"] = {"menu_set_1": {**evidence, "temp_tables": [reference]}}
        self.apply(self.plan())
        contract = json.loads((self.domain / "semantic/contracts/metric_contracts.json").read_text(encoding="utf-8"))["contracts"][0]
        self.assertEqual(reference, contract["table"])
        self.assertTrue(self.new.exists())

    def test_unmodified_evidence_concurrent_change_is_preserved_and_causes_failure(self):
        raw = self.domain / "resources/raw_sql/source.sql"

        def change_evidence(*args):
            raw.write_text("Concurrent source edit", encoding="utf-8")
            return []

        with self.assertRaisesRegex(UsageError, "evidence changed"):
            self.apply(self.plan(), change_evidence)
        self.assertEqual("Concurrent source edit", raw.read_text(encoding="utf-8"))
        self.assertTrue(self.old.exists())

    def test_incremental_mapping_keeps_prior_registry_and_explicit_missing_doc_creation(self):
        self.apply(self.plan())
        old2, new2 = "temp_table.dingxi01_qing_new", "temp_table.lvshuai01_qing_new"
        self.request["mappings"] = [{"target": "qingcheng", "old_table": old2, "new_table": new2,
                                     "merged_markdown": "# " + new2 + "\nConfirmed source, no legacy document.\n"}]
        self.catalog = {new2: {"id": "456", "name": new2}}
        plan = self.plan()
        apply_plan(self.root, plan, plan["plan_sha256"], self.catalog, self.base / "incremental", maintain=self.good)
        registry = json.loads((self.domain / "semantic/temp_table_migrations.json").read_text(encoding="utf-8"))
        self.assertEqual({OLD, old2}, {r["old_table"] for r in registry["mappings"]})
        self.assertTrue(self.new.exists())
        self.assertFalse((self.domain / "knowledge/temp_tables" / (old2 + ".md")).exists())

    def test_explicit_retirement_removes_only_the_incomplete_document_and_links_current_source(self):
        reference = "temp_table.zhangjunyan01_pingyou_jg"
        self.put("qingcheng-dashboard-sql/knowledge/temp_tables/" + reference + ".md", "# " + reference)
        row = self.request["mappings"][0]
        row["current_reference_table"] = reference
        proof = {"dataset_id": "menu_set_1", "model_id": "2688", "sql_sha256": "a" * 64}
        row["production_evidence"] = [proof]
        self.catalog["production_sql"] = {"menu_set_1": {**proof, "temp_tables": [reference]}}
        self.apply(self.plan())
        row["retire_destination"] = True
        plan = self.plan()
        apply_plan(self.root, plan, plan["plan_sha256"], self.catalog, self.base / "retirement", maintain=self.good)
        self.assertFalse(self.new.exists())
        guide = (self.domain / "knowledge/temp_table_maintenance.md").read_text(encoding="utf-8")
        self.assertNotIn("(" + "temp_tables/" + NEW + ".md)", guide)
        self.assertIn(reference + ".md)", guide)

    def test_document_only_correction_is_hash_bound_and_rebinds_contract_source(self):
        source = self.domain / "knowledge/metrics/goal.md"
        before = source.read_bytes()
        self.request["mappings"] = []
        self.request["document_updates"] = [{"target": "qingcheng", "path": "knowledge/metrics/goal.md",
            "before_sha256": digest(before), "content": "# Goal\nReviewed current source.\n"}]
        self.apply(self.plan())
        contract = json.loads((self.domain / "semantic/contracts/metric_contracts.json").read_text(encoding="utf-8"))["contracts"][0]
        self.assertEqual(digest(source.read_bytes()), contract["source_sha256"])
        self.assertTrue(self.old.exists())


if __name__ == "__main__":
    unittest.main()
