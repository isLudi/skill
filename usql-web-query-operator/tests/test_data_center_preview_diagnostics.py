import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from usql_web_query.data_center_ui import compact_api_response


class DataCenterPreviewDiagnosticTests(unittest.TestCase):
    def test_error_message_is_retained_and_sensitive_parts_are_redacted(self):
        summary = compact_api_response({"status": "error", "errorCode": 400,
                                        "errorMessage": "missing field; token=abc123; sql[select secret]"})
        self.assertIn("missing field", summary["errorMessage"])
        self.assertNotIn("abc123", summary["errorMessage"])
        self.assertNotIn("select secret", summary["errorMessage"])
