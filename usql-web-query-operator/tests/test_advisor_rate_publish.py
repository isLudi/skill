from unittest.mock import patch
from test_advisor_rate import selection
from read_dashboard.commands import advisor_rate as rate
import pytest
from _shared.errors import UsageError


def test_after_publication_may_reference_the_prepublication_draft_formula(tmp_path):
    s = selection()
    unit = rate.project_unit_field_state({"unitMeasureList": [{"fieldId": rate.FORMULA, "showName": "破蛋率"}]})
    expected = rate.definition({}, s)
    plan = {"plan_sha256": "p", "selection": s, "baseline": {"schema_sha256": "schema"}}
    receipt = {"plan_sha256": "p", "confirmed": True, "result": {"publish_status": "success"}}
    with (patch.object(rate, "_published", return_value={"schema_sha256": "schema", "units": {"u": unit}, "formulas": {"f": expected}}) as read,
          patch.object(rate, "_values", return_value={"u": {"data": [{rate.FORMULA: "1"}], "totalData": {rate.FORMULA: "1"}}})):
        out = rate.verify_publication(None, plan, receipt, tmp_path)
    assert read.call_args.kwargs == {"require_isolation": False}
    assert out["published_functionally_verified"] is True


def test_read_only_recovery_requires_a_real_successful_publication(tmp_path):
    with pytest.raises(UsageError, match="acknowledgment"):
        rate.verify_publication(None, {"plan_sha256": "p"}, {"plan_sha256": "p", "confirmed": True}, tmp_path)


def test_value_reads_preserve_fixed_local_channel_filter():
    s = selection()
    detail = {"unitFilterList": [{"fieldId": "123", "filterUnitId": "filter_1", "format": {"filterValue": ["APP"], "orgParamType": 2, "isSelectAll": 0}}]}
    calls = []
    def post(page, url, payload, **kwargs):
        calls.append(payload)
        return {"data": detail} if url.endswith("/detail") else {"data": {"unit_1": {"unitId": "unit_1", "data": [], "totalSize": 0}}}
    with patch.object(rate, "post_json", post):
        rate._values(None, s, published=True)
    assert calls[-1]["filterList"][0]["filterValue"] == ["APP"]
