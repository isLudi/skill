"""Error extraction, classification, and repair guidance."""

from __future__ import annotations

import re
from typing import Any

from _shared.errors import UsageError


class ImmediatePlatformError(UsageError):
    """A submission-time platform error shown before a query row is created."""

    def __init__(self, error_details: dict[str, Any]):
        self.error_details = error_details
        message = (
            error_details.get("detail")
            or error_details.get("raw_snippet")
            or error_details.get("title")
            or "Platform reported an error before creating a query history row."
        )
        super().__init__(message)

def _clean_error_text(text: str | None, limit: int = 4000) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\n{3,}", "\n\n", text.replace("\ufeff", "").replace("\r\n", "\n")).strip()
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned[:limit]

def _error_result(
    source: str,
    title: str | None = None,
    detail: str | None = None,
    raw_snippet: str = "",
    all_candidates: list[str] | None = None,
) -> dict[str, Any]:
    raw = _clean_error_text(raw_snippet or "\n".join(part for part in (title, detail) if part), limit=2000)
    return {
        "source": source,
        "title": _clean_error_text(title, limit=500) or None,
        "detail": _clean_error_text(detail, limit=2000) or None,
        "raw_snippet": raw,
        "all_candidates": all_candidates or [],
    }

def _looks_like_error_text(text: str | None) -> bool:
    if not text:
        return False
    return bool(re.search(
        r"error|exception|fail(?:ed)?|失败|错误|异常|权限|denied|cannot|can't|line \d+|"
        r"mismatched input|does not exist|not found|unknown|invalid|syntax|"
        r"column .* cannot|table .* not|ȱ��|Ȩ��|û��",
        text,
        flags=re.I,
    ))

def _choose_error_candidate(candidates: list[dict[str, str]]) -> dict[str, Any]:
    error_candidates = []
    for candidate in candidates:
        raw = _clean_error_text(candidate.get("raw") or "\n".join(
            part for part in (candidate.get("title"), candidate.get("detail")) if part
        ))
        if _looks_like_error_text(raw):
            error_candidates.append(candidate)

    if not error_candidates:
        return _error_result("none", raw_snippet="", all_candidates=[])

    priority = {
        "notification": 0,
        "message": 1,
        "alert": 2,
        "top_right": 3,
        "log_area": 4,
        "keyword": 5,
        "body_text": 6,
    }
    best = min(error_candidates, key=lambda item: priority.get(item.get("source", ""), 99))
    best_source = best.get("source", "")
    all_texts = []
    for candidate in error_candidates:
        if candidate.get("source") != best_source:
            continue
        raw = _clean_error_text(candidate.get("raw") or "\n".join(
            part for part in (candidate.get("title"), candidate.get("detail")) if part
        ))
        if not raw or raw in all_texts:
            continue
        content = re.sub(r"^\[[^\]]+\]\s*", "", raw)
        if len(content) <= 20 and not _looks_like_error_text(raw):
            continue
        if candidate.get("source") in {"top_right", "body_text", "keyword"} and not _looks_like_error_text(raw):
            continue
        all_texts.append(raw[:2000])
        if len(all_texts) >= 5:
            break

    raw = _clean_error_text(best.get("raw") or "\n".join(part for part in (best.get("title"), best.get("detail")) if part))
    title = _clean_error_text(best.get("title"))
    detail = _clean_error_text(best.get("detail"))
    if not title and raw:
        title = raw.splitlines()[0][:500]
    if not detail and raw:
        detail = raw
    return _error_result(best.get("source", "none"), title, detail, raw, all_texts)

def _has_error_details(error_details: dict[str, Any] | None) -> bool:
    if not error_details or error_details.get("source") == "none":
        return False
    source = str(error_details.get("source") or "")
    detail = str(error_details.get("detail") or "")
    raw = str(error_details.get("raw_snippet") or "")
    title = str(error_details.get("title") or "")
    if source in {"notification", "message", "alert"} and _looks_like_error_text(title):
        return bool(detail or raw or title)
    if detail:
        return _looks_like_error_text(detail)
    if raw:
        return _looks_like_error_text(raw)
    return _looks_like_error_text(title)

