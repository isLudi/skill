from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from lark_delivery.core import catalog
from lark_delivery.core.registry import adapter_for
from lark_delivery.domains.market_consultant.adapter import report_arguments
from lark_delivery.domains.market_consultant import scheduler
from lark_delivery.paths import SKILL_ROOT


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.definition = catalog.load_channel(catalog.DEFAULT_CHANNEL)

    def test_current_schedule_has_single_canonical_source(self):
        target = catalog.select_targets(self.definition)[0]
        cfg = catalog.schedule_config(self.definition, target)
        self.assertIs(type(cfg["enabled"]), bool)
        self.assertEqual(cfg["enabled"], self.definition["schedule"]["enabled"])
        self.assertEqual(cfg["hours"], [9, 13, 17, 21])
        self.assertEqual(catalog.resolve_compat_config(SKILL_ROOT / "config/scheduled_push.json", "schedule"), cfg)
        self.assertEqual(catalog.resolve_compat_config(SKILL_ROOT / "config/push_source.json", "source"),
                         catalog.source_defaults(self.definition, target))

    def test_qingcheng_has_its_own_domain_but_no_invented_channel(self):
        self.assertEqual(catalog.registry()["domains"]["qingcheng"]["semantic_skill"], "qingcheng-dashboard-sql")
        with self.assertRaisesRegex(ValueError, "no cross-department fallback"):
            catalog.load_channel("qingcheng/self_incubated_koc_5")

    def test_market_adapter_cannot_be_used_for_qingcheng(self):
        self.definition["domain"] = "qingcheng"
        with self.assertRaisesRegex(ValueError, "No reviewed adapter"):
            adapter_for(self.definition)

    def test_unknown_adapter_cannot_fall_back(self):
        self.definition["adapter"] = "unreviewed"
        with self.assertRaises(ValueError):
            adapter_for(self.definition)

    def test_wrong_config_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            catalog.validate_config(self.definition, "qingcheng/demo")

    def test_duplicate_target_chat_or_id_is_rejected(self):
        self.definition["targets"].append(deepcopy(self.definition["targets"][0]))
        with self.assertRaises(ValueError):
            catalog.validate_config(self.definition, catalog.DEFAULT_CHANNEL)

    def test_multiple_targets_selected_independently_without_renaming_channel(self):
        second = {"id": "other_group", "chat_id": "oc_testsecond", "display_name": "Test only", "enabled": True}
        self.definition["targets"].append(second)
        targets = catalog.select_targets(self.definition)
        self.assertEqual(len(targets), 2)
        self.assertEqual(catalog.select_targets(self.definition, ["other_group"]), [second])
        configs = [catalog.schedule_config(self.definition, target) for target in targets]
        self.assertNotEqual(configs[0]["state_dir"], configs[1]["state_dir"])
        self.assertEqual(configs[0]["channels"], configs[1]["channels"])

    def test_unknown_disabled_and_duplicate_target_selections_stop(self):
        for ids in (["unknown"], ["gaoyang", "gaoyang"]):
            with self.assertRaises(ValueError):
                catalog.select_targets(self.definition, ids)
        self.definition["targets"][0]["enabled"] = False
        with self.assertRaises(ValueError):
            catalog.select_targets(self.definition)

    def test_group_rename_does_not_change_identity_state_or_channel(self):
        target = catalog.select_targets(self.definition)[0]
        first = catalog.schedule_config(self.definition, target)
        target["display_name"] = "renamed"
        second = catalog.schedule_config(self.definition, target)
        self.assertEqual(first["chat_id"], second["chat_id"])
        self.assertEqual(first["state_dir"], second["state_dir"])

    def test_existing_ledger_namespace_is_preserved(self):
        cfg = scheduler.load_config(scheduler.DEFAULT_CONFIG)
        self.assertEqual(Path(cfg["state_dir"]).name, "scheduled")
        self.assertEqual(cfg["chat_id"], "oc_b9dc09ba622ca00059bbc472922a803d")

    def test_scope_drift_is_rejected(self):
        cfg = scheduler.load_config(scheduler.DEFAULT_CONFIG)
        cfg["chat_id"] = "oc_other"
        with self.assertRaises(ValueError):
            scheduler.validate_config(cfg)

    def test_registry_path_must_stay_in_config_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "channels.json").write_text(json.dumps({"schema_version": 1, "domains": {},
                "channels": {catalog.DEFAULT_CHANNEL: "../outside.json"}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escaped"):
                catalog.load_channel(catalog.DEFAULT_CHANNEL, root)

    def test_two_channels_cannot_share_or_nest_runtime_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = deepcopy(self.definition)
            second = deepcopy(first)
            second["channel_id"] = "second"
            second_key = "market_consultant/second"
            for state in (first["state_dir"], str(Path(first["state_dir"]) / "child")):
                second["state_dir"] = state
                (root / "first.json").write_text(json.dumps(first), encoding="utf-8")
                (root / "second.json").write_text(json.dumps(second), encoding="utf-8")
                (root / "channels.json").write_text(json.dumps({"schema_version": 1, "domains": {"market_consultant": {}},
                    "channels": {catalog.DEFAULT_CHANNEL: "first.json", second_key: "second.json"}}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "overlap"):
                    catalog.load_channel(catalog.DEFAULT_CHANNEL, root)

    def test_preview_args_keep_field_scope_and_sender(self):
        target = catalog.select_targets(self.definition)[0]
        args = report_arguments(self.definition, target, report_type="both")
        self.assertEqual(args.identity, "bot")
        self.assertEqual(args.mention_target, "manager")
        self.assertTrue(args.strict_mentions)
        self.assertEqual(args.raw_table_id, self.definition["source"]["raw_table_id"])
