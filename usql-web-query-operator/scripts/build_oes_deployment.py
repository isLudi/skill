"""Build a portable Windows OES/Base bundle containing code, never credentials."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit
import zipfile

from prepare_oes_runtime import PYTHON_SHA256, PYTHON_VERSION, WHEELS


def build(destination: Path, executable: Path, runtime_payload: Path, profile_template: Path | None = None) -> dict:
    skill = Path(__file__).resolve().parents[1]
    skills = skill.parent
    destination = destination.expanduser().resolve()
    if destination == skills or skills in destination.parents:
        raise ValueError("Deployment bundles must stay outside the skills repository.")
    if destination.exists():
        raise ValueError("Use a new bundle directory; existing contents are preserved.")
    archive = destination.with_suffix(".zip")
    if archive.exists():
        raise ValueError("Archive already exists; no overwrite was performed.")
    payload = json.loads((runtime_payload / "runtime-payload.json").read_text(encoding="utf-8"))
    expected = {f"python-{PYTHON_VERSION}-embed-amd64.zip", *("wheels/" + wheel[2] for wheel in WHEELS)}
    if (not isinstance(payload, dict) or set(payload) != {"python_version", "architecture", "files"}
            or payload["python_version"] != PYTHON_VERSION or payload["architecture"] != "AMD64"
            or not isinstance(payload["files"], list)
            or any(not isinstance(item, dict) or set(item) != {"path", "sha256", "source"} for item in payload["files"])
            or {item["path"] for item in payload["files"]} != expected or len(payload["files"]) != len(expected)):
        raise ValueError("Use the complete pinned official Windows x64 runtime payload.")
    for entry in payload["files"]:
        path = entry["path"]
        source = urlsplit(entry["source"])
        if path.startswith("wheels/"):
            source_ok = (source.scheme == "https" and source.hostname == "files.pythonhosted.org"
                         and source.username is None and source.password is None and not source.query
                         and not source.fragment and source.path.endswith("/" + Path(path).name))
        else:
            source_ok = entry["source"] == f"https://www.python.org/ftp/python/{PYTHON_VERSION}/{path}"
        if not source_ok or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise ValueError("Runtime payload manifest contains an invalid source or checksum.")
        digest = hashlib.sha256((runtime_payload / path).read_bytes()).hexdigest()
        if digest != entry["sha256"] or (entry["path"].endswith(".zip") and digest != PYTHON_SHA256):
            raise ValueError("Runtime payload checksum mismatch.")
    profile_template = profile_template or skill / "assets/oes_installer_profile.json"
    profile = json.loads(profile_template.read_text(encoding="utf-8"))
    permitted = set(json.loads((skill / "assets/oes_installer_profile.json").read_text(encoding="utf-8")))
    if set(profile) != permitted or profile["lark_profile"] or any(profile[key] != value for key, value in {
            "credentials_file": "private/usql_api.env", "runtime_dir": "data/runtime", "output_dir": "data/runs",
            "lark_cli": "tools/lark-cli.exe"}.items()):
        raise ValueError("Deployment profile must contain only public coordinates and approved local paths.")
    for key, pattern in {"base_token": r"[A-Za-z0-9]+", "table_id": r"tbl[A-Za-z0-9]+",
                         "config_table_id": r"tbl[A-Za-z0-9]+", "config_record_id": r"rec[A-Za-z0-9]+",
                         "lark_app_id": r"(?:cli_[A-Za-z0-9]+)?"}.items():
        if not isinstance(profile[key], str) or not re.fullmatch(pattern, profile[key]):
            raise ValueError("Deployment profile contains an invalid public identifier.")
    if not isinstance(profile["browser_channel"], str) or profile["browser_channel"] not in ("msedge", "chromium"):
        raise ValueError("Deployment profile contains an unsupported browser channel.")
    for key, bounds in {"mail_wait_seconds": (30, 3600), "mail_poll_seconds": (1, 60),
                        "mail_scan_pages": (1, 100), "cache_retention_days": (1, 365),
                        "log_retention_days": (1, 365)}.items():
        value = profile[key]
        if type(value) is not int or not bounds[0] <= value <= bounds[1]:
            raise ValueError("Deployment profile contains an invalid numeric setting.")
    code = destination / "skills/usql-web-query-operator/scripts"
    (code / "_shared").mkdir(parents=True)
    for filename in ("__init__.py", "config.py", "errors.py", "browser.py", "env.py", "fs_utils.py"):
        shutil.copy2(skill / "scripts/_shared" / filename, code / "_shared" / filename)
    (code / "oes_achievement").mkdir()
    for source in sorted((skill / "scripts/oes_achievement").glob("*.py")):
        shutil.copy2(source, code / "oes_achievement" / source.name)
    for filename in ("oes_achievement.py", "run_oes_base_job.py", "run_oes_base_silent.py"):
        shutil.copy2(skill / "scripts" / filename, code / filename)
    style_dir = destination / "skills/xlsx/scripts"
    style_dir.mkdir(parents=True)
    for filename in ("style_apply.py", "style_palette.py"):
        shutil.copy2(skills / "xlsx/scripts" / filename, style_dir / filename)
    (destination / "tools").mkdir()
    shutil.copy2(executable, destination / "tools/lark-cli.exe")
    (destination / "private").mkdir()
    shutil.copy2(skill / "assets/oes_credentials.env.example", destination / "private/usql_api.env.example")
    shutil.copy2(profile_template, destination / "settings.json")
    shutil.copy2(skill / "assets/oes_base_deployment.md", destination / "README.md")
    (destination / "task-scheduler").mkdir()
    shutil.copy2(skill / "assets/oes_task_template.xml", destination / "task-scheduler/task-template.xml")
    shutil.copy2(skill / "assets/oes_prepare_task.ps1", destination / "prepare-task.ps1")
    (destination / "installer").mkdir()
    for source, target in (("oes_install.ps1", "install.ps1"), ("oes_install.cmd", "Install.cmd"),
            ("oes_install_core.ps1", "installer/core.ps1"), ("oes_installer_ui.json", "installer/ui.zh-CN.json"),
            ("oes_power.ps1", "power.ps1")):
        shutil.copy2(skill / "assets" / source, destination / target)
    shutil.copy2(profile_template, destination / "installer/profile.default.json")
    (destination / "payload/wheels").mkdir(parents=True)
    for entry in payload["files"]:
        shutil.copy2(runtime_payload / entry["path"], destination / "payload" / entry["path"])
    shutil.copy2(runtime_payload / "runtime-payload.json", destination / "payload/runtime-payload.json")
    (destination / "requirements.txt").write_text("".join(f"{name}=={version}\n" for name, version, _ in WHEELS), encoding="utf-8")
    (destination / "run.ps1").write_text(
        "param([ValidateSet('sync','login','mail-login','check','health','cleanup')][string]$Action='sync',[string]$RunKey)\n"
        "$ErrorActionPreference='Stop'\n$env:PYTHONUTF8='1'\n$env:PYTHONIOENCODING='utf-8'\n"
        "$taskPython=Join-Path $PSScriptRoot 'runtime/python/python.exe'\n"
        "if(-not (Test-Path -LiteralPath $taskPython)){$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'}\n"
        "$taskArguments=@((Join-Path $PSScriptRoot 'skills/usql-web-query-operator/scripts/run_oes_base_job.py'),$Action,'--settings',(Join-Path $PSScriptRoot 'settings.json'))\n"
        "if($RunKey){$taskArguments+=@('--run-key',$RunKey)}\n& $taskPython @taskArguments\nexit $LASTEXITCODE\n", encoding="utf-8")
    (destination / "setup.ps1").write_text(
        "param([string]$PythonExecutable)\n$ErrorActionPreference='Stop'\n"
        "if(-not $PythonExecutable){ & (Join-Path $PSScriptRoot 'Install.cmd'); exit $LASTEXITCODE }\n"
        "& $PythonExecutable -m venv (Join-Path $PSScriptRoot '.venv')\nif($LASTEXITCODE){exit $LASTEXITCODE}\n"
        "$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'\n"
        "& $taskPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')\nexit $LASTEXITCODE\n", encoding="utf-8")
    license_file = executable.parent.parent / "LICENSE"
    if license_file.is_file():
        shutil.copy2(license_file, destination / "tools/LICENSE-lark-cli")
    files = [{"path": str(path.relative_to(destination)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
             for path in sorted(destination.rglob("*")) if path.is_file()]
    manifest = {"bundle_schema_version": 2, "contains_credentials": False, "python": PYTHON_VERSION,
                "architecture": "AMD64", "offline_runtime": True, "files": files}
    (destination / "bundle-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as target:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                target.write(path, Path(destination.name) / path.relative_to(destination))
    return {"status": "completed", "directory": str(destination), "archive": str(archive), "files": len(files),
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "contains_credentials": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--lark-cli", type=Path, required=True)
    parser.add_argument("--runtime-payload", type=Path, required=True)
    parser.add_argument("--profile-template", type=Path, help="Public target profile only; never include credentials.")
    options = parser.parse_args()
    print(json.dumps(build(options.output_dir, options.lark_cli, options.runtime_payload, options.profile_template), ensure_ascii=False, indent=2))
