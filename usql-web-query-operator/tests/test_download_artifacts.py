from __future__ import annotations

import io
import sys
import unittest
import zipfile
import tempfile
from unittest.mock import patch
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.artifact_validation import (  # noqa: E402
    ArtifactInspection,
    DownloadArtifactError,
    inspect_download_bytes,
    validate_download_bytes,
)
from usql_web_query.commands.template_download import _download_with_csv_fallback  # noqa: E402
from usql_web_query.commands.run import _download_result  # noqa: E402
from usql_web_query.cli import build_parser  # noqa: E402


def xlsx_bytes(rows: list[list[str]]) -> bytes:
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            reference = f"{chr(64 + column_index)}{row_index}"
            cells.append(f'<c r="{reference}" t="inlineStr"><is><t>{value}</t></is></c>')
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData></worksheet>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as workbook:
        workbook.writestr("[Content_Types].xml", "<Types />")
        workbook.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()


class DownloadArtifactValidationTests(unittest.TestCase):
    def test_template_download_has_no_cleanup_bypass_flag(self) -> None:
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions if action.__class__.__name__ == "_SubParsersAction"
        )
        option_strings = {
            option
            for action in subparsers.choices["template-download"]._actions
            for option in action.option_strings
        }
        self.assertNotIn("--keep-template", option_strings)

    def test_xml_list_bucket_result_is_rejected_as_pseudo_csv(self) -> None:
        content = b'<?xml version="1.0"?><ListBucketResult><Name>bucket</Name></ListBucketResult>'

        inspection = inspect_download_bytes(content, expected_format="csv", expected_rows=2)

        self.assertFalse(inspection.valid)
        self.assertEqual(inspection.code, "xml_pseudo_result")
        with self.assertRaises(DownloadArtifactError):
            validate_download_bytes(content, expected_format="csv", expected_rows=2)

    def test_header_only_excel_is_rejected_when_query_has_rows(self) -> None:
        inspection = inspect_download_bytes(
            xlsx_bytes([["qici", "channel"]]),
            expected_format="xlsx",
            expected_rows=29,
            expected_columns=2,
        )

        self.assertFalse(inspection.valid)
        self.assertEqual(inspection.code, "header_only_excel")

    def test_incomplete_excel_header_is_rejected_against_metadata(self) -> None:
        inspection = inspect_download_bytes(
            xlsx_bytes([["qici"], ["20260626期"]]),
            expected_format="xlsx",
            expected_rows=1,
            expected_columns=3,
        )

        self.assertFalse(inspection.valid)
        self.assertEqual(inspection.code, "incomplete_excel_header")

    def test_valid_csv_and_excel_are_accepted(self) -> None:
        csv_result = inspect_download_bytes(
            "qici,channel\n20260626期,抖音复用\n".encode("utf-8"),
            expected_format="csv",
            expected_rows=1,
            expected_columns=2,
        )
        excel_result = inspect_download_bytes(
            xlsx_bytes([["qici", "channel"], ["20260626期", "抖音复用"]]),
            expected_format="xlsx",
            expected_rows=1,
            expected_columns=2,
        )

        self.assertTrue(csv_result.valid)
        self.assertTrue(excel_result.valid)

    def test_explicit_template_download_falls_back_from_xls_to_csv(self) -> None:
        class FakeClient:
            def __init__(self, output: Path):
                self.output = output
                self.download_types: list[int] = []
                self.output_files: list[Path | None] = []

            def download_query_result(self, **kwargs):
                self.download_types.append(kwargs["download_type"])
                self.output_files.append(kwargs["output_file"])
                if kwargs["download_type"] == 2:
                    raise DownloadArtifactError(
                        ArtifactInspection(
                            False,
                            "xlsx",
                            "header_only_excel",
                            "Downloaded Excel file is header-only.",
                            0,
                            2,
                        )
                    )
                return self.output

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            client = FakeClient(root / "result.csv")
            path, actual_format, reason = _download_with_csv_fallback(
                client=client,  # type: ignore[arg-type]
                query_id=10,
                requested_format="xls",
                artifacts_dir=root,
                output_file=root / "result.xlsx",
                expected_rows=29,
                expected_columns=2,
            )

        self.assertEqual(path.name, "result.csv")
        self.assertEqual(actual_format, "csv")
        self.assertIn("header_only_excel", reason or "")
        self.assertEqual(client.download_types, [2, 1])
        self.assertEqual(client.output_files[-1].suffix, ".csv")

    def test_invalid_direct_artifact_fails_closed_without_template_writes(self) -> None:
        error = DownloadArtifactError(
            ArtifactInspection(
                False,
                "csv",
                "xml_pseudo_result",
                "Downloaded CSV is an XML ListBucketResult payload.",
            )
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch(
                "usql_web_query.commands.run.click_download_button",
                side_effect=error,
            ):
                with self.assertRaises(UsageError) as raised:
                    _download_result(
                        page=object(),
                        artifacts_dir=root,
                        query_id="123",
                        expected_rows=29,
                        expected_columns=2,
                    )

        message = str(raised.exception)
        self.assertIn("No Template Query writes were attempted", message)
        self.assertIn("template-download", message)


if __name__ == "__main__":
    unittest.main()
