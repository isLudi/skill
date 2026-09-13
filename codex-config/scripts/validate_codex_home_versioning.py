"""Validate the Git/local boundary for a Codex home without changing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]


CONFIG_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REPO_ROOT = CONFIG_DIR.parent
DEFAULT_CODEX_HOME = DEFAULT_REPO_ROOT.parent
MANIFEST_NAME = "codex-home.manifest.json"
SHARED_CONFIG_NAME = "config.shared.toml"
LOCAL_CONFIG_NAME = "machine.local.json"
ALLOWED_CLASSIFICATIONS = {"C1", "C2", "C3", "C4", "C5", "C6"}
WINDOWS_ABSOLUTE_PATH = re.compile(
    r"(?i)(?<![A-Za-z0-9_])(?:[A-Z]:[\\/]|\\\\[^\\\s]+\\[^\\\s]+)"
)
SECRET_SHAPES = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:sk|ghp|github_pat|xox[baprs])[-_][A-Za-z0-9_-]{16,}\b"),
    re.compile(
        r"(?im)^\s*[\"']?(?:api[_-]?key|access[_-]?token|password|secret)"
        r"[\"']?\s*[:=]\s*[\"']?(?!<|\$\{)[A-Za-z0-9_./+=-]{12,}"
    ),
)
FORBIDDEN_LOCAL_LEAF_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "password",
    "private_key",
    "secret",
    "token",
}
FORBIDDEN_TRACKED_BASENAMES = {
    ".env",
    "auth.json",
    "credentials.json",
    "machine.local.json",
}
FORBIDDEN_TRACKED_SUFFIXES = {
    ".db",
    ".duckdb",
    ".key",
    ".p12",
    ".pem",
    ".sqlite",
}
FORBIDDEN_TRACKED_DIRECTORIES = {
    ".sandbox-secrets",
    ".tmp",
    "attachments",
    "cache",
    "logs",
    "runtime",
    "sessions",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, label: str, failures: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        failures.append(f"invalid {label}: {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        failures.append(f"{label} must be a JSON object: {path}")
        return {}
    return value


def load_toml(path: Path, label: str, failures: list[str]) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        failures.append(f"invalid {label}: {path}: {exc}")
        return {}


def scan_portable_text(path: Path) -> list[str]:
    failures: list[str] = []
    try:
        content = path.read_bytes()
        text = content.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"portable source is not readable UTF-8: {path}: {exc}"]

    if content.startswith(b"\xef\xbb\xbf"):
        failures.append(f"portable source has a UTF-8 BOM: {path}")
    if "\ufffd" in text:
        failures.append(f"portable source contains a Unicode replacement character: {path}")
    if WINDOWS_ABSOLUTE_PATH.search(text):
        failures.append(f"portable configuration contains a Windows absolute path: {path}")
    for pattern in SECRET_SHAPES:
        if pattern.search(text):
            failures.append(f"portable configuration contains secret-shaped material: {path}")
            break
    return failures


def tracked_path_policy_violations(paths: Iterable[str]) -> list[str]:
    violations: list[str] = []
    for raw_path in paths:
        path = PurePosixPath(raw_path)
        lowered_parts = tuple(part.lower() for part in path.parts)
        name = path.name.lower()
        suffixes = {suffix.lower() for suffix in path.suffixes}

        forbidden_directory = any(
            part in FORBIDDEN_TRACKED_DIRECTORIES for part in lowered_parts[:-1]
        )
        plugin_cache = any(
            lowered_parts[index : index + 2] == ("plugins", "cache")
            for index in range(max(0, len(lowered_parts) - 1))
        )
        forbidden_suffix = bool(suffixes & FORBIDDEN_TRACKED_SUFFIXES)
        sqlite_sidecar = ".sqlite" in name and name != ".sqlite"

        if (
            name in FORBIDDEN_TRACKED_BASENAMES
            or name.endswith(".env")
            or forbidden_directory
            or plugin_cache
            or forbidden_suffix
            or sqlite_sidecar
        ):
            violations.append(raw_path)
    return violations


def git_tracked_paths(repo_root: Path, failures: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        failures.append(f"unable to enumerate tracked files: {message}")
        return []
    return [
        item.decode("utf-8", errors="strict")
        for item in result.stdout.split(b"\0")
        if item
    ]


def validate_manifest(
    manifest: dict[str, Any], repo_root: Path, failures: list[str]
) -> None:
    if manifest.get("schema_version") != 1:
        failures.append("codex-home manifest schema_version must be 1")

    policy = manifest.get("repository_policy")
    if not isinstance(policy, dict) or policy.get("codex_home_is_git_root") is not False:
        failures.append("manifest must forbid using the Codex home as a Git root")

    sources = manifest.get("versioned_sources")
    if not isinstance(sources, list) or not sources:
        failures.append("manifest must list versioned_sources")
        return

    seen: set[Path] = set()
    for source in sources:
        if not isinstance(source, dict):
            failures.append("every versioned source must be an object")
            continue
        raw_path = source.get("path")
        classification = source.get("classification")
        if not isinstance(raw_path, str) or not raw_path:
            failures.append("every versioned source must have a non-empty path")
            continue
        if classification not in ALLOWED_CLASSIFICATIONS:
            failures.append(f"invalid classification for versioned source {raw_path!r}")

        resolved = (CONFIG_DIR / raw_path).resolve()
        if not resolved.is_relative_to(repo_root.resolve()):
            failures.append(f"versioned source escapes the repository: {raw_path}")
        elif not resolved.is_file():
            failures.append(f"versioned source is missing: {raw_path}")
        elif resolved in seen:
            failures.append(f"duplicate versioned source: {raw_path}")
        seen.add(resolved)

    local_state = manifest.get("local_state")
    if not isinstance(local_state, list) or not local_state:
        failures.append("manifest must list local_state")
    else:
        for item in local_state:
            if not isinstance(item, dict) or item.get("classification") not in {
                "C2",
                "C5",
                "C6",
            }:
                failures.append("local_state entries must be classified as C2, C5, or C6")


def local_leaf_items(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, nested in value.items():
            nested_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from local_leaf_items(nested, nested_prefix)
    else:
        yield prefix, value


def validate_machine_local(
    local: dict[str, Any],
    local_path: Path,
    codex_home: Path,
    repo_root: Path,
    failures: list[str],
) -> None:
    if local.get("schema_version") != 1:
        failures.append("machine.local.json schema_version must be 1")
    if not isinstance(local.get("machine_id"), str) or not local["machine_id"].strip():
        failures.append("machine.local.json must define a non-empty machine_id")

    expected_paths = {
        "codex_home": codex_home.resolve(),
        "skills_repo": repo_root.resolve(),
    }
    for key, expected in expected_paths.items():
        raw_value = local.get(key)
        if not isinstance(raw_value, str) or not os.path.isabs(raw_value):
            failures.append(f"machine.local.json {key} must be an absolute path")
            continue
        if Path(raw_value).resolve() != expected:
            failures.append(f"machine.local.json {key} does not match the active location")

    executables = local.get("executables")
    python_path = executables.get("python") if isinstance(executables, dict) else None
    if not isinstance(python_path, str) or not os.path.isabs(python_path):
        failures.append("machine.local.json executables.python must be an absolute path")
    elif not Path(python_path).is_file():
        failures.append("machine.local.json executables.python does not exist")

    for dotted_key, value in local_leaf_items(local):
        leaf = dotted_key.rsplit(".", 1)[-1].lower()
        if leaf in FORBIDDEN_LOCAL_LEAF_KEYS:
            failures.append(
                f"machine.local.json must contain paths, not credential value key {dotted_key!r}"
            )
        if isinstance(value, str):
            if "\n" in value or "\r" in value:
                failures.append(f"machine.local.json value contains a newline: {dotted_key}")
            for pattern in SECRET_SHAPES:
                if pattern.search(value):
                    failures.append(
                        f"machine.local.json contains secret-shaped material at {dotted_key!r}"
                    )
                    break

    if local_path.parent.resolve() != codex_home.resolve():
        failures.append("machine.local.json must live directly in the Codex home")


def validate(
    repo_root: Path,
    codex_home: Path,
    local_path: Path,
    require_local_state: bool,
) -> list[str]:
    failures: list[str] = []
    manifest_path = repo_root / "codex-config" / MANIFEST_NAME
    shared_config_path = repo_root / "codex-config" / SHARED_CONFIG_NAME
    canonical_agents = repo_root / "AGENTS.md"
    runtime_agents = codex_home / "WORKSPACE_AGENTS.md"
    active_config_path = codex_home / "config.toml"

    if (codex_home / ".git").exists():
        failures.append("the Codex home must not be a Git repository")
    if not (repo_root / ".git").exists():
        failures.append("the skills repository Git marker is missing")

    manifest = load_json(manifest_path, "codex-home manifest", failures)
    shared = load_toml(shared_config_path, "shared config", failures)
    validate_manifest(manifest, repo_root, failures)

    expected_shared = manifest.get("required_shared_config", {})
    if shared != expected_shared:
        failures.append("config.shared.toml does not match required_shared_config")
    max_bytes = shared.get("project_doc_max_bytes")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 0 < max_bytes <= 32768:
        failures.append("project_doc_max_bytes must be a positive integer no greater than 32768")

    for portable_path in sorted((repo_root / "codex-config").rglob("*")):
        if portable_path.is_file() and "__pycache__" not in portable_path.parts:
            failures.extend(scan_portable_text(portable_path))

    tracked = git_tracked_paths(repo_root, failures)
    for path in tracked_path_policy_violations(tracked):
        failures.append(f"local/runtime/credential file is tracked: {path}")

    if require_local_state:
        active = load_toml(active_config_path, "active config", failures)
        for key, expected in expected_shared.items():
            if active.get(key) != expected:
                failures.append(
                    f"active config value for {key!r} differs from the shared contract"
                )

        if not canonical_agents.is_file() or not runtime_agents.is_file():
            failures.append("canonical or runtime Agent instructions are missing")
        elif canonical_agents.read_bytes() != runtime_agents.read_bytes():
            failures.append("WORKSPACE_AGENTS.md differs from the canonical AGENTS.md")

        local = load_json(local_path, "machine-local config", failures)
        validate_machine_local(local, local_path, codex_home, repo_root, failures)

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--codex-home", type=Path, default=DEFAULT_CODEX_HOME)
    parser.add_argument("--local-config", type=Path)
    parser.add_argument(
        "--skip-local-state",
        action="store_true",
        help="validate only versioned repository state",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    codex_home = args.codex_home.resolve()
    local_path = (args.local_config or codex_home / LOCAL_CONFIG_NAME).resolve()
    failures = validate(
        repo_root=repo_root,
        codex_home=codex_home,
        local_path=local_path,
        require_local_state=not args.skip_local_state,
    )
    if failures:
        print("CODEX_HOME_VERSIONING_FAILED")
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print("CODEX_HOME_VERSIONING_OK")
    print(f"manifest_sha256={sha256(repo_root / 'codex-config' / MANIFEST_NAME)}")
    print(f"canonical_agents_sha256={sha256(repo_root / 'AGENTS.md')}")
    print("codex_home_git_root=false")
    print(f"local_state_checked={str(not args.skip_local_state).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
