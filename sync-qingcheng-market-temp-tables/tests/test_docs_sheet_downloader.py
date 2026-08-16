from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from docs_sheet_downloader import (  # noqa: E402
    DocsSheetDownloadError,
    inspect_workbook,
    load_env_file,
    validate_source_url,
)


class DocsSheetDownloaderTests(unittest.TestCase):
    def test_env_file_supports_quotes_without_exposing_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials.env"
            path.write_text(
                "BAIJIA_USERNAME='user@example.com'\nBAIJIA_PASSWORD=\"secret\"\n",
                encoding="utf-8",
            )

            values = load_env_file(path)

        self.assertEqual(values["BAIJIA_USERNAME"], "user@example.com")
        self.assertEqual(values["BAIJIA_PASSWORD"], "secret")

    def test_env_file_selects_registered_section_and_rejects_unscoped_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials.env"
            path.write_text(
                "# USQL Web Query (Playwright) credentials\n"
                "BAIJIA_USERNAME='usql_user'\n"
                "BAIJIA_PASSWORD='usql_password'\n\n"
                "# tiangong2 Web Query (Playwright) credentials\n"
                "BAIJIA_USERNAME='tiangong_user'\n"
                "BAIJIA_PASSWORD='tiangong_password'\n",
                encoding="utf-8",
            )

            scoped = load_env_file(
                path,
                section="USQL Web Query (Playwright) credentials",
            )

            with self.assertRaisesRegex(DocsSheetDownloadError, "duplicate key"):
                load_env_file(path)

        self.assertEqual(
            scoped,
            {
                "BAIJIA_USERNAME": "usql_user",
                "BAIJIA_PASSWORD": "usql_password",
            },
        )

    def test_source_url_is_restricted_to_registered_https_docs_sheet(self) -> None:
        patterns = [r"^https://docs\.baijia\.com/sheet/[A-Za-z0-9]+(?:\?[^\s]*)?$"]

        validate_source_url(
            "https://docs.baijia.com/sheet/ABC123?tab=current",
            patterns,
        )
        with self.assertRaises(DocsSheetDownloadError):
            validate_source_url("https://example.com/sheet/ABC123", patterns)

    def test_workbook_inspection_records_active_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "course.xlsx"
            workbook = Workbook()
            workbook.active.title = "0722期"
            current = workbook.create_sheet("0728期")
            workbook.active = workbook.index(current)
            workbook.save(path)
            workbook.close()

            result = inspect_workbook(path)

        self.assertEqual(result["active_sheet"], "0728期")
        self.assertEqual(result["active_sheet_index"], 1)
        self.assertEqual(result["sheet_count"], 2)


if __name__ == "__main__":
    unittest.main()