def _is_immediate_platform_error(error_details: dict[str, Any] | None) -> bool:
    if not _has_error_details(error_details):
        return False
    return error_details.get("source") in {"notification", "message", "alert"}

def _is_platform_failure_details(error_details: dict[str, Any] | None) -> bool:
    if not _has_error_details(error_details):
        return False
    return error_details.get("source") in {"notification", "message", "alert", "log_area"}

def classify_error_details(error_details: dict[str, Any] | None) -> tuple[str | None, str | None]:
    if not _has_error_details(error_details):
        return None, None
    source = str((error_details or {}).get("source") or "")
    if source in {"notification", "message", "alert"}:
        return "immediate_platform_error", "即时错误"
    if source == "log_area":
        return "query_log_error", "日志区错误"
    return "other_platform_error", "其他平台错误"

def build_repair_guidance(error_details: dict[str, Any] | None) -> str | None:
    category, _ = classify_error_details(error_details)
    if not category:
        return None
    detail = _clean_error_text(
        "\n".join(
            part for part in (
                (error_details or {}).get("detail"),
                (error_details or {}).get("raw_snippet"),
                (error_details or {}).get("title"),
            )
            if part
        ),
        limit=2000,
    ).lower()
    if category == "immediate_platform_error":
        if "范围限定" in detail or "department" in detail or "部门" in detail:
            return "这是提交前即时错误。先补齐必需的部门/业务线/架构范围限定；如果用户没有给出具体取值，保留占位符并回到 SQL 知识库确认允许字段后再重跑。"
        if "权限" in detail or "permission" in detail:
            return "这是提交前即时错误。不要把它当成空数据；先改用已确认可读的表，或缩小到已知有权限的范围，再决定是否需要用户确认表权限。"
        return "这是提交前即时错误。先按右上角提示修复 SQL，再重跑；不要对同一份未修改 SQL 继续重复点击执行。"
    if category == "query_log_error":
        if "validate_sql_error" in detail or "code=1017" in detail or "column" in detail or "字段" in detail:
            return "这是已创建任务后的日志区错误。优先按日志里的表名、字段名、行列号修复字段引用或 SQL 校验错误，再重新执行。"
        if "cannot cast" in detail or "cast" in detail or "type" in detail or "类型" in detail:
            return "这是已创建任务后的日志区错误。优先检查类型转换、聚合口径和 join 后字段类型是否匹配，再重新执行。"
        return "这是已创建任务后的日志区错误。打开并读取查询日志，按日志中的 VALIDATE_SQL_ERROR、行列号、表名、字段名或运行时报错修复 SQL 后再重跑。"
    return "平台返回了错误信息，但不属于已验证的两类主路径。先保留原始错误文本，再结合页面状态或 debug artifacts 排查。"

