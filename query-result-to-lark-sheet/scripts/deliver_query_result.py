"""Plan, apply, and verify a query-result delivery to a new Feishu Sheet node.

The script deliberately keeps business semantics out of the delivery layer. It
consumes named local result files and operator evidence, calls lark-cli through
argument arrays, and writes only runtime plans/receipts supplied by the caller.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import warnings
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    warnings.filterwarnings("ignore", message=r"Pandas requires version .*bottleneck.*")
    import pandas as pd
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit("pandas is required; use D:\\anaconda3\\python.exe") from exc


SCRIPT_VERSION = "1.2.0"
DEFAULT_PARENT_URL = "https://gaotuedu.feishu.cn/wiki/FcLew9hPXi5ViSkxsf9cvrtCnZb"
META_SHEET = "运行元数据"
DATE_NAME_RE = re.compile(r"(日期|时间|date|time|dt|hour)", re.IGNORECASE)
A1_RANGE_RE = re.compile(r"^([A-Z]+)([1-9][0-9]*):([A-Z]+)([1-9][0-9]*)$")
DOMAIN_TITLE_PREFIX = {
    "market_consultant": "市场顾问部_",
    "qingcheng": "青橙项目部_",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=json_default).encode("utf-8")
    return sha256_bytes(encoded)


def json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def clean_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def parse_input_spec(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ValueError(f"--input must be NAME=PATH: {spec}")
    name, raw_path = spec.split("=", 1)
    name = name.strip()
    path = Path(raw_path.strip()).expanduser().resolve()
    if not name:
        raise ValueError("input sheet name cannot be empty")
    if not path.is_file():
        raise FileNotFoundError(path)
    if name == META_SHEET:
        raise ValueError(f"{META_SHEET} is reserved for generated run metadata")
    return name, path


def cli_command(args: list[str]) -> list[str]:
    """Resolve the Windows lark-cli shim without requiring shell=True."""
    for candidate in ("lark-cli.cmd", "lark-cli.exe", "lark-cli", "lark-cli.ps1"):
        resolved = shutil.which(candidate)
        if not resolved:
            continue
        if resolved.lower().endswith(".ps1"):
            return ["powershell.exe", "-NoProfile", "-File", resolved, *args]
        return [resolved, *args]
    raise FileNotFoundError("lark-cli was not found on PATH")


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        frame = pd.read_excel(path, sheet_name=0)
    elif suffix == ".csv":
        frame = pd.read_csv(path)
    elif suffix == ".tsv":
        frame = pd.read_csv(path, sep="\t")
    elif suffix == ".json":
        frame = pd.read_json(path)
    else:
        raise ValueError(f"unsupported input type: {path.suffix}; use csv/tsv/xlsx/xlsm/json")
    if not isinstance(frame, pd.DataFrame):
        raise ValueError(f"input is not a tabular dataset: {path}")
    frame.columns = [str(column) for column in frame.columns]
    return frame


def maybe_parse_dates(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in result.columns:
        if not DATE_NAME_RE.search(column) or pd.api.types.is_numeric_dtype(result[column]):
            continue
        non_empty = result[column].dropna()
        if non_empty.empty:
            continue
        parsed = pd.to_datetime(non_empty, errors="coerce")
        if parsed.notna().all():
            result[column] = pd.to_datetime(result[column], errors="coerce")
    return result


def dtype_name(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime64[ns]"
    if pd.api.types.is_integer_dtype(series):
        return "Int64"
    if pd.api.types.is_float_dtype(series):
        return "float64"
    return "object"


def frame_to_sheet(frame: pd.DataFrame, name: str) -> dict[str, Any]:
    frame = maybe_parse_dates(frame)
    columns = [str(column) for column in frame.columns]
    dtypes = {column: dtype_name(frame[column]) for column in columns}
    data = [[clean_value(value) for value in row] for row in frame.itertuples(index=False, name=None)]
    return {
        "name": name,
        "mode": "overwrite",
        "header": True,
        "allow_overwrite": True,
        "columns": columns,
        "data": data,
        "dtypes": dtypes,
    }


def load_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("--metadata-json must contain a JSON object")
    return payload


def validate_title(title: str, domain: Any) -> dict[str, Any]:
    domain_name = str(domain or "").strip()
    prefix = DOMAIN_TITLE_PREFIX.get(domain_name)
    if prefix is None:
        allowed = ", ".join(sorted(DOMAIN_TITLE_PREFIX))
        raise ValueError(f"metadata.domain must be one of {allowed}; got {domain_name!r}")
    if not title.startswith(prefix):
        raise ValueError(f"title must start with {prefix!r} for domain {domain_name}")
    tail = title[len(prefix) :]
    if not tail or tail.startswith("_") or tail.endswith("_") or "__" in tail:
        raise ValueError("title must contain a non-empty suffix and single underscores between name segments")
    if any(char in tail for char in ("-", "—", "－", " ", "\t", "/", "\\", "／")):
        raise ValueError("title segments must use underscores; spaces, hyphens, and slashes are not allowed")
    segments = tail.split("_")
    if any(not segment for segment in segments):
        raise ValueError("title segments must not be empty")
    return {"domain": domain_name, "required_prefix": prefix, "segments": segments}


def column_letter(number: int) -> str:
    if number < 1:
        raise ValueError("column number must be positive")
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def quote_sheet_name(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def load_pivot_specs(path: Path | None, input_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        raw_pivots = payload.get("pivots")
    else:
        raw_pivots = payload
    if not isinstance(raw_pivots, list) or not raw_pivots:
        raise ValueError("--pivot-spec must contain a non-empty pivots array")
    by_name = {item["name"]: item for item in input_records}
    pivots: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for index, raw in enumerate(raw_pivots, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"pivot #{index} must be an object")
        name = str(raw.get("name") or f"pivot_{index}").strip()
        source_sheet = str(raw.get("source_sheet") or "").strip()
        if not source_sheet or source_sheet not in by_name:
            raise ValueError(f"pivot {name!r} source_sheet must name an input sheet")
        if name in seen_names:
            raise ValueError(f"duplicate pivot name: {name}")
        seen_names.add(name)
        source_record = by_name[source_sheet]
        source_columns = source_record["columns"]
        source_row_end = int(source_record["row_count"]) + 1
        source_col_end = column_letter(len(source_columns))
        raw_range = str(raw.get("source_range") or f"A1:{source_col_end}{source_row_end}").upper()
        match = A1_RANGE_RE.fullmatch(raw_range)
        if not match or match.group(1) != "A" or match.group(2) != "1":
            raise ValueError(f"pivot {name!r} source_range must start at A1 and use A1:END notation")
        if int(match.group(4)) != source_row_end or match.group(3) != source_col_end:
            raise ValueError(
                f"pivot {name!r} source_range must cover the exact input table A1:{source_col_end}{source_row_end}"
            )
        properties: dict[str, Any] = {}
        for key in (
            "rows",
            "columns",
            "values",
            "filters",
            "auto_fit_col",
            "show_row_grand_total",
            "show_col_grand_total",
            "show_subtotals",
            "repeat_row_labels",
            "calculated_fields",
            "collapse",
        ):
            if key in raw:
                properties[key] = raw[key]
        field_groups = ("rows", "columns", "filters", "values")
        if not any(properties.get(key) for key in field_groups):
            raise ValueError(f"pivot {name!r} needs at least one rows/columns/filters/values field")
        for group in field_groups:
            for field_item in properties.get(group, []):
                if not isinstance(field_item, dict) or not field_item.get("field"):
                    raise ValueError(f"pivot {name!r} has an invalid {group} item")
                if field_item["field"] not in source_columns:
                    raise ValueError(f"pivot {name!r} field not found in {source_sheet}: {field_item['field']}")
        pivots.append(
            {
                "name": name,
                "source_sheet": source_sheet,
                "source_range": raw_range,
                "source": f"{quote_sheet_name(source_sheet)}!{raw_range}",
                "properties": properties,
            }
        )
    return pivots


def parent_info(parent_url: str) -> dict[str, Any]:
    result = run_cli(["wiki", "+node-get", "--node-token", parent_url, "--as", "user", "--format", "json"])
    data = result.get("data", {})
    if data.get("obj_type") != "docx":
        raise ValueError(f"parent Wiki node must be docx; got {data.get('obj_type')!r}")
    return data


def node_url(parent_url: str, node_token: str) -> str:
    parsed = urlparse(parent_url)
    return f"{parsed.scheme}://{parsed.netloc}/wiki/{node_token}"


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    parent = parent_info(args.parent_url)
    input_specs = [parse_input_spec(spec) for spec in args.input]
    names = [name for name, _ in input_specs]
    if len(names) != len(set(names)):
        raise ValueError("input sheet names must be unique")
    input_records: list[dict[str, Any]] = []
    for name, path in input_specs:
        frame = read_table(path)
        if frame.empty and not args.allow_empty:
            raise ValueError(f"empty input blocked: {path}; pass --allow-empty only for verified empty results")
        frame = maybe_parse_dates(frame)
        columns = [str(column) for column in frame.columns]
        dtypes = {column: dtype_name(frame[column]) for column in columns}
        schema = {"columns": columns, "dtypes": dtypes}
        input_records.append(
            {
                "name": name,
                "path": str(path),
                "source_sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "row_count": int(len(frame)),
                "columns": columns,
                "dtypes": dtypes,
                "schema_sha256": canonical_hash(schema),
            }
        )
    metadata = load_metadata(Path(args.metadata_json).resolve() if args.metadata_json else None)
    title_naming = validate_title(args.title, metadata.get("domain"))
    pivots = load_pivot_specs(Path(args.pivot_spec).resolve() if args.pivot_spec else None, input_records)
    plan: dict[str, Any] = {
        "schema_version": "1.0.0",
        "skill_version": SCRIPT_VERSION,
        "plan_created_at": utc_now(),
        "parent_url": args.parent_url,
        "parent_node_token": parent.get("node_token"),
        "parent_space_id": parent.get("space_id"),
        "parent_title": parent.get("title"),
        "parent_obj_type": parent.get("obj_type"),
        "title": args.title,
        "title_naming": title_naming,
        "placement": args.placement,
        "inputs": input_records,
        "pivots": pivots,
        "metadata": metadata,
        "allow_empty": bool(args.allow_empty),
    }
    plan["plan_sha256"] = canonical_hash(plan)
    return plan


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")


def load_plan(path: Path) -> dict[str, Any]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("plan_sha256") != canonical_hash({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("plan_sha256 mismatch")
    return plan


def assert_sources_unchanged(plan: dict[str, Any]) -> None:
    for item in plan["inputs"]:
        path = Path(item["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != item["source_sha256"]:
            raise ValueError(f"source hash drift: {path}")


def revision(url: str) -> str | None:
    result = run_cli(["sheets", "+revision-get", "--url", url, "--as", "user", "--format", "json"])
    return result.get("data", {}).get("revision")


def workbook_info(url: str) -> dict[str, Any]:
    result = run_cli(["sheets", "+workbook-info", "--url", url, "--as", "user", "--format", "json"])
    return result.get("data", {})


def table_get(url: str) -> dict[str, Any]:
    result = run_cli(["sheets", "+table-get", "--url", url, "--as", "user", "--format", "json"])
    return result.get("data", {})


def create_node(plan: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    command = [
        "wiki",
        "+node-create",
        "--space-id",
        str(plan["parent_space_id"]),
        "--obj-type",
        "sheet",
        "--title",
        plan["title"],
    ]
    if plan.get("placement", "parent") == "parent":
        command.extend(["--parent-node-token", plan["parent_node_token"]])
    command.extend(["--as", "user", "--format", "json"])
    result = run_cli(
        command
    )
    data = result.get("data", {})
    token = data.get("node_token")
    if not token:
        raise RuntimeError("node-create returned no node_token")
    return token, node_url(plan["parent_url"], token), data


def build_payload(plan: dict[str, Any], query_id: str | None, sql_sha256: str | None, result_artifact_hash: str | None) -> tuple[dict[str, Any], dict[str, str]]:
    sheets: list[dict[str, Any]] = []
    expected_hashes: dict[str, str] = {}
    total_rows = 0
    for item in plan["inputs"]:
        frame = read_table(Path(item["path"]))
        sheet = frame_to_sheet(frame, item["name"])
        sheets.append(sheet)
        expected_hashes[item["name"]] = normalized_content_hash(sheet["columns"], sheet["data"])
        total_rows += len(frame)
    metadata = {
        "domain": plan.get("metadata", {}).get("domain"),
        "report_key": plan.get("metadata", {}).get("report_key"),
        "query_id": query_id or plan.get("metadata", {}).get("query_id"),
        "sql_sha256": sql_sha256 or plan.get("metadata", {}).get("sql_sha256"),
        "result_artifact_hash": result_artifact_hash or plan.get("metadata", {}).get("result_artifact_hash"),
        "plan_sha256": plan["plan_sha256"],
        "input_count": len(plan["inputs"]),
        "input_rows_total": total_rows,
        "pivot_count": len(plan.get("pivots", [])),
        "input_hashes": ";".join(f"{item['name']}={item['source_sha256']}" for item in plan["inputs"]),
        "schema_hashes": ";".join(f"{item['name']}={item['schema_sha256']}" for item in plan["inputs"]),
        "created_at": utc_now(),
    }
    metadata_frame = pd.DataFrame([metadata])
    metadata_sheet = frame_to_sheet(metadata_frame, META_SHEET)
    sheets.append(metadata_sheet)
    expected_hashes[META_SHEET] = normalized_content_hash(metadata_sheet["columns"], metadata_sheet["data"])
    return {"sheets": sheets}, expected_hashes


def rename_initial_sheet(url: str, info: dict[str, Any], title: str) -> None:
    sheets = info.get("sheets", [])
    if len(sheets) != 1:
        return
    first = sheets[0]
    current = first.get("title") or first.get("sheet_name")
    sheet_id = first.get("sheet_id")
    if not sheet_id or not current or current == title:
        return
    run_cli(
        [
            "sheets",
            "+sheet-rename",
            "--url",
            url,
            "--sheet-id",
            sheet_id,
            "--title",
            title,
            "--as",
            "user",
            "--format",
            "json",
        ]
    )


def normalized_content_hash(columns: list[Any], data: list[Any]) -> str:
    """Hash values/columns while tolerating Lark's numeric dtype widening."""
    return canonical_hash({"columns": columns, "data": normalize_hash_value(data)})


