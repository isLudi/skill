from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "deliver_query_result.py"
SPEC = importlib.util.spec_from_file_location("deliver_query_result", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TitleValidationTests(unittest.TestCase):
    def test_jingpin_title_is_accepted(self) -> None:
        result = MODULE.validate_title(
            "精品班学部_20260501起_暑秋退费专题", "jingpin_department"
        )
        self.assertEqual(result["required_prefix"], "精品班学部_")

    def test_jingpin_rejects_other_department_prefixes(self) -> None:
        for title in ("市场顾问部_20260501起_暑秋退费专题", "青橙项目部_20260501起_暑秋退费专题"):
            with self.subTest(title=title), self.assertRaises(ValueError):
                MODULE.validate_title(title, "jingpin_department")

    def test_jingpin_rejects_missing_prefix(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.validate_title("20260501起_暑秋退费专题", "jingpin_department")


if __name__ == "__main__":
    unittest.main()
