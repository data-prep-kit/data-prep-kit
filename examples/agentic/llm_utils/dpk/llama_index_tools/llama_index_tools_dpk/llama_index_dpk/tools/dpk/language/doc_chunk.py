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


class DocChunkInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for DocChunkTransform."""

    doc_chunk_chunking_type: Optional[str] = Field(
        None,
        description="Chunking type to apply. Valid options are `li_markdown` for using the LlamaIndex, which chunks the text into fixed-sized windows of tokens.",
    )
    doc_chunk_content_column_name: Optional[str] = Field(
        None,
        description="Name of the column containing the text to be chunked.",
    )
    doc_chunk_doc_id_column_name: Optional[str] = Field(
        None,
        description="Name of the column containing the doc_id to be propagated in the output.",
    )
    doc_chunk_output_chunk_column_name: Optional[str] = Field(
        None,
        description="Column name to store the chunks in the output table. ",
    )
    doc_chunk_output_source_doc_id_column_name: Optional[str] = Field(
        None,
        description="Column name to store the `doc_id` from the input table.",
    )
    doc_chunk_output_jsonpath_column_name: Optional[str] = Field(
        None,
        description="Column name to store the document path of the chunk in the output table.",
    )
    doc_chunk_output_pageno_column_name: Optional[str] = Field(
        None,
        description="path to bad word file: local folder (file or directory) that points to bad word file. You don't have to set this parameter if you don't need to set bad words.",
    )
    doc_chunk_output_bbox_column_name: Optional[str] = Field(
        None,
        description="Column name to store the bbox of the chunk in the output table",
    )
    doc_chunk_chunk_size_tokens: Optional[int] = Field(
        None,
        description="Size of the chunk in tokens for the token text chunker.",
    )
    doc_chunk_chunk_overlap_tokens: Optional[int] = Field(
        None,
        description="Number of tokens overlapping between chunks for the token text chunker.",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(DocChunkInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


def doc_chunk(**kwargs: Any) -> str:
    """Tool that apples doc_chunk transform."""

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
            from dpk_doc_chunk.ray.transform import DocChunkRayTransformConfiguration
            from data_processing_ray.runtime.ray import RayTransformLauncher

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = RayTransformLauncher(DocChunkRayTransformConfiguration())

        elif runtime_type.strip().lower() == "python":
            from data_processing.runtime.pure_python import PythonTransformLauncher
            from dpk_doc_chunk.transform_python import DocChunkPythonTransformConfiguration

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            launcher = PythonTransformLauncher(
                DocChunkPythonTransformConfiguration()
            )
        else:
            return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in doc_chunk transform - {runtime_type}."
        print(f"launching transform with params: {transform_params}")
        return_code = launcher.launch()
        if return_code != 0:
            return "Error doc_chunk Job Failed"

        return f"doc_chunk transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
    except Exception as e:
        return "Error: " + str(e)
