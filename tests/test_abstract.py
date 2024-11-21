from io import StringIO

import pytest
import yaml

from diff_k8s_manifests import check_mismatches, compare_state_dicts, load_yaml


@pytest.fixture
def load_yaml_mock():
    def _load_yaml_mock(yaml_string):
        content = yaml.safe_load(StringIO(yaml_string))
        return content if content is not None else {}

    return _load_yaml_mock


def test_no_file():
    with pytest.raises(FileNotFoundError):
        load_yaml("non_existent_file.yaml")


def test_empty_files(load_yaml_mock):
    current_state = load_yaml_mock("")
    desired_state = load_yaml_mock("")

    diff = compare_state_dicts(current_state, desired_state)

    assert not diff["added"]
    assert not diff["removed"]
    assert not diff["changed"]


def test_something_added(load_yaml_mock):
    current = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 1
    """

    desired = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 1
      template:
        spec:
          containers:
            - name: nginx
              image: nginx:1.16.3
    """

    current_state = load_yaml_mock(current)
    desired_state = load_yaml_mock(desired)

    diff = compare_state_dicts(current_state, desired_state)

    assert len(diff["added"]) == 1
    added_path = [d["path"] for d in diff["added"]]
    added_value = [d["new_value"] for d in diff["added"]]

    assert "spec.template.spec.containers[nginx]" in added_path or added_value[0] == [
        {"name": "nginx", "image": "nginx:1.16.3"}
    ]


def test_something_deleted(load_yaml_mock):
    current = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 1
      template:
        spec:
          containers:
            - name: nginx
              image: nginx:1.16.3
    """

    desired = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 1
    """

    current_state = load_yaml_mock(current)
    desired_state = load_yaml_mock(desired)

    diff = compare_state_dicts(current_state, desired_state)

    assert len(diff["removed"]) == 1
    removed_path = [d["path"] for d in diff["removed"]]
    removed_value = [d["old_value"] for d in diff["removed"]]

    expected_removed_value = {
        "spec": {"containers": [{"name": "nginx", "image": "nginx:1.16.3"}]}
    }

    assert "spec.template" in removed_path
    assert removed_value[0] == expected_removed_value


def test_something_changed(load_yaml_mock):
    current = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 1
    """

    desired = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 3
    """

    current_state = load_yaml_mock(current)
    desired_state = load_yaml_mock(desired)

    diff = compare_state_dicts(current_state, desired_state)

    assert not diff["added"]
    assert len(diff["changed"]) == 1
    assert "spec.replicas" in [d["path"] for d in diff["changed"]]


def test_no_diff_found(load_yaml_mock):
    current = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 1
    """

    current_state = load_yaml_mock(current)
    desired_state = load_yaml_mock(current)

    diff = compare_state_dicts(current_state, desired_state)

    assert not diff["added"]
    assert not diff["removed"]
    assert not diff["changed"]


def test_multi_crud(load_yaml_mock):
    current = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 1
      template:
        spec:
          containers:
            - name: nginx
              image: nginx:1.14.2
              env:
                - name: DATABASE_HOST
                  value: db1.example.com
    """

    desired = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 3
      template:
        spec:
          containers:
            - name: nginx
              image: nginx:1.16.3
              env:
                - name: DATABASE_HOST
                  value: db2.example.com
                - name: MESSAGE_BROKER_HOST
                  value: kfk1.example.com
    """

    current_state = load_yaml_mock(current)
    desired_state = load_yaml_mock(desired)

    diff = compare_state_dicts(current_state, desired_state)

    assert "spec.template.spec.containers[nginx].env[MESSAGE_BROKER_HOST]" in [
        d["path"] for d in diff["added"]
    ]
    assert "spec.replicas" in [d["path"] for d in diff["changed"]]
    assert "spec.template.spec.containers[nginx].image" in [
        d["path"] for d in diff["changed"]
    ]
    assert "spec.template.spec.containers[nginx].env[DATABASE_HOST].value" in [
        d["path"] for d in diff["changed"]
    ]


def test_mismatches(load_yaml_mock):
    current = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 1
    """

    desired_kind_mismatch = """
    kind: StatefulSet
    apiVersion: apps/v1
    spec:
      replicas: 1
    """

    desired_version_mismatch = """
    kind: Deployment
    apiVersion: apps/v2
    spec:
      replicas: 1
    """

    current_state = load_yaml_mock(current)
    desired_state = load_yaml_mock(desired_kind_mismatch)
    mismatches = check_mismatches(current_state, desired_state, ["kind", "apiVersion"])

    assert mismatches["kind"] is True
    assert mismatches["apiVersion"] is False

    desired_state = load_yaml_mock(desired_version_mismatch)
    mismatches = check_mismatches(current_state, desired_state, ["kind", "apiVersion"])

    assert mismatches["kind"] is False
    assert mismatches["apiVersion"] is True


def test_create_object(load_yaml_mock):
    current = ""
    desired = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 3
      template:
        spec:
          containers:
            - name: nginx
              image: nginx:1.16.3
    """

    current_state = load_yaml_mock(current)
    desired_state = load_yaml_mock(desired)

    diff = compare_state_dicts(current_state, desired_state)

    assert len(diff["added"]) == 4
    added_paths = [d["path"] for d in diff["added"]]
    assert "kind" in added_paths
    assert "apiVersion" in added_paths
    assert "spec.replicas" in added_paths
    assert "spec.template.spec.containers" in added_paths


def test_delete_object(load_yaml_mock):
    current = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 3
      template:
        spec:
          containers:
            - name: nginx
              image: nginx:1.16.3
    """
    desired = ""

    current_state = load_yaml_mock(current)
    desired_state = load_yaml_mock(desired)

    diff = compare_state_dicts(current_state, desired_state)

    assert len(diff["removed"]) == 3
    removed_paths = [d["path"] for d in diff["removed"]]
    assert "kind" in removed_paths
    assert "apiVersion" in removed_paths
    assert "spec" in removed_paths


def test_kind_change(load_yaml_mock):
    current = """
    kind: Deployment
    apiVersion: apps/v1
    spec:
      replicas: 3
      template:
        spec:
          containers:
            - name: nginx
              image: nginx:1.16.3
    """
    desired = """
    kind: StatefulSet
    apiVersion: apps/v1
    spec:
      replicas: 3
      template:
        spec:
          containers:
            - name: nginx
              image: nginx:1.16.3
    """

    current_state = load_yaml_mock(current)
    desired_state = load_yaml_mock(desired)

    diff = compare_state_dicts(current_state, desired_state)

    assert len(diff["changed"]) == 1
    assert "kind" in [d["path"] for d in diff["changed"]]
