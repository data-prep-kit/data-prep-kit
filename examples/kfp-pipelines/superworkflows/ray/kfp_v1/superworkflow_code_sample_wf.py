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
import json
import kfp.compiler as compiler
import kfp.components as comp
import kfp.dsl as dsl
from workflow_support.compile_utils import ONE_WEEK_SEC

from python_apiserver_client.params import (
        EnvironmentVariables,
        EnvVarFrom,
        EnvVarSource,
)

ORCH_HOST = "http://ml-pipeline:8888"

# Components
component_spec_path = os.getenv("KFP_COMPONENT_SPEC_PATH", "../../../../../kfp/kfp_ray_components/")
run_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")

code_to_parquet_image = "quay.io/dataprep1/data-prep-kit/code2parquet-ray:latest"
proglang_select_image = "quay.io/dataprep1/data-prep-kit/proglang_select-ray:latest"
code_quality_image = "quay.io/dataprep1/data-prep-kit/code_quality-ray:latest"
malware_image = "quay.io/dataprep1/data-prep-kit/malware-ray:latest"
doc_id_image = "quay.io/dataprep1/data-prep-kit/doc_id-ray:latest"
ededup_image = "quay.io/dataprep1/data-prep-kit/ededup-ray:latest"
fdedup_image = "quay.io/dataprep1/data-prep-kit/fdedup-ray:latest"
tokenizer_image = "quay.io/dataprep1/data-prep-kit/tokenization-ray:latest"


# The name of the secret that holds the HugginFace token
HF_SECRET = "hf-secret"
# The secret key that holds the HugginFace token
HF_SECRET_KEY = "hf-token"

env_v = EnvVarFrom(source=EnvVarSource.SECRET, name=HF_SECRET, key=HF_SECRET_KEY)
envs = EnvironmentVariables(from_ref={"HF_READ_ACCESS_TOKEN": env_v})


