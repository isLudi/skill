"""Run summary model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class RunSummary:
    ok: bool
    status: str
    message: str
    artifacts_dir: str
    query_id: str | None = None
    result_preview: dict[str, Any] | None = None
    download_path: str | None = None
    error_details: dict[str, Any] | None = None
    requested_engine: str | None = None
    selected_engine_label: str | None = None
    selected_engine_key: str | None = None
    history_engine: str | None = None
    query_duration_text: str | None = None
    query_duration_seconds: float | None = None
    elapsed_seconds: float | None = None
    error_category: str | None = None
    error_category_label: str | None = None
    repair_guidance: str | None = None
    editor_evidence: dict[str, Any] | None = None
    submission_evidence: dict[str, Any] | None = None
    result_state: str | None = None
    result_evidence: dict[str, Any] | None = None
    ui_result_state: str | None = None
    query_plan_contract: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "status": self.status,
            "message": self.message,
            "artifacts_dir": self.artifacts_dir,
            "query_id": self.query_id,
            "result_preview": self.result_preview,
            "download_path": self.download_path,
            "error_details": self.error_details,
            "requested_engine": self.requested_engine,
            "selected_engine_label": self.selected_engine_label,
            "selected_engine_key": self.selected_engine_key,
            "history_engine": self.history_engine,
            "query_duration_text": self.query_duration_text,
            "query_duration_seconds": self.query_duration_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "error_category": self.error_category,
            "error_category_label": self.error_category_label,
            "repair_guidance": self.repair_guidance,
            "editor_evidence": self.editor_evidence,
            "submission_evidence": self.submission_evidence,
            "result_state": self.result_state,
            "result_evidence": self.result_evidence,
            "ui_result_state": self.ui_result_state,
        }
        if self.query_plan_contract is not None:
            payload["query_plan_contract"] = self.query_plan_contract
        if self.provenance is not None:
            payload["provenance"] = self.provenance
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
