from typing import Any, Dict
import os
import json
import yaml


def load_workflow_config(config_path: str) -> dict:
    """
    Load a workflow configuration file (YAML or JSON) into a Python dictionary.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Parsed configuration as a Python dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not supported.
        Exception: If the content fails to parse.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    ext = os.path.splitext(config_path)[1].lower()

    with open(config_path, "r") as f:
        try:
            if ext in [".yaml", ".yml"]:
                return yaml.safe_load(f)
            elif ext == ".json":
                return json.load(f)
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
        except Exception as e:
            raise Exception(f"Failed to parse config file '{config_path}': {e}")


class WorkflowConfigValidationError(Exception):
    """Custom error raised when validation of the workflow config fails."""
    pass

def validate_workflow_config(config: Dict[str, Any]) -> None:
    """
    Validate the structure of a workflow config loaded from JSON or YAML.

    Args:
        config (dict): The workflow configuration.

    Raises:
        WorkflowConfigValidationError: If the config is invalid.
    """

    if "flow" not in config:
        raise WorkflowConfigValidationError("Missing top-level key: 'flow'")

    flow = config["flow"]

    required_flow_keys = ["name", "execute_type", "global_config", "sequence"]
    for key in required_flow_keys:
        if key not in flow:
            raise WorkflowConfigValidationError(f"Missing key in 'flow': '{key}'")

    if not isinstance(flow["sequence"], list) or len(flow["sequence"]) == 0:
        raise WorkflowConfigValidationError("'flow.sequence' must be a non-empty list")

    for idx, step in enumerate(flow["sequence"]):
        for required_step_key in ["name", "transform", "params", "input_edges", "output_edges"]:
            if required_step_key not in step:
                raise WorkflowConfigValidationError(
                    f"Step {idx} missing required key: '{required_step_key}'"
                )

        if not isinstance(step["input_edges"], list) or not isinstance(step["output_edges"], list):
            raise WorkflowConfigValidationError(
                f"Step {idx} 'input_edges' and 'output_edges' must be lists"
            )

    data_access = flow["global_config"].get("data_access", {})
    if "batch_size" in data_access and not isinstance(data_access["batch_size"], int):
        raise WorkflowConfigValidationError("'batch_size' must be an integer")

    if "files_to_use" in data_access and not isinstance(data_access["files_to_use"], list):
        raise WorkflowConfigValidationError("'files_to_use' must be a list")

    # Optional: validate s3_credentials fields are present (not empty)
    if flow["global_config"].get("data_storage_type") == "s3":
        s3_creds = data_access.get("s3_credentials", {})
        for key in ["access_key", "secret_key", "url"]:
            if key not in s3_creds:
                raise WorkflowConfigValidationError(f"Missing S3 credential field: '{key}'")

        if "s3_config" not in data_access:
            raise WorkflowConfigValidationError(f"Missing required config for s3 input/output")

    else:
        if "local_config" not in data_access:
            raise WorkflowConfigValidationError(f"Missing required config for local input/output")