# Pipeline to invoke execution on remote resource
@dsl.pipeline(
    name="super-kubeflow-pipeline-code",
    description="Super pipeline for programming languages data preprocessing",
)
def sample_code_ray_orchestrator(
    # the super pipeline parameters
    p1_orch_code_to_parquet_name: str = "code2parquet_wf",
    p1_orch_code_quality_name: str = "code_quality_wf",
    p1_orch_malware_name: str = "malware_wf",
    p1_orch_proglang_select_name: str = "proglang_select_wf",
    p1_orch_doc_id_name: str = "doc_id_wf",
    p1_orch_exact_dedup_name: str = "ededup_wf",
    p1_orch_fuzzy_dedup_name: str = "fdedup_wf",
    p1_orch_tokenization_wf_name: str = "tokenization_wf",
    p2_pipeline_runtime_pipeline_id: str = "pipeline_id",
    p2_pipeline_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": ""},
    p2_pipeline_ray_worker_options: dict = {"replicas": 2, "max_replicas": 2, "min_replicas": 2, "cpu": 2, "memory": 4, "image_pull_secret": ""},
    p2_pipeline_server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    p2_pipeline_input_parent_path: str = "test/code2parquet/input/",
    p2_pipeline_output_parent_path: str = "test/super/output/",
    p2_pipeline_parent_path_suffix: str = "",
    p2_pipeline_additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
    p2_pipeline_data_s3_access_secret: str = "s3-secret",
    p2_pipeline_runtime_code_location: dict = {'github': 'github', 'commit_hash': '12345', 'path': 'path'},
    p2_pipeline_runtime_actor_options: dict = {'num_cpus': 0.7},
    p2_pipeline_data_max_files: int = -1,
    p2_pipeline_data_num_samples: int = -1,
    # code to parquet step parameters
    p3_name: str = "code2parquet",
    p3_skip: bool = False,
    # code to parquet parameters
    p3_code2parquet_supported_langs_file: str = "test/code2parquet/languages/lang_extensions.json",
    p3_code2parquet_detect_programming_lang: bool = True,
    p3_code2parquet_domain: str = "code",
    p3_code2parquet_snapshot: str = "github",
    p3_code2parquet_s3_access_secret: str = "s3-secret",
    # overriding parameters
    p3_overriding_params: str = '{"ray_worker_options": {"image": "'
    + code_to_parquet_image
    + '"}, "ray_head_options": {"image": "'
    + code_to_parquet_image
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
    # Exact dedup step parameters
    p5_name: str = "ededup",
    p5_skip: bool = False,
    p5_ededup_doc_column: str = "contents",
    p5_ededup_hash_cpu: float = 0.5,
    p5_ededup_use_snapshot: bool = False,
    p5_ededup_snapshot_directory: str = None,  # data sampling
    p5_ededup_n_samples: int = 10,
    # overriding parameters
    p5_overriding_params: str = '{"ray_worker_options": {"image": "'
    + ededup_image
    + '"}, "ray_head_options": {"image": "'
    + ededup_image
    + '"}}',

    # proglang_select step parameters
    p6_name: str = "proglang_select",
    p6_skip: bool = False,
    p6_proglang_select_allowed_langs_file: str = "test/proglang_select/languages/allowed-code-languages.txt",
    p6_proglang_select_language_column: str = "programming_language",
    p6_proglang_select_s3_access_secret: str = "s3-secret",
    # overriding parameters
    p6_overriding_params: str = '{"ray_worker_options": {"image": "'
    + proglang_select_image
    + '"}, "ray_head_options": {"image": "'
    + proglang_select_image
    + '"}}',
    # Code quality step parameters
    p7_name: str = "code_quality",
    p7_skip: bool = False,
    p7_cq_contents_column_name: str = "contents",
    p7_cq_language_column_name: str = "programming_language",
    p7_cq_tokenizer: str = "codeparrot/codeparrot",
    # orchestrator
    # overriding parameters
    p7_overriding_params: str = '{"ray_worker_options": {"image": "'
    + code_quality_image
    + '", "environment": "'
    + json.dumps(envs.to_dict())
    + '"}, "ray_head_options": {"image": "'
    + code_quality_image
    + '", "environment": "'
    + json.dumps(envs.to_dict())
    + '"}}',
    # malware step parameters
    p8_name: str = "malware",
    p8_skip: bool = False,
    p8_malware_input_column: str = "contents",
    p8_malware_output_column: str = "virus_detection",
    # orchestrator
    # overriding parameters
    p8_overriding_params: str = '{"ray_worker_options": {"image": "'
    + malware_image
    + '"}, "ray_head_options": {"image": "'
    + malware_image
    + '"}}',
    # tokenization parameters
    p9_name: str = "tokenization",
    p9_skip: bool = False,
    p9_tkn_tokenizer: str = "hf-internal-testing/llama-tokenizer",
    p9_tkn_doc_id_column: str = "document_id",
    p9_tkn_doc_content_column: str = "contents",
    p9_tkn_text_lang: str = "en",
    p9_tkn_tokenizer_args: str = "cache_dir=/tmp/hf",
    p9_tkn_chunk_size: int = 0,
    p9_overriding_params: str = '{"ray_worker_options": {"image": "'
    + tokenizer_image
    + '"}, "ray_head_options": {"image": "'
    + tokenizer_image
    + '"}}',
):

    # get all arguments
    args = locals()

    def _create_component(
            pipeline_name: str,
            displayed_name: str,
            prefix="",
            input_folder="",
            prev_op: dsl.BaseOp = None,
    ):
        component = run_op(
            name=pipeline_name, prefix=prefix, params=args, host=ORCH_HOST, input_folder=input_folder
        )
        # set the sub component UI name
        component.set_display_name(displayed_name)

        # Add pod labels
        component.add_pod_label("app", "ml-pipeline").add_pod_label("component", "data-science-pipelines")
        # No cashing
        component.execution_options.caching_strategy.max_cache_staleness = "P0D"
        # image pull policy
        component.set_image_pull_policy("Always")
        if prev_op is not None:
            component.after(prev_op)
        return component

    # code to parquet deduplication
    code_to_parquet = _create_component(
        pipeline_name=p1_orch_code_to_parquet_name,
        displayed_name="code to parquet",
        prefix="p3_",
        input_folder=p2_pipeline_input_parent_path,
    )

    # document ID
    doc_id = _create_component(
        pipeline_name=p1_orch_doc_id_name,
        displayed_name="doc ID",
        prefix="p4_",
        input_folder=code_to_parquet.output,
        prev_op=code_to_parquet
    )

    # exact deduplication
    exact_dedup = _create_component(
        pipeline_name=p1_orch_exact_dedup_name,
        displayed_name="exact dedup",
        prefix="p5_",
        input_folder=doc_id.output,
        prev_op=doc_id
    )

    # proglang_select
    proglang_select = _create_component(
        pipeline_name=p1_orch_proglang_select_name,
        displayed_name="proglang select",
        prefix="p6_",
        input_folder=exact_dedup.output,
        prev_op=exact_dedup,
    )

    # code_quality
    code_quality = _create_component(
        pipeline_name=p1_orch_code_quality_name,
        displayed_name="code_quality",
        prefix="p7_",
        input_folder=proglang_select.output,
        prev_op=proglang_select,
    )

    # malware
    malware = _create_component(
        pipeline_name=p1_orch_malware_name,
        displayed_name="malware",
        prefix="p8_",
        input_folder=code_quality.output,
        prev_op=code_quality,
    )

    # tokenization
    tokenization = _create_component(
        pipeline_name=p1_orch_tokenization_wf_name,
        displayed_name="tokenization",
        prefix="p9_",
        input_folder=malware.output,
        prev_op=malware,
    )

    # Configure the pipeline level to one week (in seconds)
    dsl.get_pipeline_conf().set_timeout(ONE_WEEK_SEC)


if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(sample_code_ray_orchestrator, __file__.replace(".py", ".yaml"))
