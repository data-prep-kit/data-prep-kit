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


class Code2ParquetInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for Code2ParquetTransform."""

    code2parquet_supported_langs_file: Optional[str] = Field(
        None,
        description="set the `supported_langs_file` configuration key.",
    )
    code2parquet_detect_programming_lang: Optional[str] = Field(
        None,
        description="set the `detect_programming_lang` configuration key.",
    )
    code2parquet_snapshot: Optional[str] = Field(
        None,
        description="set the `snapshot` configuration key.",
    )
    code2parquet_domain: Optional[str] = Field(
        None,
        description="set the `domain` configuration key.",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(Code2ParquetInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


def code2parquet(**kwargs: Any) -> str:
    """Tool that apples code2parquet transform."""

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
            from code2parquet_transform_ray import (
                CodeToParquetRayConfiguration,
            )
            from data_processing_ray.runtime.ray import RayTransformLauncher

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = RayTransformLauncher(CodeToParquetRayConfiguration())

        elif runtime_type.strip().lower() == "python":
            from data_processing.runtime.pure_python import PythonTransformLauncher
            from code2parquet_transform_python import (
                CodeToParquetPythonConfiguration,
            )

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = PythonTransformLauncher(CodeToParquetPythonConfiguration())

        else:
            return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in code2parquet transform - {runtime_type}."
        print(f"launching transform with params: {transform_params}")
        return_code = launcher.launch()
        if return_code != 0:
            return "Error code2parquet Job Failed"

        return f"code2parquet transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
    except Exception as e:
        return "Error: " + str(e)
