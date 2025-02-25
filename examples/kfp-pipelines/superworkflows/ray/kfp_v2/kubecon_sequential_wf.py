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
from universal.ededup.kfp_ray.ededup_wf import ededup
from language.lang_id.kfp_ray.lang_id_wf import lang_id
from language.pii_redactor.kfp_ray.pii_redactor_wf import pii_redactor
from universal.filter.kfp_ray.filter_wf import filtering
from universal.tokenization.kfp_ray.tokenization_wf import tokenization

from kfp import dsl

ededup_image = "quay.io/dataprep1/data-prep-kit/ededup-ray:latest"
lang_id_image = "quay.io/dataprep1/data-prep-kit/lang_id-ray:latest"
pii_redactor_image = "quay.io/dataprep1/data-prep-kit/pii_redactor-ray:latest"
filter_image = "quay.io/dataprep1/data-prep-kit/filter-ray:latest"
tokenization_image = "quay.io/dataprep1/data-prep-kit/tokenization-ray:latest"
doc_quality_image = "quay.io/dataprep1/data-prep-kit/doc_quality-ray:latest"


def _remove_unused_params(d: dict[str, Any]) -> None:
    d.pop("input_path", None)
    d.pop("output_path", None)
    d.pop("intermediate_path", None)
    d.pop("skip", None)
    d.pop("name", None)
    d.pop("overriding_params", None)
    return


@dsl.component
def prepare_params(input_path: str, output_path: str) -> str:
    data_s3_config = "{'input_folder': '" + input_path + "', 'output_folder': '" + output_path + "'}"
    return data_s3_config


