from typing import Optional
from pydantic import Field
import sys
from data_processing.utils import ParamsUtils


class DPKDataAccessInput:
    """DPK Input for Data access params"""

    data_type: str = Field(
        "local", description="type of the data access can be one of local, s3"
    )
    output_folder: str = Field("", description="ast string containing output folder.")
    input_folder: str = Field("", description="string containing input folder.")
    data_s3_cred: Optional[str] = Field(
        None,
        description="AST string of options for s3 credentials. Only required for S3 data access.",
    )
    data_max_files: Optional[int] = Field(
        None, description="Max amount of files to process"
    )
    data_checkpointing: Optional[str] = Field(None, description="checkpointing flag")
    data_files_to_checkpoint: Optional[str] = Field(
        None, description="list of file extensions to choose for checkpointing."
    )
    data_data_sets: Optional[str] = Field(
        None,
        description="List of sub-directories of input directory to use for input. For example, ['dir1', 'dir2']",
    )
    data_files_to_use: Optional[str] = Field(
        None, description="list of file extensions to choose for input."
    )
    data_num_samples: Optional[str] = Field(
        None, description="number of random input files to process"
    )


worker_options = {"num_cpus": 0.8}


class DPKRuntimeInput:
    """DPK Input for Runtime params"""

    runtime_type: str = Field(
        "python", description="type of the runtime can be one of python, ray or spark"
    )
    run_locally: Optional[str] = Field(None, description="running ray local flag")
    runtime_num_processors: Optional[str] = Field(
        None, description="size of multiprocessing pool"
    )
    runtime_pipeline_id: Optional[str] = Field(None, description="pipeline id")
    runtime_job_id: Optional[str] = Field(None, description="job id")
    runtime_code_location: Optional[str] = Field(
        None, description="AST string containing code location"
    )
    runtime_num_workers: Optional[int] = Field(None, description="number of workers")
    runtime_worker_options: Optional[str] = Field(
        ParamsUtils.convert_to_ast(worker_options),
        description="AST string defining worker resource requirements.",
    )
    runtime_creation_delay: Optional[int] = Field(
        None, description="delay between actor creation"
    )


def add_runtime_params(transform_params: dict, runtime_type: str, kwargs):
    """Add parameters related to runtime"""

    def _remove_ray_runtime_params():
        transform_params.pop("run_locally", None)
        transform_params.pop("runtime_worker_options", None)
        transform_params.pop("runtime_num_workers", None)
        transform_params.pop("runtime_creation_delay", None)

    fields = list(DPKRuntimeInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]
    if runtime_type.strip().lower() == "python":
        _remove_ray_runtime_params()
    transform_params.pop("runtime_type", None)


def add_data_access_params(transform_params: dict, data_type: str, kwargs):
    """Add parameters related to data access"""

    def _get_data_access_key():
        if data_type.strip().lower() == "local":
            return "data_local_config"
        elif data_type.strip().lower() == "s3":
            return "data_s3_config"
        else:
            print(f"Unrecognizable type of TransformRuntimeConfiguration - {data_type}")
        sys.exit(1)

    input_folder = transform_params.get("input_folder", "")
    output_folder = transform_params.get("output_folder", "")
    data_conf = {
        "input_folder": f"{input_folder}",
        "output_folder": f"{output_folder}",
    }
    data_key = _get_data_access_key()
    transform_params[data_key] = ParamsUtils.convert_to_ast(data_conf)
    fields = list(DPKDataAccessInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]
    transform_params.pop("input_folder", None)
    transform_params.pop("output_folder", None)
    transform_params.pop("data_type", None)


def check_params(transform_params: dict, kwargs):
    """A basic check for the transform params"""
    # input/output path are added as one param to the final transform params
    if len(transform_params) != len(kwargs) + 1:
        print("Warning: unexpected parameter provided for the transform")
        print(kwargs.keys())
