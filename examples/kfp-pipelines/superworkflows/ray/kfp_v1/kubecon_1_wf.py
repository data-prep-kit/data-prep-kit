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


# Components
# path to kfp component specifications files
component_spec_path = os.getenv("KFP_COMPONENT_SPEC_PATH", "../../../../../kfp/kfp_ray_components/")

# For every sub workflow we need a separate components, that knows about this subworkflow.
run_exact_dedup_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_doc_id_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_lang_id_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_filter_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")
run_doc_quality_op = comp.load_component_from_file(component_spec_path + "executeSubWorkflowComponent.yaml")

ededup_image = "quay.io/dataprep1/data-prep-kit/ededup-ray:latest"
lang_id_image = "quay.io/dataprep1/data-prep-kit/lang_id-ray:latest"
doc_id_image = "quay.io/dataprep1/data-prep-kit/doc_id-ray:latest"
filter_image = "quay.io/dataprep1/data-prep-kit/filter-ray:latest"
doc_quality_image = "quay.io/dataprep1/data-prep-kit/doc_quality-ray:latest"

# Pipeline to invoke execution on remote resource
@dsl.pipeline(
    name="demo-of-kubeflow-pipeline",
    description="Pipeline to show how to run combine several transformer pipelines",
)
def sample_ray_orchestrator(
    # the super pipeline parameters
    p1_orch_exact_dedup_name: str = "ededup_wf",
    p1_orch_lang_id_name: str = "lang_id_wf",
    p1_orch_filter_name: str = "filter_wf",
    p1_orch_doc_quality_name: str = "doc_quality_wf",
    p1_orch_doc_id_name: str = "doc_id_wf",
    p2_pipeline_runtime_pipeline_id: str = "pipeline_id",
    p2_pipeline_ray_head_options: dict = {
        "cpu": 1,
        "memory": 4,
        "image_pull_secret": "",
    },
    p2_pipeline_ray_worker_options: dict = {
        "replicas": 2,
        "max_replicas": 2,
        "min_replicas": 2,
        "cpu": 2,
        "memory": 4,
        "image_pull_secret": "",
    },
    p2_pipeline_server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    p2_pipeline_input_parent_path: str = "test/kubecon",
    p2_pipeline_output_parent_path: str = "test/super/output/",
    p2_pipeline_parent_path_suffix: str = "",
    p2_pipeline_additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
    p2_pipeline_data_s3_access_secret: str = "s3-secret",
    p2_pipeline_runtime_code_location: dict = {"github": "github", "commit_hash": "12345", "path": "path"},
    p2_pipeline_runtime_actor_options: dict = {"num_cpus": 0.7},
    # data access.
    p2_pipeline_data_max_files: int = -1,
    p2_pipeline_data_num_samples: int = -1,
    # Document ID step parameters
    p3_name: str = "doc id",
    # doc id parameters
    # p3_doc_id_doc_column: str = "contents",
    p3_doc_id_hash_column: str = "document_id",
    # p3_doc_id_start_id: int = 0,
    # overriding parameters
    p3_overriding_params: str = '{"ray_worker_options": {"image": "'
    + doc_id_image
    + '"}, "ray_head_options": {"image": "'
    + doc_id_image
    + '"}}',
    # Exact dedup step parameters
    p4_name: str = "exact dedup",
    # p4_ededup_doc_column: str = "contents",
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
    # language ID step parameters
    p5_name: str = "lang_id",
    p5_lang_id_model_credential: str = "PUT YOUR HF TOKEN HERE",
    p5_lang_id_model_kind: str = "fasttext",
    p5_lang_id_model_url: str = "facebook/fasttext-language-identification",
    p5_lang_id_content_column_name: str = "contents",
    p5_lang_id_output_lang_column_name: str = "lang",
    p5_lang_id_output_score_column_name: str = "score",
    # overriding parameters
    p5_overriding_params: str = '{"ray_worker_options": {"image": "'
    + lang_id_image
    + '"}, "ray_head_options": {"image": "'
    + lang_id_image
    + '"}}',
    # filter_en step parameters
    p6_name: str = "filter_en",
    p6_filter_criteria_list: str = "['lang=\\\\'en\\\\'', 'score>=0.8', 'contents!=\\\\'\\\\'']",
    p6_filter_logical_operator: str = "AND",
    p6_filter_columns_to_drop: str = "",
    # overriding parameters
    p6_overriding_params: str = '{"ray_worker_options": {"image": "'
    + filter_image
    + '"}, "ray_head_options": {"image": "'
    + filter_image
    + '"}}',
    # document en quality step parameters
    p7_name: str = "doc_quality_en",
    p7_docq_text_lang: str = "en",
    # p7_docq_doc_content_column: str = "contents",
    p7_docq_bad_word_filepath: str = "/home/ray/dpk_doc_quality/ldnoobw/en",
    # overriding parameters
    p7_overriding_params: str = '{"ray_worker_options": {"image": "'
    + doc_quality_image
    + '"}, "ray_head_options": {"image": "'
    + doc_quality_image
    + '"}}',
    # filter ja step parameters
    p8_name: str = "filter_ja",
    p8_filter_criteria_list: list = "['lang=\\\\'ja\\\\'', 'score>=0.8', 'contents!=\\\\'\\\\'']",
    p8_filter_logical_operator: str = "AND",
    p8_filter_columns_to_drop: str = "",
    # overriding parameters
    p8_overriding_params: str = '{"ray_worker_options": {"image": "'
    + filter_image
    + '"}, "ray_head_options": {"image": "'
    + filter_image
    + '"}}',
    # document ja quality step parameters
    p9_name: str = "doc_quality_ja",
    p9_docq_text_lang: str = "ja",
    # p9_docq_doc_content_column: str = "contents",
    p9_docq_bad_word_filepath: str = "/home/ray/dpk_doc_quality/ldnoobw/ja",
    # overriding parameters
    p9_overriding_params: str = '{"ray_worker_options": {"image": "'
    + doc_quality_image
    + '"}, "ray_head_options": {"image": "'
    + doc_quality_image
    + '"}}',
    # filter fr step parameters
    p10_name: str = "filter_fr",
    p10_filter_criteria_list: list = "['lang=\\\\'fr\\\\'', 'score>=0.8', 'contents!=\\\\'\\\\'']",
    p10_filter_logical_operator: str = "AND",
    p10_filter_columns_to_drop: str = "",
    # overriding parameters
    p10_overriding_params: str = '{"ray_worker_options": {"image": "'
    + filter_image
    + '"}, "ray_head_options": {"image": "'
    + filter_image
    + '"}}',
    # document fr quality step parameters
    p11_name: str = "doc_quality_fr",
    p11_docq_text_lang: str = "fr",
    # p11_docq_doc_content_column: str = "contents",
    p11_docq_bad_word_filepath: str = "/home/ray/dpk_doc_quality/ldnoobw/fr",
    # overriding parameters
    p11_overriding_params: str = '{"ray_worker_options": {"image": "'
    + doc_quality_image
    + '"}, "ray_head_options": {"image": "'
    + doc_quality_image
    + '"}}',
):

    # get all arguments
    args = locals()
    orch_host = "http://ml-pipeline:8888"

    def _set_component(op: dsl.BaseOp, displayed_name: str, prev_op: dsl.BaseOp = None):
        # set the sub component UI name
        op.set_display_name(displayed_name)

        # Add pod labels
        op.add_pod_label("app", "ml-pipeline").add_pod_label("component", "data-science-pipelines")
        # No cashing
        op.execution_options.caching_strategy.max_cache_staleness = "P0D"
        # image pull policy
        # op.set_image_pull_policy("Always")
        if prev_op is not None:
            op.after(prev_op)

    # exact deduplication
    # document ID
    doc_id = run_doc_id_op(
        name=p1_orch_doc_id_name, prefix="p3_", params=args, host=orch_host, input_folder=p2_pipeline_input_parent_path
    )
    _set_component(doc_id, "doc ID")

    exact_dedup = run_exact_dedup_op(
        name=p1_orch_exact_dedup_name, prefix="p4_", params=args, host=orch_host, input_folder=doc_id.output
    )
    _set_component(exact_dedup, "exact dedup", doc_id)

    # language ID
    lang_id = run_lang_id_op(
        name=p1_orch_lang_id_name, prefix="p5_", params=args, host=orch_host, input_folder=exact_dedup.output
    )
    _set_component(lang_id, "language ID", exact_dedup)

    # English filter
    filter_en = run_filter_op(
        name=p1_orch_filter_name,
        prefix="p6_",
        params=args,
        host=orch_host,
        input_folder=lang_id.output,
    )
    _set_component(filter_en, "filter en", lang_id)

    # document quality en
    doc_quality_en = run_doc_quality_op(
        name=p1_orch_doc_quality_name, prefix="p7_", params=args, host=orch_host, input_folder=filter_en.output
    )
    _set_component(doc_quality_en, "doc quality en", filter_en)

    # Japanese filter
    filter_ja = run_filter_op(
        name=p1_orch_filter_name,
        prefix="p8_",
        params=args,
        host=orch_host,
        input_folder=lang_id.output,
    )
    _set_component(filter_ja, "filter ja", lang_id)

    # document quality ja
    doc_quality_ja = run_doc_quality_op(
        name=p1_orch_doc_quality_name, prefix="p9_", params=args, host=orch_host, input_folder=filter_ja.output
    )
    _set_component(doc_quality_ja, "doc quality ja", filter_ja)

    # French filter
    filter_fr = run_filter_op(
        name=p1_orch_filter_name,
        prefix="p10_",
        params=args,
        host=orch_host,
        input_folder=lang_id.output,
    )
    _set_component(filter_fr, "filter fr", lang_id)

    # document quality fr
    doc_quality_fr = run_doc_quality_op(
        name=p1_orch_doc_quality_name, prefix="p11_", params=args, host=orch_host, input_folder=filter_fr.output
    )
    _set_component(doc_quality_fr, "doc quality fr", filter_fr)


if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(sample_ray_orchestrator, __file__.replace(".py", ".yaml"))
