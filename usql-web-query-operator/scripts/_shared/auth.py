"""Authentication helpers shared by SQL and dashboard automation."""

from __future__ import annotations

import argparse
import getpass
import os
from typing import Any

from .config import QUERY_URL
from .errors import UsageError


def is_login_page(page: Any) -> bool:
    return "cas.baijia.com" in page.url or "login" in page.url.lower()


def fill_login_if_present(
    page: Any,
    username: str | None,
    password: str | None,
    *,
    username_env: str = "BAIJIA_USERNAME",
    password_env: str = "BAIJIA_PASSWORD",
    prompt_label: str = "Baijia",
) -> bool:
    if not is_login_page(page):
        return False

    if not username:
        username = os.environ.get(username_env)
    if not password:
        password = os.environ.get(password_env)

    if not username:
        username = input(f"{prompt_label} username: ").strip()
    if not password:
        password = getpass.getpass(f"{prompt_label} password: ")

    inputs = page.locator("input")
    if inputs.count() < 2:
        raise UsageError("Login page detected, but username/password inputs were not found.")

    inputs.nth(0).fill(username)
    inputs.nth(1).fill(password)
    page.get_by_text("登录", exact=True).click()
    return True


def ensure_authenticated(
    page: Any,
    args: argparse.Namespace,
    context: Any | None = None,
    *,
    target_url: str = QUERY_URL,
    username_env: str = "BAIJIA_USERNAME",
    password_env: str = "BAIJIA_PASSWORD",
    prompt_label: str = "Baijia",
) -> None:
    page.goto(target_url, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(1500)
    if is_login_page(page):
        fill_login_if_present(
            page,
            getattr(args, "username", None),
            getattr(args, "password", None),
            username_env=username_env,
            password_env=password_env,
            prompt_label=prompt_label,
        )
        page.wait_for_load_state("domcontentloaded", timeout=45_000)
        page.wait_for_timeout(3000)
        if context is not None:
            context.storage_state(path=str(args.state_path))
    if is_login_page(page):
        raise UsageError("Login failed or requires manual verification.")
