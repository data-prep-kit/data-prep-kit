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

import kfp.dsl as dsl
from workflow_support.compile_utils import ONE_HOUR_SEC, ONE_WEEK_SEC, ComponentUtils
from kubernetes import client as k8s_client
ops={}
short_name = "enrichment"
description = "computes a number of features that can be used to estimate data quality"
task_image = f"{short_name}-ray:latest"
def compute_exec_params_func(
    worker_options: dict,
    actor_options: dict,
    data_s3_config: str,
    data_max_files: int,
    data_num_samples: int,
    data_checkpointing: bool,
    data_files_to_use: str,
    runtime_pipeline_id: str,
    runtime_job_id: str,
    runtime_code_location: dict,
    enrichment_output_column_prefix: str,
    enrichment_content_column_name: str,
    enrichment_lang_column_name: str,
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
    enrichment_dup_10_gram_char_ratio_column_name: str
) -> dict:
    from runtime_utils import KFPUtils
    return {
        "runtime_num_workers": KFPUtils.default_compute_execution_params(worker_options, actor_options),
        "runtime_worker_options": actor_options,
        "data_s3_config": data_s3_config,
        "data_max_files": data_max_files,
        "data_num_samples": data_num_samples,
        "data_checkpointing": data_checkpointing,
        "data_files_to_use": data_files_to_use,
        "runtime_pipeline_id": runtime_pipeline_id,
        "runtime_job_id": runtime_job_id,
        "runtime_code_location": runtime_code_location,
        "enrichment_output_column_prefix": enrichment_output_column_prefix,
        "enrichment_content_column_name": enrichment_content_column_name,
        "enrichment_lang_column_name": enrichment_lang_column_name,
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
@dsl.pipeline(
    name="enrichment-ray-pipeline",
    description="enrichment pipeline, computes a number of features that can be used to estimate data quality",
    )
def enrichment(
    ray_name: str = "enrichment-kfp-ray",
    ray_head_options: dict = {"cpu": 1, "memory": 4, "image": task_image },
    ray_worker_options: dict = {"replicas": 2, "max_replicas": 2, "min_replicas": 2, "cpu": 4, "memory": 16, "image": task_image},
    server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    data_s3_config: str = "",
    data_s3_access_secret: str = "s3-secret",
    data_max_files: int = -1,
    data_num_samples: int = -1,
    data_checkpointing: bool = False,
    data_files_to_use: str = "['.parquet']",
    runtime_actor_options: dict = {'num_cpus': 0.8},
    runtime_pipeline_id: str = "pipeline_id",
    runtime_code_location: dict = {'github': 'github', 'commit_hash': '12345', 'path': 'path'},
    enrichment_output_column_prefix: str = "",
    enrichment_content_column_name: str = "text",
    enrichment_lang_column_name: str = "lang",
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
    additional_params: str = "{\"wait_interval\": 2, \"wait_cluster_ready_tmout\": 400, \"wait_cluster_up_tmout\": 300, \"wait_job_ready_tmout\": 400, \"wait_print_tmout\": 30, \"http_retries\": 5}",
) -> None:
    clean_up_task = ops['cleanup_ray'](ray_name=ray_name, run_id=run_id, server_url=server_url)
    ComponentUtils.add_settings_to_component(clean_up_task, 60)
    with dsl.ExitHandler(clean_up_task):
        compute_exec_params = ops['compute_exec_params'](
            worker_options=ray_worker_options,
                actor_options=runtime_actor_options,
                data_s3_config=data_s3_config,
                data_max_files=data_max_files,
                data_num_samples=data_num_samples,
                data_checkpointing=data_checkpointing,
                data_files_to_use=data_files_to_use,
                runtime_pipeline_id=runtime_pipeline_id,
                runtime_job_id=run_id,
                runtime_code_location=runtime_code_location,
            enrichment_output_column_prefix=enrichment_output_column_prefix,
            enrichment_content_column_name=enrichment_content_column_name,
            enrichment_lang_column_name=enrichment_lang_column_name,
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
        ComponentUtils.set_s3_env_vars_to_component(compute_exec_params, data_s3_access_secret)
        ray_cluster = ops['create_ray'](
            ray_name=ray_name,
            run_id=run_id,
            ray_head_options=ray_head_options,
            ray_worker_options=ray_worker_options,
            server_url=server_url,
            additional_params=additional_params,
        )
        ComponentUtils.add_settings_to_component(ray_cluster, ONE_HOUR_SEC * 2)
        ray_cluster.after(compute_exec_params)
        execute_job = ops['execute_ray_jobs'](
            ray_name=ray_name,
            run_id=run_id,
            additional_params=additional_params,
            exec_params=compute_exec_params.output,
            exec_script_name="{short_name}_transform_ray.py",
            server_url=server_url,
        )
        ComponentUtils.add_settings_to_component(execute_job, ONE_WEEK_SEC)
        ComponentUtils.set_s3_env_vars_to_component(execute_job, data_s3_access_secret)
        execute_job.after(ray_cluster)
    dsl.get_pipeline_conf().set_image_pull_secrets([k8s_client.V1ObjectReference(name="image-pull-secrets")])
