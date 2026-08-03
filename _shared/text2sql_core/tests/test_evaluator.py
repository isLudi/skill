from __future__ import annotations

import sys
import unittest
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CORE_ROOT.parents[1]
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.builder import DOMAIN_CONFIG  # noqa: E402
from text2sql_core.evaluator import evaluate_resolution_cases  # noqa: E402


class EvaluatorCoverageTests(unittest.TestCase):
    def test_curated_adversarial_and_alias_inventory_pass_for_each_domain(self) -> None:
        for domain, config in DOMAIN_CONFIG.items():
            with self.subTest(domain=domain):
                report = evaluate_resolution_cases(REPO_ROOT / config["skill"], domain)
                self.assertTrue(report["ok"], report["failures"][:5])
                self.assertGreaterEqual(report["curated"]["total"], 16)
                self.assertGreater(report["alias_recall"]["total"], report["curated"]["total"])
                self.assertEqual(report["alias_recall"]["recall"], 1.0)
                self.assertIn("adversarial_sql_text", report["curated"]["categories"])


if __name__ == "__main__":
    unittest.main()
