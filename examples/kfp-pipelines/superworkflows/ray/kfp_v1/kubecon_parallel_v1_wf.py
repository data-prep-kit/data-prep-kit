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
from typing import Dict

import kfp.compiler as compiler
import kfp.components as comp
import kfp.dsl as dsl
from workflow_support.compile_utils import ONE_WEEK_SEC

# Components
# path to kfp component specifications files
component_spec_path = os.getenv("KFP_COMPONENT_SPEC_PATH", "../../../../../kfp/kfp_ray_components/")
# For every sub workflow we need a separate components, that knows about this subworkflow.
run_exact_dedup_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_doc_id_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_lang_id_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_filter_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_tokenization_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_doc_quality_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_merge_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")

ededup_image = "quay.io/dataprep1/data-prep-kit/ededup-ray:latest"
lang_id_image = "quay.io/dataprep1/data-prep-kit/lang_id-ray:latest"
doc_id_image = "quay.io/dataprep1/data-prep-kit/doc_id-ray:latest"
filter_image = "quay.io/dataprep1/data-prep-kit/filter-ray:latest"
tokenization_image = "quay.io/dataprep1/data-prep-kit/tokenization-ray:latest"
doc_quality_image = "quay.io/dataprep1/data-prep-kit/doc_quality-ray:latest"
merge_image = "quay.io/dataprep1/data-prep-kit/merge-ray:latest"

def prepare_merge_params(prefix: str, params: dict, merged_dir: str) -> dict:
    params[prefix + "merge_input_dirs"] = merged_dir
    return params

run_prepare_merge_params_op = comp.create_component_from_func(func=prepare_merge_params)

