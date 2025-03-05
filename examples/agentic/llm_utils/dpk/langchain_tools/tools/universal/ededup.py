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
    check_params,
)
from data_processing.utils import ParamsUtils


class EdedupInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for EdedupTransform."""

    ededup_doc_column: Optional[str] = Field(
        None,
        description="name of the column containing document",
    )
    ededup_doc_id_column: Optional[str] = Field(
        None,
        description="name of the column containing document id",
    )
    ededup_use_snapshot: Optional[str] = Field(
        None,
        description="flag to continue from snapshot",
    )
    ededup_snapshot_directory: Optional[str] = Field(
        None,
        description="location of snapshot files",
    )
    ededup_doc_column: Optional[str] = Field(
        None,
        description="name of the column containing document",
    )
    ededup_num_hashes: Optional[int]= Field(
        None,
        description="Number of hashes should be greater then zero",)
    ededup_hash_cpu: Optional[float]=Field(
        None,
        description="number of CPUs per hash",)


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(EdedupInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


class EdedupTransform(BaseTool):
    """Tool that apples Ededup transform."""

    name: str = "ededup"
    args_schema: Type[BaseModel] = EdedupInput
    description: str = "Apply Ededup transform on files in input folder"

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
                from dpk_ededup.ray.transform import EdedupRayTransformRuntimeConfiguration
                from data_processing_ray.runtime.ray import RayTransformLauncher
                
                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = RayTransformLauncher(EdedupRayTransformRuntimeConfiguration())

            elif runtime_type.strip().lower() == "python":
                from data_processing.runtime.pure_python import PythonTransformLauncher
                from dpk_ededup.transform_python import EdedupPythonTransformRuntimeConfiguration

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = PythonTransformLauncher(
                    EdedupPythonTransformRuntimeConfiguration()
                )
            else:
                return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in ededup transform - {runtime_type}."
            check_params(transform_params, kwargs)
            print(f"launching transform with params: {transform_params}")
            return_code = launcher.launch()
            if return_code != 0:
                return "Error ededup Job Failed"

            return f"Ededup transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
        except Exception as e:
            return "Error: " + str(e)
