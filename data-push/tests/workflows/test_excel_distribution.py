from argparse import Namespace
import io
from contextlib import redirect_stdout
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

import excel_split_send as compatibility
from lark_delivery.workflows import excel_distribution as excel


class ExcelWorkflowTests(unittest.TestCase):
    def test_compatibility_entry_is_the_same_implementation(self):
        self.assertIs(compatibility, excel)

    def test_exact_recipient_only_and_no_guessing_duplicates(self):
        for names, expected in ((["张三"], "ou_0"), (["张三", "张三"], None), (["张三1"], None)):
            users = [{"localized_name": name, "open_id": f"ou_{i}"} for i, name in enumerate(names)]
            with patch.object(excel, "run_lark", return_value=json.dumps({"ok": True, "data": {"users": users}})):
                self.assertEqual(excel.resolve_user("张三")[0], expected)

    def test_dry_run_performs_no_send(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "张三.xlsx").touch()
            args = Namespace(dir=directory, strip_digits=False, dry_run=True, message=None)
            with patch.object(excel, "resolve_user", return_value=("ou_test", None)), patch.object(excel, "run_lark") as cli, redirect_stdout(io.StringIO()):
                excel.cmd_send(args)
            cli.assert_not_called()
