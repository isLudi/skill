"""Account-scoped, persistent OES browser sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from _shared.browser import launch_browser
from _shared.config import OES_ACHIEVEMENT_URL, OES_CREDENTIAL_SECTION, OES_RUNTIME_DIR
from _shared.env import read_env_section
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime


@dataclass(frozen=True)
class OesCredentials:
    username: str
    password: str = field(default="", repr=False)


@dataclass
class OesSession:
    browser: Any
    context: Any
    page: Any
    login_performed: bool

    def close(self) -> None:
        self.browser.close()


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def validate_state_path(path: Path) -> None:
    if not _within(path, OES_RUNTIME_DIR):
        raise UsageError(f"OES state must stay under its isolated runtime directory: {OES_RUNTIME_DIR}")


def state_expiry_summary(path: Path) -> list[dict[str, Any]]:
    """Return non-sensitive declared expirations without exposing cookie values."""
    if not path.is_file():
        return []
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"OES state file is unreadable: {path}") from exc
    now = datetime.now(timezone.utc).timestamp()
    result: list[dict[str, Any]] = []
    for cookie in state.get("cookies", []):
        domain = str(cookie.get("domain") or "")
        if "baijia.com" not in domain and "gaotu100.com" not in domain:
            continue
        expires = float(cookie.get("expires") or -1)
        result.append(
            {
                "domain": domain,
                "name": str(cookie.get("name") or ""),
                "session_cookie": expires <= 0,
                "expires_at": datetime.fromtimestamp(expires, timezone.utc).isoformat() if expires > 0 else None,
                "remaining_hours": round((expires - now) / 3600, 2) if expires > 0 else None,
            }
        )
    return result


def load_credentials(env_file: Path) -> OesCredentials:
    try:
        values = read_env_section(env_file, OES_CREDENTIAL_SECTION)
    except ValueError as exc:
        raise UsageError(str(exc)) from exc
    username = values.get("BAIJIA_USERNAME", "").strip()
    password = values.get("BAIJIA_PASSWORD", "")
    if not username or not password:
        raise UsageError(
            "Missing OES credentials in the exact usql_api.env section: "
            f"# {OES_CREDENTIAL_SECTION}"
        )
    return OesCredentials(username=username, password=password)


def is_login_page(page: Any) -> bool:
    return "cas.baijia.com" in page.url or "/cas/login" in page.url


def _new_context(browser: Any, state_path: Path, *, use_state: bool) -> Any:
    kwargs: dict[str, Any] = {
        "viewport": {"width": 1600, "height": 1000},
        "accept_downloads": True,
    }
    if use_state and state_path.is_file():
        kwargs["storage_state"] = str(state_path)
    return browser.new_context(**kwargs)


def _fill_login(page: Any, credentials: OesCredentials) -> None:
    username = page.locator("#username")
    password = page.locator("#password")
    if username.count() != 1 or password.count() != 1:
        raise UsageError("OES CAS login fields changed; #username and #password were not found.")
    username.fill(credentials.username)
    password.fill(credentials.password)


def open_session(playwright: Any, args: Any, *, allow_interactive_login: bool = False) -> OesSession:
    validate_state_path(args.state_path)
    ensure_runtime([OES_RUNTIME_DIR, args.state_path.parent])
    credentials = load_credentials(args.env_file)
    browser = launch_browser(playwright, args.headed, args.browser_channel, args.executable_path)
    context = _new_context(browser, args.state_path, use_state=True)
    page = context.new_page()
    login_performed = False
    try:
        page.goto(OES_ACHIEVEMENT_URL, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(1_500)
        if is_login_page(page):
            context.close()
            context = _new_context(browser, args.state_path, use_state=False)
            page = context.new_page()
            page.goto(OES_ACHIEVEMENT_URL, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(1_000)
            _fill_login(page, credentials)
            if not allow_interactive_login or not args.headed:
                raise UsageError(
                    "OES login state is missing or expired and CAS requires a visual verification code. "
                    "Run oes_achievement.py login --headed, complete the verification once, then rerun silently."
                )
            try:
                page.wait_for_url(lambda url: "cas.baijia.com" not in url, timeout=args.login_timeout_ms)
            except Exception as exc:
                raise UsageError("OES interactive login did not complete before the timeout.") from exc
            page.wait_for_load_state("domcontentloaded", timeout=45_000)
            page.wait_for_timeout(2_000)
            login_performed = True
        if is_login_page(page):
            raise UsageError("OES login failed or still requires verification.")
        context.storage_state(path=str(args.state_path))
        return OesSession(browser, context, page, login_performed)
    except Exception:
        browser.close()
        raise
