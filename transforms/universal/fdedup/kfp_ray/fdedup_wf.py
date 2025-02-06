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
from src.fdedup_compute_execution_params import (
    cluster_analysis_compute_execution_params,
    compute_common_params,
    data_cleaning_compute_execution_params,
    get_duplicate_list_compute_execution_params,
    signature_calc_compute_execution_params,
)
from workflow_support.compile_utils import ONE_HOUR_SEC, ONE_WEEK_SEC, DEFAULT_KFP_COMPONENT_SPEC_PATH, ComponentUtils


task_image = os.getenv("FDEDUP_IMAGE_LOCATION", "quay.io/dataprep1/data-prep-kit/fdedup-ray:latest")
image_pull_secret = os.getenv("FDEDUP_IMAGE_PULL_SECRET", "my_secret")

# the name of the job script
SIGNATURE_CALC_EXEC_SCRIPT_NAME: str = "-m dpk_fdedup.signature_calc.ray.transform"
CLUSTER_ANALYSIS_EXEC_SCRIPT_NAME: str = "-m dpk_fdedup.cluster_analysis.ray.transform"
GET_DUPLICATE_LIST_EXEC_SCRIPT_NAME: str = "-m dpk_fdedup.get_duplicate_list.ray.transform"
DATA_CLEANING_EXEC_SCRIPT_NAME: str = "-m dpk_fdedup.data_cleaning.ray.transform"

# components
base_kfp_image = "quay.io/dataprep1/data-prep-kit/kfp-data-processing:latest"

# path to kfp component specifications files
component_spec_path = os.getenv("KFP_COMPONENT_SPEC_PATH", DEFAULT_KFP_COMPONENT_SPEC_PATH)


# KFPv1 and KFP2 uses different methods to create a component from a function. KFPv1 uses the
# `create_component_from_func` function, but it is deprecated by KFPv2 and so has a different import path.
# KFPv2 recommends using the `@dsl.component` decorator, which doesn't exist in KFPv1. Therefore, here we use
# this if/else statement and explicitly call the decorator.
if os.getenv("KFPv2", "0") == "1":
    # In KFPv2 dsl.RUN_ID_PLACEHOLDER is deprecated and cannot be used since SDK 2.5.0. On another hand we cannot create
    # a unique string in a component (at runtime) and pass it to the `clean_up_task` of `ExitHandler`, due to
    # https://github.com/kubeflow/pipelines/issues/10187. Therefore, meantime we use a unique string created at
    # compilation time.
    import uuid

    compute_common_params_op = dsl.component_decorator.component(func=compute_common_params, base_image=base_kfp_image)
    compute_signature_calc_exec_params_op = dsl.component_decorator.component(
        func=signature_calc_compute_execution_params, base_image=base_kfp_image
    )
    compute_cluster_analysis_exec_params_op = dsl.component_decorator.component(
        func=cluster_analysis_compute_execution_params, base_image=base_kfp_image
    )
    compute_get_duplicate_list_exec_params_op = dsl.component_decorator.component(
        func=get_duplicate_list_compute_execution_params, base_image=base_kfp_image
    )
    compute_data_cleaning_exec_params_op = dsl.component_decorator.component(
        func=data_cleaning_compute_execution_params, base_image=base_kfp_image
    )
    
else:
    compute_common_params_op = comp.create_component_from_func(func=compute_common_params, base_image=base_kfp_image)
    compute_signature_calc_exec_params_op = comp.create_component_from_func(
        func=signature_calc_compute_execution_params, base_image=base_kfp_image
    )
    compute_cluster_analysis_exec_params_op = comp.create_component_from_func(
        func=cluster_analysis_compute_execution_params, base_image=base_kfp_image
    )
    compute_get_duplicate_list_exec_params_op = comp.create_component_from_func(
        func=get_duplicate_list_compute_execution_params, base_image=base_kfp_image
    )
    compute_data_cleaning_exec_params_op = comp.create_component_from_func(
        func=data_cleaning_compute_execution_params, base_image=base_kfp_image
    )
    run_id = dsl.RUN_ID_PLACEHOLDER

