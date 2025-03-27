import logging
from typing import Optional, Type
import sys

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from llm_utils.dpk.dpk_common import (
    DPKDataAccessInput,
    DPKRuntimeInput,
    add_runtime_params,
    add_data_access_params,
)
from data_processing.utils import ParamsUtils


class ResizeInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for ResizeTransform."""

    resize_max_rows_per_table: Optional[int] = Field(
        None,
        description="Max number of rows per table",
    )
    resize_max_mbytes_per_table: Optional[float] = Field(
        None,
        description="Max table size (MB). Size is measured according to the --resize_size_type parameter",
    )
    resize_size_type: Optional[str] = Field(
        None,
        description="Determines how memory is measured when using the --resize_max_mbytes_per_table option.",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(ResizeInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


class ResizeTransform(BaseTool):
    """Tool that apples Code Quality transform."""

    name: str = "resize"
    args_schema: Type[BaseModel] = ResizeInput
    description: str = "Apply resize transform on files in input folder"

    def _run(
        self,
        input_folder: str = "",
        output_folder: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> str:
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
                from resize_transform_ray import (
                    ResizeRayTransformConfiguration,
                )
                from data_processing_ray.runtime.ray import RayTransformLauncher

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = RayTransformLauncher(ResizeRayTransformConfiguration())

            elif runtime_type.strip().lower() == "python":
                from data_processing.runtime.pure_python import PythonTransformLauncher
                from resize_transform_python import (
                    ResizePythonTransformConfiguration,
                )

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = PythonTransformLauncher(ResizePythonTransformConfiguration())

            else:
                return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in resize transform - {runtime_type}."
            print(f"launching transform with params: {transform_params}")
            return_code = launcher.launch()
            if return_code != 0:
                return "Error resize Job Failed"
            return f"resize transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
        except Exception as e:
            return "Error: " + str(e)
