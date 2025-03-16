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
from language.doc_quality.kfp_ray.doc_quality_wf import doc_quality

from python_apiserver_client.params import (
        EnvironmentVariables,
        EnvVarFrom,
        EnvVarSource,
)

# The name of the secret that holds the HugginFace token
HF_SECRET = "hf-secret"
# The secret key that holds the HugginFace token
HF_SECRET_KEY = "hf-token"
env_v = EnvVarFrom(source=EnvVarSource.SECRET, name=HF_SECRET, key=HF_SECRET_KEY)
envs = EnvironmentVariables(from_ref={"HF_READ_ACCESS_TOKEN": env_v})



from kfp import dsl

ededup_image = "quay.io/dataprep1/data-prep-kit/ededup-ray:0.2.5.kubecon"
lang_id_image = "quay.io/dataprep1/data-prep-kit/lang_id-ray:0.2.5.kubecon"
doc_id_image = "quay.io/dataprep1/data-prep-kit/doc_id-ray:0.2.5.kubecon"
filter_image = "quay.io/dataprep1/data-prep-kit/filter-ray:0.2.5.kubecon"
doc_quality_image = "quay.io/dataprep1/data-prep-kit/doc_quality-ray:0.2.5.kubecon"

# A list of transform names, organized in the order they appear in the pipeline input parameters.
ordered_transforms_names = ["doc_id", "ededup", "lang_id",
        "filter_en", "filter_ja", "filter_fr", "doc_quality_en", "doc_quality_ja", "doc_quality_fr"]

# A list containing the names of the last transforms in the flow.
last_transforms_step = ["doc_quality_en", "doc_quality_ja", "doc_quality_fr"]

# A dict which holds for each transform the task it depends on.
prev_task_name = {
        "ededup": "doc_id",
        "lang_id": "ededup",
        "filter_en": "lang_id",
        "doc_quality_en": "filter_en",
        "filter_ja": "lang_id",
        "doc_quality_ja": "filter_ja",
        "filter_fr": "lang_id",
        "doc_quality_fr": "filter_fr",
}



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
        ordered_transforms_names: list, prev_task_name: dict, last_transforms_step: list) -> \
        NamedTuple('outputs', ededup=str, doc_id=str, lang_id=str, filter_en=str, doc_quality_en=str,
              filter_ja=str, doc_quality_ja=str, filter_fr=str, doc_quality_fr=str):
    """
    This method prepares the data_s3_config parameter
    :param first_transfom_input_path: input path of the first transform step
    :param final_output_path: output path of the last transform step
    :param intermediate_path: path of the intermediate transforms outputs
    :param ordered_transforms_names: A list of the transform names,
           arranged in the order of their execution within the superpipeline
    :param prev_task_name: A dict which holds for each transform its previous task
    :param last_transforms_step: the transforms that are executed at the end of the flow
    :return: Multiple outputs where each is the data_s3_config of the nested pipelines.
    """
    input_path = first_transfom_input_path
    data_s3_config_dict = {}

    # Calculate the directories of nested pipelines within the intermediate path.
    for i, transform_name in enumerate(ordered_transforms_names):
        if i != 0:
            input_path = intermediate_path + "/" + prev_task_name[transform_name]
        if transform_name not in last_transforms_step:
            output_path = intermediate_path + "/" + transform_name
        else:
            output_path = final_output_path + "/" + transform_name
        data_s3_config_dict[transform_name] = "{'input_folder': '" + input_path + "', 'output_folder': '" + output_path + "'}"
        print(transform_name)
        print(data_s3_config_dict[transform_name])

    # returned value of the prepare_params component which prepares the params for each task
    prepare_params_outputs = NamedTuple('outputs', doc_id=str, ededup=str, lang_id=str, filter_en=str, doc_quality_en=str,
                                        filter_ja=str, doc_quality_ja=str, filter_fr=str, doc_quality_fr=str)
    
    return prepare_params_outputs(data_s3_config_dict["doc_id"], data_s3_config_dict["ededup"], 
            data_s3_config_dict["lang_id"],
            data_s3_config_dict["filter_en"], data_s3_config_dict["doc_quality_en"],
            data_s3_config_dict["filter_ja"], data_s3_config_dict["doc_quality_ja"],
            data_s3_config_dict["filter_fr"], data_s3_config_dict["doc_quality_fr"],)


