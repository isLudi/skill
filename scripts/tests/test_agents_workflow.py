"""Exercise instruction discovery and sync side effects in isolated repositories."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT.parent / "runtime" / "agents-workflow-tests"
SPEC = importlib.util.spec_from_file_location("agents_layout_under_test", ROOT / "scripts/check_agents_layout.py")
layout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(layout)
CANONICAL_TEXT = (ROOT / "AGENTS.md").read_text(encoding="utf-8")


def remove_test_workspace(workspace, attempts=20):
    """Retry transient Windows handles without hiding a cleanup failure."""
    if attempts < 1:
        raise ValueError("cleanup must make at least one attempt")
    workspace = Path(workspace).resolve()
    if workspace.parent != RUNTIME.resolve() or not workspace.name.startswith("case-"):
        raise ValueError("cleanup is restricted to an isolated case directory")

    def remove_readonly(action, path, error):
        target = Path(path).resolve()
        if not target.is_relative_to(workspace):
            raise ValueError("cleanup error target escapes the isolated case")
        exception = error[1]
        if isinstance(exception, PermissionError) and getattr(exception, "winerror", None) == 5:
            target.chmod(stat.S_IWRITE)
            action(path)
        else:
            raise exception

    for attempt in range(attempts):
        try:
            if workspace.exists():
                shutil.rmtree(workspace, onerror=remove_readonly)
            return
        except PermissionError as exception:
            if getattr(exception, "winerror", None) not in (5, 32) or attempt == attempts - 1:
                raise
            time.sleep(0.1)


class WorkspaceFixture(unittest.TestCase):
    def setUp(self):
        RUNTIME.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=RUNTIME)
        self.workspace = Path(self.temp.name).resolve()
        self.assertTrue(self.workspace.is_relative_to(RUNTIME.resolve()))
        self.repo = self.workspace / "skills"
        self.repo.mkdir()
        self.canonical = self.repo / "AGENTS.md"
        self.mirror = self.workspace / "WORKSPACE_AGENTS.md"
        self.config = self.workspace / "config.toml"
        self.canonical.write_text(CANONICAL_TEXT, encoding="utf-8")
        self.mirror.write_bytes(self.canonical.read_bytes())
        self.config.write_text('project_doc_fallback_filenames = ["WORKSPACE_AGENTS.md"]\nproject_doc_max_bytes = 32768\n', encoding="utf-8")
        self.machine_config = self.workspace / "machine.local.json"
        self.machine_config.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "machine_id": "Fixture",
                    "codex_home": str(self.workspace),
                    "skills_repo": str(self.repo),
                    "executables": {"python": sys.executable},
                    "paths": {},
                    "credential_file_paths": {},
                }
            ),
            encoding="utf-8",
        )
        for reference in layout.local_links(CANONICAL_TEXT):
            target = self.repo / reference
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("Fixture reference.\n", encoding="utf-8")
        (self.repo / ".git").mkdir()
        self.patcher = patch.multiple(layout, REPO_ROOT=self.repo, CODEX_ROOT=self.workspace,
                                      CANONICAL_AGENTS=self.canonical, RUNTIME_AGENTS=self.mirror,
                                      CONFIG_FILE=self.config)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        # Only the verified temporary test tree may be removed.
        self.assertTrue(self.workspace.is_relative_to(RUNTIME.resolve()))
        remove_test_workspace(self.workspace)
        self.temp.cleanup()

    def validate(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = layout.main()
        return result, output.getvalue()


class CleanupTests(unittest.TestCase):
    def make_workspace(self):
        RUNTIME.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="case-", dir=RUNTIME)).resolve()

    def locked(self):
        exception = PermissionError("transient Windows directory handle")
        exception.winerror = 32
        return exception

    def test_transient_lock_retries_then_removes(self):
        workspace = self.make_workspace()
        actual_remove = shutil.rmtree
        calls = []

        def remove(path, **kwargs):
            calls.append(path)
            if len(calls) == 1:
                raise self.locked()
            return actual_remove(path, **kwargs)

        try:
            with patch.object(shutil, "rmtree", side_effect=remove), patch.object(time, "sleep") as sleep:
                remove_test_workspace(workspace, attempts=3)
            self.assertEqual(calls, [workspace, workspace])
            sleep.assert_called_once_with(0.1)
            self.assertFalse(workspace.exists())
        finally:
            if workspace.exists():
                actual_remove(workspace)

    def test_persistent_lock_remains_a_failure(self):
        workspace = self.make_workspace()
        try:
            with patch.object(shutil, "rmtree", side_effect=self.locked()) as remove, patch.object(time, "sleep"):
                with self.assertRaises(PermissionError):
                    remove_test_workspace(workspace, attempts=3)
                self.assertEqual(remove.call_count, 3)
            self.assertTrue(workspace.exists())
        finally:
            shutil.rmtree(workspace)

    def test_runtime_root_is_never_deleted(self):
        with patch.object(shutil, "rmtree") as remove:
            with self.assertRaises(ValueError):
                remove_test_workspace(RUNTIME)
            remove.assert_not_called()


class LayoutTests(WorkspaceFixture):
    def test_valid_layout_and_editorial_changes(self):
        self.assertEqual(self.validate()[0], 0)
        edited = CANONICAL_TEXT.replace("## Scope and authorization", "## Authority")
        edited += "\nA wording change need not freeze a heading.\n"
        self.canonical.write_text(edited, encoding="utf-8")
        self.mirror.write_bytes(self.canonical.read_bytes())
        self.assertEqual(self.validate()[0], 0)

    def test_missing_and_misrouted_workflows(self):
        for workflow in ("P", "Q", "R", "S"):
            with self.subTest(workflow=workflow):
                edited = "\n".join(line for line in CANONICAL_TEXT.splitlines()
                                   if not line.startswith(f"| {workflow} |"))
                failures = []
                layout.validate_routes(edited, failures)
                self.assertIn(f"missing workflow ID: {workflow}", failures)
        edited = CANONICAL_TEXT.replace("| N | Existing Data Center", "| O | Existing Data Center")
        failures = []
        layout.validate_routes(edited, failures)
        self.assertIn("duplicate workflow ID: O", failures)
        edited = CANONICAL_TEXT.replace("data_center_replacement.md", "data_center_creation.md")
        failures = []
        layout.validate_routes(edited, failures)
        self.assertTrue(any("workflow N must link" in message for message in failures))

    def test_missing_reference_and_outside_repository_link(self):
        (self.repo / "market-consultant-dashboard-sql/SKILL.md").unlink()
        failures = []
        layout.validate_routes(CANONICAL_TEXT + "\n[unexpected](../outside.md)\n", failures)
        self.assertTrue(any("missing instruction reference" in message for message in failures))
        self.assertTrue(any("escapes repository" in message for message in failures))

    def test_competing_discovery_and_mirror_drift(self):
        (self.workspace / "AGENTS.override.md").write_text("competing", encoding="utf-8")
        self.assertNotEqual(self.validate()[0], 0)
        (self.workspace / "AGENTS.override.md").unlink()
        self.mirror.write_text("stale mirror", encoding="utf-8")
        self.assertIn("runtime mirror differs", self.validate()[1])

    def test_encoding_and_document_limit(self):
        self.mirror.write_bytes(b"\xff")
        self.assertIn("not valid UTF-8", self.validate()[1])
        self.mirror.write_bytes(self.canonical.read_bytes())
        for size in (10, 32769):
            with self.subTest(size=size):
                self.config.write_text('project_doc_fallback_filenames = ["WORKSPACE_AGENTS.md"]\n'
                                       f'project_doc_max_bytes = {size}\n', encoding="utf-8")
                self.assertNotEqual(self.validate()[0], 0)


@unittest.skipUnless(os.name == "nt" and shutil.which("powershell") and shutil.which("git"),
                     "Windows PowerShell and Git required")
class SyncTests(WorkspaceFixture):
    def setUp(self):
        super().setUp()
        shutil.copyfile(ROOT / "sync_agents.ps1", self.repo / "sync_agents.ps1")
        (self.repo / "scripts").mkdir(exist_ok=True)
        shutil.copyfile(ROOT / "scripts/check_agents_layout.py", self.repo / "scripts/check_agents_layout.py")
        self.git("init", "--quiet")
        self.git("add", "--", ".")
        self.git("-c", "user.name=Instruction Test", "-c", "user.email=test@example.invalid",
                 "commit", "--quiet", "-m", "fixture")
        # Identity stays in this disposable repository only.
        self.git("config", "user.name", "Instruction Test")
        self.git("config", "user.email", "test@example.invalid")
        self.initial_head = self.git("rev-parse", "HEAD")
        self.canonical.write_text(CANONICAL_TEXT + "\nReviewed local change.\n", encoding="utf-8")
        (self.repo / "unrelated.txt").write_text("user change", encoding="utf-8")
        self.git("add", "--", "unrelated.txt")
        (self.repo / "untracked.txt").write_text("user work", encoding="utf-8")
        self.initial_index = self.git("diff", "--cached", "--binary")

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True,
                                text=True, encoding="utf-8", check=True, timeout=30)
        return result.stdout

    def sync(self, *args):
        return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                               str(self.repo / "sync_agents.ps1"), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=60)

    def test_default_export_preserves_head_and_index(self):
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.canonical.read_bytes(), self.mirror.read_bytes())
        self.assertEqual(self.initial_head, self.git("rev-parse", "HEAD"))
        self.assertEqual(self.initial_index, self.git("diff", "--cached", "--binary"))
        self.assertTrue((self.repo / "untracked.txt").is_file())

    def test_invalid_flags_fail_before_copy_or_git_changes(self):
        for args in (("-Push",), ("-Commit", "-NoCommit"), ("-Mode", "Import"),
                     ("-Mode", "Check", "-Commit"), ("-Mode", "Check", "-Push"),
                     ("-Mode", "Check", "-ConfirmImport"), ("-ConfirmImport",)):
            with self.subTest(args=args):
                before = (self.canonical.read_bytes(), self.mirror.read_bytes())
                self.assertNotEqual(self.sync(*args).returncode, 0)
                self.assertEqual(before, (self.canonical.read_bytes(), self.mirror.read_bytes()))
                self.assertEqual(self.initial_head, self.git("rev-parse", "HEAD"))
                self.assertEqual(self.initial_index, self.git("diff", "--cached", "--binary"))

    def test_check_does_not_repair_drift(self):
        before = self.mirror.read_bytes()
        self.assertNotEqual(self.sync("-Mode", "Check").returncode, 0)
        self.assertEqual(before, self.mirror.read_bytes())
        self.assertEqual(self.initial_head, self.git("rev-parse", "HEAD"))

    def test_explicit_import_does_not_commit(self):
        mirror = self.mirror.read_bytes()
        result = self.sync("-Mode", "Import", "-ConfirmImport", "-NoCommit")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(mirror, self.canonical.read_bytes())
        self.assertEqual(self.initial_head, self.git("rev-parse", "HEAD"))
        self.assertEqual(self.initial_index, self.git("diff", "--cached", "--binary"))

    def test_explicit_commit_is_limited_to_agents(self):
        result = self.sync("-Commit")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotEqual(self.initial_head, self.git("rev-parse", "HEAD"))
        self.assertEqual("AGENTS.md", self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").strip())
        self.assertEqual(self.initial_index, self.git("diff", "--cached", "--binary"))


if __name__ == "__main__":
    unittest.main()
