from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _shared.errors import UsageError
from read_dashboard.dashboard_build_adapters import TaitanDashboardBuildV1Adapter


def adapter(tmp_path):
    return TaitanDashboardBuildV1Adapter(page=object(), args=SimpleNamespace(artifacts_dir=tmp_path))


def dataset():
    return {"application_model_id": "2460", "subject_id": "216472",
            "config": {"field_resolution_dashboard_id": "dashboard_source"}}


def detail(name="Conversion", model=2460, subject=216472):
    return {"modelName": name, "modelId": model,
            "dashboardModel": {"applicationModelId": model, "id": subject}}


def test_explicit_label_preserves_existing_behavior_without_read(tmp_path):
    value = dataset()
    value["config"]["dataset_name"] = "Reviewed name"
    assert adapter(tmp_path)._dataset_name(value) == "Reviewed name"


def test_missing_label_uses_only_exact_source_model_and_subject_then_caches(tmp_path):
    current = adapter(tmp_path)
    with patch("read_dashboard.dashboard_build_adapters.fetch_edit_dashboard_config", return_value={"dashboardHtmlJson": "{}"}), \
         patch("read_dashboard.dashboard_build_adapters.extract_component_units", return_value=[{"unit_id": "unit_1"}, {"unit_id": "unit_2"}]), \
         patch("read_dashboard.dashboard_build_adapters.fetch_edit_unit_detail", side_effect=[detail(model=99), detail()]) as fetch:
        assert current._dataset_name(dataset()) == "Conversion"
        assert current._dataset_name(dataset()) == "Conversion"
        assert fetch.call_count == 2


@pytest.mark.parametrize("details", [[detail(subject=1)], [detail(name="A"), detail(name="B")]])
def test_wrong_subject_or_conflicting_labels_fail_before_component_write(tmp_path, details):
    with patch("read_dashboard.dashboard_build_adapters.fetch_edit_dashboard_config", return_value={"dashboardHtmlJson": "{}"}), \
         patch("read_dashboard.dashboard_build_adapters.extract_component_units", return_value=[{"unit_id": f"unit_{i}"} for i in range(len(details))]), \
         patch("read_dashboard.dashboard_build_adapters.fetch_edit_unit_detail", side_effect=details):
        with pytest.raises(UsageError, match="one exact"):
            adapter(tmp_path)._dataset_name(dataset())


def test_incomplete_identity_never_searches_or_infers_a_name(tmp_path):
    with pytest.raises(UsageError, match="exact source"):
        adapter(tmp_path)._dataset_name({"application_model_id": "2460"})
