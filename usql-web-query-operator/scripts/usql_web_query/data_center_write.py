"""Production UI workflow for one reviewed Data Center SQL replacement."""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any

from _shared.config import DATA_CENTER_DATASET_URL
from _shared.errors import UsageError

from .data_center import DataCenterClient, select_dataset_for_replacement
from .data_center_replacement import (
    DataCenterSqlReplacementPlan,
    canonical_sql_text,
    sql_sha256,
)
from .data_center_ui import (
    click_optional_save_confirmation as _click_optional_save_confirmation,
    compact_api_response as _compact_api_response,
    elapsed_ms as _elapsed_ms,
    get_codemirror_sql as _get_codemirror_sql,
    matches_schedule_trigger as _matches_schedule_trigger,
    matches_sql_response as _matches_sql_response,
    poll_for_new_success,
    preview_summary as _preview_summary,
    require_success_response as _require_success_response,
    set_codemirror_sql as _set_codemirror_sql,
    visible_save_debug as _visible_save_debug,
    wait_for_editor_sql_hash as _wait_for_editor_sql_hash,
)


class DataCenterReplacementExecutor:
    """Execute replace -> preview -> save -> refresh -> success readback."""

    def __init__(
        self,
        *,
        page: Any,
        client: DataCenterClient,
        plan: DataCenterSqlReplacementPlan,
        replacement_sql: str,
        preview_timeout_ms: int,
        refresh_timeout_ms: int,
        poll_interval_ms: int,
    ) -> None:
        self.page = page
        self.client = client
        self.plan = plan
        self.replacement_sql = canonical_sql_text(replacement_sql)
        self.preview_timeout_ms = preview_timeout_ms
        self.refresh_timeout_ms = refresh_timeout_ms
        self.poll_interval_ms = poll_interval_ms
        self.progress: dict[str, Any] = {
            "phase": "not_started",
            "remote_sql_saved": False,
            "refresh_triggered": False,
            "fully_verified": False,
            "timings_ms": {},
        }

    def execute(self) -> dict[str, Any]:
        if self.plan.status != "ready":
            raise UsageError("Data Center replacement plan is not ready")
        if sql_sha256(self.replacement_sql) != self.plan.replacement_sql_sha256:
            raise UsageError("replacement SQL hash no longer matches the reviewed plan")

        started = time.perf_counter()
        self.progress["phase"] = "preflight"
        phase_started = time.perf_counter()
        discovered = self.client.discover_datasets()
        dataset = select_dataset_for_replacement(
            discovered,
            domain=self.plan.domain,
            dataset_id=str(self.plan.dataset.get("id") or ""),
        )
        self._verify_dataset_identity(dataset)
        current = self.client.fetch_dataset_sql(dataset)
        self._verify_current_detail(current)
        self.progress["timings_ms"]["preflight"] = _elapsed_ms(phase_started)

        self.progress["phase"] = "editor_replace"
        phase_started = time.perf_counter()
        # Enter through the detail page instead of deep-linking to the editor.
        # The application binds the selected dataset to the editor when the user
        # clicks Edit; a direct editor URL can render an unbound CodeMirror value.
        detail_url = f"{DATA_CENTER_DATASET_URL}?selectId={dataset.id}"
        self.page.goto(detail_url, wait_until="domcontentloaded", timeout=45_000)
        edit_button = self.page.locator("button").filter(
            has_text=re.compile(r"编\s*辑")
        ).first
        edit_button.wait_for(state="visible", timeout=30_000)
        edit_button.click()
        editor = self.page.locator(".CodeMirror").first
        editor.wait_for(state="visible", timeout=45_000)
        editor_before = _wait_for_editor_sql_hash(
            page=self.page,
            editor=editor,
            expected_sha256=self.plan.current_sql_sha256,
            timeout_ms=45_000,
        )
        editor_before_hash = sql_sha256(editor_before)
        if editor_before_hash != self.plan.current_sql_sha256:
            raise UsageError(
                "Data Center editor content drifted from the reviewed current SQL: "
                f"expected={self.plan.current_sql_sha256}, actual={editor_before_hash}"
            )
        _set_codemirror_sql(editor, self.replacement_sql)
        editor_after = _get_codemirror_sql(editor)
        if sql_sha256(editor_after) != self.plan.replacement_sql_sha256:
            raise UsageError("Data Center CodeMirror replacement readback hash mismatch")
        self.progress["editor_readback_sha256"] = sql_sha256(editor_after)
        self.progress["timings_ms"]["editor_replace"] = _elapsed_ms(phase_started)

        self.progress["phase"] = "preview"
        phase_started = time.perf_counter()
        with self.page.expect_response(
            lambda response: _matches_sql_response(
                response,
                endpoint="/data/set/execute",
                expected_sql_sha256=self.plan.replacement_sql_sha256,
            ),
            timeout=self.preview_timeout_ms,
        ) as preview_info:
            run_control = self.page.locator('[aria-label="play-circle"]').first
            run_control.wait_for(state="visible", timeout=15_000)
            run_control.click()
        preview_payload = _require_success_response(preview_info.value, phase="preview")
        self.progress["preview"] = _preview_summary(preview_payload)
        self.progress["timings_ms"]["preview"] = _elapsed_ms(phase_started)

        self.progress["phase"] = "save"
        phase_started = time.perf_counter()
        try:
            with self.page.expect_response(
                lambda response: _matches_sql_response(
                    response,
                    endpoint="/data/set/saveAndUpdate",
                    expected_sql_sha256=self.plan.replacement_sql_sha256,
                    expected_dataset_id=dataset.id,
                ),
                timeout=60_000,
            ) as save_info:
                save_button = self.page.locator("button[type=submit]").first
                save_button.wait_for(state="visible", timeout=15_000)
                save_button.click()
                self.progress["save_confirmation_clicked"] = (
                    _click_optional_save_confirmation(self.page)
                )
        except Exception:
            self.progress["save_debug"] = _visible_save_debug(self.page)
            raise
        save_payload = _require_success_response(save_info.value, phase="save")
        self.progress["save_response"] = _compact_api_response(save_payload)
        self.progress["remote_sql_saved"] = True
        self.progress["timings_ms"]["save"] = _elapsed_ms(phase_started)

        self.progress["phase"] = "post_save_readback"
        phase_started = time.perf_counter()
        saved = self.client.fetch_dataset_sql(dataset)
        saved_hash = sql_sha256(saved.execute_sql)
        self.progress["post_save_sql_sha256"] = saved_hash
        if saved_hash != self.plan.replacement_sql_sha256:
            raise UsageError("Data Center saved SQL readback hash mismatch")
        schedule = saved.detail_payload.get("schedule") or {}
        schedule_task_id = str(schedule.get("taskId") or "").strip()
        if not schedule_task_id:
            raise UsageError("saved Data Center dataset has no synchronization taskId")
        if schedule.get("taskStatus") is not True or schedule.get("isExpire") is True:
            raise UsageError("saved Data Center dataset synchronization task is disabled or expired")
        baseline_runs = self.client.fetch_schedule_runs(schedule_task_id)
        baseline_ids = {run.id for run in baseline_runs if run.id}
        self.progress["schedule_task_id"] = schedule_task_id
        self.progress["baseline_latest_run"] = (
            baseline_runs[0].to_json() if baseline_runs else None
        )
        self.progress["timings_ms"]["post_save_readback"] = _elapsed_ms(phase_started)

        self.progress["phase"] = "refresh_trigger"
        phase_started = time.perf_counter()
        view_url = f"{DATA_CENTER_DATASET_URL}?selectId={dataset.id}"
        self.page.goto(view_url, wait_until="domcontentloaded", timeout=45_000)
        sync_tab = self.page.get_by_text("同步状态", exact=True).first
        sync_tab.wait_for(state="visible", timeout=30_000)
        sync_tab.click()
        sync_now = self.page.locator("button").filter(
            has_text=re.compile(r"立即\s*执行")
        ).first
        sync_now.wait_for(state="visible", timeout=45_000)
        sync_now.click()
        confirm = self.page.locator("button").filter(
            has_text=re.compile(r"^\s*确\s*认\s*$")
        ).last
        confirm.wait_for(state="visible", timeout=10_000)
        triggered_at = datetime.now().astimezone().isoformat()
        with self.page.expect_response(
            lambda response: _matches_schedule_trigger(response, schedule_task_id),
            timeout=60_000,
        ) as trigger_info:
            confirm.click()
        trigger_payload = _require_success_response(trigger_info.value, phase="refresh_trigger")
        self.progress["refresh_triggered"] = True
        self.progress["refresh_triggered_at"] = triggered_at
        self.progress["refresh_response"] = _compact_api_response(trigger_payload)
        self.progress["timings_ms"]["refresh_trigger"] = _elapsed_ms(phase_started)

        self.progress["phase"] = "refresh_poll"
        phase_started = time.perf_counter()
        successful_run = self._poll_for_new_success(schedule_task_id, baseline_ids)
        self.progress["latest_run"] = successful_run.to_json()
        self.progress["timings_ms"]["refresh_poll"] = _elapsed_ms(phase_started)
        self.progress["phase"] = "complete"
        self.progress["fully_verified"] = True
        self.progress["total_elapsed_ms"] = _elapsed_ms(started)
        return dict(self.progress)

    def _verify_dataset_identity(self, dataset: Any) -> None:
        expected = self.plan.dataset
        checks = {
            "id": dataset.id,
            "name": dataset.name,
            "path": dataset.path_text,
            "fileValue": dataset.file_value,
            "subjectId": dataset.subject_id,
        }
        drift = [
            key
            for key, value in checks.items()
            if str(expected.get(key) or "") != str(value or "")
        ]
        if drift:
            raise UsageError("Data Center dataset identity drift: " + ", ".join(drift))

    def _verify_current_detail(self, current: Any) -> None:
        current_hash = sql_sha256(current.execute_sql)
        if current_hash != self.plan.current_sql_sha256:
            raise UsageError("Data Center current SQL drifted from the reviewed plan")
        if current.data_source_id != str(self.plan.dataset.get("dataSourceId") or ""):
            raise UsageError("Data Center dataSourceId drifted from the reviewed plan")
        schedule = current.detail_payload.get("schedule") or {}
        current_task_id = str(schedule.get("taskId") or "").strip()
        expected_task_id = str(self.plan.dataset.get("scheduleTaskId") or "").strip()
        if current_task_id != expected_task_id:
            raise UsageError("Data Center schedule taskId drifted from the reviewed plan")

    def _poll_for_new_success(self, schedule_task_id: str, baseline_ids: set[str]) -> Any:
        """Backward-compatible wrapper around the shared synchronization poller."""

        return poll_for_new_success(
            page=self.page,
            client=self.client,
            schedule_task_id=schedule_task_id,
            baseline_ids=baseline_ids,
            timeout_ms=self.refresh_timeout_ms,
            poll_interval_ms=self.poll_interval_ms,
        )
