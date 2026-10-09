from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from run_oes_base_silent import LauncherLog, main as silent_main

NS = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
TEST_ROOT = SKILL.parents[1] / "runtime/oes-scheduler-tests"


def temporary(test):
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    temp = tempfile.TemporaryDirectory(dir=TEST_ROOT)
    def cleanup():
        assert Path(temp.name).resolve().parent == TEST_ROOT.resolve()
        for attempt in range(30):
            try:
                temp.cleanup()
                return
            except OSError:
                if attempt == 29:
                    raise
                time.sleep(0.1)  # Native Windows icon/AV readers can briefly lock executable fixtures.
    test.addCleanup(cleanup)
    return temp


class SilentLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = temporary(self)
        self.root = Path(self.temp.name).resolve()
        self.settings = self.root / "settings.json"
        self.settings.write_text(json.dumps({"runtime_dir": "data/runtime", "log_retention_days": 30}), encoding="utf-8")

    def logs(self):
        return [json.loads(line) for path in (self.root / "data/runtime/launcher-logs").glob("*.jsonl")
                for line in path.read_text(encoding="utf-8").splitlines()]

    def test_pythonw_missing_streams_are_supported_and_raw_output_is_discarded(self):
        def job(options):
            self.assertEqual(options, ["sync", "--settings", str(self.settings)])
            print("password-and-private-output-must-not-be-logged")
            print("raw-exception-must-not-be-logged", file=sys.stderr)
            return 0
        with patch("run_oes_base_job.main", side_effect=job), \
             patch.object(sys, "stdout", None), patch.object(sys, "stderr", None):
            self.assertEqual(silent_main(["--settings", str(self.settings)]), 0)
        records = self.logs()
        self.assertEqual(records[-1]["exit_code"], 0)
        self.assertNotIn("password", json.dumps(records))
        self.assertNotIn("raw-exception", json.dumps(records))

    def test_native_job_failure_exit_code_is_preserved(self):
        with patch("run_oes_base_job.main", return_value=2):
            self.assertEqual(silent_main(["--settings", str(self.settings)]), 2)
        self.assertEqual(self.logs()[-1]["exit_code"], 2)

    def test_fatal_startup_failure_records_only_error_type(self):
        with patch("run_oes_base_job.main", side_effect=ValueError("credential-url-and-secret")):
            self.assertEqual(silent_main(["--settings", str(self.settings)]), 2)
        records = self.logs()
        self.assertEqual(records[-2]["error_type"], "ValueError")
        self.assertNotIn("secret", json.dumps(records))

    def test_broken_settings_still_receive_a_bootstrap_failure_log(self):
        self.settings.write_text("{broken-json", encoding="utf-8")
        self.assertEqual(silent_main(["--settings", str(self.settings)]), 2)
        self.assertEqual(self.logs()[-2]["error_type"], "JSONDecodeError")

    def test_unwritable_bootstrap_log_stops_before_job(self):
        with patch("run_oes_base_silent.LauncherLog", side_effect=PermissionError("synthetic")), \
             patch("run_oes_base_job.main") as job:
            self.assertEqual(silent_main(["--settings", str(self.settings)]), 2)
        job.assert_not_called()

    def test_systemexit_is_safe_and_manual_login_is_not_a_scheduled_action(self):
        with patch("run_oes_base_job.main", side_effect=SystemExit("private-system-exit")):
            self.assertEqual(silent_main(["--settings", str(self.settings)]), 2)
        self.assertNotIn("private", json.dumps(self.logs()))
        with patch("run_oes_base_job.main") as job:
            self.assertEqual(silent_main(["--settings", str(self.settings), "--action", "login"]), 2)
        job.assert_not_called()

    def test_bootstrap_logs_rotate_and_respect_same_thirty_day_policy(self):
        now = datetime(2026, 10, 4, 10, tzinfo=timezone(timedelta(hours=8)))
        directory = self.root / "data/runtime/launcher-logs"
        directory.mkdir(parents=True)
        old = directory / "oes-launcher-2026-09-04.jsonl"
        old.write_text("old", encoding="utf-8")
        boundary = directory / "oes-launcher-2026-09-05.jsonl"
        boundary.write_text("keep", encoding="utf-8")
        log = LauncherLog(self.settings, "sync", clock=lambda: now)
        self.assertFalse(old.exists())
        self.assertTrue(boundary.exists())
        self.assertEqual(log.path.name, "oes-launcher-2026-10-04.jsonl")


