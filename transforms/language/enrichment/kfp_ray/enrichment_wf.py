# SPDX-License-Identifier: Apache-2.0
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
import os

import kfp.compiler as compiler
import kfp.components as comp
import kfp.dsl as dsl
from workflow_support.compile_utils import (
    DEFAULT_KFP_COMPONENT_SPEC_PATH,
    ONE_HOUR_SEC,
    ONE_WEEK_SEC,
    ComponentUtils,
)


task_image = "quay.io/dataprep1/data-prep-kit/enrichment-ray:1.1.8"

EXEC_SCRIPT_NAME: str = "-m dpk_enrichment.ray.runtime"

# components
base_kfp_image = "quay.io/dataprep1/data-prep-kit/kfp-data-processing:1.1.8"

# path to kfp component specifications files
component_spec_path = os.getenv("KFP_COMPONENT_SPEC_PATH", DEFAULT_KFP_COMPONENT_SPEC_PATH)

# compute execution parameters. Here different transforms might need different implementations. As
# a result, instead of creating a component we are creating it in place here.
def compute_exec_params_func(
    worker_options: dict,
    actor_options: dict,
    data_s3_config: str,
    data_max_files: int,
    data_num_samples: int,
    data_checkpointing: bool,
    runtime_pipeline_id: str,
    runtime_job_id: str,
    enrichment_output_column_prefix: str,
    enrichment_content_column_name: str,
    enrichment_lang_column_name: str,
    enrichment_newline_normalized_column_name: str,
    enrichment_error_column_name: str,
    enrichment_num_newlines_column_name: str,
    enrichment_num_paragraphs_column_name: str,
    enrichment_num_words_column_name: str,
    enrichment_num_chars_column_name: str,
    enrichment_total_non_newline_chars_column_name: str,
    enrichment_avg_word_length_column_name: str,
    enrichment_avg_paragraph_length_chars_column_name: str,
    enrichment_avg_paragraph_length_words_column_name: str,
    enrichment_alphanumeric_char_ratio_column_name: str,
    enrichment_control_char_ratio_column_name: str,
    enrichment_punctuation_char_ratio_column_name: str,
    enrichment_other_symbol_char_ratio_column_name: str,
    enrichment_tabs_word_ratio_column_name: str,
    enrichment_hashes_word_ratio_column_name: str,
    enrichment_ellipsis_ratio_column_name: str,
    enrichment_bulletpoint_ratio_column_name: str,
    enrichment_dup_paragraphs_ratio_column_name: str,
    enrichment_dup_paragraphs_char_ratio_column_name: str,
    enrichment_top_2_gram_char_ratio_column_name: str,
    enrichment_top_3_gram_char_ratio_column_name: str,
    enrichment_top_4_gram_char_ratio_column_name: str,
    enrichment_dup_5_gram_char_ratio_column_name: str,
    enrichment_dup_6_gram_char_ratio_column_name: str,
    enrichment_dup_7_gram_char_ratio_column_name: str,
    enrichment_dup_8_gram_char_ratio_column_name: str,
    enrichment_dup_9_gram_char_ratio_column_name: str,
    enrichment_dup_10_gram_char_ratio_column_name: str,
) -> dict:
    from runtime_utils import KFPUtils

    return {
        "data_s3_config": data_s3_config,
        "data_max_files": data_max_files,
        "data_num_samples": data_num_samples,
        "data_checkpointing": data_checkpointing,
        "runtime_num_workers": KFPUtils.default_compute_execution_params(str(worker_options), str(actor_options)),
        "runtime_worker_options": str(actor_options),
        "runtime_pipeline_id": runtime_pipeline_id,
        "runtime_job_id": runtime_job_id,
        "enrichment_output_column_prefix": enrichment_output_column_prefix,
        "enrichment_content_column_name": enrichment_content_column_name,
        "enrichment_lang_column_name": enrichment_lang_column_name,
        "enrichment_newline_normalized_column_name": enrichment_newline_normalized_column_name,
        "enrichment_error_column_name": enrichment_error_column_name,
        "enrichment_num_newlines_column_name": enrichment_num_newlines_column_name,
        "enrichment_num_paragraphs_column_name": enrichment_num_paragraphs_column_name,
        "enrichment_num_words_column_name": enrichment_num_words_column_name,
        "enrichment_num_chars_column_name": enrichment_num_chars_column_name,
        "enrichment_total_non_newline_chars_column_name": enrichment_total_non_newline_chars_column_name,
        "enrichment_avg_word_length_column_name": enrichment_avg_word_length_column_name,
        "enrichment_avg_paragraph_length_chars_column_name": enrichment_avg_paragraph_length_chars_column_name,
        "enrichment_avg_paragraph_length_words_column_name": enrichment_avg_paragraph_length_words_column_name,
        "enrichment_alphanumeric_char_ratio_column_name": enrichment_alphanumeric_char_ratio_column_name,
        "enrichment_control_char_ratio_column_name": enrichment_control_char_ratio_column_name,
        "enrichment_punctuation_char_ratio_column_name": enrichment_punctuation_char_ratio_column_name,
        "enrichment_other_symbol_char_ratio_column_name": enrichment_other_symbol_char_ratio_column_name,
        "enrichment_tabs_word_ratio_column_name": enrichment_tabs_word_ratio_column_name,
        "enrichment_hashes_word_ratio_column_name": enrichment_hashes_word_ratio_column_name,
        "enrichment_ellipsis_ratio_column_name": enrichment_ellipsis_ratio_column_name,
        "enrichment_bulletpoint_ratio_column_name": enrichment_bulletpoint_ratio_column_name,
        "enrichment_dup_paragraphs_ratio_column_name": enrichment_dup_paragraphs_ratio_column_name,
        "enrichment_dup_paragraphs_char_ratio_column_name": enrichment_dup_paragraphs_char_ratio_column_name,
        "enrichment_top_2_gram_char_ratio_column_name": enrichment_top_2_gram_char_ratio_column_name,
        "enrichment_top_3_gram_char_ratio_column_name": enrichment_top_3_gram_char_ratio_column_name,
        "enrichment_top_4_gram_char_ratio_column_name": enrichment_top_4_gram_char_ratio_column_name,
        "enrichment_dup_5_gram_char_ratio_column_name": enrichment_dup_5_gram_char_ratio_column_name,
        "enrichment_dup_6_gram_char_ratio_column_name": enrichment_dup_6_gram_char_ratio_column_name,
        "enrichment_dup_7_gram_char_ratio_column_name": enrichment_dup_7_gram_char_ratio_column_name,
        "enrichment_dup_8_gram_char_ratio_column_name": enrichment_dup_8_gram_char_ratio_column_name,
        "enrichment_dup_9_gram_char_ratio_column_name": enrichment_dup_9_gram_char_ratio_column_name,
        "enrichment_dup_10_gram_char_ratio_column_name": enrichment_dup_10_gram_char_ratio_column_name,
    }


