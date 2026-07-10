"""Validate downloaded SQL result artifacts before reporting success."""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from _shared.errors import UsageError


@dataclass(frozen=True)
class ArtifactInspection:
    valid: bool
    artifact_format: str
    code: str
    message: str
    data_rows: int | None = None
    columns: int | None = None


class DownloadArtifactError(UsageError):
    """The platform returned bytes that are not a usable query result."""

    def __init__(self, inspection: ArtifactInspection):
        super().__init__(inspection.message)
        self.inspection = inspection
        self.code = inspection.code


def inspect_download_bytes(
    content: bytes,
    *,
    expected_format: str,
    expected_rows: int | None = None,
    expected_columns: int | None = None,
) -> ArtifactInspection:
    normalized_format = expected_format.strip().lower()
    if normalized_format == "xls":
        normalized_format = "xlsx"
    if not content:
        return _invalid(normalized_format, "empty_artifact", "Downloaded result is empty.")

    xml_kind = _xml_payload_kind(content)
    if xml_kind:
        return _invalid(
            normalized_format,
            "xml_pseudo_result",
            f"Downloaded {normalized_format} is an XML {xml_kind} payload, not query-result data.",
        )

    if normalized_format == "csv":
        return _inspect_csv(
            content,
            expected_rows=expected_rows,
            expected_columns=expected_columns,
        )
    if normalized_format == "xlsx":
        return _inspect_xlsx(
            content,
            expected_rows=expected_rows,
            expected_columns=expected_columns,
        )
    return _invalid(
        normalized_format,
        "unsupported_artifact_format",
        f"Unsupported download artifact format: {expected_format}",
    )


def validate_download_bytes(
    content: bytes,
    *,
    expected_format: str,
    expected_rows: int | None = None,
    expected_columns: int | None = None,
) -> ArtifactInspection:
    inspection = inspect_download_bytes(
        content,
        expected_format=expected_format,
        expected_rows=expected_rows,
        expected_columns=expected_columns,
    )
    if not inspection.valid:
        raise DownloadArtifactError(inspection)
    return inspection


def validate_download_file(
    path: Path,
    *,
    expected_format: str,
    expected_rows: int | None = None,
    expected_columns: int | None = None,
) -> ArtifactInspection:
    return validate_download_bytes(
        path.read_bytes(),
        expected_format=expected_format,
        expected_rows=expected_rows,
        expected_columns=expected_columns,
    )


def _inspect_csv(
    content: bytes,
    *,
    expected_rows: int | None,
    expected_columns: int | None,
) -> ArtifactInspection:
    if content.startswith(b"PK\x03\x04"):
        return _invalid("csv", "format_mismatch", "Downloaded CSV contains an Excel ZIP payload.")
    text = _decode_csv(content)
    if text is None:
        return _invalid("csv", "csv_decode_failed", "Downloaded CSV could not be decoded as UTF-8 or GB18030.")
    try:
        rows = [row for row in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in row)]
    except csv.Error as exc:
        return _invalid("csv", "csv_parse_failed", f"Downloaded CSV could not be parsed: {exc}")
    if not rows:
        return _invalid("csv", "empty_csv", "Downloaded CSV contains no header or data rows.", data_rows=0, columns=0)
    columns = len(rows[0])
    data_rows = max(len(rows) - 1, 0)
    if expected_rows is not None and expected_rows > 0 and data_rows == 0:
        return _invalid(
            "csv",
            "header_only_csv",
            f"Downloaded CSV is header-only although the query reported {expected_rows} rows.",
            data_rows=data_rows,
            columns=columns,
        )
    if expected_columns is not None and expected_columns > 0 and columns < expected_columns:
        return _invalid(
            "csv",
            "incomplete_csv_header",
            f"Downloaded CSV has {columns} columns; query metadata reported {expected_columns}.",
            data_rows=data_rows,
            columns=columns,
        )
    return ArtifactInspection(True, "csv", "ok", "CSV artifact is usable.", data_rows, columns)


def _inspect_xlsx(
    content: bytes,
    *,
    expected_rows: int | None,
    expected_columns: int | None,
) -> ArtifactInspection:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as workbook:
            names = set(workbook.namelist())
            if "[Content_Types].xml" not in names:
                return _invalid("xlsx", "invalid_xlsx", "Downloaded Excel file is missing [Content_Types].xml.")
            sheet_names = sorted(
                name
                for name in names
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
            )
            if not sheet_names:
                return _invalid("xlsx", "empty_xlsx", "Downloaded Excel file contains no worksheets.")
            data_rows = 0
            columns = 0
            for sheet_name in sheet_names:
                root = ElementTree.fromstring(workbook.read(sheet_name))
                nonempty_rows: list[int] = []
                for row in root.findall(".//{*}row"):
                    cell_count = len(row.findall("{*}c"))
                    if cell_count:
                        nonempty_rows.append(cell_count)
                if nonempty_rows:
                    columns = max(columns, nonempty_rows[0])
                    data_rows += max(len(nonempty_rows) - 1, 0)
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
        return _invalid("xlsx", "invalid_xlsx", f"Downloaded Excel file is not a valid xlsx workbook: {exc}")

    if expected_rows is not None and expected_rows > 0 and data_rows == 0:
        return _invalid(
            "xlsx",
            "header_only_excel",
            f"Downloaded Excel file is header-only although the query reported {expected_rows} rows.",
            data_rows=data_rows,
            columns=columns,
        )
    if expected_columns is not None and expected_columns > 0 and columns < expected_columns:
        return _invalid(
            "xlsx",
            "incomplete_excel_header",
            f"Downloaded Excel header has {columns} columns; query metadata reported {expected_columns}.",
            data_rows=data_rows,
            columns=columns,
        )
    return ArtifactInspection(True, "xlsx", "ok", "Excel artifact is usable.", data_rows, columns)


def _decode_csv(content: bytes) -> str | None:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def _xml_payload_kind(content: bytes) -> str | None:
    head = content[:4096].lstrip(b"\xef\xbb\xbf\x00\t\r\n ").lower()
    if b"<listbucketresult" in head:
        return "ListBucketResult"
    if head.startswith(b"<?xml") or head.startswith(b"<error"):
        return "error/listing"
    return None


def _invalid(
    artifact_format: str,
    code: str,
    message: str,
    *,
    data_rows: int | None = None,
    columns: int | None = None,
) -> ArtifactInspection:
    return ArtifactInspection(False, artifact_format, code, message, data_rows, columns)
