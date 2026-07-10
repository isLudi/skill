"""Create a temporary Template Query, run it, download the result, and clean up."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.debug import save_debug_artifacts
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from usql_web_query.artifact_validation import DownloadArtifactError
from usql_web_query.sql_utils import read_sql
from usql_web_query.template_query import (
    TemplateQuery,
    TemplateQueryClient,
    TemplateQueryExecution,
    parse_download_type,
)


SUCCESS_QUERY_STATUS = 3


def cmd_template_download(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    sql = read_sql(args.sql_file)
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir) if args.debug_artifacts else args.artifacts_dir
    if args.output_file is not None:
        ensure_runtime([args.output_file.parent])

    sync_playwright = import_playwright()
    started_at = time.monotonic()
    template: TemplateQuery | None = None
    template_status: int | None = None
    query: TemplateQueryExecution | None = None
    query_log: dict[str, Any] | None = None
    query_result: dict[str, Any] | None = None
    download_path: Path | None = None
    actual_download_format = args.download_format
    download_fallback_reason: str | None = None
    error_message: str | None = None
    download_skipped_reason: str | None = None
    cleanup = {
        "attempted": not args.keep_template,
        "offlineApplied": False,
        "deleted": False,
        "errors": [],
    }

    with sync_playwright() as playwright:
        browser, context = launch_context(
            playwright,
            args.state_path,
            args.headed,
            args.browser_channel,
            args.executable_path,
        )
        page = context.new_page()
        try:
            client = TemplateQueryClient(page, args.state_path)
            client.ensure_authenticated(args.username, args.password)

            auth_profile = client.fetch_auth_profile()
            creator = _required_text(auth_profile.get("name"), "Template Query creator name")
            template_name = args.template_name or _default_template_name()
            _validate_template_name(template_name)
            template_description = args.template_description or f"Codex temp download from {args.sql_file.name}"

            template = client.save_template(
                name=template_name,
                description=template_description,
                sql=sql,
                creator=creator,
                owner="",
            )
            template_status = template.status or 1

            client.publish_template(template.id)
            template_status = 2

            query_detail = client.fetch_query_detail(template_id=template.id, query_type=1)
            unresolved_conditions = _collect_unresolved_conditions(query_detail)
            if unresolved_conditions:
                joined = ", ".join(unresolved_conditions)
                raise UsageError(
                    "Template Query download currently supports concrete SQL without template parameters. "
                    f"Found unresolved query conditions: {joined}"
                )

            query_name = args.query_name or _default_query_name(template.name)
            query_id = client.create_query(
                query_name=query_name,
                template_id=template.id,
                query_type=1,
                required_conditions=_copy_rows(query_detail.get("requiredConditions")),
                partition_conditions=_copy_rows(query_detail.get("partitionConditions")),
                query_column=_select_all_query_columns(query_detail.get("queryColumn")),
                query_conditions=_copy_rows(query_detail.get("queryConditions")),
            )

            query = client.wait_for_query_completion(
                query_id=query_id,
                timeout_ms=args.timeout_ms,
                poll_interval_ms=args.poll_interval_ms,
            )

            if query.status != SUCCESS_QUERY_STATUS:
                query_log = client.fetch_query_log(query.id)
                raise UsageError(_build_query_failure_message(query, query_log))

            query_result = client.fetch_query_result(query.id)

            if (query.count or 0) > 0:
                expected_columns = _query_result_column_count(query_result)
                download_path, actual_download_format, download_fallback_reason = (
                    _download_with_csv_fallback(
                        client=client,
                        query_id=query.id,
                        requested_format=args.download_format,
                        artifacts_dir=artifacts_dir,
                        output_file=args.output_file,
                        expected_rows=query.count,
                        expected_columns=expected_columns,
                    )
                )
            else:
                download_skipped_reason = "query returned 0 rows"
        except Exception as exc:
            error_message = str(exc)
            if args.debug_artifacts:
                try:
                    save_debug_artifacts(page, artifacts_dir, "error")
                except Exception:
                    pass
        finally:
            if template is not None and not args.keep_template:
                _cleanup_template(client=TemplateQueryClient(page, args.state_path), template=template, current_status=template_status, cleanup=cleanup)
            context.close()
            browser.close()

    elapsed_seconds = round(time.monotonic() - started_at, 3)
    ok = error_message is None and not cleanup["errors"]
    if error_message is None and query is not None and (query.count or 0) == 0:
        message = "Query finished with 0 rows."
    elif error_message is None:
        message = "Template Query download finished."
    elif download_path is not None and not cleanup["errors"]:
        message = f"Download finished, but the command reported an error: {error_message}"
    else:
        message = error_message
    if cleanup["errors"]:
        ok = False
        cleanup_error = "; ".join(cleanup["errors"])
        message = f"{message} Cleanup failed: {cleanup_error}" if message else f"Cleanup failed: {cleanup_error}"

    summary = {
        "ok": ok,
        "message": message,
        "template": template.to_summary_json() if template else None,
        "query": query.to_summary_json() if query else None,
        "queryLog": query_log,
        "queryResult": _compact_query_result(query_result) if query_result else None,
        "downloadFormat": args.download_format,
        "downloadFormatRequested": args.download_format,
        "downloadFormatActual": actual_download_format,
        "downloadFallbackReason": download_fallback_reason,
        "downloadPath": str(download_path) if download_path else None,
        "downloadSkippedReason": download_skipped_reason,
        "cleanup": cleanup,
        "state_path": str(args.state_path),
        "artifacts_dir": str(artifacts_dir),
        "elapsed_seconds": elapsed_seconds,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def _validate_template_name(name: str) -> None:
    normalized = name.strip()
    if not normalized:
        raise UsageError("Template Query template name cannot be empty.")
    if len(normalized) > 20:
        raise UsageError(f"Template Query template name must be 20 characters or fewer: {name}")


def _default_template_name() -> str:
    centiseconds = (time.time_ns() // 10_000_000) % 100
    return f"td_{time.strftime('%Y%m%d%H%M%S')}{centiseconds:02d}"[:20]


def _default_query_name(template_name: str) -> str:
    return f"{template_name}_{time.strftime('%Y-%m-%d %H:%M:%S')}"


def _required_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise UsageError(f"Missing {label} from Template Query auth profile.")
    return text


def _copy_rows(rows: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in rows or [] if isinstance(row, dict)]


def _select_all_query_columns(rows: Any) -> list[dict[str, Any]]:
    columns = [dict(row) for row in rows or [] if isinstance(row, dict)]
    if not columns:
        raise UsageError("Template Query query/detail returned no query columns.")
    for column in columns:
        column["selected"] = True
    return columns


def _collect_unresolved_conditions(detail: dict[str, Any]) -> list[str]:
    unresolved: list[str] = []
    for key in ("requiredConditions", "queryConditions", "partitionConditions"):
        for row in detail.get(key) or []:
            if isinstance(row, dict):
                unresolved.append(_condition_name(row))
    return unresolved


def _condition_name(row: dict[str, Any]) -> str:
    for key in ("showName", "name", "paramName", "columnName"):
        text = str(row.get(key) or "").strip()
        if text:
            return text
    return json.dumps(row, ensure_ascii=False)


def _build_query_failure_message(query: TemplateQueryExecution, query_log: dict[str, Any] | None) -> str:
    log_text = ""
    task_status = None
    if isinstance(query_log, dict):
        log_text = str(query_log.get("data") or "").strip()
        task_status = query_log.get("taskStatus")
    log_tail = "\n".join(log_text.splitlines()[-8:]).strip()
    base = (
        "Template Query execution did not finish successfully: "
        f"queryId={query.id}, status={query.status}, statusLabel={query.status_label}, taskStatus={task_status}"
    )
    if log_tail:
        return f"{base}\n{log_tail}"
    return base


def _compact_query_result(result: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "records": result.get("records"),
        "meta": result.get("meta"),
    }
    data_rows = result.get("data")
    if isinstance(data_rows, list):
        compact["previewRows"] = data_rows[:5]
    else:
        compact["previewRows"] = None
    return compact


def _query_result_column_count(result: dict[str, Any] | None) -> int | None:
    if not isinstance(result, dict):
        return None
    meta = result.get("meta")
    return len(meta) if isinstance(meta, list) and meta else None


def _csv_fallback_output(output_file: Path | None) -> Path | None:
    if output_file is None:
        return None
    return output_file if output_file.suffix.lower() == ".csv" else output_file.with_suffix(".csv")


def _download_with_csv_fallback(
    *,
    client: TemplateQueryClient,
    query_id: int,
    requested_format: str,
    artifacts_dir: Path,
    output_file: Path | None,
    expected_rows: int | None,
    expected_columns: int | None,
) -> tuple[Path, str, str | None]:
    download_type = parse_download_type(requested_format)
    try:
        path = client.download_query_result(
            query_id=query_id,
            download_type=download_type,
            artifacts_dir=artifacts_dir,
            output_file=output_file,
            expected_rows=expected_rows,
            expected_columns=expected_columns,
        )
        return path, requested_format, None
    except DownloadArtifactError as exc:
        if download_type != parse_download_type("xls"):
            raise
        fallback_reason = f"{exc.code}: {exc}"
        path = client.download_query_result(
            query_id=query_id,
            download_type=parse_download_type("csv"),
            artifacts_dir=artifacts_dir,
            output_file=_csv_fallback_output(output_file),
            expected_rows=expected_rows,
            expected_columns=expected_columns,
        )
        return path, "csv", fallback_reason


def download_concrete_sql_via_template_csv(
    *,
    page: Any,
    state_path: Path,
    sql: str,
    artifacts_dir: Path,
    username: str | None,
    password: str | None,
    timeout_ms: int,
    poll_interval_ms: int = 2000,
) -> tuple[Path, dict[str, Any]]:
    """Re-run concrete SQL through a temporary Template Query and return CSV.

    This is the correctness fallback for direct downloads that resolve to XML
    listings or header-only Excel workbooks. The temporary template is always
    taken offline and deleted before success is reported.
    """

    client = TemplateQueryClient(page, state_path)
    template: TemplateQuery | None = None
    template_status: int | None = None
    query: TemplateQueryExecution | None = None
    query_result: dict[str, Any] | None = None
    error: Exception | None = None
    download_path: Path | None = None
    cleanup: dict[str, Any] = {
        "attempted": True,
        "offlineApplied": False,
        "deleted": False,
        "errors": [],
    }
    try:
        client.ensure_authenticated(username, password)
        auth_profile = client.fetch_auth_profile()
        creator = _required_text(auth_profile.get("name"), "Template Query creator name")
        template = client.save_template(
            name=_default_template_name(),
            description="Codex automatic fallback for invalid direct download artifact",
            sql=sql,
            creator=creator,
            owner="",
        )
        template_status = template.status or 1
        client.publish_template(template.id)
        template_status = 2
        query_detail = client.fetch_query_detail(template_id=template.id, query_type=1)
        unresolved_conditions = _collect_unresolved_conditions(query_detail)
        if unresolved_conditions:
            raise UsageError(
                "Automatic Template Query fallback requires concrete SQL without template parameters. "
                f"Found unresolved query conditions: {', '.join(unresolved_conditions)}"
            )
        query_id = client.create_query(
            query_name=_default_query_name(template.name),
            template_id=template.id,
            query_type=1,
            required_conditions=_copy_rows(query_detail.get("requiredConditions")),
            partition_conditions=_copy_rows(query_detail.get("partitionConditions")),
            query_column=_select_all_query_columns(query_detail.get("queryColumn")),
            query_conditions=_copy_rows(query_detail.get("queryConditions")),
        )
        query = client.wait_for_query_completion(
            query_id=query_id,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )
        if query.status != SUCCESS_QUERY_STATUS:
            raise UsageError(_build_query_failure_message(query, client.fetch_query_log(query.id)))
        if (query.count or 0) <= 0:
            raise UsageError("Automatic Template Query fallback returned 0 rows.")
        query_result = client.fetch_query_result(query.id)
        download_path = client.download_query_result(
            query_id=query.id,
            download_type=parse_download_type("csv"),
            artifacts_dir=artifacts_dir,
            expected_rows=query.count,
            expected_columns=_query_result_column_count(query_result),
        )
    except Exception as exc:  # noqa: BLE001
        error = exc
    finally:
        if template is not None:
            _cleanup_template(
                client=client,
                template=template,
                current_status=template_status,
                cleanup=cleanup,
            )

    if error is not None:
        if cleanup["errors"]:
            raise UsageError(f"{error} Cleanup failed: {'; '.join(cleanup['errors'])}") from error
        raise error
    if cleanup["errors"]:
        raise UsageError(f"Automatic Template Query fallback cleanup failed: {'; '.join(cleanup['errors'])}")
    if download_path is None or query is None or template is None:
        raise UsageError("Automatic Template Query fallback did not produce a CSV artifact.")
    return download_path, {
        "source": "temporary_template_csv",
        "templateId": template.id,
        "queryId": query.id,
        "rowCount": query.count,
        "actualFormat": "csv",
        "cleanup": cleanup,
    }


def _cleanup_template(
    *,
    client: TemplateQueryClient,
    template: TemplateQuery,
    current_status: int | None,
    cleanup: dict[str, Any],
) -> None:
    try:
        if current_status == 2:
            client.offline_template(template.id)
            cleanup["offlineApplied"] = True
            current_status = 3
        client.delete_template(template.id)
        cleanup["deleted"] = True
    except Exception as exc:
        if current_status != 2:
            try:
                client.offline_template(template.id)
                cleanup["offlineApplied"] = True
                client.delete_template(template.id)
                cleanup["deleted"] = True
                return
            except Exception as nested_exc:
                cleanup["errors"].append(str(nested_exc))
                return
        cleanup["errors"].append(str(exc))
