import importlib.util
from pathlib import Path
import unittest

from lark_delivery.paths import SKILL_ROOT


class LayoutTests(unittest.TestCase):
    def test_code_and_docs_follow_registered_layout(self):
        spec = importlib.util.spec_from_file_location("data_push_layout_check", SKILL_ROOT / "scripts/validate_layout.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.validate()
        self.assertTrue(report["ok"], report["errors"])
