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


class TokenizationInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for TokenizationTransform."""

    tkn_tokenizer: Optional[int] = Field(
        None,
        description="Tokenizer used for tokenization. It also can be a path to a pre-trained tokenizer. By default, `hf-internal-testing/llama-tokenizer` from HuggingFace is used",
    )
    tkn_tokenizer_args: Optional[int] = Field(
        None,
        description="Arguments for tokenizer. For example, `cache_dir=/tmp/hf,use_auth_token=Your_HF_authentication_token` could be arguments for `bigcode/starcoder`",
    )
    tkn_doc_id_column: Optional[int] = Field(
        None,
        description="Column contains document id which values should be unique across dataset",
    )
    tkn_doc_content_column: Optional[int] = Field(
        None,
        description="Column contains document content",
    )
    tkn_text_lang: Optional[int] = Field(
        None,
        description="Specify language used in text content for better text splitting if needed",
    )
    tkn_chunk_size: Optional[int] = Field(
        None,
        description="Specify >0 value to tokenize each row/text in chunks of characters (rounded in words)",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(TokenizationInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


class TokenizationTransform(BaseTool):  # type: ignore[override, override]
    """Tool that apples tokenization transform."""

    name: str = "tokenization"
    args_schema: Type[BaseModel] = TokenizationInput
    description: str = "Apply Tokenization transform on files in input folder"

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
                from data_processing_ray.runtime.ray import RayTransformLauncher
                from dpk_tokenization.ray.transform import TokenizationRayConfiguration

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = RayTransformLauncher(TokenizationRayConfiguration())

            elif runtime_type.strip().lower() == "python":
                from data_processing.runtime.pure_python import PythonTransformLauncher
                from dpk_tokenization.transform_python import TokenizationPythonConfiguration

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = PythonTransformLauncher(TokenizationPythonConfiguration())

            else:
                return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in tokenization transform - {runtime_type}."
            print(f"Launching transform with params: {transform_params}")
            return_code = launcher.launch()
            if return_code != 0:
                return "Error Tokenization Job Failed"

            return f"Tokenization transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
        except Exception as e:
            return "Error!!: " + str(e)
