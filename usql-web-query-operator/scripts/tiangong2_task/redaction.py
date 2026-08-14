"""Secret-aware redaction for runtime-only task source snapshots."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


SECRET_NAME = r"(?:pass(?:word|wd)?|pwd|token|secret|api[_-]?key|access[_-]?key|private[_-]?key|app[_-]?secret|authorization|cookie)"
NAMED_ASSIGNMENT = re.compile(
    r"(?im)(?P<prefix>[\"']?(?P<name>[A-Za-z_][A-Za-z0-9_]*)[\"']?\s*[:=]\s*)"
    r"(?P<quote>[\"'])(?P<value>[^\"'\r\n]{6,})(?P=quote)"
)
UNQUOTED_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:export\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
    r"(?P<value>[A-Za-z0-9_./:+@-]{6,})\s*(?:#.*)?$"
)
URL_SECRET = re.compile(
    rf"(?i)(?P<prefix>[?&](?:{SECRET_NAME})=)(?P<value>[^&#\s\"']{{6,}})"
)
CLI_SECRET = re.compile(
    rf"(?i)(?P<prefix>--(?:{SECRET_NAME})(?:=|\s+))(?P<value>[^\s\"']{{6,}})"
)
FEISHU_WEBHOOK = re.compile(
    r"(?i)(?P<prefix>https://open\.feishu\.cn/open-apis/bot/v2/hook/)(?P<value>[A-Za-z0-9_-]{8,})"
)
CREDENTIAL_URL = re.compile(
    r"(?i)(?P<prefix>://[^:/@\s\"']+:)(?P<value>[^@/\s\"']{6,})(?=@)"
)
MYSQL_SHORT_PASSWORD = re.compile(
    r"(?i)(?P<prefix>(?:^|\s)-p)(?P<value>(?!\$\{|%)[A-Za-z0-9_./:+@-]{6,})"
)
PRIVATE_KEY_BODY = re.compile(
    r"(?s)(?P<prefix>-----BEGIN [A-Z ]*PRIVATE KEY-----\s*)"
    r"(?P<value>.+?)"
    r"(?=\s*-----END [A-Z ]*PRIVATE KEY-----)"
)
SECRET_KEY = re.compile(SECRET_NAME, re.I)


@dataclass(frozen=True)
class RedactionResult:
    text: str
    findings: tuple[dict[str, Any], ...]


def redact_text(text: str) -> RedactionResult:
    candidates: dict[str, set[str]] = {
        "named_secret_assignment": set(),
        "unquoted_secret_assignment": set(),
        "url_secret_parameter": set(),
        "cli_secret_argument": set(),
        "feishu_webhook": set(),
        "credential_url": set(),
        "mysql_short_password": set(),
        "private_key_body": set(),
    }
    candidates["named_secret_assignment"].update(
        match.group("value")
        for match in NAMED_ASSIGNMENT.finditer(text)
        if SECRET_KEY.search(match.group("name"))
    )
    candidates["unquoted_secret_assignment"].update(
        match.group("value")
        for match in UNQUOTED_ASSIGNMENT.finditer(text)
        if SECRET_KEY.search(match.group("name"))
        and match.group("value").lower() not in {"none", "null", "true", "false", "redacted"}
    )
    for rule, pattern in (
        ("url_secret_parameter", URL_SECRET),
        ("cli_secret_argument", CLI_SECRET),
        ("feishu_webhook", FEISHU_WEBHOOK),
        ("credential_url", CREDENTIAL_URL),
        ("mysql_short_password", MYSQL_SHORT_PASSWORD),
        ("private_key_body", PRIVATE_KEY_BODY),
    ):
        candidates[rule].update(match.group("value") for match in pattern.finditer(text))

    redacted = text
    for value in sorted({item for values in candidates.values() for item in values}, key=len, reverse=True):
        redacted = redacted.replace(value, "<redacted>")
    findings = tuple(
        {"rule": rule, "count": len(values)}
        for rule, values in candidates.items()
        if values
    )
    return RedactionResult(text=redacted, findings=findings)


def redact_structure(value: Any) -> tuple[Any, list[dict[str, Any]]]:
    findings: dict[str, int] = {}

    def visit(item: Any, key_hint: str = "") -> Any:
        if SECRET_KEY.search(key_hint):
            if item not in (None, "", [], {}):
                findings["secret_named_field"] = findings.get("secret_named_field", 0) + 1
            return "<redacted>"
        if isinstance(item, dict):
            return {str(key): visit(child, str(key)) for key, child in item.items()}
        if isinstance(item, list):
            return [visit(child, key_hint) for child in item]
        if isinstance(item, str):
            result = redact_text(item)
            for finding in result.findings:
                findings[finding["rule"]] = findings.get(finding["rule"], 0) + int(finding["count"])
            return result.text
        return item

    redacted = visit(value)
    return redacted, [
        {"rule": rule, "count": count}
        for rule, count in sorted(findings.items())
    ]


def structure_as_redacted_json(value: Any) -> RedactionResult:
    redacted, findings = redact_structure(value)
    return RedactionResult(
        text=json.dumps(redacted, ensure_ascii=False, indent=2, sort_keys=True),
        findings=tuple(findings),
    )
