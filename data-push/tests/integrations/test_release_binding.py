"""Offline exact-release migration tests; no API calls or production state writes."""
import copy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import release_binding as rb
import scheduled_push as sp


class ReleaseBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cfg = sp.load_config(sp.DEFAULT_CONFIG)
        self.cfg["upstream"].pop("log_protocol", None)  # Explicit historical single-period migration fixture.
        self.cfg["state_dir"] = str(self.root / "state")
        self.slot = datetime(2026, 9, 8, 13, tzinfo=sp.TZ)
        self.at = self.slot + timedelta(minutes=20)
        self.policy = {
            "version_id": 987, "source_sha256": "a" * 64, "source_comparison_sha256": "b" * 64,
            "previous_exec_file_id": self.cfg["upstream"]["exec_file_id"],
            "publication_verified_at": "2026-09-08T10:32:27+08:00",
            "not_before": self.slot.isoformat(), "expires_at": (self.slot + timedelta(hours=11)).isoformat(),
            "success_template": "SUCCESS: 全部渠道{period} lead_id原始数据已安全写入飞书多维表格",
        }
        self.cfg["upstream"]["approved_release_binding"] = self.policy
        self.execution = {"id": 123, "taskId": 66504, "status": 6,
                          "periodTime": "2026-09-08 13:00:00", "planRunTime": "2026-09-08 13:00:00",
                          "startTime": "2026-09-08 13:00:04", "endTime": "2026-09-08 13:10:00",
                          "runConfig": json.dumps({"execFileId": 900, "triggerSourceEnum": "SCHEDULE"})}

    def plan(self):
        u = self.cfg["upstream"]
        plan = {"schema_version": "tiangong2-task-publish-plan-v2", "operation": "publish_saved_tiangong2_task",
                "status": "blocked_already_published", "read_only_plan": True, "remote_mutations": 0,
                "created_at": (self.at - timedelta(seconds=10)).isoformat(),
                "identity": {"name": u["owner"]}, "scope": {**u, "owner_name": u["owner"]},
                "baseline": {"current_source_sha256": self.policy["source_sha256"],
                             "current_source_comparison_sha256": self.policy["source_comparison_sha256"],
                             "latest_published_source_comparison_sha256": self.policy["source_comparison_sha256"],
                             "latest_published_version_id": 987, "source_matches_latest_published": True,
                             "versions": [{"id": 987, "status": "已发布", "publishTime": "2026-09-08 10:32:00"}]}}
        plan["plan_sha256"] = rb.digest(plan)
        return plan

    def resign(self, plan):
        plan.pop("plan_sha256", None)
        plan["plan_sha256"] = rb.digest(plan)
        return plan

    def test_exact_current_publication_accepted(self):
        rb.validate_publication(self.plan(), self.cfg, self.policy, self.execution, self.at)

    def test_uses_actual_operator_plan_wire_contract(self):
        scripts = Path(__file__).resolve().parents[3] / "usql-web-query-operator/scripts"
        sys.path.insert(0, str(scripts))
        self.addCleanup(lambda: sys.path.remove(str(scripts)))
        from tiangong2_task.config import TASK_CONTENT_SPECS
        from tiangong2_task.publishing import build_publish_plan
        source = "print('fixture')\n"

        class Reader:
            def get_task_content(self, **kwargs):
                return TASK_CONTENT_SPECS[4], {"python": source}

            def list_versions(self, task_id):
                return [{"id": 987, "status": "已发布", "ver": "V4", "publishTime": "2026-09-08 10:32:00"}]

            def get_version_code(self, version_id):
                return {"code": source}

        u = self.cfg["upstream"]
        task = SimpleNamespace(project={"id": u["project_id"]}, menu={"taskType": 4},
                               metadata={"taskType": 4}, path=("数据开发", u["folder"], u["task_name"]),
                               folder_name=u["folder"], owner_name=u["owner"],
                               **{key: u[key] for key in ("project_id", "menu_id", "task_id", "nezha_task_id", "task_name")})
        plan = build_publish_plan(Reader(), task=task, identity={"name": u["owner"]})
        self.policy["source_sha256"] = plan["baseline"]["current_source_sha256"]
        self.policy["source_comparison_sha256"] = plan["baseline"]["current_source_comparison_sha256"]
        plan["created_at"] = (self.at - timedelta(seconds=10)).isoformat()
        rb.validate_publication(self.resign(plan), self.cfg, self.policy, self.execution, self.at)
        plan.pop("read_only_plan")
        plan["read_only"] = True
        with self.assertRaises(ValueError):
            rb.validate_publication(self.resign(plan), self.cfg, self.policy, self.execution, self.at)

    def test_publication_hash_scope_owner_and_source_drift_rejected(self):
        mutations = [
            ("scope", "task_id", 0), ("scope", "owner_name", "other"), ("identity", "name", "other"),
            ("baseline", "current_source_sha256", "c" * 64),
            ("baseline", "current_source_comparison_sha256", "c" * 64),
            ("baseline", "latest_published_source_comparison_sha256", "c" * 64),
            ("baseline", "latest_published_version_id", 988),
            ("baseline", "source_matches_latest_published", False),
        ]
        for section, key, value in mutations:
            with self.subTest(key=key):
                plan = self.plan()
                plan[section][key] = value
                with self.assertRaises(ValueError):
                    rb.validate_publication(self.resign(plan), self.cfg, self.policy, self.execution, self.at)
        plan = self.plan()
        plan["plan_sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "Hash"):
            rb.validate_publication(plan, self.cfg, self.policy, self.execution, self.at)

    def test_stale_unpublished_and_mid_execution_publication_rejected(self):
        for kind in ("stale", "unpublished", "after_start", "pre_execution", "ambiguous"):
            with self.subTest(kind=kind):
                plan = self.plan()
                if kind == "stale":
                    plan["created_at"] = (self.at - timedelta(minutes=6)).isoformat()
                elif kind == "unpublished":
                    plan["status"] = "ready"
                elif kind == "after_start":
                    plan["baseline"]["versions"][0]["publishTime"] = "2026-09-08 13:05:00"
                elif kind == "pre_execution":
                    plan["created_at"] = "2026-09-08T12:00:00+08:00"
                else:
                    plan["baseline"]["versions"].append(copy.deepcopy(plan["baseline"]["versions"][0]))
                with self.assertRaises(ValueError):
                    rb.validate_publication(self.resign(plan), self.cfg, self.policy, self.execution, self.at)

    def test_submit_timestamp_is_not_sufficient_publication_evidence(self):
        policy = {**self.policy, "publication_verified_at": "2026-09-08T13:05:00+08:00"}
        with self.assertRaisesRegex(ValueError, "postdates execution start"):
            rb.validate_publication(self.plan(), self.cfg, policy, self.execution, self.at)

    def test_completion_marker_must_be_unique_and_summary_free(self):
        line = self.policy["success_template"].format(period="20260911期")
        rb.verify_raw_only_log(line + "\nexit_code: 0\n", self.policy, "20260911期")
        for log in [line + "\n" + line, line.replace("全部渠道", "两个指定IP渠道"),
                    line + "\n汇总键同步完成：1条", line + "\n汇总表字段校验通过：2个键字段"]:
            with self.subTest(log=log):
                with self.assertRaises(ValueError):
                    rb.verify_raw_only_log(log, self.policy, "20260911期")

    def test_binding_is_durable_and_cannot_automatically_change_again(self):
        self.assertIsNone(rb.bound_file_id(self.cfg, self.policy))
        rb.persist_binding(self.cfg, self.policy, 900, self.execution, self.plan(), self.at)
        self.assertEqual(rb.bound_file_id(self.cfg, self.policy), 900)
        rb.persist_binding(self.cfg, self.policy, 900, self.execution, self.plan(), self.at)
        with self.assertRaises(ValueError):
            rb.persist_binding(self.cfg, self.policy, 901, self.execution, self.plan(), self.at)
        path = rb.binding_path(self.cfg, self.policy)
        record = json.loads(path.read_text(encoding="utf-8"))
        record["exec_file_id"] = 901
        path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaises(ValueError):
            rb.bound_file_id(self.cfg, self.policy)

    def test_binding_cannot_be_reused_for_changed_task_scope(self):
        rb.persist_binding(self.cfg, self.policy, 900, self.execution, self.plan(), self.at)
        self.cfg["upstream"]["task_id"] += 1
        with self.assertRaises(ValueError):
            rb.bound_file_id(self.cfg, self.policy)

    def upstream_fixtures(self, old_log=False):
        directory = self.root / "runtime/usql-web-query-operator/tiangong2-task"
        directory.mkdir(parents=True)
        u = self.cfg["upstream"]
        history = {"scope": u, "identity": {"name": u["owner"]},
                   "task_schedule": {"supervisor": u["owner"], "scheduleId": u["schedule_id"], "scheduleFrequency": "4h"},
                   "executions": [self.execution]}
        (directory / "history.json").write_text(json.dumps(history), encoding="utf-8")
        log = ('采用dt=20260908, hour=11，延迟2小时\n目标多维表格校验通过：table_id=tbljWRvaqKTdrCx4\n'
               '渠道分布：{"KOC-周帅数学":2}\n数据校验通过：2行，期次20260911期，1个渠道\n'
               '新记录回读校验通过\n旧记录删除完成：1条\n最终回读校验通过：2条\n'
               + self.policy["success_template"].format(period="20260911期") + '\nexit_code:  0\n')
        if old_log:
            log = log.replace("全部渠道", "两个指定IP渠道")
        raw = log.encode("utf-8")
        (directory / "stage.log").write_bytes(raw)
        doc = {**history, "execution": self.execution, "execution_detail": {"status": 6},
               "stages": [{"metadata": {"statusDesc": "success", "taskId": 66504},
                           "log_file": "stage.log", "log_sha256": hashlib.sha256(raw).hexdigest()}]}
        (directory / "execution.json").write_text(json.dumps(doc), encoding="utf-8")
        plan = self.plan()
        plan_path = directory / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        return directory, {"status": "blocked_already_published", "plan_file": str(plan_path), "plan_sha256": plan["plan_sha256"]}

    def test_upstream_binds_once_then_keeps_strict_file_pin(self):
        directory, reply = self.upstream_fixtures()
        with patch.object(sp, "SKILLS", self.root / "skills"), patch.object(sp, "now", return_value=self.at), \
                patch.object(sp, "operator", return_value=directory), patch.object(sp, "operator_reply", return_value=reply) as read_plan:
            evidence = sp.upstream_ready(self.cfg, self.slot)
            self.assertEqual(evidence["exec_file_id"], 900)
            self.assertEqual(rb.bound_file_id(self.cfg, self.policy), 900)
            sp.upstream_ready(self.cfg, self.slot)
            self.assertEqual(read_plan.call_count, 1)
            history = sp.read_json(directory / "history.json")
            history["executions"][0]["runConfig"] = json.dumps({"execFileId": 901, "triggerSourceEnum": "SCHEDULE"})
            (directory / "history.json").write_text(json.dumps(history), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "published execution file changed"):
                sp.upstream_ready(self.cfg, self.slot)
            self.assertEqual(read_plan.call_count, 1)

    def test_old_log_never_binds_or_checks_publication(self):
        directory, reply = self.upstream_fixtures(old_log=True)
        with patch.object(sp, "SKILLS", self.root / "skills"), patch.object(sp, "now", return_value=self.at), \
                patch.object(sp, "operator", return_value=directory), patch.object(sp, "operator_reply", return_value=reply) as read_plan:
            with self.assertRaises(ValueError):
                sp.upstream_ready(self.cfg, self.slot)
            read_plan.assert_not_called()
            self.assertFalse(rb.binding_path(self.cfg, self.policy).exists())

    def test_expired_initial_binding_and_previous_pin_drift_block(self):
        directory, _ = self.upstream_fixtures()
        with patch.object(sp, "operator", return_value=directory), patch.object(sp, "now", return_value=self.at + timedelta(days=1)):
            with self.assertRaisesRegex(ValueError, "expired"):
                sp.upstream_ready(self.cfg, self.slot)
        self.policy["previous_exec_file_id"] = 12
        with patch.object(sp, "operator", return_value=directory):
            with self.assertRaisesRegex(ValueError, "previous file pin"):
                sp.upstream_ready(self.cfg, self.slot)


if __name__ == "__main__":
    unittest.main()
