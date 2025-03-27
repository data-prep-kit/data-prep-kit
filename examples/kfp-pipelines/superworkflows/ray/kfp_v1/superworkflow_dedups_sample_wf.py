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
from workflow_support.compile_utils import ONE_WEEK_SEC

ORCH_HOST = "http://ml-pipeline:8888"

component_spec_path = os.getenv("KFP_COMPONENT_SPEC_PATH", "../../../../../kfp/kfp_ray_components/")
run_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")

doc_id_image = "quay.io/dataprep1/data-prep-kit/doc_id-ray:latest"
ededup_image = "quay.io/dataprep1/data-prep-kit/ededup-ray:latest"
fdedup_image = "quay.io/dataprep1/data-prep-kit/fdedup-ray:latest"

# Pipeline to invoke execution on remote resource
@dsl.pipeline(
    name="sample-super-kubeflow-pipeline",
    description="Pipeline to show how to run combine several transformer pipelines",
)
def sample_ray_orchestrator(
    # the super pipeline parameters
    p1_orch_doc_id_name: str = "doc_id_wf",
    p1_orch_exact_dedup_name: str = "ededup_wf",
    p1_orch_fuzzy_dedup_name: str = "fdedup_wf",
    p2_pipeline_runtime_pipeline_id: str = "pipeline_id",
    p2_pipeline_ray_head_options: dict = {"cpu": 1, "memory": 4, "image_pull_secret": ""},
    p2_pipeline_ray_worker_options: dict = {"replicas": 2, "max_replicas": 2, "min_replicas": 2, "cpu": 2, "memory": 4, "image_pull_secret": ""},
    p2_pipeline_server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    p2_pipeline_input_parent_path: str = "test/doc_id/input/",
    p2_pipeline_output_parent_path: str = "test/super/output/",
    p2_pipeline_parent_path_suffix: str = "",
    p2_pipeline_additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
    p2_pipeline_data_s3_access_secret: str = "s3-secret",
    p2_pipeline_runtime_code_location: dict = {'github': 'github', 'commit_hash': '12345', 'path': 'path'},
    p2_pipeline_runtime_actor_options: dict = {'num_cpus': 0.7},
    # data access.
    p2_pipeline_data_max_files: int = -1,
    p2_pipeline_data_num_samples: int = -1,
    # Document ID step parameters
    p3_name: str = "doc_id",
    p3_skip: bool = False,
    # orchestrator
    # doc id parameters
    p3_doc_id_doc_column: str = "contents",
    p3_doc_id_hash_column: str = "hash_column",
    p3_doc_id_int_column: str = "int_id_column",
    p3_doc_id_start_id: int = 0,
    # overriding parameters
    p3_overriding_params: str = '{"ray_worker_options": {"image": "'
    + doc_id_image
    + '"}, "ray_head_options": {"image": "'
    + doc_id_image
    + '"}}',
    # Exact dedup step parameters
    p4_name: str = "ededup",
    p4_skip: bool = False,
    p4_ededup_doc_column: str = "contents",
    p4_ededup_hash_cpu: float = 0.5,
    p4_ededup_use_snapshot: bool = False,
    p4_ededup_snapshot_directory: str = None,
    # data sampling
    p4_ededup_n_samples: int = 10,
    # overriding parameters
    p4_overriding_params: str = '{"ray_worker_options": {"image": "'
    + ededup_image
    + '"}, "ray_head_options": {"image": "'
    + ededup_image
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
        # component.set_image_pull_policy("Always")
        if prev_op is not None:
            component.after(prev_op)
        return component

    # document ID
    doc_id = _create_component(
        pipeline_name=p1_orch_doc_id_name,
        displayed_name="doc ID",
        prefix="p3_",
        input_folder=p2_pipeline_input_parent_path,
    )

    # exact deduplication
    exact_dedup = _create_component(
        pipeline_name=p1_orch_exact_dedup_name,
        displayed_name="exact dedup",
        prefix="p4_",
        input_folder=doc_id.output,
        prev_op=doc_id,
    )

    # Configure the pipeline level to one week (in seconds)
    dsl.get_pipeline_conf().set_timeout(ONE_WEEK_SEC)


if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(sample_ray_orchestrator, __file__.replace(".py", ".yaml"))
