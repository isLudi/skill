"""Local Codex runtime helpers for invoking the native Feishu CLI safely."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence


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
            return discovered
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
        raise RuntimeError(
            "lark-cli 失败: %s\n%s" % (_redacted_args(args), detail)
        )
    return result.stdout
