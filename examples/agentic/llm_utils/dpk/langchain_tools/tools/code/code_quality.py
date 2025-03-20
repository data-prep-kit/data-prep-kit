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


class CodeQualityInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for CodeQualityTransform."""

    cq_contents_column_name: Optional[str] = Field(
        None,
        description="Name of the column holds the data to process",
    )
    cq_language_column_name: Optional[str] = Field(
        None,
        description="Name of the column holds the programming language details",
    )
    cq_tokenizer: Optional[str] = Field(
        None,
        description="Name or path to the tokenizer.",
    )
    cq_hf_token: Optional[str] = Field(
        None,
        description="Huggingface auth token to download and use the tokenizer.",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(CodeQualityInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


class CodeQualityTransform(BaseTool):
    """Tool that apples Code Quality transform."""

    name: str = "code_quality"
    args_schema: Type[BaseModel] = CodeQualityInput
    description: str = "Apply code_quality transform on files in input folder"

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
                from code_quality_transform_ray import (
                    CodeQualityRayTransformConfiguration,
                )
                from data_processing_ray.runtime.ray import RayTransformLauncher

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = RayTransformLauncher(CodeQualityRayTransformConfiguration())

            elif runtime_type.strip().lower() == "python":
                from data_processing.runtime.pure_python import PythonTransformLauncher
                from code_quality_transform_python import (
                    CodeQualityPythonTransformConfiguration,
                )

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = PythonTransformLauncher(
                    CodeQualityPythonTransformConfiguration()
                )

            else:
                return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in code quality transform - {runtime_type}."
            print(f"launching transform with params: {transform_params}")
            return_code = launcher.launch()
            if return_code != 0:
                return "Error code quality Job Failed"
            return f"code quality transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
        except Exception as e:
            return "Error: " + str(e)
