import kfp.dsl as dsl
from workflow_support.compile_utils import ONE_HOUR_SEC, ONE_WEEK_SEC, ComponentUtils
from kubernetes import client as k8s_client
ops={}
short_name = "ml_filter"
description = "filter using a per-language table of conditions"
def compute_exec_params_func(
    worker_options: str,
    actor_options: str,
    data_s3_config: str,
    data_lh_config: str,
    data_max_files: int,
    data_num_samples: int,
    data_checkpointing: bool,
    data_files_to_use: str,
    runtime_pipeline_id: str,
    runtime_job_id: str,
    runtime_code_location: str,
    ml_filter_column_prefix: str,
    ml_filter_lang_column_name: str,
    ml_filter_config: str,
    ml_filter_ignore_missing_columns: bool
) -> dict:
    from runtime_utils import KFPUtils
    return {
        "runtime_num_workers": KFPUtils.default_compute_execution_params(worker_options, actor_options),
        "runtime_worker_options": actor_options,
        "data_s3_config": data_s3_config,
        "data_lh_config": data_lh_config,
        "data_max_files": data_max_files,
        "data_num_samples": data_num_samples,
        "data_checkpointing": data_checkpointing,
        "data_files_to_use": data_files_to_use,
        "runtime_pipeline_id": runtime_pipeline_id,
        "runtime_job_id": runtime_job_id,
        "runtime_code_location": runtime_code_location,
        "ml_filter_column_prefix": ml_filter_column_prefix,
        "ml_filter_lang_column_name": ml_filter_lang_column_name,
        "ml_filter_config": ml_filter_config,
        "ml_filter_ignore_missing_columns": ml_filter_ignore_missing_columns,
    }
@dsl.pipeline(
    name="ml_filter-ray-pipeline",
    description="ml_filter pipeline, filter using a per-language table of conditions",
    )
def ml_filter(
    ray_name: str = "ml_filter-kfp-ray",
    ray_head_options: str = "{\"cpu\": 1, \"memory\": 4, \"image_pull_secret\": \"prod-all-icr-io\", \"image\": \"us.icr.io/cil15-shared-registry/preprocessing-pipelines/ml_filter-ray:0.3.1\" }",
    ray_worker_options: str = "{\"replicas\": 2, \"max_replicas\": 2, \"min_replicas\": 2, \"cpu\": 4, \"memory\": 16, \"image_pull_secret\": \"prod-all-icr-io\", \"image\": \"us.icr.io/cil15-shared-registry/preprocessing-pipelines/ml_filter-ray:0.3.1\"}",
    server_url: str = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888",
    data_lh_config = "{'lh_environment': 'STAGING', 'input_table': 'ibmdatapile.academic.ieee', 'input_dataset': '', 'input_version': 'main', 'output_table': 'processed.ibmdatapile.academic.ieee.lang_id_kfp_0729_01', 'output_path': 'lh-test/tables/processed/ibmdatapile/academic/ieee/lang_id_kfp_0729_01', 'token': 'YOUR_LAKEHOUSE_TOKEN'}",
    data_s3_config: str = "",
    data_s3_access_secret: str = "cos-lh-access",
    data_max_files: int = -1,
    data_num_samples: int = -1,
    data_checkpointing: bool = False,
    data_files_to_use: str = "['.parquet']",
    runtime_actor_options: str = "{'num_cpus': 0.8}",
    runtime_pipeline_id: str = "pipeline_id",
    runtime_code_location: str = "{'github': 'github', 'commit_hash': '12345', 'path': 'path'}",
    ml_filter_column_prefix: str = "",
    ml_filter_lang_column_name: str = "lang",
    ml_filter_config: str = "cleansing-config.yaml",
    ml_filter_ignore_missing_columns: bool = False,
    additional_params: str = "{\"wait_interval\": 2, \"wait_cluster_ready_tmout\": 400, \"wait_cluster_up_tmout\": 300, \"wait_job_ready_tmout\": 400, \"wait_print_tmout\": 30, \"http_retries\": 5}",
) -> None:
    clean_up_task = ops['cleanup_ray'](ray_name=ray_name, run_id=run_id, server_url=server_url)
    ComponentUtils.add_settings_to_component(clean_up_task, 60)
    with dsl.ExitHandler(clean_up_task):
        compute_exec_params = ops['compute_exec_params'](
            worker_options=ray_worker_options,
                actor_options=runtime_actor_options,
                data_s3_config=data_s3_config,
                data_lh_config=data_lh_config,
                data_max_files=data_max_files,
                data_num_samples=data_num_samples,
                data_checkpointing=data_checkpointing,
                data_files_to_use=data_files_to_use,
                runtime_pipeline_id=runtime_pipeline_id,
                runtime_job_id=run_id,
                runtime_code_location=runtime_code_location,
            ml_filter_column_prefix=ml_filter_column_prefix,
            ml_filter_lang_column_name=ml_filter_lang_column_name,
            ml_filter_config=ml_filter_config,
            ml_filter_ignore_missing_columns=ml_filter_ignore_missing_columns,
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
    dsl.get_pipeline_conf().set_image_pull_secrets([k8s_client.V1ObjectReference(name="prod-all-icr-io")])