@dsl.pipeline
def super_pipeline_sequential(
    # the super pipeline parameters
    p0_pipeline_runtime_pipeline_id: str = "pipeline_id",
    p0_pipeline_server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    p0_pipeline_input_path: str = "test/ededup/input/",
    p0_pipeline_output_path: str = "test/super/output/",
    p0_pipeline_intermediate_path: str = "test/super/output/tmp",
    p0_pipeline_additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
    p0_pipeline_data_s3_access_secret: str = "s3-secret",
    p0_pipeline_runtime_code_location: dict = {"github": "github", "commit_hash": "12345", "path": "path"},
    p0_pipeline_runtime_actor_options: dict = {"num_cpus": 0.8},
    # data access
    p0_pipeline_data_max_files: int = -1,
    p0_pipeline_data_num_samples: int = -1,
    #p1_pipeline_data_checkpointing: bool = False,
    p0_pipeline_ray_run_id_KFPv2: str = "123",

    # ededup step parameters
    p1_name: str = "ededup",
    p1_ray_name: str = "ededup-kfp-ray",
    p1_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": ededup_image},
    p1_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
        "image": ededup_image,
    },
    p1_ededup_hash_cpu: float = 0.5,
    p1_ededup_doc_column: str = "contents",
    #p1_ededup_use_snapshot: bool = False,
    #p1_ededup_snapshot_directory: str = "",
    # data sampling
    p1_ededup_n_samples: int = 10,
    # Language ID step parameters
    p2_name: str = "lang_id",
    p2_ray_name: str = "langid-kfp-ray",
    p2_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": lang_id_image},
    p2_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
        "image": lang_id_image,
    },
    p2_lang_id_model_credential: str = "PUT YOUR OWN HUGGINGFACE CREDENTIAL",
    p2_lang_id_model_kind: str = "fasttext",
    p2_lang_id_model_url: str = "facebook/fasttext-language-identification",
    p2_lang_id_content_column_name: str = "text",
    p2_lang_id_output_lang_column_name: str = "lang",
    p2_lang_id_output_score_column_name: str = "score",

    # pii redactor step parameters
    p3_name: str = "pii_id",
    p3_ray_name: str = "pii-kfp-ray",
    p3_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": pii_redactor_image},
    p3_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
        "image": pii_redactor_image,
    },
    p3_pii_redactor_contents: str = "title",

    # filter step parameters
    p4_name: str = "filter_id",
    p4_ray_name: str = "filter-kfp-ray",
    p4_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": filter_image},
    p4_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
        "image": filter_image,
    },
    p4_filter_criteria_list: str = "['docq_total_words > 100 AND docq_total_words < 200', 'ibmkenlm_docq_perplex_score < 230']",
    p4_filter_logical_operator: str = "AND",
    p4_filter_columns_to_drop: str = "['extra', 'cluster']",

    # tokenization step parameters
    p5_name: str = "token_id",
    p5_ray_name: str = "token-kfp-ray",
    p5_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": tokenization_image},
    p5_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
        "image": tokenization_image,
    },
    p5_tkn_tokenizer: str = "hf-internal-testing/llama-tokenizer",
    p5_tkn_doc_id_column: str = "document_id",
    p5_tkn_doc_content_column: str = "contents",
    p5_tkn_text_lang: str = "en",
    p5_tkn_tokenizer_args: str = "cache_dir=/tmp/hf",
    p5_tkn_chunk_size: int = 0,

):
    args = locals()
    common_params_prefix = "p0_pipeline_"
    # transform1_prefix = "p1_"
    # transform2_prefix = "p2_"
    # transform3_prefix = "p3_"
    # transform4_prefix = "p4_"
    # transform5_prefix = "p5_"

    # split the input parameters according to their prefixes.
    common_params = {
        key[len(common_params_prefix):]: value for key, value in args.items() if key.startswith(common_params_prefix)
    }
    # task1_params = {
    #     key[len(transform1_prefix):]: value for key, value in args.items() if key.startswith(transform1_prefix)
    # }
    # task2_params = {
    #     key[len(transform2_prefix):]: value for key, value in args.items() if key.startswith(transform2_prefix)
    # }
    # task3_params = {
    #     key[len(transform2_prefix):]: value for key, value in args.items() if key.startswith(transform3_prefix)
    # }
    # task4_params = {
    #     key[len(transform2_prefix):]: value for key, value in args.items() if key.startswith(transform4_prefix)
    # }
    # task5_params = {
    #     key[len(transform2_prefix):]: value for key, value in args.items() if key.startswith(transform5_prefix)
    # }


    # get the input path, output path of the whole pipeline, and the intermediate path for storing the files between the transforms
    input_path = common_params.get("input_path", "")
    output_path = common_params.get("output_path", "")
    inter_path = common_params.get("intermediate_path", "")

    def _set_step(nested_pipeline, prefix: str, execute_after = None ):
        task_params = {
            key[len(prefix):]: value for key, value in args.items() if key.startswith(prefix)
        }
        pipeline_prms_to_pass = common_params | task_params
        # TODO check if we need it
        _remove_unused_params(pipeline_prms_to_pass)
        data_config = prepare_params(input_path=input_path, output_path=inter_path)
        pipeline_prms_to_pass["data_s3_config"] = data_config.output
        task = nested_pipeline(**pipeline_prms_to_pass)
        if execute_after is not None:
            task.after(execute_after)
        return task

    # execute the first transform
    # pipeline_prms_to_pass = common_params | task1_params
    # _remove_unused_params(pipeline_prms_to_pass)
    # # get the data config
    # data_config = prepare_params(input_path=input_path, output_path=inter_path)
    #
    # # call the noop pipeline from noop_wf.py file with the expected parameters
    # ededup_task = ededup(**pipeline_prms_to_pass)
    #
    # # execute the second transform
    # pipeline_prms_to_pass = common_params | task2_params
    # _remove_unused_params(pipeline_prms_to_pass)
    # # get the data config
    # data_config = prepare_params(input_path=inter_path, output_path=output_path)
    # pipeline_prms_to_pass["data_s3_config"] = data_config.output
    #lang_id_task = lang_id(**pipeline_prms_to_pass)
    #lang_id_task.after(ededup_task)
    ededup_task = _set_step(ededup, "p1_")
    lang_id_task = _set_step(lang_id, "p2_", ededup_task)
    filter_task = _set_step(filtering, "p4_", lang_id_task)
    tokenization_task = _set_step(tokenization, "p5_", filter_task)

    # execute the third transform
    # pipeline_prms_to_pass = common_params | task3_params
    # _remove_unused_params(pipeline_prms_to_pass)
    # # get the data config
    # data_config = prepare_params(input_path=inter_path, output_path=output_path)
    # pipeline_prms_to_pass["data_s3_config"] = data_config.output
    # pii_redactor_task = pii_redactor(**pipeline_prms_to_pass)
    # pii_redactor_task.after(lang_id_task)

    # execute the fourth transform
    # pipeline_prms_to_pass = common_params | task4_params
    # _remove_unused_params(pipeline_prms_to_pass)
    # # get the data config
    # data_config = prepare_params(input_path=inter_path, output_path=output_path)
    # pipeline_prms_to_pass["data_s3_config"] = data_config.output
    # filter_task = filtering(**pipeline_prms_to_pass)
    # filter_task.after(pii_redactor_task)

    # execute the fifth transform
    # pipeline_prms_to_pass = common_params | task5_params
    # _remove_unused_params(pipeline_prms_to_pass)
    # # get the data config
    # data_config = prepare_params(input_path=inter_path, output_path=output_path)
    # pipeline_prms_to_pass["data_s3_config"] = data_config.output
    # tokenization_task = tokenization(**pipeline_prms_to_pass)
    # tokenization_task.after(filter_task)

if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(super_pipeline_sequential, __file__.replace(".py", ".yaml"))
