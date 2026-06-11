"""Doctor command implementation."""

from __future__ import annotations

import argparse
from pathlib import Path

from _shared.browser import import_playwright
from _shared.config import DEFAULT_BROWSER_CHANNEL, DEFAULT_STATE, RUNTIME_DIR
from _shared.errors import UsageError


def cmd_doctor(_: argparse.Namespace) -> int:
    try:
        import_playwright()
    except UsageError as exc:
        print(str(exc))
        return 1
    print("Python Playwright is available.")
    print(f"Runtime dir: {RUNTIME_DIR}")
    print(f"Default state: {DEFAULT_STATE}")
    edge_path = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    chrome_path = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    print(f"Edge available: {edge_path.exists()} ({edge_path})")
    print(f"Chrome available: {chrome_path.exists()} ({chrome_path})")
    print(f"Default browser channel: {DEFAULT_BROWSER_CHANNEL}")
    return 0
