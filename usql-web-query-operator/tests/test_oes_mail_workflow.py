from __future__ import annotations

from datetime import date, datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _shared.config import DEFAULT_STATE
from _shared.errors import UsageError
from oes_achievement.board import inspect_range, query_all
from oes_achievement.cli import build_parser
from oes_achievement.mailbox import ExportMail, matching_mails, open_outlook_session, parse_mail_count, parse_timestamp
from oes_achievement.workflow import exclusive_workflow_lock, resolve_job_options, run_pipeline, wait_for_attachment
from oes_achievement.workbook import SKILLS_ROOT, file_info, validate_output_dir, verify_xlsx


def native_workbook(rows=None, *, stale_dimension=False):
    from openpyxl import Workbook
    book = Workbook()
    sheet = book.active
    sheet.append(["订单号", "班级bizNumber", "userId", "业绩金额"])
    for row in rows or [("order1", "class1", "user1", 12.50), ("order1", "class1", "user1", -2.50)]:
        sheet.append(row)
    target = BytesIO()
    book.save(target)
    book.close()
    if not stale_dimension:
        return target.getvalue()
    output = BytesIO()
    with zipfile.ZipFile(target) as source, zipfile.ZipFile(output, "w") as dest:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == "xl/worksheets/sheet1.xml":
                data = re.sub(br'<dimension ref="[^"]+"', b'<dimension ref="A1"', data)
            dest.writestr(item, data)
    return output.getvalue()


QUERY_ROWS = [
    {"id": 1, "orderNumber": "order1", "clazzBizNumber": "class1", "userId": "user1", "price": "12.50"},
    {"id": 2, "orderNumber": "order1", "clazzBizNumber": "class1", "userId": "user1", "price": "-2.50"},
]


class MailMatchingTests(unittest.TestCase):
    def test_mail_count_preserves_thousands_groups(self):
        self.assertEqual(parse_mail_count("数据总条数总数：3,676 详情请见附件"), 3676)
        self.assertEqual(parse_mail_count("数据总条数总数：10，986 详情请见附件"), 10986)
        self.assertEqual(parse_mail_count("数据总条数总数：52 详情请见附件"), 52)
        with self.assertRaisesRegex(UsageError, "invalid thousands"):
            parse_mail_count("数据总条数总数：12,34")
    def test_old_same_minute_message_is_excluded_by_baseline(self):
        received = datetime(2026, 10, 4, 7, 1, tzinfo=timezone.utc)
        old = ExportMail("old", "gtkt-lvyue", "20261003业绩数据明细导出", received)
        new = ExportMail("new", "gtkt-lvyue", old.subject, received)
        result = matching_mails([old, new], received_after=received.replace(second=21), excluded_hashes={old.identity_hash})
        self.assertEqual(result, [new])
        self.assertNotIn("old", repr(old))

    def test_mail_time_bounds_and_exact_subject(self):
        now = datetime(2026, 10, 4, 7, 1, tzinfo=timezone.utc)
        mails = [ExportMail("a", "sender", "wanted", now), ExportMail("b", "sender", "other", now)]
        self.assertEqual(len(matching_mails(mails, received_after=now, exact_subject="wanted")), 1)
        self.assertEqual(matching_mails(mails, received_after=now.replace(hour=8)), [])
        self.assertEqual(matching_mails(mails, received_after=now.replace(hour=6), received_before=now.replace(hour=6)), [])

    def test_mail_timestamps_require_timezone(self):
        with self.assertRaises(UsageError):
            parse_timestamp("2026-10-04T15:01:00")
        self.assertEqual(parse_timestamp("2026-10-04T15:01:00+08:00").hour, 7)

    def test_outlook_cannot_overwrite_usql_state(self):
        with self.assertRaisesRegex(UsageError, "isolated runtime"):
            open_outlook_session(None, SimpleNamespace(mail_state_path=DEFAULT_STATE))

    def test_ambiguous_same_count_mails_are_not_downloaded(self):
        now = datetime.now(timezone.utc)
        mails = [ExportMail("a", "sender", "subject", now), ExportMail("b", "sender", "subject", now)]
        args = SimpleNamespace(wait_seconds=0, mail_sender="sender", mail_subject_contains="subject", scan_pages=1)
        with patch("oes_achievement.workflow.list_export_mails", return_value=mails), \
             patch("oes_achievement.workflow.read_export_mail", return_value=(2, [Mock()])), \
             patch("oes_achievement.workflow.download_attachment") as download:
            with self.assertRaisesRegex(UsageError, "Multiple new"):
                wait_for_attachment(Mock(), args, received_after=now, expected_count=2, query_rows=QUERY_ROWS, output_dir=Path("unused"))
            download.assert_not_called()

    def test_latest_cannot_guess_between_equal_minute_timestamps(self):
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        mails = [ExportMail("a", "sender", "subject", now), ExportMail("b", "sender", "subject", now)]
        args = SimpleNamespace(wait_seconds=0, mail_sender="sender", mail_subject_contains="subject", scan_pages=1, latest=True)
        with patch("oes_achievement.workflow.list_export_mails", return_value=mails), \
             patch("oes_achievement.workflow.read_export_mail", return_value=(2, [Mock()])):
            with self.assertRaisesRegex(UsageError, "cannot disambiguate"):
                wait_for_attachment(Mock(), args, received_after=now, expected_count=2, query_rows=QUERY_ROWS, output_dir=Path("unused"))


