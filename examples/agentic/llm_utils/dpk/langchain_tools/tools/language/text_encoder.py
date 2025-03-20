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


class TextEncoderInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for TextEncoderTransform."""

    text_encoder_content_column_name: Optional[str] = Field(
        None,
        description="Name of the column containing the text to be encoded.",
    )
    text_encoder_output_embeddings_column_name: Optional[str] = Field(
        None,
        description="Column name to store the embeddings in the output table.",
    )
    text_encoder_model_name: Optional[str] = Field(
        None,
        description="The HF model to use for encoding the text.",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(TextEncoderInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


class TextEncoderTransform(BaseTool):
    """Tool that apples text_encoder transform."""

    name: str = "text_encoder"
    args_schema: Type[BaseModel] = TextEncoderInput
    description: str = "Apply text_encoder transform on files in input folder"

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
                from dpk_text_encoder.ray.transform import TextEncoderRayTransformConfiguration
                from data_processing_ray.runtime.ray import RayTransformLauncher

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = RayTransformLauncher(TextEncoderRayTransformConfiguration())

            elif runtime_type.strip().lower() == "python":
                from data_processing.runtime.pure_python import PythonTransformLauncher
                from dpk_text_encoder.transform_python import TextEncoderPythonTransformConfiguration

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = PythonTransformLauncher(
                    TextEncoderPythonTransformConfiguration()
                )

            else:
                return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in text_encoder transform - {runtime_type}."
            print(f"launching transform with params: {transform_params}")
            return_code = launcher.launch()
            if return_code != 0:
                return "Error text_encoder Job Failed"

            return f"text_encoder transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
        except Exception as e:
            return "Error: " + str(e)
