import logging
from typing import Optional, Type
import sys
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from llm_utils.dpk.dpk_common import (
    DPKDataAccessInput,
    DPKRuntimeInput,
    add_runtime_params,
    add_data_access_params,
)
from data_processing.utils import ParamsUtils


class FilterInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for FilterTransform."""

    filter_criteria_list: Optional[str] = Field(
        None,
        description="list of filter criteria (in SQL WHERE clause format).",
    )
    filter_columns_to_drop: Optional[str] = Field(
        None,
        description="list of columns to drop after filtering.",
    )
    filter_logical_operator: Optional[str] = Field(
        None,
        description="Compute unique integer id and place in the given named column",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(FilterInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


def filter(**kwargs: Any) -> str:
    """Tool that apples filter transform."""

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
            from dpk_ededup.ray.transform import FilterRayTransformConfiguration
            from data_processing_ray.runtime.ray import RayTransformLauncher

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = RayTransformLauncher(FilterRayTransformConfiguration())

        elif runtime_type.strip().lower() == "python":
            from data_processing.runtime.pure_python import PythonTransformLauncher
            from dpk_filter.transform_python import (
                FilterPythonTransformConfiguration,
            )

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = PythonTransformLauncher(FilterPythonTransformConfiguration())

        else:
            return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in filter transform - {runtime_type}."
        print(f"launching transform with params: {transform_params}")
        return_code = launcher.launch()
        if return_code != 0:
            return "Error filter Job Failed"

        return f"filter transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
    except Exception as e:
        return "Error: " + str(e)
