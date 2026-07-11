from __future__ import annotations

import json
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SQL = SKILL_ROOT / "resources" / "raw_sql" / "data_center_qingcheng_2064.sql"
DIMENSION_CONTRACTS = SKILL_ROOT / "semantic" / "contracts" / "dimension_contracts.json"


class ChannelContractAlignmentTests(unittest.TestCase):
    def test_douyin_refund_reuse_is_paired_in_sql_and_dimension_contracts(self) -> None:
        sql = CANONICAL_SQL.read_text(encoding="utf-8")
        branch = "when f.rule_name like '%抖音正价退费%' then '抖音复用'"
        self.assertEqual(sql.lower().count(branch.lower()), 2)

        envelope = json.loads(DIMENSION_CONTRACTS.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in envelope["contracts"]}
        for contract_id in (
            "qingcheng:dimension:process_channel_level_1",
            "qingcheng:dimension:process_channel_level_2",
        ):
            with self.subTest(contract_id=contract_id):
                contract = by_id[contract_id]
                self.assertEqual(contract["status"], "confirmed")
                self.assertTrue(contract["automatic_compile"])
                expression = contract["sql_expression"].lower()
                self.assertIn("%抖音正价退费%", expression)
                self.assertIn("'抖音复用'", expression)


if __name__ == "__main__":
    unittest.main()
