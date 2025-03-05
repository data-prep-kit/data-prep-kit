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
from language.lang_id.kfp_ray.lang_id_wf import lang_id
from universal.filter.kfp_ray.filter_wf import filtering
from universal.tokenization.kfp_ray.tokenization_wf import tokenization
from language.doc_quality.kfp_ray.doc_quality_wf import doc_quality


from kfp import dsl


ededup_image = "quay.io/dataprep1/data-prep-kit/ededup-ray:latest"
lang_id_image = "quay.io/dataprep1/data-prep-kit/lang_id-ray:latest"
doc_id_image = "quay.io/dataprep1/data-prep-kit/doc_id-ray:latest"
filter_image = "quay.io/dataprep1/data-prep-kit/filter-ray:latest"
tokenization_image = "quay.io/dataprep1/data-prep-kit/tokenization-ray:latest"
doc_quality_image = "quay.io/dataprep1/data-prep-kit/doc_quality-ray:latest"

# A list of the transform names, arranged in the order of their execution within the super-pipeline.
ordered_transforms = ["ededup", "doc_id", "doc_quality", "filter", "tokenization"]

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
    p1_pipeline_input_path: str = "test/ededup/input/",
    p1_pipeline_output_path: str = "test/super/output_v2/",
    p1_pipeline_intermediate_path: str = "test/super/output/tmp_v2",
    p1_pipeline_additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
    p1_pipeline_data_s3_access_secret: str = "s3-secret",
    p1_pipeline_runtime_code_location: dict = {"github": "github", "commit_hash": "12345", "path": "path"},
    p1_pipeline_runtime_actor_options: dict = {"num_cpus": 0.8},
    # data access
    p1_pipeline_data_max_files: int = -1,
    p1_pipeline_data_num_samples: int = -1,
    p1_pipeline_data_checkpointing: bool = False,
    p1_pipeline_ray_run_id_KFPv2: str = "aa",

    # ededup step parameters
    p2_name: str = "ededup",
    p2_ray_name: str = "ededup-kfp-ray",
    p2_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": ededup_image},
    p2_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
        "image": ededup_image,
    },
    # ededup parameters
    p2_ededup_n_samples: int = 10,
    p2_ededup_hash_cpu: float = 0.5,
    p2_ededup_doc_column: str = "contents",
    p2_ededup_use_snapshot: bool = False,
    p2_ededup_snapshot_directory: str = "",

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
    # p3_data_data_sets: str = "",
    p3_data_files_to_use: str = "['.parquet']",

    # doc id parameters
    p3_doc_id_doc_column: str = "contents",
    p3_doc_id_hash_column: str = "hash_column",
    p3_doc_id_int_column: str = "int_id_column",
    p3_doc_id_start_id: int = 0,

    # doc quality
    p4_name: str = "doc_quality",
    p4_ray_name: str = "doc-quality-kfp-ray",
    p4_docq_text_lang: str = "en",
    p4_docq_doc_content_column: str = "contents",
    p4_docq_bad_word_filepath: str = "/home/ray/dpk_doc_quality/ldnoobw/en",
    # overriding parameters
    p4_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": doc_quality_image},
    p4_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image_pull_secret": "",
            "image": doc_quality_image,
        },

    # filter step parameters
    p5_name: str = "filtering",
    p5_ray_name: str = "filtering-kfp-ray",
    p5_filter_criteria_list: str = "['docq_total_words > 100 AND docq_total_words < 200', 'ibmkenlm_docq_perplex_score < 230']",
    p5_filter_logical_operator: str = "AND",
    p5_filter_columns_to_drop: str = "['extra', 'cluster']",
    p5_ray_head_options: dict = {"cpu": 1, "memory": 4, "image": filter_image},
    p5_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image": filter_image,
        },

    # # tokenization1 step parameters
    p6_name: str = "tokenization",
    p6_ray_name: str = "tokenization-kfp-ray",
    p6_tkn_tokenizer: str = "hf-internal-testing/llama-tokenizer",
    p6_tkn_doc_id_column: str = "document_id",
    p6_tkn_doc_content_column: str = "contents",
    p6_tkn_text_lang: str = "en",
    p6_tkn_tokenizer_args: str = "cache_dir=/tmp/hf",
    p6_tkn_chunk_size: int = 0,
    # overriding parameters
    p6_ray_head_options: dict = {"cpu": 1, "memory": 4, "image": tokenization_image},
    p6_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image": tokenization_image,
        },

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
        print(prefix)
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
       
    ededup_task = _set_step(nested_pipeline=ededup, remove_params=["data_checkpointing"])
    doc_id_task = _set_step(doc_id, ededup_task)
    doc_quality_task = _set_step(doc_quality, doc_id_task, ["data_checkpointing"])
    filtering_task = _set_step(filtering, doc_quality_task, ["data_checkpointing"])
    tokenization_task = _set_step(tokenization, filtering_task, ["data_checkpointing"])

if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(super_pipeline, __file__.replace(".py", ".yaml"))
