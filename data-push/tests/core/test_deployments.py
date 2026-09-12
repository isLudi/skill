from copy import deepcopy
import json
from pathlib import Path
import tempfile

import pytest

from lark_delivery.core import catalog
from lark_delivery.paths import CONFIG_ROOT, WORKSPACE_ROOT


def test_current_miaoda_deployment_is_market_only_and_identity_bound():
    deployment = catalog.load_deployment(catalog.DEFAULT_MIAODA_DEPLOYMENT)
    assert deployment["domain"] == "market_consultant"
    assert deployment["execution_surface"] == "miaoda"
    assert deployment["lifecycle"] == "prototype"
    assert deployment["local_schedule_relation"] == "independent"
    workflow = catalog.load_deployment_workflow(
        catalog.DEFAULT_MIAODA_DEPLOYMENT,
        catalog.DEFAULT_MIAODA_WORKFLOW,
    )
    assert workflow["style_owner"] == "market_consultant"
    assert workflow["source_channel_ref"] == "market_consultant/supervisor_koc_douyin_sync"
    identity = json.loads((WORKSPACE_ROOT / deployment["runtime_root"] / deployment["identity_file"]).read_text(encoding="utf-8"))
    assert identity["app_id"] == deployment["expected_app_id"]


def test_qingcheng_cannot_fall_back_to_the_market_miaoda_deployment():
    with pytest.raises(ValueError, match="no cross-department fallback"):
        catalog.load_deployment("qingcheng/miaoda/cloud_data_push")


def test_miaoda_source_reference_and_style_owner_must_match_department():
    workflow = deepcopy(catalog.deployment_registry()["deployments"][catalog.DEFAULT_MIAODA_DEPLOYMENT]["workflows"][catalog.DEFAULT_MIAODA_WORKFLOW])
    workflow["contract_ref"] = "departments/qingcheng/example.md"
    with pytest.raises(ValueError, match="same-department"):
        catalog.validate_deployment_workflow(catalog.DEFAULT_MIAODA_WORKFLOW, workflow, "qingcheng")
    workflow["source_channel_ref"] = "qingcheng/supervisor_koc_douyin_sync"
    with pytest.raises(ValueError, match="style owner"):
        catalog.validate_deployment_workflow(catalog.DEFAULT_MIAODA_WORKFLOW, workflow, "qingcheng")


def test_miaoda_deployments_cannot_share_app_or_runtime():
    index = deepcopy(catalog.deployment_registry())
    duplicate = deepcopy(index["deployments"][catalog.DEFAULT_MIAODA_DEPLOYMENT])
    duplicate["deployment_id"] = "second"
    index["deployments"]["market_consultant/miaoda/second"] = duplicate
    with pytest.raises(ValueError, match="must not share"):
        catalog.validate_deployment_registry(index)


def test_miaoda_workflows_cannot_share_module_or_namespaces():
    index = deepcopy(catalog.deployment_registry())
    deployment = index["deployments"][catalog.DEFAULT_MIAODA_DEPLOYMENT]
    deployment["workflows"]["second"] = deepcopy(deployment["workflows"][catalog.DEFAULT_MIAODA_WORKFLOW])
    with pytest.raises(ValueError, match="Miaoda workflows must not share"):
        catalog.validate_deployment_registry(index)


def test_native_miaoda_workflow_does_not_need_a_local_channel_reference():
    workflow = deepcopy(catalog.deployment_registry()["deployments"][catalog.DEFAULT_MIAODA_DEPLOYMENT]["workflows"][catalog.DEFAULT_MIAODA_WORKFLOW])
    workflow.pop("source_channel_ref")
    assert catalog.validate_deployment_workflow(catalog.DEFAULT_MIAODA_WORKFLOW, workflow, "market_consultant") == workflow


def test_miaoda_runtime_must_stay_under_codex_runtime():
    definition = deepcopy(catalog.deployment_registry()["deployments"][catalog.DEFAULT_MIAODA_DEPLOYMENT])
    definition["runtime_root"] = "../outside"
    with pytest.raises(ValueError, match="Invalid deployment path"):
        catalog.validate_deployment(definition, catalog.DEFAULT_MIAODA_DEPLOYMENT)


def test_missing_or_drifted_runtime_identity_is_rejected():
    source_registry = catalog.registry()
    source_deployments = catalog.deployment_registry()
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        config_root = workspace / "config"
        runtime_root = workspace / "runtime" / "cloud-data-push-miaoda"
        module_root = runtime_root / "server" / "modules" / "cloud-push-demo"
        config_root.mkdir()
        module_root.mkdir(parents=True)
        deployment = source_deployments["deployments"][catalog.DEFAULT_MIAODA_DEPLOYMENT]
        workflow = deployment["workflows"][catalog.DEFAULT_MIAODA_WORKFLOW]
        channel_ref = workflow["source_channel_ref"]
        channel_relative_path = Path(source_registry["channels"][channel_ref])
        isolated_registry = deepcopy(source_registry)
        isolated_registry["channels"] = {channel_ref: channel_relative_path.as_posix()}
        (config_root / "channels.json").write_text(json.dumps(isolated_registry), encoding="utf-8")
        (config_root / "deployments.json").write_text(json.dumps(source_deployments), encoding="utf-8")
        channel_path = config_root / channel_relative_path
        channel_path.parent.mkdir(parents=True)
        channel_path.write_text((CONFIG_ROOT / channel_relative_path).read_text(encoding="utf-8"), encoding="utf-8")
        contract_path = workspace / "references" / workflow["contract_ref"]
        contract_path.parent.mkdir(parents=True)
        contract_path.write_text(
            (CONFIG_ROOT.parent / "references" / workflow["contract_ref"]).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (runtime_root / ".spark").mkdir()
        (runtime_root / ".spark" / "meta.json").write_text(json.dumps({"app_id": "app_drifted"}), encoding="utf-8")
        with pytest.raises(ValueError, match="identity drift"):
            catalog.load_deployment(catalog.DEFAULT_MIAODA_DEPLOYMENT, config_root, workspace)
