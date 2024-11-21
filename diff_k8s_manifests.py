import json
import logging
import os
import sys

import yaml


class JSONFormatter(logging.Formatter):
    """Custom logging formatter to output logs in JSON format."""

    def format(self, record):
        log_message = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
        }
        return json.dumps(log_message)


def setup_logging() -> str:
    """
    Sets up logging.

    The log format and log level can be configured through environment variables:
    LOG_FORMAT (either "json" or "text") and LOG_LEVEL (e.g., "INFO", "DEBUG").

    Returns:
        str: The format of the logs ("json" or "text").
    """
    log_format = os.getenv("LOG_FORMAT", "text")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logger = logging.getLogger()
    logger.setLevel(log_level)

    handler = logging.StreamHandler()

    if log_format.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(handler)

    return log_format.lower()


def load_yaml(file_path: str) -> dict:
    """
    Loads a YAML file and returns its contents as a Python dictionary.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The contents of the YAML file as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If there is an error in parsing the YAML file.
    """
    try:
        with open(file_path, "r") as data:
            content = yaml.safe_load(data)
            return content if content is not None else {}
    except FileNotFoundError as e:
        logging.error(
            f"File not found: {file_path}. Please check the file path and try again."
        )
        raise e
    except yaml.YAMLError as e:
        logging.error(f"Failed to parse YAML file {file_path}: {e}")
        raise e


def compare_state_lists(
    current_state: list[dict], desired_state: list[dict], path: str
) -> dict:
    """
    Compares two lists of dictionaries (e.g., containers in k8s specs) and
    returns the differences (added, removed, and changed items).

    Args:
        current_state (list[dict]): The current state list.
        desired_state (list[dict]): The desired state list.
        path (str): The path of the list in the object (used for detailed diffs).

    Returns:
        dict: A dictionary containing the 'removed', 'added', and 'changed' items.
    """
    diff = {"removed": [], "added": [], "changed": []}

    if not current_state:
        diff["removed"].append({"path": path, "message": "Current state list is empty"})
        return diff

    if not desired_state:
        diff["added"].append({"path": path, "message": "Desired state list is empty"})
        return diff

    unique_key = (
        "name" if "name" in current_state[0] else list(current_state[0].keys())[0]
    )

    current_state_dict = {item[unique_key]: item for item in current_state}
    desired_state_dict = {item[unique_key]: item for item in desired_state}

    for key in current_state_dict:
        if key not in desired_state_dict:
            diff["removed"].append(
                {"path": f"{path}[{key}]", "old_value": current_state_dict[key]}
            )

    for key in desired_state_dict:
        if key not in current_state_dict:
            diff["added"].append(
                {"path": f"{path}[{key}]", "new_value": desired_state_dict[key]}
            )

    for key in current_state_dict:
        if (
            key in desired_state_dict
            and current_state_dict[key] != desired_state_dict[key]
        ):
            sub_diff = compare_state_dicts(
                current_state_dict[key], desired_state_dict[key], f"{path}[{key}]"
            )
            diff["removed"].extend(sub_diff["removed"])
            diff["added"].extend(sub_diff["added"])
            diff["changed"].extend(sub_diff["changed"])

    return diff


def compare_state_dicts(
    current_state: dict, desired_state: dict, path: str = ""
) -> dict:
    """
    Compares two dictionaries (e.g., Kubernetes manifest YAML) and returns
    the differences (added, removed, and changed keys/values).

    Args:
        current_state (dict): The current state dictionary.
        desired_state (dict): The desired state dictionary.
        path (str, optional): The path in the object (used for detailed diffs). Defaults to "".

    Returns:
        dict: A dictionary containing the 'removed', 'added', and 'changed' items.
    """
    diff = {"removed": [], "added": [], "changed": []}

    logging.debug(
        f"Comparing current: {current_state} with desired: {desired_state} at path: {path}"
    )

    for key in current_state:
        key_path = f"{path}.{key}" if path else key
        logging.debug(f"Processing key '{key}' with path '{key_path}'")
        if key not in desired_state:
            logging.debug(f"Key '{key}' removed. Path: {key_path}")
            diff["removed"].append({"path": key_path, "old_value": current_state[key]})
        elif isinstance(current_state[key], dict) and isinstance(
            desired_state[key], dict
        ):
            sub_diff = compare_state_dicts(
                current_state[key], desired_state[key], key_path
            )
            diff["removed"].extend(sub_diff["removed"])
            diff["added"].extend(sub_diff["added"])
            diff["changed"].extend(sub_diff["changed"])
        elif isinstance(current_state[key], list) and isinstance(
            desired_state[key], list
        ):
            sub_diff = compare_state_lists(
                current_state[key], desired_state[key], key_path
            )
            diff["removed"].extend(sub_diff["removed"])
            diff["added"].extend(sub_diff["added"])
            diff["changed"].extend(sub_diff["changed"])
        elif current_state[key] != desired_state[key]:
            logging.debug(f"Key '{key}' changed at path: {key_path}")
            diff["changed"].append(
                {
                    "path": key_path,
                    "old_value": current_state[key],
                    "new_value": desired_state[key],
                }
            )

    for key in desired_state:
        key_path = f"{path}.{key}" if path else key
        if key not in current_state:
            logging.debug(f"Key '{key}' added. Path: {key_path}")
            if isinstance(desired_state[key], dict):
                sub_diff = compare_state_dicts({}, desired_state[key], key_path)
                diff["added"].extend(sub_diff["added"])
            else:
                diff["added"].append(
                    {"path": key_path, "new_value": desired_state[key]}
                )

    logging.debug(f"Diff for path '{path}': {diff}")
    return diff


