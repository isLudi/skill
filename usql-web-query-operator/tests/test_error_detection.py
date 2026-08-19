from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from usql_web_query.error_detection import (  # noqa: E402
    _choose_error_candidate,
    _looks_like_error_text,
)


class ErrorDetectionTests(unittest.TestCase):
    def test_sql_business_literal_is_not_a_platform_error(self) -> None:
        sql_line = (
            "when flow_pool_name='电商退款用户池' "
            "then 'KOC赠课失败'"
        )

        self.assertFalse(_looks_like_error_text(sql_line))
        result = _choose_error_candidate(
            [{"source": "log_area", "raw": sql_line, "title": "", "detail": ""}]
        )
        self.assertEqual("none", result["source"])

    def test_diagnostic_outside_sql_literal_still_matches(self) -> None:
        self.assertTrue(_looks_like_error_text("Cannot cast '失败' as bigint"))
        self.assertTrue(_looks_like_error_text("Query failed near '赠课失败'"))


if __name__ == "__main__":
    unittest.main()
