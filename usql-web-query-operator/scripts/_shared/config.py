"""Shared configuration for local Playwright automation scripts."""

from __future__ import annotations

from pathlib import Path


QUERY_URL = "https://uanalysis.baijia.com/getDataSql"
DATA_CENTER_DATASET_URL = "https://uanalysis.baijia.com/data-center/data-set"
DATA_CENTER_API_BASE = "https://uanalysis.baijia.com/uanalysis-intelligence/data"
TEMPLATE_QUERY_MY_CREATE_URL = "https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate"
TEMPLATE_QUERY_API_BASE = "https://uanalysis.baijia.com/uanalysis-template"
DATAMAP_URL = "https://tiangong2.baijia.com/dataMap/dataMapNew"
DATAMAP_API_BASE = "https://tiangong2.baijia.com/md-admin/api/tableV2"
RUNTIME_DIR = Path.home() / ".codex" / "runtime" / "usql-web-query-operator"
DATAMAP_RUNTIME_DIR = Path.home() / ".codex" / "runtime" / "data-map"
DATA_CENTER_RUNTIME_DIR = RUNTIME_DIR / "data-center"
TEMPLATE_QUERY_RUNTIME_DIR = RUNTIME_DIR / "template-query"
DEFAULT_STATE = RUNTIME_DIR / "state.json"
DEFAULT_DATAMAP_STATE = DATAMAP_RUNTIME_DIR / "state.json"
DEFAULT_DATAMAP_CACHE = DATAMAP_RUNTIME_DIR / "datamap_table_catalog.json"
DEFAULT_ARTIFACTS = RUNTIME_DIR / "artifacts"
DEFAULT_BROWSER_CHANNEL = "msedge"
DEFAULT_ENV_FILE = Path("E:\\2000_work\\GAOTU\\20002_\u5e02\u573a\u987e\u95ee\u90e8\u770b\u677f\u7ef4\u62a4\u8868\u683c\\usql_api.env")