# create Ray cluster
create_ray_op = comp.load_component_from_file(component_spec_path + "createRayClusterComponent.yaml")
# execute signature calculation job
execute_signature_calc_job_op = comp.load_component_from_file(
    component_spec_path + "executeRayJobComponent_multi_s3.yaml"
)
# execute cluster analysis job
execute_cluster_analysis_job_op = comp.load_component_from_file(component_spec_path + "executeRayJobComponent.yaml")
# execute get duplicate list job
execute_get_duplicate_list_job_op = comp.load_component_from_file(component_spec_path + "executeRayJobComponent.yaml")
# execute data cleaning job
execute_data_cleaning_job_op = comp.load_component_from_file(
    component_spec_path + "executeRayJobComponent_multi_s3.yaml"
)
# clean up Ray
cleanup_ray_op = comp.load_component_from_file(component_spec_path + "deleteRayClusterComponent.yaml")

# Task name is part of the pipeline name, the ray cluster name and the job name in DMF.
TASK_NAME: str = "fuzzydedup"


@dsl.pipeline(
    name=TASK_NAME + "-ray-pipeline",
    description="Pipeline for fuzzy dedup",
)
def fuzzydedup(
    # folders used
    # Ray cluster
    ray_name: str = "fuzzydedup-kfp-ray",  # name of Ray cluster
    ray_run_id_KFPv2: str = "",   # Ray cluster unique ID used only in KFP v2
    # Add image_pull_secret and image_pull_policy to ray workers if needed
    ray_head_options: dict = {
        "cpu": 8,
        "memory": 64,
        "image": task_image,
        "image_pull_secret": image_pull_secret,
        "imagePullPolicy": "Always",
    },
    ray_worker_options: dict = {
        "replicas": 10,
        "max_replicas": 10,
        "min_replicas": 10,
        "cpu": 16,
        "memory": 128,
        "image": task_image,
        "image_pull_secret": image_pull_secret,
        "imagePullPolicy": "Always",
    },
    runtime_actor_options: dict = {"num_cpus": 0.8, "memory": 16},
    server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    # data access. checkpointing is not supported by dedup
    data_s3_config: str = "{'input_folder': 's3://cos-llm-pile-south/spark_test/fd_xs_dataset_test/', 'output_folder': 's3://cos-llm-pile-south/spark_test/fuzzy_dedup_test_output_data/kfp_test_1/'}",
    data_s3_access_secret: str = "s3-south-secret",
    scdata_s3_access_secret: str = "s3-south-secret",
    dcdata_s3_access_secret: str = "s3-south-secret",
    data_max_files: int = -1,
    data_num_samples: int = -1,
    # orchestrator
    runtime_pipeline_id: str = "pipeline_id",
    runtime_code_location: dict = {"github": "github", "commit_hash": "12345", "path": "path"},
    # columns used
    fdedup_contents_column: str = "contents",
    fdedup_document_id_column: str = "int_id_column",
    # fuzzy parameters
    fdedup_num_permutations: int = 112,
    fdedup_num_bands: int = 14,
    fdedup_num_minhashes_per_band: int = 8,
    fdedup_word_shingle_size: int = 5,
    fdedup_shingle_option: str = "word",
    fdedup_jaccard_similarity_threshold: float = 0.75,
    fdedup_seed: int = 42,
    fdedup_operation_mode: str = "annotate",
    # data sampling
    fdedup_n_samples: int = 10,
    # additional parameters
    additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
):
    """
    Pipeline to execute FDEDUP transform
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
    :param scdata_s3_access_secret - signature calculation s3 access secret
    :param dcdata_s3_access_secret - data cleaning s3 access secret
    :param data_s3_config - s3 configuration
    :param data_max_files - max files to process
    :param data_num_samples - num samples to process
    :param runtime_pipeline_id - pipeline id
    :param runtime_code_location - code location
    :param fdedup_contents_column - document column name
    :param fdedup_document_id_column - integer document id column name
    :param fdedup_num_permutations - number of permutations
    :param fdedup_num_bands - number of bands
    :param fdedup_num_minhashes_per_band - length of a band
    :param fdedup_word_shingle_size - length of word shingles
    :param fdedup_shingle_option - type of shingle, one of 'word', or 'char'
    :param fdedup_jaccard_similarity_threshold - similarity threshold
    :param fdedup_seed - seed for the random number generator
    :param fdedup_operation_mode - data cleaning mode, one of 'filter_duplicates', 'filter_non_duplicates', or 'annotate'
    :param fdedup_n_samples - number of samples for parameters computation
    :return: None
    """
    # In KFPv2 dsl.RUN_ID_PLACEHOLDER is deprecated and cannot be used since SDK 2.5.0. On another hand we cannot create
    # a unique string in a component (at runtime) and pass it to the `clean_up_task` of `ExitHandler`, due to
    # https://github.com/kubeflow/pipelines/issues/10187. Therefore, meantime the user is requested to insert
    # a unique string created at run creation time.
    if os.getenv("KFPv2", "0") == "1":
        print("WARNING: the ray cluster name can be non-unique at runtime, please do not execute simultaneous Runs of the "
              "same version of the same pipeline !!!")
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
        compute_common_exec_params = compute_common_params_op(
            worker_options=ray_worker_options,
            actor_options=runtime_actor_options,
            data_s3_config=data_s3_config,
            num_permutations=fdedup_num_permutations,
            n_samples=fdedup_n_samples,
        )
        ComponentUtils.add_settings_to_component(compute_common_exec_params, ONE_HOUR_SEC * 2)
        ComponentUtils.set_s3_env_vars_to_component(compute_common_exec_params, data_s3_access_secret)
        fdedup_num_segments = compute_common_exec_params.outputs["num_segments"]
        runtime_num_actors = compute_common_exec_params.outputs["num_actors"]
        runtime_actor_cpus = compute_common_exec_params.outputs["actor_cpu"]
        runtime_actor_memory = compute_common_exec_params.outputs["actor_memory"]

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
        ray_cluster.after(compute_common_exec_params)

        # Get the parameters for the signature calculation job
        compute_signature_calc_exec_params = compute_signature_calc_exec_params_op(
            runtime_num_actors=runtime_num_actors,
            runtime_actor_cpus=runtime_actor_cpus,
            runtime_actor_memory=runtime_actor_memory,
            data_s3_config=data_s3_config,
            data_max_files=data_max_files,
            data_num_samples=data_num_samples,
            runtime_pipeline_id=runtime_pipeline_id,
            runtime_job_id=run_id,
            runtime_code_location=runtime_code_location,
            doc_column=fdedup_contents_column,
            id_column=fdedup_document_id_column,
            num_permutations=fdedup_num_permutations,
            num_bands=fdedup_num_bands,
            num_minhashes_per_band=fdedup_num_minhashes_per_band,
            word_shingle_size=fdedup_word_shingle_size,
            shingle_option=fdedup_shingle_option,
            threshold=fdedup_jaccard_similarity_threshold,
            num_segments=fdedup_num_segments,
            seed=fdedup_seed,
        )
        ComponentUtils.add_settings_to_component(compute_signature_calc_exec_params, ONE_HOUR_SEC * 2)
        compute_signature_calc_exec_params.after(ray_cluster)

        # Execute signature calculation job
        execute_signature_calc_job = execute_signature_calc_job_op(
            ray_name=ray_name,
            run_id=run_id,
            additional_params=additional_params,
            exec_params=compute_signature_calc_exec_params.output,
            exec_script_name=SIGNATURE_CALC_EXEC_SCRIPT_NAME,
            server_url=server_url,
            prefix="scdata",
        )
        ComponentUtils.add_settings_to_component(execute_signature_calc_job, ONE_WEEK_SEC)
        # FIXME: see https://github.com/kubeflow/pipelines/issues/10914
        if os.getenv("KFPv2", "0") != "1":
            ComponentUtils.set_s3_env_vars_to_component(execute_signature_calc_job, data_s3_access_secret)
            ComponentUtils.set_s3_env_vars_to_component(
                execute_signature_calc_job, scdata_s3_access_secret, prefix="scdata"
            )
        execute_signature_calc_job.after(compute_signature_calc_exec_params)

        # Get the parameters for the cluster analysis job
        compute_cluster_analysis_exec_params = compute_cluster_analysis_exec_params_op(
            runtime_num_actors=runtime_num_actors,
            runtime_actor_cpus=runtime_actor_cpus,
            runtime_actor_memory=runtime_actor_memory,
            data_s3_config=data_s3_config,
            data_max_files=data_max_files,
            data_num_samples=data_num_samples,
            runtime_pipeline_id=runtime_pipeline_id,
            runtime_job_id=run_id,
            runtime_code_location=runtime_code_location,
            num_bands=fdedup_num_bands,
            threshold=fdedup_jaccard_similarity_threshold,
            num_segments=fdedup_num_segments,
        )
        ComponentUtils.add_settings_to_component(compute_cluster_analysis_exec_params, ONE_HOUR_SEC * 2)
        compute_cluster_analysis_exec_params.after(execute_signature_calc_job)
        # Execute job
        execute_cluster_analysis_job = execute_cluster_analysis_job_op(
            ray_name=ray_name,
            run_id=run_id,
            additional_params=additional_params,
            exec_params=compute_cluster_analysis_exec_params.output,
            exec_script_name=CLUSTER_ANALYSIS_EXEC_SCRIPT_NAME,
            server_url=server_url,
        )
        ComponentUtils.add_settings_to_component(execute_cluster_analysis_job, ONE_WEEK_SEC)
        # FIXME: see https://github.com/kubeflow/pipelines/issues/10914
        if os.getenv("KFPv2", "0") != "1":
            ComponentUtils.set_s3_env_vars_to_component(execute_cluster_analysis_job, data_s3_access_secret)
        execute_cluster_analysis_job.after(compute_cluster_analysis_exec_params)

        compute_get_duplicate_list_exec_params = compute_get_duplicate_list_exec_params_op(
            runtime_num_actors=runtime_num_actors,
            runtime_actor_cpus=runtime_actor_cpus,
            runtime_actor_memory=runtime_actor_memory,
            data_s3_config=data_s3_config,
            data_max_files=data_max_files,
            data_num_samples=data_num_samples,
            runtime_pipeline_id=runtime_pipeline_id,
            runtime_job_id=run_id,
            runtime_code_location=runtime_code_location,
        )
        ComponentUtils.add_settings_to_component(compute_get_duplicate_list_exec_params, ONE_HOUR_SEC * 2)
        compute_get_duplicate_list_exec_params.after(execute_cluster_analysis_job)
        # Execute job
        execute_get_duplicate_list_job = execute_get_duplicate_list_job_op(
            ray_name=ray_name,
            run_id=run_id,
            additional_params=additional_params,
            exec_params=compute_get_duplicate_list_exec_params.output,
            exec_script_name=GET_DUPLICATE_LIST_EXEC_SCRIPT_NAME,
            server_url=server_url,
        )
        ComponentUtils.add_settings_to_component(execute_get_duplicate_list_job, ONE_WEEK_SEC)
        # FIXME: see https://github.com/kubeflow/pipelines/issues/10914
        if os.getenv("KFPv2", "0") != "1":
            ComponentUtils.set_s3_env_vars_to_component(execute_get_duplicate_list_job, data_s3_access_secret)
        execute_get_duplicate_list_job.after(compute_get_duplicate_list_exec_params)

        compute_data_cleaning_exec_params = compute_data_cleaning_exec_params_op(
            runtime_num_actors=runtime_num_actors,
            runtime_actor_cpus=runtime_actor_cpus,
            runtime_actor_memory=runtime_actor_memory,
            data_s3_config=data_s3_config,
            data_max_files=data_max_files,
            data_num_samples=data_num_samples,
            runtime_pipeline_id=runtime_pipeline_id,
            runtime_job_id=run_id,
            runtime_code_location=runtime_code_location,
            id_column=fdedup_document_id_column,
            operation_mode=fdedup_operation_mode,
        )
        ComponentUtils.add_settings_to_component(compute_data_cleaning_exec_params, ONE_HOUR_SEC * 2)
        compute_data_cleaning_exec_params.after(execute_get_duplicate_list_job)

        # Execute job
        execute_data_cleaning_job = execute_data_cleaning_job_op(
            ray_name=ray_name,
            run_id=run_id,
            additional_params=additional_params,
            exec_params=compute_data_cleaning_exec_params.output,
            exec_script_name=DATA_CLEANING_EXEC_SCRIPT_NAME,
            server_url=server_url,
            prefix="dcdata",
        )
        ComponentUtils.add_settings_to_component(execute_data_cleaning_job, ONE_WEEK_SEC)
        # FIXME: see https://github.com/kubeflow/pipelines/issues/10914
        if os.getenv("KFPv2", "0") != "1":
            ComponentUtils.set_s3_env_vars_to_component(execute_data_cleaning_job, data_s3_access_secret)
            ComponentUtils.set_s3_env_vars_to_component(
                execute_data_cleaning_job, dcdata_s3_access_secret, prefix="dcdata"
            )
        execute_data_cleaning_job.after(compute_data_cleaning_exec_params)


if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(fuzzydedup, __file__.replace(".py", ".yaml"))
