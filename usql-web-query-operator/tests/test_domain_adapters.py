from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from _shared.domain_adapters import (  # noqa: E402
    adapters_by_domain,
    adapters_by_target,
    dashboard_folder_adapters,
    load_domain_adapters,
)
from _shared.errors import UsageError  # noqa: E402


class DomainAdapterRegistryTests(unittest.TestCase):
    def test_default_registry_resolves_current_domain_skills(self) -> None:
        adapters = load_domain_adapters()
        by_target = adapters_by_target(adapters)
        by_domain = adapters_by_domain(adapters)
        by_folder = dashboard_folder_adapters(adapters)

        self.assertEqual(
            by_target["market"].skill_name,
            "market-consultant-dashboard-sql",
        )
        self.assertEqual(
            by_target["market"].skill_root.name,
            "market-consultant-dashboard-sql",
        )
        self.assertEqual(
            by_domain["qingcheng"].skill_name,
            "qingcheng-dashboard-sql",
        )
        self.assertEqual(
            by_folder["市场顾问数据"].domain_id,
            "market_consultant",
        )
        self.assertEqual(by_folder["青橙播报"].domain_id, "qingcheng")

    def test_registry_rejects_relative_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills_root = root / "skills"
            skill_root = skills_root / "market-skill"
            skill_root.mkdir(parents=True)
            (skill_root / "metadata.json").write_text(
                json.dumps(
                    {
                        "name": "market-skill",
                        "domain_id": "market_consultant",
                    }
                ),
                encoding="utf-8",
            )
            registry = self._registry("market-skill")
            registry["adapters"][0]["dashboard"]["profiles_dir"] = "../escape"
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            with self.assertRaisesRegex(UsageError, "safe relative path"):
                load_domain_adapters(registry_path, skills_root=skills_root)

    def test_registry_rejects_skill_metadata_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills_root = root / "skills"
            skill_root = skills_root / "market-skill"
            skill_root.mkdir(parents=True)
            (skill_root / "metadata.json").write_text(
                json.dumps(
                    {
                        "name": "different-name",
                        "domain_id": "market_consultant",
                    }
                ),
                encoding="utf-8",
            )
            registry_path = root / "registry.json"
            registry_path.write_text(
                json.dumps(self._registry("market-skill")),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(UsageError, "metadata name mismatch"):
                load_domain_adapters(registry_path, skills_root=skills_root)

    @staticmethod
    def _registry(skill_name: str) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "adapters": [
                {
                    "target": "market",
                    "domain_id": "market_consultant",
                    "skill_name": skill_name,
                    "row_style": "market",
                    "dashboard": {
                        "profile_folders": ["market-folder"],
                        "edit_folders": ["market-folder"],
                        "knowledge_folders": ["market-folder"],
                        "profiles_dir": "knowledge/dashboard_web_profiles",
                        "profiles_readme": "knowledge/dashboard_web_profiles/README.md",
                        "dashboards_readme": "knowledge/dashboards/README.md",
                        "changelog": "knowledge/update_log/changelog.md",
                    },
                    "data_center": {
                        "selector": "market_from_start",
                        "dataset_prefix": "market",
                        "doc_filename": "data_center_market_datasets.md",
                        "title": "Market",
                        "scope_note_template": "Market from {market_start_name}.",
                    },
                }
            ],
        }


if __name__ == "__main__":
    unittest.main()
