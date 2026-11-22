"""Unit coverage for the bounded Qingcheng receiving-key operation."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import sys
import tempfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from _shared.errors import UsageError
from read_dashboard.commands import receiving_key_draft as receiving


MAIN = "dashboard_3885764906392891392"


def board(formula=receiving.OLD_FORMULA):
    dependencies = [
        {"paramId": "123", "orgParamType": 1, "needBoundaryValue": False},
        {"paramId": "124", "orgParamType": 2, "needBoundaryValue": False},
    ]
    definition = {
        "subjectId": 100, "columnKey": "customized_120", "columnName": "接量人力",
        "columnDesc": "接量", "dataType": 1, "formula": formula,
        "dependencyIndicators": dependencies, "globalFilterSpecialConfig": [],
    }
    return receiving.BoardVersion(
        "draft", {"htmlId": "html_123"}, {"componentsTree": []},
        {"formulas": {"formula:2460:接量人力": definition}, "units": {"unit_1": "observable"}},
        {"formula:2460:接量人力": definition}, {"unit_1": "渠道-总"},
        definition, "125", dependencies,
    )


def test_dependency_switch_is_exact_and_preserves_formula_identity():
    current = board()
    changed = receiving._headcount_change(current)
    assert changed == {
        **current.receiving, "formula": receiving.NEW_FORMULA,
        "dependencyIndicators": [{"paramId": "125", "orgParamType": 2, "needBoundaryValue": False}],
    }
    after = receiving._expected_semantic(current, changed)
    assert after["units"] == current.semantic["units"]
    assert current.receiving["formula"] == receiving.OLD_FORMULA
    assert after["formulas"]["formula:2460:接量人力"]["formula"] == receiving.NEW_FORMULA


def test_different_original_contract_does_not_enter_plan():
    with pytest.raises(UsageError, match="supported metric contract"):
        receiving._headcount_change(board("COUNT(${v_lead})"))


def test_recovery_restores_the_exact_original_expression_and_dependencies():
    current = board(receiving.NEW_FORMULA)
    current.receiving["dependencyIndicators"] = [
        {"paramId": "125", "orgParamType": 2, "needBoundaryValue": False},
    ]
    after = receiving._headcount_change(current, "restore-stock")
    assert after == {**current.receiving, "formula": receiving.OLD_FORMULA,
                     "dependencyIndicators": current.old_dependencies}
    with pytest.raises(UsageError, match="supported metric contract"):
        receiving._headcount_change(board(), "restore-stock")


def test_normalization_keeps_layout_and_resolves_version_resource_references():
    value = {"subjectId": 100, "unitId": "unit_1", "htmlId": "html_1",
             "format": {"preFilterTaskId": ";123", "uniqueKeyWithTimeStamp": "customized_120-456-fixed"},
             "colWidthsConfigPivot": {"customized_120": 70}}
    result = receiving._sanitize_version_fields(value, {"customized_120": "formula:2460:人效"}, {100: "2460"})
    assert result == {
        "subjectId": "2460", "unitId": "unit_1",
        "format": {"uniqueKeyWithTimeStamp": "formula:2460:人效-456-fixed"},
        "colWidthsConfigPivot": {"formula:2460:人效": 70},
    }


def test_unique_active_full_release_required():
    active = {"versionStatus": 1, "isGrayscale": 0, "dashboardId": MAIN,
              "dashboardName": "转化数据看板", "versionId": "version_7"}
    with patch.object(receiving, "post_json", return_value={"data": [active, {**active, "isGrayscale": 1}]}):
        assert receiving._active_version(None, MAIN) == active
    with patch.object(receiving, "post_json", return_value={"data": [active, active]}):
        with pytest.raises(UsageError, match="one unambiguous"):
            receiving._active_version(None, MAIN)


def test_plan_requires_the_exact_reviewed_sha():
    content = {"artifact_type": receiving.PLAN_TYPE, "operation": receiving.OPERATION,
               "dashboard_id": MAIN, "owner": receiving.OWNER}
    expected = receiving.canonical_sha256(content)
    with tempfile.TemporaryDirectory() as tmp:
        plan = Path(tmp) / "plan.json"
        plan.write_text(json.dumps({**content, "plan_sha256": expected}), encoding="utf-8")
        assert receiving._checked_plan(plan, expected)["dashboard_id"] == MAIN
        with pytest.raises(UsageError, match="exact reviewed"):
            receiving._checked_plan(plan, "b" * 64)


def test_plan_blocks_unpublished_unrelated_configuration():
    draft, published = board(), board()
    published.version = "version_1"
    published.semantic["units"] = {"unit_1": "changed"}
    with patch.object(receiving, "_read_version", return_value=draft), patch.object(receiving, "_published", return_value=published):
        with pytest.raises(UsageError, match="other changes"):
            receiving._build_plan(None, MAIN, Path("state.json"), {})


def test_plan_blocks_formula_shared_between_publish_and_draft():
    draft, published = board(), board()
    published.version = "version_1"
    with patch.object(receiving, "_read_version", return_value=draft), patch.object(receiving, "_published", return_value=published):
        with pytest.raises(UsageError, match="not isolated"):
            receiving._build_plan(None, MAIN, Path("state.json"), {})


def test_publish_blind_retry_is_blocked_by_durable_claim():
    plan = {"dashboard_id": MAIN, "plan_sha256": "c" * 64}
    with tempfile.TemporaryDirectory() as tmp, patch.object(receiving, "RUNTIME_DIR", Path(tmp)):
        receiving._claim(plan, "publish")
        with pytest.raises(UsageError, match="already attempted"):
            receiving._claim(plan, "publish")


def test_pivot_value_readback_requires_the_versioned_formula_column_and_numeric_rows():
    plan = {
        "dashboard_id": MAIN,
        "targets": {"unit_1": "渠道-总"},
        "after": {"columnKey": "customized_120"},
        "published_receiving_field_id": "customized_90",
    }

    def read(rows, *, draft=True):
        response = {"data": {"unit_1": {
            "unitId": "unit_1", "errorCode": 0, "title": "接量人力", "data": rows,
        }}}
        with patch.object(receiving, "fetch_dashboard_config", return_value={}), patch.object(
            receiving, "parse_dashboard_html", return_value={}
        ), patch.object(receiving, "extract_component_units", return_value=[]), patch.object(
            receiving, "post_json", return_value=response
        ):
            return receiving._verify_pivot_values(None, plan, draft=draft)

    draft_result = read([{"customized_120": "0"}])
    published_result = read([{"customized_90": 2}], draft=False)
    assert draft_result[0]["metric_field_id"] == "customized_120"
    assert published_result[0]["metric_field_id"] == "customized_90"
    assert draft_result[0]["metric_value_count"] == 1

    for rows in ([], [{"customized_120": None}], [{"customized_120": "not-a-number"}], [{"other": "1"}]):
        with pytest.raises(UsageError, match="receiving metric"):
            read(rows)


def test_failed_save_restores_only_the_exact_attempted_draft():
    before, after = board(), board()
    after.receiving = receiving._headcount_change(before)
    after.semantic = receiving._expected_semantic(before, after.receiving)
    plan = {"dashboard_id": MAIN, "dashboard_name": "转化数据看板", "plan_sha256": "c" * 64,
            "before": before.receiving, "after": after.receiving, "draft_layout_sha256": "d" * 64,
            "after_sha256": receiving.canonical_sha256(after.semantic),
            "draft_sha256": receiving.canonical_sha256(before.semantic)}
    receipt = {"writes": []}
    with tempfile.TemporaryDirectory() as tmp, (
        patch.object(receiving, "_assert_current_public")
    ), patch.object(receiving, "_claim"), patch.object(
        receiving, "_write_formula"
    ) as writes, patch.object(
        receiving, "_read_version", side_effect=[after, after, before]
    ), patch.object(receiving, "_verify_pivot_values", return_value=[]), patch.object(
        receiving, "_write_dashboard_schema", side_effect=UsageError("save failed")
    ):
        with pytest.raises(UsageError, match="save failed"):
            receiving._apply(None, plan, before, Path(tmp), receipt)
        assert [call.args[1] for call in writes.call_args_list] == [after.receiving, before.receiving]
    assert receipt["restored_draft_sha256"] == plan["draft_sha256"]


def test_publish_pins_the_loaded_editor_html_id_across_config_reads():
    first, second = board(receiving.NEW_FORMULA), board(receiving.NEW_FORMULA)
    first.config = {"htmlId": "html_2", "dashboardId": MAIN, "dashboardHtmlJson": "{}"}
    second.config = {**first.config, "htmlId": "html_3"}
    second.receiving["dependencyIndicators"] = [
        {"paramId": "125", "orgParamType": 2, "needBoundaryValue": False},
    ]
    first.receiving["dependencyIndicators"] = second.receiving["dependencyIndicators"]
    # Keep the descriptor and its new dependency the same in both snapshots.
    after_sha = receiving.canonical_sha256(second.semantic)
    version = board(receiving.NEW_FORMULA)
    version.receiving = second.receiving
    version.semantic = second.semantic
    version.version = "version_2"
    plan = {"dashboard_id": MAIN, "after": second.receiving, "after_sha256": after_sha,
            "compatibility": {}, "published_version": "version_1"}
    page = SimpleNamespace(url=f"https://udata.baijia.com/taitan/?dashboardId={MAIN}&htmlId=html_1")
    receipt = {}
    with patch.object(receiving, "_assert_current_public"), patch.object(
        receiving, "_read_version", side_effect=[first, second]
    ), patch.object(receiving, "_compatibility", return_value={}), patch.object(
        receiving, "_claim"
    ), patch.object(
        receiving, "publish_dashboard", return_value={"publish_status": "success", "publish_error_code": 0}
    ) as publish, patch.object(
        receiving, "_active_version", return_value={"versionId": "version_2", "versionDescription": "version note"}
    ), patch.object(receiving, "_published", return_value=version), patch.object(
        receiving, "_verify_pivot_values", return_value=[]
    ):
        receiving._publish(page, plan, {}, Path("state.json"), "version note", receipt)
    assert receipt["fully_verified"] and publish.call_args.args[-1] == "html_1"
