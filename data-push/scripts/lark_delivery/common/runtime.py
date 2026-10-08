"""Local Codex runtime helpers for invoking the native Feishu CLI safely."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence

# Hide every child console: scheduled push tasks run under pythonw.exe (no console
# of their own), so a console-subsystem child (lark-cli) would otherwise allocate a
# visible window. CREATE_NO_WINDOW only exists on Windows.
CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def ensure_console_streams() -> None:
    """Keep print()/logging safe under pythonw.exe, where sys.stdout is None."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


_SENSITIVE_FLAGS = {
    "--base-token",
    "--token",
    "--password",
    "--secret",
    "--authorization",
    "--content",
    "--data",
    "--text",
    "--markdown",
}


def _redacted_args(args: Sequence[object]) -> str:
    rendered = []
    redact_next = False
    for value in args:
        item = str(value)
        if redact_next:
            rendered.append("<redacted>")
            redact_next = False
            continue
        if item in _SENSITIVE_FLAGS:
            rendered.append(item)
            redact_next = True
            continue
        if any(item.startswith(flag + "=") for flag in _SENSITIVE_FLAGS):
            flag = item.split("=", 1)[0]
            rendered.append(flag + "=<redacted>")
            continue
        rendered.append(item)
    return " ".join(rendered)


def _existing_executable(path: Path) -> str | None:
    if path.is_file() and (os.name != "nt" or path.suffix.lower() not in {".cmd", ".bat"}):
        return str(path)
    return None


def resolve_lark_cli() -> str:
    """Resolve a native lark-cli executable without silently using cmd shims."""

    override = os.environ.get("LARK_CLI", "").strip()
    if override:
        expanded = Path(os.path.expandvars(override)).expanduser()
        direct = _existing_executable(expanded)
        if direct:
            return direct
        discovered = shutil.which(override)
        if discovered:
            direct = _existing_executable(Path(discovered))
            if direct:
                return direct
        raise FileNotFoundError("LARK_CLI 指向的 lark-cli 不存在或不可执行: %s" % override)

    candidates: list[Path] = []
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            npm_root = Path(appdata) / "npm"
            candidates.extend(
                [
                    npm_root / "node_modules" / "@larksuite" / "cli" / "bin" / "lark-cli.exe",
                    npm_root / "lark-cli.exe",
                ]
            )
        candidates.extend(
            [
                Path(sys.prefix) / "Scripts" / "lark-cli.exe",
                Path(sys.executable).resolve().parent / "lark-cli.exe",
            ]
        )
        # S4U 计划任务会话不加载用户配置文件，APPDATA/PATH 可能缺失；
        # 用 USERPROFILE 兜底定位本机 nodejs 安装目录中的 lark-cli。
        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            nodejs_dir = Path(user_profile) / "AppData" / "Local" / "Programs" / "nodejs"
            candidates.extend(
                [
                    nodejs_dir / "node_modules" / "@larksuite" / "cli" / "bin" / "lark-cli.exe",
                    nodejs_dir / "lark-cli.exe",
                ]
            )
        for candidate in candidates:
            resolved = _existing_executable(candidate)
            if resolved:
                return resolved
        discovered = shutil.which("lark-cli.exe")
        if discovered:
            return discovered
        raise FileNotFoundError(
            "未找到原生 lark-cli.exe；请安装本地 lark-cli，或设置 LARK_CLI 为已验证的 exe 路径"
        )

    discovered = shutil.which("lark-cli")
    if discovered:
        return discovered
    raise FileNotFoundError("未找到 lark-cli；请安装 lark-cli，或设置 LARK_CLI")


class LarkTransportError(RuntimeError):
    """lark-cli could not complete the call because the connection failed.

    Subclasses ``RuntimeError`` so every existing ``except RuntimeError`` keeps
    working. It exists so a caller can tell "the read did not happen" apart from
    "the read happened and disagreed" -- only the first may be retried.
    """


# Markers seen in production when the connection was reset rather than the call
# rejected. `wsarecv ... forcibly closed` is the Windows socket wording; the
# `"type": "network"` pair is lark-cli's own classification.
TRANSPORT_MARKERS = (
    '"subtype": "transport"',
    '"type": "network"',
    "wsarecv",
    "forcibly closed",
    "Connection reset",
    "Connection aborted",
    "i/o timeout",
)


def looks_like_transport(detail: str) -> bool:
    """Whether a lark-cli failure looks like a connection fault, not a rejection."""
    return any(marker in detail for marker in TRANSPORT_MARKERS)


def run_lark(
    args: Sequence[object],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
    timeout: int = 120,
) -> str:
    """Run lark-cli with UTF-8 and no shell interpolation."""

    command = [resolve_lark_cli(), *(str(item) for item in args)]
    child_env = dict(os.environ if env is None else env)
    child_env.setdefault("PYTHONIOENCODING", "utf-8")
    child_env.setdefault("PYTHONUTF8", "1")
    result = subprocess.run(
        command,
        cwd=os.fspath(cwd) if cwd is not None else None,
        env=child_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW,
    )
    if result.returncode != 0:
        detail = result.stderr[-1000:].strip()
        for index, item in enumerate(args[:-1]):
            if str(item) in _SENSITIVE_FLAGS:
                detail = detail.replace(str(args[index + 1]), "<redacted>")
        for item in args:
            rendered = str(item)
            for flag in _SENSITIVE_FLAGS:
                prefix = flag + "="
                if rendered.startswith(prefix):
                    detail = detail.replace(rendered[len(prefix):], "<redacted>")
        message = "lark-cli 失败: %s\n%s" % (_redacted_args(args), detail)
        # A connection-level failure is not a verdict about the data; callers that use a
        # read as a precondition may retry it (see common/retry.py). Anything else keeps
        # the plain RuntimeError so it is never retried.
        if looks_like_transport(detail):
            raise LarkTransportError(message)
        raise RuntimeError(message)
    return result.stdout
