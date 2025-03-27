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
    check_params,
)
from data_processing.utils import ParamsUtils


class FdedupInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for FdedupTransform."""

    operation_mode: Optional[str] = Field(
        None,
        description="operation mode for data cleanup",
    )
    contents_column: Optional[str] = Field(
        None,
        description="name of the column that stores document text",
    )
    document_id_column: Optional[str] = Field(
        None,
        description="name of the column containing document id",
    )
    seed: Optional[int] = Field(
        None,
        description="seed of the random number generator",
    )
    num_permutations: Optional[int] = Field(
        None,
        description="number of permutations to use for minhash calculation",
    )
    num_bands: Optional[int] = Field(
        None,
        description="number of permutations to use for minhash calculation",
    )
    num_minhashes_per_band: Optional[int] = Field(
        None,
        description="number of minhashes to use in each band", )
    word_shingle_size: Optional[int] = Field(
        None,
        description="number of words included in one shingle", )
    jaccard_similarity_threshold: Optional[float] = Field(
        None,
        description="jaccard similarity threshold above which two documents", )
    num_segments: Optional[int] = Field(
        None,
        description="the number of segments dividing the hashing space for each band (for scalability)", )
    services: Optional[str] = Field(
        None,
        description="Comma separated list of services to run", )
    shingle_option: Optional[str] = Field(
        None,
        description="Option used for shinglingComma separated list of services to run", )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(FdedupInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


def fdedup(**kwargs: Any) -> str:
    """Tool that apples fdedup transform."""

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
        # add_data_access_params(transform_params, data_type, kwargs)
        add_transform_params(transform_params, kwargs)
        transform_params.pop("data_type", None)

        if runtime_type.strip().lower() == "ray":
            from dpk_fdedup.ray.transform import RayServiceOrchestrator
            from dpk_fdedup.transform_python import parse_args

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            args = parse_args()
            orchestrator = RayServiceOrchestrator(global_params=args)

        elif runtime_type.strip().lower() == "python":
            from dpk_fdedup.transform_python import ServiceOrchestrator, parse_args

            sys.argv = ParamsUtils.dict_to_req(d=transform_params)
            args = parse_args()
            orchestrator = ServiceOrchestrator(global_params=args)

        else:
            return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in Fdedup transform - {runtime_type}."
        print(f"launching transform with params: {transform_params}")
        return_code = orchestrator.orchestrate()
        if return_code != 0:
            return "Error Fdedup Job Failed"

        return f"Fdedup transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
    except Exception as e:
        return "Error: " + str(e)
