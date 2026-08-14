from __future__ import annotations

import unittest
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from tiangong2_task.analysis import analyze_source
from tiangong2_task.redaction import redact_structure, redact_text


class Tiangong2RedactionTests(unittest.TestCase):
    def test_literal_secrets_are_redacted_without_hiding_variable_reference(self) -> None:
        source = (
            'DORIS_PASSWORD="literal-secret-value"\n'
            'url="https://example.test/hook?token=url-secret-value"\n'
            'AUTHORIZATION=unquoted-secret-value\n'
            'dsn="mysql://reader:database-password@example.test/db"\n'
            'mysql -h example.test -ureader -pcommand-password\n'
            'print("${DORIS_PASSWORD}")\n'
        )
        result = redact_text(source)
        self.assertNotIn("literal-secret-value", result.text)
        self.assertNotIn("url-secret-value", result.text)
        self.assertNotIn("unquoted-secret-value", result.text)
        self.assertNotIn("database-password", result.text)
        self.assertNotIn("command-password", result.text)
        self.assertIn("${DORIS_PASSWORD}", result.text)
        self.assertGreaterEqual(len(result.findings), 2)

    def test_nested_secret_named_fields_are_redacted(self) -> None:
        redacted, findings = redact_structure(
            {"source": {"password": "secret-value", "table": "db.table"}}
        )
        self.assertEqual(redacted["source"]["password"], "<redacted>")
        self.assertEqual(redacted["source"]["table"], "db.table")
        self.assertTrue(findings)


class Tiangong2AnalysisTests(unittest.TestCase):
    def test_static_analysis_extracts_data_flow_without_execution(self) -> None:
        source = """
import requests
DROP TABLE IF EXISTS mart.refund_daily;
CREATE TABLE mart.refund_daily AS
SELECT a.user_id FROM dw.refund_detail a JOIN dim.user_info b ON a.user_id=b.user_id;
CREATE DATABASE IF NOT EXISTS reporting;
requests.post("https://open.feishu.cn/open-apis/bot/v2/hook/<redacted>")
"""
        result = analyze_source(
            task_name="refund_to_feishu",
            path=["数据开发", "owner", "refund_to_feishu"],
            task_type_name="PYTHON",
            source_kind="python",
            source=source,
            redactions=[{"rule": "feishu_webhook", "count": 1}],
        )
        self.assertIn("mart.refund_daily", result["created_tables"])
        self.assertIn("mart.refund_daily", result["dropped_or_truncated_tables"])
        self.assertIn("dw.refund_detail", result["read_tables"])
        self.assertIn("Feishu/Lark", result["systems"])
        self.assertIn("reporting", result["created_databases_or_schemas"])
        self.assertIn("database_or_schema_creation_present", result["risk_findings"])
        self.assertIn("destructive_table_ddl_present", result["risk_findings"])
        self.assertIn("财务流水与退费", result["workflow_categories"])


if __name__ == "__main__":
    unittest.main()
