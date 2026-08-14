"""Account-isolated browser session for Tiangong2 task reads."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from _shared.auth import fill_login_if_present, is_login_page
from _shared.browser import launch_browser
from _shared.config import (
    TIANGONG2_BASE_API_BASE,
    TIANGONG2_CREDENTIAL_SECTION,
    TIANGONG2_TASK_RUNTIME_DIR,
    TIANGONG2_TASK_URL,
)
from _shared.env import read_env_section
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime


@dataclass(frozen=True)
class ScopedCredentials:
    username: str
    password: str = field(default="", repr=False)


@dataclass
class AuthenticatedSession:
    browser: Any
    context: Any
    identity: dict[str, Any]
    login_performed: bool

    def close(self) -> None:
        self.browser.close()


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def validate_runtime_state_path(state_path: Path) -> None:
    if not _within(state_path, TIANGONG2_TASK_RUNTIME_DIR):
        raise UsageError(
            "Tiangong2 task state must stay under the isolated runtime directory: "
            f"{TIANGONG2_TASK_RUNTIME_DIR}"
        )


def load_scoped_credentials(env_file: Path) -> ScopedCredentials:
    try:
        values = read_env_section(env_file, TIANGONG2_CREDENTIAL_SECTION)
    except ValueError as exc:
        raise UsageError(str(exc)) from exc
    username = values.get("BAIJIA_USERNAME", "").strip()
    password = values.get("BAIJIA_PASSWORD", "")
    if not username or not password:
        raise UsageError(
            "Missing Tiangong2 credentials in the exact usql_api.env section: "
            f"# {TIANGONG2_CREDENTIAL_SECTION}"
        )
    return ScopedCredentials(username=username, password=password)


def _normalize_username(value: str) -> str:
    normalized = value.strip().lower().split("@", 1)[0]
    if "\\" in normalized:
        normalized = normalized.rsplit("\\", 1)[-1]
    return normalized


def identity_matches_username(identity: dict[str, Any], username: str) -> bool:
    active = _normalize_username(str(identity.get("name") or ""))
    expected = _normalize_username(username)
    return bool(active and expected and active == expected)


def _new_context(browser: Any, state_path: Path, *, use_state: bool) -> Any:
    kwargs: dict[str, Any] = {
        "viewport": {"width": 1600, "height": 1000},
        "accept_downloads": False,
    }
    if use_state and state_path.is_file():
        kwargs["storage_state"] = str(state_path)
    return browser.new_context(**kwargs)


def _read_identity(context: Any) -> dict[str, Any]:
    response = context.request.get(f"{TIANGONG2_BASE_API_BASE}/cas/getAuth", timeout=45_000)
    if not response.ok:
        return {}
    try:
        body = response.json()
    except Exception:
        return {}
    if not isinstance(body, dict) or body.get("status") != "success":
        return {}
    return dict(body.get("data") or {})


def _authenticate_context(
    context: Any,
    *,
    state_path: Path,
    credentials: ScopedCredentials,
) -> tuple[dict[str, Any], bool]:
    page = context.new_page()
    page.goto(TIANGONG2_TASK_URL, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(1_500)
    login_performed = False
    if is_login_page(page):
        login_performed = fill_login_if_present(
            page,
            credentials.username,
            credentials.password,
            prompt_label="Tiangong2",
        )
        page.wait_for_load_state("domcontentloaded", timeout=45_000)
        page.wait_for_timeout(3_000)
    if is_login_page(page):
        page.close()
        raise UsageError("Tiangong2 login failed or requires manual verification.")
    context.storage_state(path=str(state_path))
    identity = _read_identity(context)
    page.close()
    return identity, login_performed


def open_authenticated_session(playwright: Any, args: Any) -> AuthenticatedSession:
    validate_runtime_state_path(args.state_path)
    ensure_runtime([TIANGONG2_TASK_RUNTIME_DIR, args.state_path.parent])
    credentials = load_scoped_credentials(args.env_file)
    browser = launch_browser(playwright, args.headed, args.browser_channel, args.executable_path)
    context = _new_context(browser, args.state_path, use_state=True)
    try:
        identity, login_performed = _authenticate_context(
            context,
            state_path=args.state_path,
            credentials=credentials,
        )
        if not identity_matches_username(identity, credentials.username):
            context.close()
            context = _new_context(browser, args.state_path, use_state=False)
            identity, fresh_login = _authenticate_context(
                context,
                state_path=args.state_path,
                credentials=credentials,
            )
            login_performed = login_performed or fresh_login
        if not identity_matches_username(identity, credentials.username):
            raise UsageError(
                "Active Tiangong2 identity does not match the scoped credential section; "
                "the isolated state was not accepted."
            )
        return AuthenticatedSession(
            browser=browser,
            context=context,
            identity=identity,
            login_performed=login_performed,
        )
    except Exception:
        browser.close()
        raise
