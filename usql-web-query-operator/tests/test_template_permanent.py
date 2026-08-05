from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.commands.apply_template_creation import validate_apply_request  # noqa: E402
from usql_web_query.commands.publish_template import validate_publish_request  # noqa: E402
from usql_web_query.template_permanent import (  # noqa: E402
    CREATE_RECEIPT_OPERATION,
    UPDATE_PLAN_OPERATION,
    UPDATE_RECEIPT_OPERATION,
    PLAN_SCHEMA_VERSION,
    PermanentTemplateCreationPlan,
    build_permanent_template_plan,
    load_create_receipt,
    template_params_for_save,
    verify_template_readback,
    write_receipt,
)
from usql_web_query.template_query import (  # noqa: E402
    TemplateQueryClient,
    parse_template_row,
)


SQL = """select
  owner_name as \"tmk顾问姓名\",
  user_id as \"用户id\"
from example.table_name
where assign_day >= ${day:1}
  and assign_day < ${day:2}
"""

PARSER_PAYLOAD = {
    "templateVariable": [
        {
            "name": "tmk顾问姓名",
            "showName": "tmk顾问姓名",
            "attribute": 2,
            "type": "varchar",
        },
        {
            "name": "用户id",
            "showName": "用户id",
            "attribute": 2,
            "type": "bigint",
        },
    ],
    "templateParam": [
        {"name": "day:1", "showName": "day:1", "type": "varchar", "condition": ">="},
        {"name": "day:2", "showName": "day:2", "type": "varchar", "condition": "<"},
    ],
    "tableName": ["example.table_name"],
}

PARAMETER_CONFIG = {
    "day:1": {
        "showName": "维护日期开始",
        "mode": "date",
        "mandatory": 2,
        "format": "yyyy-MM-dd",
    },
    "day:2": {
        "showName": "维护日期结束",
        "mode": "date",
        "mandatory": 2,
        "format": "yyyy-MM-dd",
    },
}


