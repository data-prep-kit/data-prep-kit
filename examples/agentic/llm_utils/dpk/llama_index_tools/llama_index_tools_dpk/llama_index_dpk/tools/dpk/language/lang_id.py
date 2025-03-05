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


class LangIdentificationInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for LangIdentificationTransform."""

    lang_id_model_credential: Optional[str] = Field(
        None,
        description="Credential to access model for language detection placed in url.",
    )
    lang_id_model_kind: Optional[str] = Field(
        None,
        description="Kind of model for language detection.",
    )
    lang_id_model_url: Optional[str] = Field(
        None,
        description="Url to model for language detection.",
    )
    lang_id_content_column_name: Optional[str] = Field(
        None,
        description="Column name to get content.",
    )
    lang_id_output_lang_column_name: Optional[str] = Field(
        None,
        description="Column name to store identified language.",
    )
    lang_id_output_score_column_name: Optional[str] = Field(
        None,
        description="Column name to store the score of language identification.",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(LangIdentificationInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


def lang_id(**kwargs: Any) -> str:
    """Tool that apples lang_id transform."""

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
            from dpk_lang_id.ray.transform import LangIdentificationRayTransformConfiguration
            from data_processing_ray.runtime.ray import RayTransformLauncher

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = RayTransformLauncher(
                LangIdentificationRayTransformConfiguration()
            )

        elif runtime_type.strip().lower() == "python":
            from data_processing.runtime.pure_python import PythonTransformLauncher
            from dpk_lang_id.transform_python import LangIdentificationPythonTransformConfiguration

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = PythonTransformLauncher(
                LangIdentificationPythonTransformConfiguration()
            )

        else:
            return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in lang_id transform - {runtime_type}."
        return_code = launcher.launch()
        if return_code != 0:
            return "Error Job Failed"

        return f"lang_id transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
    except Exception as e:
        return "Error: " + str(e)
