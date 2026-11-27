import json
import shutil

import pytest

from lark_delivery.integrations import producer_bindings as bindings


@pytest.mark.parametrize("task_key", bindings.PRODUCER_FILES)
def test_local_release_records_match_registered_identity(task_key):
    domain = task_key.partition(".")[0]
    document = bindings.read_binding_document(task_key, expected_domain=domain)
    resolved = bindings.load_binding(task_key, expected_domain=domain)
    assert resolved["exec_file_id"] == document["upstream"]["exec_file_id"]
    assert document["task_key"] == task_key
    assert document["execution_surface"] == "local"


def test_replacing_a_single_release_is_visible_to_the_next_lookup(tmp_path):
    key = "market_consultant.leads"
    domain = "market_consultant"
    original = bindings.binding_path(key, expected_domain=domain)
    path = tmp_path / "release" / original.name
    path.parent.mkdir()
    shutil.copyfile(original, path)
    old = bindings.load_binding(key, expected_domain=domain, config_root=tmp_path)
    new = json.loads(path.read_text(encoding="utf-8"))
    new["upstream"]["exec_file_id"] = old["exec_file_id"] + 1
    new["upstream"]["verified_version_id"] = old["verified_version_id"] + 1
    path.write_text(json.dumps(new), encoding="utf-8")

    updated = bindings.load_binding(key, expected_domain=domain, config_root=tmp_path)
    assert updated["exec_file_id"] == old["exec_file_id"] + 1
    assert updated["verified_version_id"] == old["verified_version_id"] + 1
    assert updated["channel_mapping_version"] == old["channel_mapping_version"]


def test_producer_binding_refuses_another_department():
    with pytest.raises(ValueError, match="Unknown upstream producer"):
        bindings.load_binding("qingcheng.process", expected_domain="market_consultant")


def test_binding_refuses_a_different_execution_surface(tmp_path):
    key = "qingcheng.process"
    domain = "qingcheng"
    record = bindings.read_binding_document(key, expected_domain=domain)
    record["execution_surface"] = "miaoda"
    path = bindings.binding_path(key, expected_domain=domain, config_root=tmp_path)
    path.parent.mkdir()
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="binding identity differs"):
        bindings.load_binding(key, expected_domain=domain, config_root=tmp_path)
