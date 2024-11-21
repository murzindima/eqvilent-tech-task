import pytest

from diff_k8s_manifests import compare_state_dicts, load_yaml


@pytest.fixture
def load_yaml_file():
    def _load_yaml_file(file_name):
        return load_yaml(f"tests/{file_name}")

    return _load_yaml_file


def test_compare_config_file_1_and_2(load_yaml_file):
    current_state = load_yaml_file("config_file_1.yaml")
    desired_state = load_yaml_file("config_file_2.yaml")

    diff = compare_state_dicts(current_state, desired_state)

    assert len(diff["added"]) > 0
    assert len(diff["removed"]) > 0
    assert len(diff["changed"]) > 0

    assert any(d["path"] == "spec.replicas" for d in diff["changed"])
    assert any(
        d["path"] == "spec.template.spec.containers[nginx].image"
        for d in diff["changed"]
    )


def test_compare_config_file_2_and_3(load_yaml_file):
    current_state = load_yaml_file("config_file_2.yaml")
    desired_state = load_yaml_file("config_file_3.yaml")

    diff = compare_state_dicts(current_state, desired_state)

    assert len(diff["added"]) > 0
    assert len(diff["removed"]) > 0
    assert len(diff["changed"]) > 0

    assert any(
        d["path"] == "spec.template.spec.containers[nginx].image"
        for d in diff["changed"]
    )
    assert any(
        d["path"] == "spec.template.spec.containers[nginx].resources.limits.memory"
        for d in diff["added"]
    )


def test_compare_config_file_1_and_3(load_yaml_file):
    current_state = load_yaml_file("config_file_1.yaml")
    desired_state = load_yaml_file("config_file_3.yaml")

    diff = compare_state_dicts(current_state, desired_state)

    assert len(diff["added"]) > 0
    assert len(diff["removed"]) > 0
    assert len(diff["changed"]) > 0

    assert any(d["path"] == "spec.replicas" for d in diff["changed"])
    assert any(
        d["path"] == "spec.template.spec.containers[nginx].image"
        for d in diff["changed"]
    )
    assert any(
        d["path"] == "spec.template.spec.containers[nginx].resources.limits.memory"
        for d in diff["added"]
    )
