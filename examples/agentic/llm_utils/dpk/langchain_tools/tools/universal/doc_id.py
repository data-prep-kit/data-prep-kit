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


class DocIDInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for DocIDTransform."""

    doc_id_doc_column: Optional[str] = Field(
        None,
        description="doc column name",
    )
    doc_id_hash_column: Optional[str] = Field(
        None,
        description="Compute document hash and place in the given named column",
    )
    doc_id_int_column: Optional[str] = Field(
        None,
        description="Compute unique integer id and place in the given named column",
    )
    doc_id_start_id: Optional[str] = Field(
        None,
        description="starting integer id",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(DocIDInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


class DocIDTransform(BaseTool):
    """Tool that apples doc id transform."""

    name: str = "doc_id"
    args_schema: Type[BaseModel] = DocIDInput
    description: str = "Apply doc_id transform on files in input folder"

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
                from dpk_doc_id.ray.transform import DocIDRayTransformRuntimeConfiguration
                from data_processing_ray.runtime.ray import RayTransformLauncher

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = RayTransformLauncher(DocIDRayTransformRuntimeConfiguration())

            elif runtime_type.strip().lower() == "python":
                from data_processing.runtime.pure_python import PythonTransformLauncher
                from dpk_doc_id.transform_python import DocIDPythonTransformRuntimeConfiguration

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = PythonTransformLauncher(
                    DocIDPythonTransformRuntimeConfiguration()
                )

            else:
                return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in doc id transform - {runtime_type}."
            print(f"launching transform with params: {transform_params}")
            return_code = launcher.launch()
            if return_code != 0:
                return "Error Job Failed"

            return f"doc_id transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
        except Exception as e:
            return "Error: " + str(e)