def build_plan(**overrides: Any) -> PermanentTemplateCreationPlan:
    values: dict[str, Any] = {
        "template_name": "测试参数模板",
        "description": "测试",
        "owner": "",
        "creator": "tester01",
        "sql_file": Path("template.sql"),
        "sql_text": SQL,
        "instance_key": "dlc_presto",
        "existing_template_ids": [],
        "parser_payload": PARSER_PAYLOAD,
        "parameter_config": PARAMETER_CONFIG,
        "variable_display_names": {
            "tmk顾问姓名": "TMK顾问姓名",
            "用户id": "用户ID",
        },
        "created_at": datetime(2026, 8, 3, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return build_permanent_template_plan(**values)


def detail_for(plan: PermanentTemplateCreationPlan, *, status: int) -> dict[str, Any]:
    params = []
    for row in plan.template_params:
        item = dict(row)
        item.update({"id": 1, "templateId": 42, "selected": False})
        params.append(item)
    variables = []
    for row in plan.template_variables:
        item = dict(row)
        item.update({"id": 1, "templateId": 42, "mandatory": 0})
        variables.append(item)
    return {
        "id": 42,
        "name": plan.template_name,
        "status": status,
        "sqlDetail": SQL,
        "instanceKey": plan.instance_key,
        "templateVariable": variables,
        "templateParam": params,
        "tableName": list(plan.table_names),
    }


class PermanentTemplatePlanTests(unittest.TestCase):
    def test_ready_plan_binds_date_params_labels_parser_and_metadata(self) -> None:
        plan = build_plan()
        self.assertEqual(plan.status, "ready")
        self.assertEqual(plan.baseline_template_ids, ())
        self.assertEqual(plan.template_variables[0]["showName"], "TMK顾问姓名")
        self.assertEqual(plan.template_variables[1]["showName"], "用户ID")
        self.assertEqual(
            [(item["showName"], item["paramType"], item["format"], item["mandatory"]) for item in plan.template_params],
            [
                ("维护日期开始", 3, "yyyy-MM-dd", 2),
                ("维护日期结束", 3, "yyyy-MM-dd", 2),
            ],
        )
        self.assertTrue(plan.sql_policy["allowed"])
        self.assertEqual(plan.plan_sha256, plan.computed_sha256())

    def test_plan_round_trip_rejects_tampering(self) -> None:
        plan = build_plan()
        restored = PermanentTemplateCreationPlan.from_json(plan.to_json())
        self.assertEqual(restored.plan_sha256, plan.plan_sha256)
        payload = plan.to_json()
        payload["template_name"] = "changed"
        with self.assertRaisesRegex(UsageError, "hash is invalid"):
            PermanentTemplateCreationPlan.from_json(payload)

    def test_duplicate_name_and_incomplete_config_block_plan(self) -> None:
        plan = build_plan(existing_template_ids=[99], parameter_config={"day:1": PARAMETER_CONFIG["day:1"]})
        self.assertEqual(plan.status, "blocked")
        codes = {item["code"] for item in plan.diagnostics}
        self.assertIn("TEMPLATE_NAME_ALREADY_EXISTS", codes)
        self.assertIn("MISSING_PARAMETER_CONFIG", codes)

    def test_update_plan_allows_exact_existing_target_and_preserves_id(self) -> None:
        plan = build_plan(
            existing_template_ids=[42],
            target_template_id=42,
            baseline_state={"id": 42, "name": "测试参数模板", "status": 2, "sql_sha256": "old"},
        )
        self.assertEqual(plan.status, "ready")
        self.assertEqual(plan.operation, UPDATE_PLAN_OPERATION)
        self.assertEqual(plan.policy["target_template_id"], 42)
        self.assertTrue(plan.policy["preserve_existing_template_id_and_access"])

    def test_update_plan_blocks_missing_exact_target(self) -> None:
        plan = build_plan(
            existing_template_ids=[99],
            target_template_id=42,
            baseline_state={"id": 42, "name": "测试参数模板", "status": 2},
        )
        self.assertEqual(plan.status, "blocked")
        self.assertIn("TARGET_TEMPLATE_NOT_FOUND", {item["code"] for item in plan.diagnostics})

    def test_one_parameter_can_be_reused_in_multiple_predicates(self) -> None:
        sql = SQL.replace(
            "  and assign_day < ${day:2}",
            "  and coalesce(other_day, assign_day) >= ${day:1}\n  and assign_day < ${day:2}",
        )
        plan = build_plan(sql_text=sql)
        self.assertEqual(plan.status, "ready")
        self.assertEqual([item["name"] for item in plan.template_params], ["day:1", "day:2"])

    def test_non_query_sql_is_blocked_before_browser_apply(self) -> None:
        plan = build_plan(sql_text="delete from example.table_name where id = ${day:1}")
        self.assertEqual(plan.status, "blocked")
        self.assertIn("SQL_POLICY_BLOCKED", {item["code"] for item in plan.diagnostics})

    def test_date_save_payload_omits_parser_condition_and_type(self) -> None:
        params = template_params_for_save(build_plan().template_params)
        self.assertEqual(params[0]["paramType"], 3)
        self.assertEqual(params[0]["format"], "yyyy-MM-dd")
        self.assertNotIn("condition", params[0])
        self.assertNotIn("type", params[0])

    def test_readback_requires_exact_status_sql_and_metadata(self) -> None:
        plan = build_plan()
        verified = verify_template_readback(detail_for(plan, status=1), plan, expected_status=1)
        self.assertTrue(verified["verified"])
        self.assertEqual(verified["parameter_count"], 2)
        drifted = detail_for(plan, status=1)
        drifted["templateParam"][0]["showName"] = "changed"
        with self.assertRaisesRegex(UsageError, "metadata hash mismatch"):
            verify_template_readback(drifted, plan, expected_status=1)


class PermanentTemplateAuthorizationTests(unittest.TestCase):
    def test_apply_requires_confirmation_and_exact_plan_hash(self) -> None:
        plan = build_plan()
        args = argparse.Namespace(confirm_production_write=False, expected_plan_sha256=plan.plan_sha256)
        with self.assertRaisesRegex(UsageError, "confirm-production-write"):
            validate_apply_request(args, plan)
        args.confirm_production_write = True
        args.expected_plan_sha256 = "0" * 64
        with self.assertRaisesRegex(UsageError, "hash mismatch"):
            validate_apply_request(args, plan)

    def test_receipt_hash_and_publish_confirmation_are_required(self) -> None:
        plan = build_plan()
        base = {
            "schema_version": PLAN_SCHEMA_VERSION,
            "operation": CREATE_RECEIPT_OPERATION,
            "ok": True,
            "status": "success",
            "fully_verified": True,
            "template_id": 42,
            "plan_file": "plan.json",
            "plan_sha256": plan.plan_sha256,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "receipt.json"
            receipt = write_receipt(path, base)
            loaded = load_create_receipt(path)
            self.assertEqual(loaded["receipt_sha256"], receipt["receipt_sha256"])
            args = argparse.Namespace(
                confirm_publish=False,
                expected_receipt_sha256=receipt["receipt_sha256"],
            )
            with self.assertRaisesRegex(UsageError, "confirm-publish"):
                validate_publish_request(args, loaded)
            args.confirm_publish = True
            validate_publish_request(args, loaded)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["template_id"] = 43
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(UsageError, "hash is invalid"):
                load_create_receipt(path)

    def test_update_receipt_is_accepted(self) -> None:
        plan = build_plan(
            existing_template_ids=[42],
            target_template_id=42,
            baseline_state={"id": 42, "name": "测试参数模板", "status": 2},
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "update.json"
            receipt = write_receipt(
                path,
                {
                    "schema_version": PLAN_SCHEMA_VERSION,
                    "operation": UPDATE_RECEIPT_OPERATION,
                    "ok": True,
                    "status": "success",
                    "fully_verified": True,
                    "template_id": 42,
                    "plan_file": "plan.json",
                    "plan_sha256": plan.plan_sha256,
                },
            )
            loaded = load_create_receipt(path)
            self.assertEqual(loaded["operation"], UPDATE_RECEIPT_OPERATION)
            self.assertEqual(loaded["receipt_sha256"], receipt["receipt_sha256"])


class FakePage:
    context = object()


class RecordingTemplateClient(TemplateQueryClient):
    def __init__(self) -> None:
        super().__init__(FakePage(), Path("state.json"))
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def post_json(self, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append((endpoint, payload))
        return {"status": "success", "data": None}

    def fetch_created_templates(self, **_: Any) -> list[Any]:
        return [
            parse_template_row(
                {
                    "id": 42,
                    "name": "测试参数模板",
                    "status": 1,
                    "sqlDetail": SQL,
                    "creator": "tester01",
                }
            )
        ]


class TemplateQueryClientPayloadTests(unittest.TestCase):
    def test_save_includes_instance_key_and_reviewed_metadata_without_publish(self) -> None:
        plan = build_plan()
        client = RecordingTemplateClient()
        saved = client.save_template(
            name=plan.template_name,
            description=plan.description,
            sql=SQL,
            creator=plan.creator,
            instance_key=plan.instance_key,
            template_variables=[dict(item) for item in plan.template_variables],
            template_params=template_params_for_save(plan.template_params),
        )
        self.assertEqual(saved.id, 42)
        endpoint, payload = client.calls[0]
        self.assertEqual(endpoint, "template/saveAndUpdate")
        self.assertEqual(payload["instanceKey"], "dlc_presto")
        self.assertEqual(payload["templateParam"][0]["paramType"], 3)
        self.assertNotIn("condition", payload["templateParam"][0])
        self.assertFalse(any(item[0] == "template/publish" for item in client.calls))

    def test_sql_parser_includes_instance_key(self) -> None:
        client = RecordingTemplateClient()
        client.parse_sql(SQL, instance_key="dlc_presto")
        endpoint, payload = client.calls[0]
        self.assertEqual(endpoint, "template/sqlParser")
        self.assertEqual(payload["instanceKey"], "dlc_presto")

    def test_save_update_includes_existing_template_id(self) -> None:
        plan = build_plan()
        client = RecordingTemplateClient()
        saved = client.save_template(
            name=plan.template_name,
            description=plan.description,
            sql=SQL,
            creator=plan.creator,
            instance_key=plan.instance_key,
            template_variables=[dict(item) for item in plan.template_variables],
            template_params=template_params_for_save(plan.template_params),
            template_id=42,
        )
        self.assertEqual(saved.id, 42)
        self.assertEqual(client.calls[0][1]["id"], 42)


if __name__ == "__main__":
    unittest.main()