class WorkbookVerificationTests(unittest.TestCase):
    def test_native_a1_dimension_is_ignored_and_duplicate_orders_are_preserved(self):
        result = verify_xlsx(native_workbook(stale_dimension=True), 2, QUERY_ROWS)
        self.assertEqual(result["row_count"], 2)
        self.assertTrue(result["order_numbers_verified"])
        self.assertEqual(result["reconciled_fields"], ["orderNumber", "clazzBizNumber", "userId", "price"])

    def test_wrong_count_and_order_are_rejected(self):
        with self.assertRaisesRegex(UsageError, "row count mismatch"):
            verify_xlsx(native_workbook(), 3)
        changed = [dict(row, orderNumber="wrong") for row in QUERY_ROWS]
        with self.assertRaisesRegex(UsageError, "order numbers differ"):
            verify_xlsx(native_workbook(), 2, changed)

    def test_same_orders_with_changed_amount_are_rejected(self):
        changed = [dict(row, price="99.00") for row in QUERY_ROWS]
        with self.assertRaisesRegex(UsageError, "amounts differ"):
            verify_xlsx(native_workbook(), 2, changed)

    def test_html_download_is_rejected(self):
        with self.assertRaisesRegex(UsageError, "not a readable XLSX"):
            verify_xlsx(b"<html>login required</html>", 2)

    def test_downloads_cannot_be_written_in_any_skill(self):
        with self.assertRaisesRegex(UsageError, "outside the skills"):
            validate_output_dir(SKILLS_ROOT / "another-skill" / "data")


