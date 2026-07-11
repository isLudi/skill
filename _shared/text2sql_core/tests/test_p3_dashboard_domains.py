from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from text2sql_core.dashboard_domains import (
    DOMAIN_SKILLS,
    validate_dashboard_domain_registration,
)


class DashboardDomainRegistrationTests(unittest.TestCase):
    dashboard_id = "dashboard_1234567890"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for domain in DOMAIN_SKILLS:
            self._write_domain(domain, registered=(domain == "qingcheng"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_domain(self, domain: str, *, registered: bool) -> Path:
        skill_root = self.root / DOMAIN_SKILLS[domain]
        source_path = "knowledge/dashboard_web_profiles/profile.md"
        source = skill_root / source_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            f"# profile\n\ndashboard_id: `{self.dashboard_id}`\n",
            encoding="utf-8",
        )
        source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
        evidence = [
            {
                "source_path": source_path,
                "source_sha256": source_sha256,
            }
        ]
        manifest = {
            "domain": {"id": domain},
            "dashboard_registry": {
                "registered": (
                    [
                        {
                            "dashboard_id": self.dashboard_id,
                            "status": "registered",
                            "evidence": evidence,
                        }
                    ]
                    if registered
                    else []
                )
            },
            "entities": {
                "dashboard_web_profiles": [
                    {
                        "source_path": source_path,
                        "sha256": source_sha256,
                    }
                ]
            },
        }
        manifest_path = skill_root / "semantic/domain_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return source

    def test_registered_dashboard_accepts_only_its_domain(self) -> None:
        resolution, diagnostics = validate_dashboard_domain_registration(
            self.dashboard_id,
            "qingcheng",
            repo_root=self.root,
        )
        self.assertEqual("registered", resolution["status"])
        self.assertEqual([], diagnostics)

        resolution, diagnostics = validate_dashboard_domain_registration(
            self.dashboard_id,
            "market_consultant",
            repo_root=self.root,
        )
        self.assertEqual("blocked", resolution["status"])
        self.assertIn(
            "DASHBOARD_DOMAIN_REGISTRATION_MISMATCH",
            {item["code"] for item in diagnostics},
        )

    def test_unregistered_dashboard_is_blocked(self) -> None:
        resolution, diagnostics = validate_dashboard_domain_registration(
            "dashboard_9999999999",
            "qingcheng",
            repo_root=self.root,
        )
        self.assertEqual("blocked", resolution["status"])
        self.assertIn("DASHBOARD_DOMAIN_UNREGISTERED", {item["code"] for item in diagnostics})

    def test_stale_source_hash_is_blocked(self) -> None:
        source = self.root / DOMAIN_SKILLS["qingcheng"] / "knowledge/dashboard_web_profiles/profile.md"
        source.write_text("changed", encoding="utf-8")
        resolution, diagnostics = validate_dashboard_domain_registration(
            self.dashboard_id,
            "qingcheng",
            repo_root=self.root,
        )
        self.assertEqual("blocked", resolution["status"])
        self.assertIn(
            "DASHBOARD_DOMAIN_EVIDENCE_HASH_MISMATCH",
            {item["code"] for item in diagnostics},
        )

    def test_cross_domain_duplicate_is_blocked(self) -> None:
        self._write_domain("market_consultant", registered=True)
        resolution, diagnostics = validate_dashboard_domain_registration(
            self.dashboard_id,
            "qingcheng",
            repo_root=self.root,
        )
        self.assertEqual("blocked", resolution["status"])
        self.assertIn("DASHBOARD_DOMAIN_AMBIGUOUS", {item["code"] for item in diagnostics})


if __name__ == "__main__":
    unittest.main()