# KFPv1 and KFP2 uses different methods to create a component from a function. KFPv1 uses the
# `create_component_from_func` function, but it is deprecated by KFPv2 and so has a different import path.
# KFPv2 recommends using the `@dsl.component` decorator, which doesn't exist in KFPv1. Therefore, here we use
# this if/else statement and explicitly call the decorator.
if os.getenv("KFPv2", "0") == "1":
    compute_exec_params_op = dsl.component_decorator.component(
        func=compute_exec_params_func, base_image=base_kfp_image
    )
else:
    compute_exec_params_op = comp.create_component_from_func(func=compute_exec_params_func, base_image=base_kfp_image)

# create Ray cluster
create_ray_op = comp.load_component_from_file(component_spec_path + "createRayClusterComponent.yaml")
# execute job
execute_ray_jobs_op = comp.load_component_from_file(component_spec_path + "executeRayJobComponent.yaml")
# clean up Ray
cleanup_ray_op = comp.load_component_from_file(component_spec_path + "deleteRayClusterComponent.yaml")

# Task name is part of the pipeline name, the ray cluster name and the job name in DMF.
TASK_NAME: str = "enrichment"


@dsl.pipeline(
    name=TASK_NAME + "-ray-pipeline",
    description="computes a number of features that can be used estimate data quality",
)
def enrichment(
    # Ray cluster
    ray_name: str = "enrichment-kfp-ray",  # name of Ray cluster
    ray_run_id_KFPv2: str = "",  # Ray cluster unique ID used only in KFP v2
    # Add image_pull_secret and image_pull_policy to ray workers if needed
    ray_head_options: dict = {"cpu": 1, "memory": 4, "image": task_image},
    ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image": task_image,
    },
    server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    # data access
    data_s3_config: str = "{'input_folder': 'test/enrichment/input/', 'output_folder': 'test/enrichment/output/'}",
    data_s3_access_secret: str = "s3-secret",
    data_max_files: int = -1,
    data_num_samples: int = -1,
    data_checkpointing: bool = False,
    # orchestrator
    runtime_actor_options: dict = {"num_cpus": 0.8},
    runtime_pipeline_id: str = "pipeline_id",
    # enrichment parameters
    enrichment_output_column_prefix: str = "e_",
    enrichment_content_column_name: str = "text",
    enrichment_lang_column_name: str = "lang",
    enrichment_newline_normalized_column_name: str = "",
    enrichment_error_column_name: str = "",
    enrichment_num_newlines_column_name: str = "num_newlines",
    enrichment_num_paragraphs_column_name: str = "num_paragraphs",
    enrichment_num_words_column_name: str = "num_words",
    enrichment_num_chars_column_name: str = "num_chars",
    enrichment_total_non_newline_chars_column_name: str = "total_non_newline_chars",
    enrichment_avg_word_length_column_name: str = "avg_word_length",
    enrichment_avg_paragraph_length_chars_column_name: str = "avg_paragraph_length_chars",
    enrichment_avg_paragraph_length_words_column_name: str = "avg_paragraph_length_words",
    enrichment_alphanumeric_char_ratio_column_name: str = "alphanumeric_char_ratio",
    enrichment_control_char_ratio_column_name: str = "control_char_ratio",
    enrichment_punctuation_char_ratio_column_name: str = "punctuation_char_ratio",
    enrichment_other_symbol_char_ratio_column_name: str = "other_symbol_char_ratio",
    enrichment_tabs_word_ratio_column_name: str = "tabs_word_ratio",
    enrichment_hashes_word_ratio_column_name: str = "hashes_word_ratio",
    enrichment_ellipsis_ratio_column_name: str = "ellipsis_ratio",
    enrichment_bulletpoint_ratio_column_name: str = "bulletpoint_ratio",
    enrichment_dup_paragraphs_ratio_column_name: str = "dup_paragraphs_ratio",
    enrichment_dup_paragraphs_char_ratio_column_name: str = "dup_paragraphs_char_ratio",
    enrichment_top_2_gram_char_ratio_column_name: str = "top_2_gram_char_ratio",
    enrichment_top_3_gram_char_ratio_column_name: str = "top_3_gram_char_ratio",
    enrichment_top_4_gram_char_ratio_column_name: str = "top_4_gram_char_ratio",
    enrichment_dup_5_gram_char_ratio_column_name: str = "dup_5_gram_char_ratio",
    enrichment_dup_6_gram_char_ratio_column_name: str = "dup_6_gram_char_ratio",
    enrichment_dup_7_gram_char_ratio_column_name: str = "dup_7_gram_char_ratio",
    enrichment_dup_8_gram_char_ratio_column_name: str = "dup_8_gram_char_ratio",
    enrichment_dup_9_gram_char_ratio_column_name: str = "dup_9_gram_char_ratio",
    enrichment_dup_10_gram_char_ratio_column_name: str = "dup_10_gram_char_ratio",
    # additional parameters
    additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
):
    """
    Pipeline to execute enrichment transform
    :param ray_name: name of the Ray cluster
    :param ray_run_id_KFPv2: a unique string id used for the Ray cluster, applicable only in KFP v2.
    :param ray_head_options: head node options, containing the following:
        cpu - number of cpus
        memory - memory
        image - image to use
        image_pull_secret - image pull secret
        tolerations - (optional) tolerations for the ray pods
    :param ray_worker_options: worker node options (we here are using only 1 worker pool), containing the following:
        replicas - number of replicas to create
        max_replicas - max number of replicas
        min_replicas - min number of replicas
        cpu - number of cpus
        memory - memory
        image - image to use
        image_pull_secret - image pull secret
        tolerations - (optional) tolerations for the ray pods
    :param server_url - server url
    :param additional_params: additional (support) parameters, containing the following:
        wait_interval - wait interval for API server, sec
        wait_cluster_ready_tmout - time to wait for cluster ready, sec
        wait_cluster_up_tmout - time to wait for cluster up, sec
        wait_job_ready_tmout - time to wait for job ready, sec
        wait_print_tmout - time between prints, sec
        http_retries - http retries for API server calls
    :param data_s3_access_secret - s3 access secret
    :param data_s3_config - s3 configuration
    :param data_max_files - max files to process
    :param data_num_samples - num samples to process
    :param runtime_actor_options - actor options
    :param runtime_pipeline_id - pipeline id
    :param enrichment_output_column_prefix - Prefix to add to all output column names that are not explicitly defined
    :param enrichment_content_column_name - Name of the content column
    :param enrichment_lang_column_name - Name of the column with the language identifier
    :param enrichment_newline_normalized_column_name - Name of an output column for newline normalized text
    :param enrichment_error_column_name - Name of an output column for the eventual error encountered during processing
    :param enrichment_num_newlines_column_name - Column name for num_newlines
    :param enrichment_num_paragraphs_column_name - Column name for num_paragraphs
    :param enrichment_num_words_column_name - Column name for num_words
    :param enrichment_num_chars_column_name - Column name for num_chars
    :param enrichment_total_non_newline_chars_column_name - Column name for total_non_newline_chars
    :param enrichment_avg_word_length_column_name - Column name for avg_word_length
    :param enrichment_avg_paragraph_length_chars_column_name - Column name for avg_paragraph_length_chars
    :param enrichment_avg_paragraph_length_words_column_name - Column name for avg_paragraph_length_words
    :param enrichment_alphanumeric_char_ratio_column_name - Column name for alphanumeric_char_ratio
    :param enrichment_control_char_ratio_column_name - Column name for control_char_ratio
    :param enrichment_punctuation_char_ratio_column_name - Column name for punctuation_char_ratio
    :param enrichment_other_symbol_char_ratio_column_name - Column name for other_symbol_char_ratio
    :param enrichment_tabs_word_ratio_column_name - Column name for tabs_word_ratio
    :param enrichment_hashes_word_ratio_column_name - Column name for hashes_word_ratio
    :param enrichment_ellipsis_ratio_column_name - Column name for ellipsis_ratio
    :param enrichment_bulletpoint_ratio_column_name - Column name for bulletpoint_ratio
    :param enrichment_dup_paragraphs_ratio_column_name - Column name for dup_paragraphs_ratio
    :param enrichment_dup_paragraphs_char_ratio_column_name - Column name for dup_paragraphs_char_ratio
    :param enrichment_top_2_gram_char_ratio_column_name - Column name for top_2_gram_char_ratio
    :param enrichment_top_3_gram_char_ratio_column_name - Column name for top_3_gram_char_ratio
    :param enrichment_top_4_gram_char_ratio_column_name - Column name for top_4_gram_char_ratio
    :param enrichment_dup_5_gram_char_ratio_column_name - Column name for dup_5_gram_char_ratio
    :param enrichment_dup_6_gram_char_ratio_column_name - Column name for dup_6_gram_char_ratio
    :param enrichment_dup_7_gram_char_ratio_column_name - Column name for dup_7_gram_char_ratio
    :param enrichment_dup_8_gram_char_ratio_column_name - Column name for dup_8_gram_char_ratio
    :param enrichment_dup_9_gram_char_ratio_column_name - Column name for dup_9_gram_char_ratio
    :param enrichment_dup_10_gram_char_ratio_column_name - Column name for dup_10_gram_char_ratio
    :return: None
    """
    # In KFPv2 dsl.RUN_ID_PLACEHOLDER is deprecated and cannot be used since SDK 2.5.0. On another hand we cannot create
    # a unique string in a component (at runtime) and pass it to the `clean_up_task` of `ExitHandler`, due to
    # https://github.com/kubeflow/pipelines/issues/10187. Therefore, meantime the user is requested to insert
    # a unique string created at run creation time.
    if os.getenv("KFPv2", "0") == "1":
        print(
            "WARNING: the ray cluster name can be non-unique at runtime, please do not execute simultaneous Runs of the "
            "same version of the same pipeline !!!"
        )
        run_id = ray_run_id_KFPv2
    else:
        run_id = dsl.RUN_ID_PLACEHOLDER
    # create clean_up task
    clean_up_task = cleanup_ray_op(
        ray_name=ray_name, run_id=run_id, server_url=server_url, additional_params=additional_params
    )
    ComponentUtils.add_settings_to_component(clean_up_task, ONE_HOUR_SEC * 2)
    # pipeline definition
    with dsl.ExitHandler(clean_up_task):
        # compute execution params
        compute_exec_params = compute_exec_params_op(
            worker_options=ray_worker_options,
            actor_options=runtime_actor_options,
            data_s3_config=data_s3_config,
            data_max_files=data_max_files,
            data_num_samples=data_num_samples,
            data_checkpointing=data_checkpointing,
            runtime_pipeline_id=runtime_pipeline_id,
            runtime_job_id=run_id,
            enrichment_output_column_prefix=enrichment_output_column_prefix,
            enrichment_content_column_name=enrichment_content_column_name,
            enrichment_lang_column_name=enrichment_lang_column_name,
            enrichment_newline_normalized_column_name=enrichment_newline_normalized_column_name,
            enrichment_error_column_name=enrichment_error_column_name,
            enrichment_num_newlines_column_name=enrichment_num_newlines_column_name,
            enrichment_num_paragraphs_column_name=enrichment_num_paragraphs_column_name,
            enrichment_num_words_column_name=enrichment_num_words_column_name,
            enrichment_num_chars_column_name=enrichment_num_chars_column_name,
            enrichment_total_non_newline_chars_column_name=enrichment_total_non_newline_chars_column_name,
            enrichment_avg_word_length_column_name=enrichment_avg_word_length_column_name,
            enrichment_avg_paragraph_length_chars_column_name=enrichment_avg_paragraph_length_chars_column_name,
            enrichment_avg_paragraph_length_words_column_name=enrichment_avg_paragraph_length_words_column_name,
            enrichment_alphanumeric_char_ratio_column_name=enrichment_alphanumeric_char_ratio_column_name,
            enrichment_control_char_ratio_column_name=enrichment_control_char_ratio_column_name,
            enrichment_punctuation_char_ratio_column_name=enrichment_punctuation_char_ratio_column_name,
            enrichment_other_symbol_char_ratio_column_name=enrichment_other_symbol_char_ratio_column_name,
            enrichment_tabs_word_ratio_column_name=enrichment_tabs_word_ratio_column_name,
            enrichment_hashes_word_ratio_column_name=enrichment_hashes_word_ratio_column_name,
            enrichment_ellipsis_ratio_column_name=enrichment_ellipsis_ratio_column_name,
            enrichment_bulletpoint_ratio_column_name=enrichment_bulletpoint_ratio_column_name,
            enrichment_dup_paragraphs_ratio_column_name=enrichment_dup_paragraphs_ratio_column_name,
            enrichment_dup_paragraphs_char_ratio_column_name=enrichment_dup_paragraphs_char_ratio_column_name,
            enrichment_top_2_gram_char_ratio_column_name=enrichment_top_2_gram_char_ratio_column_name,
            enrichment_top_3_gram_char_ratio_column_name=enrichment_top_3_gram_char_ratio_column_name,
            enrichment_top_4_gram_char_ratio_column_name=enrichment_top_4_gram_char_ratio_column_name,
            enrichment_dup_5_gram_char_ratio_column_name=enrichment_dup_5_gram_char_ratio_column_name,
            enrichment_dup_6_gram_char_ratio_column_name=enrichment_dup_6_gram_char_ratio_column_name,
            enrichment_dup_7_gram_char_ratio_column_name=enrichment_dup_7_gram_char_ratio_column_name,
            enrichment_dup_8_gram_char_ratio_column_name=enrichment_dup_8_gram_char_ratio_column_name,
            enrichment_dup_9_gram_char_ratio_column_name=enrichment_dup_9_gram_char_ratio_column_name,
            enrichment_dup_10_gram_char_ratio_column_name=enrichment_dup_10_gram_char_ratio_column_name,
        )

        ComponentUtils.add_settings_to_component(compute_exec_params, ONE_HOUR_SEC * 2)
        # start Ray cluster
        ray_cluster = create_ray_op(
            ray_name=ray_name,
            run_id=run_id,
            ray_head_options=ray_head_options,
            ray_worker_options=ray_worker_options,
            server_url=server_url,
            additional_params=additional_params,
        )
        ComponentUtils.add_settings_to_component(ray_cluster, ONE_HOUR_SEC * 2)
        ray_cluster.after(compute_exec_params)

        # Execute job
        execute_job = execute_ray_jobs_op(
            ray_name=ray_name,
            run_id=run_id,
            additional_params=additional_params,
            exec_params=compute_exec_params.output,
            exec_script_name=EXEC_SCRIPT_NAME,
            server_url=server_url,
        )
        ComponentUtils.add_settings_to_component(execute_job, ONE_WEEK_SEC)
        if os.getenv("KFPv2", "0") == "1":
            from kfp import kubernetes

            # FIXME: Due to kubeflow/pipelines#10914, secret names cannot be provided as pipeline arguments.
            # As a workaround, the secret name is hard coded.
            env2key = ComponentUtils.set_secret_key_to_env()
            kubernetes.use_secret_as_env(task=execute_job, secret_name="s3-secret", secret_key_to_env=env2key)
        else:
            ComponentUtils.set_s3_env_vars_to_component(execute_job, data_s3_access_secret)
        execute_job.after(ray_cluster)


if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(enrichment, __file__.replace(".py", ".yaml"))