def _scan_error_candidates_in_document(scope: Any, scope_name: str) -> list[dict[str, str]]:
    """Return possible error text candidates from one document context."""
    try:
        return scope.evaluate(
            """scopeName => {
                function visible(el) {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 &&
                        style.visibility !== 'hidden' &&
                        style.display !== 'none' &&
                        style.opacity !== '0';
                }
                function text(el) {
                    if (!el) return '';
                    return (el.innerText || el.textContent || '').trim().replace(/\\n{3,}/g, '\\n\\n');
                }
                function add(result, source, el, title, detail) {
                    const raw = [title, detail].filter(Boolean).join('\\n').trim() || text(el);
                    if (!raw) return;
                    result.push({
                        source,
                        title: (title || '').trim(),
                        detail: (detail || '').trim(),
                        raw: `[${scopeName}] ${raw}`.slice(0, 4000),
                    });
                }

                const result = [];

                for (const el of document.querySelectorAll('.ant-notification-notice, .notification-notice, [class*=notification-notice]')) {
                    if (!visible(el)) continue;
                    const title = text(el.querySelector('.ant-notification-notice-message, [class*=notice-message]'));
                    const detail = text(el.querySelector('.ant-notification-notice-description, [class*=notice-description]'));
                    add(result, 'notification', el, title, detail);
                }

                for (const el of document.querySelectorAll('.ant-message-notice-content, [class*=message-notice-content]')) {
                    if (visible(el)) add(result, 'message', el, '', text(el));
                }

                for (const el of document.querySelectorAll('.ant-alert-error, [class*=alert-error]')) {
                    if (!visible(el)) continue;
                    const title = text(el.querySelector('.ant-alert-message, [class*=alert-message]'));
                    const detail = text(el.querySelector('.ant-alert-description, [class*=alert-description]'));
                    add(result, 'alert', el, title, detail);
                }

                for (const el of Array.from(document.querySelectorAll('body *'))) {
                    if (!visible(el)) continue;
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    const nearRight = window.innerWidth - rect.right < 160 || parseFloat(style.right || '9999') < 160;
                    const nearTop = rect.top < 220 || parseFloat(style.top || '9999') < 220;
                    if ((style.position === 'fixed' || style.position === 'absolute') && nearRight && nearTop) {
                        const raw = text(el);
                        if (raw && raw.length < 2000) add(result, 'top_right', el, '', raw);
                    }
                }

                const logSelectors = [
                    '.antd-pro-src-components-history-infinite-scroll-log-index-logContainer',
                    '[class*=logContainer]',
                    '[class*=log-container]',
                    '.logContainer',
                    'pre',
                    'code',
                    '.ant-table-expanded-row',
                    '.ant-collapse-content',
                    '.ant-modal',
                    '.ant-drawer'
                ];
                for (const selector of logSelectors) {
                    for (const el of document.querySelectorAll(selector)) {
                        if (!visible(el)) continue;
                        const raw = text(el);
                        if (/error|exception|fail(?:ed)?|失败|错误|异常|cannot|denied|line \\d+/i.test(raw)) {
                            add(result, 'log_area', el, '', raw);
                        }
                    }
                }

                const keywordSelector = [
                    '[role=alert]',
                    '[role=dialog]',
                    '[role=status]',
                    '[class*=error]',
                    '[class*=Error]',
                    '[class*=fail]',
                    '[class*=Fail]',
                    '[class*=notice]',
                    '[class*=message]',
                    '[class*=toast]'
                ].join(',');
                for (const el of document.querySelectorAll(keywordSelector)) {
                    if (!visible(el)) continue;
                    const raw = text(el);
                    if (raw && raw.length < 2500 && /error|fail(?:ed)?|失败|错误|异常|cannot|denied|line \\d+/i.test(raw)) {
                        add(result, 'keyword', el, '', raw);
                    }
                }

                const bodyText = text(document.body);
                if (bodyText && /error|exception|fail(?:ed)?|失败|错误|异常|cannot|denied/i.test(bodyText)) {
                    const lines = bodyText.split('\\n').map(s => s.trim()).filter(Boolean);
                    const hits = lines.filter(line => /error|exception|fail(?:ed)?|失败|错误|异常|cannot|denied|line \\d+/i.test(line));
                    if (hits.length) {
                        result.push({
                            source: 'body_text',
                            title: hits[0].slice(0, 500),
                            detail: hits.slice(0, 20).join('\\n'),
                            raw: `[${scopeName}] ${hits.slice(0, 30).join('\\n')}`.slice(0, 4000),
                        });
                    }
                }
                return result;
            }""",
            scope_name,
        )
    except Exception:
        return []

def extract_error_from_page(page: Any) -> dict[str, Any]:
    """Scan the page for error details after a query failure.

    The function is intentionally failure-safe: selector drift or cross-frame
    issues must not mask the original SQL failure.
    """
    candidates: list[dict[str, str]] = []
    try:
        candidates.extend(_scan_error_candidates_in_document(page, "outer"))
    except Exception:
        pass

    for frame_obj in getattr(page, "frames", []):
        try:
            if frame_obj == page.main_frame:
                continue
            candidates.extend(_scan_error_candidates_in_document(frame_obj, frame_obj.url or "iframe"))
        except Exception:
            continue

    return _choose_error_candidate(candidates)