@dsl.pipeline
def super_pipeline(
        # the super pipeline parameters
        p1_pipeline_runtime_pipeline_id: str = "pipeline_id",
        p1_pipeline_server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
        p1_pipeline_input_path: str = "test/kubecon/input",
        p1_pipeline_output_path: str = "test/kubecon/output/",
        p1_pipeline_intermediate_path: str = "test/kubecon/output/tmp_v2",
        p1_pipeline_additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
        p1_pipeline_data_s3_access_secret: str = "s3-secret",
        p1_pipeline_runtime_code_location: dict = {"github": "github", "commit_hash": "12345", "path": "path"},
        p1_pipeline_runtime_actor_options: dict = {"num_cpus": 0.8},
        # data access
        p1_pipeline_data_max_files: int = -1,
        p1_pipeline_data_num_samples: int = -1,
        p1_pipeline_data_checkpointing: bool = False,
        p1_pipeline_ray_run_id_KFPv2: str = "aa",

        # Document ID step parameters
        p2_name: str = "doc_id",
        p2_ray_name: str = "docid-kfp-ray",
        p2_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": doc_id_image},
        p2_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image_pull_secret": "",
            "image": doc_id_image,
        },
        # orchestrator
        # p2_data_data_sets: str = "",
        p2_data_files_to_use: str = "['.parquet']",

        # doc id parameters
        p2_doc_id_doc_column: str = "contents",
        p2_doc_id_hash_column: str = "hash_column",
        p2_doc_id_int_column: str = "int_id_column",
        p2_doc_id_start_id: int = 0,


        # Exact dedup step parameters
        p3_name: str = "ededup",
        p3_ray_name: str = "ededup-kfp-ray",
        p3_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": "", "image": ededup_image},
        p3_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image_pull_secret": "",
            "image": ededup_image,
        },
        # ededup parameters
        p3_ededup_n_samples: int = 10,
        p3_ededup_hash_cpu: float = 0.5,
        p3_ededup_doc_column: str = "contents",
        p3_ededup_use_snapshot: bool = False,
        p3_ededup_snapshot_directory: str = "",

        # language ID step parameters
        p4_name: str = "lang_ID",
        p4_ray_name: str = "lang-id-kfp-ray",
        p4_ray_head_options: dict = {"cpu": 1, "memory": 4, "image": lang_id_image, "environment": envs.to_dict()},
        p4_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image": lang_id_image,
            "environment": envs.to_dict(),
        },
        # lang_id parameters
        p4_lang_id_model_kind: str = "fasttext",
        p4_lang_id_model_url: str = "facebook/fasttext-language-identification",
        p4_lang_id_content_column_name: str = "contents",
        p4_lang_id_output_lang_column_name: str = "lang",
        p4_lang_id_output_score_column_name: str = "score",

        # Filter EN step parameters
        p5_name: str = "filter_en",
        p5_ray_name: str = "en_filter_kfp-ray",
        p5_filter_criteria_list: str = "['lang=\\\\'en\\\\'', 'score>=0.8', 'contents!=\\\\'\\\\'']",
        p5_filter_logical_operator: str = "AND",
        p5_filter_columns_to_drop: str = "[]",
        p5_ray_head_options: dict = {"cpu": 1, "memory": 4, "image": filter_image},
        p5_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image": filter_image,
        },

        # Document EN quality step parameters
        p6_name: str = "doc_quality_en",
        p6_ray_name: str = "en_doc_quality-kfp-ray",
        p6_docq_text_lang: str = "en",
        p6_docq_doc_content_column: str = "contents",
        p6_docq_bad_word_filepath: str = "/home/ray/dpk_doc_quality/ldnoobw/en",
        p6_ray_head_options: dict = {"cpu": 1, "memory": 4, "image": doc_quality_image},
        p6_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image": doc_quality_image,
        },

        # Filter JA step parameters
        p7_name: str = "filter_ja",
        p7_ray_name: str = "ja_filter-kfp-ray",
        p7_filter_criteria_list: str = "['lang=\\\\'ja\\\\'', 'score>=0.8', 'contents!=\\\\'\\\\'']",
        p7_filter_logical_operator: str = "AND",
        p7_filter_columns_to_drop: str = "[]",
        p7_ray_head_options: dict = {"cpu": 1, "memory": 4, "image": filter_image},
        p7_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image": filter_image,
        },

        # Document JA quality step parameters
        p8_name: str = "doc_quality_ja",
        p8_ray_name: str = "ja_doc_quality-kfp-ray",
        p8_docq_text_lang: str = "ja",
        p8_docq_doc_content_column: str = "contents",
        p8_docq_bad_word_filepath: str = "/home/ray/dpk_doc_quality/ldnoobw/ja",
        p8_ray_head_options: dict = {"cpu": 1, "memory": 4, "image": doc_quality_image},
        p8_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image": doc_quality_image,
        },

        # Filter FR step parameters
        p9_name: str = "filter_fr",
        p9_ray_name: str = "fr_filter-kfp-ray",
        p9_filter_criteria_list: str = "['lang=\\\\'fr\\\\'', 'score>=0.8', 'contents!=\\\\'\\\\'']",
        p9_filter_logical_operator: str = "AND",
        p9_filter_columns_to_drop: str = "[]",
        p9_ray_head_options: dict = {"cpu": 1, "memory": 4, "image": filter_image},
        p9_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image": filter_image,
        },

        # Document FR quality step parameters
        p10_name: str = "doc_quality_fr",
        p10_ray_name: str = "fr_doc_quality-kfp-ray",
        p10_docq_text_lang: str = "fr",
        p10_docq_doc_content_column: str = "contents",
        p10_docq_bad_word_filepath: str = "/home/ray/dpk_doc_quality/ldnoobw/fr",
        p10_ray_head_options: dict = {"cpu": 1, "memory": 4, "image": doc_quality_image},
        p10_ray_worker_options: dict = {
            "replicas": 2,
            "max_replicas": 2,
            "min_replicas": 2,
            "cpu": 2,
            "memory": 4,
            "image": doc_quality_image,
        },
):
    args = locals()
    common_params_prefix = "p1_pipeline_"
    # split the input parameters according to thier prefixes.
    common_params = {
        key[len(common_params_prefix):]: value for key, value in args.items() if key.startswith(common_params_prefix)
    }
    # get the input path, output path of the whole pipeline, and the intermediate path for storing the files between the transforms
    input_path = common_params.get("input_path", "")
    output_path = common_params.get("output_path", "")
    intermediate_path = common_params.get("intermediate_path")

    # The index of the current task
    # It is used to calculate the directories of nested pipelines within the intermediate path.
    task_index: int = 0
    data_s3_config_dict = prepare_params(first_transfom_input_path=input_path, final_output_path=output_path,
            intermediate_path=intermediate_path, ordered_transforms_names=ordered_transforms_names, prev_task_name=prev_task_name, last_transforms_step=last_transforms_step)

    def _set_step(nested_pipeline, displayed_name: str, execute_after=None, remove_params: list = None):
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
        pipeline_prms_to_pass["data_s3_config"] = data_s3_config_dict.outputs[ordered_transforms_names[task_index]]
        task = nested_pipeline(**pipeline_prms_to_pass)
        if execute_after is not None:
            task.after(execute_after)
        if displayed_name is not None and len(displayed_name.strip()) > 0:
            task.set_display_name(displayed_name)
        # increment the task index
        task_index = task_index + 1
        return task

    doc_id_task = _set_step(nested_pipeline=doc_id, displayed_name="doc ID")
    ededup_task = _set_step(nested_pipeline=ededup, displayed_name="exact dedup", execute_after=doc_id_task, remove_params=["data_checkpointing"])
    lang_id_task = _set_step(nested_pipeline=lang_id, displayed_name="language ID", execute_after=ededup_task, remove_params=["data_checkpointing"])
    filter_en_task = _set_step(nested_pipeline=filtering, displayed_name="filter en", execute_after=lang_id_task, remove_params=["data_checkpointing"])
    doc_quality_en_task = _set_step(nested_pipeline=doc_quality, displayed_name="doc quality en", execute_after=filter_en_task, remove_params=["data_checkpointing"])
    filter_ja_task = _set_step(nested_pipeline=filtering, displayed_name="filter ja", execute_after=lang_id_task, remove_params=["data_checkpointing"])
    doc_quality_ja_task = _set_step(nested_pipeline=doc_quality, displayed_name="doc quality ja", execute_after=filter_ja_task, remove_params=["data_checkpointing"])
    filter_fr_task = _set_step(nested_pipeline=filtering, displayed_name="filter fr", execute_after=lang_id_task, remove_params=["data_checkpointing"])
    doc_quality_fr_task = _set_step(nested_pipeline=doc_quality, displayed_name="doc quality fr", execute_after=filter_fr_task, remove_params=["data_checkpointing"])



if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(super_pipeline, __file__.replace(".py", ".yaml"))