class QueryCompletenessTests(unittest.TestCase):
    def test_range_probe_reports_limit_without_native_export(self):
        body = {"code": 0, "data": {"attribution": [QUERY_ROWS[0]]}, "pager": {"count": 20305}}
        with patch("oes_achievement.board._post_json", return_value=body) as request:
            result = inspect_range(None, date(2026, 4, 7), date(2026, 10, 3), 100)
        self.assertEqual(result["days_inclusive"], 180)
        self.assertFalse(result["native_export_complete_possible"])
        self.assertFalse(result["export_requested"])
        self.assertEqual(request.call_args.args[2]["pager"]["pageSize"], 1)

    def test_pager_drift_and_duplicate_rows_are_rejected(self):
        for responses, message in ((
            [{"code": 0, "data": {"attribution": [QUERY_ROWS[0]]}, "pager": {"count": 2}},
             {"code": 0, "data": {"attribution": [QUERY_ROWS[1]]}, "pager": {"count": 3}}], "changed during pagination"), (
            [{"code": 0, "data": {"attribution": [QUERY_ROWS[0], QUERY_ROWS[0]]}, "pager": {"count": 2}}], "duplicate row IDs")):
            with self.subTest(message=message), patch("oes_achievement.board._post_json", side_effect=responses):
                with self.assertRaisesRegex(UsageError, message):
                    query_all(None, date(2026, 10, 1), date(2026, 10, 3), page_size=1, timeout_ms=100)

    def test_missing_count_is_not_treated_as_verified_empty(self):
        with patch("oes_achievement.board._post_json", return_value={"code": 0, "data": {"attribution": []}}):
            with self.assertRaisesRegex(UsageError, "pager/count"):
                query_all(None, date(2026, 10, 1), date(2026, 10, 3), page_size=1, timeout_ms=100)


