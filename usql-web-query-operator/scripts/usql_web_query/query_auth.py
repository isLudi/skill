"""USQL-specific credential selection and live identity verification."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from _shared.env import read_env_section
from _shared.errors import UsageError

USQL_CREDENTIAL_SECTION = "USQL Web Query (Playwright) credentials"
AUTH_URL = "https://uanalysis.baijia.com/uanalysis-sql/api/cas/getAuth"


def query_credentials(path: Path | None, username: str | None = None,
                      password: str | None = None) -> tuple[str | None, str | None]:
    if username is not None or password is not None:
        if not username or not password:
            raise UsageError("Provide both explicit USQL credentials, or neither.")
        return username, password
    if path and path.is_file():
        try:
            values = read_env_section(path, USQL_CREDENTIAL_SECTION)
        except ValueError as exc:
            raise UsageError("The exact USQL Web Query credentials section is invalid.") from exc
        user, secret = values.get("BAIJIA_USERNAME"), values.get("BAIJIA_PASSWORD")
        if not user or not secret:
            raise UsageError("The exact USQL Web Query credentials section is missing or incomplete.")
        return user, secret
    return os.environ.get("BAIJIA_USERNAME"), os.environ.get("BAIJIA_PASSWORD")


def verify_query_identity(page: Any, expected_username: str | None) -> dict[str, Any]:
    response = page.context.request.get(AUTH_URL, timeout=15_000)
    if not response.ok:
        raise UsageError("USQL identity lookup failed; no query will be submitted.")
    try:
        payload = response.json()
    except Exception as exc:
        raise UsageError("USQL identity response is not JSON; refresh login.") from exc
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict) or not data.get("name"):
        raise UsageError("USQL did not return a logged-in identity; refresh login.")
    if payload.get("status") not in (None, "success") or payload.get("errorCode") not in (None, 0):
        raise UsageError("USQL rejected the identity check; refresh login.")
    actual = str(data["name"])
    if expected_username and actual.casefold() != expected_username.casefold():
        raise UsageError("The active USQL account does not match the requested credential section; refresh login.")
    return {"account": actual, "display_name": data.get("displayName"),
            "matches_requested_account": bool(expected_username), "verified": True}
