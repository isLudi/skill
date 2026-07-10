"""Validate the P0-P2 local Text2SQL skill stack with one read-only command."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
QUICK_VALIDATE = REPO_ROOT / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
CORE_ROOT = REPO_ROOT / "_shared" / "text2sql_core"
BUILD_CATALOG = REPO_ROOT / "scripts" / "build_text2sql_catalog.py"
AUDIT_CORPUS = REPO_ROOT / "scripts" / "audit_text2sql_corpus.py"
EXPECTED_SQLGLOT_VERSION = "30.12.0"
SKILL_NAMES = (
    "qingcheng-dashboard-sql",
    "sql-query-writer-for-dashboard",
    "usql-web-query-operator",
)
BUSINESS_SKILLS = (
    "qingcheng-dashboard-sql",
    "sql-query-writer-for-dashboard",
)
REFERENCE_PREFIXES = (
    "knowledge/",
    "resources/",
    "scripts/",
    "docs/",
    "references/",
    "agents/",
    "semantic/",
)
BACKTICK_REFERENCE_RE = re.compile(
    r"`((?:knowledge|resources|scripts|docs|references|agents|semantic)/[^`\r\n]+)`"
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
PLACEHOLDER_MARKERS = ("*", "<", ">", "${", "...", "MMDD", "YYYY")
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".sql", ".txt", ".ps1"}


@dataclass(frozen=True)
class ReferenceIssue:
    skill: str
    source: Path
    line: int
    reference: str
    historical: bool


def run_command(label: str, command: list[str], cwd: Path) -> bool:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    status = "PASS" if completed.returncode == 0 else "FAIL"
    print(f"[{status}] {label}")
    if output:
        for line in output.splitlines():
            print(f"  {line}")
    return completed.returncode == 0


def validate_registration(skill_root: Path) -> list[str]:
    failures: list[str] = []
    skill_md = skill_root / "SKILL.md"
    raw = skill_md.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        failures.append(f"{skill_md}: UTF-8 BOM prevents reliable frontmatter discovery")
    openai_yaml = skill_root / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        failures.append(f"{openai_yaml}: missing skill registration metadata")
    elif f"${skill_root.name}" not in openai_yaml.read_text(encoding="utf-8"):
        failures.append(f"{openai_yaml}: default_prompt does not reference ${skill_root.name}")
    return failures


def candidate_documents(skill_root: Path) -> list[Path]:
    documents = [skill_root / "SKILL.md"]
    for folder in ("knowledge", "references", "docs"):
        root = skill_root / folder
        if root.exists():
            documents.extend(sorted(root.rglob("*.md")))
    return [path for path in documents if path.exists()]


def normalize_reference(raw: str) -> str | None:
    reference = raw.strip().strip("<>").split("#", 1)[0].strip()
    reference = reference.rstrip(".,;:")
    if not reference or reference.startswith(("http://", "https://", "mailto:")):
        return None
    if WINDOWS_ABSOLUTE_RE.match(reference) or reference.startswith("/"):
        return None
    if any(marker in reference for marker in PLACEHOLDER_MARKERS):
        return None
    if " " in reference and not reference.endswith((".md", ".sql", ".json", ".py", ".yaml", ".yml")):
        return None
    return reference.replace("\\", "/")


def iter_references(skill_root: Path, source: Path):
    text = source.read_text(encoding="utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in BACKTICK_REFERENCE_RE.finditer(line):
            reference = normalize_reference(match.group(1))
            if reference:
                yield line_number, reference, skill_root / reference
        for match in MARKDOWN_LINK_RE.finditer(line):
            reference = normalize_reference(match.group(1))
            if not reference:
                continue
            if reference.startswith(REFERENCE_PREFIXES):
                target = skill_root / reference
            else:
                target = source.parent / reference
            yield line_number, reference, target


def check_references(skill_root: Path) -> list[ReferenceIssue]:
    issues: list[ReferenceIssue] = []
    for source in candidate_documents(skill_root):
        historical = source.as_posix().endswith("knowledge/update_log/changelog.md")
        seen: set[tuple[int, str]] = set()
        for line_number, reference, target in iter_references(skill_root, source):
            key = (line_number, reference)
            if key in seen:
                continue
            seen.add(key)
            allowed_cross_skill_reference = (
                skill_root.name == "usql-web-query-operator"
                and reference in {"scripts/build_reverse_indexes.py", "scripts/check_skill_integrity.py"}
                and any((REPO_ROOT / sibling_name / reference).resolve().exists() for sibling_name in BUSINESS_SKILLS)
            )
            if not target.resolve().exists() and not allowed_cross_skill_reference:
                issues.append(
                    ReferenceIssue(
                        skill=skill_root.name,
                        source=source.relative_to(skill_root),
                        line=line_number,
                        reference=reference,
                        historical=historical,
                    )
                )
    return issues


def check_utf8_bom() -> list[str]:
    roots = [REPO_ROOT / skill_name for skill_name in SKILL_NAMES]
    roots.extend((CORE_ROOT, REPO_ROOT / "scripts"))
    failures: list[str] = []
    candidates = [REPO_ROOT / "AGENTS.md", REPO_ROOT.parent / "AGENTS.md"]
    for root in roots:
        candidates.extend(
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        )
    for path in candidates:
        if path.read_bytes().startswith(b"\xef\xbb\xbf"):
            failures.append(f"UTF-8 BOM remains: {path}")
    return failures


def main() -> int:
    failures: list[str] = []

    if not run_command(
        "Text2SQL parser dependencies",
        [
            sys.executable,
            "-c",
            (
                "import importlib.metadata, jsonschema, sqlglot; "
                f"assert sqlglot.__version__ == '{EXPECTED_SQLGLOT_VERSION}', sqlglot.__version__; "
                "print('sqlglot=' + sqlglot.__version__ + ', jsonschema=' + importlib.metadata.version('jsonschema'))"
            ),
        ],
        REPO_ROOT,
    ):
        failures.append("Text2SQL parser dependencies missing or version mismatch")

    root_agents = REPO_ROOT.parent / "AGENTS.md"
    repo_agents = REPO_ROOT / "AGENTS.md"
    if root_agents.read_bytes() == repo_agents.read_bytes():
        print("[PASS] AGENTS boundary copies are byte-identical")
    else:
        print("[FAIL] AGENTS boundary copies differ")
        failures.append("root and skills AGENTS.md must remain byte-identical")

    bom_failures = check_utf8_bom()
    if bom_failures:
        print(f"[FAIL] UTF-8 without BOM policy: {len(bom_failures)} file(s)")
        for failure in bom_failures:
            print(f"  {failure}")
            failures.append(failure)
    else:
        print("[PASS] UTF-8 without BOM policy")

    for skill_name in SKILL_NAMES:
        skill_root = REPO_ROOT / skill_name
        failures.extend(validate_registration(skill_root))
        if not run_command(
            f"quick_validate {skill_name}",
            [sys.executable, str(QUICK_VALIDATE), str(skill_root)],
            REPO_ROOT,
        ):
            failures.append(f"quick_validate failed for {skill_name}")

    for skill_name in BUSINESS_SKILLS:
        skill_root = REPO_ROOT / skill_name
        if not run_command(
            f"reverse index reproducibility {skill_name}",
            [sys.executable, "scripts/build_reverse_indexes.py", "--check"],
            skill_root,
        ):
            failures.append(f"reverse indexes are stale for {skill_name}")

    if not run_command(
        "P2 generated manifests, contracts, and physical catalog reproducibility",
        [sys.executable, str(BUILD_CATALOG), "--check"],
        REPO_ROOT,
    ):
        failures.append("P2 generated manifests, contract indexes, or physical catalog are stale")

    for skill_name in BUSINESS_SKILLS:
        skill_root = REPO_ROOT / skill_name
        if not run_command(
            f"integrity {skill_name}",
            [sys.executable, "scripts/check_skill_integrity.py"],
            skill_root,
        ):
            failures.append(f"integrity check failed for {skill_name}")
        if not run_command(
            f"P2 semantic resolution evals {skill_name}",
            [sys.executable, "scripts/text2sql.py", "evaluate"],
            skill_root,
        ):
            failures.append(f"P2 semantic resolution evals failed for {skill_name}")

    for skill_name in SKILL_NAMES:
        skill_root = REPO_ROOT / skill_name
        issues = check_references(skill_root)
        live_issues = [issue for issue in issues if not issue.historical]
        historical_issues = [issue for issue in issues if issue.historical]
        status = "PASS" if not live_issues else "FAIL"
        print(
            f"[{status}] references {skill_name}: "
            f"live_missing={len(live_issues)} historical_missing={len(historical_issues)}"
        )
        for issue in live_issues:
            print(f"  {issue.source}:{issue.line} -> {issue.reference}")
            failures.append(
                f"missing live reference in {issue.skill}: {issue.source}:{issue.line} -> {issue.reference}"
            )
        for issue in historical_issues:
            print(f"  [WARN historical] {issue.source}:{issue.line} -> {issue.reference}")

    tests_dir = REPO_ROOT / "usql-web-query-operator" / "tests"
    if not run_command(
        "USQL safety and QueryPlan contract tests",
        [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-p", "test_*.py"],
        REPO_ROOT / "usql-web-query-operator",
    ):
        failures.append("USQL safety or QueryPlan contract tests failed")

    core_tests = CORE_ROOT / "tests"
    if not run_command(
        "P1-P2 QuerySpec, QueryPlan, compiler, probes, catalog, AST, and boundary tests",
        [sys.executable, "-m", "unittest", "discover", "-s", str(core_tests), "-p", "test_*.py"],
        REPO_ROOT,
    ):
        failures.append("P1-P2 shared-core tests failed")

    if not run_command(
        "Retained SQL corpus audit",
        [sys.executable, str(AUDIT_CORPUS)],
        REPO_ROOT,
    ):
        failures.append("retained SQL corpus audit failed")

    for skill_name in BUSINESS_SKILLS:
        skill_root = REPO_ROOT / skill_name
        if not run_command(
            f"Text2SQL domain wrapper smoke {skill_name}",
            [sys.executable, "scripts/text2sql.py", "summary"],
            skill_root,
        ):
            failures.append(f"Text2SQL domain wrapper failed for {skill_name}")

    if failures:
        print("\nText2SQL stack validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nText2SQL stack validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
