import logging
from typing import Optional, Type
import sys

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


from llm_utils.dpk.dpk_common import (
    DPKDataAccessInput,
    DPKRuntimeInput,
    add_runtime_params,
    add_data_access_params,
)
from data_processing.utils import ParamsUtils

logger = logging.getLogger(__name__)


class ProgLangSelectInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for ProgLangSelectTransform."""

    proglang_select_allowed_langs: Optional[str] = Field(
        None,
        description="Path to file containing the list of languages to be matched",
    )
    proglang_select_language_column: Optional[str] = Field(
        None,
        description="The column name holding the name of the programming language assigned to the document",
    )
    proglang_select_output_column: Optional[int] = Field(
        None,
        description="he column name to add and that contains the matching information",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(ProgLangSelectInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


class ProgLangSelectTransform(BaseTool):  # type: ignore[override, override]
    """Tool that apples progLang_select transform."""

    name: str = "proglang_select"
    args_schema: Type[BaseModel] = ProgLangSelectInput
    description: str = "Apply proglang_select transform on files in input folder"

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
                from progLang_select_transform_ray import (
                    ProgLangSelectRayConfiguration,
                )
                from data_processing_ray.runtime.ray import RayTransformLauncher

                print(f"running ray with transform_params: {transform_params}")
                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = RayTransformLauncher(ProgLangSelectRayConfiguration())

            elif runtime_type.strip().lower() == "python":
                from data_processing.runtime.pure_python import PythonTransformLauncher
                from progLang_select_transform_python import (
                    ProgLangSelectPythonConfiguration,
                )

                print(f"running python with transform_params: {transform_params}")
                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = PythonTransformLauncher(ProgLangSelectPythonConfiguration())

            else:
                return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in progLang_select transform - {runtime_type}."
            print(f"launching transform with params: {transform_params}")
            return_code = launcher.launch()
            if return_code != 0:
                return "Error progLang_select Job Failed"

            return f"progLang_select transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
        except Exception as e:
            return "Error: " + str(e)
