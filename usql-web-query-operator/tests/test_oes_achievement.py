from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from _shared.config import DEFAULT_OES_STATE, DEFAULT_STATE, OES_CREDENTIAL_SECTION, OES_RUNTIME_DIR  # noqa: E402
from _shared.errors import UsageError  # noqa: E402
from oes_achievement.board import build_payload, resolve_date_range  # noqa: E402
from oes_achievement.cli import build_parser  # noqa: E402
from oes_achievement.session import load_credentials, state_expiry_summary, validate_state_path  # noqa: E402


class OesConfigurationTests(unittest.TestCase):
    def test_exact_credential_section_is_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "usql_api.env"
            env_file.write_text(
                "# another\nBAIJIA_USERNAME=wrong\nBAIJIA_PASSWORD=wrong\n"
                f"# {OES_CREDENTIAL_SECTION}\nBAIJIA_USERNAME=oes-user\nBAIJIA_PASSWORD=oes-pass\n",
                encoding="utf-8",
            )
            credentials = load_credentials(env_file)
        self.assertEqual(credentials.username, "oes-user")
        self.assertEqual(credentials.password, "oes-pass")
        self.assertNotIn("oes-pass", repr(credentials))

    def test_state_is_isolated(self) -> None:
        self.assertNotEqual(DEFAULT_OES_STATE, DEFAULT_STATE)
        self.assertEqual(DEFAULT_OES_STATE.parent, OES_RUNTIME_DIR)
        validate_state_path(DEFAULT_OES_STATE)
        with self.assertRaisesRegex(UsageError, "isolated runtime"):
            validate_state_path(DEFAULT_STATE)

    def test_expiry_summary_never_returns_cookie_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            state.write_text(
                '{"cookies":[{"domain":"mi.gaotu100.com","name":"session","value":"secret","expires":-1}]}',
                encoding="utf-8",
            )
            summary = state_expiry_summary(state)
        self.assertEqual(summary[0]["name"], "session")
        self.assertTrue(summary[0]["session_cookie"])
        self.assertNotIn("value", summary[0])
        self.assertNotIn("secret", repr(summary))


class OesDateFilterTests(unittest.TestCase):
    def test_single_date_and_range(self) -> None:
        self.assertEqual(resolve_date_range("2026-10-03", None, None), (date(2026, 10, 3), date(2026, 10, 3)))
        self.assertEqual(resolve_date_range(None, "2026-10-01", "2026-10-03"), (date(2026, 10, 1), date(2026, 10, 3)))

    def test_incomplete_or_reversed_range_is_rejected(self) -> None:
        with self.assertRaises(UsageError):
            resolve_date_range(None, "2026-10-01", None)
        with self.assertRaises(UsageError):
            resolve_date_range(None, "2026-10-03", "2026-10-01")

    def test_payload_preserves_observed_api_contract(self) -> None:
        payload = build_payload(date(2026, 10, 3), date(2026, 10, 3), page_num=2, page_size=500)
        self.assertEqual(payload["pager"], {"pageNum": 2, "pageSize": 500})
        self.assertEqual(payload["roleSign"], 1)
        self.assertIsNone(payload["employeeName"])
        self.assertLess(int(payload["beginTime"]), int(payload["endTime"]))

    def test_export_parser_accepts_single_date(self) -> None:
        args = build_parser().parse_args(["export", "--output-dir", "out", "--date", "2026-10-03"])
        self.assertEqual(args.date, "2026-10-03")


if __name__ == "__main__":
    unittest.main()
