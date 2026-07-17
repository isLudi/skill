from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROCESS_SQL = SKILL_ROOT / "resources" / "raw_sql" / "data_center_qingcheng_2064.sql"
CONVERSION_SQL = SKILL_ROOT / "resources" / "raw_sql" / "data_center_qingcheng_2460.sql"
DIMENSION_CONTRACTS = SKILL_ROOT / "semantic" / "contracts" / "dimension_contracts.json"


class ChannelContractAlignmentTests(unittest.TestCase):
    def test_process_sql_uses_image_standard_channel_outputs(self) -> None:
        sql = PROCESS_SQL.read_text(encoding="utf-8")
        for expected in (
            "then concat('IP', chr(36192), chr(35838), chr(22833), chr(36133))",
            "then '星义IP'",
            "then '朱博士IP'",
            "then '春春IP'",
            "then '郭艺IP'",
            "then '抖音正价退费'",
            "then '进校9元'",
            "then '本地化'",
            "then '公域'",
            "then '图书'",
            "then '订单复用'",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, sql)

        for old_output in (
            "青橙私域",
            "青橙IP",
            "青橙公海",
            "青橙公域",
            "青橙图书",
            "青橙本地化",
            "青橙训练营",
            "IP星义",
            "IP朱博士",
            "IP春春",
            "IP郭艺",
            "IP亚飞",
        ):
            with self.subTest(old_output=old_output):
                self.assertIsNone(re.search(rf"then\s+'{old_output}'", sql, re.IGNORECASE))

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
                self.assertIn("进校9元", expression)
                if contract_id.endswith("process_channel_level_1"):
                    self.assertIn("concat('ip', chr(36192), chr(35838), chr(22833), chr(36133))", expression)
                    self.assertIsNone(re.search(r"then\s+'青橙ip'", expression, re.IGNORECASE))
                    self.assertIsNone(re.search(r"then\s+'青橙私域'", expression, re.IGNORECASE))
                else:
                    self.assertIn("then '抖音正价退费'", expression)
                    self.assertIn("then '星义ip'", expression)
                    self.assertIsNone(re.search(r"then\s+'ip星义'", expression, re.IGNORECASE))
                    self.assertIsNone(re.search(r"then\s+'青橙ip'", expression, re.IGNORECASE))

    def test_conversion_sql_carries_primary_channel_into_final_output(self) -> None:
        sql = CONVERSION_SQL.read_text(encoding="utf-8")
        self.assertIn("coalesce(bb1.channel_map_1, ud.channel_map_1, '未知') as channel_1", sql)
        self.assertIn("and ud.channel_map_1 = bb1.channel_map_1", sql)
        self.assertIn("mm.channel_1", sql)
        self.assertIn("when channel_map_2 = '进校9元' then 70", sql)
        self.assertNotIn("when channel_map_2 like '%IP%' then 'IP'", sql)
        self.assertNotIn("when channel_map_2 like '%进校%' then '进校'", sql)


if __name__ == "__main__":
    unittest.main()
