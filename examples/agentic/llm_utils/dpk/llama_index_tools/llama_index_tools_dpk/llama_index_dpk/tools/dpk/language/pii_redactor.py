import logging
from typing import Optional, Type
import sys
from typing import Any

from pydantic import BaseModel, Field

from llm_utils.dpk.dpk_common import (
    DPKDataAccessInput,
    DPKRuntimeInput,
    add_runtime_params,
    add_data_access_params,
)
from data_processing.utils import ParamsUtils

logger = logging.getLogger(__name__)


class PIIRedactorInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for PIIRedactorTransform."""

    pii_redactor_entities: Optional[str] = Field(
        None,
        description="List of entities to be redacted from the input data: {json.dumps(default_supported_entities, indent=2, default=str)}. ",
    )
    pii_redactor_operator: Optional[str] = Field(
        None,
        description="Redaction technique to be applied on detected pii data. Supported techniques redact, replace. ",
    )
    pii_redactor_transformed_contents: Optional[str] = Field(
        None,
        description="Mention column name in which transformed contents will be added. ",
    )
    pii_redactor_score_threshold: Optional[float] = Field(
        None,
        description="The score_threshold is a parameter that "
                    "sets the minimum confidence score required for an entity to be considered a match."
                    "Provide a value above 0.6 ",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(PIIRedactorInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


def pii_redactor(**kwargs: Any) -> str:
    """Tool that apples pii_redactor transform."""

    kwargs = kwargs.get("kwargs", None)

    input_folder = kwargs.get("input_folder", "")
    output_folder = kwargs.get("output_folder", "")

    if input_folder == "" or output_folder == "":
        return "Error: input folder or output folder are missing"
    try:
        runtime_type = kwargs.get("runtime_type", "python")
        data_type = kwargs.get("data_type", "local")
        transform_params = {
            "input_folder": input_folder,
            "output_folder": output_folder,
        }
        add_runtime_params(transform_params, runtime_type, kwargs)
        add_data_access_params(transform_params, data_type, kwargs)
        add_transform_params(transform_params, kwargs)

        if runtime_type.strip().lower() == "ray":
            from pii_redactor_transform_ray import (
                PIIRedactorRayTransformConfiguration,
            )
            from data_processing_ray.runtime.ray import RayTransformLauncher

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = RayTransformLauncher(PIIRedactorRayTransformConfiguration())

        elif runtime_type.strip().lower() == "python":
            from data_processing.runtime.pure_python import PythonTransformLauncher
            from pii_redactor_transform_python import (
                PIIRedactorPythonTransformConfiguration,
            )

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = PythonTransformLauncher(
                PIIRedactorPythonTransformConfiguration()
            )

        else:
            return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in pii_redactor transform - {runtime_type}."
        print(f"launching transform with params: {transform_params}")
        return_code = launcher.launch()
        if return_code != 0:
            return "Error pii_redactor Job Failed"

        return f"pii_redactor transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
    except Exception as e:
        return "Error: " + str(e)