# Pipeline to invoke execution on remote resource
@dsl.pipeline(
    name="sample-parallel-kubeflow-pipeline",
    description="Pipeline to show how to run combine several transformer pipelines",
)
def sample_ray_orchestrator(
    # the super pipeline parameters
    p1_orch_exact_dedup_name: str = "ededup_wf",
    p1_orch_lang_id_name: str = "lang_id_wf",
    p1_orch_filter_name: str = "filter_wf",
    p1_orch_tokenization_name: str = "tokenization_wf",
    p1_orch_doc_quality_name: str = "doc_quality_wf",
    p1_orch_doc_id_name: str = "doc_id_wf",
    p1_orch_merge_name: str = "merge_wf",

    p2_pipeline_runtime_pipeline_id: str = "pipeline_id",
    p2_pipeline_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": ""},
    p2_pipeline_ray_worker_options: dict = {"replicas": 2, "max_replicas": 2, "min_replicas": 2, "cpu": 2, "memory": 4, "image_pull_secret": ""},
    p2_pipeline_server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    p2_pipeline_input_parent_path: str = "test/ededup/input/",
    p2_pipeline_output_parent_path: str = "test/super/output/",
    p2_pipeline_parent_path_suffix: str = "",
    p2_pipeline_additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
    p2_pipeline_data_s3_access_secret: str = "s3-secret",
    p2_pipeline_runtime_code_location: dict = {'github': 'github', 'commit_hash': '12345', 'path': 'path'},
    p2_pipeline_runtime_actor_options: dict = {'num_cpus': 0.7},
    # data access.
    p2_pipeline_data_max_files: int = -1,
    p2_pipeline_data_num_samples: int = -1,

    # Exact dedup step parameters
    p3_name: str = "ededup",
    p3_skip: bool = False,
    p3_ededup_doc_column: str = "contents",
    p3_ededup_hash_cpu: float = 0.5,
    p3_ededup_use_snapshot: bool = False,
    p3_ededup_snapshot_directory: str = None,
    # data sampling
    p3_ededup_n_samples: int = 10,
    # overriding parameters
    p3_overriding_params: str = '{"ray_worker_options": {"image": "'
    + ededup_image
    + '"}, "ray_head_options": {"image": "'
    + ededup_image
    + '"}}',

    # Document ID step parameters
    p4_name: str = "doc_id",
    p4_skip: bool = False,
    # doc id parameters
    p4_doc_id_doc_column: str = "contents",
    p4_doc_id_hash_column: str = "hash_column",
    p4_doc_id_int_column: str = "int_id_column",
    p4_doc_id_start_id: int = 0,
    # overriding parameters
    p4_overriding_params: str = '{"ray_worker_options": {"image": "'
    + doc_id_image
    + '"}, "ray_head_options": {"image": "'
    + doc_id_image
    + '"}}',

    # document quality step parameters
    p5_name: str = "doc_quality",
    p5_skip: bool = False,
    p5_docq_text_lang: str = "en",
    p5_docq_doc_content_column: str = "contents",
    p5_docq_bad_word_filepath: str = "/home/ray/dpk_doc_quality/ldnoobw/en",
    # overriding parameters
    p5_overriding_params: str = '{"ray_worker_options": {"image": "'
    + doc_quality_image
    + '"}, "ray_head_options": {"image": "'
    + doc_quality_image
    + '"}}',

    # filter step parameters
    p6_name: str = "filter",
    p6_skip: bool = False,
    p6_filter_criteria_list: str = "['docq_total_words > 100 AND docq_total_words < 200', 'ibmkenlm_docq_perplex_score < 230']",
    p6_filter_logical_operator: str = "AND",
    p6_filter_columns_to_drop: str = "['extra', 'cluster']",
    # overriding parameters
    p6_overriding_params: str = '{"ray_worker_options": {"image": "'
    + filter_image
    + '"}, "ray_head_options": {"image": "'
    + filter_image
    + '"}}',

    # tokenization step parameters
    p7_name: str = "tokenization",
    p7_skip: bool = False,
    p7_tkn_tokenizer: str = "hf-internal-testing/llama-tokenizer",
    p7_tkn_doc_id_column: str = "document_id",
    p7_tkn_doc_content_column: str = "contents",
    p7_tkn_text_lang: str = "en",
    p7_tkn_tokenizer_args: str = "cache_dir=/tmp/hf",
    p7_tkn_chunk_size: int = 0,
    # overriding parameters
    p7_overriding_params: str = '{"ray_worker_options": {"image": "'
    + tokenization_image
    + '"}, "ray_head_options": {"image": "'
    + tokenization_image
    + '"}}',

    # merge step parameters
    p8_name: str = "merge",
    p8_skip: bool = False,
    # overriding parameters
    p8_overriding_params: str = '{"ray_worker_options": {"image": "'
    + merge_image
    + '"}, "ray_head_options": {"image": "'
    + merge_image
    + '"}}'
):

    # get all arguments
    args = locals()
    orch_host = "http://ml-pipeline:8888"

    def _set_component(op: dsl.BaseOp, displaied_name: str, prev_op: dsl.BaseOp = None):
        # set the sub component UI name
        op.set_display_name(displaied_name)

        # Add pod labels
        op.add_pod_label("app", "ml-pipeline").add_pod_label("component", "data-science-pipelines")
        # No cashing
        op.execution_options.caching_strategy.max_cache_staleness = "P0D"
        # image pull policy
        op.set_image_pull_policy("Always")
        # Set the timeout for each task to one week (in seconds)
        op.set_timeout(ONE_WEEK_SEC)
        if prev_op is not None:
            op.after(prev_op)

    # exact deduplication
    exact_dedup = run_exact_dedup_op(
        name=p1_orch_exact_dedup_name, prefix="p3_", params=args, host=orch_host, input_folder=p2_pipeline_input_parent_path
    )
    _set_component(exact_dedup, "exact dedup")

    # document ID
    doc_id = run_doc_id_op(
        name=p1_orch_doc_id_name, prefix="p4_", params=args, host=orch_host, input_folder=exact_dedup.output
    )
    _set_component(doc_id, "doc ID", exact_dedup)

    # document quality
    doc_quality = run_doc_quality_op(
        name=p1_orch_doc_quality_name, prefix="p5_", params=args, host=orch_host, input_folder=exact_dedup.output
    )
    _set_component(doc_quality, "doc quality", exact_dedup)

    # merge component
    prep_merge = run_prepare_merge_params_op(prefix="p8_", params=args, merged_dir=doc_quality.output)
    merge = run_merge_op(
        name=p1_orch_merge_name, prefix="p8_", params=prep_merge.output, host=orch_host, input_folder=doc_id.output
    )
    _set_component(merge, "merge", doc_id)


    # filtering
    filtering = run_filter_op(
        name=p1_orch_filter_name, prefix="p6_", params=args, host=orch_host, input_folder=merge.output
    )
    _set_component(filtering, "filtering", merge)

    # tokenization
    tokenization = run_tokenization_op(
        name=p1_orch_tokenization_name, prefix="p7_", params=args, host=orch_host, input_folder=filtering.output
    )
    _set_component(tokenization, "tokenization", filtering)


    # Configure the pipeline level to one week (in seconds)
    dsl.get_pipeline_conf().set_timeout(ONE_WEEK_SEC)


if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(sample_ray_orchestrator, __file__.replace(".py", ".yaml"))
