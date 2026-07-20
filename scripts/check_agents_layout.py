"""Validate the single-source AGENTS layout used by the local Codex workspace."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_ROOT = REPO_ROOT.parent
CANONICAL_AGENTS = REPO_ROOT / "AGENTS.md"
RUNTIME_AGENTS = CODEX_ROOT / "WORKSPACE_AGENTS.md"
CONFIG_FILE = CODEX_ROOT / "config.toml"
EXPECTED_FALLBACKS = [RUNTIME_AGENTS.name]
DEFAULT_PROJECT_DOC_MAX_BYTES = 32 * 1024
MOJIBAKE_MARKERS = (
    "\ufffd",
    "\u951f\u65a4\u62f7",
    "\u9225",
    "\u00c3",
    "\u00c2",
)


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_config(failures: list[str]) -> dict[str, Any]:
    if not CONFIG_FILE.is_file():
        failures.append(f"missing config: {CONFIG_FILE}")
        return {}
    try:
        with CONFIG_FILE.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        failures.append(f"invalid config.toml: {exc}")
        return {}


def validate_text_file(path: Path, label: str, failures: list[str]) -> bytes:
    if not path.is_file():
        failures.append(f"missing {label}: {path}")
        return b""

    content = path.read_bytes()
    if content.startswith(b"\xef\xbb\xbf"):
        failures.append(f"{label} has a UTF-8 BOM: {path}")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        failures.append(f"{label} is not valid UTF-8: {exc}")
        return content

    if not text.strip():
        failures.append(f"{label} is empty: {path}")
    for marker in MOJIBAKE_MARKERS:
        if marker in text:
            failures.append(f"{label} contains mojibake marker {marker!r}: {path}")
    return content


def source_in_directory(directory: Path, fallback_names: list[str]) -> Path | None:
    for name in ("AGENTS.override.md", "AGENTS.md", *fallback_names):
        candidate = directory / name
        if candidate.is_file():
            return candidate.resolve()
    return None


def simulated_sources(
    cwd: Path,
    project_root: Path,
    fallback_names: list[str],
) -> list[Path]:
    sources: list[Path] = []

    global_override = CODEX_ROOT / "AGENTS.override.md"
    global_default = CODEX_ROOT / "AGENTS.md"
    if global_override.is_file():
        sources.append(global_override.resolve())
    elif global_default.is_file():
        sources.append(global_default.resolve())

    resolved_root = project_root.resolve()
    resolved_cwd = cwd.resolve()
    relative_cwd = resolved_cwd.relative_to(resolved_root)
    project_directories = [resolved_root]
    current = resolved_root
    for part in relative_cwd.parts:
        current = current / part
        project_directories.append(current)

    for current in project_directories:
        source = source_in_directory(current, fallback_names)
        if source is not None:
            sources.append(source)
    return sources


def main() -> int:
    failures: list[str] = []

    config = load_config(failures)
    fallback_names = config.get("project_doc_fallback_filenames")
    if fallback_names != EXPECTED_FALLBACKS:
        failures.append(
            "config.toml must set project_doc_fallback_filenames exactly to "
            f"{EXPECTED_FALLBACKS!r}; found {fallback_names!r}"
        )
        fallback_names = EXPECTED_FALLBACKS

    max_bytes = config.get("project_doc_max_bytes", DEFAULT_PROJECT_DOC_MAX_BYTES)
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        failures.append(f"project_doc_max_bytes must be a positive integer; found {max_bytes!r}")
        max_bytes = DEFAULT_PROJECT_DOC_MAX_BYTES

    forbidden_paths = (
        CODEX_ROOT / "AGENTS.md",
        CODEX_ROOT / "AGENTS.override.md",
        REPO_ROOT / "AGENTS.global.md",
    )
    for path in forbidden_paths:
        if path.exists():
            failures.append(f"forbidden competing instruction file exists: {path}")

    if (CODEX_ROOT / ".git").exists():
        failures.append(
            f"{CODEX_ROOT} must not become a Git root; that would layer the root fallback and repository AGENTS.md"
        )
    if not (REPO_ROOT / ".git").exists():
        failures.append(f"skills repository marker is missing: {REPO_ROOT / '.git'}")

    canonical_bytes = validate_text_file(CANONICAL_AGENTS, "canonical AGENTS", failures)
    runtime_bytes = validate_text_file(RUNTIME_AGENTS, "runtime AGENTS mirror", failures)

    if canonical_bytes and len(canonical_bytes) > max_bytes:
        failures.append(
            f"canonical AGENTS exceeds project_doc_max_bytes: {len(canonical_bytes)} > {max_bytes}"
        )
    if runtime_bytes and len(runtime_bytes) > max_bytes:
        failures.append(
            f"runtime AGENTS mirror exceeds project_doc_max_bytes: {len(runtime_bytes)} > {max_bytes}"
        )
    if canonical_bytes and runtime_bytes and canonical_bytes != runtime_bytes:
        failures.append("runtime mirror differs from the Git-versioned canonical AGENTS.md")

    discovery_cases = {
        CODEX_ROOT: (CODEX_ROOT, [RUNTIME_AGENTS.resolve()]),
        REPO_ROOT: (REPO_ROOT, [CANONICAL_AGENTS.resolve()]),
    }
    actual_sources: dict[Path, list[Path]] = {}
    for cwd, (project_root, expected) in discovery_cases.items():
        actual = simulated_sources(cwd, project_root, list(fallback_names))
        actual_sources[cwd] = actual
        if actual != expected:
            failures.append(
                f"simulated discovery for cwd={cwd} expected {expected!r}, found {actual!r}"
            )

    if failures:
        print("AGENTS_LAYOUT_FAILED")
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    digest = sha256(canonical_bytes)
    print("AGENTS_LAYOUT_OK")
    print(f"canonical_sha256={digest}")
    print(f"runtime_sha256={sha256(runtime_bytes)}")
    print(f"canonical_bytes={len(canonical_bytes)}")
    for cwd, sources in actual_sources.items():
        print(f"cwd={cwd}; sources={','.join(str(path) for path in sources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
