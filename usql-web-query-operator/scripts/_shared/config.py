"""Shared configuration for local Playwright automation scripts."""

from __future__ import annotations

from pathlib import Path


QUERY_URL = "https://uanalysis.baijia.com/getDataSql"
RUNTIME_DIR = Path.home() / ".codex" / "runtime" / "usql-web-query-operator"
DEFAULT_STATE = RUNTIME_DIR / "state.json"
DEFAULT_ARTIFACTS = RUNTIME_DIR / "artifacts"
DEFAULT_BROWSER_CHANNEL = "msedge"
DEFAULT_ENV_FILE = Path("E:\\2000_work\\GAOTU\\20002_\u5e02\u573a\u987e\u95ee\u90e8\u770b\u677f\u7ef4\u62a4\u8868\u683c\\usql_api.env")
