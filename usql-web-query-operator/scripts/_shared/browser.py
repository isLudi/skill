"""Playwright import and browser launch helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import UsageError


def import_playwright(include_timeout_error: bool = False) -> Any:
    try:
        from playwright.sync_api import sync_playwright
        if include_timeout_error:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    except ModuleNotFoundError as exc:
        raise UsageError(
            "Python Playwright is not installed. Install with:\n"
            "D:\\anaconda3\\python.exe -m pip install playwright\n"
            "D:\\anaconda3\\python.exe -m playwright install chromium"
        ) from exc
    if include_timeout_error:
        return sync_playwright, PlaywrightTimeoutError
    return sync_playwright


def launch_browser(playwright: Any, headed: bool, browser_channel: str | None, executable_path: str | None):
    launch_kwargs: dict[str, Any] = {"headless": not headed}
    if executable_path:
        launch_kwargs["executable_path"] = executable_path
    elif browser_channel:
        launch_kwargs["channel"] = browser_channel
    return playwright.chromium.launch(**launch_kwargs)


def launch_context(playwright: Any, state_path: Path, headed: bool, browser_channel: str | None, executable_path: str | None):
    browser = launch_browser(playwright, headed, browser_channel, executable_path)
    context_kwargs: dict[str, Any] = {
        "viewport": {"width": 1600, "height": 1000},
        "accept_downloads": True,
    }
    if state_path.exists():
        context_kwargs["storage_state"] = str(state_path)
    context = browser.new_context(**context_kwargs)
    return browser, context
