# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

from typing import Any, NamedTuple

import kfp.compiler as compiler
import kfp.components as comp
import kfp.dsl as dsl
from universal.doc_id.kfp_ray.doc_id_wf import doc_id
from universal.ededup.kfp_ray.ededup_wf import ededup
from universal.noop.kfp_ray.noop_wf import noop

from kfp import dsl


noop_image = "quay.io/dataprep1/data-prep-kit/noop-ray:latest"
doc_id_image = "quay.io/dataprep1/data-prep-kit/doc_id-ray:latest"
ededup_image = "quay.io/dataprep1/data-prep-kit/ededup-ray:latest"

# A list of the transform names, arranged in the order of their execution within the superpipeline.
ordered_transforms = ["noop", "doc_id", "ededup"]

def _remove_unused_params(d: dict[str, Any], remove_params: list = None) -> None:
    d.pop("input_path", None)
    d.pop("output_path", None)
    d.pop("intermediate_path", None)
    d.pop("name", None)
    d.pop("overriding_params", None)
    if remove_params is None or remove_params == []:
        return

    for param in remove_params:
        d.pop(param)
    return

@dsl.component
def prepare_params(first_transfom_input_path: str, final_output_path: str, intermediate_path: str,
        current_task_index: int, ordered_transforms: list) -> str:
    """
    This method prepares the data_s3_config parameter
    :param first_transfom_input_path: input path of the first transform step
    :param final_output_path: output path of the last transform step
    :param intermediate_path: path of the intermediate transforms outputs
    :param current_task_index: the index of the current transform
    :param ordered_transforms: A list of the transform names, 
           arranged in the order of their execution within the superpipeline
    :return: data_s3_config
    """
    input_path = first_transfom_input_path
    output_path = final_output_path

    # Calculate the directories of nested pipelines within the intermediate path.
    if current_task_index != 0:
        input_path = intermediate_path + "/" + ordered_transforms[current_task_index - 1]
    if current_task_index != len(ordered_transforms) -  1:
        output_path = intermediate_path + "/" + ordered_transforms[current_task_index]
        
    data_s3_config = "{'input_folder': '" + input_path + "', 'output_folder': '" + output_path + "'}"
    return data_s3_config


@dsl.pipeline
def super_pipeline(
    # the super pipeline parameters
    p1_pipeline_runtime_pipeline_id: str = "pipeline_id",
    p1_pipeline_server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    p1_pipeline_input_path: str = "test/doc_id/input/",
    p1_pipeline_output_path: str = "test/super/output/",
    p1_pipeline_intermediate_path: str = "test/super/output/tmp",
    p1_pipeline_additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
    p1_pipeline_data_s3_access_secret: str = "s3-secret",
    p1_pipeline_runtime_code_location: dict = {"github": "github", "commit_hash": "12345", "path": "path"},
    p1_pipeline_runtime_actor_options: dict = {"num_cpus": 0.8},
    # data access
    p1_pipeline_data_max_files: int = -1,
    p1_pipeline_data_num_samples: int = -1,
    p1_pipeline_data_checkpointing: bool = False,
    p1_pipeline_ray_run_id_KFPv2: str = "",
    # noop step parameters
    p2_name: str = "noop",
    p2_noop_sleep_sec: int = 10,
    p2_ray_name: str = "noop-kfp-ray",
    p2_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": noop_image},
    p2_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
        "image": noop_image,
    },
    # Document ID step parameters
    p3_name: str = "doc_id",
    p3_ray_name: str = "docid-kfp-ray",
    p3_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": doc_id_image},
    p3_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
        "image": doc_id_image,
    },
    # orchestrator
    p3_data_data_sets: str = "",
    p3_data_files_to_use: str = "['.parquet']",
    # doc id parameters
    p3_doc_id_doc_column: str = "contents",
    p3_doc_id_hash_column: str = "hash_column",
    p3_doc_id_int_column: str = "int_id_column",
    p3_doc_id_start_id: int = 0,
    # ededup step parameters
    p4_name: str = "ededup",
    p4_ray_name: str = "ededup-kfp-ray",
    p4_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": ededup_image},
    p4_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
        "image": ededup_image,
    },
    # ededup parameters
    p4_ededup_n_samples: int = 10,
    p4_ededup_hash_cpu: float = 0.5,
    p4_ededup_doc_column: str = "contents",
    p4_ededup_use_snapshot: bool = False,
    p4_ededup_snapshot_directory: str = "",
):
    args = locals()
    common_params_prefix = "p1_pipeline_"
    # split the input parameters according to thier prefixes.
    common_params = {
        key[len(common_params_prefix) :]: value for key, value in args.items() if key.startswith(common_params_prefix)
    }
    # get the input path, output path of the whole pipeline, and the intermediate path for storing the files between the transforms
    input_path = common_params.get("input_path", "")
    output_path = common_params.get("output_path", "")
    intermediate_path=common_params.get("intermediate_path")

    # The index of the current task
    # It is used to calculate the directories of nested pipelines within the intermediate path.
    task_index: int = 0
    
    def _set_step(nested_pipeline, execute_after = None, remove_params: list = None):
        """
        Add a transform task step
        :param nested_pipeline: the transform module to execute in this pipeline step
        :param execute_after: the transform module to execute before this pipeline step
        :param remove_params: a list of params to remove for this step
        :return: the task
        """
        nonlocal task_index
        nonlocal common_params
        
        prefix = "p" + str(task_index + 2) + "_"
        task_params = {
            key[len(prefix):]: value for key, value in args.items() if key.startswith(prefix)
        }
        pipeline_prms_to_pass = common_params | task_params
        _remove_unused_params(pipeline_prms_to_pass, remove_params)
        data_config = prepare_params(first_transfom_input_path=input_path, final_output_path=output_path,
                                     intermediate_path=intermediate_path,
                                     current_task_index=task_index, ordered_transforms=ordered_transforms)
        pipeline_prms_to_pass["data_s3_config"] = data_config.output
        task = nested_pipeline(**pipeline_prms_to_pass)
        if execute_after is not None:
            task.after(execute_after)
        # increment the task index
        task_index = task_index + 1
        return task
       
    noop_task = _set_step(noop)
    doc_id_task = _set_step(doc_id, noop_task)
    # checkpointing is not supported by ededup
    _set_step(ededup, doc_id_task, ["data_checkpointing"])

if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(super_pipeline, __file__.replace(".py", ".yaml"))
