"""Build a portable Windows OES/Base bundle containing code, never credentials."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def build(destination: Path, executable: Path) -> dict:
    skill = Path(__file__).resolve().parents[1]
    skills = skill.parent
    destination = destination.expanduser().resolve()
    if destination == skills or skills in destination.parents:
        raise ValueError("Deployment bundles must stay outside the skills repository.")
    if destination.exists():
        raise ValueError("Use a new bundle directory; existing contents are preserved.")
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
    shutil.copy2(skill / "assets/oes_base_job.example.json", destination / "settings.json")
    shutil.copy2(skill / "assets/oes_base_deployment.md", destination / "README.md")
    (destination / "task-scheduler").mkdir()
    shutil.copy2(skill / "assets/oes_task_template.xml", destination / "task-scheduler/task-template.xml")
    shutil.copy2(skill / "assets/oes_prepare_task.ps1", destination / "prepare-task.ps1")
    (destination / "requirements.txt").write_text("playwright==1.60.0\nopenpyxl==3.1.5\ntzdata==2026.2\n", encoding="utf-8")
    (destination / "run.ps1").write_text(
        "param([ValidateSet('sync','login','mail-login','check','cleanup')][string]$Action='sync',[string]$RunKey)\n"
        "$ErrorActionPreference='Stop'\n$env:PYTHONUTF8='1'\n$env:PYTHONIOENCODING='utf-8'\n"
        "$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'\n"
        "$taskArguments=@((Join-Path $PSScriptRoot 'skills/usql-web-query-operator/scripts/run_oes_base_job.py'),$Action,'--settings',(Join-Path $PSScriptRoot 'settings.json'))\n"
        "if($RunKey){$taskArguments+=@('--run-key',$RunKey)}\n& $taskPython @taskArguments\nexit $LASTEXITCODE\n", encoding="utf-8")
    (destination / "setup.ps1").write_text(
        "param([Parameter(Mandatory=$true)][string]$PythonExecutable)\n$ErrorActionPreference='Stop'\n"
        "& $PythonExecutable -m venv (Join-Path $PSScriptRoot '.venv')\nif($LASTEXITCODE){exit $LASTEXITCODE}\n"
        "$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'\n"
        "& $taskPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')\nexit $LASTEXITCODE\n", encoding="utf-8")
    license_file = executable.parent.parent / "LICENSE"
    if license_file.is_file():
        shutil.copy2(license_file, destination / "tools/LICENSE-lark-cli")
    files = [{"path": str(path.relative_to(destination)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
             for path in sorted(destination.rglob("*")) if path.is_file()]
    manifest = {"bundle_schema_version": 1, "contains_credentials": False, "files": files}
    (destination / "bundle-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    archive = destination.with_suffix(".zip")
    if archive.exists():
        raise ValueError("Archive already exists; no overwrite was performed.")
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
    options = parser.parse_args()
    print(json.dumps(build(options.output_dir, options.lark_cli), ensure_ascii=False, indent=2))
