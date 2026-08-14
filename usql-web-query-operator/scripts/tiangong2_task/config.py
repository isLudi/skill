"""Tiangong2 task-explorer constants and read-only endpoint registry."""

from __future__ import annotations

from dataclasses import dataclass


DATA_DEVELOPMENT_ROOT = "数据开发"


@dataclass(frozen=True)
class TaskContentSpec:
    task_type: int
    type_name: str
    endpoint: str
    payload_key: str
    source_keys: tuple[str, ...]
    source_kind: str
    extension: str
    use_menu_id: bool = False


TASK_CONTENT_SPECS: dict[int, TaskContentSpec] = {
    1: TaskContentSpec(1, "DATA_SYNC", "DS/getDSConfig", "id", (), "data_sync", ".json", True),
    3: TaskContentSpec(3, "SPARK", "dataDevelop/getSpark", "taskId", ("sql", "spark", "code"), "spark_sql", ".sql"),
    4: TaskContentSpec(4, "PYTHON", "dataDevelop/getPython", "taskId", ("python",), "python", ".py"),
    5: TaskContentSpec(5, "SHELL", "dataDevelop/getShell", "taskId", ("shell",), "shell", ".sh"),
    6: TaskContentSpec(6, "KYUUBI", "dataDevelop/getKyuubi", "taskId", ("sql",), "kyuubi_sql", ".sql"),
}


FORM_READ_ENDPOINTS = frozenset(
    {
        "menu/listMenus",
        "constant/taskTypeNameCodeMapping",
        "dataDevelop/getTask",
        "dataDevelop/getPython",
        "dataDevelop/getShell",
        "dataDevelop/getSpark",
        "dataDevelop/getKyuubi",
        "DS/getDSConfig",
        "ver/listVersions",
        "ver/getCode",
    }
)

JSON_READ_ENDPOINTS = frozenset(
    {
        "task/getScheduleConfig",
        "resource/task/list",
        "quality/list",
    }
)

BASE_READ_ENDPOINTS = frozenset(
    {
        "cas/getAuth",
        "menu/listProjects",
    }
)

FORBIDDEN_ENDPOINT_TERMS = frozenset(
    {
        "save",
        "new",
        "create",
        "update",
        "delete",
        "remove",
        "run",
        "start",
        "stop",
        "submit",
        "publish",
        "move",
        "rename",
        "clone",
        "import",
        "test",
        "execute",
        "rollback",
    }
)