@unittest.skipUnless(os.name == "nt", "Native Windows Task Scheduler schema validation")
class TaskTemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp = temporary(self)
        self.root = Path(self.temp.name).resolve() / "OES 中文 & spaced bundle"
        self.root.mkdir()
        for relative in (".venv/Scripts/pythonw.exe", "skills/usql-web-query-operator/scripts/run_oes_base_silent.py", "settings.json"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative.endswith("pythonw.exe"):
                shutil.copy2(Path(sys.executable).with_name("pythonw.exe"), path)
            else:
                path.write_text("fixture", encoding="utf-8")
        (self.root / "task-scheduler").mkdir()
        shutil.copy2(SKILL / "assets/oes_task_template.xml", self.root / "task-scheduler/task-template.xml")

    def generate(self):
        return subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                               str(SKILL / "assets/oes_prepare_task.ps1"), "-BundleRoot", str(self.root)],
                              capture_output=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW)

    def test_generated_xml_keeps_interactive_hidden_and_no_overlap_with_safe_paths(self):
        result = self.generate()
        self.assertEqual(result.returncode, 0, result.stderr)
        metadata = json.loads(result.stdout)
        self.assertFalse(metadata["registered"])
        self.assertFalse(metadata["power_settings_changed"])
        path = Path(metadata["xml"])
        task = ET.parse(path).getroot()
        text = lambda name: task.find(name, NS).text
        self.assertEqual(text("t:Principals/t:Principal/t:LogonType"), "InteractiveToken")
        self.assertEqual(text("t:Settings/t:Hidden"), "true")
        self.assertEqual(text("t:Settings/t:Enabled"), "false")
        self.assertEqual(text("t:Settings/t:MultipleInstancesPolicy"), "IgnoreNew")
        self.assertEqual(text("t:Triggers/t:CalendarTrigger/t:Repetition/t:Interval"), "PT30M")
        self.assertEqual(text("t:Triggers/t:CalendarTrigger/t:Repetition/t:Duration"), "P1D")
        self.assertTrue(text("t:Triggers/t:CalendarTrigger/t:StartBoundary").endswith("+08:00"))
        self.assertEqual(Path(text("t:Actions/t:Exec/t:Command")), self.root / ".venv/Scripts/pythonw.exe")
        self.assertEqual(text("t:Actions/t:Exec/t:Arguments"),
                         f'"{self.root / "skills/usql-web-query-operator/scripts/run_oes_base_silent.py"}" --settings "{self.root / "settings.json"}"')
        env = dict(os.environ, OES_TEST_TASK_XML=str(path))
        validate = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
            "$ErrorActionPreference='Stop'; $oesService=New-Object -ComObject Schedule.Service; $oesService.Connect(); "
            "$oesTask=$oesService.NewTask(0); $oesTask.XmlText=[IO.File]::ReadAllText($env:OES_TEST_TASK_XML); "
            "[ordered]@{hidden=$oesTask.Settings.Hidden; enabled=$oesTask.Settings.Enabled; "
            "logon_type=$oesTask.Principal.LogonType; multiple_instances=$oesTask.Settings.MultipleInstances; "
            "actions=$oesTask.Actions.Count; interval=$oesTask.Triggers.Item(1).Repetition.Interval} | ConvertTo-Json"],
            env=env, capture_output=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(validate.returncode, 0, validate.stderr)
        actual = json.loads(validate.stdout)
        self.assertTrue(actual["hidden"])
        self.assertFalse(actual["enabled"])
        self.assertEqual((actual["logon_type"], actual["multiple_instances"], actual["interval"]), (3, 2, "PT30M"))

    def test_generation_preserves_existing_reviewed_xml(self):
        first = self.generate()
        self.assertEqual(first.returncode, 0, first.stderr)
        path = Path(json.loads(first.stdout)["xml"])
        previous = path.read_bytes()
        self.assertNotEqual(self.generate().returncode, 0)
        self.assertEqual(path.read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()
