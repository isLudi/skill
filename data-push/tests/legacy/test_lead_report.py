"""Offline migration tests: exact scope, complete snapshots, rates and sending."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import group_push as gp
import lead_report as lr


def lead(index, channel="渠道甲", person="甲", **values):
    fields = {source: 0 for source in (*lr.COUNTERS.values(), *lr.RESULT_COUNTERS.values())}
    fields.update({"lead_id": str(index), "期次": "20260911期", "渠道": channel,
                   "经理": "经理甲", "主管": "主管甲", "部门": "部门甲", "顾问": person,
                   "顾问账号": "account-" + person, "分区日期": "20260907", "分区小时": "11",
                   "退前线索": 1, "退后线索": 1})
    fields.update(values)
    return {"record_id": "record-" + str(index), **fields}


def config(section="过程数据", channel="渠道甲", **values):
    fields = {"渠道": [channel], "推送类型": [section], "推送标题": section + "标题",
              "推送期次": "20260911期", "推送说明": "渠道：旧渠道\n数据截止：2小时前\n口径说明",
              "接收群": [], "计算_提醒顾问": "旧人名", "提醒": "旧提醒"}
    fields.update(values)
    return {"record_id": "config-" + section, **fields}


def args(*extra):
    parser = argparse.ArgumentParser()
    gp.add_common_arguments(parser)
    # Keep the legacy report regression explicit; the shipped default is now
    # grade-compact with manager mentions in a different fixed group.
    return parser.parse_args(["--report-profile", "standard", "--chat-id", "oc_legacy_test",
                              "--report-type", "both", "--mention-target", "none",
                              "--channel", "渠道甲", "--no-mentions", "--no-image", *extra])


def report(records, report_type="both"):
    _fields, counters = lr.projection(set(records[0]), report_type)
    return lr.build_report(records, counters, "20260911期")


class LeadReportTests(unittest.TestCase):
    def test_supervisor_targets_come_only_from_ranked_dimensions(self):
        records = [lead(1, person="甲", **{"主管": "主管甲", "5min标记": 0, "净收款": 200}),
                   lead(2, person="乙", **{"主管": "主管乙", "5min标记": 1, "净收款": 0}),
                   lead(3, person="丙", **{"主管": "无效主管", "退后线索": 0})]
        actual = report(records)
        self.assertEqual(actual["reminders"]["过程数据"], ["甲"])
        self.assertEqual(actual["reminders"]["结果数据"], ["乙"])
        self.assertEqual(actual["reminder_supervisors"]["过程数据"], ["主管甲"])
        self.assertEqual(actual["reminder_supervisors"]["结果数据"], ["主管乙"])

    def test_supervisor_render_keeps_consultants_plain_even_if_names_overlap(self):
        row = {"fields": {"提醒": "本次5min率较低顾问：甲、乙", "计算_提醒顾问": "甲、乙",
                           "_mention_target": "supervisor", "_reminder_supervisors": ["甲", "主管乙"]}}
        rendered = gp._render_configured_reminder(row, {"甲": "ou_a", "乙": "ou_b", "主管乙": "ou_s"})
        self.assertTrue(rendered.startswith("本次5min率较低顾问：甲、乙\n"))
        self.assertEqual(rendered.count("<at "), 2)
        self.assertNotIn('user_id="ou_b"', rendered)
        self.assertIn("请主管关注：", rendered)

    def test_group_membership_requires_complete_unique_accounts(self):
        def payload(**changes):
            data = {"users": [{"member_id": "ou_a"}], "user_total": 1, "has_more": False}
            data.update(changes)
            return json.dumps({"ok": True, "data": data})
        with patch.object(gp, "run_lark", return_value=payload()):
            self.assertEqual(gp.mention_nonmembers("oc_group", {"甲": "ou_a", "乙": "ou_b"}, "bot", 30), ["乙"])
        for changes in ({"has_more": True}, {"truncations": [{"limit": 1}]}, {"user_total": 2},
                        {"users": [{"member_id": "ou_a"}, {"member_id": "ou_a"}], "user_total": 2}):
            with self.subTest(changes=changes), patch.object(gp, "run_lark", return_value=payload(**changes)), self.assertRaises(ValueError):
                gp.mention_nonmembers("oc_group", {"甲": "ou_a"}, "bot", 30)

    def test_supervisor_mode_cannot_silently_fall_back_to_legacy_view(self):
        parsed = args("--source-mode", "summary-view", "--mention-target", "supervisor")
        parsed.no_mentions = False  # Exercise the retained opt-in path, not the names-only profile.
        with self.assertRaisesRegex(ValueError, "仅支持"):
            gp.prepare(parsed)

    def test_explicit_names_only_wins_over_stale_mention_flags(self):
        parser = argparse.ArgumentParser()
        gp.add_common_arguments(parser)
        for flags in ([], ["--mention-target", "supervisor", "--strict-mentions", "--require-mention-membership"]):
            parsed = parser.parse_args(["--no-mentions", *flags])
            self.assertTrue(parsed.no_mentions)
            self.assertEqual(gp.effective_mention_target(parsed), "none")

    def test_names_only_render_ignores_resolved_accounts_and_old_supervisor_list(self):
        row = {"fields": {"提醒": "本次5min率较低顾问：甲、乙", "计算_提醒顾问": "甲、乙",
                           "_mention_target": "none", "_reminder_supervisors": ["主管甲"]}}
        rendered = gp._render_configured_reminder(row, {"甲": "ou_a", "乙": "ou_b", "主管甲": "ou_s"})
        self.assertEqual(rendered, "本次5min率较低顾问：甲、乙")
        self.assertNotIn("<at", rendered)
        self.assertNotIn("主管", rendered)

    def test_nonmember_gate_blocks_upload_even_if_unresolved_mentions_allowed(self):
        context = {"chat_id": "oc_test", "mention_info": {"lookup_error": "", "unresolved": [],
                   "ambiguous": {}, "nonmembers": ["主管甲"]}}
        with patch.object(gp, "prepare", return_value=context), patch.object(gp, "upload_image") as upload, patch.object(gp, "send_markdown") as send:
            with self.assertRaisesRegex(SystemExit, "尚未入群"):
                gp.main(["send", "--confirm-send", "--allow-unresolved-mentions"])
            upload.assert_not_called()
            send.assert_not_called()

    def test_defaults_migrate_source_and_do_not_inherit_legacy_coordinates(self):
        with patch.dict("os.environ", {"SOURCE_URL": "old", "BASE_TOKEN": "old", "TABLE_ID": "old", "VIEW_ID": "old"}):
            actual = args()
        self.assertIn("MrPNwuFvPiiDX0k4jTXcLU8anse", actual.source_url)
        self.assertIn("tblqvlnqNslL1nWA", actual.source_url)
        self.assertEqual(actual.raw_table_id, "tbljWRvaqKTdrCx4")
        self.assertEqual(actual.base_token, "")
        self.assertEqual(actual.source_mode, "lead-detail")
        self.assertEqual(actual.report_type, "both")

    def test_channel_required_before_any_read(self):
        actual = args()
        actual.channel = ""
        with patch.object(gp, "run_lark") as cli, self.assertRaises(SystemExit):
            gp.prepare(actual)
        cli.assert_not_called()

    def test_process_projection_never_fetches_financial_fields(self):
        fields, _counters = lr.projection(set(lead(1)), "process")
        self.assertFalse(set(fields) & set(lr.RESULT_COUNTERS.values()))
        self.assertNotIn("6h外呼标记", fields)
        with self.assertRaisesRegex(ValueError, "缺少必要字段"):
            lr.projection(set(fields) - {"5min标记"}, "process")

    def test_bottom_quartile_is_ranked_within_each_channel(self):
        records = [lead(1, person="甲", **{"退前线索": 9, "退后线索": 9, "5min标记": 1}),
                   lead(2, person="乙", **{"主管": "主管乙", "5min标记": 1}),
                   lead(3, channel="渠道乙", person="丙", **{"5min标记": 0})]
        actual = report(records)
        self.assertEqual(set(actual["reminders"]["过程数据"]), {"甲", "丙"})
        self.assertEqual(actual["reminder_quotas"]["渠道甲"], {"eligible_count": 2, "quota": 1})
        self.assertAlmostEqual(float(actual["totals"]["5min"].strip("%")), 2 / 11 * 100)
        self.assertEqual(len(actual["rows"]), 3)

    def test_result_counters_negative_net_refunds_and_order_conversion(self):
        records = [lead(1, person="甲", **{"净收款": 100, "当期净收款": 90, "收款": 100,
                                           "报科数": 3, "成交人头": 1, "总通时秒": 120}),
                   lead(2, person="乙", **{"净收款": -200, "退费": 200, "总通时秒": 60})]
        actual = report(records)
        totals = actual["totals"]
        self.assertEqual(totals["单效"], -50)
        self.assertEqual(totals["单效（当期）"], 45)
        self.assertEqual(totals["人均报科"], 3)
        self.assertEqual(totals["订单转化"], "150.00000000%")
        self.assertEqual(totals["退费率"], "200.00000000%")
        self.assertEqual(totals["总通时"], 3)
        self.assertEqual(actual["reminders"]["结果数据"], ["乙"])

    def test_exact_comparison_does_not_round_away_low_consultant(self):
        actual = report([lead(1, **{"净收款": "1.0000000000001"}),
                         lead(2, person="乙", **{"净收款": "1.0000000000002"})])
        self.assertEqual(actual["reminders"]["结果数据"], ["甲"])

    def test_scope_rejects_duplicate_leads_and_mixed_partitions(self):
        for bad in ([lead(1), lead(1)], [lead(1), lead(2, **{"分区小时": "12"})]):
            with self.assertRaises(ValueError):
                lr.validate_scope(bad, "渠道甲", "20260911期")
        with self.assertRaisesRegex(ValueError, "多个期次"):
            lr.validate_scope([lead(1), lead(2, **{"期次": "20260918期"})], "渠道甲", "")

    def test_zero_denominator_excluded_and_placeholders_fail(self):
        actual = report([lead(1, **{"退后线索": 0}), lead(2, person="乙", **{"5min标记": 1})])
        self.assertEqual(actual["reminders"]["过程数据"], ["乙"])
        self.assertEqual(actual["reminder_quotas"]["渠道甲"]["eligible_count"], 1)
        with self.assertRaisesRegex(ValueError, "占位记录"):
            report([lead(1, **{"退前线索": 0, "退后线索": 0})])
        for invalid in (None, "abc", "NaN", "Infinity"):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                report([lead(1, **{"5min标记": invalid})])

    def test_same_name_different_accounts_blocks_even_if_only_one_low(self):
        with self.assertRaisesRegex(ValueError, "同名不同账号"):
            report([lead(1, **{"顾问账号": "a", "5min标记": 0}),
                    lead(2, **{"顾问账号": "b", "5min标记": 1})])

    def test_config_scope_and_conflicting_period_or_chat(self):
        configs = lr.select_configs([config(), config("结果数据")], "渠道甲", "process", "")
        self.assertEqual(list(configs), ["过程数据"])
        self.assertEqual(lr.requested_period(configs, ""), "20260911期")
        with self.assertRaisesRegex(ValueError, "多条配置"):
            lr.select_configs([config(), config()], "渠道甲", "process", "")
        mismatch = lr.select_configs([config(), config("结果数据", **{"推送期次": "20260918期"})], "渠道甲", "both", "")
        with self.assertRaisesRegex(ValueError, "期次不一致"):
            lr.requested_period(mismatch, "")
        configs["过程数据"]["fields"]["接收群"] = [{"id": "oc_a"}]
        self.assertEqual(lr.configured_chat(configs, ""), "oc_a")
        with self.assertRaisesRegex(ValueError, "不一致"):
            lr.configured_chat(configs, "oc_b")

    def test_text_uses_fresh_metrics_and_channel_reminders(self):
        records = [lead(1, **{"5min标记": 1}), lead(2, person="乙")]
        configs = lr.select_configs([config(), config("结果数据")], "渠道甲", "process", "")
        sections = lr.text_sections(configs, report(records, "process"), "20260911期", "渠道甲", ["20260907", "11"])
        fields = sections["过程数据"]["fields"]
        self.assertIn("50.00%", fields["推送说明"])
        self.assertIn("2026-09-07 11:00", fields["推送说明"])
        self.assertNotIn("2小时前", fields["推送说明"])
        self.assertNotIn("净收款", fields["推送说明"])
        self.assertEqual(fields["计算_提醒顾问"], "乙")
        self.assertEqual(fields["提醒"], "本次5min率较低顾问：乙")
        self.assertNotIn("提醒规则", fields["推送说明"])

    def test_simple_message_copy_removes_rules_but_preserves_names_and_mentions(self):
        records = [lead(1, **{"5min标记": 1, "净收款": 100}), lead(2, person="乙")]
        configs = lr.select_configs([
            config(**{"推送说明": "业务说明\n提醒规则：旧规则\n  提醒规则:另一条旧规则"}),
            config("结果数据"),
        ], "渠道甲", "both", "")
        calculated = report(records)
        expected_names = {section: list(names) for section, names in calculated["reminders"].items()}
        sections = lr.text_sections(configs, calculated, "20260911期", "渠道甲", ["20260907", "11"])
        self.assertEqual(sections["过程数据"]["fields"]["提醒"], "本次5min率较低顾问：乙")
        self.assertEqual(sections["结果数据"]["fields"]["提醒"], "本次单效较低顾问：乙")
        self.assertEqual(calculated["reminders"], expected_names)
        self.assertIn("业务说明", sections["过程数据"]["fields"]["推送说明"])
        for section in sections.values():
            self.assertEqual(gp.reminder_names(section), ["乙"])
        markdown = gp.build_markdown([], period="20260911期", source_label="test",
            mention_info={"resolved": {"乙": "ou_test"}}, image_ref=None, text_sections=sections)
        self.assertNotIn("提醒规则", markdown)
        self.assertNotIn("后25%", markdown)
        self.assertNotIn("旧规则", markdown)
        self.assertEqual(markdown.count('<at user_id="ou_test">乙</at>'), 2)

    def test_mentions_none_and_substring_names(self):
        row = {"fields": {"计算_提醒顾问": "王一、王一一", "提醒": "提醒：王一、王一一"}}
        rendered = gp._render_configured_reminder(row, {"王一": "ou_a", "王一一": "ou_b"})
        self.assertEqual(rendered.count("<at "), 2)
        self.assertIn('<at user_id="ou_b">王一一</at>', rendered)
        self.assertEqual(gp.reminder_names({"提醒": "本次单效较低顾问：无"}), [])

    def test_quota_ceil_ties_dimension_order_and_all_zero_still_reminded(self):
        records = [lead(index, person="name%d" % index, **{"主管": "team%d" % (6 - index)}) for index in range(1, 6)]
        actual = report(records)
        self.assertEqual(actual["reminder_quotas"]["渠道甲"], {"eligible_count": 5, "quota": 2})
        # All scores tie: channel|supervisor|name ascending, not source order
        # or name alone; the current Base still chooses a fixed 25% quota.
        for section in ("过程数据", "结果数据"):
            self.assertEqual(actual["reminders"][section], ["name4", "name5"])
        self.assertEqual(actual["reminders"], report(list(reversed(records)))["reminders"])

    def test_same_consultant_different_supervisors_matches_helper_grain(self):
        records = [lead(1, **{"主管": "A"}), lead(2, **{"主管": "B", "5min标记": 1})]
        actual = report(records)
        self.assertEqual(actual["reminder_quotas"]["渠道甲"]["eligible_count"], 2)
        self.assertEqual(actual["reminders"]["过程数据"], ["甲"])

    def test_full_raw_population_does_not_depend_on_helper_rows(self):
        actual = report([lead(i, person="person%02d" % i) for i in range(71)])
        self.assertEqual(actual["reminder_quotas"]["渠道甲"], {"eligible_count": 71, "quota": 18})
        self.assertEqual(len(actual["reminders"]["过程数据"]), 18)
        self.assertEqual(len(actual["reminders"]["结果数据"]), 18)

    def test_delivery_identity_changes_idempotency(self):
        coords = {"base_token": "b", "table_id": "t", "view_id": "v"}
        base = {"channel": "甲", "report_type": "both", "snapshot": ["1", "2"], "markdown": "plain", "identity": "user"}
        initial = gp.idempotency_key(coords, "c", "p", [], delivery=base)
        self.assertEqual(initial, gp.idempotency_key(coords, "c", "p", [], delivery=dict(base)))
        for key in base:
            changed = {**base, key: "changed"}
            self.assertNotEqual(initial, gp.idempotency_key(coords, "c", "p", [], delivery=changed))


class FetchAndPrepareTests(unittest.TestCase):
    def test_config_read_projects_only_the_seven_retained_fields(self):
        coords = {"base_token": "b", "table_id": "config", "view_id": "v"}
        expected = ("配置名称", "渠道", "推送类型", "推送标题", "推送期次", "推送说明", "接收群")
        self.assertEqual(lr.CONFIG_FIELDS, expected)
        with patch.object(gp, "resolve_coordinates", return_value=coords), patch.object(gp, "_fetch_view_records", return_value=[]) as fetch:
            self.assertEqual(gp._read_channel_configs(args()), (coords, []))
        self.assertEqual(fetch.call_args.args[2], expected)
        self.assertEqual(fetch.call_args.args[0]["view_id"], "v")

    def test_lean_base_preserves_report_and_does_not_report_missing_cached_names(self):
        records = [lead(1, **{"5min标记": 1, "净收款": 100}), lead(2, person="乙")]
        coords = {"base_token": "b", "table_id": "config", "view_id": "v"}
        legacy = [config(), config("结果数据")]
        lean = [{k: v for k, v in row.items() if k in lr.CONFIG_FIELDS or k == "record_id"} for row in legacy]
        contexts = []
        for configs in (legacy, lean):
            with patch.object(gp, "_read_channel_configs", return_value=(coords, configs)), patch.object(gp, "_fetch_view_records", return_value=records), patch.object(gp, "run_lark", return_value=json.dumps({"fields": [{"field_name": key} for key in records[0]]})):
                contexts.append(gp.prepare(args()))
        for key in ("markdown", "period", "rows", "result_rows", "totals", "reminder_quotas", "idempotency_key"):
            self.assertEqual(contexts[0][key], contexts[1][key], key)
        self.assertEqual(contexts[1]["config_reminder_check"], {})
        self.assertIn("本次5min率较低顾问：乙", contexts[1]["markdown"])
        self.assertIn("本次单效较低顾问：乙", contexts[1]["markdown"])
        self.assertNotIn("<at", contexts[1]["markdown"])

    def test_names_only_prepare_has_no_identity_lookup_or_membership_dependency(self):
        records = [lead(1, **{"5min标记": 1}), lead(2, person="乙")]
        coords = {"base_token": "b", "table_id": "config", "view_id": "v"}
        for mode in lr.SECTIONS:
            parser = argparse.ArgumentParser()
            gp.add_common_arguments(parser)
            # Explicit legacy names-only settings no longer depend on new defaults.
            parsed = parser.parse_args([
                "--report-profile", "standard", "--chat-id", "oc_legacy_test", "--no-mentions",
                "--channel", "渠道甲", "--report-type", mode, "--no-image",
                "--mention-target", "supervisor", "--strict-mentions", "--require-mention-membership",
                "--mention-map", "nonexistent-old-mention-map.json",
            ])
            with self.subTest(mode=mode), patch.object(gp, "_read_channel_configs", return_value=(coords, [config(), config("结果数据")])), patch.object(gp, "_fetch_view_records", return_value=records), patch.object(gp, "run_lark", return_value=json.dumps({"fields": [{"field_name": key} for key in records[0]]})) as cli, patch.object(gp, "_load_mention_map", side_effect=AssertionError("No mapping should be loaded")) as mappings, patch.object(gp, "mention_nonmembers", side_effect=AssertionError("No membership lookup should run")) as membership:
                actual = gp.prepare(parsed)
            self.assertEqual(actual["mention_target"], "none")
            self.assertEqual(actual["mention_info"]["resolved"], {})
            self.assertEqual(actual["mention_info"]["unresolved"], [])
            self.assertEqual(actual["mention_info"]["ambiguous"], {})
            self.assertNotIn("<at", actual["markdown"])
            self.assertNotIn("请主管关注", actual["markdown"])
            self.assertIn("较低顾问：乙", actual["markdown"])
            self.assertEqual(actual["raw_count"], 2)
            self.assertTrue(all(call.args[0][:2] == ["base", "+field-list"] for call in cli.call_args_list))
            mappings.assert_not_called()
            membership.assert_not_called()

    def test_legacy_view_also_ignores_stale_mention_flags_in_names_only_mode(self):
        coords = {"base_token": "b", "table_id": "t", "view_id": "v"}
        sections = {"过程数据": {"record_id": "r", "fields": {
            "推送标题": "过程", "推送期次": "20260911期", "计算_提醒顾问": "乙",
            "提醒": "本次5min率较低顾问：乙", "_mention_target": "supervisor", "_reminder_supervisors": ["主管甲"],
        }}}
        parsed = args("--source-mode", "summary-view", "--mention-target", "supervisor",
                      "--strict-mentions", "--require-mention-membership", "--mention-map", "missing-map.json")
        with patch.object(gp, "resolve_coordinates", return_value=coords), patch.object(gp, "fetch_records", return_value=[]), patch.object(gp, "select_period", return_value="20260911期"), patch.object(gp, "select_rows", return_value=[]), patch.object(gp, "fetch_result_records", return_value=[]), patch.object(gp, "aggregate_result_rows", return_value=[]), patch.object(gp, "resolve_text_coordinates", return_value=coords), patch.object(gp, "fetch_text_records", return_value=[]), patch.object(gp, "select_text_config", return_value=sections), patch.object(gp, "_load_mention_map", side_effect=AssertionError("No map")), patch.object(gp, "run_lark", side_effect=AssertionError("No CLI")):
            actual = gp.prepare(parsed)
        self.assertEqual(actual["mention_target"], "none")
        self.assertIn("本次5min率较低顾问：乙", actual["markdown"])
        self.assertNotIn("<at", actual["markdown"])
        self.assertNotIn("请主管关注", actual["markdown"])

    def test_pagination_uses_manifest_offset_and_proves_final_page(self):
        manifests = [{"has_more": True, "records_count": 1, "rev": 8, "next_offset": 2000, "query_context": {"filter": "x"}},
                     {"has_more": False, "records_count": 1, "rev": 8, "query_context": {"filter": "x"}}]
        offsets = []
        def fake(command, cwd, timeout):
            offsets.append(command[command.index("--offset") + 1])
            page = Path(cwd) / command[command.index("--output") + 1]
            page.write_text(json.dumps({"record_id": "r" + str(len(offsets)), "渠道": "甲"}), encoding="utf-8")
            self.assertIn("--filter-json", command)
            self.assertNotIn("--view-id", command)
            return json.dumps(manifests[len(offsets) - 1])
        audit = {}
        with patch.object(gp, "run_lark", side_effect=fake):
            rows = gp._fetch_view_records({"base_token": "b", "table_id": "t"}, args(), ["渠道"], temp_prefix="test-pages-", filter_json={"logic": "and", "conditions": [["渠道", "==", "甲"]]}, audit=audit)
        self.assertEqual(offsets, ["0", "2000"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(audit["pages"], 2)
        self.assertFalse(audit["has_more"])

    def test_malformed_or_drifting_manifest_rejected(self):
        for bad in ({"records_count": 1}, {"has_more": False, "records_count": 3},
                    {"has_more": False, "records_count": 1, "rev": 9},
                    {"has_more": False, "records_count": 1, "rev": 8, "query_context": "changed"}):
            calls = []
            def fake(command, cwd, timeout):
                calls.append(command)
                (Path(cwd) / command[command.index("--output") + 1]).write_text(json.dumps({"record_id": str(len(calls))}), encoding="utf-8")
                return json.dumps({"has_more": True, "records_count": 1, "rev": 8, "next_offset": 2000} if len(calls) == 1 else bad)
            with self.subTest(manifest=bad), patch.object(gp, "run_lark", side_effect=fake), self.assertRaises(RuntimeError):
                gp._fetch_view_records({"base_token": "b", "table_id": "t"}, args(), [], temp_prefix="test-bad-")

    def test_prepare_modes_use_only_selected_channel_snapshot(self):
        records = [lead(1, **{"5min标记": 1}), lead(2, person="乙")]
        coords = {"base_token": "b", "table_id": "config", "view_id": "v"}
        for mode, sections in lr.SECTIONS.items():
            captures = []
            def fetch(source, parsed, fields, **kwargs):
                captures.append((source, fields, kwargs))
                kwargs["audit"].update({"pages": 1, "rev": 1, "has_more": False})
                return [{k: v for k, v in r.items() if k in fields or k == "record_id"} for r in records]
            with self.subTest(mode=mode), patch.object(gp, "_read_channel_configs", return_value=(coords, [config(), config("结果数据")])), patch.object(gp, "run_lark", return_value=json.dumps({"fields": [{"field_name": key} for key in records[0]]})), patch.object(gp, "_fetch_view_records", side_effect=fetch):
                actual = gp.prepare(args("--report-type", mode))
            self.assertEqual(tuple(actual["text_sections"]), sections)
            self.assertEqual(actual["raw_count"], 2)
            self.assertEqual(actual["reminder_rule"], "同一期次、所属渠道后25%")
            self.assertEqual(captures[0][2]["filter_json"]["conditions"], [["渠道", "==", "渠道甲"], ["期次", "==", "20260911期"]])
            self.assertEqual(captures[0][0]["view_id"], "")
            if mode == "process":
                self.assertFalse(set(captures[0][1]) & set(lr.RESULT_COUNTERS.values()))
                self.assertNotIn("净收款", actual["markdown"])
                self.assertNotIn("结果数据", actual["markdown"])
            if mode == "result":
                self.assertEqual(actual["rows"], [])

    def test_all_channel_images_keep_visible_scope_and_unique_preview_files(self):
        records = [lead(1), lead(2, channel="渠道乙", person="乙")]
        coords = {"base_token": "b", "table_id": "config", "view_id": "v"}
        def fetch(source, parsed, fields, **kwargs):
            self.assertNotIn(["渠道", "==", "全部渠道"], (kwargs.get("filter_json") or {}).get("conditions", []))
            kwargs["audit"].update({"rev": 1, "pages": 1, "has_more": False})
            return [{k: v for k, v in r.items() if k in fields or k == "record_id"} for r in records]
        for mode in lr.SECTIONS:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                parsed = args("--report-type", mode, "--state-dir", directory)
                parsed.channel = "全部渠道"
                parsed.with_image = True
                with patch.object(gp, "_read_channel_configs", return_value=(coords, [])), patch.object(gp, "run_lark", return_value=json.dumps({"fields": [{"field_name": key} for key in records[0]]})), patch.object(gp, "_fetch_view_records", side_effect=fetch):
                    first = gp.prepare(parsed)
                    second = gp.prepare(parsed)
                self.assertEqual(first["idempotency_key"], second["idempotency_key"])
                for path_field, columns_field, enabled in (("image_path", "image_columns", mode != "result"), ("result_image_path", "result_image_columns", mode != "process")):
                    path = first[path_field]
                    if enabled:
                        self.assertTrue(path.exists())
                        self.assertNotEqual(path, second[path_field])
                        self.assertIn("渠道", [source for source, _label, _kind in first[columns_field]])
                        self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))
                    else:
                        self.assertIsNone(path)

    def test_dry_run_or_missing_message_id_keeps_images(self):
        for dry_run in (True, False):
            with self.subTest(dry_run=dry_run), tempfile.TemporaryDirectory() as directory:
                paths = [Path(directory) / (name + ".png") for name in ("process", "result")]
                for path in paths:
                    path.write_bytes(b"fixture")
                context = {"mention_info": {"lookup_error": "", "unresolved": [], "ambiguous": {}},
                           "chat_id": "oc_test", "markdown": "![p](img_process_preview)\n![r](img_result_preview)",
                           "idempotency_key": "key", "identity": "user", "image_path": paths[0],
                           "result_image_path": paths[1], "ledger": Path(directory) / "ledger.jsonl", "period": "period"}
                def send(*call_args, **kwargs):
                    self.assertTrue(all(path.exists() for path in paths))
                    return {} if not dry_run else {"dry_run": True}
                with patch.object(gp, "prepare", return_value=context), patch.object(gp, "print_preview"), patch.object(gp, "upload_image", side_effect=["img_process_real", "img_result_real"]) as upload, patch.object(gp, "send_markdown", side_effect=send), redirect_stdout(io.StringIO()):
                    if dry_run:
                        self.assertEqual(gp.main(["send", "--dry-run"]), 0)
                        upload.assert_not_called()
                    else:
                        with self.assertRaisesRegex(RuntimeError, "message_id"):
                            gp.main(["send", "--confirm-send"])
                self.assertTrue(all(path.exists() for path in paths))

    def test_live_mock_replaces_exact_image_keys_before_deleting(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / (name + ".png") for name in ("process", "result")]
            for path in paths:
                path.write_bytes(b"fixture")
            context = {"mention_info": {"lookup_error": "", "unresolved": [], "ambiguous": {}},
                       "chat_id": "oc_test", "markdown": "![p](img_process_preview)\n![r](img_result_preview)",
                       "idempotency_key": "key", "identity": "user", "image_path": paths[0],
                       "result_image_path": paths[1], "ledger": Path(directory) / "ledger.jsonl", "period": "period"}
            def send(_chat, markdown, *call_args, **kwargs):
                self.assertTrue(all(path.exists() for path in paths))
                self.assertEqual(markdown, "![p](img_process_real)\n![r](img_result_real)")
                return {"message_id": "om_mock"}
            with patch.object(gp, "prepare", return_value=context), patch.object(gp, "upload_image", side_effect=["img_process_real", "img_result_real"]), patch.object(gp, "send_markdown", side_effect=send), redirect_stdout(io.StringIO()):
                self.assertEqual(gp.main(["send", "--confirm-send"]), 0)
            self.assertFalse(any(path.exists() for path in paths))


if __name__ == "__main__":
    unittest.main()
