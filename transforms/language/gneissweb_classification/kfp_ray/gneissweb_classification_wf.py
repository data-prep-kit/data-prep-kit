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
from python_apiserver_client.params import (
        EnvironmentVariables,
        EnvVarFrom,
        EnvVarSource,
)

# The name of the secret that holds the HugginFace token
HF_SECRET = "hf-secret"
# The secret key that holds the HugginFace token
HF_SECRET_KEY = "hf-token"

S3_SECRET="s3-secret"

task_image = "quay.io/dataprep1/data-prep-kit/gneissweb_classification-ray:latest"

# the name of the job script
EXEC_SCRIPT_NAME: str = "-m dpk_gneissweb_classification.ray.transform"

# components
base_kfp_image = "quay.io/dataprep1/data-prep-kit/kfp-data-processing:latest"

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
    runtime_code_location: dict,
    gcls_model_file_name: str,
    gcls_model_url: str,
    gcls_content_column_name: str,
    gcls_output_label_column_name: str,
    gcls_output_score_column_name: str,
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
        "runtime_code_location": str(runtime_code_location),
        "gcls_model_file_name": gcls_model_file_name,
        "gcls_model_url": gcls_model_url,
        "gcls_content_column_name": gcls_content_column_name,
        "gcls_output_label_column_name": gcls_output_label_column_name,
        "gcls_output_score_column_name": gcls_output_score_column_name,
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
TASK_NAME: str = "gneissweb_classification"


# HuggingFace token is exported as environment variables in Ray node pods.
# Alternatively, the secret name can be passed to the KFP component,
# which will set it as an environment variable in the Ray nodes.
# In this option the secret name can be set at runtime
# but is dependent on the KFP version.
env_v = EnvVarFrom(source=EnvVarSource.SECRET, name=HF_SECRET, key=HF_SECRET_KEY)
envs = EnvironmentVariables(from_ref={"HF_READ_ACCESS_TOKEN": env_v})


@dsl.pipeline(
    name=TASK_NAME + "-ray-pipeline",
    description="Pipeline for Gneissweb Classification task",
)
def gneissweb_classification(
    # Ray cluster
    ray_name: str = "gneissweb_classification-kfp-ray",  # name of Ray cluster
    ray_run_id_KFPv2: str = "",  # Ray cluster unique ID used only in KFP v2
    # Add image_pull_secret and image_pull_policy to ray workers if needed
    ray_head_options: dict = {"cpu": 16, "memory": 16, "image": task_image, "environment": envs.to_dict()},
    ray_worker_options: dict = {
        "replicas": 1,
        "max_replicas": 1,
        "min_replicas": 1,
        "cpu": 16,
        "memory": 16,
        "image": task_image,
        "environment": envs.to_dict()
    },
    server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    # data access
    data_s3_config: str = "{'input_folder': 'test/gneissweb_classification/input', 'output_folder': 'test/gneissweb_classification/output/'}",
    data_s3_access_secret: str = S3_SECRET,
    data_max_files: int = -1,
    data_num_samples: int = -1,
    data_checkpointing: bool = False,
    # orchestrator
    runtime_actor_options: dict = {"num_cpus": 0.8},
    runtime_pipeline_id: str = "pipeline_id",
    runtime_code_location: dict = {"github": "github", "commit_hash": "12345", "path": "path"},
    # gneissweb_classification parameters
    gcls_model_url: str = "ibm-granite/GneissWeb.Quality_annotator",
    gcls_model_file_name: str = "fasttext_gneissweb_quality_annotator.bin",
    gcls_content_column_name: str = "text",
    gcls_output_label_column_name: str = "cosmo_fastText_label",
    gcls_output_score_column_name: str = "cosmo_fastText_score",
    # additional parameters
    additional_params: str = '{"wait_interval": 2, "wait_cluster_ready_tmout": 400, "wait_cluster_up_tmout": 300, "wait_job_ready_tmout": 400, "wait_print_tmout": 30, "http_retries": 5, "delete_cluster_delay_minutes": 0}',
):
    """
    Pipeline to execute gneissweb_classification transform
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
    :param runtime_code_location - code location
    :param gcls_model_file_name - filename of model
    :param gcls_model_url - url that model locates. For fasttext, this will be repo name of the model
    :param gcls_content_column_name - Column name to get content
    :param gcls_output_label_column_name - Column name to store label
    :param gcls_output_score_column_name - Column name to store the score
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
            runtime_code_location=runtime_code_location,
            gcls_model_file_name=gcls_model_file_name,
            gcls_model_url=gcls_model_url,
            gcls_content_column_name=gcls_content_column_name,
            gcls_output_label_column_name=gcls_output_label_column_name,
            gcls_output_score_column_name=gcls_output_score_column_name,
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
            env2key = ComponentUtils.set_secret_key_to_env(prefix="jjj")
            kubernetes.use_secret_as_env(task=execute_job, secret_name=S3_SECRET, secret_key_to_env=env2key)
        else:
            ComponentUtils.set_s3_env_vars_to_component(execute_job, data_s3_access_secret)
        execute_job.after(ray_cluster)


if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(gneissweb_classification, __file__.replace(".py", ".yaml"))
