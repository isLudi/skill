"""Single-attempt query submission with privacy-preserving acknowledgement evidence."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import parse_qs, unquote_plus, urlsplit

from _shared.errors import UsageError

from .error_detection import ImmediatePlatformError, _is_immediate_platform_error, extract_error_from_page
from .page_helpers import dismiss_nps_if_present, get_sql_frame
from .query_history import _history_matches_sql, extract_open_query_tab_ids, extract_query_history_rows


@dataclass(frozen=True)
class SubmissionEvidence:
    query_id: str
    query_id_source: str
    mechanism: str
    attempt_count: int = 1
    request_path: str | None = None
    http_status: int | None = None
    submitted_sql_sha256: str | None = None
    submitted_engine: str | None = None

    def to_summary(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "query_id_source": self.query_id_source,
            "mechanism": self.mechanism,
            "attempt_count": self.attempt_count,
            "request_path": self.request_path,
            "http_status": self.http_status,
            "submitted_sql_sha256": self.submitted_sql_sha256,
            "submitted_engine": self.submitted_engine,
        }


def _iter_fields(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = path + (str(key),)
            yield child_path, item
            yield from _iter_fields(item, child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_fields(item, path + (str(index),))


def _decode_request_payload(request: Any) -> Any:
    try:
        payload = getattr(request, "post_data_json")
        payload = payload() if callable(payload) else payload
        if payload is not None:
            return payload
    except Exception:
        pass
    raw = getattr(request, "post_data", None)
    raw = raw() if callable(raw) else raw
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        parsed = parse_qs(raw, keep_blank_values=True)
        if parsed:
            return {key: values[0] if len(values) == 1 else values for key, values in parsed.items()}
    return unquote_plus(raw)


def _looks_like_sql(value: str) -> bool:
    return bool(re.match(r"^\s*(?:select|with)\b", value, flags=re.I | re.S))


def _submitted_sql(payload: Any) -> str | None:
    if isinstance(payload, str):
        return payload if _looks_like_sql(payload) else None
    preferred: list[str] = []
    fallback: list[str] = []
    for path, value in _iter_fields(payload):
        if not isinstance(value, str):
            continue
        key = path[-1].lower() if path else ""
        if "sql" in key and _looks_like_sql(value):
            preferred.append(value)
        elif key in {"query", "content", "value"} and _looks_like_sql(value):
            fallback.append(value)
    return (preferred or fallback or [None])[0]


def _submitted_engine(payload: Any) -> str | None:
    if not isinstance(payload, (dict, list)):
        return None
    preferred: list[str] = []
    fallback: list[str] = []
    for path, value in _iter_fields(payload):
        if not isinstance(value, (str, int)) or not path:
            continue
        key = path[-1].lower()
        rendered = str(value).strip()
        if not rendered:
            continue
        if "engine" in key or key in {"instancekey", "datasource", "datasourcekey"}:
            preferred.append(rendered[:200])
        elif key == "mode":
            fallback.append(rendered[:200])
    return (preferred or fallback or [None])[0]


def _extract_query_id(payload: Any) -> str | None:
    preferred: list[str] = []
    fallback: list[str] = []
    if isinstance(payload, (str, int)):
        text = str(payload)
        return text if re.fullmatch(r"\d{9,11}", text) else None
    for path, value in _iter_fields(payload):
        if not isinstance(value, (str, int)):
            continue
        text = str(value)
        if not re.fullmatch(r"\d{9,11}", text):
            continue
        key = path[-1].lower() if path else ""
        if key in {"queryid", "query_id"}:
            preferred.append(text)
        elif key in {"id", "taskid", "task_id", "data"}:
            fallback.append(text)
    return (preferred or fallback or [None])[0]


def summarize_submission_response(response: Any) -> dict[str, Any] | None:
    request = response.request
    method = str(getattr(request, "method", "")).upper()
    url = str(getattr(response, "url", ""))
    if method != "POST" or "uanalysis-sql" not in url:
        return None
    payload = _decode_request_payload(request)
    submitted_sql = _submitted_sql(payload)
    try:
        response_payload = response.json()
    except Exception:
        response_payload = None
    query_id = _extract_query_id(response_payload)
    path = urlsplit(url).path or None
    submission_path = bool(
        re.search(
            r"/(?:execute|run|submit)(?:/|$)|/(?:query|task)/(?:create|start|execute|submit)(?:/|$)",
            path or "",
            flags=re.I,
        )
    )
    if submitted_sql is None and not submission_path:
        return None
    return {
        "query_id": query_id,
        "request_path": path,
        "http_status": int(getattr(response, "status", 0)) or None,
        "submitted_sql_sha256": (
            hashlib.sha256(submitted_sql.encode("utf-8")).hexdigest()
            if submitted_sql is not None
            else None
        ),
        "submitted_engine": _submitted_engine(payload),
    }


def _matching_new_history_row(
    page: Any,
    existing_query_ids: set[str],
    expected_sql: str,
) -> dict[str, str] | None:
    return next(
        (
            row
            for row in extract_query_history_rows(page)
            if row.get("query_id") not in existing_query_ids
            and _history_matches_sql(row.get("text", ""), expected_sql)
        ),
        None,
    )


def _focus_editor_for_shortcut(page: Any) -> bool:
    for frame in getattr(page, "frames", []):
        if not str(getattr(frame, "url", "")).startswith("https://uanalysis.baijia.com/sql/"):
            continue
        try:
            return bool(
                frame.evaluate(
                    """() => {
                        const cmEl = document.querySelector('.CodeMirror');
                        if (!cmEl || !cmEl.CodeMirror) return false;
                        cmEl.CodeMirror.focus();
                        cmEl.CodeMirror.execCommand('selectAll');
                        return true;
                    }"""
                )
            )
        except Exception:
            continue
    return False


def _click_one_run_control(page: Any) -> str:
    frame = get_sql_frame(page)
    selectors = [
        ".antd-pro-src-components-editor-index-optBtnGroup button:has(.anticon-play-circle)",
        "button.antd-pro-src-components-editor-index-editorBtn:has(.anticon-play-circle)",
        "button:has([aria-label='play-circle'])",
        "button:has(.anticon-play-circle)",
        "button:has(svg[data-icon='play-circle'])",
    ]
    for selector in selectors:
        locator = frame.locator(selector).first
        try:
            if locator.count() == 0 or not locator.is_visible() or not locator.is_enabled():
                continue
            locator.click(timeout=5000)
            return "button"
        except Exception:
            continue
    if _focus_editor_for_shortcut(page):
        page.keyboard.press("Control+E")
        return "shortcut"
    raise UsageError("No enabled SQL run control was found.")


def click_run(
    page: Any,
    existing_query_ids: set[str],
    expected_sql: str,
    *,
    acknowledgement_timeout_ms: int = 15_000,
) -> SubmissionEvidence:
    """Submit exactly once and require one new query ID before status polling."""
    dismiss_nps_if_present(page)
    captured_responses: list[Any] = []

    def on_response(response: Any) -> None:
        request = response.request
        if str(getattr(request, "method", "")).upper() == "POST" and "uanalysis-sql" in str(
            getattr(response, "url", "")
        ):
            captured_responses.append(response)

    page.on("response", on_response)
    try:
        mechanism = _click_one_run_control(page)
        deadline = time.monotonic() + max(acknowledgement_timeout_ms, 0) / 1000
        expected_sql_sha256 = hashlib.sha256(expected_sql.encode("utf-8")).hexdigest()
        while True:
            response_summaries = [
                summary
                for response in captured_responses
                if (summary := summarize_submission_response(response)) is not None
            ]
            row = _matching_new_history_row(page, existing_query_ids, expected_sql)
            new_tab_ids = extract_open_query_tab_ids(page) - existing_query_ids
            response_ids = {
                str(item["query_id"])
                for item in response_summaries
                if item.get("query_id") and str(item["query_id"]) not in existing_query_ids
            }
            candidate_ids = set(response_ids) | set(new_tab_ids)
            if row and row.get("query_id"):
                candidate_ids.add(str(row["query_id"]))
            if len(candidate_ids) > 1:
                raise UsageError(
                    "SQL was submitted once, but acknowledgement evidence contained multiple new "
                    "query IDs. The operator did not choose or resubmit."
                )
            if len(candidate_ids) == 1:
                query_id = next(iter(candidate_ids))
                response_summary = next(
                    (
                        item
                        for item in response_summaries
                        if str(item.get("query_id") or "") == query_id
                        and item.get("submitted_sql_sha256") == expected_sql_sha256
                    ),
                    None,
                ) or next(
                    (
                        item
                        for item in response_summaries
                        if str(item.get("query_id") or "") == query_id
                    ),
                    None,
                ) or next(
                    (
                        item
                        for item in response_summaries
                        if item.get("query_id") is None
                        and item.get("submitted_sql_sha256") == expected_sql_sha256
                    ),
                    None,
                ) or {}
                if query_id in response_ids:
                    query_id_source = "submission_response"
                elif row and str(row.get("query_id") or "") == query_id:
                    query_id_source = "matching_history_row"
                else:
                    query_id_source = "single_new_query_tab"
                return SubmissionEvidence(
                    query_id=query_id,
                    query_id_source=query_id_source,
                    mechanism=mechanism,
                    request_path=response_summary.get("request_path"),
                    http_status=response_summary.get("http_status"),
                    submitted_sql_sha256=response_summary.get("submitted_sql_sha256"),
                    submitted_engine=response_summary.get("submitted_engine"),
                )
            error_details = extract_error_from_page(page)
            if _is_immediate_platform_error(error_details):
                raise ImmediatePlatformError(error_details)
            if time.monotonic() >= deadline:
                break
            page.wait_for_timeout(250)
    finally:
        try:
            page.remove_listener("response", on_response)
        except Exception:
            pass
    raise UsageError(
        "SQL was submitted once, but no unique new query ID was acknowledged. "
        "The operator did not retry to avoid duplicate backend jobs."
    )