def check_mismatches(
    current_state: dict, desired_state: dict, fields_to_check: list[str]
) -> dict:
    """
    Checks for mismatches between specific fields in the current and desired state.

    Args:
        current_state (dict): The current state dictionary.
        desired_state (dict): The desired state dictionary.
        fields_to_check (list[str]): List of fields to check (e.g., 'kind', 'apiVersion').

    Returns:
        dict: A dictionary indicating whether there were mismatches for each field.
    """
    mismatches = {}

    for field in fields_to_check:
        current_value = current_state.get(field)
        desired_value = desired_state.get(field)

        if current_value != desired_value:
            logging.warning(
                f"'{field}' mismatch. Current: {current_value}, Desired: {desired_value}"
            )
            mismatches[field] = True
        else:
            mismatches[field] = False

    return mismatches


def get_diff_summary(diff: dict) -> dict:
    """
    Prepares a summary of the differences between the current and desired state.

    Args:
        diff (dict): The diff containing 'removed', 'added', and 'changed' items.

    Returns:
        dict: A summary of the differences.
    """
    summary = {}

    if diff["removed"]:
        summary["removed"] = [
            f"{item['path']}: {yaml.dump(item.get('old_value', '')).strip()}"
            for item in diff["removed"]
        ]

    if diff["added"]:
        summary["added"] = [
            f"{item['path']}: {yaml.dump(item['new_value'], default_flow_style=False).strip()}"
            for item in diff["added"]
        ]

    if diff["changed"]:
        summary["changed"] = [
            f"{item['path']}: old value: {item['old_value']}, new value: {item['new_value']}"
            for item in diff["changed"]
        ]

    return summary


def print_diff(file_current: str, file_desired: str, output_format: str) -> None:
    """
    Compares two Kubernetes manifests and outputs the differences.

    Args:
        file_current (str): The path to the current state YAML file.
        file_desired (str): The path to the desired state YAML file.
        output_format (str): The output format ("json" or "text").
    """
    try:
        current_state = load_yaml(file_current)
        desired_state = load_yaml(file_desired)
    except FileNotFoundError:
        sys.exit(1)

    fields_to_check = ["kind", "apiVersion"]
    check_mismatches(current_state, desired_state, fields_to_check)

    diff = compare_state_dicts(current_state, desired_state)

    summary = get_diff_summary(diff)

    if (
        not summary.get("removed")
        and not summary.get("added")
        and not summary.get("changed")
    ):
        logging.info("No differences found.")

    def format_changes(change_type: str, changes: list) -> str:
        """Formats the changes for text output."""
        output = f"The following items were {change_type}:\n"
        for item in changes:
            parts = item.split(":", 1)
            path = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            output += f"  {path}:\n"
            if value:
                try:
                    value_dict = yaml.safe_load(value)
                    if isinstance(value_dict, dict):
                        for k, v in value_dict.items():
                            output += f"    {k}: {v}\n"
                    else:
                        output += f"    {value_dict}\n"
                except yaml.YAMLError:
                    output += f"    {value}\n"
        return output

    if output_format == "json":
        logging.info(summary)
    else:
        output = ""

        if summary.get("removed"):
            output += format_changes("removed", summary["removed"])

        if summary.get("added"):
            output += format_changes("added", summary["added"])

        if summary.get("changed"):
            output += format_changes("changed", summary["changed"])

        if output:
            logging.info(output.strip())


if __name__ == "__main__":
    log_format = setup_logging()

    if len(sys.argv) < 3:
        logging.error(
            f"Usage: python {sys.argv[0]} <current_state.yaml> <desired_state.yaml>"
        )
        sys.exit(1)

    file_current = sys.argv[1]
    file_desired = sys.argv[2]

    try:
        print_diff(file_current, file_desired, log_format)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
