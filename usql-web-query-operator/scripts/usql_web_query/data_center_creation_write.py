"""Production UI workflow for one reviewed Data Center dataset creation."""

from __future__ import annotations

import time
from datetime import date
from typing import Any

from _shared.errors import UsageError

from .data_center import (
    DataCenterClient,
    DataCenterDataset,
    select_folder_for_creation,
)
from .data_center_creation import DataCenterDatasetCreationPlan
from .data_center_replacement import canonical_sql_text, sql_sha256
from .data_center_ui import (
    click_optional_save_confirmation,
    compact_api_response,
    configure_hourly_schedule,
    elapsed_ms,
    get_codemirror_sql,
    matches_sql_response,
    open_creation_draft,
    poll_for_new_success,
    preview_summary,
    require_success_response,
    select_data_source,
    set_codemirror_sql,
    set_dataset_title,
    trigger_synchronization,
    visible_save_debug,
)


class DataCenterCreationExecutor:
    """Execute create draft -> preview -> schedule -> save -> refresh -> success."""

    def __init__(
        self,
        *,
        page: Any,
        client: DataCenterClient,
        plan: DataCenterDatasetCreationPlan,
        sql_text: str,
        preview_timeout_ms: int,
        refresh_timeout_ms: int,
        poll_interval_ms: int,
    ) -> None:
        self.page = page
        self.client = client
        self.plan = plan
        self.sql_text = canonical_sql_text(sql_text)
        self.preview_timeout_ms = preview_timeout_ms
        self.refresh_timeout_ms = refresh_timeout_ms
        self.poll_interval_ms = poll_interval_ms
        self.progress: dict[str, Any] = {
            "phase": "not_started",
            "remote_dataset_created": False,
            "refresh_triggered": False,
            "fully_verified": False,
            "timings_ms": {},
        }

    def execute(self) -> dict[str, Any]:
        if self.plan.status != "ready":
            raise UsageError("Data Center creation plan is not ready")
        if sql_sha256(self.sql_text) != self.plan.sql_sha256:
            raise UsageError("creation SQL hash no longer matches the reviewed plan")
        if date.fromisoformat(str(self.plan.schedule["dateRange"][0])) < date.today():
            raise UsageError("Data Center creation plan schedule is stale; create a new plan")

        started = time.perf_counter()
        self.progress["phase"] = "preflight"
        phase_started = time.perf_counter()
        folder = select_folder_for_creation(
            self.client.discover_folders(),
            domain=self.plan.domain,
            folder_id=str(self.plan.folder.get("id") or ""),
        )
        self._verify_folder_identity(folder)
        datasets = self.client.discover_datasets()
        self._require_name_available(datasets, folder.id)
        baseline_ids = set(self.plan.baseline_dataset_ids)
        self.progress["folder_child_drift"] = {
            "added_ids": sorted(
                item.id
                for item in datasets
                if item.parent_id == folder.id and item.id not in baseline_ids
            ),
            "removed_ids": sorted(
                baseline_ids
                - {item.id for item in datasets if item.parent_id == folder.id}
            ),
        }
        self.progress["timings_ms"]["preflight"] = elapsed_ms(phase_started)

        self.progress["phase"] = "draft_fill"
        phase_started = time.perf_counter()
        open_creation_draft(self.page, folder)
        set_dataset_title(self.page, self.plan.dataset_name)
        select_data_source(self.page, str(self.plan.data_source["name"]))
        editor = self.page.locator(".CodeMirror").first
        editor.wait_for(state="visible", timeout=30_000)
        set_codemirror_sql(editor, self.sql_text)
        if sql_sha256(get_codemirror_sql(editor)) != self.plan.sql_sha256:
            raise UsageError("Data Center creation editor SQL readback hash mismatch")
        self.progress["editor_readback_sha256"] = self.plan.sql_sha256
        self.progress["timings_ms"]["draft_fill"] = elapsed_ms(phase_started)

        self.progress["phase"] = "preview"
        phase_started = time.perf_counter()
        with self.page.expect_response(
            lambda response: matches_sql_response(
                response,
                endpoint="/data/set/execute",
                expected_sql_sha256=self.plan.sql_sha256,
                expected_data_source_id=str(self.plan.data_source["id"]),
            ),
            timeout=self.preview_timeout_ms,
        ) as preview_info:
            run_control = self.page.locator('[aria-label="play-circle"]').first
            run_control.wait_for(state="visible", timeout=15_000)
            run_control.click()
        preview_payload = require_success_response(preview_info.value, phase="preview")
        preview = preview_summary(preview_payload)
        if int(preview.get("metaCount") or 0) < 1:
            raise UsageError("Data Center creation preview returned no field metadata")
        self.progress["preview"] = preview
        self.progress["timings_ms"]["preview"] = elapsed_ms(phase_started)

        self.progress["phase"] = "schedule"
        phase_started = time.perf_counter()
        schedule = self.plan.schedule
        configure_hourly_schedule(
            self.page,
            start_date=date.fromisoformat(str(schedule["dateRange"][0])),
            end_date=date.fromisoformat(str(schedule["dateRange"][1])),
            hours=tuple(
                str(value)
                for value in schedule["synchronizationFrequency"]["timeHourMinuteList"]
            ),
        )
        self.progress["timings_ms"]["schedule"] = elapsed_ms(phase_started)

        self.progress["phase"] = "save"
        phase_started = time.perf_counter()
        try:
            with self.page.expect_response(
                lambda response: matches_sql_response(
                    response,
                    endpoint="/data/set/saveAndUpdate",
                    expected_sql_sha256=self.plan.sql_sha256,
                    require_null_dataset_id=True,
                    expected_parent_id=folder.id,
                    expected_data_source_id=str(self.plan.data_source["id"]),
                ),
                timeout=60_000,
            ) as save_info:
                save_button = self.page.locator("button[type=submit]").first
                save_button.wait_for(state="visible", timeout=15_000)
                save_button.click()
                self.progress["save_confirmation_clicked"] = (
                    click_optional_save_confirmation(self.page)
                )
        except Exception:
            self.progress["save_debug"] = visible_save_debug(self.page)
            raise
        save_payload = require_success_response(save_info.value, phase="save")
        self.progress["save_response"] = compact_api_response(save_payload)
        saved_response_id = str(save_payload.get("data") or "").strip()
        if not saved_response_id.startswith("menu_set_"):
            raise UsageError("Data Center creation save response did not return a dataset identity")
        self.progress["remote_dataset_created"] = True
        self.progress["timings_ms"]["save"] = elapsed_ms(phase_started)

        self.progress["phase"] = "post_save_readback"
        phase_started = time.perf_counter()
        created = self._wait_for_created_dataset(folder.id, baseline_ids)
        if created.id != saved_response_id:
            raise UsageError("Data Center creation save response and menu identity mismatch")
        saved = self.client.fetch_dataset_sql(created)
        self._verify_saved_detail(saved)
        schedule_detail = saved.detail_payload.get("schedule") or {}
        schedule_task_id = str(schedule_detail.get("taskId") or "").strip()
        baseline_runs = self.client.fetch_schedule_runs(schedule_task_id)
        baseline_run_ids = {run.id for run in baseline_runs if run.id}
        self.progress["created_dataset"] = created.to_json()
        self.progress["schedule_task_id"] = schedule_task_id
        self.progress["baseline_latest_run"] = (
            baseline_runs[0].to_json() if baseline_runs else None
        )
        self.progress["timings_ms"]["post_save_readback"] = elapsed_ms(phase_started)

        self.progress["phase"] = "refresh_trigger"
        phase_started = time.perf_counter()
        triggered_at, trigger_response = trigger_synchronization(
            page=self.page,
            dataset_id=created.id,
            schedule_task_id=schedule_task_id,
        )
        self.progress["refresh_triggered"] = True
        self.progress["refresh_triggered_at"] = triggered_at
        self.progress["refresh_response"] = trigger_response
        self.progress["timings_ms"]["refresh_trigger"] = elapsed_ms(phase_started)

        self.progress["phase"] = "refresh_poll"
        phase_started = time.perf_counter()
        successful_run = poll_for_new_success(
            page=self.page,
            client=self.client,
            schedule_task_id=schedule_task_id,
            baseline_ids=baseline_run_ids,
            timeout_ms=self.refresh_timeout_ms,
            poll_interval_ms=self.poll_interval_ms,
        )
        self.progress["latest_run"] = successful_run.to_json()
        self.progress["timings_ms"]["refresh_poll"] = elapsed_ms(phase_started)
        self.progress["phase"] = "complete"
        self.progress["fully_verified"] = True
        self.progress["total_elapsed_ms"] = elapsed_ms(started)
        return dict(self.progress)

    def _verify_folder_identity(self, folder: Any) -> None:
        expected = self.plan.folder
        checks = {
            "id": folder.id,
            "name": folder.name,
            "path": folder.path_text,
            "fileValue": folder.file_value,
            "subjectId": folder.subject_id,
        }
        drift = [
            key
            for key, value in checks.items()
            if str(expected.get(key) or "") != str(value or "")
        ]
        if drift:
            raise UsageError("Data Center creation folder identity drift: " + ", ".join(drift))

    def _require_name_available(
        self,
        datasets: list[DataCenterDataset],
        folder_id: str,
    ) -> None:
        matches = [
            item
            for item in datasets
            if item.parent_id == folder_id and item.name == self.plan.dataset_name
        ]
        if matches:
            raise UsageError(
                "Data Center target dataset name is no longer available: "
                + ", ".join(item.id for item in matches)
            )

    def _wait_for_created_dataset(
        self,
        folder_id: str,
        baseline_ids: set[str],
    ) -> DataCenterDataset:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            matches = [
                item
                for item in self.client.discover_datasets()
                if item.parent_id == folder_id
                and item.name == self.plan.dataset_name
                and item.id not in baseline_ids
            ]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise UsageError("Data Center creation produced an ambiguous duplicate name")
            self.page.wait_for_timeout(1000)
        raise UsageError("Data Center saved dataset did not appear in menu readback")

    def _verify_saved_detail(self, saved: Any) -> None:
        if sql_sha256(saved.execute_sql) != self.plan.sql_sha256:
            raise UsageError("Data Center created SQL readback hash mismatch")
        if saved.data_source_id != str(self.plan.data_source["id"]):
            raise UsageError("Data Center created dataSourceId readback mismatch")
        schedule = saved.detail_payload.get("schedule") or {}
        if schedule.get("taskStatus") is not True or schedule.get("isExpire") is True:
            raise UsageError("Data Center created synchronization task is disabled or expired")
        if not str(schedule.get("taskId") or "").strip():
            raise UsageError("Data Center created synchronization taskId is empty")
        expected = self.plan.schedule
        if list(schedule.get("dateRange") or []) != list(expected["dateRange"]):
            raise UsageError("Data Center created schedule date range readback mismatch")
        frequency = schedule.get("synchronizationFrequency") or {}
        expected_frequency = expected["synchronizationFrequency"]
        if int(frequency.get("timeUnit") or 0) != int(expected_frequency["timeUnit"]):
            raise UsageError("Data Center created schedule frequency readback mismatch")
        if list(frequency.get("timeHourMinuteList") or []) != list(
            expected_frequency["timeHourMinuteList"]
        ):
            raise UsageError("Data Center created schedule hours readback mismatch")
