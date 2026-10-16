"""Login command implementation."""

from __future__ import annotations

import argparse

from _shared.browser import import_playwright, launch_browser
from _shared.config import QUERY_URL
from _shared.auth import fill_login_if_present
from _shared.fs_utils import ensure_runtime
from usql_web_query.query_auth import query_credentials, verify_query_identity


def cmd_login(args: argparse.Namespace) -> int:
    username, password = query_credentials(args.env_file, args.username, args.password)
    sync_playwright, _ = import_playwright(include_timeout_error=True)
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    with sync_playwright() as playwright:
        browser = launch_browser(playwright, args.headed, args.browser_channel, args.executable_path)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()
        page.goto(QUERY_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        if args.manual:
            print("Complete login in the opened browser, then press Enter here.")
            input()
        else:
            fill_login_if_present(page, username, password)
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            page.wait_for_timeout(3000)
        identity = verify_query_identity(page, username)
        context.storage_state(path=str(args.state_path))
        print(f"Verified USQL account: {identity['account']}")
        print(f"Saved login state: {args.state_path}")
        browser.close()
    return 0
