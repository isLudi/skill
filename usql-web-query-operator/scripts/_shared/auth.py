"""Authentication helpers shared by SQL and dashboard automation."""

from __future__ import annotations

import argparse
import getpass
import os
from typing import Any

from .config import QUERY_URL
from .errors import UsageError


def fill_login_if_present(page: Any, username: str | None, password: str | None) -> bool:
    if "cas.baijia.com" not in page.url and "login" not in page.url.lower():
        return False

    if not username:
        username = os.environ.get("BAIJIA_USERNAME")
    if not password:
        password = os.environ.get("BAIJIA_PASSWORD")

    if not username:
        username = input("Baijia username: ").strip()
    if not password:
        password = getpass.getpass("Baijia password: ")

    inputs = page.locator("input")
    if inputs.count() < 2:
        raise UsageError("Login page detected, but username/password inputs were not found.")

    inputs.nth(0).fill(username)
    inputs.nth(1).fill(password)
    page.get_by_text("登录", exact=True).click()
    return True


def ensure_authenticated(page: Any, args: argparse.Namespace, context: Any | None = None) -> None:
    page.goto(QUERY_URL, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(1500)
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        fill_login_if_present(page, getattr(args, "username", None), getattr(args, "password", None))
        page.wait_for_load_state("domcontentloaded", timeout=45_000)
        page.wait_for_timeout(3000)
        if context is not None:
            context.storage_state(path=str(args.state_path))
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        raise UsageError("Login failed or requires manual verification.")
