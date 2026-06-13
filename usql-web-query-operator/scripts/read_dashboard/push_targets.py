"""Fixed single-dashboard wrappers for Qingcheng push captures."""

from __future__ import annotations

from dataclasses import dataclass


QINGCHENG_BROADCAST_FOLDER = "\u9752\u6a59\u64ad\u62a5"


@dataclass(frozen=True)
class DashboardCaptureTarget:
    dashboard_id: str
    dashboard_name: str
    folder_name: str = QINGCHENG_BROADCAST_FOLDER


QINGCHENG_PUSH_CAPTURE_TARGETS = {
    "douyin_person": DashboardCaptureTarget(
        dashboard_id="dashboard_3916483456733192193",
        dashboard_name="\u63a8\u9001--\u8f6c\u5316-\u6296\u97f3\u79c1\u4fe1",
    ),
    "douyin_team": DashboardCaptureTarget(
        dashboard_id="dashboard_3916517219847778305",
        dashboard_name="\u63a8\u9001--\u8f6c\u5316-\u6296\u97f3\u79c1\u4fe1_\u56e2",
    ),
    "private_team": DashboardCaptureTarget(
        dashboard_id="dashboard_3916532003721617409",
        dashboard_name="\u63a8\u9001--\u8f6c\u5316-\u79c1\u57df_\u56e2",
    ),
    "private_person": DashboardCaptureTarget(
        dashboard_id="dashboard_3916532959832903681",
        dashboard_name="\u63a8\u9001--\u8f6c\u5316-\u79c1\u57df_",
    ),
    "school_team": DashboardCaptureTarget(
        dashboard_id="dashboard_3916545163522686976",
        dashboard_name="\u63a8\u9001--\u8f6c\u5316-\u8fdb\u6821_\u56e2",
    ),
    "school_person": DashboardCaptureTarget(
        dashboard_id="dashboard_3916546265268498433",
        dashboard_name="\u63a8\u9001--\u8f6c\u5316-\u8fdb\u6821",
    ),
}


def build_capture_argv(target_key: str, extra_args: list[str]) -> list[str]:
    target = QINGCHENG_PUSH_CAPTURE_TARGETS[target_key]
    return [
        "capture-dashboard",
        "--dashboard-id",
        target.dashboard_id,
        "--dashboard-name",
        target.dashboard_name,
        "--folder",
        target.folder_name,
        *extra_args,
    ]