class JobConfigurationTests(unittest.TestCase):
    def test_rolling_range_uses_complete_days_ending_yesterday(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "job.json"
            config.write_text(json.dumps({"schema_version": 1, "date_filter": {"mode": "rolling_days", "lookback_days": 3}}), encoding="utf-8")
            args = build_parser().parse_args(["export-and-download", "--config-file", str(config), "--output-dir", tmp, "--run-key", "scheduled"])
            self.assertEqual(resolve_job_options(args, today=date(2026, 10, 4)), (date(2026, 10, 1), date(2026, 10, 3)))

    def test_long_rolling_range_has_no_artificial_366_day_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "job.json"
            config.write_text(json.dumps({"schema_version": 1, "date_filter": {"mode": "rolling_days", "lookback_days": 730}}), encoding="utf-8")
            args = build_parser().parse_args(["export-and-download", "--config-file", str(config), "--output-dir", tmp, "--run-key", "long"])
            self.assertEqual(resolve_job_options(args, today=date(2026, 10, 4)), (date(2024, 10, 4), date(2026, 10, 3)))

    def test_unknown_fields_and_mixed_date_sources_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "job.json"
            for body, extra in (({"schema_version": 1, "password": "unused"}, []),
                                ({"schema_version": 1, "date_filter": {"mode": "previous_day"}}, ["--date", "2026-10-03"])):
                config.write_text(json.dumps(body), encoding="utf-8")
                args = build_parser().parse_args(["export-and-download", "--config-file", str(config), "--output-dir", tmp, "--run-key", "scheduled", *extra])
                with self.assertRaises(UsageError):
                    resolve_job_options(args)


class ResumableWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.args = build_parser().parse_args(["export-and-download", "--date", "2026-10-03", "--output-dir", str(self.root / "output"), "--run-key", "stable", "--wait-seconds", "0"])
        self.start, self.end = resolve_job_options(self.args)
        self.oes = Mock()
        self.mail = Mock()
        patches = {
            "OES_RUNTIME_DIR": self.root / "runtime", "open_session": Mock(return_value=self.oes),
            "open_outlook_session": Mock(return_value=self.mail), "query_all": Mock(return_value=(QUERY_ROWS, 2, [])),
            "inspect_range": Mock(return_value={"row_count": 2}),
            "list_export_mails": Mock(return_value=[]), "request_native_export": Mock(return_value={"code": 0}),
            "wait_for_attachment": Mock(side_effect=self.fake_download),
        }
        self.mocks = patches
        for name, value in patches.items():
            item = patch("oes_achievement.workflow." + name, value)
            item.start()
            self.addCleanup(item.stop)

    def fake_download(self, session, args, **kwargs):
        path = kwargs["output_dir"] / "native.xlsx"
        path.write_bytes(native_workbook())
        return {"file": file_info(path), "verification": {"row_count": 2}}

    def test_completed_run_is_reused_without_login_query_or_export(self):
        first = run_pipeline(None, self.args, self.start, self.end)
        second = run_pipeline(None, self.args, self.start, self.end)
        self.assertEqual(first["status"], "completed")
        self.assertTrue(second["reused_completed_run"])
        for name in ("open_session", "open_outlook_session", "query_all", "request_native_export"):
            self.assertEqual(self.mocks[name].call_count, 1)

    def test_mail_timeout_resumes_without_second_native_export(self):
        self.mocks["wait_for_attachment"].side_effect = UsageError("Mail deadline")
        with self.assertRaisesRegex(UsageError, "same --run-key"):
            run_pipeline(None, self.args, self.start, self.end)
        self.mocks["wait_for_attachment"].side_effect = self.fake_download
        result = run_pipeline(None, self.args, self.start, self.end)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(self.mocks["request_native_export"].call_count, 1)
        self.assertEqual(self.mocks["query_all"].call_count, 1)

    def test_submission_can_resume_without_waiting_or_exporting_twice(self):
        self.args.submit_only = True
        first = run_pipeline(None, self.args, self.start, self.end)
        repeated = run_pipeline(None, self.args, self.start, self.end)
        self.assertEqual(first["status"], "waiting_for_mail")
        self.assertEqual(repeated["status"], "waiting_for_mail")
        self.mocks["wait_for_attachment"].assert_not_called()
        self.assertEqual(self.mocks["open_outlook_session"].call_count, 1)
        self.args.submit_only = False
        result = run_pipeline(None, self.args, self.start, self.end)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(self.mocks["request_native_export"].call_count, 1)
        self.assertEqual(self.mocks["query_all"].call_count, 1)

    def test_uncertain_export_is_not_automatically_resubmitted(self):
        self.mocks["request_native_export"].side_effect = TimeoutError("network")
        with self.assertRaisesRegex(UsageError, "uncertain"):
            run_pipeline(None, self.args, self.start, self.end)
        with self.assertRaisesRegex(UsageError, "No automatic resubmission"):
            run_pipeline(None, self.args, self.start, self.end)
        self.assertEqual(self.mocks["request_native_export"].call_count, 1)

    def test_changed_download_and_rebound_dates_are_rejected(self):
        result = run_pipeline(None, self.args, self.start, self.end)
        with self.assertRaisesRegex(UsageError, "another date range"):
            run_pipeline(None, self.args, date(2026, 10, 1), self.end)
        Path(result["mail_download"]["file"]["path"]).write_bytes(b"changed")
        with self.assertRaisesRegex(UsageError, "moved or changed"):
            run_pipeline(None, self.args, self.start, self.end)
        self.assertEqual(self.mocks["request_native_export"].call_count, 1)

    def test_empty_or_truncated_query_never_requests_native_export(self):
        self.mocks["query_all"].return_value = ([], 0, [])
        self.assertEqual(run_pipeline(None, self.args, self.start, self.end)["status"], "completed_no_data")
        self.args.run_key = "oversized"
        self.mocks["query_all"].return_value = ([], 10001, [])
        self.mocks["inspect_range"].return_value = {"row_count": 10001}
        with self.assertRaisesRegex(UsageError, "limited to 10000"):
            run_pipeline(None, self.args, self.start, self.end)
        self.mocks["request_native_export"].assert_not_called()
        self.mocks["open_outlook_session"].assert_not_called()

    def test_exclusive_lock_releases_after_scope_exit(self):
        path = self.root / "lock"
        with exclusive_workflow_lock(path):
            with self.assertRaisesRegex(UsageError, "Another OES"):
                with exclusive_workflow_lock(path):
                    self.fail("Concurrent workflow acquired the lock")
        with exclusive_workflow_lock(path):
            pass


if __name__ == "__main__":
    unittest.main()