def normalize_hash_value(value: Any) -> Any:
    if isinstance(value, list):
        return [normalize_hash_value(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_hash_value(item) for key, item in value.items()}
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        midnight = re.fullmatch(r"(\d{4}-\d{2}-\d{2})T00:00:00(?:\.0+)?(?:Z)?", value)
        if midnight:
            return midnight.group(1)
    return value


def normalized_remote_hash(sheet: dict[str, Any]) -> str:
    return normalized_content_hash(sheet.get("columns", []), sheet.get("data", []))


def pivot_objects(value: Any) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    seen: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            pivot_id = item.get("pivot_table_id") or item.get("pivot_id") or item.get("pivotTableId")
            if pivot_id:
                key = str(pivot_id)
                if key not in seen:
                    seen.add(key)
                    objects.append(item)
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return objects


def pivot_readback(url: str, info: dict[str, Any]) -> dict[str, Any]:
    listings: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for sheet in info.get("sheets", []):
        sheet_id = sheet.get("sheet_id") or sheet.get("id")
        if not sheet_id:
            continue
        result = run_cli(
            [
                "sheets",
                "+pivot-list",
                "--url",
                url,
                "--sheet-id",
                str(sheet_id),
                "--as",
                "user",
                "--format",
                "json",
            ],
            allow_failure=True,
        )
        if result.get("ok") is not True:
            failures.append({"sheet_id": sheet_id, "title": sheet.get("title"), "result": result})
        else:
            listings.append({"sheet_id": sheet_id, "title": sheet.get("title"), "data": result.get("data", {})})
    objects = pivot_objects(listings)
    errors: list[dict[str, Any]] = []
    for obj in objects:
        info_value = obj.get("info")
        if isinstance(info_value, dict):
            error_state = info_value.get("error_state")
            if error_state not in (None, "", "None", "none"):
                errors.append({"pivot_table_id": obj.get("pivot_table_id") or obj.get("pivot_id"), "error_state": error_state})
    return {"listings": listings, "failures": failures, "objects": objects, "errors": errors}


def create_and_verify_pivots(url: str, plan: dict[str, Any]) -> dict[str, Any]:
    requested = plan.get("pivots", [])
    if not requested:
        return {"requested": [], "created": [], "readback": {"listings": [], "failures": [], "objects": [], "errors": []}}
    created: list[dict[str, Any]] = []
    for pivot in requested:
        result = run_cli(
            [
                "sheets",
                "+pivot-create",
                "--url",
                url,
                "--source",
                pivot["source"],
                "--properties",
                "-",
                "--as",
                "user",
                "--format",
                "json",
            ],
            input_payload=pivot["properties"],
        )
        created.append({"name": pivot["name"], "source": pivot["source"], "result": result})
    readback = pivot_readback(url, workbook_info(url))
    if readback["failures"]:
        raise RuntimeError(f"pivot-list failed for one or more sheets: {readback['failures']}")
    if len(readback["objects"]) < len(requested):
        raise RuntimeError(
            f"pivot readback count mismatch: requested={len(requested)}, observed={len(readback['objects'])}"
        )
    if readback["errors"]:
        raise RuntimeError(f"pivot readback has error_state: {readback['errors']}")
    return {"requested": requested, "created": created, "readback": readback}


def apply_plan(args: argparse.Namespace) -> dict[str, Any]:
    if not args.confirm_write:
        raise ValueError("remote apply requires --confirm-write")
    plan_path = Path(args.plan).resolve()
    plan = load_plan(plan_path)
    assert_sources_unchanged(plan)
    validate_title(plan["title"], plan.get("metadata", {}).get("domain"))
    parent = parent_info(plan["parent_url"])
    if parent.get("node_token") != plan.get("parent_node_token") or parent.get("space_id") != plan.get("parent_space_id"):
        raise ValueError("parent node drift")
    query_id = args.query_id
    sql_sha256 = args.sql_sha256
    result_artifact_hash = args.result_artifact_hash
    payload, expected_hashes = build_payload(plan, query_id, sql_sha256, result_artifact_hash)
    node_token: str | None = None
    node_url_value: str | None = None
    receipt: dict[str, Any] = {
        "schema_version": "1.0.0",
        "delivery_id": str(uuid.uuid4()),
        "started_at": utc_now(),
        "status": "failed",
        "fully_verified": False,
        "parent_url": plan["parent_url"],
        "parent_node_token": plan["parent_node_token"],
        "parent_space_id": plan["parent_space_id"],
        "placement": plan.get("placement", "parent"),
        "title": plan["title"],
        "title_naming": plan.get("title_naming"),
        "plan_sha256": plan["plan_sha256"],
        "query_id": query_id,
        "sql_sha256": sql_sha256,
        "result_artifact_hash": result_artifact_hash,
        "expected_sheets": expected_hashes,
        "expected_pivots": [item["name"] for item in plan.get("pivots", [])],
        "pivot_results": None,
        "orphaned_node": None,
    }
    try:
        node_token, node_url_value, node_data = create_node(plan)
        receipt["node_token"] = node_token
        receipt["node_url"] = node_url_value
        receipt["spreadsheet_token"] = node_data.get("obj_token")
        info = workbook_info(node_url_value)
        first_input = plan["inputs"][0]["name"]
        rename_initial_sheet(node_url_value, info, first_input)
        before = revision(node_url_value)
        receipt["revision_before"] = before
        run_cli(["sheets", "+table-put", "--url", node_url_value, "--sheets", "-", "--as", "user", "--format", "json"], input_payload=payload)
        receipt["pivot_results"] = create_and_verify_pivots(node_url_value, plan)
        remote = table_get(node_url_value)
        remote_sheets = {sheet.get("name") or sheet.get("title"): sheet for sheet in remote.get("sheets", [])}
        readback: dict[str, Any] = {}
        for name, expected_hash in expected_hashes.items():
            remote_sheet = remote_sheets.get(name)
            if remote_sheet is None:
                raise RuntimeError(f"readback missing sheet: {name}")
            actual_hash = normalized_remote_hash(remote_sheet)
            readback[name] = {
                "row_count": len(remote_sheet.get("data", [])),
                "column_count": len(remote_sheet.get("columns", [])),
                "content_sha256": actual_hash,
                "expected_content_sha256": expected_hash,
                "ok": actual_hash == expected_hash,
            }
            if actual_hash != expected_hash:
                raise RuntimeError(f"readback hash mismatch: {name}")
        after = revision(node_url_value)
        receipt["revision_after"] = after
        receipt["readback_sheets"] = readback
        receipt["status"] = "success"
        receipt["fully_verified"] = True
        receipt["finished_at"] = utc_now()
    except Exception as exc:
        receipt["failure_reason"] = str(exc)
        receipt["orphaned_node"] = node_url_value
        receipt["finished_at"] = utc_now()
    output = Path(args.receipt_out).resolve()
    write_json(output, receipt)
    if receipt["status"] != "success":
        raise RuntimeError(f"delivery failed; receipt written to {output}")
    return receipt


def run_cli(args: list[str], *, allow_failure: bool = False, input_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    command = cli_command(args)
    stdin = None
    if input_payload is not None:
        stdin = json.dumps(input_payload, ensure_ascii=False).encode("utf-8")
    completed = subprocess.run(command, input=stdin, capture_output=True, text=False, env=env)
    stdout = completed.stdout.decode("utf-8", errors="replace").strip()
    stderr = completed.stderr.decode("utf-8", errors="replace").strip()
    if completed.returncode != 0:
        if allow_failure:
            return {"ok": False, "returncode": completed.returncode, "stdout": stdout, "stderr": stderr}
        raise RuntimeError(f"lark-cli failed ({completed.returncode}): {stderr or stdout}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"lark-cli returned non-JSON output: {stdout[:500]}") from exc
    if payload.get("ok") is not True:
        raise RuntimeError(f"lark-cli returned ok=false: {json.dumps(payload, ensure_ascii=False)[:1000]}")
    return payload


def verify_receipt(args: argparse.Namespace) -> dict[str, Any]:
    receipt = json.loads(Path(args.receipt).resolve().read_text(encoding="utf-8"))
    if receipt.get("status") != "success" or not receipt.get("fully_verified"):
        raise ValueError("receipt is not fully verified")
    remote = table_get(receipt["node_url"])
    remote_sheets = {sheet.get("name") or sheet.get("title"): sheet for sheet in remote.get("sheets", [])}
    checks = {}
    for name, expected in receipt.get("expected_sheets", {}).items():
        actual = remote_sheets.get(name)
        if actual is None:
            checks[name] = False
            continue
        checks[name] = normalized_remote_hash(actual) == expected
    pivot_check = None
    if receipt.get("expected_pivots"):
        pivot_state = pivot_readback(receipt["node_url"], workbook_info(receipt["node_url"]))
        pivot_check = {
            "requested_count": len(receipt["expected_pivots"]),
            "observed_count": len(pivot_state["objects"]),
            "failures": pivot_state["failures"],
            "errors": pivot_state["errors"],
            "ok": (
                not pivot_state["failures"]
                and not pivot_state["errors"]
                and len(pivot_state["objects"]) >= len(receipt["expected_pivots"])
            ),
        }
    result = {
        "ok": all(checks.values()) and (pivot_check is None or pivot_check["ok"]),
        "node_url": receipt["node_url"],
        "checks": checks,
        "pivot_check": pivot_check,
        "revision": revision(receipt["node_url"]),
    }
    if not result["ok"]:
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    return result


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--parent-url", default=DEFAULT_PARENT_URL)
    plan.add_argument("--title", required=True)
    plan.add_argument("--placement", choices=("parent", "space-root"), default="space-root")
    plan.add_argument("--input", action="append", required=True, help="NAME=PATH; repeat for multiple child sheets")
    plan.add_argument("--metadata-json")
    plan.add_argument("--pivot-spec", help="JSON file describing native Lark pivot objects")
    plan.add_argument("--allow-empty", action="store_true")
    plan.add_argument("--output", required=True)
    apply = sub.add_parser("apply")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--confirm-write", action="store_true")
    apply.add_argument("--query-id")
    apply.add_argument("--sql-sha256")
    apply.add_argument("--result-artifact-hash")
    apply.add_argument("--receipt-out", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--receipt", required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "plan":
            plan = build_plan(args)
            write_json(Path(args.output).resolve(), plan)
            print(json.dumps({"status": "ready", "plan": args.output, "plan_sha256": plan["plan_sha256"], "sheets": [item["name"] for item in plan["inputs"] + [{"name": META_SHEET}]], "pivots": [item["name"] for item in plan.get("pivots", [])], "placement": plan["placement"]}, ensure_ascii=False))
        elif args.command == "apply":
            receipt = apply_plan(args)
            print(json.dumps({"status": "success", "fully_verified": True, "node_url": receipt["node_url"], "receipt": args.receipt_out}, ensure_ascii=False))
        else:
            print(json.dumps(verify_receipt(args), ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
